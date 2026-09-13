-- Remediation R3 foundation and R2 cutover.
--
-- This is the expand/cutover migration from R1-D4. The legacy auth UUID owner
-- columns remain only as a bounded compatibility key until the R6 database and
-- real-token verification gates authorize a later contract migration.

create table private.athlete_identity_map (
  athlete_id uuid primary key default gen_random_uuid(),
  auth_user_id uuid not null unique
    references auth.users (id)
    on delete cascade,
  creation_source text not null,
  created_at timestamptz not null default statement_timestamp(),
  backfilled_at timestamptz,

  constraint athlete_identity_map_creation_source_valid check (
    creation_source in ('auth_user_trigger', 'r3_existing_user_backfill')
  ),
  constraint athlete_identity_map_backfill_provenance check (
    (creation_source = 'auth_user_trigger' and backfilled_at is null)
    or
    (creation_source = 'r3_existing_user_backfill' and backfilled_at is not null)
  )
);

revoke all on table private.athlete_identity_map
from public, anon, authenticated, service_role;
grant select (athlete_id, auth_user_id)
on table private.athlete_identity_map to service_role;

create function private.ensure_athlete_identity_map()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into private.athlete_identity_map (
    auth_user_id,
    creation_source
  )
  values (new.id, 'auth_user_trigger')
  on conflict (auth_user_id) do nothing;
  return new;
end;
$$;

revoke execute on function private.ensure_athlete_identity_map()
from public, anon, authenticated, service_role;

create trigger start23_create_opaque_athlete_identity
after insert on auth.users
for each row execute function private.ensure_athlete_identity_map();

create function private.backfill_athlete_identity_maps()
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_inserted bigint;
begin
  insert into private.athlete_identity_map (
    auth_user_id,
    creation_source,
    backfilled_at
  )
  select
    users.id,
    'r3_existing_user_backfill',
    statement_timestamp()
  from auth.users users
  on conflict (auth_user_id) do nothing;

  get diagnostics v_inserted = row_count;
  return v_inserted;
end;
$$;

revoke execute on function private.backfill_athlete_identity_maps()
from public, anon, authenticated, service_role;

select private.backfill_athlete_identity_maps();

create function private.current_athlete_id()
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select mapping.athlete_id
  from private.athlete_identity_map mapping
  where mapping.auth_user_id = (select auth.uid())
$$;

revoke execute on function private.current_athlete_id()
from public, anon, service_role;
grant usage on schema private to authenticated;
grant execute on function private.current_athlete_id() to authenticated;

create function private.resolve_opaque_athlete_id(p_identifier uuid)
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select mapping.athlete_id
  from private.athlete_identity_map mapping
  where mapping.athlete_id = p_identifier
     or mapping.auth_user_id = p_identifier
  limit 1
$$;

revoke execute on function private.resolve_opaque_athlete_id(uuid)
from public, anon, authenticated, service_role;

create function public.get_current_athlete_id()
returns uuid
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
begin
  if v_athlete_id is null then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;
  return v_athlete_id;
end;
$$;

revoke execute on function public.get_current_athlete_id()
from public, anon, service_role;
grant execute on function public.get_current_athlete_id() to authenticated;

create function public.resolve_legacy_auth_user_id(p_athlete_id uuid)
returns uuid
language sql
stable
security invoker
set search_path = ''
as $$
  select mapping.auth_user_id
  from private.athlete_identity_map mapping
  where mapping.athlete_id = p_athlete_id
$$;

revoke execute on function public.resolve_legacy_auth_user_id(uuid)
from public, anon, authenticated;
grant execute on function public.resolve_legacy_auth_user_id(uuid) to service_role;

create function private.sync_dual_athlete_owner_keys()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_mapping private.athlete_identity_map;
begin
  if new.athlete_id is null and new.internal_athlete_id is null then
    if tg_table_schema = 'private'
       and tg_table_name = 'webhook_receipts' then
      return new;
    end if;
    raise exception 'athlete owner is required' using errcode = '23502';
  end if;

  select mapping.* into v_mapping
  from private.athlete_identity_map mapping
  where mapping.auth_user_id = new.athlete_id
     or mapping.athlete_id = new.internal_athlete_id
  order by (mapping.auth_user_id = new.athlete_id) desc
  limit 1;

  if not found then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;
  if new.athlete_id is not null
     and new.athlete_id is distinct from v_mapping.auth_user_id then
    raise exception 'legacy and opaque athlete owners do not match'
      using errcode = '23514';
  end if;
  if new.internal_athlete_id is not null
     and new.internal_athlete_id is distinct from v_mapping.athlete_id then
    raise exception 'legacy and opaque athlete owners do not match'
      using errcode = '23514';
  end if;
  if tg_op = 'UPDATE'
     and (
       new.athlete_id is distinct from old.athlete_id
       or new.internal_athlete_id is distinct from old.internal_athlete_id
     ) then
    raise exception 'athlete owner is immutable' using errcode = '23514';
  end if;

  new.athlete_id := v_mapping.auth_user_id;
  new.internal_athlete_id := v_mapping.athlete_id;
  return new;
end;
$$;

revoke execute on function private.sync_dual_athlete_owner_keys()
from public, anon, authenticated, service_role;

