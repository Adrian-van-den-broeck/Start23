begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select no_plan();

select has_table('public', 'provider_connections', 'provider connections exist');
select has_table('public', 'import_runs', 'provider import runs exist');
select has_table('public', 'activity_files', 'private-file metadata exists');
select has_table('private', 'provider_tokens', 'provider tokens are private');
select has_table('private', 'webhook_receipts', 'webhook receipts are private');

select ok(
  not exists (
    select 1 from pg_class
    where oid in (
      'public.provider_connections'::regclass,
      'public.import_runs'::regclass,
      'public.activity_files'::regclass
    ) and (not relrowsecurity or not relforcerowsecurity)
  ),
  'RLS is enabled and forced on every exposed Phase 9 table'
);

select ok(
  has_table_privilege('authenticated', 'public.provider_connections', 'select')
  and has_table_privilege('authenticated', 'public.import_runs', 'select')
  and has_table_privilege('authenticated', 'public.activity_files', 'select')
  and not has_table_privilege('anon', 'public.provider_connections', 'select')
  and not has_table_privilege('authenticated', 'private.provider_tokens', 'select')
  and not has_table_privilege('service_role', 'private.provider_tokens', 'select'),
  'owner metadata is readable while tokens have no Data API table grant'
);

select ok(
  has_function_privilege(
    'authenticated', 'public.start_polar_oauth(text,timestamptz)', 'execute'
  )
  and not has_function_privilege(
    'authenticated', 'public.save_polar_connection(uuid,text,text,timestamptz)',
    'execute'
  )
  and has_function_privilege(
    'service_role', 'public.save_polar_connection(uuid,text,text,timestamptz)',
    'execute'
  ),
  'OAuth initiation and secret persistence privileges are separated'
);

select ok(
  exists (
    select 1 from storage.buckets
    where id = 'activity-files'
      and not public
      and file_size_limit = 26214400
  ),
  'activity file bucket is private and size bounded'
);

insert into auth.users (id)
values
  ('a0000000-0000-0000-0000-000000000090'),
  ('b0000000-0000-0000-0000-000000000090');

insert into public.athlete_profiles (athlete_id, timezone, onboarding_status)
values
  ('a0000000-0000-0000-0000-000000000090', 'Europe/Amsterdam', 'in_progress'),
  ('b0000000-0000-0000-0000-000000000090', 'Europe/Amsterdam', 'in_progress');

select set_config(
  'request.jwt.claims',
  '{"sub":"a0000000-0000-0000-0000-000000000090","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'a0000000-0000-0000-0000-000000000090';
set local role authenticated;

select lives_ok(
  $$ select public.start_polar_oauth(
    repeat('a', 64), statement_timestamp() + interval '10 minutes'
  ) $$,
  'the owner can create one expiring OAuth state'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

select is(
  public.consume_polar_oauth_state(repeat('a', 64)),
  'a0000000-0000-0000-0000-000000000090'::uuid,
  'the callback consumes the state exactly once'
);

select throws_ok(
  $$ select public.consume_polar_oauth_state(repeat('a', 64)) $$,
  'P0002',
  'oauth state not found',
  'a replayed OAuth state is rejected'
);

select is(
  public.save_polar_connection(
    'a0000000-0000-0000-0000-000000000090',
    '475',
    'provider-access-token-value',
    null
  ) ->> 'status',
  'connected',
  'the bounded callback RPC stores a connected Polar account'
);

create temporary table phase_9_import as
select public.start_polar_import(
  'a0000000-0000-0000-0000-000000000090',
  'aa000000-0000-0000-0000-000000000090',
  jsonb_build_object(
    'kind', 'historical',
    'range_start', '2026-07-19',
    'range_end', '2026-08-17'
  )
) as result;
grant select on phase_9_import to authenticated, service_role;

create temporary table phase_9_activity as
select public.import_polar_activity(
  'a0000000-0000-0000-0000-000000000090',
  (select (result ->> 'id')::uuid from phase_9_import),
  '2AC312F',
  'ab000000-0000-0000-0000-000000000090',
  repeat('b', 64),
  jsonb_build_object(
    'discipline', 'run',
    'started_at', '2026-08-17T08:00:00+02:00',
    'timezone', 'Europe/Amsterdam',
    'duration_minutes', 62.5,
    'distance_meters', 12500,
    'metrics', jsonb_build_object(
      'average_heart_rate_bpm', 149,
      'max_heart_rate_bpm', 174
    )
  )
) as result;
grant select on phase_9_activity to authenticated, service_role;

select is(
  (select result ->> 'created' from phase_9_activity),
  'true',
  'the first provider event creates a canonical activity'
);

select is(
  public.import_polar_activity(
    'a0000000-0000-0000-0000-000000000090',
    (select (result ->> 'id')::uuid from phase_9_import),
    '2AC312F',
    'ab000000-0000-0000-0000-000000000090',
    repeat('b', 64),
    jsonb_build_object(
      'discipline', 'run',
      'started_at', '2026-08-17T08:00:00+02:00',
      'timezone', 'Europe/Amsterdam',
      'duration_minutes', 62.5,
      'distance_meters', 12500
    )
  ) ->> 'created',
  'false',
  'the same provider exercise is retry-idempotent'
);

reset role;
select is(
  (
    select source from public.activities
    where id = (
      select (result #>> '{activity,id}')::uuid from phase_9_activity
    )
  ),
  'canonical_summary',
  'provider imports enter the existing canonical UC-03 activity table'
);
set local role service_role;

select is(
  public.record_polar_webhook(
    repeat('c', 64),
    repeat('c', 64),
    jsonb_build_object(
      'event', 'EXERCISE',
      'user_id', 475,
      'entity_id', 'NEXT_ACTIVITY',
      'timestamp', '2026-08-17T10:00:00Z',
      'url', 'https://www.polaraccesslink.com/v3/exercises/NEXT_ACTIVITY'
    )
  ) ->> 'duplicate',
  'false',
  'a new authenticated webhook receipt is accepted'
);

select is(
  public.record_polar_webhook(
    repeat('c', 64),
    repeat('c', 64),
    jsonb_build_object(
      'event', 'EXERCISE',
      'user_id', 475,
      'entity_id', 'NEXT_ACTIVITY',
      'timestamp', '2026-08-17T10:00:00Z',
      'url', 'https://www.polaraccesslink.com/v3/exercises/NEXT_ACTIVITY'
    )
  ) ->> 'duplicate',
  'true',
  'a replayed webhook does not create another receipt or import'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"b0000000-0000-0000-0000-000000000090","role":"authenticated"}',
  true
);
set local request.jwt.claim.sub = 'b0000000-0000-0000-0000-000000000090';
set local role authenticated;

select is(
  (select count(*)::integer from public.provider_connections),
  0,
  'another athlete cannot see the Polar connection'
);
select is(
  (select count(*)::integer from public.import_runs),
  0,
  'another athlete cannot see import state'
);
select is(
  (select count(*)::integer from public.activity_files),
  0,
  'another athlete cannot see raw-file metadata'
);

reset role;
select set_config('request.jwt.claims', '{"role":"service_role"}', true);
set local role service_role;

select lives_ok(
  $$ select public.disconnect_polar_connection(
    'a0000000-0000-0000-0000-000000000090', 'revoked'
  ) $$,
  'revocation removes the server-side token and disconnects the account'
);
reset role;
select is(
  (
    select count(*)::integer from private.provider_tokens
    where athlete_id = 'a0000000-0000-0000-0000-000000000090'
  ),
  0,
  'no provider token remains after disconnect'
);

select * from finish();
rollback;
