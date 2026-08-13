-- Phase 8.5: explicit zone setup, immutable calibration observations, and
-- fail-closed deterministic field-test evaluation persistence.

create table public.discipline_zone_setups (
  athlete_id uuid not null references auth.users (id) on delete cascade,
  discipline text not null,
  setup_route text not null,
  guidance_mode text not null,
  setup_status text not null,
  protocol_id text,
  pool_length_meters smallint,
  threshold_status text not null,
  zone_status text not null,
  source text not null,
  validation_status text not null,
  confidence text not null,
  known_thresholds jsonb not null default '[]'::jsonb,
  known_zone_profiles jsonb not null default '[]'::jsonb,
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  primary key (athlete_id, discipline),
  constraint discipline_zone_setups_discipline_valid
    check (discipline in ('swim', 'bike', 'run')),
  constraint discipline_zone_setups_route_valid
    check (
      setup_route in (
        'known_values', 'field_test', 'calibration_week', 'rpe_only'
      )
    ),
  constraint discipline_zone_setups_guidance_valid
    check (
      (discipline = 'swim' and guidance_mode in ('pace', 'rpe_only'))
      or (
        discipline = 'bike'
        and guidance_mode in ('power', 'heart_rate', 'combined', 'rpe_only')
      )
      or (
        discipline = 'run'
        and guidance_mode in ('heart_rate', 'pace', 'combined', 'rpe_only')
      )
    ),
  constraint discipline_zone_setups_status_valid
    check (setup_status in ('configured', 'test_pending', 'calibration_pending')),
  constraint discipline_zone_setups_threshold_status_valid
    check (threshold_status in ('unknown', 'user_provided')),
  constraint discipline_zone_setups_zone_status_valid
    check (zone_status in ('unknown', 'user_provided', 'pending_protocol')),
  constraint discipline_zone_setups_source_valid
    check (source in ('user_provided', 'field_test', 'week1_calibration', 'none')),
  constraint discipline_zone_setups_validation_valid
    check (validation_status in ('self_reported', 'not_assessed')),
  constraint discipline_zone_setups_confidence_valid
    check (confidence in ('not_assessed', 'low', 'medium')),
  constraint discipline_zone_setups_pool_valid
    check (
      pool_length_meters is null
      or (discipline = 'swim' and pool_length_meters in (25, 50))
    ),
  constraint discipline_zone_setups_json_valid
    check (
      jsonb_typeof(known_thresholds) = 'array'
      and jsonb_typeof(known_zone_profiles) = 'array'
      and jsonb_array_length(known_thresholds) <= 2
      and jsonb_array_length(known_zone_profiles) <= 2
    ),
  constraint discipline_zone_setups_revision_positive check (revision > 0),
  constraint discipline_zone_setups_route_consistent
    check (
      (
        setup_route = 'known_values'
        and setup_status = 'configured'
        and protocol_id is null
        and source = 'user_provided'
        and validation_status = 'self_reported'
        and jsonb_array_length(known_thresholds)
          + jsonb_array_length(known_zone_profiles) > 0
        and threshold_status = case
          when jsonb_array_length(known_thresholds) > 0
            then 'user_provided'
          else 'unknown'
        end
        and zone_status = case
          when jsonb_array_length(known_zone_profiles) > 0
            then 'user_provided'
          else 'pending_protocol'
        end
      )
      or (
        setup_route = 'field_test'
        and setup_status = 'test_pending'
        and protocol_id is not null
        and source = 'field_test'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
      or (
        setup_route = 'calibration_week'
        and setup_status = 'calibration_pending'
        and protocol_id is not null
        and source = 'week1_calibration'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
      or (
        setup_route = 'rpe_only'
        and guidance_mode = 'rpe_only'
        and setup_status = 'configured'
        and protocol_id is null
        and source = 'none'
        and validation_status = 'not_assessed'
        and threshold_status = 'unknown'
        and zone_status = 'unknown'
        and known_thresholds = '[]'::jsonb
        and known_zone_profiles = '[]'::jsonb
      )
    ),
  constraint discipline_zone_setups_protocol_valid
    check (
      protocol_id is null
      or (
        discipline = 'run'
        and protocol_id in (
          'start23_run_threshold_30min_v1',
          'start23_week1_run_calibration_v1'
        )
      )
      or (
        discipline = 'bike'
        and protocol_id in (
          'start23_bike_ftp_30min_v1',
          'start23_bike_fthr_20min_v1',
          'start23_week1_bike_calibration_v1'
        )
      )
      or (
        discipline = 'swim'
        and protocol_id in (
          'start23_swim_css_400_200_v1',
          'start23_week1_swim_calibration_v1'
        )
      )
    ),
  constraint discipline_zone_setups_swim_pool_required
    check (
      discipline <> 'swim'
      or setup_route not in ('field_test', 'calibration_week')
      or pool_length_meters in (25, 50)
    )
);

create table public.calibration_observations (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  activity_id uuid not null,
  planned_workout_id uuid,
  protocol_id text not null,
  discipline text not null,
  segment_id text not null,
  performed_at timestamptz not null,
  payload jsonb not null,
  fingerprint text not null,
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (athlete_id, protocol_id, activity_id, segment_id),
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id),
  foreign key (planned_workout_id, athlete_id)
    references public.planned_workouts (id, athlete_id),
  constraint calibration_observations_discipline_valid
    check (discipline in ('swim', 'bike', 'run')),
  constraint calibration_observations_fingerprint_valid
    check (fingerprint ~ '^[a-f0-9]{32}$'),
  constraint calibration_observations_payload_valid
    check (
      jsonb_typeof(payload) = 'object'
      and payload ?& array[
        'activity_id',
        'protocol_id',
        'discipline',
        'segment_id',
        'performed_at',
        'completed',
        'interrupted',
        'quality_status',
        'target_rpe'
      ]
      and (payload ->> 'activity_id')::uuid = activity_id
      and payload ->> 'protocol_id' = protocol_id
      and payload ->> 'discipline' = discipline
      and payload ->> 'segment_id' = segment_id
      and (payload ->> 'performed_at')::timestamptz = performed_at
      and not payload ?| array[
        'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
        'realized_tss', 'private_load', 'load'
      ]
    ),
  constraint calibration_observations_protocol_segment_valid
    check (
      (
        discipline = 'run'
        and (
          (
            protocol_id = 'start23_run_threshold_30min_v1'
            and segment_id in ('warmup', 'strides', 'test_30min', 'cooldown')
          )
          or (
            protocol_id = 'start23_week1_run_calibration_v1'
            and segment_id in (
              'warmup', 'comfortable_20min', 'steady_8min_optional', 'cooldown'
            )
          )
        )
      )
      or (
        discipline = 'bike'
        and (
          (
            protocol_id = 'start23_bike_ftp_30min_v1'
            and segment_id in ('warmup', 'test_30min', 'cooldown')
          )
          or (
            protocol_id = 'start23_bike_fthr_20min_v1'
            and segment_id in ('warmup', 'test_20min', 'cooldown')
          )
          or (
            protocol_id = 'start23_week1_bike_calibration_v1'
            and segment_id in (
              'warmup', 'comfortable_20min', 'steady_10min_optional', 'cooldown'
            )
          )
        )
      )
      or (
        discipline = 'swim'
        and (
          (
            protocol_id = 'start23_swim_css_400_200_v1'
            and segment_id in (
              'warmup', 'tt_400m', 'active_recovery', 'tt_200m', 'cooldown'
            )
          )
          or (
            protocol_id = 'start23_week1_swim_calibration_v1'
            and segment_id in (
              'warmup', '4x200_comfortable', '4x100_steady', 'cooldown'
            )
          )
        )
      )
    )
);

create index calibration_observations_owner_activity_idx
on public.calibration_observations (athlete_id, activity_id, protocol_id);

create index calibration_observations_activity_owner_idx
on public.calibration_observations (activity_id, athlete_id);

create index calibration_observations_workout_owner_idx
on public.calibration_observations (planned_workout_id, athlete_id)
where planned_workout_id is not null;

create table public.calibration_evaluations (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  activity_id uuid not null,
  protocol_id text not null,
  discipline text not null,
  ruleset_version text not null,
  status text not null,
  threshold_status text not null,
  zone_status text not null,
  confidence text not null,
  reason_codes text[] not null,
  thresholds jsonb not null,
  requires_athlete_confirmation boolean not null,
  review_status text not null,
  fingerprint text not null,
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (athlete_id, fingerprint),
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id),
  constraint calibration_evaluations_ruleset_valid
    check (ruleset_version = 'start23-calibration-ruleset-v1'),
  constraint calibration_evaluations_status_valid
    check (
      status in (
        'insufficient_data',
        'rpe_only',
        'provisionally_calibrated',
        'threshold_estimated',
        'insufficient_protocol'
      )
    ),
  constraint calibration_evaluations_threshold_status_valid
    check (threshold_status in ('unknown', 'threshold_estimated')),
  constraint calibration_evaluations_zone_status_valid
    check (zone_status in ('unknown', 'provisionally_calibrated', 'pending_protocol')),
  constraint calibration_evaluations_confidence_valid
    check (confidence in ('not_assessed', 'low', 'medium')),
  constraint calibration_evaluations_reasons_present
    check (cardinality(reason_codes) > 0),
  constraint calibration_evaluations_thresholds_valid
    check (jsonb_typeof(thresholds) = 'array'),
  constraint calibration_evaluations_review_valid
    check (review_status in ('pending_athlete_confirmation', 'not_applicable')),
  constraint calibration_evaluations_fingerprint_valid
    check (fingerprint ~ '^[a-f0-9]{64}$'),
  constraint calibration_evaluations_pending_consistent
    check (
      (
        status = 'threshold_estimated'
        and threshold_status = 'threshold_estimated'
        and zone_status = 'pending_protocol'
        and confidence = 'medium'
        and jsonb_array_length(thresholds) > 0
        and requires_athlete_confirmation
        and review_status = 'pending_athlete_confirmation'
        and 'zone_model_not_approved' = any(reason_codes)
      )
      or (
        status <> 'threshold_estimated'
        and threshold_status = 'unknown'
        and jsonb_array_length(thresholds) = 0
        and not requires_athlete_confirmation
        and review_status = 'not_applicable'
      )
    ),
  constraint calibration_evaluations_protocol_valid
    check (
      (
        discipline = 'run'
        and protocol_id in (
          'start23_run_threshold_30min_v1',
          'start23_week1_run_calibration_v1'
        )
      )
      or (
        discipline = 'bike'
        and protocol_id in (
          'start23_bike_ftp_30min_v1',
          'start23_bike_fthr_20min_v1',
          'start23_week1_bike_calibration_v1'
        )
      )
      or (
        discipline = 'swim'
        and protocol_id in (
          'start23_swim_css_400_200_v1',
          'start23_week1_swim_calibration_v1'
        )
      )
    ),
  constraint calibration_evaluations_submaximal_no_threshold
    check (
      protocol_id not in (
        'start23_week1_run_calibration_v1',
        'start23_week1_bike_calibration_v1',
        'start23_week1_swim_calibration_v1'
      )
      or status <> 'threshold_estimated'
    )
);

