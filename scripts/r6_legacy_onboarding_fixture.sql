-- Representative legacy completed-session fixture, only for a newly created
-- tagged R6 development Auth user. Never run against a real athlete account.
begin;
do $$
begin
  if not exists (
    select 1 from auth.users where id = '__R6_AUTH_ID__'::uuid
      and raw_user_meta_data ->> 'purpose' = 'phase-13-14-r6'
      and created_at > now() - interval '10 minutes'
  ) then
    raise exception 'R6 temporary-user guard failed';
  end if;
  perform set_config('start23.critical_write', 'on', true);
  insert into public.onboarding_sessions (
    athlete_id, status, current_step, completed_steps, completed_at,
    completed_onboarding_version, completed_ruleset_version
  ) values (
    '__R6_AUTH_ID__'::uuid, 'completed', 'completed',
    array['profile','history','goal','zones','review'], now() - interval '90 days',
    'legacy-unversioned', 'legacy-unversioned'
  );
end;
$$;
commit;
