# Wombo UI V2 implementation and migration plan

Date: 2026-10-02. Status: technical plan complete; runtime implementation and
device acceptance have not started through this task.

Functional reference: `fix/pre-ui-beta-blockers` at
`6bb3a047139d91c71ac065c35a8af595221b54c5`. The inspected branch/HEAD match.
This plan adds documentation only. It authorizes no production change,
deployment, main push, backend/planner/physiology/API change or package install.

## 1. Reading order and binding decisions

1. [Root instructions](../../AGENTS.md), [mobile instructions](../../mobile/AGENTS.md)
   and [current MVP roadmap](../implementation/mvp-roadmap.md).
2. Approved Astra [specification](WOMBO_UI_V2_SPEC.md),
   [screen map](WOMBO_UI_V2_SCREEN_MAP.md), and [tokens](WOMBO_UI_V2_TOKENS.md).
3. [Technical architecture](WOMBO_UI_V2_ARCHITECTURE.md), including the A/B/C/D
   code audit, boundaries, token mapping, primitives, components and navigation.
4. [Dependency decisions](WOMBO_UI_V2_DEPENDENCY_DECISIONS.md).
5. This plan's slice gates and unresolved-capability register before coding.

The user's approval of Astra's visual/UX direction takes precedence over its
older design-proposal status wording. Implement Week, Calendar, Activities
and secondary Profile in the controlled navigation slice; do not reopen that
information architecture merely because Astra lists D1 as endorsement pending.
Its safe defaults for unsupported capabilities remain binding. Existing
functional behavior is preserved unless a later explicit decision supersedes
it. For planning provenance, the [September selection final addendum](../requirements/joren-workout-selection-phase-2026-09-28.md)
and [ruleset implementation record](../implementation/joren-planning-ruleset-v2.md)
override historical roadmap paragraphs. UI work copies no numerical rules.

## 2. Main technical decisions

| Decision | Implementation instruction |
| --- | --- |
| V2 boundary | `mobile/src/ui-v2/{tokens,primitives,components,screens,motion,utils}`; existing `app` routes remain the only runtime entry |
| Styling | Typed semantic TS tokens + StyleSheet. Retain already installed NativeWind 4.2.6 configuration; no V1 style conversion |
| Shared logic | Existing API client/DTOs, auth/language providers and safe parsers. Extract coupled flow controller only before its V2 mutation presentation |
| Version selection | `src/ui/uiVersion.ts` pure development resolver + implemented-slice registry, UiVersionProvider inside AuthProvider around root Stack; dev-only control, initial `EXPO_PUBLIC_UI_VERSION`, default V1 |
| Production | `__DEV__ === false` always V1, control hidden, even with a V2 environment value. Release-mode V2 needs a later explicit reviewed change |
| First slice | Read-only full-height Workout Detail at existing Week/Calendar callbacks; same selected snapshot/onClose, no new route or API |
| Navigation | Later Expo Router JavaScript Tabs in pathless training group; preserve `/planning`, existing compatibility routes and parent task Stack |
| Mutation ownership | One controller above presentation/navigator, not one hook per UI. No dual mounted live trees, duplicated API calls, retries or approval state |
| Rollback | Change dev presentation to V1 at safe boundary; retained controllers/snapshots/revisions/keys, no database or Git rollback |
| Dependencies | Reuse installed SDK-aligned motion/gestures/sheets/list libraries. No blur/gradients/font package required. Lucide/SVG optional gated asset slice |

No scaffolding is necessary to establish feasibility: existing Router
providers, controlled full-page WorkoutDetail Modal, selected-workout state,
TypeScript source alias and installed Reanimated provide the seam. Runtime
feasibility will still be tested in slice 1; this task does not claim a toggle
has been executed on a device.

## 3. Git, baseline and deployment safety

### References and branch names

- Immutable reference tag: **`wombo-ui-v1-pre-v2-6bb3a04`**, annotated, pointing
  exactly to `6bb3a047139d91c71ac065c35a8af595221b54c5`. Its annotation must say
  that the five physical Android gates remain open; it is not a beta-certified
  tag. Do not move/force an existing tag.
- Main UI integration branch: **`feat/wombo-ui-v2`**.
- Small slice branches: `feat/wombo-ui-v2-workout-detail`,
  `feat/wombo-ui-v2-week`, `feat/wombo-ui-v2-calendar`, etc., based on the UI
  integration branch, with PRs targeting **`feat/wombo-ui-v2`**, never main.
