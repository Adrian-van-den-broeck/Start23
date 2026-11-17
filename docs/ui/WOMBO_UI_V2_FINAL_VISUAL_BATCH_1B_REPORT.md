# Wombo UI V2 final visual Batch 1B - final tokens and shared primitives

Date: 2026-10-06. Scope: Batch 1B only. Implementation, automated checks and native review are complete.

## Authority and implementation checkout

Prerequisite: [Batch 1A](WOMBO_UI_V2_FINAL_VISUAL_BATCH_1A_REPORT.md) ends `WOMBO UI V2 FINAL VISUAL BATCH 1A COMPLETE — ICONS AND LANDSCAPES ACCEPTED`. This batch follows the [FINAL token contract](WOMBO_UI_V2_FINAL_TOKENS.md), [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md), and its M4/M5 primitive recipes. The earlier token document and its old-value assertions are superseded for V2.

Implementation remains in `F:\Projecten Business\Start23\Code\.worktrees\wombo-ui-v2-activities`, branch `feat/wombo-ui-v2-activities`, HEAD `19c23d58f0b71aea01478df2306e2492a515e36e`, with the accepted uncommitted Batch 1A assets/dependencies preserved. The root checkout remains on its existing branch. No commit, branch switch, push, deployment or native rebuild was performed.

Read root/mobile instructions and current roadmap constraints. No backend, API, database, physiological rule, plan/zone/activity mutation, state owner, parser or product navigation change belongs to this batch.

## Implementation

All paths below are relative to the integrated `mobile/` directory. The existing `src/ui-v2` system is the only V2 component/token source.

| Area | Final implementation |
| --- | --- |
| `tokens/colors.ts` | Exact final canvas, forest, pale green, text, muted and decorative border; unchanged status/sport/control colors. Secondary aliases primary.soft; focus aliases primary. Landscape sage/sun live here. |
| `assets/assetColors.ts` | Compatibility aliases to the same V2 palette. No second hex palette remains. Accepted landscape/vector geometry and colors are preserved. |
| `tokens/typography.ts` | Native system sans. Final display 36/42/800, screen 30/36/800, section 24/30/700, card 22/28/700, label 16/22/600, CTA 18/24/600, navigation 14/20/600. Body/supporting/caption/numeric roles retained. |
| `tokens/layout.ts` | Retained 4/8/12/16/24/32/48 spacing; button radius 16; other radii retained. Form padding aliases focus padding. Responsive focus/form padding is 24 at width >=393 and font scale 1, otherwise 16. Field groups 24, label/field 8, field/help 4. Primary/secondary/field minima 56/52/56; multiline 112; target 48; segment track 56 with 4 inset. Shared disc, gap, future nav/utility/artwork roles are defined without migrating consumers. |
| `tokens/shadows.ts` | One soft card/nav level: forest .06, offset 0/3, radius 12, Android elevation 2. Lift: .12, 0/4, radius 16, elevation 6. Fields, list rows and discs have no shadow. |
| `primitives/Text.tsx` | Existing scalable text, expanded semantic tones; normal system font and native wrapping. No font fitting, multiplier cap or line clamp introduced. |
| `primitives/Card.tsx` | Existing ivory card, standard/focus/form padding and optional shared soft elevation. No new HeroCard/FormCard library. |
| `primitives/Button.tsx` | Existing synchronous/async submission lock retained. Primary, secondary, outline and compatible tertiary variants; final CTA typography/padding/radius, minimum targets, optional trailing semantic icon. Disabled fill remains solid/readable; busy retains label and spinner. Supplied checked/selected state has a real check icon. Focus overlay does not change layout. |
| `primitives/Input.tsx`, `FormField.tsx` | Persistent label, localized optional qualifier, unit, helper, icon, error, disabled reason and read-only value. Single-line default; multiline minimum 112. Native focus/change/blur callbacks and explicit editability retained. Read-only text announces label and value without becoming an editor. Accessible unit/error copy survives reflow. Error has a destructive boundary, warning icon and alert text. Stable 2dp focus/error overlay over 1dp normal boundary. |
| `primitives/Divider.tsx`, `Skeleton.tsx` | Final decorative border/subtle fill inherited; divider and existing static skeleton excluded from accessibility. No shimmer or fake data. Skeleton's existing placeholder shape remains. |
| `primitives/IconTile.tsx` | Decorative 40/48/64dp circles with accepted 20/24/32dp icons; forest or explicit discipline tone, no shadow or hit target. |
| `primitives/Notice.tsx` | Info/warning/error/success soft fill with explicit icon, title, full body and optional existing Button action. Severity never depends on color alone. |
| `primitives/ChoiceRow.tsx` | Controlled radio/checkbox row; checked semantics and visible check; stable selected/focus overlay. Disabled rows suppress callbacks and expose a reason. |
| `primitives/SegmentedControl.tsx` | Controlled exclusive radio group. Measured localized labels determine horizontal fit; insufficient width and >=1.5 font scale stack options. Each target >=48dp. Selected option has forest fill, check and checked semantics; no label shrinking. |

