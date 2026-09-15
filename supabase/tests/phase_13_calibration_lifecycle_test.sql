-- H-01 final-state database contract. This is pre-R6 proof only: historical
-- records remain readable, while every new current-state boundary fails closed.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table h01_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on h01_tap_results to authenticated, service_role;
grant usage, select on sequence h01_tap_results_sequence_seq
to authenticated, service_role;

insert into h01_tap_results (result) select has_table(
  'private', 'calibration_protocol_lifecycle',
  'the database has one authoritative calibration lifecycle registry'
);
insert into h01_tap_results (result) select results_eq(
  $q$select protocol_id, discipline, protocol_type, lifecycle
    from private.calibration_protocol_lifecycle order by protocol_id$q$,
  $q$values
    ('start23_bike_fthr_20min_v1', 'bike', 'field_test', 'historical_read_only'),
    ('start23_bike_ftp_30min_v1', 'bike', 'field_test', 'historical_read_only'),
    ('start23_run_threshold_30min_v1', 'run', 'field_test', 'historical_read_only'),
    ('start23_swim_css_400_200_v1', 'swim', 'field_test', 'current_selectable'),
    ('start23_week1_bike_calibration_v1', 'bike', 'submaximal_calibration', 'current_selectable'),
    ('start23_week1_run_calibration_v1', 'run', 'submaximal_calibration', 'current_selectable'),
    ('start23_week1_swim_calibration_v1', 'swim', 'submaximal_calibration', 'current_selectable')$q$,
  'current/selectable and historical/read-only classifications are exact'
);
insert into h01_tap_results (result) select ok(
  not has_table_privilege(
    'anon', 'private.calibration_protocol_lifecycle', 'select'
  )
  and not has_table_privilege(
    'authenticated', 'private.calibration_protocol_lifecycle', 'select'
  )
  and not has_table_privilege(
    'service_role', 'private.calibration_protocol_lifecycle', 'select'
  ),
  'the lifecycle registry is not a client-mutable or enumerable API'
);
insert into h01_tap_results (result) select ok(
  has_function_privilege(
    'authenticated',
    'private.is_current_calibration_protocol(text,text,text)',
    'execute'
  )
  and not has_function_privilege(
    'anon',
    'private.is_current_calibration_protocol(text,text,text)',
    'execute'
  )
  and not has_function_privilege(
    'service_role',
    'private.is_current_calibration_protocol(text,text,text)',
    'execute'
  ),
  'only authenticated scheduling may call the read-only lifecycle predicate'
);
insert into h01_tap_results (result) select ok(
  private.is_current_calibration_protocol(
    'start23_week1_swim_calibration_v1', 'swim', 'submaximal_calibration'
  )
  and private.is_current_calibration_protocol(
    'start23_week1_bike_calibration_v1', 'bike', 'submaximal_calibration'
  )
  and private.is_current_calibration_protocol(
    'start23_week1_run_calibration_v1', 'run', 'submaximal_calibration'
  )
  and private.is_current_calibration_protocol(
    'start23_swim_css_400_200_v1', 'swim', 'field_test'
  )
  and not private.is_current_calibration_protocol(
    'start23_run_threshold_30min_v1', 'run', 'field_test'
  )
  and not private.is_current_calibration_protocol(
    'start23_bike_ftp_30min_v1', 'bike', 'field_test'
  )
  and not private.is_current_calibration_protocol(
    'start23_bike_fthr_20min_v1', 'bike', 'field_test'
  ),
  'all database write boundaries consume the exact lifecycle classification'
);

insert into h01_tap_results (result) select ok(
  exists (
    select 1 from pg_trigger
    where tgrelid = 'public.discipline_zone_setups'::regclass
      and tgname = 'discipline_zone_setups_r6_entry_current_protocol'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.calibration_observations'::regclass
      and tgname = 'calibration_observations_r6_entry_current_protocol'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.calibration_evaluations'::regclass
      and tgname = 'calibration_evaluations_r6_entry_current_protocol'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.zone_profile_versions'::regclass
      and tgname = 'zone_profile_versions_r6_entry_current_calibration'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.discipline_test_assignments'::regclass
      and tgname = 'discipline_test_assignments_r6_entry_current_protocol'
      and tgenabled = 'O' and not tgisinternal
  ),
  'setup, observation, evaluation, zone-state, and scheduling guards are enabled'
);
insert into h01_tap_results (result) select ok(
  not has_function_privilege(
    'authenticated', 'public.save_integrated_test_assignment(jsonb)', 'execute'
  )
  and has_function_privilege(
    'authenticated', 'public.create_validation_test_proposal(jsonb)', 'execute'
  ),
  'deprecated integrated scheduling is closed while guarded standalone scheduling remains'
);

