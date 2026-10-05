# Wombo UI V2 Slice 5A report

## Acceptance and provenance

Slice 4C prerequisite: **VERIFIED before edits**. Its accepted report ends with
`WOMBO UI V2 SLICE 4C COMPLETE — FUNCTIONAL MOVE SCAFFOLD ACCEPTED`.
The actual report delivery commit resolved to full SHA
**`7d0b6d6bd8c2c1648b1c7199130801431537e09a`**; no older implementation SHA
was substituted. The accepted worktree was clean, and local `feat/wombo-ui-v2`
pointed to that exact head. Fresh prerequisite verification passed
**420 tests / 54 suites**, strict TypeScript, unused-code and recursive privacy.
Slice 4A creation, Slice 4B proposal review/approval/rejection, Slice 4C active
move lifecycle, navigation, Week, Calendar and Detail remained green. There was
one Planning owner and one Calendar owner. Protected backend/API/database/package
paths were unchanged in accepted 4C.

- Starting full SHA: `7d0b6d6bd8c2c1648b1c7199130801431537e09a`.
- Branch: `feat/wombo-ui-v2-activity-controller`.
- Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-activity-controller`.
- Final verified implementation SHA: `f68fae89427417d870de5a1147bae2189d3c2be5`.
- Final delivery SHA: the report-only commit containing this document. Resolve
  it exactly with `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_5A_REPORT.md`.
- Local integration: fast-forward `feat/wombo-ui-v2` from the accepted 4C SHA to
  this delivery head after clean-tree and ancestor checks; no merge/rebase/squash.
- Visual status: **V1 PRESERVED / NO V2 ACTIVITIES YET**.

Root/mobile AGENTS, current MVP roadmap, V2 implementation plan, architecture,
dependency decisions and Slice 2A/3B/4A/4B/4C reports were read. Current V1
ActivityScreen, route/shell reminder, API client/DTOs, RPE recovery helper and
their tests supplied the preservation boundary. No physiological decision,
planning rule or API contract was introduced.

## Pre-edit responsibility classification

This classification was recorded before implementation in local ignored
`mobile/.runtime/slice5a/pre-edit-audit.md`.

| Class | Existing responsibility | Boundary after extraction |
| --- | --- | --- |
| A — shared activity flow | Busy/error, confirmed timezone, create/match/save actions, stable UUID, created activity ID, synchronous create and per-activity RPE locks | One shared authenticated Activity owner |
| B — V1 presentation | JSX, styles, localized labels/results, FlashList, keyboard/safe-area presentation, measurement notices, pace display, suggested-match display and current-week correction eligibility | Remain in V1 unchanged |
| C — creation/form | Exact selected workout/external record, sport, ISO start, duration, distance, existing validation and payload | Owner retains unresolved form draft/key; small pure input helper preserves validation |
| D — feedback/RPE | Awaiting-RPE records, created ID preferred then first pending in server order, exact-ID HR draft, existing feedback transaction and key rotation | Shared owner; correction-open toggle remains V1 |
| E — list/history | Four concurrent reads, server ordering, local date range, scheduled/planned filters, timezone error after publishing rows | Shared lazy full read; no new pagination, sorting or grouping |
| F — navigation/modal/detail | Back/profile/sign-out callbacks, local correction-open state, busy callback into shell | Existing routes and V1 presentation retain navigation |
| G — global reminder | Independent shell pending endpoint read/count, per pathname/session; unused screen callback in current router path | Same owner owns pending read/state; reminder derives count and retains route/token triggers |
| H — protected behavior | API/DTOs, ambiguous-create key reuse, completed-POST refresh-only retry, one inline pending feedback form/create block, RPE helper typed recovery, HR validation, pace utilities and canonical source records | Preserved; no automatic feedback, speculative retry or private calculation |

The old screen had no read-race/lifetime guard. The old shell cancelled its
pending read on effect cleanup. Owner liveness and pending-read sequencing now
prevent old identity/older reminder results from publishing into current state.
This supplies the required lifetime protection without changing server recovery.

## Ownership, extracted responsibilities and files

Before: ActivityScreen owned domain/form/read/feedback state and mutations;
authenticated shell separately owned pending-RPE count/read. The legacy App also
had its own reminder read and received the screen count callback.

After: `ActivityOwner` invokes `useActivityController` once. V1 ActivityScreen
consumes `useActivityFlow`; the reminder consumes the same `pendingRpe` state.
Both supported app entry implementations mount the same provider abstraction,
never simultaneously two owners. Nested providers fail before creating another
controller. The package entry remains the existing Expo Router entry.

Created:

- `mobile/src/features/activities/useActivityController.ts`: shared reads, draft,
  logical create attempt, pending feedback, HR draft and existing actions.
- `mobile/src/features/activities/ActivityFlowProvider.tsx`: single context owner,
  authenticated identity lifetime and consumer seam.
- `mobile/src/features/activities/activityCreateInput.ts`: unchanged UUID
  generation and existing form-validation/payload construction, using the
  existing client parameter type rather than a new DTO.
- `mobile/src/features/activities/ActivityFlowProvider.test.tsx`: 36 focused tests.
- `mobile/src/features/activities/activities.test-fixtures.ts`: public DTO fixtures.

Modified:

- `mobile/src/screens/ActivityScreen.tsx`: consume owner and request lazy entry load.
- `mobile/app/(authenticated)/(training)/activities.tsx`: remove obsolete token prop.
- `mobile/app/(authenticated)/_layout.tsx`: authenticated provider and shared reminder.
- `mobile/App.tsx`: wire legacy entry to the same owner/reminder abstraction.
- `mobile/src/screens/ActivityScreen.regression.test.tsx`: mechanical provider setup;
  original V1 behavioral assertions retained.
- `mobile/src/navigation/TrainingNavigation.test.tsx`: three additional real-shell
  ownership/reminder/identity regressions.

V1 intentionally retains every render/style/label, correction-open toggle,
read-only correction eligibility and suggested matching presentation, formatting,
list implementation, animation and route callbacks. The complete ActivityScreen
render-and-styles tail compares identically to the accepted 4C Git blob after
normalizing line endings. Existing pace utilities/imports were not duplicated or
changed. There is no V2 Activities implementation or registry change.

## Provider lifetime and reads

The provider mounts only after authenticated loading/configuration/session
guards, keyed by authenticated `session.user.id`. Access-token rotation is a
prop update, not the owner key. It sits outside TrainingFlowHost's readiness
transition so reparenting the reminder does not recreate Activity state.
Planning/Calendar ownership was not relocated. Unauthenticated Auth and onboarding
retain their existing flow; full Activity/history/Calendar reads remain lazy
until Activities is entered. The existing authenticated shell reminder read
continues where it previously occurred.

Initial full load preserves the concurrent calls and existing argument/order
semantics: `listActivities(token)`, Calendar from local today minus 14 days to
plus 14 days, `getOnboarding(token)`, and `listPlannedExternalActivities(token)`.
Server activity order is retained. Calendar records are filtered only to
`scheduled`; external records only to `planned`. Rows/pending state are published
before the existing confirmed-timezone check, preserving partial-state/error
ordering. No range, provenance, pagination or grouping was invented.

The first Activity entry initializes the default actual-start time, matching
the original screen-entry timing rather than earlier shell authentication.
Later entries retain the same draft. Successful history is retained across
presentation mounts, and concurrent entry/full-refresh requests share one
in-flight read. Mutation refresh uses the same four reads. Failed initial load
retains the existing safe error and supports another entry/action attempt; no
background or speculative retry was introduced.

The canonical public activity source remains `canonical_summary`; imported and
manual records pass through the existing list/RPE API and available metadata.
No provider fields, Garmin flow or alternate ingestion pipeline were invented.

## Creation, idempotency and feedback contracts

| Operation | Preserved contract and state order |
| --- | --- |
| Create | POST `/api/v1/activities`, existing `Idempotency-Key`; exact optional selected workout/external ID, discipline, ISO started_at, confirmed timezone, duration string/null and optional integer distance. Existing date/duration/distance/timezone errors remain unchanged. |
| Logical key | Original UUID algorithm runs for owner state initialization; the key belongs to the unresolved attempt. Rerender, presentation return, token refresh and ambiguous transport retry reuse it. No random key per press. |
| Create lock | Synchronous ref rejects a second press before a busy render. Pending required feedback blocks a new create in the owner and existing disabled V1 control. |
| POST success | Record exact returned created ID, clear selections, reset actual-start time, then existing full read. No automatic RPE, optimistic list record or fabricated identity. |
| POST succeeded / refresh failed | Retain created ID; the next explicit save only refreshes, never repeats POST. This existing subtle recovery was preserved. |
| Pending feedback | One shared pending collection; exact created ID wins, otherwise first pending record in server order. Only one inline V1 form appears. Draft HR is keyed by exact activity ID. Navigation does not discard it. |
| RPE | Existing `submitActivityRpeWithRefresh` receives the exact existing activity snapshot, selected RPE and optional integer HR 20–260. PUT `/api/v1/activities/{id}/rpe` retains rpe, optional average_heart_rate_bpm and optional expected_current_rpe. Scale/control/correction eligibility remain unchanged. |
| Feedback success | After helper authoritative success, clear created ID/rotate key only for that created activity, clear its HR draft, then full read. Pending display clears from authoritative read. |
| Feedback failure | Retain pending identity, HR draft and unresolved key. A second save is an explicit retry; no rerender effect retries a mutation. |
| Helper success / refresh failed | Preserve original order: created ID/key and HR changes already occurred, while previously displayed rows/pending remain until successful refresh. Extraction does not invent recovery for this existing state. |
| Match | Existing PUT `/api/v1/activities/{id}/planned-workout-match`, exact planned_workout_id, then the original full refresh. No automatic matching or changed matching rule. |

The API client and DTOs are untouched. Typed conflict/retryable handling,
authoritative getActivity refresh, already-stored feedback detection, stale RPE
rejection and the helper's existing conditional retry remain exactly in that
client. “One mutation” assertions concern one controller invocation per press;
they do not remove a legitimate existing client recovery retry. NL/EN error
strings are never parsed for logic. No raw object logging was added.

## Reminder, duplicate effects and identity reset

The visible reminder JSX/styles/action/copy are unchanged. Its count is
`pendingRpe.length` from the owner, not a second count state. The shell keeps
pathname/token refresh triggers through the existing pending endpoint. A
remount for the same path/token is not a second event; same-token pending reads
coalesce. A concurrent full read supplies pending state instead of another
pending GET. A sequence guard prevents older reminder responses from undoing
the post-mutation pending result.

Create and RPE writes run only from existing explicit actions, with synchronous
in-flight refs. There are no mutation effects. Tests prove no repeated create,
feedback invocation or full refresh from rapid press, rerender, navigation or
owner token update. Full history mounts coalesce/retain data. Real shell tests
exercise Week → Activities → Calendar → Activities, UI preference changes,
shared reminder updates and one stable Activity/Planning/Calendar owner.

Authenticated identity replacement remounts an empty Activity owner; sign-out
unmounts it. Old responses cannot publish, and saved old callbacks cannot begin
new API work. Token refresh retains draft, pending identity and logical attempt
while subsequent actions use the latest token. The owner has no UI-version
dependency and is located under `features/activities`, outside `ui-v2`.

## Software verification and privacy

Final verified implementation `f68fae89427417d870de5a1147bae2189d3c2be5`:

| Gate | Result |
| --- | --- |
| Full mobile suite | **459 tests / 55 suites, all passed**, up from accepted 4C **420 / 54**: 36 new owner tests and 3 new shell tests |
| Strict TypeScript | `npm run typecheck` passed |
| Unused code | `npm run check:unused` passed |
| Recursive privacy | Existing mobile source privacy test passed in full suite; all five new source/test/fixture files and 34 public emulator JSON/XML evidence files independently scanned clean |
| V1 presentation parity | ActivityScreen render-and-styles tail identical to accepted 4C |
| Formatting/diff | TypeScript formatting applied to new files; `git diff --check` and exact-path staged checks passed |
| Protected changes | No backend, database/Supabase, API/DTO, package/lock, UI registry or V2 UI changes |
| Owner audit | One production Activity hook invocation; existing sole Planning/Calendar invocations unchanged; live counts also one each |

Focused coverage includes initial lazy load, successful ordered reads, read
failure/timezone partial publication, creation validation/success/failure,
ambiguous key reuse, POST-success refresh failure, double press/rerender,
created-ID preference, pending-create block, planned/external identity, swim
distance-only input, feedback success/failure/retry, exact HR/RPE/snapshot,
feedback-success refresh failure, stored correction precondition, pending
endpoint coalescing/race/failure, first-entry date, token/identity/sign-out and
nested-owner prevention.

Existing V1 ActivityScreen regression (3), Activity measurement presentation (2),
RpeChoiceList (1), authenticated layout (3), client feedback recovery and all
navigation tests remained green. PlanningFlowProvider (76), active move boundary
(10), creation boundary (14), proposal boundary (12), Calendar controller (7),
Calendar screen (10), Week and Workout Detail suites passed unchanged. These
include 4A availability/create/selection/placement/submit, 4B review/alternatives/
replacement/removal/approve/reject, and 4C validation/warning/cancel/confirm/
stale/occurrence/Calendar updates. Calendar request-race, mode/detail return and
root shell regressions remain intact.

No new owner, tests, fixtures, UI labels or logs expose private load, server-only
physiology or tokens. Public DTOs and existing safe errors remain the boundary.
Read-only evidence observers recorded method/path/status and allowlisted state;
they did not intercept requests or log raw API objects/credentials. Public activity
evidence was minimized to identity/status/source/RPE/HR fields; network traces
retain no response bodies. Secrets,
environment files, generated credentials, screenshots and runtime helpers were
not committed. No backend suite was run for this mobile-only extraction.

## Authenticated emulator smoke — LIVE evidence

Reused running Android emulator `emulator-5554`, API 35, development client
`com.adrivdbs.wombo`. Dedicated Metro at loopback port 8087 served this exact 5A
worktree with V2 root preference; Activities remained the existing V1 screen.
Development native computer-use transport was unavailable, so native ADB input,
fresh UI trees/screenshots and read-only Hermes observations supplied the smoke.

One authorized tagged disposable **start23-dev** athlete was created, using only
`https://r6-api-r6-staging.up.railway.app` and the start23-dev Supabase project.
Normal Auth/password sign-in, supported profile/history/calibration/threshold/
zone confirmation and onboarding were used. No token/session injection or direct
domain DB writes. No second athlete was created.

