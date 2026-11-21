# Wombo UI V2 FINAL VISUAL BATCH 4 — Week / Home

Date: 2026-10-07. Prerequisite: Batch 3 accepted. **Week accepted. All applicable Batch 4 implementation, native visual and verification gates passed.**

## Authority and scope

The [precise Week derivation](WOMBO_UI_V2_FINAL_SCREEN_MAPPING.md), [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md), [tokens](WOMBO_UI_V2_FINAL_TOKENS.md) and [sequence](WOMBO_UI_V2_FINAL_IMPLEMENTATION_SEQUENCE.md) govern this batch. [M6](mockups-final/06-activities.png) supplies the title/Profile composition; [M5](mockups-final/05-workout-selection.png) supplies the training-card anatomy. The complete twelve-image Week reference family was reviewed for content and state meaning. The provisional scaffold is not the visual target.

Runtime: `.worktrees/wombo-ui-v2-activities/mobile`, branch `feat/wombo-ui-v2-activities`, base HEAD `19c23d58f0b71aea01478df2306e2492a515e36e`, including the accepted Batch 3 working-tree changes. The root mobile checkout is older and was not substituted for this integrated runtime.

## Implementation

Week uses a 36/42 title and the accepted Profile pill on one root header row, with the accepted static ridges and bounded 140 dp fade. At narrow widths or enlarged text, the controls stack and the art uses its existing 96 dp variant and text veil. The literal week range follows at 12 dp, with 16 dp before the first card. The original WeekContext date formatting and accessible full-date range are unchanged.

NextSession composes the accepted Batch 3 WorkoutSummary with its sport circle/capsule, exact title, supplied date/status, supplied measures and effort, retained source description, and a forest detail CTA. A small optional context slot puts the existing Today/count or next-date context inside the first ivory card. Other summary callers have no visual change. Every same-day sibling gets a complete independently actionable ivory card at 12 dp separation; no execution order is inferred.

No-plan, selection, placement and pending-only states use a lifted ivory task card with a pale explicit status capsule and the existing forest action. Rest-only uses an ivory rest statement and literal 0-of-0 supporting progress. Active+pending keeps approved occurrences and progress authoritative; pending review remains a separate pale attention row. Proposed occurrences never replace active workouts.

Progress stays plain supporting text 12 dp below the cards. View week is a vector-icon ActionRow. Attention follows at 24 dp, retaining the original filtered count, priority, two-item limit and show-all/show-less behavior. Warning rows use an amber surface and explicit warning icon/text. Training tools form one ivory group with icon circles and dividers beginning at the text inset. The supplied goal follows at 24 dp in its own ivory action group.

No backend, API, domain, mapper, provider, route owner, shell, dependency, V1 theme, translation, training rule or mutation is changed. No readiness, private load, percentage gauge, clock time, countdown or new action is introduced. Existing development comparison controls remain development-only.

## Native evidence

Evidence uses the actual WeekScreen, accepted shell/navigation/reminder components and existing public planning/workout DTO fixtures. Task/navigation callbacks in the temporary gallery are inert; the read-only detail modal is real. These are explicitly fixture captures, not live-server transition evidence. No backend bridge or authentication override is installed. The temporary gallery was removed after verification. A state-specific native fixture marker protects captures against an unsettled return to the live root. One rejected unsettled capture was removed, including its XML/JSON/contact sheet; accepted evidence contains public fixtures only. Transient development refresh overlays were rejected and recaptured.

The source fixture date is 5–11 October 2026. Workout measures and descriptions come from existing public test fixtures; the long sibling title and sparse optional-data variants exercise existing supported shapes. English source descriptions remain verbatim in Dutch chrome.

Native review: existing Pixel_4_API_35_2, Android 15/API 35, `emulator-5554`, installed `com.adrivdbs.wombo` development client. Reference-width captures use 439 dpi (393.62 dp), matching accepted Batch 3 and exercising the final 24 dp focus-card padding. Per-capture JSON records UTC, physical size, density, font scale, language/state and provenance. PNG/XML/JSON evidence lives in [final-visual-batch-4](evidence/final-visual-batch-4/).

| Reference | Week state | Reference-width fixture evidence |
| --- | --- | --- |
| S089 | Active approved | [Active](evidence/final-visual-batch-4/inspection/393-font-1-nl-active-1.jpg) |
| S090 | Pending proposal | [Pending](evidence/final-visual-batch-4/inspection/393-font-1-nl-pending-1.jpg) |
| S092 | Selection in progress | [Selection](evidence/final-visual-batch-4/inspection/393-font-1-nl-selection-1.jpg) |
| S093 | Placement in progress | [Placement](evidence/final-visual-batch-4/inspection/393-font-1-nl-placement-1.jpg) |
| S094 | No plan | [No plan](evidence/final-visual-batch-4/inspection/393-font-1-nl-noPlan-1.jpg) |
| S095 | Warning | [Warning](evidence/final-visual-batch-4/inspection/393-font-1-nl-warning-1.jpg) |
| S096–S097 | Multiple same-day workouts | [Siblings](evidence/final-visual-batch-4/inspection/393-font-1-nl-siblings-1.jpg) |
| S098 | Active + pending | [Dual state](evidence/final-visual-batch-4/inspection/393-font-1-nl-activePending-1.jpg) |
| S099 | Rest-only | [Rest-only](evidence/final-visual-batch-4/inspection/393-font-1-nl-rest-1.jpg) |
| S100 | Next workout | [Next date](evidence/final-visual-batch-4/inspection/393-font-1-nl-next-1.jpg) |

