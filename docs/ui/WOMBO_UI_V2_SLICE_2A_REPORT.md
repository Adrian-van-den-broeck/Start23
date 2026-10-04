# Wombo UI V2 Slice 2a — planning state extraction

Date: 2026-10-05. Mechanical functional-preservation refactor. V1 is the only
planning presentation. No V2 Week/Home, Calendar presentation, redesign,
physiology, API contract, backend, database/schema, package or release change.

## Branch and provenance

- Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-planning-controller`.
- Local branch: `feat/wombo-ui-v2-planning-controller`, tracking the local
  `feat/wombo-ui-v2` integration branch; no remote push or merge.
- Exact starting SHA: `23243e027b9674308c13d9c946dc03ce90a01c55`.
- Runtime implementation commit: `2c7ad69`; regression commit:
  `8bab71aef55890f18ddd1e635d13bd4e71205c6b`.
- Final SHA is the documentation commit containing this report, obtainable
  with `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_2A_REPORT.md`.
- Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`; integration remains
  at the exact starting SHA. Annotated V1 tag object remains
  `d39bfcd2cf6dcc17aca231502ac4ab4e46c0465a`.
- The original dirty `fix/pre-ui-beta-blockers` checkout, coach edit and
  Garmin/privacy/PDF/UI documents were not reset, stashed, edited or staged.

Read root/mobile instructions, the current MVP roadmap, all seven requested UI
documents, the September workout selection decision/final addendum, planning
ruleset V2 record and workout distribution decision. These establish scope;
no physiological rule was copied or recalculated.

## Pre-edit responsibility audit and final ownership

| Class | Responsibility | Final location |
| --- | --- | --- |
| A: shared flow | Loaded plan/proposal, active and reviewed revisions, swipe draft/candidate/occurrences, accepted/passed state, dates/reuse, injuries, cross-training consent, placement, warnings and stale errors | One `usePlanningController`, invoked only by `PlanningFlowProvider` |
| A: actions | Create, accept/pass/undo/reset, placement, submit, approve/reject, validate/confirm/cancel move, clear rejected plan, goal-achievement write | Same planning owner |
| A: pending edits | Returned alternatives, exact proposal/revision and per-slot loading, replacement transaction | One `usePendingWorkoutActions` slot map inside the planning owner |
| B: V1 presentation | All JSX/styles/copy, cards, carousel selection/index, swipe animation/gesture refs, manual-completion display calculation, day labels, profile sheet, goal confirmation Alert | Retained in PlanningScreen |
| C: Calendar reads | Workouts/rest days, range-loading flag and monotonic latest-request guard | One separate `useCalendarController` in the flow provider |
| D: detail/modal | Selected immutable workout object, close callback, origin/date/scroll, deferred profile dismissal | Retained in the V1 presentation and unchanged existing detail boundary |
| E: development seam | Existing UiVersionControl and WorkoutDetailBoundary | Unchanged; no UI-version dependency in planning ownership |
| F: protected | Transport/DTOs, endpoint/payload/revision/retry/idempotency semantics, storage keys, server rules, gestures and visual source | Preserved |

PlanningScreen shrank from **2,395 to 1,901 lines**, a reduction of 494 lines
(20.6%) while retaining all styles. Its exported container owns the provider;
the inner V1 presentation and pending editors consume context instead of
instantiating controllers. The existing route supplies `session.user.id` only
as a local lifetime key. That value is never an API authority or payload.
Rotating access tokens do not key/remount the owner. The legacy screen entry
remains compatible through the existing accessToken/navigation props.

One WeeklyPlan DTO retains its existing active revision and pending proposal
fields. This slice does not fetch another active snapshot or invent discovery.
Flow destinations remain the existing plan/deck/calendar values so resume,
creation and submission preserve the original state-update order.

The provider refuses nesting before creating a second owner. Two consumers
share the same context value, state and actions. Before future navigation can
remount this route, its provider must move above that navigator as specified
in the architecture plan; this slice introduces no navigation shell.

## Exact operation contracts and sequencing

All functions still use the unchanged `src/api/client.ts` and public DTOs.
No transport metadata, error taxonomy, persistence or retry was added.
The following paths are relative to `/api/v1`.