An initial cross-worktree Metro transform-cache problem was identified before
Activity mutations: the manifest correctly named 5A but route source maps still
referenced an older navigation worktree. Only the task's Metro was restarted
with `--clear`; final route source maps named this 5A worktree and contained its
authenticated Activity provider. This was runtime cache recovery, not a source,
dependency or app-contract change.

Verified live:

1. Open V1 Activities and existing canonical activity list. Initial required
   feedback produced the existing global reminder and one inline RPE form;
   native create control was disabled. Explicit RPE 4 saved that initial record.
2. Save a manual 45-minute run, 5000 m: one POST 201, exact returned pending ID,
   one full refresh, no automatic feedback on creation.
3. During automation scrolling after that first create, a swipe touched the
   existing RPE 7 choice and saved feedback. This was unintended native test
   input, disclosed during the run; it is not evidence of an automatic save or
   an intentionally selected RPE. Controls/source were unchanged. The flow was
   repeated with a new activity for the **same** authorized athlete, using the
   blank margin for scrolling.
4. Repeat manual create: one POST 201 and one full refresh. Pending state stayed
   on the exact new activity after a safe scroll. Enter HR 151; switch Activities
   → Week → Calendar → Activities. Same owner, pending ID, duration/distance and
   HR draft survived; no full history reread solely from these switches. The
   existing per-root reminder refresh remained (three pending GETs), plus the
   Calendar root's own range read.
