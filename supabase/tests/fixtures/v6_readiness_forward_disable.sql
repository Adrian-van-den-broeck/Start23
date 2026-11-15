-- Disposable rehearsal only; NOT a production migration or backup restoration.
-- Covers the later A5 dispatch and frequency wrappers missed by the 2026-11-07
-- four-RPC fixture. Retain confirmed/pending state, evidence and owner reads.
begin;
do $$ begin
  if current_database() !~ '^wombo_v6_rollback_[0-9]+$'
    or inet_server_addr() is distinct from '127.0.0.1'::inet
    or current_setting('server_version_num')::integer / 10000 <> 17 then
    raise exception 'Explicit disposable loopback rollback database required';
  end if;
end; $$;

revoke execute on function
  public.create_v6_weekly_plan_proposal(uuid,jsonb),
  public.move_v6_planned_workout(uuid,jsonb),
  public.create_v6_frequency_swipe_draft(uuid,jsonb),
  public.update_v6_frequency_swipe_draft(uuid,uuid,integer,jsonb),
  public.create_v6_frequency_swipe_proposal(uuid,jsonb),
  public.get_inactive_v6_catalog_for_planning(),
  public.get_v6_plan_context_for_planning(uuid,uuid,integer),
  public.get_v6_edit_retry(uuid,text),
  public.get_v6_mobile_edit_retry(uuid,text),
  public.get_v6_frequency_context(uuid,date,text)
from service_role;

-- Shared historical create_weekly_plan_proposal_v3 dispatches directly into a
-- private SECURITY DEFINER writer. Revoking only the V6 public wrapper cannot
-- close that route. Guard persistence without withdrawing historical generation.
create function private.readiness_stop_new_v6_revisions() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  if new.planning_ruleset_version = 'joren-v6-automatic-selection-1' then
    raise exception 'V6 generation is disabled' using errcode = 'PT409';
  end if;
  return new;
end;
$$;
revoke all on function private.readiness_stop_new_v6_revisions()
from public,anon,authenticated,service_role;
create trigger a0_readiness_stop_new_v6_revisions
before insert or update of planning_ruleset_version on public.plan_revisions
for each row execute function private.readiness_stop_new_v6_revisions();

create function private.readiness_stop_v6_drafts() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  if new.ruleset_version = 'joren-v6-automatic-selection-1' then
    raise exception 'V6 generation is disabled' using errcode = 'PT409';
  end if;
  return new;
end;
$$;
revoke all on function private.readiness_stop_v6_drafts()
from public,anon,authenticated,service_role;
create trigger a0_readiness_stop_v6_drafts
before insert or update on public.swipe_week_drafts
for each row execute function private.readiness_stop_v6_drafts();
commit;
