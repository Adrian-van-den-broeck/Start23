-- DISPOSABLE LOCAL DATABASE ONLY. Synthetic rest-only fixture; never production.
begin;
insert into auth.users (id) values
  ('a0000000-0000-0000-0000-0000000000a5'),
  ('b0000000-0000-0000-0000-0000000000a5');
insert into public.athlete_profiles
  (athlete_id, timezone, timezone_source, timezone_confirmed_at, onboarding_status)
values ('a0000000-0000-0000-0000-0000000000a5', 'Europe/Amsterdam',
  'manual', statement_timestamp(), 'in_progress');
select set_config('start23.checkin_write', 'on', true);
insert into public.weekly_checkins (id, athlete_id, week_start, timezone) values
  ('c0000000-0000-0000-0000-0000000000a5',
   'a0000000-0000-0000-0000-0000000000a5', '2026-08-03', 'Europe/Amsterdam'),
  ('c1000000-0000-0000-0000-0000000000a5',
   'a0000000-0000-0000-0000-0000000000a5', '2026-08-10', 'Europe/Amsterdam');
select set_config('start23.checkin_write', '', true);
create schema a5_release_probe;
grant usage on schema a5_release_probe to service_role;
create table a5_release_probe.payload (payload jsonb, result jsonb, snapshot jsonb);
create table a5_release_probe.receipts (session text primary key, result jsonb not null);
grant select, insert on a5_release_probe.receipts to service_role;
grant select on a5_release_probe.payload to service_role;
insert into a5_release_probe.payload (payload) values (jsonb_build_object(
  'checkin_id', 'c0000000-0000-0000-0000-0000000000a5',
  'expected_base_revision', 0, 'week_start', '2026-08-03',
  'timezone', 'Europe/Amsterdam', 'phase', 'base', 'target_basis', 'injury_rest_only',
  'input_fingerprint', repeat('a', 64), 'generation_fingerprint', repeat('b', 64),
  'total_duration_minutes', 0, 'low_intensity_percent', 0, 'high_intensity_percent', 0,
  'confirmed_injuries', '["run"]'::jsonb, 'low_only_disciplines', '[]'::jsonb,
  'goal_disciplines', '["run"]'::jsonb, 'availability', '[]'::jsonb,
  'available_dates', '[]'::jsonb, 'availability_source', 'checkin',
  'workouts', '[]'::jsonb, 'warnings', jsonb_build_array(jsonb_build_object(
    'rule_id', 'BR-010', 'code', 'all_disciplines_blocked_rest_only',
    'severity', 'warning', 'message', 'Rest only; confirmation required.')),
  'target_tss', 0, 'planned_tss', 0, 'ruleset_version', 'phase-13-joren-ruleset-1',
  'planning_ruleset_version', 'joren-planning-ruleset-2'
));

commit;