- If later stabilization passes the required device gates, record an additional
  immutable tag **`wombo-ui-v1-device-verified-YYYYMMDD-<shortsha>`** and the full
  SHA/evidence in this plan. Keep the original supplied reference tag.

Branch from the supplied stabilization SHA **now for documentation/read-only
development**, because no later verified stabilization commit was observed.
If a later stabilization descendant is verified before coding begins, use that
commit as the implementation base instead. Do not branch from main simply
because it is newer; do not assume a newer commit is verified. Until baseline
device evidence exists, V2 development may continue locally but is not beta
promotion and cannot close baseline gates.

Example **future local-only commands**, not executed by this task, after
reviewing tag/branch existence and preserving current work:

```powershell
git show --no-patch 6bb3a047139d91c71ac065c35a8af595221b54c5
git tag -a wombo-ui-v1-pre-v2-6bb3a04 6bb3a047139d91c71ac065c35a8af595221b54c5 -m "Wombo V1 pre-V2 reference; physical Android gates open"
git branch feat/wombo-ui-v2 6bb3a047139d91c71ac065c35a8af595221b54c5
```

Do not checkout/reset/stash the current dirty workspace blindly. It contains
pre-existing backend work, Garmin/privacy/PDF documents and the three approved
untracked Astra documents. Later use an isolated clean worktree for coding;
carry only the reviewed six UI design/technical Markdown files into the UI
branch. Stage exact file paths, not `git add .`, so unrelated work cannot enter
UI history. This task does not create a branch, tag, commit or worktree.

### Merge and rollback strategy

Keep extraction commits separate from V2 presentation commits. Use small
reviewed slice PRs with a merge commit (`--no-ff`) into `feat/wombo-ui-v2`;
avoid squash across unrelated controller/route changes so provenance remains
reviewable. Merge later verified stabilization commits into the UI integration
branch in a separate sync PR; run V1 regressions again. Do not merge UI work
back into the stabilization branch or rebase shared published history.

V1 presentation selection is the normal development rollback. A broken shared
extraction cannot be cured by switching views: revert the isolated extraction
commit/merge on the UI branch and reverify V1, or run the immutable reference
in its clean worktree. Do not revert data, recalculate history, or reset main.
Final main merge, V1 removal and release flag changes are separate explicitly
authorized work after device/regression acceptance.

### Production deployment risk

The user identifies main as production auto-deploy risk. Local CI inspection
shows backend and database workflows triggered by relevant paths on PRs and
main pushes; neither proves Railway's external service branch binding. A UI
branch or mobile-only diff is **not** evidence that Railway cannot deploy it.

No push, publish, main merge, Railway command, EAS build/update/submit or hosted
mutation is part of this task. Before any later remote branch push, a read-only
review must establish that production tracks only the intended release branch
and that no wildcard/preview service deploys this branch into production or
inherits production credentials. If that cannot be established, keep work
local. PR base and merge target must be `feat/wombo-ui-v2`; inspect them each
time. Do not change Railway bindings as a UI-planning workaround.

`mobile/eas.json` currently has development (dev client/internal), preview
(internal release) and wombo (`environment: production`, autoIncrement), with
a wombo submit profile. Do not reuse wombo for comparisons or add deployment
automation. Local development tests use existing approved development/local
fixtures; no production endpoints, accounts or credentials. Expo's UI flag
does not select or secure a backend environment.

## 4. Slice 1: Workout Detail, exact scope

Workout Detail is still the correct first slice. It already receives a public
immutable snapshot, is read-only, and opens from both the active move board and
approved Calendar. It proves visual structure without planner behavior or new
navigation routes. Current large PlanningScreen state can remain intact.

### Required outcomes

- Same `PlannedWorkout | null` and `onClose` props through
  `WorkoutDetailBoundary`; V1 import/render remains exact when V1 selected.
- V2 full-height Modal/frame, Back/Close, safe areas, one ScrollView, source
  sport/title/measure/intensity/expected-RPE and flat ordered SessionSequence.
  No nested sheets, prescription rewriting or repeat/equipment invention.
