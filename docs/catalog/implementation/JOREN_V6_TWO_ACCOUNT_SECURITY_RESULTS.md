# WOMBO V6 two-account security results

14 November 2026. **Real GoTrue A/B execution: BLOCKED — ENVIRONMENT.**
No successful full-stack isolation result is asserted.

## Required bidirectional matrix

Each row must run **B against A and A against B**, with actual owned IDs created
by the other genuine account and real issued access tokens. Every real-token
cell below is **NOT EXECUTED / BLOCKED — ENVIRONMENT**.

| Attempt by the other account | Required result |
| --- | --- |
| Read training plan, revision or calendar occurrence | Owner-safe absence/404 or documented authorization denial, no owner payload |
| Change frequency preference | Token resolves only the caller's preference; foreign owner input rejected/ignored per contract; target unchanged |
| Create another athlete's frequency authority | No athlete HTTP issuance route; direct registrar/table access denied; no reviewer enrollment |
| Read private authorization evidence | No direct-table, RPC, embedding or API leak |
| Swipe or edit workout/draft | Foreign reference denied, target revision/choices unchanged |
| Confirm pending plan | Foreign proposal denied, still pending and inactive |
| Move workout | Foreign physical/logical ID denied, original date and evidence unchanged |
| Attach activity to physical occurrence | Foreign reference denied and no activity/occurrence mutation |
| Reuse immutable creation/edit/move/approval receipt | No cross-owner read or replay result; no new operation authorized by another account's receipt |
| Read TSS/private load/frozen context | No private field/value in response, error, UI, accessibility output, analytics or request logging |
| Missing/expired/tampered/revoked credentials | Test Auth, Data API and FastAPI individually; measure logout access window separately from revoked refresh denial |
| Concurrent account operations | No owner mix-up; revision preconditions, current authority and immutable receipts retained |

For each denial, compare the target's revision, pending state, occurrence/activity
counts and original receipts before/after. A generic server error is not sufficient
proof. Check malformed/foreign IDs without exposing whether another athlete owns
the resource. Exercise direct gateway table/RPC access as well as FastAPI routes.

## Fresh local SQL permission observations

These are actual PostgreSQL observations from this task's **SQL subset runtime**,
not actual Supabase gateway-role assertions. Full details are in
[sql-permissions.json](real-auth-20261114/sql-permissions.json).

| Boundary | Observed local SQL result |
| --- | --- |
| `private.register_frequency_decision(integer,jsonb)` EXECUTE | `anon=false`, `authenticated=false`, `service_role=false` |
| `private.frequency_decisions` SELECT | All three roles false |
| `private` schema USAGE | anon false; authenticated and service_role true. Schema visibility alone grants no table/registrar access |
| Role attributes | anon/authenticated are NOLOGIN, no BYPASSRLS; service_role is NOLOGIN with BYPASSRLS; registrar/test-executor are NOLOGIN without BYPASSRLS |
| RLS and FORCE RLS | Both true on public athlete_profiles, weekly_plans, plan_revisions, planned_workouts; private v6_plan_snapshots, frequency_preferences and frequency_decisions |
| Real positive authority | Zero reviewer rows, zero decision rows; no actual designation, individual numerical maximum or issuance |
| Catalog | 77 V6 revisions; zero active |

All 37 SQL suites complete **722 assertions** with the existing A5 fixture overlay,
including owner/RLS, generation/service boundaries, composite-owner references,
private evidence custody, approval and frequency revocation. The untouched A5
source's separate prerequisite failure is retained in
[the original-failure ledger](real-auth-20261114/a5-final-original.json).

The regular frequency runner freshly passes **9 groups**, including suspension
before commit, competing replacement/swipe, confirmation waiting on authority
invalidation, attachment serialization and immutable receipt recovery. SQL-set
claims and an injected FastAPI identity resolver are used. No GoTrue account,
real JWT or gateway request is involved. Pure numerical authorization fixtures
in pytest are hypothetical values, not actual approved maxima.

All **2,876 backend tests** and **929 mobile tests** pass, including existing
owner/replay/public-contract/privacy regressions. This does not establish that
every matrix row above has a fresh SQL test, nor that any row passed with real
GoTrue credentials. No application grants, RLS policies, operator configuration,
production dependency or historical records were changed to obtain these results.

## Remaining boundary

Repeat the full matrix through the real gateway after supplying
[the supported environment](JOREN_V6_REAL_AUTH_ENVIRONMENT.md). Preserve the
restricted operator/reviewer system. Positive multi-session issuance remains
unavailable until an actually designated operator and reviewed numerical decision
exist; the default stays at one session per goal sport. A preference above one
must remain a wish, never an authorization.
