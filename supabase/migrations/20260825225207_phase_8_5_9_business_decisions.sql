-- Business decisions 8.5-D2 through 9-G1. Forward-only hardening and MVP scope.

-- 8.5-D2: protocol targets are a first-class alternative to zone targets.
alter table public.workout_segments
  alter column zone_number drop not null,
  add column protocol_target jsonb;

alter table public.workout_segments
  drop constraint workout_segments_zone_number_check,
  drop constraint workout_segments_check,
  add constraint workout_segments_zone_target_valid check (
    zone_number is null or zone_number between 1 and 5
  ),
  add constraint workout_segments_exactly_one_target check (
    (zone_number is not null)::integer + (protocol_target is not null)::integer = 1
  ),
  add constraint workout_segments_protocol_target_valid check (
    protocol_target is null
    or (
      jsonb_typeof(protocol_target) = 'object'
      and protocol_target ?& array[
        'protocol_id', 'segment_id', 'target_rpe_min', 'target_rpe_max',
        'intensity_bucket', 'optional'
      ]
      and not protocol_target ?| array[
        'zone', 'zone_target', 'tss', 'planned_tss', 'realized_tss', 'load'
      ]
      and (protocol_target ->> 'protocol_id') ~ '^[a-z0-9][a-z0-9._-]{0,99}$'
      and (protocol_target ->> 'segment_id') ~ '^[a-z0-9][a-z0-9._-]{0,99}$'
      and (protocol_target ->> 'target_rpe_min')::integer between 1 and 10
      and (protocol_target ->> 'target_rpe_max')::integer between
        (protocol_target ->> 'target_rpe_min')::integer and 10
      and (protocol_target ->> 'intensity_bucket') in ('low', 'high')
      and jsonb_typeof(protocol_target -> 'optional') = 'boolean'
    )
  ),
  add constraint workout_segments_technique_target_valid check (
    not is_swim_technique
    or zone_number in (1, 2)
    or protocol_target ->> 'intensity_bucket' = 'low'
  );

create or replace function private.validate_workout_template(p_template_id uuid)
returns void
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_template public.workout_templates%rowtype;
  v_duration numeric;
  v_distance integer;
  v_segment_count integer;
  v_low_duration numeric;
  v_high_duration numeric;
begin
  select * into strict v_template
  from public.workout_templates
  where id = p_template_id;

  select
    count(*),
    sum(duration_minutes),
    sum(coalesce(distance_meters, 0)),
    sum(duration_minutes) filter (
      where is_swim_technique
         or zone_number in (1, 2)
         or protocol_target ->> 'intensity_bucket' = 'low'
    ),
    sum(duration_minutes) filter (
      where not is_swim_technique
        and (
          zone_number in (3, 4, 5)
          or protocol_target ->> 'intensity_bucket' = 'high'
        )
    )
  into
    v_segment_count, v_duration, v_distance, v_low_duration, v_high_duration
  from public.workout_segments
  where template_id = p_template_id;

  if v_segment_count = 0
    or v_duration <> v_template.duration_minutes
    or coalesce(v_distance, 0) <> coalesce(v_template.distance_meters, 0)
    or exists (
      select 1
      from generate_series(1, v_segment_count) expected(sequence)
      left join public.workout_segments segment
        on segment.template_id = p_template_id
       and segment.sequence = expected.sequence
      where segment.sequence is null
    )
    or exists (
      select 1 from public.workout_segments
      where template_id = p_template_id
        and expected_rpe not between
          v_template.expected_rpe_min and v_template.expected_rpe_max
    )
    or (
      v_template.discipline <> 'swim'
      and exists (
        select 1 from public.workout_segments
        where template_id = p_template_id and is_swim_technique
      )
    )
    or (
      case
        when coalesce(v_high_duration, 0) > coalesce(v_low_duration, 0) then 'high'
        when coalesce(v_low_duration, 0) > coalesce(v_high_duration, 0) then 'low'
        else 'unresolved'
      end
    ) <> v_template.intensity_bucket
    or not exists (
      select 1 from public.workout_template_phase_tags
      where template_id = p_template_id
    )
    or not exists (
      select 1 from private.workout_template_loads
      where template_id = p_template_id
    )
    or (
      v_template.fallback_compatibility = 'compatible'
      and exists (
        select 1 from public.workout_template_zone_requirements
        where template_id = p_template_id and requirement <> 'heart_rate'
      )
    )
  then
    raise exception 'workout template % is incomplete or inconsistent', p_template_id
      using errcode = '23514';
  end if;
end;
$$;

