-- Phase 13 Joren ruleset. Forward-only: no historical load is recalculated.
-- Pure Python owns physiology. SQL preserves authorization, atomicity and provenance.
alter table public.training_history_entries
  add column previous_month_weekly_minutes numeric,
  add column baseline_model_version text,
  add constraint training_history_phase_13_valid check (
    (previous_month_weekly_minutes is null and baseline_model_version is null)
    or (previous_month_weekly_minutes is not null
        and previous_month_weekly_minutes between 0 and 10080
        and previous_month_weekly_minutes::text not in ('NaN','Infinity','-Infinity')
        and baseline_model_version is not null
        and baseline_model_version = 'phase-13-joren-ruleset-1')
  );


create or replace function public.replace_training_history(p_entries jsonb)
returns setof public.training_history_entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_entries) <> 'array'
     or jsonb_array_length(p_entries) <> 3 then
    raise exception 'swim, bike, and run history are required'
      using errcode = '23514';
  end if;
  if exists (
    select 1 from jsonb_array_elements(p_entries) entry
    where (entry - 'discipline' - 'average_hours_per_week') <> '{}'::jsonb
  ) or (select count(distinct entry.discipline)
        from jsonb_to_recordset(p_entries) entry(discipline text, average_hours_per_week numeric)
        where entry.discipline in ('swim','bike','run')
          and entry.average_hours_per_week between 0 and 168
          and entry.average_hours_per_week::text not in ('NaN','Infinity','-Infinity')) <> 3
     or (select sum((entry ->> 'average_hours_per_week')::numeric)
         from jsonb_array_elements(p_entries) entry) > 168 then
    raise exception 'complete previous-month duration history is required' using errcode = '23514';
  end if;
  perform pg_advisory_xact_lock(hashtextextended(v_athlete_id::text, 13));
  insert into public.training_history_entries (
    athlete_id, discipline, previous_month_weekly_minutes, baseline_model_version
  ) select v_athlete_id, entry.discipline, entry.average_hours_per_week * 60,
           'phase-13-joren-ruleset-1'
    from jsonb_to_recordset(p_entries) entry(discipline text, average_hours_per_week numeric)
  on conflict (athlete_id, discipline) do update set
    previous_month_weekly_minutes = excluded.previous_month_weekly_minutes,
    baseline_model_version = excluded.baseline_model_version,
    confirmed_at = statement_timestamp();

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps
  )
  values (
    v_athlete_id,
    'in_progress',
    'goal',
    array['profile', 'history']::text[]
  )
  on conflict (athlete_id) do update
  set
    current_step = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.current_step
      else 'goal'
    end,
    completed_steps = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.completed_steps
      else (
        select array_agg(distinct step order by step)
        from unnest(
          public.onboarding_sessions.completed_steps
          || array['profile', 'history']::text[]
        ) as steps(step)
      )
    end;

  return query
  select *
  from public.training_history_entries
  where athlete_id = v_athlete_id
  order by discipline;
end;
$$;

create or replace function private.build_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'profile',
    (
      select jsonb_build_object(
        'athlete_id', profile.athlete_id,
        'date_of_birth', profile.date_of_birth,
        'resting_heart_rate_bpm', profile.resting_heart_rate_bpm,
        'timezone', profile.timezone,
        'revision', profile.revision
      )
      from public.athlete_profiles profile
      where profile.athlete_id = p_athlete_id
    ),
    'training_history',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'discipline', history.discipline,
            'previous_month_weekly_minutes', history.previous_month_weekly_minutes,
            'baseline_model_version', history.baseline_model_version,
            'average_weekly_distance', history.average_weekly_distance,
            'distance_unit', history.distance_unit,
            'average_sessions_per_week', history.average_sessions_per_week,
            'history_window_months', history.history_window_months,
            'source', history.source,
            'confirmed_at', history.confirmed_at
          )
          order by history.discipline
        ),
        '[]'::jsonb
      )
      from public.training_history_entries history
      where history.athlete_id = p_athlete_id
    ),
    'goal',
    (
      select jsonb_build_object(
        'id', goal.id,
        'priority', goal.priority,
        'goal_type', goal.goal_type,
        'title', goal.title,
        'specific_description', goal.specific_description,
        'measurable_outcome', goal.measurable_outcome,
        'target_date', goal.target_date,
        'race_discipline_profile', goal.race_discipline_profile,
        'revision', goal.revision
      )
      from public.goals goal
      where goal.athlete_id = p_athlete_id
        and goal.status = 'active'
    ),
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
            'metric',
            (
              select jsonb_build_object(
                'kind', metric.metric_kind,
                'value', metric.value
              )
              from public.zone_metrics metric
              where metric.zone_profile_id = profile.id
                and metric.athlete_id = p_athlete_id
            ),
            'boundaries',
            (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'zone_number', boundary.zone_number,
                    'lower_value', boundary.lower_value,
                    'upper_value', boundary.upper_value
                  )
                  order by boundary.zone_number
                ),
                '[]'::jsonb
              )
              from public.zone_boundaries boundary
              where boundary.zone_profile_id = profile.id
                and boundary.athlete_id = p_athlete_id
            )
          )
          order by profile.discipline
        ),
        '[]'::jsonb
      )
      from public.zone_profile_versions profile
      where profile.athlete_id = p_athlete_id
        and profile.status = 'active'
    ),
    'ruleset_version',
    'phase-13-joren-ruleset-1'
  );
$$;

create or replace function public.complete_onboarding()
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_request_id uuid;
  v_revision bigint;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select initial_plan_request_id into v_request_id
  from public.onboarding_sessions
  where athlete_id = v_athlete_id and status = 'completed';
  if v_request_id is not null then
    return v_request_id;
  end if;

  if not exists (
    select 1 from public.athlete_profiles
    where athlete_id = v_athlete_id
      and date_of_birth is not null
      and resting_heart_rate_bpm is not null
      and timezone is not null
  ) then
    raise exception 'profile is incomplete' using errcode = '23514';
  end if;
  if (
    select count(*) from public.training_history_entries
    where athlete_id = v_athlete_id
      and previous_month_weekly_minutes is not null
      and baseline_model_version = 'phase-13-joren-ruleset-1'
  ) <> 3 then
    raise exception 'previous-month training history is incomplete'
      using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.goals
    where athlete_id = v_athlete_id and status = 'active'
  ) then
    raise exception 'primary race goal is missing' using errcode = '23514';
  end if;
  if (
    select count(distinct configured.discipline)
    from (
      select profile.discipline
      from public.zone_profile_versions profile
      where profile.athlete_id = v_athlete_id and profile.status = 'active'
      union
      select setup.discipline
      from public.discipline_zone_setups setup
      where setup.athlete_id = v_athlete_id
        and setup.setup_status in ('configured', 'test_pending', 'calibration_pending')
    ) configured
  ) <> 3 then
    raise exception 'discipline guidance setup is incomplete' using errcode = '23514';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.athlete_profiles
  set onboarding_status = 'completed'
  where athlete_id = v_athlete_id
  returning revision into v_revision;

  select id into v_request_id
  from public.initial_plan_requests
  where athlete_id = v_athlete_id and status = 'pending';
  if v_request_id is null then
    insert into public.initial_plan_requests (
      athlete_id, onboarding_revision, ruleset_version
    ) values (v_athlete_id, v_revision, 'phase-13-joren-ruleset-1')
    returning id into v_request_id;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps,
    initial_plan_request_id,
    completed_at
  ) values (
    v_athlete_id,
    'completed',
    'completed',
    array['profile', 'history', 'goal', 'zones', 'review']::text[],
    v_request_id,
    statement_timestamp()
  )
  on conflict (athlete_id) do update
  set
    status = 'completed',
    current_step = 'completed',
    completed_steps = array['profile', 'history', 'goal', 'zones', 'review']::text[],
    initial_plan_request_id = v_request_id,
    completed_at = statement_timestamp();

  return v_request_id;
