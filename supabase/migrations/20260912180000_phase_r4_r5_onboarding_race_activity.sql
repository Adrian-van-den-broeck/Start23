-- Remediation R4/R5: explicit onboarding prerequisites, structured race goals,
-- and immutable Phase 13 average-HR/load provenance. Forward-only; the R6
-- dual-owner compatibility contract remains in place.

alter table public.athlete_profiles
  add column timezone_source text,
  add column timezone_confirmed_at timestamptz,
  add column heart_rate_monitor_confirmed_at timestamptz;

alter table public.athlete_profiles
  add constraint athlete_profiles_timezone_confirmation_consistent check (
    (timezone_source is null and timezone_confirmed_at is null)
    or (
      timezone_source in ('device', 'manual')
      and timezone_confirmed_at is not null
      and timezone is not null
    )
  );

comment on column public.athlete_profiles.timezone_source is
  'Athlete-confirmed canonical IANA timezone source; null marks legacy/unconfirmed values.';
comment on column public.athlete_profiles.heart_rate_monitor_confirmed_at is
  'Athlete assertion that average-HR measurement is available; no provider is required.';

alter table public.onboarding_sessions
  drop constraint onboarding_sessions_current_step_valid,
  drop constraint onboarding_sessions_completed_steps_valid;
alter table public.onboarding_sessions
  add constraint onboarding_sessions_current_step_valid check (
    current_step in (
      'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones',
      'review', 'completed'
    )
  ),
  add constraint onboarding_sessions_completed_steps_valid check (
    completed_steps <@ array[
      'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones',
      'review'
    ]::text[]
  );

grant insert (
  timezone_source, timezone_confirmed_at, heart_rate_monitor_confirmed_at
), update (
  timezone_source, timezone_confirmed_at, heart_rate_monitor_confirmed_at
) on public.athlete_profiles to authenticated;

create or replace function public.save_operational_athlete_profile(p_profile jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_profile public.athlete_profiles;
  v_has_timezone boolean := p_profile ? 'timezone';
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_profile) <> 'object'
     or p_profile = '{}'::jsonb
     or exists (
       select 1 from jsonb_object_keys(p_profile) supplied(key)
       where supplied.key not in (
         'timezone', 'timezone_source', 'timezone_confirmed',
         'heart_rate_monitor_confirmed'
       )
     ) then
    raise exception 'invalid operational profile payload' using errcode = '23514';
  end if;
  if v_has_timezone <> (p_profile ? 'timezone_source')
     or v_has_timezone <> (p_profile ? 'timezone_confirmed')
     or (v_has_timezone and (p_profile ->> 'timezone_confirmed')::boolean is distinct from true)
     or (v_has_timezone and p_profile ->> 'timezone_source' not in ('device', 'manual'))
     or (v_has_timezone and not exists (
       select 1 from pg_catalog.pg_timezone_names
       where name = p_profile ->> 'timezone'
     ))
     or (
       p_profile ? 'heart_rate_monitor_confirmed'
       and (p_profile ->> 'heart_rate_monitor_confirmed')::boolean is distinct from true
     ) then
    raise exception 'explicit valid operational confirmation is required'
      using errcode = '23514';
  end if;

  insert into public.athlete_profiles (
    athlete_id, timezone, timezone_source, timezone_confirmed_at,
    heart_rate_monitor_confirmed_at, onboarding_status
  ) values (
    v_auth_user_id,
    case when v_has_timezone then p_profile ->> 'timezone' else 'UTC' end,
    case when v_has_timezone then p_profile ->> 'timezone_source' else null end,
    case when v_has_timezone then statement_timestamp() else null end,
    case when p_profile ? 'heart_rate_monitor_confirmed'
      then statement_timestamp() else null end,
    'in_progress'
  )
  on conflict (athlete_id) do update set
    timezone = case when v_has_timezone
      then excluded.timezone else public.athlete_profiles.timezone end,
    timezone_source = case when v_has_timezone
      then excluded.timezone_source else public.athlete_profiles.timezone_source end,
    timezone_confirmed_at = case when v_has_timezone
      then excluded.timezone_confirmed_at
      else public.athlete_profiles.timezone_confirmed_at end,
    heart_rate_monitor_confirmed_at = case
      when p_profile ? 'heart_rate_monitor_confirmed'
        then coalesce(
          public.athlete_profiles.heart_rate_monitor_confirmed_at,
          excluded.heart_rate_monitor_confirmed_at
        )
      else public.athlete_profiles.heart_rate_monitor_confirmed_at end,
    onboarding_status = case
      when public.athlete_profiles.onboarding_status = 'completed'
        then 'completed' else 'in_progress' end
  returning * into v_profile;

  return jsonb_build_object(
    'athlete_id', v_athlete_id,
    'timezone', v_profile.timezone,
    'timezone_source', v_profile.timezone_source,
    'timezone_confirmed_at', v_profile.timezone_confirmed_at,
    'heart_rate_monitor_confirmed_at', v_profile.heart_rate_monitor_confirmed_at,
    'onboarding_status', v_profile.onboarding_status,
    'revision', v_profile.revision,
    'created_at', v_profile.created_at,
    'updated_at', v_profile.updated_at
  );
