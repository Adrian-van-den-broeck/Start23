alter table public.athlete_profiles
  add column date_of_birth date,
  add column height_cm numeric(5, 2),
  add column weight_kg numeric(5, 2),
  add column resting_heart_rate_bpm smallint,
  add column motivation_text text,
  add column motivation_tag text;

alter table public.athlete_profiles
  add constraint athlete_profiles_height_positive
    check (height_cm is null or height_cm > 0),
  add constraint athlete_profiles_weight_positive
    check (weight_kg is null or weight_kg > 0),
  add constraint athlete_profiles_resting_heart_rate_positive
    check (
      resting_heart_rate_bpm is null
      or resting_heart_rate_bpm > 0
    ),
  add constraint athlete_profiles_motivation_text_valid
    check (
      motivation_text is null
      or (
        char_length(btrim(motivation_text)) between 1 and 1000
        and motivation_text = btrim(motivation_text)
      )
    ),
  add constraint athlete_profiles_motivation_tag_valid
    check (
      motivation_tag is null
      or (
        char_length(btrim(motivation_tag)) between 1 and 50
        and motivation_tag = btrim(motivation_tag)
      )
    );

grant update (
  date_of_birth,
  height_cm,
  weight_kg,
  resting_heart_rate_bpm,
  motivation_text,
  motivation_tag
)
on table public.athlete_profiles
to authenticated;

grant insert (
  date_of_birth,
  height_cm,
  weight_kg,
  resting_heart_rate_bpm,
  motivation_text,
  motivation_tag
)
on table public.athlete_profiles
to authenticated;

create table public.onboarding_sessions (
  athlete_id uuid primary key
    references auth.users (id)
    on delete cascade,
  status text not null default 'in_progress',
  current_step text not null default 'profile',
  completed_steps text[] not null default '{}',
  revision bigint not null default 1,
  initial_plan_request_id uuid,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  completed_at timestamptz,

  constraint onboarding_sessions_status_valid
    check (status in ('in_progress', 'completed')),
  constraint onboarding_sessions_current_step_valid
    check (
      current_step in (
        'profile',
        'history',
        'goal',
        'zones',
        'review',
        'completed'
      )
    ),
  constraint onboarding_sessions_completed_steps_valid
    check (
      completed_steps <@ array[
        'profile',
        'history',
        'goal',
        'zones',
        'review'
      ]::text[]
    ),
  constraint onboarding_sessions_revision_positive
    check (revision > 0),
  constraint onboarding_sessions_completion_consistent
    check (
      (status = 'completed' and completed_at is not null)
      or (status = 'in_progress' and completed_at is null)
    )
);

create table public.training_history_entries (
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  discipline text not null,
  weekly_minutes integer not null,
  experience_years numeric(4, 1) not null,
  source text not null default 'athlete',
  confirmed_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  primary key (athlete_id, discipline),
  constraint training_history_discipline_valid
    check (discipline in ('swim', 'bike', 'run')),
  constraint training_history_weekly_minutes_valid
    check (weekly_minutes between 0 and 10080),
  constraint training_history_experience_years_valid
    check (experience_years between 0 and 100),
  constraint training_history_source_valid
    check (source = 'athlete')
);

create table public.goals (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  priority text not null default 'A',
  goal_type text not null default 'race',
  title text not null,
  specific_description text not null,
  measurable_outcome text not null,
  feasibility_score smallint not null,
  target_date date not null,
  race_discipline_profile text[] not null,
  status text not null default 'active',
  revision bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  constraint goals_priority_valid check (priority = 'A'),
  constraint goals_type_valid check (goal_type = 'race'),
  constraint goals_title_valid
    check (
      char_length(btrim(title)) between 1 and 120
      and title = btrim(title)
    ),
  constraint goals_specific_description_valid
    check (
      char_length(btrim(specific_description)) between 1 and 1000
      and specific_description = btrim(specific_description)
    ),
  constraint goals_measurable_outcome_valid
    check (
      char_length(btrim(measurable_outcome)) between 1 and 500
      and measurable_outcome = btrim(measurable_outcome)
    ),
  constraint goals_feasibility_score_valid
    check (feasibility_score between 1 and 10),
  constraint goals_race_disciplines_valid
    check (
      cardinality(race_discipline_profile) between 1 and 3
      and race_discipline_profile <@ array['swim', 'bike', 'run']::text[]
    ),
  constraint goals_status_valid
    check (status in ('active', 'superseded')),
  constraint goals_revision_positive check (revision > 0)
);

