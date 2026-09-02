-- MVP feedback: remove swim-technique planning and use reviewed triathlon RPE zones.

insert into public.workout_templates (
  id, template_key, version, discipline, name, description,
  duration_minutes, distance_meters, intensity_bucket,
  expected_rpe_min, expected_rpe_max, fallback_compatibility
)
values (
  '52000000-0000-0000-0000-000000000001',
  '50000000-0000-0000-0000-000000000001',
  2, 'swim', 'Aerobic swim',
  'Relaxed continuous swimming for aerobic endurance.',
  40, 1600, 'low', 2, 4, 'incompatible'
);

insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique
)
values
  ('52000000-0000-0000-0000-000000000001', 1, 'Easy warm-up', 'Complete easy warm-up in Zone 1.', 10, 400, 1, 2, false),
  ('52000000-0000-0000-0000-000000000001', 2, 'Aerobic swimming', 'Complete aerobic swimming in Zone 2.', 20, 800, 2, 4, false),
  ('52000000-0000-0000-0000-000000000001', 3, 'Easy finish', 'Complete easy finish in Zone 1.', 10, 400, 1, 2, false);

insert into public.workout_template_phase_tags (template_id, phase)
values
  ('52000000-0000-0000-0000-000000000001', 'base'),
  ('52000000-0000-0000-0000-000000000001', 'recovery');

insert into public.workout_template_zone_requirements (template_id, requirement)
values ('52000000-0000-0000-0000-000000000001', 'pace');

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
)
values (
  '52000000-0000-0000-0000-000000000001', 2,
  'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'
);

-- Preserve existing protocol versions and add canonical-RPE successors.
with successors(old_id, new_id) as (
  values
    ('54000000-0000-0000-0000-000000000008'::uuid, '56000000-0000-0000-0000-000000000008'::uuid),
    ('55000000-0000-0000-0000-000000000009'::uuid, '56000000-0000-0000-0000-000000000009'::uuid),
    ('55000000-0000-0000-0000-000000000010'::uuid, '56000000-0000-0000-0000-000000000010'::uuid),
    ('55000000-0000-0000-0000-000000000011'::uuid, '56000000-0000-0000-0000-000000000011'::uuid)
)
insert into public.workout_templates (
  id, template_key, version, discipline, name, description,
  duration_minutes, distance_meters, intensity_bucket,
  expected_rpe_min, expected_rpe_max, fallback_compatibility,
  explicit_scheduling_only
)
select
  successor.new_id, template.template_key, template.version + 1,
  template.discipline, template.name, template.description,
  template.duration_minutes, template.distance_meters, template.intensity_bucket,
  2, case when template.intensity_bucket = 'high' then 8 else 6 end,
  template.fallback_compatibility, template.explicit_scheduling_only
from successors successor
join public.workout_templates template on template.id = successor.old_id;

with successors(old_id, new_id) as (
  values
    ('54000000-0000-0000-0000-000000000008'::uuid, '56000000-0000-0000-0000-000000000008'::uuid),
    ('55000000-0000-0000-0000-000000000009'::uuid, '56000000-0000-0000-0000-000000000009'::uuid),
    ('55000000-0000-0000-0000-000000000010'::uuid, '56000000-0000-0000-0000-000000000010'::uuid),
    ('55000000-0000-0000-0000-000000000011'::uuid, '56000000-0000-0000-0000-000000000011'::uuid)
), normalized as (
  select
    successor.new_id as template_id,
    segment.sequence,
    segment.name,
    segment.instructions,
    segment.duration_minutes,
    segment.distance_meters,
    segment.expected_rpe,
    segment.protocol_target,
    case
      when (segment.protocol_target ->> 'target_rpe_min')::integer = 3 then 2
      when segment.expected_rpe <= 3 then 1
      when segment.expected_rpe <= 6 then 3
      when segment.expected_rpe <= 8 then 4
      else 5
    end as rpe_zone
  from successors successor
  join public.workout_segments segment on segment.template_id = successor.old_id
)
insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique,
  protocol_target
)
select
  template_id, sequence, name,
  instructions || ' Zone ' || rpe_zone::text || ' · RPE ' ||
    case rpe_zone when 1 then '2-3' when 2 then '4' when 3 then '5-6'
      when 4 then '7-8' else '9-10' end || '.',
  duration_minutes, distance_meters, null,
  case rpe_zone when 1 then 2 when 2 then 4 when 3 then 5
    when 4 then 8 else 9 end,
  false,
  jsonb_set(
    jsonb_set(
      protocol_target,
      '{target_rpe_min}',
      to_jsonb(case rpe_zone when 1 then 2 when 2 then 4 when 3 then 5 when 4 then 7 else 9 end)
    ),
    '{target_rpe_max}',
    to_jsonb(case rpe_zone when 1 then 3 when 2 then 4 when 3 then 6 when 4 then 8 else 10 end)
  )
