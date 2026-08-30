-- Phase 11: discipline test scheduling, RPE-guided plan snapshots, and
-- owner-visible immutable zone-profile history. Statistical UC-05 upgrades
-- remain intentionally absent until their thresholds are reviewed.

-- BR-003 already assigns exact low/high duration ties to high intensity. Keep
-- the durable catalog validator aligned with that deterministic ownership.
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
      where is_swim_technique
         or zone_number in (1, 2)
         or protocol_target ->> 'intensity_bucket' = 'low'
    ),
    sum(duration_minutes) filter (
      where not is_swim_technique
        and (
          zone_number in (3, 4, 5)
          or protocol_target ->> 'intensity_bucket' = 'high'
        )
    )
  into
    v_segment_count, v_duration, v_distance, v_low_duration, v_high_duration
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
      select 1 from public.workout_segments
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
        when coalesce(v_high_duration, 0) >= coalesce(v_low_duration, 0)
          and coalesce(v_high_duration, 0) > 0 then 'high'
        when coalesce(v_low_duration, 0) > coalesce(v_high_duration, 0) then 'low'
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

revoke all on function private.validate_workout_template(uuid)
from public, anon, authenticated, service_role;

-- A self-declared physician/lab source remains a pending calculated profile,
-- but its provenance must not be collapsed into ordinary athlete-entered data.
alter table public.zone_profile_versions
  drop constraint zone_profile_calculated_metadata_valid;
alter table public.zone_profile_versions
  add constraint zone_profile_calculated_metadata_valid
  check (
    setup_method <> 'calculated'
    or (
      zone_model_version = 'start23-zone-model-1.0'
      and source_quality in (
        'athlete_entered', 'measured_lab', 'reviewed_field_threshold'
      )
      and calculated_at is not null
      and review_status in (
        'pending_athlete_confirmation',
        'confirmed_by_athlete',
        'rejected_by_athlete'
      )
      and evidence_version = 'voorstel-start23-zone-1-5-rekenmodel-v1.0'
      and jsonb_array_length(metric_profiles) between 1 and 2
      and calculation_fingerprint is not null
      and review_reason = 'athlete_confirmation_required'
      and ruleset_version = 'start23-zone-model-1.0'
    )
  );

