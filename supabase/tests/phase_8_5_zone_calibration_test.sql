begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table(
  'public', 'discipline_zone_setups', 'discipline setup table exists'
);
select has_table(
  'public', 'calibration_observations', 'calibration observation table exists'
);
select has_table(
  'public', 'calibration_evaluations', 'calibration evaluation table exists'
);

select ok(
  not exists (
    select 1 from pg_class
    where oid in (
      'public.discipline_zone_setups'::regclass,
      'public.calibration_observations'::regclass,
      'public.calibration_evaluations'::regclass
    ) and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every Phase 8.5 public table'
);

select ok(
  not has_table_privilege('anon', 'public.discipline_zone_setups', 'select')
  and not has_table_privilege('anon', 'public.calibration_observations', 'select')
  and not has_table_privilege('anon', 'public.calibration_evaluations', 'select')
  and has_table_privilege(
    'authenticated', 'public.discipline_zone_setups', 'select'
  )
  and has_table_privilege(
    'authenticated', 'public.calibration_observations', 'select'
  )
  and has_table_privilege(
    'authenticated', 'public.calibration_evaluations', 'select'
  ),
  'explicit grants expose owner reads only to authenticated athletes'
);

select ok(
  not (
    select prosecdef from pg_proc
    where oid = 'public.save_discipline_zone_setup(jsonb)'::regprocedure
  )
  and not (
    select prosecdef from pg_proc
    where oid = 'public.save_calibration_observation(jsonb,text)'::regprocedure
  )
  and (
    select prosecdef from pg_proc
    where oid = 'public.save_calibration_evaluation(uuid,jsonb,text)'::regprocedure
  ),
  'athlete RPCs are invoker functions and generated evaluation is service-only'
);

select ok(
  has_function_privilege(
    'authenticated', 'public.save_discipline_zone_setup(jsonb)', 'execute'
  )
  and has_function_privilege(
    'authenticated', 'public.save_calibration_observation(jsonb,text)', 'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.save_calibration_evaluation(uuid,jsonb,text)',
    'execute'
  )
  and has_function_privilege(
    'service_role',
    'public.save_calibration_evaluation(uuid,jsonb,text)',
    'execute'
  ),
  'athlete and backend function privileges are separated'
);

insert into auth.users (id)
values
  ('a0000000-0000-0000-0000-000000000085'),
  ('b0000000-0000-0000-0000-000000000085');

insert into public.athlete_profiles (athlete_id, timezone, onboarding_status)
values
  ('a0000000-0000-0000-0000-000000000085', 'Europe/Amsterdam', 'in_progress'),
  ('b0000000-0000-0000-0000-000000000085', 'Europe/Amsterdam', 'in_progress');

select set_config('start23.critical_write', 'on', true);
insert into public.activities (
  id,
  athlete_id,
  idempotency_key,
  request_fingerprint,
  discipline,
  started_at,
  timezone,
  duration_minutes,
  match_status
) values (
  'aa000000-0000-0000-0000-000000000085',
  'a0000000-0000-0000-0000-000000000085',
  'aa100000-0000-0000-0000-000000000085',
  repeat('a', 64),
  'run',
  '2026-08-13T10:00:00Z',
  'Europe/Amsterdam',
  50,
  'unmatched'
);
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000085","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000085';
set local role authenticated;

select is(
  public.save_discipline_zone_setup(
    jsonb_build_object(
      'discipline', 'run',
      'setup_route', 'rpe_only',
      'guidance_mode', 'rpe_only',
      'setup_status', 'configured',
      'protocol_id', null,
      'pool_length_meters', null,
      'threshold_status', 'unknown',
      'zone_status', 'unknown',
      'source', 'none',
      'validation_status', 'not_assessed',
      'confidence', 'not_assessed',
      'known_thresholds', '[]'::jsonb,
      'known_zone_profiles', '[]'::jsonb
    )
  ) ->> 'setup_route',
  'rpe_only',
  'an explicitly empty RPE-only setup is persisted'
);

select throws_ok(
  $$
    insert into public.discipline_zone_setups (
      athlete_id,
      discipline,
      setup_route,
      guidance_mode,
      setup_status,
      threshold_status,
      zone_status,
      source,
      validation_status,
      confidence
    ) values (
      'a0000000-0000-0000-0000-000000000085',
      'bike',
      'rpe_only',
      'rpe_only',
      'configured',
      'unknown',
      'unknown',
      'none',
      'not_assessed',
      'not_assessed'
    )
  $$,
  '42501',
  'critical object writes require a Start23 RPC',
  'direct discipline setup writes cannot bypass the lifecycle RPC'
);

create temporary table phase_8_5_observation as
select public.save_calibration_observation(
  jsonb_build_object(
    'activity_id', 'aa000000-0000-0000-0000-000000000085',
    'planned_workout_id', null,
    'protocol_id', 'start23_run_threshold_30min_v1',
    'discipline', 'run',
    'segment_id', 'warmup',
    'performed_at', '2026-08-13T10:00:00Z',
    'completed', true,
    'interrupted', false,
    'quality_status', 'sufficient',
    'target_rpe', 3,
    'duration_seconds', 900,
    'reported_block_rpe', null,
    'reported_session_rpe', null,
    'steady_execution', null,
    'average_heart_rate_bpm', null,
    'ending_heart_rate_bpm', null,
    'average_heart_rate_last_20min_bpm', null,
    'average_power_watts', null,
    'average_power_last_20min_watts', null,
    'average_pace_seconds_per_km', null,
    'elapsed_time_seconds', null,
    'pool_length_meters', null,
    'stroke', null,
    'equipment', null,
    'rest_time_seconds', null,
    'data_completeness', null,
    'stable_segment', null,
    'power_source_calibrated', null,
    'repetitions', '[]'::jsonb
  ),
  repeat('b', 64)
) as result;
grant select on phase_8_5_observation to authenticated, service_role;

select is(
  public.save_calibration_observation(
    (
      select payload from public.calibration_observations
      where id = (
        select (result ->> 'id')::uuid from phase_8_5_observation
      )
    ),
    repeat('b', 64)
  ) ->> 'id',
  (select result ->> 'id' from phase_8_5_observation),
  'identical observation retries return the immutable original'
);

select throws_ok(
  $$
    select public.save_calibration_observation(
      (
        select payload || jsonb_build_object('duration_seconds', 800)
        from public.calibration_observations
        where id = (
          select (result ->> 'id')::uuid from phase_8_5_observation
        )
      ),
      repeat('c', 64)
    )
  $$,
  '40001',
  'calibration observation is immutable',
  'a conflicting retry cannot rewrite a segment observation'
);

select is(
  (select count(*)::integer from public.calibration_observations),
  1,
  'the owner can read exactly the persisted observation'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-000000000085","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'b0000000-0000-0000-0000-000000000085';
set local role authenticated;

select is(
  (select count(*)::integer from public.calibration_observations),
  0,
  'a second athlete cannot read the first athlete observation'
);
select is(
  (select count(*)::integer from public.discipline_zone_setups),
  0,
  'a second athlete cannot read the first athlete setup'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

create temporary table phase_8_5_evaluation as
select public.save_calibration_evaluation(
  'a0000000-0000-0000-0000-000000000085',
  jsonb_build_object(
    'activity_id', 'aa000000-0000-0000-0000-000000000085',
    'protocol_id', 'start23_run_threshold_30min_v1',
    'discipline', 'run',
    'ruleset_version', 'start23-calibration-ruleset-v1',
    'status', 'threshold_estimated',
    'threshold_status', 'threshold_estimated',
    'zone_status', 'pending_protocol',
    'confidence', 'medium',
    'reason_codes', jsonb_build_array('zone_model_not_approved'),
    'thresholds', jsonb_build_array(
      jsonb_build_object(
        'metric_kind', 'run_threshold_pace_seconds_per_km',
        'value', '290'
      )
    ),
    'requires_athlete_confirmation', true,
    'review_status', 'pending_athlete_confirmation'
  ),
  repeat('d', 64)
) as result;
grant select on phase_8_5_evaluation to authenticated, service_role;

select is(
  public.save_calibration_evaluation(
    'a0000000-0000-0000-0000-000000000085',
    jsonb_build_object(
      'activity_id', 'aa000000-0000-0000-0000-000000000085',
      'protocol_id', 'start23_run_threshold_30min_v1',
      'discipline', 'run',
      'ruleset_version', 'start23-calibration-ruleset-v1',
      'status', 'threshold_estimated',
      'threshold_status', 'threshold_estimated',
      'zone_status', 'pending_protocol',
      'confidence', 'medium',
      'reason_codes', jsonb_build_array('zone_model_not_approved'),
      'thresholds', jsonb_build_array(
        jsonb_build_object(
          'metric_kind', 'run_threshold_pace_seconds_per_km',
          'value', '290'
        )
      ),
      'requires_athlete_confirmation', true,
      'review_status', 'pending_athlete_confirmation'
    ),
    repeat('d', 64)
  ) ->> 'id',
  (select result ->> 'id' from phase_8_5_evaluation),
  'deterministic evaluation persistence is retry-idempotent'
);

select throws_ok(
  $$
    update public.calibration_evaluations
    set status = 'insufficient_data'
    where id = (
      select (result ->> 'id')::uuid from phase_8_5_evaluation
    )
  $$,
  '42501',
  'calibration records are immutable',
  'persisted evaluation results cannot be rewritten'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000085","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000085';
set local role authenticated;

select is(
  (select count(*)::integer from public.calibration_evaluations),
  1,
  'the athlete can read the pending server-generated evaluation'
);
select ok(
  not exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name in (
        'discipline_zone_setups',
        'calibration_observations',
        'calibration_evaluations'
      )
      and lower(column_name) like '%tss%'
  ),
  'Phase 8.5 public tables contain no TSS columns'
);

reset role;
select * from finish();
rollback;
