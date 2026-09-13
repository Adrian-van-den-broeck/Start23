-- Final Phase 13/14 R6-entry audit remediation.
--
-- This is deliberately a forward-only correction. The bounded dual-owner
-- compatibility columns remain in place; no R6 contract migration is started.

-- The legacy operational table is no longer a client-readable/writeable API.
-- Authenticated traffic uses the narrow RPCs below, which derive both owner
-- identifiers from the verified JWT and own all timestamps/status changes.
revoke all privileges on table public.athlete_profiles
from public, anon, authenticated, service_role;

create or replace function public.save_operational_athlete_profile(p_profile jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_profile public.athlete_profiles;
  v_has_timezone boolean := coalesce(p_profile ? 'timezone', false);
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_profile is null
     or jsonb_typeof(p_profile) <> 'object'
     or p_profile = '{}'::jsonb
     or exists (
       select 1 from jsonb_object_keys(p_profile) supplied(key)
       where supplied.key not in (
         'timezone', 'timezone_source', 'timezone_confirmed',
         'heart_rate_monitor_confirmed'
       )
     ) then
    raise exception 'invalid operational profile payload' using errcode = '23514';
  end if;
  if v_has_timezone <> (p_profile ? 'timezone_source')
     or v_has_timezone <> (p_profile ? 'timezone_confirmed')
     or (
       v_has_timezone
       and jsonb_typeof(p_profile -> 'timezone_confirmed') <> 'boolean'
     )
     or (
       v_has_timezone
       and (p_profile ->> 'timezone_confirmed')::boolean is distinct from true
     )
     or (
       v_has_timezone
       and p_profile ->> 'timezone_source' not in ('device', 'manual')
     )
     or (
       v_has_timezone
       and not exists (
         select 1 from pg_catalog.pg_timezone_names
         where name = p_profile ->> 'timezone'
       )
     )
     or (
       p_profile ? 'heart_rate_monitor_confirmed'
       and jsonb_typeof(p_profile -> 'heart_rate_monitor_confirmed') <> 'boolean'
     )
     or (
       p_profile ? 'heart_rate_monitor_confirmed'
       and (p_profile ->> 'heart_rate_monitor_confirmed')::boolean
         is distinct from true
     ) then
    raise exception 'explicit valid operational confirmation is required'
      using errcode = '23514';
  end if;

  insert into public.athlete_profiles (
    athlete_id,
    timezone,
    timezone_source,
    timezone_confirmed_at,
    heart_rate_monitor_confirmed_at,
    onboarding_status
  ) values (
    v_auth_user_id,
    case when v_has_timezone then p_profile ->> 'timezone' else 'UTC' end,
    case when v_has_timezone then p_profile ->> 'timezone_source' else null end,
    case when v_has_timezone then statement_timestamp() else null end,
    case when p_profile ? 'heart_rate_monitor_confirmed'
      then statement_timestamp() else null end,
    'in_progress'
  )
  on conflict (athlete_id) do update set
    timezone = case when v_has_timezone
      then excluded.timezone else public.athlete_profiles.timezone end,
    timezone_source = case when v_has_timezone
      then excluded.timezone_source else public.athlete_profiles.timezone_source end,
    timezone_confirmed_at = case when v_has_timezone
      then excluded.timezone_confirmed_at
      else public.athlete_profiles.timezone_confirmed_at end,
    heart_rate_monitor_confirmed_at = case
      when p_profile ? 'heart_rate_monitor_confirmed'
        then coalesce(
          public.athlete_profiles.heart_rate_monitor_confirmed_at,
          excluded.heart_rate_monitor_confirmed_at
        )
      else public.athlete_profiles.heart_rate_monitor_confirmed_at end,
    onboarding_status = case
      when public.athlete_profiles.onboarding_status = 'completed'
        then 'completed' else 'in_progress' end
  returning * into v_profile;

  return jsonb_build_object(
    'athlete_id', v_athlete_id,
    'timezone', v_profile.timezone,
    'timezone_source', v_profile.timezone_source,
    'timezone_confirmed_at', v_profile.timezone_confirmed_at,
    'heart_rate_monitor_confirmed_at', v_profile.heart_rate_monitor_confirmed_at,
    'onboarding_status', v_profile.onboarding_status,
    'revision', v_profile.revision,
    'created_at', v_profile.created_at,
    'updated_at', v_profile.updated_at
  );
end;
$$;

create or replace function public.get_operational_athlete_profile()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select jsonb_build_object(
    'athlete_id', v_athlete_id,
    'timezone', profile.timezone,
    'timezone_source', profile.timezone_source,
    'timezone_confirmed_at', profile.timezone_confirmed_at,
    'heart_rate_monitor_confirmed_at', profile.heart_rate_monitor_confirmed_at,
    'onboarding_status', profile.onboarding_status,
    'revision', profile.revision,
    'created_at', profile.created_at,
    'updated_at', profile.updated_at
  ) into v_result
  from public.athlete_profiles profile
  where profile.athlete_id = v_auth_user_id
    and profile.internal_athlete_id = v_athlete_id;

  return v_result;
end;
$$;

revoke execute on function public.save_operational_athlete_profile(jsonb)
from public, anon, service_role;
grant execute on function public.save_operational_athlete_profile(jsonb)
to authenticated;
revoke execute on function public.get_operational_athlete_profile()
from public, anon, service_role;
grant execute on function public.get_operational_athlete_profile()
to authenticated;

comment on table public.athlete_profiles is
  'Bounded R3 operational compatibility store. No direct authenticated API; use narrow owner-derived RPCs.';
comment on function public.get_operational_athlete_profile() is
  'Returns only current operational fields for the JWT-derived opaque athlete owner.';

-- Completion still needs to update the compatibility status after direct
-- table grants are removed. Its existing body derives and verifies the owner,
-- checks a revision precondition, and sets the trusted critical-write flag.
alter function public.complete_current_onboarding(bigint) security definer;

-- Keep broader authenticated operations as invoker functions. They consume
-- the narrow owner-derived operational projection instead of receiving table
-- access or elevated write privileges.
create or replace function public.start_weekly_checkin(p_week_start date)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_operational jsonb := public.get_operational_athlete_profile();
  v_timezone text := v_operational ->> 'timezone';
  v_checkin_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if extract(isodow from p_week_start) <> 1 then
    raise exception 'check-in week must start on Monday' using errcode = '23514';
  end if;
  if v_timezone is null
     or v_operational ->> 'timezone_source' not in ('device', 'manual')
     or v_operational ->> 'timezone_confirmed_at' is null then
    raise exception 'confirmed athlete timezone not found' using errcode = 'P0002';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  insert into public.weekly_checkins (athlete_id, week_start, timezone)
  values (v_athlete_id, p_week_start, v_timezone)
  on conflict (athlete_id, week_start) do update
    set updated_at = public.weekly_checkins.updated_at
  returning id into v_checkin_id;
  return public.get_weekly_checkin(v_checkin_id);
end;
$$;

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
     or v_discipline is distinct from 'swim'
     or v_protocol_id is distinct from 'start23_swim_css_400_200_v1'
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

alter function private.enforce_confirmed_activity_timezone() security definer;

-- One race-to-discipline mapping drives SQL onboarding and planner gates.
create or replace function private.required_disciplines_for_race_type(
  p_race_type text
)
returns text[]
language sql
immutable
security invoker
set search_path = ''
as $$
  select case p_race_type
    when 'run' then array['run']::text[]
    when 'bike' then array['bike']::text[]
    when 'swim' then array['swim']::text[]
    when 'duathlon' then array['bike', 'run']::text[]
    when 'triathlon' then array['swim', 'bike', 'run']::text[]
    else array[]::text[]
  end
$$;

revoke execute on function private.required_disciplines_for_race_type(text)
from public, anon, authenticated, service_role;

-- Keep the historical planner alias, but derive its value from the same
-- authoritative mapping used by current readiness.
create or replace function private.build_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.resolve_opaque_athlete_id(p_athlete_id);
  v_base jsonb := private.build_planning_input_snapshot_r3(p_athlete_id);
  v_profile jsonb;
  v_goal jsonb;
begin
  if v_athlete_id is null then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;

  select jsonb_build_object(
    'athlete_id', v_athlete_id,
    'date_of_birth', physiology.date_of_birth,
    'resting_heart_rate_bpm', physiology.resting_heart_rate_bpm,
    'timezone', operational.timezone,
    'timezone_source', operational.timezone_source,
    'timezone_confirmed_at', operational.timezone_confirmed_at,
    'heart_rate_monitor_confirmed_at',
      operational.heart_rate_monitor_confirmed_at,
    'revision', operational.revision
  ) into v_profile
  from public.athlete_profiles operational
  left join public.athlete_physiology_profiles physiology
    on physiology.athlete_id = operational.internal_athlete_id
  where operational.internal_athlete_id = v_athlete_id;

  select jsonb_build_object(
    'id', goal.id,
    'priority', goal.priority,
    'goal_type', goal.goal_type,
    'race_type', goal.race_type,
    'race_name', goal.race_name,
    'race_date', goal.race_date,
    'swim_distance_meters', goal.swim_distance_meters,
    'bike_distance_meters', goal.bike_distance_meters,
    'run_distance_meters', goal.run_distance_meters,
    'total_target_time_seconds', goal.total_target_time_seconds,
    'swim_target_time_seconds', goal.swim_target_time_seconds,
    'bike_target_time_seconds', goal.bike_target_time_seconds,
    'run_target_time_seconds', goal.run_target_time_seconds,
    'specific_focus', goal.specific_focus,
    'target_date', goal.race_date,
    'race_discipline_profile', to_jsonb(
      private.required_disciplines_for_race_type(goal.race_type)
    ),
    'revision', goal.revision
  ) into v_goal
  from public.goals goal
  where goal.internal_athlete_id = v_athlete_id
    and goal.status = 'active';

  return jsonb_set(
    jsonb_set(
      jsonb_set(v_base, '{profile}', coalesce(v_profile, 'null'::jsonb)),
      '{goal}', coalesce(v_goal, 'null'::jsonb)
    ),
    '{onboarding_version}', to_jsonb('phase-14-onboarding-v2'::text)
  );
end;
$$;

revoke execute on function private.build_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

create or replace function private.current_onboarding_satisfied_steps(
  p_athlete_id uuid
)
returns text[]
language sql
stable
security invoker
set search_path = ''
as $$
  select array_remove(array[
    case when exists (
      select 1 from public.athlete_profiles operational
      join public.athlete_physiology_profiles physiology
        on physiology.athlete_id = operational.internal_athlete_id
      where operational.internal_athlete_id = p_athlete_id
        and physiology.date_of_birth is not null
        and physiology.resting_heart_rate_bpm is not null
    ) then 'profile' end,
    case when exists (
      select 1 from public.athlete_profiles operational
      where operational.internal_athlete_id = p_athlete_id
        and operational.heart_rate_monitor_confirmed_at is not null
    ) then 'heart_rate_monitor' end,
    case when exists (
      select 1 from public.athlete_profiles operational
      where operational.internal_athlete_id = p_athlete_id
        and operational.timezone is not null
        and operational.timezone_source in ('device', 'manual')
        and operational.timezone_confirmed_at is not null
    ) then 'timezone' end,
    case when (
      select count(*) from public.training_history_entries history
      where history.internal_athlete_id = p_athlete_id
        and history.previous_month_weekly_minutes is not null
        and history.baseline_model_version = 'phase-13-joren-ruleset-1'
    ) = 3 then 'history' end,
    case when exists (
      select 1 from public.goals goal
      where goal.internal_athlete_id = p_athlete_id
        and goal.status = 'active'
        and cardinality(
          private.required_disciplines_for_race_type(goal.race_type)
        ) > 0
        and goal.race_name is not null
        and goal.race_date is not null
        and goal.total_target_time_seconds is not null
    ) then 'goal' end,
    case when exists (
      select 1 from public.goals goal
      where goal.internal_athlete_id = p_athlete_id
        and goal.status = 'active'
        and cardinality(
          private.required_disciplines_for_race_type(goal.race_type)
        ) > 0
        and not exists (
          select required.discipline
          from unnest(
            private.required_disciplines_for_race_type(goal.race_type)
          ) required(discipline)
          except
          select profile.discipline
          from public.zone_profile_versions profile
          where profile.internal_athlete_id = p_athlete_id
            and profile.status = 'active'
        )
    ) then 'zones' end
  ], null)
$$;

revoke execute on function private.current_onboarding_satisfied_steps(uuid)
from public, anon, authenticated, service_role;

comment on function private.current_onboarding_satisfied_steps(uuid) is
  'Current Phase 14 eligibility: all-three history, race-required active zones, and no readiness from setup intent rows.';

-- Match the current Pydantic race contract exactly. Every nullable branch is
-- explicit because SQL CHECK constraints otherwise accept UNKNOWN.
alter table public.goals
  drop constraint goals_r4_structured_race_valid;

alter table public.goals
  add constraint goals_r6_entry_structured_race_valid check (
    (
      race_type is null
      and race_name is null
      and race_date is null
      and swim_distance_meters is null
      and bike_distance_meters is null
      and run_distance_meters is null
      and total_target_time_seconds is null
      and swim_target_time_seconds is null
      and bike_target_time_seconds is null
      and run_target_time_seconds is null
      and specific_focus is null
    )
    or (
      race_type is not null
      and race_type in ('run', 'bike', 'swim', 'triathlon', 'duathlon')
      and race_name is not null
      and race_name = btrim(race_name)
      and char_length(race_name) between 1 and 120
      and race_date is not null
      and total_target_time_seconds is not null
      and total_target_time_seconds between 1 and 604800
      and (
        specific_focus is null
        or (
          specific_focus = btrim(specific_focus)
          and char_length(specific_focus) between 1 and 1000
        )
      )
      and (
        swim_distance_meters is null
        or swim_distance_meters between 1 and 1000000
      )
      and (
        bike_distance_meters is null
        or bike_distance_meters between 1 and 1000000
      )
      and (
        run_distance_meters is null
        or run_distance_meters between 1 and 1000000
      )
      and (
        swim_target_time_seconds is null
        or swim_target_time_seconds between 1 and 604800
      )
      and (
        bike_target_time_seconds is null
        or bike_target_time_seconds between 1 and 604800
      )
      and (
        run_target_time_seconds is null
        or run_target_time_seconds between 1 and 604800
      )
      and coalesce(swim_target_time_seconds, 0)
        + coalesce(bike_target_time_seconds, 0)
        + coalesce(run_target_time_seconds, 0)
        <= total_target_time_seconds
      and case race_type
        when 'run' then
          run_distance_meters is not null
          and swim_distance_meters is null
          and bike_distance_meters is null
          and swim_target_time_seconds is null
          and bike_target_time_seconds is null
        when 'bike' then
          bike_distance_meters is not null
          and swim_distance_meters is null
          and run_distance_meters is null
          and swim_target_time_seconds is null
          and run_target_time_seconds is null
        when 'swim' then
          swim_distance_meters is not null
          and bike_distance_meters is null
          and run_distance_meters is null
          and bike_target_time_seconds is null
          and run_target_time_seconds is null
        when 'triathlon' then
          swim_distance_meters is not null
          and bike_distance_meters is not null
          and run_distance_meters is not null
        when 'duathlon' then
          swim_distance_meters is null
          and bike_distance_meters is not null
          and run_distance_meters is not null
          and swim_target_time_seconds is null
        else false
      end
    )
  ) not valid;

create or replace function private.enforce_current_structured_race_goal()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.race_type is not null
     and (new.race_date is null or new.race_date <= current_date) then
    raise exception 'race date must be in the future' using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_current_structured_race_goal()
from public, anon, authenticated, service_role;

create trigger goals_r6_entry_validate_current_race
before insert or update of
  race_type,
  race_name,
  race_date,
  swim_distance_meters,
  bike_distance_meters,
  run_distance_meters,
  total_target_time_seconds,
  swim_target_time_seconds,
  bike_target_time_seconds,
  run_target_time_seconds,
  specific_focus
on public.goals
for each row execute function private.enforce_current_structured_race_goal();

comment on constraint goals_r6_entry_structured_race_valid on public.goals is
  'Current five-race contract with explicit NULL, applicability, bound, and target-time relationship validation.';

-- Submaximal calibration is now a deterministic threshold estimate, not a
-- reviewed field test. Retain the old implementation behind a non-callable
-- name and wrap it so existing idempotency/locking behavior is preserved while
-- the persisted source quality remains truthful.
alter table public.zone_profile_versions
  drop constraint zone_profile_source_quality_valid,
  drop constraint zone_profile_calculated_metadata_valid;

alter table public.zone_profile_versions
  add constraint zone_profile_source_quality_valid check (
    source_quality in (
      'measured_lab',
      'reviewed_field_threshold',
      'submaximal_calibration_estimate',
      'athlete_entered',
      'estimated',
      'unknown'
    )
  ),
  add constraint zone_profile_calculated_metadata_valid check (
    (
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
    )
    or (
      setup_method = 'calculated'
      and zone_model_version = 'phase-13-joren-ruleset-1'
      and ruleset_version = 'phase-13-joren-ruleset-1'
      and source_quality in (
        'reviewed_field_threshold', 'submaximal_calibration_estimate'
      )
      and calibration_evaluation_id is not null
      and calculated_at is not null
      and calculation_fingerprint is not null
      and evidence_version = 'phase-13-joren-ruleset-1'
      and review_reason = 'athlete_confirmation_required'
      and review_status in (
        'pending_athlete_confirmation',
        'confirmed_by_athlete',
        'rejected_by_athlete'
      )
      and jsonb_array_length(metric_profiles) = 1
    )
  );

alter function public.save_calculated_zone_profile(uuid, jsonb)
  rename to save_calculated_zone_profile_r5;

revoke execute on function public.save_calculated_zone_profile_r5(uuid, jsonb)
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
  v_model text := coalesce(
    p_profile -> 'metric_profiles' -> 0 ->> 'zone_model_version',
    ''
  );
  v_source_quality text := p_profile ->> 'source_quality';
  v_source_method text := p_profile ->> 'source_method';
  v_discipline text := p_profile ->> 'discipline';
  v_evaluation_id uuid := nullif(
    p_profile ->> 'calibration_evaluation_id',
    ''
  )::uuid;
  v_evaluation public.calibration_evaluations;
  v_forward_profile jsonb := p_profile;
  v_result jsonb;
  v_original_trusted text :=
    current_setting('start23.trusted_calculated_zone', true);
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;

  if v_model = 'phase-13-joren-ruleset-1'
     and v_source_quality not in (
       'reviewed_field_threshold', 'submaximal_calibration_estimate'
     ) then
    raise exception 'Phase 13 calibration requires attributable evaluation'
      using errcode = '23514';
  end if;

  if v_source_quality = 'submaximal_calibration_estimate' then
    if v_evaluation_id is null
       or v_discipline not in ('swim', 'bike', 'run')
       or v_source_method is distinct from
         'start23_week1_' || v_discipline || '_calibration_v1' then
      raise exception 'submaximal calibration provenance is inconsistent'
        using errcode = '23514';
    end if;

    select * into v_evaluation
    from public.calibration_evaluations evaluation
    where evaluation.id = v_evaluation_id
      and evaluation.athlete_id = p_athlete_id
      and evaluation.discipline = v_discipline
      and evaluation.protocol_id = v_source_method
      and evaluation.status = 'threshold_estimated'
      and evaluation.requires_athlete_confirmation
      and evaluation.zone_model_version = v_model;
    if not found then
      raise exception 'pending submaximal calibration evaluation not found'
        using errcode = 'P0002';
    end if;
    if v_evaluation.zone_profiles is distinct from p_profile -> 'metric_profiles' then
      raise exception 'submaximal zone calculation does not match its evaluation'
        using errcode = '23514';
    end if;

    -- The R5 implementation already supplies the transaction lock, immutable
    -- threshold decision, pending zone profile, proposal, and replay behavior.
    v_forward_profile := jsonb_set(
      p_profile,
      '{source_quality}',
      to_jsonb('reviewed_field_threshold'::text),
      false
    );
  end if;

  v_result := public.save_calculated_zone_profile_r5(
    p_athlete_id,
    v_forward_profile
  );

  if v_source_quality = 'submaximal_calibration_estimate' then
    perform set_config('start23.trusted_calculated_zone', 'on', true);
    update public.zone_profile_versions
    set source_quality = 'submaximal_calibration_estimate'
    where id = (v_result ->> 'zone_profile_id')::uuid
      and athlete_id = p_athlete_id
      and calibration_evaluation_id = v_evaluation_id;
    if not found then
      raise exception 'calculated zone profile was not persisted'
        using errcode = 'P0002';
    end if;
    perform set_config(
      'start23.trusted_calculated_zone',
      coalesce(v_original_trusted, ''),
      true
    );
  end if;

  return v_result;
end;
$$;

revoke all on function public.save_calculated_zone_profile(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.save_calculated_zone_profile(uuid, jsonb)
to service_role;

comment on function public.save_calculated_zone_profile(uuid, jsonb) is
  'Persists attributable field-test or submaximal estimates as pending profiles; activation remains athlete-confirmed and stale-safe.';

comment on column private.activity_loads.calculation_method is
  'Immutable provenance. actual_rpe_times_duration_hours is legacy Phase 7 only; Phase 13 uses observed_zone_minutes or average_hr_zone_duration.';
