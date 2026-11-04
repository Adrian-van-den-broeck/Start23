-- Start while A holds its uncommitted generation; wait for A's commit.
set application_name='wombo_a5_session_b';
begin;
set local lock_timeout='30s';
set local statement_timeout='45s';
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
insert into a5_release_probe.receipts(session,result)
select 'B', public.create_weekly_plan_proposal_v3('a0000000-0000-0000-0000-0000000000a5',payload)
from a5_release_probe.payload;
commit;
