"""Exact proposed permission exceptions; no database connection or approval mode."""

import json
from pathlib import Path

CORRECTIONS = (
    "20261116231106_v6_activity_projection_compatibility.sql",
    "20261116231107_v6_reviewed_privilege_closure.sql",
)
SIGNATURES = (
    (1, "public.get_checkin_plan_proposal(uuid)"),
    (2, "public.create_activity_summary_v2(uuid,text,jsonb)"),
    (2, "public.get_workout_registration(uuid)"),
    (2, "public.confirm_workout_registration(uuid,uuid,integer,text)"),
    (2, "public.get_v6_weekly_plan(uuid,integer)"),
    (3, "public.get_v6_mobile_weekly_plan(uuid,integer)"),
    (3, "public.get_v6_mobile_calendar(date,date)"),
    (3, "public.get_v6_move_workout_context(uuid)"),
    (3, "private.v6_revision_workouts(uuid)"),
    (3, "public.get_frequency_preferences()"),
    (3, "public.save_frequency_preferences(integer,uuid,jsonb)"),
    (3, "public.report_frequency_interruption(uuid,text,text)"),
    (3, "public.get_v6_frequency_swipe_receipt(uuid)"),
)
SERVICE_ADDITIONS = (
    "private.v6_revision_workouts(uuid)",
    "public.complete_activity_rpe_v2(uuid,uuid,jsonb)",
    "public.create_v6_frequency_swipe_draft(uuid,jsonb)",
    "public.create_v6_frequency_swipe_proposal(uuid,jsonb)",
    "public.create_v6_weekly_plan_proposal(uuid,jsonb)",
    "public.create_weekly_plan_proposal_v4(uuid,jsonb)",
    "public.get_activity_processing_context_v2(uuid,uuid)",
    "public.get_activity_presentation_v2(uuid)",
    "public.get_inactive_v6_catalog_for_planning()",
    "public.get_plan_load_history_for_planning_v16(uuid,date)",
    "public.get_v6_edit_retry(uuid,text)",
    "public.get_v6_frequency_context(uuid,date,text)",
    "public.get_v6_mobile_edit_retry(uuid,text)",
    "public.get_v6_plan_context_for_planning(uuid,uuid,integer)",
    "public.move_v6_planned_workout(uuid,jsonb)",
    "public.update_v6_frequency_swipe_draft(uuid,uuid,integer,jsonb)",
)


def privilege_snapshot(suffix: str) -> str:
    if suffix not in {"before", "after"}:
        raise ValueError("Unexpected snapshot")
    return """
create temporary table readiness_service_SUFFIX on commit drop as
select replace(n.nspname||'.'||p.proname||'('||
  oidvectortypes(p.proargtypes)||')',' ','') as signature
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname in ('public','private') and p.prokind='f'
and has_function_privilege('service_role',p.oid,'EXECUTE');
create temporary table readiness_tables_SUFFIX on commit drop as
select n.nspname,c.relname,role_name,privilege
from pg_class c join pg_namespace n on n.oid=c.relnamespace
cross join (values('anon'),('authenticated'),('service_role')) roles(role_name)
cross join (values('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),
 ('REFERENCES'),('TRIGGER'),('MAINTAIN')) privileges(privilege)
where n.nspname in ('public','private') and c.relkind in ('r','v')
and has_table_privilege(role_name,c.oid,privilege);
create temporary table readiness_defaults_SUFFIX on commit drop as
select r.rolname,n.nspname,d.defaclobjtype,a.grantee,
 a.privilege_type,a.is_grantable
from pg_default_acl d join pg_roles r on r.oid=d.defaclrole
left join pg_namespace n on n.oid=d.defaclnamespace
cross join lateral aclexplode(d.defaclacl) a;
create temporary table readiness_role_powers_SUFFIX on commit drop as
select rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,
 rolreplication,rolbypassrls from pg_roles
where rolname in ('anon','authenticated','service_role');
create temporary table readiness_memberships_SUFFIX on commit drop as
select role.rolname as granted_role,member.rolname as member,
 grantor.rolname as grantor,m.admin_option,m.inherit_option,m.set_option
from pg_auth_members m join pg_roles role on role.oid=m.roleid
join pg_roles member on member.oid=m.member
join pg_roles grantor on grantor.oid=m.grantor;
create temporary table readiness_schemas_SUFFIX on commit drop as
select n.nspname,role_name,has_schema_privilege(role_name,n.oid,'USAGE') as usage,
 has_schema_privilege(role_name,n.oid,'CREATE') as creation
from pg_namespace n
cross join (values('anon'),('authenticated'),('service_role')) roles(role_name)
where n.nspname in ('public','private');
""".replace("SUFFIX", suffix)


