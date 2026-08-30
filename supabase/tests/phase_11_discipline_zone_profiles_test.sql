begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(24);

select has_table(
  'public', 'discipline_test_assignments',
  'discipline test assignments are persisted'
);
select has_column(
  'public', 'discipline_test_assignments', 'scheduled_date',
  'test assignments store an athlete-local date'
);
select col_type_is(
  'public', 'discipline_test_assignments', 'scheduled_date', 'date',
  'test scheduling is date-only'
);
select ok(
  (select relrowsecurity and relforcerowsecurity
   from pg_class where oid = 'public.discipline_test_assignments'::regclass),
  'owner test assignments have forced RLS'
);
select has_trigger(
  'public', 'discipline_test_assignments',
  'discipline_test_assignments_require_rpc',
  'critical test assignment writes require a guarded RPC'
);
select has_trigger(
  'public', 'change_proposals',
  'change_proposals_sync_integrated_test_assignment',
  'plan decisions synchronize integrated test state'
);
select has_trigger(
  'public', 'change_proposals',
  'change_proposals_require_integrated_test_assignment',
  'a field-test plan cannot be applied without its typed assignment'
);

select has_function(
  'public', 'create_validation_test_proposal', array['jsonb'],
  'standalone tests use a pending validation proposal'
);
select has_function(
  'public', 'save_integrated_test_assignment', array['jsonb'],
  'integrated tests bind to a pending plan revision'
);
select has_function(
  'public', 'approve_validation_test_proposal', array['uuid', 'bigint'],
  'standalone test approval is stale-safe'
);
select has_function(
  'public', 'reject_validation_test_proposal', array['uuid'],
  'standalone test rejection is explicit'
);
select ok(
  not (select prosecdef from pg_proc
       where oid = 'public.create_validation_test_proposal(jsonb)'::regprocedure)
  and not (select prosecdef from pg_proc
       where oid = 'public.save_integrated_test_assignment(jsonb)'::regprocedure),
  'athlete test RPCs execute as invoker and rely on RLS'
);
select ok(
  has_function_privilege(
    'authenticated', 'public.create_validation_test_proposal(jsonb)', 'execute'
  ) and not has_function_privilege(
    'anon', 'public.create_validation_test_proposal(jsonb)', 'execute'
  ),
  'only authenticated athletes can create standalone test proposals'
);

select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'public.change_proposals'::regclass
      and conname = 'change_proposals_kind_valid'
      and pg_get_constraintdef(oid) like '%validation_test%'
  ),
  'change proposals include the typed validation-test kind'
);
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'public.discipline_test_assignments'::regclass
      and conname = 'discipline_test_assignments_target_valid'
      and pg_get_constraintdef(oid) like '%discipline <> ''swim''%'
  ),
  'integrated swim tests fail closed without an approved load contract'
);

select is(
  (select count(*)::integer from public.workout_templates
   where id in (
     '55000000-0000-0000-0000-000000000009',
     '55000000-0000-0000-0000-000000000010',
     '55000000-0000-0000-0000-000000000011'
   )),
  3,
  'all duration-complete run and bike field-test templates exist'
);
select ok(
  not exists (
    select 1 from public.workout_segments
    where template_id in (
      '55000000-0000-0000-0000-000000000009',
      '55000000-0000-0000-0000-000000000010',
      '55000000-0000-0000-0000-000000000011'
    ) and (zone_number is not null or protocol_target is null)
  ),
  'field-test templates use reviewed protocol targets and no fabricated zones'
);
select is(
  (select intensity_bucket from public.workout_templates
   where id = '55000000-0000-0000-0000-000000000010'),
  'high',
  'exact FTP low/high duration tie is owned by high intensity'
);
select ok(
  position(
    '''rpe_target''' in pg_get_functiondef(
      'private.set_planned_workout_segment_targets()'::regprocedure
    )
  ) > 0,
  'zone-free planned snapshots receive an explicit RPE target'
);

select has_function(
  'public', 'save_rpe_heart_rate_observation',
  array['uuid', 'uuid', 'smallint'],
  'RPE completion has a bounded bpm-observation RPC'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.save_rpe_heart_rate_observation(uuid,uuid,smallint)',
    'execute'
  ) and not has_function_privilege(
    'authenticated',
    'public.save_rpe_heart_rate_observation(uuid,uuid,smallint)',
    'execute'
  ),
  'only the backend can write completion-time heart-rate observations'
);
select has_function(
  'public', 'save_measured_calculated_zone_profile', array['uuid', 'jsonb'],
  'physician/lab threshold provenance has a bounded persistence RPC'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.save_measured_calculated_zone_profile(uuid,jsonb)',
    'execute'
  ) and not has_function_privilege(
    'authenticated',
    'public.save_measured_calculated_zone_profile(uuid,jsonb)',
    'execute'
  ),
  'only deterministic backend calculation can persist measured provenance'
);
select ok(
  exists (
    select 1 from pg_constraint
    where conrelid = 'public.zone_profile_versions'::regclass
      and conname = 'zone_profile_calculated_metadata_valid'
      and pg_get_constraintdef(oid) like '%measured_lab%'
  ),
  'calculated pending profiles preserve measured-lab source quality'
);

select * from finish();
rollback;
