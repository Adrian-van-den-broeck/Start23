-- Repair the START23 v0.1 catalog text that was mangled during import.
--
-- backend/scripts/generate_source_catalog_payload.py joins names and block
-- instructions with ' · ' (U+00B7), but migration 20260903074359 stored every
-- one of those separators as the replacement character U+FFFD. Athletes see
-- names such as 'BIK-012 <U+FFFD> Techniek'. Planning ruleset v2 copied the same text
-- into the version 2 templates, and planned workouts copied it into their
-- snapshots.
--
-- Product owner decision (2026-11-22): repair the stored text in place instead
-- of hiding it in clients. This is a text-only correction. It replaces U+FFFD
-- with U+00B7 and changes nothing else: template ids and versions, measures,
-- intensity, zone requirements, private load, ruleset provenance and planning
-- fingerprints (built from ids and dates, never from text) stay exactly as they
-- were. 20260903074359 is not rewritten.
--
-- The catalog immutability triggers and the planned-workout RPC guard are lifted
-- only for the statements below and restored before the migration ends.

alter table public.workout_templates disable trigger workout_templates_are_immutable;
alter table public.workout_segments disable trigger workout_segments_are_immutable;

update public.workout_templates
set name = replace(name, chr(65533), chr(183)),
    description = replace(description, chr(65533), chr(183))
where source_catalog = 'start23-v0.1'
  and (strpos(name, chr(65533)) > 0 or strpos(coalesce(description, ''), chr(65533)) > 0);

update public.workout_segments segment
set instructions = replace(segment.instructions, chr(65533), chr(183))
from public.workout_templates template
where template.id = segment.template_id
  and template.source_catalog = 'start23-v0.1'
  and strpos(coalesce(segment.instructions, ''), chr(65533)) > 0;

alter table public.workout_templates enable trigger workout_templates_are_immutable;
alter table public.workout_segments enable trigger workout_segments_are_immutable;

select set_config('start23.critical_write', 'on', true);

update public.planned_workouts workout
set name = replace(workout.name, chr(65533), chr(183)),
    description = replace(workout.description, chr(65533), chr(183)),
    segments = replace(workout.segments::text, chr(65533), chr(183))::jsonb
from public.workout_templates template
where template.id = workout.template_id
  and template.source_catalog = 'start23-v0.1'
  and (
    strpos(workout.name, chr(65533)) > 0
    or strpos(coalesce(workout.description, ''), chr(65533)) > 0
    or strpos(workout.segments::text, chr(65533)) > 0
  );

select set_config('start23.critical_write', '', true);

-- Fail the migration rather than leave a partial repair behind.
do $$
begin
  if exists (
    select 1 from public.workout_templates
    where strpos(name || coalesce(description, ''), chr(65533)) > 0
  ) or exists (
    select 1 from public.workout_segments
    where strpos(coalesce(instructions, ''), chr(65533)) > 0
  ) or exists (
    select 1 from public.planned_workouts
    where strpos(name || coalesce(description, '') || segments::text, chr(65533)) > 0
  ) then
    raise exception 'source catalog separator repair left U+FFFD behind';
  end if;
end;
$$;
