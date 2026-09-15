-- PostgreSQL executes triggers of the same timing/event in name order. The
-- original plan-revision eligibility trigger sorted before the R3 opaque-owner
-- synchronizer, so it saw NULL on inserts. Keep both guards enabled and order
-- identity derivation before eligibility validation.

drop trigger plan_revisions_r3_10_require_current_onboarding
on public.plan_revisions;

create trigger r3_10_require_current_onboarding
before insert or update on public.plan_revisions
for each row execute function private.enforce_current_planning_eligibility();
