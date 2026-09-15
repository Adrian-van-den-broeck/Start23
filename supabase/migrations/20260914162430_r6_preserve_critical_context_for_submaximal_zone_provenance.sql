-- R6 runtime remediation: the R5 implementation restores its caller's
-- critical-write setting before the Phase 13 wrapper corrects the persisted
-- source-quality provenance. Preserve both guards explicitly so the approved
-- submaximal pending lifecycle remains guarded and executable.

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
  v_original_critical text :=
    current_setting('start23.critical_write', true);
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
    perform set_config('start23.critical_write', 'on', true);
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
      'start23.critical_write',
      coalesce(v_original_critical, ''),
      true
    );
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
