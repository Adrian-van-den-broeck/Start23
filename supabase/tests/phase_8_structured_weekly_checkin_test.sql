begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_8_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_8_tap_results to authenticated, service_role;
grant usage, select on sequence phase_8_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_8_tap_results (result)
select has_table('public', 'weekly_checkins', 'weekly check-ins exist');
insert into phase_8_tap_results (result)
select has_table('public', 'weekly_checkin_contexts', 'check-in contexts exist');
insert into phase_8_tap_results (result)
select has_table('public', 'injury_restrictions', 'injury restrictions exist');
insert into phase_8_tap_results (result)
select has_table(
  'public', 'planned_external_activities', 'planned external activities exist'
);
insert into phase_8_tap_results (result)
select has_table(
  'public', 'goal_maintenance_states', 'goal maintenance states exist'
);
insert into phase_8_tap_results (result)
select has_table(
  'public', 'activity_rpe_revisions', 'RPE correction audit exists'
);

insert into phase_8_tap_results (result)
select ok(
  not exists (
    select 1 from pg_class
    where oid in (
      'public.weekly_checkins'::regclass,
      'public.weekly_checkin_contexts'::regclass,
      'public.injury_restrictions'::regclass,
      'public.planned_external_activities'::regclass,
      'public.goal_maintenance_states'::regclass,
      'public.activity_rpe_revisions'::regclass
    ) and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every public Phase 8 table'
);

insert into phase_8_tap_results (result)
select ok(
  not has_table_privilege('anon', 'public.weekly_checkins', 'select')
  and has_table_privilege('authenticated', 'public.weekly_checkins', 'select')
  and has_table_privilege(
    'authenticated', 'public.planned_external_activities', 'select'
  ),
  'explicit Data API grants expose owner reads only to authenticated athletes'
);

insert into phase_8_tap_results (result)
select ok(
  has_function_privilege(
    'authenticated', 'public.start_weekly_checkin(date)', 'execute'
  )
  and not has_function_privilege(
    'anon', 'public.start_weekly_checkin(date)', 'execute'
  )
  and has_function_privilege(
    'service_role', 'public.open_due_weekly_checkins(timestamptz)', 'execute'
  )
  and has_function_privilege(
    'service_role', 'public.create_weekly_plan_proposal_v2(uuid,jsonb)', 'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.create_weekly_plan_proposal_v2(uuid,jsonb)',
    'execute'
  ),
  'athlete and backend RPC privileges remain separated'
);

insert into auth.users (id)
values
  ('a0000000-0000-0000-0000-000000000008'),
  ('b0000000-0000-0000-0000-000000000008');

insert into public.athlete_profiles (athlete_id, timezone, onboarding_status)
values
  (
    'a0000000-0000-0000-0000-000000000008',
    'Pacific/Kiritimati',
    'completed'
  ),
  (
    'b0000000-0000-0000-0000-000000000008',
    'America/Adak',
    'completed'
  );

select set_config('start23.critical_write', 'on', true);
insert into public.initial_plan_requests (
  id, athlete_id, status, onboarding_revision, ruleset_version,
  input_snapshot, input_fingerprint
) values (
  'a1000000-0000-0000-0000-000000000008',
  'a0000000-0000-0000-0000-000000000008',
  'pending',
  1,
  'phase-3-ruleset-3',
  jsonb_build_object(
    'profile', jsonb_build_object(
      'athlete_id', 'a0000000-0000-0000-0000-000000000008',
      'timezone', 'Pacific/Kiritimati',
      'revision', 1
    ),
    'training_history', '[]'::jsonb,
    'goal', jsonb_build_object(
      'target_date', '2026-12-06',
      'race_discipline_profile', array['swim', 'bike', 'run'],
      'revision', 1
    ),
    'zones', '[]'::jsonb,
    'ruleset_version', 'phase-3-ruleset-3'
  ),
  repeat('a', 32)
);
select set_config('start23.critical_write', '', true);

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
insert into phase_8_tap_results (result)
select is(
  public.open_due_weekly_checkins('2026-08-16T10:30:00Z'),
  1,
  'the same instant opens Monday only in the athlete timezone where it is Monday'
);
insert into phase_8_tap_results (result)
select is(
  public.open_due_weekly_checkins('2026-08-16T10:30:00Z'),
  0,
  'the athlete-local Monday entrypoint is retry-idempotent'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000008","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000008';
set local role authenticated;

create temporary table phase_8_checkin as
select public.start_weekly_checkin('2026-08-17') as result;
grant select on phase_8_checkin to authenticated, service_role;

insert into phase_8_tap_results (result)
select is(
  public.start_weekly_checkin('2026-08-17') ->> 'id',
  (select result ->> 'id' from phase_8_checkin),
  'the athlete-local week start is idempotent'
);

insert into phase_8_tap_results (result)
select throws_ok(
  $$
    insert into public.weekly_checkins (
      athlete_id, week_start, timezone
    ) values (
      'a0000000-0000-0000-0000-000000000008',
      '2026-08-24',
      'Pacific/Kiritimati'
    )
  $$,
  '42501',
  'weekly context writes require an approved RPC',
  'direct context writes are rejected even for the owner'
);

insert into phase_8_tap_results (result)
select lives_ok(
  format(
    $sql$
      select public.save_weekly_checkin_context(
        %L::uuid,
        0,
        repeat('b', 64),
        jsonb_build_object(
          'blocked_dates', jsonb_build_array('2026-08-18'),
          'fatigue_level', 'moderate',
          'missed_workout_reasons', jsonb_build_array('fatigue'),
          'recurring_activities_confirmed', true,
          'external_activities', jsonb_build_array(
            jsonb_build_object(
              'name', 'Club run',
              'discipline', 'run',
              'scheduled_at', '2026-08-19T18:00:00+14:00',
              'duration_minutes', 60,
              'strenuous', true,
              'recurring', true
            )
          ),
          'restrictions', jsonb_build_array(
            jsonb_build_object(
              'discipline', 'swim', 'status', 'self_reported_blocked',
              'source', 'athlete', 'athlete_plan_choice', 'keep_blocked'
            ),
            jsonb_build_object(
              'discipline', 'bike', 'status', 'self_reported_blocked',
              'source', 'athlete', 'athlete_plan_choice', 'keep_blocked'
            ),
            jsonb_build_object(
              'discipline', 'run', 'status', 'professional_restricted',
              'source', 'physiotherapist',
              'athlete_plan_choice', 'keep_blocked',
              'professional_advice', 'No running this week.',
              'professional_advice_at', '2026-08-13T10:00:00+14:00'
            )
          ),
          'alarm_symptoms_acknowledged', true
        )
      )
    $sql$,
    (select result ->> 'id' from phase_8_checkin)
  ),
  'structured context can be saved as a revisioned draft'
);

insert into phase_8_tap_results (result)
select lives_ok(
  format(
    $sql$
      select public.confirm_weekly_checkin_context(
        %L::uuid, 1, repeat('b', 64)
      )
    $sql$,
    (select result ->> 'id' from phase_8_checkin)
  ),
  'the athlete explicitly confirms the exact fingerprinted context'
);

insert into phase_8_tap_results (result)
select is(
  (select count(*) from public.injury_restrictions where cleared_at is null),
  3::bigint,
  'all three reviewed restrictions remain active until an explicit later review'
);
insert into phase_8_tap_results (result)
select is(
  (select count(*) from public.planned_external_activities),
  1::bigint,
  'confirmed outside sport is persisted as a planned activity'
);

insert into phase_8_tap_results (result)
select is(
  public.create_external_activity_summary(
    (select id from public.planned_external_activities limit 1),
    'a2000000-0000-0000-0000-000000000008',
    repeat('d', 64),
    jsonb_build_object(
      'planned_external_activity_id',
        (select id from public.planned_external_activities limit 1),
      'discipline', 'run',
      'started_at', '2026-08-19T18:10:00+14:00',
      'timezone', 'Pacific/Kiritimati',
      'duration_minutes', 55
    )
  ) ->> 'processing_state',
  'awaiting_rpe',
  'a planned outside activity accepts actual duration and enters the RPE flow'
);
insert into phase_8_tap_results (result)
select is(
  (select status from public.planned_external_activities limit 1),
  'completed',
  'the outside activity is atomically linked to its canonical completion'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-000000000008","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'b0000000-0000-0000-0000-000000000008';
set local role authenticated;
insert into phase_8_tap_results (result)
select throws_ok(
  format(
    'select public.get_weekly_checkin(%L::uuid)',
    (select result ->> 'id' from phase_8_checkin)
  ),
  'P0002',
  'weekly check-in not found',
  'another athlete cannot discover the check-in'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
create temporary table phase_8_proposal as
select public.create_weekly_plan_proposal_v2(
  'a0000000-0000-0000-0000-000000000008',
  jsonb_build_object(
    'plan_id', null,
    'checkin_id', (select result ->> 'id' from phase_8_checkin),
    'initial_plan_request_id', 'a1000000-0000-0000-0000-000000000008',
    'expected_base_revision', 0,
    'week_start', '2026-08-17',
    'timezone', 'Pacific/Kiritimati',
    'phase', 'base',
    'target_basis', 'injury_rest_only',
    'input_fingerprint', repeat('a', 32),
    'generation_fingerprint', repeat('c', 64),
    'total_duration_minutes', 0,
    'low_intensity_percent', 0,
    'high_intensity_percent', 0,
    'confirmed_injuries', jsonb_build_array('swim', 'bike', 'run'),
    'low_only_disciplines', '[]'::jsonb,
    'goal_disciplines', jsonb_build_array('swim', 'bike', 'run'),
    'availability', '[]'::jsonb,
    'workouts', '[]'::jsonb,
    'warnings', jsonb_build_array(
      jsonb_build_object(
        'rule_id', 'BR-010',
        'code', 'all_disciplines_blocked_rest_only',
        'severity', 'warning',
        'message', 'Rest only; athlete confirmation is required.'
      )
    ),
    'target_tss', 0,
    'planned_tss', 0,
    'ruleset_version', 'phase-3-ruleset-3'
  )
) as result;
grant select on phase_8_proposal to authenticated, service_role;

insert into phase_8_tap_results (result)
select is(
  (
    select revision.target_basis
    from public.plan_revisions revision
    where revision.id = (
      select proposal.target_plan_revision_id
      from public.change_proposals proposal
      where proposal.id = (
        select (result ->> 'proposal_id')::uuid from phase_8_proposal
      )
    )
  ),
  'injury_rest_only',
  'all blocked goal disciplines create a pending rest-only revision'
);

insert into phase_8_tap_results (result)
select is(
  (
    select load.planned_tss
    from private.plan_revision_loads load
    where load.revision_id = (
      select proposal.target_plan_revision_id
      from public.change_proposals proposal
      where proposal.id = (
        select (result ->> 'proposal_id')::uuid from phase_8_proposal
      )
    )
  ),
  0::numeric,
  'rest-only private planned load is exactly zero'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000008","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000008';
set local role authenticated;
insert into phase_8_tap_results (result)
select lives_ok(
  format(
    'select public.approve_plan_proposal(%L::uuid, 0)',
    (select result ->> 'proposal_id' from phase_8_proposal)
  ),
  'the athlete, not the generator, activates the rest-only plan'
);
insert into phase_8_tap_results (result)
select is(
  (
    select count(*)
    from public.get_calendar_rest_days(
      '2026-08-16T10:00:00Z',
      '2026-08-23T10:00:00Z'
    )
  ),
  7::bigint,
  'the approved empty calendar exposes seven intentional rest days'
);

reset role;
select set_config('request.jwt.claims', '{}', true);
select set_config('start23.checkin_write', 'on', true);
select set_config('start23.critical_write', 'on', true);
delete from public.weekly_plans
where athlete_id = 'a0000000-0000-0000-0000-000000000008';
delete from public.weekly_checkins
where athlete_id = 'a0000000-0000-0000-0000-000000000008';
delete from public.initial_plan_requests
where athlete_id = 'a0000000-0000-0000-0000-000000000008';
delete from auth.users
where id in (
  'a0000000-0000-0000-0000-000000000008',
  'b0000000-0000-0000-0000-000000000008'
);

select plan(count(*)::integer) from phase_8_tap_results;
select result from phase_8_tap_results order by sequence;
select * from finish();

rollback;
