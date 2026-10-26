# WOMBO remediation A5 — idempotent check-in proposal recovery

**27 October 2026 (Europe/Amsterdam). Implemented; PostgreSQL verification pending.**
WOMBO-006 has a targeted backend/mobile implementation. All runnable checks pass:
**810 backend tests; 711 mobile tests in 71 suites**. Database transaction/RLS
claims remain subject to the unexecuted local integration gate below.

## 1. Starting SHA, branch and worktree

- Exact accepted A4 starting SHA: `4bb0cdea8f46242018ad8e5d22fa79a706cbf207`.
- Accepted branch: `fix/wombo-checkin-plan-handoff`. Its worktree was clean,
  matched that SHA, and was checked again unchanged after implementation.
- `git merge-base --is-ancestor` verified accepted A10 `11591b9` and A3
  `b65ea78` are ancestors; A4 is the immediate baseline, not the audit baseline.
- New branch: `fix/wombo-checkin-proposal-recovery`.
- Isolated worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-checkin-proposal-recovery`.
- The original main worktree was already dirty. No reset, stash or overwrite
  was performed there or in another worktree.

Read root/mobile AGENTS.md, current MVP roadmap, the full audit, prioritized fix
plan, E2E matrix, A3/A4 reports, current backend/mobile contracts and applicable
migration/RLS definitions. As documented by A3/A4, original audit documents are
in the sibling `audit-wombo-full-system-review/docs/audits` worktree, absent
from the accepted source tree; they were read there and left unchanged.
The Supabase skill was used for RPC/security review and local verification.

## 2. Reproduced root cause

`CheckInService.generate_plan_proposal` previously requested
`get_checkin_context_for_planning` first. Its latest applied definition filters
`weekly_checkins.status = 'open'`. Successful attachment changes that status to
`completed`, so retry raises `checkin_not_confirmed` before persistence's
idempotent behavior can recover anything. Mobile resume restored context but
never read the completed check-in's proposal after process restart.

Before implementation, the new deterministic orchestration regression supplied
an already committed attached result and an OPEN-only context conflict. It
failed at the context read with `CheckInRepositoryConflictError`, reproducing
the control-flow defect. `.runtime/a5-baseline.log` retains that diagnostic.
An earlier harness constructor mistake was corrected before this reproduction;
it is not counted as defect evidence. This was a local mocked-boundary
reproduction, not a PostgreSQL or hosted reproduction.

## 3. Exact replay contract and read-before-generate behavior

The existing HTTP endpoint and `WeeklyPlanProposalResponse` remain unchanged.
A new authenticated, security-invoker RPC, `get_checkin_plan_proposal`, accepts
only the check-in locator. It uses the existing owner-scoped check-in read,
then verifies the attachment through check-in -> proposal -> target revision,
including athlete ownership, revision.checkin_id and proposal kind. It reads
that **explicit revision**, not the latest/active/default revision.

| Server condition | Result |
| --- | --- |
| Owned open check-in, no attachment | SQL null; existing confirmed-context/generation path may proceed |
| Owned completed check-in with valid attachment | Exact current persisted proposal and its explicit plan revision, HTTP 200 |
| Completed check-in without a recoverable attachment, or inconsistent attachment | Explicit `checkin_proposal_unrecoverable`, HTTP 409; no generation |
| Open check-in with stale/unconfirmed context or stale plan base | Existing conflict semantics retained; no unconditional overwrite |
| Missing or foreign check-in | Same not-found response, HTTP 404 |
| Invalid UUID | FastAPI validation, HTTP 422, before repository access |
| Dependency failure or malformed stored projection | Safe generic HTTP 503; no raw stored payload disclosure |

A completed row without an attachment is already forbidden by the existing
completion constraint; the explicit fail-closed guard also covers inconsistent
historical state. No constraint is weakened to manufacture this case.

The service reads the attachment **before** the OPEN-only context operation.
If another request commits between that read and a context conflict, it reads
again and returns the attachment. With no attachment it preserves the original
conflict. After new creation/attachment it reads back the authoritative stored
snapshot rather than returning an assumed in-memory success. Planning repository
errors now use the established safe planning error mapper on this route.

## 4. Identity and historical value preservation

Replay returns existing athlete-scoped check-in attachment, proposal ID,
plan ID, revision ID/number, target/base revision, workout occurrence/planned
workout IDs, template selections, status and warnings. It creates no UUID and
calls no candidate generator, catalog selection, coach or physiological
calculation for an already attached replay. Existing public response formatting
continues unchanged. No historical physiological/private-load value, ruleset,
model version or catalog selection is transformed or recalculated.

Full response equality is asserted across repeated backend replay. Mobile
checks exact proposal/revision IDs and both distinct workout IDs sharing one
source template. The approved fixture now includes the applied proposal because
the actual explicit-revision PostgreSQL projection includes it after approval.

## 5. Concurrency, atomicity and legacy partial work

Source inspection found two RPC transaction boundaries: create persisted the
proposal, then attach completed the check-in. Existing attachment locks the
check-in and rejects attachment to another proposal; fingerprint idempotency,
plan locks and unique constraints also exist. Those guarantees alone did not
make create-plus-attach atomic or expose completed replay.

The forward-only migration replaces the current v3 persistence wrapper. For a
check-in it locks the owner-scoped check-in row **before any creation writes**.
An existing valid attachment returns its exact locator regardless of terminal
state. With no attachment, existing v2 creation and provenance validation run,
then the existing attach RPC runs **inside the same transaction**. Any failure
rolls back nested plan/revision/workout/load/attachment writes together. A later
competing create sees the attachment under that same lock. No new proposal
state machine, distributed lock, service or last-write-wins path is introduced.

For pre-A5 persistence that committed before attachment, one unambiguously owned
proposal/revision bearing that check-in ID can be attached without replacement.
Multiple possible historical results fail closed with 409; none is guessed,
deleted, revived or recalculated. Existing applied/rejected/expired state is
preserved. The service retains its idempotent attachment call for compatibility.

Two requests already calculating before either commits can still perform
candidate work. They must converge on one persisted attachment; A5 does not
implement A9 CPU deduplication. That convergence is the intended SQL behavior,
**not an executed PostgreSQL race result on this workstation**.

## 6. Completed and terminal proposals

The public response already supports pending/applied/rejected/expired proposal
states and active/rejected/expired/superseded revision states. Recovery therefore
returns these existing actual states without inventing a terminal response type.
A terminal result never becomes pending and never triggers replacement generation.
Applied and still-active results can synchronize through A4 without reapproval;
an applied but superseded revision remains historical and is not selected active.

## 7. Mobile restart recovery and A4 integration

Start/resume of the selected week reads its persisted check-in. When completed
or carrying an attachment, it calls the replayable endpoint and passes the
returned plan into A4's existing `receiveTaskPlan` boundary. This uses the
server-owned week/check-in attachment as the durable locator; no pending-plan
UUID is recreated or independently persisted locally.

A pending result stays in the retained Planning owner's task handoff. The old
active week, native active-plan locator and Calendar stay unchanged until explicit
approval. Approval continues through `approveTaskPlan`, exact revision read,
native persistence and existing Calendar synchronization. Recovery does not
POST approval. The existing rejection API can be invoked explicitly for that
reviewed proposal, followed by authoritative replay and handoff invalidation.

A fresh terminal server result clears a retained pending handoff for that task.
It displays its closed status and no approval/generation control. There is still
one Planning owner and one Calendar owner. The screen's existing local fallback
is retained, not promoted into an independent controller. Existing same-tick
locks, navigation lifetime guards and owner disposal protect late results.

## 8. Requested network/failure matrix

Evidence below is local API/orchestration/component execution unless explicitly
identified as an unexecuted database test. Synthetic server fixtures assert
stored server state separately from displayed UI; they are not real DB proof.

| Requested case | Evidence and authoritative outcome |
| --- | --- |
| 1-2. Normal generation/response | New generation orchestration reads stored attachment; existing actual planner/API persistence tests pass; pending remains separate |
| 3. Commit then HTTP loss | Backend attachment stub commits then raises; mobile fixture stores proposal before throwing; retry retains identical result |
| 4-5. One/multiple retries | Backend three repeated replays preserve complete response; no planner or attach invocation for replay; mobile retry generates once |
| 6. Restart after loss | New backend service and fully remounted mobile host recover same attached proposal from server state |
| 7. Existing pending | Restored review requires explicit approve/reject; no automatic activation |
| 8. Already approved | Applied/active replay synchronizes via A4 without another approval POST |
| 9. Rejected/superseded | API retains terminal status; mobile rejected/expired/superseded cases clear stale pending handoff, no replacement |
| 10. Stale check-in | Existing context conflict survives second replay lookup; no generation; existing plan base/revision suite passes |
| 11. Foreign athlete | Caller token transport and safe 404/error tests pass; actual RLS negative test authored in pgTAP, execution pending |
| 12. Invalid ID | API 422 occurs before repository lookup |
| 13. Concurrent requests | Ten concurrent existing-result replays tested; new-create PostgreSQL row lock reviewed; overlapping real-create probe authored, execution pending |
| 14. DB error before attachment | Context/generator failures leave attachment uncalled and errors safely mapped |
| 15. Partial DB work | pgTAP injects failure at check-in completion after nested writes and asserts no residual plan/revision; unexecuted; v3 makes transaction atomic |
| 16. Navigation away during generation | Existing A4 test still retains exact result in the live owner without late navigation; included in final focused run |
| 17. Sign-out/account replacement | New delayed recovery tests prevent publication/persistence in replacement/dead owner; no automatic approval |

## 9. A3 restrictions, security and privacy

A3 restoration, professional advice provenance, explicit restriction review,
alarm acknowledgement, exact context revision/fingerprint and injury inputs
are unchanged. All A3 component/adapter/API cases and 11 Python physiology
injury tests pass. Existing physiological and planning domain files are unchanged.

The new read uses the caller bearer token and publishable key, with existing
RLS and opaque-owner restrictive policies retained. It does not accept a client
athlete/proposal ID for authorization, grant table access, expose private schemas
or use a service credential for replay. Generation still uses verified backend
athlete identity and the existing legacy-owner adapter/service-only boundary.
Foreign/missing reads share not-found semantics. Public DTO/privacy checks pass;
malformed stored responses cannot reveal their raw validation payload. No keys,
passwords, real athlete records or private-load diagnostics were logged or committed.
Real-token/RLS execution remains a database/hosted gate, not a claimed local pass.

## 10. Exact verification results

Environment: Python 3.10.10 via the existing backend virtualenv; Node 24.18.0,
npm 11.16.0. Mobile uses an isolated `npm ci` installation of the unchanged
lockfile (952 packages). Verification spanned 26-27 October Amsterdam time.

| Check | Actual result |
| --- | --- |
| Pre-fix deterministic replay regression | Failed as expected at OPEN-only context read |
| Final focused A5/check-in/domain/injury run | **52/52 passed**, zero failures/skips; 8.31 s |
| New A5 backend coverage within that run | **26/26 passed** |
| Earlier planning/repository/check-in/injury focused run | **109/109 passed**; before final malformed-projection case; 105.14 s |
| Full backend `pytest -q -p no:cacheprovider` | **810/810 passed**, zero failures/errors/skips; 203.24 s |
| Planning API/service, domain, repository coverage in full run | **50 + 89 + 13 passed** |
| Existing check-in API/domain and injury coverage in full run | **10 + 5 + 11 passed** |
| Public contract tests in full run | **6/6 passed**, including recursive public data checks |
| Full `TZ=UTC npm test -- --ci` | **711/711 tests, 71/71 suites passed**, zero failed/skipped/todo, zero snapshots; 135.579 s |
| Final focused A5/A4/A3/navigation/Planning/Calendar/API run | **234/234 tests, 8/8 suites passed**; 52.401 s |
| Dedicated mobile privacy/public view models | **58/58 tests, 8/8 suites passed**; 2.525 s |
| `npm run typecheck` | PASS |
| `npm run check:unused` | PASS |
| `ruff check .` | PASS |
| `ruff format --check .` | PASS; **143 files** |
| Strict `mypy app tests scripts/verify_a5_local_concurrency.py` | PASS; **141 source files** |
| Migration filename inventory | PASS; **48 unique versions**, A5 latest |
| Whitespace, protected-path and committed environment scans | PASS |
| Fresh local migrations / pgTAP / actual concurrent creation | **NOT EXECUTED — runtime unavailable** |

Accepted A4 baseline was 784 backend tests and 701 mobile tests / 71 suites.
A5 adds 26 backend and 10 mobile tests; no tests were deleted, skipped or
weakened. Existing React act warnings and the Starlette/httpx deprecation warning
remain; no dependency was changed to silence them. JSON/XML/log evidence is
local under ignored `.runtime/a5-*`; this committed report is the portable record.

## 11. Actual PostgreSQL/pgTAP gate and migration

Migration: `20261026224844_wombo_a5_checkin_proposal_recovery.sql`, created with
the cached Supabase CLI `migration new` command. It adds one invoker read RPC and
replaces v3 orchestration only. No applied migration, table constraint, RLS policy,
existing grant boundary or historical row was rewritten. No migration was applied.

The local Supabase start attempt returned:
`LegacyDockerLifecycleInspectError`: Docker command not found; Podman also not
found. Neither PostgreSQL/psql nor Docker was found on PATH/standard installation
locations. The local concurrency probe exited before connecting because psql is
unavailable. **Zero pgTAP suites or PostgreSQL transaction tests were executed.**
Python mocks and SQL source inspection are not used as proof of transaction,
serialization, grant or RLS behavior. SQL function compilation/schema lint is
also unverified until a real runtime is available.

Authored rollback-only pgTAP covers invoker/service grants, owner reads, exact
repeat results and warnings, no activation, rollback after partial creation,
terminal replay and legacy persistence-before-attachment recovery. Its row-lock
source assertion is explicitly labeled structural, not a concurrent race test.

`backend/scripts/verify_a5_local_concurrency.py` is a separate real-PostgreSQL
probe: it refuses non-loopback URLs, creates synthetic local fixtures, holds a
check-in lock while another create runs, compares both locators, inspects the
persisted single pending revision/attachment, checks authenticated replay, and
cleans up those generated synthetic users. It is syntax/lint/type checked but
**not runtime verified**. After bringing up a disposable fully migrated local DB,
run the repository pgTAP suite and this probe with psql installed. Do not run
these fixtures against hosted databases or real athletes.

## 12. Complete file list

1. `backend/app/modules/checkins/repository.py` — authenticated replay read/error code.
2. `backend/app/modules/checkins/router.py` — explicit safe conflict/dependency mapping.
3. `backend/app/modules/checkins/service.py` — read-before-generate, race/read-back recovery.
4. `backend/scripts/verify_a5_local_concurrency.py` — local-only actual PostgreSQL probe.
5. `backend/tests/test_checkin_proposal_recovery.py` — 26 focused regression cases.
6. `backend/tests/test_checkins.py` — existing fake implements new read protocol.
7. `mobile/src/features/planning/planningTask.test-fixtures.ts` — actual applied-proposal projection.
8. `mobile/src/features/planning/usePlanningController.ts` — invalidate terminal task review.
9. `mobile/src/screens/CheckInScreen.tsx` — authoritative resume/rejection and closed-state copy.
10. `mobile/src/screens/PlanningTaskHandoff.test.tsx` — ten recovery lifecycle cases.
11. `supabase/migrations/20261026224844_wombo_a5_checkin_proposal_recovery.sql`.
12. `supabase/tests/wombo_a5_checkin_proposal_recovery_test.sql`.
13. `docs/audits/remediation/WOMBO_REMEDIATION_A5_REPORT.md` — this report.

## 13. Final SHA, remaining A6 limitations and open gates

Final tested implementation SHA:
**`64d974792cde3af12004357deef94f2a65be79eb`**.
This report is committed subsequently as documentation only, following A3/A4's
convention. The report-inclusive final HEAD is delivered in chat and resolves
with `git rev-parse fix/wombo-checkin-proposal-recovery`; a commit cannot include
its own SHA in its file contents.

A5 recovery is scoped to the selected week/check-in. It does not discover every
account plan/draft, choose a historical check-in across week rollover, namespace
legacy global native locators, repair all transient bootstrap deletion or legacy
late writes, or implement generic auth/transport recovery. Those remain A6/A8.
No A2 spacing, A7 activity invalidation, A9 CPU optimization or unrelated audit
finding was implemented. There is no UI redesign, new training science, catalog
rule or selection algorithm.

Open verification gates: fresh full migration-chain compilation, all relevant
pgTAP/RLS/grant suites, the actual concurrent-create probe, two-real-token/two-device
hosted isolation and fault injection, exact deployed schema compatibility, and
physical Android/iOS kill/relaunch/account/navigation behavior. Existing scientific,
privacy and release governance gates remain unchanged. Passing local suites does
not close those gates or establish whole-product beta readiness.

## 14. Production/staging and integration confirmation

**Production and staging are unchanged. No push, merge or deployment occurred.**
No hosted database mutation, hosted migration, remote configuration change,
native build or real athlete data operation was performed. A4 and unrelated
worktrees were left intact. The implementation and report are committed locally
on the requested isolated branch.

**WOMBO REMEDIATION A5 IMPLEMENTED — DATABASE VERIFICATION PENDING**
