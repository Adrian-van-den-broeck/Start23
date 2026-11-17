from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
read=lambda name:json.loads((HERE/name).read_text(encoding='utf-8'))
tests=read('full-mobile-tests.json');assert tests['success']
assert all(v==0 for v in read('command-checks.json').values())
audit=read('native-target-audit.json');assert audit['cases']==83 and not audit['failures'] and not audit['developmentOverlays']
review=read('visual-review.json');assert review['result']=='PASS'
callbacks=read('native-interactions.json')['results'];assert len(callbacks)==25
focus=read('accessibility-review.json');assert focus['result']=='PASS'
pages=sum(len(list(HERE.glob(f"{c['width']}-font-{c['fontScale']}-{c['language']}-{c['state']}-page-*.png"))) for c in read('case-ledger.json'))
text=f'''# WOMBO UI V2 FINAL VISUAL BATCH 8 REPORT

Status: ACCEPTED. Scope: the existing V2 active workout movement lifecycle only. Batch 7 was accepted before this work.

## Authority and review commit

Appearance reuses [M1 Calendar date language](mockups-final/01-calendar-week.png), [M2 selected dates](mockups-final/02-calendar-month.png) and [M5 training anatomy](mockups-final/05-workout-selection.png), following the final system, tokens, mapping and implementation sequence. All seven mapped S062–S068 movement screenshots and the three targets were inspected and [hash protected](evidence/final-visual-batch-8/reference-hashes.json).

The integrated runtime is `.worktrees/wombo-ui-v2-activities/mobile`. Review branch `feat/wombo-ui-v2-final-batch-8` starts at accepted Batch 7 commit `70568a80c0d19a88cd6b47fe1184a16ed7b4a7a1`. Its single review commit is titled `feat(ui): finalize batch 8 active workout movement`; the local evidence commit ledger records its final hash after creation. The original branches, indexes and unrelated working changes are retained.

## Presentation and functional freeze

Calendar's existing subordinate Move button gains a decorative calendar icon. Its full occurrence label, callback, placement and eligibility are unchanged. The move task supplies the existing public workout summary mapper to WorkoutMoveScreen. The screen now uses the ridge/display heading, shared WorkoutSummary with supplied sport, measures, intensity and literal description, an explicit current-date label and a separated target-date summary.

The chooser groups exactly the existing seven origin-week dates in an elevated ivory card using final ChoiceRows, with the current date labeled and the local selected date checked. The separate Review action retains the no-op predicate. Validation retains the existing announced busy state and disables date choices and dismissal. Warning review keeps every supplied warning in order as amber Notices, with separate explicit Proceed and Cancel actions. Rejected/ambiguous errors and stale/unavailable context use final error/information Notices while preserving the original warnings and action locks.

Return renders the existing Calendar's supplied authoritative layout. No optimistic success toast, forced target date, automatic approval, new gesture framework or schedule merge was introduced. The source [functional-freeze audit](evidence/final-visual-batch-8/functional-freeze.json) confirms that the move task is identical to accepted Batch 7 after reversing its two summary-presentation substitutions. The same-week guard, complete-layout validation, exact revision, warning lifecycle, authoritative PATCH, stale/ambiguous/rejected handling and occurrence identity remain owned by unchanged controllers and API clients.

Only five source/test files differ: WorkoutMoveScreen and its tests, the task's summary binding, WorkoutSummary's optional date label and WeekAgenda's decorative Move icon. The other 203 app/src files and dependency manifests remain unchanged. Existing summary consumers retain the same date formatting. V1, routes, gesture implementations, backend, database, physiology and public contracts are unchanged.

## Native visual evidence

The temporary gallery renders actual production CalendarScreen and WorkoutMoveScreen through production public mappers and existing public DTO fixtures. Every callback records only an exact identifier in an inert local ledger. Supplied return snapshots are visual fixture data. There are no backend or athlete writes, and the gallery does not claim a real HTTP PATCH. Existing production boundary/controller tests verify the actual mutation and revision semantics. [Provenance and reproduction](evidence/final-visual-batch-8/README.md) document the distinction, capture corrections and cleanup.

Android 15/API 35, emulator-5554 at 1080 × 2280, covers [83 cases](evidence/final-visual-batch-8/case-ledger.json): 64 before/chooser/warning/after cases across 320/360/~393/412 dp, default/200% system text and Dutch/English; 14 canonical variants; five narrow enlarged-text stress cases. All {pages} overlapping viewport captures are represented in {review['contactSheets']} contact sheets and {len(review['reviewedAtlases'])} [inspected atlases](evidence/final-visual-batch-8/atlas-index.json). The [visual review](evidence/final-visual-batch-8/visual-review.json) records natural wrapping, full source copy and reachable final controls.

| Mapping/state | Final evidence | Result |
| --- | --- | --- |
| S062 Calendar move entry / before | [Before](evidence/final-visual-batch-8/inspection/393-font-1-nl-before-1.jpg) | PASS |
| S063 current workout/date and chooser | [Chooser](evidence/final-visual-batch-8/inspection/393-font-1-nl-chooser-1.jpg) | PASS |
| S064 selected date and explicit Review | [Selected](evidence/final-visual-batch-8/inspection/393-font-1-nl-selected-1.jpg) | PASS |
| Validation / applying locks | [Validation](evidence/final-visual-batch-8/inspection/393-font-1-nl-validation-1.jpg), [busy](evidence/final-visual-batch-8/inspection/393-font-1-nl-confirmBusy-1.jpg) | PASS |
| S065 warning review, Proceed and Cancel | [Warning](evidence/final-visual-batch-8/inspection/393-font-1-nl-warning-1.jpg) | PASS |
| S066 Cancel return | [Cancel](evidence/final-visual-batch-8/inspection/393-font-1-nl-cancel-1.jpg) | PASS |
| S067 returned occurrence / after | [After](evidence/final-visual-batch-8/inspection/393-font-1-nl-after-1.jpg) | PASS |
| S068 separate later Calendar snapshot | [Later Calendar](evidence/final-visual-batch-8/inspection/393-font-1-nl-laterCalendar-1.jpg) | PASS |
| Rejected / ambiguous / stale | [Rejected](evidence/final-visual-batch-8/inspection/393-font-1-nl-rejected-1.jpg), [ambiguous](evidence/final-visual-batch-8/inspection/393-font-1-nl-ambiguous-1.jpg), [stale](evidence/final-visual-batch-8/inspection/393-font-1-nl-stale-1.jpg) | PASS |
| Same-day occurrence identity | [Multiple](evidence/final-visual-batch-8/inspection/393-font-1-nl-multiple-1.jpg), [return audit](evidence/final-visual-batch-8/native-occurrence-return-audit.json) | PASS |
| Source-only facts / long copy | [Distance](evidence/final-visual-batch-8/inspection/393-font-1-nl-distance-1.jpg), [absent measures](evidence/final-visual-batch-8/inspection/393-font-1-nl-sparse-1.jpg), [long warning](evidence/final-visual-batch-8/inspection/320-font-2-en-longWarning-1.jpg) | PASS |

Chronology is explicit: baseline before is Wednesday 7 October; the returned after fixture is Thursday 8 October; S068's separate later Calendar is Wednesday again. The latter is not treated as the same move target. Cancel does not undo an already completed move. Repeated same-template occurrences are independent: moving the second scheduled occurrence leaves its sibling and completed occurrence on their original date. Completed occurrence has no Move action.

## Verification and cleanup

The [native target audit](evidence/final-visual-batch-8/native-target-audit.json) passed {audit['fullyVisibleControls']} fully visible controls at a minimum of 48 dp within pixel quantization, with no development overlays. Actual ScrollView bounds exclude scroll-edge clipping. The [25 native callback checks](evidence/final-visual-batch-8/native-interactions.json) cover exact entry/date/occurrence identity, local selection, origin no-op, explicit review/proceed, chooser/warning Cancel and system Back, validation/apply dismissal locks, stale locks, rejected/ambiguous return, repeated occurrence return and 320 dp/200% actions. Backend writes remain false.

The [native keyboard review](evidence/final-visual-batch-8/keyboard-review.json) passed Tab/Enter move entry, local date selection, and Back returning focus to the exact Move button. Actual focus rings and checked state were visually inspected. The seven-button date path retains full labels and checked/disabled native state; no text input or IME is required. The [accessibility review](evidence/final-visual-batch-8/accessibility-review.json) distinguishes these results from TalkBack pointer/shortcut attempts: actual green focus was seen on Cancel and the literal description, but intended Move/date focus was not established by emulator injection and is not claimed. Full physical-device TalkBack navigation remains a whole-app release verification limit. Reduced motion ran with all three native motion scales at zero. [Accessibility cleanup](evidence/final-visual-batch-8/accessibility-cleanup.json) and [navigation cleanup](evidence/final-visual-batch-8/talkback-navigation-cleanup.json) verify restored services, motion settings and notification permission flags.

| Check | Result |
| --- | --- |
| Full mobile Jest with scoped proposal fixture clock, including move boundaries, controllers, mappers and privacy | {tests['numPassedTests']} tests / {tests['numPassedTestSuites']} suites PASS |
| Strict TypeScript / unused code | PASS |
| Focused move screen / Calendar / move boundary | 33 tests / 3 suites PASS |
| 83 native cases, complete end controls / last Calendar day | PASS |
| Native Tab/Enter/date/Back and restored exact Move focus / reduced motion | PASS |
| {audit['fullyVisibleControls']} fully visible controls / 25 native callback checks | PASS |
| Ten semantic text/control contrast pairs | PASS |
| Functional freeze, source/dependency/reference hashes | PASS |
| Whitespace / report links / temporary route removal | PASS |

[Command results](evidence/final-visual-batch-8/command-checks.json), [full Jest results](evidence/final-visual-batch-8/full-mobile-tests.json), [contrast](evidence/final-visual-batch-8/contrast.json), [final source hashes](evidence/final-visual-batch-8/final-source-hashes.json), [scope audit](evidence/final-visual-batch-8/scope-audit.json) and [verification manifest](evidence/final-visual-batch-8/verification.json) retain the evidence. No test was weakened; two screen tests add local seven-date/no-op/Cancel coverage and full summary/all-warning retention without automatic review or confirmation.

The [initial unmodified-clock suite](evidence/final-visual-batch-8/unfrozen-mobile-tests.json) passed 558 tests and failed two unchanged Batch 7 proposal tests after the system date advanced to October 8. Those fixtures schedule the approved workout on October 7; the existing Week focus selects today or a future workout. An [external review-run setup](evidence/final-visual-batch-8/deterministic-proposal-fixture-date.cjs) pins only those two exact test names to their October 7 fixture date and restores Date after each test. Their unchanged assertions [both pass](evidence/final-visual-batch-8/deterministic-proposal-tests.json), and the full suite then passes. Production code, Jest configuration, test sources and timer APIs were not changed for this date dependency. The default-clock suite's two existing date-dependent failures remain recorded rather than claimed as passing.

[Device cleanup](evidence/final-visual-batch-8/device-cleanup.json) confirms the gallery and owned transport/scratch files were removed, with original V1 preference, Dutch language, density 440/font scale 1.0 and the original port 8081 Week preview restored. The owned port 8084 server was stopped. No athlete content was saved during root restoration. No fixture route or preference override remains in production sources.

Backend and database checks are inapplicable to this presentation-only change. Physical iPhone/device and whole-app release gates remain outside this Android visual batch. No later batch is implemented.

WOMBO UI V2 FINAL VISUAL BATCH 8 COMPLETE — ACTIVE MOVEMENT ACCEPTED
'''
(HERE.parents[1]/'WOMBO_UI_V2_FINAL_VISUAL_BATCH_8_REPORT.md').write_text(text,encoding='utf-8')
print('Report written with final verification counts')
