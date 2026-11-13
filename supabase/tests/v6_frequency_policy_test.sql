begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;
select no_plan();

insert into auth.users(id,email) values
  ('fa000000-0000-0000-0000-000000000001','frequency-a@example.invalid'),
  ('fa000000-0000-0000-0000-000000000002','frequency-b@example.invalid');

select is((select count(*)::integer from private.frequency_reviewers),0,'migration enrolls no invented reviewer or operator');
select ok(not has_function_privilege('service_role','private.register_frequency_decision(integer,jsonb)','execute'),'service role cannot issue athlete maxima');
select ok(not has_function_privilege('authenticated','private.register_frequency_decision(integer,jsonb)','execute'),'athlete cannot issue a maximum');
select ok(has_function_privilege('service_role','public.create_v6_frequency_swipe_proposal(uuid,jsonb)','execute'),'atomic swipe submit is a trusted backend boundary');
select ok(not has_function_privilege('authenticated','public.create_v6_frequency_swipe_proposal(uuid,jsonb)','execute'),'athlete cannot bypass frequency checks through internal submit');
select ok(not has_function_privilege('anon','public.get_frequency_preferences()','execute'),'anonymous preference read denied');
select ok(not pg_has_role('service_role','v6_frequency_registrar','member'),'registrar not granted to backend');
select ok(not pg_has_role('service_role','v6_frequency_test_executor','member'),'TEST_ONLY execution not granted to backend');
select throws_ok($$select private.register_frequency_decision(0,'{}')$$,'42501',null,'even database-owner invocation has no designated operator');

select ok((select bool_and(relrowsecurity and relforcerowsecurity) from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='private' and relname in ('frequency_preferences','frequency_decisions','frequency_reviewers','frequency_draft_contexts')),'all frequency records have forced RLS');
select ok(not has_table_privilege('authenticated','private.frequency_decisions','select,insert,update,delete'),'authorization records remain private');
select ok(not has_table_privilege('service_role','private.frequency_decisions','insert,update,delete'),'backend cannot directly issue/alter authority');

set local role authenticated;
select set_config('request.jwt.claims','{"sub":"fa000000-0000-0000-0000-000000000001","role":"authenticated"}',true);
select set_config('request.jwt.claim.sub','fa000000-0000-0000-0000-000000000001',true);
select is(public.get_frequency_preferences()->>'revision','0','preference is optional with no onboarding requirement');
select is(public.get_frequency_preferences()#>'{preferences,run}','null'::jsonb,'missing preference is null');
select set_config('test.frequency.receipt',public.save_frequency_preferences(0,'fb000000-0000-0000-0000-000000000001','{"run":2,"bike":0,"swim":null}')::text,true);
select is(public.get_frequency_preferences()#>>'{preferences,bike}','0','zero is preserved separately from null');
select is(public.get_frequency_preferences()->>'revision','1','first save has exact revision');
select ok(public.get_frequency_preferences()->>'confirmed_at' is not null,'confirmation timestamp is server owned');
select ok(public.save_frequency_preferences(0,'fb000000-0000-0000-0000-000000000001','{"run":2,"bike":0,"swim":null}')=current_setting('test.frequency.receipt')::jsonb,'lost acknowledgement returns original immutable save');
select throws_ok($$select public.save_frequency_preferences(0,'fb000000-0000-0000-0000-000000000002','{"run":3,"bike":0,"swim":null}')$$,'PT409',null,'stale preference cannot overwrite');
select throws_ok($$select public.save_frequency_preferences(0,'fb000000-0000-0000-0000-000000000001','{"run":3,"bike":0,"swim":null}')$$,'PT409',null,'same operation with changed payload rejects');
select throws_ok($$select public.save_frequency_preferences(1,gen_random_uuid(),'{"run":true,"bike":0,"swim":null}')$$,'23514',null,'boolean count rejected');
select throws_ok($$select public.save_frequency_preferences(1,gen_random_uuid(),'{"run":1.5,"bike":0,"swim":null}')$$,'23514',null,'fractional count rejected');
select throws_ok($$select public.save_frequency_preferences(1,gen_random_uuid(),'{"run":24,"bike":1,"swim":null}')$$,'23514',null,'combined technical envelope enforced');
select throws_ok($$select public.save_frequency_preferences(1,gen_random_uuid(),'{"run":2,"bike":0,"swim":null,"maximum":5}')$$,'23514',null,'client maximum not accepted');
select throws_ok($$select * from private.frequency_preferences$$,'42501',null,'athlete cannot enumerate or rewrite history');

select is(public.report_frequency_interruption('fc000000-0000-0000-0000-000000000001','injury','run')->>'revision','2','reported injury invalidates future expansion immediately');
select is(public.get_frequency_preferences()->'reconfirmation_required','["run"]'::jsonb,'injury requires preference reconfirmation for affected sport');
select is(public.get_frequency_preferences()#>>'{preferences,run}','2','injury retains original visible wish');
select is(public.report_frequency_interruption('fc000000-0000-0000-0000-000000000001','injury','run')->>'revision','2','interruption retry does not create another revision');
select ok(public.save_frequency_preferences(0,'fb000000-0000-0000-0000-000000000001','{"run":2,"bike":0,"swim":null}')=current_setting('test.frequency.receipt')::jsonb,'historical save replay remains exact after invalidation');
select is(public.get_frequency_preferences()->'reconfirmation_required','["run"]'::jsonb,'historical receipt never clears current suspension');
select is(public.report_frequency_interruption('fc000000-0000-0000-0000-000000000002','illness')->'reconfirmation_required','["bike","run","swim"]'::jsonb,'illness invalidates all sports without invented duration');
select is(public.save_frequency_preferences(3,'fb000000-0000-0000-0000-000000000003','{"run":2,"bike":0,"swim":null}')->'reconfirmation_required','[]'::jsonb,'athlete explicitly reconfirms the wish');
select is(public.save_frequency_preferences(4,'fb000000-0000-0000-0000-000000000004','{"run":null,"bike":null,"swim":null}')->'preferences','{"run":null,"bike":null,"swim":null}'::jsonb,'athlete can revoke every preference');
select is(public.report_frequency_interruption('fc000000-0000-0000-0000-000000000003','training_interruption')->>'revision','6','explicit training interruption is independent of missed-day thresholds');

select set_config('request.jwt.claims','{"sub":"fa000000-0000-0000-0000-000000000002","role":"authenticated"}',true);
select set_config('request.jwt.claim.sub','fa000000-0000-0000-0000-000000000002',true);
select is(public.get_frequency_preferences()->>'revision','0','second athlete cannot see first preference');
reset role;
select is((select count(*)::integer from private.frequency_decisions),0,'no report/reconfirmation creates any individual maximum');
select is((select count(*)::integer from private.frequency_preferences),6,'every old preference revision remains');
select throws_ok($$update private.frequency_preferences set preferences='{}'$$,'42501',null,'even owner SQL cannot rewrite history');
select throws_ok($$delete from private.frequency_preferences$$,'42501',null,'even owner SQL cannot erase history');
delete from auth.users where id='fa000000-0000-0000-0000-000000000001';
select is((select count(*)::integer from private.frequency_preferences),0,'explicit account deletion cascades preference history');
select is((select count(*)::integer from private.athlete_identity_map where auth_user_id='fa000000-0000-0000-0000-000000000001'),0,'account deletion retains opaque-owner cleanup contract');
select * from finish();
rollback;
