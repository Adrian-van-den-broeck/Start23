# WOMBO remediation A7 — activity identity and cache synchronization

**28 October 2026 (Europe/Amsterdam). Local software verification; database deferred by owner.**

Starting SHA: `24b27ebd34ccfe662ca57994a736f4f853af8d0b`.
Branch: `fix/wombo-activity-cache-synchronization`.
Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-activity-cache-synchronization`.
The accepted A6 worktree was clean at the verified full SHA. The original dirty
worktree and all unrelated worktrees were preserved.

## Baseline reproduction and source analysis

Before application changes, the two new `activitySynchronization.test.tsx`
regressions failed against A6: a full authenticated pending-reminder row absent
from the earlier history could not reach the RPE helper; reentering after remote
activity/plan changes retained the earlier empty history and workout choices.
Local `.runtime/a7-baseline.json` records **two failed / zero passed** tests.

The exact causes are the history-only lookup in `saveRpe` and the permanent
`historyLoaded` early return in `ensureActivitiesLoaded`. Both history and
workout options share that gate. Reminders publish full public activity entities
through a separate read, but the old resolver ignored them.

There remains one retained Activity owner above the existing identity-keyed
Planning/Calendar owners. The existing `getActivity` client and authenticated
backend GET already support targeted reads. No new backend endpoint is needed.

## Database owner decision

**PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA**

This is a deferral, not a passing database result. No database tooling was
installed or provisioned. No production/staging query, mutation, migration,
configuration change, push, merge or deployment is authorized or performed.


## Identity resolution and one Activity owner

`useActivityController` remains the only Activity owner. Its index contains
full authenticated public `CompletedActivity` entities from history, the pending
endpoint, targeted GET and acknowledged mutations. It indexes identities inside
the existing owner; it is not another provider/store and has no persistent or
global current-athlete state. History order and pending membership are views of
those trusted records. Names/reminder labels never become synthetic entities.

RPE uses the exact UUID and current stored RPE snapshot:

- A complete/current entity from history or the authenticated pending endpoint
  can be reused, including a remote reminder absent from the earlier history.
- Missing/stale identity uses existing `getActivity(token, UUID)`, not a full
  history download. Identity and usable feedback shape are checked before PUT.
- A missing/foreign 404 removes only that identity. Other failures preserve
  usable data and measurements. A mismatched/malformed GET cannot reach PUT.
- A reminder found already complete is displayed as changed and never silently
  converted into a correction. A changed correction RPE requires review before
  writing; the existing expected-current-RPE/recovery helper is unchanged.
- In-flight resolution is covered by the same per-activity RPE lock as the PUT.
  Two choices cannot start two resolutions/writes for that activity.

The existing verified-token backend GET/public DTO and RPE endpoints are reused.
There are **no backend/API, schema, grant or RLS changes**. The client wire test
checks exact GET UUID and bearer header with no owner override or mutation body.
Backend ownership still derives from the verified token; no client athlete ID
becomes authorization.

## Refresh and planned-workout synchronization

The permanent history-loaded gate is removed. Its remaining flag distinguishes
initial loading from background refreshing. A successful first load is not a
permanent cache promise.

- First entry, real route refocus and explicit pull-to-refresh perform a bounded
  authoritative refresh. Existing +/-14-day workout lookup, scheduled-only and
  planned-external filters are retained, including distinct same-day occurrence
  IDs. Every bundle has the existing four reads: activities, calendar choices,
  onboarding timezone and planned external activities.
- The retained authenticated shell reports route focus after training readiness.
  This avoids duplicate entry reads from reparenting and repeated focus signals.
  Standalone V1 and standalone ActivityBoundary retain their own entry lifetime;
  embedded V1 delegates to the boundary. Render/preference changes do not refetch.
  The existing native Tabs reconstruction restores Activities through Week;
  that actual refocus performs one new bounded refresh while preserving inputs.
- Successful creates/RPE/matches refresh choices/history. Acknowledged create/RPE
  entities publish immediately, so a failed follow-up read cannot restore a
  known old feedback state. No refresh calls POST/PUT.
- The existing Planning owner exposes approved identity/revision changes to the
  optional Activity owner through one `invalidateActivities` callback. A4
  check-in approval and A6 remote discovery use this same boundary. Pending
  proposals/draft edits do not invalidate approved context. Visible Activities
  refreshes; an away owner refreshes on its next supported entry.
- There is still one Planning and one Calendar owner. Activity's calendar read
  supplies workout choices, as before; it does not create a second Calendar
  manager, reset its view/navigation state or refetch unrelated ranges on render.

The existing lists gain native pull-to-refresh and V2's existing Button pattern
for read retry. No visual shell, catalog, RPE choice, training rule or additional
RPE Save button is introduced.

## Race and account protection

History requests are coalesced while current. Mutations/context invalidation can
supersede a read; sequence checks reject older success and failure results.
Reminder requests have their own sequence and coalesce with a current full read.
Entity read ordering prevents an older projection from overwriting a newer
entity. Confirmed writes supersede prior history/reminder reads. A definitive
single-activity denial also prevents an older request resurrecting that entity.

Every asynchronous publication checks the existing owner lifetime. The provider
is keyed by the authenticated Auth subject, as in A6; token rotation uses the
current token without replacing local input. A delayed A read/create/RPE result
cannot populate B. Logout during targeted resolution cannot issue the later
RPE PUT. No global mutable identity or cross-account cache is added.

## In-progress state and retry preservation

Read refresh changes authoritative read data only. It preserves selected workout
or external identity, sport, actual start, duration/distance, HR input, feedback
identity, correction editor and logical-create retry state. Selected feedback
stays pinned when new reminders are reordered. Absence from a history/reminder
list does not erase an in-progress identity; it is marked for exact verification
before a later PUT. Definitive missing/completed reads reconcile that identity.

A logical create now retains its original key **and exact input snapshot** until
an authoritative response resolves it. A read can update the confirmed profile
timezone without rewriting an uncertain create payload. Explicit retry reuses
the same key/input; reads never create another request. A known created UUID
completed remotely, a completed idempotent replay, or definitive absence can
release its finished attempt; an unknown UUID is never guessed from labels or
similar timestamps. New create keys are used only after authoritative resolution
and a subsequent explicit create action.

Uncertain mutation errors are not cleared by a successful background read.
Confirmed writes followed by read failures remain read-retry failures, including
completed create replay. Initial/background reads cannot unlock an ongoing
POST/PUT. RPE helper success clears its HR draft; failed RPE/correction keeps the
exact identity, editor, measurement and retry controls. Corrections close only
after acknowledged success. Existing helper idempotency/expected-value rules
and all deterministic backend calculations remain unchanged.

## Required scenario evidence

All results below are local synthetic controller/component/native-JS-router
boundaries. They are not real-device, real-token or PostgreSQL verification.

| Requested scenarios | Evidence |
| --- | --- |
| 1 first load; 2 unchanged reentry | One initial four-read bundle; real reentry refreshes; rerender/repeated focus coalesces |
| 3 remote activity; 4 absent-history reminder; 5 RPE completion | Stateful server fixture gains the remote UUID, reminder resolves its full entity and one exact write completes it; actual route refocus renders a new history card |
| 6 stale reminder | Exact GET absence/mismatch/unavailability cannot write; remotely complete reminder cannot become a correction |
| 7 new approved plan; 8 new choices | Actual A4 handoff approval and A6 discovery change approved identity; exact returned occurrences replace Activity choices |
| 9 local create; 10 RPE/correction refresh | Immediate acknowledged entity plus post-mutation refresh, one logical attempt and expected RPE retained |
| 11 failed read | History/choices/form/HR remain usable; retry clears read error, not an unresolved mutation error |
| 12 overlap; 13 newer result first | Forced newer request publishes; older success/failure cannot replace it or its read status |
| 14 A/B fetch; 15 logout fetch | Old history/pending/targeted results are lifetime guarded; late resolution cannot issue a PUT |
| 16 navigation during feedback | Real shell route tests preserve selected feedback UUID, HR and owner; no duplicated mutations |
| 17 unresolved create | Navigation/refresh retain key and exact input, even after server timezone changes; pending read cannot unlock POST |
| 18 repeated workouts | Two same-date instances of one template stay separate and create sends the chosen occurrence UUID |
| 19 correction identity | Helper gets the exact entity/current RPE; stale changed RPE blocks correction; failed correction keeps its editor |
| 20 no duplicate mutations | Rapid same-ID resolution/feedback and create taps have one in-flight operation; reads issue no POST/PUT |
| 21 owners | Existing nesting rejection and retained-function identity checks pass; no second Planning, Calendar or Activity owner |
| 22 A4 invalidation | Real retained owners receive pending then explicit approval; only the approved transition refreshes Activity choices; away owner waits for focus |

The two pre-fix regressions remain in the final suite. Added fixtures use full
public activity responses, distinct activity identities and a controlled 6 October 2026 clock
so their calendar response dates belong to the requested lookup window.

Superseded assertions were updated explicitly: true reentry no longer expects a
permanent one-read cache; a confirmed RPE followed by failed GET no longer expects
an old pending row. One old history fixture supplied conflicting complete and
pending objects with the same ID; it now uses distinct IDs. Shell reminder count
fixtures formerly supplied `{}` objects; they now contain complete real-contract
pending rows with distinct IDs. These corrections preserve meaningful assertions
and do not skip, remove or weaken tests. Existing no-reread-on-render/comparison,
identity, injury, approval, idempotency and privacy assertions remain.

## Verification

| Check | Final result |
| --- | --- |
| Full mobile suite, UTC | **791/791 tests; 74/74 suites passed**; zero failed/skipped/todo; zero snapshots; **123.028 s** |
| Focused Activity owner/history/reminder/RPE, plan integration and real navigation | **137/137 tests; 6/6 suites passed**; **44.875 s** |
| New A7 identity/cache cases within full run | **30/30 passed** |
| Actual A4/A6 plan-to-Activity integration | **3/3 passed** |
| A3 restrictions within full run | **29 round-trip + 18 adapter + 6 original component tests passed** |
| A4/A5 handoff/completed proposal recovery | **30/30 component tests passed** |
| A6 account-scoped recovery | **39/39 passed** |
| Retained Planning owner / Calendar owner / real route integration | **76 / 11 / 48 passed** |
| Authenticated shell identity/reminders | **3/3 passed**, plus account/lifetime tests above |
| Dedicated privacy/public view models | **58/58 tests; 8/8 suites passed**; 2.662 s |
| Strict TypeScript | **PASS** |
| Unused-code compilation | **PASS** |
| Whitespace / protected-path checks | **PASS**; no backend, API transport/types, physiological domain, RPE input adapter, A6 resume/controller, AuthProvider or dependency changes |
| Committed environment / privileged mobile credential scan | **PASS**; example/type-declaration paths only, no privileged key matches |
| Database | **PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA** |

A6 baseline was **754 tests / 72 suites**. A7 adds **37 tests / 2 suites**:
30 synchronization cases, three plan-integration cases, two UI refresh/correction
cases, one actual route-refocus case and one targeted-GET wire contract.


Accepted backend baseline: **828 passing tests**, preserved with all A10 -> A3
-> A4 -> A5 -> A6 commits verified as ancestors. Backend, API contracts,
physiology, activity input adapter, RPE transport helper, dependencies and SQL
are unchanged. Backend pytest/Ruff/mypy were therefore not rerun for this
mobile-only remediation; they are not presented as fresh A7 execution results.

Own lockfile installation: 952 packages, Node v24.18.0, npm 11.16.0; no shared
node_modules junction or lockfile update. UTC Jest uses a worktree-local cache
and all suites. Existing React act warnings remain unsuppressed. Development
runs caught obsolete cache expectations, invalid old fixtures and a test-selector
mismatch; final results above have no failed/skipped/todo cases. JSON/log evidence
is retained under ignored `.runtime/a7-*`.

## Database deferral and remaining A8 limits

**PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA**

No Docker, Podman, PostgreSQL, psql or pg_prove installation, inventory loop,
provisioning or database test attempt was made. This is not database verification
passing. Existing real-token/RLS/private-data/transaction and A5/A6 database gates
remain integration/release work. The existing targeted read was inspected for
verified-token routing and public projection; mocks cannot prove hosted grants,
RLS, transaction behavior or service configuration.

No new database-dependent implementation was introduced. The existing all-history
API/pagination-cap uncertainty (audit U-002) remains; refreshing the supported
list/window does not add a pagination contract. This is documented rather than
claimed resolved.

A8's offline Auth bootstrap handling, application deadlines/cancellation and
generic malformed-success/ambiguous-write transport handling are unchanged.
A never-settling fetch can still wait indefinitely. This change supplies scoped
read recovery and preserves the existing RPE helper; it is not a generic network
rewrite or a process-death durable local-create store.

Production/staging are unchanged. No real athlete records, hosted mutations,
configuration changes, push, merge, deployment or native build were performed.
No A2 spacing, A9 planner performance, catalog or physiological-rule change is
included. Work remains isolated and committed locally only after software checks.

## Final SHA and modified files

Final tested implementation SHA: **c4cf3531ffabe1d14f5fdb5dae9874458d6352e3**.
The report-inclusive final HEAD is a following documentation-only commit,
consistent with A3-A6's convention; it resolves through
`git rev-parse fix/wombo-activity-cache-synchronization` and is supplied in chat.
The report cannot contain its own commit hash.

- `docs/audits/remediation/WOMBO_REMEDIATION_A7_REPORT.md`
- `mobile/app/(authenticated)/(training)/activities.tsx`
- `mobile/app/(authenticated)/_layout.tsx`
- `mobile/src/api/client.test.ts`
- `mobile/src/features/activities/ActivityFlowProvider.test.tsx`
- `mobile/src/features/activities/ActivityFlowProvider.tsx`
- `mobile/src/features/activities/activityPlanSynchronization.test.tsx`
- `mobile/src/features/activities/activitySynchronization.test.tsx`
- `mobile/src/features/activities/useActivityController.ts`
- `mobile/src/features/planning/PlanningFlowProvider.tsx`
- `mobile/src/navigation/AuthenticatedLayout.test.tsx`
- `mobile/src/navigation/TrainingNavigation.test.tsx`
- `mobile/src/screens/ActivityScreen.tsx`
- `mobile/src/ui-v2/screens/ActivitiesScreen.tsx`
- `mobile/src/ui/ActivityBoundary.test.tsx`
- `mobile/src/ui/ActivityBoundary.tsx`

WOMBO REMEDIATION A7 COMPLETE — ACTIVITY SYNCHRONIZATION VERIFIED LOCALLY
