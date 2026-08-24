begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table(
  'public',
  'calibration_threshold_decisions',
  'threshold decisions are persisted separately from zone decisions'
);
select has_column(
  'public', 'zone_profile_versions', 'metric_profiles',
  'calculated multi-metric ranges are stored on the immutable zone version'
);
select has_column(
  'public', 'zone_profile_versions', 'evidence_version',
  'calculated zone evidence provenance is stored'
);
select has_column(
  'public', 'calibration_evaluations', 'zone_profiles',
  'field-test evaluations persist their deterministic candidates'
);

select ok(
  (
    select relrowsecurity and relforcerowsecurity
    from pg_class
    where oid = 'public.calibration_threshold_decisions'::regclass
  ),
  'threshold decisions have enabled and forced RLS'
);
select ok(
  not has_table_privilege(
    'anon', 'public.calibration_threshold_decisions', 'select'
  )
  and has_table_privilege(
    'authenticated', 'public.calibration_threshold_decisions', 'select'
  )
  and not has_table_privilege(
    'authenticated', 'public.calibration_threshold_decisions', 'insert'
  ),
  'threshold decisions expose owner reads but no direct athlete writes'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.save_calculated_zone_profile(uuid,jsonb)',
    'execute'
  )
  and has_function_privilege(
    'service_role',
    'public.save_calculated_zone_profile(uuid,jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.reject_calibration_threshold(uuid,uuid)',
    'execute'
  ),
  'calculated profile and threshold-decision writes remain backend-only'
);

insert into auth.users (id)
values
  ('a0000000-0000-0000-0000-000000000105'),
  ('b0000000-0000-0000-0000-000000000105');

insert into public.athlete_profiles (athlete_id, timezone, onboarding_status)
values
  ('a0000000-0000-0000-0000-000000000105', 'Europe/Amsterdam', 'in_progress'),
  ('b0000000-0000-0000-0000-000000000105', 'Europe/Amsterdam', 'in_progress');

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
  'aa000000-0000-0000-0000-000000000105',
  'a0000000-0000-0000-0000-000000000105',
  'aa100000-0000-0000-0000-000000000105',
  repeat('a', 64),
  'run',
  '2026-08-24T10:00:00Z',
  'Europe/Amsterdam',
  50,
  'unmatched'
);
select set_config('start23.critical_write', '', true);

create temporary table zone_model_fixture as
select jsonb_build_array(
  jsonb_build_object(
    'metric_kind', 'run_threshold_pace_seconds_per_km',
    'source_value', '300',
    'is_primary', true,
    'boundary_source', 'model_derived',
    'zone_model_version', 'start23-zone-model-1.0',
    'boundaries', jsonb_build_array(
      jsonb_build_object(
        'zone_number', 1, 'lower_value', '385', 'upper_value', null
      ),
      jsonb_build_object(
        'zone_number', 2, 'lower_value', '341', 'upper_value', '385'
      ),
      jsonb_build_object(
        'zone_number', 3, 'lower_value', '316', 'upper_value', '341'
      ),
      jsonb_build_object(
        'zone_number', 4, 'lower_value', '294', 'upper_value', '316'
      ),
      jsonb_build_object(
        'zone_number', 5, 'lower_value', '0', 'upper_value', '294'
      )
    )
  )
) as metric_profiles;
grant select on zone_model_fixture to service_role;

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

create temporary table known_zone_result as
select public.save_calculated_zone_profile(
  'a0000000-0000-0000-0000-000000000105',
  jsonb_build_object(
    'discipline', 'run',
    'source_method', 'athlete_entered',
    'source_quality', 'athlete_entered',
    'metric_profiles', (select metric_profiles from zone_model_fixture),
    'input_fingerprint', repeat('b', 64),
    'calibration_evaluation_id', null
  )
) as result;
grant select on known_zone_result to authenticated, service_role;

