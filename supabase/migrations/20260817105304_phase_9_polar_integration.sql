-- Phase 9 provisional Polar AccessLink integration. Provider production approval,
-- legal review, credentials, and hosted verification remain explicit rollout gates.

create table public.provider_connections (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  provider text not null,
  provider_user_id text not null,
  status text not null,
  connected_at timestamptz not null default statement_timestamp(),
  disconnected_at timestamptz,
  last_import_at timestamptz,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  unique (id, athlete_id),
  unique (athlete_id, provider),
  unique (provider, provider_user_id),
  constraint provider_connections_provider_valid check (provider = 'polar'),
  constraint provider_connections_user_valid check (
    provider_user_id ~ '^[0-9]{1,20}$'
  ),
  constraint provider_connections_status_valid check (
    status in ('connected', 'disconnected', 'revoked', 'error')
  ),
  constraint provider_connections_disconnect_consistent check (
    (status = 'connected' and disconnected_at is null)
    or (status <> 'connected' and disconnected_at is not null)
  )
);

create table private.provider_tokens (
  connection_id uuid primary key,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  access_token text not null,
  token_expires_at timestamptz,
  updated_at timestamptz not null default statement_timestamp(),
  unique (connection_id, athlete_id),
  foreign key (connection_id, athlete_id)
    references public.provider_connections (id, athlete_id) on delete cascade,
  constraint provider_tokens_value_valid check (
    char_length(access_token) between 16 and 4096
  )
);

create table private.integration_oauth_states (
  state_hash text primary key,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  provider text not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default statement_timestamp(),
  constraint integration_oauth_state_hash_valid check (
    state_hash ~ '^[a-f0-9]{64}$'
  ),
  constraint integration_oauth_state_provider_valid check (provider = 'polar')
);

create table public.import_runs (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  connection_id uuid not null,
  idempotency_key uuid not null,
  provider text not null,
  kind text not null,
  status text not null,
  range_start date,
  range_end date,
  discovered_count integer not null default 0,
  imported_count integer not null default 0,
  skipped_count integer not null default 0,
  failure_code text,
  created_at timestamptz not null default statement_timestamp(),
  completed_at timestamptz,
  unique (id, athlete_id),
  unique (athlete_id, idempotency_key),
  foreign key (connection_id, athlete_id)
    references public.provider_connections (id, athlete_id) on delete cascade,
  constraint import_runs_provider_valid check (provider = 'polar'),
  constraint import_runs_kind_valid check (kind in ('historical', 'webhook')),
  constraint import_runs_status_valid check (
    status in ('running', 'completed', 'failed')
  ),
  constraint import_runs_range_valid check (
    (kind = 'webhook' and range_start is null and range_end is null)
    or (
      kind = 'historical'
      and range_start is not null
      and range_end is not null
      and range_end - range_start between 0 and 29
    )
  ),
  constraint import_runs_counts_valid check (
    discovered_count >= 0 and imported_count >= 0 and skipped_count >= 0
    and imported_count + skipped_count <= discovered_count
  ),
  constraint import_runs_completion_valid check (
    (status = 'running' and completed_at is null and failure_code is null)
    or (status = 'completed' and completed_at is not null and failure_code is null)
    or (status = 'failed' and completed_at is not null and failure_code is not null)
  )
);

create table private.webhook_receipts (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid references auth.users (id) on delete cascade,
  import_id uuid,
  provider text not null,
  event_key text not null,
  payload_fingerprint text not null,
  event_type text not null,
  provider_user_id text,
  provider_entity_id text,
  status text not null,
  failure_code text,
  received_at timestamptz not null default statement_timestamp(),
  processed_at timestamptz,
  unique (provider, event_key),
  foreign key (import_id, athlete_id)
    references public.import_runs (id, athlete_id) on delete cascade,
  constraint webhook_receipts_provider_valid check (provider = 'polar'),
  constraint webhook_receipts_hashes_valid check (
    event_key ~ '^[a-f0-9]{64}$'
    and payload_fingerprint ~ '^[a-f0-9]{64}$'
  ),
  constraint webhook_receipts_event_valid check (event_type in ('PING', 'EXERCISE')),
  constraint webhook_receipts_event_fields_valid check (
    (
      event_type = 'PING'
      and provider_user_id is null
      and provider_entity_id is null
    )
    or (
      event_type = 'EXERCISE'
      and provider_user_id ~ '^[0-9]{1,20}$'
      and provider_entity_id ~ '^[A-Za-z0-9_-]{1,200}$'
    )
  ),
  constraint webhook_receipts_status_valid check (
    status in ('received', 'processed', 'failed')
  )
);

