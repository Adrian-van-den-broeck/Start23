-- Prospective registration ledger. Never infer skipped status from absent data.
create table private.workout_registration_events (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  planned_workout_id uuid not null,
  revision integer not null check (revision > 0),
  status text not null check (status in ('skipped','unknown')),
  created_at timestamptz not null default statement_timestamp(),
  unique (planned_workout_id, revision),
  foreign key (planned_workout_id, athlete_id) references public.planned_workouts(id, athlete_id) on delete cascade
);
create index workout_registration_owner_idx on private.workout_registration_events(athlete_id, planned_workout_id, revision desc);
create index workout_registration_opaque_idx on private.workout_registration_events(internal_athlete_id);
create trigger r3_00_sync_opaque_athlete_owner before insert or update on private.workout_registration_events
  for each row execute function private.sync_dual_athlete_owner_keys();
create trigger workout_registration_immutable before update or delete on private.workout_registration_events
  for each row execute function private.realized_v2_immutable();
alter table private.workout_registration_events enable row level security;
alter table private.workout_registration_events force row level security;
revoke all on private.workout_registration_events from public, anon, authenticated, service_role;
grant select, insert on private.workout_registration_events to service_role;

create function public.get_workout_registration(p_workout_id uuid)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_workout public.planned_workouts; v_event private.workout_registration_events;
begin
  if (select auth.uid()) is null then raise exception 'authentication required' using errcode = '42501'; end if;
  select workout.* into v_workout from public.planned_workouts workout
    join public.weekly_plans plan on plan.id = workout.plan_id and plan.athlete_id = workout.athlete_id
    join public.plan_revisions revision on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
    where workout.id = p_workout_id and workout.athlete_id = (select auth.uid())
      and revision.revision_number = plan.active_revision and revision.state in ('active','superseded')
      and workout.status <> 'cancelled';
  if not found then raise exception 'planned workout not found' using errcode = 'P0002'; end if;
  select * into v_event from private.workout_registration_events where planned_workout_id = p_workout_id
    and athlete_id = v_workout.athlete_id order by revision desc limit 1;
  return jsonb_build_object('planned_workout_id', p_workout_id, 'plan_revision_id', v_workout.revision_id,
    'registration_revision', coalesce(v_event.revision, 0), 'status', coalesce(v_event.status, 'unknown'));
end;
$$;

