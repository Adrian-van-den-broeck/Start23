# Wombo UI V2 Slice 1 verification report

## Authenticated emulator acceptance - 2026-10-05

This record supersedes the earlier fixture-only/authenticated-blocked review.
Acceptance covers emulator-5554 / Pixel_4_API_35, Android API 35 x86_64,
the existing SDK 57 debug development client, and the normal Expo Router app.
Physical Android gates remain open. No UI redesign or physiology change was made.

### Integration and preserved provenance

The isolated local branch `sync/wombo-ui-v2-first-plan-provenance` started at
exact Slice-1 head `45e948484f769516ba1d1626641b71a62e50d58c`. The clean
`git cherry-pick -x 6b1189b70a6505726fef70c4616a2f3d6dd4c94a` produced
`1a5138f0626460e11558c788083a7aef4cc799f3`. Its message records the exact
original fix SHA. Cherry-picking necessarily creates a new commit SHA; the
original fix remains on `fix/catalog-capacity-fresh-athlete`. Both patches have
stable patch ID `d8b124ef285be361e6279042052c2bab24372961`.

All six UI commits remain unchanged ancestors, in order:

1. `0358166286076e30d9cef4501362b2622ffa4c21`
2. `1607142f9621c87cf37305b542a3136ad6157d77`
3. `f0c0402d09ca3a13b70ebdeccf7387aebaad1637`
4. `ee33e449b0dbf1dfa68304461f896cd211e5a9f1`
5. `53a647ec072f2adcccaff5cfe080bb4a1eb04c2f`
6. `45e948484f769516ba1d1626641b71a62e50d58c`

The sync adds only the verified fix and this acceptance-report commit. No
coach/Garmin/PDF/user changes were included. The Slice-1 branch remains at
`45e9484`. The annotated V1 tag object remains
`d39bfcd2cf6dcc17aca231502ac4ab4e46c0465a`, peeling to
`6bb3a047139d91c71ac065c35a8af595221b54c5`. Package, lockfile, app/native
configuration, EAS and Railway configuration match the baseline. No rebuild,
dependency installation, upgrade, rebase, squash or published-history rewrite.

`F:/wv2` now uses the sync branch. Metro was restarted from `F:/wv2/mobile`;
its manifest reports that project root, normal `expo-router/entry.bundle`, and
`dev=true`. Requested V2 is selected; only Workout Detail is enabled as V2.
The existing review data image was retained. Software rendering/headless boot
recovered a desktop graphics startup crash; an IPv4 listener recovered the ADB
bridge. Neither recovery required native/source changes.

### Sync checks

| Check | Result |
| --- | --- |
| First-plan/provenance/API/domain/repository/public contracts | 158 passed across test_planning.py, test_planning_domain.py, test_planning_repository.py and test_contracts.py; existing Starlette/httpx deprecation warning only |
| Relevant hosted migration/grant/RLS check | 10/10 pgTAP assertions, rollback-only, on start23-dev; original migration content preserved |
| All mobile tests | 31 suites / 125 tests passed, including focused V2, Week/Calendar boundary and recursive privacy suites |
| Strict TypeScript | Passed |
| Unused-code check | Passed |
| Ruff / format | Passed for all seven changed planning/test files |
| Strict mypy | Passed: 139 backend/test files |
| Whitespace / patch equivalence | Passed; identical bugfix patch IDs |

The full previously verified 778-test / 27-suite database run was not repeated.
The default system Python initially lacked pydantic-settings; the required
backend checks subsequently passed with the existing phase-review virtualenv.
No verification gate remains open for this emulator slice.

### Environment and real product flow

Only API `https://r6-api-r6-staging.up.railway.app` and Supabase `start23-dev`
(`isfumhgqphieoayqahjv`) were used. API health/readiness both reported staging
and passed. Verified fix deployment `7b499763-a64b-4762-b67c-e606172cf5ba`
was read back as SUCCESS; its approved-history RPC/provenance pgTAP checks passed.
There was no deployment or production access during this review.

Exactly one tagged disposable athlete was created with the existing supported
Auth test fixture. Random credentials stayed in helper memory and were entered
through normal app email/password sign-in; no session/token injection. Supported
profile, history, calibration observation, threshold confirmation, separate
pending-zone approval and onboarding-completion APIs were used, without direct
domain/database writes. RUN history was 180 min/week; BIKE/SWIM zero, no injuries
and no cross-training opt-ins. Calibration activity/history existed; no previous
approved weekly plan was injected.

In the actual running app, Week preparation selected 5 October 2026 and explicit
Monday/Tuesday/Wednesday/Saturday availability. `Maak weekvoorstel` returned
**HTTP 201**. The server supplied a two-RUN swipe deck. Both workouts were chosen;
`Verspreid over beschikbare dagen` placed/submitted the pending proposal with
**HTTP 201**. Its qualitative combination warning was visible and retained.
`Week goedkeuren` explicitly approved it with **HTTP 200**. The subsequent public
plan read was active revision 1, BASE / initial_catalog_baseline, with two
scheduled RUN occurrences visible in Week and Calendar. No approval DB shortcut.

