# Wombo UI V2 Slice 2b - Week / Home

Date: 2026-10-05. **Implemented; software gates green; authenticated emulator
acceptance pending.** Only the first V2 Planning root, with V1 task fallbacks.

## Prerequisite, branch and provenance

Slice 2a was verified before runtime edits:

- Clean committed feat/wombo-ui-v2-planning-controller at exact
  **5200d0ce6fd2d267390f4517ccadba4bea1353e6**.
- Its [report](WOMBO_UI_V2_SLICE_2A_REPORT.md) records accepted V1 extraction
  and authenticated emulator smoke. No repair/reopening of 2a.
- Re-ran the exact parent: **159 tests / 33 suites**, strict TypeScript and
  unused checks passed. Inspected the single provider, resume and Calendar
  helpers, mutation code, state ownership and Slice-1 boundaries.
- Integration did not include 2a: feat/wombo-ui-v2 was
  23243e027b9674308c13d9c946dc03ce90a01c55.
- New clean worktree:
  F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-week.
  Branch feat/wombo-ui-v2-week starts from that exact 2a parent and tracks
  local feat/wombo-ui-v2. No main checkout/reset/stash, tag change or push.
- Read root/mobile instructions, MVP roadmap, all requested UI documents,
  Slice-1/2a reports, September selection decision/final addendum, planning
  ruleset V2 record and workout distribution decision.

Runtime head: a079ab8. Final slice SHA is the documentation commit containing
this report, obtainable with git rev-parse feat/wombo-ui-v2-week; its full SHA
is recorded in the final user-facing report.

## Architecture and shared owner

Existing /planning route -> PlanningScreen container -> one PlanningFlowProvider
-> PlanningBoundary -> V1 PlanningPresentation OR pure V2 WeekScreen, with
one unchanged WorkoutDetailBoundary above presentation selection.

Only the provider invokes usePlanningController. Week and V1 consume the same
context/actions. No hidden dual roots, V2 controller, copied API operation,
second session/storage, or independent revision/draft owner. Calendar owner
and its race protection/loading remain unchanged.

The shared owner's only extensions are read metadata and the authoritative
active snapshot required by the approved architecture:

- resumeState reports loading/ready/failed. Draft-first restore order,
  storage reference clearing, catches and mounted guard stay unchanged.
  Existing typed 404 status distinguishes an unavailable stored reference;
  no message-string parsing or transport change.
- When a non-active plan has a known active revision, the same owner reads
  getWeeklyPlan(accessToken, plan.id, plan.active_revision) once for that
  context. Identity/revision/active state are verified before display.
- An already active plan supplies its schedule directly without another GET.
  Known matching active data survives a failed read; late reads cannot cross
  unmount/identity reset. No pending rows are merged into the active schedule.
- Dependencies are token and known plan/revision/active state, never UI
  preference, root/task rerender or detail. No discovery endpoint, polling,
  speculative recovery, new retry, or mutation lock rewrite.

The original plan and action callbacks still own V1 mutation preconditions.
Active snapshot is public read context, not a second planning owner.

## Week hierarchy, mapper and states

WeekScreen is callback-only presentation: no API, Supabase, SecureStore,
controller or physiology imports. weekHomeViewModel is deterministic with
explicit today; it allowlists existing public summary fields, preserves planned
occurrence IDs and same-date source order without claiming execution order.

Hierarchy: locale-formatted Monday-Sunday range and known state; one forest
focus session with independently reachable siblings; literal progress; known
attention; flat supporting actions. No full seven-day calendar duplication.
Existing V2 tokens/system typography/Card/Button/Divider/SportIndicator and
restrained ContentTransition are reused. Added only WeekContext, NextSession,
AttentionRow and static Skeleton.

