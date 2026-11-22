# WOMBO end-to-end test matrix

Date: 26 October 2026. Source: `aff74558d0a6511286a4a84a44ea25a03ca57549`. This is a journey/invariant matrix with evidence levels, **not a claim that a real device completed every row**. Refer to [the main audit](WOMBO_FULL_SYSTEM_AUDIT.md) for full finding records and [evidence README](evidence/README.md) for commands.

Classification:

- **PROTECTED:** exercised at the specifically stated local boundary or directly supported by a narrow source invariant. Does not imply hosted/device sign-off.
- **PARTIALLY PROTECTED:** useful guards exist, but an integration/recovery edge remains or physical validation is absent.
- **UNPROTECTED:** a confirmed failure or missing safeguard at the stated boundary.
- **NOT VERIFIED:** not executed and insufficient evidence to claim protection.

Evidence levels: **B** = backend test, **M** = mobile component/controller test, **A** = added audit probe, **S** = source inspection, **L** = live read-only metadata, **G** = open runtime gate. All test data was synthetic. No production athlete or staging mutation was used.

## Setup, identity and readiness

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| SET-01 | Register -> confirmation email or authenticated session; no accidental training state | PARTIALLY PROTECTED | M AuthScreen tests; S handles absent signup session with email notice | Real email delivery/confirmation link, duplicate taps and interrupted signup; G |
| SET-02 | Correct/incorrect password login and backend identity | PARTIALLY PROTECTED | M auth screen and B signed JWT checks; Supabase is identity source | Two real synthetic Auth sessions through mobile/API; G |
| SET-03 | Forged, expired, service-role or malformed JWT cannot identify athlete | PROTECTED | B `test_authentication.py`; existing tests passed | Hosted issuer/key rotation/session settings not inferred |
| SET-04 | Client user_id/query/header cannot override verified identity | PROTECTED | B identity override test; backend ignores authoritative client identity | PostgreSQL RLS still requires independent check |
| SET-05 | Profile/onboarding required fields and unsupported goals fail closed | PROTECTED | B onboarding eligibility/version/schema tests | No new physiological age/HR thresholds invented |
| SET-06 | Missing resting HR or DOB cannot claim completed profile | PROTECTED | B/S `satisfied_onboarding_steps`; M Onboarding resume coverage | Resolve draft policy copy that calls resting HR optional |
| SET-07 | Zero previous-month sport hours remain distinct from missing input | PROTECTED | B baseline and eligibility tests; A engine matrix | All-zero triathlon may fail catalog capacity, a separate product boundary |
| SET-08 | Current timezone/monitor confirmation and current onboarding version required | PROTECTED | B eligibility/upgrade/version tests; M resume | Device-locale detection and interrupted confirmation on native; G |
| SET-09 | App closes after saved onboarding step and resumes server-selected step | PARTIALLY PROTECTED | M `OnboardingScreen.resume.test.tsx`; server session/revision persisted | Kill/relaunch at each write with real Auth; G |
| SET-10 | Calibration interruption/poor quality/missing block evidence cannot create active zones | PROTECTED | B domain/protocol fixture tests; pending threshold/zone lifecycle | Real device measurement entry and two-user persistence; G |
| SET-11 | Threshold confirmation and zone activation remain distinct explicit decisions | PROTECTED | B calibration/onboarding tests and typed proposals | Real-token cross-owner confirmation and duplicate/native taps; G |
| SET-12 | Missing calibration blocks training readiness rather than manufacturing a threshold | PROTECTED | B current-version onboarding and calibration readiness; S active-zone check | Complete standalone calibration -> onset of training on fresh device; G |
| SET-13 | Offline startup retains valid secure credential for later retry | UNPROTECTED | A AUD-009 deletes refresh token for AuthRetryableFetchError | WOMBO-011 |
| SET-14 | Foreground/background/token rotation retains correct account owner | PARTIALLY PROTECTED | M owner/token-rotation tests; S AppState refresh start/stop | Real background expiry/rotation and secure-write failure; G |
| SET-15 | Logout stops local UI state; old activity responses cannot populate another athlete | PROTECTED | M Activity owner identity/unmount tests | All-device/access-JWT revocation is a separate product/configuration question |
| SET-16 | A/B/A login preserves each account's plan locator and late A work is isolated | UNPROTECTED | A AUD-002/003: global locator removed/overwritten | WOMBO-009; no cross-account data disclosure demonstrated |
| SET-17 | Clear optional profile name and refetch | UNPROTECTED | S form/client omit blank name; API accepts null | WOMBO-018 |
| SET-18 | Forgot password / account deletion / retention request | NOT VERIFIED | No complete integrated operation or operational channel found | WOMBO-014 plus owner support/privacy decisions |

