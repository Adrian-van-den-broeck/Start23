begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_column(
  'public', 'workout_segments', 'protocol_target',
  'planned workout segments support zone-independent protocol targets'
);

select ok(
  not (
    select attnotnull
    from pg_attribute
    where attrelid = 'public.workout_segments'::regclass
      and attname = 'zone_number'
  ),
  'zone_number is nullable when a protocol target is present'
);

select ok(
  exists (
    select 1
    from pg_constraint
    where conrelid = 'public.workout_segments'::regclass
      and conname = 'workout_segments_exactly_one_target'
  ),
  'the database requires exactly one zone or protocol target'
);

select ok(
  exists (
    select 1
    from public.workout_templates template
    where template.id = '54000000-0000-0000-0000-000000000008'
      and not exists (
        select 1 from public.workout_template_zone_requirements requirement
        where requirement.template_id = template.id
      )
      and exists (
        select 1 from public.workout_segments segment
        where segment.template_id = template.id
          and segment.zone_number is null
          and segment.protocol_target ->> 'protocol_id' =
            'start23_week1_bike_calibration_v1'
          and not (segment.protocol_target::text ilike '%tss%')
      )
  ),
  'the reviewed bike calibration is plannable without zones or TSS'
);

select ok(
  exists (
    select 1
    from pg_constraint
    where conrelid = 'public.provider_connections'::regclass
      and conname = 'provider_connections_status_valid'
      and pg_get_constraintdef(oid) like '%reconnect_required%'
  ),
  'provider connections expose reconnect_required'
);

select has_column(
  'public', 'import_runs', 'next_attempt_at',
  'imports persist the next bounded retry instant'
);

select ok(
  not (
    select prosecdef
    from pg_proc
    where oid = 'public.get_polar_connection()'::regprocedure
  ) and not (
    select prosecdef
    from pg_proc
    where oid = 'public.list_polar_imports()'::regprocedure
  ),
  'read-only Polar RPCs execute as invoker and rely on RLS'
);

select ok(
  has_function_privilege(
    'service_role', 'public.claim_due_polar_import_retries(integer)', 'execute'
  ) and not has_function_privilege(
    'authenticated', 'public.claim_due_polar_import_retries(integer)', 'execute'
  ),
  'only the backend service can claim scheduled retries'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.confirm_activity_planned_workout_match(uuid,uuid)',
    'execute'
  ) and not has_function_privilege(
    'anon',
    'public.confirm_activity_planned_workout_match(uuid,uuid)',
    'execute'
  ),
  'only an authenticated athlete can explicitly confirm an activity match'
);

select * from finish();
rollback;