| State | Presentation / next action |
| --- | --- |
| No loaded plan | Current display week; V1 preparation entry without creating anything |
| Resumed/collecting draft | Exact draft/occurrence; continue choosing |
| Placement incomplete | Dates still to confirm; same V1 automatic/manual placement |
| Pending-only | Review entry; proposal rows never shown as scheduled or progress |
| Active | Authoritative identified active schedule; today/next known date |
| Active plus pending | Active sessions/progress, separate pending review/warnings |
| Approved rest-only | Supplied planned/restriction rest reason; no invented sessions |
| Rejected/expired | Localized state and existing V1 planning entry |
| Superseded/unavailable | V1 review; no invented active state or recovery |
| Initial loading | Static inaccessible skeleton and loading text; no no-plan claim |
| Failed read | Inline uncertainty; known context retained; no invented retry |
| No session today/future | Next known date or truthful no-upcoming-session statement |

Measures remain independent. Distance-only swim has no estimated duration.
Existing RPE-description suppression remains; execution detail retains RPE.
Progress requires identified active revision, counts completed planned
occurrences / non-cancelled planned occurrences only, and omits unknown counts.
No activity matching, readiness score, load calculation or proposal-validity
inference.

Attention uses actual draft, pending proposal and warnings only. At most two
rows initially; more remain reachable. Main-action facts are not repeated.
Warnings lead to their unchanged V1 explanation. No invented zone/feedback/
check-in due count; existing global RPE reminder stays unchanged.

Display context uses loaded active/plan/draft week or current local Monday,
separate from unchanged next-Monday generation input. Previous/next discovery
controls are omitted because the owner has no supported discovery action.
Existing local-noon date helpers retain Monday-Sunday semantics; actual today
uses the loaded plan's confirmed timezone, otherwise existing device-date
convention. No invented schedule time.

## V1 tasks, detail and version seam

- Prepare opens V1 availability while retaining the active plan; entry does not
  create/refetch/clear anything. Generate still binds exact active revision.
  An existing draft preparation entry resumes it instead of clearing it.
- Selection, placement, alternatives, proposal review, approve/reject and moves
  remain V1; review consumes the exact loaded proposal/revision.
- View week opens unchanged V1 Calendar. Its range effect remains the only
  read trigger, with independent loading and latest-request protection.
- Goal entry opens existing V1 achievement confirmation; the link never writes.
  Profile, activities, check-in and zones use existing callbacks/routes.
- Visible Back to Week and Android back return after safe settle without
  discarding forms/IDs or committing. Week scroll is retained.
- Selected exact workout object is above switched bodies. Accepted
  WorkoutDetailBoundary remains unchanged; comparison cannot replace its
  Week/Calendar origin, and close/back retains that origin.
- Registry enables only workoutDetail and week. Calendar/Activities/tasks stay
  V1; non-development is still forced V1. Root selection honors the registry.
- Existing busy, pending-move and editor-loading state block unsafe root
  switching/task dismissal. Detail comparison keeps the origin pinned.
  Requested preference can change in a task without migrating its V1 body.

V1 style block and entire SwipeDraftPanel are byte-identical to the 2a parent.
PlanningScreen is **1,901 -> 1,978 lines**, adding the small presentation host.
V2 WeekScreen is 68 lines; mapper is 54. No V1 styling, gestures, labels, move
logic or source execution text redesign. Detail source and route files unchanged.

## Contracts, resume, duplicates and privacy

All 13 core action initializers are token-identical to exact 2a parent:
run, three toggles, generate, approve, reject, openDeck, transitionDraft,
placeDraftWorkout, submitDraft, applyWorkoutMove, requestWorkoutMove.

Endpoint/payload/order/revision/retry/idempotency semantics stay unchanged:
create exact dates/week/injuries/opt-ins/active binding; accept/pass exact
template AND occurrence; undo/reset exact revision; placement occurrence/date;
submit revision/mode and storage sequencing; approve proposal/base then GET;
reject proposal then GET reviewed revision; alternatives/options exact
revision/proposal; full-layout validation -> warning/cancel/confirm ->
authoritative move. No server rule was implemented in mobile.

