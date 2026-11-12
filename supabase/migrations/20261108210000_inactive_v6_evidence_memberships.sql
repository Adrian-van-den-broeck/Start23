-- Inactive V6: append-only revision membership, never evidence reassignment.
create table private.v6_revision_memberships (
  revision_id uuid not null,
  athlete_id uuid not null references auth.users(id) on delete cascade,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  parent_revision_id uuid not null,
  planned_workout_id uuid not null,
  occurrence_id uuid not null,
  ordinal integer not null check (ordinal > 0),
  primary key (revision_id, occurrence_id),
  unique (revision_id, planned_workout_id),
  unique (revision_id, ordinal),
  foreign key (revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade,
  foreign key (parent_revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade,
  foreign key (planned_workout_id, athlete_id) references public.planned_workouts(id, athlete_id) on delete cascade
);
create index v6_membership_physical_owner_idx on private.v6_revision_memberships(planned_workout_id, athlete_id);
create index v6_membership_parent_idx on private.v6_revision_memberships(parent_revision_id, athlete_id);
create index v6_membership_opaque_idx on private.v6_revision_memberships(internal_athlete_id);
create index v6_membership_owner_idx on private.v6_revision_memberships(athlete_id);
alter table private.v6_revision_memberships enable row level security;
alter table private.v6_revision_memberships force row level security;
revoke all on private.v6_revision_memberships from public, anon, authenticated, service_role;
create trigger r3_00_sync_opaque_athlete_owner before insert or update on private.v6_revision_memberships
  for each row execute function private.sync_dual_athlete_owner_keys();
create trigger v6_membership_immutable before update or delete on private.v6_revision_memberships
  for each row execute function private.realized_v2_immutable();

create view private.v6_revision_occurrences as
  select planned_workout_id, revision_id, athlete_id, internal_athlete_id, occurrence_id, ordinal
    from private.v6_occurrence_snapshots
  union all
  select planned_workout_id, revision_id, athlete_id, internal_athlete_id, occurrence_id, ordinal
    from private.v6_revision_memberships;
revoke all on private.v6_revision_occurrences from public, anon, authenticated, service_role;

create function private.guard_v6_membership_scope() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if not exists (
    select 1 from public.plan_revisions child
    join public.plan_revisions parent on parent.plan_id = child.plan_id and parent.athlete_id = child.athlete_id
    join public.planned_workouts physical on physical.plan_id = child.plan_id and physical.athlete_id = child.athlete_id
    join private.v6_revision_occurrences member on member.revision_id = parent.id
      and member.athlete_id = parent.athlete_id and member.planned_workout_id = physical.id
    join private.v6_plan_snapshots frozen on frozen.revision_id = parent.id and frozen.athlete_id = parent.athlete_id
    where child.id = new.revision_id and child.athlete_id = new.athlete_id
      and child.state = 'draft' and child.source = 'athlete_move'
      and child.planning_ruleset_version = 'joren-v6-automatic-selection-1'
      and parent.id = new.parent_revision_id and parent.state = 'active'
      and parent.revision_number < child.revision_number
      and physical.id = new.planned_workout_id and member.occurrence_id = new.occurrence_id and member.ordinal = new.ordinal
  ) or exists (select 1 from private.v6_occurrence_snapshots native
    where native.revision_id = new.revision_id and
      (native.occurrence_id = new.occurrence_id or native.ordinal = new.ordinal or native.planned_workout_id = new.planned_workout_id)) then
    raise exception 'V6 revision membership scope is invalid' using errcode = '23514';
  end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_membership_scope() from public, anon, authenticated, service_role;
create trigger v6_membership_scope before insert on private.v6_revision_memberships
  for each row execute function private.guard_v6_membership_scope();

-- Reject overlap whichever of the native/member rows is inserted first.
create function private.guard_v6_native_membership() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if not exists (select 1 from public.planned_workouts w where w.id = new.planned_workout_id
    and w.athlete_id = new.athlete_id and w.revision_id = new.revision_id)
    or exists (select 1 from private.v6_revision_memberships m where m.revision_id = new.revision_id
      and (m.occurrence_id = new.occurrence_id or m.ordinal = new.ordinal or m.planned_workout_id = new.planned_workout_id)) then
    raise exception 'V6 native membership scope is invalid' using errcode = '23514';
  end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_native_membership() from public, anon, authenticated, service_role;
create trigger v6_native_membership_scope before insert on private.v6_occurrence_snapshots
  for each row execute function private.guard_v6_native_membership();

-- Internal row projection only. The origin physical row is never changed.
-- Invoker read RPCs retain their existing execution boundary and owner filters.
create function private.v6_revision_workouts(p_owner uuid)
returns setof public.planned_workouts language plpgsql stable security definer set search_path = '' as $$
begin
  if p_owner is null or ((select auth.uid()) is distinct from p_owner
    and coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role') then
    raise exception 'workout owner authorization required' using errcode = '42501';
  end if;
  return query select w.* from public.planned_workouts w where w.athlete_id = p_owner
    union all
    select (jsonb_populate_record(null::public.planned_workouts,
      to_jsonb(w) || jsonb_build_object('revision_id', m.revision_id))).*
    from private.v6_revision_memberships m join public.planned_workouts w
      on w.id = m.planned_workout_id and w.athlete_id = m.athlete_id
    where m.athlete_id = p_owner;
end;
$$;
revoke all on function private.v6_revision_workouts(uuid) from public, anon, authenticated, service_role;
grant execute on function private.v6_revision_workouts(uuid) to authenticated, service_role;

create function private.v6_active_workout_member(p_owner uuid, p_workout uuid)
returns boolean language plpgsql stable security definer set search_path = '' as $$
begin
  if p_owner is null or ((select auth.uid()) is distinct from p_owner
    and coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role') then
    raise exception 'workout owner authorization required' using errcode = '42501';
  end if;
  return exists (select 1 from public.planned_workouts w
    join public.weekly_plans p on p.id = w.plan_id and p.athlete_id = w.athlete_id
    join public.plan_revisions r on r.plan_id = p.id and r.athlete_id = p.athlete_id
      and r.revision_number = p.active_revision and r.state = 'active'
    where w.id = p_workout and w.athlete_id = p_owner and
      (w.revision_id = r.id or exists (select 1 from private.v6_revision_memberships m
        where m.revision_id = r.id and m.athlete_id = p_owner and m.planned_workout_id = w.id)));
end;
$$;
revoke all on function private.v6_active_workout_member(uuid,uuid) from public, anon, authenticated, service_role;

-- An existing evidence FK must be a member of a successor before activation.
-- Legacy corrective generation has no approved V6 membership writer and stays closed.
create function private.guard_v6_evidence_preservation() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_previous uuid;
begin
  select r.id into v_previous from public.weekly_plans p join public.plan_revisions r
    on r.plan_id = p.id and r.athlete_id = p.athlete_id and r.revision_number = p.active_revision
    join private.v6_plan_snapshots s on s.revision_id = r.id and s.athlete_id = r.athlete_id
    where p.id = new.plan_id and p.athlete_id = new.athlete_id;
  if v_previous is null then return new; end if;
  if tg_op = 'INSERT' and new.planning_ruleset_version is distinct from 'joren-v6-automatic-selection-1' then
    raise exception 'V6 revision membership is required' using errcode = 'PT409';
  end if;
  if tg_op = 'UPDATE' and old.state is distinct from 'active' and new.state = 'active' and exists (
    select 1 from private.v6_revision_workouts(new.athlete_id) w where w.revision_id = v_previous
      and (w.status <> 'scheduled' or exists (select 1 from public.activities a where a.planned_workout_id = w.id)
        or exists (select 1 from private.workout_registration_events e where e.planned_workout_id = w.id))
      and not exists (select 1 from private.v6_revision_workouts(new.athlete_id) successor
        where successor.revision_id = new.id and successor.id = w.id)
  ) then
    raise exception 'V6 evidence membership is stale' using errcode = 'PT409';
  end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_evidence_preservation() from public, anon, authenticated, service_role;
create trigger v6_evidence_preservation before insert or update of state on public.plan_revisions
  for each row execute function private.guard_v6_evidence_preservation();

-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_weekly_plan(p_plan_id uuid, p_revision integer DEFAULT NULL::integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE
 SET search_path TO ''
AS $function$
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
      from private.v6_revision_workouts(v_athlete_id) workout
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
$function$;


-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_calendar(p_from date, p_to date)
 RETURNS SETOF jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
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
  join private.v6_revision_workouts((select auth.uid())) workout
    on workout.revision_id = revision.id
   and workout.athlete_id = plan.athlete_id
  where plan.athlete_id = (select auth.uid())
    and workout.scheduled_date >= p_from
    and workout.scheduled_date < p_to
  order by workout.scheduled_date, workout.id;
$function$;


-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_calendar_rest_days(p_from date, p_to date)
 RETURNS SETOF jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
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
      from private.v6_revision_workouts((select auth.uid())) workout
      where workout.revision_id = revision.id
        and workout.athlete_id = plan.athlete_id
        and workout.status <> 'cancelled'
        and workout.scheduled_date = day.local_date
    )
  order by day.local_date;
$function$;


-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_plan_load_history_for_planning_v14(p_athlete_id uuid, p_before_week date)
 RETURNS TABLE(week_start date, phase text, target_basis text, planned_tss numeric, realized_tss numeric, planned_high_minutes numeric, planned_total_minutes numeric, realized_high_minutes numeric, realized_classified_minutes numeric, realized_total_minutes numeric, completed_activity_count bigint, sick_week boolean, reduced_realized_progression boolean, discipline_planned_tss jsonb)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role'
        and (select auth.uid()) is distinct from p_athlete_id then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  return query
  select
    history.week_start, history.phase, history.target_basis,
    history.planned_tss, history.realized_tss,
    history.planned_high_minutes, history.planned_total_minutes,
    history.realized_high_minutes, history.realized_classified_minutes,
    history.realized_total_minutes, history.completed_activity_count,
    history.sick_week, history.reduced_realized_progression,
    coalesce((
      select jsonb_object_agg(by_sport.discipline, by_sport.planned)
      from (
        select workout.discipline, sum(load.planned_tss) as planned
        from public.weekly_plans plan
        join public.plan_revisions revision
          on revision.plan_id = plan.id
         and revision.athlete_id = plan.athlete_id
         and revision.revision_number = plan.active_revision
        join private.v6_revision_workouts(p_athlete_id) workout
          on workout.revision_id = revision.id
         and workout.athlete_id = plan.athlete_id
        join private.planned_workout_loads load
          on load.planned_workout_id = workout.id
         and load.athlete_id = plan.athlete_id
        where plan.athlete_id = p_athlete_id
          and plan.week_start = history.week_start
        group by workout.discipline
      ) by_sport
    ), '{}'::jsonb)
  from public.get_plan_load_history_for_planning_v13(
    p_athlete_id, p_before_week
  ) history;
end;
$function$;


-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_plan_load_history_for_planning_v16(p_athlete_id uuid, p_before_week date)
 RETURNS SETOF jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
  -- Direct EXECUTE remains service-only. The owner clause supports the narrow
  -- internal approval trigger; it returns no private evidence to the caller.
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role'
    and (select auth.uid()) is distinct from p_athlete_id then
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
    select jsonb_agg(workout.id order by workout.id) as ids from private.v6_revision_workouts(p_athlete_id) workout
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
        when calculation.realized_tss is not null then calculation.calculation_method else coalesce(load.calculation_method, 'unavailable') end,
      'version', case when load.ruleset_version = 'phase-13-joren-ruleset-1' and load.realized_tss is not null then load.ruleset_version
        when calculation.realized_tss is not null then calculation.calculation_version else coalesce(load.ruleset_version, 'unavailable') end,
      'eligible', activity.rpe is not null and not (calculation.realized_tss is not null and load.realized_tss is not null) and coalesce(
        (load.ruleset_version = 'phase-13-joren-ruleset-1' and load.load_status in ('complete','estimated_from_average_hr') and load.realized_tss is not null)
        or (load.realized_tss is null and calculation.planner_eligible), false)
        -- An unmatched import is not proof of distinct extra work. Keep its
        -- observed value/provenance, but hold until identity is resolved.
        and not (activity.planned_workout_id is null and exists (
          select 1 from private.provider_activity_imports imported
          where imported.activity_id = activity.id and imported.athlete_id = activity.athlete_id)),
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
    from private.v6_revision_workouts(p_athlete_id) workout
    join lateral (select e.* from private.workout_registration_events e where e.planned_workout_id = workout.id and e.athlete_id = workout.athlete_id
      order by e.revision desc limit 1) event on event.status = 'skipped'
    where workout.revision_id = revision.id and workout.athlete_id = p_athlete_id and workout.status <> 'cancelled'
  ) skipped on true
  order by history.week_start;
end;
$function$;


-- Effective revision membership, same original authorization boundary.
CREATE OR REPLACE FUNCTION public.get_v6_move_workout_context(p_workout_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_plan uuid; v_revision integer;
begin
  if (select auth.uid()) is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select p.id, r.revision_number into v_plan, v_revision
    from public.weekly_plans p
    join public.plan_revisions r on r.plan_id = p.id and r.athlete_id = p.athlete_id
      and r.revision_number = p.active_revision and r.state = 'active'
    join private.v6_revision_workouts((select auth.uid())) w on w.revision_id = r.id and w.athlete_id = p.athlete_id
    left join private.v6_revision_occurrences m on m.planned_workout_id = w.id and m.athlete_id = w.athlete_id and m.revision_id = w.revision_id
    where p.athlete_id = (select auth.uid()) and (w.id = p_workout_id or m.occurrence_id = p_workout_id);
  if not found then raise exception 'planned workout not found' using errcode = 'P0002'; end if;
  return jsonb_build_object('plan', public.get_v6_mobile_weekly_plan(v_plan, v_revision));
end;
$function$;


create or replace function private.v6_public_plan(p_athlete_id uuid, p_plan_id uuid, p_revision integer)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_claims text; v_sub text; v_result jsonb;
begin
  if not exists (select 1 from public.weekly_plans where id = p_plan_id and athlete_id = p_athlete_id) then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  v_claims := current_setting('request.jwt.claims', true);
  v_sub := current_setting('request.jwt.claim.sub', true);
  perform set_config('request.jwt.claim.sub', p_athlete_id::text, true);
  perform set_config('request.jwt.claims', jsonb_build_object('sub', p_athlete_id, 'role', 'authenticated')::text, true);
  v_result := public.get_weekly_plan(p_plan_id, p_revision);
  perform set_config('request.jwt.claims', coalesce(v_claims, '{}'), true);
  perform set_config('request.jwt.claim.sub', coalesce(v_sub, ''), true);
  return jsonb_set(v_result, '{workouts}', (
    select coalesce(jsonb_agg(jsonb_set(w.value, '{id}', to_jsonb(coalesce(m.occurrence_id,
      (w.value ->> 'id')::uuid))) order by coalesce(m.ordinal, w.ordinality)), '[]'::jsonb)
    from jsonb_array_elements(v_result -> 'workouts') with ordinality w(value, ordinality)
    left join private.v6_revision_occurrences m on m.planned_workout_id = (w.value ->> 'id')::uuid
      and m.athlete_id = p_athlete_id and m.revision_id = (v_result ->> 'revision_id')::uuid
  ));
end;
$$;
revoke all on function private.v6_public_plan(uuid, uuid, integer) from public, anon, authenticated, service_role;


CREATE OR REPLACE FUNCTION private.v6_mobile_workout(p_owner uuid, p_workout jsonb, p_revision uuid DEFAULT NULL::uuid)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  select coalesce((
    select jsonb_set(p_workout, '{id}', to_jsonb(m.occurrence_id))
      || jsonb_build_object('physical_workout_id', m.planned_workout_id)
    from private.v6_revision_occurrences m
    where m.athlete_id = p_owner
      and ((p_revision is null and m.planned_workout_id = (p_workout ->> 'id')::uuid)
        or (m.revision_id = p_revision and m.occurrence_id = (p_workout ->> 'id')::uuid))
    limit 1
  ), p_workout);
$function$;

CREATE OR REPLACE FUNCTION public.create_activity_summary_r6_pre_idempotency(p_idempotency_key uuid, p_request_fingerprint text, p_payload jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
      raise exception 'activity idempotency key reused' using errcode = 'PT409';
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

    where workout.id = (p_payload ->> 'planned_workout_id')::uuid
      and workout.athlete_id = v_athlete_id
      and private.v6_active_workout_member(v_athlete_id, workout.id);
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
      raise exception 'planned workout already matched' using errcode = 'PT409';
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
      high_intensity_minutes,
      zone_minutes
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
      (v_metrics ->> 'high_intensity_minutes')::numeric,
      case when v_metrics -> 'zone_minutes' is null then null else
        array(select jsonb_array_elements_text(v_metrics -> 'zone_minutes')::numeric) end
    );
  end if;

  return private.activity_public_json(v_activity_id, v_athlete_id);
end;
$function$;

CREATE OR REPLACE FUNCTION public.confirm_activity_planned_workout_match(p_activity_id uuid, p_planned_workout_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_athlete_id uuid := (select auth.uid());
  v_activity public.activities;
  v_workout public.planned_workouts;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select * into v_activity from public.activities
  where id = p_activity_id and athlete_id = v_athlete_id for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.planned_workout_id is not null then
    raise exception 'activity is already matched' using errcode = 'PT409';
  end if;
  if v_activity.processing_state <> 'awaiting_rpe' then
    raise exception 'activity match window closed' using errcode = 'PT409';
  end if;
  select workout.* into v_workout
  from public.planned_workouts workout
  join public.plan_revisions revision
    on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
  where workout.id = p_planned_workout_id
    and workout.athlete_id = v_athlete_id
    and private.v6_active_workout_member(v_athlete_id, workout.id)
    and workout.status = 'scheduled';
  if not found then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  if v_workout.discipline <> v_activity.discipline then
    raise exception 'activity discipline does not match planned workout'
      using errcode = '23514';
  end if;
  if exists (
    select 1 from public.activities
    where planned_workout_id = p_planned_workout_id
  ) then
    raise exception 'planned workout already matched' using errcode = 'PT409';
  end if;
  update public.activities set
    planned_workout_id = p_planned_workout_id,
    match_status = 'matched',
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = v_athlete_id;
  return private.activity_public_json(p_activity_id, v_athlete_id);
end;
$function$;

CREATE OR REPLACE FUNCTION public.get_workout_registration(p_workout_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_workout public.planned_workouts; v_event private.workout_registration_events;
begin
  if (select auth.uid()) is null then raise exception 'authentication required' using errcode = '42501'; end if;
  select workout.* into v_workout from public.planned_workouts workout
    join public.weekly_plans plan on plan.id = workout.plan_id and plan.athlete_id = workout.athlete_id
    join public.plan_revisions revision on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
    where workout.id = p_workout_id and workout.athlete_id = (select auth.uid())
      and private.v6_active_workout_member((select auth.uid()), workout.id)
      and workout.status <> 'cancelled';
  if not found then raise exception 'planned workout not found' using errcode = 'P0002'; end if;
  select * into v_event from private.workout_registration_events where planned_workout_id = p_workout_id
    and athlete_id = v_workout.athlete_id order by revision desc limit 1;
  return jsonb_build_object('planned_workout_id', p_workout_id, 'plan_revision_id', v_workout.revision_id,
    'registration_revision', coalesce(v_event.revision, 0), 'status', coalesce(v_event.status, 'unknown'));
end;
$function$;

CREATE OR REPLACE FUNCTION private.guard_skipped_workout_activity()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_status text;
begin
  if new.planned_workout_id is null then return new; end if;
  perform 1 from public.weekly_plans plan join public.planned_workouts workout
    on workout.plan_id = plan.id and workout.athlete_id = plan.athlete_id
    where workout.id = new.planned_workout_id and workout.athlete_id = new.athlete_id for no key update of plan;
  -- Recheck after acquiring the plan lock: an approval may have superseded the
  -- occurrence after the original create/match RPC's validation query.
  if not exists (select 1 from public.planned_workouts workout
    join public.weekly_plans plan on plan.id = workout.plan_id and plan.athlete_id = workout.athlete_id
    join public.plan_revisions revision on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
    where workout.id = new.planned_workout_id and workout.athlete_id = new.athlete_id
      and private.v6_active_workout_member(new.athlete_id, workout.id)
      and workout.status <> 'cancelled') then
    raise exception 'activity correction is stale' using errcode = 'PT409';
  end if;
  perform 1 from public.planned_workouts where id = new.planned_workout_id and athlete_id = new.athlete_id for update;
  select status into v_status from private.workout_registration_events
    where planned_workout_id = new.planned_workout_id and athlete_id = new.athlete_id order by revision desc limit 1;
  if v_status = 'skipped' then raise exception 'activity correction is stale' using errcode = 'PT409'; end if;
  return new;
end;
$function$;

CREATE OR REPLACE FUNCTION public.move_v6_planned_workout(p_athlete_id uuid, p_payload jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_plan public.weekly_plans; v_old public.plan_revisions; v_snapshot private.v6_plan_snapshots;
  v_new uuid := gen_random_uuid(); v_number integer; v_workout record; v_physical uuid;
  v_result jsonb; v_payload jsonb; v_key text := p_payload ->> 'operation_key';
  v_date date := (p_payload ->> 'scheduled_date')::date;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select * into v_plan from public.weekly_plans
    where id = (p_payload ->> 'plan_id')::uuid and athlete_id = p_athlete_id;
  if not found then raise exception 'weekly plan not found' using errcode = 'P0002'; end if;
  perform pg_advisory_xact_lock(hashtextextended(p_athlete_id::text || ':' || v_plan.week_start::text, 0));
  select result into v_result from private.v6_edit_results
    where athlete_id = p_athlete_id and operation_key = v_key;
  if found then
    if v_result -> 'move_request' is distinct from p_payload then
      raise exception 'idempotency key payload mismatch' using errcode = 'PT409';
    end if;
    return jsonb_set(v_result, '{plan}', private.v6_mobile_plan(p_athlete_id, v_result -> 'plan')) - 'move_request';
  end if;
  -- Same proposal -> revision -> plan row-lock order as approval and V6 edits.
  perform 1 from public.change_proposals c join public.plan_revisions r
    on r.id = c.target_plan_revision_id and r.athlete_id = c.athlete_id
    where r.plan_id = v_plan.id and r.athlete_id = p_athlete_id and c.state = 'pending'
    order by c.id for update of c;
  perform 1 from public.plan_revisions where plan_id = v_plan.id and athlete_id = p_athlete_id
    and state = 'pending_approval' order by id for update;
  select * into v_old from public.plan_revisions where id = (p_payload ->> 'revision_id')::uuid
    and plan_id = v_plan.id and athlete_id = p_athlete_id for update;
  select * into v_plan from public.weekly_plans where id = v_plan.id and athlete_id = p_athlete_id for update;
  if v_old.id is null or v_old.state is distinct from 'active' or v_plan.state is distinct from 'active'
    or v_plan.active_revision is distinct from (p_payload ->> 'expected_revision')::integer
    or v_old.revision_number is distinct from v_plan.active_revision
    or exists (select 1 from public.plan_revisions where plan_id = v_plan.id and athlete_id = p_athlete_id
      and state = 'pending_approval') then
    raise exception 'plan revision is stale' using errcode = 'PT409';
  end if;
  select * into v_snapshot from private.v6_plan_snapshots where revision_id = v_old.id and athlete_id = p_athlete_id;
  if not found then raise exception 'weekly plan not found' using errcode = 'P0002'; end if;
  if v_snapshot.input_snapshot is distinct from private.build_phase_8_5_planning_input_snapshot(p_athlete_id)
    or exists (select 1 from public.injury_restrictions i join private.v6_revision_workouts(p_athlete_id) w
      on w.athlete_id = i.athlete_id and w.discipline = i.discipline
      where i.athlete_id = p_athlete_id and i.cleared_at is null and w.revision_id = v_old.id
        and (i.allowed_intensity = 'none' or w.intensity_bucket <> 'low')) then
    raise exception 'planning input is stale' using errcode = 'PT409';
  end if;
  if v_date is null or not (v_date between v_plan.week_start and v_plan.week_start + 6)
    or not (v_date = any(v_old.available_dates)) then
    raise exception 'workout move must remain in confirmed availability' using errcode = 'PT409';
  end if;
  if not exists (select 1 from private.v6_revision_occurrences m
    join private.v6_revision_workouts(p_athlete_id) w on w.id = m.planned_workout_id and w.athlete_id = m.athlete_id
    where m.revision_id = v_old.id and m.athlete_id = p_athlete_id
      and m.occurrence_id = (p_payload ->> 'occurrence_id')::uuid
      and m.planned_workout_id = (p_payload ->> 'physical_workout_id')::uuid and w.status = 'scheduled') then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  -- Existing activity/registration writers acquire this plan lock before evidence.
  -- Preserve every sibling by reference; evidence on the target still blocks moving it.
  if exists (select 1 from private.v6_revision_workouts(p_athlete_id) w where w.revision_id = v_old.id and w.id = (p_payload ->> 'physical_workout_id')::uuid and
    (w.status <> 'scheduled' or exists (select 1 from public.activities a where a.planned_workout_id = w.id)
      or exists (select 1 from private.workout_registration_events e where e.planned_workout_id = w.id))) then
    raise exception 'recorded workout move unsupported' using errcode = 'PT409';
  end if;
  perform private.assert_current_planning_eligibility(private.resolve_opaque_athlete_id(p_athlete_id));
  perform set_config('start23.critical_write', 'on', true);
  select coalesce(max(revision_number), 0) + 1 into v_number from public.plan_revisions
    where plan_id = v_plan.id and athlete_id = p_athlete_id;
  insert into public.plan_revisions select (jsonb_populate_record(null::public.plan_revisions,
    to_jsonb(v_old) || jsonb_build_object('id', v_new, 'revision_number', v_number,
      'state', 'draft', 'source', 'athlete_move', 'generation_fingerprint', v_key,
      'created_at', statement_timestamp()))).*;
  for v_workout in select w.*, m.occurrence_id, m.ordinal from private.v6_revision_workouts(p_athlete_id) w
    join private.v6_revision_occurrences m on m.planned_workout_id = w.id and m.athlete_id = w.athlete_id and m.revision_id = w.revision_id
    where w.revision_id = v_old.id and w.athlete_id = p_athlete_id order by m.ordinal loop
    if v_workout.id <> (p_payload ->> 'physical_workout_id')::uuid then
      insert into private.v6_revision_memberships(revision_id, athlete_id, parent_revision_id,
        planned_workout_id, occurrence_id, ordinal)
      values(v_new, p_athlete_id, v_old.id, v_workout.id, v_workout.occurrence_id, v_workout.ordinal);
      v_physical := v_workout.id;
    else
    v_physical := gen_random_uuid();
    insert into public.planned_workouts select (jsonb_populate_record(null::public.planned_workouts,
      to_jsonb(v_workout) || jsonb_build_object('id', v_physical, 'revision_id', v_new,
        'created_at', statement_timestamp(),
        'scheduled_date', case when v_workout.id = (p_payload ->> 'physical_workout_id')::uuid then v_date else v_workout.scheduled_date end,
        'scheduled_at', case when v_workout.id = (p_payload ->> 'physical_workout_id')::uuid
          then (v_date + time '12:00') at time zone v_plan.timezone else v_workout.scheduled_at end))).*;
    insert into private.v6_occurrence_snapshots(planned_workout_id, revision_id, athlete_id, occurrence_id, ordinal)
      values(v_physical, v_new, p_athlete_id, v_workout.occurrence_id, v_workout.ordinal);
    insert into private.planned_workout_loads select (jsonb_populate_record(null::private.planned_workout_loads,
      to_jsonb(l) || jsonb_build_object('planned_workout_id', v_physical))).*
      from private.planned_workout_loads l where planned_workout_id = v_workout.id;
    end if;
    insert into public.plan_warnings select (jsonb_populate_record(null::public.plan_warnings,
      to_jsonb(w) || jsonb_build_object('id', gen_random_uuid(), 'revision_id', v_new,
        'planned_workout_id', v_physical))).* from public.plan_warnings w
      where revision_id = v_old.id and planned_workout_id = v_workout.id;
  end loop;
  insert into private.plan_revision_loads select (jsonb_populate_record(null::private.plan_revision_loads,
    to_jsonb(l) || jsonb_build_object('revision_id', v_new))).* from private.plan_revision_loads l where revision_id = v_old.id;
  insert into public.plan_warnings select (jsonb_populate_record(null::public.plan_warnings,
    to_jsonb(w) || jsonb_build_object('id', gen_random_uuid(), 'revision_id', v_new))).*
    from public.plan_warnings w where revision_id = v_old.id and planned_workout_id is null;
  v_payload := jsonb_set(v_snapshot.payload, '{workouts}', (select jsonb_agg(
    case when w ->> 'occurrence_id' = p_payload ->> 'occurrence_id' then w || jsonb_build_object(
      'scheduled_date', v_date, 'scheduled_at', (v_date + time '12:00') at time zone v_plan.timezone) else w end order by n)
    from jsonb_array_elements(v_snapshot.payload -> 'workouts') with ordinality rows(w,n)));
  insert into private.v6_plan_snapshots(revision_id, athlete_id, payload, input_snapshot)
    values(v_new, p_athlete_id, v_payload, v_snapshot.input_snapshot);
  insert into private.realized_v2_plan_evidence select (jsonb_populate_record(null::private.realized_v2_plan_evidence,
    to_jsonb(e) || jsonb_build_object('revision_id', v_new))).* from private.realized_v2_plan_evidence e where revision_id = v_old.id;
  update public.plan_revisions set state = 'superseded' where id = v_old.id;
  update public.plan_revisions set state = 'active' where id = v_new;
  update public.weekly_plans set active_revision = v_number where id = v_plan.id
    and active_revision = (p_payload ->> 'expected_revision')::integer;
  if not found then raise exception 'plan revision is stale' using errcode = 'PT409'; end if;
  v_result := jsonb_build_object('plan', private.v6_public_plan(p_athlete_id, v_plan.id, v_number),
    'proposal', null, 'move_request', p_payload);
  insert into private.v6_edit_results(athlete_id, operation_key, revision_id, result)
    values(p_athlete_id, v_key, v_new, v_result);
  return jsonb_set(v_result, '{plan}', private.v6_mobile_plan(p_athlete_id, v_result -> 'plan')) - 'move_request';
end;
$function$;

notify pgrst, 'reload schema';

-- Version-aware read of already stored V6 revision loads. No recalculation.
CREATE OR REPLACE FUNCTION public.get_plan_load_history_for_planning_v13(p_athlete_id uuid, p_before_week date)
 RETURNS TABLE(week_start date, phase text, target_basis text, planned_tss numeric, realized_tss numeric, planned_high_minutes numeric, planned_total_minutes numeric, realized_high_minutes numeric, realized_classified_minutes numeric, realized_total_minutes numeric, completed_activity_count bigint, sick_week boolean, reduced_realized_progression boolean)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role'
        and (select auth.uid()) is distinct from p_athlete_id then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  return query
  with earliest_evidence as (
    select min(evidence.local_week) as local_week
    from (
      select plan.week_start as local_week
      from public.weekly_plans plan
      where plan.athlete_id = p_athlete_id
      union all
      select
        (activity.started_at at time zone activity.timezone)::date
        - extract(
            isodow
            from (activity.started_at at time zone activity.timezone)::date
          )::integer + 1
      from public.activities activity
      where activity.athlete_id = p_athlete_id
    ) evidence
  ), complete_weeks as (
    select (p_before_week - (series.value * 7))::date as local_week
    from generate_series(1, 6) as series(value)
    cross join earliest_evidence earliest
    where earliest.local_week is not null
      and p_before_week - (series.value * 7) >= earliest.local_week
  )
  select
    week.local_week,
    coalesce(revision.phase, 'base'),
    coalesce(revision.target_basis, 'realized_baseline'),
    coalesce(revision_load.planned_tss, 0),
    case
      when activity_summary.activity_count = 0 then 0::numeric
      else activity_summary.realized_tss
    end,
    coalesce(
      revision.total_duration_minutes * revision.high_intensity_percent / 100,
      0
    ),
    coalesce(revision.total_duration_minutes, 0),
    activity_summary.realized_high_minutes,
    activity_summary.realized_classified_minutes,
    activity_summary.realized_total_minutes,
    activity_summary.activity_count,
    coalesce(feedback.payload -> 'missed_workout_reasons' ? 'illness', false),
    coalesce(feedback.payload ->> 'fatigue_level' <> 'none', false)
      or coalesce(jsonb_array_length(feedback.payload -> 'missed_workout_reasons') > 0, false)
  from complete_weeks week
  left join public.weekly_plans plan
    on plan.athlete_id = p_athlete_id
   and plan.week_start = week.local_week
  left join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  left join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = plan.athlete_id
   and (revision_load.ruleset_version = 'phase-13-joren-ruleset-1'
     or (revision.planning_ruleset_version = 'joren-v6-automatic-selection-1'
       and revision_load.ruleset_version = 'joren-v6-automatic-selection-1'))
  left join lateral (
    select context.payload from public.weekly_checkin_contexts context
    join public.weekly_checkins checkin on checkin.id = context.checkin_id
      and checkin.athlete_id = context.athlete_id
    where checkin.athlete_id = p_athlete_id and checkin.week_start = week.local_week + 7
      and context.state = 'confirmed'
  ) feedback on true
  left join lateral (
    select
      count(activity.id) as activity_count,
      sum(activity_load.realized_tss) as realized_tss,
      sum(metric.high_intensity_minutes) as realized_high_minutes,
      sum(metric.low_intensity_minutes + metric.high_intensity_minutes)
        as realized_classified_minutes,
      sum(activity.duration_minutes) filter (
        where activity_load.activity_id is not null
      ) as realized_total_minutes
    from public.activities activity
    left join private.activity_loads activity_load
      on activity_load.activity_id = activity.id
     and activity_load.athlete_id = activity.athlete_id
     and activity_load.ruleset_version = 'phase-13-joren-ruleset-1'
    left join public.activity_metrics metric
      on metric.activity_id = activity.id
     and metric.athlete_id = activity.athlete_id
     and activity_load.activity_id is not null
    where activity.athlete_id = p_athlete_id
      and (activity.started_at at time zone activity.timezone)::date
        between week.local_week and week.local_week + 6
  ) activity_summary on true
  where revision.id is null or revision_load.ruleset_version = 'phase-13-joren-ruleset-1'
    or (revision.planning_ruleset_version = 'joren-v6-automatic-selection-1'
      and revision_load.ruleset_version = 'joren-v6-automatic-selection-1')
  order by week.local_week;
end;
$function$;
