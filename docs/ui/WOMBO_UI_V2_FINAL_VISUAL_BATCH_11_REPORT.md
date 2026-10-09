# WOMBO UI V2 FINAL VISUAL BATCH 11 REPORT

Date: 2026-10-09. Baseline: accepted Batch 10, f25379d. Branch: feat/wombo-ui-v2-final-batch-11.

Status: Batch 11 implementation and Android visual review accepted. Scope is only Zones and the current calibration lifecycle; the release/accessibility limits below remain open.

## A — Zones overview/history

Direct visual target: [03-zones.png](evidence/final-visual-batch-11/target-03-zones.png). The existing route now uses the branded WOMBO header and fading landscape, ivory profile/context hero, real discipline count and plan context, discipline cards, forest icons in pale circles, status chips, divided route/info rows, forest actions and supplied zone tables/history. At narrow widths and large text, the hero, card identity and zone ranges stack; labels and source metadata wrap.

Active, pending and superseded profiles retain their separate blocks and original versions. Numeric-free states remain numeric-free. The complete numeric subtree is guarded by values_hidden, including primary and secondary metrics, boundaries and accessibility output. Source method, quality, review status, model and evidence provenance remain visible. Values retain their supplied precision, metric units and open bounds; run pace uses the existing formatter. No client zone calculation or historical reinterpretation was introduced.

Commit A: cbf19de — feat(ui): finalize batch 11 Zones overview and history.

## B — Calibration lifecycle

M3 cards and [M4 form language](evidence/final-visual-batch-11/target-04-profile-onboarding.png) apply to the existing ZoneSetupStep and CalibrationScreen: current server-provided route labels, known thresholds/source choices, optional five-boundary overrides, reviewed protocol choices, actual segment forms, canonical RPE drafts, measured fields/units, observation submission, prior evaluations and independent decisions. Input labels persist, focus/invalid presentation uses the accepted Input, and phone observation checkboxes and compact boundary columns reflow into full-width rows. The calibration header says Terug because its existing callback returns to the previous route or planning. Shared header callers retain their Week default.

The original loading/state owners, validation, parsers, defaults, predicates, idempotency, immutable segment identities, payloads and version preconditions are unchanged. RPE selection changes a draft; it does not save an observation. Observation submission, threshold confirmation/rejection and zone approval/rejection remain separate operations. An accepted threshold still produces a pending zone proposal; only the existing explicit zone action can apply it. No-protocol and incomplete-result states offer no invented execution or successful completion.

[Current protocol projections](evidence/final-visual-batch-11/current-protocol-projections.json) were exported read-only from the unchanged CalibrationService. [Provenance](evidence/final-visual-batch-11/protocol-provenance.json) records the source hashes. Additional tests and native source-backed forms cover the current run/bike optional blocks and the two swim repetition blocks. Existing test evaluations exercise result presentation and decision dispatch only; they are not evidence of an actually executed physiological calibration.

Commit B: feat(ui): finalize batch 11 calibration lifecycle — current forms, lifecycle coverage and review evidence.

## Verification and evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Strict TypeScript, including unused locals/parameters | PASS | [Log](evidence/final-visual-batch-11/strict-types-production.log) |
| Focused Zones/calibration and recursive privacy tests | 5 suites, 35 tests PASS | [Log](evidence/final-visual-batch-11/focused-production.log) |
| Full mobile suite, restored production roots, documented fixture clock | 63 suites, 583 tests PASS | [Log](evidence/final-visual-batch-11/full-mobile-production.log), [commands](evidence/final-visual-batch-11/command-checks.json) |
| Native visual matrix | 51 cases, 357 viewports, all 138 contact sheets inspected | [Visual review](evidence/final-visual-batch-11/visual-review.json), [index](evidence/final-visual-batch-11/inspection-index.json) |
| Native states/privacy and 48 dp controls | 232 checks, 597 fully visible controls PASS | [States](evidence/final-visual-batch-11/native-state-audit.json), [controls](evidence/final-visual-batch-11/native-target-audit.json) |
| Exact UI dispatch/validation, inert transport | 10 checks PASS, no backend writes | [Requests](evidence/final-visual-batch-11/native-interactions.json) |
| Native keyboard | Tab/Enter back and source choice; complete nested Save above IME at 320 dp / 200% PASS | [Keyboard](evidence/final-visual-batch-11/keyboard-review.json), [visual inspection](evidence/final-visual-batch-11/keyboard-visual-review.json) |
| Reduced motion | Zero-scale cold boot; zone decision and observation action reachable | [Review](evidence/final-visual-batch-11/accessibility-visual-review.json) |
| TalkBack-enabled captures | Source choice activated/checked and threshold result displayed; target focus retention and speech remain unverified | [Observed limits](evidence/final-visual-batch-11/accessibility-visual-review.json), [threshold capture](evidence/final-visual-batch-11/talkback-threshold-decision.json) |
| Contrast / source protection | 7 contrast pairs PASS; 12 reference hashes and protected scopes unchanged | [Contrast](evidence/final-visual-batch-11/contrast.json), [references](evidence/final-visual-batch-11/reference-protection-final.json), [scope](evidence/final-visual-batch-11/scope-audit-final.json), [handlers](evidence/final-visual-batch-11/functional-freeze.json) |

