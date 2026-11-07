-- Exercise the real ordered segment triggers without creating a plan fixture.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(3);
create temporary table v6_segment_probe (
  template_id uuid, athlete_id uuid, revision_id uuid, discipline text, segments jsonb
);
create trigger planned_workouts_set_segment_targets before insert on v6_segment_probe
for each row execute function private.set_planned_workout_segment_targets();
create trigger v6_set_planned_workout_segments before insert on v6_segment_probe
for each row execute function private.set_v6_planned_workout_segments();
insert into v6_segment_probe(template_id, discipline, segments)
select template_id, public_snapshot ->> 'discipline', '[{"tampered":true}]'::jsonb
from private.v6_source_revisions;
select is((select count(*) from v6_segment_probe), 77::bigint,
  'every inactive revision survives the real historical segment trigger');
select ok(not exists (
  select 1 from v6_segment_probe p join private.v6_source_revisions s using(template_id)
  where p.segments is distinct from s.public_snapshot -> 'segments'
), 'canonical immutable source segments replace arbitrary caller segments');
select ok(not has_function_privilege('authenticated',
  'private.set_v6_planned_workout_segments()', 'execute'),
  'source-reading trigger has no athlete execute grant');
select * from finish();
rollback;
