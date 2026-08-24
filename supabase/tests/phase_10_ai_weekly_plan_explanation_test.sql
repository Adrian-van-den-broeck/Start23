begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(6);

select has_function(
  'public',
  'set_weekly_plan_proposal_explanation',
  array['uuid', 'uuid', 'text'],
  'bounded weekly-plan explanation function exists'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.set_weekly_plan_proposal_explanation(uuid,uuid,text)',
    'execute'
  ),
  'trusted backend may write qualitative plan explanations'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.set_weekly_plan_proposal_explanation(uuid,uuid,text)',
    'execute'
  ),
  'athletes cannot invoke the trusted explanation write directly'
);
select ok(
  not has_function_privilege(
    'anon',
    'public.set_weekly_plan_proposal_explanation(uuid,uuid,text)',
    'execute'
  ),
  'anonymous callers cannot invoke the trusted explanation write'
);

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

select throws_ok(
  $$
    select public.set_weekly_plan_proposal_explanation(
      'a0000000-0000-0000-0000-000000000010',
      'a1000000-0000-0000-0000-000000000010',
      'Je geplande TSS is 100.'
    )
  $$,
  '23514',
  'public coach explanation is invalid',
  'private-load language is rejected before proposal lookup'
);
select throws_ok(
  $$
    select public.set_weekly_plan_proposal_explanation(
      'a0000000-0000-0000-0000-000000000010',
      'a1000000-0000-0000-0000-000000000010',
      'Controleer dit weekvoorstel.'
    )
  $$,
  'P0002',
  'weekly plan proposal not found',
  'the writer remains owner and proposal scoped'
);

reset role;

select * from finish();
rollback;
