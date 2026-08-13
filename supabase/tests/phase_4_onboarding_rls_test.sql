begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table('public', 'athlete_profiles');
select has_table('public', 'change_proposals');
select has_table('public', 'goals');
select has_table('public', 'initial_plan_requests');
select has_table('public', 'onboarding_sessions');
select has_table('public', 'training_history_entries');
select has_table('public', 'zone_boundaries');
select has_table('public', 'zone_metrics');
select has_table('public', 'zone_profile_versions');

select ok(
  not exists (
    select 1
    from pg_class
    where oid in (
      'public.onboarding_sessions'::regclass,
      'public.training_history_entries'::regclass,
      'public.goals'::regclass,
      'public.zone_profile_versions'::regclass,
      'public.zone_metrics'::regclass,
      'public.zone_boundaries'::regclass,
      'public.change_proposals'::regclass,
      'public.initial_plan_requests'::regclass
    )
    and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every Phase 4 table'
);

select ok(
  not exists (
    select 1
    from (
      values
        ('onboarding_sessions'),
        ('training_history_entries'),
        ('goals'),
        ('zone_profile_versions'),
        ('zone_metrics'),
        ('zone_boundaries'),
        ('change_proposals'),
        ('initial_plan_requests')
    ) as tables(table_name)
    where has_table_privilege(
      'anon',
      'public.' || tables.table_name,
      'select'
    )
  ),
  'anon cannot read any Phase 4 table'
);

select ok(
  not (
    select prosecdef
    from pg_proc
    where oid = 'public.save_primary_race_goal(uuid,text,text,text,smallint,date,text[])'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.save_zone_profile(text,text,text,numeric,jsonb,boolean,text,text)'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.replace_training_history(jsonb)'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.complete_onboarding()'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.approve_zone_proposal(uuid,uuid)'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.reject_zone_proposal(uuid)'::regprocedure
  ),
  'all athlete-token Phase 4 RPCs are security invoker'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.save_primary_race_goal(uuid,text,text,text,smallint,date,text[])',
    'execute'
  )
  and not has_function_privilege(
    'anon',
    'public.save_primary_race_goal(uuid,text,text,text,smallint,date,text[])',
    'execute'
  )
  and not has_function_privilege(
    'service_role',
    'public.save_primary_race_goal(uuid,text,text,text,smallint,date,text[])',
    'execute'
  ),
  'only authenticated athletes can invoke the primary-goal RPC'
);

select ok(
  (
    select prosecdef
    from pg_proc
    where oid = 'public.save_fallback_zone_profile(uuid,text,jsonb)'::regprocedure
  )
  and has_function_privilege(
    'service_role',
    'public.save_fallback_zone_profile(uuid,text,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.save_fallback_zone_profile(uuid,text,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'anon',
    'public.save_fallback_zone_profile(uuid,text,jsonb)',
    'execute'
  ),
  'only the service role can execute the trusted fallback RPC'
);

insert into auth.users (id)
values
  ('30000000-0000-0000-0000-000000000003'),
  ('40000000-0000-0000-0000-000000000004');

insert into public.athlete_profiles (
  athlete_id,
  timezone,
  onboarding_status
)
values
  (
    '30000000-0000-0000-0000-000000000003',
    'Europe/Amsterdam',
    'in_progress'
  ),
  (
    '40000000-0000-0000-0000-000000000004',
    'Europe/London',
    'in_progress'
  );

set local role authenticated;
set local request.jwt.claim.sub = '30000000-0000-0000-0000-000000000003';

select throws_ok(
  $$
    insert into public.goals (
      athlete_id,
      title,
      specific_description,
      measurable_outcome,
      feasibility_score,
      target_date,
      race_discipline_profile
    )
    values (
      '30000000-0000-0000-0000-000000000003',
      'Bypass attempt',
      'Direct writes must fail.',
      'No mutation.',
      5,
      '2027-07-01',
      array['run']
    )
  $$,
  '42501',
  'critical object writes require a Start23 RPC',
  'direct critical writes are rejected even for the owner'
);

