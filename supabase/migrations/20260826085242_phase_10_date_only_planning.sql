-- Phase 10 makes athlete availability and planned workouts date-only. Legacy
-- timestamps remain internal compatibility projections for earlier activity
-- RPCs and are no longer returned by athlete-facing planning/calendar RPCs.

alter table public.plan_revisions
  add column available_dates date[],
  add column availability_source text not null default 'explicit';

update public.plan_revisions revision
set available_dates = (
  select coalesce(
    array_agg(distinct case
      when jsonb_typeof(entry.value) = 'string'
        then (entry.value #>> '{}')::date
      when jsonb_typeof(entry.value) = 'object'
        then (
          (entry.value ->> 'starts_at')::timestamptz at time zone plan.timezone
        )::date
      else null
    end) filter (where jsonb_typeof(entry.value) in ('string', 'object')),
    '{}'::date[]
  )
  from jsonb_array_elements(revision.availability) entry
)
from public.weekly_plans plan
where plan.id = revision.plan_id
  and plan.athlete_id = revision.athlete_id;

alter table public.plan_revisions
  alter column available_dates set not null,
  add constraint plan_revisions_availability_source_valid check (
    availability_source in ('explicit', 'previous_week', 'checkin')
  ),
  add constraint plan_revisions_available_dates_count_valid check (
    cardinality(available_dates) between 0 and 7
    and (
      cardinality(available_dates) > 0
      or target_basis = 'injury_rest_only'
    )
  );

create function private.set_phase_10_plan_revision_dates()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_week_start date;
begin
  select plan.week_start into v_week_start
  from public.weekly_plans plan
  where plan.id = new.plan_id and plan.athlete_id = new.athlete_id;
  if v_week_start is null then
    raise exception 'weekly plan not found' using errcode = '23503';
  end if;

  if new.source = 'athlete_move' then
    select previous.available_dates, previous.availability_source
    into new.available_dates, new.availability_source
    from public.plan_revisions previous
    where previous.plan_id = new.plan_id
      and previous.athlete_id = new.athlete_id
      and previous.revision_number = new.revision_number - 1;
  elsif new.available_dates is null then
    select coalesce(
      array_agg(distinct case
        when jsonb_typeof(entry.value) = 'string'
          then (entry.value #>> '{}')::date
        when jsonb_typeof(entry.value) = 'object'
          then (
            (entry.value ->> 'starts_at')::timestamptz
              at time zone plan.timezone
          )::date
        else null
      end) filter (where jsonb_typeof(entry.value) in ('string', 'object')),
      '{}'::date[]
    )
    into new.available_dates
    from public.weekly_plans plan
    cross join lateral jsonb_array_elements(new.availability) entry
    where plan.id = new.plan_id and plan.athlete_id = new.athlete_id;
  end if;

  if new.available_dates is null
     or cardinality(new.available_dates) > 7
     or exists (select 1 from unnest(new.available_dates) value where value is null)
     or (
       select count(*) <> count(distinct value)
       from unnest(new.available_dates) value
     )
     or exists (
       select 1
       from unnest(new.available_dates) value
       where value not between v_week_start and v_week_start + 6
     )
     or (
       cardinality(new.available_dates) = 0
       and new.target_basis <> 'injury_rest_only'
     ) then
    raise exception 'available dates are invalid' using errcode = '23514';
  end if;
  new.availability := to_jsonb(new.available_dates);
  return new;
end;
$$;

revoke all on function private.set_phase_10_plan_revision_dates()
from public, anon, authenticated, service_role;

create trigger plan_revisions_set_phase_10_dates
before insert or update of available_dates, availability, availability_source
on public.plan_revisions
for each row execute function private.set_phase_10_plan_revision_dates();

alter table public.planned_workouts add column scheduled_date date;

update public.planned_workouts
set scheduled_date = (scheduled_at at time zone timezone)::date;

create function private.set_phase_10_planned_workout_date()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_week_start date;
begin
  if new.scheduled_date is null then
    new.scheduled_date := (new.scheduled_at at time zone new.timezone)::date;
  end if;
  select plan.week_start into v_week_start
  from public.weekly_plans plan
  where plan.id = new.plan_id and plan.athlete_id = new.athlete_id;
  if v_week_start is null
     or new.scheduled_date not between v_week_start and v_week_start + 6 then
    raise exception 'scheduled date is outside the plan week'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke all on function private.set_phase_10_planned_workout_date()
from public, anon, authenticated, service_role;

create trigger planned_workouts_set_phase_10_date
before insert or update of scheduled_date, scheduled_at
on public.planned_workouts
for each row execute function private.set_phase_10_planned_workout_date();

alter table public.planned_workouts alter column scheduled_date set not null;

create index planned_workouts_revision_date_idx
on public.planned_workouts (revision_id, scheduled_date);
create index planned_workouts_owner_calendar_date_idx
on public.planned_workouts (athlete_id, scheduled_date);

alter function public.create_weekly_plan_proposal_v2(uuid, jsonb)
rename to create_weekly_plan_proposal_v2_legacy;

revoke all on function public.create_weekly_plan_proposal_v2_legacy(uuid, jsonb)
from public, anon, authenticated, service_role;

create function public.create_weekly_plan_proposal_v2(
  p_athlete_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
  v_dates date[];
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_payload -> 'available_dates') <> 'array'
     or jsonb_typeof(p_payload -> 'availability') <> 'array'
     or p_payload ->> 'availability_source'
        not in ('explicit', 'previous_week', 'checkin') then
    raise exception 'date-only availability is invalid' using errcode = '23514';
  end if;
  select coalesce(
    array_agg((entry.value #>> '{}')::date order by entry.ordinality),
    '{}'::date[]
  ) into v_dates
  from jsonb_array_elements(p_payload -> 'available_dates')
    with ordinality entry(value, ordinality);

  v_result := public.create_weekly_plan_proposal_v2_legacy(
    p_athlete_id,
    p_payload
  );
  perform set_config('start23.critical_write', 'on', true);
  update public.plan_revisions
  set
    available_dates = v_dates,
    availability_source = p_payload ->> 'availability_source'
  where plan_id = (v_result ->> 'plan_id')::uuid
    and athlete_id = p_athlete_id
    and revision_number = (v_result ->> 'revision')::integer;
  return v_result;
end;
$$;

revoke all on function public.create_weekly_plan_proposal_v2(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v2(uuid, jsonb)
to service_role;

create or replace function public.get_plan_context_for_planning(
  p_athlete_id uuid,
  p_plan_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_context jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'plan_id', plan.id,
    'week_start', plan.week_start,
    'active_revision', plan.active_revision,
    'revision', revision.revision_number,
    'phase', revision.phase,
    'confirmed_injuries', revision.confirmed_injuries,
    'low_only_disciplines', revision.low_only_disciplines,
    'available_dates', revision.available_dates,
    'availability_source', revision.availability_source,
    'target_tss', revision_load.target_tss,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = plan.athlete_id
        and maintenance.status = 'active'
    ),
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot
  ) into v_context
  from public.weekly_plans plan
  join lateral (
    select candidate.*
    from public.plan_revisions candidate
    where candidate.plan_id = plan.id
      and candidate.athlete_id = plan.athlete_id
      and (
        candidate.revision_number = plan.active_revision
        or plan.active_revision is null
      )
    order by
      (candidate.revision_number = plan.active_revision) desc,
      candidate.revision_number desc
    limit 1
  ) revision on true
  join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = revision.athlete_id
  join public.initial_plan_requests request
    on request.id = revision.initial_plan_request_id
   and request.athlete_id = plan.athlete_id
  where plan.id = p_plan_id and plan.athlete_id = p_athlete_id;
  if v_context is null then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  return v_context;
end;
$$;

create function public.get_plan_revision_context_for_planning(
  p_athlete_id uuid,
  p_plan_id uuid,
  p_revision integer
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_context jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'plan_id', plan.id,
    'week_start', plan.week_start,
    'active_revision', plan.active_revision,
    'revision', revision.revision_number,
    'phase', revision.phase,
    'confirmed_injuries', revision.confirmed_injuries,
    'low_only_disciplines', revision.low_only_disciplines,
    'available_dates', revision.available_dates,
    'availability_source', revision.availability_source,
    'target_tss', revision_load.target_tss,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = plan.athlete_id
        and maintenance.status = 'active'
    ),
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot,
    'proposal_id', proposal.id
  ) into v_context
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = p_revision
   and revision.state = 'pending_approval'
  join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = revision.athlete_id
  join public.initial_plan_requests request
    on request.id = revision.initial_plan_request_id
   and request.athlete_id = plan.athlete_id
  join public.change_proposals proposal
    on proposal.target_plan_revision_id = revision.id
   and proposal.athlete_id = revision.athlete_id
   and proposal.state = 'pending'
  where plan.id = p_plan_id and plan.athlete_id = p_athlete_id;
  if v_context is null then
    raise exception 'pending weekly plan revision not found' using errcode = 'P0002';
  end if;
  return v_context;
end;
$$;

revoke all on function public.get_plan_revision_context_for_planning(
  uuid, uuid, integer
) from public, anon, authenticated, service_role;
grant execute on function public.get_plan_revision_context_for_planning(
  uuid, uuid, integer
) to service_role;

create function public.get_previous_week_available_dates(
  p_athlete_id uuid,
  p_week_start date
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_dates date[];
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select array(
    select value + 7
    from unnest(revision.available_dates) value
    order by value
  ) into v_dates
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
   and revision.state = 'active'
  where plan.athlete_id = p_athlete_id
    and plan.week_start = p_week_start - 7;
  return to_jsonb(coalesce(v_dates, '{}'::date[]));
end;
$$;

revoke all on function public.get_previous_week_available_dates(uuid, date)
from public, anon, authenticated, service_role;
grant execute on function public.get_previous_week_available_dates(uuid, date)
to service_role;

create or replace function public.get_weekly_plan(
  p_plan_id uuid,
  p_revision integer default null
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'id', plan.id,
    'week_start', plan.week_start,
    'timezone', plan.timezone,
    'state', plan.state,
    'active_revision', plan.active_revision,
    'revision_id', revision.id,
    'revision', revision.revision_number,
    'revision_state', revision.state,
    'phase', revision.phase,
    'target_basis', revision.target_basis,
    'taper_period', revision.taper_period,
    'total_duration_minutes', revision.total_duration_minutes,
    'low_intensity_percent', revision.low_intensity_percent,
    'high_intensity_percent', revision.high_intensity_percent,
    'confirmed_injuries', revision.confirmed_injuries,
    'low_only_disciplines', revision.low_only_disciplines,
    'available_dates', revision.available_dates,
    'availability_source', revision.availability_source,
    'workouts', (
      select coalesce(jsonb_agg(
        jsonb_build_object(
          'id', workout.id,
          'template_id', workout.template_id,
          'template_key', workout.template_key,
          'template_version', workout.template_version,
          'discipline', workout.discipline,
          'name', workout.name,
          'description', workout.description,
          'duration_minutes', workout.duration_minutes,
          'distance_meters', workout.distance_meters,
          'intensity_bucket', workout.intensity_bucket,
          'expected_rpe_min', workout.expected_rpe_min,
          'expected_rpe_max', workout.expected_rpe_max,
          'segments', workout.segments,
          'scheduled_date', workout.scheduled_date,
          'source', workout.source,
          'status', workout.status,
          'warnings', (
            select coalesce(jsonb_agg(
              jsonb_build_object(
                'id', warning.id,
                'rule_id', warning.rule_id,
                'code', warning.code,
                'severity', warning.severity,
                'message', warning.message,
                'planned_workout_id', warning.planned_workout_id
              ) order by warning.created_at, warning.id
            ), '[]'::jsonb)
            from public.plan_warnings warning
            where warning.revision_id = revision.id
              and warning.planned_workout_id = workout.id
          )
        ) order by workout.scheduled_date, workout.id
      ), '[]'::jsonb)
      from public.planned_workouts workout
      where workout.revision_id = revision.id
    ),
    'warnings', (
      select coalesce(jsonb_agg(
        jsonb_build_object(
          'id', warning.id,
          'rule_id', warning.rule_id,
          'code', warning.code,
          'severity', warning.severity,
          'message', warning.message,
          'planned_workout_id', warning.planned_workout_id
        ) order by warning.created_at, warning.id
      ), '[]'::jsonb)
      from public.plan_warnings warning
      where warning.revision_id = revision.id
    ),
    'proposal', (
      select jsonb_build_object(
        'id', proposal.id,
        'kind', proposal.kind,
        'state', proposal.state,
        'reason_codes', proposal.reason_codes,
        'public_explanation', proposal.public_explanation,
        'ruleset_version', proposal.ruleset_version,
        'created_at', proposal.created_at,
        'decided_at', proposal.decided_at,
        'applied_at', proposal.applied_at,
        'decision_actor', proposal.decision_actor,
        'target_plan_revision_id', proposal.target_plan_revision_id,
        'base_plan_revision', proposal.base_plan_revision,
        'target_zone_profile_id', proposal.target_zone_profile_id,
        'base_zone_profile_id', proposal.base_zone_profile_id
      )
      from public.change_proposals proposal
      where proposal.target_plan_revision_id = revision.id
      order by proposal.created_at desc
      limit 1
    )
  ) into v_result
  from public.weekly_plans plan
  join lateral (
    select candidate.*
    from public.plan_revisions candidate
    where candidate.plan_id = plan.id
      and candidate.athlete_id = v_athlete_id
      and (
        candidate.revision_number = p_revision
        or (
          p_revision is null
          and candidate.revision_number = coalesce(
            plan.active_revision,
            (
              select max(pending.revision_number)
              from public.plan_revisions pending
              where pending.plan_id = plan.id
                and pending.state = 'pending_approval'
            )
          )
        )
      )
    limit 1
  ) revision on true
  where plan.id = p_plan_id and plan.athlete_id = v_athlete_id;
  if v_result is null then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

create or replace function public.get_planned_workout_context(p_workout_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'plan', public.get_weekly_plan(plan.id, revision.revision_number),
    'available_dates', revision.available_dates
  ) into v_result
  from public.planned_workouts workout
  join public.plan_revisions revision
    on revision.id = workout.revision_id
   and revision.athlete_id = workout.athlete_id
  join public.weekly_plans plan
    on plan.id = workout.plan_id
   and plan.athlete_id = workout.athlete_id
  where workout.id = p_workout_id
    and workout.athlete_id = v_athlete_id
    and revision.state = 'active'
    and plan.active_revision = revision.revision_number;
  if v_result is null then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

alter function public.move_planned_workout(
  uuid, uuid, integer, timestamptz, jsonb
) rename to move_planned_workout_legacy;

revoke all on function public.move_planned_workout_legacy(
  uuid, uuid, integer, timestamptz, jsonb
) from public, anon, authenticated, service_role;

create function public.move_planned_workout(
  p_athlete_id uuid,
  p_workout_id uuid,
  p_expected_revision integer,
  p_scheduled_date date,
  p_warnings jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_timezone text;
  v_scheduled_at timestamptz;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select plan.timezone into v_timezone
  from public.weekly_plans plan
  join public.planned_workouts workout
    on workout.plan_id = plan.id and workout.athlete_id = plan.athlete_id
  where workout.id = p_workout_id and plan.athlete_id = p_athlete_id;
  if v_timezone is null then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  v_scheduled_at := (p_scheduled_date + time '12:00') at time zone v_timezone;
  return public.move_planned_workout_legacy(
    p_athlete_id,
    p_workout_id,
    p_expected_revision,
    v_scheduled_at,
    p_warnings
  );
end;
$$;

revoke all on function public.move_planned_workout(
  uuid, uuid, integer, date, jsonb
) from public, anon, authenticated, service_role;
grant execute on function public.move_planned_workout(
  uuid, uuid, integer, date, jsonb
) to service_role;

drop function public.get_calendar(timestamptz, timestamptz);
drop function public.get_calendar_rest_days(timestamptz, timestamptz);

create function public.get_calendar(p_from date, p_to date)
returns setof jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'id', workout.id,
    'template_id', workout.template_id,
    'template_key', workout.template_key,
    'template_version', workout.template_version,
    'discipline', workout.discipline,
    'name', workout.name,
    'description', workout.description,
    'duration_minutes', workout.duration_minutes,
    'distance_meters', workout.distance_meters,
    'intensity_bucket', workout.intensity_bucket,
    'expected_rpe_min', workout.expected_rpe_min,
    'expected_rpe_max', workout.expected_rpe_max,
    'segments', workout.segments,
    'scheduled_date', workout.scheduled_date,
    'source', workout.source,
    'status', workout.status,
    'warnings', (
      select coalesce(jsonb_agg(
        jsonb_build_object(
          'id', warning.id,
          'rule_id', warning.rule_id,
          'code', warning.code,
          'severity', warning.severity,
          'message', warning.message,
          'planned_workout_id', warning.planned_workout_id
        ) order by warning.created_at, warning.id
      ), '[]'::jsonb)
      from public.plan_warnings warning
      where warning.revision_id = revision.id
        and (
          warning.planned_workout_id is null
          or warning.planned_workout_id = workout.id
        )
    )
  )
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  join public.planned_workouts workout
    on workout.revision_id = revision.id
   and workout.athlete_id = plan.athlete_id
  where plan.athlete_id = (select auth.uid())
    and workout.scheduled_date >= p_from
    and workout.scheduled_date < p_to
  order by workout.scheduled_date, workout.id;
$$;

revoke all on function public.get_calendar(date, date)
from public, anon, authenticated, service_role;
grant execute on function public.get_calendar(date, date) to authenticated;

create function public.get_calendar_rest_days(p_from date, p_to date)
returns setof jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'date', day.local_date,
    'reason', case
      when revision.target_basis = 'injury_rest_only' then 'restriction_rest'
      else 'planned_rest'
    end
  )
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  cross join lateral generate_series(
    plan.week_start,
    plan.week_start + 6,
    interval '1 day'
  ) generated
  cross join lateral (select generated::date as local_date) day
  where plan.athlete_id = (select auth.uid())
    and day.local_date >= p_from
    and day.local_date < p_to
    and not exists (
      select 1
      from public.planned_workouts workout
      where workout.revision_id = revision.id
        and workout.athlete_id = plan.athlete_id
        and workout.status <> 'cancelled'
        and workout.scheduled_date = day.local_date
    )
  order by day.local_date;
$$;

revoke all on function public.get_calendar_rest_days(date, date)
from public, anon, authenticated, service_role;
grant execute on function public.get_calendar_rest_days(date, date)
to authenticated;