create unique index goals_one_active_primary_race_per_athlete
on public.goals (athlete_id)
where status = 'active';

create table public.zone_profile_versions (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  discipline text not null,
  version integer not null,
  setup_method text not null,
  status text not null,
  validated boolean not null,
  fallback_active boolean not null,
  needs_testing boolean not null,
  requires_review boolean not null,
  review_reason text not null,
  ruleset_version text not null,
  effective_from timestamptz,
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (athlete_id, discipline, version),
  constraint zone_profile_discipline_valid
    check (discipline in ('swim', 'bike', 'run')),
  constraint zone_profile_version_positive check (version > 0),
  constraint zone_profile_setup_method_valid
    check (setup_method in ('manual', 'fallback')),
  constraint zone_profile_status_valid
    check (
      status in ('pending', 'active', 'superseded', 'rejected', 'expired')
    ),
  constraint zone_profile_flags_consistent
    check (
      (
        setup_method = 'manual'
        and validated
        and not fallback_active
        and not needs_testing
      )
      or (
        setup_method = 'fallback'
        and not validated
        and fallback_active
        and needs_testing
      )
    ),
  constraint zone_profile_effective_state_consistent
    check (
      (
        status in ('active', 'superseded')
        and effective_from is not null
      )
      or (
        status in ('pending', 'rejected', 'expired')
        and effective_from is null
      )
    ),
  constraint zone_profile_review_reason_valid
    check (
      review_reason in (
        'within_soft_range',
        'outside_soft_range',
        'soft_range_not_configured',
        'fallback_unvalidated'
      )
    ),
  constraint zone_profile_ruleset_version_valid
    check (
      ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
    )
);

create unique index zone_profiles_one_active_per_discipline
on public.zone_profile_versions (athlete_id, discipline)
where status = 'active';

create index zone_profiles_owner_idx
on public.zone_profile_versions (athlete_id);

create table public.zone_metrics (
  zone_profile_id uuid not null,
  athlete_id uuid not null,
  metric_kind text not null,
  value numeric not null,

  primary key (zone_profile_id),
  foreign key (zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id)
    on delete cascade,
  constraint zone_metrics_kind_valid
    check (
      metric_kind in (
        'swim_css_seconds_per_100m',
        'bike_ftp_watts',
        'bike_threshold_heart_rate_bpm',
        'run_threshold_pace_seconds_per_km',
        'run_lthr_bpm'
      )
    ),
  constraint zone_metrics_value_positive check (value > 0)
);

create index zone_metrics_owner_idx on public.zone_metrics (athlete_id);

create table public.zone_boundaries (
  zone_profile_id uuid not null,
  athlete_id uuid not null,
  zone_number smallint not null,
  lower_value numeric not null,
  upper_value numeric not null,

  primary key (zone_profile_id, zone_number),
  foreign key (zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id)
    on delete cascade,
  constraint zone_boundaries_zone_valid check (zone_number between 1 and 5),
  constraint zone_boundaries_ordered
    check (lower_value >= 0 and upper_value > lower_value)
);

create index zone_boundaries_owner_idx
on public.zone_boundaries (athlete_id);