create table private.provider_activity_imports (
  provider text not null,
  provider_entity_id text not null,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  import_id uuid not null,
  activity_id uuid not null,
  imported_at timestamptz not null default statement_timestamp(),
  primary key (provider, provider_entity_id),
  foreign key (import_id, athlete_id)
    references public.import_runs (id, athlete_id) on delete cascade,
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id) on delete cascade,
  constraint provider_activity_imports_provider_valid check (provider = 'polar'),
  constraint provider_activity_imports_entity_valid check (
    provider_entity_id ~ '^[A-Za-z0-9_-]{1,200}$'
  )
);

create table public.activity_files (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  activity_id uuid not null,
  provider text not null,
  storage_bucket text not null,
  storage_object_name text not null,
  content_type text not null,
  size_bytes integer not null,
  sha256 text not null,
  created_at timestamptz not null default statement_timestamp(),
  unique (activity_id),
  unique (storage_bucket, storage_object_name),
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id) on delete cascade,
  constraint activity_files_provider_valid check (provider = 'polar'),
  constraint activity_files_bucket_valid check (storage_bucket = 'activity-files'),
  constraint activity_files_type_valid check (
    content_type = 'application/octet-stream'
  ),
  constraint activity_files_size_valid check (size_bytes between 1 and 26214400),
  constraint activity_files_checksum_valid check (sha256 ~ '^[a-f0-9]{64}$'),
  constraint activity_files_path_valid check (
    storage_object_name like athlete_id::text || '/%'
  )
);

create index provider_connections_owner_idx
on public.provider_connections (athlete_id);
create index provider_tokens_owner_idx
on private.provider_tokens (athlete_id);
create index integration_oauth_states_owner_idx
on private.integration_oauth_states (athlete_id, provider);
create index import_runs_owner_created_idx
on public.import_runs (athlete_id, created_at desc);
create index import_runs_connection_idx
on public.import_runs (connection_id, athlete_id);
create index webhook_receipts_pending_idx
on private.webhook_receipts (received_at) where status = 'received';
create index webhook_receipts_owner_idx
on private.webhook_receipts (athlete_id) where athlete_id is not null;
create index webhook_receipts_import_idx
on private.webhook_receipts (import_id, athlete_id) where import_id is not null;
create index provider_activity_imports_owner_idx
on private.provider_activity_imports (athlete_id);
create index provider_activity_imports_import_idx
on private.provider_activity_imports (import_id, athlete_id);
create index provider_activity_imports_activity_idx
on private.provider_activity_imports (activity_id, athlete_id);
create index activity_files_owner_idx on public.activity_files (athlete_id);

alter table public.provider_connections enable row level security;
alter table public.provider_connections force row level security;
alter table public.import_runs enable row level security;
alter table public.import_runs force row level security;
alter table public.activity_files enable row level security;
alter table public.activity_files force row level security;

revoke all on table public.provider_connections
from public, anon, authenticated, service_role;
revoke all on table public.import_runs
from public, anon, authenticated, service_role;
revoke all on table public.activity_files
from public, anon, authenticated, service_role;
revoke all on table private.provider_tokens
from public, anon, authenticated, service_role;
revoke all on table private.integration_oauth_states
from public, anon, authenticated, service_role;
revoke all on table private.webhook_receipts
from public, anon, authenticated, service_role;
revoke all on table private.provider_activity_imports
from public, anon, authenticated, service_role;

grant select on table public.provider_connections to authenticated;
grant select on table public.import_runs to authenticated;
grant select on table public.activity_files to authenticated;

create policy provider_connections_select_own
on public.provider_connections for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy import_runs_select_own
on public.import_runs for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy activity_files_select_own
on public.activity_files for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'activity-files',
  'activity-files',
  false,
  26214400,
  array['application/octet-stream']::text[]
)
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy activity_files_storage_select_own
on storage.objects for select to authenticated
using (
  bucket_id = 'activity-files'
  and (storage.foldername(name))[1] = (select auth.uid())::text
);

create function private.phase_9_require_service_role()
returns void
language plpgsql
stable
security invoker
set search_path = ''
as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
end;
$$;

