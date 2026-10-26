# WOMBO remediation A4 — authoritative task-to-plan handoff

**26 October 2026. Implemented and verified locally.** The check-in lifecycle
in WOMBO-005 now hands the approved backend revision to the retained Planning
owner, native resume locator and existing Calendar owner. Pending next-week
proposals remain separate from the selected approved week. Final verification:
**701 mobile tests / 71 suites and 784 backend tests passed.** This is not a
beta-readiness or production-safety assessment.

## 1. Starting SHA, ancestry and isolation

- Exact starting SHA: **`b65ea78be1db886586d793f721bb2910ddbc6a41`**,
  the accepted A3 head.
- The A3 worktree was clean and at that exact SHA before branching; both
  checks were repeated after implementation. `git merge-base --is-ancestor`
  verified that accepted A10 `11591b9924ebfd3872314deecb82c57fc278126b` is
  an ancestor. A3's implementation parent was also verified.
- Branch: **`fix/wombo-checkin-plan-handoff`**.
- Worktree: **`.worktrees/wombo-checkin-plan-handoff`**, beneath
  `F:\Projecten Business\Start23\Code`.
- Final tested implementation commit:
  **`1aa4e458ac1549391f78d7d64f82807f824cee44`**.

Root/mobile `AGENTS.md`, the current MVP roadmap, full audit, fix plan,
end-to-end matrix, A10/A3 reports, mobile owners/routes/clients and backend
check-in/planning contracts were read. Original audit documents were consulted
in `.worktrees/audit-wombo-full-system-review/docs/audits/`; they are not
tracked on the accepted A3 head and were left there unchanged.

The new worktree has its own lockfile-installed dependencies. Existing UI V2,
A3, main and original dirty worktrees were not reset, stashed or overwritten.
Local main and the UI integration branch remain at
`aff74558d0a6511286a4a84a44ea25a03ca57549`; neither was used as this fix's base.

## 2. Original failure sequence and evidence

At A3, `CheckInScreen.makeProposal()` retained the returned plan only in screen
state. `approve()` directly called `approvePlanProposal()` and then `onBack()`.
`TrainingFlowHost` correctly retained its Planning provider across navigation,
so returning to Week retained the previous week's object. No authoritative
follow-up read, locator write or Calendar synchronization occurred.

The new `WOMBO-005` regression was run with the accepted A3 check-in source
temporarily substituted **only in this isolated worktree**, then restored.
The synthetic server had applied approval, but the assertion looking for
`Next week supplied bike` failed: Week still rendered the old plan.
`.runtime/a4-baseline.json` records that intentional failure. With the fix, the
same test passes, including exact revision/workout IDs, Calendar and restart.
Initial harness setup errors were corrected before this defect reproduction;
they are not counted as evidence of the application defect.

Current implementation references:

- `mobile/src/screens/CheckInScreen.tsx:307` — generation and shared handoff.
- `mobile/src/screens/CheckInScreen.tsx:320` — approval/recovery through owner.
- `mobile/src/features/planning/usePlanningController.ts:337` — receive boundary.
- `mobile/src/features/planning/usePlanningController.ts:356` — approval boundary.

## 3. Shared handoff contract and ownership

`usePlanningController` exposes `receiveTaskPlan(taskKey, serverSnapshot)` and
`approveTaskPlan(taskKey, reviewedSnapshot)`. `TaskPlanHandoff` records the task
key, exact reviewed snapshot, latest server snapshot, approval receipt and local
synchronization phase: `pending`, `verify`, `read`, `persist`, `complete`.
These phases describe synchronization; they are not new backend plan statuses.

There is still **one Planning owner and one Calendar owner**, both retained by
the existing host. The screen no longer posts plan approval directly. Its
local proposal fallback preserves a successful generation result if handing it
off is temporarily blocked. Saving that fallback does not also approve it.
Direct `/check-in` entry requests the existing training-readiness host instead
of creating another controller.

