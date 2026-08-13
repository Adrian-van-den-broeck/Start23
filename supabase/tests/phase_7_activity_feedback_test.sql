begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_7_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_7_tap_results to authenticated, service_role;
grant usage, select on sequence phase_7_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_7_tap_results (result)
select has_table('public', 'activities', 'activities exists');
insert into phase_7_tap_results (result)
select has_table('public', 'activity_metrics', 'activity_metrics exists');
insert into phase_7_tap_results (result)
select has_table('private', 'activity_loads', 'private activity loads exist');

insert into phase_7_tap_results (result)
select ok(
  not exists (
    select 1 from pg_class
    where oid in (
      'public.activities'::regclass,
      'public.activity_metrics'::regclass
    )
    and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every public Phase 7 table'
);

insert into phase_7_tap_results (result)
select ok(
  has_table_privilege('authenticated', 'public.activities', 'select')
  and has_table_privilege('authenticated', 'public.activity_metrics', 'select')
  and not has_table_privilege('authenticated', 'public.activities', 'insert')
  and not has_table_privilege('anon', 'public.activities', 'select'),
  'Data API grants expose only owner-filtered activity reads'
);

insert into phase_7_tap_results (result)
select ok(
  not has_table_privilege('authenticated', 'private.activity_loads', 'select')
  and not has_table_privilege('service_role', 'private.activity_loads', 'select')
  and has_function_privilege(
    'service_role',
    'public.complete_activity_rpe(uuid,uuid,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.complete_activity_rpe(uuid,uuid,jsonb)',
    'execute'
  ),
  'hidden realized load is reachable only through the narrow backend RPC'
);

insert into auth.users (id)
values
  ('80000000-0000-0000-0000-000000000008'),
  ('90000000-0000-0000-0000-000000000009');

select set_config('start23.critical_write', 'on', true);
insert into public.weekly_plans (
  id, athlete_id, week_start, timezone, state
) values (
  '81000000-0000-0000-0000-000000000008',
  '80000000-0000-0000-0000-000000000008',
  '2026-08-10',
  'UTC',
  'active'
);

insert into public.plan_revisions (
  id, plan_id, athlete_id, revision_number, state, source, phase,
  target_basis, input_fingerprint, generation_fingerprint,
  total_duration_minutes, low_intensity_percent, high_intensity_percent,
  confirmed_injuries, availability, ruleset_version
) values (
  '82000000-0000-0000-0000-000000000008',
  '81000000-0000-0000-0000-000000000008',
  '80000000-0000-0000-0000-000000000008',
  1,
  'active',
  'system_generated',
  'build',
  'prior_planned_hold',
  repeat('a', 32),
  repeat('b', 64),
  90,
  50,
  50,
  '{}',
  jsonb_build_array(
    jsonb_build_object(
      'starts_at', '2026-08-11T07:00:00+00:00',
      'ends_at', '2026-08-11T10:00:00+00:00'
    )
  ),
  'phase-3-ruleset-2'
);

insert into public.planned_workouts (
  id, revision_id, plan_id, athlete_id, template_id, template_key,
  template_version, discipline, name, description, duration_minutes,
  intensity_bucket, expected_rpe_min, expected_rpe_max, segments,
  scheduled_at, timezone, source
) values
  (
    '83000000-0000-0000-0000-000000000008',
    '82000000-0000-0000-0000-000000000008',
    '81000000-0000-0000-0000-000000000008',
    '80000000-0000-0000-0000-000000000008',
    '52000000-0000-0000-0000-000000000005',
    '50000000-0000-0000-0000-000000000005',
    2, 'run', 'Easy aerobic run', 'Easy run.', 45, 'low', 2, 4,
    jsonb_build_array(jsonb_build_object('sequence', 1)),
    '2026-08-11T08:00:00+00:00', 'UTC', 'auto_planned'
  ),
  (
    '84000000-0000-0000-0000-000000000008',
    '82000000-0000-0000-0000-000000000008',
    '81000000-0000-0000-0000-000000000008',
    '80000000-0000-0000-0000-000000000008',
    '51000000-0000-0000-0000-000000000006',
    '50000000-0000-0000-0000-000000000006',
    1, 'run', 'Tempo intervals', 'Tempo run.', 45, 'high', 7, 8,
    jsonb_build_array(jsonb_build_object('sequence', 1)),
    '2026-08-12T08:00:00+00:00', 'UTC', 'auto_planned'
  );

insert into private.planned_workout_loads (
  planned_workout_id, athlete_id, planned_tss,
  calculation_method, ruleset_version
) values
  (
    '83000000-0000-0000-0000-000000000008',
    '80000000-0000-0000-0000-000000000008',
    2.25,
    'expected_rpe_midpoint_times_duration_hours',
    'phase-3-ruleset-3'
  ),
  (
    '84000000-0000-0000-0000-000000000008',
    '80000000-0000-0000-0000-000000000008',
    3.75,
    'expected_rpe_midpoint_times_duration_hours',
    'phase-3-ruleset-2'
  );

insert into private.plan_revision_loads (
  revision_id, athlete_id, target_tss, planned_tss, ruleset_version
) values (
  '82000000-0000-0000-0000-000000000008',
  '80000000-0000-0000-0000-000000000008',
  6,
  6,
  'phase-3-ruleset-3'
);

update public.weekly_plans
set active_revision = 1
where id = '81000000-0000-0000-0000-000000000008';
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"sub":"80000000-0000-0000-0000-000000000008","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '80000000-0000-0000-0000-000000000008';
set local role authenticated;

create temporary table phase_7_activity as
select public.create_activity_summary(
  '85000000-0000-0000-0000-000000000008',
  repeat('c', 64),
  jsonb_build_object(
    'planned_workout_id', '83000000-0000-0000-0000-000000000008',
    'discipline', 'run',
    'started_at', '2026-08-11T08:00:00+00:00',
    'timezone', 'UTC',
    'duration_minutes', 45,
    'distance_meters', 7000,
    'metrics', jsonb_build_object(
      'average_heart_rate_bpm', 150,
      'max_heart_rate_bpm', 170,
      'low_intensity_minutes', 45,
      'high_intensity_minutes', 0
    )
  )
) as result;
grant select on phase_7_activity to authenticated, service_role;

insert into phase_7_tap_results (result)
select is(
  public.create_activity_summary(
    '85000000-0000-0000-0000-000000000008',
    repeat('c', 64),
    jsonb_build_object('retry_payload_is_ignored', true)
  ) ->> 'id',
  (select result ->> 'id' from phase_7_activity),
  'the same activity idempotency key and fingerprint replays the original row'
);

insert into phase_7_tap_results (result)
select throws_ok(
  $$
    select public.create_activity_summary(
      '85000000-0000-0000-0000-000000000008',
      repeat('d', 64),
      jsonb_build_object('discipline', 'run')
    )
  $$,
  '40001',
  'activity idempotency key reused',
  'an idempotency key cannot be reused for a different summary'
);

insert into phase_7_tap_results (result)
select ok(
  position('tss' in lower((select result::text from phase_7_activity))) = 0,
  'the public activity response contains no TSS key'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"90000000-0000-0000-0000-000000000009","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '90000000-0000-0000-0000-000000000009';

insert into phase_7_tap_results (result)
select is(
  (select count(*) from public.activities),
  0::bigint,
  'another athlete cannot list the owner activity'
);
insert into phase_7_tap_results (result)
select throws_ok(
  format(
    'select public.get_activity(%L::uuid)',
    (select result ->> 'id' from phase_7_activity)
  ),
  'P0002',
  'activity not found',
  'another athlete cannot read the owner activity RPC'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

insert into phase_7_tap_results (result)
select throws_ok(
  format(
    $$
      select public.complete_activity_rpe(
        '80000000-0000-0000-0000-000000000008',
        %L::uuid,
        jsonb_build_object(
          'rpe', 7,
          'qualitative_result', 'perfect_match',
          'public_message', 'Ongeldige combinatie.',
          'correction_reason', 'hidden_fatigue',
          'realized_tss', 5.25
        )
      )
    $$,
    (select result ->> 'id' from phase_7_activity)
  ),
  '23514',
  'invalid activity rpe result',
  'the persistence boundary rejects a mismatched result and correction reason'
);

insert into phase_7_tap_results (result)
select lives_ok(
  format(
    $$
      select public.complete_activity_rpe(
        '80000000-0000-0000-0000-000000000008',
        %L::uuid,
        jsonb_build_object(
          'rpe', 7,
          'qualitative_result', 'hidden_fatigue',
          'public_message', 'Deze rustige training voelde zwaarder dan verwacht.',
          'correction_reason', 'hidden_fatigue',
          'realized_tss', 5.25,
          'calculation_method', 'actual_rpe_times_duration_hours',
          'ruleset_version', 'phase-3-ruleset-3'
        )
      )
    $$,
    (select result ->> 'id' from phase_7_activity)
  ),
  'the trusted backend atomically completes RPE and creates a correction'
);

insert into phase_7_tap_results (result)
select throws_ok(
  format(
    $$
      select public.complete_activity_rpe(
        '80000000-0000-0000-0000-000000000008',
        %L::uuid,
        jsonb_build_object('rpe', 6)
      )
    $$,
    (select result ->> 'id' from phase_7_activity)
  ),
  '40001',
  'activity rpe is immutable',
  'a later RPE score cannot rewrite completed physiological history'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"80000000-0000-0000-0000-000000000008","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  '80000000-0000-0000-0000-000000000008';
set local role authenticated;

insert into phase_7_tap_results (result)
select is(
  public.get_activity(
    (select (result ->> 'id')::uuid from phase_7_activity)
  ) ->> 'qualitative_result',
  'hidden_fatigue',
  'the owner receives only the qualitative hidden-fatigue result'
);
insert into phase_7_tap_results (result)
select is(
  (select count(*) from public.change_proposals where state = 'pending'),
  1::bigint,
  'the correction remains a pending proposal'
);
insert into phase_7_tap_results (result)
select is(
  (select active_revision from public.weekly_plans),
  1,
  'RPE completion does not apply the correction automatically'
);
insert into phase_7_tap_results (result)
select is(
  (
    select count(*)
    from public.planned_workouts workout
    join public.plan_revisions revision on revision.id = workout.revision_id
    where revision.state = 'pending_approval'
      and workout.intensity_bucket = 'high'
      and workout.status = 'cancelled'
  ),
  1::bigint,
  'the typed pending revision cancels the qualifying future hard workout'
);

insert into phase_7_tap_results (result)
select lives_ok(
  $$
    select public.approve_plan_proposal(
      (select correction_proposal_id from public.activities limit 1),
      1
    )
  $$,
  'the owner can explicitly approve the typed correction revision'
);
insert into phase_7_tap_results (result)
select is(
  (select active_revision from public.weekly_plans),
  2,
  'explicit approval, not RPE submission, activates the correction'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
insert into phase_7_tap_results (result)
select is(
  (
    select realized_tss
    from public.get_plan_load_history_for_planning(
      '80000000-0000-0000-0000-000000000008',
      '2026-08-17'
    )
  ),
  5.25::numeric,
  'the planning service receives canonical realized weekly load privately'
);
insert into phase_7_tap_results (result)
select ok(
  (
    select realized_high_minutes = 0
      and realized_classified_minutes = 45
      and realized_total_minutes = 45
    from public.get_plan_load_history_for_planning(
      '80000000-0000-0000-0000-000000000008',
      '2026-08-17'
    )
  ),
  'planning receives separate classified coverage without treating unknown time as low'
);

reset role;
select set_config('request.jwt.claims', '{}', true);
select set_config('start23.critical_write', 'on', true);
delete from public.activities
where athlete_id = '80000000-0000-0000-0000-000000000008';
delete from public.weekly_plans
where athlete_id = '80000000-0000-0000-0000-000000000008';
delete from auth.users
where id in (
  '80000000-0000-0000-0000-000000000008',
  '90000000-0000-0000-0000-000000000009'
);

select plan(count(*)::integer) from phase_7_tap_results;
select result from phase_7_tap_results order by sequence;
select * from finish();

rollback;
