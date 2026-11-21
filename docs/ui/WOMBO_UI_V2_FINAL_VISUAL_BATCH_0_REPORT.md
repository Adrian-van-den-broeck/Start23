# Wombo UI V2 Final Visual Batch 0 — baseline lock report

Date: 2026-10-06, Europe/Amsterdam. **COMPLETE — BASELINE LOCKED at `19c23d58f0b71aea01478df2306e2492a515e36e`.** Four representative states have fresh authenticated BEFORE captures. Workout Detail uses the existing functional/reference set under the user's explicit non-blocking fallback decision; no LIVE detail was available for the currently authenticated baseline athlete. No visual implementation was performed.

The emulator initially showed signed-out authentication. The user then explicitly authorized sign-in using the README test credentials. Athlete A signed in through the ordinary native password UI and passed the existing onboarding gate. Athlete B was also inspected but stops at onboarding step 2; no setup step was submitted. Authentication sessions were signed in/out as part of this authorized inspection; no account, athlete training data, activity, plan or zone was created or changed. Credentials were read only from the README, kept out of output/screenshots/evidence, and never requested in chat.

## Authority and scope

Read the root and mobile `AGENTS.md`, including their identical counterparts in the integrated worktree; the current MVP roadmap's status, supersession and device gates; [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md), [screen mapping](WOMBO_UI_V2_FINAL_SCREEN_MAPPING.md), [tokens](WOMBO_UI_V2_FINAL_TOKENS.md), [implementation sequence](WOMBO_UI_V2_FINAL_IMPLEMENTATION_SEQUENCE.md), and [screenshot index](WOMBO_UI_SCREENSHOT_REFERENCE_INDEX.md).

Appearance authority remains [mockups-final](mockups-final/). Functional/state evidence remains [reference-screenshots](reference-screenshots/). None of these assets or specifications was edited. The new read-only [audit script](evidence/final-visual-batch-0/audit-baseline.py) fingerprints 324 instruction, specification, reference, mobile source/configuration and pre-existing modified files. All 117 reference PNG hashes match the original manifest. The audit rerun checks byte preservation and unchanged refs.

## Exact source provenance

| Item | Verified value |
| --- | --- |
| Local `feat/wombo-ui-v2` | `19c23d58f0b71aea01478df2306e2492a515e36e` |
| Integrated runtime worktree | `F:\Projecten Business\Start23\Code\.worktrees\wombo-ui-v2-activities` |
| Runtime checkout branch | `feat/wombo-ui-v2-activities` |
| Runtime HEAD | `19c23d58f0b71aea01478df2306e2492a515e36e` — identical to the local feature ref |
| HEAD subject | `docs(ui): accept Slice 5B functional Activities and RPE scaffold` |
| Runtime tracked/untracked state | Clean: `git status --porcelain=v1 --untracked-files=all` is empty |
| Documentation checkout | `F:\Projecten Business\Start23\Code`, `fix/pre-ui-beta-blockers` |
| Documentation HEAD | `6bb3a047139d91c71ac065c35a8af595221b54c5` |
| Documentation state | Dirty before this task; this report/evidence are additional untracked documentation |

The documentation root is not the integrated runtime. `F:\wv2` is a separate checkout on `sync/wombo-ui-v2-first-plan-provenance` at `23243e0`; it is also the target of the integrated mobile `node_modules` junction. That dependency directory is reused, but Metro's source projectRoot is the integrated Activities worktree. No source was copied between checkouts and no branch/ref was advanced.

Pre-existing tracked root changes were `.vscode/tasks.json`, `backend/app/modules/coach/weekly_plan.py`, and `docs/deployment-tasks.md`. Pre-existing untracked root entries were `.worktrees/`, `docs/implementation/garmin-integration-design.md`, `docs/privacy/`, `docs/requirements/AI Trainingsalgoritme Overzicht.pdf`, `docs/ui/`, `scripts/android-short-paths.gradle`, `scripts/run-start23-android.ps1`, and `scripts/tests/`. Their work was preserved. Clean runtime status excludes existing ignored local `.expo`, `.runtime` and dependency artifacts; those are not claimed absent.

