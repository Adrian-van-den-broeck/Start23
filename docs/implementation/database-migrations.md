# Database migration workflow

## Status

The workflow is selected. Migration `20260724140227_create_athlete_profiles`
has been applied to the hosted development project. Catalog verification and
a rollback-only two-athlete RLS test passed. Migration
`20260724142004_restrict_rls_auto_enable_execution` resolves the database
advisor findings for the RLS event-trigger function. A subsequent security and
performance advisor run returned no issues. The local pgTAP suite is prepared;
end-to-end tests with two real Auth sessions remain pending.

## Workflow

Start23 uses reviewed imperative Supabase migrations:

1. inspect the target development project and current migration history;
2. create a named migration through the current Supabase CLI command;
3. edit and review the generated migration locally;
4. verify grants, RLS, indexes, constraints, rollback implications, and
   cross-athlete fixtures in a non-production environment;
5. run Supabase database and security advisors;
6. compare local and remote migration history;
7. apply the reviewed migration to the development project explicitly;
8. rerun integration and RLS isolation tests;
9. promote the same committed migration through controlled environments.

Commands must be discovered with the installed CLI's `--help`; command syntax
must not be assumed from memory. Production migrations are never an automatic
FastAPI or Railway startup action.

## Initial Phase 2 migration scope

The first migration will contain only the minimum profile-isolation slice:

- `athlete_profiles` linked one-to-one to `auth.users`;
- immutable `athlete_id` ownership;
- explicit least-privilege grants;
- RLS enabled for every exposed table;
- separate `SELECT`, `INSERT`, and `UPDATE` owner policies for
  `authenticated`;
- both `USING` and `WITH CHECK` on updates;
- `(select auth.uid())` ownership checks;
- ownership indexes where the primary key does not already provide one;
- no grants for `anon`;
- no service-role use in normal athlete requests.

The exact columns will be reviewed with the migration. Phase 2 needs only
identity, onboarding status, timezone, revision, and timestamps. Biometrics and
physiological inputs belong to Phase 4 and will not be guessed in the Phase 2
migration.

## Backend access decision

For authenticated athlete requests, FastAPI calls the Supabase Data API with:

- the project publishable key as the application API key; and
- the caller's verified access token as the bearer token.

This makes PostgreSQL evaluate grants and RLS as `authenticated`, with
`auth.uid()` derived from the caller. FastAPI remains the only mobile-facing
domain API and performs application ownership checks as well.

Atomic critical operations will use narrowly granted `SECURITY INVOKER`
PostgreSQL functions called with the same caller token. The function accepts no
authoritative athlete ID and reads `auth.uid()` itself. `SECURITY DEFINER` and
the Supabase service-role key are not the default athlete-request path.

New Data API objects receive explicit grants because Supabase is moving new
projects toward opt-in table exposure. Grants and RLS are separate controls and
must be tested together.

## Verification gate

Phase 2 cannot be complete until two real Supabase Auth test users prove:

- each can create, read, and update only their own profile;
- neither can select or mutate the other's row through FastAPI or the Data API;
- an unauthenticated request has no table access;
- ownership cannot be changed;
- an invalid or expired token is rejected;
- transaction and RLS behavior match the documented access decision.

Hosted catalog and rollback-only SQL verification already prove the intended
grants, policies, immutable ownership, trigger behavior, and cross-athlete row
isolation. Real access-token tests through FastAPI and the Data API remain the
final integration gate.
