-- Final-state profile boundary after the R2-R5 and Phase 13/14 remediations.
-- Fixtures deliberately retain every opaque-owner and RPC-integrity trigger.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table('public', 'athlete_profiles', 'operational compatibility table exists');
select col_is_pk(
  'public', 'athlete_profiles', 'athlete_id',
  'legacy auth owner remains the compatibility primary key before R6'
);
select ok(
  (
    select relrowsecurity and relforcerowsecurity
    from pg_class
    where oid = 'public.athlete_profiles'::regclass
  ),
  'operational compatibility rows have enabled and forced RLS'
);
select policies_are(
  'public',
  'athlete_profiles',
  array[
    'athlete_profiles_insert_own',
    'athlete_profiles_opaque_owner_restrict',
    'athlete_profiles_select_own',
    'athlete_profiles_update_own'
  ],
  'the final migration chain retains only the expected compatibility policies'
);

select ok(
  not has_table_privilege('anon', 'public.athlete_profiles', 'select')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'insert')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'update')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'delete')
  and not has_table_privilege('authenticated', 'public.athlete_profiles', 'select')
  and not has_table_privilege('authenticated', 'public.athlete_profiles', 'insert')
  and not has_table_privilege('authenticated', 'public.athlete_profiles', 'update')
  and not has_table_privilege('authenticated', 'public.athlete_profiles', 'delete')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'select')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'insert')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'update')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'delete'),
  'no Data API role has broad direct operational profile privileges'
);
select ok(
  not has_any_column_privilege(
    'authenticated', 'public.athlete_profiles', 'select'
  )
  and not has_any_column_privilege(
    'authenticated', 'public.athlete_profiles', 'insert'
  )
  and not has_any_column_privilege(
    'authenticated', 'public.athlete_profiles', 'update'
  ),
  'authenticated has no residual column-level operational-table bypass'
);

select ok(
  has_function_privilege(
    'authenticated', 'public.get_operational_athlete_profile()', 'execute'
  )
  and has_function_privilege(
    'authenticated',
    'public.save_operational_athlete_profile(jsonb)',
    'execute'
  )
  and not has_function_privilege(
    'anon', 'public.get_operational_athlete_profile()', 'execute'
  )
  and not has_function_privilege(
    'anon', 'public.save_operational_athlete_profile(jsonb)', 'execute'
  )
  and not has_function_privilege(
    'service_role', 'public.get_operational_athlete_profile()', 'execute'
  )
  and not has_function_privilege(
    'service_role', 'public.save_operational_athlete_profile(jsonb)', 'execute'
  ),
  'only authenticated owns the narrow operational read/write contracts'
);
select ok(
  has_function_privilege(
    'authenticated', 'public.save_identifying_profile(jsonb)', 'execute'
  )
  and has_function_privilege(
    'authenticated', 'public.save_physiology_profile(jsonb)', 'execute'
  )
  and not has_function_privilege(
    'anon', 'public.save_identifying_profile(jsonb)', 'execute'
  )
  and not has_function_privilege(
    'anon', 'public.save_physiology_profile(jsonb)', 'execute'
  )
  and not has_function_privilege(
    'service_role', 'public.save_identifying_profile(jsonb)', 'execute'
  )
  and not has_function_privilege(
    'service_role', 'public.save_physiology_profile(jsonb)', 'execute'
  ),
  'identifying and physiology writes are authenticated RPC-only contracts'
);

select policies_are(
  'public',
  'athlete_identifying_profiles',
  array[
    'athlete_identifying_profiles_insert_own',
    'athlete_identifying_profiles_select_own',
    'athlete_identifying_profiles_update_own'
  ],
  'identifying rows retain only final owner policies'
);
select policies_are(
  'public',
  'athlete_physiology_profiles',
  array[
    'athlete_physiology_profiles_insert_own',
    'athlete_physiology_profiles_select_own',
    'athlete_physiology_profiles_update_own'
  ],
  'physiology rows retain only final owner policies'
);
select ok(
  has_column_privilege(
    'authenticated', 'public.athlete_identifying_profiles', 'first_name', 'select'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_identifying_profiles',
    'source_legacy_profile_revision',
    'select'
  )
  and has_column_privilege(
    'authenticated',
    'public.athlete_physiology_profiles',
    'resting_heart_rate_bpm',
    'select'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_physiology_profiles',
    'source_legacy_profile_revision',
    'select'
  ),
  'authenticated reads expose only the approved split-profile projections'
);