- Exact source target precedence, mixed/distance-only data, historical and
  cancelled snapshot fidelity, no active-zone substitution. No segments shows
  explicit missing-detail copy. Planning-card RPE suppression still applies
  to summaries, while execution detail retains supplied expected RPE.
- Semantic tokens, scalable system typography, Card/focus hierarchy, labeled
  Button, divider/structured content, optional rationale disclosure only.
  Critical execution instructions stay expanded.
- Dev control can compare same selected snapshot in V1/V2 and return to V1
  without refetch, state reset, duplicate effects, or origin/date/scroll loss.
  Preserve detail scroll/focused segment across presentation selection, with
  a stable owned Modal container where practical. Android Back and visible
  Close both invoke the existing close callback.
- Restrained content fade/optional explanation expansion, system reduced
  motion, TalkBack heading/focus/units, 48 dp targets and large text.
- No activity logging shortcut in this slice: the current Activity route does
  not accept a selected planned workout. A later explicit in-memory handoff
  must be proven; do not show a button that suggests a link it cannot perform.
- Icon family is unchanged as a design target. The zero-install proof uses
  labeled actions; approved Lucide assets/IconButton acceptance await the
  small dependency gate, not emoji/initial placeholders.

### Exact expected files for slice 1 (not created here)

| Action | Files |
| --- | --- |
| Create version seam | `mobile/src/ui/uiVersion.ts`, `UiVersionProvider.tsx`, `UiVersionControl.tsx`, `WorkoutDetailBoundary.tsx` |
| Create tokens | `mobile/src/ui-v2/tokens/colors.ts`, `typography.ts`, `layout.ts`, `motion.ts`, `states.ts`, `index.ts` |
| Create used primitives only | `mobile/src/ui-v2/primitives/Screen.tsx`, `Text.tsx`, `Card.tsx`, `Button.tsx`, `Divider.tsx` |
| Create used compositions | `mobile/src/ui-v2/components/WorkoutSummary.tsx`, `SportIndicator.tsx` (text/accent until icon gate), `SessionSequence.tsx`, `ZoneBadge.tsx`, `RpeIndicator.tsx` |
| Create pure mapper and screen | `mobile/src/ui-v2/utils/workoutDetailViewModel.ts`, `workoutSummaryViewModel.ts`, `mobile/src/ui-v2/screens/WorkoutDetailScreen.tsx` |
| Create motion helpers | `mobile/src/ui-v2/motion/useMotionPolicy.ts`, `ContentTransition.tsx` |
| Modify small integration points | `mobile/app/_layout.tsx` (provider only), `mobile/src/screens/PlanningScreen.tsx` (detail boundary and dev control only), `mobile/src/i18n/LanguageProvider.tsx` (NL/EN keys), `mobile/.env.example` (document initial public switch only) |
| Create focused tests | `mobile/src/ui/uiVersion.test.ts`, `WorkoutDetailBoundary.test.tsx`; `mobile/src/ui-v2/utils/workoutDetailViewModel.test.ts`, `workoutSummaryViewModel.test.ts`; `mobile/src/ui-v2/primitives/Button.test.tsx`; `mobile/src/ui-v2/screens/WorkoutDetailScreen.test.tsx`; `mobile/src/ui-v2/motion/useMotionPolicy.test.tsx` |
| Extend integration regression | `mobile/src/navigation/RootLayout.test.tsx`, a new `mobile/src/screens/PlanningDetailBoundary.test.tsx` proving Week/Calendar entry and origin |

The relative filenames in multi-file cells share the preceding directory.
No change to `App.tsx`, V1 WorkoutDetail/theme/helpers, API client/types,
planner, backend, schema, package/lockfile, Babel/Metro/Tailwind, EAS or Railway
is required. An icon dependency slice, if separately requested, has its own
manifest/lock/native-build diff and must not be hidden in this list.

### Completion gate for slice 1

Strict TypeScript/unused checks, applicable component/navigation/privacy tests,
all existing mobile regressions, document comparison and Android detail
interaction/layout pass. Confirm the non-dev forced-V1 case in a release-mode
local bundle/test without publishing it. Record remaining icon/device gates
explicitly; do not call visual or device acceptance complete from Jest alone.
No other original stabilization gate is closed by this slice.

## 5. Complete controlled migration sequence

