-- ONLY a fresh disposable LOCAL database with every migration applied.
-- Synthetic fixture values are not physiological recommendations.
-- Intentionally commit: the integration runner uses independent psql processes.
begin;
select set_config('start23.critical_write', 'on', true);
select set_config('start23.profile_write', 'on', true);
do $$
declare v_user uuid; v_zone uuid; v_sport text;
begin
  foreach v_user in array array[
    'a6000000-0000-0000-0000-000000000006'::uuid,
    'b6000000-0000-0000-0000-000000000006'::uuid
  ] loop
    insert into auth.users(id) values (v_user);
    insert into public.athlete_profiles(athlete_id, timezone, timezone_source,
      timezone_confirmed_at, heart_rate_monitor_confirmed_at, onboarding_status)
      values (v_user, 'Europe/Amsterdam', 'manual', statement_timestamp(), statement_timestamp(), 'in_progress');
    insert into public.athlete_physiology_profiles(athlete_id, date_of_birth, resting_heart_rate_bpm)
      select athlete_id, '1990-01-02', 51 from private.athlete_identity_map where auth_user_id = v_user;
    insert into public.training_history_entries(athlete_id, discipline, previous_month_weekly_minutes, baseline_model_version)
      select v_user, s, 0, 'phase-13-joren-ruleset-1' from unnest(array['swim','bike','run']) s;
    insert into public.goals(athlete_id, race_type, race_name, race_date,
      swim_distance_meters, bike_distance_meters, run_distance_meters,
      total_target_time_seconds, swim_target_time_seconds, bike_target_time_seconds, run_target_time_seconds)
      values (v_user, 'triathlon', 'Disposable V6 test', current_date + 180,
        1500, 40000, 10000, 14400, 2400, 7200, 3600);
    foreach v_sport in array array['swim','bike','run'] loop
      insert into public.zone_profile_versions(athlete_id, discipline, version, setup_method, status,
        validated, fallback_active, needs_testing, requires_review, review_reason, ruleset_version, effective_from)
        values (v_user, v_sport, 1, 'manual', 'active', true, false, false, true,
          'soft_range_not_configured', 'phase-3-ruleset-2', statement_timestamp()) returning id into v_zone;
      insert into public.zone_metrics(zone_profile_id, athlete_id, metric_kind, value)
        values (v_zone, v_user, case v_sport when 'swim' then 'swim_css_seconds_per_100m'
          when 'bike' then 'bike_threshold_heart_rate_bpm' else 'run_lthr_bpm' end, 150);
      insert into public.zone_boundaries(zone_profile_id, athlete_id, zone_number, lower_value, upper_value)
        select v_zone, v_user, z, 100 + z * 10, 110 + z * 10 from generate_series(1,5) z;
    end loop;
    perform set_config('request.jwt.claims', jsonb_build_object('role','authenticated','sub',v_user)::text, true);
    perform set_config('request.jwt.claim.sub', v_user::text, true);
    perform public.complete_current_onboarding(coalesce(
      (select revision from public.onboarding_sessions where athlete_id = v_user), 0));
  end loop;
end;
$$;
commit;