create table public.change_proposals (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  kind text not null,
  target_zone_profile_id uuid,
  base_zone_profile_id uuid,
  state text not null default 'pending',
  reason_codes text[] not null,
  public_explanation text not null,
  ruleset_version text not null,
  created_at timestamptz not null default statement_timestamp(),
  decided_at timestamptz,
  applied_at timestamptz,

  foreign key (target_zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id),
  foreign key (base_zone_profile_id, athlete_id)
    references public.zone_profile_versions (id, athlete_id),
  constraint change_proposals_kind_valid check (kind = 'zone_update'),
  constraint change_proposals_target_required
    check (target_zone_profile_id is not null),
  constraint change_proposals_state_valid
    check (state in ('pending', 'approved', 'rejected', 'expired', 'applied')),
  constraint change_proposals_reason_codes_present
    check (cardinality(reason_codes) > 0),
  constraint change_proposals_explanation_valid
    check (
      char_length(btrim(public_explanation)) between 1 and 1000
      and public_explanation = btrim(public_explanation)
    ),
  constraint change_proposals_ruleset_version_valid
    check (ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$')
);

create index change_proposals_owner_idx
on public.change_proposals (athlete_id);

create unique index one_pending_proposal_per_zone_version
on public.change_proposals (target_zone_profile_id)
where state = 'pending';

create table public.initial_plan_requests (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references auth.users (id)
    on delete cascade,
  status text not null default 'pending',
  onboarding_revision bigint not null,
  ruleset_version text not null,
  input_snapshot jsonb not null,
  input_fingerprint text not null,
  created_at timestamptz not null default statement_timestamp(),
  refreshed_at timestamptz not null default statement_timestamp(),
  consumed_at timestamptz,

  unique (id, athlete_id),
  constraint initial_plan_requests_status_valid
    check (status in ('pending', 'consumed', 'cancelled')),
  constraint initial_plan_requests_revision_positive
    check (onboarding_revision > 0),
  constraint initial_plan_requests_ruleset_version_valid
    check (ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'),
  constraint initial_plan_requests_snapshot_valid
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
    ),
  constraint initial_plan_requests_consumed_consistent
    check (
      (status = 'consumed' and consumed_at is not null)
      or (status <> 'consumed' and consumed_at is null)
    )
);

create unique index one_pending_initial_plan_request_per_athlete
on public.initial_plan_requests (athlete_id)
where status = 'pending';

alter table public.onboarding_sessions
  add constraint onboarding_sessions_initial_plan_request_fkey
  foreign key (initial_plan_request_id, athlete_id)
  references public.initial_plan_requests (id, athlete_id);

create index onboarding_sessions_initial_plan_request_idx
on public.onboarding_sessions (initial_plan_request_id, athlete_id)
where initial_plan_request_id is not null;

create index change_proposals_target_owner_idx
on public.change_proposals (target_zone_profile_id, athlete_id);

create index change_proposals_base_owner_idx
on public.change_proposals (base_zone_profile_id, athlete_id)
where base_zone_profile_id is not null;

create function private.set_phase_4_update_metadata()
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

  if tg_table_name in ('onboarding_sessions', 'goals') then
    new.revision := old.revision + 1;
  end if;
  new.updated_at := statement_timestamp();
  return new;
end;
$$;

revoke execute
on function private.set_phase_4_update_metadata()
from public, anon, authenticated, service_role;

create trigger onboarding_sessions_set_update_metadata
before update on public.onboarding_sessions
for each row execute function private.set_phase_4_update_metadata();

create trigger goals_set_update_metadata
before update on public.goals
for each row execute function private.set_phase_4_update_metadata();

create trigger training_history_set_update_metadata
before update on public.training_history_entries
for each row execute function private.set_phase_4_update_metadata();

create function private.require_critical_write_context()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if current_setting('start23.critical_write', true) is distinct from 'on' then
    raise exception 'critical object writes require a Start23 RPC'
      using errcode = '42501';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

revoke execute
on function private.require_critical_write_context()
from public, anon, authenticated, service_role;

create trigger goals_require_rpc
before insert or update or delete on public.goals
for each row execute function private.require_critical_write_context();

create trigger zone_profiles_require_rpc
before insert or update or delete on public.zone_profile_versions
for each row execute function private.require_critical_write_context();

create trigger zone_metrics_require_rpc
before insert or update or delete on public.zone_metrics
for each row execute function private.require_critical_write_context();

create trigger zone_boundaries_require_rpc
before insert or update or delete on public.zone_boundaries
for each row execute function private.require_critical_write_context();

create trigger change_proposals_require_rpc
before insert or update or delete on public.change_proposals
for each row execute function private.require_critical_write_context();

create trigger initial_plan_requests_require_rpc
before insert or update or delete on public.initial_plan_requests
for each row execute function private.require_critical_write_context();

create function private.protect_onboarding_completion()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if tg_table_name = 'athlete_profiles' then
    if (
         (tg_op = 'INSERT' and new.onboarding_status = 'completed')
         or (
           tg_op = 'UPDATE'
           and new.onboarding_status <> old.onboarding_status
           and (
             new.onboarding_status = 'completed'
             or old.onboarding_status = 'completed'
           )
         )
       )
       and current_setting('start23.critical_write', true) is distinct from 'on'
    then
      raise exception 'onboarding completion requires the completion RPC'
        using errcode = '42501';
    end if;
  elsif tg_table_name = 'onboarding_sessions' then
    if (
         (tg_op = 'INSERT' and new.status = 'completed')
         or (
           tg_op = 'UPDATE'
           and new.status <> old.status
           and (new.status = 'completed' or old.status = 'completed')
         )
       )
       and current_setting('start23.critical_write', true) is distinct from 'on'
    then
      raise exception 'onboarding completion requires the completion RPC'
        using errcode = '42501';
    end if;
  end if;
  return new;
end;
$$;

revoke execute
on function private.protect_onboarding_completion()
from public, anon, authenticated, service_role;

create trigger athlete_profiles_protect_completion
before insert or update on public.athlete_profiles
for each row execute function private.protect_onboarding_completion();

create trigger onboarding_sessions_protect_completion
before insert or update on public.onboarding_sessions
for each row execute function private.protect_onboarding_completion();

create function private.build_planning_input_snapshot(p_athlete_id uuid)
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

create function private.set_initial_plan_input_snapshot()
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

create function private.refresh_pending_planning_input()
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

create trigger athlete_profiles_refresh_pending_planning_input
after update on public.athlete_profiles
for each row execute function private.refresh_pending_planning_input();

create trigger training_history_refresh_pending_planning_input
after insert or update or delete on public.training_history_entries
for each row execute function private.refresh_pending_planning_input();

create trigger goals_refresh_pending_planning_input
after insert or update or delete on public.goals
for each row execute function private.refresh_pending_planning_input();

create trigger zone_profiles_refresh_pending_planning_input
after insert or update or delete on public.zone_profile_versions
for each row execute function private.refresh_pending_planning_input();

alter table public.onboarding_sessions enable row level security;
alter table public.onboarding_sessions force row level security;
alter table public.training_history_entries enable row level security;
alter table public.training_history_entries force row level security;
alter table public.goals enable row level security;
alter table public.goals force row level security;
alter table public.zone_profile_versions enable row level security;
alter table public.zone_profile_versions force row level security;
alter table public.zone_metrics enable row level security;
alter table public.zone_metrics force row level security;
alter table public.zone_boundaries enable row level security;
alter table public.zone_boundaries force row level security;
alter table public.change_proposals enable row level security;
alter table public.change_proposals force row level security;
alter table public.initial_plan_requests enable row level security;
alter table public.initial_plan_requests force row level security;

revoke all on table public.onboarding_sessions
from public, anon, authenticated, service_role;
revoke all on table public.training_history_entries
from public, anon, authenticated, service_role;
revoke all on table public.goals
from public, anon, authenticated, service_role;
revoke all on table public.zone_profile_versions
from public, anon, authenticated, service_role;
revoke all on table public.zone_metrics
from public, anon, authenticated, service_role;
revoke all on table public.zone_boundaries
from public, anon, authenticated, service_role;
revoke all on table public.change_proposals
from public, anon, authenticated, service_role;
revoke all on table public.initial_plan_requests
from public, anon, authenticated, service_role;

grant select, insert, update
on table public.onboarding_sessions to authenticated;
grant select, insert, update, delete
on table public.training_history_entries to authenticated;
grant select, insert, update
on table public.goals to authenticated;
grant select, insert, update
on table public.zone_profile_versions to authenticated;
grant select, insert, update
on table public.zone_metrics to authenticated;
grant select, insert, update
on table public.zone_boundaries to authenticated;
grant select, insert, update
on table public.change_proposals to authenticated;
grant select, insert
on table public.initial_plan_requests to authenticated;

create policy onboarding_sessions_select_own
on public.onboarding_sessions for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy onboarding_sessions_insert_own
on public.onboarding_sessions for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy onboarding_sessions_update_own
on public.onboarding_sessions for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy training_history_select_own
on public.training_history_entries for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy training_history_insert_own
on public.training_history_entries for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy training_history_update_own
on public.training_history_entries for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy training_history_delete_own
on public.training_history_entries for delete to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy goals_select_own
on public.goals for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy goals_insert_own
on public.goals for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy goals_update_own
on public.goals for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy zone_profiles_select_own
on public.zone_profile_versions for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_profiles_insert_own
on public.zone_profile_versions for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_profiles_update_own
on public.zone_profile_versions for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy zone_metrics_select_own
on public.zone_metrics for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_metrics_insert_own
on public.zone_metrics for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_metrics_update_own
on public.zone_metrics for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy zone_boundaries_select_own
on public.zone_boundaries for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_boundaries_insert_own
on public.zone_boundaries for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy zone_boundaries_update_own
on public.zone_boundaries for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy change_proposals_select_own
on public.change_proposals for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy change_proposals_insert_own
on public.change_proposals for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy change_proposals_update_own
on public.change_proposals for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy initial_plan_requests_select_own
on public.initial_plan_requests for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy initial_plan_requests_insert_own
on public.initial_plan_requests for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create function public.save_primary_race_goal(
  p_goal_id uuid,
  p_title text,
  p_specific_description text,
  p_measurable_outcome text,
  p_feasibility_score smallint,
  p_target_date date,
  p_race_discipline_profile text[]
)
returns public.goals
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_goal public.goals;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_target_date <= current_date then
    raise exception 'target date must be in the future'
      using errcode = '23514';
  end if;
  perform set_config('start23.critical_write', 'on', true);

  if p_goal_id is null then
    insert into public.goals (
      athlete_id,
      title,
      specific_description,
      measurable_outcome,
      feasibility_score,
      target_date,
      race_discipline_profile
    )
    values (
      v_athlete_id,
      p_title,
      p_specific_description,
      p_measurable_outcome,
      p_feasibility_score,
      p_target_date,
      p_race_discipline_profile
    )
    returning * into v_goal;
  else
    update public.goals
    set
      title = p_title,
      specific_description = p_specific_description,
      measurable_outcome = p_measurable_outcome,
      feasibility_score = p_feasibility_score,
      target_date = p_target_date,
      race_discipline_profile = p_race_discipline_profile
    where id = p_goal_id
      and athlete_id = v_athlete_id
      and status = 'active'
    returning * into v_goal;

    if v_goal.id is null then
      raise exception 'goal not found' using errcode = 'P0002';
    end if;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps
  )
  values (
    v_athlete_id,
    'in_progress',
    'zones',
    array['profile', 'history', 'goal']::text[]
  )
  on conflict (athlete_id) do update
  set
    current_step = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.current_step
      else 'zones'
    end,
    completed_steps = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.completed_steps
      else (
        select array_agg(distinct step order by step)
        from unnest(
          public.onboarding_sessions.completed_steps
          || array['profile', 'history', 'goal']::text[]
        ) as steps(step)
      )
    end;

  return v_goal;
