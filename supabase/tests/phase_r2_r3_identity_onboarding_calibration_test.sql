begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table('private', 'athlete_identity_map', 'opaque identity map exists');
select has_pk('private', 'athlete_identity_map', 'opaque athlete id is the map PK');
select has_column('public', 'athlete_profiles', 'internal_athlete_id', 'legacy operational profile has opaque owner');
select has_table('public', 'athlete_identifying_profiles', 'identifying profile is separate');
select has_table('public', 'athlete_physiology_profiles', 'physiology profile is separate');
select has_column('public', 'athlete_identifying_profiles', 'first_name', 'identifying record owns first name');
select has_column('public', 'athlete_physiology_profiles', 'resting_heart_rate_bpm', 'physiology record owns resting HR');
select has_column('public', 'initial_plan_requests', 'onboarding_version', 'planning request records onboarding version');
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'public.activity_files'::regclass
      and conname = 'activity_files_path_dual_owner_valid'
      and contype = 'c'
  ),
  'activity-file paths preserve old owners and accept opaque owners'
);
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'private.webhook_receipts'::regclass
      and conname = 'webhook_receipts_opaque_owner_pair_valid'
      and contype = 'c'
  ),
  'nullable PING receipts preserve paired owner absence'
);
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.athlete_identifying_profiles'::regclass), 'identifying profile forces RLS');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.athlete_physiology_profiles'::regclass), 'physiology profile forces RLS');
select ok(not has_table_privilege('anon', 'public.athlete_identifying_profiles', 'select'), 'anonymous cannot read identifying data');
select ok(not has_table_privilege('anon', 'public.athlete_physiology_profiles', 'select'), 'anonymous cannot read physiology data');
select ok(not has_table_privilege('authenticated', 'private.athlete_identity_map', 'select'), 'athletes cannot enumerate identity mappings');
select ok(not has_column_privilege('authenticated', 'public.athlete_identifying_profiles', 'backfilled_at', 'select'), 'backfill provenance is not in the athlete table grant');
select ok(not has_column_privilege('authenticated', 'public.athlete_physiology_profiles', 'source_legacy_profile_revision', 'select'), 'legacy physiology provenance is not in the athlete table grant');
select ok(has_function_privilege('authenticated', 'public.get_current_athlete_id()', 'execute'), 'athlete can resolve only own opaque id');
select ok(not has_function_privilege('authenticated', 'public.resolve_legacy_auth_user_id(uuid)', 'execute'), 'legacy adapter is service-only');
select ok(not has_function_privilege('authenticated', 'public.get_current_planning_eligibility_context(uuid)', 'execute'), 'planning eligibility context is service-only');
select ok(has_function_privilege('service_role', 'public.get_current_planning_eligibility_context(uuid)', 'execute'), 'trusted backend can read planning eligibility context');
select ok(not has_function_privilege('authenticated', 'public.complete_onboarding()', 'execute'), 'unversioned completion bypass is revoked');
select ok(not has_function_privilege('authenticated', 'public.complete_current_onboarding()', 'execute'), 'temporary R1 completion bypass is revoked');
select ok(has_function_privilege('authenticated', 'public.complete_current_onboarding(bigint)', 'execute'), 'stale-safe completion is callable');
select has_trigger('public', 'weekly_plans', 'weekly_plans_r3_10_require_current_onboarding', 'weekly plan writes enforce current onboarding');
select has_trigger('public', 'plan_revisions', 'plan_revisions_r3_10_require_current_onboarding', 'plan revision writes enforce current onboarding');
select has_trigger('public', 'swipe_week_drafts', 'swipe_week_drafts_r3_10_require_current_onboarding', 'direct swipe writes enforce current onboarding');
select has_trigger('public', 'calibration_observations', 'calibration_observations_r2_10_current_contract', 'current calibration inputs are enforced at persistence');

insert into auth.users(id) values
  ('a3000000-0000-0000-0000-000000000001'),
  ('b3000000-0000-0000-0000-000000000001');

