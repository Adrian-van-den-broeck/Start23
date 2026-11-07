-- Prepared only. No production/staging execution or activation is authorized.
-- Reuse existing ownership, revisions, proposals, loads, and confirmation RPCs.
-- No V6 row is added to private.workout_template_loads: the historical catalog
-- projection joins that table and cannot discover these inactive revisions.
alter table public.workout_templates add column inactive_v6 boolean not null default false;
create policy workout_templates_hide_inactive_v6 on public.workout_templates
  as restrictive for select to authenticated using (not inactive_v6);

-- V6 uses the existing occurrence-aware draft model, not the pre-v2
-- template-keyed placement validator. Historical predicates remain identical.
alter table public.swipe_week_drafts drop constraint swipe_week_drafts_template_arrays_valid;
alter table public.swipe_week_drafts add constraint swipe_week_drafts_template_arrays_valid check (
  cardinality(accepted_template_ids) <= target_workout_count and (
    ruleset_version in ('joren-planning-ruleset-2','joren-v6-automatic-selection-1')
    or (not (accepted_template_ids && passed_template_ids) and (current_template_id is null or (
      not current_template_id = any(accepted_template_ids) and not current_template_id = any(passed_template_ids))))
  )
);
drop trigger swipe_week_drafts_validate on public.swipe_week_drafts;
create trigger swipe_week_drafts_validate before insert or update on public.swipe_week_drafts
  for each row when (new.ruleset_version not in ('joren-planning-ruleset-2','joren-v6-automatic-selection-1'))
  execute function private.validate_swipe_week_draft();
drop trigger swipe_week_drafts_validate_v2 on public.swipe_week_drafts;
create trigger swipe_week_drafts_validate_v2 before insert or update on public.swipe_week_drafts
  for each row when (new.ruleset_version in ('joren-planning-ruleset-2','joren-v6-automatic-selection-1'))
  execute function private.validate_swipe_week_draft_v2();

create table private.v6_source_revisions (
  template_id uuid primary key references public.workout_templates(id),
  logical_key uuid not null,
  source_sha256 text not null check (source_sha256 ~ '^[a-f0-9]{64}$'),
  worksheet text not null,
  source_row integer not null check (source_row >= 5),
  planned_method text not null check (planned_method = 'joren-v6-planned-if2-1'),
  reference_version text not null check (reference_version = 'joren-v6-approved-if-reference-1'),
  official_decimal text not null check (official_decimal ~ '^[0-9]+([.][0-9]+)?$'),
  planned_tss numeric not null check (planned_tss >= 0 and planned_tss::text not in ('NaN','Infinity','-Infinity')),
  numerator text not null check (numerator ~ '^[0-9]+$'),
  denominator text not null check (denominator ~ '^[1-9][0-9]*$'),
  source_snapshot jsonb not null,
  document jsonb not null,
  public_snapshot jsonb not null,
  activation text not null default 'INACTIVE' check (activation = 'INACTIVE'),
  unique (source_sha256, worksheet, source_row),
  check (planned_tss = official_decimal::numeric)
);
alter table private.v6_source_revisions enable row level security;
alter table private.v6_source_revisions force row level security;
revoke all on private.v6_source_revisions from public, anon, authenticated, service_role;
create trigger v6_source_revisions_immutable before update or delete on private.v6_source_revisions
  for each row execute function private.reject_catalog_mutation();
create index v6_source_logical_revision_idx on private.v6_source_revisions(logical_key, template_id);

