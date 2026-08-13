begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(16);

select is(
  (select count(*) from public.workout_templates),
  8::bigint,
  'the current reviewed catalog contains eight immutable versions'
);

select is(
  (
    select count(distinct template_key)
    from public.workout_templates
  ),
  7::bigint,
  'the current catalog resolves to seven logical templates'
);

select results_eq(
  $$
    select discipline, count(*)::bigint
    from (
      select distinct on (template_key) template_key, discipline
      from public.workout_templates
      order by template_key, version desc
    ) latest
    group by discipline
    order by discipline
  $$,
  $$
    values ('bike'::text, 3::bigint),
           ('run'::text, 2::bigint),
           ('swim'::text, 2::bigint)
  $$,
  'the active seed is balanced across swim, bike, and run'
);

select lives_ok(
  $$
    select private.validate_workout_template(id)
    from public.workout_templates
  $$,
  'all reviewed templates pass aggregate validation'
);

select is(
  (
    select version
    from public.workout_templates
    where template_key = '50000000-0000-0000-0000-000000000005'
    order by version desc
    limit 1
  ),
  2,
  'the latest logical run template is version two'
);

select is(
  (
    select duration_minutes
    from public.workout_templates
    where id = '51000000-0000-0000-0000-000000000005'
  ),
  40::numeric,
  'the historical version retains its original duration'
);

select is(
  (
    select planned_tss
    from private.workout_template_loads
    where template_id = '51000000-0000-0000-0000-000000000005'
  ),
  2::numeric,
  'the historical version retains its original hidden load'
);

select throws_ok(
  $$
    update public.workout_templates
    set duration_minutes = 99
    where id = '51000000-0000-0000-0000-000000000005'
  $$,
  '55000',
  'workout catalog versions are immutable',
  'published template versions cannot be edited'
);

select ok(
  not has_schema_privilege('authenticated', 'private', 'usage'),
  'authenticated athletes cannot use the private schema'
);

select ok(
  not has_table_privilege(
    'authenticated',
    'private.workout_template_loads',
    'select'
  ),
  'authenticated athletes cannot select hidden planned load'
);

select ok(
  not has_table_privilege(
    'service_role',
    'private.workout_template_loads',
    'select'
  ),
  'the service role has no direct hidden-load table access'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.get_workout_catalog_for_planning()',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.get_workout_catalog_for_planning()',
    'execute'
  )
  and not has_function_privilege(
    'anon',
    'public.get_workout_catalog_for_planning()',
    'execute'
  ),
  'only the service role can execute the private planning-catalog RPC'
);

select set_config(
  'request.jwt.claims',
  '{"role":"service_role"}',
  true
);
set local role service_role;
select is(
  (
    select count(*)
    from public.get_workout_catalog_for_planning()
  ),
  8::bigint,
  'the trusted planning RPC returns every immutable version with hidden load'
);
reset role;

select ok(
  has_table_privilege('authenticated', 'public.workout_templates', 'select')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'insert')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'update')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'delete'),
  'authenticated athletes have read-only catalog privileges'
);

set local role anon;
select throws_ok(
  $$select count(*) from public.workout_templates$$,
  '42501',
  'permission denied for table workout_templates',
  'anonymous clients cannot read the catalog'
);
reset role;

set local role authenticated;
select is(
  (select count(*) from public.workout_templates),
  8::bigint,
  'authenticated clients can read public catalog fields'
);
reset role;

select * from finish();
rollback;