Existing V2 consumers inherit shared tokens/primitives as intended. No actual screen-family composition was restyled. V1 theme, styles, components and routes retain their original bytes; no Tailwind/global theme source was changed.

## Development-only review composition

`app/dev-primitives.tsx` and `src/ui-v2/dev/PrimitiveGallery.tsx` follow the already accepted dev-assets policy: no product navigation link; direct URL only; route redirects to `/` in release; composition returns null in release. Both guards are tested. Retained safely under that existing development policy for reproducible follow-up review.

Example: `wombo:///dev-primitives?section=form&language=nl`. Valid sections are form/workout/notices/states; languages are nl/en. Invalid parameters fall back to form/en.

The form uses visibly labeled synthetic values and local field state. The workout anatomy uses the existing public `sourceWorkout` DTO fixture from `utils/workout.test-fixtures.ts`; supplied name, description and duration remain unchanged. Its source strings are intentionally English in both language modes. Surrounding interface and long state/help/error copy are supplied in Dutch and English. This is a presentation fixture, not an eligible live catalog candidate or a successful athlete operation. All CTA handlers are inert; choice/segment changes affect only local review state. No API client or training owner is imported.

Review composition covers M4 labels/icons/units/help/errors, M5 sport/title/metric/source/action anatomy, all three task button variants, disabled/busy/read-only/focused/error states, all Notice tones, selected/unselected/disabled radio and checkbox rows, segments, disc sizes/sport tones and static skeleton. Content uses one scroll owner and safe-area layout. Narrow/large text moves units into persistent labels, moves decorative field icons above the editor, stacks workout facts and segments, and permits all action/message text to wrap.

## Native review evidence

Device: existing `emulator-5554`, Pixel_4_API_35_2, Android 15/API 35, x86_64, installed SVG-capable Batch 1A development client `com.adrivdbs.wombo`. Physical display 1080 x 2280. Existing Metro at `127.0.0.1:8081` was verified to serve the integrated worktree and reused. No dependency installation, APK rebuild or reinstall was necessary.

Requested reference ~393dp is **393.62dp** at density 439; narrow width is **320.00dp** at density 540. Reference density intentionally falls on the >=393 focus-padding side of the documented rule. The normal emulator density is 440 (392.73dp). Font scales 1.0 and 2.0 use native Android scaling, without a cap. OS locale stays en-US; review interface language is explicitly NL or EN, independently of athlete settings. Every PNG has adjacent hierarchy XML and UTC/device JSON. Exact source/file hashes are retained in the evidence manifest.

The evidence includes top and scrolling lower viewports for each of the 32 section/width/font/language combinations. Contact sheets are inspection aids made from labeled captures of the same case; individual PNGs remain the native evidence. Repeated bottom images represent reaching the scroll end, not fabricated extra states. Initial-form is an intermediate diagnostic. Early reference captures were refreshed after boundary refinement; large-text NL top framing was refreshed after the review host began resetting scroll per section/language.

