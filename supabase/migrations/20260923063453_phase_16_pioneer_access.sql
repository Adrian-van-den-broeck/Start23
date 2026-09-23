-- Phase 16 Pioneer beta access.
--
-- Raw access codes are never persisted. Trusted operators provision only a
-- SHA-256 digest in the private schema. The backend redeems that digest through
-- one service-role-only transaction while athletes can read only their own
-- public redemption through RLS.

create table private.pioneer_access_codes (
  id uuid primary key default gen_random_uuid(),
  code_digest text not null unique,
  intended_athlete_id uuid
    references private.athlete_identity_map (athlete_id)
    on delete cascade,
  expires_at timestamptz,
  revoked_at timestamptz,
  redeemed_at timestamptz,
  redeemed_by_athlete_id uuid
    references private.athlete_identity_map (athlete_id)
    on delete set null,
  redemption_id uuid unique,
  created_at timestamptz not null default statement_timestamp(),

  constraint pioneer_access_codes_digest_valid check (
    code_digest ~ '^[0-9a-f]{64}$'
  ),
  constraint pioneer_access_codes_expiry_valid check (
    expires_at is null or expires_at > created_at
  ),
  constraint pioneer_access_codes_redemption_complete check (
    (redeemed_at is null and redeemed_by_athlete_id is null and redemption_id is null)
    or
    (redeemed_at is not null and redeemed_by_athlete_id is not null and redemption_id is not null)
  )
);

create table public.pioneer_access_redemptions (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null unique
    references private.athlete_identity_map (athlete_id)
    on delete cascade,
  program text not null default 'pioneer',
  status text not null default 'active',
  redeemed_at timestamptz not null default statement_timestamp(),

  constraint pioneer_access_redemptions_program_valid check (
    program = 'pioneer'
  ),
  constraint pioneer_access_redemptions_status_valid check (
    status = 'active'
  )
);

alter table private.pioneer_access_codes
  add constraint pioneer_access_codes_redemption_fk
  foreign key (redemption_id)
  references public.pioneer_access_redemptions (id)
  on delete restrict;

create table private.pioneer_access_attempts (
  id uuid primary key default gen_random_uuid(),
  athlete_id uuid not null
    references private.athlete_identity_map (athlete_id)
    on delete cascade,
  idempotency_key uuid not null,
  request_fingerprint text not null,
  code_digest text not null,
  result_status text not null,
  redemption_id uuid
    references public.pioneer_access_redemptions (id)
    on delete set null,
  attempted_at timestamptz not null default statement_timestamp(),

  constraint pioneer_access_attempts_fingerprint_valid check (
    request_fingerprint ~ '^[0-9a-f]{64}$'
  ),
  constraint pioneer_access_attempts_digest_valid check (
    code_digest ~ '^[0-9a-f]{64}$'
  ),
  constraint pioneer_access_attempts_status_valid check (
    result_status in (
      'success', 'invalid', 'expired', 'revoked', 'unauthorized', 'reused',
      'rate_limited'
    )
  ),
  constraint pioneer_access_attempts_success_has_redemption check (
    (result_status = 'success') = (redemption_id is not null)
  ),
  unique (athlete_id, idempotency_key)
);

create index pioneer_access_attempts_rate_limit_idx
on private.pioneer_access_attempts (athlete_id, attempted_at desc)
where result_status <> 'success';

alter table private.pioneer_access_codes enable row level security;
alter table private.pioneer_access_codes force row level security;
alter table private.pioneer_access_attempts enable row level security;
alter table private.pioneer_access_attempts force row level security;
alter table public.pioneer_access_redemptions enable row level security;
alter table public.pioneer_access_redemptions force row level security;

revoke all on table private.pioneer_access_codes
from public, anon, authenticated, service_role;
revoke all on table private.pioneer_access_attempts
from public, anon, authenticated, service_role;
revoke all on table public.pioneer_access_redemptions
from public, anon, authenticated, service_role;

grant select, insert, update on table private.pioneer_access_codes to service_role;
grant select, insert on table private.pioneer_access_attempts to service_role;
grant select (id, program, status, redeemed_at)
on table public.pioneer_access_redemptions to authenticated;
grant select on table public.pioneer_access_redemptions to service_role;

