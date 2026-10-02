# Wombo UI V2 Slice 1 verification report

Date: 2026-10-02 (Europe/Amsterdam).
Implementation is functionally complete. Physical Android visual/TalkBack acceptance remains pending.

| Requested report item | Result |
| --- | --- |
| 1. Worktree | `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-workout-detail`. Created clean from the supplied baseline; final tracked working tree clean. |
| 2. Baseline / tag | Commit `6bb3a047139d91c71ac065c35a8af595221b54c5` exists. Tag was absent; created annotated local `wombo-ui-v1-pre-v2-6bb3a04`, peeled SHA exactly equals baseline. Annotation: `Wombo V1 pre-V2 reference; physical Android gates open`. No tag moved/forced. |
| 3. Branches | Integration `feat/wombo-ui-v2` remains at baseline. Slice `feat/wombo-ui-v2-workout-detail` descends from it and tracks that local integration branch. Future PR/merge target is integration, never main. No PR or remote push created. |
| 4. Created files | Exact tracked file list below. Six approved input documents copied without changing their bytes. |
| 5. Modified files | Exact six existing-file list below. |
| 6. UI switch | One in-memory global development preference. Static `EXPO_PUBLIC_UI_VERSION=v1\|v2`; invalid/unset defaults V1. Registry contains only `workoutDetail`. Unsupported slice names (including inherited object keys) return V1. Labeled NL/EN controls at Planning header and inside stable detail Modal; selected button has forest fill and selected semantics. No storage, URL, remote flag or backend preference. |
| 7. Non-development proof | Resolver tests force V1 for every flag; provider/boundary test forces V1 after programmatic V2 request and hides controls. Final Android release JS export with environment V2 contains `__DEV__=false`, `initialUiVersion(false, "v2")`, false guards on setters/effective selection, a null development control, and V1-only boundary return. No release V2 route was added. |
| 8. V1 / V2 parity | Both receive the identical selected object and close callback. Only one body mounted; stable development Modal/control. V1 file is byte-for-byte unchanged. User approved reusing its stateless returned Modal content in development to avoid editing V1. Non-development renders the original V1 component directly. Week and Calendar integration tests preserve origin, Month mode and selected date after comparison and dismissal, with no extra API/storage calls. Visible Close and native Android Back invoke the same owner callback. |
| 9. Source fidelity | Adapters explicitly allowlist public fields and preserve supplied array order, sequence labels, names, instructions/newlines, independent measures, whole-session intensity, expected RPE, source date/status and supplied RPE reference. Primary target precedence: zone, RPE target, protocol target, expected RPE. Additional supplied targets are separately labeled; supplied observation/optional/technique flags remain readable. No current-zone substitution, physiology, planner, sorting/repeat parsing, recovery/equipment/session-type inference or generated coaching. Cancelled historical fixture retains 2020 date and original targets. |
| 10. Distance-only swim | Distance is numeric hero; duration stays absent. Both null and independently supplied measures covered. No segments shows exact approved qualitative missing-detail copy in NL/EN. Native 320dp / 200% Dutch swim screenshot confirms 1200 m without a duration. |
| 11. Accessibility | Scalable native system type; no font clamp, fixed critical-text height, or instruction ellipsis. Accessible headings, full dates, spoken measure units, selected/busy/disabled/expanded semantics. Buttons at least 48dp; primary 52dp. Button/header child text excluded to avoid duplicate announcements. Top/bottom safe areas, one detail ScrollView and natural wrapping. Used text contrast pairs pass 4.5:1; rail/control pair passes 3:1. Initial V2 heading focus requested; stable comparison control avoids stealing focus during a toggle. TalkBack behavior and originating-trigger focus need physical-device acceptance. |
| 12. Privacy | Recursive source privacy test passes; nested poison-field tests prove hidden extras cannot propagate into either view model, rendered text or accessibility props. Pure-import guard passes. New production V2/seam code contains no logger, transport, storage, mutation or private-field propagation. |
| 13. Mobile tests | Final `npm test`: 31 suites, 125 tests passed, zero snapshots. All existing V1 tests remain green. Existing Activity/FlashList tests emit act warnings; no new V2 failure. |
| 14. TypeScript / unused / formatting / lint | `npm run typecheck` and `npm run check:unused` pass. `git diff --check` passes for full baseline-to-slice diff. Slice files formatted with installed TypeScript formatter and reviewed. Repository has no mobile ESLint/Prettier script/config/package; no unconfigured linter was installed. Relevant backend OpenAPI/public-contract check: 6 tests passed (`tests/test_contracts.py`), using the existing local virtualenv and test fixtures. |
| 15. Android build / runtime | Final development and non-development Android JS exports pass, unpublished, under ignored `.runtime/`. Local fixture-only runtime passes on Android API 35 x86_64 emulator using the existing SDK-57 debug development APK; no new native APK compilation is claimed. Fresh workspace-only emulator data image used after original read-only image lacked space. Auth/API bypassed; no production accounts/endpoints used. Emulator, fixture server and Metro stopped afterward. |
| 16. Commits | Five implementation/input commits listed below, plus the documentation-only commit containing this report. Exact paths staged throughout. |
| 17. Packages | NONE: package.json and package-lock.json unchanged from baseline. No install, upgrade, new icons/fonts/UI/state package or native configuration change. |
| 18. Remaining device gates | Physical Android detail visual acceptance with TalkBack, focus restoration, reduced-motion settings, default/200% text, NL/EN and actual gesture-navigation insets. Native offsets are retained per presentation; different content heights can clamp/reflow, so exact pixel and focused-segment parity still needs device observation. Existing five V1 physical gates (activity/HR/RPE, delayed retry, Month/Week, drag/drop, detail) remain open. Lucide/SVG remains a separate dependency/asset gate; approved labeled sport accent used here. |
| 19. Production | Untouched. No deploy, publish, EAS command, hosted mutation, backend/API/database/planner/physiology changes or production credential use. |
| 20. Main / unpublished work | Main untouched at `fb56c51d983564c652d83fc15e02b039e9063d3f`; no branch pushed/merged. Original checkout remains `fix/pre-ui-beta-blockers` at baseline with coach edit, Garmin/privacy/PDF documents and approved untracked UI documents intact. No checkout/reset/stash of original tree. `.worktrees/` is the expected additional untracked root directory containing this registered isolated worktree. |

