-- Phase 13 supersedes the accepted write fixture; legacy columns remain asserted.
begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_column(
  'public',
  'training_history_entries',
  'average_weekly_distance',
  'two-month history stores average weekly distance'
);
select has_column(
  'public',
  'training_history_entries',
  'distance_unit',
  'two-month history stores the canonical distance unit'
);
select has_column(
  'public',
  'training_history_entries',
  'average_sessions_per_week',
  'two-month history stores average weekly frequency'
);
select has_column(
  'public',
  'training_history_entries',
  'history_window_months',
  'the observation window is explicit'
);

select ok(
  not (
    select attnotnull
    from pg_attribute
    where attrelid = 'public.training_history_entries'::regclass
      and attname = 'weekly_minutes'
  )
  and not (
    select attnotnull
    from pg_attribute
    where attrelid = 'public.training_history_entries'::regclass
      and attname = 'experience_years'
  ),
  'legacy history fields remain stored but are no longer required'
);

select ok(
  not has_table_privilege(
    'authenticated', 'public.training_history_entries', 'delete'
  ),
  'new history replacement cannot delete historical rows'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.save_primary_race_goal(uuid,text,text,text,date,text[])',
    'execute'
  )
  and not has_function_privilege(
    'authenticated',
    'public.save_primary_race_goal(uuid,text,text,text,smallint,date,text[])',
    'execute'
  ),
  'only the goal RPC without retired feasibility is writable'
);

insert into auth.users (id)
values
  ('a0000000-0000-0000-0000-000000000014'),
  ('b0000000-0000-0000-0000-000000000014');

insert into public.athlete_profiles (
  athlete_id,
  date_of_birth,
  resting_heart_rate_bpm,
  timezone,
  onboarding_status
)
values
  (
    'a0000000-0000-0000-0000-000000000014',
    '1990-05-20',
    52,
    'Europe/Amsterdam',
    'in_progress'
  ),
  (
    'b0000000-0000-0000-0000-000000000014',
    '1992-06-10',
    55,
    'Europe/London',
    'in_progress'
  );

select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000014","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'a0000000-0000-0000-0000-000000000014';
set local role authenticated;

select throws_ok(
  $$
    update public.athlete_profiles
    set height_cm = 181
    where athlete_id = 'a0000000-0000-0000-0000-000000000014'
  $$,
  '23514',
  'retired profile fields cannot be changed',
  'retired profile fields cannot receive new values'
);

select lives_ok(
  $$
    select * from public.replace_training_history(
      '[
        {"discipline":"swim","average_hours_per_week":2},
        {"discipline":"bike","average_hours_per_week":4},
        {"discipline":"run","average_hours_per_week":3}
      ]'::jsonb
    )
  $$,
  'previous-month history is stored without exposing a private baseline'
);

select is(
  (
    select count(*)
    from public.training_history_entries
    where previous_month_weekly_minutes is not null
      and baseline_model_version = 'phase-13-joren-ruleset-1'
      and history_window_months is null
      and weekly_minutes is null
      and experience_years is null
  ),
  3::bigint,
  'new history rows do not populate or reinterpret retired values'
);

select throws_ok(
  $$
    select * from public.replace_training_history(
      '[
        {"discipline":"swim","weekly_minutes":60,"experience_years":1},
        {"discipline":"bike","weekly_minutes":120,"experience_years":2},
        {"discipline":"run","weekly_minutes":90,"experience_years":3}
      ]'::jsonb
    )
  $$,
  '23514',
  'complete previous-month duration history is required',
  'the superseded history write shape is rejected'
);

select lives_ok(
  $$
    select public.save_primary_race_goal(
      null,
      'Phase 14 race',
      'Finish with an even run.',
      'Complete every selected discipline.',
      '2027-07-01',
      array['swim', 'bike', 'run']
    )
  $$,
  'a goal can be saved without feasibility'
);

select is(
  (
    select feasibility_score
    from public.goals
    where athlete_id = 'a0000000-0000-0000-0000-000000000014'
  ),
  null::smallint,
  'new goal writes leave the retained historical feasibility column empty'
);

select set_config('start23.critical_write', '', true);
select set_config(
  'request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-000000000014","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub =
  'b0000000-0000-0000-0000-000000000014';

select is(
  (select count(*) from public.training_history_entries),
  0::bigint,
  'another athlete cannot read the first athlete two-month history'
);

select is(
  (select count(*) from public.goals),
  0::bigint,
  'another athlete cannot read the first athlete goal'
);

reset role;

select * from finish();
rollback;