| Operation | Preserved contract and order |
| --- | --- |
| Resume | SecureStore draft reference first; authenticated GET `/weekly-plans/swipe-drafts/{id}`. Submitted draft fetches its plan and awaits plan-save/draft-clear before plan/week/view updates. Otherwise restore draft/consent/week/reuse/days/deck. Only if draft restore fails/does not exist, read the remembered plan and GET `/weekly-plans/{id}`; restore plan/week/reuse/days/injuries. Invalid references are cleared through the same catches. |
| Create | POST `/weekly-plans/swipe-drafts`: `week_start`, exact sorted available dates OR explicit `reuse_previous_week: true`, confirmed injuries and cross-training opt-ins. Only a loaded active revision adds `plan_id` and `expected_base_revision: active_revision ?? 0`. Await draft reference storage before setting draft/deck. Defaults and empty-day validation unchanged. |
| Selection | POST `.../swipe-drafts/{id}/transitions`: exact `expected_revision`, action, and for accept/pass both candidate template ID and occurrence ID. Undo/reset omit candidate fields. Replace state only with returned draft, then selection haptic. Repeated template occurrences stay distinct. |
| Manual placement | PUT `.../swipe-drafts/{id}/placements/{occurrence_id}`: exact expected draft revision and date. Store returned draft. The legacy internal parameter name `templateId` is preserved; V1 still passes the occurrence ID. Multiple occurrences may share a date. |
| Submit | POST `.../swipe-drafts/{id}/submit`: exact draft revision and automatic/manual mode. Await plan-reference save and draft-reference deletion together, then clear draft, set returned pending plan, switch to plan, success haptic. No approval side effect. |
| Approve | POST `/change-proposals/{proposal_id}/approve`, `expected_base_revision: proposal.base_plan_revision ?? 0`, then GET plan without a revision argument. No automatic approval after refresh. |
| Reject | POST `/change-proposals/{proposal_id}/reject`, then GET plan with the originally reviewed `plan.revision`. This unusual read revision is deliberately unchanged. |
| Alternatives | GET `/weekly-plans/{id}/pending-workouts/{workout_id}/alternatives?expected_revision={plan.revision}` on the same V1 editor mount/revision lifecycle. Clear existing error, set slot loading; on success set options and reset V1 selection before finally clearing loading. |
| Pending edit | POST `.../pending-workouts/{workout_id}/edit-proposals`: exact revision/proposal ID from returned options and selected replacement template ID. Set returned plan before success haptic, then clear slot loading. `can_remove` is retained. V1 still has no remove button; the existing null replacement transaction is preserved without exposing a new action. |
| Move | Same same-week input guard; POST `/weekly-plans/{id}/validate` with active revision and the complete occurrence/date layout. If warning array is empty, PATCH `/planned-workouts/{workout_id}` with active revision and date. Otherwise retain warning/workout/date for cancel or explicit confirm. Only authoritative PATCH result replaces plan, then clears pending warning and emits haptic. The baseline's warning-array decision remains unchanged. |
| Goal achievement | Existing V1 Alert still requires explicit confirmation. POST `/me/goals/{id}/achievement` with the same local ISO date, then mark maintenance confirmed. |
| Calendar | GET `/calendar?from={from}&to={exclusive_end}`. Separate loading and request counter; only latest success/error/finally updates range state. Retain the same shared error display/clearing behavior and localized safe fallback. No eager or duplicate range effect was added. |

Normalized TypeScript token comparison against the exact starting SHA passes
for all 13 moved core action initializers, including `run`. V1 style block
and complete SwipeDraftPanel are byte-identical. ActionButton, WorkoutCard,
WorkoutSignals and source description/target presentation are unchanged.

Pending editor state formerly disappeared on component unmount. A local
lifetime marker preserves that behavior when state moves into a shared slot
map: a late options/loading result cannot populate a remounted editor with the
same ID. This changes no endpoint, proposal, API ordering, error handling,
same-mounted-editor request race policy or returned plan write. Its delayed
unmount/remount regression passes.

## Locks, effects, resume and privacy

- Only the provider invokes the planning controller. Consumers add no bootstrap
  effects. Rerender/detail preference changes do not fetch plans, read storage,
  retry mutations or instantiate another owner.
- Existing V1 disabled controls, `busy`, pending-slot loading and synchronous
  swipe animation ref remain. `run` is mechanically unchanged: no new lock,
  retry or opportunistic behavioral fix. Direct concurrent programmatic calls
  bypassing V1 controls remain a baseline limitation; later V2 controls must
  preserve these locks or obtain a separately reviewed behavior change.