create function public.confirm_workout_registration(p_workout_id uuid, p_revision_id uuid, p_expected_registration_revision integer, p_status text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_context jsonb; v_workout public.planned_workouts; v_plan public.weekly_plans;
begin
  if (select auth.uid()) is null then raise exception 'authentication required' using errcode = '42501'; end if;
  -- Lock plan, then exact occurrence. Both
  -- registration and activity creation serialize on this occurrence below.
  select plan.* into v_plan from public.weekly_plans plan join public.planned_workouts workout
    on workout.plan_id = plan.id and workout.athlete_id = plan.athlete_id
    where workout.id = p_workout_id and workout.athlete_id = (select auth.uid()) for update of plan;
  if not found then raise exception 'planned workout not found' using errcode = 'P0002'; end if;
  select * into v_workout from public.planned_workouts where id = p_workout_id and athlete_id = (select auth.uid()) for update;
  v_context := public.get_workout_registration(p_workout_id);
  if v_workout.revision_id is distinct from p_revision_id then
    raise exception 'activity correction is stale' using errcode = '40001';
  end if;
  if p_status is null or p_status not in ('skipped','unknown') or p_expected_registration_revision is null then
    raise exception 'invalid registration status' using errcode = '23514';
  end if;
  if exists (select 1 from public.activities where planned_workout_id = p_workout_id and athlete_id = v_workout.athlete_id) then
    raise exception 'planned workout already matched' using errcode = '40001';
  end if;
  -- Same desired state is an idempotent retry, even after a lost response.
  if v_context ->> 'status' = p_status then return v_context; end if;
  if (v_context ->> 'registration_revision')::integer <> p_expected_registration_revision then
    raise exception 'activity correction is stale' using errcode = '40001';
  end if;
  insert into private.workout_registration_events(athlete_id, planned_workout_id, revision, status)
    values (v_workout.athlete_id, p_workout_id, p_expected_registration_revision + 1, p_status);
  return public.get_workout_registration(p_workout_id);
end;
$$;
revoke all on function public.get_workout_registration(uuid) from public, anon, authenticated, service_role;
revoke all on function public.confirm_workout_registration(uuid, uuid, integer, text) from public, anon, authenticated, service_role;
grant execute on function public.get_workout_registration(uuid) to authenticated;
grant execute on function public.confirm_workout_registration(uuid, uuid, integer, text) to authenticated;

-- An activity cannot race an explicit skipped decision. This covers every
-- canonical/provider/match RPC without changing any historical activity row.
create function private.guard_skipped_workout_activity() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_status text;
begin
  if new.planned_workout_id is null then return new; end if;
  perform 1 from public.weekly_plans plan join public.planned_workouts workout
    on workout.plan_id = plan.id and workout.athlete_id = plan.athlete_id
    where workout.id = new.planned_workout_id and workout.athlete_id = new.athlete_id for update of plan;
  perform 1 from public.planned_workouts where id = new.planned_workout_id and athlete_id = new.athlete_id for update;
  select status into v_status from private.workout_registration_events
    where planned_workout_id = new.planned_workout_id and athlete_id = new.athlete_id order by revision desc limit 1;
  if v_status = 'skipped' then raise exception 'activity correction is stale' using errcode = '40001'; end if;
  return new;
end;
$$;
create trigger realized_v2_guard_skipped_activity before insert or update of planned_workout_id on public.activities
  for each row execute function private.guard_skipped_workout_activity();
revoke all on function private.guard_skipped_workout_activity() from public, anon, authenticated, service_role;

-- v13-v15 are preserved for historical readers. v16 provides raw evidence,
-- never a silently trusted SUM. Deterministic Python evaluates consumer policy.
create function public.get_plan_load_history_for_planning_v16(p_athlete_id uuid, p_before_week date)
returns setof jsonb language plpgsql stable security definer set search_path = '' as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  return query
  select to_jsonb(history) || jsonb_build_object('weekly_registration', jsonb_build_object(
    'policy', 'weekly-registration-2', 'expected_known', revision.id is not null,
    'expected_occurrences', coalesce(expected.ids, '[]'::jsonb),
    'registrations', coalesce(evidence.rows, '[]'::jsonb) || coalesce(skipped.rows, '[]'::jsonb)))
  from public.get_plan_load_history_for_planning_v15(p_athlete_id, p_before_week) history
  left join public.weekly_plans plan on plan.athlete_id = p_athlete_id and plan.week_start = history.week_start
  left join public.plan_revisions revision on revision.plan_id = plan.id and revision.athlete_id = plan.athlete_id
    and revision.revision_number = plan.active_revision and revision.state in ('active','superseded')
  left join lateral (
    select jsonb_agg(workout.id order by workout.id) as ids from public.planned_workouts workout
      where workout.revision_id = revision.id and workout.athlete_id = p_athlete_id and workout.status <> 'cancelled'
  ) expected on true
  left join lateral (
    select jsonb_agg(jsonb_build_object(
      'activity_id', activity.id, 'occurrence_id', activity.planned_workout_id,
      'status', case when activity.rpe is null then 'awaiting_feedback'
        when calculation.realized_tss is not null and load.realized_tss is not null then 'partial_observed'
        when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.load_status = 'complete' then 'measured'
        when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.load_status = 'partial_observed' then 'partial_observed'
        when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.load_status = 'estimated_from_average_hr' then 'estimated'
        when calculation.realized_tss is not null then 'estimated' else 'unavailable' end,
      'value', case when activity.rpe is null then null
        when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.realized_tss is not null then load.realized_tss::text
        else calculation.realized_tss::text end,
      'method', case when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.realized_tss is not null then load.calculation_method
        when calculation.realized_tss is not null then calculation.calculation_method else 'unavailable' end,
      'version', case when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.realized_tss is not null then load.ruleset_version
        when calculation.realized_tss is not null then calculation.calculation_version else 'unavailable' end,
      'eligible', activity.rpe is not null and not (calculation.realized_tss is not null and load.realized_tss is not null) and coalesce(
        (load.ruleset_version = 'phase-13-joren-ruleset-1' and load.load_status in ('complete','estimated_from_average_hr') and load.realized_tss is not null)
        or (load.realized_tss is null and calculation.planner_eligible), false),
      'calculation_id', case when calculation.realized_tss is not null and load.realized_tss is null then calculation.id::text
        else activity.id::text || ':' || coalesce(load.ruleset_version, 'unavailable') || ':' || coalesce(activity.rpe::text, 'pending') end
    ) order by activity.id) as rows
    from public.activities activity
    left join private.activity_loads load on load.activity_id = activity.id and load.athlete_id = activity.athlete_id
    left join lateral (select c.* from private.realized_v2_calculations c where c.activity_id = activity.id and c.athlete_id = activity.athlete_id
      and c.rpe = activity.rpe order by c.revision desc limit 1) calculation on true
    where activity.athlete_id = p_athlete_id and
      (activity.started_at at time zone activity.timezone)::date between history.week_start and history.week_start + 6
  ) evidence on true
  left join lateral (
    select jsonb_agg(jsonb_build_object('activity_id', null, 'occurrence_id', workout.id,
      'status', 'skipped', 'value', null, 'method', 'explicit_skipped', 'version', 'weekly-registration-2',
      'eligible', true, 'calculation_id', event.id::text) order by workout.id) as rows
    from public.planned_workouts workout
    join lateral (select e.* from private.workout_registration_events e where e.planned_workout_id = workout.id and e.athlete_id = workout.athlete_id
      order by e.revision desc limit 1) event on event.status = 'skipped'
    where workout.revision_id = revision.id and workout.athlete_id = p_athlete_id and workout.status <> 'cancelled'
  ) skipped on true
  order by history.week_start;
end;
$$;
revoke all on function public.get_plan_load_history_for_planning_v16(uuid, date) from public, anon, authenticated, service_role;
grant execute on function public.get_plan_load_history_for_planning_v16(uuid, date) to service_role;
