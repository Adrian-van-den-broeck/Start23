begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_6_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_6_tap_results to authenticated, service_role;
grant usage, select on sequence phase_6_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_6_tap_results (result)
select has_table('public', 'weekly_plans', 'weekly_plans exists');
insert into phase_6_tap_results (result)
select has_table('public', 'plan_revisions', 'plan_revisions exists');
insert into phase_6_tap_results (result)
select has_table('public', 'planned_workouts', 'planned_workouts exists');
insert into phase_6_tap_results (result)
select has_table('public', 'plan_warnings', 'plan_warnings exists');
insert into phase_6_tap_results (result)
select has_table(
  'private',
  'planned_workout_loads',
  'private.planned_workout_loads exists'
);
insert into phase_6_tap_results (result)
select has_table(
  'private',
  'plan_revision_loads',
  'private.plan_revision_loads exists'
);

insert into phase_6_tap_results (result)
select ok(
  not exists (
    select 1
    from pg_class
    where oid in (
      'public.weekly_plans'::regclass,
      'public.plan_revisions'::regclass,
      'public.planned_workouts'::regclass,
      'public.plan_warnings'::regclass
    )
    and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every public Phase 6 table'
);

insert into phase_6_tap_results (result)
select ok(
  not exists (
    select 1
    from (
      values
        ('weekly_plans'),
        ('plan_revisions'),
        ('planned_workouts'),
        ('plan_warnings')
    ) as tables(table_name)
    where has_table_privilege(
      'anon',
      'public.' || tables.table_name,
      'select'
    )
  ),
  'anonymous clients cannot read Phase 6 planning tables'
);

insert into phase_6_tap_results (result)
select ok(
  not has_schema_privilege('authenticated', 'private', 'usage')
  and not has_table_privilege(
    'authenticated',
    'private.planned_workout_loads',
    'select'
  )
  and not has_table_privilege(
    'authenticated',
    'private.plan_revision_loads',
    'select'
  )
  and not has_table_privilege(
    'service_role',
    'private.planned_workout_loads',
    'select'
  )
  and not has_table_privilege(
    'service_role',
    'private.plan_revision_loads',
    'select'
  ),
  'hidden workout and revision loads have no direct API-role access'
);

insert into phase_6_tap_results (result)
select ok(
  (
    select prosecdef
    from pg_proc
    where oid =
      'public.create_weekly_plan_proposal(uuid,jsonb)'::regprocedure
  )
  and has_function_privilege(
    'service_role',
    'public.create_weekly_plan_proposal(uuid,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.create_weekly_plan_proposal(uuid,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'anon',
    'public.create_weekly_plan_proposal(uuid,jsonb)',
    'execute'
  ),
  'only the trusted backend can persist a generated plan proposal'
);

insert into phase_6_tap_results (result)
select ok(
  not (
    select prosecdef
    from pg_proc
    where oid =
      'public.approve_plan_proposal(uuid,integer)'::regprocedure
  )
  and not (
    select prosecdef
    from pg_proc
    where oid = 'public.reject_plan_proposal(uuid)'::regprocedure
  )
  and has_function_privilege(
    'authenticated',
    'public.approve_plan_proposal(uuid,integer)',
    'execute'
  )
  and has_function_privilege(
    'authenticated',
    'public.reject_plan_proposal(uuid)',
    'execute'
  ),
  'owner decisions use narrowly granted security-invoker RPCs'
);

insert into auth.users (id)
values
  ('60000000-0000-0000-0000-000000000006'),
  ('70000000-0000-0000-0000-000000000007');

select set_config('start23.critical_write', 'on', true);
insert into public.initial_plan_requests (
  id,
  athlete_id,
  status,
  onboarding_revision,
  ruleset_version,
  input_snapshot,
  input_fingerprint
)
values (
  '61000000-0000-0000-0000-000000000006',
  '60000000-0000-0000-0000-000000000006',
  'pending',
  1,
  'phase-3-ruleset-2',
  jsonb_build_object(
    'profile', jsonb_build_object(
      'athlete_id', '60000000-0000-0000-0000-000000000006',
      'timezone', 'UTC',
      'revision', 1
    ),
    'training_history', '[]'::jsonb,
    'goal', jsonb_build_object(
      'target_date', '2026-12-06',
      'race_discipline_profile', array['swim', 'bike', 'run'],
      'revision', 1
    ),
    'zones', '[]'::jsonb,
    'ruleset_version', 'phase-3-ruleset-2'
  ),
  md5(
    jsonb_build_object(
      'profile', jsonb_build_object(
        'athlete_id', '60000000-0000-0000-0000-000000000006',
        'timezone', 'UTC',
        'revision', 1
      ),
      'training_history', '[]'::jsonb,
      'goal', jsonb_build_object(
        'target_date', '2026-12-06',
        'race_discipline_profile', array['swim', 'bike', 'run'],
        'revision', 1
      ),
      'zones', '[]'::jsonb,
      'ruleset_version', 'phase-3-ruleset-2'
    )::text
  )
);
select set_config('start23.critical_write', '', true);

create temporary table phase_6_input as
select input_fingerprint
from public.initial_plan_requests
where id = '61000000-0000-0000-0000-000000000006';
grant select on phase_6_input to service_role;

select set_config(
  'request.jwt.claims',
  '{"role":"service_role"}',
  true
);
set local role service_role;

create temporary table phase_6_result as
select public.create_weekly_plan_proposal(
  '60000000-0000-0000-0000-000000000006',
  jsonb_build_object(
    'initial_plan_request_id',
      '61000000-0000-0000-0000-000000000006',
    'plan_id', null,
    'input_fingerprint', (select input_fingerprint from phase_6_input),
    'generation_fingerprint', repeat('b', 64),
    'expected_base_revision', 0,
    'week_start', '2026-08-03',
    'timezone', 'UTC',
    'phase', 'base',
    'target_basis', 'initial_catalog_baseline',
    'target_tss', '6.916666666666666666666666667',
    'taper_period', null,
    'total_duration_minutes', 145,
    'low_intensity_percent', 100,
    'high_intensity_percent', 0,
    'confirmed_injuries', '[]'::jsonb,
    'availability', jsonb_build_array(
      jsonb_build_object(
        'starts_at', '2026-08-03T07:00:00+00:00',
        'ends_at', '2026-08-03T09:00:00+00:00'
      ),
      jsonb_build_object(
        'starts_at', '2026-08-05T07:00:00+00:00',
        'ends_at', '2026-08-05T09:00:00+00:00'
      )
    ),
    'workouts', jsonb_build_array(
      jsonb_build_object(
        'template_id', '51000000-0000-0000-0000-000000000001',
        'discipline', 'swim',
        'scheduled_at', '2026-08-03T07:00:00+00:00',
        'source', 'auto_planned'
      ),
      jsonb_build_object(
        'template_id', '51000000-0000-0000-0000-000000000003',
        'discipline', 'bike',
        'scheduled_at', '2026-08-03T08:00:00+00:00',
        'source', 'auto_planned'
      ),
      jsonb_build_object(
        'template_id', '52000000-0000-0000-0000-000000000005',
        'discipline', 'run',
        'scheduled_at', '2026-08-05T07:00:00+00:00',
        'source', 'auto_planned'
      )
    ),
    'warnings', jsonb_build_array(
      jsonb_build_object(
        'rule_id', 'BR-003',
        'code', 'intensity_distribution_outside_target',
        'severity', 'warning',
        'message',
          'The reviewed deck does not exactly match the standard distribution.',
        'affected_template_id', null
      )
    ),
    'planned_tss', '6.916666666666666666666666667',
    'ruleset_version', 'phase-3-ruleset-2'
  )
) as result;
grant select on phase_6_result to authenticated;

insert into phase_6_tap_results (result)
select is(
  (
    select count(*)
    from public.create_weekly_plan_proposal(
      '60000000-0000-0000-0000-000000000006',
      jsonb_build_object(
        'initial_plan_request_id',
          '61000000-0000-0000-0000-000000000006',
        'plan_id', null,
        'input_fingerprint', (select input_fingerprint from phase_6_input),
        'generation_fingerprint', repeat('b', 64),
        'expected_base_revision', 0,
        'week_start', '2026-08-03',
        'timezone', 'UTC',
        'phase', 'base',
        'target_basis', 'initial_catalog_baseline',
        'target_tss', 1,
        'taper_period', null,
        'total_duration_minutes', 1,
        'low_intensity_percent', 100,
        'high_intensity_percent', 0,
        'confirmed_injuries', '[]'::jsonb,
        'availability', jsonb_build_array(jsonb_build_object('retry', true)),
        'workouts', jsonb_build_array(jsonb_build_object('retry', true)),
        'warnings', '[]'::jsonb,
        'planned_tss', 1,
        'ruleset_version', 'phase-3-ruleset-2'
      )
    )
  ),
  1::bigint,
  'generation is idempotent before evaluating a changed retry payload'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"60000000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '60000000-0000-0000-0000-000000000006';
set local role authenticated;

insert into phase_6_tap_results (result)
select is(
  (select count(*) from public.weekly_plans),
  1::bigint,
  'the owner sees one pending stable weekly plan'
);
insert into phase_6_tap_results (result)
select is(
  (
    select count(*)
    from public.plan_revisions
    where state = 'pending_approval'
  ),
  1::bigint,
  'the generated revision remains pending approval'
);
insert into phase_6_tap_results (result)
select is(
  (
    select count(*)
    from public.planned_workouts
  ),
  3::bigint,
  'the pending revision snapshots all three selected workouts'
);
insert into phase_6_tap_results (result)
select ok(
  position(
    'tss' in lower(
      public.get_weekly_plan(
        (select (result ->> 'plan_id')::uuid from phase_6_result),
        1
      )::text
    )
  ) = 0,
  'the public weekly-plan RPC contains no TSS key'
);

insert into phase_6_tap_results (result)
select throws_ok(
  $$
    select public.approve_plan_proposal(
      (select (result ->> 'proposal_id')::uuid from phase_6_result),
      1
    )
  $$,
  '40001',
  'plan proposal is stale',
  'approval rejects a mismatched expected base revision'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"70000000-0000-0000-0000-000000000007","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '70000000-0000-0000-0000-000000000007';

insert into phase_6_tap_results (result)
select throws_ok(
  $$
    select public.approve_plan_proposal(
      (select (result ->> 'proposal_id')::uuid from phase_6_result),
      0
    )
  $$,
  'P0002',
  'plan proposal not found',
  'another athlete cannot approve the pending proposal'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"60000000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '60000000-0000-0000-0000-000000000006';

insert into phase_6_tap_results (result)
select lives_ok(
  $$
    select public.approve_plan_proposal(
      (select (result ->> 'proposal_id')::uuid from phase_6_result),
      0
    )
  $$,
  'the authenticated owner can atomically approve the current revision'
);
insert into phase_6_tap_results (result)
select lives_ok(
  $$
    select public.approve_plan_proposal(
      (select (result ->> 'proposal_id')::uuid from phase_6_result),
      0
    )
  $$,
  'repeating the same approval returns the already-applied result'
);
insert into phase_6_tap_results (result)
select is(
  (select active_revision from public.weekly_plans),
  1,
  'approval activates exactly revision one'
);
insert into phase_6_tap_results (result)
select is(
  (
    select state
    from public.change_proposals
    where id = (
      select (result ->> 'proposal_id')::uuid from phase_6_result
    )
  ),
  'applied',
  'proposal application commits with active-plan promotion'
);
insert into phase_6_tap_results (result)
select is(
  (
    select decision_actor
    from public.change_proposals
    where id = (
      select (result ->> 'proposal_id')::uuid from phase_6_result
    )
  ),
  '60000000-0000-0000-0000-000000000006'::uuid,
  'the atomic decision records the authenticated athlete actor'
);

create temporary table phase_6_workout as
select id
from public.planned_workouts
where discipline = 'run'
limit 1;
grant select on phase_6_workout to service_role;

insert into phase_6_tap_results (result)
select throws_ok(
  $$
    select public.move_planned_workout(
      '60000000-0000-0000-0000-000000000006',
      (select id from phase_6_workout),
      1,
      '2026-08-06T07:00:00+00:00',
      '[]'::jsonb
    )
  $$,
  '42501',
  'permission denied for function move_planned_workout',
  'an athlete cannot bypass the backend direct-move warning path'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"role":"service_role"}',
  true
);
set local role service_role;
insert into phase_6_tap_results (result)
select lives_ok(
  $$
    select public.move_planned_workout(
      '60000000-0000-0000-0000-000000000006',
      (select id from phase_6_workout),
      1,
      '2026-08-06T07:00:00+00:00',
      jsonb_build_array(
        jsonb_build_object(
          'rule_id', 'BR-002',
          'code', 'outside_confirmed_availability',
          'severity', 'warning',
          'message', 'This move falls outside confirmed availability.'
        )
      )
    )
  $$,
  'the trusted backend persists an explicit owner move as a new revision'
);

reset role;
create temporary table phase_6_rejection (
  id uuid primary key
);

with target_revision as (
  insert into public.plan_revisions (
    plan_id, athlete_id, revision_number, state, source, phase,
    target_basis, taper_period, input_fingerprint, generation_fingerprint,
    initial_plan_request_id, total_duration_minutes, low_intensity_percent,
    high_intensity_percent, confirmed_injuries, availability, ruleset_version
  )
  select
    plan_id, athlete_id, 3, 'pending_approval', 'system_generated', phase,
    target_basis, taper_period, input_fingerprint, repeat('c', 64),
    initial_plan_request_id, total_duration_minutes, low_intensity_percent,
    high_intensity_percent, confirmed_injuries, availability, ruleset_version
  from public.plan_revisions
  where state = 'active'
  returning id, athlete_id
), rejected_proposal as (
  insert into public.change_proposals (
    athlete_id, kind, target_plan_revision_id, base_plan_revision,
    reason_codes, public_explanation, ruleset_version
  )
  select
    athlete_id, 'plan_revision', id, 2, array['weekly_plan_ready'],
    'A deterministic weekly plan is ready for review.',
    'phase-3-ruleset-2'
  from target_revision
  returning id
)
insert into phase_6_rejection (id)
select id from rejected_proposal;
grant select on phase_6_rejection to authenticated;

select set_config(
  'request.jwt.claims',
  '{"sub":"60000000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '60000000-0000-0000-0000-000000000006';
set local role authenticated;

insert into phase_6_tap_results (result)
select lives_ok(
  $$
    select public.reject_plan_proposal(
      (select id from phase_6_rejection)
    )
  $$,
  'the owner can reject a replacement plan revision'
);
insert into phase_6_tap_results (result)
select lives_ok(
  $$
    select public.reject_plan_proposal(
      (select id from phase_6_rejection)
    )
  $$,
  'repeating the same rejection returns the already-rejected result'
);

insert into phase_6_tap_results (result)
select is(
  (select active_revision from public.weekly_plans),
  2,
  'a direct move advances optimistic concurrency to revision two'
);
insert into phase_6_tap_results (result)
select is(
  (
    select count(*)
    from public.plan_revisions
    where state = 'active'
  ),
  1::bigint,
  'only one revision remains active after the direct move'
);
insert into phase_6_tap_results (result)
select is(
  (
    select count(*)
    from public.planned_workouts
    where revision_id = (
      select id
      from public.plan_revisions
      where state = 'active'
    )
  ),
  3::bigint,
  'the direct move preserves immutable workout snapshots'
);

reset role;

insert into phase_6_tap_results (result)
select * from finish();

select result
from phase_6_tap_results
order by sequence;
rollback;