## Exact created tracked files

- `docs/ui/WOMBO_UI_V2_ARCHITECTURE.md`
- `docs/ui/WOMBO_UI_V2_DEPENDENCY_DECISIONS.md`
- `docs/ui/WOMBO_UI_V2_IMPLEMENTATION_PLAN.md`
- `docs/ui/WOMBO_UI_V2_SCREEN_MAP.md`
- `docs/ui/WOMBO_UI_V2_SPEC.md`
- `docs/ui/WOMBO_UI_V2_TOKENS.md`
- `mobile/src/screens/PlanningDetailBoundary.test.tsx`
- `mobile/src/ui-v2/components/RpeIndicator.tsx`
- `mobile/src/ui-v2/components/SessionSequence.tsx`
- `mobile/src/ui-v2/components/SportIndicator.tsx`
- `mobile/src/ui-v2/components/WorkoutSummary.tsx`
- `mobile/src/ui-v2/components/ZoneBadge.tsx`
- `mobile/src/ui-v2/motion/ContentTransition.tsx`
- `mobile/src/ui-v2/motion/useMotionPolicy.test.tsx`
- `mobile/src/ui-v2/motion/useMotionPolicy.ts`
- `mobile/src/ui-v2/primitives/Button.test.tsx`
- `mobile/src/ui-v2/primitives/Button.tsx`
- `mobile/src/ui-v2/primitives/Card.tsx`
- `mobile/src/ui-v2/primitives/Divider.tsx`
- `mobile/src/ui-v2/primitives/Screen.tsx`
- `mobile/src/ui-v2/primitives/Text.tsx`
- `mobile/src/ui-v2/screens/WorkoutDetailScreen.test.tsx`
- `mobile/src/ui-v2/screens/WorkoutDetailScreen.tsx`
- `mobile/src/ui-v2/tokens/colors.ts`
- `mobile/src/ui-v2/tokens/index.ts`
- `mobile/src/ui-v2/tokens/layout.ts`
- `mobile/src/ui-v2/tokens/motion.ts`
- `mobile/src/ui-v2/tokens/states.ts`
- `mobile/src/ui-v2/tokens/tokens.test.ts`
- `mobile/src/ui-v2/tokens/typography.ts`
- `mobile/src/ui-v2/utils/workout.test-fixtures.ts`
- `mobile/src/ui-v2/utils/workoutDetailViewModel.test.ts`
- `mobile/src/ui-v2/utils/workoutDetailViewModel.ts`
- `mobile/src/ui-v2/utils/workoutSummaryViewModel.test.ts`
- `mobile/src/ui-v2/utils/workoutSummaryViewModel.ts`
- `mobile/src/ui/UiVersionControl.tsx`
- `mobile/src/ui/UiVersionProvider.tsx`
- `mobile/src/ui/WorkoutDetailBoundary.test.tsx`
- `mobile/src/ui/WorkoutDetailBoundary.tsx`
- `mobile/src/ui/uiVersion.test.ts`
- `mobile/src/ui/uiVersion.ts`
- `docs/ui/WOMBO_UI_V2_SLICE_1_REPORT.md`