end;
$$;

alter table public.goals
  alter column title drop not null,
  alter column specific_description drop not null,
  alter column measurable_outcome drop not null,
  alter column target_date drop not null,
  alter column race_discipline_profile drop not null,
  add column race_type text,
  add column race_name text,
  add column race_date date,
  add column swim_distance_meters integer,
  add column bike_distance_meters integer,
  add column run_distance_meters integer,
  add column total_target_time_seconds integer,
  add column swim_target_time_seconds integer,
  add column bike_target_time_seconds integer,
  add column run_target_time_seconds integer,
  add column specific_focus text;

alter table public.goals add constraint goals_r4_structured_race_valid check (
  (race_type is null and race_name is null and race_date is null
    and total_target_time_seconds is null)
  or (
    race_type in ('run', 'bike', 'swim', 'triathlon', 'duathlon')
    and race_name = btrim(race_name)
    and char_length(race_name) between 1 and 120
    and race_date is not null
    and total_target_time_seconds between 1 and 604800
    and (specific_focus is null or (
      specific_focus = btrim(specific_focus)
      and char_length(specific_focus) between 1 and 1000
    ))
    and (swim_distance_meters is null or swim_distance_meters > 0)
    and (bike_distance_meters is null or bike_distance_meters > 0)
    and (run_distance_meters is null or run_distance_meters > 0)
    and (swim_target_time_seconds is null or swim_target_time_seconds > 0)
    and (bike_target_time_seconds is null or bike_target_time_seconds > 0)
    and (run_target_time_seconds is null or run_target_time_seconds > 0)
    and coalesce(swim_target_time_seconds, 0)
      + coalesce(bike_target_time_seconds, 0)
      + coalesce(run_target_time_seconds, 0) <= total_target_time_seconds
    and case race_type
      when 'run' then run_distance_meters is not null
        and swim_distance_meters is null and bike_distance_meters is null
        and swim_target_time_seconds is null and bike_target_time_seconds is null
      when 'bike' then bike_distance_meters is not null
        and swim_distance_meters is null and run_distance_meters is null
        and swim_target_time_seconds is null and run_target_time_seconds is null
      when 'swim' then swim_distance_meters is not null
        and bike_distance_meters is null and run_distance_meters is null
        and bike_target_time_seconds is null and run_target_time_seconds is null
      when 'triathlon' then swim_distance_meters is not null
        and bike_distance_meters is not null and run_distance_meters is not null
      when 'duathlon' then bike_distance_meters is not null
        and run_distance_meters is not null and swim_distance_meters is null
        and swim_target_time_seconds is null
      else false
    end
  )
);

revoke execute on function public.save_primary_race_goal(
  uuid, text, text, text, date, text[]
) from authenticated;