The shared contract also accepts an already-active authoritative task result;
it retains the reviewed identity and cannot downgrade it when an older pending
snapshot is delivered again. A regression verifies this reusable path.

## 4. Pending versus active and exact identities

Receiving a pending Week N+1 proposal updates `taskHandoff` only. Week N remains
selected and active; its locator and Calendar are unchanged. Navigation back
and reopening the same check-in can recover that retained proposal without
generating another. A retained proposal also suppresses duplicate generation.

Only explicit approval posts the exact proposal ID and supplied base revision.
The response's plan ID/revision and subsequent snapshot's plan ID, week,
revision number, revision ID, active pointer and active state are checked.
Pending proposal targets must identify the supplied revision. Mismatches fail
closed; no revision is manufactured and no source-template ID becomes an
occurrence identity.

The principal fixture uses Week N `plan-a`, revision 2, followed by `next-plan`,
revision 1 / `next-revision-1`, proposal `next-proposal`, base revision 0.
Its two same-day workouts have distinct IDs `next-workout-1` and
`next-workout-2` while sharing one source template. Both survive the handoff.

## 5. Approval, refresh, persistence and navigation ordering

1. Acquire the existing owner's synchronous mutation lock.
2. POST approval with the exact reviewed proposal/base revision.
3. Retain the successful receipt before any follow-up work.
4. GET the exact receipt revision using the existing `getWeeklyPlan` client.
5. Validate its identity and active state.
6. Publish the authoritative selected/active snapshot in the retained owner.
   Clear obsolete local move/draft presentation; update week/availability/injury
   selections from that server snapshot. Existing provider effects reconcile
   Calendar and focus the newly selected task week.
7. Persist the approved plan ID, then clear the old swipe-draft locator, using
   the existing native SecureStore keys/accessibility configuration.
8. Mark synchronization complete. Only then does the mounted check-in screen
   return using its existing `onBack` route to `/planning`.

Publishing server success precedes local persistence, so a storage failure
cannot roll the athlete back to the old week. Navigation away does not cancel
an authorized mutation or prevent its result reaching the still-live owner.
An unmounted screen cannot trigger a late navigation callback.

## 6. Calendar synchronization

`useCalendarController.acceptApprovedPlan()` merges the complete approved week
into an overlapping retained range, including empty/rest-only weeks. It removes
obsolete rows for that week and preserves neighboring weeks. This cannot use
the old selected week's workout IDs: new plans have different occurrence IDs.

An overlapping in-flight read is superseded by the existing request-number
guard. Unrelated ranges remain cached and unrelated requests may finish.
If the newly focused week needs a range read, the existing `ensureCalendarRange`
performs it. Returning between tabs does not continually refetch. The existing
same-week move reconciliation remains intact.

`PlanningPresentationProvider` focuses the new approved task week even if
Calendar was previously visited. It does not reset Calendar on ordinary tab
switches or same-plan workout moves. Actual Expo Router tests verify the same
Planning/Calendar owner functions survive the task route and root return.

## 7. Failures, late responses and athlete identity

| Scenario | Verified behavior |
| --- | --- |
| Generation fails | Old selected/active plan and locator remain unchanged |
| Approval rejected / stale, 422 / 409 | No new active plan or silent revision switch |
| Approval applies, follow-up GET fails | Receipt retained; explicit recovery GETs exact revision without another POST |
| Storage fails after authoritative GET | New active plan retained; recovery retries storage without approval or GET |
| Approval outcome ambiguous | Explicit status check reads the reviewed revision first; it does not replay POST |
| Status check finds the same pending proposal | Returns to an explicit approval decision; no automatic mutation |
| Receipt or read identifies another revision/plan | Synchronization fails closed |
| Duplicate approval interaction | Shared synchronous lock prevents duplicate effects |
| Navigation during generation/approval | Successful result reaches retained owner; dead screen cannot navigate |
| Old Calendar success/failure arrives | Cannot overwrite the affected authoritative week or publish obsolete errors |
| Old resume read succeeds/fails after handoff | Cannot replace the new selection or erase its locator |
| Athlete replaced during follow-up read | Previous owner's result cannot publish into the replacement owner |
| Old native write already issued | Writes serialize; the replacement owner's later locator wins; dead-owner continuation is suppressed |