revoke all on function private.phase_9_require_service_role()
from public, anon, authenticated, service_role;

create function private.provider_connection_public_json(p_connection_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', connection.id,
    'provider', connection.provider,
    'status', connection.status,
    'connected_at', connection.connected_at,
    'disconnected_at', connection.disconnected_at,
    'last_import_at', connection.last_import_at
  )
  from public.provider_connections connection
  where connection.id = p_connection_id;
$$;

revoke all on function private.provider_connection_public_json(uuid)
from public, anon, authenticated, service_role;

create function private.import_run_public_json(p_import_id uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', run.id,
    'provider', run.provider,
    'kind', run.kind,
    'status', run.status,
    'range_start', run.range_start,
    'range_end', run.range_end,
    'discovered_count', run.discovered_count,
    'imported_count', run.imported_count,
    'skipped_count', run.skipped_count,
    'failure_code', run.failure_code,
    'created_at', run.created_at,
    'completed_at', run.completed_at
  )
  from public.import_runs run where run.id = p_import_id;
$$;

revoke all on function private.import_run_public_json(uuid)
from public, anon, authenticated, service_role;

create function public.start_polar_oauth(p_state_hash text, p_expires_at timestamptz)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_state_hash !~ '^[a-f0-9]{64}$'
     or p_expires_at <= statement_timestamp()
     or p_expires_at > statement_timestamp() + interval '15 minutes' then
    raise exception 'invalid oauth state' using errcode = '23514';
  end if;
  delete from private.integration_oauth_states
  where athlete_id = v_athlete_id and provider = 'polar';
  insert into private.integration_oauth_states (
    state_hash, athlete_id, provider, expires_at
  ) values (p_state_hash, v_athlete_id, 'polar', p_expires_at);
end;
$$;

revoke all on function public.start_polar_oauth(text, timestamptz)
from public, anon, authenticated, service_role;
grant execute on function public.start_polar_oauth(text, timestamptz) to authenticated;

