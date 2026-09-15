begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(16);

create temporary table phase_5_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_5_tap_results to anon, authenticated, service_role;
grant usage, select on sequence phase_5_tap_results_sequence_seq
to anon, authenticated, service_role;

insert into phase_5_tap_results (result) select is(
  (select count(*) from public.workout_templates),
  171::bigint,
  'the current catalog contains reviewed and source-backed immutable versions'
);

insert into phase_5_tap_results (result) select is(
  (
    select count(distinct template_key)
    from public.workout_templates
  ),
  165::bigint,
  'the current catalog resolves every logical template key'
);

insert into phase_5_tap_results (result) select results_eq(
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
    values ('bike'::text, 56::bigint),
           ('run'::text, 53::bigint),
           ('swim'::text, 56::bigint)
  $$,
  'the active seed is balanced across swim, bike, and run'
);

insert into phase_5_tap_results (result) select lives_ok(
  $$
    select private.validate_workout_template(id)
    from public.workout_templates
  $$,
  'all reviewed templates pass aggregate validation'
);

insert into phase_5_tap_results (result) select is(
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

insert into phase_5_tap_results (result) select is(
  (
    select duration_minutes
    from public.workout_templates
    where id = '51000000-0000-0000-0000-000000000005'
  ),
  40::numeric,
  'the historical version retains its original duration'
);

insert into phase_5_tap_results (result) select is(
  (
    select planned_tss
    from private.workout_template_loads
    where template_id = '51000000-0000-0000-0000-000000000005'
  ),
  2::numeric,
  'the historical version retains its original hidden load'
);

insert into phase_5_tap_results (result) select throws_ok(
  $$
    update public.workout_templates
    set duration_minutes = 99
    where id = '51000000-0000-0000-0000-000000000005'
  $$,
  '55000',
  'workout catalog versions are immutable',
  'published template versions cannot be edited'
);

insert into phase_5_tap_results (result) select ok(
  has_schema_privilege('authenticated', 'private', 'usage'),
  'authenticated receives only function-scoped private schema usage'
);

insert into phase_5_tap_results (result) select ok(
  not has_table_privilege(
    'authenticated',
    'private.workout_template_loads',
    'select'
  ),
  'authenticated athletes cannot select hidden planned load'
);

insert into phase_5_tap_results (result) select ok(
  not has_table_privilege(
    'service_role',
    'private.workout_template_loads',
    'select'
  ),
  'the service role has no direct hidden-load table access'
);

insert into phase_5_tap_results (result) select ok(
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
insert into phase_5_tap_results (result) select is(
  (
    select count(*)
    from public.get_workout_catalog_for_planning()
  ),
  171::bigint,
  'the trusted planning RPC returns every immutable version with hidden load'
);
reset role;

insert into phase_5_tap_results (result) select ok(
  has_table_privilege('authenticated', 'public.workout_templates', 'select')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'insert')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'update')
  and not has_table_privilege('authenticated', 'public.workout_templates', 'delete'),
  'authenticated athletes have read-only catalog privileges'
);

set local role anon;
insert into phase_5_tap_results (result) select throws_ok(
  $$select count(*) from public.workout_templates$$,
  '42501',
  'permission denied for table workout_templates',
  'anonymous clients cannot read the catalog'
);
reset role;

set local role authenticated;
insert into phase_5_tap_results (result) select is(
  (select count(*) from public.workout_templates),
  171::bigint,
  'authenticated clients can read public catalog fields'
);
reset role;

insert into phase_5_tap_results (result)
select * from finish();
select result from phase_5_tap_results order by sequence;
rollback;
