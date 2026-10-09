# WOMBO UI V2 FINAL VISUAL BATCH 12 REPORT

Date: 2026-10-09. Baseline: accepted Batch 11, 75fa891. Branch: feat/wombo-ui-v2-final-batch-12.

Status: visual implementation accepted for the existing captured Check-in and supporting flows, with the open gates below. Completed Check-in remains OPEN and UNACCEPTED.

## Check-in

Existing entry, questions, selected values, saved context, explicit context confirmation/request and the documented error are restyled with the final branded landscape header, ivory form/task cards, persistent fields, ChoiceRows, forest buttons and Notice feedback. Multiple-choice days/reasons and exclusive fatigue/discipline restrictions retain their actual selection models. All three discipline restriction choices, attributable professional advice, alarms acknowledgment, external activity name/sport/time/duration/strenuous/recurring controls, add/remove, recurring-sports review and optional temporary context extraction survive.

The unchanged state/operation block is recorded in functional-freeze.json. Saving still sends the existing revision and structured payload; confirmation still sends the exact saved revision/fingerprint. Candidate extraction only fills a draft and never selects injury restrictions. Confirmation is not completion. Proposal request and existing proposal approval remain separate. No protocol, plan outcome, success fixture or new approval action was added.

The original staging capture rejects proposal creation with HTTP 422 validation_failed while onboarding reports phase-14-onboarding-v2 complete and upgrade_required false. The preserved public error is “De wijziging kon niet veilig worden opgeslagen. Probeer opnieuw.” Native review replays that documented rejection through the unchanged client at the exact /plan-proposals endpoint; it is not a new staging transaction or resolution. The completed Check-in reference remains OPEN and UNACCEPTED. A real authoritative completion capture after independently authorized mismatch resolution is required.

## Existing supporting flows

Auth retains sign-in/register selection, normalization, secure inputs, validation, busy lock, existing email-confirmation notice and error/configuration handling. Authentication/session/storage ownership is unchanged. ScreenState applies the final header/card/Notice language to existing configuration/loading destinations with the same title/message/loading props.

Integrations retains the current Polar connection/refresh/OAuth actions, unlinked empty imports, existing connected history day choices, explicit native disconnect confirmation, retained-data/privacy/legal copy, bounded retry and activities destination. Native connected/history DTOs are inert source-backed public fixtures; they do not demonstrate a new real linked-provider transaction.

Pioneer retains server-owned redemption, uppercasing, 32-character field limit, existing enabled predicate, one in-flight operation/idempotency key, actual error and existing response-gated active presentation. No native redemption success was fabricated or accepted.

The existing Planning modal uses ivory surfaces, wrapping icon ActionRows, persistent exclusive language ChoiceRows, separators and the current sign-out callback. Its owner still defers profile/integration/sign-out actions until dismissal, and retains backdrop/hardware-back dismissal. BottomSheetScrollView makes lower controls reachable with large text. This is the existing sheet in the current V1 presentation; V2 root Profile routing remains unchanged. Profile’s existing Tests/Pioneer destination rows already use final components and are retained. No standalone Settings route, settings list, subscription offer or goal-achievement confirmation was created.

The accepted header now stacks when a long back label exceeds eight characters, preserving the existing Weekplanning label without a cramped three-column layout. Existing short-label callers keep their prior composition.

## Verification

The final mobile integration run passes **68 suites / 602 tests**, including the privacy, navigation, stale-state, idempotency and existing Pioneer tests. The focused run passes **7 suites / 22 tests**; five new files add 19 regression tests. Seven existing bottom-sheet mocks only export the real ScrollView substitute required by the new modal presentation; their assertions are unchanged. [Final mobile result](evidence/final-visual-batch-12/full-mobile-tests.json), [focused log](evidence/final-visual-batch-12/focused-final.log).

The normal Jest setup remains enabled. The evidence-only clock fixture stabilizes two unchanged proposal-boundary tests that explicitly name Wednesday 7 October; it resets after each test. No production clock, assertion or Jest configuration was changed. Existing React act warnings also occur in the accepted baseline.

Android 15/API 35 native review covers **51 cases / 227 captured viewports / 95 inspected contact sheets**. The main matrix checks 393 dp at normal text and 320 dp at 200% text; additional entry, Auth and modal cases cover 320/360/412 dp at normal text. All 95 contact sheets were visually inspected. The audit passes **300 state checks** and **618 fully visible control-bound checks** against the 48 dp minimum (0.5 dp rounding tolerance). Clipped scroll-edge controls and editable/scroll containers are excluded from touch-size claims. The modal audit inspects the innermost modal content, excluding the unchanged Planning screen behind it. Long text wraps, lower controls remain scrollable, secure input and choice semantics remain present, and the native status-bar inset keeps the expanded modal handle visible. [Visual review](evidence/final-visual-batch-12/visual-review.json), [inspection index](evidence/final-visual-batch-12/inspection-index.json), [state audit](evidence/final-visual-batch-12/native-state-audit.json), [control audit](evidence/final-visual-batch-12/native-target-audit.json).

Eight contrast pairs pass. Protected accepted reference images retain their hashes. Four screens retain byte-identical normalized state/operation blocks; the nine final production files are hashed separately. Native DTOs and callback fixtures use blocked live transport and inert public data. Temporary gallery code is archived as text evidence only and is removed from production entry points before final verification. [Contrast](evidence/final-visual-batch-12/contrast.json), [functional freeze](evidence/final-visual-batch-12/functional-freeze.json), [production provenance](evidence/final-visual-batch-12/production-provenance.json), [reference protection](evidence/final-visual-batch-12/batch-12-reference-protection.json).

Strict TypeScript passes with both unused checks after restoring both production entry points byte for byte. All **10 native interaction checks** pass: exact context revision/fingerprint dispatch, proposal rejection without completion, native disconnect confirmation/cancellation, English/Dutch preference switching, sign-out/profile callbacks after dismissal, secure password semantics and visible Android IME. Four additional contact sheets covering eight interaction captures were visually inspected. These checks prove UI dispatch through inert transport, not live persistence or successful sign-out/authentication. [Native interaction proof](evidence/final-visual-batch-12/native-interactions.json), [verification commands](evidence/final-visual-batch-12/command-results.json), [evidence guide](evidence/final-visual-batch-12/README.md).

The temporary executable gallery and fixture endpoint are removed. Metro is stopped and the owned emulator density/font settings are restored before shutdown. Production routing, language storage, session ownership, dependencies, backend and database files remain unchanged. Backend/Ruff/mypy/OpenAPI and database/pgTAP/RLS checks are inapplicable to this unchanged cross-stack scope; full mobile privacy/client tests pass. Scope and cleanup evidence accompanies the final commit. The implementation stays on the isolated Batch 12 branch; the canonical report/evidence copy is supplied for review without merging the unrelated dirty root workspace.

## Open gates

- Completed Check-in: documented staging onboarding-upgrade mismatch; no real completed reference, no acceptance.
- Physical devices/iOS, reduced-motion review and spoken screen-reader/target-focus behavior: not established by Android visual or unit evidence.
- Live auth/provider/redemption end-to-end transactions, backend persistence and whole-app release readiness: outside this presentation-only batch.
- Standalone Settings and goal-achievement confirmation: unresolved product capabilities; no implementation added.

Backend, database, physiology, rulesets, contracts, dependencies and navigation/auth owners remain outside this batch.

WOMBO UI V2 FINAL VISUAL BATCH 12 COMPLETE — SUPPORTING FLOWS ACCEPTED WITH DOCUMENTED OPEN GATES