The broad user order is validated with two adjustments from Astra and actual
coupling: separate read-only Calendar from later moves, and place a dedicated
navigation shell/profile organization slice after those foundations, before
complex task migrations. GoalStep lives inside onboarding, so goal form reuse
precedes onboarding shell migration. Auth, check-in, integrations, Pioneer and
zone setup are included rather than silently omitted from the broad list.

| Slice / V1 screen | V2 replacement | Shared logic / extraction prerequisite | New components | Tests and gate | Rollback / functional risk |
| --- | --- | --- | --- | --- | --- |
| 0. Reference and docs | No runtime view | Review baseline and approved files; define local flag policy | None | Documentation/source consistency and dirty-work preservation | No runtime change; all physical gates open |
| 1. `WorkoutDetail` at Week/Calendar | Full-height WorkoutDetailScreen | Existing selected snapshot/onClose; safe formatting; no controller extraction | Tokens, Text/Card/Button/Screen, WorkoutSummary, SessionSequence, target indicators | Source fidelity, null/mixed/distance, old detail tests unchanged, switch/back/origin, privacy, TalkBack/200% text | registry/detail preference to V1; low mutation risk, moderate layout/focus risk |
| 2a. Planning state extraction | Same V1 Planning view | Mechanical `features/planning/usePlanningController.ts` + `PlanningFlowProvider.tsx`, resume-ID helper; separate calendar read owner. No action/default/order changes | No visual change | Existing warnings, transitions, occurrence IDs, resume, exact payload/revisions; V1 full mobile regression | revert extraction if behavior differs; high coupling risk despite unchanged visuals |
| 2b. Planning `plan` root | WeekScreen current-week hierarchy | One planning owner; explicit active/pending snapshots, explicit selected Week context distinct from existing next-Monday creation input | WeekContext, NextSession, AttentionRow, truthful counts, static Skeleton | Active+pending/rest-only/failed load; same-date siblings; no duration estimates/count-as-readiness; creation still V1 task | registry week false; same state retained. Medium/high provenance risk |
| 3a. `TrainingCalendar` approved Week/Month | CalendarScreen read-only modes within current `/planning` | `features/calendar/useCalendarController.ts` + date-only utilities; current mode/anchor/selected date state made controlled; exclusive end and request sequence retained | WeekAgenda read-only, DayHeader, MonthGrid, SegmentedControl, selected-day list | Seven days/Sunday, 0/1/many sessions, rest+workout, narrow Month alternative, rapid ranges/out-of-order failures, no global busy | registry calendar false restores V1 view/context. High request/selection risk; original Month/Week device gate open |
| 3b. Root routes/profile organization | Three-destination V2 training Tabs, secondary Profile; V1 Stack path | Lazy TrainingFlowHost above conditional navigator, same planning/calendar owners; shared onboarding gate and pending-RPE count; route-only commit first | TrainingLayout, RootProfileAction, SettingsGroup/Row; V1 child forms remain | Auth/version resume/direct-entry, public paths/aliases, tab/back/deferred dismissal, retained date/scroll, all settings/tests/check-in/Pioneer links | settled switch to V1 Stack and mapped internal view; high remount/readiness risk |
| 4a. Availability & `SwipeDraftPanel` | Week creation, candidate selection and automatic/manual placement tasks | Existing planning owner; authoritative draft actions/payloads, synchronous duplicate lock; keep existing defaults and opt-ins | AvailabilityDays, candidate WorkoutSummary, Rpe-free card purpose, SaveStatus, occurrence date list | Accept/pass/undo/reset/exhaustion, repeat template occurrences, busy/retry/stale, one day vs multiple sessions, back/placement/submit pending only | task presentation to V1 after safe settle; high revision/identity risk |
| 4b. `PendingWorkoutEditor`, approval/rejection | Focused alternatives and PendingWeekReview | Shared pending editor fetch/mutation with exact options revision/proposal ID, plan decision callbacks | Proposal WeekAgenda, warning/AttentionRow, contextual Sheet, named approval actions | `can_remove`, no active deletion, stale options, replaced/expired proposal, warning still visible after count complete, explicit approval only | V1 editor/review restored, same proposal identity; high critical-state risk |
| 4c. `WeekSchedule` active moves | Movable WeekAgenda + accessible date moves | Shared complete-layout validate -> warning/cancel/confirm -> move with active revision; no optimistic committed placement | Dedicated DragHandle, date chooser, move status/warning panel, measured geometry | Same-week only, nonuniform growing rows, cancel/no-op, stale/reject/return, server warning cannot override hard conflict, date-button/TalkBack parity, physical frame trace | Disable V2 move sub-slice and use V1 move view. Original drag/drop gate remains required; highest gesture risk |
| 5a. Activity extraction | Same V1 ActivityScreen | `features/activities/useActivityController.ts` + `ActivityFlowProvider.tsx` preserving key/created ID, HR drafts, refs, load/feedback refresh, current-week eligibility and matching | No visual change | Existing ActivityScreen/regression/client tests; rapid taps, delayed response, partial success, returned feedback, genuine conflict | revert extraction if baseline changes; highest persistence/recovery risk |
| 5b. `/activities` + logging/HR/RPE | ActivitiesScreen history, ActivityEntry/Feedback controlled task surface | One activity owner survives history/entry/feedback and UI switch. Planned detail handoff via selected existing PlannedWorkout into owner, no new API/auto-create | Virtualized ActivityRow, ActivityFeedback, RpeChoices, Input, SaveStatus, local loaded-choice search | Optional ordinary HR, exact ten sport descriptions, tap-to-save, measured time/timezone, distance-only swim, explicit matching, current-week correction, 1 create/feedback instance; both original save/retry device gates | V1 presentation at safe boundary with same task identity; no fresh key on toggle. Highest network/state risk |
| 6. Profile editing/Connections/Account/App | ProfileScreen groups + existing Polar/Pioneer detail presentations | Small controllers for current reads/save/import/redeem; language/auth shared. Do not alter Polar callback/retry or redemption identity | ProviderRow, connection status, profile editor, field/action states | Existing Profile/Pioneer coverage, Polar returned statuses/7-14-30-day windows, retry/disconnect, sign-out/language, actual origin | per-route fallback V1; medium portal/navigation risk, high if import/redeem identity is disturbed |
| 7. Embedded `GoalStep` | Controlled GoalSetupForm used by supported onboarding/setup flow | Reuse `runPace`, `onboardingForms`, existing goal input/conversion/rounding and save operation; extract only goal form/controller | RaceTypeChoices, time/pace SegmentedControl, compact time/distance Input, goal summary | Five race types, null vs zero/exact seconds, input-mode retention/submission source, splits <= total, field errors. Existing goal tests remain | fallback form V1 preserving entered values; medium/high payload precision risk. No invented independent goal editor |
| 8. Auth + `OnboardingScreen` shell and other steps | Auth presentation; seven-step OnboardingScreen visually grouped Jij/Training/Controle | Auth unchanged; one onboarding controller; current server resume/version checks and separate profile/monitor/timezone/history/goal/setup/review writes | StepHeader, persistent labeled forms, saved progress, review summaries | Sign-in/signup/config/email notice; every current step/upgrade, partial writes, zero vs blank hours, confirmed monitor/timezone, stale finish revision, completion -> Week | same controller and completed steps; no cross-restart new draft guarantee. High readiness/resume risk |
| 9a. `ZoneSetupStep`, `ZoneProfileScreen` | Sport zones overview, setup, pending/active/history | Shared route/options/profile controller; pure visibility-safe adapter; known values/test/calibration flows preserved | ZoneTable, CalibrationState, sport selector, separate pending decision actions | Hidden values absent in rendered/a11y output, open bounds, original versions, selectable route exclusions, standalone/in-plan capabilities and exact preconditions | V1 route/view fallback; high visibility/approval/provenance risk |
| 9b. `CalibrationScreen`, `/tests`, `/calibration` | Protocol execution/result task | Shared observation/evaluation/threshold/zone controller; same activity/key/protocol IDs, required block fields and separate approvals | Protocol-specific SessionSequence adapter, observation fields, ResultSummary | Pain warning before instructions, optional vs mandatory HR, swim repetitions/rest/conditions, interruption/quality, threshold != zones active, reload failure/stale/history, aliases | same task owner; disable switch while unresolved; highest multi-stage state risk |
| 9c. `CheckInScreen` | Structured WeeklyCheckInScreen | Shared context controller, input revision/fingerprint, extraction adoption and recurring/external/restriction state | BlockedDays (explicitly not availability), fatigue/reason controls, restriction/external forms, review | All fields reachable; save -> confirm -> propose -> approve remain distinct, extraction no silent adoption, stale/context/restriction/errors | per-screen V1 fallback; high confirmation-chain risk |
| 10. Acceptance and eventual cleanup | Complete V2 coverage; V1 retained until approved removal | No domain migration; verify all registry entries and settled switch in real flows | Only missing reviewed presentation details | Whole mobile regression, non-dev V1, Android V1/V2 comparison, all applicable open release gates | No V1 removal/default release change/main merge without separate approval |

