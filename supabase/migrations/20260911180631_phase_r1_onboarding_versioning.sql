-- Remediation R1: add explicit onboarding/ruleset completion provenance.
-- Historical completions are labelled, not reinterpreted as current.

alter table public.onboarding_sessions
  add column completed_onboarding_version text,
  add column completed_ruleset_version text;

alter table public.onboarding_sessions
  add constraint onboarding_sessions_completion_versions_paired check (
    (completed_onboarding_version is null and completed_ruleset_version is null)
    or (
      completed_onboarding_version is not null
      and completed_ruleset_version is not null
      and completed_onboarding_version = btrim(completed_onboarding_version)
      and completed_ruleset_version = btrim(completed_ruleset_version)
      and char_length(completed_onboarding_version) between 1 and 100
      and char_length(completed_ruleset_version) between 1 and 100
    )
  ),
  add constraint onboarding_sessions_completion_versions_require_completion check (
    completed_onboarding_version is null or status = 'completed'
  );

create table public.onboarding_completion_records (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  onboarding_version text not null,
  ruleset_version text not null,
  completed_steps text[] not null,
  initial_plan_request_id uuid not null,
  session_revision bigint not null,
  record_source text not null,
  completed_at timestamptz not null,
  recorded_at timestamptz not null default statement_timestamp(),

  constraint onboarding_completion_records_request_fkey
    foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id)
    on delete restrict,
  constraint onboarding_completion_records_version_values_valid check (
    onboarding_version = btrim(onboarding_version)
    and ruleset_version = btrim(ruleset_version)
    and char_length(onboarding_version) between 1 and 100
    and char_length(ruleset_version) between 1 and 100
  ),
  constraint onboarding_completion_records_steps_valid check (
    completed_steps <@ array[
      'profile',
      'history',
      'goal',
      'zones',
      'review'
    ]::text[]
  ),
  constraint onboarding_completion_records_revision_positive
    check (session_revision > 0),
  constraint onboarding_completion_records_source_valid check (
    record_source in ('legacy_session_backfill', 'current_completion')
  ),
  unique (athlete_id, onboarding_version, ruleset_version)
);

create index onboarding_completion_records_request_owner_idx
on public.onboarding_completion_records (initial_plan_request_id, athlete_id);

alter table public.onboarding_completion_records enable row level security;
alter table public.onboarding_completion_records force row level security;

revoke all on table public.onboarding_completion_records
from public, anon, authenticated, service_role;
grant select, insert on table public.onboarding_completion_records to authenticated;

create policy onboarding_completion_records_select_own
on public.onboarding_completion_records for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy onboarding_completion_records_insert_own
on public.onboarding_completion_records for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create trigger onboarding_completion_records_require_rpc
before insert or update or delete on public.onboarding_completion_records
for each row execute function private.require_critical_write_context();

create function private.protect_onboarding_completion_versions()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if (
       new.completed_onboarding_version is distinct from
         old.completed_onboarding_version
       or new.completed_ruleset_version is distinct from
         old.completed_ruleset_version
     )
     and current_setting('start23.critical_write', true) is distinct from 'on'
  then
    raise exception 'onboarding version changes require the completion RPC'
      using errcode = '42501';
  end if;
  return new;
end;
$$;

revoke execute on function private.protect_onboarding_completion_versions()
from public, anon, authenticated, service_role;

create trigger onboarding_sessions_protect_completion_versions
before update on public.onboarding_sessions
for each row execute function private.protect_onboarding_completion_versions();

do $$
begin
  perform set_config('start23.critical_write', 'on', true);

  insert into public.onboarding_completion_records (
    athlete_id,
    onboarding_version,
    ruleset_version,
    completed_steps,
    initial_plan_request_id,
    session_revision,
    record_source,
    completed_at
  )
  select
    session.athlete_id,
    'legacy-unversioned',
    coalesce(request.ruleset_version, 'legacy-unversioned'),
    session.completed_steps,
    session.initial_plan_request_id,
    session.revision,
    'legacy_session_backfill',
    session.completed_at
  from public.onboarding_sessions session
  left join public.initial_plan_requests request
    on request.id = session.initial_plan_request_id
   and request.athlete_id = session.athlete_id
  where session.status = 'completed'
    and session.initial_plan_request_id is not null
    and session.completed_at is not null
  on conflict (athlete_id, onboarding_version, ruleset_version) do nothing;

  update public.onboarding_sessions session
  set
    completed_onboarding_version = 'legacy-unversioned',
    completed_ruleset_version = coalesce(
      (
        select request.ruleset_version
        from public.initial_plan_requests request
        where request.id = session.initial_plan_request_id
          and request.athlete_id = session.athlete_id
      ),
      'legacy-unversioned'
    )
  where session.status = 'completed'
    and session.completed_onboarding_version is null;
