begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(2);
select is((
  select count(*)::integer from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private') and p.prokind='f'
    and p.prosrc like '%errcode = ''40001''%'
    and p.proname not in ('prepare_polar_import_retry','record_polar_webhook','start_polar_import')
), 0, 'MVP business conflicts never deliberately raise serialization failure');
select is((
  select count(*)::integer from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private') and p.prokind='f'
    and p.prosrc like '%errcode = ''PT409''%'
), 28, 'all 28 inventoried MVP implementations use nonretryable HTTP 409');
select * from finish();
rollback;
