-- Close the two remaining R6-entry calibration gaps without starting R6.
-- Historical protocol definitions and rows remain intact and readable.

create table private.calibration_protocol_lifecycle (
  protocol_id text primary key,
  discipline text not null,
  protocol_type text not null,
  lifecycle text not null,

  constraint calibration_protocol_lifecycle_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint calibration_protocol_lifecycle_type_valid check (
    protocol_type in ('field_test', 'submaximal_calibration')
  ),
  constraint calibration_protocol_lifecycle_state_valid check (
    lifecycle in ('current_selectable', 'historical_read_only')
  )
);

insert into private.calibration_protocol_lifecycle (
  protocol_id,
  discipline,
  protocol_type,
  lifecycle
) values
  (
    'start23_run_threshold_30min_v1', 'run', 'field_test',
    'historical_read_only'
  ),
  (
    'start23_bike_ftp_30min_v1', 'bike', 'field_test',
    'historical_read_only'
  ),
  (
    'start23_bike_fthr_20min_v1', 'bike', 'field_test',
    'historical_read_only'
  ),
  (
    'start23_swim_css_400_200_v1', 'swim', 'field_test',
    'current_selectable'
  ),
  (
    'start23_week1_run_calibration_v1', 'run', 'submaximal_calibration',
    'current_selectable'
  ),
  (
    'start23_week1_bike_calibration_v1', 'bike', 'submaximal_calibration',
    'current_selectable'
  ),
  (
    'start23_week1_swim_calibration_v1', 'swim', 'submaximal_calibration',
    'current_selectable'
  );

revoke all on table private.calibration_protocol_lifecycle
from public, anon, authenticated, service_role;

create function private.is_current_calibration_protocol(
  p_protocol_id text,
  p_discipline text,
  p_protocol_type text default null
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from private.calibration_protocol_lifecycle protocol
    where protocol.protocol_id = p_protocol_id
      and protocol.discipline = p_discipline
      and protocol.lifecycle = 'current_selectable'
      and (
        p_protocol_type is null
        or protocol.protocol_type = p_protocol_type
      )
  )
$$;

revoke execute on function private.is_current_calibration_protocol(text,text,text)
from public, anon, service_role;
grant execute on function private.is_current_calibration_protocol(text,text,text)
to authenticated;

create function private.enforce_current_calibration_setup()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_expected_type text;
begin
  if new.setup_route = 'known_values' and new.protocol_id is null then
    return new;
  end if;

  v_expected_type := case new.setup_route
    when 'field_test' then 'field_test'
    when 'calibration_week' then 'submaximal_calibration'
    else null
  end;
  if v_expected_type is null
     or not private.is_current_calibration_protocol(
       new.protocol_id,
       new.discipline,
       v_expected_type
     ) then
    raise exception 'historical calibration protocol is read-only'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_calibration_setup()
from public, anon, authenticated, service_role;

create trigger discipline_zone_setups_r6_entry_current_protocol
before insert or update on public.discipline_zone_setups
for each row execute function private.enforce_current_calibration_setup();

create function private.enforce_current_calibration_observation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not private.is_current_calibration_protocol(
    new.protocol_id,
    new.discipline
  ) then
    raise exception 'historical calibration protocol is read-only'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_calibration_observation()
from public, anon, authenticated, service_role;

create trigger calibration_observations_r6_entry_current_protocol
before insert on public.calibration_observations
for each row execute function private.enforce_current_calibration_observation();

create function private.enforce_current_calibration_evaluation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not private.is_current_calibration_protocol(
    new.protocol_id,
    new.discipline
  ) then
    raise exception 'historical calibration protocol is read-only'
      using errcode = '23514';
  end if;
  if not exists (
    select 1
    from public.calibration_observations observation
    where observation.athlete_id = new.athlete_id
      and observation.activity_id = new.activity_id
      and observation.protocol_id = new.protocol_id
      and observation.discipline = new.discipline
  ) then
    raise exception 'current evaluation requires a persisted protocol observation'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_calibration_evaluation()
from public, anon, authenticated, service_role;

create trigger calibration_evaluations_r6_entry_current_protocol
before insert on public.calibration_evaluations
for each row execute function private.enforce_current_calibration_evaluation();

