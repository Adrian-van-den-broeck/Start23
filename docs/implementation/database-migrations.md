# Database migration workflow

## Status

The workflow is selected. Migration `20260724140227_create_athlete_profiles`
has been applied to the hosted development project. Catalog verification and
a rollback-only two-athlete RLS test passed. Migration
`20260724142004_restrict_rls_auto_enable_execution` resolves the database
advisor findings for the RLS event-trigger function. A subsequent security and
performance advisor run returned no issues. The local pgTAP suite is prepared;
end-to-end tests with two real Auth sessions remain pending.

Phase 4 migration
`20260727132531_phase_4_onboarding_goals_zones` is present in the hosted
development project.
Forward migration `20260728133728_phase_4_5_review_hardening` adds the trusted
fallback boundary, complete planning-input snapshots, refresh triggers, and
missing foreign-key indexes; it was applied on 2026-07-28. The original local
migration also contains the final definitions for clean database rebuilds,
while the idempotent forward migration upgrades projects where Phase 4 was
already applied. The updated pgTAP suite is committed, while execution
currently requires a Docker/`pg_prove` runtime that is not installed on this
workstation.

Phase 5 migration `20260727170000_phase_5_workout_catalog` is also created and
was applied to hosted Supabase on 2026-07-28. It creates
immutable public catalog structure, read-only authenticated policies, a
non-client-accessible private load table, seven reviewed versions representing
six current templates, and aggregate validation. Its pgTAP suite is committed,
but no Docker/`pg_prove` runtime is available locally to execute it. The linked
database linter reports no schema errors after both migrations. Hosted table
statistics confirm the expected 7 templates, 7 private load rows, 21 segments,
14 phase tags, and 7 zone-requirement rows. Server-side secret-key probes
confirm both privileged RPC authorization paths without persisting test data.

Phase 6 migration `20260729140000_phase_6_weekly_planning` was applied to
hosted `start23-dev` on 2026-08-10. It adds one immutable
power-compatible catalog item, forced-RLS weekly plan/revision/workout/warning
tables, private workout and revision load snapshots, typed plan proposal
references, service-only generation/direct-move RPCs, and owner-scoped
security-invoker read/decision RPCs. Its pgTAP suite covers grants, RLS, hidden
load access, idempotent pending generation, owner isolation, stale approval,
atomic application, and revisioned direct moves. The rollback-only suite passes
30/30 against the hosted project. It now collects TAP output in a temporary
table so the Management API returns every assertion, and its schema-existence
checks use pgTAP's unambiguous three-argument signature.

The 2026-08-09 Phase 6 review amended the then-unapplied migration so repeated
approval or rejection of the same owned proposal returns its existing public
result without repeating the transition. Its pgTAP suite now also exercises
repeated approval and rejection. The first hosted advisor run then identified
missing covering indexes for Phase 6 foreign keys. Forward migration
`20260809225626_phase_6_advisor_indexes` adds those indexes; the rerun reports
no remaining Phase 6 unindexed foreign keys. Remaining advisor output is the
project-level leaked-password-protection warning, two pre-existing Phase 4
foreign-key index notices, and expected unused-index information on the new,
low-traffic development schema. Two real Auth sessions also pass owner and
cross-owner Data API isolation using one minimal weekly-plan fixture per test
account. No test credential is stored in the repository.

Phase 7 migration `20260811103726_phase_7_activity_rpe_feedback` was created on
2026-08-11 and remains local/unapplied. It adds forced-RLS public activity and
metric tables, a grant-free private realized-load table, explicit
authenticated canonical create/read/list functions, narrow service-only
processing functions, weekly realized-load projection for planning, and typed
pending correction-plan creation. New public objects use explicit grants; the
mobile role has no direct private-table access. The companion rollback-only
pgTAP suite covers grants, owner isolation, idempotency conflicts, immutable
RPE, hidden-TSS output, pending-only correction, approval, and planning load
projection. The ruleset-3 amendment accepts partial classified intensity time,
projects private planned/realized intensity minutes into planning, stores
bounded average/maximum speed only for bike activities, and adds the
`manual_review_recovery` target basis. These changes were made in the still
unapplied Phase 7 migration rather than a second migration. Local execution is
blocked only by the absent Docker/PostgreSQL
test runtime; hosted application, advisors, pgTAP, and real-token checks remain
explicit verification gates and were not performed automatically.

Phase 8 migration `20260813105401_phase_8_structured_weekly_checkin` was
created with the current Supabase CLI workflow on 2026-08-13 and remains
local/unapplied. It adds revisioned check-ins and confirmed context,
seven-day functional restriction review, planned outside activities,
achieved-goal maintenance, explicit rest-day projection, low-only and
rest-only plan state, exact complete-local-week history, an athlete-timezone
Monday entrypoint, and current-local-week RPE audit revisions. All new public
tables have forced RLS and explicit grants; direct weekly-context writes are
blocked by a trigger and admitted only through owner-scoped RPCs. Generated
plan persistence and check-in attachment remain narrowly service-only, and no
public contract exposes planned or realized TSS.

The rollback-only `phase_8_structured_weekly_checkin_test.sql` suite covers
object existence, forced RLS, grants, local-Monday idempotency across widely
separated timezones, owner isolation, exact context confirmation, active
restriction retention, outside-activity completion, a pending rest-only plan,
zero private rest-only load, explicit approval, and seven public rest days.
The official CLI reset was attempted on 2026-08-13 but could not inspect/start
the local stack because neither Docker nor Podman is installed or available on
`PATH`. Therefore SQL execution, hosted application, advisors, pgTAP, and
real-token isolation remain explicit gates; no hosted or production change was
made automatically.

