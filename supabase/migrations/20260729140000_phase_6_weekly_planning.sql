-- Phase 6: deterministic weekly planning, immutable revisions, and approval.

-- The Phase 5 seed had no base/recovery bike workout compatible with the
-- FTP/power setup used by the Phase 4 mobile onboarding flow. Add one reviewed
-- immutable catalog item rather than weakening zone-requirement filtering.
insert into public.workout_templates (
  id,
  template_key,
  version,
  discipline,
  name,
  description,
  duration_minutes,
  distance_meters,
  intensity_bucket,
  expected_rpe_min,
  expected_rpe_max,
  fallback_compatibility
)
values (
  '53000000-0000-0000-0000-000000000007',
  '50000000-0000-0000-0000-000000000007',
  1,
  'bike',
  'Power-guided aerobic endurance',
  'Steady low-intensity endurance riding guided by power zones.',
  60,
  null,
  'low',
  2,
  4,
  'incompatible'
);

insert into public.workout_segments (
  template_id,
  sequence,
  name,
  instructions,
  duration_minutes,
  distance_meters,
  zone_number,
  expected_rpe,
  is_swim_technique
)
values
  (
    '53000000-0000-0000-0000-000000000007',
    1,
    'Easy roll-out',
    'Complete easy roll-out in Zone 1.',
    10,
    null,
    1,
    2,
    false
  ),
  (
    '53000000-0000-0000-0000-000000000007',
    2,
    'Power-zone endurance',
    'Complete power-zone endurance in Zone 2.',
    40,
    null,
    2,
    4,
    false
  ),
  (
    '53000000-0000-0000-0000-000000000007',
    3,
    'Easy finish',
    'Complete easy finish in Zone 1.',
    10,
    null,
    1,
    2,
    false
  );

insert into public.workout_template_phase_tags (template_id, phase)
values
  ('53000000-0000-0000-0000-000000000007', 'base'),
  ('53000000-0000-0000-0000-000000000007', 'build'),
  ('53000000-0000-0000-0000-000000000007', 'recovery');

insert into public.workout_template_zone_requirements (
  template_id,
  requirement
)
values ('53000000-0000-0000-0000-000000000007', 'power');

insert into private.workout_template_loads (
  template_id,
  planned_tss,
  calculation_method,
  ruleset_version
)
values (
  '53000000-0000-0000-0000-000000000007',
  3,
  'expected_rpe_midpoint_times_duration_hours',
  'phase-3-ruleset-2'
);

select private.validate_workout_template(
  '53000000-0000-0000-0000-000000000007'
);

create table public.weekly_plans (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null references auth.users (id) on delete cascade,
  week_start date not null,
  timezone text not null,
  state text not null default 'pending_approval',
  active_revision integer,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (athlete_id, week_start),
  constraint weekly_plans_monday_start check (
    extract(isodow from week_start) = 1
  ),
  constraint weekly_plans_timezone_valid check (
    char_length(btrim(timezone)) between 1 and 100
    and timezone = btrim(timezone)
  ),
  constraint weekly_plans_state_valid check (
    state in (
      'pending_approval',
      'active',
      'superseded',
      'rejected',
      'expired'
    )
  ),
  constraint weekly_plans_active_revision_positive check (
    active_revision is null or active_revision > 0
  )
);

create index weekly_plans_owner_week_idx
on public.weekly_plans (athlete_id, week_start desc);

