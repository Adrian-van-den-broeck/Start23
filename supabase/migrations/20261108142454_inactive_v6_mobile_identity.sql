-- Inactive mobile projection. Existing V6/public RPC contracts remain unchanged.
-- id is logical; physical_workout_id is the exact immutable activity FK.
create function private.v6_mobile_workout(p_owner uuid, p_workout jsonb, p_revision uuid default null)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce((
    select jsonb_set(p_workout, '{id}', to_jsonb(m.occurrence_id))
      || jsonb_build_object('physical_workout_id', m.planned_workout_id)
    from private.v6_occurrence_snapshots m
    where m.athlete_id = p_owner
      and ((p_revision is null and m.planned_workout_id = (p_workout ->> 'id')::uuid)
        or (m.revision_id = p_revision and m.occurrence_id = (p_workout ->> 'id')::uuid))
  ), p_workout);
$$;
revoke all on function private.v6_mobile_workout(uuid, jsonb, uuid) from public, anon, authenticated, service_role;

create function private.v6_mobile_plan(p_owner uuid, p_plan jsonb)
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_set(p_plan, '{workouts}', (
    select coalesce(jsonb_agg(private.v6_mobile_workout(p_owner, w.value,
      (p_plan ->> 'revision_id')::uuid) order by w.ordinality), '[]'::jsonb)
    from jsonb_array_elements(p_plan -> 'workouts') with ordinality w(value, ordinality)
  ));
$$;
revoke all on function private.v6_mobile_plan(uuid, jsonb) from public, anon, authenticated, service_role;

create function public.get_v6_mobile_weekly_plan(p_plan_id uuid, p_revision integer default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if (select auth.uid()) is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  return private.v6_mobile_plan((select auth.uid()),
    private.v6_public_plan((select auth.uid()), p_plan_id, p_revision));
end;
$$;
revoke all on function public.get_v6_mobile_weekly_plan(uuid, integer) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_mobile_weekly_plan(uuid, integer) to authenticated;

-- Existing invoker calendar performs owner/active/range filtering first.
create function public.get_v6_mobile_calendar(p_from_date date, p_to_date date)
returns setof jsonb language sql stable security definer set search_path = '' as $$
  select private.v6_mobile_workout((select auth.uid()), row)
  from public.get_calendar(p_from_date, p_to_date) row
  where (select auth.uid()) is not null;
$$;
revoke all on function public.get_v6_mobile_calendar(date, date) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_mobile_calendar(date, date) to authenticated;

create function public.get_v6_mobile_edit_retry(p_athlete_id uuid, p_operation_key text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_result jsonb;
begin
  -- Existing service-only read validates the role and exact owner key.
  v_result := public.get_v6_edit_retry(p_athlete_id, p_operation_key);
  if v_result is null then return null; end if;
  return jsonb_set(v_result, '{plan}', private.v6_mobile_plan(p_athlete_id, v_result -> 'plan'));
end;
$$;
revoke all on function public.get_v6_mobile_edit_retry(uuid, text) from public, anon, authenticated, service_role;
grant execute on function public.get_v6_mobile_edit_retry(uuid, text) to service_role;
notify pgrst, 'reload schema';