Phase 8.5 forward migration
`20260813170000_phase_8_5_zone_calibration` was added on 2026-08-13. The
Supabase CLI is not installed on this workstation, so the normal `migration
new` command could not create the empty file; the reviewed timestamped
imperative migration was added directly and remains local/unapplied. It adds
forced-RLS discipline setup, immutable calibration observation, and immutable
evaluation tables. Athlete setup/observation writes use owner-derived
`SECURITY INVOKER` RPCs; server-generated evaluation persistence uses one
narrow `service_role`-checked function. New Data API objects have explicit
least-privilege grants and owner indexes. Planning snapshots now include the
discipline setup route, and onboarding can finish with an explicit RPE-only,
field-test, or calibration route without creating fake active zones.

The rollback-only `phase_8_5_zone_calibration_test.sql` suite covers table
existence, forced RLS, function/grant separation, RPE-only persistence, direct
write rejection, immutable/idempotent observations, cross-athlete isolation,
service-only deterministic results, immutable evaluations, and absence of TSS
columns. SQL execution, advisors, hosted migration, and two-real-token checks
remain explicit gates because no local PostgreSQL/Docker runtime or Supabase
database runtime is available. A current CLI can now be invoked ephemerally
through `npx`; that does not provide the missing Docker/PostgreSQL runtime.

Decision migration `20260825225207_phase_8_5_9_business_decisions` was created
through the current Supabase CLI workflow and applied to linked development on
2026-08-26. It adds the exclusive zone/protocol segment target contract,
the reviewed week-1 bike calibration catalog item, bounded Polar import retry
state, `reconnect_required`, invoker/RLS read-only Polar RPCs and explicit
athlete-confirmed activity matching. Its rollback-only pgTAP suite verifies the
target constraint, absence of public TSS in the protocol target, retry grants,
invoker functions and authenticated match grant. All nine assertions pass via
the rollback-only Management API query path. Two-real-user isolation remains an
explicit release gate.

Phase 10 migration `20260826085242_phase_10_date_only_planning` was created
through pinned Supabase CLI `2.115.0` and applied to linked development on
2026-08-26. It adds authoritative `available_dates` and provenance to plan
revisions, authoritative `scheduled_date` to planned workouts, explicit
previous-week reuse, exact pending-revision planning context, date-based
calendar/rest/move RPCs, and a TSS-free owner plan projection. The previous
timestamp is retained only as an athlete-local-noon internal compatibility
projection for existing private relationships. New/changed objects have
explicit grants; private planning-context functions are service-role-only and
owner reads remain `SECURITY INVOKER`.

The rollback-only `phase_10_date_only_planning_test.sql` suite contains 18
assertions for columns/types, triggers, date function signatures, invoker and
service-role grant separation, and the absence of `scheduled_at` in the public
plan function. All 18 pass against development. Local and remote migration
history aligns, linked public/private error-level lint is clean, and advisors
contain no error or Phase 10-specific warning. The first push exposed an
invalid target-table alias reference in the backfill; that Phase 10 transaction
rolled back before ledger registration, the SQL was corrected to a correlated
`SET` subquery, and a dry-run plus retry then succeeded.

The pinned CLI's local reset still fails with `LegacyLocalDbRunningError`.
Likewise, `test db --linked` unexpectedly requires local Docker for `pg_prove`.
The committed rollback-only suites were therefore executed directly through
current `db query --linked --file`; successful output ended at `1..9` for the
decision suite and `ok 18` with no `finish()` failure summary for Phase 10.
Read-only hosted verification also confirms zero null backfilled dates,
date-only public move/calendar signatures, service-only private planning
context and a service-only retry claim RPC. Two-real-user isolation remains an
explicit release gate; no production project was changed.

Phase 11 migration `20260826144239_phase_11_discipline_zone_profiles` was
created through pinned Supabase CLI `2.115.0` on 2026-08-28 and remains
local/unapplied. It adds explicit RPE planned-target snapshots, bounded
completion-time heart-rate observations, independent discipline test
assignments, standalone `validation_test` proposals, run/bike plan-integrated
test binding, physician/lab provenance persistence, and approval synchronization.
Integrated plan approval is guarded so a field-test revision cannot be applied
without its exact typed assignment. All user-owned assignment rows use forced
RLS; direct critical writes remain trigger-guarded, while service-role
functions are narrow and explicitly granted. No public contract exposes TSS.

The rollback-only `phase_11_discipline_zone_profiles_test.sql` suite contains
24 assertions for RLS, triggers, grants, catalog targets, exact boundary
ownership, RPE snapshot creation, heart-rate writes, measured provenance, and
integrated-test approval binding. It has not run: local error-level lint waited
on the unavailable database service at `127.0.0.1:54322` and was interrupted.
Hosted application, linked lint/advisors, pgTAP, migration-ledger comparison,
and two-real-user isolation are explicit release gates. No hosted or production
database was changed.

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

Generated data that cannot safely be accepted from the athlete token uses a
separate exception path. A server-only Supabase secret key may execute only
explicitly granted `SECURITY DEFINER` RPCs that verify the `service_role`,
accept the athlete identifier from the already-verified FastAPI context, and
perform one bounded operation. Phase 4 uses this for deterministic fallback
zone persistence; Phase 5 uses it for a read-only durable planning-catalog
projection. Phase 6 uses it to persist Python-generated pending plans and copy
private snapshots after a verified direct athlete move. Neither role receives
direct access to any private planned-load table.

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
