-- Final H-01 activation contract. Runtime execution is R6 evidence; this file
-- is also inspected by the repository-level static migration contract tests.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select ok(
  exists (
    select 1
    from pg_trigger
    where tgrelid = 'public.zone_profile_versions'::regclass
      and tgname = 'zone_profile_versions_r6_entry_current_activation'
      and tgenabled = 'O'
      and not tgisinternal
  ),
  'the historical calibration activation transition guard is enabled'
);
select ok(
  not has_function_privilege(
    'anon',
    'private.enforce_current_calibration_zone_activation()',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'private.enforce_current_calibration_zone_activation()',
    'execute'
  )
  and not has_function_privilege(
    'service_role',
    'private.enforce_current_calibration_zone_activation()',
    'execute'
  ),
  'the transition trigger function is not a directly callable API'
);

insert into auth.users(id) values
  ('c0200000-0000-0000-0000-000000000001'),
  ('c0200000-0000-0000-0000-000000000002'),
  ('c0200000-0000-0000-0000-000000000003'),
  ('c0200000-0000-0000-0000-000000000004'),
  ('c0200000-0000-0000-0000-000000000005'),
  ('c0200000-0000-0000-0000-000000000006');

insert into public.athlete_profiles (
  athlete_id, timezone, timezone_source, timezone_confirmed_at,
  onboarding_status
) values
  ('c0200000-0000-0000-0000-000000000001', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress'),
  ('c0200000-0000-0000-0000-000000000002', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress'),
  ('c0200000-0000-0000-0000-000000000003', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress'),
  ('c0200000-0000-0000-0000-000000000004', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress'),
  ('c0200000-0000-0000-0000-000000000005', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress'),
  ('c0200000-0000-0000-0000-000000000006', 'Europe/Amsterdam', 'manual', statement_timestamp(), 'in_progress');

create temporary table h01_activation_specs (
  scenario text primary key,
  athlete_id uuid not null,
  activity_id uuid not null,
  evaluation_id uuid not null,
  protocol_id text not null,
  discipline text not null,
  ruleset_version text not null,
  zone_model_version text not null,
  source_quality text not null,
  segment_id text not null,
  threshold_kind text not null,
  threshold_value numeric not null,
  metric_profiles jsonb not null
);

insert into h01_activation_specs values
  (
    'historical_run',
    'c0200000-0000-0000-0000-000000000001',
    'c0210000-0000-0000-0000-000000000001',
    'c0220000-0000-0000-0000-000000000001',
    'start23_run_threshold_30min_v1', 'run',
    'start23-calibration-ruleset-v2', 'start23-zone-model-1.0',
    'reviewed_field_threshold', 'warmup',
    'run_threshold_pace_seconds_per_km', 300,
    '[{"metric_kind":"run_threshold_pace_seconds_per_km","source_value":"300","is_primary":true,"boundary_source":"model_derived","zone_model_version":"start23-zone-model-1.0","boundaries":[{"zone_number":1,"lower_value":"385","upper_value":null},{"zone_number":2,"lower_value":"341","upper_value":"385"},{"zone_number":3,"lower_value":"316","upper_value":"341"},{"zone_number":4,"lower_value":"294","upper_value":"316"},{"zone_number":5,"lower_value":"0","upper_value":"294"}]}]'::jsonb
  ),
  (
    'historical_bike',
    'c0200000-0000-0000-0000-000000000002',
    'c0210000-0000-0000-0000-000000000002',
    'c0220000-0000-0000-0000-000000000002',
    'start23_bike_ftp_30min_v1', 'bike',
    'start23-calibration-ruleset-v2', 'start23-zone-model-1.0',
    'reviewed_field_threshold', 'warmup', 'bike_ftp_watts', 250,
    '[{"metric_kind":"bike_ftp_watts","source_value":"250","is_primary":true,"boundary_source":"model_derived","zone_model_version":"start23-zone-model-1.0","boundaries":[{"zone_number":1,"lower_value":"0","upper_value":"140"},{"zone_number":2,"lower_value":"140","upper_value":"190"},{"zone_number":3,"lower_value":"190","upper_value":"228"},{"zone_number":4,"lower_value":"228","upper_value":"265"},{"zone_number":5,"lower_value":"265","upper_value":null}]}]'::jsonb
  ),
  (
    'historical_active',
    'c0200000-0000-0000-0000-000000000003',
    'c0210000-0000-0000-0000-000000000003',
    'c0220000-0000-0000-0000-000000000003',
    'start23_run_threshold_30min_v1', 'run',
    'start23-calibration-ruleset-v2', 'start23-zone-model-1.0',
    'reviewed_field_threshold', 'warmup',
    'run_threshold_pace_seconds_per_km', 305,
    '[{"metric_kind":"run_threshold_pace_seconds_per_km","source_value":"305","is_primary":true,"boundary_source":"model_derived","zone_model_version":"start23-zone-model-1.0","boundaries":[{"zone_number":1,"lower_value":"391","upper_value":null},{"zone_number":2,"lower_value":"347","upper_value":"391"},{"zone_number":3,"lower_value":"321","upper_value":"347"},{"zone_number":4,"lower_value":"299","upper_value":"321"},{"zone_number":5,"lower_value":"0","upper_value":"299"}]}]'::jsonb
  ),
  (
    'current_run',
    'c0200000-0000-0000-0000-000000000004',
    'c0210000-0000-0000-0000-000000000004',
    'c0220000-0000-0000-0000-000000000004',
    'start23_week1_run_calibration_v1', 'run',
    'phase-13-joren-ruleset-1', 'phase-13-joren-ruleset-1',
    'submaximal_calibration_estimate', 'comfortable_20min',
    'run_lthr_bpm', 168,
    '[{"metric_kind":"run_lthr_bpm","source_value":"168","is_primary":true,"boundary_source":"model_derived","zone_model_version":"phase-13-joren-ruleset-1","boundaries":[{"zone_number":1,"lower_value":null,"upper_value":"137"},{"zone_number":2,"lower_value":"138","upper_value":"150"},{"zone_number":3,"lower_value":"151","upper_value":"160"},{"zone_number":4,"lower_value":"161","upper_value":"168"},{"zone_number":5,"lower_value":"169","upper_value":null}]}]'::jsonb
  ),
  (
    'current_bike',
    'c0200000-0000-0000-0000-000000000005',
    'c0210000-0000-0000-0000-000000000005',
    'c0220000-0000-0000-0000-000000000005',
    'start23_week1_bike_calibration_v1', 'bike',
    'phase-13-joren-ruleset-1', 'phase-13-joren-ruleset-1',
    'submaximal_calibration_estimate', 'comfortable_20min',
    'bike_threshold_heart_rate_bpm', 160,
    '[{"metric_kind":"bike_threshold_heart_rate_bpm","source_value":"160","is_primary":true,"boundary_source":"model_derived","zone_model_version":"phase-13-joren-ruleset-1","boundaries":[{"zone_number":1,"lower_value":null,"upper_value":"130"},{"zone_number":2,"lower_value":"131","upper_value":"142"},{"zone_number":3,"lower_value":"143","upper_value":"152"},{"zone_number":4,"lower_value":"153","upper_value":"160"},{"zone_number":5,"lower_value":"161","upper_value":null}]}]'::jsonb
  ),
  (
    'current_swim',
    'c0200000-0000-0000-0000-000000000006',
    'c0210000-0000-0000-0000-000000000006',
    'c0220000-0000-0000-0000-000000000006',
    'start23_swim_css_400_200_v1', 'swim',
    'phase-13-joren-ruleset-1', 'phase-13-joren-ruleset-1',
    'reviewed_field_threshold', 'tt_400m',
    'swim_css_seconds_per_100m', 110,
    '[{"metric_kind":"swim_css_seconds_per_100m","source_value":"110","is_primary":true,"boundary_source":"model_derived","zone_model_version":"phase-13-joren-ruleset-1","boundaries":[{"zone_number":1,"lower_value":"128","upper_value":null},{"zone_number":2,"lower_value":"119","upper_value":"127"},{"zone_number":3,"lower_value":"113","upper_value":"118"},{"zone_number":4,"lower_value":"108","upper_value":"112"},{"zone_number":5,"lower_value":null,"upper_value":"107"}]}]'::jsonb
  );

-- Temporarily classify the historical protocols as current only while the
-- transaction owner constructs rows that represent pre-migration state. No
-- trigger or production privilege is disabled or weakened.
update private.calibration_protocol_lifecycle
set lifecycle = 'current_selectable'
where protocol_id in (
  'start23_run_threshold_30min_v1',
  'start23_bike_ftp_30min_v1'
);

select set_config('start23.critical_write', 'on', true);
insert into public.activities(
  id, athlete_id, idempotency_key, request_fingerprint, discipline,
  started_at, timezone, duration_minutes, distance_meters, match_status
)
select
  activity_id,
  athlete_id,
  ('c0230000-0000-0000-0000-' || right(athlete_id::text, 12))::uuid,
  md5(activity_id::text) || md5(athlete_id::text),
  discipline,
  '2026-09-14T08:00:00Z'::timestamptz,
  'Europe/Amsterdam',
  case when discipline = 'swim' then 10 else 60 end,
  case when discipline = 'swim' then 400 else null end,
  'unmatched'
from h01_activation_specs;

insert into public.calibration_observations(
  athlete_id, activity_id, protocol_id, discipline, segment_id,
  performed_at, payload, fingerprint
)
select
  athlete_id,
  activity_id,
  protocol_id,
  discipline,
  segment_id,
  '2026-09-14T08:00:00Z'::timestamptz,
  jsonb_build_object(
    'activity_id', activity_id,
    'planned_workout_id', null,
    'protocol_id', protocol_id,
    'discipline', discipline,
    'segment_id', segment_id,
    'performed_at', '2026-09-14T08:00:00Z',
    'completed', true,
    'interrupted', false,
    'quality_status', 'sufficient',
    'target_rpe', 4,
    'reported_block_rpe', case
      when scenario like 'current_%' then 4 else null end,
    'average_heart_rate_bpm', case
      when scenario in ('current_run', 'current_bike') then 148 else null end,
    'elapsed_time_seconds', case
      when scenario = 'current_swim' then 440 else null end,
    'distance_meters', case
      when scenario = 'current_swim' then 400 else null end
  ),
  md5(athlete_id::text || protocol_id)
from h01_activation_specs;

insert into public.calibration_observations(
  athlete_id, activity_id, protocol_id, discipline, segment_id,
  performed_at, payload, fingerprint
)
select
  athlete_id,
  activity_id,
  protocol_id,
  discipline,
  'tt_200m',
  '2026-09-14T08:10:00Z'::timestamptz,
  jsonb_build_object(
    'activity_id', activity_id,
    'planned_workout_id', null,
    'protocol_id', protocol_id,
    'discipline', discipline,
    'segment_id', 'tt_200m',
    'performed_at', '2026-09-14T08:10:00Z',
    'completed', true,
    'interrupted', false,
    'quality_status', 'sufficient',
    'target_rpe', 9,
    'reported_block_rpe', 9,
    'elapsed_time_seconds', 220,
    'distance_meters', 200
  ),
  md5(athlete_id::text || protocol_id || ':tt_200m')
from h01_activation_specs
where scenario = 'current_swim';

insert into public.calibration_evaluations(
  id, athlete_id, activity_id, protocol_id, discipline, ruleset_version,
  status, threshold_status, zone_status, confidence, reason_codes,
  thresholds, requires_athlete_confirmation, review_status, fingerprint,
  zone_model_version, zone_profiles
)
select
  evaluation_id,
  athlete_id,
  activity_id,
  protocol_id,
  discipline,
  ruleset_version,
  'threshold_estimated',
  'threshold_estimated',
  'pending_athlete_confirmation',
  'medium',
  array['zone_profile_pending_athlete_confirmation'],
  jsonb_build_array(jsonb_build_object(
    'metric_kind', threshold_kind,
    'value', threshold_value::text
  )),
  true,
  'pending_athlete_confirmation',
  md5(evaluation_id::text) || md5(protocol_id),
  zone_model_version,
  metric_profiles
from h01_activation_specs;
select set_config('start23.critical_write', '', true);

grant select on h01_activation_specs to service_role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

create temporary table h01_activation_results as
select
  scenario,
  athlete_id,
  public.save_calculated_zone_profile(
    athlete_id,
    jsonb_build_object(
      'discipline', discipline,
      'source_method', protocol_id,
      'source_quality', source_quality,
      'metric_profiles', metric_profiles,
      'input_fingerprint', md5(protocol_id) || md5(athlete_id::text),
      'calibration_evaluation_id', evaluation_id
    )
  ) as result
from h01_activation_specs;

select is(
  (
    select count(*)
    from h01_activation_results
    where scenario in ('current_run', 'current_bike', 'current_swim')
      and result ->> 'status' = 'pending'
      and result ->> 'proposal_id' is not null
  ),
  3::bigint,
  'current run bike and swim calibration create pending calculated profiles'
);

select is(
  (
    select public.save_calculated_zone_profile(
      athlete_id,
      jsonb_build_object(
        'discipline', discipline,
        'source_method', protocol_id,
        'source_quality', source_quality,
        'metric_profiles', metric_profiles,
        'input_fingerprint', md5(protocol_id) || md5(athlete_id::text),
        'calibration_evaluation_id', evaluation_id
      )
    ) ->> 'profile_id'
    from h01_activation_specs where scenario = 'current_run'
  ),
  (
    select result ->> 'profile_id'
    from h01_activation_results where scenario = 'current_run'
  ),
  'current calculated-profile creation retries remain idempotent'
);

grant select on h01_activation_results to authenticated, service_role;
reset role;

-- Create one already-active historical artifact while its source is still
-- classified as current, then restore the final lifecycle classification.
select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000003","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000003';
set local role authenticated;
select is(
  public.approve_zone_proposal(
    (
      select (result ->> 'proposal_id')::uuid
      from h01_activation_results where scenario = 'historical_active'
    ),
    null
  ) ->> 'state',
  'applied',
  'the fixture can represent an already-active historical profile'
);
reset role;

update private.calibration_protocol_lifecycle
set lifecycle = 'historical_read_only'
where protocol_id in (
  'start23_run_threshold_30min_v1',
  'start23_bike_ftp_30min_v1'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000001","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000001';
set local role authenticated;
select throws_ok(
  $q$select public.approve_zone_proposal(
    (select (result ->> 'proposal_id')::uuid
     from h01_activation_results where scenario = 'historical_run'),
    null
  )$q$,
  '23514', 'historical calibration profile cannot be activated',
  'historical pending run profile cannot be activated through approval RPC'
);
select is(
  (
    select status from public.zone_profile_versions
    where id = (
      select (result ->> 'profile_id')::uuid
      from h01_activation_results where scenario = 'historical_run'
    )
  ),
  'pending',
  'historical pending run profile remains readable and unchanged'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000002","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000002';
set local role authenticated;
select throws_ok(
  $q$select public.approve_zone_proposal(
    (select (result ->> 'proposal_id')::uuid
     from h01_activation_results where scenario = 'historical_bike'),
    null
  )$q$,
  '23514', 'historical calibration profile cannot be activated',
  'historical pending bike profile cannot be activated through approval RPC'
);
reset role;

select is(
  (
    select count(*)
    from public.change_proposals proposal
    join h01_activation_results result
      on (result.result ->> 'proposal_id')::uuid = proposal.id
    where result.scenario in ('historical_run', 'historical_bike')
      and proposal.state = 'pending'
  ),
  2::bigint,
  'rejected historical approvals leave pending history unchanged'
);

select set_config('start23.critical_write', 'on', true);
select throws_ok(
  $q$update public.zone_profile_versions
    set status = 'active', effective_from = statement_timestamp(),
        review_status = 'confirmed_by_athlete',
        reviewed_at = statement_timestamp()
    where id = (
      select (result ->> 'profile_id')::uuid
      from h01_activation_results where scenario = 'historical_run'
    )$q$,
  '23514', 'historical calibration profile cannot be activated',
  'direct historical pending profile transition to active is rejected'
);
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000003","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000003';
set local role authenticated;
select is(
  (
    select status from public.zone_profile_versions
    where id = (
      select (result ->> 'profile_id')::uuid
      from h01_activation_results where scenario = 'historical_active'
    )
  ),
  'active',
  'already-active historical profile remains readable and is not rewritten'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000004","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000004';
set local role authenticated;
select throws_ok(
  $q$select public.approve_zone_proposal(
    (select (result ->> 'proposal_id')::uuid
     from h01_activation_results where scenario = 'current_run'),
    'deadbeef-dead-beef-dead-beefdeadbeef'
  )$q$,
  'PT409', 'zone proposal base is stale',
  'stale current calibration approval still fails'
);
select is(
  public.approve_zone_proposal(
    (
      select (result ->> 'proposal_id')::uuid
      from h01_activation_results where scenario = 'current_run'
    ),
    null
  ) ->> 'state',
  'applied',
  'current run pending calibration profile can still be approved'
);
select throws_ok(
  $q$select public.approve_zone_proposal(
    (select (result ->> 'proposal_id')::uuid
     from h01_activation_results where scenario = 'current_run'),
    null
  )$q$,
  'P0002', 'pending zone proposal not found',
  'replayed current approval retains the existing terminal behavior'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000005","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000005';
set local role authenticated;
select is(
  public.approve_zone_proposal(
    (
      select (result ->> 'proposal_id')::uuid
      from h01_activation_results where scenario = 'current_bike'
    ),
    null
  ) ->> 'state',
  'applied',
  'current bike pending calibration profile can still be approved'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"c0200000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'c0200000-0000-0000-0000-000000000006';
set local role authenticated;
select is(
  public.approve_zone_proposal(
    (
      select (result ->> 'proposal_id')::uuid
      from h01_activation_results where scenario = 'current_swim'
    ),
    null
  ) ->> 'state',
  'applied',
  'current swim CSS pending calibration profile can still be approved'
);
reset role;

select is(
  (
    select count(*)
    from public.zone_profile_versions profile
    join h01_activation_results result
      on (result.result ->> 'profile_id')::uuid = profile.id
    where result.scenario in ('current_run', 'current_bike', 'current_swim')
      and profile.status = 'active'
      and profile.calibration_evaluation_id is not null
  ),
  3::bigint,
  'all current calibration activations retain their evaluation provenance'
);

select * from finish();
rollback;
