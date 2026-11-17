begin;
select plan(30);
select ok(has_function_privilege('authenticated','public.get_checkin_plan_proposal(uuid)','execute'),'public.get_checkin_plan_proposal(uuid) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.create_activity_summary_v2(uuid,text,jsonb)','execute'),'public.create_activity_summary_v2(uuid,text,jsonb) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_workout_registration(uuid)','execute'),'public.get_workout_registration(uuid) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.confirm_workout_registration(uuid,uuid,integer,text)','execute'),'public.confirm_workout_registration(uuid,uuid,integer,text) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_v6_weekly_plan(uuid,integer)','execute'),'public.get_v6_weekly_plan(uuid,integer) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_v6_mobile_weekly_plan(uuid,integer)','execute'),'public.get_v6_mobile_weekly_plan(uuid,integer) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_v6_mobile_calendar(date,date)','execute'),'public.get_v6_mobile_calendar(date,date) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_v6_move_workout_context(uuid)','execute'),'public.get_v6_move_workout_context(uuid) exact authenticated exception');
select ok(has_function_privilege('authenticated','private.v6_revision_workouts(uuid)','execute'),'private.v6_revision_workouts(uuid) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_frequency_preferences()','execute'),'public.get_frequency_preferences() exact authenticated exception');
select ok(has_function_privilege('authenticated','public.save_frequency_preferences(integer,uuid,jsonb)','execute'),'public.save_frequency_preferences(integer,uuid,jsonb) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.report_frequency_interruption(uuid,text,text)','execute'),'public.report_frequency_interruption(uuid,text,text) exact authenticated exception');
select ok(has_function_privilege('authenticated','public.get_v6_frequency_swipe_receipt(uuid)','execute'),'public.get_v6_frequency_swipe_receipt(uuid) exact authenticated exception');
select ok(not exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private') and p.proname like '%v6%' and has_function_privilege('anon',p.oid,'execute')),'no anonymous V6 execute');
select ok(not has_function_privilege('authenticated','public.create_v6_weekly_plan_proposal(uuid,jsonb)','execute'),'generated writer remains server-only');
select ok(not has_function_privilege('authenticated','public.get_activity_presentation_v2(uuid)','execute'),'metadata cannot be enumerated by athletes');
select ok(not has_function_privilege('anon','public.get_activity_presentation_v2(uuid)','execute'),'anonymous metadata denied');
select ok(has_function_privilege('service_role','public.get_activity_presentation_v2(uuid)','execute'),'versioned metadata available to server');
select ok(not has_function_privilege('service_role','private.activity_public_json_v2(uuid,uuid)','execute'),'internal projection remains ungranted');
select ok(not exists(select 1 from pg_auth_members m join pg_roles r on r.oid=m.roleid where r.rolname in ('v6_frequency_registrar','v6_frequency_test_executor')),'no test or registrar membership');
select is((select count(*) from private.frequency_reviewers),0::bigint,'no reviewer enrolled');
select is((select count(*) from private.frequency_decisions),0::bigint,'no frequency authority issued');
select ok(not exists(select 1 from unnest(array['workout_templates','workout_segments','workout_template_phase_tags','workout_template_zone_requirements']) t
 cross join unnest(array['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) p where has_table_privilege('service_role','public.'||t,p)),'unnecessary historical catalog service authority removed');
create table public.blocker_default_acl_probe(id integer);
select ok(not exists(select 1 from unnest(array['anon','authenticated','service_role']) r cross join unnest(array['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) p where has_table_privilege(r,'public.blocker_default_acl_probe',p)),'new app tables inherit no Dxtm client/service authority');
insert into auth.users(id) values ('ac170000-0000-0000-0000-000000000001');
set local role authenticated;
set local request.jwt.claims='{"role":"authenticated","sub":"a6000000-0000-0000-0000-000000000006"}';
select throws_ok($$select * from private.v6_revision_workouts('b6000000-0000-0000-0000-000000000006')$$,'42501','workout owner authorization required','private helper rejects foreign owner');
select lives_ok($$select * from private.v6_revision_workouts('a6000000-0000-0000-0000-000000000006')$$,'private helper preserves same-owner historical invoker dependency');
set local request.jwt.claims='{"role":"authenticated","sub":"ac170000-0000-0000-0000-000000000001"}';
select throws_ok($$select public.save_frequency_preferences(null,'ac170000-0000-0000-0000-000000000002','{"run":null,"bike":null,"swim":null}')$$,
 '23514','frequency preference precondition required','SQL NULL cannot bypass preference CAS');
select lives_ok($$select public.save_frequency_preferences(0,'ac170000-0000-0000-0000-000000000002','{"run":null,"bike":null,"swim":null}')$$,
 'valid owner preference save still works');
select lives_ok($$select public.save_frequency_preferences(0,'ac170000-0000-0000-0000-000000000002','{"run":null,"bike":null,"swim":null}')$$,
 'exact preference retry remains stable');
select throws_ok($$select public.save_frequency_preferences(0,'ac170000-0000-0000-0000-000000000003','{"run":null,"bike":null,"swim":null}')$$,
 'PT409','frequency preference changed','stale preference CAS remains closed');
reset role;
select * from finish();
rollback;