end;
$$;

create function public.save_zone_profile(
  p_discipline text,
  p_setup_method text,
  p_metric_kind text,
  p_metric_value numeric,
  p_boundaries jsonb,
  p_requires_review boolean,
  p_review_reason text,
  p_ruleset_version text
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_active_id uuid;
  v_profile_id uuid;
  v_proposal_id uuid;
  v_version integer;
  v_status text;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_boundaries) <> 'array'
     or jsonb_array_length(p_boundaries) <> 5 then
    raise exception 'exactly five boundaries are required'
      using errcode = '23514';
  end if;
  if p_setup_method = 'manual' then
    if p_metric_kind is null or p_metric_value is null then
      raise exception 'manual zones require a metric'
        using errcode = '23514';
    end if;
    if p_requires_review is distinct from true
       or p_review_reason <> 'soft_range_not_configured'
       or p_ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'manual zone review metadata is server-controlled'
        using errcode = '23514';
    end if;
    if not (
      (p_discipline = 'swim' and p_metric_kind = 'swim_css_seconds_per_100m')
      or (
        p_discipline = 'bike'
        and p_metric_kind in (
          'bike_ftp_watts',
          'bike_threshold_heart_rate_bpm'
        )
      )
      or (
        p_discipline = 'run'
        and p_metric_kind in (
          'run_threshold_pace_seconds_per_km',
          'run_lthr_bpm'
        )
      )
    ) then
      raise exception 'zone metric does not match discipline'
        using errcode = '23514';
    end if;
  elsif p_setup_method = 'fallback' then
    if current_setting('start23.trusted_fallback', true) is distinct from 'on' then
      raise exception 'fallback zones require the trusted backend RPC'
        using errcode = '42501';
    end if;
    if p_discipline = 'swim'
       or p_metric_kind is not null
       or p_metric_value is not null then
      raise exception 'fallback is heart-rate-only for bike or run'
        using errcode = '23514';
    end if;
    if p_requires_review is distinct from true
       or p_review_reason <> 'fallback_unvalidated'
       or p_ruleset_version <> 'phase-3-ruleset-2' then
      raise exception 'fallback review metadata is server-controlled'
        using errcode = '23514';
    end if;
  else
    raise exception 'unsupported zone setup method'
      using errcode = '23514';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':' || p_discipline, 0)
  );
  perform set_config('start23.critical_write', 'on', true);

  select id into v_active_id
  from public.zone_profile_versions
  where athlete_id = v_athlete_id
    and discipline = p_discipline
    and status = 'active';

  select coalesce(max(version), 0) + 1 into v_version
  from public.zone_profile_versions
  where athlete_id = v_athlete_id
    and discipline = p_discipline;

  v_status := case when v_active_id is null then 'active' else 'pending' end;

  insert into public.zone_profile_versions (
    athlete_id,
    discipline,
    version,
    setup_method,
    status,
    validated,
    fallback_active,
    needs_testing,
    requires_review,
    review_reason,
    ruleset_version,
    effective_from
  )
  values (
    v_athlete_id,
    p_discipline,
    v_version,
    p_setup_method,
    v_status,
    p_setup_method = 'manual',
    p_setup_method = 'fallback',
    p_setup_method = 'fallback',
    p_requires_review,
    p_review_reason,
    p_ruleset_version,
    case when v_status = 'active' then statement_timestamp() else null end
  )
  returning id into v_profile_id;

  if p_metric_kind is not null then
    insert into public.zone_metrics (
      zone_profile_id,
      athlete_id,
      metric_kind,
      value
    )
    values (
      v_profile_id,
      v_athlete_id,
      p_metric_kind,
      p_metric_value
    );
  elsif p_setup_method <> 'fallback' then
    raise exception 'manual zones require a metric'
      using errcode = '23514';
  end if;

  insert into public.zone_boundaries (
    zone_profile_id,
    athlete_id,
    zone_number,
    lower_value,
    upper_value
  )
  select
    v_profile_id,
    v_athlete_id,
    boundary.zone_number,
    boundary.lower_value,
    boundary.upper_value
  from jsonb_to_recordset(p_boundaries) as boundary(
    zone_number smallint,
    lower_value numeric,
    upper_value numeric
  );

  if (
    select count(distinct zone_number)
    from public.zone_boundaries
    where zone_profile_id = v_profile_id
  ) <> 5 then
    raise exception 'zones 1 through 5 are required'
      using errcode = '23514';
  end if;

  if p_setup_method = 'manual'
     and p_metric_kind in (
       'swim_css_seconds_per_100m',
       'run_threshold_pace_seconds_per_km'
     )
     and (
       p_metric_value <> trunc(p_metric_value)
       or exists (
         select 1
         from public.zone_boundaries
         where zone_profile_id = v_profile_id
           and (
             lower_value <> trunc(lower_value)
             or upper_value <> trunc(upper_value)
           )
       )
     ) then
    raise exception 'pace zones require whole seconds'
      using errcode = '23514';
  end if;

  if exists (
    select 1
    from public.zone_boundaries current_zone
    join public.zone_boundaries previous_zone
      on previous_zone.zone_profile_id = current_zone.zone_profile_id
      and previous_zone.zone_number = current_zone.zone_number - 1
    where current_zone.zone_profile_id = v_profile_id
      and (
        (
          p_setup_method = 'manual'
          and p_metric_kind in (
            'swim_css_seconds_per_100m',
            'run_threshold_pace_seconds_per_km'
          )
          and previous_zone.lower_value <> current_zone.upper_value
        )
        or (
          (
            p_setup_method = 'fallback'
            or p_metric_kind not in (
              'swim_css_seconds_per_100m',
              'run_threshold_pace_seconds_per_km'
            )
          )
          and previous_zone.upper_value <> current_zone.lower_value
        )
      )
  ) then
    raise exception 'zone boundaries must be contiguous'
      using errcode = '23514';
  end if;

  if v_status = 'pending' then
    insert into public.change_proposals (
      athlete_id,
      kind,
      target_zone_profile_id,
      base_zone_profile_id,
      reason_codes,
      public_explanation,
      ruleset_version
    )
    values (
      v_athlete_id,
      'zone_update',
      v_profile_id,
      v_active_id,
      array['zone_replacement_requires_approval'],
      'A new zone version is ready for your review. Your active zones have not changed.',
      p_ruleset_version
    )
    returning id into v_proposal_id;
  end if;

  return jsonb_build_object(
    'profile_id', v_profile_id,
    'version', v_version,
    'status', v_status,
    'proposal_id', v_proposal_id
  );