Owner lifetime guards apply to this handoff and its competing bootstrap. Native
writes already issued cannot be cancelled, so the existing persistence module
now serializes writes and accepts a current-owner predicate for queued work.
This is the minimum ordering guard exercised by the A4 account-replacement
tests, **not a resolution of WOMBO-008/009**. Global locator namespaces,
legacy mutation lifetimes, transient resume deletion and discovery remain A6.

## 8. A3 preservation and next-week input

No restriction-form helper, check-in request/response type, context save,
fingerprint confirmation or backend restriction logic changed. The handoff
uses the generated server plan; it never reconstructs restrictions from UI
defaults. The A3 fixture's professional advice, blocked run/swim and limited
bike answers remain visible and generation uses the exact check-in ID.

All **29 A3 round-trip tests**, **18 restriction-adapter tests**, six original
check-in tests and existing transport tests pass in the full run. All **784
backend tests** pass, including A3's six save/reload/confirmation/exact
next-week-input cases and existing injury/planning contract coverage.

## 9. Supporting-task audit and A5 integration boundary

`ZoneProfileScreen.schedule()` can create a weekly-plan field-test proposal;
`decideAssignment()` can approve/reject its plan proposal. Those actions still
reload only local zone/onboarding data through that screen's `run()` helper
(`ZoneProfileScreen.tsx:178`, `:210`, `:237`). The route supplies plan/revision
parameters rather than a handoff. This remains a task-specific inconsistency;
it was not necessary to refactor it to prove the requested check-in lifecycle.
A separately verified adaptation can reuse `receiveTaskPlan` and
`approveTaskPlan`, rather than introduce another controller.

`CalibrationScreen.activateZones()` approves a zone proposal, not a weekly-plan
snapshot, so it was left unchanged. No new zone-to-plan transition was invented.

A5 should reuse the same boundary when its backend can replay the exact
completed check-in proposal. A4 retains the most recent task proposal in the
live owner, but does not add durable pending-task storage or backend completed
proposal replay. A process kill or lost generation response before this handoff
is still an A5/A6 recovery gap. An approval receipt awaiting synchronization is
also currently in memory. Successful **completed** native persistence and
normal restart are tested; arbitrary interruption/restart recovery is not
claimed.

## 10. Regression tests and results

**27 tests added:** 20 in `PlanningTaskHandoff.test.tsx`, four Calendar-owner
cases, two actual-route cases and one API wire-contract case. They exercise
stateful synthetic server/storage transitions, not a preselected final owner.
The client test separately checks real client URLs, bearer headers, approval
body and exact revision query. No test was skipped or weakened.

The two existing automatic/manual submit cases now additionally verify that
draft-locator deletion waits for the serialized plan write; all original
identity, pending-only and duplicate-lock assertions remain.

Environment: Node 24.18.0, npm 11.16.0, Python 3.10.10. No dependency changed.

| Check | Actual result |
| --- | --- |
| Locked `npm ci --no-audit --no-fund` | PASS; own worktree dependencies, unchanged manifest/lockfile |
| Focused eight-suite development run | 223/223 passed; last reusable-active-result case subsequently verified by full suite |
| Final full `TZ=UTC npm test -- --ci` | **701/701 tests, 71/71 suites; zero failed/skipped/todo, zero snapshots; 126.399 s** |
| Final focused suite results within that full run | 224/224 across handoff, navigation, Planning, Calendar, both check-in screens, restriction adapter and transport suites |
| `npm run typecheck` | PASS, exit 0 |
| `npm run check:unused` | PASS, exit 0 |
| Privacy/public-data `npm test -- --ci src/privacy.test.ts src/ui-v2/utils` | **58/58 tests, 8/8 suites; zero failures/skips** |
| Date/Calendar/handoff tests, `TZ=Europe/Amsterdam` | **84/84, 6/6 suites; 20.319 s** |
| Same tests, `TZ=America/Los_Angeles` | **84/84, 6/6 suites; 17.701 s** |
| Full backend `pytest -p no:cacheprovider` | **784/784 passed, zero failures/errors/skips; 203.67 s** |
| Committed environment-file / privileged mobile credential scans | PASS, no matches |
| Whitespace and protected-path diff checks | PASS |
| Hosted Actions, native device, hosted DB/pgTAP | Not executed; no push, native build or hosted mutation authorized |

