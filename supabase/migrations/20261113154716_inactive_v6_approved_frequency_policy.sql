-- Approved policy, inactive planner. No reviewer/operator is enrolled here.
do $$ begin
  if not exists(select 1 from pg_roles where rolname='v6_frequency_registrar') then create role v6_frequency_registrar nologin; end if;
  if not exists(select 1 from pg_roles where rolname='v6_frequency_test_executor') then create role v6_frequency_test_executor nologin; end if;
end $$;
-- Neither role is granted to application roles. TEST_ONLY is never REAL authority.
create table private.frequency_reviewers (
  database_login name primary key,
  reviewer_reference text not null check (btrim(reviewer_reference) <> '' and reviewer_reference !~* 'test_only'),
  designation_reference text not null check (btrim(designation_reference) <> ''),
  enabled boolean not null default false
);
create table private.frequency_preferences (
  athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  revision integer not null check (revision > 0),
  operation_id uuid not null,
  preferences jsonb not null,
  confirmed_at timestamptz,
  recorded_at timestamptz not null default clock_timestamp(),
  confirmation_actor uuid references private.athlete_identity_map(athlete_id),
  reconfirm_sports text[] not null default '{}',
  change_reference text not null,
  primary key (athlete_id, revision), unique (athlete_id, operation_id),
  check (confirmation_actor = athlete_id),
  check ((confirmation_actor is null) = (confirmed_at is null)),
  check (reconfirm_sports <@ array['run','bike','swim'])
);
create table private.frequency_decisions (
  id uuid primary key,
  athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  sport text not null check (sport in ('run','bike','swim')),
  week_start date not null check (extract(isodow from week_start) = 1),
  timezone text not null,
  maximum integer not null check (maximum between 0 and 24),
  policy_version text not null check (policy_version = 'joren-v6-real-athlete-frequency-policy-1'),
  reviewer_reference text not null check (btrim(reviewer_reference) <> '' and reviewer_reference !~* 'test_only'),
  operator_reference text not null,
  designation_reference text not null check (btrim(designation_reference) <> ''),
  evidence jsonb not null,
  evidence_context jsonb not null,
  reviewed_at timestamptz not null,
  decided_at timestamptz not null,
  recorded_at timestamptz not null default clock_timestamp(),
  expires_at timestamptz not null,
  revision integer not null check (revision > 0),
  status text not null check (status in ('authorized','suspended','revoked')),
  predecessor_id uuid references private.frequency_decisions(id),
  lifecycle_reference text not null check (btrim(lifecycle_reference) <> ''),
  registration_request jsonb not null,
  unique (athlete_id, sport, week_start, revision),
  check (reviewed_at <= decided_at and decided_at <= recorded_at),
  check (status <> 'authorized' or expires_at > decided_at)
);
create index frequency_decisions_owner_week on private.frequency_decisions(athlete_id, week_start, sport, revision desc);

do $$
declare t text;
begin
  foreach t in array array['frequency_reviewers','frequency_preferences','frequency_decisions'] loop
    execute format('alter table private.%I enable row level security', t);
    execute format('alter table private.%I force row level security', t);
    execute format('revoke all on private.%I from public, anon, authenticated, service_role', t);
  end loop;
  foreach t in array array['frequency_preferences','frequency_decisions'] loop
    execute format('create trigger frequency_immutable before update or delete on private.%I '
      'for each row execute function private.realized_v2_immutable()', t);
  end loop;
end $$;

create function private.lock_frequency(p_owner uuid) returns void
language sql volatile security definer set search_path = '' as $$
  select pg_advisory_xact_lock(hashtextextended('v6-frequency:' || p_owner::text, 0));
$$;

create function private.frequency_preference(p_owner uuid) returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce((select jsonb_build_object('revision', p.revision, 'operation_id', p.operation_id,
    'preferences', p.preferences, 'confirmed_at', p.confirmed_at, 'recorded_at', p.recorded_at,
    'reconfirmation_required', p.reconfirm_sports)
    from private.frequency_preferences p where p.athlete_id = p_owner order by revision desc limit 1),
    jsonb_build_object('revision',0,'operation_id',null,'preferences',
      jsonb_build_object('run',null,'bike',null,'swim',null),'confirmed_at',null,
      'recorded_at',null,'reconfirmation_required','[]'::jsonb));
$$;

create function public.get_frequency_preferences() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare owner uuid := private.current_athlete_id();
begin
  if owner is null then raise exception 'authentication required' using errcode = '42501'; end if;
  return private.frequency_preference(owner);
end $$;

