-- DISPOSABLE LOCAL PG17 BOOTSTRAP ONLY. NOT A DEPLOYABLE MIGRATION.
-- Minimal upstream Supabase auth/storage SQL prerequisites, not GoTrue/Storage services.
-- Adapted/assembled for standalone testing: auth namespace rendered, roles
-- precreated, explicit grants, storage role installation disabled, test guards.
-- Upstream copyright/license notices accompany this file in fixtures/licenses.
-- Source URLs, hashes and deviations are recorded in the PostgreSQL setup report.
-- Run only inside a NEW empty database in the private workspace-local cluster.
do $$ begin
  if current_database() !~ '^wombo_v6_[a-z0-9_]+$'
    or inet_server_addr() is distinct from '127.0.0.1'::inet
    or current_setting('server_version_num')::integer / 10000 <> 17 then
    raise exception 'A fresh disposable loopback PostgreSQL 17 database is required';
  end if;
end; $$;
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'supabase_admin') then
    create role supabase_admin nologin superuser;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role nologin noinherit bypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticator') then
    create role authenticator login noinherit nosuperuser nocreatedb nocreaterole;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'supabase_auth_admin') then
    create role supabase_auth_admin login noinherit createrole noreplication;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'supabase_storage_admin') then
    create role supabase_storage_admin login noinherit createrole noreplication;
  end if;
end; $$;
grant anon, authenticated, service_role to authenticator;

create schema extensions;
create extension pgcrypto with schema extensions;
create extension "uuid-ossp" with schema extensions;
grant usage on schema public, extensions to anon, authenticated, service_role;
do $$ begin execute format('alter database %I set search_path to public, extensions', current_database()); end; $$;
-- migrate:up

CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION supabase_admin;

-- auth.users definition

CREATE TABLE auth.users (
    instance_id uuid NULL,
    id uuid NOT NULL UNIQUE,
    aud varchar(255) NULL,
    "role" varchar(255) NULL,
    email varchar(255) NULL UNIQUE,
    encrypted_password varchar(255) NULL,
    confirmed_at timestamptz NULL,
    invited_at timestamptz NULL,
    confirmation_token varchar(255) NULL,
    confirmation_sent_at timestamptz NULL,
    recovery_token varchar(255) NULL,
    recovery_sent_at timestamptz NULL,
    email_change_token varchar(255) NULL,
    email_change varchar(255) NULL,
    email_change_sent_at timestamptz NULL,
    last_sign_in_at timestamptz NULL,
    raw_app_meta_data jsonb NULL,
    raw_user_meta_data jsonb NULL,
    is_super_admin bool NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE INDEX users_instance_id_email_idx ON auth.users USING btree (instance_id, email);
CREATE INDEX users_instance_id_idx ON auth.users USING btree (instance_id);
comment on table auth.users is 'Auth: Stores user login data within a secure schema.';

-- auth.refresh_tokens definition

CREATE TABLE auth.refresh_tokens (
    instance_id uuid NULL,
    id bigserial NOT NULL,
    "token" varchar(255) NULL,
    user_id varchar(255) NULL,
    revoked bool NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id)
);
CREATE INDEX refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);
CREATE INDEX refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);
CREATE INDEX refresh_tokens_token_idx ON auth.refresh_tokens USING btree (token);
comment on table auth.refresh_tokens is 'Auth: Store of tokens used to refresh JWT tokens once they expire.';

-- auth.instances definition

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid NULL,
    raw_base_config text NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT instances_pkey PRIMARY KEY (id)
);
comment on table auth.instances is 'Auth: Manages users across multiple sites.';

-- auth.audit_log_entries definition

CREATE TABLE auth.audit_log_entries (
    instance_id uuid NULL,
    id uuid NOT NULL,
    payload json NULL,
    created_at timestamptz NULL,
    CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id)
);
CREATE INDEX audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);
comment on table auth.audit_log_entries is 'Auth: Audit trail for user actions.';

-- auth.schema_migrations definition

CREATE TABLE auth.schema_migrations (
    "version" varchar(255) NOT NULL,
    CONSTRAINT schema_migrations_pkey PRIMARY KEY ("version")
);
comment on table auth.schema_migrations is 'Auth: Manages updates to the auth system.';