5. Explicitly tap RPE 4: one PUT 200 and one normal full refresh. Authenticated
   public response verified exact activity ID, **RPE 4, HR 151, complete**. Pending
   state/form/reminder cleared; owner references remained stable.
6. After the final first-entry date preservation edit, cold-open the final
   candidate with the same normal Auth session. First Activity entry made exactly
   one each of the four existing GETs, all 200. All three stored records were
   present. Repeat Week → Calendar → Activities: one owner each and retained
   history/default start value. Normal reminder GETs did not recreate history.
7. Sign out through Profile/Afmelden. Auth session became absent and all three
   authenticated owners unmounted.

Across the mutation smoke, there were two manual POSTs and three RPE PUTs: initial
fixture feedback, unintended test-input feedback, and the explicit repeated flow.
Each affected its own exact activity once. The post-save development hot refresh
following the final timestamp edit produced additional read-only initialization
requests; these are distinguished from action refreshes in the evidence. The
final cold-run trace separately proves one full load and no duplicate mutation.

Live evidence proves the normal create/pending/block/save/reminder/navigation
flow. Fixtures prove ambiguous transport, double press, specific failure/stale
responses, repeated callback/rerender timing and token/identity replacement.
Those rare states were not manufactured against staging.

## Evidence and disposable-athlete cleanup