## First planning cycle and approval

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| PLN-01 | Availability or explicit previous-week reuse, never implicit reuse | PROTECTED | B schemas and planning tests; M controller exact payload tests | Hosted calendar/date-only parity; G |
| PLN-02 | No valid training days -> explicit fail-closed result | PROTECTED | A full-catalog no-days case: `availability_required`; B rest-only case coverage | All-blocked rest-only path still requires approval |
| PLN-03 | Eligibility obeys phases, zones, injuries and catalog provenance | PROTECTED | B domain/catalog/source fixture suites passed | Hosted catalog ledger/random successor identity not verified |
| PLN-04 | 0/0/0 history -> no invented nonzero per-sport allocation | PARTIALLY PROTECTED | A run-zero generates; tri-zero fails closed after 19.46 s | Explicit beta scope/catalog decision; WOMBO-007 performance |
| PLN-05 | One trained sport, other required sports zero -> safe result | PROTECTED | A matrix: `zero_history_discipline_baseline_unavailable`; explicit accepted rule | Product messaging/coverage decision, not a scientific defect assertion |
| PLN-06 | Accept/pass bind current draft revision, template AND occurrence | PROTECTED | B swipe/API tests; M exact occurrence payload tests | Actual simultaneous two-device PostgreSQL transitions; G |
| PLN-07 | Choose/pass/undo/reset cannot issue duplicate same-tick mutations | PROTECTED | M shared synchronous-lock tests for each action | Native repeated gesture pressure test; G |
| PLN-08 | Same template can appear twice; same date can hold several occurrences | PROTECTED | B occurrence/repeat tests; M repeated-template and placement tests | Persisted duplicate-template IDs against current hosted migration; G |
| PLN-09 | Incomplete choices/layout cannot submit | PROTECTED | B/M incomplete selection/placement tests | Real invalid API requests using disposable accounts; G |
| PLN-10 | Automatic/manual submit creates pending proposal, never accidental approval | PROTECTED | B/M submit tests assert separate approval and exact IDs | Native process kill after submit and hosted replay; G |
| PLN-11 | Same-tick double submit/approve/reject binds one reviewed state | PROTECTED | M shared lock/stale snapshot tests; B idempotent decisions | PostgreSQL concurrent transaction race; G |
| PLN-12 | Response lost after submit -> same pending proposal on explicit retry | PARTIALLY PROTECTED | B idempotent plan persistence; S draft submitted identity/read recovery | Full RPC sequence failure at every boundary not executed |
| PLN-13 | Proposal stale before approval -> 409, no newer proposal auto-approved | PROTECTED | B stale-base and owner tests; M retained reviewed snapshot/no silent retry | Real two-device concurrent update; G |
| PLN-14 | Token expires during approval | PARTIALLY PROTECTED | B expired JWT rejection; M locks/failure state; S no automatic auth-401 retry | Native refresh/retry against Supabase with exact proposal; G |
| PLN-15 | Approval commits, follow-up GET fails -> explicit idempotent retry recovers | PROTECTED | A AUD-006 control plus B repeated approval returns same result | Same-proposal retry must not be mocked as forbidden after successful apply |
| PLN-16 | Offline/503 resume does not erase existing plan/draft | UNPROTECTED | A AUD-001 deletes the only saved locator | WOMBO-008 |
| PLN-17 | Reinstall/second device discovers current plan without local ID | UNPROTECTED | S current owner restores only local IDs; existing test explicitly asserts no plan discovery | Product/API discovery remedy in WOMBO-008/009 |
| PLN-18 | Normal full-catalog triathlon calculation does not block other API requests | UNPROTECTED | A 15.84/19.46 s synchronous domain work; S single async process | WOMBO-007; actual HTTP concurrency/load remains G |

