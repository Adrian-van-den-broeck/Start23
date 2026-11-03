-- Freeze the exact evidence used by new pending plans. No approved revision is
-- recalculated, and no public DTO/table gains load or evidence JSON.
create table private.realized_v2_plan_evidence (
  revision_id uuid primary key,
  athlete_id uuid not null,
  internal_athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  week_start date not null,
  policy text not null check (policy = 'weekly-registration-2'),
  evidence jsonb not null check (jsonb_typeof(evidence) = 'array'),
  created_at timestamptz not null default statement_timestamp(),
  foreign key (revision_id, athlete_id) references public.plan_revisions(id, athlete_id) on delete cascade
);
create index realized_v2_plan_evidence_owner_idx on private.realized_v2_plan_evidence(athlete_id);
create index realized_v2_plan_evidence_opaque_idx on private.realized_v2_plan_evidence(internal_athlete_id);
create trigger r3_00_sync_opaque_athlete_owner before insert or update on private.realized_v2_plan_evidence
  for each row execute function private.sync_dual_athlete_owner_keys();
create trigger realized_v2_plan_evidence_immutable before update or delete on private.realized_v2_plan_evidence
  for each row execute function private.realized_v2_immutable();
alter table private.realized_v2_plan_evidence enable row level security;
alter table private.realized_v2_plan_evidence force row level security;
revoke all on private.realized_v2_plan_evidence from public, anon, authenticated, service_role;
grant select, insert on private.realized_v2_plan_evidence to service_role;

create function private.realized_v2_history_evidence(p_athlete_id uuid, p_before_week date)
returns jsonb language sql stable security invoker set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('week_start', row -> 'week_start',
    'weekly_registration', row -> 'weekly_registration') order by row ->> 'week_start'), '[]'::jsonb)
  from public.get_plan_load_history_for_planning_v16(p_athlete_id, p_before_week) row;
$$;
revoke all on function private.realized_v2_history_evidence(uuid, date) from public, anon, authenticated, service_role;

create function public.create_weekly_plan_proposal_v4(p_athlete_id uuid, p_payload jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v_result jsonb; v_revision_id uuid; v_evidence jsonb;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  v_evidence := private.realized_v2_history_evidence(p_athlete_id, (p_payload ->> 'week_start')::date);
  if v_evidence is distinct from p_payload -> 'weekly_registration_evidence' then
    raise exception 'planning input is stale' using errcode = '40001';
  end if;
  v_result := public.create_weekly_plan_proposal_v3(p_athlete_id, p_payload - 'weekly_registration_evidence');
  select id into v_revision_id from public.plan_revisions where plan_id = (v_result ->> 'plan_id')::uuid
    and athlete_id = p_athlete_id and revision_number = (v_result ->> 'revision')::integer;
  if v_revision_id is null then raise exception 'plan revision not found' using errcode = 'P0002'; end if;
  insert into private.realized_v2_plan_evidence(revision_id, athlete_id, week_start, policy, evidence)
    values (v_revision_id, p_athlete_id, (p_payload ->> 'week_start')::date, 'weekly-registration-2', v_evidence)
    on conflict (revision_id) do nothing;
  return v_result;
end;
$$;
revoke all on function public.create_weekly_plan_proposal_v4(uuid, jsonb) from public, anon, authenticated, service_role;
grant execute on function public.create_weekly_plan_proposal_v4(uuid, jsonb) to service_role;

-- Preserve the existing invoker/RLS approval RPC. The trigger also covers
-- alternative transition paths; an already-applied approval retry is unchanged.
create function private.guard_realized_v2_plan_approval() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_evidence private.realized_v2_plan_evidence;
begin
  if old.state = 'pending_approval' and new.state = 'active' then
    select * into v_evidence from private.realized_v2_plan_evidence
      where revision_id = new.id and athlete_id = new.athlete_id;
    if found and v_evidence.evidence is distinct from private.realized_v2_history_evidence(new.athlete_id, v_evidence.week_start) then
      raise exception 'plan proposal is stale' using errcode = '40001';
    end if;
  end if;
  return new;
end;
$$;
create trigger realized_v2_guard_plan_approval before update of state on public.plan_revisions
  for each row execute function private.guard_realized_v2_plan_approval();
revoke all on function private.guard_realized_v2_plan_approval() from public, anon, authenticated, service_role;
