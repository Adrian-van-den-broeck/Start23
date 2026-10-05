# Wombo UI V2 Slice 4A — planning creation

Date: 2026-10-05. Visual status: **PROVISIONAL FUNCTIONAL PLANNING SCAFFOLD**.
Availability, candidate selection and placement are implemented. Submission ends
at a pending proposal on V2 Week. Final visual design awaits user mockups.

## Prerequisite, branch and provenance

Before editing, resolved accepted Slice 3B `30a7b6e` to
**`30a7b6e60697844635f2b58b5fc1a1dab4ae289d`**. Read its report and verified its
closing acceptance marker, authenticated emulator result, one shared Planning
owner and one Calendar owner. Reran **289 tests / 46 suites**, strict TypeScript,
unused code and recursive privacy checks; diff checks passed. The accepted
starting worktree was clean. Local `feat/wombo-ui-v2` matched the exact accepted
head. Main and production were untouched. Provisional visuals did not block work.

Read root/mobile AGENTS, current MVP roadmap, V2 implementation plan and
architecture, Slice 2A/2B/3A/3B reports, and the referenced latest Joren
workout-selection addendum and ruleset documentation. Existing V2 specifications
supplied information hierarchy only.

- Branch: `feat/wombo-ui-v2-planning-creation`.
- Isolated worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-planning-creation`.
- Starting full SHA: `30a7b6e60697844635f2b58b5fc1a1dab4ae289d`.
- Runtime implementation SHA: `efb1ffa0e5c45676a94625796cb165947fb5df21`.
- Final verified source SHA, including a trailing-blank-line correction:
  `d804905150c1075903d8c75cd1fa3a6300c6615c`.
- Final delivery SHA is the report-only commit containing this document:
  `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_4A_REPORT.md`.

## Architecture and exact behavior

`PlanningBoundary` selects three controlled V2 task presentations:
`AvailabilityScreen`, `SelectionScreen`, `PlacementScreen`. Registry capability
`planningCreation` enables only this slice; broad Planning remains V1.
`PlanningPresentationProvider` stores only task navigation, selection/placement
step and automatic/manual display mode. These are presentation choices.
All domain state and actions come from the retained Slice 2A `PlanningFlowProvider`.
No V2 planning hook, second draft, copied revision or local selection/placement
store is introduced. One `usePlanningController` invocation and one Calendar
controller invocation remain inside the sole `PlanningOwner`. Provider nesting
guards, router identity tests and native settled snapshots verify singular owners.

| Required behavior | Result |
| --- | --- |
| Availability | Monday through Sunday; same default selected offsets, exact `week_start`, existing date parser, explicit selected dates, reuse flag, confirmed injuries and eligible cross-training opt-ins. No session-count or physiological advice added. |
| Create contract | Existing `POST /api/v1/weekly-plans/swipe-drafts`: `week_start`, either `available_dates` or `reuse_previous_week: true`, `confirmed_injuries`, `cross_training_opt_ins`; existing active binding `plan_id` and `expected_base_revision` retained. |
| Candidate | Exact template ID/key/version and occurrence ID copied from the authoritative candidate. Source name, sport, supplied duration and distance, intensity and existing safely filtered public description only. |
| Choose / Pass | Existing transition with exact draft ID/revision plus candidate template and occurrence IDs. Both are explicit accessible buttons. |
| Undo / Reset passed | Existing actions and revision semantics; no candidate identity added where the contract does not require it. Server `can_undo`, passed count and returned candidate remain authoritative. |
| Repeated template occurrences | Accepted cards keyed by occurrence ID; no deduplication by template. Tests cover two identical templates with distinct occurrences, exact transition identity and independent same-day placement. The live fixture supplied two different templates. |
| Accepted list | Original server order, exact source identity and measures; display labels “Choice 1/2” distinguish repeated occurrences without implying execution order. No calculated totals or target count. |
| Exhaustion / Continue | Only server `state === 'placement'` enables Continue. Collecting/exhausted/unavailable states never infer composition completion. |
| Automatic placement | Preferred initial mode. Existing controller operation is `submitDraft('automatic')`; the server assigns dates during submission. There is no separate preview action to recreate. UI describes this accurately. |
| Manual placement | Each accepted occurrence can choose an allowed date through radio controls. Exact occurrence/date writes; one date, multiple dates and multiple occurrences on the same date covered. |
| Completion | Same existing mechanical placement-count requirement for manual submit; server validation and warnings remain authoritative. No safety engine or client scheduling heuristics. |
| Submit | Exact draft ID, returned revision and `automatic`/`manual` mode passed to the unchanged submit operation. Only a pending proposal is created. |
| Return | Successful shared submit clears the task and returns directly to V2 Week, without transiently mounting the V1 proposal editor or fetching alternatives. |
| Resume | Settled Back returns Week without clearing/regenerating draft. Continue choosing retains identity/revision. Cold restore uses existing SecureStore keys and server reads, with no new storage. |
| V1 / V2 | Settled preference changes swap the presentation around the same shared draft. No simultaneous task bodies. V1 creation remains available; original V1 swipe panel/presentation bodies remain unchanged. |
| Error handling | Existing safe validation, stale-revision, expiry/not-found, network and capacity handling preserved. Returned warnings use the existing public mapper. No text parsing, silent retries or speculative catalog-capacity repair. |

Create/transition/place/submit operation bodies and API clients are unchanged from
accepted 3B. No defaults, retry/idempotency policy, public DTO contract, physiology
or planner behavior is changed. Existing submit sequencing is retained exactly:
submit returns, then the existing `Promise.all` settles saved plan reference and
cleared draft reference, then local draft clears, returned pending plan is set,
and view changes to plan. Both storage operations must settle before the local
transition; their existing concurrent invocation is not redesigned. Focused
deferred-storage tests verify that ordering for automatic and manual submission.

## Duplicate protection and accessibility

Existing visible busy/navigation locks remain. A synchronous ref guard in the
shared controller's existing `run` prevents a second write before React renders
busy, including presses on different controls. It releases in `finally` on
success or safe failure. There is no new mutation effect. Tests exercise same-tick
double dispatch for create, accept, pass, undo, reset, occurrence placement and
both submit modes; cross-control writes, rerender, Back, root/tab navigation,
V1/V2 preference changes and cold restoration are covered. Router tests preserve
the exact returned draft/controller and count zero navigation-generated writes.

Controls have at least 48 dp targets (primary/secondary 52 dp); observed date and
selection targets are 138 px at density 440, approximately 50 dp. Choose/Pass
labels include source workout name. Weekdays expose checkbox/checked state;
manual date radios include choice number, workout name and full date. Busy and
disabled states are exposed; saving and safe errors have live announcements.
There is no gesture-only action or drag/drop. Text wraps and final actions live
inside scroll content with a bottom safe inset. Native 200% font-size verification
reached the complete Continue and automatic Submit actions. Changing font size
recreated Android presentation; the exact revision-9 draft and placements restored.
Original font scale 1.0 was restored afterward. Physical TalkBack/focus-return
acceptance is not claimed.

Public view models use explicit allowlists. Recursive mobile source privacy
coverage and poison-field adapter tests pass, including expected-RPE planning
description suppression. Scanned 21 captured native UI XML artifacts and the
public returned plan response: no TSS, planned/realized/private load or selector
diagnostics. No new logs or accessibility outputs contain private data.

## Software verification

| Gate | Exact result |
| --- | --- |
| New creation view-model suite | 5 tests passed |
| New controlled task-screen suite | 16 tests passed |
| New shared-controller creation-boundary suite | 14 tests passed |
| Planning owner/controller additions | 9 tests passed |
| Actual navigation-shell additions | 2 tests passed |
| Full mobile suite | **335 tests / 49 suites passed**, zero failed/skipped/todo tests, zero snapshots |
| Increase over baseline | **46 tests / 3 suites** above 289 / 46 |
| Planning owner, Week, navigation shell, Calendar, Workout Detail, existing V1 Planning | Included and passed in the full suite |
| Strict TypeScript | `npm run typecheck` passed |
| Unused code | `npm run check:unused` passed |
| Privacy | Recursive source and allowlist/poison regressions passed; native/public artifact scan passed |
| Formatting / diff | Installed TypeScript formatter used on new modules; final `git diff 30a7b6e --check` passed after removing a detected trailing blank line |
| Package/native changes | **NONE** |
| Backend/API/database changes | **NONE**; backend suites are not applicable to this presentation-only change |

Earlier Week/preparation tests that intentionally asserted the superseded V1
creation body now assert the approved V2 presentation. Existing mutation and
identity assertions remain. V1 swipe and safe comparison coverage is retained.
Tests cover exact explicit/reuse/injury/opt-in create payload, invalid/empty input,
stale/busy state, all selection actions, repeated templates, server exhaustion,
source measures, allowed-date placement, incomplete manual submit, exact revisions,
automatic/manual mode, deferred storage, pending only and restored re-entry.

## Authenticated emulator flow and evidence

Reused Android `emulator-5554`, API 35, and installed development client
`com.adrivdbs.wombo`; no native rebuild/reinstall. Metro 8084 projectRoot is this
Slice-4A worktree's mobile directory, confirmed by saved manifest provenance.
The previous Metro 8083 was untouched. Native computer-use pipe failed after
retry; fresh native ADB trees, observed bounds, normal keyboard entry/taps,
scrolling and Android Back supplied verification. No session injection or domain
row writes occurred. Read-only CDP observed component identity and network calls;
it did not invoke app actions or intercept requests.

The ONE authorized tagged start23-dev athlete was created with Supabase Auth,
then prepared through supported profile/onboarding, training-history,
calibration-observation, threshold-confirmation and pending-zone approval APIs.
All hosted operations used start23-dev and the authorized staging API only.
Normal app sign-in reached V2 Week no-plan -> Prepare week -> availability ->
create -> candidate -> Pass/Undo/Pass/Reset -> Choose twice -> accepted list ->
placement -> manual same-date assignment -> automatic submit -> V2 pending Week.
Zone approval was setup only; the resulting weekly proposal was never approved.

- Exact week: `2026-10-12`; selected dates `2026-10-12`, `2026-10-14`, `2026-10-17`.
- Draft: `2e31bff7-73da-400d-a355-0ffd49ddd273`.
- Creation returned revision 1. Back -> Week -> Continue and cold reload retained
  that same draft/revision/current candidate without a new create.
- Settled V1/V2 comparison retained revision and candidate, with one owner and
  zero mutations. Source preference changes never submit a second action.
- Pass/Undo/Pass/Reset advanced revisions 2/3/4/5. Undo/reset returned new server
  candidate occurrence IDs; UI copied them instead of restoring an invented ID.
- Choose twice returned revisions 6/7. Server selected placement state at 7.
  Accepted RUN-013 (90 min) and RUN-010 (150 min) retained server order and exact
  occurrences `cda3e4a2-8675-471d-ac85-7f35f5bc2da9` and
  `171ad11e-52ff-4473-98f3-cfcec976d9b2`.
- Manual writes returned revisions 8/9, both occurrences on `2026-10-12`.
  Incomplete manual submission remained disabled. Multi-date cases are also
  covered deterministically; no second athlete or weekly draft was needed.
- Automatic submit used revision 9 and returned HTTP 201 once. The server chose
  `2026-10-14` and `2026-10-17`, demonstrating server scheduling authority.
- Plan `6bb7d006-6bda-4f4d-a0d3-39f47a0c9a98`: revision 1,
  `state/revision_state = pending_approval`, `active_revision = null`.
  Proposal `1eb65273-6ff0-4d56-ab6a-ec3b33ddfdfb` is `pending`, with no decision
  or application timestamps. V2 Week displays review required. Draft is null,
  task is null and only Week is mounted after settled submission.

Sanitized network segments show one create, one submit and one write per placed
occurrence; no approve/reject/alternative mutation. One second Pass occurred while
the observer was detached, so the trace alone is not claimed as exhaustive.
Returned revision snapshots plus software action-count/payload tests cover it.
Some CDP response bodies were unavailable; a supported authenticated public GET
supplied the returned pending-plan snapshot. Settled native owner checks exclude
development-client restart intervals. Initial detached-native-root input trouble
was resolved by cold reopening the same installed client and normal sign-in,
without destroying/replacing the athlete or changing Auth code.

Ignored local evidence is in `mobile/.runtime/slice4a/`: full test JSON/log,
TypeScript/unused logs, Metro provenance, sanitized network segments, owner/state
snapshots, `pending-plan.json`, `emulator-audit.json` and cleanup proof.
Functional-reference screenshots (PNGs with XML) for later mockups are:

| Reference | Artifact stem |
| --- | --- |
| Availability/date/reuse scaffold | `availability-options`, `availability-create` |
| Candidate | `draft-candidate`, `draft-resumed` |
| Passed/Undo/Reset | `passed-undo`, `passed-reset` |
| Accepted occurrences | `accepted-list` |
| Automatic placement | `automatic-placement`, `automatic-large-text-final` |
| Manual placement / incomplete / write busy | `manual-placement`, `manual-incomplete-final`, `manual-complete` |
| Submit busy / pending result | `pending-submit-result` (busy), `week-after-submit` (settled pending) |
| Large text final action | `selection-large-text-final`, `automatic-large-text-final` |

These are functional references, not final visual designs. `availability.png`
captured the pre-task Week and `manual-large-text.png` captured restored Week;
neither is mislabelled here as a settled task reference. Catalog replacement
characters are preserved exactly as supplied, as in preceding accepted slices.

## Cleanup, integration and remaining gates

Normal Profile sign-out completed; the final native Auth snapshot has no session
and no Planning/Calendar owner. Ownership-guarded cleanup acquired an independent
password session for the same fixture, globally revoked sessions, then deleted
only that owned tagged athlete. `slice4a-authenticated-cleanup.json` proves
**created 1 / deleted 1**, `sessions_revoked: true`, admin GET **404**, and **zero
matching owned tagged users**. No replacement was created. Helpers/observer exited.
Credentials, secret keys and tokens remained temporary helper memory and were
excluded from committed files, source logs and network evidence.

After all software/emulator/cleanup gates passed, local `feat/wombo-ui-v2` was
verified a clean ancestor at the exact 3B starting SHA. It is fast-forwarded
locally to the documentation delivery commit through an expected-old ref update.
No merge/rebase/squash/push is used. The isolated delivery worktree is clean.
Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`; the unrelated dirty original
checkout remains untouched. No production access or deployment occurred.

Slice 4B remains unimplemented: proposal agenda/review, alternatives, replacement,
can-remove presentation and approval/rejection continue using existing V1.
No active-plan moves are migrated. Physical TalkBack, focus-return,
physical-device/release gates and final user-mockup visual acceptance remain open.
No unresolved Slice-4A functional/software/emulator gate remains.

WOMBO UI V2 SLICE 4A COMPLETE — FUNCTIONAL PLANNING SCAFFOLD ACCEPTED