- Calendar never shares mutation busy. Older range successes, failures and
  finally handlers remain unable to replace the latest range.
- SecureStore keys remain `start23.latest-plan-id` and
  `start23.latest-swipe-draft-id`, with unchanged device-only accessibility and
  web no-op semantics. No new persistence or token-keyed storage.
- Sign-out unmounts the flow; identity replacement resets it. Baseline Auth
  sign-out does not delete these resume keys. Resume revalidates through the
  access-token-authenticated owner-scoped API; foreign/invalid cached IDs clear
  under the existing error path. Emulator first login observed a 404 for the
  prior deleted fixture's plan, then normal fresh creation succeeded.
- Recursive mobile privacy test passed. New controller/fixtures contain only
  existing public mobile DTO data, inputs, opaque IDs and local lifecycle state.
  No TSS/private planning load, selector diagnostics, analytics or logger was
  introduced. Errors and accessibility continue through unchanged safe paths.

## Verification

| Gate | Result |
| --- | --- |
| Focused extraction | **34 tests / 2 suites passed**: 29 owner/lifecycle and 5 actual V1 integration cases |
| Full mobile suite | **159 tests / 33 suites passed**, zero snapshots |
| Strict TypeScript | `npm run typecheck` passed |
| Unused code | `npm run check:unused` passed |
| Privacy | Existing recursive source check plus unchanged Slice-1 output/poison-field checks passed in the full suite |
| Workout Detail Slice 1 | Existing PlanningDetailBoundary, WorkoutDetailBoundary, V1/V2 detail, source adapters, motion, UI resolver/provider and root-navigation tests all passed |
| Diff/source scope | `git diff --check`, action token comparison, V1 style/swipe source parity and protected-path diff checks passed |
| Backend/database checks | Not rerun: no backend/API/DTO/database change; no cross-stack verification gate introduced |

The initial cold baseline run timed out one existing detail boundary test at
the default five-second timeout. Its unchanged test passed on focused rerun;
the final full suite passed with the normal default timeout. Existing
Activity/FlashList act warnings remain; no test was weakened or skipped.
Formatting used the installed TypeScript formatter for new modules. No new
lint package/config or dependencies were installed. Node modules reuse the
existing installation through an ignored local junction.

## Emulator smoke and cleanup

Passed on emulator-5554, Android API 35 x86_64, existing SDK-57 development
client, normal Expo Router entry. Metro manifest identifies this isolated
worktree and `dev=true`; no native build, EAS update, publishing or deployment.
Final runtime source is the implementation commit `2c7ad69`; later commits add
tests and this report only.

The only hosted targets were staging API
`https://r6-api-r6-staging.up.railway.app` and Supabase start23-dev
`isfumhgqphieoayqahjv`. Exactly one tagged disposable athlete used the existing
guarded helper and supported Auth/onboarding/calibration APIs. Generated
credentials stayed in memory and were entered into normal email/password UI;
no session/token injection or direct domain/database write.

| Runtime check | Evidence/result |
| --- | --- |
| Sign-in / Planning | Normal sign-in reached unchanged V1 Planning; stale prior fixture resume reference safely cleared |
| Draft -> pending -> active | V1 create returned 201, server deck supplied two independent RUN occurrences, selection and automatic placement/submission succeeded, pending combination warning remained, explicit V1 approval returned active revision 1 |
| Plan provenance | `fe8cd9cf-c3d6-4845-a173-0b8314756f71`, week 2026-10-05, BASE, initial_catalog_baseline, two scheduled workouts. Public plan snapshot retained locally |
| Persisted resume | Cold final-bundle reload restored the pending plan before explicit approval; controller tests separately cover active plan resume |
| Week -> V1/V2 Detail | Same RUN-013 occurrence, 90 minutes, expected RPE 2–4 and supplied source segments. Zero API requests during comparison. Visible Close restored identical Week nodes except deliberately changed development preference controls |
| Calendar | Week and October Month both read successfully; selected 2026-10-07. Exactly two unique GETs: 2026-10-05 through exclusive 2026-10-12, and 2026-09-28 through exclusive 2026-11-02 |
| Calendar -> V2/V1/V2 Detail | Same loaded occurrence; zero further requests during comparison. Native Back restored Month/date/scroll; before/after XML byte-identical |
| Cleanup | Sessions globally revoked, owned Auth user deleted, admin lookup 404, zero matching tagged users. Normal app sign-out restored sign-in form |

