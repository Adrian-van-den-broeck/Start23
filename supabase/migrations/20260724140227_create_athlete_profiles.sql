create schema if not exists private;

revoke all on schema private from public, anon, authenticated;

create table public.athlete_profiles (
  athlete_id uuid primary key
    references auth.users (id)
    on delete cascade,
  timezone text not null default 'UTC',
  onboarding_status text not null default 'not_started',
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  constraint athlete_profiles_timezone_not_blank
    check (
      char_length(btrim(timezone)) between 1 and 100
      and timezone = btrim(timezone)
    ),
  constraint athlete_profiles_onboarding_status_valid
    check (
      onboarding_status in ('not_started', 'in_progress', 'completed')
    ),
  constraint athlete_profiles_revision_positive
    check (revision > 0)
);

comment on table public.athlete_profiles is
  'One private application profile for each Supabase Auth athlete.';
comment on column public.athlete_profiles.athlete_id is
  'Immutable owner identity derived from the verified Supabase token.';
comment on column public.athlete_profiles.timezone is
  'Validated IANA timezone name; full validation is performed by FastAPI.';
comment on column public.athlete_profiles.onboarding_status is
  'Resumable onboarding state; completion is validated by FastAPI.';

create function private.set_athlete_profile_update_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.athlete_id is distinct from old.athlete_id then
    raise exception 'athlete_id is immutable'
      using errcode = '23514';
  end if;

  new.revision := old.revision + 1;
  new.updated_at := statement_timestamp();
  return new;
end;
$$;

revoke execute
on function private.set_athlete_profile_update_metadata()
from public, anon, authenticated, service_role;

create trigger athlete_profiles_set_update_metadata
before update on public.athlete_profiles
for each row
execute function private.set_athlete_profile_update_metadata();

alter table public.athlete_profiles enable row level security;
alter table public.athlete_profiles force row level security;

revoke all on table public.athlete_profiles
from public, anon, authenticated, service_role;

grant select on table public.athlete_profiles to authenticated;
grant insert (athlete_id, timezone, onboarding_status)
on table public.athlete_profiles to authenticated;
grant update (timezone, onboarding_status)
on table public.athlete_profiles to authenticated;

create policy athlete_profiles_select_own
on public.athlete_profiles
for select
to authenticated
using (
  (select auth.uid()) is not null
  and (select auth.uid()) = athlete_id
);

create policy athlete_profiles_insert_own
on public.athlete_profiles
for insert
to authenticated
with check (
  (select auth.uid()) is not null
  and (select auth.uid()) = athlete_id
);

create policy athlete_profiles_update_own
on public.athlete_profiles
for update
to authenticated
using (
  (select auth.uid()) is not null
  and (select auth.uid()) = athlete_id
)
with check (
  (select auth.uid()) is not null
  and (select auth.uid()) = athlete_id
);