create policy pioneer_access_redemptions_select_own
on public.pioneer_access_redemptions
for select
to authenticated
using (athlete_id = (select private.current_athlete_id()));

create function public.redeem_pioneer_access_code(
  p_athlete_id uuid,
  p_code_digest text,
  p_idempotency_key uuid,
  p_request_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_attempt private.pioneer_access_attempts%rowtype;
  v_code private.pioneer_access_codes%rowtype;
  v_redemption public.pioneer_access_redemptions%rowtype;
  v_status text;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'service role required' using errcode = '42501';
  end if;
  if p_athlete_id is null
     or p_code_digest !~ '^[0-9a-f]{64}$'
     or p_request_fingerprint !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid pioneer redemption input' using errcode = '22023';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_athlete_id::text, 0));
  perform pg_advisory_xact_lock(hashtextextended(p_code_digest, 0));

  select * into v_attempt
  from private.pioneer_access_attempts attempts
  where attempts.athlete_id = p_athlete_id
    and attempts.idempotency_key = p_idempotency_key;

  if found then
    if v_attempt.request_fingerprint <> p_request_fingerprint then
      return jsonb_build_object('status', 'idempotency_conflict');
    end if;
    if v_attempt.result_status = 'success' then
      select * into strict v_redemption
      from public.pioneer_access_redemptions redemptions
      where redemptions.id = v_attempt.redemption_id;
      return jsonb_build_object(
        'status', 'success',
        'redemption', jsonb_build_object(
          'id', v_redemption.id,
          'program', v_redemption.program,
          'status', v_redemption.status,
          'redeemed_at', v_redemption.redeemed_at
        )
      );
    end if;
    return jsonb_build_object('status', v_attempt.result_status);
  end if;

  if (
    select count(*)
    from private.pioneer_access_attempts attempts
    where attempts.athlete_id = p_athlete_id
      and attempts.result_status <> 'success'
      and attempts.attempted_at >= statement_timestamp() - interval '15 minutes'
  ) >= 5 then
    insert into private.pioneer_access_attempts (
      athlete_id, idempotency_key, request_fingerprint, code_digest,
      result_status
    ) values (
      p_athlete_id, p_idempotency_key, p_request_fingerprint, p_code_digest,
      'rate_limited'
    );
    return jsonb_build_object('status', 'rate_limited');
  end if;

  select * into v_code
  from private.pioneer_access_codes codes
  where codes.code_digest = p_code_digest
  for update;

  if not found then
    v_status := 'invalid';
  elsif v_code.revoked_at is not null then
    v_status := 'revoked';
  elsif v_code.expires_at is not null
        and v_code.expires_at <= statement_timestamp() then
    v_status := 'expired';
  elsif v_code.intended_athlete_id is not null
        and v_code.intended_athlete_id <> p_athlete_id then
    v_status := 'unauthorized';
  elsif v_code.redemption_id is not null then
    v_status := 'reused';
  else
    insert into public.pioneer_access_redemptions (athlete_id)
    values (p_athlete_id)
    on conflict (athlete_id) do nothing
    returning * into v_redemption;

    if not found then
      v_status := 'reused';
    else
      update private.pioneer_access_codes
      set redeemed_at = v_redemption.redeemed_at,
          redeemed_by_athlete_id = p_athlete_id,
          redemption_id = v_redemption.id
      where id = v_code.id;
      v_status := 'success';
    end if;
  end if;

  insert into private.pioneer_access_attempts (
    athlete_id, idempotency_key, request_fingerprint, code_digest,
    result_status, redemption_id
  ) values (
    p_athlete_id, p_idempotency_key, p_request_fingerprint, p_code_digest,
    v_status,
    case when v_status = 'success' then v_redemption.id else null end
  );

  if v_status = 'success' then
    return jsonb_build_object(
      'status', 'success',
      'redemption', jsonb_build_object(
        'id', v_redemption.id,
        'program', v_redemption.program,
        'status', v_redemption.status,
        'redeemed_at', v_redemption.redeemed_at
      )
    );
  end if;
  return jsonb_build_object('status', v_status);
end;
$$;

revoke all on function public.redeem_pioneer_access_code(uuid, text, uuid, text)
from public, anon, authenticated, service_role;
grant execute on function public.redeem_pioneer_access_code(uuid, text, uuid, text)
to service_role;
