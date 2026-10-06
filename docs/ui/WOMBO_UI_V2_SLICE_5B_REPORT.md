# Wombo UI V2 Slice 5B report

Verified on 6 October 2026. Scope: Activities, existing manual entry and existing
RPE feedback presentation only. Visual status: **PROVISIONAL FUNCTIONAL
ACTIVITIES/RPE SCAFFOLD**. Final visual design remains deferred to user mockups.

## Acceptance and provenance

1. **Slice-5A prerequisite: VERIFIED before runtime edits.** The accepted report
   ends with `WOMBO UI V2 SLICE 5A COMPLETE — V1 ACTIVITY BEHAVIOR PRESERVED`.
   Its actual report delivery SHA was resolved from Git, its worktree was clean,
   and local `feat/wombo-ui-v2` contained that exact accepted head. Fresh baseline
   verification passed **459 tests / 55 suites**, strict TypeScript, unused-code
   and recursive privacy. Slice 4A/4B/4C, navigation and single ownership remained
   green; protected backend/API/database/package paths were unchanged.
2. **Starting full SHA:** `697f9e82a0c265036fe535674231f2476b9e1435`.
3. **Branch/worktree:** `feat/wombo-ui-v2-activities`, isolated at
   `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-activities`.
   Unrelated root-worktree changes were retained without reset/stash/staging.
4. **Final verified implementation SHA:**
   `4925a4458357f5bbfbc3d27b538dbb9735af28ef`.
   Final delivery SHA is the report-only commit containing this document;
   resolve its full value with
   `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_5B_REPORT.md`.

Root/mobile AGENTS, current MVP roadmap, V2 specification, screen map,
implementation plan, architecture and accepted 3B/5A reports informed the work.
Actual V1 ActivityScreen, shared Activity owner, API/DTOs, shell reminder,
RPE recovery helper, pace utilities and tests supplied the behavior boundary.
The pre-edit audit was recorded in ignored
`mobile/.runtime/slice5b/pre-edit-audit.md` before runtime changes.

## Functional findings

5. **Implemented registry:** only `activities` was added. Existing
   `workoutDetail`, `week`, `calendar`, `planningCreation`, `proposalReview`
   stay enabled as previously accepted. Unknown/unimplemented destinations
   still fall back to V1. Release/non-development resolution still forces V1.
6. **One shared Activity owner:** ActivityBoundary consumes `useActivityFlow`.
   The accepted `ActivityFlowProvider`, `useActivityController` and create-input
   helper are unchanged. There is no V2 owner, API mutation, idempotency key,
   pending-feedback copy or separate list/reminder store. Source audit finds
   one controller invocation per provider; real native inspection finds one
   Activity, Planning and Calendar owner throughout root/presentation switches.
   Authenticated identity remains their lifetime boundary; rotating tokens and
   UI preference do not recreate them. Sign-out removes all three.
7. **Activities root:** heading, Profile, explicit Add activity, shared loading
   and safe error, truthful settled empty state, recent history and inline
   pending continuation. Add is disabled and explains the existing feedback
   block. There is no second global reminder, dashboard or automatic feedback.
8. **History:** one FlashList retains controller/server order and exact activity
   IDs. Public sport, full local date/time, independently available duration and
   distance, existing pace, returned feedback/HR, qualitative result/message,
   measurement notices and correction-proposal notice remain available.
   Existing suggested match requires explicit confirmation; current-local-week
   RPE correction uses the exact stored snapshot. No record sorting, grouping,
   pagination, status reinterpretation or synthetic measurements were added.
   Public provenance currently supplies only `canonical_summary`; the generic
   localized source label makes no manual/imported/synced/provider claim.
9. **Entry:** exact scheduled-workout or planned-external selection, or explicit
   extra activity. Sport is editable for extra activity; ISO actual start,
   confirmed athlete timezone, duration and optional integer metres are the
   existing inputs. Swimming with distance and null duration remains supported.
   No editable pace/HR/new field was invented at create. Back performs no POST
   and preserves the unresolved owner draft and logical attempt.