The principal screen tests use a controlled current date of 5 October 2026.
The real navigation test also retains elapsed wall time for native animation
timing while calendar constructors stay controlled. A10's date-regression
coverage remains unchanged. Existing rapid-action tests emit React `act`
warnings; the backend emits its existing Starlette/httpx deprecation warning.
Warnings were not suppressed and no dependency was changed to remove them.

Machine-readable JSON/XML and logs remain locally under ignored `.runtime/`:
`a4-baseline`, `a4-focused-final`, `a4-mobile-full`, `a4-privacy`,
`a4-amsterdam`, `a4-los-angeles`, and `a4-backend`. The inherited mobile CI
workflow remains unchanged; its full/static/privacy gates were run locally.

## 11. Exact files changed

Application files:

1. `mobile/app/(authenticated)/check-in.tsx`
2. `mobile/src/features/planning/usePlanningController.ts`
3. `mobile/src/features/planning/PlanningFlowProvider.tsx`
4. `mobile/src/features/planning/planningResume.ts`
5. `mobile/src/features/calendar/useCalendarController.ts`
6. `mobile/src/features/calendar/useCalendarNavigation.ts`
7. `mobile/src/navigation/PlanningPresentationProvider.tsx`
8. `mobile/src/screens/CheckInScreen.tsx`

Tests/fixtures:

9. `mobile/src/screens/PlanningTaskHandoff.test.tsx` — new
10. `mobile/src/features/planning/planningTask.test-fixtures.ts` — new
11. `mobile/src/navigation/TrainingNavigation.test.tsx`
12. `mobile/src/features/calendar/useCalendarController.test.tsx`
13. `mobile/src/features/planning/PlanningFlowProvider.test.tsx`
14. `mobile/src/api/client.test.ts`

Report:

15. `docs/audits/remediation/WOMBO_REMEDIATION_A4_REPORT.md`

## 12. Scope, final commit and remaining verification

There are **no backend, API, schema, migration, formula, coefficient, catalog,
planner algorithm, private-load calculation, dependency, production
configuration or CI changes**. Ruff/mypy were not rerun because Python source
and tests are unchanged; the full backend suite was rerun against this branch.

Final application/test commit SHA:
**`1aa4e458ac1549391f78d7d64f82807f824cee44`**. This report is included by a
subsequent documentation-only commit, following the A10/A3 report convention.
The report-inclusive final HEAD is recorded in the delivery message and
resolves with `git rev-parse fix/wombo-checkin-plan-handoff`, avoiding a
self-referential report hash.

A2, A5, full A6, A7, A8, A9 and other original findings remain outside scope.
In particular, durable completed-proposal recovery, global/account-scoped
discovery, legacy late writes and general transport/auth recovery are not
claimed fixed. Physical-device kill/relaunch, native storage fault injection,
real-token/two-device hosted concurrency and deployed revision compatibility
remain release verification gates. No claim of whole-product beta readiness
is made.

**Production and staging are unchanged.** Synthetic fixtures only were used.
There was no push, main merge, deployment, hosted mutation, schema application
or change to an existing UI V2 worktree. All commits are local to the isolated
A4 branch.

WOMBO REMEDIATION A4 COMPLETE — AUTHORITATIVE PLAN HANDOFF VERIFIED