create table private.v6_plan_snapshots (
  revision_id uuid primary key,
  athlete_id uuid not null references auth.users(id) on delete cascade,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  payload jsonb not null,
  input_snapshot jsonb not null,
  foreign key (revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade
);
create table private.v6_occurrence_snapshots (
  planned_workout_id uuid primary key,
  revision_id uuid not null,
  athlete_id uuid not null references auth.users(id) on delete cascade,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  occurrence_id uuid not null,
  ordinal integer not null check (ordinal > 0),
  unique (revision_id, occurrence_id),
  unique (revision_id, ordinal),
  foreign key (revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade,
  foreign key (planned_workout_id, athlete_id) references public.planned_workouts(id, athlete_id) on delete cascade
);
create table private.v6_edit_results (
  athlete_id uuid not null references auth.users(id) on delete cascade,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  operation_key text not null check (operation_key ~ '^[a-f0-9]{64}$'),
  revision_id uuid not null,
  result jsonb not null,
  primary key (athlete_id, operation_key),
  foreign key (revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade
);
create index v6_plan_snapshot_owner_idx on private.v6_plan_snapshots(athlete_id);
create index v6_plan_snapshot_opaque_idx on private.v6_plan_snapshots(internal_athlete_id);
create index v6_occurrence_owner_idx on private.v6_occurrence_snapshots(athlete_id, occurrence_id);
create index v6_occurrence_opaque_idx on private.v6_occurrence_snapshots(internal_athlete_id);
create index v6_edit_result_revision_idx on private.v6_edit_results(revision_id, athlete_id);
create index v6_edit_result_opaque_idx on private.v6_edit_results(internal_athlete_id);

do $migration$
declare v_table text;
begin
  foreach v_table in array array['v6_plan_snapshots','v6_occurrence_snapshots','v6_edit_results'] loop
    execute format('alter table private.%I enable row level security', v_table);
    execute format('alter table private.%I force row level security', v_table);
    execute format('revoke all on private.%I from public, anon, authenticated, service_role', v_table);
    execute format('create trigger r3_00_sync_opaque_athlete_owner before insert or update on private.%I '
      'for each row execute function private.sync_dual_athlete_owner_keys()', v_table);
    execute format('create trigger v6_snapshot_immutable before update or delete on private.%I '
      'for each row execute function private.realized_v2_immutable()', v_table);
  end loop;
end;
$migration$;

-- V6 may have no known timed duration (zero workouts or distance-only swimming).
-- Preserve the complete historical predicate, extending only the versioned case.
alter table public.plan_revisions drop constraint plan_revisions_distribution_valid;
alter table public.plan_revisions add constraint plan_revisions_distribution_valid check (
  low_intensity_percent between 0 and 100 and high_intensity_percent between 0 and 100
  and (low_intensity_percent + high_intensity_percent = 100
    or (low_intensity_percent = 0 and high_intensity_percent = 0
      and (target_basis = 'injury_rest_only'
        or (planning_ruleset_version = 'joren-v6-automatic-selection-1' and total_duration_minutes = 0))))
);

create function public.get_inactive_v6_catalog_for_planning() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  return (select coalesce(jsonb_agg(document order by template_id), '[]'::jsonb) from private.v6_source_revisions);
end;
$$;
revoke all on function public.get_inactive_v6_catalog_for_planning() from public, anon, authenticated, service_role;
grant execute on function public.get_inactive_v6_catalog_for_planning() to service_role;

-- Reuse the established explicit public projection; replace only physical row
-- IDs with logical IDs and preserve the frozen V6 occurrence ordering.
create function private.v6_public_plan(p_athlete_id uuid, p_plan_id uuid, p_revision integer)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_claims text; v_sub text; v_result jsonb;
begin
  if not exists (select 1 from public.weekly_plans where id = p_plan_id and athlete_id = p_athlete_id) then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  v_claims := current_setting('request.jwt.claims', true);
  v_sub := current_setting('request.jwt.claim.sub', true);
  perform set_config('request.jwt.claim.sub', p_athlete_id::text, true);
  perform set_config('request.jwt.claims', jsonb_build_object('sub', p_athlete_id, 'role', 'authenticated')::text, true);
  v_result := public.get_weekly_plan(p_plan_id, p_revision);
  perform set_config('request.jwt.claims', coalesce(v_claims, '{}'), true);
  perform set_config('request.jwt.claim.sub', coalesce(v_sub, ''), true);
  return jsonb_set(v_result, '{workouts}', (
    select coalesce(jsonb_agg(jsonb_set(w.value, '{id}', to_jsonb(coalesce(m.occurrence_id,
      (w.value ->> 'id')::uuid))) order by coalesce(m.ordinal, w.ordinality)), '[]'::jsonb)
    from jsonb_array_elements(v_result -> 'workouts') with ordinality w(value, ordinality)
    left join private.v6_occurrence_snapshots m on m.planned_workout_id = (w.value ->> 'id')::uuid
      and m.athlete_id = p_athlete_id and m.revision_id = (v_result ->> 'revision_id')::uuid
  ));
end;
$$;
revoke all on function private.v6_public_plan(uuid, uuid, integer) from public, anon, authenticated, service_role;

create function public.get_v6_weekly_plan(p_plan_id uuid, p_revision integer default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if (select auth.uid()) is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  return private.v6_public_plan((select auth.uid()), p_plan_id, p_revision);
end;
$$;
revoke all on function public.get_v6_weekly_plan(uuid, integer) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_weekly_plan(uuid, integer) to authenticated;

create function public.get_v6_edit_retry(p_athlete_id uuid, p_operation_key text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  return (select result from private.v6_edit_results where athlete_id = p_athlete_id and operation_key = p_operation_key);
end;
$$;
revoke all on function public.get_v6_edit_retry(uuid, text) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_edit_retry(uuid, text) to service_role;

create function public.get_v6_plan_context_for_planning(p_athlete_id uuid, p_plan_id uuid, p_revision integer default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_context jsonb; v_snapshot private.v6_plan_snapshots;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if p_revision is null then
    v_context := public.get_plan_context_for_planning(p_athlete_id, p_plan_id);
  else
    v_context := public.get_plan_revision_context_for_planning(p_athlete_id, p_plan_id, p_revision);
  end if;
  select s.* into v_snapshot from private.v6_plan_snapshots s join public.plan_revisions r on r.id = s.revision_id
    and r.athlete_id = s.athlete_id where r.plan_id = p_plan_id and r.athlete_id = p_athlete_id
    and r.revision_number = (v_context ->> 'revision')::integer;
  if not found then raise exception 'weekly plan not found' using errcode = 'P0002'; end if;
  return v_context || jsonb_build_object('v6_frozen_snapshot', v_snapshot.payload -> 'v6_frozen_snapshot',
    'weekly_registration_evidence', v_snapshot.payload -> 'weekly_registration_evidence',
    'cross_training_opt_ins', v_snapshot.payload -> 'cross_training_opt_ins',
    'input_snapshot', v_snapshot.input_snapshot);
end;
$$;
revoke all on function public.get_v6_plan_context_for_planning(uuid, uuid, integer) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_plan_context_for_planning(uuid, uuid, integer) to service_role;

create function public.create_v6_weekly_plan_proposal(p_athlete_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_plan public.weekly_plans; v_pending public.plan_revisions; v_proposal public.change_proposals;
  v_request public.initial_plan_requests; v_prior private.v6_plan_snapshots;
  v_revision_id uuid; v_revision integer; v_proposal_id uuid; v_workout_id uuid;
  v_workout jsonb; v_warning jsonb; v_row private.v6_source_revisions; v_total numeric := 0;
  v_result jsonb; v_public jsonb; v_retry_payload jsonb;
  v_key text; v_ordinal integer := 0; v_checkin uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  -- Serialize absent-plan creation, duplicate messages, and edits for this week.
  -- Hash collisions only add serialization; they never confer ownership.
  perform pg_advisory_xact_lock(hashtextextended(p_athlete_id::text || ':' || (p_payload ->> 'week_start'), 0));
  v_key := p_payload ->> 'v6_edit_operation_key';
  if v_key is not null then
    select e.result, s.payload into v_result, v_retry_payload from private.v6_edit_results e
      join private.v6_plan_snapshots s on s.revision_id = e.revision_id and s.athlete_id = e.athlete_id
      where e.athlete_id = p_athlete_id and e.operation_key = v_key;
    if found then
      if v_retry_payload is distinct from p_payload then
        raise exception 'idempotency key payload mismatch' using errcode = 'PT409';
      end if;
      return jsonb_build_object('plan_id', v_result #>> '{plan,id}',
        'revision', (v_result #>> '{plan,revision}')::integer, 'proposal_id', v_result #>> '{proposal,id}');
    end if;
  end if;
  if p_payload ->> 'planning_ruleset_version' is distinct from 'joren-v6-automatic-selection-1'
    or p_payload #>> '{v6_frozen_snapshot,policy}' is distinct from 'joren-v6-automatic-selection-1'
    or p_payload ->> 'ruleset_version' is distinct from 'phase-13-joren-ruleset-1'
    or p_payload #>> '{v6_frozen_snapshot,planned_method}' is distinct from 'joren-v6-planned-if2-1'
    or p_payload #>> '{v6_frozen_snapshot,activation}' is distinct from 'INACTIVE_PREVIEW'
    or p_payload #>> '{v6_frozen_snapshot,input_fingerprint}' is distinct from p_payload ->> 'input_fingerprint'
    or jsonb_typeof(p_payload -> 'workouts') is distinct from 'array'
    or jsonb_typeof(p_payload -> 'weekly_registration_evidence') is distinct from 'array' then
    raise exception 'planning payload is invalid' using errcode = '23514';
  end if;
  if (p_payload #>> '{v6_frozen_snapshot,controls,athlete_scope}' is not null
      and (p_payload #>> '{v6_frozen_snapshot,controls,athlete_scope}')::uuid
        is distinct from private.resolve_opaque_athlete_id(p_athlete_id))
    or (p_payload #>> '{v6_frozen_snapshot,controls,week_scope}' is not null
      and (p_payload #>> '{v6_frozen_snapshot,controls,week_scope}')::date
        is distinct from (p_payload ->> 'week_start')::date) then
    raise exception 'planning evidence scope is invalid' using errcode = '23514';
  end if;
  -- A3-A9 check-in attachment/replay remains a single existing transaction contract.
  -- V6 currently implements initial-proposal + pending-edit scope only.
  v_checkin := nullif(p_payload ->> 'checkin_id', '')::uuid;
  if v_checkin is not null then
    raise exception 'V6 check-in generation is unavailable' using errcode = '23514';
  end if;
  select * into v_plan from public.weekly_plans where athlete_id = p_athlete_id
    and week_start = (p_payload ->> 'week_start')::date;
  if nullif(p_payload ->> 'plan_id', '') is not null and
    (v_plan.id is null or v_plan.id <> (p_payload ->> 'plan_id')::uuid) then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  -- Same lock order as approve/reject: proposal, revision, plan. The advisory
  -- lock is V6-only; correctness against legacy confirmation uses row locks.
  if v_plan.id is not null then
    select p.* into v_proposal from public.change_proposals p join public.plan_revisions r
      on r.id = p.target_plan_revision_id and r.athlete_id = p.athlete_id
      where r.plan_id = v_plan.id and r.athlete_id = p_athlete_id and p.state = 'pending'
      for update of p;
    if v_proposal.id is not null then
      select * into v_pending from public.plan_revisions where id = v_proposal.target_plan_revision_id
        and athlete_id = p_athlete_id for update;
    end if;
    select * into v_plan from public.weekly_plans where id = v_plan.id and athlete_id = p_athlete_id for update;
    select jsonb_build_object('plan_id', r.plan_id, 'revision', r.revision_number, 'proposal_id', p.id), s.payload
      into v_result, v_retry_payload from public.plan_revisions r join public.change_proposals p
      on p.target_plan_revision_id = r.id and p.athlete_id = r.athlete_id
      join private.v6_plan_snapshots s on s.revision_id = r.id and s.athlete_id = r.athlete_id
      where r.plan_id = v_plan.id and r.athlete_id = p_athlete_id
      and r.generation_fingerprint = p_payload ->> 'generation_fingerprint';
    if found then
      if v_retry_payload is distinct from p_payload then
        raise exception 'idempotency key payload mismatch' using errcode = 'PT409';
      end if;
      return v_result;
    end if;
  end if;
  if coalesce(v_plan.active_revision, 0) is distinct from (p_payload ->> 'expected_base_revision')::integer then
    raise exception 'plan revision is stale' using errcode = 'PT409';
  end if;
  if p_payload ? 'expected_pending_revision' then
    if v_pending.id is null or v_pending.state is distinct from 'pending_approval' or v_proposal.state is distinct from 'pending'
      or v_pending.revision_number is distinct from (p_payload ->> 'expected_pending_revision')::integer
      or v_proposal.id is distinct from (p_payload ->> 'expected_proposal_id')::uuid then
      raise exception 'plan proposal is stale' using errcode = 'PT409';
    end if;
    select * into v_prior from private.v6_plan_snapshots where revision_id = v_pending.id and athlete_id = p_athlete_id;
    if not found or (v_prior.payload -> 'v6_frozen_snapshot' - 'templates' - 'optimality' - 'examined' - 'estimated_sports')
      is distinct from (p_payload -> 'v6_frozen_snapshot' - 'templates' - 'optimality' - 'examined' - 'estimated_sports') then
      raise exception 'planning input is stale' using errcode = 'PT409';
    end if;
    if exists (select 1 from unnest(array['week_start','timezone','phase','target_basis','target_tss',
      'taper_period','confirmed_injuries','low_only_disciplines','cross_training_opt_ins','goal_disciplines',
      'availability','available_dates','availability_source','initial_plan_request_id','input_fingerprint',
      'weekly_registration_evidence']) field where v_prior.payload -> field is distinct from p_payload -> field) then
      raise exception 'planning input is stale' using errcode = 'PT409';
    end if;
  elsif v_plan.id is not null then
    -- Resuming is a read, never silent regeneration over an accepted choice.
    raise exception 'plan proposal is stale' using errcode = 'PT409';
  end if;
  select * into v_request from public.initial_plan_requests
    where id = (p_payload ->> 'initial_plan_request_id')::uuid and athlete_id = p_athlete_id for update;
  if not found then raise exception 'planning input not found' using errcode = 'P0002'; end if;
  if v_request.input_fingerprint is distinct from p_payload ->> 'input_fingerprint'
    or v_request.status not in ('pending','consumed')
    or v_request.input_snapshot is distinct from private.build_phase_8_5_planning_input_snapshot(p_athlete_id)
    or private.realized_v2_history_evidence(p_athlete_id, (p_payload ->> 'week_start')::date)
      is distinct from p_payload -> 'weekly_registration_evidence' then
    raise exception 'planning input is stale' using errcode = 'PT409';
  end if;
  if (p_payload ->> 'target_tss')::numeric::text in ('NaN','Infinity','-Infinity')
    or (p_payload ->> 'target_tss')::numeric < 0
    or (p_payload ->> 'target_tss')::numeric is distinct from
      (p_payload #>> '{v6_frozen_snapshot,target,target,value}')::numeric then
    raise exception 'planning target snapshot is invalid' using errcode = '23514';
  end if;
  perform set_config('start23.critical_write', 'on', true);
  if v_plan.id is null then
    insert into public.weekly_plans(athlete_id, week_start, timezone, state)
      values (p_athlete_id, (p_payload ->> 'week_start')::date, p_payload ->> 'timezone', 'pending_approval') returning * into v_plan;
  end if;
  if v_pending.id is not null then
    update public.change_proposals set state = 'expired', decided_at = statement_timestamp() where id = v_proposal.id;
    update public.plan_revisions set state = 'expired' where id = v_pending.id;
  end if;
  select coalesce(max(revision_number), 0) + 1 into v_revision from public.plan_revisions
    where plan_id = v_plan.id and athlete_id = p_athlete_id;
  insert into public.plan_revisions(plan_id, athlete_id, revision_number, state, source, phase, target_basis,
    taper_period, input_fingerprint, generation_fingerprint, initial_plan_request_id, total_duration_minutes,
    low_intensity_percent, high_intensity_percent, confirmed_injuries, low_only_disciplines, cross_training_opt_ins,
    availability, available_dates, availability_source, ruleset_version, planning_ruleset_version)
  values (v_plan.id, p_athlete_id, v_revision, 'pending_approval', 'system_generated', p_payload ->> 'phase',
    p_payload ->> 'target_basis', nullif(p_payload ->> 'taper_period',''), p_payload ->> 'input_fingerprint',
    p_payload ->> 'generation_fingerprint', v_request.id, (p_payload ->> 'total_duration_minutes')::numeric,
    (p_payload ->> 'low_intensity_percent')::numeric, (p_payload ->> 'high_intensity_percent')::numeric,
    array(select jsonb_array_elements_text(p_payload -> 'confirmed_injuries')),
    array(select jsonb_array_elements_text(p_payload -> 'low_only_disciplines')),
    array(select jsonb_array_elements_text(p_payload -> 'cross_training_opt_ins')),
    p_payload -> 'availability', array(select value::date from jsonb_array_elements_text(p_payload -> 'available_dates')),
    p_payload ->> 'availability_source', p_payload ->> 'ruleset_version', p_payload ->> 'planning_ruleset_version')
    returning id into v_revision_id;
  -- Serialize ownership checks on a logical occurrence even across two athletes.
  -- A stable lock order prevents opposing complete-week writes from deadlocking.
  perform pg_advisory_xact_lock(hashtextextended('v6-occurrence:' || identity, 0))
    from (select value ->> 'occurrence_id' as identity from jsonb_array_elements(p_payload -> 'workouts')
      order by value ->> 'occurrence_id') ids;
  for v_workout in select value from jsonb_array_elements(p_payload -> 'workouts') loop
    select * into v_row from private.v6_source_revisions where template_id = (v_workout ->> 'template_id')::uuid;
    if not found or v_row.planned_tss is distinct from (v_workout ->> 'planned_tss')::numeric
      or v_row.source_sha256 is distinct from v_workout ->> 'source_revision_sha256'
      or v_row.planned_method is distinct from v_workout ->> 'planned_method'
      or v_row.planned_method is distinct from v_workout ->> 'planned_method_version'
      or not (p_payload #> '{v6_frozen_snapshot,templates}' @> jsonb_build_array(v_row.source_snapshot)) then
      raise exception 'workout source snapshot is invalid' using errcode = '23514';
    end if;
    if exists (select 1 from private.v6_occurrence_snapshots where occurrence_id = (v_workout ->> 'occurrence_id')::uuid
      and (athlete_id <> p_athlete_id or revision_id not in (select id from public.plan_revisions where plan_id = v_plan.id))) then
      raise exception 'workout occurrence is invalid' using errcode = '23514';
    end if;
    if exists (select 1 from public.planned_workouts where id = (v_workout ->> 'occurrence_id')::uuid
      and (athlete_id <> p_athlete_id or plan_id <> v_plan.id)) then
      raise exception 'workout occurrence is invalid' using errcode = '23514';
    end if;
    insert into public.planned_workouts(revision_id, plan_id, athlete_id, template_id, template_key, template_version,
      discipline, name, description, duration_minutes, distance_meters, intensity_bucket, expected_rpe_min,
      expected_rpe_max, segments, scheduled_at, scheduled_date, timezone, source)
    select v_revision_id, v_plan.id, p_athlete_id, t.id, t.template_key, t.version, t.discipline, t.name, t.description,
      t.duration_minutes, t.distance_meters, t.intensity_bucket, t.expected_rpe_min, t.expected_rpe_max,
      v_row.public_snapshot -> 'segments', (v_workout ->> 'scheduled_at')::timestamptz,
      (v_workout ->> 'scheduled_date')::date, p_payload ->> 'timezone', v_workout ->> 'source'
      from public.workout_templates t where t.id = v_row.template_id returning id into v_workout_id;
    v_ordinal := v_ordinal + 1;
    insert into private.v6_occurrence_snapshots(planned_workout_id, revision_id, athlete_id, occurrence_id, ordinal)
      values (v_workout_id, v_revision_id, p_athlete_id, (v_workout ->> 'occurrence_id')::uuid, v_ordinal);
    insert into private.planned_workout_loads(planned_workout_id, athlete_id, planned_tss, calculation_method, ruleset_version)
      values (v_workout_id, p_athlete_id, v_row.planned_tss, v_row.planned_method, v_row.planned_method);
    v_total := v_total + v_row.planned_tss;
  end loop;
  -- These are storage consistency checks on Python's complete-week result, not
  -- a second physiological selector or a second rounding authority.
  if v_total is distinct from (p_payload ->> 'planned_tss')::numeric
    or v_total > (p_payload ->> 'target_tss')::numeric then
    raise exception 'planned snapshot mismatch' using errcode = '23514';
  end if;
  insert into private.plan_revision_loads(revision_id, athlete_id, target_tss, planned_tss, ruleset_version)
    values (v_revision_id, p_athlete_id, (p_payload ->> 'target_tss')::numeric, v_total, p_payload ->> 'planning_ruleset_version');
  insert into private.v6_plan_snapshots(revision_id, athlete_id, payload, input_snapshot)
    values (v_revision_id, p_athlete_id, p_payload, v_request.input_snapshot);
  insert into private.realized_v2_plan_evidence(revision_id, athlete_id, week_start, policy, evidence)
    values (v_revision_id, p_athlete_id, v_plan.week_start, 'weekly-registration-2', p_payload -> 'weekly_registration_evidence');
  for v_warning in select value from jsonb_array_elements(p_payload -> 'warnings') loop
    insert into public.plan_warnings(revision_id, athlete_id, rule_id, code, severity, message)
      values (v_revision_id, p_athlete_id, v_warning ->> 'rule_id', v_warning ->> 'code',
        v_warning ->> 'severity', v_warning ->> 'message');
  end loop;
  insert into public.change_proposals(athlete_id, kind, target_plan_revision_id, base_plan_revision, reason_codes,
    public_explanation, ruleset_version)
    values (p_athlete_id, 'plan_revision', v_revision_id, (p_payload ->> 'expected_base_revision')::integer,
      case when jsonb_array_length(p_payload -> 'warnings') = 0 then array['weekly_plan_ready'] else
        array(select value ->> 'code' from jsonb_array_elements(p_payload -> 'warnings')) end,
      'A deterministic weekly plan is ready for review.', p_payload ->> 'ruleset_version') returning id into v_proposal_id;
  update public.initial_plan_requests set status = 'consumed', consumed_at = statement_timestamp()
    where id = v_request.id and status = 'pending';
  v_result := jsonb_build_object('plan_id', v_plan.id, 'revision', v_revision, 'proposal_id', v_proposal_id);
  if v_key is not null then
    v_public := private.v6_public_plan(p_athlete_id, v_plan.id, v_revision);
    insert into private.v6_edit_results(athlete_id, operation_key, revision_id, result)
      values (p_athlete_id, v_key, v_revision_id, jsonb_build_object('plan', v_public, 'proposal', v_public -> 'proposal'));
  end if;
  return v_result;
end;
$$;
revoke all on function public.create_v6_weekly_plan_proposal(uuid, jsonb) from public, anon, authenticated, service_role;
grant execute on function public.create_v6_weekly_plan_proposal(uuid, jsonb) to service_role;

-- Recheck input custody on confirmation, including consumed requests which
-- historical refresh triggers deliberately leave immutable. Existing V2 evidence
-- guard still applies independently; no historical plan is reinterpreted.
create function private.guard_v6_plan_approval() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_snapshot private.v6_plan_snapshots;
begin
  if old.state = 'pending_approval' and new.state = 'active' then
    select * into v_snapshot from private.v6_plan_snapshots where revision_id = new.id and athlete_id = new.athlete_id;
    if found and v_snapshot.input_snapshot is distinct from private.build_phase_8_5_planning_input_snapshot(new.athlete_id) then
      raise exception 'plan proposal is stale' using errcode = 'PT409';
    end if;
  end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_plan_approval() from public, anon, authenticated, service_role;
create trigger v6_guard_plan_approval before update of state on public.plan_revisions
  for each row execute function private.guard_v6_plan_approval();

-- The V6 immutable snapshot contract is enforced even if an owner opens a SQL
-- session and sets the legacy critical_write GUC themselves. Existing status /
-- approval transitions remain available; source/load/schedule snapshots do not.
create function private.guard_v6_frozen_snapshot_mutation() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_protected boolean := false; v_mutable text[] := '{}';
begin
  if tg_op = 'DELETE' and pg_trigger_depth() > 1 then return old; end if;
  if tg_table_name = 'planned_workouts' then
    v_protected := exists(select 1 from private.v6_occurrence_snapshots where planned_workout_id = old.id);
    v_mutable := array['status'];
  elsif tg_table_name = 'plan_revisions' then
    v_protected := exists(select 1 from private.v6_plan_snapshots where revision_id = old.id);
    v_mutable := array['state'];
  elsif tg_table_name = 'planned_workout_loads' then
    v_protected := exists(select 1 from private.v6_occurrence_snapshots where planned_workout_id = old.planned_workout_id);
  elsif tg_table_name = 'plan_revision_loads' then
    v_protected := exists(select 1 from private.v6_plan_snapshots where revision_id = old.revision_id);
  end if;
  if v_protected and (tg_op = 'DELETE' or (to_jsonb(new) - v_mutable) is distinct from (to_jsonb(old) - v_mutable)) then
    raise exception 'V6 revision snapshots are immutable' using errcode = '55000';
  end if;
  if tg_op = 'DELETE' then return old; end if;
  return new;
end;
$$;
revoke all on function private.guard_v6_frozen_snapshot_mutation() from public, anon, authenticated, service_role;
create trigger v6_frozen_snapshot_immutable before update or delete on public.planned_workouts
  for each row execute function private.guard_v6_frozen_snapshot_mutation();
create trigger v6_frozen_snapshot_immutable before update or delete on public.plan_revisions
  for each row execute function private.guard_v6_frozen_snapshot_mutation();
create trigger v6_frozen_snapshot_immutable before update or delete on private.planned_workout_loads
  for each row execute function private.guard_v6_frozen_snapshot_mutation();
create trigger v6_frozen_snapshot_immutable before update or delete on private.plan_revision_loads
  for each row execute function private.guard_v6_frozen_snapshot_mutation();
notify pgrst, 'reload schema';
