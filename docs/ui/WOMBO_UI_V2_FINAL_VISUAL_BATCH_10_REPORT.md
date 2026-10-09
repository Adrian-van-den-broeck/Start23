# WOMBO UI V2 FINAL VISUAL BATCH 10 REPORT

Date: 2026-10-09. Baseline: accepted Batch 9, `5891858`. Branch: `feat/wombo-ui-v2-final-batch-10`.

Status: ACCEPTED. Profile, Onboarding and Goal meet the Batch 10 visual and interaction scope.

## Scope and direct reference

Batch 10 changes only Profile, the existing onboarding form presentation and Goal. The direct composition reference is `04-profile-onboarding.png`: centered WOMBO wordmark, quiet landscape with a fading lower edge, a literal task heading and explanation, ivory form cards, persistent field labels, pale semantic icon circles and forest save/confirm actions. Existing Profile destinations follow as icon rows. The [reference contact sheets](evidence/final-visual-batch-10/references-1.jpg) and [17 source hashes](evidence/final-visual-batch-10/reference-hashes.json) retain the M4 and functional comparison evidence.

Profile has no onboarding progress. Onboarding renders the existing owner's actual current step, seven-step total and completed steps, including physiology resume and version-upgrade guards. The branded header is centered without inserting a back action into onboarding. At narrow widths and large text, its wordmark and utility actions occupy separate rows; labels wrap and the entire header/progress/forms scroll inside the keyboard-aware viewport.

The implementation is split into three reviewable commits:

| Commit | Scope |
| --- | --- |
| A — `feat(ui): finalize batch 10 Profile forms` | Shared branded composition; existing profile fields, save and destinations; no progress |
| B — `feat(ui): finalize batch 10 Onboarding forms` | Actual progress, existing monitor/timezone/history/review; unchanged state owner |
| C — `feat(ui): finalize batch 10 Goal forms` | Existing race modes, all five race types, distance/time/pace, duration controls, optional splits/focus; final report and evidence |

## Preserved behavior

The [functional freeze](evidence/final-visual-batch-10/functional-freeze.json) compares the accepted source with the extracted forms. Profile validation and exact split physiology/identifying payloads remain. Device timezone detection, manual selection, explicit confirmation and history's independent previous-month baselines retain their defaults and predicates. Onboarding reads, resume guard, mutations, reload behavior and completion revision remain identical.

Goal retains its existing state, future-date normalization, required discipline mapping, validation, pace conversion and payload expression. All supported race types remain: run, bike, swim, triathlon and duathlon. Optional split times and focus remain; a pace edit clears the existing run split as before. The coming-later personal-goal panel can still be inspected, but it has no editable or saving flow. No achievement, maintenance, planner, physiology or new product behavior was added.

The existing DurationPicker gains an opt-in final appearance. Its existing ranges, 168-hour default maximum, 0–59 minute/second choices, clamping, exact seconds, optional clear and required semantics remain. Direct native Pressables preserve 48 dp targets, pressed state and visible keyboard focus rings. Goal validation now focuses the first existing invalid field; it does not introduce another validation condition. Input names keep units and optional qualifiers while required asterisks remain visual; errors are marked invalid and retain hints/alerts.

The existing Zones step keeps its inner setup/zone/calibration UI unchanged for Batch 11. This batch applies and verifies only its shared onboarding header and actual step-six shell. No authentication, navigation owner, API client/contract, parser, dependency, backend, database, ruleset or deployment file changes belong to this batch.

## Native evidence and limits

Native evidence uses the existing Pixel 4 Android 15/API 35 development client at 1080×2280 physical pixels. Each PNG has an XML hierarchy and JSON recording logical width, density, font scale, state and time. Widths are 320, 360, approximately 393 and 412 dp at default and 200% text. The [case ledger](evidence/final-visual-batch-10/case-ledger.json) and [inspection index](evidence/final-visual-batch-10/inspection-index.json) identify the captured viewports. Contact sheets combine unmodified viewports for inspection; they are not stitched live screens.

The temporary gallery renders actual production ProfileScreen/OnboardingScreen/GoalStep through typed inert public DTOs and the existing client. It blocks non-fixture transport, records exact request bodies and uses callback markers. Captures prove UI dispatch and presentation, not real backend persistence or physiological readiness. The visible fixture footer is outside the production screen and makes the tested scrolling area conservatively smaller. No athlete storage, credentials or live mutations are used. The original auth/router providers are restored before final tests.

