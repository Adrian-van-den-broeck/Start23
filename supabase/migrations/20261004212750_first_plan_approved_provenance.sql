-- Approval provenance is independent of the six-week activity/load window.
-- Keep historical load calculations and versions untouched.
create function public.get_plan_load_history_for_planning_v15(
  p_athlete_id uuid, p_before_week date
)
returns table (
  week_start date, phase text, target_basis text, planned_tss numeric,
  realized_tss numeric, planned_high_minutes numeric,
  planned_total_minutes numeric, realized_high_minutes numeric,
  realized_classified_minutes numeric, realized_total_minutes numeric,
  completed_activity_count bigint, sick_week boolean,
  reduced_realized_progression boolean, discipline_planned_tss jsonb,
  has_prior_approved_plan boolean
)
language plpgsql stable security definer set search_path = '' as $$
declare
  v_has_prior_approved_plan boolean;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;

  -- Approval sets this owner-scoped composite foreign-key pointer. Superseded
  -- historical plans retain it. Pending plans and activity rows cannot set it.
  select exists (
    select 1 from public.weekly_plans plan
    join public.plan_revisions revision
      on revision.plan_id = plan.id
     and revision.athlete_id = plan.athlete_id
     and revision.revision_number = plan.active_revision
    where plan.athlete_id = p_athlete_id
      and plan.week_start < p_before_week
      and revision.state in ('active', 'superseded')
  ) into v_has_prior_approved_plan;

  return query
  select history.*, v_has_prior_approved_plan
  from public.get_plan_load_history_for_planning_v14(
    p_athlete_id, p_before_week
  ) history;
end;
$$;
revoke all on function public.get_plan_load_history_for_planning_v15(uuid, date)
  from public, anon, authenticated, service_role;
grant execute on function public.get_plan_load_history_for_planning_v15(uuid, date)
  to service_role;