create index calibration_evaluations_owner_created_idx
on public.calibration_evaluations (athlete_id, created_at desc);

create index calibration_evaluations_activity_owner_idx
on public.calibration_evaluations (activity_id, athlete_id);

create function private.set_discipline_zone_setup_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.athlete_id is distinct from old.athlete_id
     or new.discipline is distinct from old.discipline then
    raise exception 'discipline setup identity is immutable'
      using errcode = '23514';
  end if;
  new.revision := old.revision + 1;
  new.created_at := old.created_at;
  new.updated_at := statement_timestamp();
  return new;
end;
$$;

revoke execute on function private.set_discipline_zone_setup_metadata()
from public, anon, authenticated, service_role;

create trigger discipline_zone_setups_set_metadata
before update on public.discipline_zone_setups
for each row execute function private.set_discipline_zone_setup_metadata();

create function private.reject_calibration_record_mutation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  raise exception 'calibration records are immutable' using errcode = '42501';
end;
$$;

revoke execute on function private.reject_calibration_record_mutation()
from public, anon, authenticated, service_role;

create trigger calibration_observations_are_immutable
before update or delete on public.calibration_observations
for each row execute function private.reject_calibration_record_mutation();

create trigger calibration_evaluations_are_immutable
before update or delete on public.calibration_evaluations
for each row execute function private.reject_calibration_record_mutation();

