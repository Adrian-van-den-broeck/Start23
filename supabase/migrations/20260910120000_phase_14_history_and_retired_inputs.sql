-- Phase 14 independent slice: collect two-month distance/frequency history,
-- retire superseded write inputs, and stop new RPE-only setup selection.
-- No baseline, calibration, load, progression, or taper value is derived here.

alter table public.training_history_entries
  add column average_weekly_distance numeric,
  add column distance_unit text,
  add column average_sessions_per_week numeric,
  add column history_window_months smallint;

-- Historical minutes/experience values remain stored but are not required for
-- new Phase 14 rows. They are deliberately not converted to the new fields.
alter table public.training_history_entries
  alter column weekly_minutes drop not null,
  alter column experience_years drop not null;

alter table public.training_history_entries
  add constraint training_history_phase_14_values_consistent check (
    (
      average_weekly_distance is null
      and distance_unit is null
      and average_sessions_per_week is null
      and history_window_months is null
    )
    or (
      average_weekly_distance >= 0
      and average_sessions_per_week >= 0
      and average_weekly_distance::text not in ('NaN', 'Infinity', '-Infinity')
      and average_sessions_per_week::text not in ('NaN', 'Infinity', '-Infinity')
      and history_window_months = 2
      and (
        (discipline = 'swim' and distance_unit = 'meters')
        or (discipline in ('bike', 'run') and distance_unit = 'kilometers')
      )
    )
  );

alter table public.goals
  alter column feasibility_score drop not null;

create function private.preserve_phase_14_retired_values()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_table_name = 'athlete_profiles' then
    if tg_op = 'INSERT' then
      if new.height_cm is not null
         or new.weight_kg is not null
         or new.motivation_text is not null
         or new.motivation_tag is not null then
        raise exception 'retired profile fields cannot be written'
          using errcode = '23514';
      end if;
    elsif new.height_cm is distinct from old.height_cm
       or new.weight_kg is distinct from old.weight_kg
       or new.motivation_text is distinct from old.motivation_text
       or new.motivation_tag is distinct from old.motivation_tag then
      raise exception 'retired profile fields cannot be changed'
        using errcode = '23514';
    end if;
  elsif tg_table_name = 'training_history_entries' then
    if tg_op = 'INSERT' then
      if new.weekly_minutes is not null or new.experience_years is not null then
        raise exception 'retired training history fields cannot be written'
          using errcode = '23514';
      end if;
    elsif new.weekly_minutes is distinct from old.weekly_minutes
       or new.experience_years is distinct from old.experience_years then
      raise exception 'retired training history fields cannot be changed'
        using errcode = '23514';
    end if;
  elsif tg_table_name = 'goals' then
    if tg_op = 'INSERT' and new.feasibility_score is not null then
      raise exception 'retired feasibility field cannot be written'
        using errcode = '23514';
    elsif tg_op = 'UPDATE'
       and new.feasibility_score is distinct from old.feasibility_score then
      raise exception 'retired feasibility field cannot be changed'
        using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

revoke execute on function private.preserve_phase_14_retired_values()
from public, anon, authenticated, service_role;

create trigger athlete_profiles_preserve_phase_14_retired_values
before insert or update on public.athlete_profiles
for each row execute function private.preserve_phase_14_retired_values();

create trigger training_history_preserve_phase_14_retired_values
before insert or update on public.training_history_entries
for each row execute function private.preserve_phase_14_retired_values();

create trigger goals_preserve_phase_14_retired_values
before insert or update on public.goals
for each row execute function private.preserve_phase_14_retired_values();

