-- R6 runtime remediation: statement_timestamp() is constant for the complete
-- outer RPC statement. Use a guaranteed-distinct marker so the snapshot trigger
-- recognizes the post-mutation refresh as a separate refresh request.

create or replace function private.refresh_authenticated_planning_input_after_rpc()
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_auth_user_id uuid := (select auth.uid());
begin
  if v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.initial_plan_requests
  set refreshed_at = greatest(
    clock_timestamp(),
    refreshed_at + interval '1 microsecond'
  )
  where athlete_id = v_auth_user_id
    and status = 'pending';
end;
$$;

revoke all on function private.refresh_authenticated_planning_input_after_rpc()
from public, anon, authenticated, service_role;
grant execute on function private.refresh_authenticated_planning_input_after_rpc()
to authenticated;
