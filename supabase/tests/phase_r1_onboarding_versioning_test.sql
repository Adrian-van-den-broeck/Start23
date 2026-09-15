begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_r1_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_r1_tap_results to authenticated, service_role;
grant usage, select on sequence phase_r1_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_r1_tap_results (result) select has_column(
  'public',
  'onboarding_sessions',
  'completed_onboarding_version',
  'onboarding completion has an explicit version'
);
insert into phase_r1_tap_results (result) select has_column(
  'public',
  'onboarding_sessions',
  'completed_ruleset_version',
  'onboarding completion retains its ruleset version'
);
insert into phase_r1_tap_results (result) select has_table(
  'public',
  'onboarding_completion_records',
  'versioned completion history is durable'
);
insert into phase_r1_tap_results (result) select ok(
  (
    select relrowsecurity and relforcerowsecurity
    from pg_class
    where oid = 'public.onboarding_completion_records'::regclass
  ),
  'completion history has forced RLS'
);
insert into phase_r1_tap_results (result) select ok(
  has_table_privilege('authenticated', 'public.onboarding_completion_records', 'select'),
  'authenticated athletes can read their own completion history'
);
insert into phase_r1_tap_results (result) select ok(
  not has_table_privilege(
    'authenticated',
    'public.onboarding_completion_records',
    'update'
  )
  and not has_table_privilege(
    'authenticated',
    'public.onboarding_completion_records',
    'delete'
  ),
  'completion history cannot be updated or deleted by athletes'
);
insert into phase_r1_tap_results (result) select has_trigger(
  'public',
  'onboarding_completion_records',
  'onboarding_completion_records_require_rpc',
  'completion history inserts require the critical RPC context'
);
insert into phase_r1_tap_results (result) select has_trigger(
  'public',
  'onboarding_sessions',
  'onboarding_sessions_protect_completion_versions',
  'stored completion versions are RPC protected'
);
insert into phase_r1_tap_results (result) select ok(
  has_function_privilege(
    'authenticated',
    'public.complete_current_onboarding(bigint)',
    'execute'
  ),
  'authenticated athletes can invoke current version completion'
);
insert into phase_r1_tap_results (result) select ok(
  not has_function_privilege(
    'anon',
    'public.complete_current_onboarding(bigint)',
    'execute'
  ),
  'anonymous callers cannot invoke current version completion'
);

insert into phase_r1_tap_results (result)
select * from finish();
select result from phase_r1_tap_results order by sequence;
rollback;
