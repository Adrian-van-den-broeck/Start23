-- Representative legacy completed-session fixture for a newly created,
-- tagged R6 development Auth user. Never run against a real athlete account.
-- Keep this as one statement for the linked CLI query endpoint.
with guarded_actor as materialized (
  select
    users.id as auth_user_id,
    set_config('start23.critical_write', 'on', true) as critical_write
  from auth.users users
  join private.athlete_identity_map mapping on mapping.auth_user_id = users.id
  where users.id = '__R6_AUTH_ID__'::uuid
    and users.raw_user_meta_data ->> 'purpose' = 'phase-13-14-r6'
    and users.created_at > now() - interval '10 minutes'
)
insert into public.onboarding_sessions (
  athlete_id, status, current_step, completed_steps, completed_at,
  completed_onboarding_version, completed_ruleset_version
)
select
  guarded_actor.auth_user_id, 'completed', 'completed',
  array['profile','history','goal','zones','review'], now() - interval '90 days',
  'legacy-unversioned', 'legacy-unversioned'
from guarded_actor
where guarded_actor.critical_write = 'on'
returning status;