do $$
declare
  v_table text;
  v_schema text;
  v_name text;
  v_constraint text;
  v_index text;
begin
  foreach v_table in array array[
    'public.athlete_profiles',
    'public.onboarding_sessions',
    'public.training_history_entries',
    'public.goals',
    'public.zone_profile_versions',
    'public.zone_metrics',
    'public.zone_boundaries',
    'public.change_proposals',
    'public.initial_plan_requests',
    'public.weekly_plans',
    'public.plan_revisions',
    'public.planned_workouts',
    'public.plan_warnings',
    'private.planned_workout_loads',
    'private.plan_revision_loads',
    'public.activities',
    'public.activity_metrics',
    'private.activity_loads',
    'public.weekly_checkins',
    'public.weekly_checkin_contexts',
    'public.injury_restrictions',
    'public.planned_external_activities',
    'public.goal_maintenance_states',
    'public.activity_rpe_revisions',
    'public.discipline_zone_setups',
    'public.calibration_observations',
    'public.calibration_evaluations',
    'public.calibration_threshold_decisions',
    'public.provider_connections',
    'private.provider_tokens',
    'private.integration_oauth_states',
    'public.import_runs',
    'private.webhook_receipts',
    'private.provider_activity_imports',
    'public.activity_files',
    'public.discipline_test_assignments',
    'public.swipe_week_drafts',
    'private.phase_13_activity_load_history',
    'public.onboarding_completion_records'
  ]
  loop
    v_schema := split_part(v_table, '.', 1);
    v_name := split_part(v_table, '.', 2);
    v_constraint := left(v_name, 40) || '_opaque_athlete_fkey';
    v_index := left(v_name, 45) || '_opaque_owner_idx';

    execute format(
      'alter table %I.%I add column internal_athlete_id uuid',
      v_schema,
      v_name
    );
    execute format(
      'update %I.%I target set internal_athlete_id = mapping.athlete_id '
      || 'from private.athlete_identity_map mapping '
      || 'where target.athlete_id = mapping.auth_user_id',
      v_schema,
      v_name
    );
    if v_table <> 'private.webhook_receipts' then
      execute format(
        'alter table %I.%I alter column internal_athlete_id set not null',
        v_schema,
        v_name
      );
    end if;
    execute format(
      'alter table %I.%I add constraint %I foreign key (internal_athlete_id) '
      || 'references private.athlete_identity_map (athlete_id) on delete cascade',
      v_schema,
      v_name,
      v_constraint
    );
    execute format(
      'create index %I on %I.%I (internal_athlete_id)',
      v_index,
      v_schema,
      v_name
    );
    execute format(
      'create trigger r3_00_sync_opaque_athlete_owner before insert or update '
      || 'on %I.%I for each row execute function '
      || 'private.sync_dual_athlete_owner_keys()',
      v_schema,
      v_name
    );
  end loop;
end;
$$;

alter table private.webhook_receipts
  add constraint webhook_receipts_opaque_owner_pair_valid check (
    (event_type = 'PING' and athlete_id is null and internal_athlete_id is null)
    or (
      event_type = 'EXERCISE'
      and athlete_id is not null
      and internal_athlete_id is not null
    )
  );

-- New activity files use the opaque owner in their storage path. Existing
-- Auth-UUID paths remain readable during the bounded dual-key window and are
-- not renamed without R6 storage-object migration evidence.
alter table public.activity_files
  drop constraint activity_files_path_valid;
alter table public.activity_files
  add constraint activity_files_path_dual_owner_valid check (
    storage_object_name like internal_athlete_id::text || '/%'
    or storage_object_name like athlete_id::text || '/%'
  );

drop policy activity_files_storage_select_own on storage.objects;
create policy activity_files_storage_select_own
on storage.objects for select to authenticated
using (
  bucket_id = 'activity-files'
  and (
    (storage.foldername(name))[1] = (select private.current_athlete_id())::text
    or (storage.foldername(name))[1] = (select auth.uid())::text
  )
);

do $$
declare
  v_table text;
  v_name text;
begin
  foreach v_table in array array[
    'athlete_profiles',
    'onboarding_sessions',
    'training_history_entries',
    'goals',
    'zone_profile_versions',
    'zone_metrics',
    'zone_boundaries',
    'change_proposals',
    'initial_plan_requests',
    'weekly_plans',
    'plan_revisions',
    'planned_workouts',
    'plan_warnings',
    'activities',
    'activity_metrics',
    'weekly_checkins',
    'weekly_checkin_contexts',
    'injury_restrictions',
    'planned_external_activities',
    'goal_maintenance_states',
    'activity_rpe_revisions',
    'discipline_zone_setups',
    'calibration_observations',
    'calibration_evaluations',
    'calibration_threshold_decisions',
    'provider_connections',
    'import_runs',
    'activity_files',
    'discipline_test_assignments',
    'swipe_week_drafts',
    'onboarding_completion_records'
  ]
  loop
    v_name := left(v_table, 42) || '_opaque_owner_restrict';
    execute format(
      'create policy %I on public.%I as restrictive for all to authenticated '
      || 'using (internal_athlete_id = (select private.current_athlete_id())) '
      || 'with check (internal_athlete_id = (select private.current_athlete_id()))',
      v_name,
      v_table
    );
  end loop;
