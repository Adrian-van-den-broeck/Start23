begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_column('public', 'athlete_profiles', 'timezone_source', 'timezone source is persisted');
select has_column('public', 'athlete_profiles', 'timezone_confirmed_at', 'timezone confirmation is persisted');
select has_column('public', 'athlete_profiles', 'heart_rate_monitor_confirmed_at', 'HR-monitor confirmation is persisted');
select has_column('public', 'goals', 'race_type', 'structured race type is persisted');
select has_column('public', 'goals', 'race_name', 'race name is retained');
select has_column('public', 'goals', 'total_target_time_seconds', 'total target time is persisted');
select has_trigger('public', 'activity_metrics', 'activity_metrics_r5_protect_average_hr', 'Phase 13 HR observation has a persistence guard');
select has_trigger('public', 'activities', 'activities_r4_10_require_confirmed_timezone', 'activity writes use the confirmed profile timezone');
select ok(has_function_privilege('authenticated', 'public.save_operational_athlete_profile(jsonb)', 'execute'), 'athlete can explicitly confirm operational prerequisites');
select ok(not has_function_privilege('authenticated', 'public.save_primary_race_goal(uuid,text,text,text,date,text[])', 'execute'), 'obsolete generic goal RPC is no longer callable');
select ok(has_function_privilege('authenticated', 'public.save_primary_race_goal(uuid,text,text,date,integer,integer,integer,integer,integer,integer,integer,text)', 'execute'), 'structured race RPC is callable');
select ok(not has_function_privilege('authenticated', 'public.revise_activity_rpe(uuid,uuid,jsonb)', 'execute'), 'athlete cannot call private-load correction directly');
select ok(has_function_privilege('service_role', 'public.revise_activity_rpe(uuid,uuid,jsonb)', 'execute'), 'trusted backend can call correction RPC');

insert into auth.users(id) values ('c4000000-0000-0000-0000-000000000001');

