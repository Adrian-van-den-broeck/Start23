-- A5: owner-scoped replay and atomic check-in proposal persistence/attachment.
-- Historical values and states are read as persisted, never regenerated.
create function public.get_checkin_plan_proposal(p_checkin_id uuid)
returns jsonb language plpgsql stable security invoker set search_path = '' as $$
declare
  v_checkin jsonb;
  v_plan_id uuid;
  v_revision integer;
  v_plan jsonb;
begin
  -- Existing invoker RPC supplies the same not-found result for foreign IDs.
  v_checkin := public.get_weekly_checkin(p_checkin_id);
  if v_checkin ->> 'plan_proposal_id' is null then
    if v_checkin ->> 'status' = 'open' then return null; end if;
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  select revision.plan_id, revision.revision_number
  into v_plan_id, v_revision
  from public.change_proposals proposal
  join public.plan_revisions revision
    on revision.id = proposal.target_plan_revision_id
   and revision.athlete_id = proposal.athlete_id
  join public.weekly_checkins checkin
    on checkin.id = revision.checkin_id
   and checkin.athlete_id = revision.athlete_id
   and checkin.plan_proposal_id = proposal.id
  where checkin.id = p_checkin_id
    and checkin.athlete_id = (select auth.uid())
    and checkin.status = 'completed'
    and proposal.kind = 'plan_revision';
  if not found then
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  v_plan := public.get_weekly_plan(v_plan_id, v_revision);
  if v_plan #>> '{proposal,id}' is distinct from v_checkin ->> 'plan_proposal_id' then
    raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
  end if;
  return jsonb_build_object('plan', v_plan, 'proposal', v_plan -> 'proposal');
end;
$$;
revoke all on function public.get_checkin_plan_proposal(uuid)
  from public, anon, authenticated, service_role;
grant execute on function public.get_checkin_plan_proposal(uuid) to authenticated;

create or replace function public.create_weekly_plan_proposal_v3(
  p_athlete_id uuid, p_payload jsonb
)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_result jsonb;
  v_checkin_id uuid := nullif(p_payload ->> 'checkin_id', '')::uuid;
  v_checkin public.weekly_checkins%rowtype;
  v_existing_count integer;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if v_checkin_id is not null then
    -- Serialize before creating any plan/revision. Creation plus attachment
    -- commits or rolls back together, including all nested v2 writes.
    select * into v_checkin from public.weekly_checkins
    where id = v_checkin_id and athlete_id = p_athlete_id for update;
    if not found then
      raise exception 'weekly check-in not found' using errcode = 'P0002';
    end if;
    if v_checkin.plan_proposal_id is not null then
      select jsonb_build_object('plan_id', revision.plan_id,
        'revision', revision.revision_number, 'proposal_id', proposal.id)
      into v_result
      from public.change_proposals proposal
      join public.plan_revisions revision
        on revision.id = proposal.target_plan_revision_id
       and revision.athlete_id = proposal.athlete_id
      where proposal.id = v_checkin.plan_proposal_id
        and proposal.athlete_id = p_athlete_id
        and proposal.kind = 'plan_revision'
        and revision.checkin_id = v_checkin_id;
      if v_result is null then
        raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
      end if;
      return v_result;
    end if;
    if v_checkin.status <> 'open' then
      raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
    end if;
    -- Compatibility with a pre-A5 commit between persistence and attachment.
    -- Only an unambiguous owned revision can be recovered; terminal state stays.
    select count(*) into v_existing_count
    from public.plan_revisions revision
    join public.change_proposals proposal on proposal.target_plan_revision_id = revision.id
      and proposal.athlete_id = revision.athlete_id
    where revision.checkin_id = v_checkin_id and revision.athlete_id = p_athlete_id
      and proposal.kind = 'plan_revision';
    if v_existing_count > 1 then
      raise exception 'check-in proposal is not recoverable' using errcode = 'PT409';
    elsif v_existing_count = 1 then
      select jsonb_build_object('plan_id', revision.plan_id,
        'revision', revision.revision_number, 'proposal_id', proposal.id)
      into v_result
      from public.plan_revisions revision
      join public.change_proposals proposal on proposal.target_plan_revision_id = revision.id
        and proposal.athlete_id = revision.athlete_id
      where revision.checkin_id = v_checkin_id and revision.athlete_id = p_athlete_id
      and proposal.kind = 'plan_revision';
      perform public.attach_checkin_plan_proposal(p_athlete_id, v_checkin_id,
        (v_result ->> 'proposal_id')::uuid);
      return v_result;
    end if;
  end if;
  if p_payload ->> 'ruleset_version' <> 'phase-13-joren-ruleset-1'
     or p_payload ->> 'planning_ruleset_version' <>
       'joren-planning-ruleset-2' then
    raise exception 'planning ruleset provenance is invalid'
      using errcode = '23514';
  end if;
  if jsonb_typeof(coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb))
     <> 'array' then
    raise exception 'cross-training choice is invalid' using errcode = '23514';
  end if;
  v_result := public.create_weekly_plan_proposal_v2(p_athlete_id, p_payload);
  perform set_config('start23.critical_write', 'on', true);
  update public.plan_revisions
  set planning_ruleset_version = 'joren-planning-ruleset-2',
      cross_training_opt_ins = array(
        select jsonb_array_elements_text(
          coalesce(p_payload -> 'cross_training_opt_ins', '[]'::jsonb)
        )
      )
  where plan_id = (v_result ->> 'plan_id')::uuid
    and athlete_id = p_athlete_id
    and revision_number = (v_result ->> 'revision')::integer
    and (planning_ruleset_version is null
      or planning_ruleset_version = 'joren-planning-ruleset-2');
  if not found then
    raise exception 'planning revision provenance is invalid'
      using errcode = '23514';
  end if;
  if v_checkin_id is not null then
    perform public.attach_checkin_plan_proposal(p_athlete_id, v_checkin_id,
      (v_result ->> 'proposal_id')::uuid);
  end if;
  return v_result;
end;
$$;
revoke all on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v3(uuid, jsonb)
  to service_role;