create or replace function public.get_workout_catalog_for_planning()
returns table (
  id uuid, template_key uuid, version integer, discipline text, name text,
  description text, duration_minutes numeric, distance_meters integer,
  intensity_bucket text, expected_rpe_min smallint, expected_rpe_max smallint,
  fallback_compatibility text, training_phases text[], zone_requirements text[],
  segments jsonb, planned_tss numeric, calculation_method text,
  ruleset_version text
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  return query
  select
    template.id, template.template_key, template.version, template.discipline,
    template.name, template.description, template.duration_minutes,
    template.distance_meters, template.intensity_bucket,
    template.expected_rpe_min, template.expected_rpe_max,
    template.fallback_compatibility,
    array(
      select tag.phase from public.workout_template_phase_tags tag
      where tag.template_id = template.id order by tag.phase
    ),
    array(
      select requirement.requirement
      from public.workout_template_zone_requirements requirement
      where requirement.template_id = template.id order by requirement.requirement
    ),
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'sequence', segment.sequence,
            'name', segment.name,
            'instructions', segment.instructions,
            'duration_minutes', segment.duration_minutes,
            'distance_meters', segment.distance_meters,
            'zone_target', segment.zone_number,
            'protocol_target', segment.protocol_target,
            'expected_rpe', segment.expected_rpe,
            'is_swim_technique', segment.is_swim_technique
          ) order by segment.sequence
        ), '[]'::jsonb
      )
      from public.workout_segments segment
      where segment.template_id = template.id
    ),
    load.planned_tss, load.calculation_method, load.ruleset_version
  from public.workout_templates template
  join private.workout_template_loads load on load.template_id = template.id
  order by template.template_key, template.version;
end;
$$;

insert into public.workout_templates (
  id, template_key, version, discipline, name, description, duration_minutes,
  distance_meters, intensity_bucket, expected_rpe_min, expected_rpe_max,
  fallback_compatibility
) values (
  '54000000-0000-0000-0000-000000000008',
  '50000000-0000-0000-0000-000000000008',
  1, 'bike', 'Week-1 fietskalibratie',
  'Submaximale fietskalibratie op protocol en RPE, zonder verzonnen zones.',
  55, null, 'low', 1, 6, 'incompatible'
);

insert into public.workout_segments (
  template_id, sequence, name, instructions, duration_minutes,
  distance_meters, zone_number, expected_rpe, is_swim_technique, protocol_target
) values
(
  '54000000-0000-0000-0000-000000000008', 1, 'Warming-up',
  'Rustig opwarmen volgens het kalibratieprotocol.', 15, null, null, 2, false,
  '{"protocol_id":"start23_week1_bike_calibration_v1","segment_id":"warmup","target_rpe_min":2,"target_rpe_max":3,"intensity_bucket":"low","optional":false}'
),
(
  '54000000-0000-0000-0000-000000000008', 2, 'Comfortabel blok',
  'Rijd comfortabel en gelijkmatig; registreer de observaties.', 20, null, null, 3, false,
  '{"protocol_id":"start23_week1_bike_calibration_v1","segment_id":"comfortable_20min","target_rpe_min":3,"target_rpe_max":4,"intensity_bucket":"low","optional":false}'
),
(
  '54000000-0000-0000-0000-000000000008', 3, 'Gestaag blok (optioneel)',
  'Voer alleen uit als het comfortabele blok goed voelde.', 10, null, null, 5, false,
  '{"protocol_id":"start23_week1_bike_calibration_v1","segment_id":"steady_10min_optional","target_rpe_min":5,"target_rpe_max":6,"intensity_bucket":"high","optional":true}'
),
(
  '54000000-0000-0000-0000-000000000008', 4, 'Cooling-down',
  'Rustig uitrijden en daarna sessie-RPE registreren.', 10, null, null, 1, false,
  '{"protocol_id":"start23_week1_bike_calibration_v1","segment_id":"cooldown","target_rpe_min":1,"target_rpe_max":2,"intensity_bucket":"low","optional":false}'
);

insert into public.workout_template_phase_tags (template_id, phase)
values ('54000000-0000-0000-0000-000000000008', 'base');

insert into private.workout_template_loads (
  template_id, planned_tss, calculation_method, ruleset_version
) values (
  '54000000-0000-0000-0000-000000000008',
  3.20833333333333333333,
  'expected_rpe_midpoint_times_duration_hours',
  'phase-3-ruleset-3'
);

select private.validate_workout_template('54000000-0000-0000-0000-000000000008');

-- Normalize every newly persisted plan snapshot to the target-union contract.
create function private.set_planned_workout_segment_targets()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  select jsonb_agg(
    jsonb_build_object(
      'sequence', segment.sequence,
      'name', segment.name,
      'instructions', segment.instructions,
      'duration_minutes', segment.duration_minutes,
      'distance_meters', segment.distance_meters,
      'zone_target', segment.zone_number,
      'protocol_target', segment.protocol_target,
      'expected_rpe', segment.expected_rpe,
      'is_swim_technique', segment.is_swim_technique
    ) order by segment.sequence
  ) into new.segments
  from public.workout_segments segment
  where segment.template_id = new.template_id;
  return new;
