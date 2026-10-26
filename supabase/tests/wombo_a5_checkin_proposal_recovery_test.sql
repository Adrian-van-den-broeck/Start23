-- Run only against a fresh disposable local Supabase database. Entire suite rolls back.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select ok(has_function_privilege('authenticated',
  'public.get_checkin_plan_proposal(uuid)', 'execute') and
  not has_function_privilege('anon', 'public.get_checkin_plan_proposal(uuid)', 'execute') and
  not has_function_privilege('service_role', 'public.get_checkin_plan_proposal(uuid)', 'execute'),
  'replay uses the authenticated caller, not a service credential');
select ok(not (select prosecdef from pg_proc where oid =
  'public.get_checkin_plan_proposal(uuid)'::regprocedure), 'replay preserves invoker RLS');
select ok(not has_function_privilege('authenticated',
  'public.create_weekly_plan_proposal_v3(uuid,jsonb)', 'execute') and
  has_function_privilege('service_role',
  'public.create_weekly_plan_proposal_v3(uuid,jsonb)', 'execute'),
  'generation remains service only');
select ok((select prosrc like '%for update%' from pg_proc where oid =
  'public.create_weekly_plan_proposal_v3(uuid,jsonb)'::regprocedure),
  'generation acquires a check-in row lock (structural assertion, not a race test)');

insert into auth.users (id) values
  ('a0000000-0000-0000-0000-0000000000a5'),
  ('b0000000-0000-0000-0000-0000000000a5');
insert into public.athlete_profiles
  (athlete_id, timezone, timezone_source, timezone_confirmed_at, onboarding_status)
values ('a0000000-0000-0000-0000-0000000000a5', 'Europe/Amsterdam',
  'manual', statement_timestamp(), 'in_progress');
select set_config('start23.checkin_write', 'on', true);
insert into public.weekly_checkins (id, athlete_id, week_start, timezone) values
  ('c0000000-0000-0000-0000-0000000000a5',
   'a0000000-0000-0000-0000-0000000000a5', '2026-08-03', 'Europe/Amsterdam'),
  ('c1000000-0000-0000-0000-0000000000a5',
   'a0000000-0000-0000-0000-0000000000a5', '2026-08-10', 'Europe/Amsterdam');
select set_config('start23.checkin_write', '', true);
create temporary table a5_data (payload jsonb, result jsonb, snapshot jsonb);
grant select, update on a5_data to authenticated, service_role;
insert into a5_data (payload) values (jsonb_build_object(
  'checkin_id', 'c0000000-0000-0000-0000-0000000000a5',
  'expected_base_revision', 0, 'week_start', '2026-08-03',
  'timezone', 'Europe/Amsterdam', 'phase', 'base', 'target_basis', 'injury_rest_only',
  'input_fingerprint', repeat('a', 64), 'generation_fingerprint', repeat('b', 64),
  'total_duration_minutes', 0, 'low_intensity_percent', 0, 'high_intensity_percent', 0,
  'confirmed_injuries', '["run"]'::jsonb, 'low_only_disciplines', '[]'::jsonb,
  'goal_disciplines', '["run"]'::jsonb, 'availability', '[]'::jsonb,
  'available_dates', '[]'::jsonb, 'availability_source', 'checkin',
  'workouts', '[]'::jsonb, 'warnings', jsonb_build_array(jsonb_build_object(
    'rule_id', 'BR-010', 'code', 'all_disciplines_blocked_rest_only',
    'severity', 'warning', 'message', 'Rest only; confirmation required.')),
  'target_tss', 0, 'planned_tss', 0, 'ruleset_version', 'phase-13-joren-ruleset-1',
  'planning_ruleset_version', 'joren-planning-ruleset-2'
));