## Exact existing files modified

- `mobile/.env.example`
- `mobile/app/_layout.tsx`
- `mobile/jest.setup.ts`
- `mobile/src/i18n/LanguageProvider.tsx`
- `mobile/src/navigation/RootLayout.test.tsx`
- `mobile/src/screens/PlanningScreen.tsx`

`mobile/jest.setup.ts` adds only the existing Reanimated Easing mock needed to exercise the approved fade; no existing test was weakened. V1 WorkoutDetail, theme, API types/client, provider session/storage behavior, NativeWind, package/native/release config, backend and Supabase paths are unchanged.

## Local commits

- `0358166` — preserve approved UI implementation documents.
- `1607142` — fail-closed development resolver/provider and tests.
- `f0c0402` — approved tokens/primitives and focused tests.
- `ee33e44` — pure adapters, detail components/screen, motion and NL/EN source-faithful tests.
- `53a647e` — Week/Calendar integration, controls, boundary/state parity and focused accessibility refinement.
- Documentation-only report commit: `git log -1 -- docs/ui/WOMBO_UI_V2_SLICE_1_REPORT.md` identifies the commit containing this report (its own SHA cannot be embedded in the same commit).

## Visual comparison and local evidence

Reviewed against SPEC section 8, SCREEN_MAP section 14, and token/component tables. Warm canvas/ivory card/forest actions and sport accent match the approved values; single summary card, flat rail/sequence, 16dp card padding/gutters, 24dp section gaps, system hierarchy and source text are retained. Only optional RPE reference collapses. Mandatory instructions, observation requirement and targets stay expanded.

Emulator evidence is a local fixture smoke, not physical-phone or authenticated end-to-end acceptance. The following images were visually inspected; XML trees were captured alongside them:

- [Dutch distance-only swim at 320dp / 200%, top](../../mobile/.runtime/smoke-swim-320dp-200-nl-top.png)
- [Dutch distance-only swim at 320dp / 200%, final missing-detail state](../../mobile/.runtime/smoke-swim-320dp-200-nl-bottom.png)
- [English complete fixture at 360dp / default](../../mobile/.runtime/smoke-360dp-default-en.png)
- [English source sequence at 360dp](../../mobile/.runtime/smoke-360dp-sequence-en.png)
- [English source instructions at 412dp / 200%](../../mobile/.runtime/smoke-412dp-200-en-sequence.png)
- [Optional source RPE reference expanded](../../mobile/.runtime/smoke-final-expanded.png)

Ignored local evidence/artifacts: `.runtime/mobile-test-final.log`, `android-development-final.log`, `android-release-final.log`, Android development/release export directories, fixture-only harness/server scripts, screenshot/XML pairs and fresh emulator data image. They are not staged or bundled through the normal Expo Router application entry. This report links retained local evidence; those ignored artifacts will not travel in a future Git PR.

WOMBO UI V2 SLICE 1 IMPLEMENTED — DEVICE VISUAL ACCEPTANCE PENDING