insert into auth.users(id)
values ('c0100000-0000-0000-0000-000000000001');

insert into public.athlete_profiles (
  athlete_id, timezone, timezone_source, timezone_confirmed_at,
  onboarding_status
) values (
  'c0100000-0000-0000-0000-000000000001', 'Europe/Amsterdam',
  'manual', statement_timestamp(), 'in_progress'
);

select set_config('start23.critical_write', 'on', true);
insert into public.activities(
  id, athlete_id, idempotency_key, request_fingerprint, discipline,
  started_at, timezone, duration_minutes, distance_meters, match_status
) values
  (
    'c0110000-0000-0000-0000-000000000001',
    'c0100000-0000-0000-0000-000000000001',
    'c0120000-0000-0000-0000-000000000001', repeat('1', 64), 'run',
    '2026-09-14T08:00:00Z', 'Europe/Amsterdam', 60, null, 'unmatched'
  ),
  (
    'c0110000-0000-0000-0000-000000000002',
    'c0100000-0000-0000-0000-000000000001',
    'c0120000-0000-0000-0000-000000000002', repeat('2', 64), 'bike',
    '2026-09-14T09:00:00Z', 'Europe/Amsterdam', 75, null, 'unmatched'
  ),
  (
    'c0110000-0000-0000-0000-000000000003',
    'c0100000-0000-0000-0000-000000000001',
    'c0120000-0000-0000-0000-000000000003', repeat('3', 64), 'swim',
    '2026-09-14T10:00:00Z', 'Europe/Amsterdam', null, 300, 'unmatched'
  );
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"sub":"c0100000-0000-0000-0000-000000000001","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0100000-0000-0000-0000-000000000001';
set local role authenticated;

insert into h01_tap_results (result) select lives_ok(
  $q$select public.save_discipline_zone_setup(jsonb_build_object(
    'discipline', 'run', 'setup_route', 'calibration_week',
    'guidance_mode', 'heart_rate', 'setup_status', 'calibration_pending',
    'protocol_id', 'start23_week1_run_calibration_v1',
    'pool_length_meters', null, 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'source', 'week1_calibration',
    'validation_status', 'not_assessed', 'confidence', 'not_assessed',
    'known_thresholds', '[]'::jsonb, 'known_zone_profiles', '[]'::jsonb
  ))$q$,
  'current run submaximal setup succeeds'
);
insert into h01_tap_results (result) select lives_ok(
  $q$select public.save_discipline_zone_setup(jsonb_build_object(
    'discipline', 'bike', 'setup_route', 'calibration_week',
    'guidance_mode', 'combined', 'setup_status', 'calibration_pending',
    'protocol_id', 'start23_week1_bike_calibration_v1',
    'pool_length_meters', null, 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'source', 'week1_calibration',
    'validation_status', 'not_assessed', 'confidence', 'not_assessed',
    'known_thresholds', '[]'::jsonb, 'known_zone_profiles', '[]'::jsonb
  ))$q$,
  'current bike submaximal setup succeeds'
);
insert into h01_tap_results (result) select lives_ok(
  $q$select public.save_discipline_zone_setup(jsonb_build_object(
    'discipline', 'swim', 'setup_route', 'calibration_week',
    'guidance_mode', 'pace', 'setup_status', 'calibration_pending',
    'protocol_id', 'start23_week1_swim_calibration_v1',
    'pool_length_meters', 25, 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'source', 'week1_calibration',
    'validation_status', 'not_assessed', 'confidence', 'not_assessed',
    'known_thresholds', '[]'::jsonb, 'known_zone_profiles', '[]'::jsonb
  ))$q$,
  'current swim submaximal setup succeeds'
);