Reviewed all 32 labeled contact sheets (96 matrix PNGs), with individual native images inspected for M4/M5 comparison, 320dp/200% reflow, focus, lower actions and icon/skeleton detail. No remaining Batch 1B primitive visual defect was found.

| Width | Text | Language | Form | Workout | Notices | States |
| --- | --- | --- | --- | --- | --- | --- |
| ~393 dp | 100% | NL | [form](evidence/final-visual-batch-1b/inspection-form-393-font-1-nl.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-393-font-1-nl.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-393-font-1-nl.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-393-font-1-nl.jpg) |
| ~393 dp | 100% | EN | [form](evidence/final-visual-batch-1b/inspection-form-393-font-1-en.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-393-font-1-en.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-393-font-1-en.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-393-font-1-en.jpg) |
| ~393 dp | 200% | NL | [form](evidence/final-visual-batch-1b/inspection-form-393-font-2-nl.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-393-font-2-nl.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-393-font-2-nl.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-393-font-2-nl.jpg) |
| ~393 dp | 200% | EN | [form](evidence/final-visual-batch-1b/inspection-form-393-font-2-en.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-393-font-2-en.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-393-font-2-en.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-393-font-2-en.jpg) |
| ~320 dp | 100% | NL | [form](evidence/final-visual-batch-1b/inspection-form-320-font-1-nl.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-320-font-1-nl.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-320-font-1-nl.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-320-font-1-nl.jpg) |
| ~320 dp | 100% | EN | [form](evidence/final-visual-batch-1b/inspection-form-320-font-1-en.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-320-font-1-en.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-320-font-1-en.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-320-font-1-en.jpg) |
| ~320 dp | 200% | NL | [form](evidence/final-visual-batch-1b/inspection-form-320-font-2-nl.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-320-font-2-nl.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-320-font-2-nl.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-320-font-2-nl.jpg) |
| ~320 dp | 200% | EN | [form](evidence/final-visual-batch-1b/inspection-form-320-font-2-en.jpg) | [workout](evidence/final-visual-batch-1b/inspection-workout-320-font-2-en.jpg) | [notices](evidence/final-visual-batch-1b/inspection-notices-320-font-2-en.jpg) | [states](evidence/final-visual-batch-1b/inspection-states-320-font-2-en.jpg) |

Additional native proof: [focused field with keyboard](evidence/final-visual-batch-1b/form-focused-keyboard.png), [keyboard dismissed with stable focus](evidence/final-visual-batch-1b/form-focused-keyboard-dismissed.png), [320dp NL form footer](evidence/final-visual-batch-1b/form-footer-320-font-1-nl.png), [320dp EN form footer](evidence/final-visual-batch-1b/form-footer-320-font-1-en.png), [320dp complete controls/icons/skeleton](evidence/final-visual-batch-1b/controls-footer-320-font-1-en.png), [reference icons/skeleton](evidence/final-visual-batch-1b/icons-skeleton-reference.png), [320dp/200% icon circles](evidence/final-visual-batch-1b/icons-skeleton-320-font-2.png).

| Criterion | Native assessment |
| --- | --- |
| M4 form anatomy | Accepted: persistent labels and optional qualifiers, pale field circles, accessible outline, quiet units, clear helper/error, ivory form and forest submit. The stronger control boundary is intentional under the final contrast contract. |
| M5 workout anatomy | Accepted: large sport disc beside wrapping title/chip, supplied duration and effort groups, source description, forest Choose and pale Skip, outline Undo; restrained card lift. Fixture sport/source copy deliberately differs from raster sample data. |
| CTA metrics | Primary/secondary minima are 56/52, 18/24 label, 16dp horizontal/vertical padding and 16dp radius. Actual heights may exceed minima due to content and border. Labels wrap naturally; no text height is fixed. |
| 320dp and 200% text | Accepted: field units remain in labels, field icons/facts reflow, choice/help/error/source/action text wraps and the footer remains reachable. Large text uses 16dp card padding. Extra footer captures prove controls beyond the initial viewport; viewport edge crops are not content truncation. |
| Notices and state cues | Accepted: four explicit titles/icons/bodies; selected choices/segments show checks and checked semantics; disabled copy stays readable; busy spinner retains its label. |
| Targets | **264 fully visible native target measurements PASS; minimum height 48.0dp**, minimum measured width 137.78dp. [Target audit](evidence/final-visual-batch-1b/native-target-audit.json) excludes viewport intersections of scrolled partially visible controls and preserves signed XML coordinates. Component tests separately verify 48dp minima. |
| Focus and contrast | Accepted: field focus shows stable 2dp forest boundary with keyboard open; input/value geometry does not shift; error stays explicit. Opaque component fills use the verified contrast pairs. |
| Decoration | Accepted: measured discs are unchanged accepted icons at the specified scales; no extra accessibility targets; divider/skeleton are static and hidden. |