reset role;
select is(
  (select result ->> 'status' from known_zone_result),
  'pending',
  'known thresholds produce a pending calculated zone version'
);
select is(
  (
    select count(*)::integer
    from public.zone_profile_versions
    where athlete_id = 'a0000000-0000-0000-0000-000000000105'
      and status = 'active'
  ),
  0,
  'a calculated version is never auto-activated, including the first version'
);
select is(
  (
    select base_zone_profile_id
    from public.change_proposals
    where id = (select (result ->> 'proposal_id')::uuid from known_zone_result)
  ),
  null,
  'the first calculated proposal records an explicit null base version'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000105","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000105';
set local role authenticated;

select is(
  public.approve_zone_proposal(
    (select (result ->> 'proposal_id')::uuid from known_zone_result),
    null
  ) ->> 'state',
  'applied',
  'explicit athlete confirmation activates the first calculated version'
);

reset role;
select is(
  (
    select review_status
    from public.zone_profile_versions
    where id = (select (result ->> 'profile_id')::uuid from known_zone_result)
  ),
  'confirmed_by_athlete',
  'activation records athlete review separately from calculation provenance'
);

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

create temporary table field_evaluation as
select public.save_calibration_evaluation(
  'a0000000-0000-0000-0000-000000000105',
  jsonb_build_object(
    'activity_id', 'aa000000-0000-0000-0000-000000000105',
    'protocol_id', 'start23_run_threshold_30min_v1',
    'discipline', 'run',
    'ruleset_version', 'start23-calibration-ruleset-v2',
    'status', 'threshold_estimated',
    'threshold_status', 'threshold_estimated',
    'zone_status', 'pending_athlete_confirmation',
    'confidence', 'medium',
    'reason_codes', jsonb_build_array(
      'zone_profile_pending_athlete_confirmation'
    ),
    'thresholds', jsonb_build_array(
      jsonb_build_object(
        'metric_kind', 'run_threshold_pace_seconds_per_km', 'value', '300'
      )
    ),
    'zone_model_version', 'start23-zone-model-1.0',
    'zone_profiles', (select metric_profiles from zone_model_fixture),
    'requires_athlete_confirmation', true,
    'review_status', 'pending_athlete_confirmation'
  ),
  repeat('c', 64)
) as result;
grant select on field_evaluation to authenticated, service_role;

create temporary table threshold_acceptance as
select public.save_calculated_zone_profile(
  'a0000000-0000-0000-0000-000000000105',
  jsonb_build_object(
    'discipline', 'run',
    'source_method', 'start23_run_threshold_30min_v1',
    'source_quality', 'reviewed_field_threshold',
    'metric_profiles', (select metric_profiles from zone_model_fixture),
    'input_fingerprint', repeat('d', 64),
    'calibration_evaluation_id',
      (select result ->> 'id' from field_evaluation)
  )
) as result;
grant select on threshold_acceptance to authenticated, service_role;

select is(
  (select result ->> 'state' from threshold_acceptance),
  'accepted',
  'threshold confirmation is persisted as its own decision'
);

reset role;
select is(
  (
    select count(*)::integer
    from public.zone_profile_versions
    where athlete_id = 'a0000000-0000-0000-0000-000000000105'
      and status = 'active'
  ),
  1,
  'confirming a threshold leaves the prior active zones unchanged'
);
select is(
  (
    select count(*)::integer
    from public.zone_profile_versions
    where athlete_id = 'a0000000-0000-0000-0000-000000000105'
      and status = 'pending'
  ),
  1,
  'threshold confirmation creates a separately pending zone proposal'
);

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

create temporary table rejected_evaluation as
select public.save_calibration_evaluation(
  'a0000000-0000-0000-0000-000000000105',
  jsonb_build_object(
    'activity_id', 'aa000000-0000-0000-0000-000000000105',
    'protocol_id', 'start23_run_threshold_30min_v1',
    'discipline', 'run',
    'ruleset_version', 'start23-calibration-ruleset-v2',
    'status', 'threshold_estimated',
    'threshold_status', 'threshold_estimated',
    'zone_status', 'pending_athlete_confirmation',
    'confidence', 'medium',
    'reason_codes', jsonb_build_array(
      'zone_profile_pending_athlete_confirmation'
    ),
    'thresholds', jsonb_build_array(
      jsonb_build_object(
        'metric_kind', 'run_threshold_pace_seconds_per_km', 'value', '300'
      )
    ),
    'zone_model_version', 'start23-zone-model-1.0',
    'zone_profiles', (select metric_profiles from zone_model_fixture),
    'requires_athlete_confirmation', true,
    'review_status', 'pending_athlete_confirmation'
  ),
  repeat('e', 64)
) as result;
grant select on rejected_evaluation to authenticated, service_role;

select is(
  public.reject_calibration_threshold(
    'a0000000-0000-0000-0000-000000000105',
    (select (result ->> 'id')::uuid from rejected_evaluation)
  ) ->> 'state',
  'rejected',
  'an athlete rejection is persisted without generating zones'
);

reset role;
select is(
  (
    select count(*)::integer
    from public.zone_profile_versions
    where calibration_evaluation_id = (
      select (result ->> 'id')::uuid from rejected_evaluation
    )
  ),
  0,
  'a rejected threshold has no calculated zone version'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-000000000105","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'b0000000-0000-0000-0000-000000000105';
set local role authenticated;
select is(
  (select count(*)::integer from public.calibration_threshold_decisions),
  0,
  'RLS hides another athlete threshold decisions'
);

reset role;
select ok(
  not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name in (
        'zone_profile_versions',
        'calibration_evaluations',
        'calibration_threshold_decisions'
      )
      and lower(column_name) like '%tss%'
  ),
  'the public zone lifecycle contains no TSS fields'
);

select * from finish();
rollback;