select ok(
  not has_table_privilege(
    'authenticated', 'private.athlete_identity_map', 'select'
  )
  and not has_any_column_privilege(
    'authenticated', 'private.athlete_identity_map', 'select'
  )
  and not has_table_privilege('service_role', 'private.athlete_identity_map', 'select')
  and has_column_privilege(
    'service_role', 'private.athlete_identity_map', 'athlete_id', 'select'
  )
  and has_column_privilege(
    'service_role', 'private.athlete_identity_map', 'auth_user_id', 'select'
  )
  and not has_column_privilege(
    'service_role', 'private.athlete_identity_map', 'creation_source', 'select'
  ),
  'identity mapping cannot be enumerated by clients and service access is column-limited'
);
select ok(
  has_function_privilege(
    'service_role', 'public.resolve_legacy_auth_user_id(uuid)', 'execute'
  )
  and not has_function_privilege(
    'authenticated', 'public.resolve_legacy_auth_user_id(uuid)', 'execute'
  )
  and has_function_privilege(
    'authenticated', 'public.get_current_athlete_id()', 'execute'
  )
  and not has_function_privilege(
    'service_role', 'public.get_current_athlete_id()', 'execute'
  ),
  'opaque-owner adapters retain their intended role separation'
);

select ok(
  exists (
    select 1 from pg_trigger
    where tgrelid = 'auth.users'::regclass
      and tgname = 'start23_create_opaque_athlete_identity'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.athlete_profiles'::regclass
      and tgname = 'r3_00_sync_opaque_athlete_owner'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.athlete_identifying_profiles'::regclass
      and tgname = 'athlete_identifying_profiles_00_require_rpc'
      and tgenabled = 'O' and not tgisinternal
  )
  and exists (
    select 1 from pg_trigger
    where tgrelid = 'public.athlete_physiology_profiles'::regclass
      and tgname = 'athlete_physiology_profiles_00_require_rpc'
      and tgenabled = 'O' and not tgisinternal
  ),
  'identity creation, opaque-owner, and split-profile RPC guards remain enabled'
);

-- The auth trigger is the legitimate fixture path for opaque identities.
insert into auth.users (id)
values
  ('10000000-0000-0000-0000-000000000001'),
  ('20000000-0000-0000-0000-000000000002');

