-- Phase 10.1: server-authoritative swipe selection and date-only placement.
-- Draft rows contain no private load. Only the trusted backend can mutate them;
-- athletes can read their own current state through forced RLS.

create table public.swipe_week_drafts (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  plan_id uuid,
  initial_plan_request_id uuid not null,
  base_plan_revision integer not null,
  context_plan_revision integer,
  week_start date not null,
  timezone text not null,
  available_dates date[] not null,
  availability_source text not null,
  confirmed_injuries text[] not null default '{}',
  low_only_disciplines text[] not null default '{}',
  input_fingerprint text not null,
  context_fingerprint text not null,
  ruleset_version text not null,
  target_workout_count integer not null,
  target_composition jsonb not null,
  accepted_template_ids uuid[] not null default '{}',
  passed_template_ids uuid[] not null default '{}',
  current_template_id uuid references public.workout_templates (id),
  decision_history jsonb not null default '[]',
  placements jsonb not null default '{}',
  state text not null default 'collecting',
  revision bigint not null default 1,
  proposal_id uuid,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  submitted_at timestamptz,

  unique (id, athlete_id),
  foreign key (plan_id, athlete_id)
    references public.weekly_plans (id, athlete_id),
  foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id),
  foreign key (proposal_id, athlete_id)
    references public.change_proposals (id, athlete_id),
  constraint swipe_week_drafts_base_revision_valid check (
    base_plan_revision >= 0
    and (context_plan_revision is null or context_plan_revision > 0)
  ),
  constraint swipe_week_drafts_monday_start check (
    extract(isodow from week_start) = 1
  ),
  constraint swipe_week_drafts_timezone_valid check (
    char_length(btrim(timezone)) between 1 and 100
    and timezone = btrim(timezone)
  ),
  constraint swipe_week_drafts_available_dates_valid check (
    cardinality(available_dates) between 1 and 7
  ),
  constraint swipe_week_drafts_availability_source_valid check (
    availability_source in ('explicit', 'previous_week')
  ),
  constraint swipe_week_drafts_restrictions_valid check (
    confirmed_injuries <@ array['swim', 'bike', 'run']::text[]
    and low_only_disciplines <@ array['swim', 'bike', 'run']::text[]
    and not (confirmed_injuries && low_only_disciplines)
  ),
  constraint swipe_week_drafts_fingerprints_valid check (
    input_fingerprint ~ '^[a-f0-9]{32}$'
    and context_fingerprint ~ '^[a-f0-9]{64}$'
  ),
  constraint swipe_week_drafts_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  ),
  constraint swipe_week_drafts_target_count_valid check (
    target_workout_count between 0 and 24
  ),
  constraint swipe_week_drafts_target_composition_valid check (
    jsonb_typeof(target_composition) = 'object'
    and target_composition ?& array['swim', 'bike', 'run']
    and (target_composition ->> 'swim')::integer >= 0
    and (target_composition ->> 'bike')::integer >= 0
    and (target_composition ->> 'run')::integer >= 0
    and target_composition - 'swim' - 'bike' - 'run' = '{}'::jsonb
    and (target_composition ->> 'swim')::integer
      + (target_composition ->> 'bike')::integer
      + (target_composition ->> 'run')::integer = target_workout_count
  ),
  constraint swipe_week_drafts_template_arrays_valid check (
    not (accepted_template_ids && passed_template_ids)
    and cardinality(accepted_template_ids) <= target_workout_count
    and (
      current_template_id is null
      or (
        not current_template_id = any(accepted_template_ids)
        and not current_template_id = any(passed_template_ids)
      )
    )
  ),
  constraint swipe_week_drafts_history_valid check (
    jsonb_typeof(decision_history) = 'array'
    and jsonb_array_length(decision_history) <= 128
  ),
  constraint swipe_week_drafts_placements_valid check (
    jsonb_typeof(placements) = 'object'
  ),
  constraint swipe_week_drafts_state_valid check (
    state in ('collecting', 'placement', 'submitted', 'cancelled')
  ),
  constraint swipe_week_drafts_revision_positive check (revision > 0),
  constraint swipe_week_drafts_state_consistent check (
    (
      state = 'collecting'
      and cardinality(accepted_template_ids) < target_workout_count
      and proposal_id is null
      and submitted_at is null
    )
    or (
      state = 'placement'
      and cardinality(accepted_template_ids) = target_workout_count
      and current_template_id is null
      and proposal_id is null
      and submitted_at is null
    )
    or (
      state = 'submitted'
      and cardinality(accepted_template_ids) = target_workout_count
      and current_template_id is null
      and plan_id is not null
      and proposal_id is not null
      and submitted_at is not null
    )
    or (
      state = 'cancelled'
      and proposal_id is null
      and submitted_at is null
    )
  )
);

