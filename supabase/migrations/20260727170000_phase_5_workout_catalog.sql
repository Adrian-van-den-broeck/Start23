-- Phase 5: immutable workout catalog with server-private planned load.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table public.workout_templates (
  id uuid primary key,
  template_key uuid not null,
  version integer not null check (version > 0),
  discipline text not null check (discipline in ('swim', 'bike', 'run')),
  name text not null check (length(btrim(name)) between 1 and 120),
  description text not null check (length(btrim(description)) between 1 and 1000),
  duration_minutes numeric not null check (duration_minutes > 0),
  distance_meters integer check (distance_meters > 0),
  intensity_bucket text not null check (intensity_bucket in ('low', 'high')),
  expected_rpe_min smallint not null check (expected_rpe_min between 1 and 10),
  expected_rpe_max smallint not null check (
    expected_rpe_max between expected_rpe_min and 10
  ),
  fallback_compatibility text not null check (
    fallback_compatibility in ('compatible', 'incompatible')
  ),
  created_at timestamptz not null default now(),
  unique (template_key, version)
);

create table public.workout_segments (
  template_id uuid not null references public.workout_templates(id),
  sequence integer not null check (sequence > 0),
  name text not null check (length(btrim(name)) between 1 and 120),
  instructions text not null check (length(btrim(instructions)) between 1 and 1000),
  duration_minutes numeric not null check (duration_minutes > 0),
  distance_meters integer check (distance_meters > 0),
  zone_number smallint not null check (zone_number between 1 and 5),
  expected_rpe smallint not null check (expected_rpe between 1 and 10),
  is_swim_technique boolean not null default false,
  primary key (template_id, sequence),
  check (not is_swim_technique or zone_number in (1, 2))
);

create table public.workout_template_phase_tags (
  template_id uuid not null references public.workout_templates(id),
  phase text not null check (phase in ('base', 'build', 'recovery', 'taper')),
  primary key (template_id, phase)
);

create table public.workout_template_zone_requirements (
  template_id uuid not null references public.workout_templates(id),
  requirement text not null check (requirement in ('heart_rate', 'pace', 'power')),
  primary key (template_id, requirement)
);