The native gallery renders the actual production screens on the existing Android 15/API 35 Pixel 4 client, with typed inert public DTOs and blocked live transport. Each PNG has XML and JSON with state, density, font scale and time. Contact sheets arrange captured scrolling viewports; they do not stitch or simulate a live screen. Callback evidence verifies exact UI requests, not backend persistence. Fixture roots/config are removed and production auth/router providers restored before final integration checks.

Widths are 320, 360, approximately 393 and 412 dp at default and 200% text. Dutch source copy, the existing English pain warning, and long English protocol/source identifiers are reviewed; this batch does not add a localization system. Long described radio rows may span a scrolling viewport at 200% text. Their fully visible labels and at least 48 dp visible touch regions remain selectable without shrinking or hiding the description; clipped edge rectangles are excluded from whole-control size counts.

Superseded captures are excluded. Native review caught cramped status/hero wrapping and observation checkbox rows; those layouts were corrected and their affected states recaptured. The stale cached observation bundle is retained only as rejected evidence. Inert-driver runs with inverted field bounds, duplicate development-client roots and an Android numeric-input timeout were rejected separately; their corrections and emulator recovery are recorded in native-driver-notes.json. Production source was unchanged during these corrections. Final-6 captures require the fresh cache-cleared marker. Retained final-5 overview/history/result/known states are unaffected by the later observation/boundary column refinement.

Full-suite verification retains the normal Jest setup and the accepted external clock setup scoped only to two unchanged proposal tests whose fixtures name Wednesday 7 October. The unadjusted-date run retains its two known fixture-date failures. A preliminary command that omitted the normal Jest setup is rejected evidence, not a production failure; assertions/configuration were not weakened.

Production root routes are restored byte-for-byte to accepted Batch 10; the executable fixture module and public polling config are removed. [Root proof](evidence/final-visual-batch-11/production-roots-restored.json). The owned emulator is restored to physical density 440 and font scale 1.0; keyboard, accessibility, animation and notification-permission settings are restored. Port reversal is removed and only the owned emulator/Metro processes are stopped. [Device](evidence/final-visual-batch-11/device-restored.json), [accessibility cleanup](evidence/final-visual-batch-11/accessibility-cleanup.json), [keyboard cleanup](evidence/final-visual-batch-11/keyboard-cleanup.json), [processes](evidence/final-visual-batch-11/process-cleanup.json).

Open verification gates: physical devices/iOS, spoken screen-reader behavior and TalkBack target focus retention. The enabled-service threshold capture displays the real pending result, but its exact hierarchy target was unavailable after service activation; no threshold touch or retained focus is claimed. These captures do not verify physiological execution, server persistence or whole-app release readiness.

No authentication/navigation owner, API contract/client, dependency, parser, physiology/backend, database migration, ruleset or deployment change belongs to this batch. Backend/database checks are inapplicable to that unchanged stack. Android visual and dispatch evidence does not close physical iPhone/device, spoken screen-reader or whole-app release gates.

WOMBO UI V2 FINAL VISUAL BATCH 11 COMPLETE — ZONES AND CALIBRATION ACCEPTED
