begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_r2_r3_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_r2_r3_tap_results to authenticated, service_role;
grant usage, select on sequence phase_r2_r3_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_r2_r3_tap_results (result) select has_table('private', 'athlete_identity_map', 'opaque identity map exists');
insert into phase_r2_r3_tap_results (result) select has_pk('private', 'athlete_identity_map', 'opaque athlete id is the map PK');
insert into phase_r2_r3_tap_results (result) select has_column('public', 'athlete_profiles', 'internal_athlete_id', 'legacy operational profile has opaque owner');
insert into phase_r2_r3_tap_results (result) select has_table('public', 'athlete_identifying_profiles', 'identifying profile is separate');
insert into phase_r2_r3_tap_results (result) select has_table('public', 'athlete_physiology_profiles', 'physiology profile is separate');
insert into phase_r2_r3_tap_results (result) select has_column('public', 'athlete_identifying_profiles', 'first_name', 'identifying record owns first name');
insert into phase_r2_r3_tap_results (result) select has_column('public', 'athlete_physiology_profiles', 'resting_heart_rate_bpm', 'physiology record owns resting HR');
insert into phase_r2_r3_tap_results (result) select has_column('public', 'initial_plan_requests', 'onboarding_version', 'planning request records onboarding version');
insert into phase_r2_r3_tap_results (result) select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'public.activity_files'::regclass
      and conname = 'activity_files_path_dual_owner_valid'
      and contype = 'c'
  ),
  'activity-file paths preserve old owners and accept opaque owners'
);
insert into phase_r2_r3_tap_results (result) select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'private.webhook_receipts'::regclass
      and conname = 'webhook_receipts_opaque_owner_pair_valid'
      and contype = 'c'
  ),
  'nullable PING receipts preserve paired owner absence'
);
insert into phase_r2_r3_tap_results (result) select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.athlete_identifying_profiles'::regclass), 'identifying profile forces RLS');
insert into phase_r2_r3_tap_results (result) select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.athlete_physiology_profiles'::regclass), 'physiology profile forces RLS');
insert into phase_r2_r3_tap_results (result) select ok(not has_table_privilege('anon', 'public.athlete_identifying_profiles', 'select'), 'anonymous cannot read identifying data');
insert into phase_r2_r3_tap_results (result) select ok(not has_table_privilege('anon', 'public.athlete_physiology_profiles', 'select'), 'anonymous cannot read physiology data');
insert into phase_r2_r3_tap_results (result) select ok(not has_table_privilege('authenticated', 'private.athlete_identity_map', 'select'), 'athletes cannot enumerate identity mappings');
insert into phase_r2_r3_tap_results (result) select ok(not has_column_privilege('authenticated', 'public.athlete_identifying_profiles', 'backfilled_at', 'select'), 'backfill provenance is not in the athlete table grant');
insert into phase_r2_r3_tap_results (result) select ok(not has_column_privilege('authenticated', 'public.athlete_physiology_profiles', 'source_legacy_profile_revision', 'select'), 'legacy physiology provenance is not in the athlete table grant');
insert into phase_r2_r3_tap_results (result) select ok(has_function_privilege('authenticated', 'public.get_current_athlete_id()', 'execute'), 'athlete can resolve only own opaque id');
insert into phase_r2_r3_tap_results (result) select ok(not has_function_privilege('authenticated', 'public.resolve_legacy_auth_user_id(uuid)', 'execute'), 'legacy adapter is service-only');
insert into phase_r2_r3_tap_results (result) select ok(not has_function_privilege('authenticated', 'public.get_current_planning_eligibility_context(uuid)', 'execute'), 'planning eligibility context is service-only');
insert into phase_r2_r3_tap_results (result) select ok(has_function_privilege('service_role', 'public.get_current_planning_eligibility_context(uuid)', 'execute'), 'trusted backend can read planning eligibility context');
insert into phase_r2_r3_tap_results (result) select ok(not has_function_privilege('authenticated', 'public.complete_onboarding()', 'execute'), 'unversioned completion bypass is revoked');
insert into phase_r2_r3_tap_results (result) select ok(not has_function_privilege('authenticated', 'public.complete_current_onboarding()', 'execute'), 'temporary R1 completion bypass is revoked');
insert into phase_r2_r3_tap_results (result) select ok(has_function_privilege('authenticated', 'public.complete_current_onboarding(bigint)', 'execute'), 'stale-safe completion is callable');
insert into phase_r2_r3_tap_results (result) select has_trigger('public', 'weekly_plans', 'weekly_plans_r3_10_require_current_onboarding', 'weekly plan writes enforce current onboarding');
insert into phase_r2_r3_tap_results (result) select has_trigger('public', 'plan_revisions', 'r3_10_require_current_onboarding', 'plan revision writes enforce current onboarding');
insert into phase_r2_r3_tap_results (result) select has_trigger('public', 'swipe_week_drafts', 'swipe_week_drafts_r3_10_require_current_onboarding', 'direct swipe writes enforce current onboarding');
insert into phase_r2_r3_tap_results (result) select has_trigger('public', 'calibration_observations', 'calibration_observations_r2_10_current_contract', 'current calibration inputs are enforced at persistence');

