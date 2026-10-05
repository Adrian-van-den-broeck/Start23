# Wombo UI V2 Slice 4B report

## Acceptance, provenance and scope

Slice 4A prerequisite: **VERIFIED before runtime edits**. Its report ends with
`WOMBO UI V2 SLICE 4A COMPLETE — FUNCTIONAL PLANNING SCAFFOLD ACCEPTED`.
The actual clean accepted delivery head, resolved from that report, is
`addaffc7300d745e72017abcadd5cab486b5b8b7`. Local `feat/wombo-ui-v2` matched it.
Slice 3B remains accepted at `30a7b6e60697844635f2b58b5fc1a1dab4ae289d`.
Before editing, the accepted 4A mobile suite was rerun: **335 tests / 49 suites**,
zero failures; strict TypeScript, unused, privacy and diff checks passed.
Its source, focused coverage and authenticated report verified availability,
Choose/Pass/Undo/Reset, occurrence identities, automatic/manual placement,
pending-only submit, resume/re-entry and duplicate protection. Protected-path
checks confirmed no package/backend/API/database changes. One Planning owner and
one Calendar owner remained. The accepted starting worktree was clean.

- Starting full SHA: `addaffc7300d745e72017abcadd5cab486b5b8b7`.
- Dedicated branch: `feat/wombo-ui-v2-proposal-review`.
- Isolated worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-proposal-review`.
- Verified implementation SHA: `8cebff9593aa04282a0a5f50e210febeae942f64`.
- Final delivery SHA is the report-only commit containing this document. Resolve
  its exact full SHA with `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_4B_REPORT.md`.
- Target: local `feat/wombo-ui-v2`, fast-forward only after all gates passed.
- Visual status: **PROVISIONAL FUNCTIONAL PROPOSAL-REVIEW SCAFFOLD**.

Root/mobile AGENTS, current roadmap, V2 implementation plan/architecture,
Slice 2A/3B/4A reports, Joren workout-selection phase including its final addendum,
and Joren planning ruleset records supplied the functional constraints.
No Slice 4C or new active-plan move UI is implemented.

## Shared owner and review behavior

`PlanningBoundary` opens task `review` from the existing Week review action.
The `proposalReview` registry capability selects `PlanningProposalTask` and the
controlled V2 `ProposalReviewScreen` / `ProposalAlternativesScreen`.
Broad Planning remains V1; release behavior still forces V1. Review is a task,
not a fourth root tab. Calendar and Activities retain their existing roots.

There is one `PlanningFlowProvider`, one `PlanningOwner` invocation of
`usePlanningController`, one Calendar controller and one existing
`usePendingWorkoutActions` transaction owner. The task consumes existing values
and actions; it has no API client or second domain hook. Presentation state adds
only the selected editor's workout ID. Local radio selection/removal confirmation
are presentation choices. References used to invalidate old callbacks/options
point to the shared snapshot; they are not copied proposal/revision stores.
Provider nesting tests, actual-router identity tests and read-only native
component snapshots prove retained singular owners.

The public review model explicitly allowlists the plan/proposal/revision context,
exact pending workout ID, template ID/key/version, source, assigned date, public
status, sport/name, supplied duration/distance/intensity, safely filtered
planning description and existing qualitative warnings. Workouts retain server
order and are keyed by workout ID. Repeated templates remain distinguishable
with independent IDs and numbered choices; there is no aesthetic reordering.
Planning-card expected-RPE description suppression remains intact.

An active approved snapshot remains the authoritative Week schedule while a
replacement proposal is reviewed separately. Review displays only proposed
workouts and explicitly says the approved plan remains active until approval.
**FIXTURE/TEST:** different active and pending workout names/IDs prove Week and
review never merge schedules; only explicit approval advances the active
snapshot. Explicit rejection retains the original active workout. Native live
verification used pending-only proposals, so active-plus-pending coexistence is
not claimed as a live staging state.

Actual warnings retain supplied severity and existing safe public wording.
Info is neutral; real warning/conflict data receives its existing meaning.
Pending context itself is neutral. Warnings stay visible, including after editing;
no local spacing, count, safety, target-fit or physiological calculation is added.
A warning is not converted into a new approval blocker.

## Alternatives, edits and decisions

| Requirement | Result |
| --- | --- |
| Alternatives lifecycle | V2 fetches only after opening a specific pending workout editor. No eager per-workout V2 GET. Existing shared slot/release lifecycle is reused. V1's original eager editor mounting behavior and carousel body remain unchanged. |
| Exact options request | Existing GET `/api/v1/weekly-plans/{plan_id}/pending-workouts/{workout_id}/alternatives?expected_revision={revision}`. Exact owner plan/workout IDs and reviewed revision are retained. |
| Returned options | Exact returned plan/revision/proposal/workout identifiers, returned template IDs and `can_remove` are retained. Loading, safe error, empty results and explicit retry are usable. Current template is displayed separately using the existing V1 filtering convention. No recommendations or tradeoffs are inferred. |
| Replacement | Existing POST `.../pending-workouts/{workout_id}/edit-proposals`, with `expected_revision`, `expected_proposal_id`, `replacement_template_id` from reviewed options/selection. Only returned templates are eligible. Shared owner receives `result.plan`; success returns to review. No fabricated optimistic replacement or automatic approval. |
| Removal capability | Functional Remove exists only when `can_remove === true` and the snapshot remains pending. False or unknown produces no removal action. No active-plan deletion or new delete endpoint. |
| Removal confirmation | First press names the consequence; Keep cancels. Separate Confirm removal invokes the same edit transaction with `replacement_template_id: null`. Exact null payload and returned state tested. Live server returned false, so removal acceptance is **FIXTURE/TEST**. |
| Stale/superseded/expired | Shared pending/current-snapshot guards reject old captured decision callbacks and edits from obsolete options. Changed proposal closes the old editor. Expired/superseded/rejected/active snapshots cannot decide. Late options/edit acknowledgments cannot resurrect cleared or replaced state. |
| Safe errors | Existing transport-safe errors remain visible. No backend-message parsing, automatic recreation, replay of decision intent, hidden refresh or speculative repair. Stale failures preserve the reviewed state and require another explicit action. |
| Approval | Only explicit Approve week / Week goedkeuren calls existing POST `/api/v1/change-proposals/{proposal_id}/approve` with exact `expected_base_revision`. Existing follow-up `getWeeklyPlan(token, plan.id)` has no revision argument. Returned active snapshot goes to V2 Week. |
| Rejection | Only explicit Reject proposal / Voorstel afwijzen calls existing reject endpoint. The unusual existing follow-up `getWeeklyPlan(token, plan.id, originallyReviewedPlan.revision)` is preserved exactly. Authoritative result returns to Week; active snapshot is retained where applicable. |
| Back / Close | Editor Back returns to the same review; review Back returns Week without approve/reject, recreation, discard or revision reset. Unresolved writes and unsafe switches remain locked. |
| V1 / V2 | Settled comparison swaps one task body around the same shared proposal/revision/workouts/warnings. No simultaneous task presentations or mutation from preference changes. |

Shared synchronous mutation locking now covers pending edits and decisions using
the controller's existing ref. Double presses and cross-control calls are blocked
before React renders busy. Outstanding alternatives requests also block writes;
requests deduplicate within the same snapshot/editor lifetime. Request identity,
plan reference and lifetime checks prevent released late responses from populating
a newly mounted same-ID editor or clearing its newer loading state. No V2 lock or
mutation effect is introduced. Existing navigation/slot loading locks announce
busy and disable critical controls. Deferred tests cover rapid duplicate GET,
replace/remove/approve/reject, cross-decision/edit calls, rerender, stale callbacks,
release/remount, root navigation and preference switching.

## Accessibility and privacy

Review has a heading, explicit pending state, readable actual warnings,
independently reachable workout actions naming choice and source workout,
radio checked state, clear removal consequence and explicit NL/EN decision labels.
Approve and Reject use different button hierarchy with divider/target separation.
There is no gesture-only action. Existing buttons have minimum 48 dp targets;
native critical controls measured approximately 50.2–52 dp at density 440.
Busy/disabled state and safe errors have accessibility state/live announcements.
Text wraps without fixed text heights and final actions scroll within safe-area
content; native final decision/replace controls were reachable and unclipped.
These are accessibility fundamentals, not physical TalkBack or comprehensive
large-font acceptance. Physical screen-reader, focus-return and device/release
checks remain open.

Public models use explicit allowlists. Poison-field/recursive source privacy
coverage passes, including TSS, private planned/realized load, target-fit and
selector diagnostic exclusion. The new UI has no proposal-object logging.
Scanned **18 native XML/public response/network artifacts**, zero forbidden
matches. Public descriptions continue through the existing RPE suppression mapper.
Auth credentials, secrets and sessions remained helper memory / established
secure storage; no environment file or runtime evidence is committed.

## Software verification

| Gate | Exact result |
| --- | --- |
| Accepted 4A rerun before edits | 335 tests / 49 suites passed |
| New proposal model suite | 10 tests passed |
| New controlled review/alternatives screen suite | 6 tests passed |
| New shared-owner proposal boundary suite | 12 tests passed |
| Planning owner suite | 53 tests passed, including 13 new Slice 4B cases |
| Actual navigation-shell suite | 34 tests passed, including 2 new Slice 4B cases |
| Full mobile suite | **378 tests / 52 suites passed**, zero failures/skipped/todo; zero snapshots |
| Increase over accepted 4A | **43 tests / 3 suites** |
| 4A / Week / Calendar / Workout Detail / V1 planning regressions | Included and passed in the full suite |
| Strict TypeScript | `npm run typecheck` passed |
| Unused code | `npm run check:unused` passed |
| Privacy | Recursive source, poisoned public allowlists and native artifact scan passed |
| Formatting/diff | Installed TypeScript formatter on new modules; staged and accepted-parent diff checks passed |
| Source parity | Original V1 editor/presentation bodies, 4A create/transition/place/submit bodies and existing active-move bodies compared byte-for-byte unchanged |
| Package changes | **NONE** |
| Backend/API/database changes | **NONE**; protected-path diff empty, backend suite not applicable |

Older Week-boundary tests asserting the superseded V1 review body were updated to
assert the approved V2 body and direct authoritative Week return. Their identity,
read and mutation assertions were retained. Existing V1 owner/transaction tests
and late-response lifetime regression remain green. New distinct-schedule tests
explicitly prove active/pending separation across both decisions.

## Authenticated emulator: LIVE evidence

Reused Android `emulator-5554` API 35 and installed development client
`com.adrivdbs.wombo`, with no native rebuild/reinstall. Metro 8085 manifest
provenance points to this Slice 4B worktree's mobile directory. Earlier 8083/8084
sessions were untouched. Computer-use native pipe remained unavailable after
retry; fresh Android native trees/observed controls, normal keyboard input,
taps, scrolling and Android Back supplied the authorized fallback. Read-only
CDP observed owner/component identity and network events, never app callbacks,
request interception, session injection or domain row modification.

ONE tagged disposable start23-dev Auth athlete was created, then prepared using
supported profile/onboarding, history, calibration observation, threshold
confirmation and zone approval APIs. Normal app sign-in was used. All hosted
operations used start23-dev and `r6-api-r6-staging.up.railway.app` only.

1. V2 Week no-plan -> availability with exact week `2026-10-12` and dates
   `2026-10-12/14/17` -> draft `ac1b8663-d73c-4d71-86e1-bd150a54d5fd`
   -> Choose RUN-013 and RUN-010 -> placement revision 3 -> automatic submit.
2. Pending plan `8940268c-0c1b-4887-a252-b762a074d189`, revision 1, proposal
   `6ec208d3-03fa-4224-b646-2538deea7716`, active revision null.
   Review displayed both assigned dates, measures and actual supplied warning.
   Back -> Week -> review and settled V1/V2 comparison kept identity/revision.
   Native snapshots prove one owner and one selected presentation. V1 mount
   performed its original two alternatives reads; opening V2's first editor
   performed one separate intentional GET, not duplicate V2 eager fetching.
3. Editor Back preserved pending review. Explicit Reject posted once to that
   proposal and followed GET `?revision=1`. V2 Week showed rejected, not active.
4. Existing V1 rejected-plan Prepare again action returned to V2 Week no-plan.
   Same athlete created draft `74dc9bb2-2f5f-4354-8fc8-a017a43f7090`, chose
   two occurrences and automatically submitted once. Server reused the plan ID
   with revision 2 and proposal `c93f6a40-6135-45ff-9884-5087439f614b`.
5. V2 review opened pending workout `dc731fec-2d13-434a-b1ea-8eef06b9e0a3`.
   Options GET used revision 2; the server returned eight alternatives and
   `can_remove=false`. No Remove control appeared. Explicit radio selection chose
   RUN-019, template `41a64759-4b5a-4f94-af34-aa947c46cafd` (60 min).
   Explicit Replace posted once, returning revision 3 and proposal
   `a592c465-0387-4aac-9294-a679803fb518`, still pending with no active revision.
   The source date remained Wednesday 14 October and warning remained visible.
6. Explicit Week goedkeuren posted once to the returned proposal. Existing base
   revision is 0; exact body behavior is covered by source/transaction tests.
   Follow-up GET had no revision query. V2 Week showed ACTIVE revision 3,
   applied proposal, replaced RUN-019 and 0 of 2 completed workouts.
7. Calendar and Activities read successfully; settled Activities content and
   Android Back returned to the unchanged active Week. Shared owners remained.
8. Normal Profile sign-out completed. Settled Auth has no session or Planning
   owner. Cleanup then globally revoked sessions and deleted only the owned user.

Sanitized native trace contains **2 creates, 4 transitions, 2 submits, 1 pending
edit, 1 explicit reject, 1 explicit approve**: 11 writes, all successful; zero
active-date PATCH. Approve/reject occurred only after their explicit buttons,
never submit/edit/Back/comparison. Native payload bodies were not available for
all requests; exact bodies are proved by focused tests and unchanged client
contracts. Supported authenticated public GETs saved returned proposal/options/
active snapshots. Two optional helper snapshot attempts failed (wrong path / no
longer pending); the helper retained the athlete and required native flow passed.
These diagnostic reads neither mutated state nor caused a replacement athlete.

**FIXTURE/TEST**, rather than forced staging data: `can_remove=true` with separate
confirmation/null edit; unknown capability; empty/error/retry; expired/superseded
snapshots; stale decisions/options; late-response/remount races; rapid duplicate
cross-control actions; repeated source templates; distinct active-plus-pending
schedule with both approval and rejection. Removal and coexistence are not
misreported as LIVE acceptance.

## Functional references, cleanup and integration

Ignored evidence: `mobile/.runtime/slice4b/` contains full/focused test JSON/logs,
TypeScript/unused logs, Metro provenance, sanitized network trace, public API
snapshots, native owner/state records, `source-parity.json`, `emulator-audit.json`
and ownership-guarded cleanup proof. Functional-reference PNGs with XML:

| Reference | Stem |
| --- | --- |
| Pending context and actual warning | `pending-review` |
| Proposed workout/date/measures | `proposal-workouts` |
| Alternatives/current workout | `alternatives-first` |
| Selection interaction | `selected-replacement` (immediate post-tap frame; subsequent native tree confirmed checked selection) |
| Final replace / false removal capability | `alternatives-final-action` |
| Returned pending replacement | `replaced-workout` |
| Explicit separated approve/reject controls | `proposal-decision-controls`, `approval-controls-updated` |
| Week after rejection | `week-rejected` |
| Week after approval | `week-after-approval` |
| Signed-out Auth | `signed-out` |

These are functional references for later user mockups, not final visual designs.
Source catalog replacement characters are shown exactly as supplied; they were
not repaired or reinterpreted in this presentation slice.

`slice4b-authenticated-cleanup.json` proves **created 1 / deleted 1**,
`sessions_revoked: true`, admin lookup **404** and **zero matching owned tagged
users**. Settled native sign-out proves no session or owner. No athlete was
accidentally destroyed or replaced. Auth helper and network observer exited.

After software, emulator, privacy and cleanup gates passed, local
`feat/wombo-ui-v2` was verified at the clean accepted 4A ancestor and fast-forwarded
locally to the report delivery commit using an expected-old ref update. No merge,
rebase, squash or push. The isolated delivery worktree is clean. Main remains
`fb56c51d983564c652d83fc15e02b039e9063d3f`. Original unrelated dirty
coach/Garmin/privacy/PDF work remains untouched. No production access/deployment.

Physical TalkBack/focus-return, physical-device/release gates and final visual
acceptance through user mockups remain open. No unresolved Slice 4B functional,
software, authenticated emulator or cleanup gate remains. Slice 4C active moves
remain outside this implementation.

WOMBO UI V2 SLICE 4B COMPLETE — FUNCTIONAL PROPOSAL REVIEW SCAFFOLD ACCEPTED