S091, the adjacent selection-detail reference, was reviewed for the meaning of the Week continuation action. Its selection-screen composition belongs to Batch 6 and is not restyled by this Week-only batch. S020 is exercised with the accepted PendingRpeBanner above Week; reminder routing/owner behavior remains covered by the full navigation suite.

The capture matrix covers all ten mapped Home states at reference width/100% Dutch and 320 dp/200% English. Active+pending covers every combination of 320, 360, approximately 393 and 412 dp, 100%/200% text and Dutch/English. Supplementary cases cover the reminder, long siblings, absent measures/description, three attention items, initial loading and failed reads. All lower viewports are captured in the same scroll owner. Keyboard entry does not apply to Week, which has no input fields.

The first 320 dp/200% rendering exposed a collapsed stacked header title. Its zero flex basis was replaced with an automatic basis; the affected captures were repeated. Native evidence, not the style-only test, found this defect. A second native gate found the final goal card cropped with long siblings at 320 dp/200% text. Removing Week's explicit overflow-hidden override restored the native ScrollView extent and the complete goal control, retaining the single owner and existing padding. The final reference family and affected cases were recaptured after this correction; temporary geometry logging was removed. Overlapping viewport captures verify complete controls rather than accepting a cropped reference edge.

## Verification and acceptance

The [verification summary](evidence/final-visual-batch-4/verification-summary.json), [visual review](evidence/final-visual-batch-4/visual-review.json), [native audit](evidence/final-visual-batch-4/native-audit.json) and [scope audit](evidence/final-visual-batch-4/scope-audit.json) record the completed gates.

| Gate | Result |
| --- | --- |
| Full mobile regression suite | 540 tests / 62 suites passed after the final scroll correction. |
| Strict TypeScript and unused checks | Both passed; unused checks repeated after gallery removal. |
| Complete native state matrix | 42 cases, 268 matrix screenshots, all ten mapped states, complete lower viewports. Seven interaction screenshots plus reduced-motion and actual TalkBack focus evidence supplement the matrix. |
| Content/actions/privacy | Literal range/progress, supplied fields, independent sibling detail actions, authoritative active schedule and separate proposal preserved. 145 runtime public source files and native content scanned with zero private-load findings. |
| Native accessibility | 1,509 fully visible touch-target measurements passed the 48 dp requirement with integer-pixel rounding. Actual green TalkBack Profile focus was reviewed. All three animation scales were zero during reduced-motion capture. |
| Detail origin and attention | Close and Android Back restored the exact Week text/label/bounds footprint and selected destination. Count 3, default limit 2 and expand/collapse passed. |
| Contrast | Nine relevant text/surface pairs passed; minimum 5.59:1. |
| Scope and references | Ten existing mobile files changed, one WeekHeader added; 196 other baseline files and all fourteen protected reference/mockup images unchanged. Dependencies unchanged. |
| Evidence/credentials/whitespace | Source and artifact SHA-256 integrity, README credential exclusion and root/integrated-worktree diff checks passed. |
| Cleanup | Gallery and geometry logging removed; original app root layout byte-identical. Physical 440 dpi, 100% text, Dutch locale and normal authenticated Week restored. Accessibility/motion settings and notification permission flags exactly restored. Existing Metro/emulator retained. |

The changed production files are WeekScreen, WeekHeader, NextSession, WeekTaskCard, AttentionRow, QuickActionRow, GoalSummaryRow and the optional WorkoutSummary context slot. Three existing test files were updated. The final mapping supersedes the old pending-warning-before-calendar ordering and flat sibling formatting; those assertions now cover the approved order and shared summary anatomy. The fixed-padding assumption was replaced by the existing responsive Card behavior. Callback, disabled/focus, literal-content and attention coverage remains, with additional active+pending authority and missing-optional-data coverage.

Native [detail return](evidence/final-visual-batch-4/week-detail-return.png), [attention expansion](evidence/final-visual-batch-4/attention-expanded.png), [reduced motion](evidence/final-visual-batch-4/reduced-motion-week.png), [TalkBack focus](evidence/final-visual-batch-4/talkback-profile-focus.png) and [enlarged long siblings](evidence/final-visual-batch-4/inspection/320-font-2-en-siblings-4.jpg) provide supplementary review evidence. The first TalkBack screenshot hit the Accessibility Suite notification prompt and was replaced with actual Profile focus; the temporary notification suppression flag was then removed and its original denied permission/flags verified.

The final Week visual review passes: M6 title/Profile/art, M5 ivory workout anatomy, forest CTA, separate pale review, amber warning, grouped tools/goal and the accepted shell form one coherent composition. No full-forest workout hero or provisional Week scaffold remains. No later visual batch was started. Backend/Ruff/mypy/OpenAPI/database/RLS checks are not applicable to this presentation-only delta. Physical Android/iOS, signing and release approval remain separate release gates.

WOMBO UI V2 FINAL VISUAL BATCH 4 COMPLETE — WEEK ACCEPTED