from normalized;

with successors(old_id, new_id) as (
  values
    ('54000000-0000-0000-0000-000000000008'::uuid, '56000000-0000-0000-0000-000000000008'::uuid),
    ('55000000-0000-0000-0000-000000000009'::uuid, '56000000-0000-0000-0000-000000000009'::uuid),
    ('55000000-0000-0000-0000-000000000010'::uuid, '56000000-0000-0000-0000-000000000010'::uuid),
    ('55000000-0000-0000-0000-000000000011'::uuid, '56000000-0000-0000-0000-000000000011'::uuid)
)
insert into public.workout_template_phase_tags (template_id, phase)
select successor.new_id, tag.phase
from successors successor
join public.workout_template_phase_tags tag on tag.template_id = successor.old_id;

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
)
values
  ('56000000-0000-0000-0000-000000000008', 3.666666666666666666666666667, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('56000000-0000-0000-0000-000000000009', 4.583333333333333333333333333, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('56000000-0000-0000-0000-000000000010', 5, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('56000000-0000-0000-0000-000000000011', 4.166666666666666666666666667, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2');

select private.validate_workout_template('52000000-0000-0000-0000-000000000001');
select private.validate_workout_template('56000000-0000-0000-0000-000000000008');
select private.validate_workout_template('56000000-0000-0000-0000-000000000009');
select private.validate_workout_template('56000000-0000-0000-0000-000000000010');
select private.validate_workout_template('56000000-0000-0000-0000-000000000011');

-- New RPE-only snapshots use the same five canonical ranges as the source workbook.
create or replace function private.set_planned_workout_segment_targets()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_rpe_guided boolean;
begin
  select
    setup.setup_route in ('field_test', 'calibration_week', 'rpe_only')
    and not exists (
      select 1 from public.zone_profile_versions profile
      where profile.athlete_id = new.athlete_id
        and profile.discipline = new.discipline
        and profile.status = 'active'
    )
  into v_rpe_guided
  from public.discipline_zone_setups setup
  where setup.athlete_id = new.athlete_id
    and setup.discipline = new.discipline;

  select jsonb_agg(
    jsonb_build_object(
      'sequence', segment.sequence,
      'name', segment.name,
      'instructions', case
        when coalesce(v_rpe_guided, false) and segment.protocol_target is null then
          segment.name || ': volg Zone ' || segment.zone_number::text || ' · RPE ' ||
          case segment.zone_number when 1 then '2-3' when 2 then '4'
            when 3 then '5-6' when 4 then '7-8' else '9-10' end ||
          '; gebruik geen onbevestigde numerieke zones.'
        else segment.instructions
      end,
      'duration_minutes', segment.duration_minutes,
      'distance_meters', segment.distance_meters,
      'zone_target', case when coalesce(v_rpe_guided, false) then null else segment.zone_number end,
      'protocol_target', segment.protocol_target,
      'rpe_target', case
        when coalesce(v_rpe_guided, false) and segment.protocol_target is null then
          jsonb_build_object(
            'target_rpe_min', case segment.zone_number when 1 then 2 when 2 then 4 when 3 then 5 when 4 then 7 else 9 end,
            'target_rpe_max', case segment.zone_number when 1 then 3 when 2 then 4 when 3 then 6 when 4 then 8 else 10 end,
            'intensity_bucket', case when segment.zone_number in (1, 2) then 'low' else 'high' end,
            'heart_rate_observation_required', true
          )
        else null
      end,
      'expected_rpe', case
        when coalesce(v_rpe_guided, false) and segment.protocol_target is null then
          case segment.zone_number when 1 then 2 when 2 then 4 when 3 then 5 when 4 then 8 else 9 end
        else segment.expected_rpe
      end,
      'is_swim_technique', segment.is_swim_technique
    ) order by segment.sequence
  ) into new.segments
  from public.workout_segments segment
  where segment.template_id = new.template_id;
  return new;
end;
$$;

revoke execute on function private.set_planned_workout_segment_targets()
from public, anon, authenticated, service_role;
