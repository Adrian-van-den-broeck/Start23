-- Session A: execute only in the kit-created disposable container.
set application_name='wombo_a5_session_a';
begin;
set local statement_timeout='45s';
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
insert into a5_release_probe.receipts(session,result)
select 'A', public.create_weekly_plan_proposal_v3('a0000000-0000-0000-0000-0000000000a5',payload)
from a5_release_probe.payload;
\echo A_GENERATED_START_SESSION_B_NOW
select pg_sleep(15);
commit;