-- The replacement now upserts only the new observations. It does not delete
-- rows or rewrite the legacy values retained on those rows.
create or replace function public.replace_training_history(p_entries jsonb)
returns setof public.training_history_entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_entries) <> 'array'
     or jsonb_array_length(p_entries) <> 3 then
    raise exception 'swim, bike, and run history are required'
      using errcode = '23514';
  end if;
  if exists (
    select 1
    from jsonb_array_elements(p_entries) entry
    where entry ?| array[
      'athlete_id', 'user_id', 'weekly_minutes', 'experience_years',
      'tss', 'rtss', 'planned_tss', 'realized_tss', 'private_load', 'load'
    ]
  ) then
    raise exception 'retired or private training history fields are not accepted'
      using errcode = '23514';
  end if;
  if (
    select count(distinct entry.discipline)
    from jsonb_to_recordset(p_entries) as entry(
      discipline text,
      average_weekly_distance numeric,
      distance_unit text,
      average_sessions_per_week numeric
    )
    where entry.discipline in ('swim', 'bike', 'run')
      and entry.average_weekly_distance >= 0
      and entry.average_sessions_per_week >= 0
      and entry.average_weekly_distance::text
        not in ('NaN', 'Infinity', '-Infinity')
      and entry.average_sessions_per_week::text
        not in ('NaN', 'Infinity', '-Infinity')
      and (
        (entry.discipline = 'swim' and entry.distance_unit = 'meters')
        or (
          entry.discipline in ('bike', 'run')
          and entry.distance_unit = 'kilometers'
        )
      )
  ) <> 3 then
    raise exception 'complete canonical two-month history is required'
      using errcode = '23514';
  end if;

  insert into public.training_history_entries (
    athlete_id,
    discipline,
    average_weekly_distance,
    distance_unit,
    average_sessions_per_week,
    history_window_months
  )
  select
    v_athlete_id,
    entry.discipline,
    entry.average_weekly_distance,
    entry.distance_unit,
    entry.average_sessions_per_week,
    2
  from jsonb_to_recordset(p_entries) as entry(
    discipline text,
    average_weekly_distance numeric,
    distance_unit text,
    average_sessions_per_week numeric
  )
  on conflict (athlete_id, discipline) do update
  set
    average_weekly_distance = excluded.average_weekly_distance,
    distance_unit = excluded.distance_unit,
    average_sessions_per_week = excluded.average_sessions_per_week,
    history_window_months = excluded.history_window_months,
    confirmed_at = statement_timestamp();

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps
  )
  values (
    v_athlete_id,
    'in_progress',
    'goal',
    array['profile', 'history']::text[]
  )
  on conflict (athlete_id) do update
  set
    current_step = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.current_step
      else 'goal'
    end,
    completed_steps = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.completed_steps
      else (
        select array_agg(distinct step order by step)
        from unnest(
          public.onboarding_sessions.completed_steps
          || array['profile', 'history']::text[]
        ) as steps(step)
      )
    end;

  return query
  select *
  from public.training_history_entries
  where athlete_id = v_athlete_id
  order by discipline;
end;
$$;

revoke delete on table public.training_history_entries from authenticated;

-- New goal writes omit feasibility. Updates retain any historical value.
create function public.save_primary_race_goal(
  p_goal_id uuid,
  p_title text,
  p_specific_description text,
  p_measurable_outcome text,
  p_target_date date,
  p_race_discipline_profile text[]
)
returns public.goals
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_goal public.goals;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_target_date <= current_date then
    raise exception 'target date must be in the future'
      using errcode = '23514';
  end if;
  perform set_config('start23.critical_write', 'on', true);

  if p_goal_id is null then
    insert into public.goals (
      athlete_id,
      title,
      specific_description,
      measurable_outcome,
      target_date,
      race_discipline_profile
    )
    values (
      v_athlete_id,
      p_title,
      p_specific_description,
      p_measurable_outcome,
      p_target_date,
      p_race_discipline_profile
    )
    returning * into v_goal;
  else
    update public.goals
    set
      title = p_title,
      specific_description = p_specific_description,
      measurable_outcome = p_measurable_outcome,
      target_date = p_target_date,
      race_discipline_profile = p_race_discipline_profile
    where id = p_goal_id
      and athlete_id = v_athlete_id
      and status = 'active'
    returning * into v_goal;

    if v_goal.id is null then
      raise exception 'goal not found' using errcode = 'P0002';
    end if;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps
  )
  values (
    v_athlete_id,
    'in_progress',
    'zones',
    array['profile', 'history', 'goal']::text[]
  )
  on conflict (athlete_id) do update
  set
    current_step = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.current_step
      else 'zones'
    end,
    completed_steps = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.completed_steps
      else (
        select array_agg(distinct step order by step)
        from unnest(
          public.onboarding_sessions.completed_steps
          || array['profile', 'history', 'goal']::text[]
        ) as steps(step)
      )
    end;

  return v_goal;
