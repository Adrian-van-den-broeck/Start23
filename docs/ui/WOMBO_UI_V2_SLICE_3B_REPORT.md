# Wombo UI V2 Slice 3B — root training navigation shell

Date: 2026-10-05. Visual status: **PROVISIONAL FUNCTIONAL NAVIGATION SCAFFOLD**.
Only the approved Week / Calendar / Activities navigation slice is implemented.
Activities and all unimplemented tasks retain their V1 bodies. Final mockups,
premium styling and Activity controller extraction remain deferred.

## Prerequisite and provenance

Before runtime edits, verified exact commit
`c68cdf5a9f7e62b6f609f2ae9cf8abfe50600960` on
`feat/wombo-ui-v2-calendar-readonly`. Its report ends with
`WOMBO UI V2 SLICE 3A COMPLETE — FUNCTIONAL CALENDAR SCAFFOLD ACCEPTED`.
Reran **259 tests / 45 suites**, strict TypeScript and unused checks successfully;
recursive privacy coverage passed. Audited the singular Slice 2A Planning owner
and the Calendar owner inside the same PlanningFlowProvider. Week and Workout
Detail were green. No unresolved functional 3A defect blocked this slice;
final visual acceptance was intentionally not required.

Read root/mobile AGENTS, the current MVP roadmap, V2 specification, screen map,
implementation plan, architecture, and Slice 2A/2B/3A reports.

