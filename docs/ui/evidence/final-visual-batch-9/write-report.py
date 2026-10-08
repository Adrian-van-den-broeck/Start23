from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
root=HERE.parents[3]
read=lambda name:json.loads((HERE/name).read_text(encoding='utf-8'))
native=read('native-target-audit.json');assert native['cases']==101
visual=read('visual-review.json');assert visual['result']=='PASS'
callbacks=len(read('native-interactions.json')['results'])
pages=sum(len(list(HERE.glob(f"{c['width']}-font-{c['fontScale']}-{c['language']}-{c['state']}-page-*.png"))) for c in read('case-ledger.json'))
report=f"""# WOMBO UI V2 FINAL VISUAL BATCH 9 REPORT

Status: ACCEPTED. Scope: Activities root/history, existing activity entry and immediate-save RPE only. Batch 8 was accepted before this work.

## Authority and review commits

[06-activities.png / M6](mockups-final/06-activities.png) is the direct Activities target. [M4](mockups-final/04-profile-onboarding.png) supplies the form language. The final visual system, tokens, mapping and implementation sequence govern composition. All S001–S022 Activities references and both targets were visually inspected and [hash protected](evidence/final-visual-batch-9/reference-hashes.json).

The runtime is `.worktrees/wombo-ui-v2-activities/mobile`. Review branch `feat/wombo-ui-v2-final-batch-9` starts at accepted Batch 8 `2b5c7753bde1e5dae2446da40c12469a29bf855e` and has two commits: A, `feat(ui): finalize batch 9 Activities history`; B, `feat(ui): finalize batch 9 activity entry and RPE`. The local commit ledger records hashes after creation. Existing branches, indexes and unrelated working changes are retained.

## Presentation and functional freeze

Activities now uses M6's large title/Profile row (stacked below 390 dp or with enlarged text), trees/river landscape, decorated forest Add banner with ivory plus circle, Recent heading and naturally sized ivory cards. Shared ActivitySummary uses actual sport icon circles, supplied date, duration/distance/pace/source rows, execution/RPE block, optional actual HR and pale titleless Notices. Supplied view-model copy is retained in full. The unchanged public mapper uses its existing localized fallback for completed English activities; Dutch long-history stress captures verify the complete 602-character supplied message. Correction appears only under the existing eligibility predicate. Pending feedback remains above disabled Add/history. Existing final bottom navigation and shell-owned reminder remain unchanged.

Entry retains its existing planned/external/deliberate-extra context, sport choices, timestamp, confirmed timezone, duration and optional distance. M4 ivory form groups, persistent labels, field icons, final ChoiceRows and explicit Save restyle the current form. The existing KeyboardAvoidingView, one ScrollView, all values, validation predicates, create identity and callbacks remain. No new field or required input was added.

Feedback uses a compact final task heading, shared activity card, HR form group and exactly ten canonical sport-specific RPE ChoiceRows. **A choice invokes the existing save callback immediately; there is no added Save button or staged score.** The previous Button's per-choice ref lock and promise-pending handling are retained. Checked state comes from the owner. A supplied selected value can coexist with awaiting-RPE status and is not treated as server acknowledgment. Busy states retain action/dismissal locks; supplied validation/stale/ambiguous errors use final Notices without losing fields or identity.

The [freeze audit](evidence/final-visual-batch-9/functional-freeze.json) confirms eight presentation/test files changed and 200 app/src files unchanged, including the activity controller/provider, boundary, clients/contracts, public mapper, canonical RPE, V1, navigation and reminder. Dependency manifests remain unchanged. Notice's optional heading and ChoiceRow's optional busy presentation retain existing defaults. No backend, database, physiology, public contract, dependency, navigation-framework or later-batch change is included. No charts, streaks or invented analytics were added.

## Native visual evidence

The temporary review route renders actual production screens/primitives, the production public mapper, canonical RPE data and existing shell components from inert public DTO fixtures. Exact callback markers demonstrate native UI interaction and identity. Supplied after-feedback snapshots are visual fixtures, not proof of live create/feedback HTTP or server acknowledgment. Existing boundary/controller/transport tests verify real validation, retry/idempotency, stale recovery and observation ownership. No athlete/server writes occur. [Provenance](evidence/final-visual-batch-9/README.md) records these limits and reproducibility.

Android 15/API 35, emulator-5554 at 1080 × 2280, covers [101 cases](evidence/final-visual-batch-9/case-ledger.json): 64 empty/history/entry/RPE cases across 320/360/~393/412 dp, default/200% system text and Dutch/English; 28 canonical variants; nine narrow enlarged-text stress cases. All {pages} overlapping viewport captures appear in {visual['contactSheets']} complete contact sheets and {len(visual['reviewedAtlases'])} [visually inspected atlases](evidence/final-visual-batch-9/atlas-index.json). Captures require exact fixture and final-4 native build markers and refuse development overlays. The [visual review](evidence/final-visual-batch-9/visual-review.json) records natural wrapping, complete copy and reachable final controls.

| Mapping/state | Final evidence | Result |
| --- | --- | --- |
| S001 pending root | [Pending](evidence/final-visual-batch-9/inspection/393-font-1-nl-pending-1.jpg) | PASS |
| S002 empty root | [Empty](evidence/final-visual-batch-9/inspection/393-font-1-nl-empty-1.jpg) | PASS |
| S003 / S004 history with / without HR | [History](evidence/final-visual-batch-9/inspection/393-font-1-nl-history-1.jpg), [no HR](evidence/final-visual-batch-9/inspection/393-font-1-nl-noHR-1.jpg) | PASS |
| S005 / S006 empty entry top / fields | [Entry](evidence/final-visual-batch-9/inspection/393-font-1-nl-entryEmpty-1.jpg) | PASS |
| S007 / S008 filled entry top / fields | [Filled entry](evidence/final-visual-batch-9/inspection/393-font-1-nl-entry-1.jpg) | PASS |
| S009 / S010 feedback without / with entered HR | [No HR](evidence/final-visual-batch-9/inspection/393-font-1-nl-rpeNoHR-1.jpg), [HR](evidence/final-visual-batch-9/inspection/393-font-1-nl-rpeHR-1.jpg) | PASS |
| S011–S014 choices top / lower / live / last row | [RPE](evidence/final-visual-batch-9/inspection/393-font-1-nl-rpe-1.jpg), [narrow enlarged text](evidence/final-visual-batch-9/inspection/320-font-2-en-rpe-1.jpg) | PASS |
| S015 / S016 supplied selected fixture, checked 7 | [Selected](evidence/final-visual-batch-9/inspection/393-font-1-nl-selected-1.jpg) | PASS |
| S017 / S018 blocked Add and resume feedback | [Blocked](evidence/final-visual-batch-9/inspection/393-font-1-nl-blocked-1.jpg) | PASS |
| S019 after supplied feedback | [After](evidence/final-visual-batch-9/inspection/393-font-1-nl-after-1.jpg) | PASS |
| S020 global reminder over Week | [Reminder](evidence/final-visual-batch-9/inspection/393-font-1-nl-reminderWeek-1.jpg) | PASS |
| S021 reminder Activities destination | [Destination](evidence/final-visual-batch-9/inspection/393-font-1-nl-reminderDestination-1.jpg) | PASS |
| S022 reminder feedback destination | [Feedback destination](evidence/final-visual-batch-9/inspection/393-font-1-nl-reminderFeedback-1.jpg) | PASS |
| Planned / external / repeated occurrence context | [Context](evidence/final-visual-batch-9/inspection/393-font-1-nl-context-1.jpg), [planned](evidence/final-visual-batch-9/inspection/393-font-1-nl-planned-1.jpg), [external](evidence/final-visual-batch-9/inspection/393-font-1-nl-external-1.jpg) | PASS |
| Swim distance / partial coverage / explicit match | [Distance](evidence/final-visual-batch-9/inspection/393-font-1-nl-distanceOnly-1.jpg), [coverage](evidence/final-visual-batch-9/inspection/393-font-1-nl-partialCoverage-1.jpg), [match](evidence/final-visual-batch-9/inspection/393-font-1-nl-match-1.jpg) | PASS |
| Busy / validation / stale-ambiguous / missing timezone | [Create busy](evidence/final-visual-batch-9/inspection/393-font-1-nl-busyCreate-1.jpg), [RPE busy](evidence/final-visual-batch-9/inspection/393-font-1-nl-busyRpe-1.jpg), [entry error](evidence/final-visual-batch-9/inspection/393-font-1-nl-entryError-1.jpg), [feedback error](evidence/final-visual-batch-9/inspection/393-font-1-nl-rpeError-1.jpg), [timezone](evidence/final-visual-batch-9/inspection/393-font-1-nl-timezoneMissing-1.jpg) | PASS |
| Long source copy / long context / multiple sports | [History](evidence/final-visual-batch-9/inspection/320-font-2-nl-longHistory-1.jpg), [context](evidence/final-visual-batch-9/inspection/320-font-2-en-longContext-1.jpg), [multiple](evidence/final-visual-batch-9/inspection/320-font-2-en-multiple-1.jpg) | PASS |

The [native navigation audit](evidence/final-visual-batch-9/native-navigation-audit.json) verifies selected footer controls and actual forest pixels across captured viewports. The canonical [native state audit](evidence/final-visual-batch-9/native-state-audit.json) checks all ten complete radio labels against unchanged src/lib/rpe.ts, native checked/disabled states and absence of an added Save button. Canonical descriptions retain their source language even in the English UI. No missing HR is displayed as zero or inferred. All supplied view-model explanations and supported correction conditions remain.

## Verification and cleanup

The [native target audit](evidence/final-visual-batch-9/native-target-audit.json) passes {native['fullyVisibleControls']} fully visible controls at 48 dp within native pixel quantization, excluding viewport-edge clipping, with no accepted development overlays. The [{callbacks} native callback checks](evidence/final-visual-batch-9/native-interactions.json) cover Add, context expansion, exact repeated/planned/external identity, deliberate-extra reset, local sport selection, explicit create, immediate RPE return/correction, pending Add lock, busy dismissal/save locks, explicit match, missing timezone, reminder identity and last canonical choice at 320 dp/200% text.

The [keyboard review](evidence/final-visual-batch-9/keyboard-review.json) records actual Tab/Enter immediate RPE and IME-visible entry Save / feedback choice reachability. [Accessibility review](evidence/final-visual-batch-9/accessibility-review.json) distinguishes native radio/checked/disabled/focus evidence and reduced motion from emulator TalkBack touch-focus limits; entry touch capture shows the editable Distance accessibility rectangle, while the injected RPE touch returns to Activities with its heading focused. This does not prove RPE TalkBack focus or double-tap activation. Full physical-device TalkBack navigation, announcements and activation remain a whole-app release verification limit. [Accessibility cleanup](evidence/final-visual-batch-9/accessibility-cleanup.json) restores actual services, motion scales and notification permission flags.

| Check | Result |
| --- | --- |
| Full mobile Jest with scoped unchanged proposal fixture clock | 562 tests / 62 suites PASS |
| Strict TypeScript / unused code, including after gallery removal | PASS |
| Focused Activities / boundaries / provider / canonical RPE / primitives / assets | 92 tests / 8 suites PASS |
| 101 native cases / ten exact canonical choices / complete end controls | PASS |
| Native Tab/Enter immediate RPE / IME entry and feedback / reduced motion | PASS |
| {native['fullyVisibleControls']} fully visible controls / {callbacks} native callbacks | PASS |
| Ten contrast pairs / source and dependency freeze / 24 reference hashes | PASS |
| Report links / whitespace / temporary route and review transport removal | PASS |

[Command checks](evidence/final-visual-batch-9/command-checks.json), [full Jest](evidence/final-visual-batch-9/full-mobile-tests.json), [contrast](evidence/final-visual-batch-9/contrast.json), [source hashes](evidence/final-visual-batch-9/final-source-hashes.json), [scope](evidence/final-visual-batch-9/scope-audit.json) and [verification manifest](evidence/final-visual-batch-9/verification.json) retain the results. No test was weakened. Two focused tests verify delayed immediate-save locking without staged selection/Save and retention of complete source facts/Notices with absent HR and unsupported correction omitted.

Full Jest uses the accepted Batch 8 external setup scoped only to two unchanged Batch 7 proposal tests whose October 7 fixtures depend on that date. Assertions, production code, Jest configuration, other clocks and timer APIs remain unchanged. Batch 8 retains the default October 8 run's two known fixture-date failures; this report does not claim a default-clock full-suite pass.

Superseded captures are explicitly rejected and excluded from accepted counts: initial stale fixture/bundle data, header overlap/non-CI development overlay, narrow display heading, the 360 dp title/Profile breakpoint and an Expo startup linking toast. The compact feedback task heading fixes the one-letter Dutch wrap at 320 dp; the responsive root stacks below 390 dp to avoid the same issue beside Profile at 360 dp. Two aborted interaction-harness runs are retained as rejected partial ledgers: Back required returning to the header, and correction required the existing curly apostrophe in its exact accessible label. Both selectors were corrected without production changes. Review automation swipes the scroll gutter so editable HR fields do not consume injected scrolling. A resumed final-3 startup toast was inspected and dismissed with its visible Close control; every subsequent capture still rejects any recurrence. No navigation fix or production error suppression was introduced. This development-client transport limitation is documented separately from application state behavior.

The session restart stopped both previews and the emulator. The existing Wombo review device was restarted without clearing data, and port 8081 was restored. [Device cleanup](evidence/final-visual-batch-9/device-cleanup.json) removes the temporary route and owned scratch/8084 transport, verifies original language/version/display settings and restores the normal original Week preview without retaining athlete text or screenshots in the evidence. The owned 8084 server is stopped; original port 8081 remains available.

Backend/database checks are inapplicable to this presentation-only batch. Physical iPhone/device and whole-app release gates remain outside this Android visual batch. No later batch is implemented.

WOMBO UI V2 FINAL VISUAL BATCH 9 COMPLETE — ACTIVITIES AND RPE ACCEPTED
"""
(root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_9_REPORT.md').write_text(report,encoding='utf-8')
print('Batch 9 report written')
