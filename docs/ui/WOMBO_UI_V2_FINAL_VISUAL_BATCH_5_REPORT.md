# WOMBO UI V2 FINAL VISUAL BATCH 5 REPORT

Status: ACCEPTED. Scope: Calendar only. Batch 4 was accepted before this work.

## Authority and implementation

Appearance follows [M1 Calendar Week](mockups-final/01-calendar-week.png) and [M2 Calendar Month](mockups-final/02-calendar-month.png), read with the final visual system, tokens, screen mapping and implementation sequence. All seven Calendar reference images and movement cross-references S062/S066-S068 were inspected as functional evidence, not design targets. [Reference hashes and inspection sheets](evidence/final-visual-batch-5/reference-hashes.json) preserve the originals.

Implementation remains in `.worktrees/wombo-ui-v2-activities/mobile`, branch `feat/wombo-ui-v2-activities`, based on `19c23d58f0b71aea01478df2306e2492a515e36e`. The accepted prior batches and unrelated root/worktree changes were retained.

Calendar now has the landscape/title/explanation composition, final pale pill segment, circular range arrows and centered Today action. Week uses an open date rail with large day numerals, natural-height rows, fine separators, explicit prescribed rest and independent ivory workout summaries. Narrow or enlarged Week rows use full-width date headings and cards.

Month uses an ivory rounded grid card, fine lines, muted outside-month dates, amber Today and a forest outline/pale-green selection. When Today is selected, the amber fill and forest selection outline coexist. Actual workout counts and existing sport/rest abbreviations remain explicit, with a visible localized key. No dots or new dot semantics were introduced. Selected dates have an ivory heading/detail card and an independent summary/action for every supplied workout.

The existing Month list decision includes the grid card's actual inset and perimeter, preserving 48 dp cells. It uses full-width date targets at 320/360 dp and all 200% settings; ~393/412 dp retain the default-text grid. Visual short dates retain the complete date, count, sport/rest and Today in their accessibility labels. Fonts remain unclamped and content grows naturally.

Two shared presentation extensions retain their previous defaults: SegmentedControl accepts Calendar's existing tab semantics, and HeaderLandscape can leave a decorative band before applying the full protective veil beneath Calendar copy. No Calendar controller, navigation owner, mapper, API, movement state machine, shell route, dependency, token or backend changed. The explicit Calendar scroll clipping override was removed so the last card remains reachable.

## Evidence and visual review

Native review uses the actual CalendarScreen, calendarViewModel, useCalendarNavigation, accepted shell/footer and real read-only WorkoutDetailScreen. DTO fixtures reuse existing public test data. Movement return captures show supplied stored locations; they do not claim native moves were submitted. Move entry invokes an inert callback, while the existing production boundary tests verify the mutation owner. No athlete data was changed or captured.

The Android 15 / API 35 review completed 47 native cases, 534 complete viewport captures and 3,488 fully visible target measurements. The 32-case base matrix covers Week and selected Month at 320/360/~393/412 dp, default/200% text, Dutch/English. Eleven canonical state cases and four 320 dp/200% English stress cases add empty/rest, movement locations, long names, absent measures, loading, failure and retained-range evidence. [Native audit](evidence/final-visual-batch-5/native-audit.json), [case ledger](evidence/final-visual-batch-5/case-ledger.json) and [evidence provenance](evidence/final-visual-batch-5/README.md) retain actual PNG/XML/metadata triples and hashes.

The complete Calendar reference family was reviewed against M1/M2. The final Week is an open rail composition with restrained separators and independent ivory summaries. Month has an elevated rounded grid, clearly different Today and selection styling, muted outside dates, and a separate selected-day card. These replace the provisional panel/toolbar presentation. Narrow and large-text pages grow naturally; enlarged labels wrap, including root-tab labels at 320 dp/200%, while complete controls and the last workout remain reachable. The Profile utility row stacks below 393 dp or with enlarged text; its final 320 dp cases were recaptured after spacing refinement.

| Mapped reference | Final native evidence | Review |
| --- | --- | --- |
| S023: Week workouts/rest | [Week sequence](evidence/final-visual-batch-5/inspection/393-font-1-nl-week-1.jpg) | PASS |
| S024: empty Week | [Empty sequence](evidence/final-visual-batch-5/inspection/393-font-1-nl-empty-1.jpg) | PASS |
| S025: Month | [Month/rest selection](evidence/final-visual-batch-5/inspection/393-font-1-nl-month-1.jpg) | PASS |
| S026: selected-date detail | [Selected detail and summaries](evidence/final-visual-batch-5/inspection/393-font-1-nl-selected-2.jpg) | PASS |
| S027/S028: same-day siblings, top/bottom | [Independent summaries and final actions](evidence/final-visual-batch-5/inspection/393-font-1-nl-week-2.jpg) | PASS |
| S029: Calendar detail entry/return | [Real detail](evidence/final-visual-batch-5/interaction-detail-entry.png), [Back return](evidence/final-visual-batch-5/interaction-detail-back-return.png) | PASS |
| S062: active move entry | [Move entry](evidence/final-visual-batch-5/inspection/393-font-1-nl-moveEntry-1.jpg) | PASS |
| S066: cancel return, supplied stored date | [Thursday location](evidence/final-visual-batch-5/inspection/393-font-1-nl-cancelReturn-1.jpg) | PASS |
| S067: after move, supplied stored date | [After-move sequence](evidence/final-visual-batch-5/inspection/393-font-1-nl-afterMove-1.jpg) | PASS |
| S068: Calendar after move | [Wednesday location](evidence/final-visual-batch-5/inspection/393-font-1-nl-calendarAfterMove-1.jpg) | PASS |

