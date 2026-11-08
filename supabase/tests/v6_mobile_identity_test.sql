-- Local role/RPC contract; real account sessions remain a separate gate.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(10);
select ok(not has_function_privilege('anon', 'public.get_v6_mobile_weekly_plan(uuid,integer)', 'execute'), 'anonymous plan projection denied');
select ok(not has_function_privilege('service_role', 'public.get_v6_mobile_weekly_plan(uuid,integer)', 'execute'), 'plan projection requires caller token');
select ok(not has_function_privilege('authenticated', 'public.get_v6_mobile_edit_retry(uuid,text)', 'execute'), 'edit retry remains server private');
select ok(not has_function_privilege('authenticated', 'private.v6_mobile_plan(uuid,jsonb)', 'execute'), 'owner parameter cannot be forged');
select ok(not has_function_privilege('authenticated', 'private.v6_mobile_workout(uuid,jsonb,uuid)', 'execute'), 'private mapping is inaccessible');
select ok(has_function_privilege('authenticated', 'public.get_v6_mobile_calendar(date,date)', 'execute'), 'caller calendar projection allowed');
select set_config('request.jwt.claims', '{"role":"authenticated","sub":"cccccccc-cccc-4ccc-8ccc-cccccccccccc"}', true);
set local role authenticated;
select throws_ok($$select public.get_v6_mobile_weekly_plan('cccccccc-cccc-4ccc-8ccc-cccccccccccc',1)$$,
  'P0002', 'weekly plan not found', 'missing/foreign owner plan is not disclosed');
select is((select count(*) from public.get_v6_mobile_calendar('2026-10-26','2026-11-02')), 0::bigint, 'another owner sees no calendar occurrences');
select throws_ok($$select public.get_v6_mobile_edit_retry('cccccccc-cccc-4ccc-8ccc-cccccccccccc','fixture')$$,
  '42501', null, 'caller cannot invoke service retry');
reset role;
set local role anon;
select throws_ok($$select public.get_v6_mobile_calendar('2026-10-26','2026-11-02')$$,
  '42501', null, 'anonymous calendar denied');
reset role;
select * from finish();
rollback;