Shared tests preserve repeats, accepted/passed state, placement, proposal/active
identity, stale errors, warnings, injuries/consent, mutation busy, move actions,
alternatives lifetime, token rotation and identity reset.
Resume keys/accessibility and baseline sign-out clearing semantics are unchanged.
No new persistence or access-token-keyed long-lived state.

One-owner/nesting/rerender tests prove one restore per reference and one
known-active read per context; no bootstrap/plan read on root/detail switch;
no eager Calendar/alternatives read in Week; one read per actual Calendar range;
no transition/submit/approve retry caused by rerender. Latest pending read and
known-active-revision read are distinct intentional snapshots, not duplicates.
Existing control-based mutation locking and its programmatic-call limitation
are retained.

Privacy: recursive source and poison-field output tests passed. No TSS/private
planned/realized load, selector diagnostic or hidden physiology field is copied
into Week state, text, accessibility or logs. No logger introduced. Mapper
allowlists summaries instead of spreading responses.

## Software verification

Final runtime source a079ab8:

| Gate | Result |
| --- | --- |
| Full mobile | **190 tests / 36 suites passed**, zero snapshots |
| New Week mapper | 18 cases covering states, identity, local dates, progress, distance-only, poison fields |
| Week component | 5 cases: NL/EN siblings, attention access, hidden skeleton/error, busy controls |
| Week boundary | 6 cases: V1 entry, single root, exact draft, active+pending/approve/locks, Calendar/Detail/scroll, goal confirmation |
| Shared owner | Existing 29 plus 2 read-lifecycle cases passed |
| Existing V1 Planning | Controller, warning, detail-origin regressions passed |
| Slice-1 Detail | Original boundary/detail/adapter/motion/registry/navigation suites passed |
| TypeScript | npm run typecheck passed |
| Unused | npm run check:unused passed |
| Privacy | Recursive source and output checks passed |
| Formatting | Installed TypeScript formatter on new files; git diff --check passed |
| Mutation parity | All 13 initializers unchanged |
| Protected scope | No API/DTO/backend/database/package/route/native/accepted-detail diff |

Explicitly superseded test expectations: registry includes Week; active plus
pending needs one distinct known-active GET; V1 mutation tests select V1 instead
of assuming V2 only changes Detail. Exact mutation assertions remain, and new
tests verify the implemented root switch. No skipped/weakened mutation test.

No new mobile lint tool/config/script; no backend suite rerun because no backend
or API changes. Node modules reused through an ignored local junction.

## Emulator attempt, screenshots and cleanup

**Authenticated Week acceptance pending. No successful Week screenshot, real
proposal/approval, Week Detail or Calendar smoke is claimed for this slice.**
User explicitly requested continuing 2b if emulator testing failed.

- Existing emulator-5554, API 35 x86_64, SDK-57 development client.
- Hung ADB server/transport recovered by restart/reconnect without data reset.
- Normal Expo Router bundle from this isolated worktree verified in manifest,
  loopback **127.0.0.1:8082 only**. No LAN, rebuild, publishing or deployment.
- Exactly one tagged disposable start23-dev athlete. Existing guarded helper
  completed supported profile/history/calibration, explicit threshold/zone
  confirmation and onboarding APIs. No direct domain/database writes.
- Credentials stayed in helper memory for normal sign-in; no session injection.
  Auth was initially visible, then its content became invisible before sign-in
  completed. Tree showed only development Tools. Auth/FadeInView source unchanged;
  symptom resembles the earlier documented V1 fade issue, but cause is unproven.
- Cold entry with/without read-only observer and emulator reduced-motion
  diagnostic did not restore the form. Original animation setting (unset)
  restored. No unrelated Auth/motion repair.
- Helper failed closed, globally revoked sessions, deleted its owned user,
  verified Auth lookup **404** and **zero tagged users**. One created/one deleted.
- Sanitized observer recorded zero staging app API requests during failed entry;
  no tokens/headers, interception or source instrumentation.
- Observer/task Metro stopped and task forwarding removed; prior server and
  emulator retained.