One early focus capture attempt followed Android activity recreation before the form settled. It produced no accepted focus image; the retry observed the actual editable field and captured the final native focus/keyboard states. The review host resets scroll per section/language to avoid mislabeled top captures. No product navigation behavior was changed to recover review tooling.

Final restoration: density reset to original physical **440**, font scale **1.0**, OS locale en-US, authenticated V2 Week route. [Restored Week](evidence/final-visual-batch-1b/week-restored.png), [device record](evidence/final-visual-batch-1b/week-restored.json). No training action was invoked. [Capture ledger](evidence/final-visual-batch-1b/capture-ledger.json) and [source/evidence manifest](evidence/final-visual-batch-1b/evidence-manifest.json) retain individual paths, device values and hashes.

This accepts the shared primitives and requested development composition only. Shell/navigation, actual workout summaries and all later screen families still need their own visual batches. Native 360/412dp cross-family rendering, physical-device, release and TalkBack verification remain later gates; this batch's requested native matrix is reference/320dp, NL/EN and default/200% text.

## Automated verification

| Check | Result |
| --- | --- |
| Full mobile suite after final runtime edits | **523 tests / 60 suites PASS** |
| Final affected token/primitives/assets/privacy suites | **21 tests / 5 suites PASS** |
| Strict TypeScript | PASS |
| Unused-code | PASS |
| FINAL token contract | Every color and typography table entry checked against the authoritative file; old-value tests replaced because FINAL explicitly supersedes them |
| Contrast arithmetic | PASS, unrounded comparisons. Supplemental 22 pairs include all required text/status/sport/control/focus combinations; text/canvas 16.48:1. Component token tests additionally cover destructive text on ivory. |
| Recursive source privacy | PASS, 139 non-test src/app files; no prohibited private-data or secret markers |
| Scope fingerprints | 195 pre-existing mobile source/config files recorded; exactly 12 intentional existing-file changes, 183 unchanged, 9 new files. Screen-family, controller, navigation, V1 and package/config fingerprints unchanged. |
| Hex/clamp checks | Zero new hex values outside the palette; no font fitting, multiplier caps or line counts in primitives |
| Git diff whitespace | PASS in root and integrated worktree; preserved pre-existing root changes |

Evidence: [full tests](evidence/final-visual-batch-1b/mobile-tests.json), [test log](evidence/final-visual-batch-1b/mobile-tests.log), [focused tests](evidence/final-visual-batch-1b/final-focused-tests.json), [TypeScript](evidence/final-visual-batch-1b/typecheck.log), [unused](evidence/final-visual-batch-1b/unused.log), [contrast](evidence/final-visual-batch-1b/contrast.json), [scope audit](evidence/final-visual-batch-1b/scope-audit.json), [before fingerprints](evidence/final-visual-batch-1b/baseline.json), [native capture helper](evidence/final-visual-batch-1b/native-review.py).

Backend/Ruff/mypy/OpenAPI/database/RLS suites are not applicable: no corresponding source, contract or dependency was changed. Existing physical Android/iOS, Apple signing, TalkBack device interaction, release APK and later screen-family focus/inset/navigation gates remain open. Primitive semantics/unit tests and these Android development renders do not claim those broader gates passed.

WOMBO UI V2 FINAL VISUAL BATCH 1B COMPLETE — FINAL PRIMITIVES ACCEPTED