end;
$$;

create table public.athlete_identifying_profiles (
  athlete_id uuid primary key
    references private.athlete_identity_map (athlete_id)
    on delete cascade,
  first_name text,
  last_name text,
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  source_legacy_profile_revision bigint,
  backfilled_at timestamptz,

  constraint athlete_identifying_first_name_valid check (
    first_name is null
    or (first_name = btrim(first_name) and char_length(first_name) between 1 and 100)
  ),
  constraint athlete_identifying_last_name_valid check (
    last_name is null
    or (last_name = btrim(last_name) and char_length(last_name) between 1 and 100)
  ),
  constraint athlete_identifying_revision_positive check (revision > 0)
);

create table public.athlete_physiology_profiles (
  athlete_id uuid primary key
    references private.athlete_identity_map (athlete_id)
    on delete cascade,
  date_of_birth date,
  resting_heart_rate_bpm smallint,
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  source_legacy_profile_revision bigint,
  source_legacy_profile_updated_at timestamptz,
  backfilled_at timestamptz,

  constraint athlete_physiology_birth_date_past check (
    date_of_birth is null or date_of_birth < current_date
  ),
  constraint athlete_physiology_resting_hr_positive check (
    resting_heart_rate_bpm is null or resting_heart_rate_bpm > 0
  ),
  constraint athlete_physiology_revision_positive check (revision > 0)
);

create function private.backfill_split_athlete_profiles()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.athlete_identifying_profiles (
    athlete_id,
    source_legacy_profile_revision,
    backfilled_at
  )
  select
    mapping.athlete_id,
    profile.revision,
    statement_timestamp()
  from private.athlete_identity_map mapping
  left join public.athlete_profiles profile
    on profile.athlete_id = mapping.auth_user_id
  on conflict (athlete_id) do nothing;

  insert into public.athlete_physiology_profiles (
    athlete_id,
    date_of_birth,
    resting_heart_rate_bpm,
    source_legacy_profile_revision,
    source_legacy_profile_updated_at,
    backfilled_at
  )
  select
    mapping.athlete_id,
    profile.date_of_birth,
    profile.resting_heart_rate_bpm,
    profile.revision,
    profile.updated_at,
    statement_timestamp()
  from private.athlete_identity_map mapping
  left join public.athlete_profiles profile
    on profile.athlete_id = mapping.auth_user_id
  on conflict (athlete_id) do nothing;
end;
$$;

revoke execute on function private.backfill_split_athlete_profiles()
from public, anon, authenticated, service_role;

select private.backfill_split_athlete_profiles();

alter table public.athlete_identifying_profiles enable row level security;
alter table public.athlete_identifying_profiles force row level security;
alter table public.athlete_physiology_profiles enable row level security;
alter table public.athlete_physiology_profiles force row level security;

revoke all on table public.athlete_identifying_profiles
from public, anon, authenticated, service_role;
revoke all on table public.athlete_physiology_profiles
from public, anon, authenticated, service_role;
grant select (
  athlete_id, first_name, last_name, revision, created_at, updated_at
) on table public.athlete_identifying_profiles to authenticated;
grant select (
  athlete_id, date_of_birth, resting_heart_rate_bpm, revision, created_at,
  updated_at
) on table public.athlete_physiology_profiles to authenticated;
grant insert (athlete_id, first_name, last_name), update (first_name, last_name)
on table public.athlete_identifying_profiles to authenticated;
grant insert (athlete_id, date_of_birth, resting_heart_rate_bpm),
  update (date_of_birth, resting_heart_rate_bpm)
on table public.athlete_physiology_profiles to authenticated;

create policy athlete_identifying_profiles_select_own
on public.athlete_identifying_profiles for select to authenticated
using (athlete_id = (select private.current_athlete_id()));
create policy athlete_identifying_profiles_insert_own
on public.athlete_identifying_profiles for insert to authenticated
with check (athlete_id = (select private.current_athlete_id()));
create policy athlete_identifying_profiles_update_own
on public.athlete_identifying_profiles for update to authenticated
using (athlete_id = (select private.current_athlete_id()))
with check (athlete_id = (select private.current_athlete_id()));

create policy athlete_physiology_profiles_select_own
on public.athlete_physiology_profiles for select to authenticated
using (athlete_id = (select private.current_athlete_id()));
create policy athlete_physiology_profiles_insert_own
on public.athlete_physiology_profiles for insert to authenticated
with check (athlete_id = (select private.current_athlete_id()));
create policy athlete_physiology_profiles_update_own
on public.athlete_physiology_profiles for update to authenticated
using (athlete_id = (select private.current_athlete_id()))
with check (athlete_id = (select private.current_athlete_id()));

create function private.set_split_profile_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_op = 'UPDATE' then
    if new.athlete_id is distinct from old.athlete_id then
      raise exception 'athlete owner is immutable' using errcode = '23514';
    end if;
    new.revision := old.revision + 1;
    new.updated_at := statement_timestamp();
  end if;
  return new;
end;
$$;

