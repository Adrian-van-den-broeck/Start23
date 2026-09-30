-- Joren planning ruleset 2. Historical catalog, plan and load rows stay intact.
-- The 154 source prescriptions are immutable: version 2 changes eligibility,
-- while version 1 remains attributable to already generated plans.

drop index public.workout_templates_source_reference_unique;
create unique index workout_templates_source_reference_version_unique
  on public.workout_templates (source_catalog, source_workout_id, version)
  where source_catalog is not null;

create temporary table joren_source_version_map on commit drop as
select old.id as old_id, gen_random_uuid() as new_id
from public.workout_templates old
where old.source_catalog = 'start23-v0.1' and old.version = 1;

do $$
begin
  if (select count(*) from joren_source_version_map) <> 154 then
    raise exception 'reviewed source catalog count changed' using errcode = '23514';
  end if;
end;
$$;

insert into public.workout_templates (
  id, template_key, version, discipline, name, description, duration_minutes,
  distance_meters, intensity_bucket, expected_rpe_min, expected_rpe_max,
  fallback_compatibility, explicit_scheduling_only, source_catalog,
  source_workout_id, athlete_selection_only
)
select
  map.new_id, old.template_key, old.version + 1, old.discipline, old.name,
  old.description, old.duration_minutes, old.distance_meters,
  old.intensity_bucket, old.expected_rpe_min, old.expected_rpe_max,
  old.fallback_compatibility, old.explicit_scheduling_only,
  old.source_catalog, old.source_workout_id, false
from joren_source_version_map map
join public.workout_templates old on old.id = map.old_id;

insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique
)
select
  map.new_id, segment.sequence, segment.name, segment.instructions,
  segment.duration_minutes, segment.distance_meters, segment.zone_number,
  segment.expected_rpe, segment.is_swim_technique
from joren_source_version_map map
join public.workout_segments segment on segment.template_id = map.old_id;

insert into public.workout_template_zone_requirements (template_id, requirement)
select map.new_id, requirement.requirement
from joren_source_version_map map
join public.workout_template_zone_requirements requirement
  on requirement.template_id = map.old_id;

insert into public.workout_template_phase_tags (template_id, phase)
select map.new_id, phase.phase
from joren_source_version_map map
join public.workout_templates old on old.id = map.old_id
cross join lateral (
  select unnest(
    case when exists (
      select 1 from public.workout_segments segment
      where segment.template_id = old.id and segment.zone_number > 2
    ) then array['build']::text[]
    else array['base', 'build', 'recovery', 'taper']::text[] end
  ) as phase
) phase;

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
)
select map.new_id, load.planned_tss, load.calculation_method, load.ruleset_version
from joren_source_version_map map
join private.workout_template_loads load on load.template_id = map.old_id;

do $$
declare v_template_id uuid;
begin
  for v_template_id in select new_id from joren_source_version_map loop
    perform private.validate_workout_template(v_template_id);
  end loop;
end;
$$;

alter table public.plan_revisions
  add column planning_ruleset_version text,
  add column cross_training_opt_ins text[] not null default '{}'
    check (cross_training_opt_ins <@ array['bike', 'swim']::text[]
      and not (cross_training_opt_ins && confirmed_injuries))
  ;
alter table public.plan_revisions
  add constraint plan_revisions_planning_ruleset_version_valid
  check (planning_ruleset_version is null or
    planning_ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$');
-- Historical revisions retain their existing ruleset_version. The new
-- planning provenance is populated only for proposals created by v3.

create function public.create_weekly_plan_proposal_v3(
  p_athlete_id uuid, p_payload jsonb
)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_result jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if p_payload ->> 'ruleset_version' <> 'phase-13-joren-ruleset-1'
     or p_payload ->> 'planning_ruleset_version' <>
       'joren-planning-ruleset-2' then
    raise exception 'planning ruleset provenance is invalid'
      using errcode = '23514';
  end if;
  if jsonb_typeof(coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb))
     <> 'array' then
    raise exception 'cross-training choice is invalid' using errcode = '23514';
  end if;
  v_result := public.create_weekly_plan_proposal_v2(p_athlete_id, p_payload);
  perform set_config('start23.critical_write', 'on', true);
  update public.plan_revisions
  set planning_ruleset_version = 'joren-planning-ruleset-2',
      cross_training_opt_ins = array(
        select jsonb_array_elements_text(
          coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb)
        )
      )
  where plan_id = (v_result ->> 'plan_id')::uuid
    and athlete_id = p_athlete_id
    and revision_number = (v_result ->> 'revision')::integer
    and (planning_ruleset_version is null
      or planning_ruleset_version = 'joren-planning-ruleset-2');
  if not found then
    raise exception 'planning revision provenance is invalid'
      using errcode = '23514';
  end if;
  return v_result;