create function public.save_measured_calculated_zone_profile(
  p_athlete_id uuid,
  p_profile jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
  v_profile_id uuid;
  v_source_method text := p_profile ->> 'source_method';
  v_original_critical_write text :=
    current_setting('start23.critical_write', true);
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_profile ->> 'source_quality' <> 'measured_lab'
     or v_source_method <> 'physician_or_lab_reported'
     or nullif(p_profile ->> 'calibration_evaluation_id', '') is not null then
    raise exception 'measured zone provenance is inconsistent'
      using errcode = '23514';
  end if;

  v_result := public.save_calculated_zone_profile(
    p_athlete_id,
    p_profile || jsonb_build_object(
      'source_method', 'athlete_entered',
      'source_quality', 'athlete_entered'
    )
  );
  v_profile_id := (v_result ->> 'profile_id')::uuid;
  if v_profile_id is null then
    raise exception 'measured zone profile was not persisted'
      using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.zone_profile_versions
  set source_method = v_source_method, source_quality = 'measured_lab'
  where id = v_profile_id
    and athlete_id = p_athlete_id
    and setup_method = 'calculated'
    and status = 'pending';
  if not found then
    raise exception 'pending measured zone profile not found'
      using errcode = '40001';
  end if;
  perform set_config(
    'start23.critical_write',
    coalesce(v_original_critical_write, ''),
    true
  );
  return v_result;
end;
$$;

revoke all on function public.save_measured_calculated_zone_profile(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute
on function public.save_measured_calculated_zone_profile(uuid, jsonb)
to service_role;

-- Reviewed run and bike field tests have complete duration/RPE contracts and
-- can therefore participate in private-load planning. Swim CSS remains
-- standalone because its distance-only protocol has no approved planned
-- duration/private-load treatment.
insert into public.workout_templates (
  id, template_key, version, discipline, name, description, duration_minutes,
  distance_meters, intensity_bucket, expected_rpe_min, expected_rpe_max,
  fallback_compatibility
) values
(
  '55000000-0000-0000-0000-000000000009',
  '50000000-0000-0000-0000-000000000009',
  1, 'run', 'Loopdrempel 30-minuten veldtest',
  'Beoordeelde veldtest op protocol en RPE; alleen na expliciete dagkeuze.',
  60, null, 'high', 1, 9, 'incompatible'
),
(
  '55000000-0000-0000-0000-000000000010',
  '50000000-0000-0000-0000-000000000010',
  1, 'bike', 'Fiets FTP 30-minuten veldtest',
  'Beoordeelde vermogensveldtest; alleen na expliciete dagkeuze.',
  60, null, 'high', 1, 9, 'incompatible'
),
(
  '55000000-0000-0000-0000-000000000011',
  '50000000-0000-0000-0000-000000000011',
  1, 'bike', 'Fiets drempelhartslag veldtest',
  'Beoordeelde hartslagveldtest; alleen na expliciete dagkeuze.',
  50, null, 'low', 1, 9, 'incompatible'
);

insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique, protocol_target
) values
(
  '55000000-0000-0000-0000-000000000009', 1, 'Rustige opwarming',
  'Rustig lopen; volledige zinnen mogelijk.', 15, null, null, 2, false,
  '{"protocol_id":"start23_run_threshold_30min_v1","segment_id":"warmup","target_rpe_min":2,"target_rpe_max":3,"intensity_bucket":"low","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000009', 2, 'Korte versnellingen',
  'Korte gecontroleerde versnellingen; niet maximaal.', 5, null, null, 6, false,
  '{"protocol_id":"start23_run_threshold_30min_v1","segment_id":"strides","target_rpe_min":5,"target_rpe_max":7,"intensity_bucket":"high","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000009', 3, '30-minuten tijdrit',
  'Zo hard mogelijk maar gelijkmatig; geen sprintstart.', 30, null, null, 8, false,
  '{"protocol_id":"start23_run_threshold_30min_v1","segment_id":"test_30min","target_rpe_min":8,"target_rpe_max":9,"intensity_bucket":"high","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000009', 4, 'Uitlopen',
  'Zeer rustig uitlopen en sessie-RPE registreren.', 10, null, null, 1, false,
  '{"protocol_id":"start23_run_threshold_30min_v1","segment_id":"cooldown","target_rpe_min":1,"target_rpe_max":2,"intensity_bucket":"low","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000010', 1, 'Opwarming',
  'Rustig opbouwen met korte gecontroleerde versnellingen.', 20, null, null, 3, false,
  '{"protocol_id":"start23_bike_ftp_30min_v1","segment_id":"warmup","target_rpe_min":2,"target_rpe_max":4,"intensity_bucket":"low","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000010', 2, '30-minuten vermogenstest',
  'Zo hard mogelijk maar gelijkmatig; vermijd pieken en vrijloop.', 30, null, null, 8, false,
  '{"protocol_id":"start23_bike_ftp_30min_v1","segment_id":"test_30min","target_rpe_min":8,"target_rpe_max":9,"intensity_bucket":"high","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000010', 3, 'Cooling-down',
  'Zeer rustig uitfietsen en sessie-RPE registreren.', 10, null, null, 1, false,
  '{"protocol_id":"start23_bike_ftp_30min_v1","segment_id":"cooldown","target_rpe_min":1,"target_rpe_max":2,"intensity_bucket":"low","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000011', 1, 'Opwarming',
  'Rustig opbouwen met korte versnellingen.', 20, null, null, 3, false,
  '{"protocol_id":"start23_bike_fthr_20min_v1","segment_id":"warmup","target_rpe_min":2,"target_rpe_max":4,"intensity_bucket":"low","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000011', 2, '20-minuten tijdrit',
  'Gelijkmatige zware solo-inspanning; geen sprintstart.', 20, null, null, 8, false,
  '{"protocol_id":"start23_bike_fthr_20min_v1","segment_id":"test_20min","target_rpe_min":8,"target_rpe_max":9,"intensity_bucket":"high","optional":false}'
),
(
  '55000000-0000-0000-0000-000000000011', 3, 'Cooling-down',
  'Zeer rustig uitfietsen en sessie-RPE registreren.', 10, null, null, 1, false,
  '{"protocol_id":"start23_bike_fthr_20min_v1","segment_id":"cooldown","target_rpe_min":1,"target_rpe_max":2,"intensity_bucket":"low","optional":false}'
);

insert into public.workout_template_phase_tags (template_id, phase) values
('55000000-0000-0000-0000-000000000009', 'base'),
('55000000-0000-0000-0000-000000000009', 'build'),
('55000000-0000-0000-0000-000000000010', 'base'),
('55000000-0000-0000-0000-000000000010', 'build'),
('55000000-0000-0000-0000-000000000011', 'base'),
('55000000-0000-0000-0000-000000000011', 'build');

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
) values
(
  '55000000-0000-0000-0000-000000000009',
  5,
  'expected_rpe_midpoint_times_duration_hours',
  'phase-3-ruleset-3'
),
(
  '55000000-0000-0000-0000-000000000010',
  5,
  'expected_rpe_midpoint_times_duration_hours',
  'phase-3-ruleset-3'
),
(
  '55000000-0000-0000-0000-000000000011',
  4.166666666666666666666666667,
  'expected_rpe_midpoint_times_duration_hours',
  'phase-3-ruleset-3'
);