10. **Create contract:** unchanged `createActivity` action and `POST
    /api/v1/activities`, with the existing stable request key. Payload retains
    optional exact `planned_workout_id` or `planned_external_activity_id`,
    `discipline`, `started_at`, `timezone`, normalized string/null
    `duration_minutes`, and optional `distance_meters`. Existing validation,
    mutation ordering, selected-context clearing and four-read refresh remain
    in the owner. Only authoritative results become current state.
11. **Idempotency:** V2 never generates a key. Tests prove one create under
    double press/rerender/token rotation, the same key and draft across an
    ambiguous failure and explicit retry/Back, successful-POST refresh-only
    recovery, and a fresh athlete's independent logical attempt. Existing
    key rotation after the created activity's authoritative feedback is intact.
12. **Pending feedback:** post-create transitions presentation to feedback for
    the exact owner-selected activity. Back, root navigation, reminder return
    and safe V1/V2 switching retain that identity and the per-activity HR draft.
    None submits feedback or marks it complete. One feedback composition exists;
    history may also show the same public pending record as before.
13. **Second create:** owner guard is unchanged. V2 disables Add and submit from
    the same pending/busy state; direct shared-action regression remains green.
    Live Back from pending exposed the continuation and blocked another create.
14. **RPE:** RpeChoices imports all ten exact canonical sport descriptions and
    values from the existing helper. Selection explicitly saves immediately,
    exactly as V1; copy explains that transaction. Stored correction selection
    is visibly checked and announced, rather than fabricating an unsaved RPE.
    Optional HR uses the existing 20–260 integer validation. The unchanged
    `submitActivityRpeWithRefresh` receives the exact activity snapshot, chosen
    RPE and HR. Existing `PUT /api/v1/activities/{id}/rpe`, typed stale recovery,
    payload, retry and refresh behavior remain intact. Failure preserves pending
    identity/draft; busy controls prevent a second or different-choice submit.
15. **Global reminder:** existing shell count/read still derives from the sole
    owner. Its V2 action sets the navigation-only feedback view and navigates
    to Activities. Banner text/style are unchanged. Existing pathname/token
    pending-read triggers and coalescing remain; root changes may still perform
    their supported reminder reads. No second global count/read was introduced.
16. **V1/V2 and navigation:** safe comparison retains Activities as its origin
    and the same owner/task/draft/pending identity. A minimal navigator-origin
    fix retains the Activities route through Stack/Tabs replacement; Tabs still
    initializes and goes Back to Week. Real router and native comparisons pass.
    Shared mutation busy state blocks root tabs, Back, reminder and preference
    switching while create/RPE is unresolved, then releases them. No mutation
    runs from navigation, rerender or presentation-transition effects.
17. **Sign-out/identity:** tests replace athlete A with B and prove no inherited
    history, feedback identity, HR/form draft, stored RPE selection or attempt
    key; old async completions cannot publish into B. Live normal sign-out
    reached Auth with zero authenticated owners and no remaining session.
18. **Accessibility:** persistent localized input labels, full date/time context,
    units, headings, safe alert/live loading state, exact-ID action labels,
    radio checked state, explicit Save activity/Save RPE/Back and busy/disabled
    semantics are covered. Shared primary targets have minimum 52 dp; new
    controls allow font scaling and natural multiline growth without clamps.
    On the 360 dp Android emulator, 200% text wrapped naturally and scrolling
    reached the entire RPE-10 control with Back still available. NL/EN critical
    copy uses LanguageProvider. Canonical descriptions retain their existing
    Dutch source text even with English UI, preserving V1 behavior. Physical
    TalkBack/release-device acceptance is not claimed.
19. **Privacy:** an explicit allowlisted public view-model supplies presentation,
    rather than spreading API objects. Unknown/nested private fields are excluded
    by tests. Existing public measurement-notice and pace helpers are reused;
    no private-load or physiology calculation pipeline was added. Recursive
    privacy passes. Runtime observers save method/path/status and allowlisted
    public fields only, never authorization headers, credentials or full API
    objects. Secrets and runtime artifacts remain ignored and unstaged.

