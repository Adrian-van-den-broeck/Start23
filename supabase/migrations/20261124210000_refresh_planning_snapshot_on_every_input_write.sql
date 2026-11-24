-- A pending planning snapshot must follow the last input write of an RPC.
--
-- refresh_pending_planning_input() marked a refresh with statement_timestamp(),
-- which is constant for the whole outer RPC statement. The snapshot trigger
-- only rebuilds when refreshed_at changes, so the second input write inside
-- one RPC was ignored. approve_zone_proposal() supersedes the active zone
-- before it activates the new one; the snapshot was rebuilt between the two
-- writes and kept an empty zone list, so planning rejected an athlete whose
-- onboarding was current ("Complete the current onboarding upgrade").
--
-- Use the same guaranteed-distinct marker as
-- refresh_authenticated_planning_input_after_rpc() (20260914173500), so every
-- input write rebuilds from the state that write left behind.

create or replace function private.refresh_pending_planning_input()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := case
    when tg_op = 'DELETE' then old.athlete_id
    else new.athlete_id
  end;
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then
    return null;
  end if;
  if exists (
    select 1
    from public.initial_plan_requests request
    where request.athlete_id = v_athlete_id
      and request.status = 'pending'
  ) then
    perform set_config('start23.critical_write', 'on', true);
    update public.initial_plan_requests
    set refreshed_at = greatest(
      clock_timestamp(),
      refreshed_at + interval '1 microsecond'
    )
    where athlete_id = v_athlete_id
      and status = 'pending';
  end if;
  return null;
end;
$$;

revoke execute on function private.refresh_pending_planning_input()
from public, anon, authenticated, service_role;

comment on function private.refresh_pending_planning_input() is
  'Rebuilds the pending planning snapshot after every input write, including several writes inside one RPC statement.';

-- Pending requests are not historical: they are defined to follow the current
-- inputs. Rebuild them once so snapshots left stale by the skipped refresh
-- match the current inputs again. Consumed and cancelled requests keep their
-- recorded snapshot.
select set_config('start23.critical_write', 'on', true);

update public.initial_plan_requests
set refreshed_at = greatest(
  clock_timestamp(),
  refreshed_at + interval '1 microsecond'
)
where status = 'pending';

select set_config('start23.critical_write', '', true);