create function public.save_primary_race_goal(
  p_goal_id uuid,
  p_race_type text,
  p_race_name text,
  p_race_date date,
  p_swim_distance_meters integer,
  p_bike_distance_meters integer,
  p_run_distance_meters integer,
  p_total_target_time_seconds integer,
  p_swim_target_time_seconds integer,
  p_bike_target_time_seconds integer,
  p_run_target_time_seconds integer,
  p_specific_focus text
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
  if p_race_date <= current_date then
    raise exception 'race date must be in the future' using errcode = '23514';
  end if;
  perform set_config('start23.critical_write', 'on', true);

  if p_goal_id is null then
    -- A legacy active goal is not exposed through the current public model, so
    -- upgrade that owned row in place and retain its historical generic values.
    update public.goals set
      race_type = p_race_type, race_name = p_race_name, race_date = p_race_date,
      swim_distance_meters = p_swim_distance_meters,
      bike_distance_meters = p_bike_distance_meters,
      run_distance_meters = p_run_distance_meters,
      total_target_time_seconds = p_total_target_time_seconds,
      swim_target_time_seconds = p_swim_target_time_seconds,
      bike_target_time_seconds = p_bike_target_time_seconds,
      run_target_time_seconds = p_run_target_time_seconds,
      specific_focus = p_specific_focus
    where athlete_id = v_athlete_id and status = 'active' and race_type is null
    returning * into v_goal;
    if v_goal.id is null then
      insert into public.goals (
        athlete_id, race_type, race_name, race_date,
        swim_distance_meters, bike_distance_meters, run_distance_meters,
        total_target_time_seconds, swim_target_time_seconds,
        bike_target_time_seconds, run_target_time_seconds, specific_focus
      ) values (
        v_athlete_id, p_race_type, p_race_name, p_race_date,
        p_swim_distance_meters, p_bike_distance_meters, p_run_distance_meters,
        p_total_target_time_seconds, p_swim_target_time_seconds,
        p_bike_target_time_seconds, p_run_target_time_seconds, p_specific_focus
      ) returning * into v_goal;
    end if;
  else
    update public.goals set
      race_type = p_race_type, race_name = p_race_name, race_date = p_race_date,
      swim_distance_meters = p_swim_distance_meters,
      bike_distance_meters = p_bike_distance_meters,
      run_distance_meters = p_run_distance_meters,
      total_target_time_seconds = p_total_target_time_seconds,
      swim_target_time_seconds = p_swim_target_time_seconds,
      bike_target_time_seconds = p_bike_target_time_seconds,
      run_target_time_seconds = p_run_target_time_seconds,
      specific_focus = p_specific_focus
    where id = p_goal_id and athlete_id = v_athlete_id and status = 'active'
    returning * into v_goal;
    if v_goal.id is null then
      raise exception 'goal not found' using errcode = 'P0002';
    end if;
  end if;
  return v_goal;
end;
$$;

revoke execute on function public.save_primary_race_goal(
  uuid, text, text, date, integer, integer, integer, integer,
  integer, integer, integer, text
) from public, anon, service_role;
grant execute on function public.save_primary_race_goal(
  uuid, text, text, date, integer, integer, integer, integer,
  integer, integer, integer, text
) to authenticated;

create or replace function private.current_onboarding_satisfied_steps(p_athlete_id uuid)
returns text[]
language sql
stable
security invoker
set search_path = ''
as $$
  select array_remove(array[
    case when exists (
      select 1 from public.athlete_profiles operational
      join public.athlete_physiology_profiles physiology
        on physiology.athlete_id = operational.internal_athlete_id
      where operational.internal_athlete_id = p_athlete_id
        and physiology.date_of_birth is not null
        and physiology.resting_heart_rate_bpm is not null
    ) then 'profile' end,
    case when exists (
      select 1 from public.athlete_profiles operational
      where operational.internal_athlete_id = p_athlete_id
        and operational.heart_rate_monitor_confirmed_at is not null
    ) then 'heart_rate_monitor' end,
    case when exists (
      select 1 from public.athlete_profiles operational
      where operational.internal_athlete_id = p_athlete_id
        and operational.timezone is not null
        and operational.timezone_source in ('device', 'manual')
        and operational.timezone_confirmed_at is not null
    ) then 'timezone' end,
    case when (
      select count(*) from public.training_history_entries history
      where history.internal_athlete_id = p_athlete_id
        and history.previous_month_weekly_minutes is not null
        and history.baseline_model_version = 'phase-13-joren-ruleset-1'
    ) = 3 then 'history' end,
    case when exists (
      select 1 from public.goals goal
      where goal.internal_athlete_id = p_athlete_id and goal.status = 'active'
        and goal.race_type is not null and goal.race_name is not null
        and goal.race_date is not null and goal.total_target_time_seconds is not null
    ) then 'goal' end,
    case when (
      select count(distinct configured.discipline) from (
        select profile.discipline from public.zone_profile_versions profile
        where profile.internal_athlete_id = p_athlete_id and profile.status = 'active'
        union
        select setup.discipline from public.discipline_zone_setups setup
        where setup.internal_athlete_id = p_athlete_id
          and setup.setup_status in ('configured', 'test_pending', 'calibration_pending')
          and (
            setup.setup_route = 'known_values'
            or (setup.setup_route = 'field_test' and setup.discipline = 'swim'
              and setup.protocol_id = 'start23_swim_css_400_200_v1'
              and setup.guidance_mode = 'pace')
            or (setup.setup_route = 'calibration_week' and (
              (setup.discipline = 'run' and setup.guidance_mode = 'heart_rate')
              or (setup.discipline = 'bike' and setup.guidance_mode in ('heart_rate', 'combined'))
              or (setup.discipline = 'swim' and setup.guidance_mode = 'pace')
            ))
          )
      ) configured
    ) = 3 then 'zones' end
  ], null)
$$;

alter function private.build_planning_input_snapshot(uuid)
  rename to build_planning_input_snapshot_r3;

create function private.build_planning_input_snapshot(p_athlete_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.resolve_opaque_athlete_id(p_athlete_id);
  v_base jsonb := private.build_planning_input_snapshot_r3(p_athlete_id);
  v_profile jsonb;
  v_goal jsonb;
begin
  if v_athlete_id is null then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;
  select jsonb_build_object(
    'athlete_id', v_athlete_id,
    'date_of_birth', physiology.date_of_birth,
    'resting_heart_rate_bpm', physiology.resting_heart_rate_bpm,
    'timezone', operational.timezone,
    'timezone_source', operational.timezone_source,
    'timezone_confirmed_at', operational.timezone_confirmed_at,
    'heart_rate_monitor_confirmed_at', operational.heart_rate_monitor_confirmed_at,
    'revision', operational.revision
  ) into v_profile
  from public.athlete_profiles operational
  left join public.athlete_physiology_profiles physiology
    on physiology.athlete_id = operational.internal_athlete_id
  where operational.internal_athlete_id = v_athlete_id;

  select jsonb_build_object(
    'id', goal.id, 'priority', goal.priority, 'goal_type', goal.goal_type,
    'race_type', goal.race_type, 'race_name', goal.race_name,
    'race_date', goal.race_date,
    'swim_distance_meters', goal.swim_distance_meters,
    'bike_distance_meters', goal.bike_distance_meters,
    'run_distance_meters', goal.run_distance_meters,
    'total_target_time_seconds', goal.total_target_time_seconds,
    'swim_target_time_seconds', goal.swim_target_time_seconds,
    'bike_target_time_seconds', goal.bike_target_time_seconds,
    'run_target_time_seconds', goal.run_target_time_seconds,
    'specific_focus', goal.specific_focus,
    -- Internal compatibility aliases consumed by the deterministic planner.
    'target_date', goal.race_date,
    'race_discipline_profile', case goal.race_type
      when 'run' then jsonb_build_array('run')
      when 'bike' then jsonb_build_array('bike')
      when 'swim' then jsonb_build_array('swim')
      when 'duathlon' then jsonb_build_array('bike', 'run')
      when 'triathlon' then jsonb_build_array('swim', 'bike', 'run')
      else '[]'::jsonb end,
    'revision', goal.revision
  ) into v_goal
  from public.goals goal
  where goal.internal_athlete_id = v_athlete_id and goal.status = 'active';

  return jsonb_set(
    jsonb_set(
      jsonb_set(v_base, '{profile}', coalesce(v_profile, 'null'::jsonb)),
      '{goal}', coalesce(v_goal, 'null'::jsonb)
    ),
    '{onboarding_version}', to_jsonb('phase-14-onboarding-v2'::text)
  );
end;
$$;

revoke execute on function private.build_planning_input_snapshot_r3(uuid)
from public, anon, authenticated, service_role;
revoke execute on function private.build_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

create or replace function public.complete_current_onboarding(
  p_expected_session_revision bigint
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_session public.onboarding_sessions;
  v_request_id uuid;
  v_completion_revision bigint;
  v_satisfied text[];
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_expected_session_revision is null or p_expected_session_revision < 0 then
    raise exception 'expected onboarding revision is required' using errcode = '23514';
  end if;
  select session.* into v_session from public.onboarding_sessions session
  where session.internal_athlete_id = v_athlete_id for update;

  if v_session.athlete_id is not null and v_session.status = 'completed'
     and v_session.completed_onboarding_version = 'phase-14-onboarding-v2'
     and v_session.completed_ruleset_version = 'phase-13-joren-ruleset-1'
     and exists (
       select 1 from public.initial_plan_requests request
       where request.id = v_session.initial_plan_request_id
         and request.internal_athlete_id = v_athlete_id
         and request.onboarding_version = 'phase-14-onboarding-v2'
         and request.ruleset_version = 'phase-13-joren-ruleset-1'
         and request.status <> 'cancelled'
     ) then
    return v_session.initial_plan_request_id;
  end if;
  if (v_session.athlete_id is null and p_expected_session_revision <> 0)
     or (v_session.athlete_id is not null
       and v_session.revision <> p_expected_session_revision) then
    raise exception 'onboarding session revision is stale' using errcode = '40001';
  end if;
  v_satisfied := private.current_onboarding_satisfied_steps(v_athlete_id);
  if not v_satisfied @> array[
    'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones'
  ]::text[] then
    raise exception 'current onboarding prerequisites are incomplete'
      using errcode = '23514';
  end if;
  v_completion_revision := case when v_session.athlete_id is null
    then 1 else v_session.revision + 1 end;
  perform set_config('start23.critical_write', 'on', true);
  update public.initial_plan_requests set status = 'cancelled'
  where internal_athlete_id = v_athlete_id and status = 'pending';
  update public.athlete_profiles set onboarding_status = 'completed'
  where internal_athlete_id = v_athlete_id and onboarding_status <> 'completed';
  insert into public.initial_plan_requests (
    athlete_id, internal_athlete_id, onboarding_revision,
    onboarding_version, ruleset_version
  ) values (
    v_auth_user_id, v_athlete_id, v_completion_revision,
    'phase-14-onboarding-v2', 'phase-13-joren-ruleset-1'
  ) returning id into v_request_id;
  insert into public.onboarding_sessions (
    athlete_id, internal_athlete_id, status, current_step, completed_steps,
    revision, initial_plan_request_id, completed_onboarding_version,
    completed_ruleset_version, completed_at
  ) values (
    v_auth_user_id, v_athlete_id, 'completed', 'completed',
    array['profile','heart_rate_monitor','timezone','history','goal','zones','review']::text[],
    v_completion_revision, v_request_id, 'phase-14-onboarding-v2',
    'phase-13-joren-ruleset-1', statement_timestamp()
  ) on conflict (athlete_id) do update set
    status = 'completed', current_step = 'completed',
    completed_steps = excluded.completed_steps,
    initial_plan_request_id = excluded.initial_plan_request_id,
    completed_onboarding_version = excluded.completed_onboarding_version,
    completed_ruleset_version = excluded.completed_ruleset_version,
    completed_at = excluded.completed_at;
  select session.revision into strict v_completion_revision
  from public.onboarding_sessions session
  where session.internal_athlete_id = v_athlete_id;
  if v_completion_revision <> (select request.onboarding_revision
    from public.initial_plan_requests request where request.id = v_request_id) then
    raise exception 'onboarding completion revision mismatch' using errcode = '23514';
  end if;
  insert into public.onboarding_completion_records (
    athlete_id, internal_athlete_id, onboarding_version, ruleset_version,
    completed_steps, initial_plan_request_id, session_revision,
    record_source, completed_at
  ) values (
    v_auth_user_id, v_athlete_id, 'phase-14-onboarding-v2',
    'phase-13-joren-ruleset-1',
    array['profile','heart_rate_monitor','timezone','history','goal','zones','review']::text[],
    v_request_id, v_completion_revision, 'current_completion', statement_timestamp()
  ) on conflict (athlete_id, onboarding_version, ruleset_version) do nothing;
  return v_request_id;
end;
$$;

create or replace function private.assert_current_planning_eligibility(p_athlete_id uuid)
returns void
language plpgsql
stable
security definer
set search_path = ''
as $$
declare v_satisfied text[];
begin
  if p_athlete_id is null then
    raise exception 'opaque athlete owner is required' using errcode = '23514';
  end if;
  v_satisfied := private.current_onboarding_satisfied_steps(p_athlete_id);
  if not exists (
    select 1 from public.onboarding_sessions session
    join public.initial_plan_requests request
      on request.id = session.initial_plan_request_id
      and request.internal_athlete_id = session.internal_athlete_id
    where session.internal_athlete_id = p_athlete_id
      and session.status = 'completed'
      and session.completed_onboarding_version = 'phase-14-onboarding-v2'
      and session.completed_ruleset_version = 'phase-13-joren-ruleset-1'
      and request.onboarding_version = 'phase-14-onboarding-v2'
      and request.ruleset_version = 'phase-13-joren-ruleset-1'
      and request.status <> 'cancelled'
  ) or not v_satisfied @> array[
    'profile','heart_rate_monitor','timezone','history','goal','zones'
  ]::text[] then
    raise exception 'current onboarding completion is required for planning'
      using errcode = '23514';
  end if;
end;
$$;

-- Activity-local dates and weeks must use the explicitly confirmed persisted
-- timezone, including imports and direct RPC/table writes.
create function private.enforce_confirmed_activity_timezone()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_timezone text;
begin
  select profile.timezone into v_timezone
  from public.athlete_profiles profile
  where profile.athlete_id = new.athlete_id
    and profile.timezone_source in ('device', 'manual')
    and profile.timezone_confirmed_at is not null;
  if v_timezone is null or new.timezone is distinct from v_timezone then
    raise exception 'activity timezone must match the confirmed athlete timezone'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_confirmed_activity_timezone()
from public, anon, authenticated, service_role;
create trigger activities_r4_10_require_confirmed_timezone
before insert or update of timezone on public.activities
for each row execute function private.enforce_confirmed_activity_timezone();

-- R1-D1: once Phase 13 load exists, the source average-HR observation is
-- immutable. Rejection happens before any metric update and therefore cannot
-- diverge from its load/profile/ruleset snapshot.
create function private.protect_phase_13_average_hr_observation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.average_heart_rate_bpm is distinct from old.average_heart_rate_bpm
     and exists (
       select 1 from private.activity_loads load
       where load.activity_id = old.activity_id
         and load.athlete_id = old.athlete_id
         and load.ruleset_version = 'phase-13-joren-ruleset-1'
     ) then
    raise exception 'average heart rate is immutable after load calculation'
      using errcode = '40001';
  end if;
  return new;
end;
$$;

revoke execute on function private.protect_phase_13_average_hr_observation()
from public, anon, authenticated, service_role;
create trigger activity_metrics_r5_protect_average_hr
before update of average_heart_rate_bpm on public.activity_metrics
for each row execute function private.protect_phase_13_average_hr_observation();

alter function public.revise_activity_rpe(uuid, uuid, jsonb)
  rename to revise_activity_rpe_r5_base;

create function public.revise_activity_rpe(
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
  v_average_heart_rate_bpm smallint;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity from public.activities
  where id = p_activity_id and athlete_id = p_athlete_id for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  select metric.average_heart_rate_bpm into v_average_heart_rate_bpm
  from public.activity_metrics metric
  where metric.activity_id = p_activity_id and metric.athlete_id = p_athlete_id;
  if p_payload ? 'submitted_average_heart_rate_bpm'
     and (p_payload ->> 'submitted_average_heart_rate_bpm')::smallint
       is distinct from v_average_heart_rate_bpm
     and exists (
       select 1 from private.activity_loads load
       where load.activity_id = p_activity_id and load.athlete_id = p_athlete_id
         and load.ruleset_version = 'phase-13-joren-ruleset-1'
     ) then
    raise exception 'average heart rate is immutable after load calculation'
      using errcode = '40001';
  end if;
  if v_activity.rpe = (p_payload ->> 'rpe')::smallint then
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  if not p_payload ? 'expected_current_rpe'
     or (p_payload ->> 'expected_current_rpe')::smallint is distinct from v_activity.rpe then
    raise exception 'activity correction is stale' using errcode = '40001';
  end if;
  return public.revise_activity_rpe_r5_base(
    p_athlete_id, p_activity_id, p_payload
  );
end;
$$;

revoke execute on function public.revise_activity_rpe_r5_base(uuid, uuid, jsonb)
from public, anon, authenticated, service_role;
revoke execute on function public.revise_activity_rpe(uuid, uuid, jsonb)
from public, anon, authenticated;
grant execute on function public.revise_activity_rpe(uuid, uuid, jsonb)
to service_role;

comment on function public.revise_activity_rpe(uuid, uuid, jsonb) is
  'R5 owner-scoped stale-safe correction; Phase 13 average-HR/load provenance is immutable.';