select set_config(
  'request.jwt.claims',
  '{"sub":"10000000-0000-0000-0000-000000000001","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = '10000000-0000-0000-0000-000000000001';
set local role authenticated;

select throws_ok(
  $q$select * from public.athlete_profiles$q$,
  '42501', null,
  'authenticated broad operational reads fail before RLS can widen them'
);
select throws_ok(
  $q$insert into public.athlete_profiles(athlete_id) values (
    '10000000-0000-0000-0000-000000000001'
  )$q$,
  '42501', null,
  'authenticated direct operational inserts fail'
);
select throws_ok(
  $q$update public.athlete_profiles set timezone = 'Europe/Paris'$q$,
  '42501', null,
  'authenticated direct operational updates fail'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"athlete_id":"20000000-0000-0000-0000-000000000002"}'::jsonb
  )$q$,
  '23514', 'invalid operational profile payload',
  'the owner-derived operational RPC rejects attacker-controlled athlete IDs'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Definitely_Not_A_Zone","timezone_source":"manual","timezone_confirmed":true}'::jsonb
  )$q$,
  '23514', 'explicit valid operational confirmation is required',
  'invalid IANA timezones fail'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Amsterdam","timezone_source":"manual","timezone_confirmed":true,"timezone_confirmed_at":"2000-01-01T00:00:00Z"}'::jsonb
  )$q$,
  '23514', 'invalid operational profile payload',
  'forged timezone confirmation timestamps fail'
);
select throws_ok(
  $q$select public.save_operational_athlete_profile(
    '{"heart_rate_monitor_confirmed":true,"heart_rate_monitor_confirmed_at":"2000-01-01T00:00:00Z"}'::jsonb
  )$q$,
  '23514', 'invalid operational profile payload',
  'forged monitor confirmation timestamps fail'
);
select lives_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/Amsterdam","timezone_source":"manual","timezone_confirmed":true,"heart_rate_monitor_confirmed":true}'::jsonb
  )$q$,
  'valid operational writes succeed through the narrow owner-derived RPC'
);
select lives_ok(
  $q$select public.save_identifying_profile(
    '{"first_name":"Owner","last_name":"One"}'::jsonb
  )$q$,
  'valid identifying writes succeed through the guarded RPC'
);
select lives_ok(
  $q$select public.save_physiology_profile(
    '{"date_of_birth":"1990-01-01","resting_heart_rate_bpm":52}'::jsonb
  )$q$,
  'valid physiology writes succeed through the guarded RPC'
);
select throws_ok(
  $q$select public.save_identifying_profile(
    '{"athlete_id":"20000000-0000-0000-0000-000000000002","first_name":"Forged"}'::jsonb
  )$q$,
  '23514', 'invalid identifying profile payload',
  'split-profile RPCs reject attacker-controlled athlete IDs'
);
select throws_ok(
  $q$update public.athlete_identifying_profiles set first_name = 'Bypass'$q$,
  '42501', 'profile writes require the intended RPC',
  'direct identifying writes fail at the RPC-integrity trigger'
);
select throws_ok(
  $q$update public.athlete_physiology_profiles
    set resting_heart_rate_bpm = 40$q$,
  '42501', 'profile writes require the intended RPC',
  'retired direct physiology writes fail at the RPC-integrity trigger'
);
select throws_ok(
  $q$select athlete_id, auth_user_id from private.athlete_identity_map$q$,
  '42501', null,
  'authenticated clients cannot enumerate the private identity map'
);
select is(
  (public.get_operational_athlete_profile() ->> 'athlete_id')::uuid,
  public.get_current_athlete_id(),
  'the operational read exposes only the JWT-derived opaque owner'
);
select ok(
  not public.get_operational_athlete_profile() ? 'internal_athlete_id'
  and not public.get_operational_athlete_profile() ? 'date_of_birth'
  and not public.get_operational_athlete_profile() ? 'resting_heart_rate_bpm',
  'the operational projection excludes identity internals and physiology'
);
select results_eq(
  $q$select first_name, last_name
    from public.athlete_identifying_profiles$q$,
  $q$values ('Owner'::text, 'One'::text)$q$,
  'the current owner can read only the narrow identifying projection'
);
select results_eq(
  $q$select date_of_birth, resting_heart_rate_bpm
    from public.athlete_physiology_profiles$q$,
  $q$values ('1990-01-01'::date, 52::smallint)$q$,
  'the current owner can read only the narrow physiology projection'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"sub":"20000000-0000-0000-0000-000000000002","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = '20000000-0000-0000-0000-000000000002';
set local role authenticated;
select lives_ok(
  $q$select public.save_operational_athlete_profile(
    '{"timezone":"Europe/London","timezone_source":"manual","timezone_confirmed":true}'::jsonb
  )$q$,
  'a second owner can create only their own operational record through the RPC'
);
select is(
  (select count(*) from public.athlete_identifying_profiles where first_name = 'Owner'),
  0::bigint,
  'a second owner cannot read the first owner identifying row'
);
select is(
  (
    select count(*) from public.athlete_physiology_profiles
    where resting_heart_rate_bpm = 52
  ),
  0::bigint,
  'a second owner cannot read the first owner physiology row'
);
select throws_ok(
  $q$update public.athlete_profiles
    set timezone = 'UTC'
    where athlete_id = '10000000-0000-0000-0000-000000000001'$q$,
  '42501', null,
  'a second owner cannot mutate another operational row or any direct row'
);
reset role;

set local role service_role;
select throws_ok(
  $q$select * from public.athlete_profiles$q$,
  '42501', null,
  'service operations do not regain broad legacy operational-table reads'
);
reset role;

select * from finish();
rollback;
