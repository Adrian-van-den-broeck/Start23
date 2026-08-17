-- Phase 7 canonical activity summaries, RPE feedback, hidden realized load,
-- and approval-gated current-week corrections.

alter table public.change_proposals
  add constraint change_proposals_id_athlete_id_key
  unique (id, athlete_id);

create table public.activities (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  planned_workout_id uuid,
  idempotency_key uuid not null,
  request_fingerprint text not null,
  source text not null default 'canonical_summary',
  discipline text not null,
  started_at timestamptz not null,
  timezone text not null,
  duration_minutes numeric not null,
  distance_meters integer,
  elevation_gain_meters integer,
  rpe smallint,
  rpe_submitted_at timestamptz,
  match_status text not null,
  processing_state text not null default 'awaiting_rpe',
  qualitative_result text not null default 'awaiting_rpe',
  public_message text not null default 'Voeg je ervaren inspanning toe om de training af te ronden.',
  correction_proposal_id uuid,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (athlete_id, idempotency_key),
  foreign key (planned_workout_id, athlete_id)
    references public.planned_workouts (id, athlete_id),
  foreign key (correction_proposal_id, athlete_id)
    references public.change_proposals (id, athlete_id),
  constraint activities_fingerprint_valid check (
    request_fingerprint ~ '^[a-f0-9]{64}$'
  ),
  constraint activities_source_valid check (source = 'canonical_summary'),
  constraint activities_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint activities_timezone_valid check (
    char_length(btrim(timezone)) between 1 and 100 and timezone = btrim(timezone)
  ),
  constraint activities_duration_valid check (
    duration_minutes > 0 and duration_minutes <= 1440
  ),
  constraint activities_distance_valid check (
    distance_meters is null or distance_meters between 1 and 1000000
  ),
  constraint activities_elevation_valid check (
    elevation_gain_meters is null or elevation_gain_meters between 0 and 100000
  ),
  constraint activities_swim_elevation_absent check (
    discipline <> 'swim' or elevation_gain_meters is null
  ),
  constraint activities_rpe_valid check (rpe is null or rpe between 1 and 10),
  constraint activities_rpe_state_consistent check (
    (
      processing_state = 'awaiting_rpe'
      and rpe is null
      and rpe_submitted_at is null
      and qualitative_result = 'awaiting_rpe'
      and correction_proposal_id is null
    )
    or (
      processing_state = 'complete'
      and rpe is not null
      and rpe_submitted_at is not null
      and qualitative_result in (
        'perfect_match',
        'overshoot',
        'hidden_fatigue',
        'deviation',
        'unplanned'
      )
    )
  ),
  constraint activities_match_status_valid check (
    match_status in ('matched', 'unmatched')
  ),
  constraint activities_match_reference_consistent check (
    (match_status = 'matched' and planned_workout_id is not null)
    or (match_status = 'unmatched' and planned_workout_id is null)
  ),
  constraint activities_public_message_valid check (
    char_length(btrim(public_message)) between 1 and 500
    and public_message = btrim(public_message)
  )
);

create unique index one_activity_per_planned_workout
on public.activities (planned_workout_id)
where planned_workout_id is not null;
create index activities_owner_started_idx
on public.activities (athlete_id, started_at desc);
create index activities_owner_pending_rpe_idx
on public.activities (athlete_id, created_at desc)
where processing_state = 'awaiting_rpe';
create index activities_correction_proposal_idx
on public.activities (correction_proposal_id)
where correction_proposal_id is not null;