insert into auth.users(id) values
  ('a3000000-0000-0000-0000-000000000001'),
  ('b3000000-0000-0000-0000-000000000001');

insert into phase_r2_r3_tap_results (result) select throws_ok(
  $q$
    insert into public.calibration_observations(
      athlete_id, activity_id, protocol_id, discipline, segment_id,
      performed_at, payload, fingerprint
    ) values (
      'a3000000-0000-0000-0000-000000000001',
      gen_random_uuid(),
      'start23_week1_run_calibration_v1',
      'run',
      'comfortable_20min',
      statement_timestamp(),
      jsonb_build_object(
        'activity_id', gen_random_uuid(),
        'protocol_id', 'start23_week1_run_calibration_v1',
        'discipline', 'run',
        'segment_id', 'comfortable_20min',
        'performed_at', statement_timestamp(),
        'completed', true,
        'interrupted', false,
        'quality_status', 'sufficient',
        'target_rpe', 4,
        'reported_block_rpe', 4
      ),
      md5('missing-current-observation-input')
    )
  $q$,
  '23514',
  'current run/bike calibration requires measured average HR',
  'direct persistence cannot omit current run/bike average HR'
);

insert into phase_r2_r3_tap_results (result) select is(
  (select count(*) from private.athlete_identity_map where auth_user_id in (
    'a3000000-0000-0000-0000-000000000001',
    'b3000000-0000-0000-0000-000000000001'
  )),
  2::bigint,
  'fresh auth users receive exactly one opaque identity each'
);
insert into phase_r2_r3_tap_results (result) select is(
  (select count(distinct athlete_id) from private.athlete_identity_map where auth_user_id in (
    'a3000000-0000-0000-0000-000000000001',
    'b3000000-0000-0000-0000-000000000001'
  )),
  2::bigint,
  'different auth users cannot share an athlete identity'
);
insert into phase_r2_r3_tap_results (result) select is(private.backfill_athlete_identity_maps(), 0::bigint, 'identity backfill is idempotent');

insert into public.athlete_profiles(
  athlete_id, date_of_birth, resting_heart_rate_bpm, timezone, onboarding_status
) values (
  'a3000000-0000-0000-0000-000000000001', '1990-01-02', 51, 'UTC', 'in_progress'
);
select set_config('start23.profile_write', 'on', true);
select private.backfill_split_athlete_profiles();
select private.backfill_split_athlete_profiles();
select set_config('start23.profile_write', '', true);

insert into phase_r2_r3_tap_results (result) select is(
  (
    select physiology.date_of_birth
    from public.athlete_physiology_profiles physiology
    join private.athlete_identity_map mapping on mapping.athlete_id = physiology.athlete_id
    where mapping.auth_user_id = 'a3000000-0000-0000-0000-000000000001'
  ),
  '1990-01-02'::date,
  'DOB is copied exactly without reinterpretation'
);
insert into phase_r2_r3_tap_results (result) select is(
  (
    select physiology.resting_heart_rate_bpm
    from public.athlete_physiology_profiles physiology
    join private.athlete_identity_map mapping on mapping.athlete_id = physiology.athlete_id
    where mapping.auth_user_id = 'a3000000-0000-0000-0000-000000000001'
  ),
  51::smallint,
  'resting HR is copied exactly without recalculation'
);
insert into phase_r2_r3_tap_results (result) select is(
  (select count(*) from public.athlete_physiology_profiles physiology join private.athlete_identity_map mapping on mapping.athlete_id = physiology.athlete_id where mapping.auth_user_id = 'a3000000-0000-0000-0000-000000000001'),
  1::bigint,
  'repeated split-profile backfill does not duplicate an athlete'
);

