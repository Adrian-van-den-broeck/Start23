-- Phase 8: durable structured weekly context and pending planning integration.

create table public.weekly_checkins (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  week_start date not null,
  timezone text not null,
  status text not null default 'open',
  context_revision integer not null default 0,
  plan_proposal_id uuid,
  started_at timestamptz not null default statement_timestamp(),
  completed_at timestamptz,
  updated_at timestamptz not null default statement_timestamp(),
  unique (id, athlete_id),
  unique (athlete_id, week_start),
  foreign key (plan_proposal_id, athlete_id)
    references public.change_proposals (id, athlete_id),
  constraint weekly_checkins_monday check (extract(isodow from week_start) = 1),
  constraint weekly_checkins_timezone_valid check (
    char_length(btrim(timezone)) between 1 and 100 and timezone = btrim(timezone)
  ),
  constraint weekly_checkins_status_valid check (status in ('open', 'completed')),
  constraint weekly_checkins_revision_valid check (context_revision >= 0),
  constraint weekly_checkins_completion_valid check (
    (status = 'open' and completed_at is null)
    or (status = 'completed' and completed_at is not null and plan_proposal_id is not null)
  )
);

create table public.weekly_checkin_contexts (
  id uuid primary key default gen_random_uuid(),
  checkin_id uuid not null,
  athlete_id uuid not null,
  revision integer not null,
  state text not null default 'draft',
  source text not null default 'structured_form',
  expires_at timestamptz not null,
  fingerprint text not null,
  payload jsonb not null,
  created_at timestamptz not null default statement_timestamp(),
  confirmed_at timestamptz,
  unique (id, athlete_id),
  unique (checkin_id, revision, athlete_id),
  foreign key (checkin_id, athlete_id)
    references public.weekly_checkins (id, athlete_id) on delete cascade,
  constraint weekly_checkin_contexts_revision_positive check (revision > 0),
  constraint weekly_checkin_contexts_state_valid check (
    state in ('draft', 'confirmed', 'superseded')
  ),
  constraint weekly_checkin_contexts_source_valid check (source = 'structured_form'),
  constraint weekly_checkin_contexts_fingerprint_valid check (
    fingerprint ~ '^[a-f0-9]{64}$'
  ),
  constraint weekly_checkin_contexts_payload_valid check (
    jsonb_typeof(payload) = 'object'
    and payload ?& array[
      'blocked_dates',
      'fatigue_level',
      'missed_workout_reasons',
      'recurring_activities_confirmed',
      'external_activities',
      'restrictions',
      'alarm_symptoms_acknowledged'
    ]
  ),
  constraint weekly_checkin_contexts_confirmation_valid check (
    (state = 'confirmed' and confirmed_at is not null)
    or (state <> 'confirmed' and confirmed_at is null)
  )
);

create unique index one_draft_context_per_checkin
on public.weekly_checkin_contexts (checkin_id)
where state = 'draft';

create unique index one_confirmed_context_per_checkin
on public.weekly_checkin_contexts (checkin_id)
where state = 'confirmed';

create index weekly_checkin_contexts_owner_idx
on public.weekly_checkin_contexts (athlete_id, checkin_id);

create table public.injury_restrictions (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  context_id uuid not null,
  discipline text not null,
  status text not null,
  allowed_intensity text not null,
  source text not null,
  start_at timestamptz not null,
  review_at timestamptz not null,
  professional_advice text,
  professional_advice_at timestamptz,
  athlete_plan_choice text not null,
  confirmed_at timestamptz not null,
  cleared_at timestamptz,
  unique (id, athlete_id),
  foreign key (context_id, athlete_id)
    references public.weekly_checkin_contexts (id, athlete_id) on delete cascade,
  constraint injury_restrictions_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint injury_restrictions_status_valid check (
    status in (
      'self_reported_limited',
      'self_reported_blocked',
      'professional_restricted',
      'clearance_required',
      'expired'
    )
  ),
  constraint injury_restrictions_intensity_valid check (
    allowed_intensity in ('none', 'low_only')
  ),
  constraint injury_restrictions_status_intensity_valid check (
    (status = 'self_reported_limited' and allowed_intensity = 'low_only')
    or (status <> 'self_reported_limited' and allowed_intensity = 'none')
  ),
  constraint injury_restrictions_source_valid check (
    source in ('athlete', 'physician', 'physiotherapist', 'other_professional')
  ),
  constraint injury_restrictions_timing_valid check (
    review_at >= start_at and confirmed_at >= start_at
  ),
  constraint injury_restrictions_advice_valid check (
    (professional_advice is null) = (professional_advice_at is null)
    and (status <> 'professional_restricted' or professional_advice is not null)
  ),
  constraint injury_restrictions_choice_valid check (
    (status = 'self_reported_limited' and athlete_plan_choice = 'train_low_only')
    or (status <> 'self_reported_limited' and athlete_plan_choice = 'keep_blocked')
  )
);

create unique index one_active_restriction_per_discipline
on public.injury_restrictions (athlete_id, discipline)
where cleared_at is null;

create index injury_restrictions_context_idx
on public.injury_restrictions (context_id);

create table public.planned_external_activities (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  context_id uuid not null,
  week_start date not null,
  name text not null,
  discipline text not null,
  scheduled_at timestamptz not null,
  timezone text not null,
  duration_minutes numeric not null,
  strenuous boolean not null default true,
  recurring boolean not null default false,
  status text not null default 'planned',
  completed_activity_id uuid,
  created_at timestamptz not null default statement_timestamp(),
  unique (id, athlete_id),
  foreign key (context_id, athlete_id)
    references public.weekly_checkin_contexts (id, athlete_id) on delete cascade,
  foreign key (completed_activity_id, athlete_id)
    references public.activities (id, athlete_id),
  constraint planned_external_activities_monday check (
    extract(isodow from week_start) = 1
  ),
  constraint planned_external_activities_name_valid check (
    char_length(btrim(name)) between 1 and 120 and name = btrim(name)
  ),
  constraint planned_external_activities_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint planned_external_activities_duration_valid check (
    duration_minutes > 0 and duration_minutes <= 1440
  ),
  constraint planned_external_activities_status_valid check (
    status in ('planned', 'completed', 'cancelled')
  ),
  constraint planned_external_activities_completion_valid check (
    (status = 'completed' and completed_activity_id is not null)
    or (status <> 'completed' and completed_activity_id is null)
  )
);

