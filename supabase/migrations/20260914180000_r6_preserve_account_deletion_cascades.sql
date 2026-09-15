-- R6 runtime/security remediation: Auth account deletion must cascade through
-- protected owner tables. A direct table DELETE invokes these guards at trigger
-- depth one and remains blocked; an FK cascade reaches them at a nested depth.

create or replace function private.require_critical_write_context()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then
    return old;
  end if;
  if current_setting('start23.critical_write', true) is distinct from 'on' then
    raise exception 'critical object writes require a Start23 RPC'
      using errcode = '42501';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function private.require_split_profile_rpc()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then
    return old;
  end if;
  if current_setting('start23.profile_write', true) is distinct from 'on' then
    raise exception 'profile writes require the intended RPC' using errcode = '42501';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function private.reject_calibration_record_mutation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_old jsonb;
  v_new jsonb;
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then
    return old;
  end if;
  if tg_op = 'UPDATE' then
    v_old := to_jsonb(old);
    v_new := to_jsonb(new);

    if v_old ? 'internal_athlete_id'
       and v_old ->> 'internal_athlete_id' is null
       and v_new ->> 'internal_athlete_id' is not null
       and (v_old - 'internal_athlete_id') =
         (v_new - 'internal_athlete_id') then
      return new;
    end if;
  end if;

  raise exception 'calibration records are immutable' using errcode = '42501';
end;
$$;

create or replace function private.enforce_phase_8_rpc_writes()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then
    return old;
  end if;
  if current_setting('start23.checkin_write', true) <> 'on' then
    raise exception 'weekly context writes require an approved RPC'
      using errcode = '42501';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

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
    set refreshed_at = statement_timestamp()
    where athlete_id = v_athlete_id
      and status = 'pending';
  end if;
  return null;
end;
$$;

revoke execute on function private.require_critical_write_context()
from public, anon, authenticated, service_role;
revoke execute on function private.require_split_profile_rpc()
from public, anon, authenticated, service_role;
revoke execute on function private.reject_calibration_record_mutation()
from public, anon, authenticated, service_role;
revoke execute on function private.enforce_phase_8_rpc_writes()
from public, anon, authenticated, service_role;
revoke execute on function private.refresh_pending_planning_input()
from public, anon, authenticated, service_role;

comment on function private.require_critical_write_context() is
  'Requires trusted RPC context for direct critical writes while permitting nested FK account-deletion cascades.';
comment on function private.require_split_profile_rpc() is
  'Requires the split-profile RPC for direct writes while permitting nested FK account-deletion cascades.';
comment on function private.reject_calibration_record_mutation() is
  'Keeps calibration records immutable except the historical R6 owner backfill and nested FK account-deletion cascades.';
