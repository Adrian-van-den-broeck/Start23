begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_column(
  'public',
  'onboarding_sessions',
  'completed_onboarding_version',
  'onboarding completion has an explicit version'
);
select has_column(
  'public',
  'onboarding_sessions',
  'completed_ruleset_version',
  'onboarding completion retains its ruleset version'
);
select has_table(
  'public',
  'onboarding_completion_records',
  'versioned completion history is durable'
);
select ok(
  (
    select relrowsecurity and relforcerowsecurity
    from pg_class
    where oid = 'public.onboarding_completion_records'::regclass
  ),
  'completion history has forced RLS'
);
select ok(
  has_table_privilege('authenticated', 'public.onboarding_completion_records', 'select'),
  'authenticated athletes can read their own completion history'
);
select ok(
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
select has_trigger(
  'public',
  'onboarding_completion_records',
  'onboarding_completion_records_require_rpc',
  'completion history inserts require the critical RPC context'
);
select has_trigger(
  'public',
  'onboarding_sessions',
  'onboarding_sessions_protect_completion_versions',
  'stored completion versions are RPC protected'
);
select ok(
  has_function_privilege(
    'authenticated',
    'public.complete_current_onboarding()',
    'execute'
  ),
  'authenticated athletes can invoke current version completion'
);
select ok(
  not has_function_privilege(
    'anon',
    'public.complete_current_onboarding()',
    'execute'
  ),
  'anonymous callers cannot invoke current version completion'
);

select * from finish();
rollback;
