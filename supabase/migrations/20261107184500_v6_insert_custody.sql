-- A caller can SET the legacy critical_write GUC. Do not treat that GUC as
-- authorization to manufacture V6 revisions or extend frozen workout snapshots.
create function private.guard_v6_generated_revision_insert()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  if new.planning_ruleset_version = 'joren-v6-automatic-selection-1'
    and current_user in ('anon','authenticated') then
    raise exception 'trusted V6 generation required' using errcode = '42501';
  end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_generated_revision_insert()
from public, anon, authenticated, service_role;
create trigger v6_generated_revision_insert before insert on public.plan_revisions
for each row execute function private.guard_v6_generated_revision_insert();

create or replace function private.set_v6_planned_workout_segments()
returns trigger language plpgsql security definer set search_path = '' as $$
declare v_segments jsonb;
begin
  select public_snapshot -> 'segments' into v_segments
  from private.v6_source_revisions where template_id = new.template_id;
  if found then
    -- ROLE is PostgreSQL's protected SET ROLE state, not a caller-defined GUC.
    -- The generated-write RPC runs as a definer under the service-role session;
    -- an authenticated session cannot SET ROLE to service_role.
    if current_setting('role', true) in ('anon','authenticated') then
      raise exception 'trusted V6 generation required' using errcode = '42501';
    end if;
    if exists (select 1 from private.v6_plan_snapshots where revision_id = new.revision_id) then
      raise exception 'V6 revision snapshots are immutable' using errcode = '55000';
    end if;
    new.segments := v_segments;
  elsif exists (select 1 from private.v6_plan_snapshots where revision_id = new.revision_id) then
    raise exception 'V6 revision snapshots are immutable' using errcode = '55000';
  end if;
  return new;
end;
$$;
revoke all on function private.set_v6_planned_workout_segments()
from public, anon, authenticated, service_role;
