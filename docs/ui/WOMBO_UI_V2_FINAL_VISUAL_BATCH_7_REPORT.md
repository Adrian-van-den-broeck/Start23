# WOMBO UI V2 FINAL VISUAL BATCH 7 REPORT

Status: ACCEPTED. Scope: existing V2 placement and pending proposal review/editing only. Batch 6 was accepted before this work.

## Authority and review commits

Appearance follows [M5 training anatomy](mockups-final/05-workout-selection.png) and [M3 grouped information](mockups-final/03-zones.png), with the final visual system, tokens, screen mapping and implementation sequence. All 28 original placement/proposal-folder screenshots and both targets were reviewed and [hash protected](evidence/final-visual-batch-7/reference-hashes.json). Batch 7 implements S055–S061 and S075–S088; the movement references S062–S068 were inspected but their implementation remains in Batch 8.

The integrated runtime is `.worktrees/wombo-ui-v2-activities/mobile`. Earlier accepted batches were uncommitted on `feat/wombo-ui-v2-activities`, based on `19c23d58f0b71aea01478df2306e2492a515e36e`. Review branch `feat/wombo-ui-v2-final-batch-7` starts with accepted-mobile snapshot `9e9d5b6003d13a5cf2bbfa8f11b001ce27d805bd`. The original branch/index and unrelated changes were retained.

The two review commits are:

- **A. Placement:** `f6ae7f4529151db1f3e5531f545d2f16db8f4686`, `feat(ui): finalize batch 7 placement occurrence and date groups`.
- **B. Proposal review/editing:** the review-branch tip, `feat(ui): finalize batch 7 pending proposal review and editing`. This includes the report and native evidence. The local evidence commit ledger records its final hash after commit creation.

## Placement

Placement uses the landscape/display heading, warning Notice, pending-only explanation and an elevated ivory mode group with Automatic/Manual ChoiceRows. Automatic placement retains occurrence order and shows M5 sport, supplied measures/intensity and literal source descriptions without inventing dates.

Manual placement gives every accepted occurrence its own elevated workout card and independent date ChoiceRows. Repeated source names remain separate occurrences; multiple offered dates and same-day occurrence choices remain available. The existing completeness predicate controls the forest submit action and its readable disabled reason. Back, return to selection, busy/error state, exact occurrence/date callbacks and pending submission behavior are preserved.

## Proposal review and editing

The pending overview groups the supplied week date, exact revision, status and explanation in an ivory card. The active-plan explanation is a separate Notice. Supplied warning severity selects the existing Notice tones. Every proposed occurrence uses the final WorkoutSummary anatomy and its existing date/status, source measures, intensity, description and edit callback.

Approve and Reject remain separate explicit decisions in their own action group. Alternatives retain a clearly labeled current workout and independent returned candidate cards using SportIndicator, WorkoutFacts and ChoiceRows. A checked candidate is only a local selection; the separate Replace action retains its existing selection predicate. Returned replacement results stay pending and display the authoritative supplied workout/warnings.

Removal appears only with the existing returned capability and pending predicate. The named consequence is visible before removal. The first action only opens local confirmation; the destructive confirmation invokes the existing callback. Keep and selecting another candidate cancel confirmation. Busy/loading, missing alternatives, retry, empty and stale/unavailable states retain their locks and actions.

No automatic approval or active/pending schedule merge was introduced. Controllers, public mappers, API clients, revision preconditions, idempotency, authoritative-result handling and stale-write behavior are unchanged. No physiological calculations or private-load values were added.

## Native visual evidence

The temporary gallery renders the actual three production screens through production public mappers and existing public DTO fixtures. Every callback records only exact identifiers in an inert local ledger. It makes no backend or athlete writes and does not claim actual server approval, scheduling, replacement or removal. [Evidence provenance](evidence/final-visual-batch-7/README.md) records setup, corrections and cleanup.

Android 15/API 35 review used emulator-5554 at 1080 × 2280. The [76-case matrix](evidence/final-visual-batch-7/case-ledger.json) covers 320/360/~393/412 dp, default/200% text and Dutch/English: 48 baseline cases, 21 canonical variants and seven narrow enlarged-text stress cases. All 379 overlapping viewport captures are represented by 118 contact sheets in [30 inspected atlases](evidence/final-visual-batch-7/atlas-index.json). The [visual review](evidence/final-visual-batch-7/visual-review.json) confirms natural wrapping, complete source copy, distinct occurrence/candidate identity and reachable final actions.