INSERT INTO auth.schema_migrations (version)
VALUES  ('20171026211738'),
        ('20171026211808'),
        ('20171026211834'),
        ('20180103212743'),
        ('20180108183307'),
        ('20180119214651'),
        ('20180125194653');

-- Gets the User ID from the request cookie
create or replace function auth.uid() returns uuid as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$ language sql stable;

-- Gets the User ID from the request cookie
create or replace function auth.role() returns text as $$
  select nullif(current_setting('request.jwt.claim.role', true), '')::text;
$$ language sql stable;

-- Gets the User email
create or replace function auth.email() returns text as $$
  select nullif(current_setting('request.jwt.claim.email', true), '')::text;
$$ language sql stable;

-- usage on auth functions to API roles
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;

-- Supabase super admin

GRANT ALL PRIVILEGES ON SCHEMA auth TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO supabase_auth_admin;
ALTER USER supabase_auth_admin SET search_path = "auth";
ALTER table "auth".users OWNER TO supabase_auth_admin;
ALTER table "auth".refresh_tokens OWNER TO supabase_auth_admin;
ALTER table "auth".audit_log_entries OWNER TO supabase_auth_admin;
ALTER table "auth".instances OWNER TO supabase_auth_admin;
ALTER table "auth".schema_migrations OWNER TO supabase_auth_admin;

-- migrate:down
-- migrate:up

CREATE SCHEMA IF NOT EXISTS storage AUTHORIZATION supabase_admin;


ALTER USER supabase_storage_admin SET search_path = "storage";
GRANT CREATE ON DATABASE postgres TO supabase_storage_admin;

do $$
begin
  if exists (select from pg_namespace where nspname = 'storage') then
    grant usage on schema storage to postgres, anon, authenticated, service_role;
    alter default privileges in schema storage grant all on tables to postgres, anon, authenticated, service_role;
    alter default privileges in schema storage grant all on functions to postgres, anon, authenticated, service_role;
    alter default privileges in schema storage grant all on sequences to postgres, anon, authenticated, service_role;

    grant all on schema storage to supabase_storage_admin with grant option;
  end if;
end $$;

-- migrate:down

set storage.install_roles = false;

DO $$
BEGIN
    IF NOT EXISTS(SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'storage') THEN
        CREATE SCHEMA storage;
    END IF;
END$$;

DO $$
DECLARE
    install_roles text = COALESCE(current_setting('storage.install_roles', true), 'true');
    anon_role text = COALESCE(current_setting('storage.anon_role', true), 'anon');
    authenticated_role text = COALESCE(current_setting('storage.authenticated_role', true), 'authenticated');
    service_role text = COALESCE(current_setting('storage.service_role', true), 'service_role');
BEGIN
    IF install_roles != 'true' THEN
        RETURN;
    END IF;

  -- Install ROLES
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = anon_role) THEN
        EXECUTE 'CREATE ROLE ' || anon_role || ' NOLOGIN NOINHERIT';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = authenticated_role  ) THEN
        EXECUTE 'CREATE ROLE ' || authenticated_role || ' NOLOGIN NOINHERIT';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = service_role) THEN
        EXECUTE 'CREATE ROLE ' || service_role || ' NOLOGIN NOINHERIT bypassrls';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
        EXECUTE 'CREATE USER authenticator NOINHERIT';
    END IF;


  EXECUTE 'grant ' || anon_role || ' to authenticator';
  EXECUTE 'grant ' || authenticated_role || ' to authenticator';
  EXECUTE 'grant ' || service_role || ' to authenticator';
  grant postgres          to authenticator;

  EXECUTE 'grant usage on schema storage to postgres,' ||  anon_role || ',' || authenticated_role || ',' || service_role;

  EXECUTE 'alter default privileges in schema storage grant all on tables to postgres,' ||  anon_role || ',' || authenticated_role || ',' || service_role;
  EXECUTE 'alter default privileges in schema storage grant all on functions to postgres,' ||  anon_role || ',' || authenticated_role || ',' || service_role;
  EXECUTE 'alter default privileges in schema storage grant all on sequences to postgres,' ||  anon_role || ',' || authenticated_role || ',' || service_role;
