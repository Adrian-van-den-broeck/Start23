begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select ok(
  not has_table_privilege('authenticated', 'public.athlete_profiles', 'SELECT'),
  'legacy operational rows are not directly readable by authenticated clients'
);
select ok(
  not has_table_privilege('authenticated', 'public.athlete_profiles', 'INSERT'),
  'legacy operational rows are not directly insertable by authenticated clients'
);
select ok(
  not has_table_privilege('authenticated', 'public.athlete_profiles', 'UPDATE'),
  'legacy operational rows are not directly updateable by authenticated clients'
);
select ok(
  has_function_privilege(
    'authenticated',
    'public.get_operational_athlete_profile()',
    'EXECUTE'
  ),
  'authenticated clients have the narrow operational read RPC'
);
select ok(
  has_function_privilege(
    'authenticated',
    'public.save_operational_athlete_profile(jsonb)',
    'EXECUTE'
  ),
  'authenticated clients have the narrow operational write RPC'
);
select ok(
  not has_function_privilege(
    'service_role',
    'public.save_calculated_zone_profile_r5(uuid,jsonb)',
    'EXECUTE'
  ),
  'the superseded calculated-zone implementation is not externally callable'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.save_calculated_zone_profile(uuid,jsonb)',
    'EXECUTE'
  ),
  'the provenance-correct calculated-zone wrapper is service-only'
);

select is(
  private.required_disciplines_for_race_type('run'),
  array['run']::text[],
  'run races require run zones'
);
select is(
  private.required_disciplines_for_race_type('bike'),
  array['bike']::text[],
  'bike races require bike zones'
);
select is(
  private.required_disciplines_for_race_type('swim'),
  array['swim']::text[],
  'swim races require swim zones'
);
select is(
  private.required_disciplines_for_race_type('duathlon'),
  array['bike', 'run']::text[],
  'duathlon races require bike and run zones'
);
select is(
  private.required_disciplines_for_race_type('triathlon'),
  array['swim', 'bike', 'run']::text[],
  'triathlon races require swim, bike, and run zones'
);

insert into auth.users(id) values
  ('d6000000-0000-0000-0000-000000000001'),
  ('d6000000-0000-0000-0000-000000000002'),
  ('d6000000-0000-0000-0000-000000000003'),
  ('d6000000-0000-0000-0000-000000000004'),
  ('d6000000-0000-0000-0000-000000000005'),
  ('d6000000-0000-0000-0000-000000000006'),
  ('d6000000-0000-0000-0000-000000000007'),
  ('d6000000-0000-0000-0000-000000000008');

select set_config('start23.critical_write', 'on', true);

select lives_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds, run_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000001', 'run', 'Run',
    current_date + 90, 10000, 3600, 3600
  )$q$,
  'valid run shape passes direct table validation'
);
select lives_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    bike_distance_meters, total_target_time_seconds, bike_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000002', 'bike', 'Bike',
    current_date + 90, 40000, 7200, 7200
  )$q$,
  'valid bike shape passes direct table validation'
);
select lives_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    swim_distance_meters, total_target_time_seconds, swim_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000003', 'swim', 'Swim',
    current_date + 90, 1500, 2400, 2400
  )$q$,
  'valid swim shape passes direct table validation'
);
select lives_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    bike_distance_meters, run_distance_meters, total_target_time_seconds,
    bike_target_time_seconds, run_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000004', 'duathlon', 'Duo',
    current_date + 90, 40000, 10000, 10800, 7200, 3600
  )$q$,
  'valid duathlon shape passes direct table validation'
);
select lives_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    swim_distance_meters, bike_distance_meters, run_distance_meters,
    total_target_time_seconds, swim_target_time_seconds,
    bike_target_time_seconds, run_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000005', 'triathlon', 'Tri',
    current_date + 90, 1500, 40000, 10000, 14400, 2400, 7200, 3600
  )$q$,
  'valid triathlon shape passes direct table validation'
);

select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Missing',
    current_date + 90, 3600
  )$q$,
  '23514',
  null,
  'required NULL distance cannot pass through SQL UNKNOWN semantics'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Too far',
    current_date + 90, 1000001, 3600
  )$q$,
  '23514',
  null,
  'direct SQL enforces the same maximum distance as Pydantic'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Zero',
    current_date + 90, 0, 3600
  )$q$,
  '23514',
  null,
  'zero distance is rejected'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Negative',
    current_date + 90, -1, 3600
  )$q$,
  '23514',
  null,
  'negative distance is rejected'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    bike_distance_meters, run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Extra bike',
    current_date + 90, 1000, 10000, 3600
  )$q$,
  '23514',
  null,
  'a single-sport shape rejects unrelated discipline fields'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Zero time',
    current_date + 90, 10000, 0
  )$q$,
  '23514',
  null,
  'zero total target time is rejected'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000006', 'run', 'Invalid date',
    'not-a-date', 10000, 3600
  )$q$,
  '22007',
  null,
  'invalid date input is rejected before persistence'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"d6000000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'd6000000-0000-0000-0000-000000000006';