end;
$$;

create function public.save_fallback_zone_profile(
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

create function public.replace_training_history(p_entries jsonb)
returns setof public.training_history_entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_entries) <> 'array'
     or jsonb_array_length(p_entries) <> 3 then
    raise exception 'swim, bike, and run history are required'
      using errcode = '23514';
  end if;
  if (
    select count(distinct entry.discipline)
    from jsonb_to_recordset(p_entries) as entry(
      discipline text,
      weekly_minutes integer,
      experience_years numeric
    )
    where entry.discipline in ('swim', 'bike', 'run')
  ) <> 3 then
    raise exception 'history disciplines must be unique'
      using errcode = '23514';
  end if;

  delete from public.training_history_entries
  where athlete_id = v_athlete_id;

  insert into public.training_history_entries (
    athlete_id,
    discipline,
    weekly_minutes,
    experience_years
  )
  select
    v_athlete_id,
    entry.discipline,
    entry.weekly_minutes,
    entry.experience_years
  from jsonb_to_recordset(p_entries) as entry(
    discipline text,
    weekly_minutes integer,
    experience_years numeric
  );

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps
  )
  values (
    v_athlete_id,
    'in_progress',
    'goal',
    array['profile', 'history']::text[]
  )
  on conflict (athlete_id) do update
  set
    current_step = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.current_step
      else 'goal'
    end,
    completed_steps = case
      when public.onboarding_sessions.status = 'completed'
        then public.onboarding_sessions.completed_steps
      else (
        select array_agg(distinct step order by step)
        from unnest(
          public.onboarding_sessions.completed_steps
          || array['profile', 'history']::text[]
        ) as steps(step)
      )
    end;

  return query
  select *
  from public.training_history_entries
  where athlete_id = v_athlete_id
  order by discipline;
