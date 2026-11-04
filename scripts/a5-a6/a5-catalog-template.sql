-- READ-ONLY CATALOG CHECK. Confirm the production project in its dashboard first.
-- This does NOT execute the application RPCs or prove RLS/concurrency behavior.
begin transaction read only;
set local statement_timeout = '10s';
with expected(signature, is_definer, authenticated_execute, service_execute, body_md5) as (
  values
__FUNCTION_ROWS__
), inspected as (
  select expected.*, p.oid, p.prosecdef, p.proconfig, p.provolatile,
    md5(replace(p.prosrc, E'\r\n', E'\n')) as actual_body_md5,
    coalesce(has_function_privilege('authenticated', p.oid, 'EXECUTE'), false) as authenticated_actual,
    coalesce(has_function_privilege('service_role', p.oid, 'EXECUTE'), false) as service_actual,
    coalesce(has_function_privilege('anon', p.oid, 'EXECUTE'), false) as anon_actual,
    exists(select 1 from aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) acl
      where acl.grantee = 0 and acl.privilege_type = 'EXECUTE') as public_actual
  from expected left join pg_proc p on p.oid = to_regprocedure(expected.signature)
)
select signature, oid is not null as present,
  prosecdef is not distinct from is_definer as security_mode_matches,
  authenticated_actual = authenticated_execute as authenticated_grant_matches,
  service_actual = service_execute as service_grant_matches,
  not anon_actual and not public_actual as public_anon_denied,
  actual_body_md5 = body_md5 as exact_pinned_body_matches,
  proconfig, provolatile
from inspected order by signature;
select c.relname, c.relrowsecurity as rls_enabled, c.relforcerowsecurity as rls_forced,
  exists(select 1 from pg_attribute a where a.attrelid=c.oid
    and a.attname='internal_athlete_id' and not a.attisdropped) as opaque_owner_column
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in
 ('weekly_checkins','weekly_plans','plan_revisions','change_proposals','swipe_week_drafts')
order by c.relname;
select conname, pg_get_constraintdef(oid) as definition from pg_constraint
where conname='plan_revisions_plan_id_athlete_id_fkey';
select to_regprocedure('public.get_operational_athlete_profile()') is not null as profile_rpc,
 to_regprocedure('public.get_weekly_plan(uuid,integer)') is not null as plan_rpc,
 to_regprocedure('public.create_weekly_plan_proposal_v2(uuid,jsonb)') is not null as legacy_generation_rpc,
 to_regprocedure('public.attach_checkin_plan_proposal(uuid,uuid,uuid)') is not null as attachment_rpc;
-- Any V2 object means this pre-V2 candidate requires further history review. Do not downgrade blindly.
select n.nspname, c.relname as unexpected_v2_object from pg_class c
join pg_namespace n on n.oid=c.relnamespace
where n.nspname='private' and (c.relname like 'realized_v2_%' or c.relname='workout_registration_events');
with expected(version) as (select unnest(array[__VERSIONS__]::text[]))
select expected.version as missing_required_version from expected
left join supabase_migrations.schema_migrations applied using(version) where applied.version is null;
select version as later_version_requiring_review from supabase_migrations.schema_migrations
where version > '__A5_VERSION__' order by version;
rollback;
