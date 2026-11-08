begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(6);
select is((
  select count(*)::integer from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private') and p.prokind='f'
    and p.prosrc like '%errcode = ''40001''%'
    and p.proname not in ('prepare_polar_import_retry','record_polar_webhook','start_polar_import')
), 0, 'MVP business conflicts never deliberately raise serialization failure');
select is((
  select count(*)::integer from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private') and p.prokind='f'
    and p.prosrc like '%errcode = ''PT409''%'
-- Original 28 plus two A5 recovery functions, two V6 functions, and four V2
-- registration/evidence guards, plus the confirmed V6 move writer. No original business-conflict guard is removed.
), 37, 'all 37 inventoried MVP/V2/V6 implementations use nonretryable HTTP 409');
select ok((select pg_get_constraintdef(oid) like '%heart_rate_monitor%'
  and pg_get_constraintdef(oid) like '%timezone%'
  from pg_constraint where conrelid='public.onboarding_completion_records'::regclass
  and conname='onboarding_completion_records_steps_valid'),
  'completion history accepts both mandatory Phase 14 v2 operational steps');
select ok((
  select pg_get_functiondef(p.oid) like '%''onboarding_status'', session.status%'
    and pg_get_functiondef(p.oid) like '%''completed_onboarding_version''%'
    and pg_get_functiondef(p.oid) like '%''completed_ruleset_version''%'
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'get_checkin_context_for_planning'
), 'check-in planning context carries current completion provenance');
select is((
  select count(*)::integer from pg_constraint
  where contype = 'f'
    and confrelid = 'public.initial_plan_requests'::regclass
    and confdeltype = 'c'
), 4, 'every initial request dependent cascades during account deletion');
select is((
  select count(*)::integer from pg_constraint
  where contype = 'f'
    and confrelid = 'public.initial_plan_requests'::regclass
), 4, 'the complete initial request dependency inventory remains covered');
select * from finish();
rollback;
