-- Inactive local V6 lifecycle completion. No activation or historical updates.
create or replace function public.get_checkin_context_for_planning(
  p_athlete_id uuid,
  p_checkin_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'checkin_id', checkin.id,
    'week_start', checkin.week_start,
    'timezone', checkin.timezone,
    'confirmed_context', context.payload,
    'checkin_context_revision', context.revision,
    'checkin_context_fingerprint', context.fingerprint,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = checkin.athlete_id
        and maintenance.status = 'active'
    ),
    'plan_id', plan.id,
    'active_revision', plan.active_revision,
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot,
    'onboarding_status', session.status,
    'completed_onboarding_version', session.completed_onboarding_version,
    'completed_ruleset_version', session.completed_ruleset_version
  )
  into v_result
  from public.weekly_checkins checkin
  join public.weekly_checkin_contexts context
    on context.checkin_id = checkin.id
   and context.athlete_id = checkin.athlete_id
   and context.state = 'confirmed'
  join lateral (
    select candidate.*
    from public.initial_plan_requests candidate
    where candidate.athlete_id = checkin.athlete_id
      and candidate.status in ('pending', 'consumed')
    order by candidate.refreshed_at desc
    limit 1
  ) request on true
  join public.onboarding_sessions session
    on session.athlete_id = checkin.athlete_id
  left join public.weekly_plans plan
    on plan.athlete_id = checkin.athlete_id
   and plan.week_start = checkin.week_start
  where checkin.id = p_checkin_id
    and checkin.athlete_id = p_athlete_id
    and checkin.status = 'open';
  if v_result is null then
    raise exception 'check-in context is not confirmed' using errcode = 'PT409';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_checkin_context_for_planning(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_checkin_context_for_planning(uuid, uuid)
to service_role;

create or replace function private.write_v6_weekly_plan_proposal(p_athlete_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_plan public.weekly_plans; v_pending public.plan_revisions; v_proposal public.change_proposals;
  v_request public.initial_plan_requests; v_prior private.v6_plan_snapshots;
  v_revision_id uuid; v_revision integer; v_proposal_id uuid; v_workout_id uuid;
  v_workout jsonb; v_warning jsonb; v_row private.v6_source_revisions; v_total numeric := 0;
  v_result jsonb; v_public jsonb; v_retry_payload jsonb;
  v_key text; v_ordinal integer := 0; v_checkin uuid; v_context public.weekly_checkin_contexts;
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
  -- Called only through A5 for check-ins, after its owner/check-in row lock.
  v_checkin := nullif(p_payload ->> 'checkin_id', '')::uuid;
  if v_checkin is not null then
    select c.* into v_context from public.weekly_checkin_contexts c
      join public.weekly_checkins k on k.id = c.checkin_id and k.athlete_id = c.athlete_id
      where c.checkin_id = v_checkin and c.athlete_id = p_athlete_id
        and k.status = 'open' and k.week_start = (p_payload ->> 'week_start')::date
        and k.timezone = p_payload ->> 'timezone' and c.state = 'confirmed'
        and c.revision = k.context_revision
      for update of c;
    if not found or v_context.revision is distinct from (p_payload #>> '{v6_checkin_context,revision}')::integer
      or v_context.fingerprint is distinct from p_payload #>> '{v6_checkin_context,fingerprint}'
      or v_context.payload is distinct from p_payload #> '{v6_checkin_context,payload}' then
      raise exception 'check-in context is stale' using errcode = 'PT409';
    end if;
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
    if not found or ((v_prior.payload -> 'v6_frozen_snapshot') - 'templates' - 'optimality' - 'examined' - 'estimated_sports')
      is distinct from ((p_payload -> 'v6_frozen_snapshot') - 'templates' - 'optimality' - 'examined' - 'estimated_sports') then
      raise exception 'planning input is stale' using errcode = 'PT409';
    end if;
    if exists (select 1 from unnest(array['week_start','timezone','phase','target_basis','target_tss',
      'taper_period','confirmed_injuries','low_only_disciplines','cross_training_opt_ins','goal_disciplines',
      'availability','available_dates','availability_source','initial_plan_request_id','input_fingerprint',
      'weekly_registration_evidence']) field where v_prior.payload -> field is distinct from p_payload -> field) then
      raise exception 'planning input is stale' using errcode = 'PT409';
    end if;
  elsif v_plan.id is not null and (v_checkin is null or v_pending.id is not null) then
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
    taper_period, input_fingerprint, generation_fingerprint, initial_plan_request_id, checkin_id, total_duration_minutes,
    low_intensity_percent, high_intensity_percent, confirmed_injuries, low_only_disciplines, cross_training_opt_ins,
    availability, available_dates, availability_source, ruleset_version, planning_ruleset_version)
  values (v_plan.id, p_athlete_id, v_revision, 'pending_approval', 'system_generated', p_payload ->> 'phase',
    p_payload ->> 'target_basis', nullif(p_payload ->> 'taper_period',''), p_payload ->> 'input_fingerprint',
    p_payload ->> 'generation_fingerprint', v_request.id, v_checkin, (p_payload ->> 'total_duration_minutes')::numeric,
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
create or replace function public.create_weekly_plan_proposal_v3(
  p_athlete_id uuid, p_payload jsonb
)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_result jsonb;
  v_checkin_id uuid := nullif(p_payload ->> 'checkin_id', '')::uuid;
  v_checkin public.weekly_checkins%rowtype;
  v_existing_count integer;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if v_checkin_id is not null then
    -- Serialize before creating any plan/revision. Creation plus attachment
    -- commits or rolls back together, including all nested v2 writes.
    select * into v_checkin from public.weekly_checkins
    where id = v_checkin_id and athlete_id = p_athlete_id for update;
    if not found then
      raise exception 'weekly check-in not found' using errcode = 'P0002';
    end if;
    if v_checkin.plan_proposal_id is not null then
      select jsonb_build_object('plan_id', revision.plan_id,
        'revision', revision.revision_number, 'proposal_id', proposal.id)
      into v_result
      from public.change_proposals proposal
      join public.plan_revisions revision
        on revision.id = proposal.target_plan_revision_id
       and revision.athlete_id = proposal.athlete_id
      where proposal.id = v_checkin.plan_proposal_id
        and proposal.athlete_id = p_athlete_id
        and proposal.kind = 'plan_revision'
        and revision.checkin_id = v_checkin_id;
      if v_result is null then
        raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
      end if;
      return v_result;
    end if;
    if v_checkin.status <> 'open' then
      raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
    end if;
    -- Compatibility with a pre-A5 commit between persistence and attachment.
    -- Only an unambiguous owned revision can be recovered; terminal state stays.
    select count(*) into v_existing_count
    from public.plan_revisions revision
    join public.change_proposals proposal on proposal.target_plan_revision_id = revision.id
      and proposal.athlete_id = revision.athlete_id
    where revision.checkin_id = v_checkin_id and revision.athlete_id = p_athlete_id
      and proposal.kind = 'plan_revision';
    if v_existing_count > 1 then
      raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
    elsif v_existing_count = 1 then
      select jsonb_build_object('plan_id', revision.plan_id,
        'revision', revision.revision_number, 'proposal_id', proposal.id)
      into v_result
      from public.plan_revisions revision
      join public.change_proposals proposal on proposal.target_plan_revision_id = revision.id
        and proposal.athlete_id = revision.athlete_id
      where revision.checkin_id = v_checkin_id and revision.athlete_id = p_athlete_id
      and proposal.kind = 'plan_revision';
      perform public.attach_checkin_plan_proposal(p_athlete_id, v_checkin_id,
        (v_result ->> 'proposal_id')::uuid);
      return v_result;
    end if;
  end if;
  -- Version dispatch sits INSIDE the existing A5 recovery/attachment boundary.
  if p_payload ->> 'planning_ruleset_version' = 'joren-v6-automatic-selection-1' then
    v_result := private.write_v6_weekly_plan_proposal(p_athlete_id, p_payload);
    if v_checkin_id is not null then
      perform public.attach_checkin_plan_proposal(p_athlete_id, v_checkin_id,
        (v_result ->> 'proposal_id')::uuid);
    end if;
    return v_result;
  end if;
  if p_payload ->> 'ruleset_version' <> 'phase-13-joren-ruleset-1'
     or p_payload ->> 'planning_ruleset_version' <>
       'joren-planning-ruleset-2' then
    raise exception 'planning ruleset provenance is invalid'
      using errcode = '23514';
  end if;
  if jsonb_typeof(coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb))
     <> 'array' then
    raise exception 'cross-training choice is invalid' using errcode = '23514';
  end if;
  v_result := public.create_weekly_plan_proposal_v2(p_athlete_id, p_payload);
  perform set_config('start23.critical_write', 'on', true);
  update public.plan_revisions
  set planning_ruleset_version = 'joren-planning-ruleset-2',
      cross_training_opt_ins = array(
        select jsonb_array_elements_text(
          coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb)
        )
      )
  where plan_id = (v_result ->> 'plan_id')::uuid
    and athlete_id = p_athlete_id
    and revision_number = (v_result ->> 'revision')::integer
    and (planning_ruleset_version is null
      or planning_ruleset_version = 'joren-planning-ruleset-2');
  if not found then
    raise exception 'planning revision provenance is invalid'
      using errcode = '23514';
  end if;
  if v_checkin_id is not null then
    perform public.attach_checkin_plan_proposal(p_athlete_id, v_checkin_id,
      (v_result ->> 'proposal_id')::uuid);
  end if;
  return v_result;
end;
$$;
revoke all on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  to service_role;


-- Public V6 writes cannot bypass A5 when a check-in is supplied.
create or replace function public.create_v6_weekly_plan_proposal(p_athlete_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if nullif(p_payload ->> 'checkin_id', '') is not null then
    return public.create_weekly_plan_proposal_v3(p_athlete_id, p_payload);
  end if;
  return private.write_v6_weekly_plan_proposal(p_athlete_id, p_payload);
end;
$$;
revoke all on function private.write_v6_weekly_plan_proposal(uuid,jsonb) from public, anon, authenticated, service_role;
revoke all on function public.create_v6_weekly_plan_proposal(uuid,jsonb) from public, anon, authenticated, service_role;
grant execute on function public.create_v6_weekly_plan_proposal(uuid,jsonb) to service_role;
-- A5: owner-scoped replay and atomic check-in proposal persistence/attachment.
-- Historical values and states are read as persisted, never regenerated.
create or replace function public.get_checkin_plan_proposal(p_checkin_id uuid)
returns jsonb language plpgsql stable security invoker set search_path = '' as $$
declare
  v_checkin jsonb;
  v_plan_id uuid;
  v_revision integer;
  v_plan jsonb;
begin
  -- Existing invoker RPC supplies the same not-found result for foreign IDs.
  v_checkin := public.get_weekly_checkin(p_checkin_id);
  if v_checkin ->> 'plan_proposal_id' is null then
    if v_checkin ->> 'status' = 'open' then return null; end if;
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  select revision.plan_id, revision.revision_number
  into v_plan_id, v_revision
  from public.change_proposals proposal
  join public.plan_revisions revision
    on revision.id = proposal.target_plan_revision_id
   and revision.athlete_id = proposal.athlete_id
  join public.weekly_checkins checkin
    on checkin.id = revision.checkin_id
   and checkin.athlete_id = revision.athlete_id
   and checkin.plan_proposal_id = proposal.id
  where checkin.id = p_checkin_id
    and checkin.athlete_id = (select auth.uid())
    and checkin.status = 'completed'
    and proposal.kind = 'plan_revision';
  if not found then
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  if exists (select 1 from public.plan_revisions where plan_id = v_plan_id
    and revision_number = v_revision and athlete_id = (select auth.uid())
    and planning_ruleset_version = 'joren-v6-automatic-selection-1') then
    v_plan := public.get_v6_mobile_weekly_plan(v_plan_id, v_revision);
  else
    v_plan := public.get_weekly_plan(v_plan_id, v_revision);
  end if;
  if v_plan #>> '{proposal,id}' is distinct from v_checkin ->> 'plan_proposal_id' then
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  return jsonb_build_object('plan', v_plan, 'proposal', v_plan -> 'proposal');
end;
$$;
revoke all on function public.get_checkin_plan_proposal(uuid)
  from public, anon, authenticated, service_role;
grant execute on function public.get_checkin_plan_proposal(uuid) to authenticated;

-- Resolve logical OR exact physical identity only in the owner's active revision.
create function public.get_v6_move_workout_context(p_workout_id uuid)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_plan uuid; v_revision integer;
begin
  if (select auth.uid()) is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select p.id, r.revision_number into v_plan, v_revision
    from public.weekly_plans p
    join public.plan_revisions r on r.plan_id = p.id and r.athlete_id = p.athlete_id
      and r.revision_number = p.active_revision and r.state = 'active'
    join public.planned_workouts w on w.revision_id = r.id and w.athlete_id = p.athlete_id
    left join private.v6_occurrence_snapshots m on m.planned_workout_id = w.id and m.athlete_id = w.athlete_id
    where p.athlete_id = (select auth.uid()) and (w.id = p_workout_id or m.occurrence_id = p_workout_id);
  if not found then raise exception 'planned workout not found' using errcode = 'P0002'; end if;
  return jsonb_build_object('plan', public.get_v6_mobile_weekly_plan(v_plan, v_revision));
end;
$$;
revoke all on function public.get_v6_move_workout_context(uuid) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_move_workout_context(uuid) to authenticated;

-- Direct, explicit athlete move: same revision architecture as the historical
-- athlete_move operation. No system recommendation or new approval state machine.
create function public.move_v6_planned_workout(p_athlete_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_plan public.weekly_plans; v_old public.plan_revisions; v_snapshot private.v6_plan_snapshots;
  v_new uuid := gen_random_uuid(); v_number integer; v_workout record; v_physical uuid;
  v_result jsonb; v_payload jsonb; v_key text := p_payload ->> 'operation_key';
  v_date date := (p_payload ->> 'scheduled_date')::date;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select * into v_plan from public.weekly_plans
    where id = (p_payload ->> 'plan_id')::uuid and athlete_id = p_athlete_id;
  if not found then raise exception 'weekly plan not found' using errcode = 'P0002'; end if;
  perform pg_advisory_xact_lock(hashtextextended(p_athlete_id::text || ':' || v_plan.week_start::text, 0));
  select result into v_result from private.v6_edit_results
    where athlete_id = p_athlete_id and operation_key = v_key;
  if found then
    if v_result -> 'move_request' is distinct from p_payload then
      raise exception 'idempotency key payload mismatch' using errcode = 'PT409';
    end if;
    return jsonb_set(v_result, '{plan}', private.v6_mobile_plan(p_athlete_id, v_result -> 'plan')) - 'move_request';
  end if;
  -- Same proposal -> revision -> plan row-lock order as approval and V6 edits.
  perform 1 from public.change_proposals c join public.plan_revisions r
    on r.id = c.target_plan_revision_id and r.athlete_id = c.athlete_id
    where r.plan_id = v_plan.id and r.athlete_id = p_athlete_id and c.state = 'pending'
    order by c.id for update of c;
  perform 1 from public.plan_revisions where plan_id = v_plan.id and athlete_id = p_athlete_id
    and state = 'pending_approval' order by id for update;
  select * into v_old from public.plan_revisions where id = (p_payload ->> 'revision_id')::uuid
    and plan_id = v_plan.id and athlete_id = p_athlete_id for update;
  select * into v_plan from public.weekly_plans where id = v_plan.id and athlete_id = p_athlete_id for update;
  if v_old.id is null or v_old.state is distinct from 'active' or v_plan.state is distinct from 'active'
    or v_plan.active_revision is distinct from (p_payload ->> 'expected_revision')::integer
    or v_old.revision_number is distinct from v_plan.active_revision
    or exists (select 1 from public.plan_revisions where plan_id = v_plan.id and athlete_id = p_athlete_id
      and state = 'pending_approval') then
    raise exception 'plan revision is stale' using errcode = 'PT409';
  end if;
  select * into v_snapshot from private.v6_plan_snapshots where revision_id = v_old.id and athlete_id = p_athlete_id;
  if not found then raise exception 'weekly plan not found' using errcode = 'P0002'; end if;
  if v_snapshot.input_snapshot is distinct from private.build_phase_8_5_planning_input_snapshot(p_athlete_id)
    or exists (select 1 from public.injury_restrictions i join public.planned_workouts w
      on w.athlete_id = i.athlete_id and w.discipline = i.discipline
      where i.athlete_id = p_athlete_id and i.cleared_at is null and w.revision_id = v_old.id
        and (i.allowed_intensity = 'none' or w.intensity_bucket <> 'low')) then
    raise exception 'planning input is stale' using errcode = 'PT409';
  end if;
  if v_date is null or not (v_date between v_plan.week_start and v_plan.week_start + 6)
    or not (v_date = any(v_old.available_dates)) then
    raise exception 'workout move must remain in confirmed availability' using errcode = 'PT409';
  end if;
  if not exists (select 1 from private.v6_occurrence_snapshots m
    join public.planned_workouts w on w.id = m.planned_workout_id and w.athlete_id = m.athlete_id
    where m.revision_id = v_old.id and m.athlete_id = p_athlete_id
      and m.occurrence_id = (p_payload ->> 'occurrence_id')::uuid
      and m.planned_workout_id = (p_payload ->> 'physical_workout_id')::uuid and w.status = 'scheduled') then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  -- Existing activity/registration writers acquire this plan lock before evidence.
  -- Reject the week rather than invent evidence carry-forward between physical rows.
  if exists (select 1 from public.planned_workouts w where w.revision_id = v_old.id and
    (w.status <> 'scheduled' or exists (select 1 from public.activities a where a.planned_workout_id = w.id)
      or exists (select 1 from private.workout_registration_events e where e.planned_workout_id = w.id))) then
    raise exception 'recorded workout move unsupported' using errcode = 'PT409';
  end if;
  perform private.assert_current_planning_eligibility(private.resolve_opaque_athlete_id(p_athlete_id));
  perform set_config('start23.critical_write', 'on', true);
  select coalesce(max(revision_number), 0) + 1 into v_number from public.plan_revisions
    where plan_id = v_plan.id and athlete_id = p_athlete_id;
  insert into public.plan_revisions select (jsonb_populate_record(null::public.plan_revisions,
    to_jsonb(v_old) || jsonb_build_object('id', v_new, 'revision_number', v_number,
      'state', 'draft', 'source', 'athlete_move', 'generation_fingerprint', v_key,
      'created_at', statement_timestamp()))).*;
  for v_workout in select w.*, m.occurrence_id, m.ordinal from public.planned_workouts w
    join private.v6_occurrence_snapshots m on m.planned_workout_id = w.id and m.athlete_id = w.athlete_id
    where w.revision_id = v_old.id and w.athlete_id = p_athlete_id order by m.ordinal loop
    v_physical := gen_random_uuid();
    insert into public.planned_workouts select (jsonb_populate_record(null::public.planned_workouts,
      to_jsonb(v_workout) || jsonb_build_object('id', v_physical, 'revision_id', v_new,
        'created_at', statement_timestamp(),
        'scheduled_date', case when v_workout.id = (p_payload ->> 'physical_workout_id')::uuid then v_date else v_workout.scheduled_date end,
        'scheduled_at', case when v_workout.id = (p_payload ->> 'physical_workout_id')::uuid
          then (v_date + time '12:00') at time zone v_plan.timezone else v_workout.scheduled_at end))).*;
    insert into private.v6_occurrence_snapshots(planned_workout_id, revision_id, athlete_id, occurrence_id, ordinal)
      values(v_physical, v_new, p_athlete_id, v_workout.occurrence_id, v_workout.ordinal);
    insert into private.planned_workout_loads select (jsonb_populate_record(null::private.planned_workout_loads,
      to_jsonb(l) || jsonb_build_object('planned_workout_id', v_physical))).*
      from private.planned_workout_loads l where planned_workout_id = v_workout.id;
    insert into public.plan_warnings select (jsonb_populate_record(null::public.plan_warnings,
      to_jsonb(w) || jsonb_build_object('id', gen_random_uuid(), 'revision_id', v_new,
        'planned_workout_id', v_physical))).* from public.plan_warnings w
      where revision_id = v_old.id and planned_workout_id = v_workout.id;
  end loop;
  insert into private.plan_revision_loads select (jsonb_populate_record(null::private.plan_revision_loads,
    to_jsonb(l) || jsonb_build_object('revision_id', v_new))).* from private.plan_revision_loads l where revision_id = v_old.id;
  insert into public.plan_warnings select (jsonb_populate_record(null::public.plan_warnings,
    to_jsonb(w) || jsonb_build_object('id', gen_random_uuid(), 'revision_id', v_new))).*
    from public.plan_warnings w where revision_id = v_old.id and planned_workout_id is null;
  v_payload := jsonb_set(v_snapshot.payload, '{workouts}', (select jsonb_agg(
    case when w ->> 'occurrence_id' = p_payload ->> 'occurrence_id' then w || jsonb_build_object(
      'scheduled_date', v_date, 'scheduled_at', (v_date + time '12:00') at time zone v_plan.timezone) else w end order by n)
    from jsonb_array_elements(v_snapshot.payload -> 'workouts') with ordinality rows(w,n)));
  insert into private.v6_plan_snapshots(revision_id, athlete_id, payload, input_snapshot)
    values(v_new, p_athlete_id, v_payload, v_snapshot.input_snapshot);
  insert into private.realized_v2_plan_evidence select (jsonb_populate_record(null::private.realized_v2_plan_evidence,
    to_jsonb(e) || jsonb_build_object('revision_id', v_new))).* from private.realized_v2_plan_evidence e where revision_id = v_old.id;
  update public.plan_revisions set state = 'superseded' where id = v_old.id;
  update public.plan_revisions set state = 'active' where id = v_new;
  update public.weekly_plans set active_revision = v_number where id = v_plan.id
    and active_revision = (p_payload ->> 'expected_revision')::integer;
  if not found then raise exception 'plan revision is stale' using errcode = 'PT409'; end if;
  v_result := jsonb_build_object('plan', private.v6_public_plan(p_athlete_id, v_plan.id, v_number),
    'proposal', null, 'move_request', p_payload);
  insert into private.v6_edit_results(athlete_id, operation_key, revision_id, result)
    values(p_athlete_id, v_key, v_new, v_result);
  return jsonb_set(v_result, '{plan}', private.v6_mobile_plan(p_athlete_id, v_result -> 'plan')) - 'move_request';
end;
$$;
revoke all on function public.move_v6_planned_workout(uuid,jsonb) from public, anon, authenticated, service_role;
grant execute on function public.move_v6_planned_workout(uuid,jsonb) to service_role;
notify pgrst, 'reload schema';

create or replace function public.get_v6_plan_context_for_planning(p_athlete_id uuid, p_plan_id uuid, p_revision integer default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_context jsonb; v_snapshot private.v6_plan_snapshots;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if p_revision is not null then
    select s.* into v_snapshot from private.v6_plan_snapshots s
      join public.plan_revisions r on r.id = s.revision_id and r.athlete_id = s.athlete_id
      join public.weekly_plans p on p.id = r.plan_id and p.athlete_id = r.athlete_id
      where p.id = p_plan_id and p.athlete_id = p_athlete_id
        and p.active_revision = p_revision and r.revision_number = p_revision and r.state = 'active';
    if found then
      return v_snapshot.payload || jsonb_build_object('revision', p_revision, 'active_revision', p_revision,
        'input_snapshot', v_snapshot.input_snapshot);
    end if;
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


-- Preserve prior confirmation provenance when an athlete explicitly confirms a
-- newly saved context revision. No existing record is transformed by migration.
alter table public.weekly_checkin_contexts
  drop constraint weekly_checkin_contexts_confirmation_valid,
  add constraint weekly_checkin_contexts_confirmation_valid check (
    (state = 'confirmed' and confirmed_at is not null)
    or (state = 'draft' and confirmed_at is null)
    or state = 'superseded'
  );

do $$
declare v_definition text;
begin
  v_definition := pg_get_functiondef('public.confirm_weekly_checkin_context(uuid,integer,text)'::regprocedure);
  if position('  update public.weekly_checkin_contexts' in v_definition) = 0 then
    raise exception 'check-in confirmation definition differs from reviewed contract';
  end if;
  -- Existing owner/check-in CAS lock, exact draft/fingerprint and restriction
  -- review guards run first. Both transitions roll back if either fails.
  v_definition := replace(v_definition, '  update public.weekly_checkin_contexts',
    E'  update public.weekly_checkin_contexts set state = ''superseded''\n'
    || E'  where checkin_id = p_checkin_id and athlete_id = v_athlete_id and state = ''confirmed'';\n'
    || '  update public.weekly_checkin_contexts');
  execute v_definition;
end;
$$;
notify pgrst, 'reload schema';