Machine-readable provenance and full package versions: [baseline-audit.json](evidence/final-visual-batch-0/baseline-audit.json).

## Registry, shell and state owners

The actual registry in `mobile/src/ui/uiVersion.ts` is exactly:

```text
workoutDetail, week, calendar, planningCreation, proposalReview, activities
```

Active movement is implemented through the existing planning boundary/task flow; it is not an additional registry key. Auth, onboarding/goal, Profile, zones/calibration, check-in, tests, integrations and supporting destinations remain V1. The global pending-RPE banner retains its current presentation and routes into the existing Activities flow.

`mobile/src/navigation/TrainingLayout.tsx` already supplies Week (`planning`), Calendar and Activities tabs in V2. These are text-only tabs on the current canvas, with a forest selected destination, 56 dp minimum destination height and a bottom safe-area container. Week is the initial/back destination. Locked tasks suppress the tab bar; workout detail retains an inaccessible measured bottom footprint. V1 uses the existing Stack. The navigator transition temporarily shows readiness while unregistering the old navigator, preserving owners above it. This batch did not restyle or replace that shell.

| Ownership | Existing production mount and evidence |
| --- | --- |
| Planning: one controller | Authenticated layout → identity-keyed `TrainingFlowHost` → ready `PlanningFlowProvider` → `PlanningOwner` → one `usePlanningController`. Ready host survives navigation and token refresh. Nested planning providers fail before constructing another owner. |
| Calendar: one data controller | The same `PlanningOwner` constructs one `useCalendarController`, exposed through `usePlanningCalendar`. Week/Calendar/task presentations consume it. `PlanningPresentationProvider` owns calendar navigation/scroll context, not another data controller. One active Calendar range effect calls `ensureCalendarRange`; approved-plan revision changes invalidate/replace shared data. |
| Activity: one controller | Authenticated layout mounts one identity-keyed `ActivityFlowProvider`/`ActivityOwner` → one `useActivityController`, shared by V1/V2, entry/feedback and the global reminder. Nested activity providers throw. Creation identity, retries and feedback data remain in this owner. |

`PlanningScreen.tsx` still exports a standalone provider wrapper for isolated hosts/tests. App routes import `PlanningBoundary`, not that wrapper, so it is not mounted under the ready authenticated provider. Controller-call and provider-mount searches were inspected across both `mobile/src` and `mobile/app`; the wrapper was not falsely counted as a second simultaneous runtime owner.

Fresh passing owner/navigation coverage includes PlanningFlowProvider **76 tests**, ActivityFlowProvider **36**, TrainingNavigation **43**, and useCalendarController **7**. It covers owner lifetime/identity, token refresh, nested-owner rejection, return context, state transitions, stale responses and navigation locks. These are software proofs, not a new authenticated emulator trace.

## Manifest, lock and versions

No install, upgrade, native rebuild or reinstall occurred. `package.json` declares mobile version `1.0.0`, entry `expo-router/entry`, private package; `package-lock.json` uses lockfile version **3**. Every declared direct dependency/dev dependency was compared to its installed package and exact lock entry; all installed versions match.

| Package | Manifest | Lock / installed |
| --- | --- | --- |
| Expo | `~57.0.24` | `57.0.24` |
| React Native | `0.86.3` | `0.86.3` |
| React / React DOM | `19.2.3` | `19.2.3` |
| Expo Router | `~57.0.22` | `57.0.22` |
| Expo development client | `~57.0.19` | `57.0.19` |
| TypeScript | `~6.0.3` | `6.0.3` |
| Jest / jest-expo | `~29.7.0` / `~57.0.5` | `29.7.0` / `57.0.5` |

Metro's Android manifest reports SDK `57.0.0`, runtime version `exposdk:57.0.0`, Hermes development bundle and app version `1.0.0`. `lucide-react-native`, `react-native-svg` and `@expo/vector-icons` are absent from the resolved lock. Their future dependency/asset proof remains Batch 1a work.

SHA-256 of the unchanged integrated files:

| File | SHA-256 |
| --- | --- |
| `mobile/package.json` | `3c4467c7ad402100133716dd1e95f8125d9daa2578c07320250ece06bf1a6de9` |
| `mobile/package-lock.json` | `cb65f3e0f1abf5a4e59998c0ba9c277cde9abd6d2af2e32f5f0bec1dec22438d` |
| `mobile/metro.config.js` | `a5898f8ec51acf45d28cd4810be1f920ea91553844748c3868c0934c39c879ab` |

## Fresh software verification

All commands ran against the integrated runtime mobile directory using its existing dependencies. No test or runtime source was modified to make them pass.

| Gate | Result / retained evidence |
| --- | --- |
| `npm test -- --json --outputFile=…` | **PASS: 510 tests / 58 suites**, zero snapshots, 54.446 seconds. [JSON](evidence/final-visual-batch-0/mobile-tests.json), [log](evidence/final-visual-batch-0/mobile-tests.log). Matches the accepted Slice 5B total. |
| `npm run typecheck` | **PASS**, `tsc --noEmit`. [Log](evidence/final-visual-batch-0/typecheck.log). `tsconfig.json` enables strict typing and both unused options. |
| `npm run check:unused` | **PASS**, `tsc --noEmit --noUnusedLocals --noUnusedParameters`. [Log](evidence/final-visual-batch-0/unused.log). |
| Existing recursive privacy test | **PASS** within the full suite; scans non-test TypeScript recursively under `src` for TSS/private-load fields, including UI, DTOs, errors and accessibility/analytics source. |
| Supplementary privacy audit | **PASS**, 123 non-test TypeScript files in `src` **and** `app`, no private-load or privileged-key markers. File/pattern counts retained in the baseline audit; no credential values were printed. |
| UI-version policy | **PASS: 10 tests**, including exact registry, unknown-slice fallback and release forcing V1. |
| Reference preservation | **PASS: 117/117** manifest SHA-256 checks; six final mockups fingerprinted. |
| Integrated runtime `git diff --check` | **PASS**, no runtime diff. |

Backend tests, Ruff, mypy, hosted OpenAPI/API/database/pgTAP/RLS checks were not rerun: this task changed documentation/evidence only and made no backend, API-contract or database changes. The unchanged native app used ordinary authentication and public read APIs during inspection. Existing external/release gates are not closed by these mobile results. Dependency diagnostics/native build are not claimed as fresh checks.

## Running emulator and Metro

Reused the existing emulator, installed application and Metro process. No additional Metro instance was started.

| Item | Observed baseline |
| --- | --- |
| ADB device | `emulator-5554`, online; only attached device |
| AVD / model | `Pixel_4_API_35_2`; `sdk_gphone64_x86_64` / `emu64xa` |
| OS | Android 15, API 35 |
| Full display | `1080 × 2280` physical pixels; no size override reported |
| Density / logical display | 440 dpi; approximately `392.73 × 829.09` dp before OS insets |
| Font scale | `1.0`, unchanged |
| Device locale | `en-US`, unchanged |
| Visible app language | Dutch, observed on signed-out screen; distinguish app preference from OS locale |
| Device timezone | `GMT`, unchanged; report timestamps use Europe/Amsterdam |
| Foreground app | `com.adrivdbs.wombo/com.adrivdbs.wombo.MainActivity` |
| Installed version | `versionName=1.0.0`, `versionCode=1`, min SDK 24, target SDK 36 |
| Existing install metadata | First install `2026-10-01 20:53:52`; last update `2026-10-06 09:42:09` as returned by Android, not converted to report timezone |
| Initial state | Signed out, blank authentication fields, no keyboard or developer overlay |
| Authenticated capture/final state | README Athlete A; onboarding gate passed; Dutch V2 Week/Calendar/Activities/availability; existing completed activity, no newly created training data; left authenticated on V2 Week |
| Metro listener | Port `8081`, PID `18108` |
| Metro launch command | Existing integrated-worktree Expo CLI `run:android --binary …/mobile/android/app/build/outputs/apk/debug/app-debug.apk --device Pixel_4_API_35_2 --port 8081 --no-install` |
| Current projectRoot | `F:\Projecten Business\Start23\Code\.worktrees\wombo-ui-v2-activities\mobile`, proven by HTTP 200 Android manifest |
| Config | `getDefaultConfig(__dirname)` wrapped by `withNativeWind`, input `./global.css` |
| Debug bundle | `127.0.0.1:8081`, Android, `dev=true`, Hermes, router root `app` |
| Existing ADB reverse | `tcp:8081 → tcp:8081`; `tcp:8000 → tcp:8000`; unchanged |