create trigger discipline_zone_setups_require_rpc
before insert or update or delete on public.discipline_zone_setups
for each row execute function private.require_critical_write_context();

create trigger calibration_observations_require_rpc
before insert or delete on public.calibration_observations
for each row execute function private.require_critical_write_context();

create trigger calibration_evaluations_require_rpc
before insert or delete on public.calibration_evaluations
for each row execute function private.require_critical_write_context();

alter table public.discipline_zone_setups enable row level security;
alter table public.discipline_zone_setups force row level security;
alter table public.calibration_observations enable row level security;
alter table public.calibration_observations force row level security;
alter table public.calibration_evaluations enable row level security;
alter table public.calibration_evaluations force row level security;

revoke all on table public.discipline_zone_setups
from public, anon, authenticated, service_role;
revoke all on table public.calibration_observations
from public, anon, authenticated, service_role;
revoke all on table public.calibration_evaluations
from public, anon, authenticated, service_role;

grant select, insert, update
on table public.discipline_zone_setups to authenticated;
grant select, insert
on table public.calibration_observations to authenticated;
grant select
on table public.calibration_evaluations to authenticated;

create policy discipline_zone_setups_select_own
on public.discipline_zone_setups for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy discipline_zone_setups_insert_own
on public.discipline_zone_setups for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy discipline_zone_setups_update_own
on public.discipline_zone_setups for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy calibration_observations_select_own
on public.calibration_observations for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy calibration_observations_insert_own
on public.calibration_observations for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy calibration_evaluations_select_own
on public.calibration_evaluations for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create function public.save_discipline_zone_setup(p_setup jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_setup public.discipline_zone_setups;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_setup) <> 'object'
     or not p_setup ?& array[
       'discipline', 'setup_route', 'guidance_mode', 'setup_status',
       'threshold_status', 'zone_status', 'source', 'validation_status',
       'confidence', 'known_thresholds', 'known_zone_profiles'
     ]
     or p_setup ?| array[
       'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ] then
    raise exception 'invalid discipline setup payload' using errcode = '23514';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':' || (p_setup ->> 'discipline'), 0)
  );
  perform set_config('start23.critical_write', 'on', true);

  insert into public.discipline_zone_setups (
    athlete_id,
    discipline,
    setup_route,
    guidance_mode,
    setup_status,
    protocol_id,
    pool_length_meters,
    threshold_status,
    zone_status,
    source,
    validation_status,
    confidence,
    known_thresholds,
    known_zone_profiles
  )
  values (
    v_athlete_id,
    p_setup ->> 'discipline',
    p_setup ->> 'setup_route',
    p_setup ->> 'guidance_mode',
    p_setup ->> 'setup_status',
    p_setup ->> 'protocol_id',
    (p_setup ->> 'pool_length_meters')::smallint,
    p_setup ->> 'threshold_status',
    p_setup ->> 'zone_status',
    p_setup ->> 'source',
    p_setup ->> 'validation_status',
    p_setup ->> 'confidence',
    p_setup -> 'known_thresholds',
    p_setup -> 'known_zone_profiles'
  )
  on conflict (athlete_id, discipline) do update
  set
    setup_route = excluded.setup_route,
    guidance_mode = excluded.guidance_mode,
    setup_status = excluded.setup_status,
    protocol_id = excluded.protocol_id,
    pool_length_meters = excluded.pool_length_meters,
    threshold_status = excluded.threshold_status,
    zone_status = excluded.zone_status,
    source = excluded.source,
    validation_status = excluded.validation_status,
    confidence = excluded.confidence,
    known_thresholds = excluded.known_thresholds,
    known_zone_profiles = excluded.known_zone_profiles
  returning * into v_setup;

  return to_jsonb(v_setup) - 'athlete_id';
