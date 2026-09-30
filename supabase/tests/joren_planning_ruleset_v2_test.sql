begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1' and version = 1),
  154::bigint,
  'historical source templates remain immutable and attributable'
);
select is(
  (select count(*) from public.workout_templates
   where source_catalog = 'start23-v0.1' and version = 2
     and not athlete_selection_only),
  154::bigint,
  'all reviewed source templates have normal deck-eligible successors'
);
select is(
  (select count(*) from public.workout_templates newer
   join public.workout_templates older
     on older.template_key = newer.template_key and older.version = 1
   where newer.source_catalog = 'start23-v0.1' and newer.version = 2
     and newer.source_workout_id = older.source_workout_id),
  154::bigint,
  'new catalog versions retain exact source identity'
);
select is(
  (select count(*) from public.workout_template_phase_tags tag
   join public.workout_templates template on template.id = tag.template_id
   where template.source_catalog = 'start23-v0.1' and template.version = 2
     and tag.phase in ('base', 'recovery', 'taper')
     and exists (
       select 1 from public.workout_segments segment
       where segment.template_id = template.id and segment.zone_number > 2
     )),
  0::bigint,
  'base, recovery and taper do not include source work above Z2'
);
select is(
  (select count(*) from private.workout_template_loads newer
   join public.workout_templates template on template.id = newer.template_id
   join public.workout_templates old_template
     on old_template.template_key = template.template_key
    and old_template.version = 1
   join private.workout_template_loads older
     on older.template_id = old_template.id
   where template.source_catalog = 'start23-v0.1' and template.version = 2
     and newer.planned_tss = older.planned_tss
     and newer.ruleset_version = older.ruleset_version),
  154::bigint,
  'reviewed source load provenance is preserved across versions'
);

select has_column('public', 'plan_revisions', 'planning_ruleset_version',
  'planning ruleset provenance is stored separately from Phase 13 load');
select has_column('public', 'plan_revisions', 'cross_training_opt_ins',
  'structured cross-training consent is retained on the revision');
select has_column('public', 'swipe_week_drafts', 'current_occurrence_id',
  'current swipe card has a distinct occurrence identity');
select has_column('public', 'swipe_week_drafts', 'accepted_occurrence_ids',
  'accepted occurrences are stored separately from templates');
select has_column('public', 'swipe_week_drafts', 'passed_occurrence_ids',
  'passed occurrences are stored separately from templates');
select has_trigger('public', 'swipe_week_drafts',
  'swipe_week_drafts_validate_v2', 'new swipe state is database validated');
select ok(
  (select relrowsecurity and relforcerowsecurity from pg_class
   where oid = 'public.swipe_week_drafts'::regclass),
  'owner-scoped swipe RLS remains forced'
);
select is(
  (select count(*)::integer from information_schema.columns
   where table_schema = 'public' and table_name = 'swipe_week_drafts'
     and lower(column_name) like '%tss%'),
  0,
  'swipe state contains no private load column'
);
select ok(
  has_function_privilege(
    'service_role', 'public.create_swipe_week_draft_v2(uuid,jsonb)', 'execute')
  and not has_function_privilege(
    'authenticated', 'public.create_swipe_week_draft_v2(uuid,jsonb)', 'execute'),
  'only the trusted backend can create a new-ruleset draft'
);
select ok(
  has_function_privilege(
    'service_role', 'public.create_weekly_plan_proposal_v3(uuid,jsonb)', 'execute')
  and not has_function_privilege(
    'authenticated', 'public.create_weekly_plan_proposal_v3(uuid,jsonb)', 'execute'),
  'only the trusted backend can create a new-ruleset proposal'
);
select ok(
  has_function_privilege(
    'service_role', 'public.get_plan_load_history_for_planning_v14(uuid,date)',
    'execute')
  and not has_function_privilege(
    'authenticated', 'public.get_plan_load_history_for_planning_v14(uuid,date)',
    'execute'),
  'per-sport historical load remains service-private'
);

select * from finish();
rollback;
