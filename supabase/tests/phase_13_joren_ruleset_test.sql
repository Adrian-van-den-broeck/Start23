begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_column('public','training_history_entries','previous_month_weekly_minutes','canonical previous-month duration exists');
select has_column('public','activity_metrics','zone_minutes','observed durations are stored');
select has_column('private','activity_loads','coverage_ratio','coverage is private');
select has_column('private','activity_loads','zone_profile_id','average-HR method retains exact profile');
select has_table('private','phase_13_activity_load_history','prior load revisions are preserved');
select ok((select relrowsecurity from pg_class where oid = 'private.phase_13_activity_load_history'::regclass),'audit has RLS');
select ok(not has_table_privilege('authenticated','private.phase_13_activity_load_history','select'),'athletes cannot read private audit');
select ok(not has_table_privilege('anon','private.activity_loads','select'),'anonymous clients cannot read private loads');
select ok(not has_function_privilege('authenticated','public.get_plan_load_history_for_planning_v13(uuid,date)','execute'),'planning history remains service-only');
select ok(not has_function_privilege('authenticated','public.complete_activity_rpe(uuid,uuid,jsonb)','execute'),'clients cannot submit computed load');
select ok(not has_function_privilege('anon','public.save_calculated_zone_profile(uuid,jsonb)','execute'),'anonymous clients cannot create computed profiles');
select has_trigger('private','activity_loads','phase_13_activity_load_revision','load changes retain prior provenance');

insert into auth.users(id) values
 ('a0000000-0000-0000-0000-000000000013'),
 ('b0000000-0000-0000-0000-000000000013');
insert into public.athlete_profiles(athlete_id, date_of_birth, resting_heart_rate_bpm,timezone,onboarding_status)
values ('a0000000-0000-0000-0000-000000000013','1990-01-01',50,'UTC','in_progress'),
 ('b0000000-0000-0000-0000-000000000013','1990-01-01',50,'UTC','in_progress');
select set_config('request.jwt.claims','{"sub":"a0000000-0000-0000-0000-000000000013","role":"authenticated"}',true);
set local request.jwt.claim.sub = 'a0000000-0000-0000-0000-000000000013';
set local role authenticated;
select lives_ok($q$select * from public.replace_training_history('[
 {"discipline":"swim","average_hours_per_week":2.5},
 {"discipline":"bike","average_hours_per_week":6},
 {"discipline":"run","average_hours_per_week":3}]'::jsonb)$q$,'source onboarding example is accepted');
select is((select previous_month_weekly_minutes from public.training_history_entries where discipline='swim'),150::numeric,'hours convert exactly to minutes');
select throws_ok($q$select * from public.replace_training_history('[
 {"discipline":"swim","average_hours_per_week":60},
 {"discipline":"bike","average_hours_per_week":60},
 {"discipline":"run","average_hours_per_week":60}]'::jsonb)$q$,
 '23514','complete previous-month duration history is required','combined duration above 168 is rejected');
select is((select previous_month_weekly_minutes from public.training_history_entries where discipline='swim'),150::numeric,'invalid replacement is atomic');
select throws_ok($q$select * from public.replace_training_history('[
 {"discipline":"swim","average_hours_per_week":0},
 {"discipline":"bike","average_hours_per_week":0},
 {"discipline":"run","average_hours_per_week":0,"user_id":"b0000000-0000-0000-0000-000000000013"}]'::jsonb)$q$,
 '23514','complete previous-month duration history is required','identity cannot be supplied in history');
select set_config('request.jwt.claims','{"sub":"b0000000-0000-0000-0000-000000000013","role":"authenticated"}',true);
set local request.jwt.claim.sub = 'b0000000-0000-0000-0000-000000000013';
select is((select count(*) from public.training_history_entries),0::bigint,'another athlete cannot read the history');
reset role;

select * from finish();
rollback;