select private.validate_workout_template('55000000-0000-0000-0000-000000000009');
select private.validate_workout_template('55000000-0000-0000-0000-000000000010');
select private.validate_workout_template('55000000-0000-0000-0000-000000000011');

-- The catalog remains immutable. Only each owned planned-workout snapshot is
-- projected to RPE when the discipline has no active zone profile.
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
      select 1
      from public.zone_profile_versions profile
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
        when coalesce(v_rpe_guided, false) and segment.protocol_target is null
          then segment.name || ': volg RPE ' || segment.expected_rpe::text
            || '; gebruik geen onbevestigde numerieke zones.'
        else segment.instructions
      end,
      'duration_minutes', segment.duration_minutes,
      'distance_meters', segment.distance_meters,
      'zone_target', case
        when coalesce(v_rpe_guided, false) then null
        else segment.zone_number
      end,
      'protocol_target', segment.protocol_target,
      'rpe_target', case
        when coalesce(v_rpe_guided, false) and segment.protocol_target is null
          then jsonb_build_object(
            'target_rpe_min', segment.expected_rpe,
            'target_rpe_max', segment.expected_rpe,
            'intensity_bucket', case
              when segment.is_swim_technique or segment.zone_number in (1, 2)
                then 'low'
              else 'high'
            end,
            'heart_rate_observation_required', true
          )
        else null
      end,
      'expected_rpe', segment.expected_rpe,
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