create table public.plan_revisions (
  id uuid primary key default gen_random_uuid(),
  plan_id uuid not null,
  athlete_id uuid not null,
  revision_number integer not null,
  state text not null,
  source text not null,
  phase text not null,
  target_basis text not null,
  taper_period text,
  input_fingerprint text not null,
  generation_fingerprint text not null,
  initial_plan_request_id uuid,
  total_duration_minutes numeric not null,
  low_intensity_percent numeric not null,
  high_intensity_percent numeric not null,
  confirmed_injuries text[] not null default '{}',
  availability jsonb not null,
  ruleset_version text not null,
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  unique (plan_id, revision_number, athlete_id),
  foreign key (plan_id, athlete_id)
    references public.weekly_plans (id, athlete_id)
    on delete cascade,
  foreign key (initial_plan_request_id, athlete_id)
    references public.initial_plan_requests (id, athlete_id),
  constraint plan_revisions_number_positive check (revision_number > 0),
  constraint plan_revisions_state_valid check (
    state in (
      'draft',
      'pending_approval',
      'active',
      'rejected',
      'superseded',
      'expired'
    )
  ),
  constraint plan_revisions_source_valid check (
    source in ('system_generated', 'athlete_move')
  ),
  constraint plan_revisions_phase_valid check (
    phase in ('base', 'build', 'recovery', 'taper')
  ),
  constraint plan_revisions_target_basis_valid check (
    target_basis in (
      'initial_catalog_baseline',
      'prior_planned_hold',
      'recovery_factor',
      'taper_factor'
    )
  ),
  constraint plan_revisions_taper_consistent check (
    (
      phase = 'taper'
      and taper_period in ('a_t_minus_2', 'a_t_minus_1')
    )
    or (phase <> 'taper' and taper_period is null)
  ),
  constraint plan_revisions_fingerprints_valid check (
    input_fingerprint ~ '^[a-f0-9]{32}$'
    and generation_fingerprint ~ '^[a-f0-9]{64}$'
  ),
  constraint plan_revisions_duration_valid check (
    total_duration_minutes >= 0
  ),
  constraint plan_revisions_distribution_valid check (
    low_intensity_percent between 0 and 100
    and high_intensity_percent between 0 and 100
    and low_intensity_percent + high_intensity_percent = 100
  ),
  constraint plan_revisions_injuries_valid check (
    confirmed_injuries <@ array['swim', 'bike', 'run']::text[]
  ),
  constraint plan_revisions_availability_valid check (
    jsonb_typeof(availability) = 'array'
    and jsonb_array_length(availability) > 0
  ),
  constraint plan_revisions_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

create unique index one_active_revision_per_plan
on public.plan_revisions (plan_id)
where state = 'active';

create unique index one_pending_revision_per_plan
on public.plan_revisions (plan_id)
where state = 'pending_approval';

create unique index plan_revision_generation_idempotency
on public.plan_revisions (athlete_id, plan_id, generation_fingerprint);

alter table public.weekly_plans
  add constraint weekly_plans_active_revision_fkey
  foreign key (id, active_revision, athlete_id)
  references public.plan_revisions (plan_id, revision_number, athlete_id)
  deferrable initially deferred;

create table public.planned_workouts (
  id uuid primary key default gen_random_uuid(),
  revision_id uuid not null,
  plan_id uuid not null,
  athlete_id uuid not null,
  template_id uuid not null references public.workout_templates (id),
  template_key uuid not null,
  template_version integer not null,
  discipline text not null,
  name text not null,
  description text not null,
  duration_minutes numeric not null,
  distance_meters integer,
  intensity_bucket text not null,
  expected_rpe_min smallint not null,
  expected_rpe_max smallint not null,
  segments jsonb not null,
  scheduled_at timestamptz not null,
  timezone text not null,
  source text not null,
  status text not null default 'scheduled',
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  foreign key (revision_id, athlete_id)
    references public.plan_revisions (id, athlete_id)
    on delete cascade,
  foreign key (plan_id, athlete_id)
    references public.weekly_plans (id, athlete_id)
    on delete cascade,
  constraint planned_workouts_template_version_positive check (
    template_version > 0
  ),
  constraint planned_workouts_discipline_valid check (
    discipline in ('swim', 'bike', 'run')
  ),
  constraint planned_workouts_duration_positive check (
    duration_minutes > 0
  ),
  constraint planned_workouts_distance_positive check (
    distance_meters is null or distance_meters > 0
  ),
  constraint planned_workouts_intensity_valid check (
    intensity_bucket in ('low', 'high')
  ),
  constraint planned_workouts_rpe_valid check (
    expected_rpe_min between 1 and 10
    and expected_rpe_max between expected_rpe_min and 10
  ),
  constraint planned_workouts_segments_valid check (
    jsonb_typeof(segments) = 'array'
    and jsonb_array_length(segments) > 0
  ),
  constraint planned_workouts_source_valid check (
    source in (
      'auto_planned',
      'athlete_selected',
      'athlete_moved',
      'system_adjusted'
    )
  ),
  constraint planned_workouts_status_valid check (
    status in ('scheduled', 'completed', 'cancelled')
  )
);

create index planned_workouts_revision_idx
on public.planned_workouts (revision_id, scheduled_at);
create index planned_workouts_owner_calendar_idx
on public.planned_workouts (athlete_id, scheduled_at);

create table public.plan_warnings (
  id uuid primary key default gen_random_uuid(),
  revision_id uuid not null,
  athlete_id uuid not null,
  planned_workout_id uuid,
  rule_id text not null,
  code text not null,
  severity text not null,
  message text not null,
  created_at timestamptz not null default statement_timestamp(),

  unique (id, athlete_id),
  foreign key (revision_id, athlete_id)
    references public.plan_revisions (id, athlete_id)
    on delete cascade,
  foreign key (planned_workout_id, athlete_id)
    references public.planned_workouts (id, athlete_id)
    on delete cascade,
  constraint plan_warnings_rule_valid check (
    rule_id ~ '^BR-[0-9]{3}$'
  ),
  constraint plan_warnings_code_valid check (
    code ~ '^[a-z][a-z0-9_]{2,63}$'
  ),
  constraint plan_warnings_severity_valid check (
    severity in ('info', 'warning', 'conflict')
  ),
  constraint plan_warnings_message_valid check (
    char_length(btrim(message)) between 1 and 500
    and message = btrim(message)
  )
);

create index plan_warnings_revision_idx
on public.plan_warnings (revision_id);

create table private.planned_workout_loads (
  planned_workout_id uuid primary key
    references public.planned_workouts (id)
    on delete cascade,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  planned_tss numeric not null,
  calculation_method text not null,
  ruleset_version text not null,
  created_at timestamptz not null default statement_timestamp(),

  constraint planned_workout_loads_value_valid check (planned_tss >= 0),
  constraint planned_workout_loads_method_valid check (
    calculation_method ~ '^[a-z][a-z0-9._-]{2,63}$'
  ),
  constraint planned_workout_loads_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

create index planned_workout_loads_owner_idx
on private.planned_workout_loads (athlete_id);

create table private.plan_revision_loads (
  revision_id uuid primary key
    references public.plan_revisions (id)
    on delete cascade,
  athlete_id uuid not null references auth.users (id) on delete cascade,
  target_tss numeric not null,
  planned_tss numeric not null,
  ruleset_version text not null,
  created_at timestamptz not null default statement_timestamp(),

  constraint plan_revision_loads_target_valid check (target_tss >= 0),
  constraint plan_revision_loads_planned_valid check (planned_tss >= 0),
  constraint plan_revision_loads_ruleset_valid check (
    ruleset_version ~ '^[a-z0-9][a-z0-9._-]{0,63}$'
  )
);

create index plan_revision_loads_owner_idx
on private.plan_revision_loads (athlete_id);

alter table public.change_proposals
  add column target_plan_revision_id uuid,
  add column base_plan_revision integer,
  add column decision_actor uuid references auth.users (id);

alter table public.change_proposals
  drop constraint change_proposals_kind_valid,
  drop constraint change_proposals_target_required;

alter table public.change_proposals
  add constraint change_proposals_target_plan_revision_fkey
  foreign key (target_plan_revision_id, athlete_id)
  references public.plan_revisions (id, athlete_id),
  add constraint change_proposals_kind_valid check (
    kind in ('zone_update', 'plan_revision')
  ),
  add constraint change_proposals_typed_target_valid check (
    (
      kind = 'zone_update'
      and target_zone_profile_id is not null
      and target_plan_revision_id is null
      and base_plan_revision is null
    )
    or (
      kind = 'plan_revision'
      and target_plan_revision_id is not null
      and target_zone_profile_id is null
      and base_zone_profile_id is null
      and base_plan_revision >= 0
    )
  );

create unique index one_pending_proposal_per_plan_revision
on public.change_proposals (target_plan_revision_id)
where state = 'pending' and target_plan_revision_id is not null;

create index change_proposals_plan_target_owner_idx
on public.change_proposals (target_plan_revision_id, athlete_id)
where target_plan_revision_id is not null;

alter table public.weekly_plans enable row level security;
alter table public.weekly_plans force row level security;
alter table public.plan_revisions enable row level security;
alter table public.plan_revisions force row level security;
alter table public.planned_workouts enable row level security;
alter table public.planned_workouts force row level security;
alter table public.plan_warnings enable row level security;
alter table public.plan_warnings force row level security;

revoke all on table public.weekly_plans
from public, anon, authenticated, service_role;
revoke all on table public.plan_revisions
from public, anon, authenticated, service_role;
revoke all on table public.planned_workouts
from public, anon, authenticated, service_role;
revoke all on table public.plan_warnings
from public, anon, authenticated, service_role;
revoke all on table private.planned_workout_loads
from public, anon, authenticated, service_role;
revoke all on table private.plan_revision_loads
from public, anon, authenticated, service_role;

grant select, insert, update
on table public.weekly_plans to authenticated;
grant select, insert, update
on table public.plan_revisions to authenticated;
grant select, insert, update
on table public.planned_workouts to authenticated;
grant select, insert
on table public.plan_warnings to authenticated;

create policy weekly_plans_select_own
on public.weekly_plans for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy weekly_plans_insert_own
on public.weekly_plans for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy weekly_plans_update_own
on public.weekly_plans for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy plan_revisions_select_own
on public.plan_revisions for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy plan_revisions_insert_own
on public.plan_revisions for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy plan_revisions_update_own
on public.plan_revisions for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy planned_workouts_select_own
on public.planned_workouts for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy planned_workouts_insert_own
on public.planned_workouts for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy planned_workouts_update_own
on public.planned_workouts for update to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create policy plan_warnings_select_own
on public.plan_warnings for select to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);
create policy plan_warnings_insert_own
on public.plan_warnings for insert to authenticated
with check ((select auth.uid()) is not null and (select auth.uid()) = athlete_id);

create trigger weekly_plans_require_rpc
before insert or update or delete on public.weekly_plans
for each row execute function private.require_critical_write_context();
create trigger plan_revisions_require_rpc
before insert or update or delete on public.plan_revisions
for each row execute function private.require_critical_write_context();
create trigger planned_workouts_require_rpc
before insert or update or delete on public.planned_workouts
for each row execute function private.require_critical_write_context();
create trigger plan_warnings_require_rpc
before insert or update or delete on public.plan_warnings
for each row execute function private.require_critical_write_context();

create function private.set_phase_6_update_metadata()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := statement_timestamp();
  return new;
end;
$$;

revoke execute on function private.set_phase_6_update_metadata()
from public, anon, authenticated, service_role;

create trigger weekly_plans_set_update_metadata
before update on public.weekly_plans
for each row execute function private.set_phase_6_update_metadata();

create function public.create_weekly_plan_proposal(
  p_athlete_id uuid,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_plan_id uuid;
  v_revision_id uuid;
  v_revision integer;
  v_proposal_id uuid;
  v_request_id uuid;
  v_workout jsonb;
  v_warning jsonb;
  v_workout_id uuid;
  v_planned_tss numeric := 0;
  v_existing record;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  if p_athlete_id is null
     or not exists (select 1 from auth.users where id = p_athlete_id) then
    raise exception 'athlete not found' using errcode = 'P0002';
  end if;
  if jsonb_typeof(p_payload) <> 'object'
     or not p_payload ?& array[
       'input_fingerprint',
       'generation_fingerprint',
       'expected_base_revision',
       'week_start',
       'timezone',
       'phase',
       'target_basis',
       'total_duration_minutes',
       'low_intensity_percent',
       'high_intensity_percent',
       'confirmed_injuries',
       'availability',
       'workouts',
       'warnings',
       'target_tss',
       'planned_tss',
       'ruleset_version'
     ] then
    raise exception 'planning payload is incomplete' using errcode = '23514';
  end if;
  if jsonb_typeof(p_payload -> 'workouts') <> 'array'
     or jsonb_array_length(p_payload -> 'workouts') = 0 then
    raise exception 'planning payload requires workouts' using errcode = '23514';
  end if;

  v_request_id := nullif(p_payload ->> 'initial_plan_request_id', '')::uuid;
  v_plan_id := nullif(p_payload ->> 'plan_id', '')::uuid;

  if v_request_id is not null and not exists (
    select 1
    from public.initial_plan_requests request
    where request.id = v_request_id
      and request.athlete_id = p_athlete_id
      and request.input_fingerprint = p_payload ->> 'input_fingerprint'
      and request.status in ('pending', 'consumed')
  ) then
    raise exception 'planning input is stale' using errcode = '40001';
  end if;

  if v_plan_id is not null then
    select plan.id, plan.active_revision
    into v_existing
    from public.weekly_plans plan
    where plan.id = v_plan_id and plan.athlete_id = p_athlete_id
    for update;
    if not found then
      raise exception 'weekly plan not found' using errcode = 'P0002';
    end if;
    if coalesce(v_existing.active_revision, 0)
       <> (p_payload ->> 'expected_base_revision')::integer then
      raise exception 'plan revision is stale' using errcode = '40001';
    end if;
  else
    select plan.id, plan.active_revision
    into v_existing
    from public.weekly_plans plan
    where plan.athlete_id = p_athlete_id
      and plan.week_start = (p_payload ->> 'week_start')::date
    for update;
    if found then
      v_plan_id := v_existing.id;
      if coalesce(v_existing.active_revision, 0)
         <> (p_payload ->> 'expected_base_revision')::integer then
        raise exception 'plan revision is stale' using errcode = '40001';
      end if;
    end if;
  end if;

  if v_plan_id is not null then
    select
      proposal.id,
      revision.revision_number
    into v_proposal_id, v_revision
    from public.plan_revisions revision
    join public.change_proposals proposal
      on proposal.target_plan_revision_id = revision.id
     and proposal.athlete_id = revision.athlete_id
    where revision.plan_id = v_plan_id
      and revision.athlete_id = p_athlete_id
      and revision.generation_fingerprint =
        p_payload ->> 'generation_fingerprint'
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
    insert into public.weekly_plans (
      athlete_id,
      week_start,
      timezone,
      state
    )
    values (
      p_athlete_id,
      (p_payload ->> 'week_start')::date,
      p_payload ->> 'timezone',
      'pending_approval'
    )
    returning id into v_plan_id;
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

  select coalesce(max(revision_number), 0) + 1
  into v_revision
  from public.plan_revisions
  where plan_id = v_plan_id and athlete_id = p_athlete_id;

  insert into public.plan_revisions (
    plan_id,
    athlete_id,
    revision_number,
    state,
    source,
    phase,
    target_basis,
    taper_period,
    input_fingerprint,
    generation_fingerprint,
    initial_plan_request_id,
    total_duration_minutes,
    low_intensity_percent,
    high_intensity_percent,
    confirmed_injuries,
    availability,
    ruleset_version
  )
  values (
    v_plan_id,
    p_athlete_id,
    v_revision,
    'pending_approval',
    'system_generated',
    p_payload ->> 'phase',
    p_payload ->> 'target_basis',
    nullif(p_payload ->> 'taper_period', ''),
    p_payload ->> 'input_fingerprint',
    p_payload ->> 'generation_fingerprint',
    v_request_id,
    (p_payload ->> 'total_duration_minutes')::numeric,
    (p_payload ->> 'low_intensity_percent')::numeric,
    (p_payload ->> 'high_intensity_percent')::numeric,
    array(
      select jsonb_array_elements_text(p_payload -> 'confirmed_injuries')
    ),
    p_payload -> 'availability',
    p_payload ->> 'ruleset_version'
  )
  returning id into v_revision_id;

  for v_workout in
    select value from jsonb_array_elements(p_payload -> 'workouts')
  loop
    if not exists (
      select 1
      from public.workout_templates template
      where template.id = (v_workout ->> 'template_id')::uuid
        and template.discipline = v_workout ->> 'discipline'
    ) then
      raise exception 'workout template is invalid' using errcode = '23514';
    end if;
    if (v_workout ->> 'discipline') = any(
      array(
        select jsonb_array_elements_text(
          p_payload -> 'confirmed_injuries'
        )
      )
    ) then
      raise exception 'injured discipline cannot be planned'
        using errcode = '23514';
    end if;

    insert into public.planned_workouts (
      revision_id,
      plan_id,
      athlete_id,
      template_id,
      template_key,
      template_version,
      discipline,
      name,
      description,
      duration_minutes,
      distance_meters,
      intensity_bucket,
      expected_rpe_min,
      expected_rpe_max,
      segments,
      scheduled_at,
      timezone,
      source
    )
    select
      v_revision_id,
      v_plan_id,
      p_athlete_id,
      template.id,
      template.template_key,
      template.version,
      template.discipline,
      template.name,
      template.description,
      template.duration_minutes,
      template.distance_meters,
      template.intensity_bucket,
      template.expected_rpe_min,
      template.expected_rpe_max,
      (
        select jsonb_agg(
          jsonb_build_object(
            'sequence', segment.sequence,
            'name', segment.name,
            'instructions', segment.instructions,
            'duration_minutes', segment.duration_minutes,
            'distance_meters', segment.distance_meters,
            'zone', segment.zone_number,
            'expected_rpe', segment.expected_rpe,
            'is_swim_technique', segment.is_swim_technique
          )
          order by segment.sequence
        )
        from public.workout_segments segment
        where segment.template_id = template.id
      ),
      (v_workout ->> 'scheduled_at')::timestamptz,
      p_payload ->> 'timezone',
      v_workout ->> 'source'
    from public.workout_templates template
    where template.id = (v_workout ->> 'template_id')::uuid
    returning id into v_workout_id;

    insert into private.planned_workout_loads (
      planned_workout_id,
      athlete_id,
      planned_tss,
      calculation_method,
      ruleset_version
    )
    select
      v_workout_id,
      p_athlete_id,
      load.planned_tss,
      load.calculation_method,
      load.ruleset_version
    from private.workout_template_loads load
    where load.template_id = (v_workout ->> 'template_id')::uuid;
  end loop;

  select coalesce(sum(load.planned_tss), 0)
  into v_planned_tss
  from private.planned_workout_loads load
  join public.planned_workouts workout
    on workout.id = load.planned_workout_id
  where workout.revision_id = v_revision_id;

  if v_planned_tss <> (p_payload ->> 'planned_tss')::numeric then
    raise exception 'planned load snapshot mismatch' using errcode = '23514';
  end if;

  insert into private.plan_revision_loads (
    revision_id,
    athlete_id,
    target_tss,
    planned_tss,
    ruleset_version
  )
  values (
    v_revision_id,
    p_athlete_id,
    (p_payload ->> 'target_tss')::numeric,
    v_planned_tss,
    p_payload ->> 'ruleset_version'
  );

  for v_warning in
    select value from jsonb_array_elements(p_payload -> 'warnings')
  loop
    insert into public.plan_warnings (
      revision_id,
      athlete_id,
      planned_workout_id,
      rule_id,
      code,
      severity,
      message
    )
    values (
      v_revision_id,
      p_athlete_id,
      (
        select workout.id
        from public.planned_workouts workout
        where workout.revision_id = v_revision_id
          and workout.template_id =
            nullif(v_warning ->> 'affected_template_id', '')::uuid
        limit 1
      ),
      v_warning ->> 'rule_id',
      v_warning ->> 'code',
      v_warning ->> 'severity',
      v_warning ->> 'message'
    );
  end loop;

  insert into public.change_proposals (
    athlete_id,
    kind,
    target_plan_revision_id,
    base_plan_revision,
    reason_codes,
    public_explanation,
    ruleset_version
  )
  values (
    p_athlete_id,
    'plan_revision',
    v_revision_id,
    (p_payload ->> 'expected_base_revision')::integer,
    case
      when jsonb_array_length(p_payload -> 'warnings') = 0
        then array['weekly_plan_ready']
      else array(
        select warning ->> 'code'
        from jsonb_array_elements(p_payload -> 'warnings') warning
      )
    end,
    'A deterministic weekly plan is ready for review.',
    p_payload ->> 'ruleset_version'
  )
  returning id into v_proposal_id;

  if v_request_id is not null then
    update public.initial_plan_requests
    set status = 'consumed', consumed_at = statement_timestamp()
    where id = v_request_id
      and athlete_id = p_athlete_id
      and status = 'pending';
  end if;

  update public.weekly_plans
  set state = case
    when active_revision is null then 'pending_approval'
    else state
  end
  where id = v_plan_id and athlete_id = p_athlete_id;

  return jsonb_build_object(
    'plan_id', v_plan_id,
    'revision', v_revision,
    'proposal_id', v_proposal_id
  );
end;
$$;

revoke all on function public.create_weekly_plan_proposal(uuid, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal(uuid, jsonb)
to service_role;

create function public.get_plan_load_history_for_planning(
  p_athlete_id uuid,
  p_before_week date
)
returns table (
  week_start date,
  phase text,
  planned_tss numeric
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
  select plan.week_start, revision.phase, load.planned_tss
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  join private.plan_revision_loads load
    on load.revision_id = revision.id
   and load.athlete_id = plan.athlete_id
  where plan.athlete_id = p_athlete_id
    and plan.week_start < p_before_week
  order by plan.week_start;
end;
$$;

revoke all
on function public.get_plan_load_history_for_planning(uuid, date)
from public, anon, authenticated, service_role;
grant execute
on function public.get_plan_load_history_for_planning(uuid, date)
to service_role;

create function public.get_plan_context_for_planning(
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

revoke all on function public.get_plan_context_for_planning(uuid, uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_plan_context_for_planning(uuid, uuid)
to service_role;

create function public.get_weekly_plan(
  p_plan_id uuid,
  p_revision integer default null
)
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
    'id', plan.id,
    'week_start', plan.week_start,
    'timezone', plan.timezone,
    'state', plan.state,
    'active_revision', plan.active_revision,
    'revision_id', revision.id,
    'revision', revision.revision_number,
    'revision_state', revision.state,
    'phase', revision.phase,
    'target_basis', revision.target_basis,
    'taper_period', revision.taper_period,
    'total_duration_minutes', revision.total_duration_minutes,
    'low_intensity_percent', revision.low_intensity_percent,
    'high_intensity_percent', revision.high_intensity_percent,
    'confirmed_injuries', revision.confirmed_injuries,
    'workouts', (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'id', workout.id,
            'template_id', workout.template_id,
            'template_key', workout.template_key,
            'template_version', workout.template_version,
            'discipline', workout.discipline,
            'name', workout.name,
            'description', workout.description,
            'duration_minutes', workout.duration_minutes,
            'distance_meters', workout.distance_meters,
            'intensity_bucket', workout.intensity_bucket,
            'expected_rpe_min', workout.expected_rpe_min,
            'expected_rpe_max', workout.expected_rpe_max,
            'segments', workout.segments,
            'scheduled_at', workout.scheduled_at,
            'timezone', workout.timezone,
            'source', workout.source,
            'status', workout.status,
            'warnings', (
              select coalesce(
                jsonb_agg(
                  jsonb_build_object(
                    'id', warning.id,
                    'rule_id', warning.rule_id,
                    'code', warning.code,
                    'severity', warning.severity,
                    'message', warning.message,
                    'planned_workout_id', warning.planned_workout_id
                  )
                  order by warning.created_at, warning.id
                ),
                '[]'::jsonb
              )
              from public.plan_warnings warning
              where warning.revision_id = revision.id
                and warning.planned_workout_id = workout.id
            )
          )
          order by workout.scheduled_at, workout.id
        ),
        '[]'::jsonb
      )
      from public.planned_workouts workout
      where workout.revision_id = revision.id
    ),
    'warnings', (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'id', warning.id,
            'rule_id', warning.rule_id,
            'code', warning.code,
            'severity', warning.severity,
            'message', warning.message,
            'planned_workout_id', warning.planned_workout_id
          )
          order by warning.created_at, warning.id
        ),
        '[]'::jsonb
      )
      from public.plan_warnings warning
      where warning.revision_id = revision.id
    ),
    'proposal', (
      select jsonb_build_object(
        'id', proposal.id,
        'kind', proposal.kind,
        'state', proposal.state,
        'reason_codes', proposal.reason_codes,
        'public_explanation', proposal.public_explanation,
        'ruleset_version', proposal.ruleset_version,
        'created_at', proposal.created_at,
        'decided_at', proposal.decided_at,
        'applied_at', proposal.applied_at,
        'decision_actor', proposal.decision_actor,
        'target_plan_revision_id', proposal.target_plan_revision_id,
        'base_plan_revision', proposal.base_plan_revision,
        'target_zone_profile_id', proposal.target_zone_profile_id,
        'base_zone_profile_id', proposal.base_zone_profile_id
      )
      from public.change_proposals proposal
      where proposal.target_plan_revision_id = revision.id
      order by proposal.created_at desc
      limit 1
    )
  )
  into v_result
  from public.weekly_plans plan
  join lateral (
    select candidate.*
    from public.plan_revisions candidate
    where candidate.plan_id = plan.id
      and candidate.athlete_id = v_athlete_id
      and (
        candidate.revision_number = p_revision
        or (
          p_revision is null
          and candidate.revision_number = coalesce(
            plan.active_revision,
            (
              select max(pending.revision_number)
              from public.plan_revisions pending
              where pending.plan_id = plan.id
                and pending.state = 'pending_approval'
            )
          )
        )
      )
    limit 1
  ) revision on true
  where plan.id = p_plan_id and plan.athlete_id = v_athlete_id;

  if v_result is null then
    raise exception 'weekly plan not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_weekly_plan(uuid, integer)