Sanitized manifest metadata: [metro-manifest.json](evidence/final-visual-batch-0/metro-manifest.json). The NativeWind worker/dependencies resolve through `F:\wv2\mobile\node_modules`; that does not change the manifest's source projectRoot.

The computer-use skill's Windows native pipe was unavailable (`os error 2`) after a retry and kernel-reset recovery. ADB diagnostics, Android UI input and native screen capture were available, so those were used. Initial process inspection required read-only sandbox escalation and succeeded. No automatic approval rejection occurred. Following explicit user authorization, native app sign-in used README credentials through the existing password UI, with focus checks and without token/session injection.

## Current V1/V2 development behavior

`initialUiVersion` selects V2 only when `__DEV__` is true and the flag is exactly lowercase `v2`; absent/invalid flags default to V1. `effectiveUiVersion` further requires one of the six own registry keys. Release forces V1 regardless of requested flag. `UiVersionControl` is development-only and disables switching under the existing busy/sheet/task locks. Planning boundaries retain origin during detail comparison; Activities comparator preserves the Activities destination; V1 Calendar comparison uses Planning's internal Calendar view.

These behaviors were verified in current source and freshly passing policy/navigation suites. A request to the running Metro provider bundle confirms it reads the Expo virtual environment's `EXPO_PUBLIC_UI_VERSION`; it did not expose the startup flag value. The authenticated development selector **freshly confirms requested V2**. Activities **V2 → V1 → V2** was exercised with the existing completed activity retained and Activities restored as the destination; Week/Calendar navigation and return from availability were also observed. [V1 comparator PNG](evidence/final-visual-batch-0/activities-v1-before.png), [restored V2 XML](evidence/final-visual-batch-0/activities-restored-v2.xml). The V1 diagnostic line overlaps the OS status area in its existing layout; this is recorded BEFORE evidence, with no style fix in Batch 0. Release-client behavior remains a software-policy proof rather than a fresh native release-build run.

## BEFORE evidence and explicit inherited-detail fallback

Initial capture: [current-runtime.png](evidence/final-visual-batch-0/current-runtime.png), native `1080 × 2280`, taken approximately 15:53 Europe/Amsterdam on 2026-10-06. Visually inspected: stable signed-out Dutch authentication UI, blank fields, no credentials. Subsequent native BEFORE captures use the same device, viewport, font scale 1.0, Dutch UI and integrated SHA `19c23d58f0b71aea01478df2306e2492a515e36e`, with README Athlete A's existing data. No keyboard, loading transition or developer overlay is retained in the screenshots.

Representative evidence status (all BEFORE references):

| Required representative | BEFORE reference | Batch 0 status |
| --- | --- | --- |
| Week | [week-before.png](evidence/final-visual-batch-0/week-before.png) | Captured LIVE V2: no week loaded, current-week date context, existing goal and task/tools |
| Calendar | [calendar-before.png](evidence/final-visual-batch-0/calendar-before.png) | Captured LIVE V2: empty approved Week agenda for 12–18 October, existing tabs/range controls |
| Activities | [activities-before.png](evidence/final-visual-batch-0/activities-before.png) | Captured LIVE V2: existing completed Run activity, HR/RPE/result copy and correction capability; no save performed |
| Workout Detail | Existing [Run top](reference-screenshots/workout-detail/run-01-top.png), [ordered segments](reference-screenshots/workout-detail/run-02-segments.png), [instructions/RPE](reference-screenshots/workout-detail/run-03-instructions.png) | **Inherited functional/reference baseline, explicitly authorized by the user. No LIVE Workout Detail was available for the currently authenticated baseline athlete.** Not a fresh Batch 0 capture. |
| One planning task | [planning-task-before.png](evidence/final-visual-batch-0/planning-task-before.png) | Captured LIVE V2: existing availability task for 12 October with unchanged default selections; no field edited, no generation submitted; returned to Week |