END$$;


CREATE TABLE IF NOT EXISTS "storage"."migrations" (
  id integer PRIMARY KEY,
  name varchar(100) UNIQUE NOT NULL,
  hash varchar(40) NOT NULL, -- sha1 hex encoded hash of the file name and contents, to ensure it hasn't been altered since applying the migration
  executed_at timestamp DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS "storage"."buckets" (
    "id" text not NULL,
    "name" text NOT NULL,
    "owner" uuid,
    "created_at" timestamptz DEFAULT now(),
    "updated_at" timestamptz DEFAULT now(),
    PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX IF NOT EXISTS "bname" ON "storage"."buckets" USING BTREE ("name");

CREATE TABLE IF NOT EXISTS "storage"."objects" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "bucket_id" text,
    "name" text,
    "owner" uuid,
    "created_at" timestamptz DEFAULT now(),
    "updated_at" timestamptz DEFAULT now(),
    "last_accessed_at" timestamptz DEFAULT now(),
    "metadata" jsonb,
    CONSTRAINT "objects_bucketId_fkey" FOREIGN KEY ("bucket_id") REFERENCES "storage"."buckets"("id"),
    PRIMARY KEY ("id")
);
-- Single-version uniqueness of (bucket_id, name). Migration 0072
-- (drop-bucketid-objname-index) removes it once objects may carry several
-- versions per name. A replay must not bring the index back on a schema that
-- has moved past the single-version era: rebuilding it takes a ShareLock on
-- storage.objects for the whole build (0002 runs in a transaction), fails
-- outright if several rows share a name, and is dropped again anyway when
-- 0072 replays. The sentinel is the replacement index from 0066
-- (objects-current-version-index): the earliest schema marker of that era,
-- never dropped or renamed by a later migration. Guarding on the trigger
-- function from 0073 left a window — 0072 applied, 0073 not — where a replay
-- rebuilt the doomed index. The migrations bookkeeping table cannot be the
-- guard: resetMigration deletes its rows without undoing schema, so it lies
-- during exactly the replays this guard exists for.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'storage'
          AND c.relname = 'idx_objects_current_version'
          AND c.relkind = 'i'
    ) THEN
        CREATE UNIQUE INDEX IF NOT EXISTS "bucketid_objname" ON "storage"."objects" USING BTREE ("bucket_id","name");
    END IF;
END$$;
CREATE INDEX IF NOT EXISTS name_prefix_search ON storage.objects(name text_pattern_ops);

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION storage.foldername(name text)
 RETURNS text[]
 LANGUAGE plpgsql
AS $function$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[1:array_length(_parts,1)-1];
END
$function$;