## Active Week, Calendar and workout details

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| ACT-01 | Pending proposal never replaces active workouts on Week | PARTIALLY PROTECTED | B/M active/pending ownership tests; canonical two assertions currently date-fail | WOMBO-016; fixed-date 12/12 diagnostic supports intended behavior, not full suite green |
| ACT-02 | Rapid Week/Month switches cannot publish obsolete Calendar results | PROTECTED | M latest request success/failure/finally tests passed | Real render/frame/gesture behavior; G |
| ACT-03 | Detail opens exact occurrence with ordered source segments/targets | PROTECTED | M WorkoutDetail, boundary and repeated-workout tests | Native long-text/scroll/keyboard/accessibility; G |
| ACT-04 | Move stays within local plan week and sends expected active revision | PROTECTED | B/M invalid/outside-week and exact-revision tests | Two-device transaction check; G |
| ACT-05 | Complete layout is validated before the exact move | PROTECTED | B/M complete-layout and authoritative move tests | Neighboring week is not included; ACT-10 |
| ACT-06 | Cancel/back on move warning sends no PATCH and consumes intent | PROTECTED | M warning cancellation/old-confirm callback tests | Physical Android/iOS back/gesture; G |
| ACT-07 | Server 409/422/network failure keeps authoritative schedule unchanged | PROTECTED | B/M rejected/stale move tests; no optimistic plan mutation | Hung requests still unbounded (012) |
| ACT-08 | Successful move replaces returned IDs/revision in Week/Calendar/detail | PROTECTED | M authoritative update and renewed workout-ID tests | Supporting-task mutations need shared invalidation (005/010) |
| ACT-09 | Completed/cancelled/historical/foreign occurrence cannot be moved via current UI | PROTECTED | M negative entry/controller tests; B service checks | Direct PostgreSQL/API negative tests on current schema; G |
| ACT-10 | Sunday/Monday high workouts obey the same hard spacing rule | UNPROTECTED | A three sports: combined validator rejects but current-week layout service accepts | WOMBO-003 |
| ACT-11 | Athlete timezone differs from device -> Week/Calendar share Today | UNPROTECTED | S explicit plan-timezone versus device-date paths | WOMBO-020; physical timezone switch still G |
| ACT-12 | App remains open across local midnight/foreground and date context updates | NOT VERIFIED | No dedicated day-rollover/foreground date refresh test | Add date-clock lifecycle test and physical gate |

## Activity, feedback and execution history

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| RPE-01 | User taps activity Save twice -> one create identity | PROTECTED | M rapid same-tick create tests and B idempotent create | Real delayed POST/disconnect against synthetic database; G |
| RPE-02 | Ambiguous POST retry in same owner lifetime reuses key/payload | PROTECTED | M timeout retry and retained logical attempt tests | Editing payload after unknown commit and process death need integrated testing |
| RPE-03 | POST succeeds but refresh fails -> retry reads, not another POST | PROTECTED | M explicit existing regression test | Native crash timing not established |
| RPE-04 | Pending feedback survives navigation and blocks another local create | PROTECTED | M owner/feedback identity/pending-block tests | A/B device inserts can break cached context (RPE-10) |
| RPE-05 | RPE saves on choice; rapid repeated choice submits once | PROTECTED | M exact feedback/per-activity lock tests; B initial/correction contracts | Physical touch/accessibility input test; G |
| RPE-06 | Missing HR with assigned HR observation requirement -> truthful rejection | PROTECTED | B activity service checks; M invalid-HR preservation | Actual user-friendly field error and session integration; G |
| RPE-07 | Missing measurement load/distance-only swim is not fabricated | PROTECTED | B zone-load and activity cases; M null swim duration path | U-001 aggregate completeness across several activities |
| RPE-08 | Retryable RPE PUT failure checks exact stored activity before retry | PROTECTED | M client helper and activity controller tests | Successful-but-unreadable response excluded by current helper (RPE-09) |
| RPE-09 | HTTP 200 truncated JSON after committed RPE -> reconcile state | UNPROTECTED | A AUD-011 emits raw SyntaxError, performs no authoritative GET | WOMBO-013 |
| RPE-10 | New pending activity from another device is immediately completable | UNPROTECTED | A AUD-004 shows banner row then history lookup failure | WOMBO-010 |
| RPE-11 | New approved plan/new activity appears when reentering Activities | UNPROTECTED | A AUD-005 permanent historyLoaded gate suppresses read | WOMBO-010 |
| RPE-12 | Planned versus extra activity preserves exact matching identity | PROTECTED | B/M planned/external/unplanned payload and matching tests | Real-token cross-owner match and concurrent match constraint; G |
| RPE-13 | RPE correction obeys expected current value, local-week window and original model provenance | PROTECTED | B activity correction and private snapshot tests | PostgreSQL race with two correction requests; G |
| RPE-14 | Process dies while POST is still committing; later app creates same workout | NOT VERIFIED | Key is memory-only; pending server reminder handles many but not all ordering cases | Fault-injected process-death test with disposable account; G |
| RPE-15 | 1,001 history rows incl. pending RPE remain reachable | NOT VERIFIED | U-002: unpaginated RPC/client, local Data API row cap | Isolated SQL/Data API pagination test required |

