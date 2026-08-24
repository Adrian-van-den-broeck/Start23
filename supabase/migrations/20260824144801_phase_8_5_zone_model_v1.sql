-- Start23 Zone 1-5 model v1.0.
-- Calculations stay in deterministic Python; this migration persists their
-- provenance and enforces the two explicit athlete decisions:
-- threshold confirmation first, zone-profile activation second.

alter table public.zone_profile_versions
  drop constraint zone_profile_setup_method_valid,
  drop constraint zone_profile_flags_consistent,
  drop constraint zone_profile_review_reason_valid;

alter table public.zone_profile_versions
  add column zone_model_version text,
  add column source_method text not null default 'athlete_entered',
  add column source_quality text not null default 'athlete_entered',
  add column calculated_at timestamptz,
  add column review_status text not null default 'confirmed_by_athlete',
  add column reviewer_id text,
  add column reviewed_at timestamptz,
  add column evidence_version text,
  add column metric_profiles jsonb not null default '[]'::jsonb,
  add column calculation_fingerprint text,
  add column calibration_evaluation_id uuid;

update public.zone_profile_versions
set
  source_method = 'tanaka_karvonen_age_hrrest',
  source_quality = 'estimated'
where setup_method = 'fallback';

alter table public.zone_profile_versions
  add constraint zone_profile_setup_method_valid
    check (setup_method in ('manual', 'fallback', 'calculated')),
  add constraint zone_profile_flags_consistent
    check (
      (
        setup_method = 'manual'
        and validated
        and not fallback_active
        and not needs_testing
      )
      or (
        setup_method = 'fallback'
        and not validated
        and fallback_active
        and needs_testing
      )
      or (
        setup_method = 'calculated'
        and not validated
        and not fallback_active
        and not needs_testing
        and requires_review
      )
    ),
  add constraint zone_profile_review_reason_valid
    check (
      review_reason in (
        'within_soft_range',
        'outside_soft_range',
        'soft_range_not_configured',
        'fallback_unvalidated',
        'athlete_confirmation_required'
      )
    ),
  add constraint zone_profile_source_quality_valid
    check (
      source_quality in (
        'measured_lab',
        'reviewed_field_threshold',
        'athlete_entered',
        'estimated',
        'unknown'
      )
    ),
  add constraint zone_profile_review_status_valid
    check (
      review_status in (
        'pending_athlete_confirmation',
        'confirmed_by_athlete',
        'rejected_by_athlete',
        'unreviewed'
      )
    ),
  add constraint zone_profile_metric_profiles_array
    check (jsonb_typeof(metric_profiles) = 'array'),
  add constraint zone_profile_calculation_fingerprint_valid
    check (
      calculation_fingerprint is null
      or calculation_fingerprint ~ '^[a-f0-9]{64}$'
    ),
  add constraint zone_profile_calculated_metadata_valid
    check (
      setup_method <> 'calculated'
      or (
        zone_model_version = 'start23-zone-model-1.0'
        and source_quality in ('athlete_entered', 'reviewed_field_threshold')
        and calculated_at is not null
        and review_status in (
          'pending_athlete_confirmation',
          'confirmed_by_athlete',
          'rejected_by_athlete'
        )
        and evidence_version = 'voorstel-start23-zone-1-5-rekenmodel-v1.0'
        and jsonb_array_length(metric_profiles) between 1 and 2
        and calculation_fingerprint is not null
        and review_reason = 'athlete_confirmation_required'
        and ruleset_version = 'start23-zone-model-1.0'
      )
    ),
  add constraint zone_profile_calibration_evaluation_fkey
    foreign key (calibration_evaluation_id, athlete_id)
    references public.calibration_evaluations (id, athlete_id);

create unique index zone_profiles_calculation_retry_idx
on public.zone_profile_versions (
  athlete_id,
  discipline,
  calculation_fingerprint
)
where setup_method = 'calculated' and status in ('pending', 'active');

create unique index zone_profiles_one_per_calibration_evaluation
on public.zone_profile_versions (calibration_evaluation_id)
where calibration_evaluation_id is not null;

alter table public.calibration_evaluations
  add column zone_model_version text,
  add column zone_profiles jsonb not null default '[]'::jsonb;