## Software and authenticated evidence

20. **Full mobile suite: 510 tests / 58 suites, all passed.** Accepted baseline
    was 459/55; this slice adds **51 tests / 3 suites**: 10 public view-model,
    21 composition, 15 real-owner boundary and 5 real-router regressions.
    Existing Activity owner 36, V1 Activity 3, Planning owner 76, navigation 43,
    creation 14, proposal review 12, Calendar latest-request/range/return,
    Week, Workout Detail, active moves and transport/RPE/idempotency tests pass.
    New tests cover external selection and swim distance-only submission too.
    Earlier placeholder Activities assertions were replaced by actual V2
    content assertions; expected Calendar/onboarding calls now include the
    unchanged activity entry's supported four-read load. No guard was weakened.
    Existing unrelated act/layout console warnings remain without failures.
21. **Strict TypeScript / unused:** `npm run typecheck` and
    `npm run check:unused` passed. New sources use the existing TypeScript
    formatter; final staged and complete-parent diff checks pass. No dependency
    or formatter package was installed. Final JSON/logs are in ignored
    `mobile/.runtime/slice5b/final-tests.*`, `final-typecheck.log`,
    `final-unused.log` and focused `final-boundary.log`.
22. **Authenticated emulator: PASSED.** Reused emulator-5554, API 35 and the
    existing Wombo development client. Metro on 8088 supplies this exact
    worktree, verified by manifest projectRoot/bundle URL and native V2
    component/owner inspection. One tagged start23-dev athlete used normal
    Auth/profile/history/calibration/zone onboarding; login typed generated
    credentials into normal Auth UI without token/session injection.
    The naturally pending calibration activity was explicitly completed first.
    Then V2 Add → valid 45-minute/5000-metre run → one POST (201) → exact
    pending item → blocked Add → Back/Week/Calendar/Activities/reminder → same
    feedback → explicit RPE 4/151 bpm → one PUT (200) → server history complete,
    pending/reminder clear → Week/Calendar/Activities again. Unsaved Back and
    both safe presentation-switch directions also passed.
23. **LIVE versus TEST:** sanitized native network evidence records precisely
    one manual POST and one PUT for that new activity, plus one PUT for the
    separate calibration item. Initial Activities entry and each successful
    mutation perform one full history read. Root and UI comparisons alone cause
    zero extra full history reads/mutations. Two later full history reads follow
    full Android restarts caused by changing/restoring system font scale, not
    presentation switches; supported reminder reads remain visible separately.
    Deterministic tests cover empty/error, all measure combinations, all sports,
    external/planned repeated identities, ambiguous transport, post-POST read
    failure, typed RPE recovery/stale responses, rapid taps, token rotation,
    concurrent changes and athlete replacement. Rare states were not
    manufactured in staging. LIVE mutation evidence is not claimed for those.
24. **Functional references:** 20 ignored PNG/XML captures under
    `mobile/.runtime/slice5b/`. Core references: `activities-initial`,
    `activity-entry`, `activity-entry-filled`, `pending-feedback`,
    `pending-create-blocked`, `reminder-feedback-return`,
    `pending-v1-comparison`, `pending-v2-return`, `rpe-before-save`,
    `activities-after-rpe`, `activities-result-detail`,
    `rpe-large-text-choices`, `rpe-large-text-last`, `signed-out`.
    List state was available live; truthful empty state is test evidence.
    Screenshots were visually inspected and are functional references for later
    mockups, never final art direction. The recovery/loading captures remain
    separately identifiable by name.
25. **Disposable cleanup: PASSED.** Exactly one owned tagged athlete created
    and reused, no replacement. Normal app sign-out preceded global session
    revocation and deletion of only the owned Auth user. Admin lookup returned
    404; zero matching owned/tagged users remain. Ignored
    `slice5b-authenticated-cleanup.json` records created=1, deleted=1,
    sessions_revoked=true, admin_get_status=404 and matching users=0.

## Boundaries and delivery