create table private.workout_template_loads (
  template_id uuid primary key references public.workout_templates(id),
  planned_tss numeric not null check (planned_tss >= 0),
  calculation_method text not null check (
    calculation_method = 'expected_rpe_midpoint_times_duration_hours'
  ),
  ruleset_version text not null check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

comment on table private.workout_template_loads is
  'Server-private planned load. Never expose through an athlete-facing model.';
comment on column private.workout_template_loads.planned_tss is
  'Internal planned TSS; prohibited from public APIs and direct athlete access.';

create or replace function private.reject_catalog_mutation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  raise exception 'workout catalog versions are immutable'
    using errcode = '55000';
end;
$$;

revoke all on function private.reject_catalog_mutation() from public;

create trigger workout_templates_are_immutable
before update or delete on public.workout_templates
for each row execute function private.reject_catalog_mutation();
create trigger workout_segments_are_immutable
before update or delete on public.workout_segments
for each row execute function private.reject_catalog_mutation();
create trigger workout_phase_tags_are_immutable
before update or delete on public.workout_template_phase_tags
for each row execute function private.reject_catalog_mutation();
create trigger workout_zone_requirements_are_immutable
before update or delete on public.workout_template_zone_requirements
for each row execute function private.reject_catalog_mutation();
create trigger workout_loads_are_immutable
before update or delete on private.workout_template_loads
for each row execute function private.reject_catalog_mutation();

create or replace function private.validate_workout_template(p_template_id uuid)
returns void
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_template public.workout_templates%rowtype;
  v_duration numeric;
  v_distance integer;
  v_segment_count integer;
  v_low_duration numeric;
  v_high_duration numeric;
begin
  select * into strict v_template
  from public.workout_templates
  where id = p_template_id;

  select
    count(*),
    sum(duration_minutes),
    sum(coalesce(distance_meters, 0)),
    sum(duration_minutes) filter (
      where is_swim_technique or zone_number in (1, 2)
    ),
    sum(duration_minutes) filter (
      where not is_swim_technique and zone_number in (3, 4, 5)
    )
  into
    v_segment_count,
    v_duration,
    v_distance,
    v_low_duration,
    v_high_duration
  from public.workout_segments
  where template_id = p_template_id;

  if v_segment_count = 0
    or v_duration <> v_template.duration_minutes
    or coalesce(v_distance, 0) <> coalesce(v_template.distance_meters, 0)
    or exists (
      select 1
      from generate_series(1, v_segment_count) expected(sequence)
      left join public.workout_segments segment
        on segment.template_id = p_template_id
        and segment.sequence = expected.sequence
      where segment.sequence is null
    )
    or exists (
      select 1
      from public.workout_segments
      where template_id = p_template_id
        and expected_rpe not between
          v_template.expected_rpe_min and v_template.expected_rpe_max
    )
    or (
      v_template.discipline <> 'swim'
      and exists (
        select 1 from public.workout_segments
        where template_id = p_template_id and is_swim_technique
      )
    )
    or (
      case
        when coalesce(v_high_duration, 0) > coalesce(v_low_duration, 0)
          then 'high'
        when coalesce(v_low_duration, 0) > coalesce(v_high_duration, 0)
          then 'low'
        else 'unresolved'
      end
    ) <> v_template.intensity_bucket
    or not exists (
      select 1 from public.workout_template_phase_tags
      where template_id = p_template_id
    )
    or not exists (
      select 1 from private.workout_template_loads
      where template_id = p_template_id
    )
    or (
      v_template.fallback_compatibility = 'compatible'
      and exists (
        select 1 from public.workout_template_zone_requirements
        where template_id = p_template_id and requirement <> 'heart_rate'
      )
    )
  then
    raise exception 'workout template % is incomplete or inconsistent', p_template_id
      using errcode = '23514';
  end if;
end;
$$;

revoke all on function private.validate_workout_template(uuid) from public;

alter table public.workout_templates enable row level security;
alter table public.workout_templates force row level security;
alter table public.workout_segments enable row level security;
alter table public.workout_segments force row level security;
alter table public.workout_template_phase_tags enable row level security;
alter table public.workout_template_phase_tags force row level security;
alter table public.workout_template_zone_requirements enable row level security;
alter table public.workout_template_zone_requirements force row level security;

create policy workout_templates_authenticated_read
on public.workout_templates for select to authenticated
using (true);
create policy workout_segments_authenticated_read
on public.workout_segments for select to authenticated
using (true);
create policy workout_phase_tags_authenticated_read
on public.workout_template_phase_tags for select to authenticated
using (true);
create policy workout_zone_requirements_authenticated_read
on public.workout_template_zone_requirements for select to authenticated
using (true);

revoke all on table public.workout_templates from public, anon, authenticated;
revoke all on table public.workout_segments from public, anon, authenticated;
revoke all on table public.workout_template_phase_tags
from public, anon, authenticated;
revoke all on table public.workout_template_zone_requirements
from public, anon, authenticated;
revoke all on table private.workout_template_loads
from public, anon, authenticated, service_role;
grant select on table public.workout_templates to authenticated;
grant select on table public.workout_segments to authenticated;
grant select on table public.workout_template_phase_tags to authenticated;
grant select on table public.workout_template_zone_requirements to authenticated;

create function public.get_workout_catalog_for_planning()
returns table (
  id uuid,
  template_key uuid,
  version integer,
  discipline text,
  name text,
  description text,
  duration_minutes numeric,
  distance_meters integer,
  intensity_bucket text,
  expected_rpe_min smallint,
  expected_rpe_max smallint,
  fallback_compatibility text,
  training_phases text[],
  zone_requirements text[],
  segments jsonb,
  planned_tss numeric,
  calculation_method text,
  ruleset_version text
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;

  return query
  select
    template.id,
    template.template_key,
    template.version,
    template.discipline,
    template.name,
    template.description,
    template.duration_minutes,
    template.distance_meters,
    template.intensity_bucket,
    template.expected_rpe_min,
    template.expected_rpe_max,
    template.fallback_compatibility,
    array(
      select tag.phase
      from public.workout_template_phase_tags tag
      where tag.template_id = template.id
      order by tag.phase
    ),
    array(
      select requirement.requirement
      from public.workout_template_zone_requirements requirement
      where requirement.template_id = template.id
      order by requirement.requirement
    ),
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'sequence', segment.sequence,
            'name', segment.name,
            'instructions', segment.instructions,
            'duration_minutes', segment.duration_minutes,
            'distance_meters', segment.distance_meters,
            'zone_number', segment.zone_number,
            'expected_rpe', segment.expected_rpe,
            'is_swim_technique', segment.is_swim_technique
          )
          order by segment.sequence
        ),
        '[]'::jsonb
      )
      from public.workout_segments segment
      where segment.template_id = template.id
    ),
    load.planned_tss,
    load.calculation_method,
    load.ruleset_version
  from public.workout_templates template
  join private.workout_template_loads load
    on load.template_id = template.id
  order by template.template_key, template.version;