create function private.enforce_current_calibration_zone_profile()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_evaluation public.calibration_evaluations;
begin
  if new.calibration_evaluation_id is null then
    return new;
  end if;

  select evaluation.* into v_evaluation
  from public.calibration_evaluations evaluation
  where evaluation.id = new.calibration_evaluation_id
    and evaluation.athlete_id = new.athlete_id;
  if not found
     or not private.is_current_calibration_protocol(
       v_evaluation.protocol_id,
       v_evaluation.discipline
     ) then
    raise exception 'historical calibration cannot create current zone state'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_calibration_zone_profile()
from public, anon, authenticated, service_role;

create trigger zone_profile_versions_r6_entry_current_calibration
before insert on public.zone_profile_versions
for each row execute function private.enforce_current_calibration_zone_profile();

create function private.enforce_current_validation_test_assignment()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'INSERT'
     or (new.state = 'scheduled' and old.state is distinct from 'scheduled') then
    if not private.is_current_calibration_protocol(
      new.protocol_id,
      new.discipline,
      'field_test'
    ) then
      raise exception 'historical calibration protocol is read-only'
        using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_validation_test_assignment()
from public, anon, authenticated, service_role;

create trigger discipline_test_assignments_r6_entry_current_protocol
before insert or update on public.discipline_test_assignments
for each row execute function private.enforce_current_validation_test_assignment();

-- No current protocol supports integrated field-test replacement. The old RPC
-- remains as historical implementation but is no longer an authenticated API.
revoke execute on function public.save_integrated_test_assignment(jsonb)
from public, anon, authenticated, service_role;

create or replace function public.create_validation_test_proposal(
  p_assignment jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_discipline text := p_assignment ->> 'discipline';
  v_protocol_id text := p_assignment ->> 'protocol_id';
  v_scheduled_date date := (p_assignment ->> 'scheduled_date')::date;
  v_operational jsonb := public.get_operational_athlete_profile();
  v_timezone text := v_operational ->> 'timezone';
  v_assignment public.discipline_test_assignments;
  v_proposal public.change_proposals;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_assignment) <> 'object'
     or p_assignment ->> 'scheduling_mode' <> 'standalone'
     or not private.is_current_calibration_protocol(
       v_protocol_id,
       v_discipline,
       'field_test'
     )
     or p_assignment ?| array[
       'athlete_id', 'user_id', 'tss', 'planned_tss', 'realized_tss', 'load'
     ] then
    raise exception 'invalid validation test assignment' using errcode = '23514';
  end if;
  if v_timezone is null
     or v_operational ->> 'timezone_source' not in ('device', 'manual')
     or v_operational ->> 'timezone_confirmed_at' is null
     or v_scheduled_date <
       (statement_timestamp() at time zone v_timezone)::date then
    raise exception 'test date is in the past or timezone is unconfirmed'
      using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.discipline_zone_setups setup
    where setup.athlete_id = v_athlete_id
      and setup.discipline = v_discipline
      and setup.setup_route = 'field_test'
      and setup.protocol_id = v_protocol_id
  ) then
    raise exception 'field test setup is not current' using errcode = '40001';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':test:' || v_discipline, 0)
  );
  perform set_config('start23.critical_write', 'on', true);
  insert into public.discipline_test_assignments (
    athlete_id, discipline, protocol_id, scheduling_mode, scheduled_date
  ) values (
    v_athlete_id, v_discipline, v_protocol_id, 'standalone', v_scheduled_date
  ) returning * into v_assignment;

  insert into public.change_proposals (
    athlete_id, kind, target_test_assignment_id,
    base_test_assignment_revision, reason_codes, public_explanation,
    ruleset_version
  ) values (
    v_athlete_id, 'validation_test', v_assignment.id, v_assignment.revision,
    array['athlete_selected_validation_test'],
    'Een veldtest staat klaar op de gekozen lokale datum en wacht op bevestiging.',
    'phase-11-ruleset-1'
  ) returning * into v_proposal;

  return (to_jsonb(v_assignment) - 'athlete_id') || jsonb_build_object(
    'proposal_id', v_proposal.id,
    'proposal_state', v_proposal.state
  );
end;
$$;

comment on table private.calibration_protocol_lifecycle is
  'Authoritative database classification for current-selectable versus historical-read-only calibration protocols.';
