-- Phase 10.1 production fix: keep the swipe RPCs invoker-secure while granting
-- the trusted backend only the public catalog read needed by draft validation.
-- Athlete existence remains enforced by the swipe_week_drafts foreign key;
-- querying auth.users directly would require an unnecessarily broad grant.

grant select on table public.workout_templates to service_role;

create or replace function public.create_swipe_week_draft(
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
  if p_athlete_id is null or jsonb_typeof(p_payload) <> 'object' then
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