end;
$$;

revoke all on function public.get_workout_catalog_for_planning()
from public, anon, authenticated;
grant execute on function public.get_workout_catalog_for_planning()
to service_role;

insert into public.workout_templates (
  id, template_key, version, discipline, name, description,
  duration_minutes, distance_meters, intensity_bucket,
  expected_rpe_min, expected_rpe_max, fallback_compatibility
)
values
  ('51000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 1, 'swim', 'Technique foundation', 'Relaxed technique work with an aerobic finish.', 40, 1600, 'low', 2, 3, 'incompatible'),
  ('51000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', 1, 'swim', 'Threshold repeats', 'Controlled threshold blocks with easy swimming around them.', 50, 2000, 'high', 2, 8, 'incompatible'),
  ('51000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', 1, 'bike', 'Aerobic endurance', 'Steady low-intensity endurance ride.', 60, null, 'low', 2, 4, 'compatible'),
  ('51000000-0000-0000-0000-000000000004', '50000000-0000-0000-0000-000000000004', 1, 'bike', 'Power intervals', 'High-intensity bike intervals guided by power.', 50, null, 'high', 2, 8, 'incompatible'),
  ('51000000-0000-0000-0000-000000000005', '50000000-0000-0000-0000-000000000005', 1, 'run', 'Easy aerobic run', 'Comfortable aerobic running with a relaxed finish.', 40, null, 'low', 2, 4, 'compatible'),
  ('51000000-0000-0000-0000-000000000006', '50000000-0000-0000-0000-000000000006', 1, 'run', 'Tempo intervals', 'Structured high-intensity running with easy bookends.', 45, null, 'high', 2, 8, 'incompatible'),
  ('52000000-0000-0000-0000-000000000005', '50000000-0000-0000-0000-000000000005', 2, 'run', 'Easy aerobic run', 'Comfortable aerobic running with a longer steady middle.', 45, null, 'low', 2, 4, 'compatible');

insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique
)
values
  ('51000000-0000-0000-0000-000000000001', 1, 'Easy warm-up', 'Complete easy warm-up in Zone 1.', 10, 400, 1, 2, true),
  ('51000000-0000-0000-0000-000000000001', 2, 'Technique drills', 'Complete technique drills in Zone 2.', 20, 800, 2, 3, true),
  ('51000000-0000-0000-0000-000000000001', 3, 'Aerobic finish', 'Complete aerobic finish in Zone 2.', 10, 400, 2, 3, false),
  ('51000000-0000-0000-0000-000000000002', 1, 'Warm-up', 'Complete warm-up in Zone 2.', 10, 400, 2, 3, false),
  ('51000000-0000-0000-0000-000000000002', 2, 'Threshold repeats', 'Complete threshold repeats in Zone 4.', 30, 1200, 4, 8, false),
  ('51000000-0000-0000-0000-000000000002', 3, 'Cool-down', 'Complete cool-down in Zone 1.', 10, 400, 1, 2, false),
  ('51000000-0000-0000-0000-000000000003', 1, 'Easy roll-out', 'Complete easy roll-out in Zone 1.', 10, null, 1, 2, false),
  ('51000000-0000-0000-0000-000000000003', 2, 'Endurance riding', 'Complete endurance riding in Zone 2.', 40, null, 2, 4, false),
  ('51000000-0000-0000-0000-000000000003', 3, 'Easy finish', 'Complete easy finish in Zone 1.', 10, null, 1, 2, false),
  ('51000000-0000-0000-0000-000000000004', 1, 'Warm-up', 'Complete warm-up in Zone 2.', 10, null, 2, 3, false),
  ('51000000-0000-0000-0000-000000000004', 2, 'Power intervals', 'Complete power intervals in Zone 4.', 30, null, 4, 8, false),
  ('51000000-0000-0000-0000-000000000004', 3, 'Cool-down', 'Complete cool-down in Zone 1.', 10, null, 1, 2, false),
  ('51000000-0000-0000-0000-000000000005', 1, 'Easy start', 'Complete easy start in Zone 1.', 10, null, 1, 2, false),
  ('51000000-0000-0000-0000-000000000005', 2, 'Aerobic running', 'Complete aerobic running in Zone 2.', 25, null, 2, 4, false),
  ('51000000-0000-0000-0000-000000000005', 3, 'Relaxed finish', 'Complete relaxed finish in Zone 1.', 5, null, 1, 2, false),
  ('51000000-0000-0000-0000-000000000006', 1, 'Warm-up', 'Complete warm-up in Zone 2.', 10, null, 2, 3, false),
  ('51000000-0000-0000-0000-000000000006', 2, 'Tempo intervals', 'Complete tempo intervals in Zone 4.', 25, null, 4, 8, false),
  ('51000000-0000-0000-0000-000000000006', 3, 'Cool-down', 'Complete cool-down in Zone 1.', 10, null, 1, 2, false),
  ('52000000-0000-0000-0000-000000000005', 1, 'Easy start', 'Complete easy start in Zone 1.', 10, null, 1, 2, false),
  ('52000000-0000-0000-0000-000000000005', 2, 'Aerobic running', 'Complete aerobic running in Zone 2.', 30, null, 2, 4, false),
  ('52000000-0000-0000-0000-000000000005', 3, 'Relaxed finish', 'Complete relaxed finish in Zone 1.', 5, null, 1, 2, false);