create function public.consume_polar_oauth_state(p_state_hash text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_state private.integration_oauth_states;
begin
  perform private.phase_9_require_service_role();
  delete from private.integration_oauth_states
  where state_hash = p_state_hash and provider = 'polar'
  returning * into v_state;
  if not found or v_state.expires_at <= statement_timestamp() then
    raise exception 'oauth state not found' using errcode = 'P0002';
  end if;
  return v_state.athlete_id;
end;
$$;

revoke all on function public.consume_polar_oauth_state(text)
from public, anon, authenticated, service_role;
grant execute on function public.consume_polar_oauth_state(text) to service_role;

create function public.save_polar_connection(
  p_athlete_id uuid,
  p_provider_user_id text,
  p_access_token text,
  p_token_expires_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_connection_id uuid;
begin
  perform private.phase_9_require_service_role();
  if not exists (select 1 from auth.users where id = p_athlete_id) then
    raise exception 'athlete not found' using errcode = 'P0002';
  end if;
  insert into public.provider_connections (
    athlete_id, provider, provider_user_id, status, connected_at,
    disconnected_at, updated_at
  ) values (
    p_athlete_id, 'polar', p_provider_user_id, 'connected',
    statement_timestamp(), null, statement_timestamp()
  )
  on conflict (athlete_id, provider) do update set
    provider_user_id = excluded.provider_user_id,
    status = 'connected',
    connected_at = statement_timestamp(),
    disconnected_at = null,
    updated_at = statement_timestamp()
  returning id into v_connection_id;
  insert into private.provider_tokens (
    connection_id, athlete_id, access_token, token_expires_at, updated_at
  ) values (
    v_connection_id, p_athlete_id, p_access_token, p_token_expires_at,
    statement_timestamp()
  )
  on conflict (connection_id) do update set
    access_token = excluded.access_token,
    token_expires_at = excluded.token_expires_at,
    updated_at = statement_timestamp();
  return private.provider_connection_public_json(v_connection_id);
end;
$$;

revoke all on function public.save_polar_connection(uuid, text, text, timestamptz)
from public, anon, authenticated, service_role;
grant execute on function public.save_polar_connection(uuid, text, text, timestamptz)
to service_role;

create function public.get_polar_connection()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_connection_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select id into v_connection_id from public.provider_connections
  where athlete_id = v_athlete_id and provider = 'polar';
  if not found then
    raise exception 'connection not found' using errcode = 'P0002';
  end if;
  return private.provider_connection_public_json(v_connection_id);
end;
$$;

revoke all on function public.get_polar_connection()
from public, anon, authenticated, service_role;
grant execute on function public.get_polar_connection() to authenticated;

create function public.get_polar_credentials(p_athlete_id uuid)
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
  select jsonb_build_object(
    'connection_id', connection.id,
    'provider_user_id', connection.provider_user_id,
    'access_token', token.access_token,
    'token_expires_at', token.token_expires_at,
    'timezone', profile.timezone
  ) into v_result
  from public.provider_connections connection
  join private.provider_tokens token
    on token.connection_id = connection.id and token.athlete_id = connection.athlete_id
  join public.athlete_profiles profile on profile.athlete_id = connection.athlete_id
  where connection.athlete_id = p_athlete_id
    and connection.provider = 'polar'
    and connection.status = 'connected';
  if v_result is null then
    raise exception 'connection not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_polar_credentials(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_polar_credentials(uuid) to service_role;

create function public.disconnect_polar_connection(p_athlete_id uuid, p_status text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_connection_id uuid;
begin
  perform private.phase_9_require_service_role();
  if p_status not in ('disconnected', 'revoked') then
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

revoke all on function public.disconnect_polar_connection(uuid, text)
from public, anon, authenticated, service_role;
grant execute on function public.disconnect_polar_connection(uuid, text)
to service_role;

create function public.start_polar_import(
  p_athlete_id uuid,
  p_idempotency_key uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_connection public.provider_connections;
  v_import_id uuid;
  v_existing public.import_runs;
begin
  perform private.phase_9_require_service_role();
  if p_payload ->> 'kind' <> 'historical' then
    raise exception 'invalid import kind' using errcode = '23514';
  end if;
  select * into v_connection from public.provider_connections
  where athlete_id = p_athlete_id and provider = 'polar' and status = 'connected';
  if not found then
    raise exception 'connection not found' using errcode = 'P0002';
  end if;
  insert into public.import_runs (
    athlete_id, connection_id, idempotency_key, provider, kind, status,
    range_start, range_end
  ) values (
    p_athlete_id, v_connection.id, p_idempotency_key, 'polar',
    p_payload ->> 'kind', 'running',
    (p_payload ->> 'range_start')::date,
    (p_payload ->> 'range_end')::date
  )
  on conflict (athlete_id, idempotency_key) do nothing
  returning id into v_import_id;
  if v_import_id is null then
    select * into strict v_existing from public.import_runs
    where athlete_id = p_athlete_id and idempotency_key = p_idempotency_key;
    if v_existing.kind <> p_payload ->> 'kind'
       or v_existing.range_start <> (p_payload ->> 'range_start')::date
       or v_existing.range_end <> (p_payload ->> 'range_end')::date then
      raise exception 'import idempotency key reused' using errcode = '40001';
    end if;
    return private.import_run_public_json(v_existing.id);
  end if;
  return private.import_run_public_json(v_import_id);
end;
$$;

revoke all on function public.start_polar_import(uuid, uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.start_polar_import(uuid, uuid, jsonb) to service_role;

create function public.finish_polar_import(
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

revoke all on function public.finish_polar_import(uuid, uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.finish_polar_import(uuid, uuid, jsonb) to service_role;

create function public.list_polar_imports()
returns setof jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select private.import_run_public_json(run.id)
  from public.import_runs run
  where run.athlete_id = (select auth.uid()) and run.provider = 'polar'
  order by run.created_at desc;
$$;

revoke all on function public.list_polar_imports()
from public, anon, authenticated, service_role;
grant execute on function public.list_polar_imports() to authenticated;

create function public.import_polar_activity(
  p_athlete_id uuid,
  p_import_id uuid,
  p_provider_entity_id text,
  p_idempotency_key uuid,
  p_request_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_activity_id uuid;
  v_metrics jsonb := p_payload -> 'metrics';
begin
  perform private.phase_9_require_service_role();
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('polar-activity:' || p_provider_entity_id, 0)
  );
  if not exists (
    select 1 from public.import_runs
    where id = p_import_id and athlete_id = p_athlete_id and status = 'running'
  ) then
    raise exception 'import not found' using errcode = 'P0002';
  end if;
  select activity_id into v_activity_id
  from private.provider_activity_imports
  where provider = 'polar' and provider_entity_id = p_provider_entity_id;
  if found then
    return jsonb_build_object(
      'created', false,
      'activity', private.activity_public_json(v_activity_id, p_athlete_id)
    );
  end if;
  if p_request_fingerprint !~ '^[a-f0-9]{64}$'
     or not exists (
       select 1 from pg_catalog.pg_timezone_names
       where name = p_payload ->> 'timezone'
     ) then
    raise exception 'invalid canonical activity' using errcode = '23514';
  end if;
  insert into public.activities (
    athlete_id, idempotency_key, request_fingerprint, discipline, started_at,
    timezone, duration_minutes, distance_meters, elevation_gain_meters,
    match_status
  ) values (
    p_athlete_id, p_idempotency_key, p_request_fingerprint,
    p_payload ->> 'discipline', (p_payload ->> 'started_at')::timestamptz,
    p_payload ->> 'timezone', (p_payload ->> 'duration_minutes')::numeric,
    (p_payload ->> 'distance_meters')::integer,
    (p_payload ->> 'elevation_gain_meters')::integer, 'unmatched'
  ) returning id into v_activity_id;
  if v_metrics is not null then
    insert into public.activity_metrics (
      activity_id, athlete_id, average_heart_rate_bpm, max_heart_rate_bpm,
      normalized_power_watts, average_speed_kmh, max_speed_kmh,
      average_pace_seconds_per_km, low_intensity_minutes,
      high_intensity_minutes
    ) values (
      v_activity_id, p_athlete_id,
      (v_metrics ->> 'average_heart_rate_bpm')::smallint,
      (v_metrics ->> 'max_heart_rate_bpm')::smallint,
      (v_metrics ->> 'normalized_power_watts')::integer,
      (v_metrics ->> 'average_speed_kmh')::numeric,
      (v_metrics ->> 'max_speed_kmh')::numeric,
      (v_metrics ->> 'average_pace_seconds_per_km')::numeric,
      (v_metrics ->> 'low_intensity_minutes')::numeric,
      (v_metrics ->> 'high_intensity_minutes')::numeric
    );
  end if;
  insert into private.provider_activity_imports (
    provider, provider_entity_id, athlete_id, import_id, activity_id
  ) values ('polar', p_provider_entity_id, p_athlete_id, p_import_id, v_activity_id);
  return jsonb_build_object(
    'created', true,
    'activity', private.activity_public_json(v_activity_id, p_athlete_id)
  );
end;
$$;

revoke all on function public.import_polar_activity(
  uuid, uuid, text, uuid, text, jsonb
)
from public, anon, authenticated, service_role;
grant execute on function public.import_polar_activity(
  uuid, uuid, text, uuid, text, jsonb
) to service_role;

create function public.save_polar_activity_file(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_object_name text,
  p_checksum text,
  p_size_bytes integer
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.phase_9_require_service_role();
  if not exists (
    select 1 from private.provider_activity_imports
    where activity_id = p_activity_id and athlete_id = p_athlete_id
  ) then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  insert into public.activity_files (
    athlete_id, activity_id, provider, storage_bucket, storage_object_name,
    content_type, size_bytes, sha256
  ) values (
    p_athlete_id, p_activity_id, 'polar', 'activity-files', p_object_name,
    'application/octet-stream', p_size_bytes, p_checksum
  )
  on conflict (activity_id) do nothing;
end;
$$;

revoke all on function public.save_polar_activity_file(
  uuid, uuid, text, text, integer
)
from public, anon, authenticated, service_role;
grant execute on function public.save_polar_activity_file(
  uuid, uuid, text, text, integer
) to service_role;

create function public.record_polar_webhook(
  p_event_key text,
  p_payload_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_connection public.provider_connections;
  v_receipt_id uuid;
  v_import_id uuid;
  v_existing_fingerprint text;
begin
  perform private.phase_9_require_service_role();
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('polar-webhook:' || p_event_key, 0)
  );
  select id, payload_fingerprint into v_receipt_id, v_existing_fingerprint
  from private.webhook_receipts
  where provider = 'polar' and event_key = p_event_key;
  if found then
    if v_existing_fingerprint <> p_payload_fingerprint then
      raise exception 'webhook event key reused' using errcode = '40001';
    end if;
    return jsonb_build_object('id', v_receipt_id, 'duplicate', true);
  end if;
  if p_payload ->> 'event' = 'EXERCISE' then
    select * into v_connection from public.provider_connections
    where provider = 'polar'
      and provider_user_id = p_payload ->> 'user_id'
      and status = 'connected';
    if not found then
      raise exception 'connection not found' using errcode = 'P0002';
    end if;
    insert into public.import_runs (
      athlete_id, connection_id, idempotency_key, provider, kind, status
    ) values (
      v_connection.athlete_id, v_connection.id, gen_random_uuid(),
      'polar', 'webhook', 'running'
    ) returning id into v_import_id;
  end if;
  insert into private.webhook_receipts (
    athlete_id, import_id, provider, event_key, payload_fingerprint,
    event_type, provider_user_id, provider_entity_id, status, processed_at
  ) values (
    v_connection.athlete_id, v_import_id, 'polar', p_event_key,
    p_payload_fingerprint, p_payload ->> 'event', p_payload ->> 'user_id',
    p_payload ->> 'entity_id',
    case when p_payload ->> 'event' = 'PING' then 'processed' else 'received' end,
    case when p_payload ->> 'event' = 'PING' then statement_timestamp() end
  ) returning id into v_receipt_id;
  return jsonb_build_object('id', v_receipt_id, 'duplicate', false);
end;
$$;

revoke all on function public.record_polar_webhook(text, text, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.record_polar_webhook(text, text, jsonb)
to service_role;

create function public.get_polar_webhook_context(p_receipt_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
  v_import_id uuid;
begin
  perform private.phase_9_require_service_role();
  select import_id into v_import_id
  from private.webhook_receipts
  where id = p_receipt_id and status in ('received', 'failed')
  for update;
  if not found then
    raise exception 'webhook not found' using errcode = 'P0002';
  end if;
  update private.webhook_receipts set
    status = 'received', failure_code = null, processed_at = null
  where id = p_receipt_id;
  update public.import_runs set
    status = 'running',
    discovered_count = 0,
    imported_count = 0,
    skipped_count = 0,
    failure_code = null,
    completed_at = null
  where id = v_import_id and status = 'failed';
  select jsonb_build_object(
    'athlete_id', receipt.athlete_id,
    'import_id', receipt.import_id,
    'entity_id', receipt.provider_entity_id,
    'access_token', token.access_token,
    'timezone', profile.timezone
  ) into v_result
  from private.webhook_receipts receipt
  join public.provider_connections connection
    on connection.athlete_id = receipt.athlete_id and connection.provider = 'polar'
  join private.provider_tokens token on token.connection_id = connection.id
  join public.athlete_profiles profile on profile.athlete_id = receipt.athlete_id
  where receipt.id = p_receipt_id and receipt.status = 'received'
    and connection.status = 'connected';
  if v_result is null then
    raise exception 'webhook not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_polar_webhook_context(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_polar_webhook_context(uuid) to service_role;

create function public.finish_polar_webhook(
  p_receipt_id uuid,
  p_status text,
  p_failure_code text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_receipt private.webhook_receipts;
begin
  perform private.phase_9_require_service_role();
  if p_status not in ('processed', 'failed')
     or (p_status = 'processed' and p_failure_code is not null)
     or (p_status = 'failed' and p_failure_code is null) then
    raise exception 'invalid webhook completion' using errcode = '23514';
  end if;
  update private.webhook_receipts set
    status = p_status,
    failure_code = p_failure_code,
    processed_at = statement_timestamp()
  where id = p_receipt_id and status in ('received', 'failed')
  returning * into v_receipt;
  if not found then
    raise exception 'webhook not found' using errcode = 'P0002';
  end if;
  update public.import_runs set
    status = case when p_status = 'processed' then 'completed' else 'failed' end,
    discovered_count = 1,
    imported_count = case
      when p_status = 'processed' and exists (
        select 1 from private.provider_activity_imports
        where import_id = v_receipt.import_id
      ) then 1 else 0 end,
    skipped_count = case
      when p_status = 'processed' and exists (
        select 1 from private.provider_activity_imports
        where import_id = v_receipt.import_id
      ) then 0 else 1 end,
    failure_code = p_failure_code,
    completed_at = statement_timestamp()
  where id = v_receipt.import_id and status = 'running';
end;
$$;

revoke all on function public.finish_polar_webhook(uuid, text, text)
from public, anon, authenticated, service_role;
grant execute on function public.finish_polar_webhook(uuid, text, text)
to service_role;