create unique index one_open_swipe_week_draft_per_athlete_week
on public.swipe_week_drafts (athlete_id, week_start)
where state in ('collecting', 'placement');

create index swipe_week_drafts_owner_updated_idx
on public.swipe_week_drafts (athlete_id, updated_at desc);

create function private.validate_swipe_week_draft()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_accepted uuid[];
  v_passed uuid[];
  v_discipline text;
  v_expected_count integer;
  v_actual_count integer;
  v_key text;
  v_date date;
begin
  if cardinality(new.available_dates) <> (
       select count(distinct value) from unnest(new.available_dates) value
     )
     or exists (
    select 1 from unnest(new.available_dates) value
    where value is null or value not between new.week_start and new.week_start + 6
  ) then
    raise exception 'swipe draft dates must stay inside the local week'
      using errcode = '23514';
  end if;

  select coalesce(
    array_agg((entry.value ->> 'template_id')::uuid order by entry.ordinality)
      filter (where entry.value ->> 'action' = 'accept'),
    '{}'::uuid[]
  ), coalesce(
    array_agg((entry.value ->> 'template_id')::uuid
      order by (entry.value ->> 'template_id')::uuid)
      filter (where entry.value ->> 'action' = 'pass'),
    '{}'::uuid[]
  ) into v_accepted, v_passed
  from jsonb_array_elements(new.decision_history)
    with ordinality entry(value, ordinality)
  where jsonb_typeof(entry.value) = 'object'
    and entry.value ->> 'action' in ('accept', 'pass')
    and entry.value ->> 'template_id' is not null;

  if v_accepted <> new.accepted_template_ids
     or v_passed <> new.passed_template_ids
     or cardinality(v_accepted) + cardinality(v_passed)
        <> jsonb_array_length(new.decision_history)
     or cardinality(v_accepted) <> (
       select count(distinct value) from unnest(v_accepted) value
     )
     or cardinality(v_passed) <> (
       select count(distinct value) from unnest(v_passed) value
     ) then
    raise exception 'swipe decision history is inconsistent'
      using errcode = '23514';
  end if;

  foreach v_discipline in array array['swim', 'bike', 'run']::text[] loop
    v_expected_count := (new.target_composition ->> v_discipline)::integer;
    select count(*) into v_actual_count
    from public.workout_templates template
    where template.id = any(new.accepted_template_ids)
      and template.discipline = v_discipline;
    if v_actual_count > v_expected_count then
      raise exception 'swipe selection exceeds target composition'
        using errcode = '23514';
    end if;
    if new.state in ('placement', 'submitted')
       and v_actual_count <> v_expected_count then
      raise exception 'swipe selection composition is incomplete'
        using errcode = '23514';
    end if;
  end loop;

  for v_key, v_date in
    select entry.key, (entry.value #>> '{}')::date
    from jsonb_each(new.placements) entry
  loop
    if v_key::uuid <> all(new.accepted_template_ids)
       or v_date <> all(new.available_dates) then
      raise exception 'swipe placement is not an accepted available date'
        using errcode = '23514';
    end if;
  end loop;
  if new.state = 'submitted'
     and jsonb_object_length(new.placements)
       <> cardinality(new.accepted_template_ids) then
    raise exception 'submitted swipe layout is incomplete'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke all on function private.validate_swipe_week_draft()
from public, anon, authenticated, service_role;

create trigger swipe_week_drafts_validate
before insert or update on public.swipe_week_drafts
for each row execute function private.validate_swipe_week_draft();

create trigger swipe_week_drafts_require_rpc
before insert or update or delete on public.swipe_week_drafts
for each row execute function private.require_critical_write_context();

alter table public.swipe_week_drafts enable row level security;
alter table public.swipe_week_drafts force row level security;
revoke all on table public.swipe_week_drafts
from public, anon, authenticated, service_role;
grant select on table public.swipe_week_drafts to authenticated;
grant select, insert, update on table public.swipe_week_drafts to service_role;

create policy swipe_week_drafts_select_own
on public.swipe_week_drafts for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create function public.create_swipe_week_draft(
  p_athlete_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_existing public.swipe_week_drafts;
  v_result public.swipe_week_drafts;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if p_athlete_id is null
     or not exists (select 1 from auth.users where id = p_athlete_id)
     or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'invalid swipe draft input' using errcode = '23514';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(
      p_athlete_id::text || ':swipe:' || (p_payload ->> 'week_start'), 0
    )
  );
  select * into v_existing
  from public.swipe_week_drafts
  where athlete_id = p_athlete_id
    and week_start = (p_payload ->> 'week_start')::date
    and state in ('collecting', 'placement')
  for update;

  if found
     and v_existing.context_fingerprint = p_payload ->> 'context_fingerprint' then
    return to_jsonb(v_existing) - 'athlete_id';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  if v_existing.id is not null then
    update public.swipe_week_drafts
    set state = 'cancelled', current_template_id = null,
        updated_at = statement_timestamp(), revision = revision + 1
    where id = v_existing.id and athlete_id = p_athlete_id;
  end if;

  insert into public.swipe_week_drafts (
    athlete_id, plan_id, initial_plan_request_id, base_plan_revision,
    context_plan_revision, week_start, timezone, available_dates,
    availability_source, confirmed_injuries, low_only_disciplines,
    input_fingerprint, context_fingerprint, ruleset_version,
    target_workout_count, target_composition, accepted_template_ids,
    passed_template_ids, current_template_id, decision_history, placements,
    state
  ) values (
    p_athlete_id, nullif(p_payload ->> 'plan_id', '')::uuid,
    (p_payload ->> 'initial_plan_request_id')::uuid,
    (p_payload ->> 'base_plan_revision')::integer,
    nullif(p_payload ->> 'context_plan_revision', '')::integer,
    (p_payload ->> 'week_start')::date, p_payload ->> 'timezone',
    array(select jsonb_array_elements_text(p_payload -> 'available_dates'))::date[],
    p_payload ->> 'availability_source',
    array(select jsonb_array_elements_text(p_payload -> 'confirmed_injuries')),
    array(select jsonb_array_elements_text(p_payload -> 'low_only_disciplines')),
    p_payload ->> 'input_fingerprint', p_payload ->> 'context_fingerprint',
    p_payload ->> 'ruleset_version',
    (p_payload ->> 'target_workout_count')::integer,
    p_payload -> 'target_composition', '{}', '{}',
    nullif(p_payload ->> 'current_template_id', '')::uuid, '[]', '{}',
    p_payload ->> 'state'
  ) returning * into v_result;
  return to_jsonb(v_result) - 'athlete_id';
end;
$$;

revoke all on function public.create_swipe_week_draft(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_swipe_week_draft(uuid, jsonb)
to service_role;

create function public.update_swipe_week_draft(
  p_athlete_id uuid,
  p_draft_id uuid,
  p_expected_revision bigint,
  p_payload jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_current public.swipe_week_drafts;
  v_result public.swipe_week_drafts;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  select * into v_current
  from public.swipe_week_drafts
  where id = p_draft_id and athlete_id = p_athlete_id
  for update;
  if not found then
    raise exception 'swipe draft not found' using errcode = 'P0002';
  end if;
  if v_current.revision <> p_expected_revision then
    raise exception 'swipe draft is stale' using errcode = '40001';
  end if;
  if v_current.state not in ('collecting', 'placement') then
    raise exception 'swipe draft is closed' using errcode = '40001';
  end if;
  if p_payload ->> 'context_fingerprint' <> v_current.context_fingerprint then
    raise exception 'swipe draft context changed' using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.swipe_week_drafts set
    accepted_template_ids = array(
      select jsonb_array_elements_text(p_payload -> 'accepted_template_ids')
    )::uuid[],
    passed_template_ids = array(
      select jsonb_array_elements_text(p_payload -> 'passed_template_ids')
    )::uuid[],
    current_template_id = nullif(p_payload ->> 'current_template_id', '')::uuid,
    decision_history = p_payload -> 'decision_history',
    placements = p_payload -> 'placements',
    state = p_payload ->> 'state',
    plan_id = case
      when p_payload ->> 'state' = 'submitted'
        then (p_payload ->> 'plan_id')::uuid
      else plan_id
    end,
    proposal_id = nullif(p_payload ->> 'proposal_id', '')::uuid,
    submitted_at = case
      when p_payload ->> 'state' = 'submitted' then statement_timestamp()
      else null
    end,
    revision = revision + 1,
    updated_at = statement_timestamp()
  where id = p_draft_id and athlete_id = p_athlete_id
  returning * into v_result;
  return to_jsonb(v_result) - 'athlete_id';
end;
$$;

revoke all on function public.update_swipe_week_draft(uuid, uuid, bigint, jsonb)
from public, anon, authenticated, service_role;
grant execute
on function public.update_swipe_week_draft(uuid, uuid, bigint, jsonb)
to service_role;
