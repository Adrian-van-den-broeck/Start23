# A9 mobile journey and loading review

This inventory covers implemented routes and internal tasks; it does not invent
separate Goal, workout-detail, candidate or RPE routes. The timing evidence uses
representative actual V1 screens, Expo Router and shared owners, plus an isolated
native release-variant app. Other rows are source/dependency inspection and
functional/call-count regression coverage, not invented device timings.

| Screen / task | Existing loading and ownership | A9 assessment and evidence boundary |
| --- | --- | --- |
| App startup / authentication | One AuthProvider, stored refresh credential, SDK refresh and A8 recovery gate; one authenticated host keyed by athlete | Native authenticated process-restart benchmark; actual synthetic SDK sign-in exercised. Auth lifecycle/offline/retry/token rotation/logout/account-switch remain covered by A8 tests. Real provider latency and a repeated password-login timing series were not measured. |
| Login → intake → training | Completed intake previously awaited three parallel reads, including two unrelated form resources; a changing callback restarted its effect | Actual OnboardingScreen timing 257 → 59 ms under controlled 40/240 ms reads. Auxiliary requests remain parallel for incomplete intake. Completion no longer waits for them; callback changes no longer restart loading. No authenticated access is granted by this shortcut: confirmed completion and AuthProvider gating remain required. |
| Onboarding profile, HR-monitor, timezone, history, goal, zones, review | Steps within OnboardingScreen; authoritative state plus goal-options and physiology form resources; subsequent writes reload state | All step/form regressions retained; no new standalone Goal route. Initial incomplete intake still waits for its required form resources. No new timing claim for every individual step. Existing revision guards and explicit zone approval are unchanged. |
| Profile | One complete onboarding read per mount; retained shell also refreshes pending-RPE reminder on the route change | Native cold/warm revisit measured: two requests each, preserved. Profile is not made authoritative from a permanent cache. Native measurements show no convincing improvement and no gain is claimed. |
| Profile → Tests; `/tests` and `/calibration` | Both route aliases use CalibrationScreen: calibration-status and onboarding in parallel, then protocol loads for configured disciplines | Actual ProfileScreen + CalibrationScreen + A8 client integration verifies one onboarding transport while both consumers overlap. Sequential protocol loads depend on status; no speculative unrelated fetches added. Full calibration regressions pass. Dedicated native calibration timing not captured. |
| Zone profile | `/zone-profile`; zone-profile state and onboarding load in parallel; pending zone/test decisions remain explicit | Source and zone/profile/calibration regressions; no redesigned approval or physiological behavior. No dedicated native latency claim. |
| Week / Home | TrainingFlowHost readiness, PlanningFlowProvider and PlanningPresentationProvider retained above Stack; saved locator plus account discovery enforce A6 freshness | Native cold startup and development cold/warm screen benchmark. Locator/discovery reads deliberately retained; transient errors cannot become empty-plan success. Native startup request count remains nine in the documented fixture. |
| Week → Calendar → Week | Shared calendar owner/navigation; initial range read, valid warm reuse; A4 approval handoff replaces authoritative week | Native and actual-router tests. Warm transitions remain zero-request. V1's view-keyed entrance wrapper unnecessarily remounted and restarted its 420 ms fade; it now persists while retaining first entrance/layout styling. Calendar → Week stable-marker median 876 → 530 ms with coarse capture overhead. Calendar entry shows no convincing native gain. |
| Week / Calendar → Workout Detail → Back | Existing workout snapshot and presentation owner; no new detail data owner or required detail fetch | Detail, supporting-sheet and return-navigation regressions; source confirms local snapshot use. Native detail latency not sampled. No stale snapshot is promoted into permission to mutate. |
| Planning → candidates → placement → proposal | Internal tasks of the shared planning/presentation owners; server-curated draft, occurrence IDs, placement revision and mutation locks | Full creation/boundary/controller tests and backend parity. The actual full-catalog swipe-create HTTP path is measured before/after. No optimistic success, early approximate selection or new retry loop. Individual native card/placement latency not sampled. |
| Proposal approval → Week / Calendar | Exact receipt/revision read-back, authoritative handoff and existing return route | A4/A5/A6/A8 navigation and proposal/approval regressions. Approved data replaces old snapshots; pending remains separate. Approval is not made optimistic for speed. |
| Week → Check-in → Week | Shared readiness; check-in controller retains week/check-in/proposal identity and immutable confirmed context | Actual check-in navigation and A3/A5/A8 tests retained, including injury/professional advice and ambiguous proposal replay. CPU planning uses the same bounded worker. No dedicated native check-in timing claim. |
| Week / Calendar → Activities | One ActivityFlowProvider retained by athlete. Genuine entry/focus refreshes activities, calendar, onboarding timezone and external tasks; pending reminder is separately refreshed | A7's four-way refresh and remote pending-RPE resolution are preserved. No new TTL suppresses remote results or drops unresolved local work. Existing V1 and V2 history presentation already uses FlashList; no unnecessary list dependency/refactor. |
| Activity entry → RPE / correction | Form and unresolved create/RPE operation held by existing owner; synchronous locks; immutable original payload/key/precondition; RPE saves on selection | Full activity, real navigation and A8 transport/reconciliation tests retained. No extra confirmation or delayed save. No native save/RPE latency series is claimed. |
| Activities history / detail | Shared activity state; existing virtualized lists and public view models | Activity/view-model/privacy tests retained. Source review found the existing list-activities RPC is unpaginated. No database/history-volume performance was measured; changing its response/history contract is a separately scoped follow-up, not an arbitrary cap added here. |
| Workout movement | Existing calendar/workout task, expected revision, qualitative warnings and owner lock | Movement/domain/navigation regressions pass; no new scheduling rule or mutation shortcut. No native movement latency series captured. |
| Integrations | Connection first; imports fetched only for a connected account | Dependent fetch retained, not parallelized into unnecessary work. Integration regressions pass. Hosted integration latency not measured. |
| Pioneer access / supporting tasks | Existing task routes and shared return boundary; explicit user action for redemption | Existing tests and source review. No new screen, confirmation or data owner. Dedicated native timing not captured. |
| Revisit / plan mutation / owner switch / offline / foreground | A4 invalidation and authoritative handoff; A6 locators; A7 refresh and unresolved activity state; A8 deadlines, recovery and retired-token cancellation | Deterministic state/call-count tests cover invalidation, warm reuse, late results, account switching, offline/retry, background/foreground, bounded settlement and preserved forms. These are functional benchmark-matrix entries, not production latency distributions. |

