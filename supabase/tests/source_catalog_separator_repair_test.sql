begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(7);

select is(
  (select count(*) from public.workout_templates
   where strpos(name || coalesce(description, ''), chr(65533)) > 0),
  0::bigint,
  'no catalog template name or description keeps a replacement character'
);
select is(
  (select count(*) from public.workout_segments
   where strpos(coalesce(instructions, ''), chr(65533)) > 0),
  0::bigint,
  'no catalog block instruction keeps a replacement character'
);
select is(
  (select count(*) from public.planned_workouts
   where strpos(name || coalesce(description, '') || segments::text, chr(65533)) > 0),
  0::bigint,
  'no planned workout snapshot keeps a replacement character'
);
select is(
  (select count(distinct name) from public.workout_templates where source_workout_id = 'BIK-012'),
  1::bigint,
  'both catalog versions of BIK-012 carry the same repaired name'
);
select is(
  (select min(name) from public.workout_templates where source_workout_id = 'BIK-012'),
  'BIK-012 ' || chr(183) || ' Techniek',
  'source names use the generator middle dot separator'
);
select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1' and version in (1, 2)),
  308::bigint,
  'the repair keeps every catalog version and creates none'
);
select is(
  (select count(*) from pg_trigger
   where tgname in ('workout_templates_are_immutable', 'workout_segments_are_immutable')
     and tgenabled = 'O'),
  2::bigint,
  'catalog immutability triggers are enabled again'
);

select * from finish();
rollback;
