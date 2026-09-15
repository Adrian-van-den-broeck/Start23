-- R6 historical-state repair: permit only the one-time opaque-owner expansion
-- performed by the following R2/R3 migration on immutable calibration rows.
--
-- The calibration integrity triggers remain enabled. Every update or delete
-- other than adding a previously-null internal_athlete_id while leaving the
-- complete historical row unchanged is still rejected.

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

revoke execute on function private.reject_calibration_record_mutation()
from public, anon, authenticated, service_role;

comment on function private.reject_calibration_record_mutation() is
  'Immutable calibration guard with one-time null-to-opaque-owner expansion support for migration 20260912072232.';