end;
$$;

create function public.approve_zone_proposal(
  p_proposal_id uuid,
  p_expected_base_zone_profile_id uuid
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_target_id uuid;
  v_base_id uuid;
  v_active_id uuid;
  v_discipline text;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select
    proposal.target_zone_profile_id,
    proposal.base_zone_profile_id,
    profile.discipline
  into
    v_target_id,
    v_base_id,
    v_discipline
  from public.change_proposals proposal
  join public.zone_profile_versions profile
    on profile.id = proposal.target_zone_profile_id
    and profile.athlete_id = proposal.athlete_id
  where proposal.id = p_proposal_id
    and proposal.athlete_id = v_athlete_id
    and proposal.kind = 'zone_update'
    and proposal.state = 'pending'
  for update of proposal;

  if v_target_id is null then
    raise exception 'pending zone proposal not found'
      using errcode = 'P0002';
  end if;
  if v_base_id is distinct from p_expected_base_zone_profile_id then
    raise exception 'zone proposal base is stale'
      using errcode = '40001';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(v_athlete_id::text || ':' || v_discipline, 0)
  );

  select id into v_active_id
  from public.zone_profile_versions
  where athlete_id = v_athlete_id
    and discipline = v_discipline
    and status = 'active'
  for update;

  if v_active_id is distinct from v_base_id then
    raise exception 'active zone version has changed'
      using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);

  update public.change_proposals
  set
    state = 'approved',
    decided_at = statement_timestamp()
  where id = p_proposal_id
    and athlete_id = v_athlete_id;

  update public.zone_profile_versions
  set status = 'superseded'
  where id = v_base_id
    and athlete_id = v_athlete_id
    and status = 'active';

  update public.zone_profile_versions
  set
    status = 'active',
    effective_from = statement_timestamp()
  where id = v_target_id
    and athlete_id = v_athlete_id
    and status = 'pending';

  if not found then
    raise exception 'target zone version is no longer pending'
      using errcode = '40001';
  end if;

  update public.change_proposals
  set
    state = 'applied',
    applied_at = statement_timestamp()
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and state = 'approved';

  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'applied',
    'active_zone_profile_id', v_target_id,
    'superseded_zone_profile_id', v_base_id
  );
