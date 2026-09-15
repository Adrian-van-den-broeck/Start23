-- R6 hosted-lint remediation: qualify private-load subqueries so the activity
-- source column cannot conflict with a composite table alias named `source`.

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
    'zone_minutes', metrics.zone_minutes,
    'known_hr_profile_id', hr_profile.id,
    'known_hr_profile', coalesce(hr_metric.value, (
      select jsonb_build_object(
        'metric_kind', metric.metric_kind, 'source_value', metric.value,
        'boundary_kind', 'manual', 'zone_model_version', 'start23-zone-model-1.0',
        'boundaries', (select jsonb_agg(jsonb_build_object(
          'zone_number', boundary.zone_number, 'lower_value', boundary.lower_value,
          'upper_value', boundary.upper_value) order by boundary.zone_number)
          from public.zone_boundaries boundary where boundary.zone_profile_id = hr_profile.id
            and boundary.athlete_id = activity.athlete_id)
      ) from public.zone_metrics metric where metric.zone_profile_id = hr_profile.id
        and metric.athlete_id = activity.athlete_id
        and metric.metric_kind in ('run_lthr_bpm','bike_threshold_heart_rate_bpm') limit 1
    )),
    'private_load_snapshot', (
      select to_jsonb(load_snapshot)
      from private.activity_loads load_snapshot
      where load_snapshot.activity_id = activity.id
        and load_snapshot.athlete_id = activity.athlete_id
    ),
    'load_ruleset_version', (
      select current_load.ruleset_version
      from private.activity_loads current_load
      where current_load.activity_id = activity.id
        and current_load.athlete_id = p_athlete_id
    ),
    'average_heart_rate_bpm', metrics.average_heart_rate_bpm,
    'requires_heart_rate_observation', activity.discipline <> 'swim' and workout.id is not null and exists (
      select 1
      from jsonb_array_elements(workout.segments) segment
      where coalesce(
        (segment -> 'rpe_target' ->> 'heart_rate_observation_required')::boolean,
        false
      )
    ),
    'planned', case when workout.id is null then null else jsonb_build_object(
      'planned_tss', case when load.ruleset_version = 'phase-13-joren-ruleset-1'
        or exists (select 1 from private.activity_loads original
          where original.activity_id = activity.id and original.athlete_id = activity.athlete_id
            and original.ruleset_version <> 'phase-13-joren-ruleset-1')
        then load.planned_tss else null end,
      'expected_rpe_min', workout.expected_rpe_min,
      'expected_rpe_max', workout.expected_rpe_max,
      'intensity_bucket', workout.intensity_bucket
    ) end
  ) into v_result
  from public.activities activity
  left join lateral (
    select profile.id, profile.metric_profiles
    from public.zone_profile_versions profile
    where profile.athlete_id = activity.athlete_id
      and profile.discipline = activity.discipline
      and profile.id = coalesce(
        (select load_source.zone_profile_id from private.activity_loads load_source
         where load_source.activity_id = activity.id and load_source.athlete_id = activity.athlete_id),
        (select active.id from public.zone_profile_versions active
         where active.athlete_id = activity.athlete_id and active.discipline = activity.discipline
           and active.status = 'active')
      )
  ) hr_profile on true
  left join lateral (
    select value from jsonb_array_elements(hr_profile.metric_profiles)
    where value ->> 'metric_kind' in ('run_lthr_bpm','bike_threshold_heart_rate_bpm')
    limit 1
  ) hr_metric on true
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