Local ignored evidence is under `mobile/.runtime/slice5a/`:

- `accepted-tests.json` / `.log`, `typecheck-final.log`, `unused-final.log` and
  `final-audit.json`: final software/privacy/parity gates.
- `metro-provenance.json`, `route-provenance-final.json`: correct final Metro/routes.
- `network-flow.json`: live mutation trace; `network.json`: final cold-run read trace.
- `explicit-created-before-input-state.json`, `explicit-pending-after-scroll-state.json`,
  `pending-week-state.json`, `pending-calendar-state.json`, `pending-return-state.json`:
  exact pending identity, retained state and stable owners.
- `explicit-feedback-saved.json` and `explicit-feedback-saved-state.json`:
  authoritative RPE/HR result and cleared pending state.
- `final-cold-week-state.json`, `final-entry-state.json`, `final-return-state.json`,
  `final-signout-state.json`: lazy entry/default date, final owner/root state and reset.
- Functional V1 screenshots: `v1-activities-initial.png`,
  `pending-create-blocked.png`, `explicit-pending-rpe.png`,
  `explicit-feedback-saved.png`, `final-v1-activities.png`, `signed-out.png`.
  These are functional references, not final visual designs. Final Activities
  and explicit pending feedback captures were visually inspected.

Cleanup completed **after** all authenticated verification: normal app sign-out,
global session revocation, ownership-guarded deletion of only this disposable
athlete, admin lookup **404**, **zero matching tagged users**. Local
`slice5a-authenticated-cleanup.json` records created_count 1, deleted_count 1,
sessions_revoked true, admin_get_status 404 and remaining_own_tagged_users 0.
No disposable account remains.

## Integration and remaining physical gates

The isolated implementation worktree was clean after implementation commits.
The local target remained the exact accepted 4C head and was verified an ancestor
of the final 5A delivery head; promotion is a guarded local fast-forward only.
The accepted 4C worktree stayed clean. Exact-path staging was used for every
commit. No reset, stash, tag alteration or unrelated work was included.

Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`; the original root branch
and its unrelated dirty coach/Garmin/privacy/PDF/config work were untouched.
No push, deployment or production operation occurred. Packages **NONE**;
backend/API/database changes **NONE**.

Physical device/TalkBack, release-client and later visual acceptance gates remain
open. No physical accessibility acceptance is claimed. Slice 5B UI and art
direction remain future work; 5A intentionally preserves V1 presentation.

WOMBO UI V2 SLICE 5A COMPLETE — V1 ACTIVITY BEHAVIOR PRESERVED