from public, anon, authenticated, service_role;
grant execute on function public.get_weekly_plan(uuid, integer)
to authenticated;

create function public.approve_plan_proposal(
  p_proposal_id uuid,
  p_expected_base_revision integer
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_proposal public.change_proposals;
  v_revision public.plan_revisions;
  v_plan public.weekly_plans;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select * into v_proposal
  from public.change_proposals
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and kind = 'plan_revision'
  for update;
  if not found then
    raise exception 'plan proposal not found' using errcode = 'P0002';
  end if;
  if v_proposal.base_plan_revision <> p_expected_base_revision then
    raise exception 'plan proposal is stale' using errcode = '40001';
  end if;

  select * into v_revision
  from public.plan_revisions
  where id = v_proposal.target_plan_revision_id
    and athlete_id = v_athlete_id
  for update;
  select * into v_plan
  from public.weekly_plans
  where id = v_revision.plan_id and athlete_id = v_athlete_id
  for update;
  if v_proposal.state = 'applied' then
    return jsonb_build_object(
      'proposal_id', p_proposal_id,
      'state', 'applied',
      'plan_id', v_plan.id,
      'active_revision', v_revision.revision_number,
      'target_revision_id', v_revision.id
    );
  end if;
  if v_proposal.state <> 'pending' then
    raise exception 'plan proposal is not pending' using errcode = '40001';
  end if;
  if v_revision.state <> 'pending_approval'
     or coalesce(v_plan.active_revision, 0) <> p_expected_base_revision then
    raise exception 'plan proposal is stale' using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  if v_plan.active_revision is not null then
    update public.plan_revisions
    set state = 'superseded'
    where plan_id = v_plan.id
      and athlete_id = v_athlete_id
      and revision_number = v_plan.active_revision
      and state = 'active';
  end if;
  update public.plan_revisions
  set state = 'active'
  where id = v_revision.id and athlete_id = v_athlete_id;
  update public.weekly_plans
  set state = 'active', active_revision = v_revision.revision_number
  where id = v_plan.id and athlete_id = v_athlete_id;
  update public.change_proposals
  set
    state = 'applied',
    decided_at = statement_timestamp(),
    applied_at = statement_timestamp(),
    decision_actor = v_athlete_id
  where id = p_proposal_id and athlete_id = v_athlete_id;

  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'applied',
    'plan_id', v_plan.id,
    'active_revision', v_revision.revision_number,
    'target_revision_id', v_revision.id
  );