end;
$$;

revoke execute on function private.set_planned_workout_segment_targets()
from public, anon, authenticated, service_role;

create trigger planned_workouts_set_segment_targets
before insert on public.planned_workouts
for each row execute function private.set_planned_workout_segment_targets();

-- 9-D6: a revoked credential is distinct from an ordinary disconnect.
alter table public.provider_connections
  drop constraint provider_connections_status_valid,
  add constraint provider_connections_status_valid check (
    status in ('connected', 'disconnected', 'revoked', 'reconnect_required', 'error')
  );

create or replace function public.disconnect_polar_connection(
  p_athlete_id uuid,
  p_status text
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_connection_id uuid;
begin
  perform private.phase_9_require_service_role();
  if p_status not in ('disconnected', 'revoked', 'reconnect_required') then
    raise exception 'invalid disconnect status' using errcode = '23514';
  end if;
  select id into v_connection_id from public.provider_connections
  where athlete_id = p_athlete_id and provider = 'polar' for update;
  if not found then
    raise exception 'connection not found' using errcode = 'P0002';
  end if;
  delete from private.provider_tokens where connection_id = v_connection_id;
  update public.provider_connections set
    status = p_status,
    disconnected_at = statement_timestamp(),
    updated_at = statement_timestamp()
  where id = v_connection_id;
end;
$$;

-- 9-D5: retry state is bounded and claimable by one Railway scheduled command.
alter table public.import_runs
  add column retry_count smallint not null default 0,
  add column max_attempts smallint not null default 4,
  add column next_attempt_at timestamptz,
  add column last_attempt_at timestamptz not null default statement_timestamp(),
  add constraint import_runs_retry_bounds check (
    retry_count between 0 and max_attempts - 1 and max_attempts between 1 and 8
  ),
  add constraint import_runs_retry_schedule_valid check (
    next_attempt_at is null or status = 'failed'
  );

create index import_runs_due_retry_idx
on public.import_runs (next_attempt_at, id)
where status = 'failed' and next_attempt_at is not null;

create or replace function private.import_run_public_json(p_import_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', run.id, 'provider', run.provider, 'kind', run.kind,
    'status', run.status, 'range_start', run.range_start,
    'range_end', run.range_end, 'discovered_count', run.discovered_count,
    'imported_count', run.imported_count, 'skipped_count', run.skipped_count,
    'failure_code', run.failure_code, 'retry_count', run.retry_count,
    'max_attempts', run.max_attempts, 'next_attempt_at', run.next_attempt_at,
    'created_at', run.created_at, 'completed_at', run.completed_at
  ) from public.import_runs run where run.id = p_import_id;
$$;

create or replace function public.finish_polar_import(
  p_athlete_id uuid,
  p_import_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.phase_9_require_service_role();
  update public.import_runs set
    status = p_payload ->> 'status',
    discovered_count = (p_payload ->> 'discovered_count')::integer,
    imported_count = (p_payload ->> 'imported_count')::integer,
    skipped_count = (p_payload ->> 'skipped_count')::integer,
    failure_code = p_payload ->> 'failure_code',
    next_attempt_at = nullif(p_payload ->> 'next_attempt_at', '')::timestamptz,
    completed_at = statement_timestamp()
  where id = p_import_id and athlete_id = p_athlete_id and status = 'running';
  if not found then
    if exists (
      select 1 from public.import_runs
      where id = p_import_id and athlete_id = p_athlete_id
    ) then
      return private.import_run_public_json(p_import_id);
    end if;
    raise exception 'import not found' using errcode = 'P0002';
  end if;
  update public.provider_connections set
    last_import_at = statement_timestamp(), updated_at = statement_timestamp()
  where athlete_id = p_athlete_id and provider = 'polar';
  return private.import_run_public_json(p_import_id);
end;
$$;

create function public.prepare_polar_import_retry(
  p_athlete_id uuid,
  p_import_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.phase_9_require_service_role();
  update public.import_runs set
    status = 'running',
    failure_code = null,
    completed_at = null,
    next_attempt_at = null,
    last_attempt_at = statement_timestamp(),
    retry_count = retry_count + 1
  where id = p_import_id
    and athlete_id = p_athlete_id
    and kind = 'historical'
    and status = 'failed'
    and retry_count < max_attempts - 1;
  if not found then
    raise exception 'import is not retryable' using errcode = '40001';
  end if;
  return private.import_run_public_json(p_import_id);
end;
$$;

revoke all on function public.prepare_polar_import_retry(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.prepare_polar_import_retry(uuid, uuid) to service_role;

create function public.claim_due_polar_import_retries(p_limit integer default 20)
returns table (athlete_id uuid, import_id uuid)
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.phase_9_require_service_role();
  if p_limit not between 1 and 100 then
    raise exception 'invalid retry batch limit' using errcode = '23514';
  end if;
  return query
  with due as (
    select run.id, run.athlete_id
    from public.import_runs run
    join public.provider_connections connection
      on connection.id = run.connection_id
     and connection.athlete_id = run.athlete_id
     and connection.status = 'connected'
    where run.provider = 'polar'
      and run.kind = 'historical'
      and run.status = 'failed'
      and run.next_attempt_at <= statement_timestamp()
      and run.retry_count < run.max_attempts - 1
    order by run.next_attempt_at, run.id
    for update of run skip locked
    limit p_limit
  ), claimed as (
    update public.import_runs run set
      status = 'running', failure_code = null, completed_at = null,
      next_attempt_at = null, last_attempt_at = statement_timestamp(),
      retry_count = run.retry_count + 1
    from due
    where run.id = due.id and run.athlete_id = due.athlete_id
    returning run.athlete_id, run.id
  )
  select claimed.athlete_id, claimed.id from claimed;
end;
$$;

revoke all on function public.claim_due_polar_import_retries(integer)
from public, anon, authenticated, service_role;
grant execute on function public.claim_due_polar_import_retries(integer) to service_role;

create function public.get_polar_import_retry_context(
  p_athlete_id uuid,
  p_import_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
begin
  perform private.phase_9_require_service_role();
  select private.import_run_public_json(run.id) into v_result
  from public.import_runs run
  where run.id = p_import_id
    and run.athlete_id = p_athlete_id
    and run.kind = 'historical';
  if v_result is null then
    raise exception 'import not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_polar_import_retry_context(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_polar_import_retry_context(uuid, uuid)
to service_role;

-- 9-D10: owner reads now execute as invoker and rely on table grants plus RLS.
create or replace function public.get_polar_connection()
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_result jsonb;
begin
  select jsonb_build_object(
    'id', connection.id, 'provider', connection.provider,
    'status', connection.status, 'connected_at', connection.connected_at,
    'disconnected_at', connection.disconnected_at,
    'last_import_at', connection.last_import_at
  ) into v_result
  from public.provider_connections connection
  where connection.athlete_id = (select auth.uid()) and connection.provider = 'polar';
  if v_result is null then
    raise exception 'connection not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

create or replace function public.list_polar_imports()
returns setof jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'id', run.id, 'provider', run.provider, 'kind', run.kind,
    'status', run.status, 'range_start', run.range_start,
    'range_end', run.range_end, 'discovered_count', run.discovered_count,
    'imported_count', run.imported_count, 'skipped_count', run.skipped_count,
    'failure_code', run.failure_code, 'retry_count', run.retry_count,
    'max_attempts', run.max_attempts, 'next_attempt_at', run.next_attempt_at,
    'created_at', run.created_at, 'completed_at', run.completed_at
  )
  from public.import_runs run
  where run.athlete_id = (select auth.uid()) and run.provider = 'polar'
  order by run.created_at desc;
$$;

-- 9-D9: imported activities can only be linked by an explicit athlete action.
create function public.confirm_activity_planned_workout_match(
  p_activity_id uuid,
  p_planned_workout_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_activity public.activities;
  v_workout public.planned_workouts;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select * into v_activity from public.activities
  where id = p_activity_id and athlete_id = v_athlete_id for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.planned_workout_id is not null then
    raise exception 'activity is already matched' using errcode = '40001';
  end if;
  if v_activity.processing_state <> 'awaiting_rpe' then
    raise exception 'activity match window closed' using errcode = '40001';
  end if;
  select workout.* into v_workout
  from public.planned_workouts workout
  join public.plan_revisions revision
    on revision.id = workout.revision_id and revision.athlete_id = workout.athlete_id
  where workout.id = p_planned_workout_id
    and workout.athlete_id = v_athlete_id
    and revision.state = 'active'
    and workout.status = 'scheduled';
  if not found then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  if v_workout.discipline <> v_activity.discipline then
    raise exception 'activity discipline does not match planned workout'
      using errcode = '23514';
  end if;
  if exists (
    select 1 from public.activities
    where planned_workout_id = p_planned_workout_id
  ) then
    raise exception 'planned workout already matched' using errcode = '40001';
  end if;
  update public.activities set
    planned_workout_id = p_planned_workout_id,
    match_status = 'matched',
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = v_athlete_id;
  return private.activity_public_json(p_activity_id, v_athlete_id);
end;
$$;

revoke all on function public.confirm_activity_planned_workout_match(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.confirm_activity_planned_workout_match(uuid, uuid)
to authenticated;
