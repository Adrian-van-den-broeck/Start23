-- R6 runtime remediation: refresh a pending planning snapshot in a separate
-- command after the structured goal mutation is complete. The historical row
-- trigger fires inside the goal UPDATE command and therefore rebuilt from the
-- preceding goal revision.

create function private.refresh_authenticated_planning_input_after_rpc()
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_auth_user_id uuid := (select auth.uid());
begin
  if v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.initial_plan_requests
  set refreshed_at = statement_timestamp()
  where athlete_id = v_auth_user_id
    and status = 'pending';
end;
$$;

revoke all on function private.refresh_authenticated_planning_input_after_rpc()
from public, anon, authenticated, service_role;
grant execute on function private.refresh_authenticated_planning_input_after_rpc()
to authenticated;

comment on function private.refresh_authenticated_planning_input_after_rpc() is
  'Refreshes only the authenticated athlete pending planning snapshot after a completed input RPC mutation.';

create or replace function public.save_primary_race_goal(
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
    update public.goals set
      race_type = p_race_type, race_name = p_race_name, race_date = p_race_date,
      swim_distance_meters = p_swim_distance_meters,
      bike_distance_meters = p_bike_distance_meters,
      run_distance_meters = p_run_distance_meters,
      total_target_time_seconds = p_total_target_time_seconds,
      swim_target_time_seconds = p_swim_target_time_seconds,
      bike_target_time_seconds = p_bike_target_time_seconds,
      run_target_time_seconds = p_run_target_time_seconds,
      specific_focus = p_specific_focus,
      revision = revision + 1,
      updated_at = statement_timestamp()
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
      specific_focus = p_specific_focus,
      revision = revision + 1,
      updated_at = statement_timestamp()
    where id = p_goal_id and athlete_id = v_athlete_id and status = 'active'
    returning * into v_goal;
    if v_goal.id is null then
      raise exception 'goal not found' using errcode = 'P0002';
    end if;
  end if;

  perform private.refresh_authenticated_planning_input_after_rpc();
  return v_goal;
end;
$$;

revoke all on function public.save_primary_race_goal(
  uuid, text, text, date, integer, integer, integer, integer,
  integer, integer, integer, text
) from public, anon, authenticated, service_role;
grant execute on function public.save_primary_race_goal(
  uuid, text, text, date, integer, integer, integer, integer,
  integer, integer, integer, text
) to authenticated;

comment on function public.save_primary_race_goal(
  uuid, text, text, date, integer, integer, integer, integer,
  integer, integer, integer, text
) is 'Creates or revises a structured race goal and refreshes pending planning input after the mutation is visible.';