end;
$$;

revoke all on function public.save_primary_race_goal(
  uuid, text, text, text, smallint, date, text[]
) from authenticated;
revoke all on function public.save_primary_race_goal(
  uuid, text, text, text, date, text[]
) from public, anon, service_role;
grant execute on function public.save_primary_race_goal(
  uuid, text, text, text, date, text[]
) to authenticated;

-- RPE-only remains a valid historical row shape, but the owner RPC refuses
-- every new selection or replacement with that route/guidance.
create or replace function public.save_discipline_zone_setup(p_setup jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_setup public.discipline_zone_setups;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_setup) <> 'object'
     or not p_setup ?& array[
       'discipline', 'setup_route', 'guidance_mode', 'setup_status',
       'threshold_status', 'zone_status', 'source', 'validation_status',
       'confidence', 'known_thresholds', 'known_zone_profiles'
     ]
     or p_setup ?| array[
       'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ] then
    raise exception 'invalid discipline setup payload' using errcode = '23514';
  end if;
  if p_setup ->> 'setup_route' = 'rpe_only'
     or p_setup ->> 'guidance_mode' = 'rpe_only' then
    raise exception 'RPE-only setup is not available in the MVP'
      using errcode = '23514';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':' || (p_setup ->> 'discipline'), 0)
  );
  perform set_config('start23.critical_write', 'on', true);

  insert into public.discipline_zone_setups (
    athlete_id,
    discipline,
    setup_route,
    guidance_mode,
    setup_status,
    protocol_id,
    pool_length_meters,
    threshold_status,
    zone_status,
    source,
    validation_status,
    confidence,
    known_thresholds,
    known_zone_profiles
  )
  values (
    v_athlete_id,
    p_setup ->> 'discipline',
    p_setup ->> 'setup_route',
    p_setup ->> 'guidance_mode',
    p_setup ->> 'setup_status',
    p_setup ->> 'protocol_id',
    (p_setup ->> 'pool_length_meters')::smallint,
    p_setup ->> 'threshold_status',
    p_setup ->> 'zone_status',
    p_setup ->> 'source',
    p_setup ->> 'validation_status',
    p_setup ->> 'confidence',
    p_setup -> 'known_thresholds',
    p_setup -> 'known_zone_profiles'
  )
  on conflict (athlete_id, discipline) do update
  set
    setup_route = excluded.setup_route,
    guidance_mode = excluded.guidance_mode,
    setup_status = excluded.setup_status,
    protocol_id = excluded.protocol_id,
    pool_length_meters = excluded.pool_length_meters,
    threshold_status = excluded.threshold_status,
    zone_status = excluded.zone_status,
    source = excluded.source,
    validation_status = excluded.validation_status,
    confidence = excluded.confidence,
    known_thresholds = excluded.known_thresholds,
    known_zone_profiles = excluded.known_zone_profiles
  returning * into v_setup;

  return to_jsonb(v_setup) - 'athlete_id';
end;
$$;