create index planned_external_activities_owner_week_idx
on public.planned_external_activities (athlete_id, week_start, scheduled_at);

create index planned_external_activities_context_idx
on public.planned_external_activities (context_id);

create table public.goal_maintenance_states (
  goal_id uuid not null,
  athlete_id uuid not null,
  status text not null default 'active',
  achieved_at date not null,
  confirmed_at timestamptz not null default statement_timestamp(),
  ended_at timestamptz,
  primary key (goal_id, athlete_id),
  foreign key (goal_id, athlete_id)
    references public.goals (id, athlete_id) on delete cascade,
  constraint goal_maintenance_states_status_valid check (
    status in ('active', 'ended')
  ),
  constraint goal_maintenance_states_end_valid check (
    (status = 'active' and ended_at is null)
    or (status = 'ended' and ended_at is not null)
  )
);

create index goal_maintenance_states_owner_status_idx
on public.goal_maintenance_states (athlete_id, status);

alter table public.weekly_checkins enable row level security;
alter table public.weekly_checkins force row level security;
alter table public.weekly_checkin_contexts enable row level security;
alter table public.weekly_checkin_contexts force row level security;
alter table public.injury_restrictions enable row level security;
alter table public.injury_restrictions force row level security;
alter table public.planned_external_activities enable row level security;
alter table public.planned_external_activities force row level security;
alter table public.goal_maintenance_states enable row level security;
alter table public.goal_maintenance_states force row level security;

revoke all on public.weekly_checkins from public, anon, authenticated, service_role;
revoke all on public.weekly_checkin_contexts from public, anon, authenticated, service_role;
revoke all on public.injury_restrictions from public, anon, authenticated, service_role;
revoke all on public.planned_external_activities from public, anon, authenticated, service_role;
revoke all on public.goal_maintenance_states
from public, anon, authenticated, service_role;

grant select on public.weekly_checkins to authenticated;
grant select on public.weekly_checkin_contexts to authenticated;
grant select on public.injury_restrictions to authenticated;
grant select on public.planned_external_activities to authenticated;
grant select, insert, update on public.goal_maintenance_states to authenticated;

create policy weekly_checkins_select_own
on public.weekly_checkins for select to authenticated
using ((select auth.uid()) = athlete_id);

create policy weekly_checkin_contexts_select_own
on public.weekly_checkin_contexts for select to authenticated
using ((select auth.uid()) = athlete_id);

create policy injury_restrictions_select_own
on public.injury_restrictions for select to authenticated
using ((select auth.uid()) = athlete_id);

create policy planned_external_activities_select_own
on public.planned_external_activities for select to authenticated
using ((select auth.uid()) = athlete_id);

create policy goal_maintenance_states_select_own
on public.goal_maintenance_states for select to authenticated
using ((select auth.uid()) = athlete_id);
create policy goal_maintenance_states_insert_own
on public.goal_maintenance_states for insert to authenticated
with check ((select auth.uid()) = athlete_id);
create policy goal_maintenance_states_update_own
on public.goal_maintenance_states for update to authenticated
using ((select auth.uid()) = athlete_id)
with check ((select auth.uid()) = athlete_id);

alter table public.plan_revisions add column checkin_id uuid;
alter table public.plan_revisions
  add column low_only_disciplines text[] not null default '{}';
alter table public.plan_revisions
  add foreign key (checkin_id, athlete_id)
  references public.weekly_checkins (id, athlete_id);
alter table public.plan_revisions
  add constraint plan_revisions_low_only_valid check (
    low_only_disciplines <@ array['swim', 'bike', 'run']::text[]
    and not low_only_disciplines && confirmed_injuries
  );

create index plan_revisions_checkin_idx
on public.plan_revisions (checkin_id) where checkin_id is not null;

alter table public.plan_revisions drop constraint plan_revisions_target_basis_valid;
alter table public.plan_revisions add constraint plan_revisions_target_basis_valid check (
  target_basis in (
    'initial_catalog_baseline',
    'prior_planned_hold',
    'realized_progression',
    'realized_baseline',
    'inactive_restart',
    'maintenance_hold',
    'physiological_debt',
    'manual_review_recovery',
    'activity_correction',
    'recovery_factor',
    'taper_factor',
    'injury_rest_only'
  )
);

alter table public.plan_revisions drop constraint plan_revisions_availability_valid;
alter table public.plan_revisions add constraint plan_revisions_availability_valid check (
  jsonb_typeof(availability) = 'array'
  and (
    jsonb_array_length(availability) > 0
    or target_basis = 'injury_rest_only'
  )
);

alter table public.plan_revisions drop constraint plan_revisions_distribution_valid;
alter table public.plan_revisions add constraint plan_revisions_distribution_valid check (
  low_intensity_percent between 0 and 100
  and high_intensity_percent between 0 and 100
  and (
    low_intensity_percent + high_intensity_percent = 100
    or (
      target_basis = 'injury_rest_only'
      and low_intensity_percent = 0
      and high_intensity_percent = 0
    )
  )
);

create function private.enforce_phase_8_rpc_writes()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if current_setting('start23.checkin_write', true) <> 'on' then
    raise exception 'weekly context writes require an approved RPC'
      using errcode = '42501';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

revoke execute on function private.enforce_phase_8_rpc_writes()
from public, anon, authenticated, service_role;

create trigger weekly_checkins_rpc_writes
before insert or update or delete on public.weekly_checkins
for each row execute function private.enforce_phase_8_rpc_writes();
create trigger weekly_checkin_contexts_rpc_writes
before insert or update or delete on public.weekly_checkin_contexts
for each row execute function private.enforce_phase_8_rpc_writes();
create trigger injury_restrictions_rpc_writes
before insert or update or delete on public.injury_restrictions
for each row execute function private.enforce_phase_8_rpc_writes();
create trigger planned_external_activities_rpc_writes
before insert or update or delete on public.planned_external_activities
for each row execute function private.enforce_phase_8_rpc_writes();
create trigger goal_maintenance_states_rpc_writes
before insert or update or delete on public.goal_maintenance_states
for each row execute function private.enforce_phase_8_rpc_writes();