Dutch is the existing source language of these forms. Supplied English goal-option labels and long names/focus are also reviewed. Fixed Dutch product copy is preserved; this batch does not manufacture a localization system.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Full mobile regression, restored production app | PASS — 62 suites, 564 tests, no skips | [Results](evidence/final-visual-batch-10/full-mobile-tests.json), [commands](evidence/final-visual-batch-10/command-checks.json) |
| Strict TypeScript and unused locals/parameters | PASS | [Log](evidence/final-visual-batch-10/typecheck.log) |
| Focused Profile/onboarding/resume/Goal/duration/primitives | PASS — 5 suites, 34 tests | [Results](evidence/final-visual-batch-10/focused-tests.json) |
| Native responsive matrix | PASS — 48 cases, 214 viewports, 54 inspected contact sheets | [Ledger](evidence/final-visual-batch-10/case-ledger.json), [visual review](evidence/final-visual-batch-10/visual-review.json) |
| Native progress/state/private-load checks | PASS — 201 checks | [Audit](evidence/final-visual-batch-10/native-state-audit.json) |
| Fully visible changed controls | PASS — 617 controls at least 48 dp, with 0.5 dp pixel tolerance | [Bounds](evidence/final-visual-batch-10/native-target-audit.json) |
| Exact callbacks, validation, locks and versioned completion | PASS — 24 native checks, inert transport only | [Interactions](evidence/final-visual-batch-10/native-interactions.json) |
| Keyboard, modal and first-error focus | PASS — Tab/Enter, visible focus rings, trigger focus restored, first invalid field focused | [Keyboard](evidence/final-visual-batch-10/keyboard-review.json), [visual observations](evidence/final-visual-batch-10/accessibility-visual-review.json) |
| Save controls above visible keyboard, 320 dp / 200% | PASS — complete labels and buttons reached through Tab without dismissing the IME | [Corrected audit](evidence/final-visual-batch-10/keyboard-save-audit.json), [Profile](evidence/final-visual-batch-10/keyboard-profile-save-reachable.png), [Goal](evidence/final-visual-batch-10/keyboard-goal-save-reachable.png) |
| Contrast | PASS — 12 source-token pairs | [Ratios](evidence/final-visual-batch-10/contrast.json) |
| Functional/scope/reference freeze | PASS — 28 checks, 17 unchanged references | [Freeze](evidence/final-visual-batch-10/functional-freeze.json) |
| Reduced motion / TalkBack | Modal remains operable with system animation scales zero; TalkBack observations and limits below | [Run](evidence/final-visual-batch-10/accessibility-native-run.json), [visual observations](evidence/final-visual-batch-10/accessibility-visual-review.json) |
| Fixture/process/device cleanup | PASS — production routes restored, fixture route/config removed, owned preview/emulator stopped, device settings restored | [Cleanup](evidence/final-visual-batch-10/cleanup.json), [accessibility settings](evidence/final-visual-batch-10/accessibility-cleanup.json) |

The resumed native interaction/keyboard checks ran on the same Android 15 Pixel 4 development-client family, AVD Pixel_4_API_35_2 / emulator-5556. [Source provenance](evidence/final-visual-batch-10/resumed-verification-provenance.json) records the exact production hashes. After the retained layout matrix, the only appearance refinement was adding missing duration-chooser and option focus overlays; field dimensions, labels and state were unchanged.

TalkBack was enabled for actual touch captures. The heart-rate input has a visually observed green focus outline. Pace mode activates and displays its checked state, but that synthetic-touch capture subsequently focuses the Lopen heading; it does not establish focus retention on the radio. Spoken announcements and physical-device behavior were not verified. Native keyboard focus, radio roles/states and callbacks are verified separately. These evidence limits do not claim a complete screen-reader or whole-app release audit.

Full-suite verification uses the accepted external date setup scoped only to two unchanged Batch 7 proposal tests whose fixtures name Wednesday, October 7. No assertions, production clocks, Jest configuration or other timers are changed. The rejected preliminary full run occurred with the temporary gallery root that deliberately omitted production providers; its RootLayout failure is retained separately and is not accepted evidence.

Superseded native runs are excluded from accepted counts. They include the initial status-bar/composition pass, a deep-link fixture-switch failure, centering refinement and rejected duration controls. The duration failure was identified from actual pixels and native bounds, then corrected with direct native controls and style arrays that preserve pressed/focus behavior. The audit also excludes clipped viewport-edge rectangles and the unchanged Batch 11 inner setup controls.

Backend/database checks are inapplicable to the unchanged stack. Physical iPhone/device and whole-app release gates remain outside this Android visual batch. TalkBack observations and limitations are recorded above and in accessibility-visual-review.json.

WOMBO UI V2 FINAL VISUAL BATCH 10 COMPLETE — PROFILE ONBOARDING AND GOAL ACCEPTED