Slices 2a and 5a preserve V1 functional behavior but necessarily change where
its logic lives; they are the limited exception to byte-for-byte V1 source
preservation. V1 JSX/styles remain intact wherever practical. Do not call a
copied PlanningScreen under `ui-v2` a safe extraction. Keep old regression
tests against the V1 wrapper and test the shared action once, not twice.

## 6. Contracts that must remain shared

| Contract | Authoritative source / non-fork rule |
| --- | --- |
| Auth/session | AuthProvider + singleton Supabase client + established SecureStore refresh flow. Token-derived identity; no V2 login/session cache or authoritative UI user_id |
| API endpoints and payloads | `src/api/client.ts`, `types.ts`, existing FastAPI public contract. No V2 endpoint versions, copied fetch wrappers or direct Supabase domain reads |
| Weekly-plan lifecycle | Loaded plan/revision/proposal and existing create/approve/reject operations. Pending remains pending; active and pending replacement can coexist |
| Swipe draft lifecycle | Same draft ID/revision/current candidate occurrence, accept/pass/undo/reset/placements/submit. Server decides count/composition and feasibility |
| Activity/HR/RPE persistence | Same create key/fingerprint and created activity ID; `submitActivityRpeWithRefresh`, exact average-HR and correction preconditions. UI switch is not a new logical submission |
| Calibration | Existing observation/evaluation/threshold and zone decisions. Ordinary activity save does not become calibration; no implicit activation |
| Planner errors | Existing safe transport messages, warning severity/code/action eligibility; no message-string parsing, speculative recovery/spacing logic or exposure of raw server internals |
| Workout move | Same full-layout validation and move endpoint with exact active revision/same-week scope. Warning confirmation never bypasses server conflict |
| Privacy | Server-private planned/realized load never enters DTOs, UI/a11y, errors, logs or analytics. Adapters allowlist public fields; recursive privacy test includes new `src/ui-v2` automatically |
| Ruleset/model handling | Retain supplied snapshot versions and historical values. UI labels/copy do not recompute/reinterpret old data under current zones or active planning rules |
| Onboarding/readiness | Same server required steps/version, operational timezone/monitor confirmations and separate writes; no tab shell bypass |
| Check-in/provider/Pioneer | Same explicit context confirmation, Polar import/retry, code redemption and idempotency. No new Garmin, account recovery/deletion or commercial behavior |

