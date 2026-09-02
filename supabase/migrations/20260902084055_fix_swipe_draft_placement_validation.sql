-- Phase 10.1 production fix: PostgreSQL has jsonb_array_length but no
-- jsonb_object_length. Count placement keys without weakening validation.

create or replace function private.validate_swipe_week_draft()
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
     and (select count(*) from jsonb_object_keys(new.placements))
       <> cardinality(new.accepted_template_ids) then
    raise exception 'submitted swipe layout is incomplete'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke all on function private.validate_swipe_week_draft()
from public, anon, authenticated, service_role;
