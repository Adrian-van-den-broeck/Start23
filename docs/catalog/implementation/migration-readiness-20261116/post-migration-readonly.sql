-- Metadata/source-state assertions after ALL 63 migrations, owner session only.
-- Not a fixture: no accounts, DDL, writes, recalculation or permission changes.
begin read only;
set local statement_timeout='10s';
select count(*) = 63 as expected_migration_count,
  count(distinct version) = 63 as distinct_versions
from supabase_migrations.schema_migrations;
select count(*) = 77 as all_sources_installed,
  count(*) filter (where activation <> 'INACTIVE') = 0 as all_sources_inactive,
  count(*) filter (where planned_tss <> official_decimal::numeric) = 0
    as exact_decimal_storage
from private.v6_source_revisions;
select count(*) = 77 as hidden_templates,
  bool_and(t.inactive_v6) as all_template_flags_inactive,
  count(l.template_id) = 0 as no_historical_load_projection
from private.v6_source_revisions s
join public.workout_templates t on t.id=s.template_id
left join private.workout_template_loads l on l.template_id=s.template_id;
select not exists(select 1 from private.frequency_reviewers) as no_enrolled_reviewers,
  not exists(select 1 from private.frequency_decisions) as no_issued_authorizations;
select not exists (
  select 1 from pg_auth_members m join pg_roles r on r.oid=m.roleid
  where r.rolname in ('v6_frequency_registrar','v6_frequency_test_executor')
) as no_registrar_or_test_memberships;
select n.nspname,c.relname,c.relrowsecurity,c.relforcerowsecurity,
  c.relacl::text as acl
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='private' and c.relkind='r'
  and (c.relname like 'v6_%' or c.relname like 'realized_v2_%'
       or c.relname like 'frequency_%' or c.relname='workout_registration_events')
order by c.relname;
select p.oid::regprocedure::text as signature,
  has_function_privilege('anon',p.oid,'EXECUTE') as anon_execute,
  has_function_privilege('authenticated',p.oid,'EXECUTE') as athlete_execute,
  has_function_privilege('service_role',p.oid,'EXECUTE') as service_execute,
  p.prosecdef as security_definer,p.proconfig
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname in ('public','private') and p.prokind='f'
order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid);
rollback;