create temporary table h01_current_observations(result jsonb);
insert into h01_current_observations
select public.save_calibration_observation(
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000001',
    'planned_workout_id', null,
    'protocol_id', 'start23_week1_run_calibration_v1',
    'discipline', 'run', 'segment_id', 'warmup',
    'performed_at', '2026-09-14T08:00:00Z', 'completed', true,
    'interrupted', false, 'quality_status', 'sufficient', 'target_rpe', 3,
    'duration_seconds', 600
  ), repeat('4', 64)
)
union all
select public.save_calibration_observation(
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000002',
    'planned_workout_id', null,
    'protocol_id', 'start23_week1_bike_calibration_v1',
    'discipline', 'bike', 'segment_id', 'warmup',
    'performed_at', '2026-09-14T09:00:00Z', 'completed', true,
    'interrupted', false, 'quality_status', 'sufficient', 'target_rpe', 3,
    'duration_seconds', 900
  ), repeat('5', 64)
)
union all
select public.save_calibration_observation(
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000003',
    'planned_workout_id', null,
    'protocol_id', 'start23_week1_swim_calibration_v1',
    'discipline', 'swim', 'segment_id', 'warmup',
    'performed_at', '2026-09-14T10:00:00Z', 'completed', true,
    'interrupted', false, 'quality_status', 'sufficient', 'target_rpe', 3,
    'distance_meters', 300, 'elapsed_time_seconds', 600,
    'pool_length_meters', 25
  ), repeat('6', 64)
);
insert into h01_tap_results (result) select is(
  (select count(*) from h01_current_observations), 3::bigint,
  'current swim, bike, and run observations are newly persistable'
);

insert into h01_tap_results (result) select throws_ok(
  $q$select public.save_calibration_observation(jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000001',
    'planned_workout_id', null,
    'protocol_id', 'start23_run_threshold_30min_v1',
    'discipline', 'run', 'segment_id', 'warmup',
    'performed_at', '2026-09-14T08:00:00Z', 'completed', true,
    'interrupted', false, 'quality_status', 'sufficient', 'target_rpe', 3,
    'duration_seconds', 900
  ), repeat('7', 64))$q$,
  '23514', 'historical calibration protocol is read-only',
  'the authenticated observation API rejects a new historical observation'
);
insert into h01_tap_results (result) select throws_ok(
  $q$select public.save_discipline_zone_setup(jsonb_build_object(
    'discipline', 'run', 'setup_route', 'field_test',
    'guidance_mode', 'heart_rate', 'setup_status', 'test_pending',
    'protocol_id', 'start23_run_threshold_30min_v1',
    'pool_length_meters', null, 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'source', 'field_test',
    'validation_status', 'not_assessed', 'confidence', 'not_assessed',
    'known_thresholds', '[]'::jsonb, 'known_zone_profiles', '[]'::jsonb
  ))$q$,
  '23514', 'historical calibration protocol is read-only',
  'authenticated setup cannot configure a historical field test'
);
insert into h01_tap_results (result) select throws_ok(
  $q$select public.create_validation_test_proposal(jsonb_build_object(
    'discipline', 'run',
    'protocol_id', 'start23_run_threshold_30min_v1',
    'scheduling_mode', 'standalone',
    'scheduled_date', current_date + 1
  ))$q$,
  '23514', 'invalid validation test assignment',
  'historical field tests cannot be newly scheduled'
);