Ignored local evidence in mobile/.runtime:
prerequisite-tests.json, slice2b-tests-final.json, action-token-parity.json,
source-preservation.json, metro-provenance.json, slice2b-authenticated-network.json,
slice2b-authenticated-actor-marker.json, slice2b-authenticated-cleanup.json,
slice2b-signin.png/xml, slice2b-auth-fade-unavailable.png/xml.
Failure capture is not labeled successful no-plan Week. Requested Week
no-plan/active/attention/detail/return screenshots remain pending.

The [Supabase skill](C:/Users/Adria/.codex/plugins/cache/plugins-cli/supabase/0.1.12/skills/supabase/SKILL.md)
was used for the disposable lifecycle; admin operations checked against
[createUser](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
and [deleteUser](https://supabase.com/docs/reference/javascript/auth-admin-deleteuser).
Only staging API and start23-dev isfumhgqphieoayqahjv touched. No production access.

## Files, commits and integration

Created:

- mobile/src/ui-v2/utils/weekHomeViewModel.ts and .test.ts
- mobile/src/ui-v2/components/WeekContext.tsx
- mobile/src/ui-v2/components/NextSession.tsx
- mobile/src/ui-v2/components/AttentionRow.tsx
- mobile/src/ui-v2/primitives/Skeleton.tsx
- mobile/src/ui-v2/screens/WeekScreen.tsx and .test.tsx
- mobile/src/screens/PlanningWeekBoundary.test.tsx
- docs/ui/WOMBO_UI_V2_SLICE_2B_REPORT.md

Modified existing:

- mobile/src/features/planning/usePlanningController.ts
- mobile/src/features/planning/PlanningFlowProvider.test.tsx
- mobile/src/screens/PlanningScreen.tsx
- mobile/src/screens/PlanningControllerBoundary.test.tsx
- mobile/src/i18n/LanguageProvider.tsx
- mobile/src/ui/UiVersionControl.tsx
- mobile/src/ui/uiVersion.ts and .test.ts

Local commits:

1. f8a565e - authoritative Week mapper/tests.
2. 1d5466e - localized Week presentation/components/accessibility tests.
3. 6e98438 - single-owner boundary, known-active read and integration regressions.
4. a079ab8 - V1 goal confirmation access and registry-aware root selection.
5. Documentation commit containing this report.

Packages **NONE**. Backend/API/DTO/database/schema/physiology code **NONE**.
Only the deleted nonproduction fixture used supported API data writes.

Integration not promoted: authenticated Week acceptance remains pending, so
the fully-green promotion gate was not claimed. Local feat/wombo-ui-v2 remains
23243e027b9674308c13d9c946dc03ce90a01c55.
Main remains fb56c51d983564c652d83fc15e02b039e9063d3f; V1 tag object remains
d39bfcd2cf6dcc17aca231502ac4ab4e46c0465a. Original dirty workspace, coach edit,
Garmin/privacy/PDF documents untouched. Nothing pushed; production untouched.
No historical commit squash/report rewrite.

## Remaining gates and risks

Recover normal Auth in the existing client, then run real Week no-plan -> V1
preparation/selection/proposal/approval -> Week active -> Detail -> Week ->
V1 Calendar -> Week; capture requested images and real active+pending if practical.
Runtime duplicate-read and actual hierarchy review remain in that gate.

Physical gates remain open: Activity/HR/RPE, delayed retry, Month/Week,
drag/drop/performance, Workout Detail, TalkBack/focus, reduced motion, large text
and physical insets/layout. No physical acceptance claimed.

Existing risks retained: provider stays under current Planning route until
authorized navigation host slice; token-refresh bootstrap reads; V1 editor
component-lifetime reads; control-based mutation locks. No arbitrary week
discovery; today updates on normal rerender without new timer.

Slice 1 remains **EMULATOR ACCEPTED - PHYSICAL DEVICE GATES REMAIN**, all its
software tests green. Slice 2a stays accepted and was not reopened.

WOMBO UI V2 SLICE 2B COMPLETE — EMULATOR ACCEPTANCE PENDING
