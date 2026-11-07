begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(4);
select ok(not exists (
  select 1 from generate_series(13,16) v
  where has_function_privilege('authenticated', format(
    'public.get_plan_load_history_for_planning_v%s(uuid,date)',v), 'execute')
    or has_function_privilege('anon', format(
      'public.get_plan_load_history_for_planning_v%s(uuid,date)',v), 'execute')
), 'all private history RPCs remain inaccessible to athletes and anonymous users');
select set_config('request.jwt.claims',
  '{"role":"authenticated","sub":"a6000000-0000-0000-0000-000000000006"}',true);
select lives_ok($$select private.realized_v2_history_evidence(
  'a6000000-0000-0000-0000-000000000006','2026-10-26')$$,
  'owner-bound internal approval evidence traverses the complete history chain');
select throws_ok($$select private.realized_v2_history_evidence(
  'b6000000-0000-0000-0000-000000000006','2026-10-26')$$,
  '42501','service role required','internal evidence rejects a foreign subject');
set local role authenticated;
select throws_ok($$select public.get_plan_load_history_for_planning_v15(
  'a6000000-0000-0000-0000-000000000006','2026-10-26')$$,
  '42501',null,'even the owner cannot invoke the private load RPC directly');
reset role;
select * from finish();
rollback;
