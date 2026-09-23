begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

create temporary table phase_16_tap_results (
  sequence bigint generated always as identity primary key,
  result text not null
);
grant insert, select on phase_16_tap_results to authenticated, service_role;
grant usage, select on sequence phase_16_tap_results_sequence_seq
to authenticated, service_role;

insert into phase_16_tap_results (result) select has_table('private', 'pioneer_access_codes', 'raw-code metadata stays private');
insert into phase_16_tap_results (result) select has_table('private', 'pioneer_access_attempts', 'abuse and idempotency ledger stays private');
insert into phase_16_tap_results (result) select has_table('public', 'pioneer_access_redemptions', 'owner-readable redemption exists');
insert into phase_16_tap_results (result) select ok(
  (select relrowsecurity and relforcerowsecurity from pg_class where oid = 'public.pioneer_access_redemptions'::regclass),
  'redemptions force RLS'
);
insert into phase_16_tap_results (result) select ok(
  not has_table_privilege('anon', 'public.pioneer_access_redemptions', 'select'),
  'anonymous users cannot inspect redemptions'
);
insert into phase_16_tap_results (result) select ok(
  not has_table_privilege('authenticated', 'private.pioneer_access_codes', 'select'),
  'athletes cannot inspect code digests or lifecycle metadata'
);
insert into phase_16_tap_results (result) select ok(
  not has_table_privilege('authenticated', 'private.pioneer_access_attempts', 'select'),
  'athletes cannot inspect another athlete attempt ledger'
);
insert into phase_16_tap_results (result) select ok(
  not has_column_privilege('authenticated', 'public.pioneer_access_redemptions', 'athlete_id', 'select'),
  'opaque ownership is not in the public table grant'
);
insert into phase_16_tap_results (result) select ok(
  not has_function_privilege(
    'authenticated',
    'public.redeem_pioneer_access_code(uuid,text,uuid,text)',
    'execute'
  ),
  'mobile users cannot bypass backend redemption validation'
);
insert into phase_16_tap_results (result) select ok(
  has_function_privilege(
    'service_role',
    'public.redeem_pioneer_access_code(uuid,text,uuid,text)',
    'execute'
  ),
  'trusted backend can call the single redemption transaction'
);

insert into auth.users(id) values
  ('a1600000-0000-0000-0000-000000000001'),
  ('b1600000-0000-0000-0000-000000000001'),
  ('c1600000-0000-0000-0000-000000000001');

select set_config(
  'start23.phase16_athlete_a',
  (select athlete_id::text from private.athlete_identity_map where auth_user_id = 'a1600000-0000-0000-0000-000000000001'),
  true
);
select set_config(
  'start23.phase16_athlete_b',
  (select athlete_id::text from private.athlete_identity_map where auth_user_id = 'b1600000-0000-0000-0000-000000000001'),
  true
);
select set_config(
  'start23.phase16_athlete_c',
  (select athlete_id::text from private.athlete_identity_map where auth_user_id = 'c1600000-0000-0000-0000-000000000001'),
  true
);

insert into private.pioneer_access_codes (
  code_digest, intended_athlete_id, expires_at, revoked_at, created_at
) values
  (encode(digest('VALID-A1', 'sha256'), 'hex'), null, statement_timestamp() + interval '1 day', null, statement_timestamp()),
  (encode(digest('VALID-B1', 'sha256'), 'hex'), null, statement_timestamp() + interval '1 day', null, statement_timestamp()),
  (encode(digest('EXPIRED1', 'sha256'), 'hex'), null, statement_timestamp() - interval '1 day', null, statement_timestamp() - interval '2 days'),
  (encode(digest('REVOKED1', 'sha256'), 'hex'), null, statement_timestamp() + interval '1 day', statement_timestamp(), statement_timestamp()),
  (
    encode(digest('BOUND-A1', 'sha256'), 'hex'),
    current_setting('start23.phase16_athlete_a')::uuid,
    statement_timestamp() + interval '1 day',
    null,
    statement_timestamp()
  );

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_a')::uuid,
    encode(digest('VALID-A1', 'sha256'), 'hex'),
    '16000000-0000-0000-0000-000000000001',
    encode(digest('request-valid-a', 'sha256'), 'hex')
  ) ->> 'status',
  'success',
  'valid code succeeds'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_a')::uuid,
    encode(digest('VALID-A1', 'sha256'), 'hex'),
    '16000000-0000-0000-0000-000000000001',
    encode(digest('request-valid-a', 'sha256'), 'hex')
  ) ->> 'status',
  'success',
  'exact retry is idempotent'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_a')::uuid,
    encode(digest('EXPIRED1', 'sha256'), 'hex'),
    '16000000-0000-0000-0000-000000000001',
    encode(digest('different-request', 'sha256'), 'hex')
  ) ->> 'status',
  'idempotency_conflict',
  'same idempotency key with different payload conflicts'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('MISSING1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('invalid-request', 'sha256'), 'hex')
  ) ->> 'status',
  'invalid',
  'invalid code fails'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('EXPIRED1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('expired-request', 'sha256'), 'hex')
  ) ->> 'status',
  'expired',
  'expired code fails'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('REVOKED1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('revoked-request', 'sha256'), 'hex')
  ) ->> 'status',
  'revoked',
  'revoked code fails'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('BOUND-A1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('bound-request', 'sha256'), 'hex')
  ) ->> 'status',
  'unauthorized',
  'athlete-bound code rejects another athlete'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('VALID-A1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('reuse-request', 'sha256'), 'hex')
  ) ->> 'status',
  'reused',
  'successful code cannot be reused by another athlete'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_b')::uuid,
    encode(digest('VALID-B1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('request-valid-b', 'sha256'), 'hex')
  ) ->> 'status',
  'success',
  'second athlete can redeem a distinct valid code'
);
insert into phase_16_tap_results (result) select is(
  public.redeem_pioneer_access_code(
    current_setting('start23.phase16_athlete_c')::uuid,
    encode(digest('ANOTHER1', 'sha256'), 'hex'),
    gen_random_uuid(),
    encode(digest('rate-limited-request', 'sha256'), 'hex')
  ) ->> 'status',
  'rate_limited',
  'sixth rejected attempt inside fifteen minutes is rate limited'
);

select set_config('request.jwt.claims', '{"sub":"a1600000-0000-0000-0000-000000000001","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'a1600000-0000-0000-0000-000000000001';
set local role authenticated;
insert into phase_16_tap_results (result) select is(
  (select count(*) from public.pioneer_access_redemptions),
  1::bigint,
  'athlete A sees only athlete A redemption through RLS'
);
reset role;

select set_config('request.jwt.claims', '{"sub":"b1600000-0000-0000-0000-000000000001","role":"authenticated"}', true);
set local request.jwt.claim.sub = 'b1600000-0000-0000-0000-000000000001';
set local role authenticated;
insert into phase_16_tap_results (result) select is(
  (select count(*) from public.pioneer_access_redemptions),
  1::bigint,
  'athlete B sees only athlete B redemption through RLS'
);
reset role;

select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;
insert into phase_16_tap_results (result)
select is(
  (
    select count(*)
    from private.pioneer_access_attempts
    where athlete_id in (
      current_setting('start23.phase16_athlete_a')::uuid,
      current_setting('start23.phase16_athlete_b')::uuid,
      current_setting('start23.phase16_athlete_c')::uuid
    )
  ),
  8::bigint,
  'safe retry does not duplicate the attempt ledger'
);
reset role;

insert into phase_16_tap_results (result)
select * from finish();
select result from phase_16_tap_results order by sequence;
rollback;