[Mapped-state ledger](evidence/final-visual-batch-5/mapped-state-coverage.json) binds these references to fixture prefixes. [Long-name stress](evidence/final-visual-batch-5/inspection/320-font-2-en-long-5.jpg), [absent-data stress](evidence/final-visual-batch-5/inspection/320-font-2-en-sparse-3.jpg), and [320 dp/200% Month end](evidence/final-visual-batch-5/inspection/320-font-2-en-selected-7.jpg) show complete source content and final actions without font clamping or truncation.

[Native interaction results](evidence/final-visual-batch-5/native-interactions.json) passed previous/next Week and Month, actual-device Today, outside-month selection, selected-date View Week and ten rapid mode changes. The real detail modal opens each sibling's identity, hides the underlying footer, and Close/Android Back restore the exact Calendar accessibility footprint, selection and viewport. The permitted Move seam invokes the exact occurrence callback without mutation.

[Reduced motion](evidence/final-visual-batch-5/reduced-motion-calendar.json) passed with all three Android animation scales at zero. Actual [TalkBack Profile focus](evidence/final-visual-batch-5/talkback-profile-focus.png) and [Today-date focus](evidence/final-visual-batch-5/talkback-today-date-focus.png) were visually inspected; the date's spoken label retains full date, count and Today. [Accessibility cleanup](evidence/final-visual-batch-5/accessibility-cleanup.json) restores all original settings and notification-permission flags. Native captures include the system gesture inset. Keyboard ownership/evidence remains in accepted Batch 2; Calendar adds no editable input. Physical iPhone/device/release validation remains outside this Android visual batch, as specified by the final implementation sequence.

## Functional and source gates

The final complete mobile run passed **547 tests in 62 suites**. Strict TypeScript and unused-symbol checks passed. Calendar tests cover seven dates, rest/empty/unknown distinctions, independent siblings, exact callbacks, selection, range navigation, grid/list fit and permitted move entry. [Check exit codes](evidence/final-visual-batch-5/command-checks.json) and [full test results](evidence/final-visual-batch-5/full-mobile-tests.json) retain the results.

Unchanged controller tests pass latest-request wins, old-finally isolation, retained successful ranges after failure, authoritative-move supersession and reconciliation without duplicate occurrences. Unchanged movement-boundary tests pass cancellation without validation/mutation, stale revision recovery, detail origin, active-plan retention and unavailable Move for unsupported occurrences. The former distance-format assertion now expects the accepted shared summary's literal `1200 m`; the source value and mapper are unchanged.

[Source audit](evidence/final-visual-batch-5/scope-audit.json) records eight existing files changed and one new presentation helper against accepted Batch 4, with 201 baseline files unchanged. Protected controller/navigation/mapper/V1/token/route/dependency fingerprints remain unchanged. Recursive runtime-source and native-text privacy scans passed. No physiological formulas, private load, invented readiness/times, or Start workout action were added. Backend, database, RLS and deployment checks are not applicable to this presentation-only delta.

[Contrast audit](evidence/final-visual-batch-5/contrast.json) passes every text/control pair; minimum text contrast is **4.645:1**, including the worst-case landscape under Calendar copy. All interactive source targets retain at least 48 dp; native measurements allow only normal integer-pixel quantization of that minimum.

[Device cleanup](evidence/final-visual-batch-5/device-cleanup.json) passed: temporary route and emulator capture files removed; original root layout unchanged; physical density, default text scale and Dutch preference restored; normal authenticated Week verified without saving live content. The normal app's existing UI preference was retained.

On resume, the prior Metro server was absent and the Windows emulator window stalled. Recovery reopened the same stored AVD in headless mode with the documented software renderer and restored the local Metro server on port 8081. A transient existing expired-session gate was observed; normal authenticated Week subsequently returned with the stored session. No logout, authentication override, app-data wipe, backend bridge or training mutation was performed. [Recovery provenance](evidence/final-visual-batch-5/emulator-recovery.json) and [headless environment](evidence/final-visual-batch-5/headless-recovery.json) record this limitation; Metro and the headless emulator remain running.

[Final combined verification](evidence/final-visual-batch-5/verification-summary.json) is **PASS**: 547 tests, 47 cases, 534 matrix PNGs / 552 total PNGs, 3,488 native target checks, unchanged protected owners and 201 baseline files, restored settings, artifact/source/reference integrity, valid UTF-8, valid report links and no privacy findings. Calendar visual fidelity and functional parity are accepted. Physical iPhone/device/release roadmap gates remain outside this batch; no claim is made that the full application or rollout is complete.

WOMBO UI V2 FINAL VISUAL BATCH 5 COMPLETE — CALENDAR ACCEPTED