-- Completed RPE-guided assigned workouts require an average-HR observation in
-- BPM. No reference is fabricated: tolerance assessment remains not_applicable
-- until trusted reviewed context supplies a reference value.
create or replace function public.get_activity_processing_context(
  p_athlete_id uuid,
  p_activity_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'duration_minutes', activity.duration_minutes,
    'processing_state', activity.processing_state,
    'rpe', activity.rpe,
    'discipline', activity.discipline,
    'average_heart_rate_bpm', metrics.average_heart_rate_bpm,
    'requires_heart_rate_observation', workout.id is not null and exists (
      select 1
      from jsonb_array_elements(workout.segments) segment
      where coalesce(
        (segment -> 'rpe_target' ->> 'heart_rate_observation_required')::boolean,
        false
      )
    ),
    'planned', case when workout.id is null then null else jsonb_build_object(
      'planned_tss', load.planned_tss,
      'expected_rpe_min', workout.expected_rpe_min,
      'expected_rpe_max', workout.expected_rpe_max,
      'intensity_bucket', workout.intensity_bucket
    ) end
  ) into v_result
  from public.activities activity
  left join public.activity_metrics metrics
    on metrics.activity_id = activity.id
   and metrics.athlete_id = activity.athlete_id
  left join public.planned_workouts workout
    on workout.id = activity.planned_workout_id
   and workout.athlete_id = activity.athlete_id
  left join private.planned_workout_loads load
    on load.planned_workout_id = workout.id
   and load.athlete_id = activity.athlete_id
  where activity.id = p_activity_id and activity.athlete_id = p_athlete_id;
  if v_result is null then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_activity_processing_context(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_activity_processing_context(uuid, uuid)
to service_role;

create function public.save_rpe_heart_rate_observation(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_average_heart_rate_bpm smallint
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_max_heart_rate_bpm smallint;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  if p_average_heart_rate_bpm not between 20 and 260 then
    raise exception 'invalid heart-rate observation' using errcode = '23514';
  end if;
  if not exists (
    select 1
    from public.activities activity
    where activity.id = p_activity_id
      and activity.athlete_id = p_athlete_id
  ) then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  select max_heart_rate_bpm into v_max_heart_rate_bpm
  from public.activity_metrics
  where activity_id = p_activity_id and athlete_id = p_athlete_id;
  if v_max_heart_rate_bpm is not null
     and p_average_heart_rate_bpm > v_max_heart_rate_bpm then
    raise exception 'average heart rate exceeds maximum' using errcode = '23514';
  end if;
  insert into public.activity_metrics (
    activity_id, athlete_id, average_heart_rate_bpm
  ) values (
    p_activity_id, p_athlete_id, p_average_heart_rate_bpm
  )
  on conflict (activity_id) do update
  set average_heart_rate_bpm = excluded.average_heart_rate_bpm;
end;
$$;

revoke all on function public.save_rpe_heart_rate_observation(uuid, uuid, smallint)
from public, anon, authenticated, service_role;
grant execute on function public.save_rpe_heart_rate_observation(uuid, uuid, smallint)
to service_role;

create table public.discipline_test_assignments (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  discipline text not null,
  protocol_id text not null,
  scheduling_mode text not null,
  scheduled_date date not null,
  state text not null default 'pending_approval',
  plan_id uuid,
  target_plan_revision_id uuid,
  plan_proposal_id uuid,
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  decided_at timestamptz,

  unique (id, athlete_id),
  foreign key (plan_id, athlete_id)
    references public.weekly_plans (id, athlete_id),
  foreign key (target_plan_revision_id, athlete_id)
    references public.plan_revisions (id, athlete_id),
  foreign key (plan_proposal_id, athlete_id)
    references public.change_proposals (id, athlete_id),
  constraint discipline_test_assignments_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint discipline_test_assignments_protocol_valid check (
    (discipline = 'swim' and protocol_id = 'start23_swim_css_400_200_v1')
    or (discipline = 'run' and protocol_id = 'start23_run_threshold_30min_v1')
    or (
      discipline = 'bike'
      and protocol_id in (
        'start23_bike_ftp_30min_v1', 'start23_bike_fthr_20min_v1'
      )
    )
  ),
  constraint discipline_test_assignments_mode_valid check (
    scheduling_mode in ('standalone', 'weekly_plan')
  ),
  constraint discipline_test_assignments_state_valid check (
    state in ('pending_approval', 'scheduled', 'completed', 'rejected', 'cancelled')
  ),
  constraint discipline_test_assignments_revision_positive check (revision > 0),
  constraint discipline_test_assignments_target_valid check (
    (
      scheduling_mode = 'standalone'
      and plan_id is null
      and target_plan_revision_id is null
      and plan_proposal_id is null
    )
    or (
      scheduling_mode = 'weekly_plan'
      and discipline <> 'swim'
      and plan_id is not null
      and target_plan_revision_id is not null
      and plan_proposal_id is not null
    )
  )
);

create index discipline_test_assignments_owner_date_idx
on public.discipline_test_assignments (athlete_id, scheduled_date desc);
create index discipline_test_assignments_plan_proposal_idx
on public.discipline_test_assignments (plan_proposal_id, athlete_id)
where plan_proposal_id is not null;
create unique index one_open_test_assignment_per_discipline
on public.discipline_test_assignments (athlete_id, discipline)
where state in ('pending_approval', 'scheduled');

create trigger discipline_test_assignments_require_rpc
before insert or update or delete on public.discipline_test_assignments
for each row execute function private.require_critical_write_context();

alter table public.discipline_test_assignments enable row level security;
alter table public.discipline_test_assignments force row level security;
revoke all on table public.discipline_test_assignments
from public, anon, authenticated, service_role;
grant select, insert, update on table public.discipline_test_assignments
to authenticated;

create policy discipline_test_assignments_select_own
on public.discipline_test_assignments for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy discipline_test_assignments_insert_own
on public.discipline_test_assignments for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy discipline_test_assignments_update_own
on public.discipline_test_assignments for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

alter table public.change_proposals
  add column target_test_assignment_id uuid,
  add column base_test_assignment_revision bigint;

alter table public.change_proposals
  drop constraint change_proposals_kind_valid,
  drop constraint change_proposals_typed_target_valid;

alter table public.change_proposals
  add constraint change_proposals_target_test_assignment_fkey
  foreign key (target_test_assignment_id, athlete_id)
  references public.discipline_test_assignments (id, athlete_id),
  add constraint change_proposals_kind_valid check (
    kind in ('zone_update', 'plan_revision', 'validation_test')
  ),
  add constraint change_proposals_typed_target_valid check (
    (
      kind = 'zone_update'
      and target_zone_profile_id is not null
      and target_plan_revision_id is null
      and target_test_assignment_id is null
      and base_plan_revision is null
      and base_test_assignment_revision is null
    )
    or (
      kind = 'plan_revision'
      and target_plan_revision_id is not null
      and target_zone_profile_id is null
      and target_test_assignment_id is null
      and base_zone_profile_id is null
      and base_plan_revision >= 0
      and base_test_assignment_revision is null
    )
    or (
      kind = 'validation_test'
      and target_test_assignment_id is not null
      and target_zone_profile_id is null
      and target_plan_revision_id is null
      and base_zone_profile_id is null
      and base_plan_revision is null
      and base_test_assignment_revision > 0
    )
  );

create unique index one_pending_proposal_per_test_assignment
on public.change_proposals (target_test_assignment_id)
where state = 'pending' and target_test_assignment_id is not null;

create function private.phase_11_test_protocol_matches(
  p_discipline text,
  p_protocol_id text
)
returns boolean
language sql
immutable
security invoker
set search_path = ''
as $$
  select
    (p_discipline = 'swim' and p_protocol_id = 'start23_swim_css_400_200_v1')
    or (p_discipline = 'run' and p_protocol_id = 'start23_run_threshold_30min_v1')
    or (
      p_discipline = 'bike'
      and p_protocol_id in (
        'start23_bike_ftp_30min_v1', 'start23_bike_fthr_20min_v1'
      )
    );
$$;

revoke execute on function private.phase_11_test_protocol_matches(text, text)
from public, anon, authenticated, service_role;

create function public.create_validation_test_proposal(p_assignment jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_discipline text := p_assignment ->> 'discipline';
  v_protocol_id text := p_assignment ->> 'protocol_id';
  v_scheduled_date date := (p_assignment ->> 'scheduled_date')::date;
  v_timezone text;
  v_assignment public.discipline_test_assignments;
  v_proposal public.change_proposals;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_assignment) <> 'object'
     or p_assignment ->> 'scheduling_mode' <> 'standalone'
     or not private.phase_11_test_protocol_matches(v_discipline, v_protocol_id)
     or p_assignment ?| array[
       'athlete_id', 'user_id', 'tss', 'planned_tss', 'realized_tss', 'load'
     ] then
    raise exception 'invalid validation test assignment' using errcode = '23514';
  end if;
  select profile.timezone into v_timezone
  from public.athlete_profiles profile
  where profile.athlete_id = v_athlete_id;
  if v_timezone is null
     or v_scheduled_date < (statement_timestamp() at time zone v_timezone)::date then
    raise exception 'test date is in the past' using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.discipline_zone_setups setup
    where setup.athlete_id = v_athlete_id
      and setup.discipline = v_discipline
      and setup.setup_route = 'field_test'
      and setup.protocol_id = v_protocol_id
  ) then
    raise exception 'field test setup is not current' using errcode = '40001';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':test:' || v_discipline, 0)
  );
  perform set_config('start23.critical_write', 'on', true);
  insert into public.discipline_test_assignments (
    athlete_id, discipline, protocol_id, scheduling_mode, scheduled_date
  ) values (
    v_athlete_id, v_discipline, v_protocol_id, 'standalone', v_scheduled_date
  ) returning * into v_assignment;

  insert into public.change_proposals (
    athlete_id, kind, target_test_assignment_id,
    base_test_assignment_revision, reason_codes, public_explanation,
    ruleset_version
  ) values (
    v_athlete_id, 'validation_test', v_assignment.id, v_assignment.revision,
    array['athlete_selected_validation_test'],
    'Een veldtest staat klaar op de gekozen lokale datum en wacht op bevestiging.',
    'phase-11-ruleset-1'
  ) returning * into v_proposal;

  return (to_jsonb(v_assignment) - 'athlete_id') || jsonb_build_object(
    'proposal_id', v_proposal.id,
    'proposal_state', v_proposal.state
  );