alter table public.calibration_evaluations
  drop constraint calibration_evaluations_ruleset_valid,
  drop constraint calibration_evaluations_zone_status_valid,
  drop constraint calibration_evaluations_pending_consistent;

alter table public.calibration_evaluations
  add constraint calibration_evaluations_ruleset_valid
    check (
      ruleset_version in (
        'start23-calibration-ruleset-v1',
        'start23-calibration-ruleset-v2'
      )
    ),
  add constraint calibration_evaluations_zone_status_valid
    check (
      zone_status in (
        'unknown',
        'provisionally_calibrated',
        'pending_protocol',
        'pending_athlete_confirmation'
      )
    ),
  add constraint calibration_evaluations_zone_profiles_valid
    check (
      jsonb_typeof(zone_profiles) = 'array'
      and jsonb_array_length(zone_profiles) <= 2
    ),
  add constraint calibration_evaluations_pending_consistent
    check (
      (
        ruleset_version = 'start23-calibration-ruleset-v1'
        and status = 'threshold_estimated'
        and threshold_status = 'threshold_estimated'
        and zone_status = 'pending_protocol'
        and confidence = 'medium'
        and jsonb_array_length(thresholds) > 0
        and requires_athlete_confirmation
        and review_status = 'pending_athlete_confirmation'
        and 'zone_model_not_approved' = any(reason_codes)
        and zone_model_version is null
        and zone_profiles = '[]'::jsonb
      )
      or (
        ruleset_version = 'start23-calibration-ruleset-v2'
        and status = 'threshold_estimated'
        and threshold_status = 'threshold_estimated'
        and zone_status = 'pending_athlete_confirmation'
        and confidence = 'medium'
        and jsonb_array_length(thresholds) > 0
        and requires_athlete_confirmation
        and review_status = 'pending_athlete_confirmation'
        and 'zone_profile_pending_athlete_confirmation' = any(reason_codes)
        and zone_model_version = 'start23-zone-model-1.0'
        and jsonb_array_length(zone_profiles) between 1 and 2
      )
      or (
        status <> 'threshold_estimated'
        and threshold_status = 'unknown'
        and jsonb_array_length(thresholds) = 0
        and not requires_athlete_confirmation
        and review_status = 'not_applicable'
        and zone_model_version is null
        and zone_profiles = '[]'::jsonb
      )
    );

alter table public.discipline_zone_setups
  drop constraint discipline_zone_setups_zone_status_valid,
  drop constraint discipline_zone_setups_route_consistent;