-- Pending planning snapshots record the observations but perform no baseline
-- calculation and omit all retired profile/history/goal fields.
create or replace function private.build_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'profile',
    (
      select jsonb_build_object(
        'athlete_id', profile.athlete_id,
        'date_of_birth', profile.date_of_birth,
        'resting_heart_rate_bpm', profile.resting_heart_rate_bpm,
        'timezone', profile.timezone,
        'revision', profile.revision
      )
      from public.athlete_profiles profile
      where profile.athlete_id = p_athlete_id
    ),
    'training_history',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'discipline', history.discipline,
            'average_weekly_distance', history.average_weekly_distance,
            'distance_unit', history.distance_unit,
            'average_sessions_per_week', history.average_sessions_per_week,
            'history_window_months', history.history_window_months,
            'source', history.source,
            'confirmed_at', history.confirmed_at
          )
          order by history.discipline
        ),
        '[]'::jsonb
      )
      from public.training_history_entries history
      where history.athlete_id = p_athlete_id
    ),
    'goal',
    (
      select jsonb_build_object(
        'id', goal.id,
        'priority', goal.priority,
        'goal_type', goal.goal_type,
        'title', goal.title,
        'specific_description', goal.specific_description,
        'measurable_outcome', goal.measurable_outcome,
        'target_date', goal.target_date,
        'race_discipline_profile', goal.race_discipline_profile,
        'revision', goal.revision
      )
      from public.goals goal
      where goal.athlete_id = p_athlete_id
        and goal.status = 'active'
    ),
    'zones',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'id', profile.id,
            'discipline', profile.discipline,
            'version', profile.version,
            'setup_method', profile.setup_method,
            'validated', profile.validated,
            'fallback_active', profile.fallback_active,
            'needs_testing', profile.needs_testing,
            'requires_review', profile.requires_review,
            'review_reason', profile.review_reason,
            'ruleset_version', profile.ruleset_version,
            'metric',
            (
              select jsonb_build_object(
                'kind', metric.metric_kind,
                'value', metric.value
              )
              from public.zone_metrics metric
              where metric.zone_profile_id = profile.id
                and metric.athlete_id = p_athlete_id
            ),
            'boundaries',
            (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'zone_number', boundary.zone_number,
                    'lower_value', boundary.lower_value,
                    'upper_value', boundary.upper_value
                  )
                  order by boundary.zone_number
                ),
                '[]'::jsonb
              )
              from public.zone_boundaries boundary
              where boundary.zone_profile_id = profile.id
                and boundary.athlete_id = p_athlete_id
            )
          )
          order by profile.discipline
        ),
        '[]'::jsonb
      )
      from public.zone_profile_versions profile
      where profile.athlete_id = p_athlete_id
        and profile.status = 'active'
    ),
    'ruleset_version',
    'phase-3-ruleset-2'
  );
$$;

create or replace function public.complete_onboarding()
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_request_id uuid;
  v_revision bigint;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select initial_plan_request_id into v_request_id
  from public.onboarding_sessions
  where athlete_id = v_athlete_id and status = 'completed';
  if v_request_id is not null then
    return v_request_id;
  end if;

  if not exists (
    select 1 from public.athlete_profiles
    where athlete_id = v_athlete_id
      and date_of_birth is not null
      and resting_heart_rate_bpm is not null
      and timezone is not null
  ) then
    raise exception 'profile is incomplete' using errcode = '23514';
  end if;
  if (
    select count(*) from public.training_history_entries
    where athlete_id = v_athlete_id
      and average_weekly_distance is not null
      and distance_unit is not null
      and average_sessions_per_week is not null
      and history_window_months = 2
  ) <> 3 then
    raise exception 'two-month training history is incomplete'
      using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.goals
    where athlete_id = v_athlete_id and status = 'active'
  ) then
    raise exception 'primary race goal is missing' using errcode = '23514';
  end if;
  if (
    select count(distinct configured.discipline)
    from (
      select profile.discipline
      from public.zone_profile_versions profile
      where profile.athlete_id = v_athlete_id and profile.status = 'active'
      union
      select setup.discipline
      from public.discipline_zone_setups setup
      where setup.athlete_id = v_athlete_id
        and setup.setup_status in ('configured', 'test_pending', 'calibration_pending')
    ) configured
  ) <> 3 then
    raise exception 'discipline guidance setup is incomplete' using errcode = '23514';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.athlete_profiles
  set onboarding_status = 'completed'
  where athlete_id = v_athlete_id
  returning revision into v_revision;

  select id into v_request_id
  from public.initial_plan_requests
  where athlete_id = v_athlete_id and status = 'pending';
  if v_request_id is null then
    insert into public.initial_plan_requests (
      athlete_id, onboarding_revision, ruleset_version
    ) values (v_athlete_id, v_revision, 'phase-3-ruleset-2')
    returning id into v_request_id;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps,
    initial_plan_request_id,
    completed_at
  ) values (
    v_athlete_id,
    'completed',
    'completed',
    array['profile', 'history', 'goal', 'zones', 'review']::text[],
    v_request_id,
    statement_timestamp()
  )
  on conflict (athlete_id) do update
  set
    status = 'completed',
    current_step = 'completed',
    completed_steps = array['profile', 'history', 'goal', 'zones', 'review']::text[],
    initial_plan_request_id = v_request_id,
    completed_at = statement_timestamp();

  return v_request_id;
end;
$$;