revoke execute on function private.set_split_profile_metadata()
from public, anon, authenticated, service_role;

create function private.require_split_profile_rpc()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if current_setting('start23.profile_write', true) is distinct from 'on' then
    raise exception 'profile writes require the intended RPC' using errcode = '42501';
  end if;
  return new;
end;
$$;

revoke execute on function private.require_split_profile_rpc()
from public, anon, authenticated, service_role;

create trigger athlete_identifying_profiles_00_require_rpc
before insert or update or delete on public.athlete_identifying_profiles
for each row execute function private.require_split_profile_rpc();
create trigger athlete_identifying_profiles_10_metadata
before update on public.athlete_identifying_profiles
for each row execute function private.set_split_profile_metadata();
create trigger athlete_physiology_profiles_00_require_rpc
before insert or update or delete on public.athlete_physiology_profiles
for each row execute function private.require_split_profile_rpc();
create trigger athlete_physiology_profiles_10_metadata
before update on public.athlete_physiology_profiles
for each row execute function private.set_split_profile_metadata();

create function public.save_identifying_profile(p_profile jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_first_name text;
  v_last_name text;
  v_revision bigint;
  v_created_at timestamptz;
  v_updated_at timestamptz;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_profile) <> 'object'
     or p_profile = '{}'::jsonb
     or exists (
       select 1
       from jsonb_object_keys(p_profile) supplied(key)
       where supplied.key not in ('first_name', 'last_name')
     ) then
    raise exception 'invalid identifying profile payload' using errcode = '23514';
  end if;

  perform set_config('start23.profile_write', 'on', true);
  insert into public.athlete_identifying_profiles (
    athlete_id,
    first_name,
    last_name
  )
  values (
    v_athlete_id,
    nullif(btrim(p_profile ->> 'first_name'), ''),
    nullif(btrim(p_profile ->> 'last_name'), '')
  )
  on conflict (athlete_id) do update
  set
    first_name = case
      when p_profile ? 'first_name'
        then nullif(btrim(p_profile ->> 'first_name'), '')
      else public.athlete_identifying_profiles.first_name
    end,
    last_name = case
      when p_profile ? 'last_name'
        then nullif(btrim(p_profile ->> 'last_name'), '')
      else public.athlete_identifying_profiles.last_name
    end
  returning first_name, last_name, revision, created_at, updated_at
  into v_first_name, v_last_name, v_revision, v_created_at, v_updated_at;

  return jsonb_build_object(
    'athlete_id', v_athlete_id,
    'first_name', v_first_name,
    'last_name', v_last_name,
    'revision', v_revision,
    'created_at', v_created_at,
    'updated_at', v_updated_at
  );
end;
$$;

create function public.save_physiology_profile(p_profile jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_date_of_birth date;
  v_resting_heart_rate_bpm smallint;
  v_revision bigint;
  v_created_at timestamptz;
  v_updated_at timestamptz;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_profile) <> 'object'
     or p_profile = '{}'::jsonb
     or exists (
       select 1
       from jsonb_object_keys(p_profile) supplied(key)
       where supplied.key not in ('date_of_birth', 'resting_heart_rate_bpm')
     ) then
    raise exception 'invalid physiology profile payload' using errcode = '23514';
  end if;

  perform set_config('start23.profile_write', 'on', true);
  insert into public.athlete_physiology_profiles (
    athlete_id,
    date_of_birth,
    resting_heart_rate_bpm
  )
  values (
    v_athlete_id,
    (p_profile ->> 'date_of_birth')::date,
    (p_profile ->> 'resting_heart_rate_bpm')::smallint
  )
  on conflict (athlete_id) do update
  set
    date_of_birth = case
      when p_profile ? 'date_of_birth'
        then (p_profile ->> 'date_of_birth')::date
      else public.athlete_physiology_profiles.date_of_birth
    end,
    resting_heart_rate_bpm = case
      when p_profile ? 'resting_heart_rate_bpm'
        then (p_profile ->> 'resting_heart_rate_bpm')::smallint
      else public.athlete_physiology_profiles.resting_heart_rate_bpm
    end
  returning date_of_birth, resting_heart_rate_bpm, revision, created_at,
    updated_at
  into v_date_of_birth, v_resting_heart_rate_bpm, v_revision, v_created_at,
    v_updated_at;

  return jsonb_build_object(
    'athlete_id', v_athlete_id,
    'date_of_birth', v_date_of_birth,
    'resting_heart_rate_bpm', v_resting_heart_rate_bpm,
    'revision', v_revision,
    'created_at', v_created_at,
    'updated_at', v_updated_at
  );
end;
$$;

create function public.save_operational_athlete_profile(p_profile jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_profile public.athlete_profiles;
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_profile) <> 'object'
     or p_profile = '{}'::jsonb
     or exists (
       select 1
       from jsonb_object_keys(p_profile) supplied(key)
       where supplied.key <> 'timezone'
     ) then
    raise exception 'invalid operational profile payload' using errcode = '23514';
  end if;

  insert into public.athlete_profiles (
    athlete_id,
    timezone,
    onboarding_status
  )
  values (
    v_auth_user_id,
    p_profile ->> 'timezone',
    'in_progress'
  )
  on conflict (athlete_id) do update
  set
    timezone = p_profile ->> 'timezone',
    onboarding_status = case
      when public.athlete_profiles.onboarding_status = 'completed'
        then 'completed'
      else 'in_progress'
    end
  returning * into v_profile;

  return jsonb_build_object(
    'athlete_id', v_athlete_id,
    'timezone', v_profile.timezone,
    'onboarding_status', v_profile.onboarding_status,
    'revision', v_profile.revision,
    'created_at', v_profile.created_at,
    'updated_at', v_profile.updated_at
  );