end;
$$;

revoke all on function public.approve_plan_proposal(uuid, integer)
from public, anon, authenticated, service_role;
grant execute on function public.approve_plan_proposal(uuid, integer)
to authenticated;

create function public.reject_plan_proposal(p_proposal_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_proposal public.change_proposals;
  v_revision public.plan_revisions;
  v_plan public.weekly_plans;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  select * into v_proposal
  from public.change_proposals
  where id = p_proposal_id
    and athlete_id = v_athlete_id
    and kind = 'plan_revision'
  for update;
  if not found then
    raise exception 'plan proposal not found' using errcode = 'P0002';
  end if;
  select * into v_revision
  from public.plan_revisions
  where id = v_proposal.target_plan_revision_id
    and athlete_id = v_athlete_id
  for update;
  select * into v_plan
  from public.weekly_plans
  where id = v_revision.plan_id and athlete_id = v_athlete_id
  for update;
  if v_proposal.state = 'rejected' then
    return jsonb_build_object(
      'proposal_id', p_proposal_id,
      'state', 'rejected',
      'plan_id', v_plan.id,
      'active_revision', v_plan.active_revision,
      'target_revision_id', v_revision.id
    );
  end if;
  if v_proposal.state <> 'pending' then
    raise exception 'plan proposal is not pending' using errcode = '40001';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  update public.plan_revisions
  set state = 'rejected'
  where id = v_revision.id and athlete_id = v_athlete_id;
  update public.change_proposals
  set
    state = 'rejected',
    decided_at = statement_timestamp(),
    decision_actor = v_athlete_id
  where id = p_proposal_id and athlete_id = v_athlete_id;
  if v_plan.active_revision is null then
    update public.weekly_plans
    set state = 'rejected'
    where id = v_plan.id and athlete_id = v_athlete_id;
  end if;

  return jsonb_build_object(
    'proposal_id', p_proposal_id,
    'state', 'rejected',
    'plan_id', v_plan.id,
    'active_revision', v_plan.active_revision,
    'target_revision_id', v_revision.id
  );
end;
$$;

revoke all on function public.reject_plan_proposal(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.reject_plan_proposal(uuid)
to authenticated;

create function public.get_planned_workout_context(p_workout_id uuid)
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
    'plan', public.get_weekly_plan(plan.id, revision.revision_number),
    'availability', revision.availability
  )
  into v_result
  from public.planned_workouts workout
  join public.plan_revisions revision
    on revision.id = workout.revision_id
   and revision.athlete_id = workout.athlete_id
  join public.weekly_plans plan
    on plan.id = workout.plan_id
   and plan.athlete_id = workout.athlete_id
  where workout.id = p_workout_id
    and workout.athlete_id = v_athlete_id
    and revision.state = 'active'
    and plan.active_revision = revision.revision_number;
  if v_result is null then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  return v_result;
end;
$$;

revoke all on function public.get_planned_workout_context(uuid)
from public, anon, authenticated, service_role;
grant execute on function public.get_planned_workout_context(uuid)
to authenticated;

create function public.move_planned_workout(
  p_athlete_id uuid,
  p_workout_id uuid,
  p_expected_revision integer,
  p_scheduled_at timestamptz,
  p_warnings jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_plan public.weekly_plans;
  v_old_revision public.plan_revisions;
  v_new_revision_id uuid;
  v_new_revision integer;
  v_old_workout record;
  v_new_workout_id uuid;
  v_warning jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required'
      using errcode = '42501';
  end if;
  select plan.* into v_plan
  from public.weekly_plans plan
  join public.planned_workouts workout
    on workout.plan_id = plan.id
   and workout.athlete_id = plan.athlete_id
  where workout.id = p_workout_id
    and plan.athlete_id = p_athlete_id
  for update of plan;
  if not found then
    raise exception 'planned workout not found' using errcode = 'P0002';
  end if;
  if v_plan.active_revision <> p_expected_revision then
    raise exception 'plan revision is stale' using errcode = '40001';
  end if;
  select * into v_old_revision
  from public.plan_revisions
  where plan_id = v_plan.id
    and athlete_id = p_athlete_id
    and revision_number = p_expected_revision
    and state = 'active'
  for update;
  if not found then
    raise exception 'active plan revision not found' using errcode = '40001';
  end if;
  if exists (
    select 1
    from public.planned_workouts workout
    where workout.id = p_workout_id
      and workout.revision_id = v_old_revision.id
      and workout.discipline = any(v_old_revision.confirmed_injuries)
  ) then
    raise exception 'injured discipline cannot be scheduled'
      using errcode = '23514';
  end if;
  if (p_scheduled_at at time zone v_plan.timezone)::date
     not between v_plan.week_start and v_plan.week_start + 6 then
    raise exception 'workout move must remain in its plan week'
      using errcode = '23514';
  end if;
  if jsonb_typeof(p_warnings) <> 'array' then
    raise exception 'warnings must be an array' using errcode = '23514';
  end if;

  perform set_config('start23.critical_write', 'on', true);
  v_new_revision := p_expected_revision + 1;
  insert into public.plan_revisions (
    plan_id,
    athlete_id,
    revision_number,
    state,
    source,
    phase,
    target_basis,
    taper_period,
    input_fingerprint,
    generation_fingerprint,
    initial_plan_request_id,
    total_duration_minutes,
    low_intensity_percent,
    high_intensity_percent,
    confirmed_injuries,
    availability,
    ruleset_version
  )
  values (
    v_plan.id,
    p_athlete_id,
    v_new_revision,
    'draft',
    'athlete_move',
    v_old_revision.phase,
    v_old_revision.target_basis,
    v_old_revision.taper_period,
    v_old_revision.input_fingerprint,
    encode(
      sha256(
        convert_to(
          v_old_revision.generation_fingerprint
          || ':' || v_new_revision::text
          || ':' || p_scheduled_at::text,
          'UTF8'
        )
      ),
      'hex'
    ),
    v_old_revision.initial_plan_request_id,
    v_old_revision.total_duration_minutes,
    v_old_revision.low_intensity_percent,
    v_old_revision.high_intensity_percent,
    v_old_revision.confirmed_injuries,
    v_old_revision.availability,
    v_old_revision.ruleset_version
  )
  returning id into v_new_revision_id;

  for v_old_workout in
    select *
    from public.planned_workouts
    where revision_id = v_old_revision.id
    order by scheduled_at, id
  loop
    insert into public.planned_workouts (
      revision_id,
      plan_id,
      athlete_id,
      template_id,
      template_key,
      template_version,
      discipline,
      name,
      description,
      duration_minutes,
      distance_meters,
      intensity_bucket,
      expected_rpe_min,
      expected_rpe_max,
      segments,
      scheduled_at,
      timezone,
      source,
      status
    )
    values (
      v_new_revision_id,
      v_plan.id,
      p_athlete_id,
      v_old_workout.template_id,
      v_old_workout.template_key,
      v_old_workout.template_version,
      v_old_workout.discipline,
      v_old_workout.name,
      v_old_workout.description,
      v_old_workout.duration_minutes,
      v_old_workout.distance_meters,
      v_old_workout.intensity_bucket,
      v_old_workout.expected_rpe_min,
      v_old_workout.expected_rpe_max,
      v_old_workout.segments,
      case
        when v_old_workout.id = p_workout_id then p_scheduled_at
        else v_old_workout.scheduled_at
      end,
      v_old_workout.timezone,
      case
        when v_old_workout.id = p_workout_id then 'athlete_moved'
        else v_old_workout.source
      end,
      v_old_workout.status
    )
    returning id into v_new_workout_id;

    insert into private.planned_workout_loads (
      planned_workout_id,
      athlete_id,
      planned_tss,
      calculation_method,
      ruleset_version
    )
    select
      v_new_workout_id,
      p_athlete_id,
      load.planned_tss,
      load.calculation_method,
      load.ruleset_version
    from private.planned_workout_loads load
    where load.planned_workout_id = v_old_workout.id;
  end loop;

  insert into private.plan_revision_loads (
    revision_id,
    athlete_id,
    target_tss,
    planned_tss,
    ruleset_version
  )
  select
    v_new_revision_id,
    p_athlete_id,
    load.target_tss,
    load.planned_tss,
    load.ruleset_version
  from private.plan_revision_loads load
  where load.revision_id = v_old_revision.id;

  insert into public.plan_warnings (
    revision_id,
    athlete_id,
    rule_id,
    code,
    severity,
    message
  )
  select
    v_new_revision_id,
    p_athlete_id,
    warning.rule_id,
    warning.code,
    warning.severity,
    warning.message
  from public.plan_warnings warning
  where warning.revision_id = v_old_revision.id
    and warning.code not in (
      'anti_stack_violation',
      'outside_confirmed_availability'
    );

  for v_warning in
    select value from jsonb_array_elements(p_warnings)
  loop
    insert into public.plan_warnings (
      revision_id,
      athlete_id,
      planned_workout_id,
      rule_id,
      code,
      severity,
      message
    )
    values (
      v_new_revision_id,
      p_athlete_id,
      (
        select workout.id
        from public.planned_workouts workout
        where workout.revision_id = v_new_revision_id
          and workout.source = 'athlete_moved'
        limit 1
      ),
      v_warning ->> 'rule_id',
      v_warning ->> 'code',
      v_warning ->> 'severity',
      v_warning ->> 'message'
    );
  end loop;

  update public.plan_revisions
  set state = 'superseded'
  where id = v_old_revision.id and athlete_id = p_athlete_id;
  update public.plan_revisions
  set state = 'active'
  where id = v_new_revision_id and athlete_id = p_athlete_id;
  update public.weekly_plans
  set active_revision = v_new_revision, state = 'active'
  where id = v_plan.id and athlete_id = p_athlete_id;

  update public.change_proposals proposal
  set state = 'expired', decided_at = statement_timestamp()
  from public.plan_revisions revision
  where proposal.target_plan_revision_id = revision.id
    and revision.plan_id = v_plan.id
    and proposal.athlete_id = p_athlete_id
    and proposal.state = 'pending';
  update public.plan_revisions
  set state = 'expired'
  where plan_id = v_plan.id
    and athlete_id = p_athlete_id
    and state = 'pending_approval';

  return jsonb_build_object(
    'plan_id', v_plan.id,
    'revision', v_new_revision
  );
end;
$$;

revoke all
on function public.move_planned_workout(
  uuid,
  uuid,
  integer,
  timestamptz,
  jsonb
)
from public, anon, authenticated, service_role;
grant execute
on function public.move_planned_workout(
  uuid,
  uuid,
  integer,
  timestamptz,
  jsonb
)
to service_role;

create function public.get_calendar(
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
    'id', workout.id,
    'template_id', workout.template_id,
    'template_key', workout.template_key,
    'template_version', workout.template_version,
    'discipline', workout.discipline,
    'name', workout.name,
    'description', workout.description,
    'duration_minutes', workout.duration_minutes,
    'distance_meters', workout.distance_meters,
    'intensity_bucket', workout.intensity_bucket,
    'expected_rpe_min', workout.expected_rpe_min,
    'expected_rpe_max', workout.expected_rpe_max,
    'segments', workout.segments,
    'scheduled_at', workout.scheduled_at,
    'timezone', workout.timezone,
    'source', workout.source,
    'status', workout.status,
    'warnings', (
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'id', warning.id,
            'rule_id', warning.rule_id,
            'code', warning.code,
            'severity', warning.severity,
            'message', warning.message,
            'planned_workout_id', warning.planned_workout_id
          )
          order by warning.created_at, warning.id
        ),
        '[]'::jsonb
      )
      from public.plan_warnings warning
      where warning.revision_id = revision.id
        and (
          warning.planned_workout_id is null
          or warning.planned_workout_id = workout.id
        )
    )
  )
  from public.weekly_plans plan
  join public.plan_revisions revision
    on revision.plan_id = plan.id
   and revision.athlete_id = plan.athlete_id
   and revision.revision_number = plan.active_revision
  join public.planned_workouts workout
    on workout.revision_id = revision.id
   and workout.athlete_id = plan.athlete_id
  where plan.athlete_id = (select auth.uid())
    and workout.scheduled_at >= p_from
    and workout.scheduled_at < p_to
  order by workout.scheduled_at, workout.id;
$$;

revoke all on function public.get_calendar(timestamptz, timestamptz)
from public, anon, authenticated, service_role;
grant execute on function public.get_calendar(timestamptz, timestamptz)
to authenticated;