select set_config('request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-0000000000a5","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'a0000000-0000-0000-0000-0000000000a5';
set local role authenticated;
select is(public.get_checkin_plan_proposal('c0000000-0000-0000-0000-0000000000a5'),
  null::jsonb, 'an open ungenerated check-in permits generation');
reset role;

-- Force a failure at attachment, after nested plan/revision/load writes.
create function pg_temp.fail_a5_attachment() returns trigger language plpgsql as $$
begin raise exception 'synthetic attachment failure' using errcode = 'PT409'; end;
$$;
create trigger a5_fail_attachment before update on public.weekly_checkins
for each row when (new.status = 'completed') execute function pg_temp.fail_a5_attachment();
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
select throws_ok($$select public.create_weekly_plan_proposal_v3(
  'a0000000-0000-0000-0000-0000000000a5', (select payload from a5_data))$$,
  'PT409', 'synthetic attachment failure', 'partial creation rolls back on attachment failure');
reset role;
select is((select count(*) from public.plan_revisions where
  checkin_id = 'c0000000-0000-0000-0000-0000000000a5'), 0::bigint,
  'failed atomic operation left no revision');
select is((select count(*) from public.weekly_plans where
  athlete_id = 'a0000000-0000-0000-0000-0000000000a5'), 0::bigint,
  'failed atomic operation left no plan');
select is((select status from public.weekly_checkins where
  id = 'c0000000-0000-0000-0000-0000000000a5'), 'open', 'failed attachment left check-in open');
drop trigger a5_fail_attachment on public.weekly_checkins;
set local role service_role;
update a5_data set result = public.create_weekly_plan_proposal_v3(
  'a0000000-0000-0000-0000-0000000000a5', payload);
select is(public.create_weekly_plan_proposal_v3(
  'a0000000-0000-0000-0000-0000000000a5', (select payload from a5_data)),
  (select result from a5_data), 'repeated create returns identical persisted locator');
reset role;
select is((select count(*) from public.plan_revisions where
  checkin_id = 'c0000000-0000-0000-0000-0000000000a5'), 1::bigint,
  'one authoritative revision exists');
select is((select status from public.weekly_checkins where
  id = 'c0000000-0000-0000-0000-0000000000a5'), 'completed', 'creation attached atomically');
select ok((select plan_proposal_id::text = (result ->> 'proposal_id')
  from public.weekly_checkins cross join a5_data
  where id = 'c0000000-0000-0000-0000-0000000000a5'), 'exact proposal identity is attached');

select set_config('request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-0000000000a5","role":"authenticated"}', true);
set local role authenticated;
update a5_data set snapshot = public.get_checkin_plan_proposal(
  'c0000000-0000-0000-0000-0000000000a5');
select is(public.get_checkin_plan_proposal('c0000000-0000-0000-0000-0000000000a5'),
  (select snapshot from a5_data), 'retry retains complete snapshot including warnings and base revision');
select is((select snapshot #>> '{proposal,state}' from a5_data), 'pending', 'recovery does not approve');
select is((select snapshot #>> '{plan,active_revision}' from a5_data), null::text,
  'active revision remains unchanged');
select is((select jsonb_array_length(snapshot #> '{plan,warnings}') from a5_data), 1,
  'existing warning survives');
select throws_ok($$select public.get_checkin_plan_proposal(
  'd0000000-0000-0000-0000-0000000000a5')$$, 'P0002', 'weekly check-in not found', 'missing check-in is 404');
select public.reject_plan_proposal((select (result ->> 'proposal_id')::uuid from a5_data));
select is(public.get_checkin_plan_proposal('c0000000-0000-0000-0000-0000000000a5') #>> '{proposal,state}',
  'rejected', 'rejected attachment stays rejected');
select is(public.get_checkin_plan_proposal('c0000000-0000-0000-0000-0000000000a5') #>> '{proposal,id}',
  (select result ->> 'proposal_id' from a5_data), 'terminal replay keeps exact proposal ID');
reset role;
select set_config('request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-0000000000a5","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'b0000000-0000-0000-0000-0000000000a5';
set local role authenticated;
select throws_ok($$select public.get_checkin_plan_proposal(
  'c0000000-0000-0000-0000-0000000000a5')$$, 'P0002', 'weekly check-in not found',
  'foreign check-in and proposal identities remain undiscoverable');
reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
select is(public.create_weekly_plan_proposal_v3(
  'a0000000-0000-0000-0000-0000000000a5', (select payload from a5_data)),
  (select result from a5_data), 'terminal create replay does not create a replacement');
reset role;
select is((select count(*) from public.plan_revisions where
  checkin_id = 'c0000000-0000-0000-0000-0000000000a5'), 1::bigint,
  'terminal replay left historical revision count unchanged');
-- Pre-A5 persistence without attachment: reuse the unambiguous historical row.
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
update a5_data set payload = payload || jsonb_build_object(
  'checkin_id', 'c1000000-0000-0000-0000-0000000000a5',
  'week_start', '2026-08-10', 'generation_fingerprint', repeat('c', 64));
update a5_data set result = public.create_weekly_plan_proposal_v2(
  'a0000000-0000-0000-0000-0000000000a5', payload);
reset role;
select is((select status from public.weekly_checkins where
  id = 'c1000000-0000-0000-0000-0000000000a5'), 'open',
  'legacy persistence can precede attachment');
set local role service_role;
select is(public.create_weekly_plan_proposal_v3(
  'a0000000-0000-0000-0000-0000000000a5', (select payload from a5_data)),
  (select result from a5_data), 'legacy orphan is attached without replacement');
reset role;
select is((select count(*) from public.plan_revisions where
  checkin_id = 'c1000000-0000-0000-0000-0000000000a5'), 1::bigint,
  'orphan recovery preserves the revision');
select set_config('request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-0000000000a5","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'a0000000-0000-0000-0000-0000000000a5';
set local role authenticated;
select public.approve_plan_proposal((select (result ->> 'proposal_id')::uuid from a5_data), 0);
select is(public.get_checkin_plan_proposal('c1000000-0000-0000-0000-0000000000a5') #>> '{proposal,state}',
  'applied', 'approved attachment replays applied');
select is(public.get_checkin_plan_proposal('c1000000-0000-0000-0000-0000000000a5') #>> '{plan,revision_state}',
  'active', 'approved attachment returns actual active revision');
select is(public.get_checkin_plan_proposal('c1000000-0000-0000-0000-0000000000a5') #>> '{proposal,id}',
  (select result ->> 'proposal_id' from a5_data), 'approval preserves attached proposal ID');
reset role;
select * from finish();
rollback;