The eleven onboarding Data API operations were **already parallel**. A new
barrier-based MockTransport regression verifies all eleven start before any can
complete, and each query/RPC retains its owner token/filter. A9 coalesces only
overlapping complete-state reads by exact token. Write start/settlement fences
ensure a post-write refresh cannot join a pre-write or mid-write read; late
cleanup cannot remove a newer flight. There is no completed-response cache.
Two overlapping consumers issue one state request instead of two. Independently,
MockTransport confirms eleven parallel operations per `fetch_state`. Removing
one such state request removes one eleven-read fan-out; this is a derived count,
not a measurement of hosted Supabase traffic or latency.
Nonoverlapping Profile and Activity freshness reads are deliberately preserved.

Development React Profiler and real-time controlled mocks measured renders,
commits, request counts and loading/callback durations for representative screens.
The native harness measures a stable public heading/form-label marker after
required data, with its capture overhead included. It does not measure exact
first-frame visibility, physical touch latency, all Hermes JS stalls or native
commit duration. Those limits prevent treating renderer numbers as release
performance or treating the emulator's sampled upper bounds as production SLAs.

No visual tokens/styles, training rules, owner-scoped locks, localization strings,
database architecture or API payload semantics were changed. No generic cache,
background synchronization framework or automatic mutation replay was introduced.