select lives_ok(
  $$
    select public.save_primary_race_goal(
      null,
      'Owned A race',
      'Finish the race with an even run.',
      'Complete all three disciplines.',
      8::smallint,
      '2027-07-01',
      array['swim', 'bike', 'run']
    )
  $$,
  'the authenticated owner can save the goal through the invoker RPC'
);

select is(
  (select count(*) from public.goals where status = 'active'),
  1::bigint,
  'the owner sees one active primary goal'
);

select lives_ok(
  $$
    select * from public.replace_training_history(
      '[
        {"discipline":"swim","weekly_minutes":60,"experience_years":1},
        {"discipline":"bike","weekly_minutes":120,"experience_years":2},
        {"discipline":"run","weekly_minutes":90,"experience_years":3}
      ]'::jsonb
    )
  $$,
  'the owner can atomically replace all three history rows'
);

select is(
  (select count(*) from public.training_history_entries),
  3::bigint,
  'the owner sees exactly three history rows'
);

select throws_ok(
  $$
    select public.save_zone_profile(
      'bike',
      'fallback',
      null,
      null,
      '[
        {"zone_number":1,"lower_value":100,"upper_value":110},
        {"zone_number":2,"lower_value":110,"upper_value":120},
        {"zone_number":3,"lower_value":120,"upper_value":130},
        {"zone_number":4,"lower_value":130,"upper_value":140},
        {"zone_number":5,"lower_value":140,"upper_value":150}
      ]'::jsonb,
      false,
      'within_soft_range',
      'forged-ruleset'
    )
  $$,
  '42501',
  'fallback zones require the trusted backend RPC',
  'an authenticated athlete cannot persist forged fallback output directly'
);

select throws_ok(
  $$
    select public.save_zone_profile(
      'run',
      'manual',
      'run_lthr_bpm',
      170,
      '[
        {"zone_number":1,"lower_value":100,"upper_value":110},
        {"zone_number":2,"lower_value":110,"upper_value":120},
        {"zone_number":3,"lower_value":120,"upper_value":130},
        {"zone_number":4,"lower_value":130,"upper_value":140},
        {"zone_number":5,"lower_value":140,"upper_value":150}
      ]'::jsonb,
      false,
      'within_soft_range',
      'forged-ruleset'
    )
  $$,
  '23514',
  'manual zone review metadata is server-controlled',
  'an authenticated athlete cannot forge manual review metadata'
);

select lives_ok(
  $$
    select public.save_zone_profile(
      'run',
      'manual',
      'run_lthr_bpm',
      170,
      '[
        {"zone_number":1,"lower_value":100,"upper_value":110},
        {"zone_number":2,"lower_value":110,"upper_value":120},
        {"zone_number":3,"lower_value":120,"upper_value":130},
        {"zone_number":4,"lower_value":130,"upper_value":140},
        {"zone_number":5,"lower_value":140,"upper_value":150}
      ]'::jsonb,
      true,
      'soft_range_not_configured',
      'phase-3-ruleset-2'
    )
  $$,
  'the first confirmed zone version activates'
);

select lives_ok(
  $$
    select public.save_zone_profile(
      'run',
      'manual',
      'run_lthr_bpm',
      172,
      '[
        {"zone_number":1,"lower_value":101,"upper_value":111},
        {"zone_number":2,"lower_value":111,"upper_value":121},
        {"zone_number":3,"lower_value":121,"upper_value":131},
        {"zone_number":4,"lower_value":131,"upper_value":141},
        {"zone_number":5,"lower_value":141,"upper_value":151}
      ]'::jsonb,
      true,
      'soft_range_not_configured',
      'phase-3-ruleset-2'
    )
  $$,
  'a replacement zone version remains pending'
);

select is(
  (
    select count(*)
    from public.zone_profile_versions
    where discipline = 'run' and status = 'active'
  ),
  1::bigint,
  'a pending replacement does not replace the active version'
);