select set_config('request.jwt.claims', '{"sub":"c4000000-0000-0000-0000-000000000001","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'c4000000-0000-0000-0000-000000000001';
set local role authenticated;

select throws_ok(
  $q$select public.save_operational_athlete_profile('{"timezone":"Amsterdam-ish","timezone_source":"manual","timezone_confirmed":true}'::jsonb)$q$,
  '23514',
  'explicit valid operational confirmation is required',
  'free-text timezone is rejected'
);
select lives_ok(
  $q$select public.save_operational_athlete_profile('{"heart_rate_monitor_confirmed":true}'::jsonb)$q$,
  'HR-monitor access can be confirmed without naming a provider'
);
select lives_ok(
  $q$select public.save_operational_athlete_profile('{"timezone":"Europe/Amsterdam","timezone_source":"manual","timezone_confirmed":true}'::jsonb)$q$,
  'valid IANA timezone requires explicit confirmation'
);
select lives_ok(
  $q$select public.save_primary_race_goal(null, 'run', 'Owner run', current_date + 90, null, null, 10000, 3600, null, null, 3600, null)$q$,
  'owner can persist a valid structured run race'
);
select throws_ok(
  $q$select public.save_primary_race_goal(null, 'run', 'Invalid run', current_date + 90, null, 40000, null, 3600, null, null, null, null)$q$,
  '23514',
  null,
  'race-specific distance constraint rejects the wrong discipline'
);
reset role;

insert into public.activities(
  id, athlete_id, idempotency_key, request_fingerprint, discipline,
  started_at, timezone, duration_minutes, match_status, rpe, rpe_submitted_at,
  processing_state, qualitative_result, public_message
) values (
  'c4000000-0000-0000-0000-000000000010',
  'c4000000-0000-0000-0000-000000000001',
  'c4000000-0000-4000-8000-000000000011', repeat('a', 64), 'run',
  statement_timestamp(), 'Europe/Amsterdam', 60, 'unmatched', 4,
  statement_timestamp(), 'complete', 'unplanned', 'Activiteit verwerkt.'
);
select throws_ok(
  $q$update public.activities set timezone = 'UTC' where id = 'c4000000-0000-0000-0000-000000000010'$q$,
  '23514',
  'activity timezone must match the confirmed athlete timezone',
  'direct activity writes cannot bypass the persisted confirmed timezone'
);
insert into public.activity_metrics(
  activity_id, athlete_id, average_heart_rate_bpm, zone_minutes
) values (
  'c4000000-0000-0000-0000-000000000010',
  'c4000000-0000-0000-0000-000000000001', 150,
  array[60,0,0,0,0]::numeric[]
);

select lives_ok(
  $q$update public.activity_metrics set average_heart_rate_bpm = 151 where activity_id = 'c4000000-0000-0000-0000-000000000010'$q$,
  'average HR may still be corrected before Phase 13 load exists'
);
update public.activity_metrics set average_heart_rate_bpm = 150
where activity_id = 'c4000000-0000-0000-0000-000000000010';
insert into private.activity_loads(
  activity_id, athlete_id, realized_tss, calculation_method, ruleset_version,
  total_minutes, valid_minutes, coverage_ratio, load_status
) values (
  'c4000000-0000-0000-0000-000000000010',
  'c4000000-0000-0000-0000-000000000001', 40,
  'observed_zone_minutes', 'phase-13-joren-ruleset-1', 60, 60, 1, 'complete'
);

select throws_ok(
  $q$update public.activity_metrics set average_heart_rate_bpm = 152 where activity_id = 'c4000000-0000-0000-0000-000000000010'$q$,
  'PT409',
  'average heart rate is immutable after load calculation',
  'direct metric update cannot diverge from Phase 13 provenance'
);
select is(
  (select average_heart_rate_bpm from public.activity_metrics where activity_id = 'c4000000-0000-0000-0000-000000000010'),
  150::smallint,
  'rejected HR correction leaves the source observation unchanged'
);

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
select throws_ok(
  $q$select public.revise_activity_rpe('c4000000-0000-0000-0000-000000000001', 'c4000000-0000-0000-0000-000000000010', '{"rpe":4,"submitted_average_heart_rate_bpm":152}'::jsonb)$q$,
  'PT409',
  'average heart rate is immutable after load calculation',
  'ordinary correction rejects a changed HR before any RPE mutation'
);
select lives_ok(
  $q$select public.revise_activity_rpe('c4000000-0000-0000-0000-000000000001', 'c4000000-0000-0000-0000-000000000010', '{"rpe":4,"submitted_average_heart_rate_bpm":150}'::jsonb)$q$,
  'exact duplicate correction is idempotent'
);
reset role;
select is(
  (select count(*) from public.activity_rpe_revisions where activity_id = 'c4000000-0000-0000-0000-000000000010'),
  0::bigint,
  'duplicate correction creates no audit revision'
);
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
select lives_ok(
  $q$select public.revise_activity_rpe(
    'c4000000-0000-0000-0000-000000000001',
    'c4000000-0000-0000-0000-000000000010',
    '{"rpe":5,"expected_current_rpe":4,"submitted_average_heart_rate_bpm":150,"qualitative_result":"unplanned","public_message":"Activiteit verwerkt.","correction_reason":null,"realized_tss":"40","calculation_method":"observed_zone_minutes","ruleset_version":"phase-13-joren-ruleset-1","total_minutes":"60","valid_minutes":"60","coverage_ratio":"1","load_status":"complete","assigned_zone":null,"average_heart_rate_bpm":null,"zone_profile_id":null}'::jsonb
  )$q$,
  'matching stale precondition permits atomic RPE-only correction'
);
reset role;
select is(
  (select count(*) from public.activity_rpe_revisions where activity_id = 'c4000000-0000-0000-0000-000000000010'),
  1::bigint,
  'successful correction appends one audit revision'
);
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
select throws_ok(
  $q$select public.revise_activity_rpe('c4000000-0000-0000-0000-000000000001', 'c4000000-0000-0000-0000-000000000010', '{"rpe":6,"expected_current_rpe":4}'::jsonb)$q$,
  'PT409',
  'activity correction is stale',
  'stale correction is rejected'
);
reset role;
select is(
  (select rpe from public.activities where id = 'c4000000-0000-0000-0000-000000000010'),
  5::smallint,
  'stale rejection preserves the accepted RPE'
);

select * from finish();
rollback;
