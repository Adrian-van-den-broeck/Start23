-- R6 runtime remediation: exact retries and key conflicts must be resolved
-- before validating fields that are irrelevant once an immutable activity
-- already exists. New writes still use the unchanged Phase 13 implementation.

alter function public.create_activity_summary(uuid, text, jsonb)
  rename to create_activity_summary_r6_pre_idempotency;

revoke all on function public.create_activity_summary_r6_pre_idempotency(
  uuid, text, jsonb
) from public, anon, authenticated, service_role;

create function public.create_activity_summary(
  p_idempotency_key uuid,
  p_request_fingerprint text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_athlete_id uuid := (select auth.uid());
  v_existing public.activities;
begin
  if v_athlete_id is null then
    raise exception 'authentication required' using errcode = '42501';
  end if;
  if p_request_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid activity fingerprint' using errcode = '23514';
  end if;

  select * into v_existing
  from public.activities activity
  where activity.athlete_id = v_athlete_id
    and activity.idempotency_key = p_idempotency_key;
  if found then
    if v_existing.request_fingerprint <> p_request_fingerprint then
      raise exception 'activity idempotency key reused' using errcode = '40001';
    end if;
    return private.activity_public_json(v_existing.id, v_athlete_id);
  end if;

  return public.create_activity_summary_r6_pre_idempotency(
    p_idempotency_key,
    p_request_fingerprint,
    p_payload
  );
end;
$$;

revoke all on function public.create_activity_summary(uuid, text, jsonb)
from public, anon, authenticated, service_role;
grant execute on function public.create_activity_summary(uuid, text, jsonb)
to authenticated;

comment on function public.create_activity_summary(uuid, text, jsonb) is
  'Creates an owner activity; exact retries and key conflicts resolve before new-write payload validation.';
