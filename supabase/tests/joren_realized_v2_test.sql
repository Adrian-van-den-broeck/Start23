-- DEFERRED BY OWNER - PRE-BETA. Run after replaying the forward chain.
begin;
select plan(10);
select has_table('private', 'realized_v2_calculations');
select has_table('private', 'realized_v2_activity_inputs');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.realized_v2_calculations'::regclass), 'private calculation RLS forced');
select ok((select relrowsecurity and relforcerowsecurity from pg_class where oid = 'private.realized_v2_activity_inputs'::regclass), 'private input RLS forced');
select ok(not has_table_privilege('authenticated','private.realized_v2_calculations','SELECT'), 'athlete cannot read private calculations');
select ok(not has_table_privilege('anon','private.realized_v2_calculations','SELECT'), 'anonymous cannot read private calculations');
select ok(not has_table_privilege('service_role','private.realized_v2_calculations','UPDATE'), 'service cannot rewrite calculation history');
select ok(has_function_privilege('service_role','public.complete_activity_rpe_v2(uuid,uuid,jsonb)','EXECUTE'), 'trusted completion allowed');
select ok(not has_function_privilege('authenticated','public.complete_activity_rpe_v2(uuid,uuid,jsonb)','EXECUTE'), 'athlete cannot submit private calculation');
select ok(not has_function_privilege('authenticated','public.get_activity_processing_context_v2(uuid,uuid)','EXECUTE'), 'private context denied');
select * from finish();
rollback;
