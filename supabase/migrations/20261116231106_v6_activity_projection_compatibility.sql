-- Forward compatibility correction. Include atomically in G2; no accepted SQL edited.
-- Legacy RPCs retain their exact 47-migration projection. V2 is explicit, service-only.
create or replace function private.activity_public_json(p_activity_id uuid, p_athlete_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', activity.id,
    'planned_workout_id', activity.planned_workout_id,
    'discipline', activity.discipline,
    'source', activity.source,
    'started_at', activity.started_at,
    'timezone', activity.timezone,
    'duration_minutes', activity.duration_minutes,
    'distance_meters', activity.distance_meters,
    'elevation_gain_meters', activity.elevation_gain_meters,
    'rpe', activity.rpe,
    'rpe_submitted_at', activity.rpe_submitted_at,
    'match_status', activity.match_status,
    'processing_state', activity.processing_state,
    'qualitative_result', activity.qualitative_result,
    'public_message', activity.public_message,
    'correction_proposal_id', activity.correction_proposal_id,
    'metrics', (
      select jsonb_build_object(
        'average_heart_rate_bpm', metric.average_heart_rate_bpm,
        'max_heart_rate_bpm', metric.max_heart_rate_bpm,
        'normalized_power_watts', metric.normalized_power_watts,
        'average_speed_kmh', metric.average_speed_kmh,
        'max_speed_kmh', metric.max_speed_kmh,
        'average_pace_seconds_per_km', metric.average_pace_seconds_per_km,
        'zone_minutes', metric.zone_minutes,
        'low_intensity_minutes', metric.low_intensity_minutes,
        'high_intensity_minutes', metric.high_intensity_minutes
      )
      from public.activity_metrics metric
      where metric.activity_id = activity.id
        and metric.athlete_id = p_athlete_id
    ),
    'created_at', activity.created_at,
    'updated_at', activity.updated_at
  )
  from public.activities activity
  where activity.id = p_activity_id and activity.athlete_id = p_athlete_id;
$$;
revoke all on function private.activity_public_json(uuid,uuid) from public,anon,authenticated,service_role;
-- New Session-RPE semantics only. Historical prescriptions/calibration remain.
create or replace function private.activity_public_json_v2(p_activity_id uuid, p_athlete_id uuid)
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'id', activity.id, 'planned_workout_id', activity.planned_workout_id,
    'discipline', activity.discipline, 'source', activity.source,
    'started_at', activity.started_at, 'timezone', activity.timezone,
    'duration_minutes', activity.duration_minutes, 'distance_meters', activity.distance_meters,
    'elevation_gain_meters', activity.elevation_gain_meters,
    'rpe', activity.rpe, 'rpe_submitted_at', activity.rpe_submitted_at,
    'session_rpe_version', case when exists (select 1 from private.realized_v2_activity_inputs input
      where input.activity_id = activity.id and input.athlete_id = p_athlete_id) then '2' else 'legacy' end,
    'match_status', activity.match_status, 'processing_state', activity.processing_state,
    'qualitative_result', activity.qualitative_result, 'public_message', activity.public_message,
    'correction_proposal_id', activity.correction_proposal_id,
    'metrics', (select jsonb_build_object(
      'average_heart_rate_bpm', metric.average_heart_rate_bpm,
      'max_heart_rate_bpm', metric.max_heart_rate_bpm,
      'normalized_power_watts', metric.normalized_power_watts,
      'average_speed_kmh', metric.average_speed_kmh, 'max_speed_kmh', metric.max_speed_kmh,
      'average_pace_seconds_per_km', metric.average_pace_seconds_per_km,
      'zone_minutes', metric.zone_minutes, 'low_intensity_minutes', metric.low_intensity_minutes,
      'high_intensity_minutes', metric.high_intensity_minutes
    ) from public.activity_metrics metric where metric.activity_id = activity.id and metric.athlete_id = p_athlete_id),
    'created_at', activity.created_at, 'updated_at', activity.updated_at
  ) from public.activities activity where activity.id = p_activity_id and activity.athlete_id = p_athlete_id;
$$;
revoke all on function private.activity_public_json_v2(uuid, uuid) from public, anon, authenticated, service_role;

create function public.get_activity_presentation_v2(p_activity_id uuid)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare result jsonb;
begin
  if coalesce((select auth.jwt()->>'role'),'') <> 'service_role' then
    raise exception 'service role required' using errcode='42501';
  end if;
  -- Called only after an existing owner-scoped activity operation succeeds.
  -- Metadata is immutable, contains no private load, and cannot authorize a write.
  select jsonb_build_object('session_rpe_version',
    case when exists(select 1 from private.realized_v2_activity_inputs i
      where i.activity_id=a.id and i.athlete_id=a.athlete_id) then '2' else 'legacy' end)
    into result from public.activities a where a.id=p_activity_id;
  if result is null then raise exception 'activity not found' using errcode='P0002'; end if;
  return result;
end; $$;
revoke all on function public.get_activity_presentation_v2(uuid) from public,anon,authenticated,service_role;
grant execute on function public.get_activity_presentation_v2(uuid) to service_role;
notify pgrst, 'reload schema';