## 7. Test strategy and commands

### Layered coverage without duplicating V1

- **Pure adapters:** frozen public fixtures, deterministic explicit locale/date,
  stable occurrence keys/order, target precedence, null/zero/mixed units,
  absent optional data and no guessed capabilities. Verify unexpected private
  fields are not copied into view models/accessibility. Test hidden-zone VM
  variants contain no numeric payload, including historical visibility.
- **Primitives:** meaningful interactions/state/labels/font scaling semantics,
  disabled/busy callback suppression, retained label and input/error association.
  Test control behavior rather than snapshots of every token literal. Contrast
  calculation is appropriate for approved/added token pairs, not pixel QA.
- **Compositions:** one detail/feedback form, all siblings/segments/dates,
  distinct proposal/approved labels, canonical RPE text, loading/error/stale/
  partial-success outcomes. Use existing Jest/RNTL; no giant new snapshot suite.
- **Shared controllers:** reuse V1 transport and screen regressions; add only
  extraction/migration-specific assertions for retained IDs/keys/revisions/
  values and one action across presentation switch. Pending network resolves
  against same owner even if a read-only child changes.
- **Switch:** table of unset/v1/v2/invalid and development/non-development;
  every unimplemented slice falls back to V1. Toggling does not duplicate
  fetch/mutation effects or remount auth/state owners; block unresolved writes,
  gesture/sheet states correctly; preserve same snapshot/scroll/context.
