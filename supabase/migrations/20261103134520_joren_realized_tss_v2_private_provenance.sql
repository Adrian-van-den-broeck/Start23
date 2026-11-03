-- LOCAL CANDIDATE ONLY. PostgreSQL/pgTAP and release review remain open.
-- No existing load, calibration, plan or historical calculation is rewritten.
create table private.realized_v2_activity_inputs (
  activity_id uuid primary key,
  athlete_id uuid not null,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  performed_duration_confirmed boolean not null,
  calculation_version text not null default 'joren-realized-tss-matrix-2'
    check (calculation_version = 'joren-realized-tss-matrix-2'),
  created_at timestamptz not null default statement_timestamp(),
  foreign key (activity_id, athlete_id) references public.activities(id, athlete_id) on delete cascade
);
create index realized_v2_inputs_owner_idx on private.realized_v2_activity_inputs(athlete_id);
create index realized_v2_inputs_opaque_owner_idx on private.realized_v2_activity_inputs(internal_athlete_id);
create trigger r3_00_sync_opaque_athlete_owner before insert or update
  on private.realized_v2_activity_inputs for each row execute function private.sync_dual_athlete_owner_keys();

create table private.realized_v2_calculations (
  id uuid primary key default gen_random_uuid(),
  activity_id uuid not null,
  athlete_id uuid not null,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  revision integer not null check (revision > 0),
  rpe smallint not null check (rpe between 1 and 10),
  calculation_version text not null check (calculation_version = 'joren-realized-tss-matrix-2'),
  calculation_method text not null check (calculation_method = 'duration_adjusted_session_rpe'),
  realized_tss numeric,
  planner_eligible boolean not null,
  unavailable_reason text,
  provenance jsonb not null check (jsonb_typeof(provenance) = 'object'),
  created_at timestamptz not null default statement_timestamp(),
  unique (activity_id, revision),
  foreign key (activity_id, athlete_id) references public.activities(id, athlete_id) on delete cascade,
  check (realized_tss is null or (realized_tss >= 0 and realized_tss::text not in ('NaN','Infinity','-Infinity'))),
  check (not planner_eligible or (realized_tss is not null and unavailable_reason is null)),
  check (realized_tss is not null or unavailable_reason is not null),
  check (realized_tss is null or (
    provenance ->> 'version' = 'joren-realized-tss-matrix-2'
    and provenance ->> 'mapping_version' = 'joren-realized-tss-matrix-2'
    and provenance ->> 'numeric_policy' = 'decimal-50-half-even-divide-last-1'
    and provenance ->> 'method' = 'duration_adjusted_session_rpe'
  ) is true)
);
create index realized_v2_calculations_owner_idx on private.realized_v2_calculations(athlete_id, activity_id, revision desc);
create index realized_v2_calculations_opaque_idx on private.realized_v2_calculations(internal_athlete_id);
create trigger r3_00_sync_opaque_athlete_owner before insert or update
  on private.realized_v2_calculations for each row execute function private.sync_dual_athlete_owner_keys();

create function private.realized_v2_immutable() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then return old; end if;
  raise exception 'calculation evidence is immutable' using errcode = '42501';
end;
$$;
create trigger realized_v2_input_immutable before update or delete on private.realized_v2_activity_inputs
  for each row execute function private.realized_v2_immutable();
create trigger realized_v2_calculation_immutable before update or delete on private.realized_v2_calculations
  for each row execute function private.realized_v2_immutable();
alter table private.realized_v2_activity_inputs enable row level security;
alter table private.realized_v2_activity_inputs force row level security;
alter table private.realized_v2_calculations enable row level security;
alter table private.realized_v2_calculations force row level security;
revoke all on private.realized_v2_activity_inputs, private.realized_v2_calculations from public, anon, authenticated, service_role;
grant select, insert on private.realized_v2_activity_inputs, private.realized_v2_calculations to service_role;
revoke all on function private.realized_v2_immutable() from public, anon, authenticated, service_role;