end;
$$;

revoke execute on function public.save_identifying_profile(jsonb)
from public, anon, service_role;
revoke execute on function public.save_physiology_profile(jsonb)
from public, anon, service_role;
revoke execute on function public.save_operational_athlete_profile(jsonb)
from public, anon, service_role;
grant execute on function public.save_identifying_profile(jsonb) to authenticated;
grant execute on function public.save_physiology_profile(jsonb) to authenticated;
grant execute on function public.save_operational_athlete_profile(jsonb)
to authenticated;

comment on table public.athlete_profiles is
  'Bounded R3 operational/legacy profile compatibility. Current physiology writes use athlete_physiology_profiles.';
comment on column public.athlete_profiles.date_of_birth is
  'Historical compatibility value; current writes use athlete_physiology_profiles.';
comment on column public.athlete_profiles.resting_heart_rate_bpm is
  'Historical compatibility value; current writes use athlete_physiology_profiles.';

-- Existing observations retain their original payload. New current-protocol
-- result observations must satisfy the same measured-input contract as Python,
-- including calls made directly to the authenticated persistence RPC.
create function private.enforce_current_calibration_observation_contract()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_is_current_result boolean :=
    (
      new.protocol_id = 'start23_week1_run_calibration_v1'
      and new.discipline = 'run'
      and new.segment_id in ('comfortable_20min', 'steady_8min_optional')
    )
    or (
      new.protocol_id = 'start23_week1_bike_calibration_v1'
      and new.discipline = 'bike'
      and new.segment_id in ('comfortable_20min', 'steady_10min_optional')
    )
    or (
      new.protocol_id = 'start23_swim_css_400_200_v1'
      and new.discipline = 'swim'
      and new.segment_id in ('tt_400m', 'tt_200m')
    )
    or (
      new.protocol_id = 'start23_week1_swim_calibration_v1'
      and new.discipline = 'swim'
      and new.segment_id in ('4x200_comfortable', '4x100_steady')
    );
begin
  if not v_is_current_result
     or new.payload ->> 'completed' <> 'true'
     or new.payload ->> 'quality_status' <> 'sufficient' then
    return new;
  end if;

  if new.payload ->> 'reported_block_rpe' is null
     or (new.payload ->> 'reported_block_rpe')::integer not between 1 and 10 then
    raise exception 'current calibration result requires reported block RPE'
      using errcode = '23514';
  end if;

  if new.discipline in ('run', 'bike')
     and (
       new.payload ->> 'average_heart_rate_bpm' is null
       or (new.payload ->> 'average_heart_rate_bpm')::numeric <= 0
     ) then
    raise exception 'current run/bike calibration requires measured average HR'
      using errcode = '23514';
  end if;

  if new.discipline = 'swim'
     and (
       new.payload ->> 'elapsed_time_seconds' is null
       or (new.payload ->> 'elapsed_time_seconds')::numeric <= 0
       or new.payload ->> 'distance_meters' is null
       or (new.payload ->> 'distance_meters')::integer <= 0
     ) then
    raise exception 'current swim calibration requires elapsed time and distance'
      using errcode = '23514';
  end if;

  return new;
end;
$$;

revoke execute
on function private.enforce_current_calibration_observation_contract()
from public, anon, authenticated, service_role;

create trigger calibration_observations_r2_10_current_contract
before insert on public.calibration_observations
for each row
execute function private.enforce_current_calibration_observation_contract();