grant insert, update, delete on public.weekly_checkins to authenticated;
grant insert, update, delete on public.weekly_checkin_contexts to authenticated;
grant insert, update, delete on public.injury_restrictions to authenticated;
grant insert, update, delete on public.planned_external_activities to authenticated;

create policy weekly_checkins_insert_own
on public.weekly_checkins for insert to authenticated
with check ((select auth.uid()) = athlete_id);
create policy weekly_checkins_update_own
on public.weekly_checkins for update to authenticated
using ((select auth.uid()) = athlete_id)
with check ((select auth.uid()) = athlete_id);
create policy weekly_checkins_delete_own
on public.weekly_checkins for delete to authenticated
using ((select auth.uid()) = athlete_id);

create policy weekly_checkin_contexts_insert_own
on public.weekly_checkin_contexts for insert to authenticated
with check ((select auth.uid()) = athlete_id);
create policy weekly_checkin_contexts_update_own
on public.weekly_checkin_contexts for update to authenticated
using ((select auth.uid()) = athlete_id)
with check ((select auth.uid()) = athlete_id);
create policy weekly_checkin_contexts_delete_own
on public.weekly_checkin_contexts for delete to authenticated
using ((select auth.uid()) = athlete_id);

create policy injury_restrictions_insert_own
on public.injury_restrictions for insert to authenticated
with check ((select auth.uid()) = athlete_id);
create policy injury_restrictions_update_own
on public.injury_restrictions for update to authenticated
using ((select auth.uid()) = athlete_id)
with check ((select auth.uid()) = athlete_id);
create policy injury_restrictions_delete_own
on public.injury_restrictions for delete to authenticated
using ((select auth.uid()) = athlete_id);

create policy planned_external_activities_insert_own
on public.planned_external_activities for insert to authenticated
with check ((select auth.uid()) = athlete_id);
create policy planned_external_activities_update_own
on public.planned_external_activities for update to authenticated
using ((select auth.uid()) = athlete_id)
with check ((select auth.uid()) = athlete_id);
create policy planned_external_activities_delete_own
on public.planned_external_activities for delete to authenticated
using ((select auth.uid()) = athlete_id);

create function public.get_weekly_checkin(p_checkin_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'id', checkin.id,
    'week_start', checkin.week_start,
    'timezone', checkin.timezone,
    'status', checkin.status,
    'context_revision', checkin.context_revision,
    'plan_proposal_id', checkin.plan_proposal_id,
    'started_at', checkin.started_at,
    'completed_at', checkin.completed_at,
    'context', case when context.id is null then null else jsonb_build_object(
      'revision', context.revision,
      'state', context.state,
      'source', context.source,
      'expires_at', context.expires_at,
      'fingerprint', context.fingerprint,
      'blocked_dates', context.payload -> 'blocked_dates',
      'fatigue_level', context.payload ->> 'fatigue_level',
      'missed_workout_reasons', context.payload -> 'missed_workout_reasons',
      'recurring_activities_confirmed',
        (context.payload ->> 'recurring_activities_confirmed')::boolean,
      'external_activities', context.payload -> 'external_activities',
      'restrictions', context.payload -> 'restrictions',
      'alarm_symptoms_acknowledged',
        (context.payload ->> 'alarm_symptoms_acknowledged')::boolean,
      'confirmed_at', context.confirmed_at
    ) end
  )
  into v_result
  from public.weekly_checkins checkin
  left join lateral (
    select candidate.*
    from public.weekly_checkin_contexts candidate
    where candidate.checkin_id = checkin.id
      and candidate.athlete_id = checkin.athlete_id
    order by candidate.revision desc
    limit 1
  ) context on true
  where checkin.id = p_checkin_id and checkin.athlete_id = v_athlete_id;
  if v_result is null then
    raise exception 'weekly check-in not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_weekly_checkin(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_weekly_checkin(uuid) to authenticated;

create function public.start_weekly_checkin(p_week_start date)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_timezone text;
  v_checkin_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if extract(isodow from p_week_start) <> 1 then
    raise exception 'check-in week must start on Monday' using errcode = '23514';
  end if;
  select profile.timezone into v_timezone
  from public.athlete_profiles profile
  where profile.athlete_id = v_athlete_id;
  if v_timezone is null then
    raise exception 'athlete profile not found' using errcode = 'P0002';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  insert into public.weekly_checkins (athlete_id, week_start, timezone)
  values (v_athlete_id, p_week_start, v_timezone)
  on conflict (athlete_id, week_start) do update
    set updated_at = public.weekly_checkins.updated_at
  returning id into v_checkin_id;
  return public.get_weekly_checkin(v_checkin_id);
end;
$$;

revoke all on function public.start_weekly_checkin(date)
from public, anon, authenticated, service_role;
grant execute on function public.start_weekly_checkin(date) to authenticated;