alter table public.discipline_zone_setups
  add constraint discipline_zone_setups_zone_status_valid
    check (
      zone_status in (
        'unknown',
        'user_provided',
        'pending_protocol',
        'pending_athlete_confirmation'
      )
    ),
  add constraint discipline_zone_setups_route_consistent
    check (
      (
        setup_route = 'known_values'
        and setup_status = 'configured'
        and protocol_id is null
        and source = 'user_provided'
        and validation_status = 'self_reported'
        and jsonb_array_length(known_thresholds)
          + jsonb_array_length(known_zone_profiles) > 0
        and threshold_status = case
          when jsonb_array_length(known_thresholds) > 0
            then 'user_provided'
          else 'unknown'
        end
        and zone_status = case
          when jsonb_array_length(known_thresholds) > 0
            then 'pending_athlete_confirmation'
          else 'user_provided'
        end
      )
      or (
        setup_route = 'field_test'
        and setup_status = 'test_pending'
        and protocol_id is not null
        and source = 'field_test'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
      or (
        setup_route = 'calibration_week'
        and setup_status = 'calibration_pending'
        and protocol_id is not null
        and source = 'week1_calibration'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
      or (
        setup_route = 'rpe_only'
        and guidance_mode = 'rpe_only'
        and setup_status = 'configured'
        and protocol_id is null
        and source = 'none'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
    );

create table public.calibration_threshold_decisions (
  evaluation_id uuid primary key,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  state text not null,
  zone_profile_id uuid,
  zone_proposal_id uuid,
  base_zone_profile_id uuid,
  decided_at timestamptz not null default statement_timestamp(),

  unique (evaluation_id, athlete_id),
  foreign key (evaluation_id, athlete_id)
    references public.calibration_evaluations (id, athlete_id),
  foreign key (zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id),
  foreign key (zone_proposal_id)
    references public.change_proposals (id),
  foreign key (base_zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id),
  constraint calibration_threshold_decisions_state_valid
    check (state in ('accepted', 'rejected')),
  constraint calibration_threshold_decisions_result_valid
    check (
      (
        state = 'accepted'
        and zone_profile_id is not null
        and zone_proposal_id is not null
      )
      or (
        state = 'rejected'
        and zone_profile_id is null
        and zone_proposal_id is null
        and base_zone_profile_id is null
      )
    )
);

create index calibration_threshold_decisions_owner_idx
on public.calibration_threshold_decisions (athlete_id, decided_at desc);

create trigger calibration_threshold_decisions_are_immutable
before update or delete on public.calibration_threshold_decisions
for each row execute function private.reject_calibration_record_mutation();

create trigger calibration_threshold_decisions_require_rpc
before insert or delete on public.calibration_threshold_decisions
for each row execute function private.require_critical_write_context();

alter table public.calibration_threshold_decisions enable row level security;
alter table public.calibration_threshold_decisions force row level security;

revoke all on table public.calibration_threshold_decisions
from public, anon, authenticated, service_role;
grant select on table public.calibration_threshold_decisions to authenticated;

create policy calibration_threshold_decisions_select_own
on public.calibration_threshold_decisions for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create or replace function public.save_calibration_evaluation(
  p_athlete_id uuid,
  p_evaluation jsonb,
  p_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_existing public.calibration_evaluations;
  v_evaluation public.calibration_evaluations;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_athlete_id is null
     or jsonb_typeof(p_evaluation) <> 'object'
     or not p_evaluation ?& array[
       'activity_id', 'protocol_id', 'discipline', 'ruleset_version',
       'status', 'threshold_status', 'zone_status', 'confidence',
       'reason_codes', 'thresholds', 'requires_athlete_confirmation',
       'review_status'
     ]
     or p_evaluation ?| array[
       'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ]
     or p_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid calibration evaluation payload'
      using errcode = '23514';
  end if;
  if p_evaluation ->> 'ruleset_version' = 'start23-calibration-ruleset-v2'
     and not p_evaluation ?& array['zone_model_version', 'zone_profiles'] then
    raise exception 'zone-model evaluation metadata is required'
      using errcode = '23514';
  end if;
  if not exists (
    select 1
    from public.activities activity
    where activity.id = (p_evaluation ->> 'activity_id')::uuid
      and activity.athlete_id = p_athlete_id
  ) then
    raise exception 'owned activity not found' using errcode = 'P0002';
  end if;

  select * into v_existing
  from public.calibration_evaluations
  where athlete_id = p_athlete_id and fingerprint = p_fingerprint;
  if found then
    return to_jsonb(v_existing) - 'athlete_id';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  insert into public.calibration_evaluations (
    athlete_id,
    activity_id,
    protocol_id,
    discipline,
    ruleset_version,
    status,
    threshold_status,
    zone_status,
    confidence,
    reason_codes,
    thresholds,
    zone_model_version,
    zone_profiles,
    requires_athlete_confirmation,
    review_status,
    fingerprint
  )
  values (
    p_athlete_id,
    (p_evaluation ->> 'activity_id')::uuid,
    p_evaluation ->> 'protocol_id',
    p_evaluation ->> 'discipline',
    p_evaluation ->> 'ruleset_version',
    p_evaluation ->> 'status',
    p_evaluation ->> 'threshold_status',
    p_evaluation ->> 'zone_status',
    p_evaluation ->> 'confidence',
    array(select jsonb_array_elements_text(p_evaluation -> 'reason_codes')),
    p_evaluation -> 'thresholds',
    p_evaluation ->> 'zone_model_version',
    coalesce(p_evaluation -> 'zone_profiles', '[]'::jsonb),
    (p_evaluation ->> 'requires_athlete_confirmation')::boolean,
    p_evaluation ->> 'review_status',
    p_fingerprint
  )
  returning * into v_evaluation;

  return to_jsonb(v_evaluation) - 'athlete_id';
end;
$$;

revoke all on function public.save_calibration_evaluation(uuid, jsonb, text)
from public, anon, authenticated, service_role;
grant execute
on function public.save_calibration_evaluation(uuid, jsonb, text)
to service_role;

create or replace function private.require_trusted_zone_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.setup_method = 'fallback' then
    if current_setting('start23.trusted_fallback', true) is distinct from 'on' then
      raise exception 'fallback zones require the trusted backend RPC'
        using errcode = '42501';
    end if;
    if new.requires_review is distinct from true
       or new.review_reason <> 'fallback_unvalidated'
       or new.ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'fallback review metadata is server-controlled'
        using errcode = '23514';
    end if;
    new.source_method := 'tanaka_karvonen_age_hrrest';
    new.source_quality := 'estimated';
    new.review_status := 'confirmed_by_athlete';
  elsif new.setup_method = 'manual' then
    if new.requires_review is distinct from true
       or new.review_reason <> 'soft_range_not_configured'
       or new.ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'manual zone review metadata is server-controlled'
        using errcode = '23514';
    end if;
    new.source_method := 'athlete_entered';
    new.source_quality := 'athlete_entered';
    new.review_status := 'confirmed_by_athlete';
  elsif new.setup_method = 'calculated' then
    if current_setting('start23.trusted_calculated_zone', true)
         is distinct from 'on' then
      raise exception 'calculated zones require the trusted backend RPC'
        using errcode = '42501';
    end if;
    if new.requires_review is distinct from true
       or new.review_reason <> 'athlete_confirmation_required'
       or new.ruleset_version <> 'start23-zone-model-1.0'
       or new.zone_model_version <> 'start23-zone-model-1.0'
       or new.evidence_version <>
          'voorstel-start23-zone-1-5-rekenmodel-v1.0'
       or new.review_status <> 'pending_athlete_confirmation' then
      raise exception 'calculated zone provenance is server-controlled'
        using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

revoke execute on function private.require_trusted_zone_metadata()
from public, anon, authenticated, service_role;

create function public.save_calculated_zone_profile(
  p_athlete_id uuid,
  p_profile jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_profile public.zone_profile_versions;
  v_existing public.zone_profile_versions;
  v_evaluation public.calibration_evaluations;
  v_decision public.calibration_threshold_decisions;
  v_proposal public.change_proposals;
  v_metric jsonb;
  v_metric_count integer;
  v_primary_count integer := 0;
  v_active_id uuid;
  v_version integer;
  v_source_quality text;
  v_source_method text;
  v_evaluation_id uuid;
  v_original_trusted text :=
    current_setting('start23.trusted_calculated_zone', true);
  v_original_critical_write text :=
    current_setting('start23.critical_write', true);
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_athlete_id is null
     or not exists (select 1 from auth.users where id = p_athlete_id) then
    raise exception 'athlete not found' using errcode = 'P0002';
  end if;
  if jsonb_typeof(p_profile) <> 'object'
     or not p_profile ?& array[
       'discipline', 'source_method', 'source_quality', 'metric_profiles',
       'input_fingerprint', 'calibration_evaluation_id'
     ]
     or p_profile ?| array[
       'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ]
     or p_profile ->> 'discipline' not in ('swim', 'bike', 'run')
     or p_profile ->> 'input_fingerprint' !~ '^[a-f0-9]{64}$'
     or jsonb_typeof(p_profile -> 'metric_profiles') <> 'array'
     or jsonb_array_length(p_profile -> 'metric_profiles') not between 1 and 2 then
    raise exception 'invalid calculated zone payload' using errcode = '23514';
  end if;

  v_source_quality := p_profile ->> 'source_quality';
  v_source_method := p_profile ->> 'source_method';
  v_evaluation_id := nullif(
    p_profile ->> 'calibration_evaluation_id',
    ''
  )::uuid;

  if v_source_quality = 'athlete_entered' then
    if v_source_method <> 'athlete_entered' or v_evaluation_id is not null then
      raise exception 'athlete-entered zone provenance is inconsistent'
        using errcode = '23514';
    end if;
  elsif v_source_quality = 'reviewed_field_threshold' then
    if v_evaluation_id is null then
      raise exception 'field threshold requires an evaluation'
        using errcode = '23514';
    end if;
    select * into v_evaluation
    from public.calibration_evaluations
    where id = v_evaluation_id
      and athlete_id = p_athlete_id
      and discipline = p_profile ->> 'discipline'
      and status = 'threshold_estimated'
      and requires_athlete_confirmation
      and zone_model_version = 'start23-zone-model-1.0';
    if not found then
      raise exception 'pending calibration evaluation not found'
        using errcode = 'P0002';
    end if;
    if v_evaluation.zone_profiles is distinct from p_profile -> 'metric_profiles'
       or v_source_method is distinct from v_evaluation.protocol_id then
      raise exception 'field-test zone calculation does not match its evaluation'
        using errcode = '23514';
    end if;
  else
    raise exception 'unsupported calculated zone source quality'
      using errcode = '23514';
  end if;

  v_metric_count := jsonb_array_length(p_profile -> 'metric_profiles');
  for v_metric in
    select value from jsonb_array_elements(p_profile -> 'metric_profiles')
  loop
    if jsonb_typeof(v_metric) <> 'object'
       or not v_metric ?& array[
         'metric_kind', 'source_value', 'is_primary', 'boundary_source',
         'zone_model_version', 'boundaries'
       ]
       or v_metric ->> 'zone_model_version' <> 'start23-zone-model-1.0'
       or v_metric ->> 'boundary_source'
          not in ('model_derived', 'athlete_entered')
       or (v_metric ->> 'source_value')::numeric <= 0
       or jsonb_typeof(v_metric -> 'boundaries') <> 'array'
       or jsonb_array_length(v_metric -> 'boundaries') <> 5
       or (
         select count(distinct (boundary ->> 'zone_number')::integer)
         from jsonb_array_elements(v_metric -> 'boundaries') boundary
         where (boundary ->> 'zone_number')::integer between 1 and 5
       ) <> 5 then
      raise exception 'invalid calculated metric profile'
        using errcode = '23514';
    end if;
    if (v_metric ->> 'is_primary')::boolean then
      v_primary_count := v_primary_count + 1;
    end if;
    if not (
      (
        p_profile ->> 'discipline' = 'swim'
        and v_metric ->> 'metric_kind' = 'swim_css_seconds_per_100m'
      )
      or (
        p_profile ->> 'discipline' = 'bike'
        and v_metric ->> 'metric_kind' in (
          'bike_ftp_watts', 'bike_threshold_heart_rate_bpm'
        )
      )
      or (
        p_profile ->> 'discipline' = 'run'
        and v_metric ->> 'metric_kind' in (
          'run_threshold_pace_seconds_per_km', 'run_lthr_bpm'
        )
      )
    ) then
      raise exception 'calculated metric does not belong to discipline'
        using errcode = '23514';
    end if;
  end loop;
  if v_primary_count <> 1 then
    raise exception 'exactly one calculated metric must be primary'
      using errcode = '23514';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(
    p_athlete_id::text || ':' || (p_profile ->> 'discipline'),
    0
  ));

  select * into v_existing
  from public.zone_profile_versions
  where athlete_id = p_athlete_id
    and discipline = p_profile ->> 'discipline'
    and setup_method = 'calculated'
    and status in ('pending', 'active')
    and calculation_fingerprint = p_profile ->> 'input_fingerprint';
  if found then
    select * into v_proposal
    from public.change_proposals
    where target_zone_profile_id = v_existing.id
      and athlete_id = p_athlete_id;
    if v_evaluation_id is not null then
      select * into v_decision
      from public.calibration_threshold_decisions
      where evaluation_id = v_evaluation_id
        and athlete_id = p_athlete_id;
    end if;
    return jsonb_build_object(
      'profile_id', v_existing.id,
      'version', v_existing.version,
      'status', v_existing.status,
      'proposal_id', v_proposal.id,
      'evaluation_id', v_evaluation_id,
      'state', case when v_evaluation_id is null then null else 'accepted' end,
      'zone_profile_id', v_existing.id,
      'zone_proposal_id', v_proposal.id,
      'base_zone_profile_id', v_proposal.base_zone_profile_id,
      'decided_at', v_decision.decided_at
    );
  end if;

  if v_evaluation_id is not null then
    select * into v_decision
    from public.calibration_threshold_decisions
    where evaluation_id = v_evaluation_id
      and athlete_id = p_athlete_id;
    if found then
      return to_jsonb(v_decision) - 'athlete_id';
    end if;
  end if;

  select id into v_active_id
  from public.zone_profile_versions
  where athlete_id = p_athlete_id
    and discipline = p_profile ->> 'discipline'
    and status = 'active'
  for update;

  select coalesce(max(version), 0) + 1 into v_version
  from public.zone_profile_versions
  where athlete_id = p_athlete_id
    and discipline = p_profile ->> 'discipline';

  perform set_config('start23.critical_write', 'on', true);
  perform set_config('start23.trusted_calculated_zone', 'on', true);

  insert into public.zone_profile_versions (
    athlete_id,
    discipline,
    version,
    setup_method,
    status,
    validated,
    fallback_active,
    needs_testing,
    requires_review,
    review_reason,
    ruleset_version,
    zone_model_version,
    source_method,
    source_quality,
    calculated_at,
    review_status,
    evidence_version,
    metric_profiles,
    calculation_fingerprint,
    calibration_evaluation_id
  ) values (
    p_athlete_id,
    p_profile ->> 'discipline',
    v_version,
    'calculated',
    'pending',
    false,
    false,
    false,
    true,
    'athlete_confirmation_required',
    'start23-zone-model-1.0',
    'start23-zone-model-1.0',
    v_source_method,
    v_source_quality,
    statement_timestamp(),
    'pending_athlete_confirmation',
    'voorstel-start23-zone-1-5-rekenmodel-v1.0',
    p_profile -> 'metric_profiles',
    p_profile ->> 'input_fingerprint',
    v_evaluation_id
  ) returning * into v_profile;

  insert into public.change_proposals (
    athlete_id,
    kind,
    target_zone_profile_id,
    base_zone_profile_id,
    reason_codes,
    public_explanation,
    ruleset_version
  ) values (
    p_athlete_id,
    'zone_update',
    v_profile.id,
    v_active_id,
    array['calculated_zone_profile_requires_approval'],
    'Nieuwe berekende zones staan klaar. Je actieve zones wijzigen pas na jouw bevestiging.',
    'start23-zone-model-1.0'
  ) returning * into v_proposal;

  if v_evaluation_id is not null then
    insert into public.calibration_threshold_decisions (
      evaluation_id,
      athlete_id,
      state,
      zone_profile_id,
      zone_proposal_id,
      base_zone_profile_id
    ) values (
      v_evaluation_id,
      p_athlete_id,
      'accepted',
      v_profile.id,
      v_proposal.id,
      v_active_id
    ) returning * into v_decision;
  end if;

  perform set_config(
    'start23.trusted_calculated_zone',
    coalesce(v_original_trusted, ''),
    true
  );
  perform set_config(
    'start23.critical_write',
    coalesce(v_original_critical_write, ''),
    true
  );

  return jsonb_build_object(
    'profile_id', v_profile.id,
    'version', v_profile.version,
    'status', v_profile.status,
    'proposal_id', v_proposal.id,
    'evaluation_id', v_evaluation_id,
    'state', case when v_evaluation_id is null then null else 'accepted' end,
    'zone_profile_id', v_profile.id,
    'zone_proposal_id', v_proposal.id,
    'base_zone_profile_id', v_active_id,
    'decided_at', v_decision.decided_at
  );
end;
$$;

revoke all on function public.save_calculated_zone_profile(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.save_calculated_zone_profile(uuid, jsonb)
to service_role;

create function public.reject_calibration_threshold(
  p_athlete_id uuid,
  p_evaluation_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_evaluation public.calibration_evaluations;
  v_decision public.calibration_threshold_decisions;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  select * into v_decision
  from public.calibration_threshold_decisions
  where evaluation_id = p_evaluation_id and athlete_id = p_athlete_id;
  if found then
    return to_jsonb(v_decision) - 'athlete_id';
  end if;
  select * into v_evaluation
  from public.calibration_evaluations
  where id = p_evaluation_id
    and athlete_id = p_athlete_id
    and status = 'threshold_estimated'
    and requires_athlete_confirmation;
  if not found then
    raise exception 'pending calibration evaluation not found'
      using errcode = 'P0002';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  insert into public.calibration_threshold_decisions (
    evaluation_id,
    athlete_id,
    state
  ) values (
    p_evaluation_id,
    p_athlete_id,
    'rejected'
  ) returning * into v_decision;

  return to_jsonb(v_decision) - 'athlete_id';
end;
$$;

revoke all on function public.reject_calibration_threshold(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.reject_calibration_threshold(uuid, uuid)
to service_role;

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

create or replace function public.reject_zone_proposal(p_proposal_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_target_id uuid;
  v_base_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select target_zone_profile_id, base_zone_profile_id
  into v_target_id, v_base_id
  from public.change_proposals
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and kind = 'zone_update'
    and state = 'pending'
  for update;
  if v_target_id is null then
    raise exception 'pending zone proposal not found' using errcode = 'P0002';
  end if;
  perform set_config('start23.critical_write', 'on', true);
  update public.zone_profile_versions
  set
    status = 'rejected',
    review_status = case
      when setup_method = 'calculated' then 'rejected_by_athlete'
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
  set
    state = 'rejected',
    decided_at = statement_timestamp(),
    decision_actor = v_athlete_id
  where id = p_proposal_id and athlete_id = v_athlete_id and state = 'pending';
  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'rejected',
    'active_zone_profile_id', v_base_id,
    'superseded_zone_profile_id', null
  );
end;
$$;

revoke all on function public.approve_zone_proposal(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.approve_zone_proposal(uuid, uuid)
to authenticated;
revoke all on function public.reject_zone_proposal(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.reject_zone_proposal(uuid)
to authenticated;

alter function private.build_planning_input_snapshot(uuid)
rename to build_legacy_planning_input_snapshot;

revoke execute on function private.build_legacy_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

create function private.build_planning_input_snapshot(p_athlete_id uuid)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select private.build_legacy_planning_input_snapshot(p_athlete_id)
    || jsonb_build_object(
      'zones',
      (
        select coalesce(
          jsonb_agg(
            jsonb_build_object(
              'id', profile.id,
              'discipline', profile.discipline,
              'version', profile.version,
              'setup_method', profile.setup_method,
              'validated', profile.validated,
              'fallback_active', profile.fallback_active,
              'needs_testing', profile.needs_testing,
              'requires_review', profile.requires_review,
              'review_reason', profile.review_reason,
              'ruleset_version', profile.ruleset_version,
              'zone_model_version', profile.zone_model_version,
              'source_method', profile.source_method,
              'source_quality', profile.source_quality,
              'calculated_at', profile.calculated_at,
              'review_status', profile.review_status,
              'reviewer_id', profile.reviewer_id,
              'reviewed_at', profile.reviewed_at,
              'evidence_version', profile.evidence_version,
              'metric_profiles', profile.metric_profiles,
              'metric',
              case
                when profile.setup_method = 'calculated' then (
                  select jsonb_build_object(
                    'kind', metric ->> 'metric_kind',
                    'value', metric ->> 'source_value'
                  )
                  from jsonb_array_elements(profile.metric_profiles) metric
                  where (metric ->> 'is_primary')::boolean
                  limit 1
                )
                else (
                  select jsonb_build_object(
                    'kind', metric.metric_kind,
                    'value', metric.value
                  )
                  from public.zone_metrics metric
                  where metric.zone_profile_id = profile.id
                    and metric.athlete_id = p_athlete_id
                )
              end,
              'boundaries',
              case
                when profile.setup_method = 'calculated' then (
                  select metric -> 'boundaries'
                  from jsonb_array_elements(profile.metric_profiles) metric
                  where (metric ->> 'is_primary')::boolean
                  limit 1
                )
                else (
                  select coalesce(
                    jsonb_agg(
                      jsonb_build_object(
                        'zone_number', boundary.zone_number,
                        'lower_value', boundary.lower_value,
                        'upper_value', boundary.upper_value
                      ) order by boundary.zone_number
                    ),
                    '[]'::jsonb
                  )
                  from public.zone_boundaries boundary
                  where boundary.zone_profile_id = profile.id
                    and boundary.athlete_id = p_athlete_id
                )
              end
            ) order by profile.discipline
          ),
          '[]'::jsonb
        )
        from public.zone_profile_versions profile
        where profile.athlete_id = p_athlete_id
          and profile.status = 'active'
      )
    );
$$;

revoke execute on function private.build_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

create or replace function private.build_phase_8_5_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select private.build_planning_input_snapshot(p_athlete_id)
    || jsonb_build_object(
      'discipline_setups',
      (
        select coalesce(
          jsonb_agg(
            to_jsonb(setup) - array['athlete_id', 'created_at', 'updated_at']
            order by setup.discipline
          ),
          '[]'::jsonb
        )
        from public.discipline_zone_setups setup
        where setup.athlete_id = p_athlete_id
      )
    );
$$;

revoke execute
on function private.build_phase_8_5_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;