| Mapped family or state | Final native evidence | Result |
| --- | --- | --- |
| S055 automatic placement | [Automatic](evidence/final-visual-batch-7/inspection/393-font-1-nl-automatic-1.jpg) | PASS |
| S056–S059 manual occurrence/date grouping and submit | [Manual](evidence/final-visual-batch-7/inspection/393-font-1-nl-manual-1.jpg), [multiple dates](evidence/final-visual-batch-7/inspection/393-font-1-nl-multiple-1.jpg), [same day](evidence/final-visual-batch-7/inspection/393-font-1-nl-sameDay-1.jpg) | PASS |
| S060–S061 incomplete placement | [Incomplete](evidence/final-visual-batch-7/inspection/393-font-1-nl-incomplete-1.jpg) | PASS |
| S075–S077 pending overview, warnings, workouts and decisions | [Review](evidence/final-visual-batch-7/inspection/393-font-1-nl-review-1.jpg) | PASS |
| S078–S081 alternatives and selected replacement | [Alternatives](evidence/final-visual-batch-7/inspection/393-font-1-nl-alternatives-1.jpg), [selected](evidence/final-visual-batch-7/inspection/393-font-1-nl-selected-1.jpg) | PASS |
| S082–S083 returned replacement remains pending | [Replacement](evidence/final-visual-batch-7/inspection/393-font-1-nl-replacement-1.jpg) | PASS |
| S084–S086 capability and explicit removal | [Capability](evidence/final-visual-batch-7/inspection/393-font-1-nl-remove-1.jpg), [confirmation](evidence/final-visual-batch-7/interaction-remove-confirmation.png) | PASS |
| S087–S088 active plus pending | [Separate context and decisions](evidence/final-visual-batch-7/inspection/393-font-1-nl-activePending-1.jpg) | PASS |
| Stale review and alternatives | [Stale](evidence/final-visual-batch-7/inspection/393-font-1-nl-stale-1.jpg), [stale alternatives](evidence/final-visual-batch-7/inspection/393-font-1-nl-staleAlternatives-1.jpg) | PASS |
| Source-only facts and long copy | [Distance](evidence/final-visual-batch-7/inspection/393-font-1-nl-distance-1.jpg), [absent measures](evidence/final-visual-batch-7/inspection/393-font-1-nl-sparse-1.jpg), [long copy](evidence/final-visual-batch-7/inspection/393-font-1-nl-long-1.jpg) | PASS |
| 320 dp / 200% explicit removal | [Confirmation](evidence/final-visual-batch-7/confirmation-320-font-2-en-page-0.png), [Confirm and Keep](evidence/final-visual-batch-7/confirmation-320-font-2-en-page-1.png) | PASS |

The [native target audit](evidence/final-visual-batch-7/native-target-audit.json) passed 645 fully visible controls with no development overlays or undersized targets, using the actual override density and 48 dp minimum within pixel quantization. [Additional confirmation targets](evidence/final-visual-batch-7/confirmation-target-audit.json) cover complete Confirm and Keep controls; scroll-edge clips are excluded using actual ScrollView bounds.

Actual [TalkBack mode-row focus](evidence/final-visual-batch-7/talkback-mode-focus.png) was visually inspected. The requested date touch did not establish date focus; metadata explicitly records this distinction. Complete occurrence/date labels and checked state are verified by native hierarchies and exact interaction callbacks. [Reduced motion](evidence/final-visual-batch-7/reduced-motion-placement.json) ran with all three native motion scales at zero; [accessibility cleanup](evidence/final-visual-batch-7/accessibility-cleanup.json) verifies restored settings and notification flags.

## Verification and cleanup

The [20 native interaction checks](evidence/final-visual-batch-7/native-interactions.json) passed: explicit automatic/manual submit, exact repeated occurrence/date identity, same-day choices, incomplete and busy locks, return controls, exact edit identity, independent approval/rejection, select then replace, removal confirmation/Keep, capability restrictions, stale retry and Back. Opening confirmation, selecting a candidate and Back never approved or removed a workout. Production boundary tests preserve the existing revision and stale behavior.

| Final check | Result |
| --- | --- |
| Full mobile Jest, including boundaries, mappers and privacy | 558 tests / 62 suites PASS |
| Strict TypeScript and unused-code check | PASS |
| Focused placement/proposal screen tests | 33 tests / 2 suites PASS |
| 76 native cases / 379 viewports / 118 contact sheets / 30 atlases | PASS |
| 645 fully visible controls and complete confirmation targets | PASS |
| 20 exact native callback checks | PASS |
| Actual TalkBack mode focus and reduced motion | PASS |
| Ten semantic text/control contrast pairs | PASS |
| Source scope, dependency manifests and original reference hashes | PASS |
| Review commit whitespace checks | PASS |

[Command results](evidence/final-visual-batch-7/command-checks.json), [full Jest results](evidence/final-visual-batch-7/full-mobile-tests.json), [contrast](evidence/final-visual-batch-7/contrast.json), and [verification manifest](evidence/final-visual-batch-7/verification.json) retain the final evidence. No test was weakened.

Only five accepted-baseline source/test files change: placement screen/tests, proposal screen/tests and Button's optional destructive variant. The [scope audit](evidence/final-visual-batch-7/scope-audit.json) protects the other 203 sources, including V1, routes, controllers, mappers and API clients. [Final source hashes](evidence/final-visual-batch-7/final-source-hashes.json) also verify unchanged dependency manifests. The focused screen tests retain existing cases and add explicit decision, local selection/confirmation cancellation, incomplete placement and stale/capability coverage.

[Device cleanup](evidence/final-visual-batch-7/device-cleanup.json) confirms the temporary route and owned transport were removed, with original V1 preference, Dutch language, density 440/font scale 1.0 and original preview on port 8081 restored. The owned review server was stopped. No athlete content was retained during original-root verification. No fixture route or preference override remains in production sources.

Backend, database, APIs and physiology are unchanged. Physical iPhone/device and whole-app release gates remain outside this Android visual batch. Batch 8 movement and later batches are not implemented here.

WOMBO UI V2 FINAL VISUAL BATCH 7 COMPLETE — PLACEMENT AND PROPOSALS ACCEPTED