create function public.open_due_weekly_checkins(
  p_instant timestamptz default statement_timestamp()
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_inserted integer;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  insert into public.weekly_checkins (
    athlete_id, week_start, timezone
  )
  select
    profile.athlete_id,
    (p_instant at time zone profile.timezone)::date
      - extract(
          isodow from (p_instant at time zone profile.timezone)::date
        )::integer + 1,
    profile.timezone
  from public.athlete_profiles profile
  where profile.onboarding_status = 'completed'
    and extract(
      isodow from (p_instant at time zone profile.timezone)::date
    ) = 1
  on conflict (athlete_id, week_start) do nothing;
  get diagnostics v_inserted = row_count;
  return v_inserted;
end;
$$;

revoke all on function public.open_due_weekly_checkins(timestamptz)
from public, anon, authenticated, service_role;
grant execute on function public.open_due_weekly_checkins(timestamptz)
to service_role;

create function public.save_weekly_checkin_context(
  p_checkin_id uuid,
  p_expected_revision integer,
  p_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_checkin public.weekly_checkins;
  v_revision integer;
begin
  select * into v_checkin
  from public.weekly_checkins
  where id = p_checkin_id and athlete_id = v_athlete_id
  for update;
  if not found then
    raise exception 'weekly check-in not found' using errcode = 'P0002';
  end if;
  if v_checkin.status <> 'open' then
    raise exception 'check-in is already completed' using errcode = '40001';
  end if;
  if v_checkin.context_revision <> p_expected_revision then
    raise exception 'check-in context is stale' using errcode = '40001';
  end if;
  if jsonb_typeof(p_payload) <> 'object'
     or p_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'check-in context is invalid' using errcode = '23514';
  end if;
  v_revision := p_expected_revision + 1;
  perform set_config('start23.checkin_write', 'on', true);
  update public.weekly_checkin_contexts
  set state = 'superseded'
  where checkin_id = p_checkin_id and athlete_id = v_athlete_id and state = 'draft';
  insert into public.weekly_checkin_contexts (
    checkin_id, athlete_id, revision, expires_at, fingerprint, payload
  ) values (
    p_checkin_id,
    v_athlete_id,
    v_revision,
    ((v_checkin.week_start + 7)::timestamp at time zone v_checkin.timezone),
    p_fingerprint,
    p_payload
  );
  update public.weekly_checkins
  set context_revision = v_revision, updated_at = statement_timestamp()
  where id = p_checkin_id and athlete_id = v_athlete_id;
  return public.get_weekly_checkin(p_checkin_id);
end;
$$;

revoke all on function public.save_weekly_checkin_context(uuid, integer, text, jsonb)
from public, anon, authenticated, service_role;
grant execute
on function public.save_weekly_checkin_context(uuid, integer, text, jsonb)
to authenticated;

create function public.confirm_weekly_checkin_context(
  p_checkin_id uuid,
  p_expected_revision integer,
  p_fingerprint text
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_checkin public.weekly_checkins;
  v_context public.weekly_checkin_contexts;
  v_restriction jsonb;
  v_external jsonb;
  v_status text;
  v_allowed text;
  v_choice text;
  v_now timestamptz := statement_timestamp();
begin
  select * into v_checkin
  from public.weekly_checkins
  where id = p_checkin_id and athlete_id = v_athlete_id
  for update;
  if not found then
    raise exception 'weekly check-in not found' using errcode = 'P0002';
  end if;
  if v_checkin.status <> 'open' then
    raise exception 'check-in is already completed' using errcode = '40001';
  end if;
  if v_checkin.context_revision <> p_expected_revision then
    raise exception 'check-in context is stale' using errcode = '40001';
  end if;
  select * into v_context
  from public.weekly_checkin_contexts
  where checkin_id = p_checkin_id
    and athlete_id = v_athlete_id
    and revision = p_expected_revision
    and state = 'draft'
  for update;
  if not found or v_context.fingerprint <> p_fingerprint then
    raise exception 'check-in context is stale' using errcode = '40001';
  end if;
  if exists (
    select 1
    from public.injury_restrictions active
    where active.athlete_id = v_athlete_id
      and active.cleared_at is null
      and not exists (
        select 1
        from jsonb_array_elements(v_context.payload -> 'restrictions') item
        where item ->> 'discipline' = active.discipline
      )
  ) then
    raise exception 'active restriction review is missing' using errcode = '40001';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  update public.weekly_checkin_contexts
  set state = 'confirmed', confirmed_at = v_now
  where id = v_context.id and athlete_id = v_athlete_id;

  for v_restriction in
    select value from jsonb_array_elements(v_context.payload -> 'restrictions')
  loop
    v_status := v_restriction ->> 'status';
    v_allowed := case
      when v_status = 'none' then 'unrestricted'
      when v_status = 'self_reported_limited' then 'low_only'
      else 'none'
    end;
    v_choice := v_restriction ->> 'athlete_plan_choice';
    update public.injury_restrictions
    set cleared_at = v_now
    where athlete_id = v_athlete_id
      and discipline = v_restriction ->> 'discipline'
      and cleared_at is null;
    if v_status <> 'none' then
      insert into public.injury_restrictions (
        athlete_id, context_id, discipline, status, allowed_intensity, source,
        start_at, review_at, professional_advice, professional_advice_at,
        athlete_plan_choice, confirmed_at
      ) values (
        v_athlete_id,
        v_context.id,
        v_restriction ->> 'discipline',
        v_status,
        v_allowed,
        v_restriction ->> 'source',
        v_now,
        v_now + interval '7 days',
        nullif(v_restriction ->> 'professional_advice', ''),
        nullif(v_restriction ->> 'professional_advice_at', '')::timestamptz,
        v_choice,
        v_now
      );
    end if;
  end loop;

  for v_external in
    select value from jsonb_array_elements(v_context.payload -> 'external_activities')
  loop
    insert into public.planned_external_activities (
      athlete_id, context_id, week_start, name, discipline, scheduled_at,
      timezone, duration_minutes, strenuous, recurring
    ) values (
      v_athlete_id,
      v_context.id,
      v_checkin.week_start,
      v_external ->> 'name',
      v_external ->> 'discipline',
      (v_external ->> 'scheduled_at')::timestamptz,
      v_checkin.timezone,
      (v_external ->> 'duration_minutes')::numeric,
      (v_external ->> 'strenuous')::boolean,
      (v_external ->> 'recurring')::boolean
    );
  end loop;
  update public.weekly_checkins
  set updated_at = v_now
  where id = p_checkin_id and athlete_id = v_athlete_id;
  return public.get_weekly_checkin(p_checkin_id);
end;
$$;

revoke all on function public.confirm_weekly_checkin_context(uuid, integer, text)
from public, anon, authenticated, service_role;
grant execute
on function public.confirm_weekly_checkin_context(uuid, integer, text)
to authenticated;

create function public.mark_goal_achieved(
  p_goal_id uuid,
  p_achieved_at date
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_result jsonb;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_achieved_at > current_date then
    raise exception 'goal achievement date cannot be in the future'
      using errcode = '23514';
  end if;
  if not exists (
    select 1 from public.goals goal
    where goal.id = p_goal_id
      and goal.athlete_id = v_athlete_id
      and goal.status = 'active'
  ) then
    raise exception 'goal not found' using errcode = 'P0002';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  insert into public.goal_maintenance_states (
    goal_id, athlete_id, achieved_at
  ) values (
    p_goal_id, v_athlete_id, p_achieved_at
  )
  on conflict (goal_id, athlete_id) do update
  set
    status = 'active',
    achieved_at = excluded.achieved_at,
    confirmed_at = statement_timestamp(),
    ended_at = null
  returning jsonb_build_object(
    'goal_id', goal_id,
    'status', status,
    'achieved_at', achieved_at,
    'confirmed_at', confirmed_at
  ) into v_result;
  return v_result;
end;
$$;

revoke all on function public.mark_goal_achieved(uuid, date)
from public, anon, authenticated, service_role;
grant execute on function public.mark_goal_achieved(uuid, date) to authenticated;

alter table public.plan_revisions drop constraint plan_revisions_taper_consistent;
alter table public.plan_revisions add constraint plan_revisions_taper_consistent check (
  target_basis = 'injury_rest_only'
  or (
    phase = 'taper'
    and taper_period in ('a_t_minus_2', 'a_t_minus_1')
  )
  or (phase <> 'taper' and taper_period is null)
);

create function public.get_checkin_context_for_planning(
  p_athlete_id uuid,
  p_checkin_id uuid
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
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'checkin_id', checkin.id,
    'week_start', checkin.week_start,
    'timezone', checkin.timezone,
    'confirmed_context', context.payload,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = checkin.athlete_id
        and maintenance.status = 'active'
    ),
    'plan_id', plan.id,
    'active_revision', plan.active_revision,
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot
  )
  into v_result
  from public.weekly_checkins checkin
  join public.weekly_checkin_contexts context
    on context.checkin_id = checkin.id
   and context.athlete_id = checkin.athlete_id
   and context.state = 'confirmed'
  join lateral (
    select candidate.*
    from public.initial_plan_requests candidate
    where candidate.athlete_id = checkin.athlete_id
      and candidate.status in ('pending', 'consumed')
    order by candidate.refreshed_at desc
    limit 1
  ) request on true
  left join public.weekly_plans plan
    on plan.athlete_id = checkin.athlete_id
   and plan.week_start = checkin.week_start
  where checkin.id = p_checkin_id
    and checkin.athlete_id = p_athlete_id
    and checkin.status = 'open';
  if v_result is null then
    raise exception 'check-in context is not confirmed' using errcode = '40001';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_checkin_context_for_planning(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_checkin_context_for_planning(uuid, uuid)
to service_role;

create function public.create_weekly_plan_proposal_v2(
  p_athlete_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
  v_plan_id uuid := nullif(p_payload ->> 'plan_id', '')::uuid;
  v_checkin_id uuid := nullif(p_payload ->> 'checkin_id', '')::uuid;
  v_request_id uuid := nullif(p_payload ->> 'initial_plan_request_id', '')::uuid;
  v_revision_id uuid;
  v_revision integer;
  v_proposal_id uuid;
  v_existing record;
  v_warning jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if jsonb_typeof(p_payload -> 'low_only_disciplines') <> 'array'
     or jsonb_typeof(p_payload -> 'goal_disciplines') <> 'array' then
    raise exception 'phase 8 planning context is incomplete' using errcode = '23514';
  end if;

  if jsonb_array_length(p_payload -> 'workouts') > 0 then
    v_result := public.create_weekly_plan_proposal(p_athlete_id, p_payload);
    perform set_config('start23.critical_write', 'on', true);
    update public.plan_revisions revision
    set
      checkin_id = v_checkin_id,
      low_only_disciplines = array(
        select jsonb_array_elements_text(p_payload -> 'low_only_disciplines')
      )
    from public.change_proposals proposal
    where proposal.id = (v_result ->> 'proposal_id')::uuid
      and proposal.target_plan_revision_id = revision.id
      and proposal.athlete_id = p_athlete_id;
    return v_result;
  end if;

  if p_payload ->> 'target_basis' <> 'injury_rest_only'
     or not (
       array(select jsonb_array_elements_text(p_payload -> 'goal_disciplines'))
       <@ array(select jsonb_array_elements_text(p_payload -> 'confirmed_injuries'))
     ) then
    raise exception 'rest-only planning context is invalid' using errcode = '23514';
  end if;
  if (p_payload ->> 'planned_tss')::numeric <> 0
     or (p_payload ->> 'target_tss')::numeric <> 0
     or (p_payload ->> 'total_duration_minutes')::numeric <> 0 then
    raise exception 'rest-only load must be zero' using errcode = '23514';
  end if;

  if v_plan_id is not null then
    select plan.id, plan.active_revision into v_existing
    from public.weekly_plans plan
    where plan.id = v_plan_id and plan.athlete_id = p_athlete_id
    for update;
    if not found then
      raise exception 'weekly plan not found' using errcode = 'P0002';
    end if;
  else
    select plan.id, plan.active_revision into v_existing
    from public.weekly_plans plan
    where plan.athlete_id = p_athlete_id
      and plan.week_start = (p_payload ->> 'week_start')::date
    for update;
    if found then
      v_plan_id := v_existing.id;
    end if;
  end if;
  if found and coalesce(v_existing.active_revision, 0)
     <> (p_payload ->> 'expected_base_revision')::integer then
    raise exception 'plan revision is stale' using errcode = '40001';
  end if;

  if v_plan_id is not null then
    select proposal.id, revision.revision_number
    into v_proposal_id, v_revision
    from public.plan_revisions revision
    join public.change_proposals proposal
      on proposal.target_plan_revision_id = revision.id
     and proposal.athlete_id = revision.athlete_id
    where revision.plan_id = v_plan_id
      and revision.athlete_id = p_athlete_id
      and revision.generation_fingerprint = p_payload ->> 'generation_fingerprint'
      and proposal.state in ('pending', 'applied')
    order by revision.revision_number desc
    limit 1;
    if v_proposal_id is not null then
      return jsonb_build_object(
        'plan_id', v_plan_id,
        'revision', v_revision,
        'proposal_id', v_proposal_id
      );
    end if;
  end if;

  perform set_config('start23.critical_write', 'on', true);
  if v_plan_id is null then
    insert into public.weekly_plans (athlete_id, week_start, timezone, state)
    values (
      p_athlete_id,
      (p_payload ->> 'week_start')::date,
      p_payload ->> 'timezone',
      'pending_approval'
    ) returning id into v_plan_id;
  end if;
  update public.change_proposals proposal
  set state = 'expired', decided_at = statement_timestamp()
  from public.plan_revisions revision
  where proposal.target_plan_revision_id = revision.id
    and revision.plan_id = v_plan_id
    and proposal.athlete_id = p_athlete_id
    and proposal.state = 'pending';
  update public.plan_revisions
  set state = 'expired'
  where plan_id = v_plan_id
    and athlete_id = p_athlete_id
    and state = 'pending_approval';
  select coalesce(max(revision_number), 0) + 1 into v_revision
  from public.plan_revisions
  where plan_id = v_plan_id and athlete_id = p_athlete_id;

  insert into public.plan_revisions (
    plan_id, athlete_id, revision_number, state, source, phase, target_basis,
    taper_period, input_fingerprint, generation_fingerprint,
    initial_plan_request_id, checkin_id, total_duration_minutes,
    low_intensity_percent, high_intensity_percent, confirmed_injuries,
    low_only_disciplines, availability, ruleset_version
  ) values (
    v_plan_id,
    p_athlete_id,
    v_revision,
    'pending_approval',
    'system_generated',
    p_payload ->> 'phase',
    'injury_rest_only',
    nullif(p_payload ->> 'taper_period', ''),
    p_payload ->> 'input_fingerprint',
    p_payload ->> 'generation_fingerprint',
    v_request_id,
    v_checkin_id,
    0,
    0,
    0,
    array(select jsonb_array_elements_text(p_payload -> 'confirmed_injuries')),
    '{}',
    p_payload -> 'availability',
    p_payload ->> 'ruleset_version'
  ) returning id into v_revision_id;

  insert into private.plan_revision_loads (
    revision_id, athlete_id, target_tss, planned_tss, ruleset_version
  ) values (v_revision_id, p_athlete_id, 0, 0, p_payload ->> 'ruleset_version');

  for v_warning in select value from jsonb_array_elements(p_payload -> 'warnings')
  loop
    insert into public.plan_warnings (
      revision_id, athlete_id, rule_id, code, severity, message
    ) values (
      v_revision_id,
      p_athlete_id,
      v_warning ->> 'rule_id',
      v_warning ->> 'code',
      v_warning ->> 'severity',
      v_warning ->> 'message'
    );
  end loop;

  insert into public.change_proposals (
    athlete_id, kind, target_plan_revision_id, base_plan_revision,
    reason_codes, public_explanation, ruleset_version
  ) values (
    p_athlete_id,
    'plan_revision',
    v_revision_id,
    (p_payload ->> 'expected_base_revision')::integer,
    array['all_disciplines_blocked_rest_only'],
    'A rest-only weekly revision is ready for review.',
    p_payload ->> 'ruleset_version'
  ) returning id into v_proposal_id;

  update public.weekly_plans
  set state = case when active_revision is null then 'pending_approval' else state end
  where id = v_plan_id and athlete_id = p_athlete_id;
  return jsonb_build_object(
    'plan_id', v_plan_id,
    'revision', v_revision,
    'proposal_id', v_proposal_id
  );
end;
$$;

revoke all on function public.create_weekly_plan_proposal_v2(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v2(uuid, jsonb)
to service_role;

create function public.attach_checkin_plan_proposal(
  p_athlete_id uuid,
  p_checkin_id uuid,
  p_proposal_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_existing uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select plan_proposal_id into v_existing
  from public.weekly_checkins
  where id = p_checkin_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'weekly check-in not found' using errcode = 'P0002';
  end if;
  if v_existing is not null and v_existing <> p_proposal_id then
    raise exception 'check-in is already completed' using errcode = '40001';
  end if;
  if not exists (
    select 1
    from public.change_proposals proposal
    join public.plan_revisions revision
      on revision.id = proposal.target_plan_revision_id
     and revision.athlete_id = proposal.athlete_id
    where proposal.id = p_proposal_id
      and proposal.athlete_id = p_athlete_id
      and revision.checkin_id = p_checkin_id
  ) then
    raise exception 'plan proposal does not belong to check-in' using errcode = '23514';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  update public.weekly_checkins
  set
    status = 'completed',
    plan_proposal_id = p_proposal_id,
    completed_at = coalesce(completed_at, statement_timestamp()),
    updated_at = statement_timestamp()
  where id = p_checkin_id and athlete_id = p_athlete_id;
  return jsonb_build_object(
    'checkin_id', p_checkin_id,
    'proposal_id', p_proposal_id,
    'status', 'completed'
  );
end;
$$;

revoke all on function public.attach_checkin_plan_proposal(uuid, uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.attach_checkin_plan_proposal(uuid, uuid, uuid)
to service_role;

create or replace function public.get_plan_context_for_planning(
  p_athlete_id uuid,
  p_plan_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_context jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  select jsonb_build_object(
    'plan_id', plan.id,
    'week_start', plan.week_start,
    'active_revision', plan.active_revision,
    'revision', revision.revision_number,
    'phase', revision.phase,
    'confirmed_injuries', revision.confirmed_injuries,
    'low_only_disciplines', revision.low_only_disciplines,
    'target_tss', revision_load.target_tss,
    'maintenance_active', exists (
      select 1 from public.goal_maintenance_states maintenance
      where maintenance.athlete_id = plan.athlete_id
        and maintenance.status = 'active'
    ),
    'initial_plan_request_id', request.id,
    'input_fingerprint', request.input_fingerprint,
    'input_snapshot', request.input_snapshot
  )
  into v_context
  from public.weekly_plans plan
  join lateral (
    select candidate.*
    from public.plan_revisions candidate
    where candidate.plan_id = plan.id
      and candidate.athlete_id = plan.athlete_id
      and (
        candidate.revision_number = plan.active_revision
        or plan.active_revision is null
      )
    order by
      (candidate.revision_number = plan.active_revision) desc,
      candidate.revision_number desc
    limit 1
  ) revision on true
  join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = revision.athlete_id
  join public.initial_plan_requests request
    on request.id = revision.initial_plan_request_id
   and request.athlete_id = plan.athlete_id
  where plan.id = p_plan_id and plan.athlete_id = p_athlete_id;
  if v_context is null then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  return v_context;
end;
$$;

drop function public.get_plan_load_history_for_planning(uuid, date);

create function public.get_plan_load_history_for_planning(
  p_athlete_id uuid,
  p_before_week date
)
returns table (
  week_start date,
  phase text,
  target_basis text,
  planned_tss numeric,
  realized_tss numeric,
  planned_high_minutes numeric,
  planned_total_minutes numeric,
  realized_high_minutes numeric,
  realized_classified_minutes numeric,
  realized_total_minutes numeric,
  completed_activity_count bigint
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  return query
  with earliest_evidence as (
    select min(evidence.local_week) as local_week
    from (
      select plan.week_start as local_week
      from public.weekly_plans plan
      where plan.athlete_id = p_athlete_id
      union all
      select
        (activity.started_at at time zone activity.timezone)::date
        - extract(
            isodow
            from (activity.started_at at time zone activity.timezone)::date
          )::integer + 1
      from public.activities activity
      where activity.athlete_id = p_athlete_id
    ) evidence
  ), complete_weeks as (
    select (p_before_week - (series.value * 7))::date as local_week
    from generate_series(1, 6) as series(value)
    cross join earliest_evidence earliest
    where earliest.local_week is not null
      and p_before_week - (series.value * 7) >= earliest.local_week
  )
  select
    week.local_week,
    coalesce(revision.phase, 'base'),
    coalesce(revision.target_basis, 'realized_baseline'),
    coalesce(revision_load.planned_tss, 0),
    case
      when activity_summary.activity_count = 0 then 0::numeric
      else activity_summary.realized_tss
    end,
    coalesce(
      revision.total_duration_minutes * revision.high_intensity_percent / 100,
      0
    ),
    coalesce(revision.total_duration_minutes, 0),
    activity_summary.realized_high_minutes,
    activity_summary.realized_classified_minutes,
    activity_summary.realized_total_minutes,
    activity_summary.activity_count
  from complete_weeks week
  left join public.weekly_plans plan
    on plan.athlete_id = p_athlete_id
   and plan.week_start = week.local_week
  left join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  left join private.plan_revision_loads revision_load
    on revision_load.revision_id = revision.id
   and revision_load.athlete_id = plan.athlete_id
  left join lateral (
    select
      count(activity.id) as activity_count,
      sum(activity_load.realized_tss) as realized_tss,
      sum(metric.high_intensity_minutes) as realized_high_minutes,
      sum(metric.low_intensity_minutes + metric.high_intensity_minutes)
        as realized_classified_minutes,
      sum(activity.duration_minutes) filter (
        where activity_load.activity_id is not null
      ) as realized_total_minutes
    from public.activities activity
    left join private.activity_loads activity_load
      on activity_load.activity_id = activity.id
     and activity_load.athlete_id = activity.athlete_id
    left join public.activity_metrics metric
      on metric.activity_id = activity.id
     and metric.athlete_id = activity.athlete_id
     and activity_load.activity_id is not null
    where activity.athlete_id = p_athlete_id
      and (activity.started_at at time zone activity.timezone)::date
        between week.local_week and week.local_week + 6
  ) activity_summary on true
  order by week.local_week;
end;
$$;

revoke all on function public.get_plan_load_history_for_planning(uuid, date)
from public, anon, authenticated, service_role;
grant execute on function public.get_plan_load_history_for_planning(uuid, date)
to service_role;

create function public.get_calendar_rest_days(
  p_from timestamptz,
  p_to timestamptz
)
returns setof jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'date', day.local_date,
    'reason', case
      when revision.target_basis = 'injury_rest_only' then 'restriction_rest'
      else 'planned_rest'
    end
  )
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  cross join lateral generate_series(
    plan.week_start,
    plan.week_start + 6,
    interval '1 day'
  ) generated
  cross join lateral (
    select generated::date as local_date
  ) day
  where plan.athlete_id = (select auth.uid())
    and (day.local_date::timestamp at time zone plan.timezone) >= p_from
    and (day.local_date::timestamp at time zone plan.timezone) < p_to
    and not exists (
      select 1
      from public.planned_workouts workout
      where workout.revision_id = revision.id
        and workout.athlete_id = plan.athlete_id
        and workout.status <> 'cancelled'
        and (workout.scheduled_at at time zone plan.timezone)::date = day.local_date
    )
  order by day.local_date;
$$;

revoke all on function public.get_calendar_rest_days(timestamptz, timestamptz)
from public, anon, authenticated, service_role;
grant execute on function public.get_calendar_rest_days(timestamptz, timestamptz)
to authenticated;

create function public.create_external_activity_summary(
  p_external_activity_id uuid,
  p_idempotency_key uuid,
  p_request_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_external public.planned_external_activities;
  v_result jsonb;
  v_activity_id uuid;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_payload ->> 'planned_workout_id' is not null then
    raise exception 'activity planning references are mutually exclusive'
      using errcode = '23514';
  end if;
  select * into v_external
  from public.planned_external_activities
  where id = p_external_activity_id and athlete_id = v_athlete_id
  for update;
  if not found then
    raise exception 'planned external activity not found' using errcode = 'P0002';
  end if;
  if v_external.discipline <> p_payload ->> 'discipline' then
    raise exception 'activity discipline does not match planned external activity'
      using errcode = '23514';
  end if;
  if ((p_payload ->> 'started_at')::timestamptz at time zone v_external.timezone)::date
     not between v_external.week_start and v_external.week_start + 6 then
    raise exception 'external activity must be recorded in its planned local week'
      using errcode = '23514';
  end if;

  v_result := public.create_activity_summary(
    p_idempotency_key,
    p_request_fingerprint,
    p_payload
  );
  v_activity_id := (v_result ->> 'id')::uuid;
  if v_external.completed_activity_id is not null then
    if v_external.completed_activity_id = v_activity_id then
      return v_result;
    end if;
    raise exception 'planned external activity already completed'
      using errcode = '40001';
  end if;
  perform set_config('start23.checkin_write', 'on', true);
  update public.planned_external_activities
  set status = 'completed', completed_activity_id = v_activity_id
  where id = p_external_activity_id and athlete_id = v_athlete_id;
  return v_result;
end;
$$;

revoke all on function public.create_external_activity_summary(uuid, uuid, text, jsonb)
from public, anon, authenticated, service_role;
grant execute
on function public.create_external_activity_summary(uuid, uuid, text, jsonb)
to authenticated;

create table public.activity_rpe_revisions (
  id bigint generated always as identity primary key,
  activity_id uuid not null,
  athlete_id uuid not null,
  previous_rpe smallint not null,
  corrected_rpe smallint not null,
  previous_qualitative_result text not null,
  corrected_qualitative_result text not null,
  corrected_at timestamptz not null default statement_timestamp(),
  ruleset_version text not null,
  foreign key (activity_id, athlete_id)
    references public.activities (id, athlete_id) on delete cascade,
  constraint activity_rpe_revisions_scores_valid check (
    previous_rpe between 1 and 10
    and corrected_rpe between 1 and 10
    and previous_rpe <> corrected_rpe
  ),
  constraint activity_rpe_revisions_results_valid check (
    previous_qualitative_result in (
      'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
    )
    and corrected_qualitative_result in (
      'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
    )
  ),
  constraint activity_rpe_revisions_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

create index activity_rpe_revisions_owner_activity_idx
on public.activity_rpe_revisions (athlete_id, activity_id, corrected_at);

alter table public.activity_rpe_revisions enable row level security;
alter table public.activity_rpe_revisions force row level security;
revoke all on public.activity_rpe_revisions
from public, anon, authenticated, service_role;
grant select on public.activity_rpe_revisions to authenticated;
create policy activity_rpe_revisions_select_own
on public.activity_rpe_revisions for select to authenticated
using ((select auth.uid()) = athlete_id);

create function public.revise_activity_rpe(
  p_athlete_id uuid,
  p_activity_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_activity public.activities;
  v_new_rpe smallint := (p_payload ->> 'rpe')::smallint;
  v_result text := p_payload ->> 'qualitative_result';
  v_reason text := p_payload ->> 'correction_reason';
  v_realized numeric := (p_payload ->> 'realized_tss')::numeric;
  v_activity_week date;
  v_current_week date;
  v_pending_revision_id uuid;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  select * into v_activity
  from public.activities
  where id = p_activity_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'activity not found' using errcode = 'P0002';
  end if;
  if v_activity.rpe is null or v_activity.processing_state <> 'complete' then
    raise exception 'activity rpe is missing' using errcode = '40001';
  end if;
  if v_activity.rpe = v_new_rpe then
    return private.activity_public_json(p_activity_id, p_athlete_id);
  end if;
  v_activity_week :=
    (v_activity.started_at at time zone v_activity.timezone)::date
    - extract(
        isodow from (v_activity.started_at at time zone v_activity.timezone)::date
      )::integer + 1;
  v_current_week :=
    (statement_timestamp() at time zone v_activity.timezone)::date
    - extract(
        isodow from (statement_timestamp() at time zone v_activity.timezone)::date
      )::integer + 1;
  if v_activity_week <> v_current_week then
    raise exception 'rpe correction window closed' using errcode = '40001';
  end if;
  if v_new_rpe not between 1 and 10
     or v_result not in (
       'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned'
     )
     or v_reason is not null and v_reason not in (
       'volume_overshoot', 'hidden_fatigue', 'unplanned_load'
     )
     or v_realized <> v_activity.duration_minutes * v_new_rpe / 60 then
    raise exception 'invalid activity rpe result' using errcode = '23514';
  end if;

  insert into public.activity_rpe_revisions (
    activity_id, athlete_id, previous_rpe, corrected_rpe,
    previous_qualitative_result, corrected_qualitative_result, ruleset_version
  ) values (
    p_activity_id,
    p_athlete_id,
    v_activity.rpe,
    v_new_rpe,
    v_activity.qualitative_result,
    v_result,
    p_payload ->> 'ruleset_version'
  );
  update private.activity_loads
  set
    realized_tss = v_realized,
    calculation_method = p_payload ->> 'calculation_method',
    ruleset_version = p_payload ->> 'ruleset_version'
  where activity_id = p_activity_id and athlete_id = p_athlete_id;

  if v_activity.correction_proposal_id is not null then
    select target_plan_revision_id into v_pending_revision_id
    from public.change_proposals
    where id = v_activity.correction_proposal_id
      and athlete_id = p_athlete_id
      and state = 'pending';
    if v_pending_revision_id is not null then
      perform set_config('start23.critical_write', 'on', true);
      update public.change_proposals
      set state = 'expired', decided_at = statement_timestamp()
      where id = v_activity.correction_proposal_id
        and athlete_id = p_athlete_id
        and state = 'pending';
      update public.plan_revisions
      set state = 'expired'
      where id = v_pending_revision_id
        and athlete_id = p_athlete_id
        and state = 'pending_approval';
    end if;
  end if;

  update public.activities
  set
    rpe = v_new_rpe,
    rpe_submitted_at = statement_timestamp(),
    qualitative_result = v_result,
    public_message = p_payload ->> 'public_message',
    correction_proposal_id = null,
    updated_at = statement_timestamp()
  where id = p_activity_id and athlete_id = p_athlete_id;
  return private.activity_public_json(p_activity_id, p_athlete_id);
end;
$$;

revoke all on function public.revise_activity_rpe(uuid, uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.revise_activity_rpe(uuid, uuid, jsonb)
to service_role;