end;
$$;

revoke all on function public.create_validation_test_proposal(jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_validation_test_proposal(jsonb)
to authenticated;

create function public.save_integrated_test_assignment(p_assignment jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_assignment public.discipline_test_assignments;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_assignment) <> 'object'
     or p_assignment ->> 'scheduling_mode' <> 'weekly_plan'
     or p_assignment ->> 'discipline' = 'swim'
     or not private.phase_11_test_protocol_matches(
       p_assignment ->> 'discipline', p_assignment ->> 'protocol_id'
     ) then
    raise exception 'invalid integrated test assignment' using errcode = '23514';
  end if;
  if not exists (
    select 1
    from public.change_proposals proposal
    join public.plan_revisions revision
      on revision.id = proposal.target_plan_revision_id
     and revision.athlete_id = proposal.athlete_id
    join public.planned_workouts workout
      on workout.revision_id = revision.id
     and workout.athlete_id = revision.athlete_id
    where proposal.id = (p_assignment ->> 'plan_proposal_id')::uuid
      and proposal.athlete_id = v_athlete_id
      and proposal.kind = 'plan_revision'
      and proposal.state = 'pending'
      and revision.id = (p_assignment ->> 'target_plan_revision_id')::uuid
      and revision.plan_id = (p_assignment ->> 'plan_id')::uuid
      and workout.discipline = p_assignment ->> 'discipline'
      and workout.scheduled_date = (p_assignment ->> 'scheduled_date')::date
      and exists (
        select 1 from jsonb_array_elements(workout.segments) segment
        where segment -> 'protocol_target' ->> 'protocol_id'
          = p_assignment ->> 'protocol_id'
      )
  ) then
    raise exception 'pending plan test workout not found' using errcode = '40001';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(
      v_athlete_id::text || ':test:' || (p_assignment ->> 'discipline'), 0
    )
  );
  perform set_config('start23.critical_write', 'on', true);
  insert into public.discipline_test_assignments (
    athlete_id, discipline, protocol_id, scheduling_mode, scheduled_date,
    plan_id, target_plan_revision_id, plan_proposal_id
  ) values (
    v_athlete_id,
    p_assignment ->> 'discipline',
    p_assignment ->> 'protocol_id',
    'weekly_plan',
    (p_assignment ->> 'scheduled_date')::date,
    (p_assignment ->> 'plan_id')::uuid,
    (p_assignment ->> 'target_plan_revision_id')::uuid,
    (p_assignment ->> 'plan_proposal_id')::uuid
  ) returning * into v_assignment;
  return (to_jsonb(v_assignment) - 'athlete_id') || jsonb_build_object(
    'proposal_id', v_assignment.plan_proposal_id,
    'proposal_state', 'pending'
  );