select throws_ok(
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

select is(
  (select count(*) from private.athlete_identity_map where auth_user_id in (
    'a3000000-0000-0000-0000-000000000001',
    'b3000000-0000-0000-0000-000000000001'
  )),
  2::bigint,
  'fresh auth users receive exactly one opaque identity each'
);
select is(
  (select count(distinct athlete_id) from private.athlete_identity_map where auth_user_id in (
    'a3000000-0000-0000-0000-000000000001',
    'b3000000-0000-0000-0000-000000000001'
  )),
  2::bigint,
  'different auth users cannot share an athlete identity'
);
select is(private.backfill_athlete_identity_maps(), 0::bigint, 'identity backfill is idempotent');

insert into public.athlete_profiles(
  athlete_id, date_of_birth, resting_heart_rate_bpm, timezone, onboarding_status
) values (
  'a3000000-0000-0000-0000-000000000001', '1990-01-02', 51, 'UTC', 'in_progress'
);
select private.backfill_split_athlete_profiles();
select private.backfill_split_athlete_profiles();

select is(
  (
    select physiology.date_of_birth
    from public.athlete_physiology_profiles physiology
    join private.athlete_identity_map mapping on mapping.athlete_id = physiology.athlete_id
    where mapping.auth_user_id = 'a3000000-0000-0000-0000-000000000001'
  ),
  '1990-01-02'::date,
  'DOB is copied exactly without reinterpretation'
);
select is(
  (
    select physiology.resting_heart_rate_bpm
    from public.athlete_physiology_profiles physiology
    join private.athlete_identity_map mapping on mapping.athlete_id = physiology.athlete_id
    where mapping.auth_user_id = 'a3000000-0000-0000-0000-000000000001'
  ),
  51::smallint,
  'resting HR is copied exactly without recalculation'
);
select is(
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
select is((select count(*) from public.athlete_physiology_profiles), 1::bigint, 'owner can read only own physiology row');
select throws_ok($q$insert into public.athlete_identifying_profiles(athlete_id, first_name) values (public.get_current_athlete_id(), 'Bypass')$q$, '42501', 'profile writes require the intended RPC', 'direct identifying write is denied');
select lives_ok($q$select public.save_identifying_profile('{"first_name":"Ada","last_name":"Lovelace"}'::jsonb)$q$, 'owner can use identifying RPC');
select lives_ok($q$select public.save_physiology_profile('{"resting_heart_rate_bpm":52}'::jsonb)$q$, 'owner can use physiology RPC');
select ok(not (public.save_identifying_profile('{"first_name":"Ada"}'::jsonb) ? 'backfilled_at'), 'identifying RPC excludes migration provenance');
select ok(not (public.save_physiology_profile('{"resting_heart_rate_bpm":52}'::jsonb) ? 'source_legacy_profile_revision'), 'physiology RPC excludes legacy provenance');
select throws_ok($q$insert into public.athlete_physiology_profiles(athlete_id, resting_heart_rate_bpm) values (current_setting('start23.test_other_athlete_id')::uuid, 55)$q$, '42501', null, 'cross-athlete physiology write is denied');
select throws_ok($q$insert into public.weekly_plans(athlete_id) values ('a3000000-0000-0000-0000-000000000001')$q$, '23514', 'current onboarding completion is required for planning', 'direct plan write cannot bypass current onboarding eligibility');
reset role;

select is(
  (select count(*) from public.athlete_profiles where internal_athlete_id is null)
  + (select count(*) from public.onboarding_sessions where internal_athlete_id is null)
  + (select count(*) from public.activities where internal_athlete_id is null)
  + (select count(*) from public.calibration_evaluations where internal_athlete_id is null)
  + (select count(*) from public.weekly_plans where internal_athlete_id is null),
  0::bigint,
  'representative active domains have no orphan opaque owners'
);
select is(
  (
    select count(*)
    from private.webhook_receipts
    where (athlete_id is null) <> (internal_athlete_id is null)
  ),
  0::bigint,
  'nullable webhook ownership cannot be half-mapped'
);

select * from finish();
rollback;