The CDP observer repeats events three times with the same request ID; six
records represent two actual Calendar reads. It excludes headers/credentials
and does not intercept requests or instrument app source.

An auxiliary helper Calendar snapshot request mistakenly used `from_date` /
`to_date` and returned 422; its finally cleanup revoked/deleted the fixture.
The actual app had already loaded Calendar with correct `from` / `to` and HTTP
200. The following detail comparisons used that same loaded snapshot without
I/O. No API change or recovery workaround was made, and no successful auxiliary
snapshot is claimed.

Development Fast Refresh during editing left V1's existing fade surface blank;
normal cold reload restored it. Final acceptance used settled source with no
editing, and retained all original animation code. No HMR behavior was repaired.

Loopback initially bound IPv6, which adb's IPv4 forwarding could not reach.
Automatic approval review rejected a LAN listener because of broader exposure.
The safe resolution kept Metro on **127.0.0.1 only**, using Node's IPv4-first
DNS preference and adb loopback forwarding. No LAN approval or exposure occurred.

Ignored local evidence under `mobile/.runtime/`: `metro-provenance.json`,
`mobile-tests-final.json`, `action-token-parity.json`, `mechanical-parity.json`,
`slice2a-approved-plan-before.json`, `slice2a-setup-network.json`,
`slice2a-authenticated-network.json`, `slice2a-acceptance-audit.json`,
`slice2a-authenticated-cleanup.json`, and matching PNG/XML captures for Week
before/after, V1/V2 detail, Calendar before/after, Calendar V1/V2 detail and
signed-out state. Credentials/secrets are not evidence or tracked artifacts.

The [Supabase skill](C:/Users/Adria/.codex/plugins/cache/plugins-cli/supabase/0.1.12/skills/supabase/SKILL.md)
was used for the development fixture lifecycle. Existing server-only Auth
admin operations were checked against [createUser](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
and [deleteUser](https://supabase.com/docs/reference/javascript/auth-admin-deleteuser).
No Supabase feature/schema/library implementation was changed.

## Files, commits and remaining risks

Created:

- `mobile/src/features/planning/usePlanningController.ts`
- `mobile/src/features/planning/PlanningFlowProvider.tsx`
- `mobile/src/features/planning/planningResume.ts`
- `mobile/src/features/planning/planningDates.ts`
- `mobile/src/features/planning/usePendingWorkoutActions.ts`
- `mobile/src/features/calendar/useCalendarController.ts`
- `mobile/src/features/planning/PlanningFlowProvider.test.tsx`
- `mobile/src/features/planning/planning.test-fixtures.ts`
- `mobile/src/screens/PlanningControllerBoundary.test.tsx`
- `docs/ui/WOMBO_UI_V2_SLICE_2A_REPORT.md`

Modified only:

- `mobile/src/screens/PlanningScreen.tsx`
- `mobile/app/(authenticated)/planning.tsx`

Local commits:

1. `2c7ad69` — atomic extraction plus V1 wiring and independent calendar reader.
   These stay together to keep the runnable provider/consumer boundary reviewable.
2. `8bab71a` — focused ownership, lifecycle, exact-call and V1 regressions.
3. Documentation commit containing this report.

Package changes: **NONE**. Backend/API/DTO/database/physiology changes: **NONE**.
No previous Slice-1 history was squashed or rewritten. Main/integration/V1 tag
remain unchanged; nothing was pushed. Production was untouched.

Remaining risks are existing V1 control-based locking, token-refresh bootstrap
reads, component-lifetime alternatives, shared error display, and physical
Android gates. This slice preserves those semantics. A future navigation host
must retain this owner above conditional presentation/navigation, and later V2
mutating controls require their own acceptance; no V2 Week was implemented to
prove it. No required Slice-2a software/emulator gate remains open.

Slice 1 remains **WOMBO UI V2 SLICE 1 EMULATOR ACCEPTED — PHYSICAL DEVICE GATES
REMAIN**. No physical activity/HR/RPE, delayed retry, Month/Week, drag/performance,
detail, TalkBack/focus, reduced-motion, text-scale or inset gate was closed.

WOMBO UI V2 SLICE 2A COMPLETE — V1 BEHAVIOR PRESERVED
