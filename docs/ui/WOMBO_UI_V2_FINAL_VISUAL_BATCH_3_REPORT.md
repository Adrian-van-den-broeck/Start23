# Wombo UI V2 FINAL VISUAL BATCH 3 — Workout Detail and summaries

Date: 2026-10-07. Prerequisite: Batch 2 accepted. Status: **workout visual language accepted**.

## Authority and runtime

[M5](mockups-final/05-workout-selection.png), the [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md), [tokens](WOMBO_UI_V2_FINAL_TOKENS.md), [screen mapping](WOMBO_UI_V2_FINAL_SCREEN_MAPPING.md) and [batch sequence](WOMBO_UI_V2_FINAL_IMPLEMENTATION_SEQUENCE.md) govern this batch. All seven detail references S101–S107 and Calendar detail entry S029 were inspected individually for functional content.

Runtime: `.worktrees/wombo-ui-v2-activities/mobile`, branch `feat/wombo-ui-v2-activities`, base HEAD `19c23d58f0b71aea01478df2306e2492a515e36e`. The baseline includes accepted Batches 1A, 1B and 2. No second design library or dependency was introduced.

## Implementation

The existing `WorkoutSummary` now uses an ivory lifted card, a vector sport circle, visible sport capsule, strong 22/28 title, date and explicit icon/label status. Its focus variant uses 64 dp circles and responsive focus padding. Shared `WorkoutFacts` presents supplied duration/distance alongside effort using pale metric circles and restrained rules. Focus facts follow M5's 16/24 time typography; scheduled summaries retain 28/34 primary measures. Distance-only remains a primary numeric distance with no time row. Narrow/enlarged fact groups stack and grow naturally.

An optional summary footer accommodates existing actions inside the card with the documented 24 dp separation. It is demonstrated only by inert public candidate buttons in this batch; no production chooser or screen action was migrated.

`SportIndicator` uses the accepted Run/Bike/Swim SVGs, with visible labels and neutral/discipline tones. Existing callers receive the shared sport treatment; Week, Calendar, creation, proposal and activity screen compositions were not migrated.

`SessionSequence` places the supplied blocks in one ivory card, retaining their array order and original sequence numbers. A rail and quiet separators organize the blocks; supplied measures precede a pale target group, followed by flags and complete source instructions. Zone, RPE, protocol and expected fallback targets retain the existing mapper precedence and additional targets. Required HR observation, optional protocol and technique wording remain explicit. No block-level elevated cards or inferred intervals were added.

`RpeIndicator` gives the existing exact labels/ranges persistent label emphasis. Workout Detail separates its summary, full source description/expected RPE, ordered sequence and expandable RPE explanations. The RPE reference is a growing pale secondary control with the original expanded-state semantics. Reference labels, training types and descriptions remain complete. The existing native modal, single scroll owner, supplied scroll props, focus behavior, close callback and hardware-back callback remain.

Only five production files and one existing test file changed; two files were added for shared facts and component regression coverage. No mapper, API type, source fixture, route, provider, owner, shell, V1 theme/component, training rule or mutation was changed. No Start workout action exists.

## Evidence and verification

The native review uses existing public `sourceWorkout`/`sourceSegment` fixtures. Run exercises the existing target-precedence/order test variant; Bike exercises the existing discipline enum variant; Swim preserves the cancelled mixed-measure source; distance-only preserves the existing sparse test variant. These are presentation fixtures, not new catalog prescriptions or translations of source instructions. Their English source strings remain unchanged in NL chrome. The seven reference captures map to Bike top, sparse distance-only, Run top/sequence/reference, and Swim top/instructions; the original live Run catalog capture is functional reference, not a raster/data fixture to reproduce.

A temporary development-only route rendered the actual `WorkoutDetailScreen` and inert candidate summary. An isolated loopback fixture bridge supplied the existing Week/Calendar owners for real detail entry/return. It stripped authorization/header/body data, rejected writes and left authentication untouched. Its request ledger contains 141 GET requests and zero mutations. Both temporary files were removed and the root layout restored byte-for-byte to accepted Batch 2. Accepted earlier dev hosts were retained.

The native review ran on `Pixel_4_API_35_2`, Android 15/API 35, `emulator-5554`, using the installed `com.adrivdbs.wombo` development client. The existing README Athlete A login was retained. No credentials or real athlete contents were recorded.

All seven original Workout Detail references and the Calendar detail-entry reference were visually inspected. Their content roles were exercised in native fixtures:

