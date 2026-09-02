begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_10_1_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_10_1_tap_results to authenticated, service_role;
grant usage, select on sequence phase_10_1_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_10_1_tap_results (result)
select has_table(
  'public', 'swipe_week_drafts',
  'server-authoritative swipe drafts are persisted'
);
insert into phase_10_1_tap_results (result)
select col_type_is(
  'public', 'swipe_week_drafts', 'available_dates', 'date[]',
  'draft availability remains date-only'
);
insert into phase_10_1_tap_results (result)
select col_type_is(
  'public', 'swipe_week_drafts', 'placements', 'jsonb',
  'manual placement is a bounded date map'
);
insert into phase_10_1_tap_results (result)
select ok(
  (select relrowsecurity and relforcerowsecurity
   from pg_class where oid = 'public.swipe_week_drafts'::regclass),
  'swipe drafts have forced RLS'
);
insert into phase_10_1_tap_results (result)
select has_trigger(
  'public', 'swipe_week_drafts', 'swipe_week_drafts_require_rpc',
  'direct critical draft writes require a trusted RPC context'
);
insert into phase_10_1_tap_results (result)
select has_trigger(
  'public', 'swipe_week_drafts', 'swipe_week_drafts_validate',
  'draft state and composition are database-validated'
);
insert into phase_10_1_tap_results (result)
select has_function(
  'public', 'create_swipe_week_draft', array['uuid', 'jsonb'],
  'draft creation has a bounded backend RPC'
);
insert into phase_10_1_tap_results (result)
select has_function(
  'public', 'update_swipe_week_draft',
  array['uuid', 'uuid', 'bigint', 'jsonb'],
  'draft transitions have a stale-safe backend RPC'
);
insert into phase_10_1_tap_results (result)
select ok(
  not (select prosecdef from pg_proc where oid =
    'public.create_swipe_week_draft(uuid,jsonb)'::regprocedure)
  and not (select prosecdef from pg_proc where oid =
    'public.update_swipe_week_draft(uuid,uuid,bigint,jsonb)'::regprocedure),
  'backend draft RPCs remain security invoker'
);
insert into phase_10_1_tap_results (result)
select ok(
  has_function_privilege(
    'service_role', 'public.create_swipe_week_draft(uuid,jsonb)', 'execute'
  )
  and has_function_privilege(
    'service_role',
    'public.update_swipe_week_draft(uuid,uuid,bigint,jsonb)', 'execute'
  )
  and not has_function_privilege(
    'authenticated', 'public.create_swipe_week_draft(uuid,jsonb)', 'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.update_swipe_week_draft(uuid,uuid,bigint,jsonb)', 'execute'
  ),
  'only the trusted backend can mutate draft state'
);
insert into phase_10_1_tap_results (result)
select ok(
  has_table_privilege('authenticated', 'public.swipe_week_drafts', 'select')
  and not has_table_privilege(
    'authenticated', 'public.swipe_week_drafts', 'insert'
  )
  and not has_table_privilege(
    'authenticated', 'public.swipe_week_drafts', 'update'
  )
  and not has_table_privilege(
    'authenticated', 'public.swipe_week_drafts', 'delete'
  )
  and not has_table_privilege('anon', 'public.swipe_week_drafts', 'select'),
  'table grants expose owner reads and no direct athlete or anonymous writes'
);
insert into phase_10_1_tap_results (result)
select ok(
  has_table_privilege('service_role', 'public.workout_templates', 'select')
  and not has_table_privilege('service_role', 'auth.users', 'select'),
  'the backend can validate public templates without broad auth.users access'
);
insert into phase_10_1_tap_results (result)
select is(
  (select count(*)::integer from information_schema.columns
   where table_schema = 'public' and table_name = 'swipe_week_drafts'
     and lower(column_name) like '%tss%'),
  0,
  'durable swipe state contains no TSS column'
);

insert into auth.users (id)
values
  ('a1000000-0000-0000-0000-000000000001'),
  ('b1000000-0000-0000-0000-000000000002');

select set_config('start23.critical_write', 'on', true);
insert into public.initial_plan_requests (
  id, athlete_id, status, onboarding_revision, ruleset_version,
  input_snapshot, input_fingerprint
)
select
  'a1100000-0000-0000-0000-000000000001',
  'a1000000-0000-0000-0000-000000000001',
  'pending', 1, 'phase-3-ruleset-2', snapshot, md5(snapshot::text)