- **Navigation:** actual configured Expo Router root, not legacy App.tsx;
  normal auth -> onboarding -> planning, incomplete/upgrade/direct-entry states,
  public URL compatibility, tests/calibration aliases, origin/date/scroll,
  detail Android back, profile sheet deferred dismiss, secondary routes,
  Activity handoff and selected workout. Assert endpoint calls only once.
- **Privacy:** retain `src/privacy.test.ts` unchanged and run it each slice;
  it recursively scans new TS/TSX under src excluding tests. Add output-level
  adapter/render/a11y checks so source scanning is not the only privacy proof.
  Do not place forbidden private-field names in production source comments.
- **Existing domain suites:** remain authoritative and unchanged. V2 tests
  exercise supplied public fixtures/callbacks rather than copying physiology,
  server state machines or the entire V1 suite. A presentation-only slice does
  not require rerunning backend/DB suites merely to claim more coverage.
- **Visual/manual:** same public fixture/state/build/environment in each UI;
  compare against Astra tokens/screen requirements at 320/360/412 dp and default/
  200% font, NL/EN, keyboard, gesture safe area, empty/error/stale/long text.
  Compare sequentially or with non-mutating fixtures, never two live mutation
  owners. Record screenshots and observed failures; no visual fidelity claim
  from source/Jest alone.
- **Physical Android:** existing save/HR/RPE, delayed retry, Month/Week,
  drag/drop and detail gates remain explicit. Test return/rejection, multiple
  Sunday sessions, repeated templates, lost response/refresh partial success,
  TalkBack/focus, reduced motion and mid-range frame traces. Only authorized
  development/staging fixtures; no production testing. Each device record
  names V1/V2, SHA, installed native build, public environment name and result.

From `mobile`, later coding passes run at least:

```powershell
npm run typecheck
npm run check:unused
npm test
```

Targeted iteration may use `npm test -- --runTestsByPath <paths>`; the full
mobile suite is the integration gate after a shared extraction/navigation or
completed slice. Existing scripts `test:components` and `test:transport` are
useful subsets, but `test:components` matches screens only and will not cover
all new primitives/adapters. Do not claim all V2 coverage from that script.

Run installed Expo dependency diagnostics/native smoke if packages or native
configuration are separately changed; do not install new tools during this
documentation task. If another task authorizes cross-stack changes, relevant
backend tests, Ruff/format, strict mypy, OpenAPI/public leak and pgTAP/RLS gates
remain required under AGENTS.md. UI scope here provides no such authorization.
Any unavailable required environment is an **open verification gate**, not a
pass. No physical test is replaced by a JS-driven gesture test.

## 8. Ambiguities, conflicts and safe defaults

This register identifies actual implementation boundaries; it does not reopen
resolved visual language or invent product rules.

| Boundary | Repository/design evidence | Implementation disposition |
| --- | --- | --- |
| Astra D1 wording | Documents predate this explicit approved-direction instruction | Three tabs + secondary Profile accepted as direction; controlled nav slice still needs technical verification |
| Next week vs current Week | Planning initially uses `nextMonday()`, Astra Week home uses current week | Separate display context from generation input. Keep generation defaults; derive current Week display from explicit loaded context. No silently changed create date |
| Active-plan discovery | Calendar DTO lacks plan/approval metadata; latest remembered plan can be a pending revision | Load known active revision via existing client where identified; omit unknown progress/move/provenance. Arbitrary historical plan discovery/combined overlay is unsupported, not a new API request |
| Detail -> activity | Activity route currently offers choices but accepts no selected-workout route prop | First slice read-only. Later activities owner can receive explicitly chosen existing snapshot in memory; test link identity. No tracker or completion operation |
| Candidate detail | Public candidate is not PlannedWorkout; no scheduled date/occurrence row status | Later discriminated UI input; do not fake DTOs, date, plan state or template-derived occurrence ID |
| Expected RPE in quick cards (D2) | Baseline helper suppresses RPE prose | Keep suppression; execution detail retains actual supplied RPE. Promotion requires a separate product decision |
| RPE interaction (D3) | Baseline saves on tap | Keep ten canonical sport descriptions + explicit save-on-choice copy. No extra Save action introduced silently |
| Rich repeats/equipment/type (D6) | Planned segments lack structured hierarchy/equipment/type | Show source names/instructions as given, omit absent fields. No text parsing/LLM classification or new contract |
| Frequency/distribution (D4), race splits (D5) | Server owns composition; current goal stores total and optional sport time | No new count cap, one-per-day model, swim duration, transitions or split allocation. Existing conversion only |
| Calibration labels/legacy states (D9) | Setup/evaluation/threshold/profile are distinct; historical RPE-only/Week-2 records may exist | Status from actual returned context; show history truthfully. No automatic improvement/RPE-only route promise |
| Unsupported settings/provider/persistence (D8) | Existing Polar/Pioneer/language only; no Garmin runtime/account extras | Existing capabilities only; no Garmin row without approval and no new local draft/offline persistence guarantee |
| Live rollback during uncertain write | State/keys currently screen-owned; unresolved outcome must reconcile | Shared controller first; no remount/reset/discard. Switch at read-only/settled boundary; outcome uncertainty is a deliberate temporary switch block |
| Lucide package pin | No installed library/SVG; exact current stable registry payload unverified | Later exact stable pin/peers/native build gate; zero-install first proof uses labeled controls, not alternate icon design |
| Sheet Reanimated compatibility | Installed peers support v4, public overview wording is older | Retain existing package; do not claim device proof. Accessibility/keyboard/transition tests before V2 Sheet use |