insert into public.workout_template_phase_tags (template_id, phase)
values
  ('51000000-0000-0000-0000-000000000001', 'base'),
  ('51000000-0000-0000-0000-000000000001', 'recovery'),
  ('51000000-0000-0000-0000-000000000002', 'build'),
  ('51000000-0000-0000-0000-000000000003', 'base'),
  ('51000000-0000-0000-0000-000000000003', 'build'),
  ('51000000-0000-0000-0000-000000000003', 'recovery'),
  ('51000000-0000-0000-0000-000000000004', 'build'),
  ('51000000-0000-0000-0000-000000000005', 'base'),
  ('51000000-0000-0000-0000-000000000005', 'recovery'),
  ('51000000-0000-0000-0000-000000000005', 'taper'),
  ('51000000-0000-0000-0000-000000000006', 'build'),
  ('52000000-0000-0000-0000-000000000005', 'base'),
  ('52000000-0000-0000-0000-000000000005', 'recovery'),
  ('52000000-0000-0000-0000-000000000005', 'taper');

insert into public.workout_template_zone_requirements (template_id, requirement)
values
  ('51000000-0000-0000-0000-000000000001', 'pace'),
  ('51000000-0000-0000-0000-000000000002', 'pace'),
  ('51000000-0000-0000-0000-000000000003', 'heart_rate'),
  ('51000000-0000-0000-0000-000000000004', 'power'),
  ('51000000-0000-0000-0000-000000000005', 'heart_rate'),
  ('51000000-0000-0000-0000-000000000006', 'pace'),
  ('52000000-0000-0000-0000-000000000005', 'heart_rate');

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
)
values
  ('51000000-0000-0000-0000-000000000001', 1.666666666666666666666666667, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('51000000-0000-0000-0000-000000000002', 4.166666666666666666666666667, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('51000000-0000-0000-0000-000000000003', 3, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('51000000-0000-0000-0000-000000000004', 4.166666666666666666666666667, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('51000000-0000-0000-0000-000000000005', 2, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('51000000-0000-0000-0000-000000000006', 3.75, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2'),
  ('52000000-0000-0000-0000-000000000005', 2.25, 'expected_rpe_midpoint_times_duration_hours', 'phase-3-ruleset-2');

do $$
declare
  template record;
begin
  for template in select id from public.workout_templates loop
    perform private.validate_workout_template(template.id);
  end loop;
end;
$$;