end;
$$;

create function public.reject_zone_proposal(p_proposal_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_target_id uuid;
  v_base_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;

  select
    target_zone_profile_id,
    base_zone_profile_id
  into
    v_target_id,
    v_base_id
  from public.change_proposals
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and kind = 'zone_update'
    and state = 'pending'
  for update;

  if v_target_id is null then
    raise exception 'pending zone proposal not found'
      using errcode = 'P0002';
  end if;

  perform set_config('start23.critical_write', 'on', true);

  update public.zone_profile_versions
  set status = 'rejected'
  where id = v_target_id
    and athlete_id = v_athlete_id
    and status = 'pending';

  if not found then
    raise exception 'target zone version is no longer pending'
      using errcode = '40001';
  end if;

  update public.change_proposals
  set
    state = 'rejected',
    decided_at = statement_timestamp()
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and state = 'pending';

  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'rejected',
    'active_zone_profile_id', v_base_id,
    'superseded_zone_profile_id', null
  );
end;
$$;

create function public.complete_onboarding()
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
  where athlete_id = v_athlete_id
    and status = 'completed';

  if v_request_id is not null then
    return v_request_id;
  end if;

  if not exists (
    select 1
    from public.athlete_profiles
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
    select count(*)
    from public.training_history_entries
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
    select count(*)
    from public.zone_profile_versions
    where athlete_id = v_athlete_id and status = 'active'
  ) <> 3 then
    raise exception 'active discipline zones are incomplete' using errcode = '23514';
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
      athlete_id,
      onboarding_revision,
      ruleset_version
    )
    values (
      v_athlete_id,
      v_revision,
      'phase-3-ruleset-2'
    )
    returning id into v_request_id;
  end if;

  insert into public.onboarding_sessions (
    athlete_id,
    status,
    current_step,
    completed_steps,
    initial_plan_request_id,
    completed_at
  )
  values (
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

revoke all on function public.save_primary_race_goal(
  uuid,
  text,
  text,
  text,
  smallint,
  date,
  text[]
) from public, anon, service_role;
revoke all on function public.save_zone_profile(
  text,
  text,
  text,
  numeric,
  jsonb,
  boolean,
  text,
  text
) from public, anon, service_role;
revoke all on function public.save_fallback_zone_profile(uuid, text, jsonb)
from public, anon, authenticated;
revoke all on function public.complete_onboarding()
from public, anon, service_role;
revoke all on function public.replace_training_history(jsonb)
from public, anon, service_role;
revoke all on function public.approve_zone_proposal(uuid, uuid)
from public, anon, service_role;
revoke all on function public.reject_zone_proposal(uuid)
from public, anon, service_role;

grant execute on function public.save_primary_race_goal(
  uuid,
  text,
  text,
  text,
  smallint,
  date,
  text[]
) to authenticated;
grant execute on function public.save_zone_profile(
  text,
  text,
  text,
  numeric,
  jsonb,
  boolean,
  text,
  text
) to authenticated;
grant execute on function public.save_fallback_zone_profile(uuid, text, jsonb)
to service_role;
grant execute on function public.complete_onboarding()
to authenticated;
grant execute on function public.replace_training_history(jsonb)
to authenticated;
grant execute on function public.approve_zone_proposal(uuid, uuid)
to authenticated;
grant execute on function public.reject_zone_proposal(uuid)
to authenticated;