| Reference | Native coverage |
| --- | --- |
| S101 Bike top | Bike vector/title, date/state, supplied metrics and expected RPE |
| S102 distance-only | Swim distance without duration, cancelled state, sparse sequence |
| S103 Run top | Run summary and prescription hierarchy |
| S104 Run sequence | Exact supplied array order, measures, zone/RPE/protocol/fallback targets and instructions |
| S105 Run reference | Expand/collapse, full source range, training type and explanation |
| S106 Swim top | Swim vector, cancelled state and simultaneous time/distance |
| S107 Swim instructions | Full multiline source instructions and required observation flag |
| S029 Calendar detail entry | Actual Calendar owner entry, Close and Android Back restoration |

There are **22 native cases and 102 accepted captures**. Run covers every combination of reference width (~393 dp)/320 dp, 100%/200% text and NL/EN. Bike, mixed-measure Swim and distance-only Swim each cover reference/100% and 320/200% in both languages. Candidate anatomy covers reference/100% NL and 320/200% EN. Every lower viewport and applicable expanded RPE explanation was inspected; source strings stay verbatim in both locales.

Representative contact sheets: [NL Run reference](evidence/final-visual-batch-3/inspection/393-font-1-nl-run.jpg), [EN Run 320/200%](evidence/final-visual-batch-3/inspection/320-font-2-en-run.jpg), [EN Swim 320/200%](evidence/final-visual-batch-3/inspection/320-font-2-en-swim.jpg), [EN distance-only 320/200%](evidence/final-visual-batch-3/inspection/320-font-2-en-distance.jpg), [M5 candidate reference](evidence/final-visual-batch-3/inspection/393-font-1-nl-candidate.jpg) and [candidate 320/200%](evidence/final-visual-batch-3/inspection/320-font-2-en-candidate.jpg).

Calendar and Week return to the same selected destination, visible content bounds and scroll position after Close. Calendar also passes native Android Back. Detail keeps root destination actions outside its footprint. The [native audit](evidence/final-visual-batch-3/native-audit.json) compares text/labels/bounds and interactive selection; Android's incidental selected flag on a decorative child Text is excluded. The actual destination control's selected state is asserted separately before and after return. No origin behavior was modified.

Accessibility passed: 54 fully visible native controls meet the 48 dp minimum, allowing less than one physical pixel for integer endpoint rounding. Clipped controls at scroll boundaries are excluded from target measurements and remain reachable by scrolling. The RPE reference retains its 52 dp secondary minimum and expanded semantics; candidate controls use the accepted 56 dp CTA metrics and grow with text. Headings, dates, status, measures and instructions wrap naturally, with no line truncation, font shrinking or scaling clamp. Status is conveyed by icon and label, not color alone. Eight text/background contrast pairs pass 4.5:1; the lowest is 5.44:1. Existing reduced-motion handling is preserved.

Verification passed:

- Full mobile suite: **538 tests / 62 suites**, including component/token, mapper, boundary/origin, shell, provider and privacy coverage.
- Strict TypeScript and unused-code checks.
- Recursive privacy audit: 144 runtime public source files, zero findings.
- Source preservation: 198 of 204 baseline files unchanged; only the six scoped existing files differ. Two scoped files were added. Dependency manifest/lock fingerprints match the earlier accepted baseline.
- Native/content/target/origin audit, eight contrast pairs and SHA-256 evidence/source integrity.
- README credential evidence scan, read-only fixture request ledger, new-source whitespace and root/integrated-worktree diff checks.

The [verification summary](evidence/final-visual-batch-3/verification-summary.json), [scope audit](evidence/final-visual-batch-3/scope-audit.json), [contrast results](evidence/final-visual-batch-3/contrast.json), [test results](evidence/final-visual-batch-3/full-mobile-tests.json), [source cleanup](evidence/final-visual-batch-3/source-cleanup.json) and [device cleanup](evidence/final-visual-batch-3/device-cleanup.json) record the final gates. The fixture service was stopped and reverse port 8123 removed. Display density and font scale were restored to physical 440 dpi/100%; accessibility and motion settings match the accepted prior baseline. A fresh authenticated V2 root was verified after cleanup without fixture hooks. Metro and the emulator remain running.

Backend, Ruff, mypy, OpenAPI, database and RLS checks are not applicable because their implementation/contracts are unchanged. Physical Android/iOS, signing and release artifacts remain separate release gates; this batch concerns Android development-emulator visual acceptance.

**WOMBO UI V2 FINAL VISUAL BATCH 3 COMPLETE — WORKOUT VISUAL LANGUAGE ACCEPTED**
