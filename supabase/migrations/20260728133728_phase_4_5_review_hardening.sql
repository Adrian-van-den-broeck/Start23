-- Phase 4/5 review hardening for the already-deployed Phase 4 schema.

alter table public.initial_plan_requests
  add column if not exists input_snapshot jsonb,
  add column if not exists input_fingerprint text,
  add column if not exists refreshed_at timestamptz
    default statement_timestamp();

create or replace function private.build_planning_input_snapshot(
  p_athlete_id uuid
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'profile',
    (
      select jsonb_build_object(
        'athlete_id', profile.athlete_id,
        'date_of_birth', profile.date_of_birth,
        'height_cm', profile.height_cm,
        'weight_kg', profile.weight_kg,
        'resting_heart_rate_bpm', profile.resting_heart_rate_bpm,
        'motivation_text', profile.motivation_text,
        'motivation_tag', profile.motivation_tag,
        'timezone', profile.timezone,
        'revision', profile.revision
      )
      from public.athlete_profiles profile
      where profile.athlete_id = p_athlete_id
    ),
    'training_history',
    (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'discipline', history.discipline,
            'weekly_minutes', history.weekly_minutes,
            'experience_years', history.experience_years,
            'source', history.source,
            'confirmed_at', history.confirmed_at
          )
          order by history.discipline
        ),
        '[]'::jsonb
      )
      from public.training_history_entries history
      where history.athlete_id = p_athlete_id
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
        'feasibility_score', goal.feasibility_score,
        'target_date', goal.target_date,
        'race_discipline_profile', goal.race_discipline_profile,
        'revision', goal.revision
      )
      from public.goals goal
      where goal.athlete_id = p_athlete_id
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
            'metric',
            (
              select jsonb_build_object(
                'kind', metric.metric_kind,
                'value', metric.value
              )
              from public.zone_metrics metric
              where metric.zone_profile_id = profile.id
                and metric.athlete_id = p_athlete_id
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
                and boundary.athlete_id = p_athlete_id
            )
          )
          order by profile.discipline
        ),
        '[]'::jsonb
      )
      from public.zone_profile_versions profile
      where profile.athlete_id = p_athlete_id
        and profile.status = 'active'
    ),
    'ruleset_version',
    'phase-3-ruleset-2'
  );
$$;

revoke execute
on function private.build_planning_input_snapshot(uuid)
from public, anon, authenticated, service_role;

drop trigger if exists initial_plan_requests_set_input_snapshot
on public.initial_plan_requests;

do $$
declare
  request record;
  snapshot jsonb;
begin
  perform set_config('start23.critical_write', 'on', true);
  for request in
    select id, athlete_id
    from public.initial_plan_requests
  loop
    snapshot := private.build_planning_input_snapshot(request.athlete_id);
    update public.initial_plan_requests
    set
      input_snapshot = snapshot,
      input_fingerprint = md5(snapshot::text),
      refreshed_at = statement_timestamp()
    where id = request.id;
  end loop;
end;
$$;

alter table public.initial_plan_requests
  alter column input_snapshot set not null,
  alter column input_fingerprint set not null,
  alter column refreshed_at set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'initial_plan_requests_snapshot_valid'
      and conrelid = 'public.initial_plan_requests'::regclass
  ) then
    alter table public.initial_plan_requests
      add constraint initial_plan_requests_snapshot_valid
      check (
        jsonb_typeof(input_snapshot) = 'object'
        and input_snapshot ?& array[
          'profile',
          'training_history',
          'goal',
          'zones',
          'ruleset_version'
        ]
        and input_fingerprint = md5(input_snapshot::text)
      );
  end if;
end;
$$;

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
    v_snapshot := private.build_planning_input_snapshot(new.athlete_id);
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

revoke execute
on function private.set_initial_plan_input_snapshot()
from public, anon, authenticated, service_role;

create trigger initial_plan_requests_set_input_snapshot
before insert or update on public.initial_plan_requests
for each row execute function private.set_initial_plan_input_snapshot();

create or replace function private.refresh_pending_planning_input()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := case
    when tg_op = 'DELETE' then old.athlete_id
    else new.athlete_id
  end;
begin
  if exists (
    select 1
    from public.initial_plan_requests request
    where request.athlete_id = v_athlete_id
      and request.status = 'pending'
  ) then
    perform set_config('start23.critical_write', 'on', true);
    update public.initial_plan_requests
    set refreshed_at = statement_timestamp()
    where athlete_id = v_athlete_id
      and status = 'pending';
  end if;
  return null;
end;
$$;