end;
$$;

create function public.complete_current_onboarding()
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_request_id uuid;
  v_session_revision bigint;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  if exists (
    select 1
    from public.onboarding_sessions session
    where session.athlete_id = v_athlete_id
      and session.status = 'completed'
      and (
        session.completed_onboarding_version is distinct from
          'phase-13-onboarding-v1'
        or session.completed_ruleset_version is distinct from
          'phase-13-joren-ruleset-1'
      )
  ) then
    raise exception 'version-aware onboarding upgrade is required'
      using errcode = '23514';
  end if;

  if not exists (
    select 1
    from public.athlete_profiles profile
    where profile.athlete_id = v_athlete_id
      and profile.date_of_birth is not null
      and profile.resting_heart_rate_bpm is not null
      and profile.timezone is not null
  ) then
    raise exception 'profile is incomplete' using errcode = '23514';
  end if;

  if (
    select count(*)
    from public.training_history_entries history
    where history.athlete_id = v_athlete_id
      and history.previous_month_weekly_minutes is not null
      and history.baseline_model_version = 'phase-13-joren-ruleset-1'
  ) <> 3 then
    raise exception 'previous-month training history is incomplete'
      using errcode = '23514';
  end if;

  if not exists (
    select 1
    from public.goals goal
    where goal.athlete_id = v_athlete_id
      and goal.status = 'active'
  ) then
    raise exception 'primary race goal is missing' using errcode = '23514';
  end if;

  if (
    select count(distinct configured.discipline)
    from (
      select profile.discipline
      from public.zone_profile_versions profile
      where profile.athlete_id = v_athlete_id
        and profile.status = 'active'
      union
      select setup.discipline
      from public.discipline_zone_setups setup
      where setup.athlete_id = v_athlete_id
        and setup.setup_status in (
          'configured',
          'test_pending',
          'calibration_pending'
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
              or (setup.discipline = 'swim' and setup.guidance_mode = 'pace')
            )
          )
        )
    ) configured
  ) <> 3 then
    raise exception 'current discipline guidance setup is incomplete'
      using errcode = '23514';
  end if;

  v_request_id := public.complete_onboarding();

  if not exists (
    select 1
    from public.initial_plan_requests request
    where request.id = v_request_id
      and request.athlete_id = v_athlete_id
      and request.ruleset_version = 'phase-13-joren-ruleset-1'
  ) then
    raise exception 'current ruleset planning request is required'
      using errcode = '23514';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.onboarding_sessions
  set
    completed_onboarding_version = 'phase-13-onboarding-v1',
    completed_ruleset_version = 'phase-13-joren-ruleset-1'
  where athlete_id = v_athlete_id
  returning revision into v_session_revision;

  insert into public.onboarding_completion_records (
    athlete_id,
    onboarding_version,
    ruleset_version,
    completed_steps,
    initial_plan_request_id,
    session_revision,
    record_source,
    completed_at
  )
  select
    session.athlete_id,
    session.completed_onboarding_version,
    session.completed_ruleset_version,
    session.completed_steps,
    session.initial_plan_request_id,
    v_session_revision,
    'current_completion',
    session.completed_at
  from public.onboarding_sessions session
  where session.athlete_id = v_athlete_id
  on conflict (athlete_id, onboarding_version, ruleset_version) do nothing;

  return v_request_id;
end;
$$;

revoke execute on function public.complete_current_onboarding()
from public, anon, service_role;
grant execute on function public.complete_current_onboarding() to authenticated;

comment on function public.complete_current_onboarding() is
  'R1 current-version completion entry point; legacy upgrade orchestration is deferred to R2.';