## Several consecutive weeks and injury lifecycle

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| WK-01 | Activity-only calibration history is not a prior approved plan | PROTECTED | B provenance/domain/repository cases passed; v15 adds explicit approval flag | Fresh v15 pgTAP/ledger verification; G |
| WK-02 | Multiple approved historical revisions use authoritative approved snapshot without reinterpretation | PARTIALLY PROTECTED | S active_revision joins and version filters; B history/progression tests | Current PostgreSQL mixed/superseded revision fixture; G |
| WK-03 | Four build weeks then recovery/Z5 follow explicit policy | PROTECTED | B synthetic four-week build, injury caps and recovery tests | Persisted month-long real-API journey not executed |
| WK-04 | Missed/illness/fatigue weeks and missing actual data are distinct | PARTIALLY PROTECTED | B explicit zero, sickness exclusion, hold, debt/progression tests | U-001 mixed measurement completeness and actual check-in history query |
| WK-05 | New/resumed check-in preserves restriction and professional advice | UNPROTECTED | A AUD-007 saved blocked run displays/sends unrestricted | WOMBO-004 |
| WK-06 | A due seven-day injury review does not automatically clear it | PARTIALLY PROTECTED | B pure restriction object and S SQL review model retain restriction | Mobile defaults/hydration violate review intent; WOMBO-004 |
| WK-07 | Injury introduced mid-program -> safe pending restriction/redistribution under caps | PARTIALLY PROTECTED | B injury/selection/cap tests passed | Persisted check-in -> shared Week state and cross-week schedule missing |
| WK-08 | Injury removed later -> explicit attributable change and appropriate future plan | PARTIALLY PROTECTED | S typed choices/confirmation, B pure restriction mapping | Device journey plus approved reintroduction/multi-sport contract; no new formula assumed |
| WK-09 | Check-in next-week proposal/approval updates shared Week/Calendar | UNPROTECTED | A AUD-008 leaves old plan and locator | WOMBO-005 |
| WK-10 | Response lost after completed check-in attachment -> same proposal on retry/restart | UNPROTECTED | S latest context RPC accepts only open; mobile completed context loses local proposal | WOMBO-006; SQL/API fault injection still needed |
| WK-11 | Monday race taper and unavailable taper baseline fail as specified | PROTECTED | B exact Monday taper/absence tests | Full catalog/staged fixture on final candidate; G |
| WK-12 | Non-Monday race week always generates a complete taper | UNPROTECTED | Intentional fail-closed `partial_week_taper_rule_required` | Product/scientific scope decision, **not a technical formula bug** |

## Network, platform, security and release gates