Plan ID: `acd5d9a7-750e-4029-a4e3-39416ac44542`.
Acceptance occurrence: `2d843c5e-cb95-43ec-beb7-46a6c38f65e7`, RUN-013
Wisselduur, scheduled 7 October 2026, template version 2. Source name and
instructions contain an existing replacement character; both presentations
preserve it. The other approved occurrence was RUN-010 on 10 October.

### Authenticated detail and real V1/V2 parity

| Acceptance | Observed result |
| --- | --- |
| Week -> V2 Detail | Exact real occurrence, 90 minutes, absent distance stays absent, supplied low intensity, expected RPE 2-4; five blocks in source order |
| Source execution | Durations 15/15/15/15/30 minutes; zone targets 1/2/1/2/1; literal source instructions retained; supplied RPE reference expanded and inspected; no invented content |
| V2 Detail -> Week | Visible Close restored the same Week, selected 2026-10-05 plan and scroll position; before/after accessibility XML byte-identical |
| Calendar -> V2 Detail | Normal Calendar, October Month mode, selected 2026-10-07; same real occurrence and execution fields; detail-top accessibility labels identical to Week entry |
| V2 Detail -> Calendar | Native Android Back restored Calendar, Month mode, selected date, October anchor, range 2026-09-28 through exclusive 2026-11-02 and scroll position; before/after XML byte-identical |
| Real V1/V2 parity | Existing in-modal switch compared the same selected real object. Identity/name, 90 minutes/null distance, all five ordered blocks, targets/instructions and supplied RPE matched. V1 native Back restored the same Week position. Approved presentation differs; V1 source unchanged |
| No mutation/refetch/reset | Public plan before/after deeply identical, active revision still 1. Network mark counts unchanged during Week detail, V1/V2 comparison and Calendar detail: zero additional API requests, including writes. No navigation reset |
| Privacy | Public responses, rendered text and accessibility evidence contain no private TSS/load; recursive mobile and poison-field tests also passed |

Calendar adds the existing plan-level `target_outside_catalog_capacity` warning
to its workout envelope; Week carries that warning on the plan. Every other
occurrence field, including all execution data, matches. That warning placement
is outside the read-only detail snapshot. It was retained, not transformed.

The read-only CDP observer records some events three times with the same request
ID. Deduplication gives 16 actual app requests from 48 records. They are not three
mutations. Some response-body captures were unavailable; authenticated read-only
API snapshots supply the retained plan/Calendar evidence. HTTP status and detail
boundary request-count observations remained available.

### Screenshots and evidence

All required PNGs were produced with matching accessibility XML in the ignored
local `F:/wv2/mobile/.runtime` directory and visually inspected:

- [Week before](../../mobile/.runtime/authenticated-week-before-detail.png)
- [V2 RUN top](../../mobile/.runtime/authenticated-v2-run-detail-top.png)
- [V2 RUN lower](../../mobile/.runtime/authenticated-v2-run-detail-lower.png)
- [Week after](../../mobile/.runtime/authenticated-week-after-detail.png)
- [Calendar before](../../mobile/.runtime/authenticated-calendar-before-detail.png)
- [Calendar V2 detail](../../mobile/.runtime/authenticated-calendar-v2-detail.png)
- [Calendar after](../../mobile/.runtime/authenticated-calendar-after-detail.png)

Additional evidence: V2 middle, V1 top/lower, V1 Back origin and signed-out PNGs;
`sync-metro-provenance.json`, `sync-approved-plan-before.json`,
`sync-approved-plan-after.json`, `sync-calendar-public.json`,
`sync-authenticated-network.json`, and
[acceptance audit](../../mobile/.runtime/sync-authenticated-acceptance-audit.json).
These local artifacts are retained but are not Git-tracked or bundled.

### Cleanup, promotion and remaining gates

Normal app `Veilig afmelden` returned to the sign-in screen. The exact owned
athlete was metadata/email-guarded, sessions globally revoked, and Auth-deleted.
Admin lookup returned 404. Independent start23-dev readback found zero matching
Auth users, zero sessions for that actor, and zero Slice-1-tagged disposable
athletes. Exactly one actor was created and deleted in this run. No real athlete
was deleted. Cleanup evidence: `sync-authenticated-cleanup.json` and
`sync-cleanup-db-verification.json`.

After these gates passed, local `feat/wombo-ui-v2` was fast-forwarded from the V1
baseline to the sync branch's acceptance-report head, using an ancestry check
and the expected old ref. `git rev-parse sync/wombo-ui-v2-first-plan-provenance
feat/wombo-ui-v2` identifies both final equal SHAs; the documentation commit
cannot embed its own SHA. Slice-1 and V1 rollback references remain unchanged.

Physical gates remain separately open: activity/HR/RPE; delayed-response retry;
physical Month/Week; drag/drop and performance; physical workout detail;
TalkBack, initial/return focus, reduced motion, default/200% text, NL/EN and
physical gesture-navigation inset behavior. No physical-device acceptance.

Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`. The original dirty
checkout, coach file hash and Garmin/privacy/PDF documents are unchanged.
Nothing was pushed. Production remains untouched.

WOMBO UI V2 SLICE 1 EMULATOR ACCEPTED — PHYSICAL DEVICE GATES REMAIN

## Historical implementation record - 2026-10-02

The original implementation/fixture verification below is preserved for
provenance. Its branch/status statements describe that earlier date.


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

Historical result: Slice 1 implemented; device visual acceptance pending.