create table public.activity_metrics (
  activity_id uuid primary key,
  athlete_id uuid not null,
  average_heart_rate_bpm smallint,
  max_heart_rate_bpm smallint,
  normalized_power_watts integer,
  average_speed_kmh numeric,
  max_speed_kmh numeric,
  average_pace_seconds_per_km numeric,
  low_intensity_minutes numeric,
  high_intensity_minutes numeric,
  created_at timestamptz not null default statement_timestamp(),

  unique (activity_id, athlete_id),
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id)
    on delete cascade,
  constraint activity_metrics_hr_valid check (
    (average_heart_rate_bpm is null or average_heart_rate_bpm between 20 and 260)
    and (max_heart_rate_bpm is null or max_heart_rate_bpm between 20 and 260)
    and (
      average_heart_rate_bpm is null
      or max_heart_rate_bpm is null
      or average_heart_rate_bpm <= max_heart_rate_bpm
    )
  ),
  constraint activity_metrics_power_valid check (
    normalized_power_watts is null or normalized_power_watts between 1 and 3000
  ),
  constraint activity_metrics_speed_valid check (
    (average_speed_kmh is null or average_speed_kmh > 0 and average_speed_kmh <= 300)
    and (max_speed_kmh is null or max_speed_kmh > 0 and max_speed_kmh <= 300)
    and (
      average_speed_kmh is null
      or max_speed_kmh is null
      or average_speed_kmh <= max_speed_kmh
    )
  ),
  constraint activity_metrics_pace_valid check (
    average_pace_seconds_per_km is null
    or average_pace_seconds_per_km > 0
    and average_pace_seconds_per_km <= 3600
  ),
  constraint activity_metrics_intensity_pair check (
    (low_intensity_minutes is null) = (high_intensity_minutes is null)
    and (low_intensity_minutes is null or low_intensity_minutes >= 0)
    and (high_intensity_minutes is null or high_intensity_minutes >= 0)
  ),
  constraint activity_metrics_not_empty check (
    num_nonnulls(
      average_heart_rate_bpm,
      max_heart_rate_bpm,
      normalized_power_watts,
      average_speed_kmh,
      max_speed_kmh,
      average_pace_seconds_per_km,
      low_intensity_minutes,
      high_intensity_minutes
    ) > 0
  )
);

create index activity_metrics_owner_idx
on public.activity_metrics (athlete_id);