revoke execute
on function private.refresh_pending_planning_input()
from public, anon, authenticated, service_role;

drop trigger if exists athlete_profiles_refresh_pending_planning_input
on public.athlete_profiles;
create trigger athlete_profiles_refresh_pending_planning_input
after update on public.athlete_profiles
for each row execute function private.refresh_pending_planning_input();

drop trigger if exists training_history_refresh_pending_planning_input
on public.training_history_entries;
create trigger training_history_refresh_pending_planning_input
after insert or update or delete on public.training_history_entries
for each row execute function private.refresh_pending_planning_input();

drop trigger if exists goals_refresh_pending_planning_input
on public.goals;
create trigger goals_refresh_pending_planning_input
after insert or update or delete on public.goals
for each row execute function private.refresh_pending_planning_input();

drop trigger if exists zone_profiles_refresh_pending_planning_input
on public.zone_profile_versions;
create trigger zone_profiles_refresh_pending_planning_input
after insert or update or delete on public.zone_profile_versions
for each row execute function private.refresh_pending_planning_input();

create or replace function private.require_trusted_zone_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.setup_method = 'fallback' then
    if current_setting('start23.trusted_fallback', true) is distinct from 'on' then
      raise exception 'fallback zones require the trusted backend RPC'
        using errcode = '42501';
    end if;
    if new.requires_review is distinct from true
       or new.review_reason <> 'fallback_unvalidated'
       or new.ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'fallback review metadata is server-controlled'
        using errcode = '23514';
    end if;
  elsif new.setup_method = 'manual' then
    if new.requires_review is distinct from true
       or new.review_reason <> 'soft_range_not_configured'
       or new.ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'manual zone review metadata is server-controlled'
        using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

revoke execute
on function private.require_trusted_zone_metadata()
from public, anon, authenticated, service_role;

drop trigger if exists zone_profiles_require_trusted_metadata
on public.zone_profile_versions;
create trigger zone_profiles_require_trusted_metadata
before insert on public.zone_profile_versions
for each row execute function private.require_trusted_zone_metadata();

create or replace function public.save_fallback_zone_profile(
  p_athlete_id uuid,
  p_discipline text,
  p_boundaries jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
  v_original_claims text := current_setting('request.jwt.claims', true);
  v_original_claim_sub text := current_setting('request.jwt.claim.sub', true);
  v_original_claim_role text := current_setting('request.jwt.claim.role', true);
  v_original_trusted_fallback text :=
    current_setting('start23.trusted_fallback', true);
  v_original_critical_write text :=
    current_setting('start23.critical_write', true);
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_athlete_id is null
     or not exists (
       select 1 from auth.users where id = p_athlete_id
     ) then
    raise exception 'athlete not found' using errcode = 'P0002';
  end if;

  perform set_config(
    'request.jwt.claims',
    jsonb_build_object(
      'sub', p_athlete_id,
      'role', 'authenticated'
    )::text,
    true
  );
  perform set_config('request.jwt.claim.sub', p_athlete_id::text, true);
  perform set_config('request.jwt.claim.role', 'authenticated', true);
  perform set_config('start23.trusted_fallback', 'on', true);

  select public.save_zone_profile(
    p_discipline,
    'fallback',
    null,
    null,
    p_boundaries,
    true,
    'fallback_unvalidated',
    'phase-3-ruleset-2'
  )
  into v_result;

  perform set_config(
    'request.jwt.claims',
    coalesce(v_original_claims, ''),
    true
  );
  perform set_config(
    'request.jwt.claim.sub',
    coalesce(v_original_claim_sub, ''),
    true
  );
  perform set_config(
    'request.jwt.claim.role',
    coalesce(v_original_claim_role, ''),
    true
  );
  perform set_config(
    'start23.trusted_fallback',
    coalesce(v_original_trusted_fallback, ''),
    true
  );
  perform set_config(
    'start23.critical_write',
    coalesce(v_original_critical_write, ''),
    true
  );

  return v_result;
end;
$$;

revoke all on function public.save_fallback_zone_profile(uuid, text, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.save_fallback_zone_profile(uuid, text, jsonb)
to service_role;

create index if not exists onboarding_sessions_initial_plan_request_idx
on public.onboarding_sessions (initial_plan_request_id, athlete_id)
where initial_plan_request_id is not null;

create index if not exists change_proposals_target_owner_idx
on public.change_proposals (target_zone_profile_id, athlete_id);

create index if not exists change_proposals_base_owner_idx
on public.change_proposals (base_zone_profile_id, athlete_id)
where base_zone_profile_id is not null;