end;
$$;

revoke all on function public.save_integrated_test_assignment(jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.save_integrated_test_assignment(jsonb)
to authenticated;

create function public.approve_validation_test_proposal(
  p_proposal_id uuid,
  p_expected_revision bigint
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_proposal public.change_proposals;
  v_assignment public.discipline_test_assignments;
begin
  select * into v_proposal from public.change_proposals
  where id = p_proposal_id and athlete_id = v_athlete_id
    and kind = 'validation_test' for update;
  if not found then
    raise exception 'validation test proposal not found' using errcode = 'P0002';
  end if;
  select * into v_assignment from public.discipline_test_assignments
  where id = v_proposal.target_test_assignment_id
    and athlete_id = v_athlete_id for update;
  if v_assignment.revision <> p_expected_revision
     or v_proposal.base_test_assignment_revision <> p_expected_revision then
    raise exception 'validation test proposal is stale' using errcode = '40001';
  end if;
  if v_proposal.state = 'applied' then
    return jsonb_build_object(
      'proposal_id', v_proposal.id, 'state', v_proposal.state,
      'test_assignment_id', v_assignment.id,
      'test_assignment_state', v_assignment.state
    );
  end if;
  if v_proposal.state <> 'pending' or v_assignment.state <> 'pending_approval' then
    raise exception 'validation test proposal is not pending' using errcode = '40001';
  end if;
  perform set_config('start23.critical_write', 'on', true);
  update public.discipline_test_assignments set
    state = 'scheduled', decided_at = statement_timestamp(),
    updated_at = statement_timestamp()
  where id = v_assignment.id;
  update public.change_proposals set
    state = 'applied', decision_actor = v_athlete_id,
    decided_at = statement_timestamp(), applied_at = statement_timestamp()
  where id = v_proposal.id;
  return jsonb_build_object(
    'proposal_id', v_proposal.id, 'state', 'applied',
    'test_assignment_id', v_assignment.id,
    'test_assignment_state', 'scheduled'
  );
end;
$$;

revoke all on function public.approve_validation_test_proposal(uuid, bigint)
from public, anon, authenticated, service_role;
grant execute on function public.approve_validation_test_proposal(uuid, bigint)
to authenticated;

create function public.reject_validation_test_proposal(p_proposal_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_proposal public.change_proposals;
begin
  select * into v_proposal from public.change_proposals
  where id = p_proposal_id and athlete_id = v_athlete_id
    and kind = 'validation_test' for update;
  if not found then
    raise exception 'validation test proposal not found' using errcode = 'P0002';
  end if;
  if v_proposal.state = 'rejected' then
    return jsonb_build_object(
      'proposal_id', v_proposal.id, 'state', 'rejected',
      'test_assignment_id', v_proposal.target_test_assignment_id,
      'test_assignment_state', 'rejected'
    );
  end if;
  if v_proposal.state <> 'pending' then
    raise exception 'validation test proposal is not pending' using errcode = '40001';
  end if;
  perform set_config('start23.critical_write', 'on', true);
  update public.discipline_test_assignments set
    state = 'rejected', decided_at = statement_timestamp(),
    updated_at = statement_timestamp()
  where id = v_proposal.target_test_assignment_id and athlete_id = v_athlete_id;
  update public.change_proposals set
    state = 'rejected', decision_actor = v_athlete_id,
    decided_at = statement_timestamp()
  where id = v_proposal.id;
  return jsonb_build_object(
    'proposal_id', v_proposal.id, 'state', 'rejected',
    'test_assignment_id', v_proposal.target_test_assignment_id,
    'test_assignment_state', 'rejected'
  );
end;
$$;

revoke all on function public.reject_validation_test_proposal(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.reject_validation_test_proposal(uuid)
to authenticated;

create function private.sync_integrated_test_assignment_state()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.kind = 'plan_revision' and new.state is distinct from old.state then
    perform set_config('start23.critical_write', 'on', true);
    update public.discipline_test_assignments set
      state = case
        when new.state = 'applied' then 'scheduled'
        when new.state in ('rejected', 'expired') then 'rejected'
        else state
      end,
      decided_at = case
        when new.state in ('applied', 'rejected', 'expired')
          then statement_timestamp()
        else decided_at
      end,
      updated_at = statement_timestamp()
    where plan_proposal_id = new.id
      and athlete_id = new.athlete_id
      and state = 'pending_approval';
  end if;
  return new;
end;
$$;

revoke execute on function private.sync_integrated_test_assignment_state()
from public, anon, authenticated, service_role;

create trigger change_proposals_sync_integrated_test_assignment
after update of state on public.change_proposals
for each row execute function private.sync_integrated_test_assignment_state();

create function private.require_integrated_test_assignment_before_plan_apply()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.kind = 'plan_revision'
     and new.state = 'applied'
     and new.state is distinct from old.state
     and exists (
       select 1
       from public.planned_workouts workout
       cross join lateral jsonb_array_elements(workout.segments) segment
       where workout.revision_id = new.target_plan_revision_id
         and workout.athlete_id = new.athlete_id
         and segment -> 'protocol_target' ->> 'protocol_id' in (
           'start23_run_threshold_30min_v1',
           'start23_bike_ftp_30min_v1',
           'start23_bike_fthr_20min_v1'
         )
     )
     and not exists (
       select 1
       from public.discipline_test_assignments assignment
       where assignment.plan_proposal_id = new.id
         and assignment.target_plan_revision_id = new.target_plan_revision_id
         and assignment.athlete_id = new.athlete_id
         and assignment.scheduling_mode = 'weekly_plan'
         and assignment.state = 'pending_approval'
     ) then
    raise exception 'integrated test assignment required before plan approval'
      using errcode = '40001';
  end if;
  return new;
end;
$$;

revoke execute on function private.require_integrated_test_assignment_before_plan_apply()
from public, anon, authenticated, service_role;

create trigger change_proposals_require_integrated_test_assignment
before update of state on public.change_proposals
for each row execute function private.require_integrated_test_assignment_before_plan_apply();