create or replace function private.build_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.resolve_opaque_athlete_id(p_athlete_id);
begin
  if v_athlete_id is null then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;

  return jsonb_build_object(
    'profile',
    (
      select jsonb_build_object(
        'athlete_id', v_athlete_id,
        'first_name', identifying.first_name,
        'last_name', identifying.last_name,
        'date_of_birth', physiology.date_of_birth,
        'resting_heart_rate_bpm', physiology.resting_heart_rate_bpm,
        'timezone', operational.timezone,
        'revision', operational.revision,
        'identifying_revision', identifying.revision,
        'physiology_revision', physiology.revision
      )
      from public.athlete_profiles operational
      left join public.athlete_identifying_profiles identifying
        on identifying.athlete_id = operational.internal_athlete_id
      left join public.athlete_physiology_profiles physiology
        on physiology.athlete_id = operational.internal_athlete_id
      where operational.internal_athlete_id = v_athlete_id
    ),
    'training_history',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'discipline', history.discipline,
            'previous_month_weekly_minutes', history.previous_month_weekly_minutes,
            'baseline_model_version', history.baseline_model_version,
            'average_weekly_distance', history.average_weekly_distance,
            'distance_unit', history.distance_unit,
            'average_sessions_per_week', history.average_sessions_per_week,
            'history_window_months', history.history_window_months,
            'source', history.source,
            'confirmed_at', history.confirmed_at
          )
          order by history.discipline
        ),
        '[]'::jsonb
      )
      from public.training_history_entries history
      where history.internal_athlete_id = v_athlete_id
    ),
    'goal',
    (
      select jsonb_build_object(
        'id', goal.id,
        'priority', goal.priority,
        'goal_type', goal.goal_type,
        'title', goal.title,
        'specific_description', goal.specific_description,
        'measurable_outcome', goal.measurable_outcome,
        'target_date', goal.target_date,
        'race_discipline_profile', goal.race_discipline_profile,
        'revision', goal.revision
      )
      from public.goals goal
      where goal.internal_athlete_id = v_athlete_id
        and goal.status = 'active'
    ),
    'zones',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'id', profile.id,
            'discipline', profile.discipline,
            'version', profile.version,
            'setup_method', profile.setup_method,
            'validated', profile.validated,
            'fallback_active', profile.fallback_active,
            'needs_testing', profile.needs_testing,
            'requires_review', profile.requires_review,
            'review_reason', profile.review_reason,
            'ruleset_version', profile.ruleset_version,
            'zone_model_version', profile.zone_model_version,
            'metric_profiles', profile.metric_profiles,
            'metric',
            (
              select jsonb_build_object(
                'kind', metric.metric_kind,
                'value', metric.value
              )
              from public.zone_metrics metric
              where metric.zone_profile_id = profile.id
                and metric.internal_athlete_id = v_athlete_id
            ),
            'boundaries',
            (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'zone_number', boundary.zone_number,
                    'lower_value', boundary.lower_value,
                    'upper_value', boundary.upper_value
                  )
                  order by boundary.zone_number
                ),
                '[]'::jsonb
              )
              from public.zone_boundaries boundary
              where boundary.zone_profile_id = profile.id
                and boundary.internal_athlete_id = v_athlete_id
            )
          )
          order by profile.discipline
        ),
        '[]'::jsonb
      )
      from public.zone_profile_versions profile
      where profile.internal_athlete_id = v_athlete_id
        and profile.status = 'active'
    ),
    'discipline_setups',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'discipline', setup.discipline,
            'setup_route', setup.setup_route,
            'guidance_mode', setup.guidance_mode,
            'setup_status', setup.setup_status,
            'protocol_id', setup.protocol_id,
            'zone_status', setup.zone_status
          )
          order by setup.discipline
        ),
        '[]'::jsonb
      )
      from public.discipline_zone_setups setup
      where setup.internal_athlete_id = v_athlete_id
    ),
    'ruleset_version',
    'phase-13-joren-ruleset-1',
    'onboarding_version',
    'phase-13-onboarding-v1'
  );
end;
$$;

alter table public.initial_plan_requests
  add column onboarding_version text;

alter table public.initial_plan_requests
  add constraint initial_plan_requests_onboarding_version_valid check (
    onboarding_version is null
    or (
      onboarding_version = btrim(onboarding_version)
      and char_length(onboarding_version) between 1 and 100
    )
  );

update public.initial_plan_requests request
set onboarding_version = session.completed_onboarding_version
from public.onboarding_sessions session
where session.initial_plan_request_id = request.id
  and session.internal_athlete_id = request.internal_athlete_id
  and session.completed_onboarding_version is not null;

create function private.current_onboarding_satisfied_steps(p_athlete_id uuid)
returns text[]
language sql
stable
security invoker
set search_path = ''
as $$
  select array_remove(array[
    case when exists (
      select 1
      from public.athlete_profiles operational
      join public.athlete_physiology_profiles physiology
        on physiology.athlete_id = operational.internal_athlete_id
      where operational.internal_athlete_id = p_athlete_id
        and operational.timezone is not null
        and physiology.date_of_birth is not null
        and physiology.resting_heart_rate_bpm is not null
    ) then 'profile' end,
    case when (
      select count(*)
      from public.training_history_entries history
      where history.internal_athlete_id = p_athlete_id
        and history.previous_month_weekly_minutes is not null
        and history.baseline_model_version = 'phase-13-joren-ruleset-1'
    ) = 3 then 'history' end,
    case when exists (
      select 1
      from public.goals goal
      where goal.internal_athlete_id = p_athlete_id
        and goal.status = 'active'
    ) then 'goal' end,
    case when (
      select count(distinct configured.discipline)
      from (
        select profile.discipline
        from public.zone_profile_versions profile
        where profile.internal_athlete_id = p_athlete_id
          and profile.status = 'active'
        union
        select setup.discipline
        from public.discipline_zone_setups setup
        where setup.internal_athlete_id = p_athlete_id
          and setup.setup_status in (
            'configured', 'test_pending', 'calibration_pending'
          )
          and (
            setup.setup_route = 'known_values'
            or (
              setup.setup_route = 'field_test'
              and setup.discipline = 'swim'
              and setup.protocol_id = 'start23_swim_css_400_200_v1'
              and setup.guidance_mode = 'pace'
            )
            or (
              setup.setup_route = 'calibration_week'
              and (
                (setup.discipline = 'run' and setup.guidance_mode = 'heart_rate')
                or (
                  setup.discipline = 'bike'
                  and setup.guidance_mode in ('heart_rate', 'combined')
                )
                or (
                  setup.discipline = 'swim' and setup.guidance_mode = 'pace'
                )
              )
            )
          )
      ) configured
    ) = 3 then 'zones' end
  ], null)
