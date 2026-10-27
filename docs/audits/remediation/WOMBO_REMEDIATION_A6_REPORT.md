# WOMBO remediation A6 — account-scoped plan recovery

**27 October 2026 (Europe/Amsterdam). Implemented; database verification pending.**

Starting SHA: `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf`.
Branch: `fix/wombo-account-scoped-plan-recovery`.
Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-account-scoped-plan-recovery`.
A5 worktree was clean at that exact SHA; the unrelated original dirty worktree
was preserved. The new worktree started clean. Accepted A10 `11591b9`, A3 `b65ea78`
and A4 `4bb0cde` were verified ancestors; no original audit/main baseline was used.
Root/mobile AGENTS.md, current MVP roadmap, the four requested audit documents
and all A10/A3/A4/A5 reports were consulted. Original audit files were read
in the sibling `audit-wombo-full-system-review/docs/audits` worktree; they are
absent from the accepted A5 source tree and were left unchanged. The Supabase
skill was used for the ownership/grant/read-boundary review.

## Root causes recorded before implementation

WOMBO-008: `usePlanningController` catches any draft/plan GET error and deletes
its SecureStore locator, including offline, authentication, 5xx and malformed
responses. 404 only changes the displayed read state, not the deletion decision.
There is no explicit resume retry and no plan discovery without native storage.
Web skips resume entirely. Draft restore precedes plan restore unconditionally.

WOMBO-009: `planningResume` uses two global keys across athletes. A4 serializes
writes and guards task handoffs, but older generate/submit/clear operations use
unguarded writes. A late A mutation can overwrite B's global key. Provider
identity keys isolate React objects but cannot isolate global SecureStore data.

| Lifecycle | A5 behavior |
| --- | --- |
| Startup | Native draft then plan global locator; no locator means empty |
| Temporary network failure | Deletes locator; failed state hides empty in V2 only |
| Token refresh | Retained owner, repeats global locator reads |
| Logout | Owner unmounts; global locators survive; older mutation writes may finish |
| Login B | B reads A's global locator; denied read deletes it |
| Return A | A's deleted/overwritten locator is lost |
| Restart | Depends on whichever global keys remain |
| Reinstall | No server discovery; cannot recover lost keys |
| Second device | No plan locator unless created locally |
| Remote approval/revision | No foreground plan reconciliation; local owner can remain stale |

Backend plan reads use the caller JWT and owner-scoped `get_weekly_plan`; draft
reads use RLS and verified opaque-athlete ownership in the service. Proposal
reads and A5 completed-check-in replay already enforce ownership. A4 retains one
Planning and one Calendar owner and separates pending task plans from active
Week state. A6 must integrate with these boundaries.

## Initial database environment inspection

Docker, Podman, psql, pg_ctl and initdb absent on PATH; no standard PostgreSQL or
Docker installation/service found. Elevated read-only WSL inventory returned no
distributions. No hosted database was contacted. Fresh migration, pgTAP and A5
real PostgreSQL concurrency verification remain OPEN.


## Owner-scoped persistence and legacy migration

The authenticated Supabase Auth subject (`session.user.id`) is now required by
PlanningFlowProvider, including the standalone App entry. Its existing React key
isolates one Planning owner and one Calendar owner. Token rotation retains that
owner. The subject is only a local lifetime/storage namespace; the backend still
resolves verified tokens to its opaque athlete identity.

Native keys are `start23.<auth-subject>.latest-plan-id` and
`start23.<auth-subject>.latest-swipe-draft-id`, with the existing device-only
SecureStore accessibility. No email/name or full plan/health snapshot is stored.
Writes capture the initiating owner. The existing write-order guard now queues
per owner, so an issued slow A write cannot block B. Queued dead-owner writes are
dropped; already issued native writes finish only in A's namespace. No mutable
"current account" singleton exists. Reads, handoffs, generation, submission,
placement, onboarding reads, moves and pending-editor continuations discard late
results after their owner/request lifetime ends. Plan mutations supersede older
resume generations. Explicit read retries coalesce while a resume is running.

Legacy global keys are bounded read-only hints: at most the existing two keys
are consulted per attempt when a scoped key is absent. A successful authenticated
GET with a valid matching resource identity is required before copying a legacy
locator into that owner's namespace. Foreign/missing/unverifiable global hints
are never adopted or deleted. Discovery supplies authenticated recovery instead.
Global keys are deliberately retained because they may belong to another athlete;
there is no unverified global cleanup or migration of full athlete state.
SecureStore read failure can fall back to discovery. A successful creation whose
locator write fails retains its returned draft for recovery instead of losing it.

## Read-only server discovery contract

Added `GET /api/v1/weekly-plans/recovery`, before the dynamic plan-ID route.
There are no owner inputs, no mutations, no physiological calculations and no
catalog generation on this endpoint. `get_authenticated_athlete` derives the
opaque owner from the verified token. Extra client identity query parameters
cannot override it.

The strict Pydantic response contains nullable `active` and `pending` existing
public plan DTOs, plus nullable `draft` with ID, revision, collecting/placement
status and week. The repository reuses existing authenticated public-table reads,
the operational-profile timezone read and exact `get_weekly_plan` RPC. Every
metadata table query has an explicit opaque-owner filter, deterministic ordering
and limit 1. It uses the caller bearer token and publishable key throughout.
The plan-parent embedding explicitly identifies its composite foreign key to
avoid ambiguity with the reverse active-revision relationship. No private load
projection or service-role discovery call is introduced.

Bound: four metadata requests normally, five if the active fallback is needed,
including timezone, then at most two exact public plan reads. Mobile additionally
verifies at most its two saved locators and reads a discovered draft through the
existing owner-checked draft endpoint. No all-history list is downloaded.

Selection is recovery presentation, not a new plan lifecycle or training rule:

1. Derive current Monday in the operational profile's timezone. Prefer the
   latest **active** plan week through next Monday, the existing planning target
   in `planningDates.nextMonday` and A4's approved following-week handoff. If none
   exists, choose the earliest later active week. UUID breaks ties. Creation time
   never promotes a rejected/expired/pending row over an active plan.
2. Select a pending revision from the earliest current/future week on/after the
   selected active week, then highest revision number, then UUID. Its parent must
   be active/pending, its proposal still pending, with the exact target revision
   and current base. Stale/inconsistent/racing projections fail with safe 503.
   Past pending proposals are not selected as current tasks by discovery.
3. Select an open collecting/placement draft from the earliest week on/after
   both current and selected active week, then most recent update and UUID.
   Closed drafts are recovered through their plan/proposal. A locally verified
   submitted draft can resolve its bound plan. An older draft cannot displace a
   newer approved plan.
4. A freshly owner-verified local historical or later approved selection remains
   usable; an earlier discovery default does not undo a later explicit A4
   selection. Newer applicable authoritative active state wins. Historical
   snapshots/provenance are read as stored, never recalculated under new rules.
5. A same-plan pending revision retains its separate exact active snapshot.
   A different next-week pending proposal uses the existing A4 `TaskPlanHandoff`;
   Week and its locator remain active. Both V1/V2 can explicitly review and
   return, approve through A4 or reject. Discovery never approves anything.

API-contract documentation, OpenAPI path inventory, typed mobile response and
bearer-only client contract tests were updated. There is no generated-type
pipeline in this slice; the existing manually typed client contract is retained.

## Startup, retry and lifecycle after A6

The owner loads its scoped hints, verifies them authoritatively, preserves
trustworthy snapshots on later failure, then performs bounded discovery and
reconciles exact active/pending/draft identities. Confirmed results hydrate the
existing owner and persist only changed locators. `recoveryVersion` invalidates
the existing Calendar read cache; the existing approved-plan merge still handles
A4 handoffs. Invalidating the read cache does not claim that its displayed range
becomes null; a subsequent `ensureCalendarRange` must fetch again, as tested.

| Result | Behavior |
| --- | --- |
| Offline/network, timeout rejection, 500/502/503, temporarily unavailable auth | Keep scoped locators and trustworthy state; recoverable failed read; explicit retry |
| Malformed JSON or unusable recovery projection | Same uncertainty; no partial successful plan or inferred empty state |
| Missing/foreign resource, authoritative 404 | Remove only this owner's scoped hint, then discover; leave global and other-owner keys untouched |
| 403 without owner-scoped absence proof | Preserve hint; a permission/auth fault is not proof of foreign ownership |
| Stale revision/context, 409 | Preserve locator; attempt authoritative discovery/reconciliation, otherwise expose retry; no automatic mutation |
| Valid empty discovery with no verified local selection | Existing empty state; no automatic plan/draft creation |
| Local storage failure | Discover from server where possible; retain authoritative state if persistence fails |

Explicit accessible retry uses the existing Wombo Button/error patterns. V1 no
longer presents its empty preparation form while startup is unknown. V2 retains
its existing uncertainty model. Navigation/Calendar stay available. Foreground
and token refresh perform reads, not mutation retries; a still-running resume is
not duplicated. Pending proposals remain pending and exact IDs/revisions are
retained. No successful response or approval receipt is manufactured.

| Lifecycle | A6 behavior |
| --- | --- |
| Normal startup / restart | Verify owner-scoped plan/draft, then reconcile discovery |
| Temporary failure | Preserve identity and useful owner state; explicit retry |
| Auth refresh | Same owner, new-token reads, obsolete response guard |
| Logout | Unmount owner, suppress late publications and queued writes |
| Login B | Independent keys and fresh owner; no deletion/overwrite of A |
| Return A | A's own saved identity and authenticated discovery remain available |
| Reinstall | Discovery does not depend on retained SecureStore data |
| Second device | Same authenticated discovery; no local UUID prerequisite |
| Remote approval/revision | Foreground/read retry adopts authoritative applicable revision and invalidates Calendar |

## Regression and adversarial evidence

Tests use the real hooks, provider, screen transitions and client against
stateful synthetic owner/storage/server fixtures. These are software-boundary
results, not real PostgreSQL, real Supabase sessions or physical-device proof.

| Requested matrix | Evidence |
| --- | --- |
| 1 normal resume; 9 restart | Exact authenticated GET, preserved scoped ID, unmount/remount |
| 2 offline; 3 503; 4 timeout; 5 retry | Parameterized read rejection -> failed/unknown -> explicit retry -> retained plan; also 500/502/auth/403/malformed |
| 6 missing; 7 foreign; 8 empty | Only caller's definitive 404 hint removed; foreign owner retained; valid empty creates nothing |
| 10 reinstall; 11 second device | No saved locator; bounded server discovery hydrates active state |
| 12 A/B/A | Independent maps, exact plans and both surviving account locators |
| 13 late GET; 14 late native write | Switch/logout before response; B completes while A native write remains unresolved; A result cannot target B |
| 15 legacy migration; 16 unverified legacy | Owner GET before copy; global unchanged; denied/transient hint falls back to authenticated discovery |
| 17 active plus pending | Exact pending handoff, old active locator preserved, explicit V1/V2 review/back/approval |
| 18 draft | Exact open draft revision/occurrence recovery and submitted-draft plan resolution |
| 19 stale revision; 20 concurrent resumes | Draft revision changes between reads -> fail safely with locator retained; two retry intents -> one resume |
| 21 A4 handoff | Existing explicit approval, exact revision, storage-failure recovery, old read races, Week/Calendar/restart tests pass with scoped keys |
| 22 A5 recovery | All 30 handoff/replay component cases and 26 A5 backend replay cases pass; no duplicate generation/automatic approval |
| 23 A3 injuries | 29 round-trip, 18 adapter and 6 original component cases; 10 check-in API and 11 physiology injury cases pass; no implicit clearance |
| 24 Calendar invalidation | Remote approval followed by ensure performs a new range read; existing approved-week merging and late Calendar response tests pass |
| 25 authorization denial | Token A/B discovery, actual foreign draft/plan/proposal IDs, missing/foreign safe errors, ignored client owner override, token-only wire contract |

Additional tests cover late creation/submission after account replacement,
pending-editor unmount continuation, malformed successful local plan read,
verified draft surviving discovery failure, storage read/write errors, and a
later verified explicit approved selection surviving an earlier default.

Superseded tests were updated deliberately: generic errors no longer mean
"foreign/missing" and deletion fixtures now carry an authoritative 404; native
write tests assert two namespaces instead of the last global writer winning.
Submitted-draft tests wait for synchronization before asserting persistence.
All prior behavioral assertions remain except the explicitly superseded global
storage/destructive-error expectations. No test was skipped or weakened.

## Exact verification results

Environment: Python 3.10.10 in the existing backend virtualenv; isolated mobile
`npm ci` from the unchanged lockfile installed 952 packages. Node/npm versions
are v24.18.0 / 11.16.0; no dependency upgrade or shared node_modules
junction was used. Jest runs in UTC with a worktree-local cache and watchman
disabled; all suites are included.

| Check | Final result |
| --- | --- |
| Full backend pytest, no cache provider | **828/828 passed**, zero failures/errors/skips; 196.40 s |
| A6 backend cases within full run | **18/18 passed** |
| A6 + public-contract focused run | **24/24 passed** |
| A5 backend replay / check-in / injury within full run | **26 / 10 / 11 passed** |
| Backend OpenAPI/public contracts | **6/6 passed**, including full route inventory and recursive privacy checks |
| Backend authentication / identity repositories | **7 / 2 passed** |
| Full mobile Jest | **754/754 tests, 72/72 suites passed**, zero failed/skipped/todo, zero snapshots; 103.977 s |
| A6 recovery hook cases within full run | **39/39 passed** |
| Planning/A3/A4/A5/Calendar/navigation/client/Week subset within full run | **288/288, 10/10 suites passed** |
| Dedicated mobile privacy/public view models | **58/58, 8/8 suites passed**; 2.953 s |
| Strict TypeScript | PASS |
| Unused-code compilation | PASS |
| Ruff lint / format | PASS; **144 files** formatted |
| Strict mypy, including A5 local concurrency script | PASS; **142 source files** |
| Whitespace and protected-path scans | PASS; no physiology/domain/swipe/auth/dependency/schema changes |
| Tracked env / privileged mobile credential scans | PASS; examples/type declaration only; no privileged key matches |
| Migration inventory | **48 unique migrations**, unchanged; **28 pgTAP suites**, unchanged |

A5 baseline was 810 backend and 711 mobile tests in 71 suites. A6 adds 18
backend tests and 43 mobile tests (39 recovery, three Week/retry/review cases,
one discovery transport case). Early development runs exposed test-harness
reset/key/text-selector mismatches and the intentionally changed OpenAPI
inventory. Those were corrected; final complete runs above have no failures.
Existing React act warnings and the Starlette/httpx deprecation warning remain.
PowerShell renders native Jest stderr as an error record even for PASS lines;
machine-readable Jest success/totals and explicit final process exit were checked.
Logs/JSON/XML are retained locally under ignored `.runtime/a6-*`.

## PostgreSQL/pgTAP and security gate — OPEN

The initial runtime inventory above was repeated. Docker, Podman, psql, initdb,
pg_ctl and pg_prove are absent; no local PostgreSQL/Docker service or WSL distro
was found. No safe ready-to-run isolated PostgreSQL/pgTAP environment is present.
No system service/virtualization installation or hosted fallback was attempted.

The existing loopback-only A5 concurrency probe was invoked again and exited
before connecting: `psql is unavailable; PostgreSQL concurrency gate remains
open.` Thus **zero fresh databases, zero applied migrations, zero pgTAP suites
and zero actual PostgreSQL concurrency/replay runs** are claimed here.

Before closing this gate, apply all 48 migrations to a disposable local Supabase
PostgreSQL, run all 28 pgTAP suites including A5 replay/security, and run
`backend/scripts/verify_a5_local_concurrency.py`. Also exercise the actual
PostgREST recovery projections/embedding/order with synthetic A/B tokens and
distinct Auth/opaque IDs, including remote approvals and the full security
negative matrix. Unit/MockTransport repositories do not prove these database
queries, RLS, grants, SQL compilation or transaction behavior.

A6 introduces **no SQL migration, function, EXECUTE grant, table grant or RLS
change**. Existing SELECT grants, FORCE RLS and opaque-owner policies were
inspected and preserved. Discovery never uses service-role privileges. Source
privacy and cross-owner software tests pass; final native binary/hosted security
certification remains outside this local implementation evidence.

## Scope and final commits

No A2 spacing, A7 activity cache, A8 global auth/transport, A9 performance or
physiological/planning-rule change is included. A7's activity history/reminder
invalidation is still open. A8's offline Auth bootstrap credential deletion,
general transport deadlines/cancellation and global malformed-response handling
are unchanged. Timeout tests inject the existing read rejection; A6 does not
claim that a never-settling fetch now has an application deadline. Physical
keychain/reinstall/background behavior and real two-device hosted execution
remain deployment/device gates.

Production and staging are unchanged. Synthetic fixtures only were used.
No hosted mutation, push, merge, deployment, native build or production
configuration change occurred. All commits are local to the isolated A6 branch.

Final tested implementation SHA: **63a3d7c97278213cafa35ca1eeb3db5ff5a1b1b2**.
The report-inclusive HEAD is a subsequent documentation-only commit, following
A3/A4/A5's convention; it resolves with
`git rev-parse fix/wombo-account-scoped-plan-recovery` and is supplied in chat.
A report cannot contain its own commit hash.

## Files modified

- `backend/app/modules/planning/repository.py`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/service.py`
- `backend/tests/test_contracts.py`
- `backend/tests/test_planning.py`
- `backend/tests/test_planning_recovery.py`
- `docs/architecture/api-contracts.md`
- `docs/audits/remediation/WOMBO_REMEDIATION_A6_REPORT.md`
- `mobile/App.tsx`
- `mobile/src/api/client.test.ts`
- `mobile/src/api/client.ts`
- `mobile/src/api/types.ts`
- `mobile/src/features/planning/PlanningFlowProvider.test.tsx`
- `mobile/src/features/planning/PlanningFlowProvider.tsx`
- `mobile/src/features/planning/planningRecovery.test.tsx`
- `mobile/src/features/planning/planningResume.ts`
- `mobile/src/features/planning/usePendingWorkoutActions.ts`
- `mobile/src/features/planning/usePlanningController.ts`
- `mobile/src/navigation/TrainingNavigation.test.tsx`
- `mobile/src/screens/PlanningControllerBoundary.test.tsx`
- `mobile/src/screens/PlanningCreationBoundary.test.tsx`
- `mobile/src/screens/PlanningDetailBoundary.test.tsx`
- `mobile/src/screens/PlanningProposalBoundary.test.tsx`
- `mobile/src/screens/PlanningScreen.tsx`
- `mobile/src/screens/PlanningSupportingSheet.test.tsx`
- `mobile/src/screens/PlanningTaskHandoff.test.tsx`
- `mobile/src/screens/PlanningWeekBoundary.test.tsx`
- `mobile/src/screens/PlanningWorkoutMoveBoundary.test.tsx`
- `mobile/src/ui-v2/utils/weekHomeViewModel.ts`

WOMBO REMEDIATION A6 IMPLEMENTED — DATABASE VERIFICATION PENDING