| ID | Scenario / expected invariant | Status | Evidence and actual result | Remaining verification / finding |
| --- | --- | --- | --- | --- |
| REL-01 | Server returns 409/422/503 -> stable safe envelope without submitted secrets | PROTECTED | B public error/contract tests; S explicit DTOs/repository translation | Real deployed error corpus/logging without athlete data; G |
| REL-02 | Backend never responds -> app exits busy state within an application deadline | UNPROTECTED | A AUD-010 remains unsettled after five minutes | WOMBO-012 |
| REL-03 | Logout while request in flight isolates all new account state | PARTIALLY PROTECTED | M Activity guards; A planning storage write escapes old owner | WOMBO-009 |
| REL-04 | Athlete A cannot read/update B through hosted API/Data API/Storage | NOT VERIFIED | Existing synthetic memory/SQL suites present; current database runtime unavailable | Fresh two-token negative tests, no real-athlete access |
| REL-05 | Private load cannot appear in nested DTO/error/mobile accessibility output | PARTIALLY PROTECTED | B schema/response and M source privacy tests passed | Compiled bundle, dynamic exceptions/logging/analytics not fully verified |
| REL-06 | Production only starts with correct active-review/configuration gates | UNPROTECTED | L production-designated /ready reports local; A Phase-13-only review accepts new planner | WOMBO-001/002 |
| REL-07 | /ready proves required schema and exact new deployment | UNPROTECTED | A dependency-free readiness; S release script only checks ready | WOMBO-019 |
| REL-08 | Current main mobile binary talks correctly to deployed backend | NOT VERIFIED | L API operations match; production Decimal schema patterns differ; no protected workflow executed | Exact Railway SHA/schema + new AAB + synthetic end-to-end test |
| REL-09 | UI V2 glyphs/SVG/gestures/keyboard work on fresh native build | NOT VERIFIED | Source dependency present; latest inspected EAS build predates additions | Android release + physical Android/iPhone validation; no visual redesign required |
| REL-10 | GitHub/Railway auto-deploy does not promote unapproved feature/main changes | NOT VERIFIED | Authenticated Railway metadata request rejected expired grant | Read branch/root/CI-wait settings and deployment history; no deploy |
| REL-11 | Mobile-only regression is caught by CI | UNPROTECTED | S only backend/database workflows | WOMBO-015 |
| REL-12 | Test suite stays valid after fixture dates pass | UNPROTECTED | M canonical 611/2; isolated 10/2; frozen diagnostic 12/0 | WOMBO-016 |
| REL-13 | Current dependencies have reviewed security status | PARTIALLY PROTECTED | L npm advisory result 21 affected package entries | WOMBO-017 reachability/compatible update/native rebuild |
| REL-14 | Polar/Storage retry, revocation and deletion work against actual test provider | NOT VERIFIED | B mocked tests pass; no provider/session/file writes performed | Separate staging permission and optional-provider release approvals |
| REL-15 | Failed rollout can recover without rewriting historical data | NOT VERIFIED | S forward migrations and historical provenance retained | Rehearse exact prior app/image rollback against migrated isolated DB; backups/restore and incident owner |

## Authoritative contracts to use in follow-up verification

The snapshots `evidence/local-openapi.json`, `production-openapi.json` and `staging-openapi.json` are public schema only, not athlete responses.

- Create/select: `POST /api/v1/weekly-plans/swipe-drafts`; `POST .../{draft_id}/transitions` with `expected_revision`, action, candidate template and occurrence IDs.
- Place: `PUT .../{draft_id}/placements/{occurrence_id}` with expected revision/date; submit: `POST .../{draft_id}/submit` with revision and placement mode.
- Read: `GET /api/v1/weekly-plans/{plan_id}` with optional revision; validate: `POST .../{plan_id}/validate` with **all** occurrence workout IDs/dates for the selected revision.
- Move: `PATCH /api/v1/planned-workouts/{workout_id}` with expected active revision and scheduled date. No unconditional last-write-wins path is authorized.
- Approve/reject: `POST /api/v1/change-proposals/{proposal_id}/approve|reject`; approve binds expected base plan revision (or the separately typed zone precondition).
- Activity: `POST /api/v1/activities` with stable UUID `Idempotency-Key`; RPE: `PUT /api/v1/activities/{activity_id}/rpe` with canonical integer choice, optional measured HR and expected current RPE for a correction.
- Check-in: `POST /api/v1/checkins`; `PUT /{checkin_id}/context` with expected context revision; `POST /{checkin_id}/context-confirmation` with exact fingerprint/revision; `POST /{checkin_id}/plan-proposals` remains pending until separate approval.

Do not run the hosted mutation rows against real athletes. The minimum authorized follow-up environment is a synthetic isolated local database, or an explicitly approved disposable staging account/project with a cleanup and retention plan. No elapsed time or implicit request authorizes a staging mutation.