$$;

revoke execute on function private.current_onboarding_satisfied_steps(uuid)
from public, anon, service_role;
grant execute on function private.current_onboarding_satisfied_steps(uuid)
to authenticated;

-- Service-only compatibility adapters are deliberately isolated at this
-- boundary. Application contracts use the opaque athlete id; older stored
-- procedures continue to receive the auth UUID until the R6 contract gate.
grant usage on schema private to service_role;

create function public.resolve_opaque_athlete_id_for_auth_user(
  p_auth_user_id uuid
)
returns uuid
language sql
stable
security invoker
set search_path = ''
as $$
  select mapping.athlete_id
  from private.athlete_identity_map mapping
  where mapping.auth_user_id = p_auth_user_id
$$;

revoke execute on function public.resolve_opaque_athlete_id_for_auth_user(uuid)
from public, anon, authenticated;
grant execute on function public.resolve_opaque_athlete_id_for_auth_user(uuid)
to service_role;

create function public.get_current_planning_eligibility_context(
  p_athlete_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;

  v_athlete_id := private.resolve_opaque_athlete_id(p_athlete_id);
  if v_athlete_id is null then
    raise exception 'athlete identity is not mapped' using errcode = 'P0002';
  end if;

  return coalesce(
    (
      select jsonb_build_object(
        'onboarding_status', session.status,
        'completed_onboarding_version', session.completed_onboarding_version,
        'completed_ruleset_version', session.completed_ruleset_version,
        'onboarding_version', request.onboarding_version,
        'ruleset_version', request.ruleset_version
      )
      from public.onboarding_sessions session
      left join public.initial_plan_requests request
        on request.id = session.initial_plan_request_id
       and request.internal_athlete_id = session.internal_athlete_id
      where session.internal_athlete_id = v_athlete_id
    ),
    jsonb_build_object(
      'onboarding_status', null,
      'completed_onboarding_version', null,
      'completed_ruleset_version', null,
      'onboarding_version', null,
      'ruleset_version', null
    )
  );
end;
$$;

revoke execute on function public.get_current_planning_eligibility_context(uuid)
from public, anon, authenticated;
grant execute on function public.get_current_planning_eligibility_context(uuid)
to service_role;

-- The original unversioned endpoint and R1's temporary no-argument endpoint
-- must no longer be callable. Keeping their definitions preserves migration
-- history while removing both bypasses from the API surface.
revoke execute on function public.complete_onboarding()
from public, anon, authenticated, service_role;
revoke execute on function public.complete_current_onboarding()
from public, anon, authenticated, service_role;

create function public.complete_current_onboarding(
  p_expected_session_revision bigint
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := private.current_athlete_id();
  v_auth_user_id uuid := (select auth.uid());
  v_session public.onboarding_sessions;
  v_request_id uuid;
  v_completion_revision bigint;
  v_satisfied text[];
begin
  if v_athlete_id is null or v_auth_user_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_expected_session_revision is null
     or p_expected_session_revision < 0 then
    raise exception 'expected onboarding revision is required'
      using errcode = '23514';
  end if;

  select session.* into v_session
  from public.onboarding_sessions session
  where session.internal_athlete_id = v_athlete_id
  for update;

  -- A successfully committed replay is idempotent even when its precondition
  -- is now stale. Only the exact current completion can take this path.
  if v_session.athlete_id is not null
     and v_session.status = 'completed'
     and v_session.completed_onboarding_version = 'phase-13-onboarding-v1'
     and v_session.completed_ruleset_version = 'phase-13-joren-ruleset-1'
     and exists (
       select 1
       from public.initial_plan_requests request
       where request.id = v_session.initial_plan_request_id
         and request.internal_athlete_id = v_athlete_id
         and request.onboarding_version = 'phase-13-onboarding-v1'
         and request.ruleset_version = 'phase-13-joren-ruleset-1'
         and request.status <> 'cancelled'
     ) then
    return v_session.initial_plan_request_id;
  end if;

  if (v_session.athlete_id is null and p_expected_session_revision <> 0)
     or (
       v_session.athlete_id is not null
       and v_session.revision <> p_expected_session_revision
     ) then
    raise exception 'onboarding session revision is stale'
      using errcode = '40001';
  end if;

  v_satisfied := private.current_onboarding_satisfied_steps(v_athlete_id);
  if not v_satisfied @> array['profile', 'history', 'goal', 'zones']::text[] then
    raise exception 'current onboarding prerequisites are incomplete'
      using errcode = '23514';
  end if;

  v_completion_revision := case
    when v_session.athlete_id is null then 1
    else v_session.revision + 1
  end;

  perform set_config('start23.critical_write', 'on', true);

  update public.initial_plan_requests
  set status = 'cancelled'
  where internal_athlete_id = v_athlete_id
    and status = 'pending';

  update public.athlete_profiles
  set onboarding_status = 'completed'
  where internal_athlete_id = v_athlete_id
    and onboarding_status <> 'completed';

  insert into public.initial_plan_requests (
    athlete_id,
    internal_athlete_id,
    onboarding_revision,
    onboarding_version,
    ruleset_version
  )
  values (
    v_auth_user_id,
    v_athlete_id,
    v_completion_revision,
    'phase-13-onboarding-v1',
    'phase-13-joren-ruleset-1'
  )
  returning id into v_request_id;

  insert into public.onboarding_sessions (
    athlete_id,
    internal_athlete_id,
    status,
    current_step,
    completed_steps,
    revision,
    initial_plan_request_id,
    completed_onboarding_version,
    completed_ruleset_version,
    completed_at
  )
  values (
    v_auth_user_id,
    v_athlete_id,
    'completed',
    'completed',
    array['profile', 'history', 'goal', 'zones', 'review']::text[],
    v_completion_revision,
    v_request_id,
    'phase-13-onboarding-v1',
    'phase-13-joren-ruleset-1',
    statement_timestamp()
  )
  on conflict (athlete_id) do update
  set
    status = 'completed',
    current_step = 'completed',
    completed_steps = array[
      'profile', 'history', 'goal', 'zones', 'review'
    ]::text[],
    initial_plan_request_id = excluded.initial_plan_request_id,
    completed_onboarding_version = excluded.completed_onboarding_version,
    completed_ruleset_version = excluded.completed_ruleset_version,
    completed_at = excluded.completed_at;

  -- The update metadata trigger owns the increment for existing sessions.
  select session.revision into strict v_completion_revision
  from public.onboarding_sessions session
  where session.internal_athlete_id = v_athlete_id;

  if v_completion_revision <> (
    select request.onboarding_revision
    from public.initial_plan_requests request
    where request.id = v_request_id
  ) then
    raise exception 'onboarding completion revision mismatch'
      using errcode = '23514';
  end if;

  insert into public.onboarding_completion_records (
    athlete_id,
    internal_athlete_id,
    onboarding_version,
    ruleset_version,
    completed_steps,
    initial_plan_request_id,
    session_revision,
    record_source,
    completed_at
  )
  values (
    v_auth_user_id,
    v_athlete_id,
    'phase-13-onboarding-v1',
    'phase-13-joren-ruleset-1',
    array['profile', 'history', 'goal', 'zones', 'review']::text[],
    v_request_id,
    v_completion_revision,
    'current_completion',
    statement_timestamp()
  )
  on conflict (athlete_id, onboarding_version, ruleset_version) do nothing;

  return v_request_id;
end;
$$;

revoke execute on function public.complete_current_onboarding(bigint)
from public, anon, service_role;
grant execute on function public.complete_current_onboarding(bigint)
to authenticated;

comment on function public.complete_current_onboarding(bigint) is
  'R2 stale-safe, idempotent completion for the exact current onboarding and ruleset versions.';

create function private.assert_current_planning_eligibility(p_athlete_id uuid)
returns void
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_satisfied text[];
begin
  if p_athlete_id is null then
    raise exception 'opaque athlete owner is required' using errcode = '23514';
  end if;

  v_satisfied := private.current_onboarding_satisfied_steps(p_athlete_id);

  if not exists (
    select 1
    from public.onboarding_sessions session
    join public.initial_plan_requests request
      on request.id = session.initial_plan_request_id
     and request.internal_athlete_id = session.internal_athlete_id
    where session.internal_athlete_id = p_athlete_id
      and session.status = 'completed'
      and session.completed_onboarding_version = 'phase-13-onboarding-v1'
      and session.completed_ruleset_version = 'phase-13-joren-ruleset-1'
      and request.onboarding_version = 'phase-13-onboarding-v1'
      and request.ruleset_version = 'phase-13-joren-ruleset-1'
      and request.status <> 'cancelled'
  ) or not v_satisfied @> array[
    'profile', 'history', 'goal', 'zones'
  ]::text[] then
    raise exception 'current onboarding completion is required for planning'
      using errcode = '23514';
  end if;
end;
$$;

revoke execute on function private.assert_current_planning_eligibility(uuid)
from public, anon, authenticated, service_role;

create function private.enforce_current_planning_eligibility()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.assert_current_planning_eligibility(new.internal_athlete_id);
  return new;
end;
$$;

revoke execute on function private.enforce_current_planning_eligibility()
from public, anon, authenticated, service_role;

create trigger weekly_plans_r3_10_require_current_onboarding
before insert or update on public.weekly_plans
for each row execute function private.enforce_current_planning_eligibility();

create trigger plan_revisions_r3_10_require_current_onboarding
before insert or update on public.plan_revisions
for each row execute function private.enforce_current_planning_eligibility();

create trigger swipe_week_drafts_r3_10_require_current_onboarding
before insert or update on public.swipe_week_drafts
for each row execute function private.enforce_current_planning_eligibility();

comment on function private.assert_current_planning_eligibility(uuid) is
  'Shared SQL planning gate. Service RPC writes and direct RPC writes fail under the same R2 current-version prerequisites.';