end;
$$;

create function public.save_calibration_observation(
  p_observation jsonb,
  p_fingerprint text
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_existing public.calibration_observations;
  v_observation public.calibration_observations;
  v_database_fingerprint text;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_observation) <> 'object'
     or p_observation ?| array[
       'athlete_id', 'user_id', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ]
     or p_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid calibration observation payload'
      using errcode = '23514';
  end if;

  v_database_fingerprint := md5(p_observation::text);
  perform pg_advisory_xact_lock(hashtextextended(
    v_athlete_id::text || ':'
    || (p_observation ->> 'protocol_id') || ':'
    || (p_observation ->> 'activity_id') || ':'
    || (p_observation ->> 'segment_id'),
    0
  ));

  select * into v_existing
  from public.calibration_observations
  where athlete_id = v_athlete_id
    and protocol_id = p_observation ->> 'protocol_id'
    and activity_id = (p_observation ->> 'activity_id')::uuid
    and segment_id = p_observation ->> 'segment_id';

  if found then
    if v_existing.payload is distinct from p_observation then
      raise exception 'calibration observation is immutable'
        using errcode = '40001';
    end if;
    return v_existing.payload || jsonb_build_object(
      'id', v_existing.id,
      'fingerprint', v_existing.fingerprint,
      'created_at', v_existing.created_at
    );
  end if;

  if not exists (
    select 1
    from public.activities activity
    where activity.id = (p_observation ->> 'activity_id')::uuid
      and activity.athlete_id = v_athlete_id
  ) then
    raise exception 'owned activity not found' using errcode = 'P0002';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  insert into public.calibration_observations (
    athlete_id,
    activity_id,
    planned_workout_id,
    protocol_id,
    discipline,
    segment_id,
    performed_at,
    payload,
    fingerprint
  )
  values (
    v_athlete_id,
    (p_observation ->> 'activity_id')::uuid,
    (p_observation ->> 'planned_workout_id')::uuid,
    p_observation ->> 'protocol_id',
    p_observation ->> 'discipline',
    p_observation ->> 'segment_id',
    (p_observation ->> 'performed_at')::timestamptz,
    p_observation,
    v_database_fingerprint
  )
  returning * into v_observation;

  return v_observation.payload || jsonb_build_object(
    'id', v_observation.id,
    'fingerprint', v_observation.fingerprint,
    'created_at', v_observation.created_at
  );
