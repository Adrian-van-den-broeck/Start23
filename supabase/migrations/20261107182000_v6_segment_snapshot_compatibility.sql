-- Forward correction observed on disposable PostgreSQL 17.11. Preserve the two
-- original V6 candidates and every applied historical migration unchanged.
-- The historical BEFORE INSERT trigger rebuilds segments from workout_segments;
-- inactive V6 sources deliberately have no rows in that historical projection.
-- Restore only V6 segments from the immutable trusted source after that trigger.
create function private.set_v6_planned_workout_segments()
returns trigger language plpgsql security definer set search_path = '' as $$
declare v_segments jsonb;
begin
  select public_snapshot -> 'segments' into v_segments
  from private.v6_source_revisions where template_id = new.template_id;
  if found then
    new.segments := v_segments;
  end if;
  return new;
end;
$$;
revoke all on function private.set_v6_planned_workout_segments()
from public, anon, authenticated, service_role;

create trigger v6_set_planned_workout_segments before insert on public.planned_workouts
for each row execute function private.set_v6_planned_workout_segments();
