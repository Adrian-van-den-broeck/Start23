# Wombo UI V2 FINAL VISUAL BATCH 2 - shell and navigation

Completed: 2026-10-07. Native evidence: 2026-10-06–07. Prerequisite: Batch 1B accepted. Status: final shell accepted after Android emulator review and final source cleanup.

## Authority and runtime

The six [user mockups](mockups-final/) and the [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md), [token contract](WOMBO_UI_V2_FINAL_TOKENS.md), [screen mapping](WOMBO_UI_V2_FINAL_SCREEN_MAPPING.md), and [implementation sequence](WOMBO_UI_V2_FINAL_IMPLEMENTATION_SEQUENCE.md) govern this batch. The mockups were inspected individually. Functional behavior follows the current roadmap and retained integrated owners.

Runtime: `.worktrees/wombo-ui-v2-activities/mobile`, branch `feat/wombo-ui-v2-activities`, base HEAD `19c23d58f0b71aea01478df2306e2492a515e36e`. The root mobile checkout is historical; no parallel UI library was created. Final source/evidence fingerprints are recorded in the [accepted evidence manifest](evidence/final-visual-batch-2/accepted-evidence.json).

## Implementation scope

- Existing `TrainingLayout` keeps exactly Week, Calendar and Activities. Its custom footer uses the warm canvas, rounded ivory capsule, forest selection, semantic Lucide icons and visible labels. Profile remains a secondary action.
- Shared `AppHeader` and `ProfileAction` replace repeated V2 header JSX. Week uses ridges; Calendar and Activities use trees/river. Landscapes remain in scrolling content and finish before title text. Activities uses M6's display title role. Utility actions wrap onto separate rows at narrow widths or enlarged text.
- Shared task/detail `Screen` uses compact Back/Close headers with literal existing callbacks. The header shares the existing scroll view, so large text and keyboard layouts can scroll it away.
- The V2 global pending-RPE reminder occupies normal flow below the top safe area and above content. Its existing count, refresh owner, navigation callback and lock remain. V1 retains its original blur reminder and theme.
- Footer inset ownership prevents consuming the bottom safe area twice. The reminder owns the top inset when present. The existing detail footprint retains the last measured navigation height and remains noninteractive.
- Navigation labels switch together to icon-above-label at 320/360 dp, text scale >=1.5, or when native measurements show that any label will not fit. Labels, titles and actions wrap without line limits or font clamping.

No screen cards, Calendar controls, agenda/grid, activity forms, domain/API contracts, providers, routes, owner lifetimes, onboarding decisions, unsafe locks or root-switch behavior were migrated. The three protected screen body sections are byte-identical to HEAD: [body scope audit](evidence/final-visual-batch-2/body-scope-audit.json). No new dependencies, palette values or spacing scales were added.

The Batch 2 delta is eight existing files and five new files: six existing production composition files, two existing test files, and five shared component/test files. Of the 203 baseline files, 195 remain byte-identical. The [scope audit](evidence/final-visual-batch-2/scope-audit.json), [51 protected source fingerprints](evidence/final-visual-batch-2/protected-source-audit.json) and [provider/V1 audit](evidence/final-visual-batch-2/provider-v1-audit.json) document the boundaries. Accepted Batch 1A/1B changes were preserved.

Final verification crossed midnight in Amsterdam. Two existing workout-move assertions expected `Wednesday 7 October`, while the unchanged production model correctly added its Today label using the plan timezone. The test now freezes Date at its fixture's 6 October noon and retains real asynchronous timers. All original assertions remain; no owner, date semantics or production behavior changed. The isolated ten-test suite passed before the final full run. Both diagnostic full-suite failures remain recorded, including the unsuccessful process-timezone attempt.

## Automated verification

| Check | Result |
| --- | --- |
| Full mobile suite after final production edits | 530 tests / 61 suites PASS |
| Affected shell/navigation/owners/detail suites | 77 tests / 5 suites PASS |
| Strict TypeScript | PASS |
| Unused-code check | PASS |
| Shell contrast | Seven source-derived pairs PASS; muted text/ivory 5.79:1, selected text/forest 9.60:1, reminder text/pale surface 8.26:1 |
| Recursive athlete-facing source privacy | 143 runtime files scanned; zero findings |
| Native targets | 288 checks PASS; source minimum 48 dp |
| Narrow / enlarged navigation layout | 52 required stacked captures PASS |
| Native origins, reminder, gate and keyboard | 21 structural checks PASS |
| Scope fingerprints, temporary-host removal and diff checks | PASS |

