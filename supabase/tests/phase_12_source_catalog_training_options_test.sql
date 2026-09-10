begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(12);

select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1'),
  154::bigint,
  'all time- or distance-driven source workouts are imported'
);

select results_eq(
  $$
    select discipline, count(*)::bigint
    from public.workout_templates
    where source_catalog = 'start23-v0.1'
    group by discipline
    order by discipline
  $$,
  $$
    values ('bike'::text, 50::bigint),
           ('run'::text, 50::bigint),
           ('swim'::text, 54::bigint)
  $$,
  'the import preserves all bike, run, and swim rows'
);

select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1' and discipline = 'swim'),
  54::bigint,
  'all distance-driven swim rows are available'
);

select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1'
     and discipline = 'swim'
     and duration_minutes is null
     and distance_meters > 0),
  54::bigint,
  'swim templates retain distance and do not receive an inferred duration'
);

select is(
  (select count(*)
   from public.workout_templates template
   where template.source_catalog = 'start23-v0.1'
     and template.discipline = 'swim'
     and template.distance_meters = (
       select sum(segment.distance_meters)
       from public.workout_segments segment
       where segment.template_id = template.id
         and segment.duration_minutes is null
     )),
  54::bigint,
  'each swim distance equals the sum of its distance-driven segments'
);

select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1' and athlete_selection_only),
  154::bigint,
  'source workouts are explicit athlete choices only'
);

select is(
  (select count(distinct source_workout_id) from public.workout_templates
   where source_catalog = 'start23-v0.1'),
  154::bigint,
  'source workout identifiers remain unique and attributable'
);

select lives_ok(
  $$
    select private.validate_workout_template(id)
    from public.workout_templates
    where source_catalog = 'start23-v0.1'
  $$,
  'every imported template passes aggregate catalog validation'
);

select is(
  (select count(*) from private.workout_template_loads load
   join public.workout_templates template on template.id = load.template_id
   where template.source_catalog = 'start23-v0.1'
     and load.calculation_method = 'source_catalog_predefined_tss'),
  154::bigint,
  'predefined source load stays in the private catalog boundary'
);

select ok(
  has_function_privilege(
    'service_role', 'public.get_workout_catalog_for_planning()', 'execute'
  ),
  'the backend service can read the enlarged private planning catalog'
);

select ok(
  not has_function_privilege(
    'authenticated', 'public.get_workout_catalog_for_planning()', 'execute'
  ),
  'athletes cannot call the private-load planning catalog RPC'
);

select ok(
  not has_table_privilege(
    'authenticated', 'private.workout_template_loads', 'select'
  ),
  'source planned load remains inaccessible to the mobile role'
);

select * from finish();
rollback;