def infrastructure_guard() -> str:
    services = json.dumps(SERVICE_ADDITIONS)
    return (
        privilege_snapshot("after")
        + """
do $infrastructure$ begin
if exists(select * from readiness_role_powers_before
 except select * from readiness_role_powers_after)
or exists(select * from readiness_role_powers_after
 except select * from readiness_role_powers_before)
or exists(select * from readiness_memberships_before
 except select * from readiness_memberships_after)
or exists(select * from readiness_memberships_after
 except select * from readiness_memberships_before) then
 raise exception 'Unexpected role powers or membership'; end if;
if exists(select * from readiness_schemas_before
 except select * from readiness_schemas_after)
or exists(select * from readiness_schemas_after
 except select * from readiness_schemas_before) then
 raise exception 'Unexpected application schema authority'; end if;
if exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 cross join lateral aclexplode(p.proacl) a
 where n.nspname in ('public','private') and a.is_grantable
 and pg_get_userbyid(a.grantee) in ('anon','authenticated','service_role'))
or exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 cross join lateral aclexplode(c.relacl) a
 where n.nspname in ('public','private') and a.is_grantable
 and pg_get_userbyid(a.grantee) in ('anon','authenticated','service_role'))
or exists(select 1 from pg_namespace n cross join lateral aclexplode(n.nspacl) a
 where n.nspname in ('public','private') and a.is_grantable
 and pg_get_userbyid(a.grantee) in ('anon','authenticated','service_role')) then
 raise exception 'Unreviewed privilege grant options'; end if;
if exists(select signature from readiness_service_after
 except select signature from readiness_service_before
 except select jsonb_array_elements_text('SERVICES'::jsonb))
or exists(select signature from readiness_service_before
 except select signature from readiness_service_after) then
 raise exception 'Unexpected server EXECUTE delta'; end if;
if exists(select * from (select * from readiness_tables_after
 except select * from readiness_tables_before) d where not
 (d.role_name='service_role' and d.nspname='private'
 and d.relname in ('realized_v2_activity_inputs','realized_v2_calculations',
 'workout_registration_events','realized_v2_plan_evidence')
 and d.privilege in ('SELECT','INSERT')))
or exists(select * from (select * from readiness_tables_before
 except select * from readiness_tables_after) d where not
 (d.role_name='service_role' and d.nspname='public'
 and d.relname in ('workout_templates','workout_segments',
 'workout_template_phase_tags','workout_template_zone_requirements')
 and d.privilege in ('TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'))) then
 raise exception 'Unexpected table privilege delta'; end if;
if exists(select * from readiness_defaults_after
 except select * from readiness_defaults_before)
or exists(select * from (select * from readiness_defaults_before
 except select * from readiness_defaults_after) d where not
 (d.rolname='postgres' and d.nspname='public' and d.defaclobjtype='r'
 and pg_get_userbyid(d.grantee) in ('anon','authenticated','service_role')
 and d.privilege_type in ('TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'))) then
 raise exception 'Unexpected default ACL delta'; end if;
end; $infrastructure$;
""".replace("SERVICES", services)
    )


def reviewed_exceptions(path: Path | None) -> tuple[tuple[int, str], ...]:
    if path is None:
        return ()
    expected = {
        "version": 1,
        "status": "PROPOSED_REQUIRES_OWNER_APPROVAL",
        "production_execution_approved": False,
        "exceptions": [
            {"role": "authenticated", "signature": s, "introduced_in_group": g}
            for g, s in SIGNATURES
        ],
    }
    if json.loads(path.read_text(encoding="utf-8")) != expected:
        raise RuntimeError("Only the exact reviewed proposed allowlist is supported")
    return SIGNATURES


def permission_guard(exceptions: tuple[tuple[int, str], ...], group: int) -> str:
    allowed = [s for g, s in exceptions if g == group]
    payload = json.dumps(allowed).replace("'", "''")
    return """
-- Exact delta only: no anonymous exception; removed historical rights also STOP.
create temporary table readiness_client_execute_after on commit drop as
select replace(n.nspname||'.'||p.proname||'('||
  oidvectortypes(p.proargtypes)||')',' ','') as signature,
role_name from pg_proc p join pg_namespace n on n.oid=p.pronamespace
cross join (values ('anon'),('authenticated')) roles(role_name)
where n.nspname in ('public','private') and p.prokind='f'
and has_function_privilege(role_name,p.oid,'EXECUTE');
do $exact_execute$ begin
if exists(select 1 from readiness_client_execute_after a
  where not exists(select 1 from readiness_client_execute_before b
    where b.signature=a.signature and b.role_name=a.role_name)
  and (a.role_name<>'authenticated' or not a.signature in
    (select jsonb_array_elements_text('PAYLOAD'::jsonb))))
or exists(select 1 from readiness_client_execute_before b
  where not exists(select 1 from readiness_client_execute_after a
    where a.signature=b.signature and a.role_name=b.role_name))
or exists(select 1 from jsonb_array_elements_text('PAYLOAD'::jsonb) e(signature)
  where not exists(select 1 from readiness_client_execute_after a
    where a.signature=e.signature and a.role_name='authenticated'))
then raise exception 'Unexpected client EXECUTE delta; exact approval required';
end if;
end; $exact_execute$;
""".replace("PAYLOAD", payload)
