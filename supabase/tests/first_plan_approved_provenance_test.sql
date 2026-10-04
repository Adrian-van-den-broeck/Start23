begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
create temporary table provenance_tap_results (
  sequence bigint generated always as identity, result text not null
);
insert into provenance_tap_results(result) select plan(10);

insert into provenance_tap_results(result)
select ok(has_function_privilege('service_role',
  'public.get_plan_load_history_for_planning_v15(uuid,date)', 'execute'),
  'the private history reader is available to the trusted backend');
insert into provenance_tap_results(result)
select ok(not has_function_privilege('authenticated',
  'public.get_plan_load_history_for_planning_v15(uuid,date)', 'execute'),
  'athletes cannot read private provenance/load history');
insert into provenance_tap_results(result)
select ok(not has_function_privilege('anon',
  'public.get_plan_load_history_for_planning_v15(uuid,date)', 'execute'),
  'anonymous clients cannot read private provenance/load history');
insert into provenance_tap_results(result)
select ok(not has_table_privilege('service_role', 'public.weekly_plans', 'select'),
  'the new reader does not broaden direct table grants');
insert into provenance_tap_results(result)
select ok((select relrowsecurity and relforcerowsecurity from pg_class
  where oid = 'public.weekly_plans'::regclass), 'plan RLS remains enabled and forced');

select set_config('request.jwt.claims', '{"role":"authenticated"}', true);
insert into provenance_tap_results(result)
select throws_ok($q$select * from public.get_plan_load_history_for_planning_v15(
  'c0150000-0000-0000-0000-000000000001', '2026-10-05')$q$,
  '42501', 'trusted backend authorization required', 'JWT role is checked in the function');

insert into auth.users(id) values ('c0150000-0000-0000-0000-000000000001');
insert into public.athlete_profiles(
  athlete_id, timezone, timezone_source, timezone_confirmed_at, onboarding_status
)
values ('c0150000-0000-0000-0000-000000000001', 'Europe/Amsterdam',
  'manual', statement_timestamp(), 'in_progress');
select set_config('start23.critical_write', 'on', true);
insert into public.activities(
  id, athlete_id, idempotency_key, request_fingerprint, discipline,
  started_at, timezone, duration_minutes, match_status
) values (
  'c0150000-0000-0000-0000-000000000002',
  'c0150000-0000-0000-0000-000000000001',
  'c0150000-0000-0000-0000-000000000003', repeat('1',64), 'run',
  '2026-10-02T10:00:00Z', 'Europe/Amsterdam', 40, 'unmatched'
);
select set_config('start23.critical_write', '', true);
select set_config('request.jwt.claims', '{"role":"service_role"}', true);

insert into provenance_tap_results(result)
select is((select count(*) from public.get_plan_load_history_for_planning_v15(
  'c0150000-0000-0000-0000-000000000001', '2026-10-05')), 1::bigint,
  'activity-only calendar history is retained');
insert into provenance_tap_results(result)
select ok((select not has_prior_approved_plan
  from public.get_plan_load_history_for_planning_v15(
    'c0150000-0000-0000-0000-000000000001', '2026-10-05')),
  'activity without an approved revision is not approved-plan provenance');
insert into provenance_tap_results(result)
select results_eq(
  $q$select week_start, phase, target_basis, planned_tss, realized_tss,
    completed_activity_count from public.get_plan_load_history_for_planning_v15(
      'c0150000-0000-0000-0000-000000000001', '2026-10-05')$q$,
  $q$select week_start, phase, target_basis, planned_tss, realized_tss,
    completed_activity_count from public.get_plan_load_history_for_planning_v14(
      'c0150000-0000-0000-0000-000000000001', '2026-10-05')$q$,
  'historical physiology and activity data are passed through unchanged');
insert into provenance_tap_results(result)
select is((select count(*) from public.get_plan_load_history_for_planning_v15(
  'c0150000-0000-0000-0000-000000000009', '2026-10-05')), 0::bigint,
  'another athlete does not inherit activity history or approval provenance');

insert into provenance_tap_results(result) select * from finish();
select result from provenance_tap_results order by sequence;
rollback;
