-- R6 MVP runtime remediation.
--
-- Weekly check-in planning uses the same immutable planning snapshot as initial
-- planning, but the service also requires the current completion provenance.
-- Return that provenance from the trusted context RPC.
--
-- Auth-account deletion cascades to initial_plan_requests and its dependent
-- owner rows in an implementation-defined order. Make every composite request
-- dependency cascade as well so the deletion cannot be blocked by that order.

create or replace function public.get_checkin_context_for_planning(
  p_athlete_id uuid,
  p_checkin_id uuid
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
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'checkin_id', checkin.id,
    'week_start', checkin.week_start,
    'timezone', checkin.timezone,
    'confirmed_context', context.payload,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = checkin.athlete_id
        and maintenance.status = 'active'
    ),
    'plan_id', plan.id,
    'active_revision', plan.active_revision,
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot,
    'onboarding_status', session.status,
    'completed_onboarding_version', session.completed_onboarding_version,
    'completed_ruleset_version', session.completed_ruleset_version
  )
  into v_result
  from public.weekly_checkins checkin
  join public.weekly_checkin_contexts context
    on context.checkin_id = checkin.id
   and context.athlete_id = checkin.athlete_id
   and context.state = 'confirmed'
  join lateral (
    select candidate.*
    from public.initial_plan_requests candidate
    where candidate.athlete_id = checkin.athlete_id
      and candidate.status in ('pending', 'consumed')
    order by candidate.refreshed_at desc
    limit 1
  ) request on true
  join public.onboarding_sessions session
    on session.athlete_id = checkin.athlete_id
  left join public.weekly_plans plan
    on plan.athlete_id = checkin.athlete_id
   and plan.week_start = checkin.week_start
  where checkin.id = p_checkin_id
    and checkin.athlete_id = p_athlete_id
    and checkin.status = 'open';
  if v_result is null then
    raise exception 'check-in context is not confirmed' using errcode = 'PT409';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_checkin_context_for_planning(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_checkin_context_for_planning(uuid, uuid)
to service_role;

alter table public.onboarding_sessions
  drop constraint onboarding_sessions_initial_plan_request_fkey,
  add constraint onboarding_sessions_initial_plan_request_fkey
    foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id)
    on delete cascade;

alter table public.plan_revisions
  drop constraint plan_revisions_initial_plan_request_id_athlete_id_fkey,
  add constraint plan_revisions_initial_plan_request_id_athlete_id_fkey
    foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id)
    on delete cascade;

alter table public.swipe_week_drafts
  drop constraint swipe_week_drafts_initial_plan_request_id_athlete_id_fkey,
  add constraint swipe_week_drafts_initial_plan_request_id_athlete_id_fkey
    foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id)
    on delete cascade;

alter table public.onboarding_completion_records
  drop constraint onboarding_completion_records_request_fkey,
  add constraint onboarding_completion_records_request_fkey
    foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id)
    on delete cascade;

comment on function public.get_checkin_context_for_planning(uuid, uuid) is
  'Returns trusted confirmed check-in, planning snapshot, and current onboarding completion provenance.';