end;
$$;
revoke all on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  to service_role;

alter table public.swipe_week_drafts
  add column current_occurrence_id uuid,
  add column accepted_occurrence_ids uuid[] not null default '{}',
  add column passed_occurrence_ids uuid[] not null default '{}',
  add column cross_training_opt_ins text[] not null default '{}'
    check (cross_training_opt_ins <@ array['bike', 'swim']::text[]
      and not (cross_training_opt_ins && confirmed_injuries));

alter table public.swipe_week_drafts
  drop constraint swipe_week_drafts_template_arrays_valid,
  add constraint swipe_week_drafts_template_arrays_valid check (
    cardinality(accepted_template_ids) <= target_workout_count
    and (
      ruleset_version = 'joren-planning-ruleset-2'
      or (
        not (accepted_template_ids && passed_template_ids)
        and (current_template_id is null or (
          not current_template_id = any(accepted_template_ids)
          and not current_template_id = any(passed_template_ids)
        ))
      )
    )
  );

drop trigger swipe_week_drafts_validate on public.swipe_week_drafts;
create trigger swipe_week_drafts_validate
before insert or update on public.swipe_week_drafts
for each row when (new.ruleset_version <> 'joren-planning-ruleset-2')
execute function private.validate_swipe_week_draft();

create function private.validate_swipe_week_draft_v2()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare
  v_accepted uuid[];
  v_passed uuid[];
  v_accepted_occurrences uuid[];
  v_passed_occurrences uuid[];
  v_discipline text;
  v_expected_count integer;
  v_actual_count integer;
  v_key text;
  v_date date;