create table private.activity_loads (
  activity_id uuid primary key references public.activities (id) on delete cascade,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  realized_tss numeric not null,
  calculation_method text not null,
  ruleset_version text not null,
  created_at timestamptz not null default statement_timestamp(),

  constraint activity_loads_value_valid check (realized_tss > 0),
  constraint activity_loads_method_valid check (
    calculation_method = 'actual_rpe_times_duration_hours'
  ),
  constraint activity_loads_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

create index activity_loads_owner_idx on private.activity_loads (athlete_id);

alter table public.activities enable row level security;
alter table public.activities force row level security;
alter table public.activity_metrics enable row level security;
alter table public.activity_metrics force row level security;

revoke all on table public.activities
from public, anon, authenticated, service_role;
revoke all on table public.activity_metrics
from public, anon, authenticated, service_role;
revoke all on table private.activity_loads
from public, anon, authenticated, service_role;

-- Explicit grants are required by the 2026 Data API exposure default.
grant select on table public.activities to authenticated;
grant select on table public.activity_metrics to authenticated;

create policy activities_select_own
on public.activities for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy activity_metrics_select_own
on public.activity_metrics for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

alter table public.plan_revisions
  drop constraint plan_revisions_target_basis_valid;
alter table public.plan_revisions
  add constraint plan_revisions_target_basis_valid check (
    target_basis in (
      'initial_catalog_baseline',
      'prior_planned_hold',
      'realized_progression',
      'realized_baseline',
      'physiological_debt',
      'manual_review_recovery',
      'activity_correction',
      'recovery_factor',
      'taper_factor'
    )
  );

create function private.activity_public_json(p_activity_id uuid, p_athlete_id uuid)
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

revoke all on function private.activity_public_json(uuid, uuid)
from public, anon, authenticated, service_role;

create function public.create_activity_summary(
  p_idempotency_key uuid,
  p_request_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_existing public.activities;
  v_workout public.planned_workouts;
  v_activity_id uuid;
  v_metrics jsonb := p_payload -> 'metrics';
  v_discipline text := p_payload ->> 'discipline';
  v_duration numeric := (p_payload ->> 'duration_minutes')::numeric;
  v_timezone text := p_payload ->> 'timezone';
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_request_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid activity fingerprint' using errcode = '23514';
  end if;
  if not exists (
    select 1 from pg_catalog.pg_timezone_names where name = v_timezone
  ) then
    raise exception 'invalid activity timezone' using errcode = '23514';
  end if;

  select * into v_existing
  from public.activities
  where athlete_id = v_athlete_id and idempotency_key = p_idempotency_key;
  if found then
    if v_existing.request_fingerprint <> p_request_fingerprint then
      raise exception 'activity idempotency key reused' using errcode = '40001';
    end if;
    return private.activity_public_json(v_existing.id, v_athlete_id);
  end if;

  if p_payload ->> 'planned_workout_id' is not null then
    select workout.* into v_workout
    from public.planned_workouts workout
    join public.plan_revisions revision
      on revision.id = workout.revision_id
     and revision.athlete_id = workout.athlete_id
    join public.weekly_plans plan
      on plan.id = workout.plan_id
     and plan.athlete_id = workout.athlete_id
     and plan.active_revision = revision.revision_number
    where workout.id = (p_payload ->> 'planned_workout_id')::uuid
      and workout.athlete_id = v_athlete_id
      and revision.state = 'active';
    if not found then
      raise exception 'planned workout not found' using errcode = 'P0002';
    end if;
    if v_workout.discipline <> v_discipline then
      raise exception 'activity discipline does not match planned workout'
      using errcode = '23514';
    end if;
    if exists (
      select 1 from public.activities
      where planned_workout_id = v_workout.id
    ) then
      raise exception 'planned workout already matched' using errcode = '40001';
    end if;
  end if;

  if v_metrics is not null
     and v_metrics ->> 'low_intensity_minutes' is not null
     and (
       (v_metrics ->> 'low_intensity_minutes')::numeric
       + (v_metrics ->> 'high_intensity_minutes')::numeric
     ) > v_duration then
    raise exception 'activity intensity duration mismatch' using errcode = '23514';
  end if;
  if v_metrics is not null
     and v_discipline <> 'bike'
     and (
       v_metrics ->> 'average_speed_kmh' is not null
       or v_metrics ->> 'max_speed_kmh' is not null
     ) then
    raise exception 'activity speed telemetry requires bike discipline'
    using errcode = '23514';
  end if;

  insert into public.activities (
    athlete_id,
    planned_workout_id,
    idempotency_key,
    request_fingerprint,
    discipline,
    started_at,
    timezone,
    duration_minutes,
    distance_meters,
    elevation_gain_meters,
    match_status
  ) values (
    v_athlete_id,
    (p_payload ->> 'planned_workout_id')::uuid,
    p_idempotency_key,
    p_request_fingerprint,
    v_discipline,
    (p_payload ->> 'started_at')::timestamptz,
    v_timezone,
    v_duration,
    (p_payload ->> 'distance_meters')::integer,
    (p_payload ->> 'elevation_gain_meters')::integer,
    case when p_payload ->> 'planned_workout_id' is null
      then 'unmatched' else 'matched' end
  ) returning id into v_activity_id;

  if v_metrics is not null then
    insert into public.activity_metrics (
      activity_id,
      athlete_id,
      average_heart_rate_bpm,
      max_heart_rate_bpm,
      normalized_power_watts,
      average_speed_kmh,
      max_speed_kmh,
      average_pace_seconds_per_km,
      low_intensity_minutes,
      high_intensity_minutes
    ) values (
      v_activity_id,
      v_athlete_id,
      (v_metrics ->> 'average_heart_rate_bpm')::smallint,
      (v_metrics ->> 'max_heart_rate_bpm')::smallint,
      (v_metrics ->> 'normalized_power_watts')::integer,
      (v_metrics ->> 'average_speed_kmh')::numeric,
      (v_metrics ->> 'max_speed_kmh')::numeric,
      (v_metrics ->> 'average_pace_seconds_per_km')::numeric,
      (v_metrics ->> 'low_intensity_minutes')::numeric,
      (v_metrics ->> 'high_intensity_minutes')::numeric
    );
  end if;

  return private.activity_public_json(v_activity_id, v_athlete_id);
end;
$$;

revoke all on function public.create_activity_summary(uuid, text, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_activity_summary(uuid, text, jsonb)
to authenticated;

create function public.get_activity(p_activity_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  v_result := private.activity_public_json(p_activity_id, v_athlete_id);
  if v_result is null then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_activity(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_activity(uuid) to authenticated;

create function public.list_activities(p_pending_rpe boolean default false)
returns setof jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select private.activity_public_json(activity.id, (select auth.uid()))
  from public.activities activity
  where activity.athlete_id = (select auth.uid())
    and (not p_pending_rpe or activity.processing_state = 'awaiting_rpe')
  order by activity.started_at desc, activity.id;
$$;

revoke all on function public.list_activities(boolean)
from public, anon, authenticated, service_role;
grant execute on function public.list_activities(boolean) to authenticated;

drop function public.get_plan_load_history_for_planning(uuid, date);

create function public.get_plan_load_history_for_planning(
  p_athlete_id uuid,
  p_before_week date
)
returns table (
  week_start date,
  phase text,
  target_basis text,
  planned_tss numeric,
  realized_tss numeric,
  planned_high_minutes numeric,
  planned_total_minutes numeric,
  realized_high_minutes numeric,
  realized_classified_minutes numeric,
  realized_total_minutes numeric
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
    plan.week_start,
    revision.phase,
    revision.target_basis,
    revision_load.planned_tss,
    (
      select sum(activity_load.realized_tss)
      from public.activities activity
      join private.activity_loads activity_load
        on activity_load.activity_id = activity.id
       and activity_load.athlete_id = activity.athlete_id
      where activity.athlete_id = plan.athlete_id
        and (activity.started_at at time zone activity.timezone)::date
          between plan.week_start and plan.week_start + 6
    ) as realized_tss,
    revision.total_duration_minutes * revision.high_intensity_percent / 100,
    revision.total_duration_minutes,
    (
      select sum(metric.high_intensity_minutes)
      from public.activities activity
      join private.activity_loads activity_load
        on activity_load.activity_id = activity.id
       and activity_load.athlete_id = activity.athlete_id
      join public.activity_metrics metric
        on metric.activity_id = activity.id and metric.athlete_id = activity.athlete_id
      where activity.athlete_id = plan.athlete_id
        and (activity.started_at at time zone activity.timezone)::date
          between plan.week_start and plan.week_start + 6
    ),
    (
      select sum(metric.low_intensity_minutes + metric.high_intensity_minutes)
      from public.activities activity
      join private.activity_loads activity_load
        on activity_load.activity_id = activity.id
       and activity_load.athlete_id = activity.athlete_id
      join public.activity_metrics metric
        on metric.activity_id = activity.id and metric.athlete_id = activity.athlete_id
      where activity.athlete_id = plan.athlete_id
        and (activity.started_at at time zone activity.timezone)::date
          between plan.week_start and plan.week_start + 6
    ),
    (
      select sum(activity.duration_minutes)
      from public.activities activity
      join private.activity_loads activity_load
        on activity_load.activity_id = activity.id
       and activity_load.athlete_id = activity.athlete_id
      where activity.athlete_id = plan.athlete_id
        and (activity.started_at at time zone activity.timezone)::date
          between plan.week_start and plan.week_start + 6
    )
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = plan.athlete_id
  where plan.athlete_id = p_athlete_id
    and plan.week_start < p_before_week
  order by plan.week_start;
end;
$$;

revoke all
on function public.get_plan_load_history_for_planning(uuid, date)
from public, anon, authenticated, service_role;
grant execute
on function public.get_plan_load_history_for_planning(uuid, date)
to service_role;

create function public.get_activity_processing_context(
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
    'planned', case when workout.id is null then null else jsonb_build_object(
      'planned_tss', load.planned_tss,
      'expected_rpe_min', workout.expected_rpe_min,
      'expected_rpe_max', workout.expected_rpe_max,
      'intensity_bucket', workout.intensity_bucket
    ) end
  ) into v_result
  from public.activities activity
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

create function public.complete_activity_rpe(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_activity public.activities;
  v_rpe smallint := (p_payload ->> 'rpe')::smallint;
  v_result text := p_payload ->> 'qualitative_result';
  v_reason text := p_payload ->> 'correction_reason';
  v_realized numeric := (p_payload ->> 'realized_tss')::numeric;
  v_plan public.weekly_plans;
  v_old_revision public.plan_revisions;
  v_new_revision_id uuid;
  v_new_revision integer;
  v_old_workout public.planned_workouts;
  v_new_workout_id uuid;
  v_cancel boolean;
  v_total numeric;
  v_low numeric;
  v_high numeric;
  v_planned numeric;
  v_proposal_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity
  from public.activities
  where id = p_activity_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.processing_state = 'complete' then
    if v_activity.rpe <> v_rpe then
      raise exception 'activity rpe is immutable' using errcode = '40001';
    end if;
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  if v_rpe not between 1 and 10
     or v_result not in (
       'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
     )
     or v_reason is not null and v_reason not in (
       'volume_overshoot', 'hidden_fatigue', 'unplanned_load'
     )
     or (v_result = 'overshoot') <>
       coalesce(v_reason = 'volume_overshoot', false)
     or (v_result = 'hidden_fatigue') <>
       coalesce(v_reason = 'hidden_fatigue', false)
     or (v_result = 'unplanned') <>
       coalesce(v_reason = 'unplanned_load', false)
     or v_result in ('perfect_match', 'deviation') and v_reason is not null
     or v_realized <> v_activity.duration_minutes * v_rpe / 60 then
    raise exception 'invalid activity rpe result' using errcode = '23514';
  end if;

  insert into private.activity_loads (
    activity_id, athlete_id, realized_tss, calculation_method, ruleset_version
  ) values (
    p_activity_id,
    p_athlete_id,
    v_realized,
    p_payload ->> 'calculation_method',
    p_payload ->> 'ruleset_version'
  );

  perform set_config('start23.critical_write', 'on', true);
  if v_activity.planned_workout_id is not null then
    update public.planned_workouts
    set status = 'completed'
    where id = v_activity.planned_workout_id and athlete_id = p_athlete_id;
  end if;

  if v_reason is not null then
    if v_activity.planned_workout_id is not null then
      select plan.* into v_plan
      from public.planned_workouts workout
      join public.weekly_plans plan
        on plan.id = workout.plan_id and plan.athlete_id = workout.athlete_id
      join public.plan_revisions revision
        on revision.plan_id = plan.id
       and revision.athlete_id = plan.athlete_id
       and revision.revision_number = plan.active_revision
      where workout.id = v_activity.planned_workout_id
        and workout.athlete_id = p_athlete_id
        and revision.state = 'active';
    else
      select plan.* into v_plan
      from public.weekly_plans plan
      where plan.athlete_id = p_athlete_id
        and plan.state = 'active'
        and (v_activity.started_at at time zone plan.timezone)::date
          between plan.week_start and plan.week_start + 6
      limit 1;
    end if;
  end if;

  if v_plan.id is not null
     and not exists (
       select 1 from public.plan_revisions
       where plan_id = v_plan.id and state = 'pending_approval'
     ) then
    select * into v_old_revision
    from public.plan_revisions
    where plan_id = v_plan.id
      and athlete_id = p_athlete_id
      and revision_number = v_plan.active_revision
      and state = 'active'
    for update;

    if exists (
      select 1 from public.planned_workouts workout
      where workout.revision_id = v_old_revision.id
        and workout.status = 'scheduled'
        and workout.intensity_bucket = 'high'
        and workout.scheduled_at > v_activity.started_at
          + make_interval(mins => v_activity.duration_minutes::integer)
        and (
          v_reason <> 'hidden_fatigue'
          or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
        )
    ) then
      select
        coalesce(sum(
          case when workout.status = 'cancelled' then 0
          when workout.status = 'scheduled'
             and workout.intensity_bucket = 'high'
             and workout.scheduled_at > v_activity.started_at
               + make_interval(mins => v_activity.duration_minutes::integer)
             and (
               v_reason <> 'hidden_fatigue'
               or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
             )
          then 0 else workout.duration_minutes end
        ), 0),
        coalesce(sum(
          case when workout.status <> 'cancelled'
             and workout.intensity_bucket = 'low' then workout.duration_minutes
          else 0 end
        ), 0),
        coalesce(sum(
          case when workout.status <> 'cancelled'
             and workout.intensity_bucket = 'high'
             and not (
               workout.status = 'scheduled'
               and workout.scheduled_at > v_activity.started_at
                 + make_interval(mins => v_activity.duration_minutes::integer)
               and (
                 v_reason <> 'hidden_fatigue'
                 or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
               )
             )
          then workout.duration_minutes else 0 end
        ), 0)
      into v_total, v_low, v_high
      from public.planned_workouts workout
      where workout.revision_id = v_old_revision.id;

      v_new_revision := (
        select coalesce(max(revision_number), 0) + 1
        from public.plan_revisions where plan_id = v_plan.id
      );
      insert into public.plan_revisions (
        plan_id,
        athlete_id,
        revision_number,
        state,
        source,
        phase,
        target_basis,
        taper_period,
        input_fingerprint,
        generation_fingerprint,
        initial_plan_request_id,
        total_duration_minutes,
        low_intensity_percent,
        high_intensity_percent,
        confirmed_injuries,
        availability,
        ruleset_version
      ) values (
        v_plan.id,
        p_athlete_id,
        v_new_revision,
        'pending_approval',
        'system_generated',
        v_old_revision.phase,
        'activity_correction',
        v_old_revision.taper_period,
        pg_catalog.md5(p_activity_id::text || ':' || v_reason),
        pg_catalog.encode(
          extensions.digest(
            p_activity_id::text || ':' || v_reason || ':' || v_new_revision::text,
            'sha256'
          ),
          'hex'
        ),
        v_old_revision.initial_plan_request_id,
        v_total,
        case when v_total = 0 then 100 else v_low * 100 / v_total end,
        case when v_total = 0 then 0 else v_high * 100 / v_total end,
        v_old_revision.confirmed_injuries,
        v_old_revision.availability,
        p_payload ->> 'ruleset_version'
      ) returning id into v_new_revision_id;

      for v_old_workout in
        select * from public.planned_workouts
        where revision_id = v_old_revision.id
        order by scheduled_at, id
      loop
        v_cancel := v_old_workout.status = 'scheduled'
          and v_old_workout.intensity_bucket = 'high'
          and v_old_workout.scheduled_at > v_activity.started_at
            + make_interval(mins => v_activity.duration_minutes::integer)
          and (
            v_reason <> 'hidden_fatigue'
            or v_old_workout.scheduled_at <= v_activity.started_at + interval '72 hours'
          );
        insert into public.planned_workouts (
          revision_id, plan_id, athlete_id, template_id, template_key,
          template_version, discipline, name, description, duration_minutes,
          distance_meters, intensity_bucket, expected_rpe_min, expected_rpe_max,
          segments, scheduled_at, timezone, source, status
        ) values (
          v_new_revision_id, v_plan.id, p_athlete_id, v_old_workout.template_id,
          v_old_workout.template_key, v_old_workout.template_version,
          v_old_workout.discipline, v_old_workout.name, v_old_workout.description,
          v_old_workout.duration_minutes, v_old_workout.distance_meters,
          v_old_workout.intensity_bucket, v_old_workout.expected_rpe_min,
          v_old_workout.expected_rpe_max, v_old_workout.segments,
          v_old_workout.scheduled_at, v_old_workout.timezone,
          case when v_cancel then 'system_adjusted' else v_old_workout.source end,
          case when v_cancel then 'cancelled' else v_old_workout.status end
        ) returning id into v_new_workout_id;
        insert into private.planned_workout_loads (
          planned_workout_id, athlete_id, planned_tss,
          calculation_method, ruleset_version
        ) select
          v_new_workout_id, p_athlete_id, load.planned_tss,
          load.calculation_method, load.ruleset_version
        from private.planned_workout_loads load
        where load.planned_workout_id = v_old_workout.id;
      end loop;

      select coalesce(sum(load.planned_tss), 0) into v_planned
      from private.planned_workout_loads load
      join public.planned_workouts workout on workout.id = load.planned_workout_id
      where workout.revision_id = v_new_revision_id and workout.status <> 'cancelled';

      insert into private.plan_revision_loads (
        revision_id, athlete_id, target_tss, planned_tss, ruleset_version
      ) select
        v_new_revision_id, p_athlete_id, old_load.target_tss,
        v_planned, p_payload ->> 'ruleset_version'
      from private.plan_revision_loads old_load
      where old_load.revision_id = v_old_revision.id;

      insert into public.plan_warnings (
        revision_id, athlete_id, rule_id, code, severity, message
      ) values (
        v_new_revision_id,
        p_athlete_id,
        'BR-002',
        v_reason,
        'warning',
        p_payload ->> 'public_message'
      );

      insert into public.change_proposals (
        athlete_id, kind, state, target_plan_revision_id,
        base_plan_revision, reason_codes, public_explanation, ruleset_version
      ) values (
        p_athlete_id,
        'plan_revision',
        'pending',
        v_new_revision_id,
        v_plan.active_revision,
        array[v_reason],
        p_payload ->> 'public_message',
        p_payload ->> 'ruleset_version'
      ) returning id into v_proposal_id;
    end if;
  end if;

  update public.activities
  set
    rpe = v_rpe,
    rpe_submitted_at = statement_timestamp(),
    processing_state = 'complete',
    qualitative_result = v_result,
    public_message = p_payload ->> 'public_message',
    correction_proposal_id = v_proposal_id,
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = p_athlete_id;

  return private.activity_public_json(p_activity_id, p_athlete_id);
end;
$$;

revoke all on function public.complete_activity_rpe(uuid, uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.complete_activity_rpe(uuid, uuid, jsonb)
to service_role;