CREATE OR REPLACE FUNCTION storage.filename(name text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[array_length(_parts,1)];
END
$function$;

CREATE OR REPLACE FUNCTION storage.extension(name text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
_parts text[];
_filename text;
BEGIN
	select string_to_array(name, '/') into _parts;
	select _parts[array_length(_parts,1)] into _filename;
	-- @todo return the last part instead of 2
	return reverse(split_part(reverse(_filename), '.', 1));
END
$function$;

-- @todo can this query be optimised further?
CREATE OR REPLACE FUNCTION storage.search(prefix text, bucketname text, limits int DEFAULT 100, levels int DEFAULT 1, offsets int DEFAULT 0)
 RETURNS TABLE (
    name text,
    id uuid,
    updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ,
    metadata jsonb
  )
 LANGUAGE plpgsql
AS $function$
BEGIN
	return query
		with files_folders as (
			select ((string_to_array(objects.name, '/'))[levels]) as folder
			from objects
			where objects.name ilike prefix || '%'
			and bucket_id = bucketname
			GROUP by folder
			limit limits
			offset offsets
		)
		select files_folders.folder as name, objects.id, objects.updated_at, objects.created_at, objects.last_accessed_at, objects.metadata from files_folders
		left join objects
		on prefix || files_folders.folder = objects.name and objects.bucket_id=bucketname;
END
$function$;


DO $$
DECLARE
    install_roles text = COALESCE(current_setting('storage.install_roles', true), 'true');
    super_user text = COALESCE(current_setting('storage.super_user', true), 'supabase_storage_admin');
BEGIN
    IF install_roles != 'true' THEN
        RETURN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = super_user) THEN
        EXECUTE 'CREATE USER ' || super_user || ' NOINHERIT CREATEROLE LOGIN NOREPLICATION';
    END IF;

    -- Grant privileges to Super User
    EXECUTE 'GRANT ALL PRIVILEGES ON SCHEMA storage TO ' || super_user;
    EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA storage TO ' || super_user;
    EXECUTE 'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA storage TO ' || super_user;

    IF super_user != 'postgres' THEN
        EXECUTE 'ALTER USER ' || super_user || ' SET search_path = "storage"';
    END IF;

    EXECUTE 'ALTER table "storage".objects owner to ' || super_user;
    EXECUTE 'ALTER table "storage".buckets owner to ' || super_user;
    EXECUTE 'ALTER table "storage".migrations OWNER TO ' || super_user;
    EXECUTE 'ALTER function "storage".foldername(text) owner to ' || super_user;
    EXECUTE 'ALTER function "storage".filename(text) owner to ' || super_user;
    EXECUTE 'ALTER function "storage".extension(text) owner to ' || super_user;
    EXECUTE 'ALTER function "storage".search(text,text,int,int,int) owner to ' || super_user;
END$$;

ALTER TABLE storage.buckets ADD COLUMN if not exists "public" boolean default false;
alter table storage.buckets add column if not exists max_file_size_kb int default null;
alter table storage.buckets add column if not exists allowed_mime_types text[] default null;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'buckets' AND column_name = 'max_file_size_kb') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'buckets' AND column_name = 'file_size_limit') THEN
            ALTER TABLE storage.buckets RENAME COLUMN max_file_size_kb TO file_size_limit;
            ALTER TABLE storage.buckets ALTER COLUMN file_size_limit TYPE bigint;
        ELSE
            ALTER TABLE storage.buckets DROP COLUMN max_file_size_kb;
        END IF;
    END IF;
END$$;

-- update auth functions

create or replace function auth.uid()
returns uuid
language sql stable
as $$
  select
  coalesce(
    current_setting('request.jwt.claim.sub', true),
    (current_setting('request.jwt.claims', true)::jsonb ->> 'sub')
  )::uuid
$$;

create or replace function auth.role()
returns text
language sql stable
as $$
  select
  coalesce(
    current_setting('request.jwt.claim.role', true),
    (current_setting('request.jwt.claims', true)::jsonb ->> 'role')
  )::text
$$;

create or replace function auth.email()
returns text
language sql stable
as $$
  select
  coalesce(
    current_setting('request.jwt.claim.email', true),
    (current_setting('request.jwt.claims', true)::jsonb ->> 'email')
  )::text
$$;

-- update auth.uid()

create or replace function auth.uid()
returns uuid
language sql stable
as $$
  select
  nullif(
    coalesce(
      current_setting('request.jwt.claim.sub', true),
      (current_setting('request.jwt.claims', true)::jsonb ->> 'sub')
    ),
    ''
  )::uuid
$$;

-- update auth functions

create or replace function auth.uid()
returns uuid
language sql stable
as $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;

create or replace function auth.role()
returns text
language sql stable
as $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;

create or replace function auth.email()
returns text
language sql stable
as $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;

-- add auth.jwt function

comment on function auth.uid() is 'Deprecated. Use auth.jwt() -> ''sub'' instead.';
comment on function auth.role() is 'Deprecated. Use auth.jwt() -> ''role'' instead.';
comment on function auth.email() is 'Deprecated. Use auth.jwt() -> ''email'' instead.';

create or replace function auth.jwt()
returns jsonb
language sql stable
as $$
  select
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$$;

CREATE OR REPLACE FUNCTION rls_auto_enable()
RETURNS EVENT_TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
          RAISE;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;

DROP EVENT TRIGGER IF EXISTS ensure_rls;
CREATE EVENT TRIGGER ensure_rls
ON ddl_command_end
WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
EXECUTE FUNCTION rls_auto_enable();

create extension pgtap with schema extensions;