Evidence: [final verification summary](evidence/final-visual-batch-2/verification-summary.json), [full suite](evidence/final-visual-batch-2/mobile-tests.json), [full log](evidence/final-visual-batch-2/mobile-tests.log), [affected suites](evidence/final-visual-batch-2/shell-navigation-tests.json), [TypeScript](evidence/final-visual-batch-2/typecheck.log), [unused](evidence/final-visual-batch-2/unused.log), [contrast](evidence/final-visual-batch-2/contrast.json), [before fingerprints](evidence/final-visual-batch-2/baseline.json).

## Native evidence

Android emulator `emulator-5554`, AVD `Pixel_4_API_35_2`, Android 15, 1080x2280, OS locale en-US. App language uses existing NL/EN preferences supplied only in memory by the public fixture bridge. Widths 320, 360, approximately 393 and approximately 412 dp are produced by density 540, 480, 439 and 420 respectively. Font scales are 1 and 2. The emulator was restarted and README Athlete A signed in through the existing native password form; credentials were never recorded in screenshots, source or logs.

Actual integrated routes/controllers use existing public test DTOs. The loopback fixture service strips authorization/header/body data and rejects every mutation. No Generate, Save or RPE choice was activated. A separate temporary development-only host exercises deliberately long public labels through the same shared shell components.

The final [matrix](evidence/final-visual-batch-2/matrix-ledger.json) contains 64 accepted captures: four widths × two font scales × two languages × Week/Calendar/Activities/long-label composition. All 16 contact sheets were inspected. Another 16 lower-viewport captures prove that long labels remain reachable at 200% text. Narrow/enlarged navigation consistently places every icon above its label, with aligned icon rows and natural label wrapping. The final manifest explicitly indexes 114 native captures and excludes diagnostic, stale, prompt and unsettled frames.

Native review verified all three selected destinations, secondary Profile access and return to Calendar, exact Week/Calendar detail origin restoration, hidden/noninteractive root navigation in tasks/details, activity task entry/return, pending-RPE placement at reference and 320 dp/200% NL, feedback entry/return, and onboarding gates from both Calendar and Activities deep entries. Keyboard evidence at reference and 320 dp/200% proves the lower Save control is fully above the IME; no Save was activated. Existing owners, providers, origin callbacks and unsafe locks are unchanged.

Evidence: [native flow audit](evidence/final-visual-batch-2/native-flow-audit.json), [navigation layout audit](evidence/final-visual-batch-2/native-label-layout-audit.json), [target audit](evidence/final-visual-batch-2/native-target-audit.json), [fixture audit](evidence/final-visual-batch-2/fixture-audit.json). Native hierarchy bounds use integer physical pixels; target checks permit less than one physical pixel of endpoint rounding below the exact 48 dp conversion (lowest measured height 47.745 dp). Source styles and component assertions retain the actual 48 dp minimum.

TalkBack 15.0.0.639625893 was verified through actual emulator touchscreen events, using one console connection for timed double taps. Week, Calendar and Activities received accessibility focus and activated the correct destination. Week restored focus to its heading; Profile received focus and opened the secondary profile. UIAutomation was not used while TalkBack was enabled. Screenshots record native focus, while source/component assertions verify roles, labels, selected/disabled state and decorative landscape exclusion; speech audio was not recorded. [Accessibility review](evidence/final-visual-batch-2/accessibility-review.json) indexes only these successful captures. Reduced-motion evidence was captured with all three Android animation scales set to zero and then restored. Selection has both semantic selected state and icon/label treatment; labels never rely on color alone. No title/action text overlaps decorative landscape art.

The temporary bridge and gallery were removed and the root layout restored byte-for-byte. Existing accepted asset/primitive development hosts remain. The fixture service is stopped and its 8123 adb reverse removed; Metro forwarding remains for the running emulator. Font scale 1.0, physical density 440, accessibility services, notification permission flags and all animation settings are restored to their original values. A fresh app process without the bridge restored README Athlete A's authenticated session; the existing development switch selected V2. The emulator and integrated Metro remain running for review. [Source cleanup](evidence/final-visual-batch-2/source-cleanup.json), [device cleanup](evidence/final-visual-batch-2/device-cleanup.json) and [sign-in verification](evidence/final-visual-batch-2/login-review.json) record these checks without real athlete contents.

Backend, Ruff, mypy, OpenAPI, database and RLS suites are not applicable: their sources/contracts/dependencies are unchanged. Physical Android/iOS, signing and release artifacts remain separate release gates; this report concerns Android development-emulator acceptance of the shared shell only.

WOMBO UI V2 FINAL VISUAL BATCH 2 COMPLETE — FINAL SHELL ACCEPTED