from (
  select jsonb_build_object(
    'profile', jsonb_build_object(
      'athlete_id', 'a1000000-0000-0000-0000-000000000001',
      'timezone', 'UTC', 'revision', 1
    ),
    'training_history', '[]'::jsonb,
    'goal', jsonb_build_object(
      'target_date', '2026-12-06',
      'race_discipline_profile', array['swim', 'bike', 'run'],
      'revision', 1
    ),
    'zones', '[]'::jsonb,
    'ruleset_version', 'phase-3-ruleset-2'
  ) as snapshot
) source;

insert into public.swipe_week_drafts (
  id, athlete_id, initial_plan_request_id, base_plan_revision,
  context_plan_revision, week_start, timezone, available_dates,
  availability_source, input_fingerprint, context_fingerprint,
  ruleset_version, target_workout_count, target_composition,
  current_template_id
)
select
  'a1200000-0000-0000-0000-000000000001',
  request.athlete_id, request.id, 0, null, '2026-09-07', 'UTC',
  array['2026-09-07', '2026-09-09', '2026-09-12']::date[],
  'explicit', request.input_fingerprint, repeat('b', 64),
  'phase-10-ruleset-1', 3,
  '{"swim":1,"bike":1,"run":1}'::jsonb,
  '51000000-0000-0000-0000-000000000001'
from public.initial_plan_requests request
where request.id = 'a1100000-0000-0000-0000-000000000001';
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"role":"service_role"}',
  true
);
set local role service_role;

insert into phase_10_1_tap_results (result)
select lives_ok(
  $$
    select public.create_swipe_week_draft(
      'a1000000-0000-0000-0000-000000000001',
      jsonb_build_object(
        'plan_id', null,
        'initial_plan_request_id', 'a1100000-0000-0000-0000-000000000001',
        'base_plan_revision', 0,
        'context_plan_revision', null,
        'week_start', '2026-09-14',
        'timezone', 'UTC',
        'available_dates', jsonb_build_array(
          '2026-09-14', '2026-09-16', '2026-09-19'
        ),
        'availability_source', 'explicit',
        'confirmed_injuries', '[]'::jsonb,
        'low_only_disciplines', '[]'::jsonb,
        'input_fingerprint', repeat('a', 32),
        'context_fingerprint', repeat('c', 64),
        'ruleset_version', 'phase-10-ruleset-1',
        'target_workout_count', 3,
        'target_composition', '{"swim":1,"bike":1,"run":1}'::jsonb,
        'current_template_id', '51000000-0000-0000-0000-000000000001',
        'state', 'collecting'
      )
    )
  $$,
  'the production service role can create a validated swipe draft'
);
insert into phase_10_1_tap_results (result)
select is(
  (select count(*) from public.swipe_week_drafts
   where week_start = '2026-09-14'),
  1::bigint,
  'the service-role RPC persists exactly one draft'
);

reset role;
select set_config('start23.critical_write', 'on', true);
delete from public.swipe_week_drafts where week_start = '2026-09-14';
select set_config('start23.critical_write', '', true);

select set_config(
  'request.jwt.claims',
  '{"sub":"a1000000-0000-0000-0000-000000000001","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a1000000-0000-0000-0000-000000000001';
set local role authenticated;

insert into phase_10_1_tap_results (result)
select is(
  (select count(*) from public.swipe_week_drafts),
  1::bigint,
  'the authenticated owner reads exactly their own open draft'
);
insert into phase_10_1_tap_results (result)
select throws_ok(
  $$ update public.swipe_week_drafts set placements = '{}' where true $$,
  '42501',
  null,
  'an athlete cannot write draft state directly'
);

select set_config(
  'request.jwt.claims',
  '{"sub":"b1000000-0000-0000-0000-000000000002","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'b1000000-0000-0000-0000-000000000002';

insert into phase_10_1_tap_results (result)
select is(
  (select count(*) from public.swipe_week_drafts),
  0::bigint,
  'another athlete cannot read the owner draft'
);

reset role;
select result
from (
  select sequence, result from phase_10_1_tap_results
  union all
  select 9223372036854775807, finish from finish()
) reported
order by sequence;
rollback;