select set_config('start23.critical_write', 'on', true);
insert into h01_tap_results (result) select throws_ok(
  $q$insert into public.calibration_observations(
    athlete_id, activity_id, protocol_id, discipline, segment_id,
    performed_at, payload, fingerprint
  ) values (
    'c0100000-0000-0000-0000-000000000001',
    'c0110000-0000-0000-0000-000000000002',
    'start23_bike_ftp_30min_v1', 'bike', 'warmup',
    '2026-09-14T09:00:00Z',
    jsonb_build_object(
      'activity_id', 'c0110000-0000-0000-0000-000000000002',
      'protocol_id', 'start23_bike_ftp_30min_v1',
      'discipline', 'bike', 'segment_id', 'warmup',
      'performed_at', '2026-09-14T09:00:00Z', 'completed', true,
      'interrupted', false, 'quality_status', 'sufficient', 'target_rpe', 3
    ), repeat('8', 32)
  )$q$,
  '23514', 'historical calibration protocol is read-only',
  'even an authenticated direct insert with the legacy guard flag cannot persist history'
);
reset role;

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
create temporary table h01_current_evaluations(result jsonb);
insert into h01_current_evaluations
select public.save_calibration_evaluation(
  'c0100000-0000-0000-0000-000000000001',
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000001',
    'protocol_id', 'start23_week1_run_calibration_v1', 'discipline', 'run',
    'ruleset_version', 'phase-13-joren-ruleset-1',
    'status', 'insufficient_data', 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'confidence', 'not_assessed',
    'reason_codes', jsonb_build_array('required_segment_missing'),
    'thresholds', '[]'::jsonb, 'requires_athlete_confirmation', false,
    'review_status', 'not_applicable'
  ), repeat('9', 64)
)
union all
select public.save_calibration_evaluation(
  'c0100000-0000-0000-0000-000000000001',
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000002',
    'protocol_id', 'start23_week1_bike_calibration_v1', 'discipline', 'bike',
    'ruleset_version', 'phase-13-joren-ruleset-1',
    'status', 'insufficient_data', 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'confidence', 'not_assessed',
    'reason_codes', jsonb_build_array('required_segment_missing'),
    'thresholds', '[]'::jsonb, 'requires_athlete_confirmation', false,
    'review_status', 'not_applicable'
  ), repeat('a', 64)
)
union all
select public.save_calibration_evaluation(
  'c0100000-0000-0000-0000-000000000001',
  jsonb_build_object(
    'activity_id', 'c0110000-0000-0000-0000-000000000003',
    'protocol_id', 'start23_week1_swim_calibration_v1', 'discipline', 'swim',
    'ruleset_version', 'phase-13-joren-ruleset-1',
    'status', 'insufficient_data', 'threshold_status', 'unknown',
    'zone_status', 'unknown', 'confidence', 'not_assessed',
    'reason_codes', jsonb_build_array('required_segment_missing'),
    'thresholds', '[]'::jsonb, 'requires_athlete_confirmation', false,
    'review_status', 'not_applicable'
  ), repeat('b', 64)
);
insert into h01_tap_results (result) select is(
  (select count(*) from h01_current_evaluations), 3::bigint,
  'current swim, bike, and run observations are newly evaluable'
);
insert into h01_tap_results (result) select throws_ok(
  $q$select public.save_calibration_evaluation(
    'c0100000-0000-0000-0000-000000000001',
    jsonb_build_object(
      'activity_id', 'c0110000-0000-0000-0000-000000000001',
      'protocol_id', 'start23_run_threshold_30min_v1', 'discipline', 'run',
      'ruleset_version', 'start23-calibration-ruleset-v2',
      'status', 'insufficient_data', 'threshold_status', 'unknown',
      'zone_status', 'unknown', 'confidence', 'not_assessed',
      'reason_codes', jsonb_build_array('required_segment_missing'),
      'thresholds', '[]'::jsonb, 'requires_athlete_confirmation', false,
      'review_status', 'not_applicable',
      'zone_model_version', null, 'zone_profiles', '[]'::jsonb
    ), repeat('c', 64)
  )$q$,
  '23514', 'historical calibration protocol is read-only',
  'the service evaluation persistence RPC rejects historical protocols'
);
insert into h01_tap_results (result) select throws_ok(
  $q$select public.save_calibration_evaluation(
    'c0100000-0000-0000-0000-000000000001',
    jsonb_build_object(
      'activity_id', 'c0110000-0000-0000-0000-000000000001',
      'protocol_id', 'start23_swim_css_400_200_v1', 'discipline', 'swim',
      'ruleset_version', 'start23-calibration-ruleset-v2',
      'status', 'insufficient_data', 'threshold_status', 'unknown',
      'zone_status', 'unknown', 'confidence', 'not_assessed',
      'reason_codes', jsonb_build_array('required_segment_missing'),
      'thresholds', '[]'::jsonb, 'requires_athlete_confirmation', false,
      'review_status', 'not_applicable',
      'zone_model_version', null, 'zone_profiles', '[]'::jsonb
    ), repeat('d', 64)
  )$q$,
  '23514', 'current evaluation requires a persisted protocol observation',
  'even a current evaluation requires a matching existing observation'
);
reset role;

insert into h01_tap_results (result) select is(
  (
    select count(*) from public.change_proposals
    where athlete_id = 'c0100000-0000-0000-0000-000000000001'
  ),
  0::bigint,
  'no historical protocol can generate a new pending proposal'
);
insert into h01_tap_results (result) select ok(
  has_table_privilege(
    'authenticated', 'public.calibration_observations', 'select'
  )
  and has_table_privilege(
    'authenticated', 'public.calibration_evaluations', 'select'
  ),
  'the fix preserves authenticated owner reads of already-stored history'
);

insert into h01_tap_results (result)
select * from finish();
select result from h01_tap_results order by sequence;
rollback;