end;
$$;

create function public.save_calibration_evaluation(
  p_athlete_id uuid,
  p_evaluation jsonb,
  p_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_existing public.calibration_evaluations;
  v_evaluation public.calibration_evaluations;
begin
  if p_athlete_id is null
     or jsonb_typeof(p_evaluation) <> 'object'
     or not p_evaluation ?& array[
       'activity_id', 'protocol_id', 'discipline', 'ruleset_version',
       'status', 'threshold_status', 'zone_status', 'confidence',
       'reason_codes', 'thresholds', 'requires_athlete_confirmation',
       'review_status'
     ]
     or p_evaluation ?| array[
       'athlete_id', 'user_id', 'boundaries', 'tss', 'rtss', 'planned_tss',
       'realized_tss', 'private_load', 'load'
     ]
     or p_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid calibration evaluation payload'
      using errcode = '23514';
  end if;
  if not exists (
    select 1
    from public.activities activity
    where activity.id = (p_evaluation ->> 'activity_id')::uuid
      and activity.athlete_id = p_athlete_id
  ) then
    raise exception 'owned activity not found' using errcode = 'P0002';
  end if;

  select * into v_existing
  from public.calibration_evaluations
  where athlete_id = p_athlete_id and fingerprint = p_fingerprint;
  if found then
    return to_jsonb(v_existing) - 'athlete_id';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  insert into public.calibration_evaluations (
    athlete_id,
    activity_id,
    protocol_id,
    discipline,
    ruleset_version,
    status,
    threshold_status,
    zone_status,
    confidence,
    reason_codes,
    thresholds,
    requires_athlete_confirmation,
    review_status,
    fingerprint
  )
  values (
    p_athlete_id,
    (p_evaluation ->> 'activity_id')::uuid,
    p_evaluation ->> 'protocol_id',
    p_evaluation ->> 'discipline',
    p_evaluation ->> 'ruleset_version',
    p_evaluation ->> 'status',
    p_evaluation ->> 'threshold_status',
    p_evaluation ->> 'zone_status',
    p_evaluation ->> 'confidence',
    array(select jsonb_array_elements_text(p_evaluation -> 'reason_codes')),
    p_evaluation -> 'thresholds',
    (p_evaluation ->> 'requires_athlete_confirmation')::boolean,
    p_evaluation ->> 'review_status',
    p_fingerprint
  )
  returning * into v_evaluation;

  return to_jsonb(v_evaluation) - 'athlete_id';
end;
$$;

-- Extend planning snapshots without changing the older base snapshot function.
create function private.build_phase_8_5_planning_input_snapshot(p_athlete_id uuid)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select private.build_planning_input_snapshot(p_athlete_id)
    || jsonb_build_object(
      'discipline_setups',
      (
        select coalesce(
          jsonb_agg(
            to_jsonb(setup) - array['athlete_id', 'created_at', 'updated_at']
            order by setup.discipline
          ),
          '[]'::jsonb
        )
        from public.discipline_zone_setups setup
        where setup.athlete_id = p_athlete_id
      )
    );
$$;

revoke execute
on function private.build_phase_8_5_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

create or replace function private.set_initial_plan_input_snapshot()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_snapshot jsonb;
  v_should_refresh boolean;
begin
  if tg_op = 'INSERT' then
    v_should_refresh := true;
  else
    v_should_refresh :=
      new.status = 'pending'
      and old.status = 'pending'
      and new.refreshed_at is distinct from old.refreshed_at;
  end if;

  if v_should_refresh then
    v_snapshot := private.build_phase_8_5_planning_input_snapshot(new.athlete_id);
    new.input_snapshot := v_snapshot;
    new.input_fingerprint := md5(v_snapshot::text);
    new.refreshed_at := statement_timestamp();
  else
    new.input_snapshot := old.input_snapshot;
    new.input_fingerprint := old.input_fingerprint;
    new.refreshed_at := old.refreshed_at;
  end if;
  return new;
end;
$$;

create trigger discipline_zone_setups_refresh_pending_planning_input
after insert or update or delete on public.discipline_zone_setups
for each row execute function private.refresh_pending_planning_input();

create or replace function public.complete_onboarding()
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_request_id uuid;
  v_revision bigint;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select initial_plan_request_id into v_request_id
  from public.onboarding_sessions
  where athlete_id = v_athlete_id and status = 'completed';
  if v_request_id is not null then
    return v_request_id;
  end if;

  if not exists (
    select 1 from public.athlete_profiles
    where athlete_id = v_athlete_id
      and date_of_birth is not null
      and height_cm is not null
      and weight_kg is not null
      and resting_heart_rate_bpm is not null
      and motivation_text is not null
  ) then
    raise exception 'profile is incomplete' using errcode = '23514';
  end if;
  if (
    select count(*) from public.training_history_entries
    where athlete_id = v_athlete_id
  ) <> 3 then
    raise exception 'training history is incomplete' using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.goals
    where athlete_id = v_athlete_id and status = 'active'
  ) then
    raise exception 'primary race goal is missing' using errcode = '23514';
  end if;
  if (
    select count(distinct configured.discipline)
    from (
      select profile.discipline
      from public.zone_profile_versions profile
      where profile.athlete_id = v_athlete_id and profile.status = 'active'
      union
      select setup.discipline
      from public.discipline_zone_setups setup
      where setup.athlete_id = v_athlete_id
        and setup.setup_status in ('configured', 'test_pending', 'calibration_pending')
    ) configured
  ) <> 3 then
    raise exception 'discipline guidance setup is incomplete' using errcode = '23514';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.athlete_profiles
  set onboarding_status = 'completed'
  where athlete_id = v_athlete_id
  returning revision into v_revision;

  select id into v_request_id
  from public.initial_plan_requests
  where athlete_id = v_athlete_id and status = 'pending';
  if v_request_id is null then
    insert into public.initial_plan_requests (
      athlete_id, onboarding_revision, ruleset_version
    ) values (v_athlete_id, v_revision, 'phase-3-ruleset-2')
    returning id into v_request_id;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps,
    initial_plan_request_id,
    completed_at
  ) values (
    v_athlete_id,
    'completed',
    'completed',
    array['profile', 'history', 'goal', 'zones', 'review']::text[],
    v_request_id,
    statement_timestamp()
  )
  on conflict (athlete_id) do update
  set
    status = 'completed',
    current_step = 'completed',
    completed_steps = array['profile', 'history', 'goal', 'zones', 'review']::text[],
    initial_plan_request_id = v_request_id,
    completed_at = statement_timestamp();

  return v_request_id;
end;
$$;

revoke all on function public.save_discipline_zone_setup(jsonb)
from public, anon, service_role;
revoke all on function public.save_calibration_observation(jsonb, text)
from public, anon, service_role;
revoke all on function public.save_calibration_evaluation(uuid, jsonb, text)
from public, anon, authenticated, service_role;

grant execute on function public.save_discipline_zone_setup(jsonb)
to authenticated;
grant execute on function public.save_calibration_observation(jsonb, text)
to authenticated;
grant execute on function public.save_calibration_evaluation(uuid, jsonb, text)
to service_role;