select lives_ok(
  $$
    select public.approve_zone_proposal(
      (
        select id
        from public.change_proposals
        where kind = 'zone_update' and state = 'pending'
      ),
      (
        select base_zone_profile_id
        from public.change_proposals
        where kind = 'zone_update' and state = 'pending'
      )
    )
  $$,
  'zone approval atomically promotes the pending version'
);

select is(
  (
    select version
    from public.zone_profile_versions
    where discipline = 'run' and status = 'active'
  ),
  2,
  'the approved version is the only active run profile'
);

select is(
  (
    select state
    from public.change_proposals
    where kind = 'zone_update'
  ),
  'applied',
  'approval reaches applied in the same transaction'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"role":"service_role"}',
  true
);
set local role service_role;

select lives_ok(
  $$
    select public.save_fallback_zone_profile(
      '30000000-0000-0000-0000-000000000003',
      'bike',
      '[
        {"zone_number":1,"lower_value":100,"upper_value":110},
        {"zone_number":2,"lower_value":110,"upper_value":120},
        {"zone_number":3,"lower_value":120,"upper_value":130},
        {"zone_number":4,"lower_value":130,"upper_value":140},
        {"zone_number":5,"lower_value":140,"upper_value":150}
      ]'::jsonb
    )
  $$,
  'the service-only RPC persists server-generated fallback zones'
);

reset role;
select set_config('start23.critical_write', 'on', true);
insert into public.initial_plan_requests (
  athlete_id,
  onboarding_revision,
  ruleset_version
)
values (
  '30000000-0000-0000-0000-000000000003',
  1,
  'phase-3-ruleset-2'
);

select is(
  (
    select input_fingerprint
    from public.initial_plan_requests
    where athlete_id = '30000000-0000-0000-0000-000000000003'
  ),
  (
    select md5(input_snapshot::text)
    from public.initial_plan_requests
    where athlete_id = '30000000-0000-0000-0000-000000000003'
  ),
  'the initial planning request fingerprints its complete input snapshot'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"30000000-0000-0000-0000-000000000003","role":"authenticated"}',
  true
);
set local role authenticated;

select lives_ok(
  $$
    select public.save_primary_race_goal(
      (
        select id from public.goals where status = 'active'
      ),
      'Updated owned A race',
      'Finish the race with a negative-split run.',
      'Complete all three disciplines.',
      8::smallint,
      '2027-07-01',
      array['swim', 'bike', 'run']
    )
  $$,
  'updating a planning input refreshes the pending request snapshot'
);

select is(
  (
    select (input_snapshot #>> '{goal,revision}')::bigint
    from public.initial_plan_requests
    where athlete_id = '30000000-0000-0000-0000-000000000003'
  ),
  2::bigint,
  'the pending planning snapshot follows the current goal revision'
);

select set_config('start23.critical_write', '', true);
select set_config(
  'request.jwt.claims',
  '{"sub":"40000000-0000-0000-0000-000000000004","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = '40000000-0000-0000-0000-000000000004';

select is(
  (select count(*) from public.goals),
  0::bigint,
  'a second athlete cannot read the first athlete goal'
);

select is(
  (select count(*) from public.training_history_entries),
  0::bigint,
  'a second athlete cannot read the first athlete history'
);

select results_eq(
  $$
    update public.athlete_profiles
    set timezone = 'Europe/Paris'
    where athlete_id = '30000000-0000-0000-0000-000000000003'
    returning athlete_id
  $$,
  $$select null::uuid where false$$,
  'a second athlete cannot update the first athlete profile'
);

select throws_ok(
  $$
    update public.athlete_profiles
    set onboarding_status = 'completed'
    where athlete_id = '40000000-0000-0000-0000-000000000004'
  $$,
  '42501',
  'onboarding completion requires the completion RPC',
  'onboarding completion cannot bypass validation'
);

reset role;

select * from finish();
rollback;
