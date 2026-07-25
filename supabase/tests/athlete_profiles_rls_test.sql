begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table(
  'public',
  'athlete_profiles',
  'athlete_profiles exists'
);

select col_is_pk(
  'public',
  'athlete_profiles',
  'athlete_id',
  'athlete_id is the primary key'
);

select ok(
  exists (
    select 1
    from pg_constraint
    where conrelid = 'public.athlete_profiles'::regclass
      and conname = 'athlete_profiles_athlete_id_fkey'
      and contype = 'f'
  ),
  'athlete_id references auth.users'
);

select ok(
  (
    select relrowsecurity
    from pg_class
    where oid = 'public.athlete_profiles'::regclass
  ),
  'RLS is enabled'
);

select ok(
  (
    select relforcerowsecurity
    from pg_class
    where oid = 'public.athlete_profiles'::regclass
  ),
  'RLS is forced for table owners'
);

select policies_are(
  'public',
  'athlete_profiles',
  array[
    'athlete_profiles_insert_own',
    'athlete_profiles_select_own',
    'athlete_profiles_update_own'
  ],
  'only the expected profile policies exist'
);

select ok(
  not has_table_privilege('anon', 'public.athlete_profiles', 'select')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'insert')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'update')
  and not has_table_privilege('anon', 'public.athlete_profiles', 'delete'),
  'anon has no profile privileges'
);

select ok(
  not has_table_privilege('service_role', 'public.athlete_profiles', 'select')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'insert')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'update')
  and not has_table_privilege('service_role', 'public.athlete_profiles', 'delete'),
  'service_role has no profile privileges'
);

select ok(
  has_table_privilege('authenticated', 'public.athlete_profiles', 'select'),
  'authenticated may select profiles subject to RLS'
);

select ok(
  has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'athlete_id',
    'insert'
  )
  and has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'timezone',
    'insert'
  )
  and has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'onboarding_status',
    'insert'
  ),
  'authenticated may insert only supported profile input columns'
);

select ok(
  not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'revision',
    'insert'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'created_at',
    'insert'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'updated_at',
    'insert'
  ),
  'authenticated cannot choose generated metadata on insert'
);

select ok(
  has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'timezone',
    'update'
  )
  and has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'onboarding_status',
    'update'
  ),
  'authenticated may update supported profile fields'
);

select ok(
  not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'athlete_id',
    'update'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'revision',
    'update'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'created_at',
    'update'
  )
  and not has_column_privilege(
    'authenticated',
    'public.athlete_profiles',
    'updated_at',
    'update'
  )
  and not has_table_privilege(
    'authenticated',
    'public.athlete_profiles',
    'delete'
  ),
  'authenticated cannot change ownership or generated metadata or delete profiles'
);

select ok(
  exists (
    select 1
    from pg_trigger
    where tgrelid = 'public.athlete_profiles'::regclass
      and tgname = 'athlete_profiles_set_update_metadata'
      and not tgisinternal
  ),
  'profile update metadata trigger exists'
);

select ok(
  not (
    select prosecdef
    from pg_proc
    where oid =
      'private.set_athlete_profile_update_metadata()'::regprocedure
  ),
  'profile update trigger function is security invoker'
);

select ok(
  not has_schema_privilege('anon', 'private', 'usage')
  and not has_schema_privilege('authenticated', 'private', 'usage')
  and not has_schema_privilege('service_role', 'private', 'usage'),
  'Data API roles cannot use the private schema'
);

select ok(
  not has_function_privilege(
    'anon',
    'private.set_athlete_profile_update_metadata()',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'private.set_athlete_profile_update_metadata()',
    'execute'
  )
  and not has_function_privilege(
    'service_role',
    'private.set_athlete_profile_update_metadata()',
    'execute'
  ),
  'Data API roles cannot execute the trigger function'
);

alter table public.athlete_profiles disable trigger all;

insert into auth.users (id)
values
  ('10000000-0000-0000-0000-000000000001'),
  ('20000000-0000-0000-0000-000000000002');

insert into public.athlete_profiles (athlete_id, timezone)
values
  ('10000000-0000-0000-0000-000000000001', 'Europe/Amsterdam'),
  ('20000000-0000-0000-0000-000000000002', 'Europe/London');

alter table public.athlete_profiles enable trigger all;

set local role authenticated;
set local request.jwt.claim.sub = '10000000-0000-0000-0000-000000000001';

select results_eq(
  $$select athlete_id from public.athlete_profiles order by athlete_id$$,
  $$values ('10000000-0000-0000-0000-000000000001'::uuid)$$,
  'an athlete can select only their own profile'
);

select results_eq(
  $$
    update public.athlete_profiles
    set timezone = 'Europe/Paris'
    where athlete_id = '20000000-0000-0000-0000-000000000002'
    returning athlete_id
  $$,
  $$select null::uuid where false$$,
  'an athlete cannot update another profile'
);

select lives_ok(
  $$
    update public.athlete_profiles
    set timezone = 'Europe/Brussels'
    where athlete_id = '10000000-0000-0000-0000-000000000001'
  $$,
  'an athlete can update their own supported fields'
);

select is(
  (
    select revision
    from public.athlete_profiles
    where athlete_id = '10000000-0000-0000-0000-000000000001'
  ),
  2::bigint,
  'an update increments the profile revision'
);

reset role;

select * from finish();
rollback;
