# Wombo UI V2 Slice 4C report

## Acceptance and provenance

Slice 4B prerequisite: **VERIFIED before edits**. Its report ends with
`WOMBO UI V2 SLICE 4B COMPLETE — FUNCTIONAL PROPOSAL REVIEW SCAFFOLD ACCEPTED`.
The reported `bf10fde` resolves to accepted full SHA
**`bf10fde0bfa6ced4fb8ebd99d71b4f88acbb57e4`**. The accepted worktree was clean;
local `feat/wombo-ui-v2` contained that exact head. The baseline was rerun:
**378 tests / 52 suites**, strict TypeScript, unused and privacy green.
Slice 4A availability/create/selection/placement/submit and Slice 4B
replacement/removal/explicit approval/explicit rejection remained green.
There was one Planning owner, one Calendar owner and no duplicate owner.
Package, backend, API and database paths were unchanged.

- Starting SHA: `bf10fde0bfa6ced4fb8ebd99d71b4f88acbb57e4`.
- Branch: `feat/wombo-ui-v2-active-workout-moves`.
- Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-active-workout-moves`.
- Verified implementation SHA: `415fe4af98bab49baf9631e4c9df85e333bd329f`.
- Final delivery SHA: the report-only commit containing this document; resolve
  its full SHA with `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_4C_REPORT.md`.
- Integration target: local `feat/wombo-ui-v2`, fast-forward only to that delivery
  head after verification. No merge, rebase, squash or push.
- Visual status: **PROVISIONAL FUNCTIONAL MOVE SCAFFOLD**.

Root/mobile AGENTS, current roadmap, V2 implementation plan/architecture,
Slice 2A/3A/3B/4A/4B reports, exact V1 request/validate/warning/PATCH lifecycle
and its tests supplied the constraints. The Slice 2A move lifecycle remains
authoritative. No planning, physiological or cross-week rule was added.

## Shared ownership and move entry

`PlanningOwner` still invokes exactly one `usePlanningController` and one
`useCalendarController`. The task consumes existing `requestWorkoutMove`,
`confirmWorkoutMove`, `cancelWorkoutMove` and the shared pending-move state.
Existing internal `applyWorkoutMove` remains the sole PATCH path. There is no
V2 move hook, copied mutation, second revision or second active-plan store.
Snapshot references guard intent provenance; they do not clone domain state.

The smallest entry is the existing **V2 Calendar workout card**, in both
Week/Month agenda presentations. An action appears only when the exact Calendar
workout ID/date matches a scheduled workout in the shared active approved plan.
Pending proposal rows, historical activities, cancelled/completed workouts and
foreign/stale Calendar rows have no move action. Shared-controller eligibility
guards independently protect the action. Pending proposal editing remains the
separate Slice 4B operation. Week and Detail are consumers of the updated plan;
this slice does not add another move entry or Detail implementation.

The Calendar remains mounted under a simple task modal. Calendar mode, anchor,
selection and scroll survive Cancel and success. No Calendar redesign, drag
system, dependency, icon set or decorative schedule presentation was added.

## Exact transaction behavior

| Requirement | Result |
| --- | --- |
| Accessible chooser | Full workout name, full localized current date, seven full dates from the existing plan week, current-date annotation, checked selected-date state, explicit Review move and Cancel. No recommended date and no gesture-only path. |
| Same-week guard | Existing `isDateInWeek` guard retained. Invalid/outside-week input is rejected locally before validation, without clamping or a new rule. |
| Same-date behavior | The chooser disables Review on the current date. Direct shared-controller same-date input retains the existing validate/PATCH behavior; a regression test records that existing semantic. |
| Complete validation | Existing POST `/api/v1/weekly-plans/{plan_id}/validate`, body `{ expected_revision: active_revision, workouts: [{ workout_id, scheduled_date }, ...] }`. Every unchanged workout is included; only the selected exact ID receives the chosen date. |
| No warnings | Existing authoritative PATCH follows validation once. No optimistic date change, fabricated revision, local safety calculation or manual plan reordering. |
| Warnings | The sole shared pending state retains exact workout, target date, all returned warnings and reviewed active snapshot. No automatic PATCH. Existing `warningPresentation` supplies the same safe public display semantics as V1. Unsupported internal data is not rendered. |
| Explicit confirmation | Only Move anyway / Toch verplaatsen calls shared confirmation with the already-reviewed workout, target and revision. A callback from cancelled/consumed/replaced intent cannot bind to a later intent. |
| Cancel / Back | Clear pending intent and return to the same Calendar origin. No validation/PATCH from Cancel, no plan date or revision change. Modal Back uses Cancel. Busy dismissal is blocked during an outstanding mutation. |
| Authoritative PATCH | Existing PATCH `/api/v1/planned-workouts/{exact_workout_id}` with `{ expected_revision: reviewed_active_revision, scheduled_date: exact_target }`. The returned `WeeklyPlan` replaces shared active state; pending intent clears and existing success haptic remains. |
| Stale / rejected / network | Existing safe error handling is retained. No localized-string parsing, automatic replay, force, unconditional write or speculative repair. Validation failures do not PATCH. Failed PATCH does not change the local plan. Failed warned PATCH retains review until Cancel or another explicit action in the same context. A changed authoritative snapshot disables old confirmation; the athlete must inspect the current plan before retrying. No automatic rebind to its revision. |
| Late results | Captured snapshot and owner lifetime checks prevent late validation from installing a warning/PATCH, and prevent a late PATCH acknowledgement from overwriting a newer current plan. |
| Occurrence identity | Layout and PATCH use workout IDs, never template ID alone. Repeated-template/same-day fixtures prove one selected occurrence changes and its sibling keeps its supplied date. |
| Rest coexistence | Returned rest records are retained, including rest plus workout on one date. Rest data never locally authorizes or blocks a move. |

The existing synchronous controller mutation ref blocks repeated requests and
cross-control confirmation before React renders busy. Pending-review identity
also blocks a second validation while a warning is unresolved. Rerenders,
Calendar renders, Detail return, root attempts, preference changes and task
animation do not perform writes. There are no mutation effects; the task uses
`animationType="none"`. Warned flow is validation, explicit decision, exactly
one PATCH; it cannot become automatic PATCH followed by a second confirmed PATCH.

## Calendar, Week, Detail and navigation

The existing Calendar owner now accepts the complete authoritative approved-plan
result through `replaceApprovedPlan(previous, updated)`. It supersedes older
range requests using the existing request counter, replaces affected workout
rows and supplied week rest records within the loaded range, and retains other
weeks. Filtering the union of old and returned IDs handles server revisions
that renew every workout ID, including a concurrent GET that already saw new
IDs. No duplicate Calendar plan state or API client is introduced.

The current loaded range needs no GET when the returned plan supplies the whole
affected week. A different displayed range still uses the existing deduplicated
range read. Latest-request-wins success/failure tests cover old reads resolving
after the move. Calendar Week/Month/selected-date and Detail-return regression
coverage remains green.

Week derives today/next and progress from the existing authoritative mapper.
Fixtures verify its updated date and existing progress without introducing new
progress semantics. Detail opens the exact returned Calendar workout object;
close restores Calendar. Live checks confirmed Week progress stayed 0 of 2 and
the next date followed both server moves.

The chooser's selected workout ID is presentation navigation state only. The
existing unsafe-switch/root lock includes the open chooser, shared busy and
pending warning. V1/V2 controls and root/global-RPE navigation cannot discard or
apply unresolved intent. Cancel/success releases the lock. Existing pending
proposal safety remains separate and unchanged.

## Accessibility and privacy

NL/EN copy uses explicit Training verplaatsen / Move workout, Nieuwe datum /
New date, Verplaatsing controleren / Review move, Annuleren / Cancel and Toch
verplaatsen / Move anyway. Dates include weekday, day, month and year. Radios
announce checked state; current date is identified in both context and choice.
Warning heading/text, busy announcement, errors, disabled confirmation and Cancel
are covered in presentation/boundary tests. Buttons use existing V2 minimum
48 dp targets and naturally growing Text/Card/Screen primitives.

**LIVE:** native emulator text was temporarily set from 1.0 to 2.0. Full current
date and date buttons wrapped; all seven choices and explicit Review/Cancel
remained reachable through the existing scroll. A different target was selected
and cancelled without submission. Screenshots were visually inspected, and
font scale was restored to 1.0. Android configuration recreation remounted the
app and reloaded the same authenticated authoritative plan; it was not treated
as a UI preference/root switch test.

No new UI/log/view-model/accessibility field exposes TSS, planned/realized private
load or selector diagnostics. No full plan object is logged by runtime source.
The existing privacy suite passed; a separate scan of **57 public response,
native state and accessibility XML evidence files** found zero private-load
matches. Evidence observers omit authorization headers/tokens and log only
allowlisted IDs/dates/revisions and request method/path/status.

Physical TalkBack, physical-device ergonomics and release/build/distribution
gates remain open. No physical acceptance or final visual-design acceptance is
claimed. Supplied catalog titles include an existing replacement-character
artifact; this slice retains the supplied name rather than editing catalog data.

## Software verification

Final full mobile suite: **420 tests / 54 suites**, all passed, zero failures,
skips or todo tests. Baseline was 378 / 52: **42 added tests and 2 added suites**.
Final artifacts: `mobile/.runtime/slice4c/accepted-tests.json` and
`accepted-tests.log`.

- New move presentation/boundary, existing V1 move, shared Planning controller:
  complete layout/revision, no-warning and multiple-warning decisions, Cancel,
  Back, rapid double presses, old callbacks, stale validation/PATCH/context,
  network/rejected failures, owner unmount and exact returned state.
- Repeated-template occurrences, same-day siblings, renewed server IDs, returned
  rest coexistence, Week mapper and Calendar cache/range races.
- Slice 4A availability/create/selection/placement/submit and Slice 4B review,
  alternatives/replacement/removal/approve/reject.
- Calendar latest-request-wins/Week/Month/Detail return, Week, Workout Detail
  origin, navigation shell and sole-owner regressions.
- `npm run typecheck`: passed strict TypeScript.
- `npm run check:unused`: passed.
- Privacy tests and public evidence scan: passed.
- Installed TypeScript formatter applied to the four new modules/tests;
  staged and final `git diff --check`: passed. A trailing test-file blank line
  was removed after the suite, with no executable change.

Package/manifests/lockfiles: **NONE changed**. Backend/API/database: **NONE
changed**, confirmed against the accepted SHA. No backend, migration, RLS or
physiology behavior was modified; Python/mypy/pgTAP checks are not new gates for
this mobile-only slice.

## Authenticated emulator evidence

Only `r6-api-r6-staging.up.railway.app` and Supabase **start23-dev** were used.
The existing Android API 35 emulator/development client was reused. Loopback
Metro port **8086**, dev manifest and project root were verified to point to this
Slice 4C worktree with V2 enabled. No build/deployment/session injection/Auth
bypass/direct planning-domain row edits occurred. Native automation used fresh
ADB UI trees and observed labels/bounds after the native computer-use provider
failed to connect. CDP observation was read-only, without interception or invoking
app mutation callbacks.

**LIVE:** normal sign-in; supported onboarding/history/calibration/threshold and
zone approval for the disposable actor; V2 Week availability; draft creation;
two independent Choose actions; automatic placement and explicit proposal submit;
existing V2 proposal review and explicit approval; active plan; Calendar; chooser;
server validation; authoritative moves; Calendar/Week/Detail coherence; Cancel.

| Live item | Exact result |
| --- | --- |
| Draft | `d92a2174-d8db-4685-804e-d5714ea9530a`, normal create/select/select/submit responses 201/200/200/201. |
| Proposal | `90666b99-2854-4867-9a5a-25091db68d05`, explicit approve 200. |
| Active plan | `05b7f9e5-6d59-42a9-b51f-502468e5bc0d`, revision 1, RUN-013 Wednesday 14 October and RUN-010 Saturday 17 October 2026. |
| First move | Exact RUN-013 ID `70ef8656-4c3b-413a-baf0-8de04a92a0e3`, Wednesday 14 to Thursday 15. One validate 200, one PATCH 200; returned active revision 2 and renewed workout IDs. RUN-010 retained Saturday 17. |
| Cancel | Reopened the exact returned RUN-013 in revision 2, selected Monday 12, explicitly cancelled. No additional validate/PATCH, same revision/date, Calendar selection/mode and 572 dp scroll retained; lock cleared. |
| Final source move | Returned revision-2 ID `8260eff6-01db-438b-981f-1534e4312af2`, Thursday 15 to Wednesday 14. One validate 200 and one PATCH 200. Revision 3 returned RUN-013 `0ba96c71-1d9c-4ce1-b6f6-37b018aa4aff` on Wednesday 14 and RUN-010 `3864af70-da9b-4219-8c49-260b95951fde` still Saturday 17. |
| Calendar after | Exact two returned IDs, no duplicates, supplied rest days, pending intent clear, no post-move range GET, selected date/mode and 561.45 dp scroll retained in the final settled flow. |
| Week / Detail | Same sole owners during settled root/Detail transitions; Week next Wednesday 14, progress 0/2; Detail exact Calendar object/new ID/current date; close returns to Calendar. |
| Total move writes | Exactly two validate POSTs and two authoritative PATCHes for two explicit submitted moves. Both chooser Cancel paths added zero writes. |

Both live validations returned no warnings. **FIXTURE/TEST** evidence covers
warning Cancel, explicit warning confirmation exactly once, multiple warnings,
repeated-template identities, stale/concurrent changes, rare failure paths and
rest-plus-workout coexistence. No live warned confirmation is claimed and no
rare warning was manufactured. Public snapshots are `active-before.json`,
`active-after.json`, `final-active.json`; sanitized traces are `network.json` and
`network-before-restart.json` under `mobile/.runtime/slice4c`.

An initial Fast Refresh session hit a native Wombo ANR before move validation.
Waiting did not recover it; the same development client was cold-restarted and
the same authenticated athlete/active plan restored. The subsequent move,
Cancel and final-source flows completed. A later source refresh remounted
development owners while no warning was pending; final settled-flow evidence
was recorded separately. Neither incident is presented as a production device
acceptance or as feature-root-switch identity preservation.

## Functional reference screenshots

These are **FUNCTIONAL REFERENCES**, not final visual designs. Files remain in
the ignored local evidence directory `mobile/.runtime/slice4c/` for later
user-created mockups; no screenshots containing credentials were committed.

| Reference | File |
| --- | --- |
| Active Calendar before | `calendar-before-move.png` |
| Move entry / current context | `move-entry.png` |
| Accessible chooser | `date-chooser.png` |
| Selected target / review action | `selected-target.png` |
| Successful first move | `successful-move-result.png` |
| Cancel target / restored Calendar | `cancel-selected-date.png`, `cancel-state.png` |
| Calendar after final move | `final-calendar-after.png` |
| Week after final move | `final-week-after.png` |
| Detail after final move | `final-detail-after.png` |
| Large text context/actions | `large-text-move.png`, `large-text-actions.png` |
| Warning review | Not available naturally live; explicit warning screen/decisions verified by fixtures. |

## Disposable-athlete cleanup and integration

The original explicitly authorized tagged athlete was accidentally cleaned up
when a noninteractive helper's stdin closed, before emulator testing. Work
stopped for replacement authorization, as required by the user. The user then
explicitly authorized **one replacement dev-athlete**. Its helper retained an
interactive stdin through all live verification. No further athlete was created.

After testing the replacement, normal app Profile sign-out was verified with
`sessionPresent: false`. Owned-tag guards preceded cleanup; sessions were revoked
globally, the replacement Auth user deleted, admin lookup returned **404**, and
**zero matching tagged users remained**. Both original and replacement cleanup
records show created 1 / deleted 1 / global revoke true / 404 / zero remaining:
`first-slice4c-authenticated-cleanup.json` and
`slice4c-authenticated-cleanup.json`. The network observer was stopped; emulator
font scale was restored. No active disposable session remains.

Local `feat/wombo-ui-v2` was verified at the accepted 4B head and an ancestor of
the delivery head, with no checked-out target or dirty target worktree. It is
promoted only by an expected-old-SHA local fast-forward reference update.
The Slice 4C worktree is clean after the report commit. The unrelated root dirty
checkout and accepted 4B worktree remain untouched.

`main` remains `fb56c51d983564c652d83fc15e02b039e9063d3f`, untouched and unpushed.
No branch was pushed. Production was untouched. Planning rules, physiology,
backend/API/database contracts and packages were unchanged. Final user-mockup
visual work and physical acceptance gates remain open.

WOMBO UI V2 SLICE 4C COMPLETE — FUNCTIONAL MOVE SCAFFOLD ACCEPTED
