-- Close the final H-01 activation path without rewriting historical rows.
-- Existing active historical profiles remain intact; only new transitions into
-- active state are rejected when calibration provenance is read-only.

-- Phase 8.5 prohibited threshold output from every submaximal protocol. Phase
-- 13 explicitly superseded that behavior for its versioned run/bike/swim
-- calibration protocols, but the old constraint was never advanced with the
-- newer evaluation contract.
alter table public.calibration_evaluations
  drop constraint calibration_evaluations_submaximal_no_threshold;

alter table public.calibration_evaluations
  add constraint calibration_evaluations_submaximal_no_threshold check (
    protocol_id not in (
      'start23_week1_run_calibration_v1',
      'start23_week1_bike_calibration_v1',
      'start23_week1_swim_calibration_v1'
    )
    or status <> 'threshold_estimated'
    or ruleset_version = 'phase-13-joren-ruleset-1'
  );

create function private.enforce_current_calibration_zone_activation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_evaluation_id uuid := coalesce(
    old.calibration_evaluation_id,
    new.calibration_evaluation_id
  );
  v_evaluation public.calibration_evaluations;
begin
  if old.status is distinct from 'active'
     and new.status = 'active'
     and v_evaluation_id is not null then
    select evaluation.* into v_evaluation
    from public.calibration_evaluations evaluation
    where evaluation.id = v_evaluation_id
      and evaluation.athlete_id = new.athlete_id;

    if not found
       or not private.is_current_calibration_protocol(
         v_evaluation.protocol_id,
         v_evaluation.discipline
       ) then
      raise exception 'historical calibration profile cannot be activated'
        using errcode = '23514';
    end if;
  end if;

  return new;
end;
$$;

revoke execute
on function private.enforce_current_calibration_zone_activation()
from public, anon, authenticated, service_role;

create trigger zone_profile_versions_r6_entry_current_activation
before update on public.zone_profile_versions
for each row
execute function private.enforce_current_calibration_zone_activation();

create or replace function public.approve_zone_proposal(
  p_proposal_id uuid,
  p_expected_base_zone_profile_id uuid
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_target_id uuid;
  v_base_id uuid;
  v_active_id uuid;
  v_discipline text;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select
    proposal.target_zone_profile_id,
    proposal.base_zone_profile_id,
    profile.discipline
  into v_target_id, v_base_id, v_discipline
  from public.change_proposals proposal
  join public.zone_profile_versions profile
    on profile.id = proposal.target_zone_profile_id
    and profile.athlete_id = proposal.athlete_id
  where proposal.id = p_proposal_id
    and proposal.athlete_id = v_athlete_id
    and proposal.kind = 'zone_update'
    and proposal.state = 'pending'
  for update of proposal;

  if v_target_id is null then
    raise exception 'pending zone proposal not found' using errcode = 'P0002';
  end if;

  if exists (
    select 1
    from public.zone_profile_versions profile
    join public.calibration_evaluations evaluation
      on evaluation.id = profile.calibration_evaluation_id
      and evaluation.athlete_id = profile.athlete_id
    where profile.id = v_target_id
      and profile.athlete_id = v_athlete_id
      and not private.is_current_calibration_protocol(
        evaluation.protocol_id,
        evaluation.discipline
      )
  ) then
    raise exception 'historical calibration profile cannot be activated'
      using errcode = '23514';
  end if;

  if v_base_id is distinct from p_expected_base_zone_profile_id then
    raise exception 'zone proposal base is stale' using errcode = '40001';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':' || v_discipline, 0)
  );
  select id into v_active_id
  from public.zone_profile_versions
  where athlete_id = v_athlete_id
    and discipline = v_discipline
    and status = 'active'
  for update;
  if v_active_id is distinct from v_base_id then
    raise exception 'active zone version has changed' using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.change_proposals
  set
    state = 'approved',
    decided_at = statement_timestamp(),
    decision_actor = v_athlete_id
  where id = p_proposal_id and athlete_id = v_athlete_id;
  update public.zone_profile_versions
  set status = 'superseded'
  where id = v_base_id and athlete_id = v_athlete_id and status = 'active';
  update public.zone_profile_versions
  set
    status = 'active',
    effective_from = statement_timestamp(),
    review_status = case
      when setup_method = 'calculated' then 'confirmed_by_athlete'
      else review_status
    end,
    reviewed_at = case
      when setup_method = 'calculated' then statement_timestamp()
      else reviewed_at
    end
  where id = v_target_id and athlete_id = v_athlete_id and status = 'pending';
  if not found then
    raise exception 'target zone version is no longer pending'
      using errcode = '40001';
  end if;
  update public.change_proposals
  set state = 'applied', applied_at = statement_timestamp()
  where id = p_proposal_id and athlete_id = v_athlete_id and state = 'approved';

  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'applied',
    'active_zone_profile_id', v_target_id,
    'superseded_zone_profile_id', v_base_id
  );
end;
$$;

revoke all on function public.approve_zone_proposal(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.approve_zone_proposal(uuid, uuid)
to authenticated;

comment on function private.enforce_current_calibration_zone_activation() is
  'Rejects new activation of zone profiles sourced from historical calibration while preserving already-active history.';

comment on function public.approve_zone_proposal(uuid, uuid) is
  'Applies an owner and stale-safe pending zone proposal only when any calibration provenance is current-selectable.';