create function public.save_frequency_preferences(p_expected_revision integer, p_operation_id uuid, p_preferences jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare owner uuid := private.current_athlete_id(); old private.frequency_preferences; current_revision integer; total integer;
begin
  if owner is null then raise exception 'authentication required' using errcode = '42501'; end if;
  perform private.lock_frequency(owner);
  if jsonb_typeof(p_preferences) is distinct from 'object' or
    (select array_agg(k order by k) from jsonb_object_keys(p_preferences) k) is distinct from array['bike','run','swim'] then
    raise exception 'invalid frequency preference' using errcode = '23514';
  end if;
  if exists (select 1 from jsonb_each(p_preferences) e where e.value <> 'null'::jsonb and
    (e.value::text !~ '^(0|[1-9][0-9]*)$' or length(e.value::text) > 2)) then
    raise exception 'invalid frequency preference' using errcode = '23514';
  end if;
  select coalesce(sum(case when value = 'null'::jsonb then 0 else value::text::integer end),0)
    into total from jsonb_each(p_preferences);
  if total > 24 then raise exception 'technical frequency input envelope exceeded' using errcode = '23514'; end if;
  select * into old from private.frequency_preferences where athlete_id = owner and operation_id = p_operation_id;
  if found then
    if old.preferences <> p_preferences or old.revision <> p_expected_revision + 1 or old.change_reference <> 'athlete_confirmation' then
      raise exception 'frequency operation conflict' using errcode = 'PT409';
    end if;
    return jsonb_build_object('revision',old.revision,'operation_id',old.operation_id,'preferences',old.preferences,
      'confirmed_at',old.confirmed_at,'recorded_at',old.recorded_at,'reconfirmation_required',old.reconfirm_sports);
  end if;
  select coalesce(max(revision),0) into current_revision from private.frequency_preferences where athlete_id = owner;
  if current_revision <> p_expected_revision then raise exception 'frequency preference changed' using errcode = 'PT409'; end if;
  insert into private.frequency_preferences(athlete_id,revision,operation_id,preferences,confirmed_at,confirmation_actor,change_reference)
    values(owner,current_revision+1,p_operation_id,p_preferences,clock_timestamp(),owner,'athlete_confirmation');
  return private.frequency_preference(owner);
end $$;

-- Current source evidence is compared by value; no historical data is recalculated.
create function private.frequency_basis(p_owner uuid) returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object('planning_input_fingerprint',md5(private.build_phase_8_5_planning_input_snapshot(m.auth_user_id)::text),
    'restrictions',coalesce((select jsonb_agg(jsonb_build_object('id',r.id,'sport',r.discipline,'status',r.status,
      'cleared_at',r.cleared_at) order by r.id) from public.injury_restrictions r where r.internal_athlete_id=p_owner),'[]'::jsonb))
  from private.athlete_identity_map m where m.athlete_id=p_owner;
$$;

create function private.invalidate_frequency(p_owner uuid, p_sports text[], p_reference text, p_operation uuid default null)
returns void language plpgsql security definer set search_path = '' as $$
declare d private.frequency_decisions; p private.frequency_preferences; op uuid := coalesce(p_operation,gen_random_uuid());
begin
  perform private.lock_frequency(p_owner);
  if exists(select 1 from private.frequency_preferences where athlete_id=p_owner and operation_id=op) then return; end if;
  for d in select distinct on (sport,week_start) * from private.frequency_decisions
    where athlete_id=p_owner and sport=any(p_sports) order by sport,week_start,revision desc loop
    if d.status='authorized' then
      insert into private.frequency_decisions(id,athlete_id,sport,week_start,timezone,maximum,policy_version,
        reviewer_reference,operator_reference,designation_reference,evidence,evidence_context,reviewed_at,decided_at,expires_at,
        revision,status,predecessor_id,lifecycle_reference,registration_request)
      values(gen_random_uuid(),d.athlete_id,d.sport,d.week_start,d.timezone,d.maximum,d.policy_version,
        d.reviewer_reference,'system:invalidation',d.designation_reference,d.evidence,d.evidence_context,d.reviewed_at,clock_timestamp(),d.expires_at,
        d.revision+1,'suspended',d.id,p_reference,jsonb_build_object('invalidation',p_reference));
    end if;
  end loop;
  select * into p from private.frequency_preferences where athlete_id=p_owner order by revision desc limit 1;
  insert into private.frequency_preferences(athlete_id,revision,operation_id,preferences,confirmed_at,confirmation_actor,
    reconfirm_sports,change_reference)
    values(p_owner,coalesce(p.revision,0)+1,op,coalesce(p.preferences,jsonb_build_object('run',null,'bike',null,'swim',null)),
      p.confirmed_at,p.confirmation_actor,
      array(select distinct s from unnest(coalesce(p.reconfirm_sports,'{}') || p_sports) s order by s),p_reference);
end $$;

create function public.report_frequency_interruption(p_operation_id uuid, p_reason text, p_sport text default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare owner uuid := private.current_athlete_id(); ref text;
begin
  if owner is null then raise exception 'authentication required' using errcode='42501'; end if;
  if p_reason not in ('illness','training_interruption','injury') or
    (p_reason='injury' and (p_sport is null or p_sport not in ('run','bike','swim'))) or
    (p_reason<>'injury' and p_sport is not null) then
    raise exception 'invalid interruption report' using errcode='23514';
  end if;
  ref := 'athlete_report:' || p_reason || ':' || coalesce(p_sport,'all');
  perform private.lock_frequency(owner);
  if exists(select 1 from private.frequency_preferences where athlete_id=owner and operation_id=p_operation_id
    and change_reference<>ref) then raise exception 'frequency operation conflict' using errcode='PT409'; end if;
  perform private.invalidate_frequency(owner,case when p_sport is null then array['run','bike','swim'] else array[p_sport] end,ref,p_operation_id);
  return private.frequency_preference(owner);
end $$;

-- Direct SQL login plus separately enrolled designation; service/JWT/user metadata cannot issue a maximum.
create function private.register_frequency_decision(p_expected_revision integer, p_decision jsonb) returns uuid
language plpgsql security definer set search_path = '' as $$
declare reviewer private.frequency_reviewers; prior private.frequency_decisions; owner uuid; v_sport text; week date;
  evidence jsonb; d_id uuid; zone text; st text; decision_time timestamptz; expiration timestamptz;
begin
  select * into reviewer from private.frequency_reviewers where database_login=session_user and enabled;
  if not found or not pg_has_role(session_user,'v6_frequency_registrar','member') then
    raise exception 'designated frequency reviewer required' using errcode='42501';
  end if;
  if jsonb_typeof(p_decision) is distinct from 'object' or p_decision - array[
      'id','athlete_id','sport','week_start','timezone','maximum','policy_version','reviewer_reference',
      'evidence','reviewed_at','decided_at','status','predecessor_id','lifecycle_reference'] <> '{}'::jsonb
    or jsonb_typeof(p_decision->'maximum') is distinct from 'number'
    or p_decision->>'maximum' !~ '^(0|[1-9][0-9]*)$' then
    raise exception 'invalid frequency decision' using errcode='23514';
  end if;
  if p_decision::text ~* 'test_only' or p_decision->>'reviewer_reference' is distinct from reviewer.reviewer_reference
    or p_decision->>'policy_version' is distinct from 'joren-v6-real-athlete-frequency-policy-1' then
    raise exception 'real frequency authority required' using errcode='23514';
  end if;
  owner:=(p_decision->>'athlete_id')::uuid; v_sport:=p_decision->>'sport'; week:=(p_decision->>'week_start')::date;
  zone:=p_decision->>'timezone'; st:=p_decision->>'status'; d_id:=(p_decision->>'id')::uuid;
  perform private.lock_frequency(owner);
  select * into prior from private.frequency_decisions where id=d_id;
  if found then
    if prior.athlete_id<>owner or prior.registration_request<>p_decision or prior.revision<>p_expected_revision+1 then
      raise exception 'frequency decision conflict' using errcode='PT409'; end if;
    return d_id;
  end if;
  select * into prior from private.frequency_decisions where athlete_id=owner and sport=v_sport
    and week_start=week order by revision desc limit 1;
  if coalesce(prior.revision,0)<>p_expected_revision or st not in ('authorized','revoked','suspended') then
    raise exception 'frequency decision changed' using errcode='PT409'; end if;
  if p_decision->>'predecessor_id' is distinct from prior.id::text then
    raise exception 'explicit replacement required' using errcode='PT409'; end if;
  if not exists(select 1 from pg_timezone_names where name=zone) or not exists(
    select 1 from public.athlete_profiles a where a.internal_athlete_id=owner and a.timezone=zone
      and a.timezone_confirmed_at is not null) then
    raise exception 'confirmed frequency timezone required' using errcode='23514'; end if;
  evidence:=p_decision->'evidence';
  if jsonb_typeof(evidence) is distinct from 'object' or exists(select 1 from unnest(array[
    'history_source_reference','history_completeness_reference','current_context_reference','capability_reference',
    'phase_reference','rationale_reference','review_record_reference']) k where coalesce(btrim(evidence->>k),'')=''
      or jsonb_typeof(evidence->k) is distinct from 'string')
    or (evidence->>'period_from')::date > (evidence->>'period_to')::date
    or evidence->>'period_from' is null or evidence->>'period_to' is null then
    raise exception 'individual frequency evidence required' using errcode='23514'; end if;
  decision_time:=(p_decision->>'decided_at')::timestamptz;
  expiration:=((week+7)::timestamp at time zone zone);
  if st='authorized' and (expiration<=clock_timestamp() or decision_time>clock_timestamp()
    or exists(select 1 from private.frequency_preferences where athlete_id=owner and revision=(
      select max(revision) from private.frequency_preferences where athlete_id=owner) and v_sport=any(reconfirm_sports))) then
    raise exception 'current frequency assessment required' using errcode='PT409'; end if;
  insert into private.frequency_decisions(id,athlete_id,sport,week_start,timezone,maximum,policy_version,
    reviewer_reference,operator_reference,designation_reference,evidence,evidence_context,reviewed_at,decided_at,expires_at,revision,status,
    predecessor_id,lifecycle_reference,registration_request)
  values(d_id,owner,v_sport,week,zone,(p_decision->>'maximum')::integer,p_decision->>'policy_version',
    reviewer.reviewer_reference,session_user,reviewer.designation_reference,evidence,private.frequency_basis(owner),(p_decision->>'reviewed_at')::timestamptz,
    decision_time,expiration,p_expected_revision+1,st,prior.id,p_decision->>'lifecycle_reference',p_decision);
  return d_id;
end $$;

create function private.frequency_context(p_owner uuid, p_week date, p_timezone text) returns jsonb
language sql volatile security definer set search_path = '' as $$
  select jsonb_build_object('policy_version','joren-v6-real-athlete-frequency-policy-1',
    'athlete_id',p_owner,'week_start',p_week,'timezone',p_timezone,
    'preference',private.frequency_preference(p_owner),'basis',private.frequency_basis(p_owner),
    'decisions',coalesce((select jsonb_agg((to_jsonb(d)-'registration_request') || jsonb_build_object('unexpired',d.expires_at>clock_timestamp(),'reviewer_authorized',exists(select 1 from private.frequency_reviewers r where r.enabled and r.database_login::text=d.operator_reference and r.reviewer_reference=d.reviewer_reference and pg_has_role(r.database_login,'v6_frequency_registrar','member'))) order by sport) from (
      select distinct on (sport) * from private.frequency_decisions where athlete_id=p_owner and week_start=p_week
      order by sport,revision desc) d),'[]'::jsonb),
    'retained_counts',coalesce((select jsonb_object_agg(discipline,n) from (
      select w.discipline,count(distinct w.id) n from private.v6_revision_workouts(
        (select auth_user_id from private.athlete_identity_map where athlete_id=p_owner)) w
      join public.plan_revisions r on r.id=w.revision_id join public.weekly_plans p on p.id=r.plan_id
      where p.internal_athlete_id=p_owner and p.week_start=p_week and r.revision_number=p.active_revision
      group by w.discipline) c),'{}'::jsonb),
    'unmatched_activities',coalesce((select jsonb_agg(a.id order by a.id) from public.activities a
      where a.internal_athlete_id=p_owner and (a.started_at at time zone p_timezone)::date between p_week and p_week+6
        and (a.planned_workout_id is null or not private.v6_active_workout_member(a.athlete_id,a.planned_workout_id))),'[]'::jsonb));
$$;

create function public.get_v6_frequency_context(p_athlete_id uuid, p_week_start date, p_timezone text) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'trusted backend required' using errcode='42501'; end if;
  if not exists(select 1 from public.athlete_profiles where internal_athlete_id=p_athlete_id and timezone=p_timezone
    and timezone_confirmed_at is not null) or extract(isodow from p_week_start)<>1 then
    raise exception 'frequency scope unavailable' using errcode='PT409'; end if;
  return private.frequency_context(p_athlete_id,p_week_start,p_timezone);
end $$;

-- A decision's continued validity is always checked with wall-clock time, including a transaction that waited on a lock.
create function private.assert_frequency_context(p_context jsonb) returns void
language plpgsql security definer set search_path = '' as $$
declare current_context jsonb; owner uuid := (p_context->>'athlete_id')::uuid;
begin
  if owner is null then raise exception 'frequency context required' using errcode='PT409'; end if;
  perform private.lock_frequency(owner);
  current_context:=private.frequency_context(owner,(p_context->>'week_start')::date,p_context->>'timezone');
  if (current_context-'retained_counts') is distinct from (p_context-'retained_counts') then
    raise exception 'frequency context changed; review a new proposal' using errcode='PT409'; end if;
end $$;

-- Only explicitly permissioned synthetic harnesses may persist historical TEST_ONLY controls.
create function private.frequency_test_caller() returns boolean
language sql stable security definer set search_path = '' as $$
  select pg_has_role(coalesce(nullif(current_setting('role',true),'none'),session_user::text),
    'v6_frequency_test_executor','member');
$$;

create function private.guard_frequency_snapshot() returns trigger
language plpgsql security definer set search_path = '' as $$
declare ctx jsonb; f jsonb; d jsonb; sport text; n integer; cap integer; retained integer; pref jsonb; valid boolean;
begin
  ctx:=new.payload #> '{v6_frozen_snapshot,controls,frequency_policy_context}';
  if jsonb_typeof(ctx)='string' then ctx:=(ctx#>>'{}')::jsonb; end if;
  if ctx is null or ctx='null'::jsonb then
    if private.frequency_test_caller() then return new; end if;
    raise exception 'frequency context required' using errcode='PT409';
  end if;
  if ctx->>'athlete_id' is distinct from new.internal_athlete_id::text
    or ctx->>'week_start' is distinct from new.payload->>'week_start'
    or ctx->>'timezone' is distinct from new.payload->>'timezone' then
    raise exception 'frequency scope mismatch' using errcode='PT409'; end if;
  perform private.assert_frequency_context(ctx);
  for sport in select unnest(array['run','bike','swim']) loop
    select count(*) into n from jsonb_array_elements(new.payload->'workouts') w where w->>'discipline'=sport;
    retained:=coalesce((private.frequency_context(new.internal_athlete_id,(ctx->>'week_start')::date,ctx->>'timezone') #>> array['retained_counts',sport])::integer,0);
    pref:=ctx #> array['preference','preferences',sport];
    select value into d from jsonb_array_elements(ctx->'decisions') where value->>'sport'=sport;
    valid:=d is not null and d->>'status'='authorized' and d->>'reviewer_authorized'='true' and d->>'timezone'=ctx->>'timezone'
      and d->'evidence_context'=ctx->'basis' and d->>'policy_version'=ctx->>'policy_version'
      and (d->>'expires_at')::timestamptz>clock_timestamp()
      and not (ctx #> '{preference,reconfirmation_required}' ? sport);
    cap:=case when valid then (d->>'maximum')::integer else greatest(1,retained) end;
    if valid and retained>cap then
      raise exception 'retained frequency requires assessment' using errcode='PT409'; end if;
    if jsonb_array_length(ctx->'unmatched_activities')>0 or (pref='0'::jsonb and not valid) then cap:=least(cap,retained); end if;
    if n>cap or (pref='0'::jsonb and n>retained) then
      raise exception 'frequency week requires assessment' using errcode='PT409'; end if;
    -- The submitted numerical control must agree with current separate authority.
    select value into f from jsonb_array_elements(new.payload #> '{v6_frozen_snapshot,controls,session_frequency}')
      where value->>'sport'=sport;
    if f is not null and ((f->>'maximum')::integer>cap or f->>'reference' ~* 'test_only') then
      raise exception 'real frequency authority required' using errcode='PT409'; end if;
  end loop;
  return new;
end $$;
create trigger v6_frequency_snapshot_guard before insert on private.v6_plan_snapshots
  for each row execute function private.guard_frequency_snapshot();

create function private.guard_frequency_approval() returns trigger
language plpgsql security definer set search_path = '' as $$
declare ctx jsonb; payload jsonb;
begin
  if old.state='pending_approval' and new.state='active' then
    select s.payload into payload from private.v6_plan_snapshots s where revision_id=new.id;
    if found then
      ctx:=payload #> '{v6_frozen_snapshot,controls,frequency_policy_context}';
      if jsonb_typeof(ctx)='string' then ctx:=(ctx#>>'{}')::jsonb; end if;
      if ctx is null or ctx='null'::jsonb then
        if private.frequency_test_caller() then return new; end if;
        raise exception 'frequency context required' using errcode='PT409';
      end if;
      perform private.assert_frequency_context(ctx);
    end if;
  end if;
  return new;
end $$;
create trigger frequency_approval_guard before update of state on public.plan_revisions
  for each row execute function private.guard_frequency_approval();

-- Relevance is explicit; no missed-day threshold, diagnosis or automatic clearance.
create function private.frequency_checkin_invalidation() returns trigger
language plpgsql security definer set search_path = '' as $$
declare sports text[];
begin
  if tg_op='UPDATE' and old.payload=new.payload then return new; end if;
  if new.payload->'missed_workout_reasons' ?| array['illness','injury'] then
    sports:=array['run','bike','swim'];
  else
    select array_agg(value->>'discipline') into sports from jsonb_array_elements(new.payload->'restrictions')
      where value->>'status'<>'none';
  end if;
  if cardinality(sports)>0 then
    perform private.invalidate_frequency(new.internal_athlete_id,sports,'checkin_context:' || new.id::text);
  end if;
  return new;
end $$;
create trigger frequency_checkin_invalidation after insert or update of payload on public.weekly_checkin_contexts
  for each row execute function private.frequency_checkin_invalidation();

-- Draft metadata is private; the public draft never returns authorization records.
create table private.frequency_draft_contexts (
  draft_id uuid primary key references public.swipe_week_drafts(id) on delete cascade,
  athlete_id uuid not null references private.athlete_identity_map(athlete_id) on delete cascade,
  context jsonb not null
);
alter table private.frequency_draft_contexts enable row level security;
alter table private.frequency_draft_contexts force row level security;
revoke all on private.frequency_draft_contexts from public,anon,authenticated,service_role;
create trigger frequency_draft_immutable before update or delete on private.frequency_draft_contexts
  for each row execute function private.realized_v2_immutable();

create function private.guard_frequency_draft() returns trigger
language plpgsql security definer set search_path = '' as $$
declare ctx jsonb; saved jsonb;
begin
  if new.ruleset_version<>'joren-v6-automatic-selection-1' then return new; end if;
  if tg_op='UPDATE' and new.state='cancelled' then return new; end if;
  ctx:=nullif(current_setting('start23.frequency_context',true),'')::jsonb;
  if ctx is null then
    if private.frequency_test_caller() then return new; end if;
    raise exception 'frequency context required' using errcode='PT409';
  end if;
  if ctx->>'athlete_id' is distinct from new.internal_athlete_id::text
    or ctx->>'week_start' is distinct from new.week_start::text or ctx->>'timezone' is distinct from new.timezone then
    raise exception 'frequency scope mismatch' using errcode='PT409'; end if;
  perform private.assert_frequency_context(ctx);
  select context into saved from private.frequency_draft_contexts where draft_id=new.id;
  if found and (saved-'retained_counts') is distinct from (ctx-'retained_counts') then
    raise exception 'frequency draft changed' using errcode='PT409'; end if;
  if tg_op='INSERT' then
    insert into private.frequency_draft_contexts values(new.id,new.internal_athlete_id,ctx);
  end if;
  return new;
end $$;
-- AFTER permits the companion FK and runs after the existing draft custody/CAS checks.
create trigger v6_frequency_draft_guard after insert or update on public.swipe_week_drafts
  for each row execute function private.guard_frequency_draft();

create function public.create_v6_frequency_swipe_draft(p_athlete_id uuid,p_payload jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'trusted backend required' using errcode='42501'; end if;
  perform set_config('start23.frequency_context',(p_payload->'v6_frequency_context')::text,true);
  return public.create_swipe_week_draft_v2(p_athlete_id,p_payload);
end $$;
create function public.update_v6_frequency_swipe_draft(p_athlete_id uuid,p_draft_id uuid,p_expected_revision integer,p_payload jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare d public.swipe_week_drafts;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'trusted backend required' using errcode='42501'; end if;
  select * into d from public.swipe_week_drafts where id=p_draft_id and athlete_id=p_athlete_id for update;
  if not found then raise exception 'draft not found' using errcode='P0002'; end if;
  if d.state='submitted' and p_payload->>'state'='submitted' and d.plan_id::text=p_payload->>'plan_id'
    and d.proposal_id::text=p_payload->>'proposal_id' then return to_jsonb(d)-'athlete_id'; end if;
  perform set_config('start23.frequency_context',(p_payload->'v6_frequency_context')::text,true);
  return public.update_swipe_week_draft(p_athlete_id,p_draft_id,p_expected_revision,p_payload);
end $$;

-- One transaction owns proposal persistence and the existing submitted locator.
-- A committed retry reads that locator before any current-authority check.
create function public.create_v6_frequency_swipe_proposal(p_athlete_id uuid,p_payload jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare d public.swipe_week_drafts; r public.plan_revisions; result jsonb; placements jsonb;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'trusted backend required' using errcode='42501'; end if;
  select * into d from public.swipe_week_drafts where id=(p_payload#>>'{v6_swipe_draft,id}')::uuid
    and athlete_id=p_athlete_id for update;
  if not found then raise exception 'draft not found' using errcode='P0002'; end if;
  if d.state='submitted' then
    select revision.* into r from public.change_proposals p join public.plan_revisions revision
      on revision.id=p.target_plan_revision_id and revision.athlete_id=p.athlete_id
      where p.id=d.proposal_id and p.athlete_id=p_athlete_id and revision.plan_id=d.plan_id;
    if not found then raise exception 'draft receipt unavailable' using errcode='PT409'; end if;
    return jsonb_build_object('plan_id',d.plan_id,'proposal_id',d.proposal_id,'revision',r.revision_number);
  end if;
  if d.state<>'placement' or d.revision is distinct from (p_payload#>>'{v6_swipe_draft,revision}')::bigint
    or d.week_start::text is distinct from p_payload->>'week_start' or d.timezone is distinct from p_payload->>'timezone'
    or d.initial_plan_request_id::text is distinct from p_payload->>'initial_plan_request_id'
    or cardinality(d.accepted_template_ids)<>d.target_workout_count
    or cardinality(d.accepted_occurrence_ids)<>jsonb_array_length(p_payload->'workouts')
    or (select coalesce(jsonb_object_agg(x.occurrence::text,x.template::text),'{}'::jsonb)
      from unnest(d.accepted_occurrence_ids,d.accepted_template_ids) x(occurrence,template))
      is distinct from (select coalesce(jsonb_object_agg(w->>'occurrence_id',w->>'template_id'),'{}'::jsonb)
        from jsonb_array_elements(p_payload->'workouts') w) then
    raise exception 'swipe submission changed' using errcode='PT409';
  end if;
  result:=public.create_v6_weekly_plan_proposal(p_athlete_id,p_payload);
  select coalesce(jsonb_object_agg(w->>'occurrence_id',w->>'scheduled_date'),'{}'::jsonb)
    into placements from jsonb_array_elements(p_payload->'workouts') w;
  perform set_config('start23.frequency_context',coalesce(p_payload#>>'{v6_frozen_snapshot,controls,frequency_policy_context}',''),true);
  perform public.update_swipe_week_draft(p_athlete_id,d.id,d.revision,
    to_jsonb(d) || jsonb_build_object('state','submitted','current_template_id',null,
      'placements',placements,'plan_id',result->>'plan_id','proposal_id',result->>'proposal_id'));
  return result;
end $$;

-- These mutations invalidate review grounds. The frequency lock is always last;
-- invalidation/registration never lock a plan, proposal, check-in or source row.
create function private.frequency_source_invalidation() returns trigger
language plpgsql security definer set search_path = '' as $$
declare owner uuid; sports text[] := array['run','bike','swim'];
begin
  owner:=coalesce(new.internal_athlete_id,old.internal_athlete_id);
  if not exists(select 1 from private.athlete_identity_map m join auth.users u on u.id=m.auth_user_id where m.athlete_id=owner) then
    return coalesce(new,old);
  end if;
  if tg_table_name='injury_restrictions' then sports:=array[coalesce(new.discipline,old.discipline)]; end if;
  if exists(select 1 from private.frequency_decisions d where d.athlete_id=owner and d.status='authorized') then
    if exists(select 1 from private.frequency_decisions d where d.athlete_id=owner and d.status='authorized'
      and d.evidence_context is distinct from private.frequency_basis(owner)) then
      perform private.invalidate_frequency(owner,sports,tg_table_name || ':' || coalesce(to_jsonb(new)->>'id',to_jsonb(old)->>'id',owner::text));
    end if;
  elsif exists(select 1 from private.frequency_preferences where athlete_id=owner) and (
    tg_table_name in ('goals','injury_restrictions') or
    (tg_table_name='zone_profile_versions' and (to_jsonb(new)->>'status'='active' or to_jsonb(old)->>'status'='active')) or
    (tg_table_name='athlete_profiles' and
      (to_jsonb(new)->'timezone',to_jsonb(new)->'timezone_confirmed_at',to_jsonb(new)->'heart_rate_monitor_confirmed_at')
      is distinct from
      (to_jsonb(old)->'timezone',to_jsonb(old)->'timezone_confirmed_at',to_jsonb(old)->'heart_rate_monitor_confirmed_at'))
  ) then
    perform private.invalidate_frequency(owner,sports,tg_table_name || ':' || coalesce(to_jsonb(new)->>'id',to_jsonb(old)->>'id',owner::text));
  end if;
  return coalesce(new,old);
end $$;
create trigger frequency_restriction_invalidation after insert or update or delete on public.injury_restrictions
  for each row execute function private.frequency_source_invalidation();
create trigger frequency_goal_invalidation after insert or update or delete on public.goals
  for each row execute function private.frequency_source_invalidation();
create trigger frequency_zone_invalidation after insert or update or delete on public.zone_profile_versions
  for each row execute function private.frequency_source_invalidation();
create trigger frequency_profile_invalidation after update on public.athlete_profiles
  for each row execute function private.frequency_source_invalidation();

create function private.frequency_reviewer_invalidation() returns trigger
language plpgsql security definer set search_path = '' as $$
declare owner uuid;
begin
  if tg_op='UPDATE' and new is not distinct from old then return new; end if;
  for owner in select distinct athlete_id from private.frequency_decisions
    where operator_reference=old.database_login::text order by athlete_id loop
    perform private.invalidate_frequency(owner,array['run','bike','swim'],
      'reviewer_designation_changed:' || old.database_login::text);
  end loop;
  return coalesce(new,old);
end $$;
create trigger frequency_reviewer_invalidation after update or delete on private.frequency_reviewers
  for each row execute function private.frequency_reviewer_invalidation();

-- Public presentation is restricted to P and actual counts; immutable receipts
-- continue to use the original snapshot, not today's preference.
alter function private.v6_public_plan(uuid,uuid,integer) rename to v6_public_plan_without_frequency;
create function private.v6_public_plan(p_athlete_id uuid,p_plan_id uuid,p_revision integer) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare result jsonb; ctx jsonb;
begin
  result:=private.v6_public_plan_without_frequency(p_athlete_id,p_plan_id,p_revision);
  select payload #> '{v6_frozen_snapshot,controls,frequency_policy_context}' into ctx from private.v6_plan_snapshots
    where revision_id=(result->>'revision_id')::uuid and athlete_id=p_athlete_id;
  if jsonb_typeof(ctx)='string' then ctx:=(ctx#>>'{}')::jsonb; end if;
  if ctx is not null and ctx<>'null'::jsonb then
    result:=result || jsonb_build_object('frequency_summary',(select jsonb_agg(jsonb_build_object(
      'sport',s,'requested',ctx #> array['preference','preferences',s],
      'proposed',(select count(*) from jsonb_array_elements(result->'workouts') w where w->>'discipline'=s)) order by s)
      from unnest(array['run','bike','swim']) s));
  end if;
  return result;
end $$;

-- All helper procedures default to no application execute permission.
create function public.get_v6_frequency_swipe_receipt(p_draft_id uuid) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare d public.swipe_week_drafts; r public.plan_revisions; result jsonb; owner uuid := auth.uid();
begin
  if owner is null then raise exception 'authentication required' using errcode='42501'; end if;
  select * into d from public.swipe_week_drafts where id=p_draft_id and athlete_id=owner;
  if not found then raise exception 'draft not found' using errcode='P0002'; end if;
  if d.state<>'submitted' then return null; end if;
  select revision.* into r from public.change_proposals p join public.plan_revisions revision
    on revision.id=p.target_plan_revision_id and revision.athlete_id=p.athlete_id
    where p.id=d.proposal_id and p.athlete_id=owner and revision.plan_id=d.plan_id;
  if not found then raise exception 'draft receipt unavailable' using errcode='PT409'; end if;
  result:=private.v6_public_plan(owner,r.plan_id,r.revision_number);
  return jsonb_build_object('plan',private.v6_mobile_plan(owner,result),'proposal',result->'proposal');
end $$;
revoke all on function public.get_v6_frequency_swipe_receipt(uuid) from public,anon,authenticated,service_role;
grant execute on function public.get_v6_frequency_swipe_receipt(uuid) to authenticated;

do $$
declare f record;
begin
  for f in select p.oid::regprocedure signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='private' and (p.proname like '%frequency%' or p.proname='register_frequency_decision') loop
    execute format('revoke all on function %s from public, anon, authenticated, service_role',f.signature);
  end loop;
end $$;
revoke all on function public.get_frequency_preferences() from public, anon, authenticated, service_role;
revoke all on function public.save_frequency_preferences(integer,uuid,jsonb) from public, anon, authenticated, service_role;
revoke all on function public.report_frequency_interruption(uuid,text,text) from public, anon, authenticated, service_role;
revoke all on function public.get_v6_frequency_context(uuid,date,text) from public, anon, authenticated, service_role;
grant execute on function public.get_frequency_preferences(), public.save_frequency_preferences(integer,uuid,jsonb),
  public.report_frequency_interruption(uuid,text,text) to authenticated;
grant execute on function public.get_v6_frequency_context(uuid,date,text) to service_role;
revoke all on function public.create_v6_frequency_swipe_draft(uuid,jsonb),
  public.update_v6_frequency_swipe_draft(uuid,uuid,integer,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.create_v6_frequency_swipe_draft(uuid,jsonb),
  public.update_v6_frequency_swipe_draft(uuid,uuid,integer,jsonb) to service_role;
revoke all on function public.create_v6_frequency_swipe_proposal(uuid,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.create_v6_frequency_swipe_proposal(uuid,jsonb) to service_role;
revoke all on function private.v6_public_plan(uuid,uuid,integer) from public,anon,authenticated,service_role;
grant usage on schema private to v6_frequency_registrar;
grant execute on function private.register_frequency_decision(integer,jsonb) to v6_frequency_registrar;
notify pgrst,'reload schema';