begin
  if cardinality(new.available_dates) <> (
       select count(distinct value) from unnest(new.available_dates) value
     ) or exists (
    select 1 from unnest(new.available_dates) value
    where value is null or value not between new.week_start and new.week_start + 6
  ) then
    raise exception 'swipe draft dates must stay inside the local week'
      using errcode = '23514';
  end if;

  select
    coalesce(array_agg((entry.value ->> 'template_id')::uuid
      order by entry.ordinality) filter (
        where entry.value ->> 'action' = 'accept'), '{}'::uuid[]),
    coalesce(array_agg((entry.value ->> 'template_id')::uuid
      order by entry.ordinality) filter (
        where entry.value ->> 'action' = 'pass'), '{}'::uuid[]),
    coalesce(array_agg((entry.value ->> 'occurrence_id')::uuid
      order by entry.ordinality) filter (
        where entry.value ->> 'action' = 'accept'), '{}'::uuid[]),
    coalesce(array_agg((entry.value ->> 'occurrence_id')::uuid
      order by entry.ordinality) filter (
        where entry.value ->> 'action' = 'pass'), '{}'::uuid[])
  into v_accepted, v_passed, v_accepted_occurrences, v_passed_occurrences
  from jsonb_array_elements(new.decision_history)
    with ordinality entry(value, ordinality)
  where jsonb_typeof(entry.value) = 'object'
    and entry.value ->> 'action' in ('accept', 'pass')
    and entry.value ->> 'template_id' is not null
    and entry.value ->> 'occurrence_id' is not null;

  if v_accepted <> new.accepted_template_ids
     or v_passed <> new.passed_template_ids
     or cardinality(v_accepted) + cardinality(v_passed)
       <> jsonb_array_length(new.decision_history)
     or cardinality(v_accepted_occurrences) +
        cardinality(v_passed_occurrences)
       <> jsonb_array_length(new.decision_history)
     or (select count(distinct value) from unnest(
           v_accepted_occurrences || v_passed_occurrences
         ) value) <> jsonb_array_length(new.decision_history)
     or exists (
       select 1 from unnest(v_accepted || v_passed) value
       where value is null or not exists (
         select 1 from public.workout_templates template
         where template.id = value
       )
     ) then
    raise exception 'swipe occurrence history is inconsistent'
      using errcode = '23514';
  end if;

  new.accepted_occurrence_ids := v_accepted_occurrences;
  new.passed_occurrence_ids := v_passed_occurrences;
  if new.state = 'collecting' and new.current_template_id is not null then
    if tg_op = 'INSERT' then
      new.current_occurrence_id := gen_random_uuid();
    elsif old.current_template_id is distinct from new.current_template_id
       or old.decision_history is distinct from new.decision_history then
      new.current_occurrence_id := gen_random_uuid();
    end if;
  else
    new.current_occurrence_id := null;
  end if;
  if new.current_occurrence_id = any(
       v_accepted_occurrences || v_passed_occurrences
     ) then
    raise exception 'current swipe occurrence is already decided'
      using errcode = '23514';
  end if;

  foreach v_discipline in array array['swim', 'bike', 'run']::text[] loop
    v_expected_count := (new.target_composition ->> v_discipline)::integer;
    select count(*) into v_actual_count
    from unnest(new.accepted_template_ids) accepted(template_id)
    join public.workout_templates template on template.id = accepted.template_id
    where template.discipline = v_discipline;
    if v_actual_count > v_expected_count or (
      new.state in ('placement', 'submitted')
      and v_actual_count <> v_expected_count
    ) then
      raise exception 'swipe selection composition is invalid'
        using errcode = '23514';
    end if;
  end loop;

  for v_key, v_date in
    select entry.key, (entry.value #>> '{}')::date
    from jsonb_each(new.placements) entry
  loop
    if v_key::uuid <> all(v_accepted_occurrences)
       or v_date <> all(new.available_dates) then
      raise exception 'swipe occurrence placement is invalid'
        using errcode = '23514';
    end if;
  end loop;
  if new.state = 'submitted' and (
    select count(*) from jsonb_object_keys(new.placements)
  ) <> cardinality(v_accepted_occurrences) then
    raise exception 'submitted swipe layout is incomplete'
      using errcode = '23514';
  end if;
  return new;
end;
$$;
revoke all on function private.validate_swipe_week_draft_v2()
  from public, anon, authenticated, service_role;
create trigger swipe_week_drafts_validate_v2
before insert or update on public.swipe_week_drafts
for each row when (new.ruleset_version = 'joren-planning-ruleset-2')
execute function private.validate_swipe_week_draft_v2();

-- Historical private load provenance remains Phase 13. New planning uses the
-- previous approved sport snapshots only to bound injury redistribution.
create function public.get_plan_load_history_for_planning_v14(
  p_athlete_id uuid, p_before_week date
)
returns table (
  week_start date, phase text, target_basis text, planned_tss numeric,
  realized_tss numeric, planned_high_minutes numeric,
  planned_total_minutes numeric, realized_high_minutes numeric,
  realized_classified_minutes numeric, realized_total_minutes numeric,
  completed_activity_count bigint, sick_week boolean,
  reduced_realized_progression boolean, discipline_planned_tss jsonb
)
language plpgsql stable security definer set search_path = '' as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
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
        join public.planned_workouts workout
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
$$;
revoke all on function public.get_plan_load_history_for_planning_v14(uuid, date)
  from public, anon, authenticated, service_role;
grant execute on function public.get_plan_load_history_for_planning_v14(uuid, date)
  to service_role;

create function public.create_swipe_week_draft_v2(
  p_athlete_id uuid, p_payload jsonb
)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  v_row public.swipe_week_drafts;
  v_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if jsonb_typeof(coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb))
     <> 'array' then
    raise exception 'cross-training choice is invalid' using errcode = '23514';
  end if;
  v_id := (public.create_swipe_week_draft(p_athlete_id, p_payload) ->> 'id')::uuid;
  perform set_config('start23.critical_write', 'on', true);
  update public.swipe_week_drafts
  set cross_training_opt_ins = array(
    select jsonb_array_elements_text(
      coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb)
    )
  )
  where id = v_id and athlete_id = p_athlete_id
  returning * into v_row;
  if not found then
    raise exception 'swipe draft not found' using errcode = 'P0002';
  end if;
  return to_jsonb(v_row) - 'athlete_id';
end;
$$;
revoke all on function public.create_swipe_week_draft_v2(uuid, jsonb)
  from public, anon, authenticated, service_role;
grant execute on function public.create_swipe_week_draft_v2(uuid, jsonb)
  to service_role;