Each fresh PNG and all three inherited Run detail PNGs were opened and inspected; accompanying fresh XML records visible controls and state. Retained textual evidence was checked against all README credential values: zero matches. No archived screenshot was relabeled as a fresh capture, no fixture host was inserted, and no domain outcome was manufactured. Account setup, generation or approval remained outside this verification task.

**User-approved evidence exception:** after the initial blocked report, the user authorized README sign-in and then explicitly instructed that if a reasonable read-only Calendar check found no existing Athlete A workout, Batch 0 must not be blocked: use the existing Workout Detail references, document the lack of LIVE detail and preserve athlete state. This later instruction governs the exit decision. Athlete B's onboarding remained untouched.

Athlete A's settled Calendar reads showed no approved workouts in the inspected July, August, September and October month ranges, including the current and upcoming weeks. The earlier-month check was bounded to three previous-month navigation actions. [September inventory](evidence/final-visual-batch-0/calendar-search-september.xml), [August inventory](evidence/final-visual-batch-0/calendar-historical-search-2.xml), [July inventory](evidence/final-visual-batch-0/calendar-historical-search-3.xml) retain the read-only observations. The first historical-search XML is a transient September loading observation, not accepted empty-state evidence; the separately settled September inventory establishes that result.

Inherited detail source: Slice 1 `2c7ad69392d945651a6b453318e6763ec2514239`, as recorded in the original index; its original temporary athlete was subsequently deleted. `git diff --quiet 2c7ad69 HEAD --` for `WorkoutDetailScreen.tsx`, `workoutDetailViewModel.ts`, `SessionSequence.tsx` and `WorkoutSummary.tsx` succeeds: these detail rendering sources are unchanged at the integrated baseline. This source comparison does not turn historical shell/actor state into today's live state. The original three image SHA-256 values remain in the unchanged reference manifest.

During the second Athlete A sign-in, one intake read briefly reported an expired session; the existing read-only retry recovered to Week. This was observed and resolved through current app behavior, with no runtime fix or token injection. Final app state is [authenticated V2 Week](evidence/final-visual-batch-0/final-state.xml). Capture classifications, image hashes, dimensions, times and inherited provenance are recorded in [capture-ledger.json](evidence/final-visual-batch-0/capture-ledger.json); local evidence fingerprints are in [evidence-manifest.json](evidence/final-visual-batch-0/evidence-manifest.json).

## Physical and outstanding gates

Only an emulator is attached. Existing physical gates remain open: Android activity plus HR/RPE save and delayed-response retry; Month/Week switching; drag/drop hit testing, scrolling and performance; workout-detail behavior; TalkBack/focus return, large text and system/keyboard insets on physical hardware. SDK 57 physical iPhone validation still requires Apple signing/team and device registration. Release-client acceptance and final mockup fidelity are future gates. Source/software and emulator results do not close them.

The existing reference gaps also remain: Check-in completed state after the staging onboarding-upgrade mismatch; standalone Settings scope/route; goal-achievement consumer confirmation. Linked integration and executable calibration/result variants remain uncaptured additional evidence. These were not repaired or expanded in Batch 0. Accountable physiological review and other roadmap release gates are unchanged.

## Exit decision

Source SHA/worktree, ownership, registry/shell, packages, mobile software/privacy baseline, running Metro root and emulator configuration are verified. No genuine baseline code defect was found. Runtime source, tests, manifests/lockfiles, backend/API/database, physiology and product behavior were left unchanged. No use of the main checkout, commit, push, deployment, package change, rebuild or reinstall occurred.

**Batch 0 exit:** authentication, four fresh representative captures, explicitly accepted inherited Workout Detail evidence and live V1/V2 observation are verified. The exact source baseline is locked. Lack of a LIVE detail for this athlete is a documented evidence limitation, not a Batch 0 blocker under the user's latest instruction. Existing physical-device, missing product-reference and release gates remain open; Batch 0 completion does not close them or authorize another visual batch.

WOMBO UI V2 FINAL VISUAL BATCH 0 COMPLETE — BASELINE LOCKED
