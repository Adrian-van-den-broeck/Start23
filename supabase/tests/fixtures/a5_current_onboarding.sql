-- Test-only overlay after the original A5 athlete_profiles INSERT.
-- Synthetic values follow existing onboarding fixtures; no planning bypass.
-- The caller is the disposable database owner, inside the A5 rollback transaction.
select set_config('start23.profile_write', 'on', true);
select set_config('start23.critical_write', 'on', true);
update public.athlete_profiles set heart_rate_monitor_confirmed_at = statement_timestamp()
where athlete_id = 'a0000000-0000-0000-0000-0000000000a5';
insert into public.athlete_physiology_profiles
  (athlete_id, date_of_birth, resting_heart_rate_bpm)
select athlete_id, '1990-01-02', 51 from private.athlete_identity_map
where auth_user_id = 'a0000000-0000-0000-0000-0000000000a5';
insert into public.training_history_entries
  (athlete_id, discipline, previous_month_weekly_minutes, baseline_model_version)
select 'a0000000-0000-0000-0000-0000000000a5', discipline, 0,
  'phase-13-joren-ruleset-1' from unnest(array['swim','bike','run']) discipline;
insert into public.goals
  (athlete_id, race_type, race_name, race_date, run_distance_meters,
   total_target_time_seconds, run_target_time_seconds)
values ('a0000000-0000-0000-0000-0000000000a5', 'run', 'Synthetic A5 recovery',
  current_date + 90, 10000, 3600, 3600);
-- Only the race-required discipline needs an active zone profile.
insert into public.zone_profile_versions
  (athlete_id, discipline, version, setup_method, status, validated,
   fallback_active, needs_testing, requires_review, review_reason,
   ruleset_version, effective_from)
values ('a0000000-0000-0000-0000-0000000000a5', 'run', 1, 'manual', 'active',
  true, false, false, true, 'soft_range_not_configured',
  'phase-3-ruleset-2', statement_timestamp());
insert into public.zone_metrics (zone_profile_id, athlete_id, metric_kind, value)
select id, athlete_id, 'run_lthr_bpm', 150 from public.zone_profile_versions
where athlete_id = 'a0000000-0000-0000-0000-0000000000a5';
insert into public.zone_boundaries
  (zone_profile_id, athlete_id, zone_number, lower_value, upper_value)
select id, athlete_id, z, 100 + z * 10, 110 + z * 10
from public.zone_profile_versions cross join generate_series(1,5) z
where athlete_id = 'a0000000-0000-0000-0000-0000000000a5';
select set_config('start23.profile_write', '', true);
select set_config('start23.critical_write', '', true);
select set_config('request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-0000000000a5","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'a0000000-0000-0000-0000-0000000000a5';
set local role authenticated;
select public.complete_current_onboarding(coalesce(
  (select revision from public.onboarding_sessions
   where athlete_id = 'a0000000-0000-0000-0000-0000000000a5'), 0));
reset role;
