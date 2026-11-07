-- Actual PostgreSQL catalog, grants, immutability and RLS tests; NOT EXECUTED here.
-- Run after migrations in a disposable local Supabase database. All rolls back.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();
select is((select count(*) from private.v6_source_revisions), 77::bigint, '77 exact inactive revisions');
select is((select count(*) from private.v6_source_revisions where activation <> 'INACTIVE'), 0::bigint, 'zero active revisions');
select is((select count(*) from private.v6_source_revisions where planned_tss <> official_decimal::numeric), 0::bigint, 'unscaled numeric equals canonical decimal');
select ok(not exists(select 1 from private.v6_source_revisions r join private.workout_template_loads l
  on l.template_id = r.template_id), 'historical catalog projection cannot see V6');
select throws_ok($$update private.v6_source_revisions set official_decimal = '0'$$,
  '55000', 'workout catalog versions are immutable', 'even an administrative source update is rejected');
select throws_ok($$update public.workout_templates set inactive_v6 = false where inactive_v6$$,
  '55000', 'workout catalog versions are immutable', 'no catalog activation mutation');
select ok(not has_table_privilege('service_role','private.v6_source_revisions','select'), 'no direct service catalog read grant');
select ok(not has_table_privilege('authenticated','private.v6_plan_snapshots','select'), 'no private athlete plan snapshots grant');
select ok(not has_table_privilege('authenticated','private.planned_workout_loads','select'), 'no private athlete load grant');
select ok(not has_function_privilege('authenticated','public.create_v6_weekly_plan_proposal(uuid,jsonb)','execute'), 'athletes cannot forge generated weeks');
select ok(not has_function_privilege('anon','public.get_v6_weekly_plan(uuid,integer)','execute'), 'anonymous reads are denied');
select ok(not has_function_privilege('authenticated','public.get_v6_edit_retry(uuid,text)','execute'), 'private retry projection is service only');
select ok(not has_function_privilege('service_role','private.v6_public_plan(uuid,uuid,integer)','execute'), 'internal owner projection is not externally callable');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.weekly_plans'::regclass), 'existing plan RLS forced');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.v6_source_revisions'::regclass), 'source RLS forced');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.v6_plan_snapshots'::regclass), 'frozen context RLS forced');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.v6_occurrence_snapshots'::regclass), 'occurrence RLS forced');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.v6_edit_results'::regclass), 'retry RLS forced');
select set_config('request.jwt.claims','{"role":"authenticated","sub":"a6000000-0000-0000-0000-000000000006"}',true);
set local role authenticated;
select is((select count(*) from public.workout_templates where inactive_v6), 0::bigint, 'direct SQL cannot see inactive catalog rows');
select throws_ok($$select public.get_inactive_v6_catalog_for_planning()$$, '42501', null, 'athlete cannot read private source/TSS catalog');
select throws_ok($$select public.create_v6_weekly_plan_proposal('a6000000-0000-0000-0000-000000000006','{}')$$,
  '42501', null, 'athlete cannot forge source/evidence context');
reset role;
select * from finish();
rollback;