- Exact starting SHA: `c68cdf5a9f7e62b6f609f2ae9cf8abfe50600960`.
- Branch: `feat/wombo-ui-v2-navigation-shell`.
- Isolated worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-navigation-shell`.
- Initial runtime commit: `c6e8cb1d1283dbf1975834f87bb5a816825d3f19`.
- Navigator replacement fix: `2eb1e52e589a5f03eff44160c458dcfdb9e79c94`.
- Final verified runtime SHA: `dfa47d51c9a182e506f352a8c8cccc85ddae8655`.
- Final delivery SHA is the documentation commit containing this report:
  `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_3B_REPORT.md`.

## Navigation architecture and ownership

The existing authenticated Expo Router Stack hosts a pathless `(training)` group.
V2 uses the installed, non-experimental JavaScript Tabs with exactly **Week,
Calendar, Activities**, lazy destination mounting and `backBehavior="initialRoute"`.
V1 uses the original Stack navigation and original Planning presentation.
Public `/planning` and `/activities` URLs remain unchanged; `/calendar` is added.
Profile remains an existing secondary route reached from each root.
There is no fourth tab, Coach destination, second bootstrap, new navigation
library, state library, icon dependency or experimental navigator.

| Responsibility | Before | After |
| --- | --- | --- |
| AuthProvider / LanguageProvider / UiVersionProvider | App root | Same app root, unchanged |
| PlanningFlowProvider / Planning controller | PlanningScreen above conditional screen bodies | Readiness-gated TrainingFlowHost above authenticated Stack |
| Calendar controller | One hook inside PlanningOwner | Same sole hook inside that same retained owner |
| Root/task/detail selection and scroll refs | PlanningBoundary-local state | PlanningPresentationProvider beside the flow owner, above navigators |
| Calendar mode, anchor, selected date | Boundary-local navigation hook | Same navigation hook in shared presentation owner |
| Activity form/RPE | V1 ActivityScreen | Same V1 screen, lazy mounted; no extraction |

The host is keyed by **actual authenticated athlete identity**, never the access
token. It activates only on first training entry, checks the existing onboarding
current step, and mounts flow ownership only after readiness succeeds. Auth and
direct onboarding/task routes do not bootstrap Planning. Loading/error stays
closed; incomplete or version-resume states redirect to the existing onboarding.
The gate's initial onboarding snapshot supplies the controller's primary goal,
avoiding a duplicate initial gate/controller read. Token refresh preserves owner
identity and the original token-dependent controller behavior.

PlanningFlowProvider still guards against nesting a second owner. Actual router
tests preserve controller function identity, the exact draft object and revision,
proposal/plan context, Calendar reader identity, mode/date/range and scroll refs.
They assert one restore and no root-switch draft creation, transition or approval.
Native snapshots count **one PlanningOwner** and one Calendar context; stable
function references survive roots, Profile and safe V1/V2 comparison.

Changing Stack/Tabs type uses a brief presentation-only teardown commit before
mounting the replacement. Native verification caught incompatible state reuse
when the old navigator had not unregistered; a key alone was insufficient. The
final fix waits for teardown, keeps owners mounted, and passed both native switch
directions plus repeated approved-plan and resumed-draft router regressions.
An additional native bottom-of-Month check exposed scroll clamping when removing
the tab bar behind detail enlarged the viewport. The final modal keeps the
measured destination footprint and safe bottom inset, inaccessible and inert,
so the underlying Calendar viewport does not change. No hidden duplicate tabs
are announced. A measured-height regression and the native bottom check cover it.

## Destination and compatibility results

| Requirement | Result |
| --- | --- |
| Week | Existing V2 WeekScreen/mainAction reused; accepted plan/draft/provenance and V1 task fallbacks retained |
| Calendar | Existing read-only Calendar reused; mode/date/anchor, loaded provenance and latest-request guard retained; no moves added |
| Activities | Root destination renders original V1 ActivityScreen; form, HR/RPE, persistence and idempotency behavior retained |
| Profile | Existing route/settings/integrations/Pioneer/language/sign-out retained; actual root origin restored |
| Workout Detail | Existing shared WorkoutDetailBoundary receives the exact selected source object; Week/Calendar origin remains intact |
| Task routes | Existing creation, availability, selection, placement, review/editor, activity, check-in, zones, tests/calibration and onboarding bodies retained |
| Direct routes | `/planning`, `/calendar`, `/activities`, `/profile`, `/tests`, `/calibration`, `/onboarding` resolve through existing Router hierarchy; tests cover legacy calibration redirect and task-to-Week fallback |
| Android Back | Calendar/Activities roots settle Week through initial-route semantics, not tab history; Week delegates existing parent/root behavior; detail closes to its exact origin; settled planning task returns Week |
| Onboarding gate | Unauthenticated entry returns Auth with no training reads; incomplete/version-resume direct roots reach onboarding; completed readiness reaches shell; failed readiness retries closed |
| Pending RPE | One existing global reminder/count/action across roots; native fixture count 1 remained discoverable; navigation disabled during unresolved flow/sheet writes |
| UI fallback | Requested V1 retains original presentation/internal navigation; requested development V2 enables shell; non-development remains forced V1 |
| Language | Same LanguageProvider; Dutch Week/Kalender/Activiteiten and English Week/Calendar/Activities covered |

Unsafe switching remains disabled during planning writes, pending move confirmation,
editor loading, Activity writes and the pre-write swipe animation. Existing V1
transient tasks remain V1 until settled. Existing deferred-dismiss helper closes
Profile sheets before route actions; root/reminder navigation cannot occur beneath
an open/dismissing sheet. Back performs no data rollback.

Calendar's `ensureCalendarRange` reuses the same pending or successfully loaded
range. A different in-flight range is superseded even when returning to a retained
range; baseline rapid-request protection remains green. Approved plan identity or
active revision changes invalidate reuse without erasing rendered provenance.
Hidden Calendar does not fetch: the next focused presentation reloads invalidated
data. Only the focused PlanningBoundary renders Week/Calendar and runs the range
effect. There is no duplicate Planning bootstrap, hidden range effect or dual
V1/V2 root. Activity's lazy presentation retains its existing local state after
first visit; flow ownership remains independent of presentation mounting.

## Verification

| Gate | Exact result |
| --- | --- |
| New navigation/provider suite | **30 tests / 1 suite passed** |
| Full mobile suite | **289 tests / 46 suites passed**, zero snapshots |
| Increase from prerequisite | **30 tests / 1 suite** above 259 / 45 |
| Planning / Week / Calendar / Workout Detail / Activity V1 / root navigation | All included and passed in the full suite |
| Strict TypeScript | `npm run typecheck` passed |
| Unused code | `npm run check:unused` passed |
| Privacy | Recursive source/adapters privacy suite passed; public Calendar/plan response and 21 reference UI XML artifacts scanned |
| Formatting / diff | Installed TypeScript formatter on changed modules/boundary; `git diff --check` passed |
| Package/native changes | **NONE** |
| Backend/API contracts/database changes | **NONE**; no backend suite needed |

New actual-router regressions cover singular ownership, cached/pending Calendar
returns, active-revision invalidation, exact selected detail object, drafts and
safe navigator replacement, readiness/retry/version-resume, all Profile origins,
legacy direct routes, root/task Back, RPE, language, mutation/sheet locks, token
rotation, sign-out and identity replacement both with and without an intermediate
sign-out. No skipped or weakened baseline tests.

Accessibility fundamentals: visible localized labels, role tab/selected state,
one announcement per destination, logical route order, text wrapping without a
line cap, minimum 56 dp destination height/48 dp width, safe bottom inset and
global reminder's top inset. Native root targets measured 360 × 154 px at density
440: approximately **131 × 56 dp**, no overlap. Physical TalkBack, focus-return
and physical-device/release acceptance remain open; none is claimed here.
Registry remains exactly `workoutDetail`, `week`, `calendar`.

## Authenticated emulator and functional references

Reused running `emulator-5554`, API 35, and `com.adrivdbs.wombo`, without native
rebuild/reinstall. Task Metro **8083** serves this isolated worktree; previous
Metro 8082 was preserved. Native computer-use pipe was unavailable after retry;
ADB helpers used fresh native UI trees/observed bounds, normal taps, scrolling,
keyboard entry and Android Back. No session/token injection or app instrumentation.

One user-authorized tagged start23-dev disposable athlete was prepared through
supported Auth/domain APIs. Normal UI created one draft, selected two genuine
catalog workouts, submitted a pending proposal and explicitly approved it.
The real active plan has two run occurrences and five server-supplied rest dates.
Verified sign-in -> Week -> Calendar -> Activities -> Week, Calendar Month/date
selection -> detail -> Android Back, Profile origins from each root, existing V1
planning task -> Week, safe V1/V2 comparison, sign-out -> Auth -> normal re-entry.
Re-entry mounted fresh owners, an empty Calendar range and supported saved-plan
restoration. Different-athlete isolation is explicitly covered by router tests;
no second disposable athlete was created.

Month detail returned to selected **2026-10-14**, October mode, anchor/range
`2026-09-28` through exclusive `2026-11-02`, retaining the scroll context.
The original verified pre/post detail interval stayed at **57 observed API requests**;
the later detail interval stayed at **110**: zero detail reads/mutations.
The committed bottom check retains **647.272705078125 dp** before, during and
after detail, and proves `exactCalendarObject=true` for the actual occurrence.
Timestamped network evidence also shows zero requests during that final committed
bottom-of-Month interval.
Stable native owner references and router call-count
assertions distinguish navigation from the preserved global pending-RPE refresh.
Network evidence includes earlier Fast Refresh/error-recovery intervals; those
are excluded from owner-lifetime or duplicate-bootstrap acceptance claims.
Read-only network observation archives method/path/status and public responses,
without headers, credentials, Auth responses or tokens. Some response bodies
were unavailable; supported authenticated public snapshots supply source/privacy
comparison. Tests prove loaded Calendar return and pending reads do not duplicate.

Functional reference PNGs with companion XML are local, ignored artifacts under
`mobile/.runtime/slice3b/`: `week-root`, `calendar-root`, `activities-root`,
`profile-from-calendar`, `profile-return-activities`, `calendar-month`,
`calendar-month-selected`, `calendar-detail-open`, `calendar-return-verified`,
`existing-v1-task`, `task-return-week`, `root-back-week`, `navigator-v1-verified`,
`navigator-v2-verified`, `profile-final-source`, `final-calendar-root`,
`final-calendar-month`, `final-calendar-selected`, `calendar-scroll-fixed-detail`,
`calendar-scroll-fixed-return`, and `final-signedout`. These are references for later custom mockups, not final
art direction. Literal replacement characters supplied in catalog names remain
intact, as in accepted 3A.

## Fixture cleanup, isolation and remaining gates

The user explicitly authorized **one disposable start23-dev athlete for Slice 3B**;
no previous slice authorization was assumed. Exactly one account was created and
deleted. Hosted mutations were limited to this owned fixture, its supported
onboarding/calibration/zone/plan workflow and its lifecycle; no production access
or direct domain-row writes occurred.

Native input truncated the long temporary password during re-entry. An
ownership-checked password reset of the same fixture plus slow normal keyboard
entry resolved the automation issue, without creating a second account or
changing Auth implementation. The original helper's cleanup JWT subsequently
returned 403 because its session was already revoked. A separate ownership-guarded
cleanup session was acquired for that same actor, globally revoked, and the actor
was deleted. Final proof: **created 1 / deleted 1**, global revocation successful,
admin GET **404**, **zero matching own tagged users**. Evidence is
`slice3b-authenticated-cleanup.json`. Credentials/keys/tokens remained temporary
in helper memory, never committed or recorded in network evidence. Helpers and
observer are stopped. The final app is signed out with no Planning/Calendar owner.

Local `feat/wombo-ui-v2` was verified an ancestor of the fully tested Slice 3B
head. It is fast-forwarded locally from
`7a7259125d2a6a907cf9c175379ae6570aabf71b` to the documentation delivery commit
using an expected-old ref update. No merge, rebase, squash or push is used.
Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`.
Annotated V1 baseline tag object remains `d39bfcd2cf6dcc17aca231502ac4ab4e46c0465a`.
The original dirty `fix/pre-ui-beta-blockers` checkout and unrelated coach,
Garmin, privacy, PDF and deployment work remain untouched: no reset/stash/staging.
Nothing was pushed or deployed. Production is untouched.

Open gates: physical TalkBack/focus return, physical-device acceptance and
existing release gates. Final user mockups will supersede provisional visuals.
This slice claims functional navigation acceptance, not final visual or physical
accessibility acceptance. No functional navigation defect remains unresolved.

WOMBO UI V2 SLICE 3B COMPLETE — FUNCTIONAL NAVIGATION SCAFFOLD ACCEPTED