26. **Intentionally V1:** Auth, onboarding, Profile, zones, check-in, tests,
    integrations and other unimplemented destinations retain their accepted
    fallback. The development V1 Activities comparator remains usable with its
    original body/styles. There is no separate existing ActivityDetail screen;
    its existing history/result/matching/correction capabilities are preserved
    inside Activities. No new WorkoutDetail-to-entry handoff or root was added.
27. **Visual status:** PROVISIONAL FUNCTIONAL ACTIVITIES/RPE SCAFFOLD. Tokens,
    Text/Card/Button/Divider/SportIndicator and FlashList are reused; only a
    small growing Input primitive and RpeChoices composition were necessary.
    No final icons, animation redesign, charts, filters or decorative analytics.
28. **Packages:** NONE changed, including manifests/lockfiles/native dependencies.
29. **Backend/API/database:** NONE changed. API client/DTOs and all three domain
    controllers/providers are unchanged. No Garmin, coach, PDF/privacy-project,
    ingestion or physiological/planning-rule work was included.
30. **Local integration:** `feat/wombo-ui-v2` is advanced locally from the exact
    accepted 5A SHA to this report delivery head only after clean worktree,
    expected-ref and ancestor checks. No merge/rebase/squash or history rewrite.
31. **Physical gates:** physical TalkBack, iOS/device coverage, release acceptance
    and final visual/mockup validation remain open. All required Slice-5B
    software and authenticated emulator functional gates passed.
32. **Main/unpushed:** main remains
    `fb56c51d983564c652d83fc15e02b039e9063d3f`; root branch/head and unrelated
    dirt are untouched. Exact-path staging only. No push performed.
33. **Production:** untouched. Only `r6-api-r6-staging.up.railway.app` and
    start23-dev were used for the owned disposable fixture; no deployment.

## Autonomous decisions and recoveries

- History, entry and feedback are controlled presentations over one shared
  owner. The existing authenticated presentation context holds only view and
  correction ID above navigator replacement; no domain/form state was moved.
- Existing read-only week/matching presentation helpers were relocated intact
  into `features/activities/activityPresentation.ts` so V1/V2 reuse them.
  Current ISO entry/validation and canonical save-on-choice semantics were
  retained; a new date conversion, RPE transaction or unsupported input would
  change behavior. Full localized dates are displayed from supplied timezone.
- Real router tests exposed safe Activities comparison returning to Week during
  navigator replacement. The smallest origin restoration fixes that while
  preserving the accepted initial-Week/Back behavior; native comparisons pass.
- Native computer-use IPC was unavailable. Authorized ADB interaction with fresh
  native trees and read-only Hermes inspection supplied the emulator evidence.
- Initial Metro bound IPv6 `::1`, incompatible with ADB's IPv4 loopback. Only the
  verified 5B Metro process was stopped; restarting with IPv4-first DNS and
  cleared cache restored the client. No source workaround or native rebuild.
- Android font-scale changes restarted the app. The same server-pending item
  was resumed through normal Auth/session/reminder behavior; ephemeral HR was
  re-entered after that full restart. The original 1.0 font setting was restored.
  Live draft retention is proven across ordinary roots/UI comparisons, not
  incorrectly claimed across process/configuration restarts.
- An interactive fixture helper retained stdin until all flows were finished,
  then performed guarded cleanup. No account replacement or mid-run question
  was needed. A test's external-context wording was corrected to the existing
  product label “Outside Wombo”; product copy/behavior did not change for it.

Commits before this report:

- `5bd93f23c3f52e36395ec2672b4621d615f3c7b4`: provisional public compositions.
- `cccdd830b0f8015988d3d341cdd088750ac926ee`: shared boundary/shell/navigation.
- `4925a4458357f5bbfbc3d27b538dbb9735af28ef`: identity/idempotency/RPE/navigation
  regressions. The report-only delivery commit follows without runtime changes.

WOMBO UI V2 SLICE 5B COMPLETE — FUNCTIONAL ACTIVITIES/RPE SCAFFOLD ACCEPTED
