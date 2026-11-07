-- Rehearsal fixture only. Never part of the deployable migration directory.
-- Preserve source/snapshot/evidence/receipt rows and authenticated historical RPCs.
begin;
do $$ begin
  if current_database() !~ '^wombo_v6_rollback_[0-9]+$' then
    raise exception 'Explicit disposable V6 rollback database required';
  end if;
end; $$;
revoke execute on function public.create_v6_weekly_plan_proposal(uuid,jsonb) from service_role;
revoke execute on function public.get_inactive_v6_catalog_for_planning() from service_role;
revoke execute on function public.get_v6_plan_context_for_planning(uuid,uuid,integer) from service_role;
revoke execute on function public.get_v6_edit_retry(uuid,text) from service_role;
-- Keep get_v6_weekly_plan so retained immutable confirmed locators stay readable.
commit;