end;
$$;

alter table public.zone_profile_versions drop constraint zone_profile_calculated_metadata_valid;
alter table public.zone_profile_versions add constraint zone_profile_calculated_metadata_valid check ((
    setup_method <> 'calculated'
    or (
      zone_model_version = 'start23-zone-model-1.0'
      and source_quality in (
        'athlete_entered', 'measured_lab', 'reviewed_field_threshold'
      )
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
  ) or (setup_method = 'calculated' and zone_model_version = 'phase-13-joren-ruleset-1'
    and ruleset_version = 'phase-13-joren-ruleset-1'
    and source_quality = 'reviewed_field_threshold' and calibration_evaluation_id is not null
    and calculated_at is not null and calculation_fingerprint is not null
    and evidence_version = 'phase-13-joren-ruleset-1'
    and review_reason = 'athlete_confirmation_required'
    and review_status in ('pending_athlete_confirmation','confirmed_by_athlete','rejected_by_athlete')
    and jsonb_array_length(metric_profiles) = 1));

alter table public.calibration_evaluations drop constraint calibration_evaluations_ruleset_valid;
alter table public.calibration_evaluations add constraint calibration_evaluations_ruleset_valid check ((
      ruleset_version in (
        'start23-calibration-ruleset-v1',
        'start23-calibration-ruleset-v2'
      )
    ) or (ruleset_version = 'phase-13-joren-ruleset-1'));

alter table public.calibration_evaluations drop constraint calibration_evaluations_pending_consistent;
alter table public.calibration_evaluations add constraint calibration_evaluations_pending_consistent check ((
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
    ) or (ruleset_version = 'phase-13-joren-ruleset-1'
    and status = 'threshold_estimated' and threshold_status = 'threshold_estimated'
    and zone_status = 'pending_athlete_confirmation' and confidence = 'medium'
    and requires_athlete_confirmation and review_status = 'pending_athlete_confirmation'
    and jsonb_array_length(thresholds) = 1 and jsonb_array_length(zone_profiles) = 1
    and zone_model_version = 'phase-13-joren-ruleset-1'
    and 'zone_profile_pending_athlete_confirmation' = any(reason_codes)));

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
       or not ((new.ruleset_version = 'start23-zone-model-1.0'
         and new.zone_model_version = 'start23-zone-model-1.0'
         and new.evidence_version = 'voorstel-start23-zone-1-5-rekenmodel-v1.0')
         or (new.ruleset_version = 'phase-13-joren-ruleset-1'
         and new.zone_model_version = 'phase-13-joren-ruleset-1'
         and new.evidence_version = 'phase-13-joren-ruleset-1'))
       or new.review_status <> 'pending_athlete_confirmation' then
      raise exception 'calculated zone provenance is server-controlled'
        using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

create or replace function public.save_calculated_zone_profile(
  p_athlete_id uuid,
  p_profile jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_model text := coalesce(p_profile -> 'metric_profiles' -> 0 ->> 'zone_model_version', '');
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

  if v_model = 'phase-13-joren-ruleset-1' and v_source_quality <> 'reviewed_field_threshold' then
    raise exception 'Phase 13 calibration requires attributable evaluation' using errcode = '23514';
  end if;
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
      and zone_model_version = v_model;
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
       or v_metric ->> 'zone_model_version' <> v_model
       or v_model not in ('start23-zone-model-1.0','phase-13-joren-ruleset-1')
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
    v_model,
    v_model,
    v_source_method,
    v_source_quality,
    statement_timestamp(),
    'pending_athlete_confirmation',
    case when v_model = 'phase-13-joren-ruleset-1' then v_model
         else 'voorstel-start23-zone-1-5-rekenmodel-v1.0' end,
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
    v_model
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

alter table public.activity_metrics add column zone_minutes numeric[];
alter table public.activity_metrics drop constraint activity_metrics_not_empty;
alter table public.activity_metrics add constraint activity_metrics_not_empty check (
  num_nonnulls(average_heart_rate_bpm,max_heart_rate_bpm,normalized_power_watts,
    average_speed_kmh,max_speed_kmh,average_pace_seconds_per_km,
    low_intensity_minutes,high_intensity_minutes,zone_minutes) > 0
);
alter table public.activities alter column duration_minutes drop not null;
alter table public.activities add constraint activities_phase_13_duration_required check (
  duration_minutes is not null or (discipline = 'swim' and distance_meters is not null and distance_meters > 0)
);
create function private.validate_phase_13_zone_minutes()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare v_duration numeric;
begin
  if new.zone_minutes is not null then
    select duration_minutes into v_duration from public.activities
    where id = new.activity_id and athlete_id = new.athlete_id;
    if cardinality(new.zone_minutes) <> 5 or v_duration is null
       or exists(select 1 from unnest(new.zone_minutes) m where m is null or m < 0 or m::text in ('NaN','Infinity','-Infinity'))
       or (select sum(m) from unnest(new.zone_minutes) m) > v_duration then
      raise exception 'invalid observed zone durations' using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;
revoke all on function private.validate_phase_13_zone_minutes() from public, anon, authenticated, service_role;
create trigger activity_metrics_phase_13_zone_minutes before insert or update on public.activity_metrics
for each row execute function private.validate_phase_13_zone_minutes();


create or replace function public.create_activity_summary(
  p_idempotency_key uuid,
  p_request_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_existing public.activities;
  v_workout public.planned_workouts;
  v_activity_id uuid;
  v_metrics jsonb := p_payload -> 'metrics';
  v_discipline text := p_payload ->> 'discipline';
  v_duration numeric := (p_payload ->> 'duration_minutes')::numeric;
  v_timezone text := p_payload ->> 'timezone';
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_request_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid activity fingerprint' using errcode = '23514';
  end if;
  if not exists (
    select 1 from pg_catalog.pg_timezone_names where name = v_timezone
  ) then
    raise exception 'invalid activity timezone' using errcode = '23514';
  end if;

  select * into v_existing
  from public.activities
  where athlete_id = v_athlete_id and idempotency_key = p_idempotency_key;
  if found then
    if v_existing.request_fingerprint <> p_request_fingerprint then
      raise exception 'activity idempotency key reused' using errcode = '40001';
    end if;
    return private.activity_public_json(v_existing.id, v_athlete_id);
  end if;

  if p_payload ->> 'planned_workout_id' is not null then
    select workout.* into v_workout
    from public.planned_workouts workout
    join public.plan_revisions revision
      on revision.id = workout.revision_id
     and revision.athlete_id = workout.athlete_id
    join public.weekly_plans plan
      on plan.id = workout.plan_id
     and plan.athlete_id = workout.athlete_id
     and plan.active_revision = revision.revision_number
    where workout.id = (p_payload ->> 'planned_workout_id')::uuid
      and workout.athlete_id = v_athlete_id
      and revision.state = 'active';
    if not found then
      raise exception 'planned workout not found' using errcode = 'P0002';
    end if;
    if v_workout.discipline <> v_discipline then
      raise exception 'activity discipline does not match planned workout'
      using errcode = '23514';
    end if;
    if exists (
      select 1 from public.activities
      where planned_workout_id = v_workout.id
    ) then
      raise exception 'planned workout already matched' using errcode = '40001';
    end if;
  end if;

  if v_metrics is not null
     and v_metrics ->> 'low_intensity_minutes' is not null
     and (
       (v_metrics ->> 'low_intensity_minutes')::numeric
       + (v_metrics ->> 'high_intensity_minutes')::numeric
     ) > v_duration then
    raise exception 'activity intensity duration mismatch' using errcode = '23514';
  end if;
  if v_metrics is not null
     and v_discipline <> 'bike'
     and (
       v_metrics ->> 'average_speed_kmh' is not null
       or v_metrics ->> 'max_speed_kmh' is not null
     ) then
    raise exception 'activity speed telemetry requires bike discipline'
    using errcode = '23514';
  end if;

  insert into public.activities (
    athlete_id,
    planned_workout_id,
    idempotency_key,
    request_fingerprint,
    discipline,
    started_at,
    timezone,
    duration_minutes,
    distance_meters,
    elevation_gain_meters,
    match_status
  ) values (
    v_athlete_id,
    (p_payload ->> 'planned_workout_id')::uuid,
    p_idempotency_key,
    p_request_fingerprint,
    v_discipline,
    (p_payload ->> 'started_at')::timestamptz,
    v_timezone,
    v_duration,
    (p_payload ->> 'distance_meters')::integer,
    (p_payload ->> 'elevation_gain_meters')::integer,
    case when p_payload ->> 'planned_workout_id' is null
      then 'unmatched' else 'matched' end
  ) returning id into v_activity_id;

  if v_metrics is not null then
    insert into public.activity_metrics (
      activity_id,
      athlete_id,
      average_heart_rate_bpm,
      max_heart_rate_bpm,
      normalized_power_watts,
      average_speed_kmh,
      max_speed_kmh,
      average_pace_seconds_per_km,
      low_intensity_minutes,
      high_intensity_minutes,
      zone_minutes
    ) values (
      v_activity_id,
      v_athlete_id,
      (v_metrics ->> 'average_heart_rate_bpm')::smallint,
      (v_metrics ->> 'max_heart_rate_bpm')::smallint,
      (v_metrics ->> 'normalized_power_watts')::integer,
      (v_metrics ->> 'average_speed_kmh')::numeric,
      (v_metrics ->> 'max_speed_kmh')::numeric,
      (v_metrics ->> 'average_pace_seconds_per_km')::numeric,
      (v_metrics ->> 'low_intensity_minutes')::numeric,
      (v_metrics ->> 'high_intensity_minutes')::numeric,
      case when v_metrics -> 'zone_minutes' is null then null else
        array(select jsonb_array_elements_text(v_metrics -> 'zone_minutes')::numeric) end
    );
  end if;

  return private.activity_public_json(v_activity_id, v_athlete_id);
end;
$$;

create or replace function private.activity_public_json(p_activity_id uuid, p_athlete_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', activity.id,
    'planned_workout_id', activity.planned_workout_id,
    'discipline', activity.discipline,
    'source', activity.source,
    'started_at', activity.started_at,
    'timezone', activity.timezone,
    'duration_minutes', activity.duration_minutes,
    'distance_meters', activity.distance_meters,
    'elevation_gain_meters', activity.elevation_gain_meters,
    'rpe', activity.rpe,
    'rpe_submitted_at', activity.rpe_submitted_at,
    'match_status', activity.match_status,
    'processing_state', activity.processing_state,
    'qualitative_result', activity.qualitative_result,
    'public_message', activity.public_message,
    'correction_proposal_id', activity.correction_proposal_id,
    'metrics', (
      select jsonb_build_object(
        'average_heart_rate_bpm', metric.average_heart_rate_bpm,
        'max_heart_rate_bpm', metric.max_heart_rate_bpm,
        'normalized_power_watts', metric.normalized_power_watts,
        'average_speed_kmh', metric.average_speed_kmh,
        'max_speed_kmh', metric.max_speed_kmh,
        'average_pace_seconds_per_km', metric.average_pace_seconds_per_km,
        'zone_minutes', metric.zone_minutes,
        'low_intensity_minutes', metric.low_intensity_minutes,
        'high_intensity_minutes', metric.high_intensity_minutes
      )
      from public.activity_metrics metric
      where metric.activity_id = activity.id
        and metric.athlete_id = p_athlete_id
    ),
    'created_at', activity.created_at,
    'updated_at', activity.updated_at
  )
  from public.activities activity
  where activity.id = p_activity_id and activity.athlete_id = p_athlete_id;
$$;

alter table private.activity_loads
  alter column realized_tss drop not null,
  drop constraint activity_loads_method_valid,
  add column total_minutes numeric,
  add column valid_minutes numeric,
  add column coverage_ratio numeric,
  add column load_status text,
  add column assigned_zone smallint,
  add column average_heart_rate_bpm numeric,
  add column zone_profile_id uuid,
  add constraint activity_loads_zone_profile_owner foreign key (zone_profile_id, athlete_id)
    references public.zone_profile_versions(id, athlete_id);
alter table private.activity_loads add constraint activity_loads_phase_13_method check (
  (calculation_method = 'actual_rpe_times_duration_hours' and ruleset_version <> 'phase-13-joren-ruleset-1')
  or (calculation_method in ('observed_zone_minutes','average_hr_zone_duration') and ruleset_version = 'phase-13-joren-ruleset-1')
);

create or replace function public.get_activity_processing_context(
  p_athlete_id uuid,
  p_activity_id uuid
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
    raise exception 'service role required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'duration_minutes', activity.duration_minutes,
    'processing_state', activity.processing_state,
    'rpe', activity.rpe,
    'discipline', activity.discipline,
    'zone_minutes', metrics.zone_minutes,
    'known_hr_profile_id', hr_profile.id,
    'known_hr_profile', coalesce(hr_metric.value, (
      select jsonb_build_object(
        'metric_kind', metric.metric_kind, 'source_value', metric.value,
        'boundary_kind', 'manual', 'zone_model_version', 'start23-zone-model-1.0',
        'boundaries', (select jsonb_agg(jsonb_build_object(
          'zone_number', boundary.zone_number, 'lower_value', boundary.lower_value,
          'upper_value', boundary.upper_value) order by boundary.zone_number)
          from public.zone_boundaries boundary where boundary.zone_profile_id = hr_profile.id
            and boundary.athlete_id = activity.athlete_id)
      ) from public.zone_metrics metric where metric.zone_profile_id = hr_profile.id
        and metric.athlete_id = activity.athlete_id
        and metric.metric_kind in ('run_lthr_bpm','bike_threshold_heart_rate_bpm') limit 1
    )),
    'private_load_snapshot', (select to_jsonb(source) from private.activity_loads source
      where source.activity_id = activity.id and source.athlete_id = activity.athlete_id),
    'load_ruleset_version', (select ruleset_version from private.activity_loads where activity_id = activity.id and athlete_id = p_athlete_id),
    'average_heart_rate_bpm', metrics.average_heart_rate_bpm,
    'requires_heart_rate_observation', activity.discipline <> 'swim' and workout.id is not null and exists (
      select 1
      from jsonb_array_elements(workout.segments) segment
      where coalesce(
        (segment -> 'rpe_target' ->> 'heart_rate_observation_required')::boolean,
        false
      )
    ),
    'planned', case when workout.id is null then null else jsonb_build_object(
      'planned_tss', case when load.ruleset_version = 'phase-13-joren-ruleset-1'
        or exists (select 1 from private.activity_loads original
          where original.activity_id = activity.id and original.athlete_id = activity.athlete_id
            and original.ruleset_version <> 'phase-13-joren-ruleset-1')
        then load.planned_tss else null end,
      'expected_rpe_min', workout.expected_rpe_min,
      'expected_rpe_max', workout.expected_rpe_max,
      'intensity_bucket', workout.intensity_bucket
    ) end
  ) into v_result
  from public.activities activity
  left join lateral (
    select profile.id, profile.metric_profiles
    from public.zone_profile_versions profile
    where profile.athlete_id = activity.athlete_id
      and profile.discipline = activity.discipline
      and profile.id = coalesce(
        (select source.zone_profile_id from private.activity_loads source
         where source.activity_id = activity.id and source.athlete_id = activity.athlete_id),
        (select active.id from public.zone_profile_versions active
         where active.athlete_id = activity.athlete_id and active.discipline = activity.discipline
           and active.status = 'active')
      )
  ) hr_profile on true
  left join lateral (
    select value from jsonb_array_elements(hr_profile.metric_profiles)
    where value ->> 'metric_kind' in ('run_lthr_bpm','bike_threshold_heart_rate_bpm')
    limit 1
  ) hr_metric on true
  left join public.activity_metrics metrics
    on metrics.activity_id = activity.id
   and metrics.athlete_id = activity.athlete_id
  left join public.planned_workouts workout
    on workout.id = activity.planned_workout_id
   and workout.athlete_id = activity.athlete_id
  left join private.planned_workout_loads load
    on load.planned_workout_id = workout.id
   and load.athlete_id = activity.athlete_id
  where activity.id = p_activity_id and activity.athlete_id = p_athlete_id;
  if v_result is null then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

create table private.phase_13_activity_load_history (
  id bigint generated always as identity primary key,
  activity_id uuid not null,
  athlete_id uuid not null,
  recorded_at timestamptz not null default statement_timestamp(),
  snapshot jsonb not null
);
alter table private.phase_13_activity_load_history enable row level security;
revoke all on private.phase_13_activity_load_history from public, anon, authenticated;
grant all on private.phase_13_activity_load_history to service_role;
create function private.audit_phase_13_load_revision() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  insert into private.phase_13_activity_load_history(activity_id, athlete_id, snapshot)
  values (old.activity_id, old.athlete_id, to_jsonb(old));
  return new;
end;
$$;
revoke all on function private.audit_phase_13_load_revision() from public, anon, authenticated, service_role;
create trigger phase_13_activity_load_revision before update on private.activity_loads
for each row execute function private.audit_phase_13_load_revision();


create or replace function public.complete_activity_rpe(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_activity public.activities;
  v_rpe smallint := (p_payload ->> 'rpe')::smallint;
  v_result text := p_payload ->> 'qualitative_result';
  v_reason text := p_payload ->> 'correction_reason';
  v_realized numeric := (p_payload ->> 'realized_tss')::numeric;
  v_plan public.weekly_plans;
  v_old_revision public.plan_revisions;
  v_new_revision_id uuid;
  v_new_revision integer;
  v_old_workout public.planned_workouts;
  v_new_workout_id uuid;
  v_cancel boolean;
  v_total numeric;
  v_low numeric;
  v_high numeric;
  v_planned numeric;
  v_proposal_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity
  from public.activities
  where id = p_activity_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.processing_state = 'complete' then
    if v_activity.rpe <> v_rpe then
      raise exception 'activity rpe is immutable' using errcode = '40001';
    end if;
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  if v_rpe not between 1 and 10
     or v_result not in (
       'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
     )
     or v_reason is not null and v_reason not in (
       'volume_overshoot', 'hidden_fatigue', 'unplanned_load'
     )
     or (v_result = 'overshoot') <>
       coalesce(v_reason = 'volume_overshoot', false)
     or (v_result = 'hidden_fatigue') <>
       coalesce(v_reason = 'hidden_fatigue', false)
     or (v_result = 'unplanned') <>
       coalesce(v_reason = 'unplanned_load', false)
     or v_result in ('perfect_match', 'deviation') and v_reason is not null
     or (p_payload ->> 'ruleset_version' <> 'phase-13-joren-ruleset-1'
         and v_realized <> v_activity.duration_minutes * v_rpe / 60) then
    raise exception 'invalid activity rpe result' using errcode = '23514';
  end if;
  if p_payload ->> 'ruleset_version' = 'phase-13-joren-ruleset-1' then
    if (p_payload ->> 'total_minutes')::numeric is distinct from v_activity.duration_minutes then
      raise exception 'measurement duration mismatch' using errcode = '23514';
    end if;
    if p_payload ->> 'calculation_method' = 'observed_zone_minutes' and
       (p_payload ->> 'valid_minutes')::numeric is distinct from coalesce((
         select sum(minute) from public.activity_metrics metric,
           unnest(metric.zone_minutes) minute
         where metric.activity_id = p_activity_id and metric.athlete_id = p_athlete_id
       ), 0) then
      raise exception 'observed duration mismatch' using errcode = '23514';
    end if;
    if p_payload ->> 'calculation_method' = 'average_hr_zone_duration' and (
      exists (select 1 from public.activity_metrics metric, unnest(metric.zone_minutes) minute
        where metric.activity_id = p_activity_id and metric.athlete_id = p_athlete_id and minute > 0)
      or not exists (select 1 from public.zone_profile_versions profile
        where profile.id = (p_payload ->> 'zone_profile_id')::uuid
          and profile.athlete_id = p_athlete_id and profile.discipline = v_activity.discipline
          and (profile.status = 'active' or exists (select 1 from private.activity_loads original
            where original.activity_id = p_activity_id and original.athlete_id = p_athlete_id
              and original.zone_profile_id = profile.id)))
    ) then
      raise exception 'known zone measurement context mismatch' using errcode = '23514';
    end if;
  end if;


  insert into private.activity_loads (
    activity_id, athlete_id, realized_tss, calculation_method, ruleset_version,
    total_minutes, valid_minutes, coverage_ratio, load_status,
    assigned_zone, average_heart_rate_bpm, zone_profile_id
  ) values (
    p_activity_id,
    p_athlete_id,
    v_realized,
    p_payload ->> 'calculation_method',
    p_payload ->> 'ruleset_version',
    (p_payload ->> 'total_minutes')::numeric,
    (p_payload ->> 'valid_minutes')::numeric,
    (p_payload ->> 'coverage_ratio')::numeric,
    p_payload ->> 'load_status',
    (p_payload ->> 'assigned_zone')::smallint,
    (p_payload ->> 'average_heart_rate_bpm')::numeric,
    (p_payload ->> 'zone_profile_id')::uuid
  );

  perform set_config('start23.critical_write', 'on', true);
  if v_activity.planned_workout_id is not null then
    update public.planned_workouts
    set status = 'completed'
    where id = v_activity.planned_workout_id and athlete_id = p_athlete_id;
  end if;

  if v_reason is not null then
    if v_activity.planned_workout_id is not null then
      select plan.* into v_plan
      from public.planned_workouts workout
      join public.weekly_plans plan
        on plan.id = workout.plan_id and plan.athlete_id = workout.athlete_id
      join public.plan_revisions revision
        on revision.plan_id = plan.id
       and revision.athlete_id = plan.athlete_id
       and revision.revision_number = plan.active_revision
      where workout.id = v_activity.planned_workout_id
        and workout.athlete_id = p_athlete_id
        and revision.state = 'active';
    else
      select plan.* into v_plan
      from public.weekly_plans plan
      where plan.athlete_id = p_athlete_id
        and plan.state = 'active'
        and (v_activity.started_at at time zone plan.timezone)::date
          between plan.week_start and plan.week_start + 6
      limit 1;
    end if;
  end if;

  if v_plan.id is not null
     and not exists (
       select 1 from public.plan_revisions
       where plan_id = v_plan.id and state = 'pending_approval'
     ) then
    select * into v_old_revision
    from public.plan_revisions
    where plan_id = v_plan.id
      and athlete_id = p_athlete_id
      and revision_number = v_plan.active_revision
      and state = 'active'
    for update;

    if exists (
      select 1 from public.planned_workouts workout
      where workout.revision_id = v_old_revision.id
        and workout.status = 'scheduled'
        and workout.intensity_bucket = 'high'
        and workout.scheduled_at > v_activity.started_at
          + make_interval(mins => v_activity.duration_minutes::integer)
        and (
          v_reason <> 'hidden_fatigue'
          or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
        )
    ) then
      select
        coalesce(sum(
          case when workout.status = 'cancelled' then 0
          when workout.status = 'scheduled'
             and workout.intensity_bucket = 'high'
             and workout.scheduled_at > v_activity.started_at
               + make_interval(mins => v_activity.duration_minutes::integer)
             and (
               v_reason <> 'hidden_fatigue'
               or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
             )
          then 0 else workout.duration_minutes end
        ), 0),
        coalesce(sum(
          case when workout.status <> 'cancelled'
             and workout.intensity_bucket = 'low' then workout.duration_minutes
          else 0 end
        ), 0),
        coalesce(sum(
          case when workout.status <> 'cancelled'
             and workout.intensity_bucket = 'high'
             and not (
               workout.status = 'scheduled'
               and workout.scheduled_at > v_activity.started_at
                 + make_interval(mins => v_activity.duration_minutes::integer)
               and (
                 v_reason <> 'hidden_fatigue'
                 or workout.scheduled_at <= v_activity.started_at + interval '72 hours'
               )
             )
          then workout.duration_minutes else 0 end
        ), 0)
      into v_total, v_low, v_high
      from public.planned_workouts workout
      where workout.revision_id = v_old_revision.id;

      v_new_revision := (
        select coalesce(max(revision_number), 0) + 1
        from public.plan_revisions where plan_id = v_plan.id
      );
      insert into public.plan_revisions (
        plan_id,
        athlete_id,
        revision_number,
        state,
        source,
        phase,
        target_basis,
        taper_period,
        input_fingerprint,
        generation_fingerprint,
        initial_plan_request_id,
        total_duration_minutes,
        low_intensity_percent,
        high_intensity_percent,
        confirmed_injuries,
        availability,
        ruleset_version
      ) values (
        v_plan.id,
        p_athlete_id,
        v_new_revision,
        'pending_approval',
        'system_generated',
        v_old_revision.phase,
        'activity_correction',
        v_old_revision.taper_period,
        pg_catalog.md5(p_activity_id::text || ':' || v_reason),
        pg_catalog.encode(
          extensions.digest(
            p_activity_id::text || ':' || v_reason || ':' || v_new_revision::text,
            'sha256'
          ),
          'hex'
        ),
        v_old_revision.initial_plan_request_id,
        v_total,
        case when v_total = 0 then 100 else v_low * 100 / v_total end,
        case when v_total = 0 then 0 else v_high * 100 / v_total end,
        v_old_revision.confirmed_injuries,
        v_old_revision.availability,
        p_payload ->> 'ruleset_version'
      ) returning id into v_new_revision_id;

      for v_old_workout in
        select * from public.planned_workouts
        where revision_id = v_old_revision.id
        order by scheduled_at, id
      loop
        v_cancel := v_old_workout.status = 'scheduled'
          and v_old_workout.intensity_bucket = 'high'
          and v_old_workout.scheduled_at > v_activity.started_at
            + make_interval(mins => v_activity.duration_minutes::integer)
          and (
            v_reason <> 'hidden_fatigue'
            or v_old_workout.scheduled_at <= v_activity.started_at + interval '72 hours'
          );
        insert into public.planned_workouts (
          revision_id, plan_id, athlete_id, template_id, template_key,
          template_version, discipline, name, description, duration_minutes,
          distance_meters, intensity_bucket, expected_rpe_min, expected_rpe_max,
          segments, scheduled_at, timezone, source, status
        ) values (
          v_new_revision_id, v_plan.id, p_athlete_id, v_old_workout.template_id,
          v_old_workout.template_key, v_old_workout.template_version,
          v_old_workout.discipline, v_old_workout.name, v_old_workout.description,
          v_old_workout.duration_minutes, v_old_workout.distance_meters,
          v_old_workout.intensity_bucket, v_old_workout.expected_rpe_min,
          v_old_workout.expected_rpe_max, v_old_workout.segments,
          v_old_workout.scheduled_at, v_old_workout.timezone,
          case when v_cancel then 'system_adjusted' else v_old_workout.source end,
          case when v_cancel then 'cancelled' else v_old_workout.status end
        ) returning id into v_new_workout_id;
        insert into private.planned_workout_loads (
          planned_workout_id, athlete_id, planned_tss,
          calculation_method, ruleset_version
        ) select
          v_new_workout_id, p_athlete_id, load.planned_tss,
          load.calculation_method, load.ruleset_version
        from private.planned_workout_loads load
        where load.planned_workout_id = v_old_workout.id;
      end loop;

      select coalesce(sum(load.planned_tss), 0) into v_planned
      from private.planned_workout_loads load
      join public.planned_workouts workout on workout.id = load.planned_workout_id
      where workout.revision_id = v_new_revision_id and workout.status <> 'cancelled';

      insert into private.plan_revision_loads (
        revision_id, athlete_id, target_tss, planned_tss, ruleset_version
      ) select
        v_new_revision_id, p_athlete_id, old_load.target_tss,
        v_planned, p_payload ->> 'ruleset_version'
      from private.plan_revision_loads old_load
      where old_load.revision_id = v_old_revision.id;

      insert into public.plan_warnings (
        revision_id, athlete_id, rule_id, code, severity, message
      ) values (
        v_new_revision_id,
        p_athlete_id,
        'BR-002',
        v_reason,
        'warning',
        p_payload ->> 'public_message'
      );

      insert into public.change_proposals (
        athlete_id, kind, state, target_plan_revision_id,
        base_plan_revision, reason_codes, public_explanation, ruleset_version
      ) values (
        p_athlete_id,
        'plan_revision',
        'pending',
        v_new_revision_id,
        v_plan.active_revision,
        array[v_reason],
        p_payload ->> 'public_message',
        p_payload ->> 'ruleset_version'
      ) returning id into v_proposal_id;
    end if;
  end if;

  update public.activities
  set
    rpe = v_rpe,
    rpe_submitted_at = statement_timestamp(),
    processing_state = 'complete',
    qualitative_result = v_result,
    public_message = p_payload ->> 'public_message',
    correction_proposal_id = v_proposal_id,
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = p_athlete_id;

  return private.activity_public_json(p_activity_id, p_athlete_id);
end;
$$;

create or replace function public.revise_activity_rpe(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_activity public.activities;
  v_new_rpe smallint := (p_payload ->> 'rpe')::smallint;
  v_result text := p_payload ->> 'qualitative_result';
  v_reason text := p_payload ->> 'correction_reason';
  v_realized numeric := (p_payload ->> 'realized_tss')::numeric;
  v_activity_week date;
  v_current_week date;
  v_pending_revision_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity
  from public.activities
  where id = p_activity_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.rpe is null or v_activity.processing_state <> 'complete' then
    raise exception 'activity rpe is missing' using errcode = '40001';
  end if;
  if v_activity.rpe = v_new_rpe then
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  v_activity_week :=
    (v_activity.started_at at time zone v_activity.timezone)::date
    - extract(
        isodow from (v_activity.started_at at time zone v_activity.timezone)::date
      )::integer + 1;
  v_current_week :=
    (statement_timestamp() at time zone v_activity.timezone)::date
    - extract(
        isodow from (statement_timestamp() at time zone v_activity.timezone)::date
      )::integer + 1;
  if v_activity_week <> v_current_week then
    raise exception 'rpe correction window closed' using errcode = '40001';
  end if;
  if v_new_rpe not between 1 and 10
     or v_result not in (
       'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
     )
     or v_reason is not null and v_reason not in (
       'volume_overshoot', 'hidden_fatigue', 'unplanned_load'
     )
     or (p_payload ->> 'ruleset_version' <> 'phase-13-joren-ruleset-1'
         and v_realized <> v_activity.duration_minutes * v_new_rpe / 60) then
    raise exception 'invalid activity rpe result' using errcode = '23514';
  end if;
  if p_payload ->> 'ruleset_version' = 'phase-13-joren-ruleset-1' then
    if (p_payload ->> 'total_minutes')::numeric is distinct from v_activity.duration_minutes then
      raise exception 'measurement duration mismatch' using errcode = '23514';
    end if;
    if p_payload ->> 'calculation_method' = 'observed_zone_minutes' and
       (p_payload ->> 'valid_minutes')::numeric is distinct from coalesce((
         select sum(minute) from public.activity_metrics metric,
           unnest(metric.zone_minutes) minute
         where metric.activity_id = p_activity_id and metric.athlete_id = p_athlete_id
       ), 0) then
      raise exception 'observed duration mismatch' using errcode = '23514';
    end if;
    if p_payload ->> 'calculation_method' = 'average_hr_zone_duration' and (
      exists (select 1 from public.activity_metrics metric, unnest(metric.zone_minutes) minute
        where metric.activity_id = p_activity_id and metric.athlete_id = p_athlete_id and minute > 0)
      or not exists (select 1 from public.zone_profile_versions profile
        where profile.id = (p_payload ->> 'zone_profile_id')::uuid
          and profile.athlete_id = p_athlete_id and profile.discipline = v_activity.discipline
          and (profile.status = 'active' or exists (select 1 from private.activity_loads original
            where original.activity_id = p_activity_id and original.athlete_id = p_athlete_id
              and original.zone_profile_id = profile.id)))
    ) then
      raise exception 'known zone measurement context mismatch' using errcode = '23514';
    end if;
  end if;


  insert into public.activity_rpe_revisions (
    activity_id, athlete_id, previous_rpe, corrected_rpe,
    previous_qualitative_result, corrected_qualitative_result, ruleset_version
  ) values (
    p_activity_id,
    p_athlete_id,
    v_activity.rpe,
    v_new_rpe,
    v_activity.qualitative_result,
    v_result,
    p_payload ->> 'ruleset_version'
  );
  update private.activity_loads
  set
    realized_tss = v_realized,
    calculation_method = p_payload ->> 'calculation_method',
    ruleset_version = p_payload ->> 'ruleset_version',
    total_minutes = (p_payload ->> 'total_minutes')::numeric,
    valid_minutes = (p_payload ->> 'valid_minutes')::numeric,
    coverage_ratio = (p_payload ->> 'coverage_ratio')::numeric,
    load_status = p_payload ->> 'load_status',
    assigned_zone = (p_payload ->> 'assigned_zone')::smallint,
    average_heart_rate_bpm = (p_payload ->> 'average_heart_rate_bpm')::numeric,
    zone_profile_id = (p_payload ->> 'zone_profile_id')::uuid
  where activity_id = p_activity_id and athlete_id = p_athlete_id;

  if v_activity.correction_proposal_id is not null then
    select target_plan_revision_id into v_pending_revision_id
    from public.change_proposals
    where id = v_activity.correction_proposal_id
      and athlete_id = p_athlete_id
      and state = 'pending';
    if v_pending_revision_id is not null then
      perform set_config('start23.critical_write', 'on', true);
      update public.change_proposals
      set state = 'expired', decided_at = statement_timestamp()
      where id = v_activity.correction_proposal_id
        and athlete_id = p_athlete_id
        and state = 'pending';
      update public.plan_revisions
      set state = 'expired'
      where id = v_pending_revision_id
        and athlete_id = p_athlete_id
        and state = 'pending_approval';
    end if;
  end if;

  update public.activities
  set
    rpe = v_new_rpe,
    rpe_submitted_at = statement_timestamp(),
    qualitative_result = v_result,
    public_message = p_payload ->> 'public_message',
    correction_proposal_id = null,
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = p_athlete_id;
  return private.activity_public_json(p_activity_id, p_athlete_id);
end;
$$;

create or replace function public.get_plan_load_history_for_planning_v13(
  p_athlete_id uuid,
  p_before_week date
)
returns table (
  week_start date,
  phase text,
  target_basis text,
  planned_tss numeric,
  realized_tss numeric,
  planned_high_minutes numeric,
  planned_total_minutes numeric,
  realized_high_minutes numeric,
  realized_classified_minutes numeric,
  realized_total_minutes numeric,
  completed_activity_count bigint,
  sick_week boolean,
  reduced_realized_progression boolean
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  return query
  with earliest_evidence as (
    select min(evidence.local_week) as local_week
    from (
      select plan.week_start as local_week
      from public.weekly_plans plan
      where plan.athlete_id = p_athlete_id
      union all
      select
        (activity.started_at at time zone activity.timezone)::date
        - extract(
            isodow
            from (activity.started_at at time zone activity.timezone)::date
          )::integer + 1
      from public.activities activity
      where activity.athlete_id = p_athlete_id
    ) evidence
  ), complete_weeks as (
    select (p_before_week - (series.value * 7))::date as local_week
    from generate_series(1, 6) as series(value)
    cross join earliest_evidence earliest
    where earliest.local_week is not null
      and p_before_week - (series.value * 7) >= earliest.local_week
  )
  select
    week.local_week,
    coalesce(revision.phase, 'base'),
    coalesce(revision.target_basis, 'realized_baseline'),
    coalesce(revision_load.planned_tss, 0),
    case
      when activity_summary.activity_count = 0 then 0::numeric
      else activity_summary.realized_tss
    end,
    coalesce(
      revision.total_duration_minutes * revision.high_intensity_percent / 100,
      0
    ),
    coalesce(revision.total_duration_minutes, 0),
    activity_summary.realized_high_minutes,
    activity_summary.realized_classified_minutes,
    activity_summary.realized_total_minutes,
    activity_summary.activity_count,
    coalesce(feedback.payload -> 'missed_workout_reasons' ? 'illness', false),
    coalesce(feedback.payload ->> 'fatigue_level' <> 'none', false)
      or coalesce(jsonb_array_length(feedback.payload -> 'missed_workout_reasons') > 0, false)
  from complete_weeks week
  left join public.weekly_plans plan
    on plan.athlete_id = p_athlete_id
   and plan.week_start = week.local_week
  left join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  left join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = plan.athlete_id
   and revision_load.ruleset_version = 'phase-13-joren-ruleset-1'
  left join lateral (
    select context.payload from public.weekly_checkin_contexts context
    join public.weekly_checkins checkin on checkin.id = context.checkin_id
      and checkin.athlete_id = context.athlete_id
    where checkin.athlete_id = p_athlete_id and checkin.week_start = week.local_week + 7
      and context.state = 'confirmed'
  ) feedback on true
  left join lateral (
    select
      count(activity.id) as activity_count,
      sum(activity_load.realized_tss) as realized_tss,
      sum(metric.high_intensity_minutes) as realized_high_minutes,
      sum(metric.low_intensity_minutes + metric.high_intensity_minutes)
        as realized_classified_minutes,
      sum(activity.duration_minutes) filter (
        where activity_load.activity_id is not null
      ) as realized_total_minutes
    from public.activities activity
    left join private.activity_loads activity_load
      on activity_load.activity_id = activity.id
     and activity_load.athlete_id = activity.athlete_id
     and activity_load.ruleset_version = 'phase-13-joren-ruleset-1'
    left join public.activity_metrics metric
      on metric.activity_id = activity.id
     and metric.athlete_id = activity.athlete_id
     and activity_load.activity_id is not null
    where activity.athlete_id = p_athlete_id
      and (activity.started_at at time zone activity.timezone)::date
        between week.local_week and week.local_week + 6
  ) activity_summary on true
  where revision.id is null or revision_load.ruleset_version = 'phase-13-joren-ruleset-1'
  order by week.local_week;
end;
$$;

revoke all on function public.get_plan_load_history_for_planning_v13(uuid, date) from public, anon, authenticated, service_role;
grant execute on function public.get_plan_load_history_for_planning_v13(uuid, date) to service_role;

create or replace function public.create_weekly_plan_proposal(
  p_athlete_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_plan_id uuid;
  v_revision_id uuid;
  v_revision integer;
  v_proposal_id uuid;
  v_request_id uuid;
  v_workout jsonb;
  v_warning jsonb;
  v_workout_id uuid;
  v_planned_tss numeric := 0;
  v_existing record;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_athlete_id is null
     or not exists (select 1 from auth.users where id = p_athlete_id) then
    raise exception 'athlete not found' using errcode = 'P0002';
  end if;
  if jsonb_typeof(p_payload) <> 'object'
     or not p_payload ?& array[
       'input_fingerprint',
       'generation_fingerprint',
       'expected_base_revision',
       'week_start',
       'timezone',
       'phase',
       'target_basis',
       'total_duration_minutes',
       'low_intensity_percent',
       'high_intensity_percent',
       'confirmed_injuries',
       'availability',
       'workouts',
       'warnings',
       'target_tss',
       'planned_tss',
       'ruleset_version'
     ] then
    raise exception 'planning payload is incomplete' using errcode = '23514';
  end if;
  if jsonb_typeof(p_payload -> 'workouts') <> 'array'
     or jsonb_array_length(p_payload -> 'workouts') = 0 then
    raise exception 'planning payload requires workouts' using errcode = '23514';
  end if;

  v_request_id := nullif(p_payload ->> 'initial_plan_request_id', '')::uuid;
  v_plan_id := nullif(p_payload ->> 'plan_id', '')::uuid;

  if v_request_id is not null and not exists (
    select 1
    from public.initial_plan_requests request
    where request.id = v_request_id
      and request.athlete_id = p_athlete_id
      and request.input_fingerprint = p_payload ->> 'input_fingerprint'
      and request.status in ('pending', 'consumed')
  ) then
    raise exception 'planning input is stale' using errcode = '40001';
  end if;

  if v_plan_id is not null then
    select plan.id, plan.active_revision
    into v_existing
    from public.weekly_plans plan
    where plan.id = v_plan_id and plan.athlete_id = p_athlete_id
    for update;
    if not found then
      raise exception 'weekly plan not found' using errcode = 'P0002';
    end if;
    if coalesce(v_existing.active_revision, 0)
       <> (p_payload ->> 'expected_base_revision')::integer then
      raise exception 'plan revision is stale' using errcode = '40001';
    end if;
  else
    select plan.id, plan.active_revision
    into v_existing
    from public.weekly_plans plan
    where plan.athlete_id = p_athlete_id
      and plan.week_start = (p_payload ->> 'week_start')::date
    for update;
    if found then
      v_plan_id := v_existing.id;
      if coalesce(v_existing.active_revision, 0)
         <> (p_payload ->> 'expected_base_revision')::integer then
        raise exception 'plan revision is stale' using errcode = '40001';
      end if;
    end if;
  end if;

  if v_plan_id is not null then
    select
      proposal.id,
      revision.revision_number
    into v_proposal_id, v_revision
    from public.plan_revisions revision
    join public.change_proposals proposal
      on proposal.target_plan_revision_id = revision.id
     and proposal.athlete_id = revision.athlete_id
    where revision.plan_id = v_plan_id
      and revision.athlete_id = p_athlete_id
      and revision.generation_fingerprint =
        p_payload ->> 'generation_fingerprint'
      and proposal.state in ('pending', 'applied')
    order by revision.revision_number desc
    limit 1;
    if v_proposal_id is not null then
      return jsonb_build_object(
        'plan_id', v_plan_id,
        'revision', v_revision,
        'proposal_id', v_proposal_id
      );
    end if;
  end if;

  perform set_config('start23.critical_write', 'on', true);

  if v_plan_id is null then
    insert into public.weekly_plans (
      athlete_id,
      week_start,
      timezone,
      state
    )
    values (
      p_athlete_id,
      (p_payload ->> 'week_start')::date,
      p_payload ->> 'timezone',
      'pending_approval'
    )
    returning id into v_plan_id;
  end if;

  update public.change_proposals proposal
  set state = 'expired', decided_at = statement_timestamp()
  from public.plan_revisions revision
  where proposal.target_plan_revision_id = revision.id
    and revision.plan_id = v_plan_id
    and proposal.athlete_id = p_athlete_id
    and proposal.state = 'pending';

  update public.plan_revisions
  set state = 'expired'
  where plan_id = v_plan_id
    and athlete_id = p_athlete_id
    and state = 'pending_approval';

  select coalesce(max(revision_number), 0) + 1
  into v_revision
  from public.plan_revisions
  where plan_id = v_plan_id and athlete_id = p_athlete_id;

  insert into public.plan_revisions (
    plan_id,
    athlete_id,
    revision_number,
    state,
    source,
    phase,
    target_basis,
    taper_period,
    input_fingerprint,
    generation_fingerprint,
    initial_plan_request_id,
    total_duration_minutes,
    low_intensity_percent,
    high_intensity_percent,
    confirmed_injuries,
    availability,
    ruleset_version
  )
  values (
    v_plan_id,
    p_athlete_id,
    v_revision,
    'pending_approval',
    'system_generated',
    p_payload ->> 'phase',
    p_payload ->> 'target_basis',
    nullif(p_payload ->> 'taper_period', ''),
    p_payload ->> 'input_fingerprint',
    p_payload ->> 'generation_fingerprint',
    v_request_id,
    (p_payload ->> 'total_duration_minutes')::numeric,
    (p_payload ->> 'low_intensity_percent')::numeric,
    (p_payload ->> 'high_intensity_percent')::numeric,
    array(
      select jsonb_array_elements_text(p_payload -> 'confirmed_injuries')
    ),
    p_payload -> 'availability',
    p_payload ->> 'ruleset_version'
  )
  returning id into v_revision_id;

  for v_workout in
    select value from jsonb_array_elements(p_payload -> 'workouts')
  loop
    if not exists (
      select 1
      from public.workout_templates template
      where template.id = (v_workout ->> 'template_id')::uuid
        and template.discipline = v_workout ->> 'discipline'
    ) then
      raise exception 'workout template is invalid' using errcode = '23514';
    end if;
    if (v_workout ->> 'discipline') = any(
      array(
        select jsonb_array_elements_text(
          p_payload -> 'confirmed_injuries'
        )
      )
    ) then
      raise exception 'injured discipline cannot be planned'
        using errcode = '23514';
    end if;

    insert into public.planned_workouts (
      revision_id,
      plan_id,
      athlete_id,
      template_id,
      template_key,
      template_version,
      discipline,
      name,
      description,
      duration_minutes,
      distance_meters,
      intensity_bucket,
      expected_rpe_min,
      expected_rpe_max,
      segments,
      scheduled_at,
      timezone,
      source
    )
    select
      v_revision_id,
      v_plan_id,
      p_athlete_id,
      template.id,
      template.template_key,
      template.version,
      template.discipline,
      template.name,
      template.description,
      template.duration_minutes,
      template.distance_meters,
      template.intensity_bucket,
      template.expected_rpe_min,
      template.expected_rpe_max,
      (
        select jsonb_agg(
          jsonb_build_object(
            'sequence', segment.sequence,
            'name', segment.name,
            'instructions', segment.instructions,
            'duration_minutes', segment.duration_minutes,
            'distance_meters', segment.distance_meters,
            'zone', segment.zone_number,
            'expected_rpe', segment.expected_rpe,
            'is_swim_technique', segment.is_swim_technique
          )
          order by segment.sequence
        )
        from public.workout_segments segment
        where segment.template_id = template.id
      ),
      (v_workout ->> 'scheduled_at')::timestamptz,
      p_payload ->> 'timezone',
      v_workout ->> 'source'
    from public.workout_templates template
    where template.id = (v_workout ->> 'template_id')::uuid
    returning id into v_workout_id;

    insert into private.planned_workout_loads (
      planned_workout_id,
      athlete_id,
      planned_tss,
      calculation_method,
      ruleset_version
    )
    select
      v_workout_id,
      p_athlete_id,
      case when p_payload ->> 'ruleset_version' = 'phase-13-joren-ruleset-1'
        then (v_workout ->> 'planned_tss')::numeric else load.planned_tss end,
      case when p_payload ->> 'ruleset_version' = 'phase-13-joren-ruleset-1'
        then 'planned_zone_minutes' else load.calculation_method end,
      case when p_payload ->> 'ruleset_version' = 'phase-13-joren-ruleset-1'
        then 'phase-13-joren-ruleset-1' else load.ruleset_version end
    from private.workout_template_loads load
    where load.template_id = (v_workout ->> 'template_id')::uuid;
  end loop;

  select coalesce(sum(load.planned_tss), 0)
  into v_planned_tss
  from private.planned_workout_loads load
  join public.planned_workouts workout
    on workout.id = load.planned_workout_id
  where workout.revision_id = v_revision_id;

  if v_planned_tss <> (p_payload ->> 'planned_tss')::numeric then
    raise exception 'planned load snapshot mismatch' using errcode = '23514';
  end if;

  insert into private.plan_revision_loads (
    revision_id,
    athlete_id,
    target_tss,
    planned_tss,
    ruleset_version
  )
  values (
    v_revision_id,
    p_athlete_id,
    (p_payload ->> 'target_tss')::numeric,
    v_planned_tss,
    p_payload ->> 'ruleset_version'
  );

  for v_warning in
    select value from jsonb_array_elements(p_payload -> 'warnings')
  loop
    insert into public.plan_warnings (
      revision_id,
      athlete_id,
      planned_workout_id,
      rule_id,
      code,
      severity,
      message
    )
    values (
      v_revision_id,
      p_athlete_id,
      (
        select workout.id
        from public.planned_workouts workout
        where workout.revision_id = v_revision_id
          and workout.template_id =
            nullif(v_warning ->> 'affected_template_id', '')::uuid
        limit 1
      ),
      v_warning ->> 'rule_id',
      v_warning ->> 'code',
      v_warning ->> 'severity',
      v_warning ->> 'message'
    );
  end loop;

  insert into public.change_proposals (
    athlete_id,
    kind,
    target_plan_revision_id,
    base_plan_revision,
    reason_codes,
    public_explanation,
    ruleset_version
  )
  values (
    p_athlete_id,
    'plan_revision',
    v_revision_id,
    (p_payload ->> 'expected_base_revision')::integer,
    case
      when jsonb_array_length(p_payload -> 'warnings') = 0
        then array['weekly_plan_ready']
      else array(
        select warning ->> 'code'
        from jsonb_array_elements(p_payload -> 'warnings') warning
      )
    end,
    'A deterministic weekly plan is ready for review.',
    p_payload ->> 'ruleset_version'
  )
  returning id into v_proposal_id;

  if v_request_id is not null then
    update public.initial_plan_requests
    set status = 'consumed', consumed_at = statement_timestamp()
    where id = v_request_id
      and athlete_id = p_athlete_id
      and status = 'pending';
  end if;

  update public.weekly_plans
  set state = case
    when active_revision is null then 'pending_approval'
    else state
  end
  where id = v_plan_id and athlete_id = p_athlete_id;

  return jsonb_build_object(
    'plan_id', v_plan_id,
    'revision', v_revision,
    'proposal_id', v_proposal_id
  );
end;
$$;

-- Complete, partial and absent measurements cannot be confused with each other.
alter table private.activity_loads add constraint activity_loads_phase_13_provenance check (
  (calculation_method = 'actual_rpe_times_duration_hours' and realized_tss is not null)
  or (calculation_method = 'average_hr_zone_duration'
    and load_status = 'estimated_from_average_hr'
    and realized_tss is not null and realized_tss > 0
    and realized_tss::text not in ('NaN','Infinity','-Infinity')
    and total_minutes is not null and total_minutes > 0
    and total_minutes::text not in ('NaN','Infinity','-Infinity')
    and valid_minutes = 0 and coverage_ratio = 0
    and assigned_zone is not null and assigned_zone between 1 and 5
    and average_heart_rate_bpm is not null and average_heart_rate_bpm > 0
    and average_heart_rate_bpm::text not in ('NaN','Infinity','-Infinity')
    and zone_profile_id is not null)
  or (calculation_method = 'observed_zone_minutes'
    and load_status is not null
    and valid_minutes is not null and valid_minutes >= 0
    and valid_minutes::text not in ('NaN','Infinity','-Infinity')
    and (total_minutes is null or (total_minutes >= valid_minutes
      and total_minutes::text not in ('NaN','Infinity','-Infinity')))
    and (
      (load_status = 'unavailable' and realized_tss is null and valid_minutes = 0
        and (coverage_ratio = 0 or coverage_ratio is null))
      or (load_status in ('complete','partial_observed') and realized_tss is not null
        and realized_tss::text not in ('NaN','Infinity','-Infinity')
        and total_minutes is not null and total_minutes > 0 and valid_minutes > 0
        and coverage_ratio is not null and coverage_ratio > 0 and coverage_ratio <= 1
        and abs(coverage_ratio - valid_minutes / total_minutes) < 0.000000000000000001
        and (load_status = 'complete') = (valid_minutes = total_minutes))
    )
  )
);