create function public.create_activity_summary_v2(
  p_idempotency_key uuid, p_request_fingerprint text, p_payload jsonb
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_result jsonb; v_owner uuid := (select auth.uid());
begin
  if v_owner is null then raise exception 'authentication required' using errcode = '42501'; end if;
  if p_payload ? 'performed_duration_confirmed' and jsonb_typeof(p_payload -> 'performed_duration_confirmed') <> 'boolean' then
    raise exception 'invalid duration confirmation' using errcode = '23514';
  end if;
  v_result := public.create_activity_summary(p_idempotency_key, p_request_fingerprint, p_payload - 'performed_duration_confirmed');
  insert into private.realized_v2_activity_inputs(activity_id, athlete_id, performed_duration_confirmed)
    select activity.id, activity.athlete_id,
      coalesce((p_payload ->> 'performed_duration_confirmed')::boolean, false) and activity.duration_minutes is not null
    from public.activities activity where activity.id = (v_result ->> 'id')::uuid and activity.athlete_id = v_owner
    on conflict (activity_id) do nothing;
  return private.activity_public_json((v_result ->> 'id')::uuid, v_owner);
end;
$$;
revoke all on function public.create_activity_summary_v2(uuid, text, jsonb) from public, anon, authenticated, service_role;
grant execute on function public.create_activity_summary_v2(uuid, text, jsonb) to authenticated;

create function public.get_activity_processing_context_v2(p_athlete_id uuid, p_activity_id uuid)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_result jsonb; v_basis jsonb; v_selected jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  v_result := public.get_activity_processing_context(p_athlete_id, p_activity_id);
  select jsonb_build_object(
    'context_version', 'joren-realized-tss-matrix-2',
    'plan_id', workout.plan_id, 'revision_id', workout.revision_id,
    'approved_revision', revision.revision_number, 'occurrence_id', workout.id,
    'template_id', workout.template_id, 'template_version', workout.template_version,
    'source_catalog', template.source_catalog, 'source_workout_id', template.source_workout_id,
    'planned_tss', load.planned_tss::text, 'planned_method', load.calculation_method,
    'planned_version', load.ruleset_version, 'planned_duration_minutes', workout.duration_minutes::text,
    'segments', workout.segments
  ) into v_basis
  from public.activities activity
  join public.planned_workouts workout on workout.id = activity.planned_workout_id and workout.athlete_id = activity.athlete_id
  join public.plan_revisions revision on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
  join private.planned_workout_loads load on load.planned_workout_id = workout.id and load.athlete_id = workout.athlete_id
  join public.workout_templates template on template.id = workout.template_id and template.version = workout.template_version
  where activity.id = p_activity_id and activity.athlete_id = p_athlete_id and revision.state in ('active','superseded');
  select to_jsonb(calculation) into v_selected from private.realized_v2_calculations calculation
    where calculation.activity_id = p_activity_id and calculation.athlete_id = p_athlete_id order by revision desc limit 1;
  return v_result || jsonb_build_object(
    'realized_version', (select input.calculation_version from private.realized_v2_activity_inputs input
      where input.activity_id = p_activity_id and input.athlete_id = p_athlete_id),
    'performed_duration_confirmed', coalesce((select input.performed_duration_confirmed from private.realized_v2_activity_inputs input
      where input.activity_id = p_activity_id and input.athlete_id = p_athlete_id), false),
    'approved_workout_basis', case when v_selected -> 'provenance' ? 'planned'
      then v_selected -> 'provenance' -> 'planned' else v_basis end,
    'selected_realized_v2', v_selected);
end;
$$;
revoke all on function public.get_activity_processing_context_v2(uuid, uuid) from public, anon, authenticated, service_role;
grant execute on function public.get_activity_processing_context_v2(uuid, uuid) to service_role;

-- Atomic wrapper: lock, preserve the validated observation path, then append
-- the separately selected estimate. Retry after response loss appends nothing.
create function public.complete_activity_rpe_v2(p_athlete_id uuid, p_activity_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_activity public.activities; v_result jsonb; v_estimate jsonb := p_payload -> 'rpe_estimate';
  v_previous private.realized_v2_calculations; v_basis jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity from public.activities where id = p_activity_id and athlete_id = p_athlete_id for update;
  if not found then raise exception 'activity not found' using errcode = 'P0002'; end if;
  if v_activity.rpe = (p_payload ->> 'rpe')::smallint then
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  select * into v_previous from private.realized_v2_calculations
    where activity_id = p_activity_id and athlete_id = p_athlete_id order by revision desc limit 1;
  if v_estimate is not null then
    if not exists (select 1 from private.realized_v2_activity_inputs where activity_id = p_activity_id and athlete_id = p_athlete_id)
      or (v_activity.rpe is not null and v_previous.id is null) then
      raise exception 'unsupported calculation version' using errcode = '23514';
    end if;
    if v_estimate ->> 'value' is not null then
      v_basis := public.get_activity_processing_context_v2(p_athlete_id, p_activity_id) -> 'approved_workout_basis';
      if (v_estimate -> 'provenance' -> 'planned') is distinct from v_basis
        or (v_estimate -> 'provenance' ->> 'rpe')::smallint is distinct from (p_payload ->> 'rpe')::smallint
        or (v_estimate -> 'provenance' ->> 'actual_minutes')::numeric is distinct from v_activity.duration_minutes
        or not exists (select 1 from private.realized_v2_activity_inputs where activity_id = p_activity_id and athlete_id = p_athlete_id and performed_duration_confirmed)
        or p_payload ->> 'realized_tss' is not null
        or exists (select 1 from public.activity_metrics where activity_id = p_activity_id and athlete_id = p_athlete_id and zone_minutes is not null)
      then raise exception 'calculation evidence mismatch' using errcode = '23514'; end if;
    end if;
  end if;
  if v_activity.rpe is null then
    v_result := public.complete_activity_rpe(p_athlete_id, p_activity_id, p_payload - 'rpe_estimate');
  else
    v_result := public.revise_activity_rpe(p_athlete_id, p_activity_id, p_payload - 'rpe_estimate');
  end if;
  if v_estimate is not null then
    insert into private.realized_v2_calculations(activity_id, athlete_id, revision, rpe,
      calculation_version, calculation_method, realized_tss, planner_eligible, unavailable_reason, provenance)
    values (p_activity_id, p_athlete_id, coalesce(v_previous.revision, 0) + 1,
      (p_payload ->> 'rpe')::smallint, 'joren-realized-tss-matrix-2', 'duration_adjusted_session_rpe',
      (v_estimate ->> 'value')::numeric, (v_estimate ->> 'planner_eligible')::boolean,
      v_estimate ->> 'reason', v_estimate -> 'provenance');
  end if;
  return v_result;
end;
$$;
revoke all on function public.complete_activity_rpe_v2(uuid, uuid, jsonb) from public, anon, authenticated, service_role;
grant execute on function public.complete_activity_rpe_v2(uuid, uuid, jsonb) to service_role;