set local role authenticated;
select throws_ok(
  $q$select public.save_primary_race_goal(
    null, 'run', 'Too long', current_date + 90,
    null, null, 10000, 604801, null, null, 3600, null
  )$q$,
  '23514',
  null,
  'the RPC enforces the maximum total target time through the table contract'
);
reset role;
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds, run_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000007', 'run', 'Bad sum',
    current_date + 90, 10000, 3599, 3600
  )$q$,
  '23514',
  null,
  'discipline target time cannot exceed total target time'
);
select throws_ok(
  $q$insert into public.goals(
    athlete_id, race_type, race_name, race_date,
    run_distance_meters, total_target_time_seconds
  ) values (
    'd6000000-0000-0000-0000-000000000008', 'run', 'Today',
    current_date, 10000, 3600
  )$q$,
  '23514',
  'race date must be in the future',
  'direct table writes enforce the same future-date rule as the RPC'
);

-- A configured setup is only intent. Even when it is internally consistent,
-- it cannot satisfy readiness before an active zone profile exists.
insert into public.athlete_profiles(athlete_id)
values ('d6000000-0000-0000-0000-000000000001');
select set_config(
  'request.jwt.claims',
  '{"sub":"d6000000-0000-0000-0000-000000000001","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'd6000000-0000-0000-0000-000000000001';
set local role authenticated;
select lives_ok(
  $q$select public.save_discipline_zone_setup(jsonb_build_object(
    'discipline', 'run',
    'setup_route', 'known_values',
    'guidance_mode', 'heart_rate',
    'setup_status', 'configured',
    'protocol_id', null,
    'pool_length_meters', null,
    'threshold_status', 'user_provided',
    'zone_status', 'pending_athlete_confirmation',
    'source', 'user_provided',
    'validation_status', 'self_reported',
    'confidence', 'not_assessed',
    'known_thresholds',
      '[{"metric_kind":"run_lthr_bpm","value":172}]'::jsonb,
    'known_zone_profiles', '[]'::jsonb
  ))$q$,
  'the direct setup RPC accepts a threshold-only known-values request'
);
reset role;
select ok(
  not private.current_onboarding_satisfied_steps(
    (select internal_athlete_id from public.athlete_profiles
     where athlete_id = 'd6000000-0000-0000-0000-000000000001')
  ) @> array['zones']::text[],
  'setup intent alone cannot imply zone readiness'
);

insert into public.athlete_profiles(athlete_id) values
  ('d6000000-0000-0000-0000-000000000006'),
  ('d6000000-0000-0000-0000-000000000007');

create temporary table first_operational_identity as
select mapping.athlete_id
from private.athlete_identity_map mapping
where mapping.auth_user_id = 'd6000000-0000-0000-0000-000000000006';
grant select on first_operational_identity to authenticated;

select set_config(
  'request.jwt.claims',
  '{"sub":"d6000000-0000-0000-0000-000000000006","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'd6000000-0000-0000-0000-000000000006';
set local role authenticated;

select throws_ok(
  $q$select * from public.athlete_profiles$q$,
  '42501',
  null,
  'authenticated callers cannot select legacy identity or physiology columns'
);
select throws_ok(
  $q$update public.athlete_profiles set timezone = 'UTC'$q$,
  '42501',
  null,
  'authenticated callers cannot write operational fields directly'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Amsterdam","timezone_source":"manual","timezone_confirmed":true,"timezone_confirmed_at":"2000-01-01T00:00:00Z"}'::jsonb
  )$q$,
  '23514',
  'invalid operational profile payload',
  'forged confirmation timestamps are rejected'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Definitely_Not_A_Zone","timezone_source":"manual","timezone_confirmed":true}'::jsonb
  )$q$,
  '23514',
  'explicit valid operational confirmation is required',
  'the operational RPC rejects invalid IANA timezone names'
);
select lives_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Amsterdam","timezone_source":"manual","timezone_confirmed":true}'::jsonb
  )$q$,
  'the narrow RPC accepts an explicit valid IANA timezone confirmation'
);
select is(
  (public.get_operational_athlete_profile() ->> 'athlete_id')::uuid,
  private.current_athlete_id(),
  'the operational read returns the JWT-derived opaque owner only'
);
select ok(
  not public.get_operational_athlete_profile() ? 'internal_athlete_id'
  and not public.get_operational_athlete_profile() ? 'date_of_birth'
  and not public.get_operational_athlete_profile() ? 'resting_heart_rate_bpm',
  'the narrow operational read excludes legacy identity and physiology fields'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"d6000000-0000-0000-0000-000000000007","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'd6000000-0000-0000-0000-000000000007';
set local role authenticated;
select isnt(
  (public.get_operational_athlete_profile() ->> 'athlete_id')::uuid,
  (select athlete_id from first_operational_identity),
  'a second owner cannot receive the first owner operational identity'
);
reset role;

select * from finish();
rollback;