If a missing datum prevents a truthful screen/action, render a localized
unavailable/unknown state and preserve existing supported route access. Do not
invent a fallback physiology formula, endpoint, persisted preference or feature.

## 9. Highest technical risks and stop conditions

1. **Lost activity retry identity or double mutation:** screen-owned key/created
   ID/refs must be retained in one shared owner. No live switch until extraction
   regression and ambiguous-outcome cases pass.
2. **Proposal/occurrence confusion:** template IDs are not occurrence IDs;
   exact base revision/proposal must accompany existing operations. No approval
   replay against refreshed content or selected-count-as-readiness inference.
3. **Navigation remount/readiness bypass:** authentication alone is not current
   onboarding completion. Place shared training gate/owners before new tabs;
   test direct routes and all existing entry aliases.
4. **Calendar source/request races:** current range response and pending plan
   are different sources. Preserve latest-request protection, exclusive end,
   independent calendarLoading and one selected-date/mode anchor.
5. **Drag geometry/performance/accessibility:** growing rows and scroll offsets
   must stay correct; native animation does not prove the right date. Move
   callback remains server validated, with date-button fallback and device trace.
6. **Calibration/onboarding separation and historical fidelity:** multiple
   writes/decisions, hidden values and versioned records cannot collapse into
   local wizard success. Migrate last with controller/source parity.
7. **Bundler/style/native dependency blast radius:** NativeWind interop is
   already global. Keep existing presets/config and V1 tokens; do not add
   fonts/frameworks or casually upgrade the SDK to fix V2 rendering.
8. **Deployment from Git or build tooling:** branch naming/path-only changes
   cannot establish Railway safety. Keep local unless later authorization and
   branch/service binding checks establish remote push safety; never push main.

Stop a slice if parity requires a backend/API/physiology change, if the version
switch discards task identity, or if a required state cannot be truthfully
represented from public data. Record the conflict and missing decision;
continue independent approved presentation work. Do not weaken tests or hide a
functional operation to pass visual acceptance.

## 10. Handoff and verification record

Created by this task:

- `docs/ui/WOMBO_UI_V2_IMPLEMENTATION_PLAN.md`
- `docs/ui/WOMBO_UI_V2_ARCHITECTURE.md`
- `docs/ui/WOMBO_UI_V2_DEPENDENCY_DECISIONS.md`

The three Astra documents and all pre-existing dirty work remain untouched.
No runtime code/scaffolding, package, route, API, backend, physiology, database,
deployment configuration, branch or tag was changed. No commit, push, publish,
deploy or production operation was performed.

Verification for this task is document/source consistency, approved-source
unchanged checks, relative links, Markdown fences/whitespace and change-scope
review. Local relative-link, fence and trailing-whitespace checks passed for
all three new documents; `git diff --check` passed and tracked-file scope
retained only the pre-existing backend modification. All six UI Markdown files
are still untracked; the three source design documents were not edited.
Runtime suites and native/device/hosted checks were not run because
this is documentation-only. The physical Android gates for **activity +
HR/RPE save, delayed retry, Month/Week, drag/drop and workout detail remain
open**. This technical-plan completion is not beta/release acceptance.
