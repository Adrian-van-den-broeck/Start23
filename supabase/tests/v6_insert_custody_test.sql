-- SQL role simulation of the protected PostgreSQL ROLE state. Full table writes
-- against pending/confirmed fixtures are also exercised by verify_v6_postgres.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(3);
create temporary table v6_revision_insert_probe(planning_ruleset_version text);
create trigger custody before insert on v6_revision_insert_probe
for each row execute function private.guard_v6_generated_revision_insert();
create temporary table v6_workout_insert_probe(template_id uuid, revision_id uuid, segments jsonb);
create trigger custody before insert on v6_workout_insert_probe
for each row execute function private.set_v6_planned_workout_segments();
create temporary table v6_source_id as select template_id from private.v6_source_revisions limit 1;
grant insert on v6_revision_insert_probe, v6_workout_insert_probe to authenticated;
grant select on v6_source_id to authenticated;
set local role authenticated;
select set_config('start23.critical_write','on',true);
select throws_ok($$insert into v6_revision_insert_probe values ('joren-v6-automatic-selection-1')$$,
  '42501','trusted V6 generation required','spoofed critical context cannot create a V6 revision');
select throws_ok($$insert into v6_workout_insert_probe(template_id)
  select template_id from v6_source_id$$,
  '42501','trusted V6 generation required','spoofed critical context cannot insert a V6 workout');
select lives_ok($$insert into v6_revision_insert_probe values ('joren-planning-ruleset-2')$$,
  'historical revision dispatch remains unchanged');
reset role;
select * from finish();
rollback;