select set_config(
  'start23.test_other_athlete_id',
  (
    select athlete_id::text
    from private.athlete_identity_map
    where auth_user_id = 'b3000000-0000-0000-0000-000000000001'
  ),
  true
);
select set_config('request.jwt.claims', '{"sub":"a3000000-0000-0000-0000-000000000001","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'a3000000-0000-0000-0000-000000000001';
set local role authenticated;
insert into phase_r2_r3_tap_results (result) select is((select count(*) from public.athlete_physiology_profiles), 1::bigint, 'owner can read only own physiology row');
insert into phase_r2_r3_tap_results (result) select throws_ok($q$insert into public.athlete_identifying_profiles(athlete_id, first_name) values (public.get_current_athlete_id(), 'Bypass')$q$, '42501', 'profile writes require the intended RPC', 'direct identifying write is denied');
insert into phase_r2_r3_tap_results (result) select lives_ok($q$select public.save_identifying_profile('{"first_name":"Ada","last_name":"Lovelace"}'::jsonb)$q$, 'owner can use identifying RPC');
insert into phase_r2_r3_tap_results (result) select lives_ok($q$select public.save_physiology_profile('{"resting_heart_rate_bpm":52}'::jsonb)$q$, 'owner can use physiology RPC');
insert into phase_r2_r3_tap_results (result) select ok(not (public.save_identifying_profile('{"first_name":"Ada"}'::jsonb) ? 'backfilled_at'), 'identifying RPC excludes migration provenance');
insert into phase_r2_r3_tap_results (result) select ok(not (public.save_physiology_profile('{"resting_heart_rate_bpm":52}'::jsonb) ? 'source_legacy_profile_revision'), 'physiology RPC excludes legacy provenance');
insert into phase_r2_r3_tap_results (result) select throws_ok($q$insert into public.athlete_physiology_profiles(athlete_id, resting_heart_rate_bpm) values (current_setting('start23.test_other_athlete_id')::uuid, 55)$q$, '42501', null, 'cross-athlete physiology write is denied');
insert into phase_r2_r3_tap_results (result) select throws_ok($q$insert into public.weekly_plans(athlete_id) values ('a3000000-0000-0000-0000-000000000001')$q$, '23514', 'current onboarding completion is required for planning', 'direct plan write cannot bypass current onboarding eligibility');
reset role;

insert into phase_r2_r3_tap_results (result) select is(
  (select count(*) from public.athlete_profiles where internal_athlete_id is null)
  + (select count(*) from public.onboarding_sessions where internal_athlete_id is null)
  + (select count(*) from public.activities where internal_athlete_id is null)
  + (select count(*) from public.calibration_evaluations where internal_athlete_id is null)
  + (select count(*) from public.weekly_plans where internal_athlete_id is null),
  0::bigint,
  'representative active domains have no orphan opaque owners'
);
insert into phase_r2_r3_tap_results (result) select is(
  (
    select count(*)
    from private.webhook_receipts
    where (athlete_id is null) <> (internal_athlete_id is null)
  ),
  0::bigint,
  'nullable webhook ownership cannot be half-mapped'
);

insert into auth.users(id)
values ('c3000000-0000-0000-0000-000000000001');
insert into public.athlete_profiles(athlete_id, onboarding_status)
values ('c3000000-0000-0000-0000-000000000001', 'in_progress');
select set_config('start23.profile_write', 'on', true);
insert into public.athlete_identifying_profiles(athlete_id, first_name)
select athlete_id, 'Delete'
from private.athlete_identity_map
where auth_user_id = 'c3000000-0000-0000-0000-000000000001';
insert into public.athlete_physiology_profiles(
  athlete_id, date_of_birth, resting_heart_rate_bpm
)
select athlete_id, '1990-01-01', 55
from private.athlete_identity_map
where auth_user_id = 'c3000000-0000-0000-0000-000000000001';
select set_config('start23.profile_write', '', true);
select set_config('start23.critical_write', 'on', true);
insert into public.goals(
  athlete_id, race_type, race_name, race_date,
  run_distance_meters, total_target_time_seconds, run_target_time_seconds
)
values (
  'c3000000-0000-0000-0000-000000000001', 'run', 'Delete cascade',
  current_date + 90, 10000, 3600, 3600
);
select set_config('start23.critical_write', '', true);

insert into phase_r2_r3_tap_results (result) select lives_ok(
  $q$delete from auth.users where id = 'c3000000-0000-0000-0000-000000000001'$q$,
  'Auth account deletion can cascade through protected owner tables'
);
insert into phase_r2_r3_tap_results (result) select is(
  (
    select count(*) from private.athlete_identity_map
    where auth_user_id = 'c3000000-0000-0000-0000-000000000001'
  ),
  0::bigint,
  'account deletion removes the opaque identity mapping'
);
insert into phase_r2_r3_tap_results (result) select is(
  (
    select count(*) from public.goals
    where athlete_id = 'c3000000-0000-0000-0000-000000000001'
  ),
  0::bigint,
  'account deletion removes legacy-owned business rows'
);

insert into phase_r2_r3_tap_results (result)
select * from finish();
select result from phase_r2_r3_tap_results order by sequence;
rollback;
