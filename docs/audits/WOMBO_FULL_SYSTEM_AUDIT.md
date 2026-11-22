# WOMBO full system audit

## Executive summary — 26 October 2026

**Decision: do not declare the integrated application ready for unrestricted real-user beta yet.** The source review and safe local verification are complete enough to prioritize remediation, but database, exact deployed-revision and physical-device verification gates remain open. This is a technical audit, not scientific approval or a legal-compliance opinion.

The audited source is **`aff74558d0a6511286a4a84a44ea25a03ca57549`**, verified against GitHub `main` with a read-only `git ls-remote`. Local `main` and `integration/wombo-ui-v2-main` match it. Work is isolated on **`audit/wombo-full-system-review`** in `.worktrees/audit-wombo-full-system-review`. The original dirty worktree and UI V2 implementation worktrees were preserved.

**Findings: 0 P0 demonstrated, 7 P1, 12 P2 and 1 P3 confirmed findings.** No cross-athlete breach, leaked privileged key, unauthorized plan approval or physiological-formula corruption was demonstrated. Absence of a demonstration is not proof of safety. The highest-risk defects are missing spacing context across weeks, lost restriction answers on resumed check-in, disconnected check-in/Week state ownership, non-replayable completed check-in generation, and synchronous full-catalog planning that blocks the server event loop. The production-designated public URL returns `environment: local`; the production review gate also covers the older load policy without separately binding the active planning policy.

**End-to-end status:** setup, first-plan occurrence identity, within-week moves, explicit approvals and the basic activity/RPE loop have useful unit/component coverage. Multi-week operation, offline recovery and cross-device refresh have confirmed gaps. Taper for non-Monday races intentionally fails closed pending an approved rule; it must not be advertised as a complete race lifecycle. Existing styling/visual acceptance does not establish these behaviors.

**Security posture:** verified token-derived identity, opaque athlete mapping, owner-scoped database functions, private load tables, secure mobile refresh-token storage and explicit public DTO projections are strong foundations. Current hosted RLS/grants, Storage ownership, session revocation, deletion/retention operations and processor configuration were not independently exercised. There is no integrated end-to-end account-deletion/retention operation. No conclusion of GDPR compliance is made.

**Verification:** 778/778 backend tests passed; Ruff, formatting, strict mypy, strict TypeScript and unused-code compilation passed. The canonical mobile run has **611 passing / 2 failing tests across 68 suites**. Both failures are wall-clock dependent, reproduce alone, and pass in an audit-only fixed-date diagnostic; existing tests were not weakened. Eleven additional mobile audit probes and five backend probes pass; ten mobile probes and all five backend probes characterize gaps, while one mobile probe is a protected approval-retry control. Seven synthetic full-catalog scenarios were measured. The live npm advisory check reports 21 affected package entries, including 1 critical and 9 high labels; application exploitability was not established.

**Release confidence:** public production and staging API path shapes match local source; staging schemas match exactly and production differs in Decimal schema patterns. This does not prove a source SHA or correct persistence. Railway authentication is expired. The newest of three inspected EAS Android builds is finished build 22 at `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`, predating the audited UI V2/native SVG additions. No production modification, hosted migration, athlete-data request, push, merge, deployment or new build was performed.

**Top 10 next actions**

1. Resolve the production runtime environment and record its exact source/configuration/schema identity (WOMBO-001/019).
2. Bind external review evidence to both active load and planning versions (002).
3. Enforce unchanged spacing rules across adjacent approved weeks, with concurrency protection (003).
4. Preserve and explicitly review saved/active restrictions on check-in resume (004).
5. Connect check-in proposal creation/approval to the shared Week/Calendar owner and persistence (005).
6. Make committed check-in generation replayable and reviewable after response loss/restart (006).
7. Profile, bound and isolate synchronous full-catalog work; measure concurrent health latency (007).
8. Fix account-scoped, non-destructive resume and activity invalidation (008–010).
9. Fix transient auth/transport recovery and add mobile CI with explicit test clocks (011–013, 015–016).
10. Close dependency, deletion/privacy, database and freshly rebuilt device/release gates (014, 017 and the gate ledger).

## Scope, isolation and evidence standard

This audit changes documentation and audit-only synthetic probes. No implementation, formula, coefficient, planner policy, database schema or real-user data was changed. Git worktree/branch creation is the only repository-metadata mutation. The mobile dependency directory is a local junction to the existing integration dependencies; all configured Jest caches are inside the audit worktree. No install/update was performed against the shared dependency directory. This is not a clean-room `npm ci`/Docker release build.

Root and mobile `AGENTS.md`, the current MVP roadmap, current Joren decision/addendum and implementation record, architecture/API/security documents, source, migration definitions and current tests were consulted. Latest accepted decisions take precedence over historical roadmap status summaries. Some architecture and phase status prose still describes old deployment/schema states. Historical reports are context, not fresh test results. Original-worktree untracked privacy/UI material was consulted only as supplementary draft context, not treated as integrated or published commitments.

Evidence levels used below:

- **Runtime/local probe:** code exercised with synthetic inputs and mocks at the stated boundary.
- **Source confirmed:** a direct control-flow/configuration/predicate contradiction; runtime persistence may still require pgTAP verification.
- **Live metadata:** unauthenticated public health/OpenAPI GETs, remote Git HEAD and bounded EAS build metadata. No athlete records requested.
- **REQUIRES VERIFICATION:** observed risk without enough evidence of a violated product invariant; listed separately, not counted as a confirmed bug.

## System and release identity

| Surface | Verified fact | Limit |
| --- | --- | --- |
| GitHub main | `git ls-remote origin refs/heads/main` -> `aff74558d0a6511286a4a84a44ea25a03ca57549` | Point-in-time remote HEAD; no fetch/push |
| Integrated local source | `main` and `integration/wombo-ui-v2-main` point to that SHA; integration worktree initially clean | Original current branch is `fix/pre-ui-beta-blockers` at `6bb3a04` with unrelated changes; it was not the audit baseline |
| Audit workspace | `.worktrees/audit-wombo-full-system-review`, branch `audit/wombo-full-system-review` | Audit artifacts remain here; no merge into main |
| Production-designated URL | `https://start23-production.up.railway.app/ready`: HTTP 200, ready, version 0.1.0, **environment local** | URL designation comes from existing local production-mode state; actual operator intent/usage and Railway SHA unknown |
| Staging URL | `https://r6-api-r6-staging.up.railway.app/ready`: HTTP 200, ready, version 0.1.0, environment staging | No dependency or athlete workflow proof |
| Public contracts | Both deployments expose the same 69 paths/operation descriptions as local. Staging components identical. Production differs in Decimal `pattern` schema metadata | Cannot establish identical implementation, installed dependencies or database migration ledger |
| Railway | Existing cached CLI status request fails: saved grant invalid/Unauthorized | Auto-deploy source branch, latest deployment ID/SHA, variables, rollback revision, project isolation and schedules not verified. No login/redeploy attempted |
| EAS latest inspected build | Android STORE `wombo`, versionCode 22, FINISHED, source `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`, SDK 57; build ID `0b1a3606-7476-4607-b4c7-a37e763249c0` | Only latest three build records read; no Play-track/installed binary/configuration verification |
| Native dependency delta | Audited source adds `react-native-svg` 15.15.4 and `lucide-react-native` 1.48.0 after build 22 source | A new native build, not merely Metro/source changes, must be validated |
| Local public environment | Original mobile `.env` selects r6-staging, while original runtime task state selects production | Local configuration only; not EAS production-variable evidence |
| Database | 47 forward migration files and 27 pgTAP suite files tracked, latest migration `20261004212750_first_plan_approved_provenance.sql` | No hosted migration execution/ledger query or current pgTAP execution |

Python HTTPS probes failed certificate-chain validation in this environment. Windows curl succeeded with certificate verification enabled. The Python error is **not** reported as a production TLS outage. Both observations are retained.

## Architecture, ownership and critical boundaries

The system is an Expo/React Native TypeScript client, a single FastAPI Python modular monolith, hosted Supabase Auth/Data API/PostgreSQL/Storage, and a Railway backend. No Redis, Celery, microservices or LLM authority were found in the core path.

| Subsystem and source | Responsibility / dependencies | Data owner and transitions | Failure/security boundary and tests |
| --- | --- | --- | --- |
| Expo Router `mobile/app/_layout.tsx`, `(authenticated)/_layout.tsx`, `(training)/_layout.tsx`, `src/navigation/TrainingLayout.tsx` | Auth shell, supporting-task stack, V1 stack/V2 tabs; shared providers | Authenticated identity keys ActivityOwner/TrainingFlowHost. Route changes are presentation; `TrainingFlowHost` retains planning after readiness | Redirect when unauthenticated, explicit readiness failure UI. RootLayout/AuthenticatedLayout/TrainingNavigation tests; native navigator lifecycle still a device gate |
| UI gating `src/ui/uiVersion.ts`, `UiVersionProvider.tsx`, `PlanningPresentationProvider.tsx` | V1 default and explicit V2 for implemented slices; source/env selection is presentation-only and allowed in release | Version controls do not own domain plan/activity state; detail/task navigation locks shared | Boundary tests exercise actual screens; V2 switch is not a backend capability gate or authorization mechanism |
| Planning owner `src/features/planning/PlanningFlowProvider.tsx`, `usePlanningController.ts`, `planningResume.ts` | Current plan/draft, mutation lock, active versus pending snapshots, storage locators | Backend owns plan/revision truth. Mobile restores exact IDs, uses returned authoritative plans; pending rows cannot replace active rows | Same-tick locks and stale references protect many operations. Transient locator deletion and account storage defects: 008/009 |
| Calendar owner `src/features/calendar/useCalendarController.ts`, `useCalendarNavigation.ts` | Date-range reads, request sequence, cached approved calendar, local selection | Backend calendar is authoritative; latest request wins; successful approved revision replaces full week and invalidates range | Rapid-range tests pass; remote/task mutations do not universally invalidate cached state; device-versus-athlete Today split: 020 |
| Activity owner `src/features/activities/ActivityFlowProvider.tsx`, `useActivityController.ts` | Shared history, pending feedback, one logical create key, per-activity RPE lock | Server activity row and UUID are authority; POST creates awaiting_rpe, PUT processes/corrects with preconditions | Navigation preserves form/RPE in one identity lifetime. Cross-device reminder/history mismatch and permanent cache: 010; no request deadline: 012 |
| Auth `src/auth/AuthProvider.tsx`, `src/lib/supabase.ts` | Supabase password auth, memory access token, SecureStore refresh token, foreground refresh | Supabase Auth owns identity/session. Backend resolves Auth UUID to opaque athlete UUID, client identity never authorizes writes | Invalid server JWT rejected; offline bootstrap wipes stored credential (011). Logout uses local scope, not all-device revocation. Auth-screen tests do not replace session lifecycle tests |
| API `backend/app/api`, `core/security.py`, `core/errors.py`, `mobile/src/api/client.ts` | Typed Pydantic DTOs, fixed error envelope, JWT signature/issuer/audience/role/time checks; transport helpers | Verified token -> Auth subject -> opaque athlete mapping; authenticated caller forwarded on owner Data API paths | Synthetic signed-token and ownership tests pass. Mobile response JSON is a cast, not runtime validation (013); request IDs are generated server-side but discarded by mobile error type |
| Identity/onboarding `backend/app/modules/{identity,onboarding}`, mobile Onboarding/Profile/Goal screens | Separate identifying, physiology and operational profile records; previous-month history, structured race goal, zone readiness | Session completion/version and input snapshot are server-owned. DOB/resting HR, HR-monitor confirmation, timezone, all three history entries and required active zones gate readiness | Resume and upgrade tests cover selected cases. No unsupported goal family activation. Optional names cannot be cleared in mobile (018) |
| Calibration `backend/app/modules/calibration`, mobile Calibration/ZoneProfile screens | Reviewed protocol definitions, observations, deterministic evaluations, threshold decision, separate zone activation | Immutable observation/evaluation provenance; threshold acceptance and zone approval are distinct; pending values cannot drive active zones | Missing/interrupted/poor/unstable evidence fails closed. Domain, protocol fixture, service/repository/public-contract tests pass; actual two-token/Storage/device flow remains open |
| Planning backend `backend/app/modules/planning/{schemas,service,domain,swipe,repository}.py` | Snapshot eligibility, finite multiset selection, distinct occurrence IDs, placement, pending revisions, approval/moves | Immutable template != swipe occurrence != planned-workout UUID; expected draft/base revisions plus context fingerprints; DB transactions own atomic activation | Within-week constraints and retries well covered. Neighboring-week context missing (003), synchronous search (007), check-in handoff/replay defects (005/006) |
| Physiology `backend/app/modules/physiology` | Pure deterministic Decimal calculations, rule precedence, rounding, approved historical/current versions | Python owns decisions; history retains version. No FastAPI/DB/LLM imports in pure domain | Purity, equality, missing/zero, DST, injury caps, recovery/taper and catalog tests pass; this is contract integrity, not scientific endorsement |
| Catalog `backend/app/modules/workouts`, `docs/trainings`, source/v2 migrations | Reviewed versioned source templates and private load provenance; latest immutable version selection | Source workout IDs/template keys retained; immutable V2 successors alter eligibility, not old records. Distance-only source swims cannot acquire invented load | Source/seed/version parity tests pass. Synthetic multi-sport full-catalog timing exposes a hotspot. Actual hosted random IDs/candidate order not verified |
| Activity/RPE backend `modules/activities` | Idempotent canonical create, matching, HR observation, private measurement processing, stale-safe RPE correction/proposals | Private activity load separated from public DTO. Completion-time measurement method/profile snapshots retained; corrections preserve original provenance | Local owner/duplicate/stale/missing-measurement tests pass. No silent automatic zone activation; mixed-availability weekly aggregate risk U-001 needs a decision/test |
| Weekly check-in `modules/checkins`, `CheckInScreen.tsx` | Structured answers, explicit fingerprint confirmation, restrictions/external activities, next-plan proposal | DB confirms context and persists attributable restriction review; generated plan remains pending until approval | Mobile has a parallel local proposal owner and incomplete hydration; completed RPC context is not replayable (004–006). Service proposal creation and attach are separate HTTP/DB operations |
| PostgreSQL/RLS `supabase/migrations`, `supabase/tests` | Owner isolation, opaque/legacy identity cutover, grants, critical-write triggers, atomic RPCs, append-only historical provenance | Database owns approval/decision transactions. User tokens for owner RPCs; restricted secret-key repositories for private load/provider operations | Service role bypasses RLS by design, so every service RPC needs explicit owner scope and grants. Static inspection and memory tests are not a fresh PostgreSQL proof |
| Polar/Storage `modules/integrations`, `jobs/retry_polar_imports.py` | State-bound OAuth, HMAC/replay checks, bounded import retries, canonical activity mapping, private FIT upload | Provider token server-only; `activity-files` objects use athlete/activity/provider paths. Disconnect revokes provider before local token removal | Local provider/webhook/owner tests pass. Raw file size checked after buffering, background webhook durability and retention/deletion remain operational risks/gates |
| LLM `modules/coach/{context,weekly_plan}.py` | Strict context extraction and qualitative explanation; deterministic fallback, bounded output/timeout, `store:false`, no mutation tools | Candidate is inactive until structured confirmation. The model does not calculate/approve zones, plans or private load | Schema/injection/forbidden-language/fallback tests pass. Provider enablement, DPA, actual logs and retention are not independently verified |
| Pioneer `modules/pioneer`, Phase 16 migration | Owner-scoped redemption, code digest, DB rate limits/idempotency | Service-only redemption transaction; public response limited to program/status/time | Local tests and SQL assertions present. A Pioneer UI/code is not a general backend authorization gate or proof of closed beta membership |
| Railway/EAS `backend/{Dockerfile,railway.toml}`, `mobile/{app.json,eas.json}`, `scripts/*` | Single process health checks and deployment/build tooling | Deployment settings and EAS env are external authority; database and build artifacts must be matched to source | Production local mode, nonfunctional readiness, source/binary uncertainty and no mobile CI block confidence. Release scripts were inspected, never executed |

## Lifecycle and deterministic-engine conclusions

**Setup.** Auth registration/login is implemented. Email confirmation without immediate session is handled. Password reset/account recovery, account deletion and a published privacy/health-data process are not a complete in-app lifecycle. Current server onboarding requires DOB and resting HR, HR-monitor confirmation, confirmed IANA timezone, current-version per-sport previous-month minutes, a structured race goal with required distances/target time, and active required discipline zones. Names and focus/optional metric fields do not authorize physiology. Missing data and legacy onboarding versions fail closed rather than silently upgrading history. Several draft privacy statements describe resting HR as optional while current readiness requires it; resolve the disclosure/requirement with the product owner instead of silently changing physiology inputs.

**First plan.** `POST /api/v1/weekly-plans/swipe-drafts` returns an owner draft with revision, fixed count/composition and distinct candidate occurrence ID. Transitions bind `expected_revision`, action, template and occurrence. Manual placement uses `/placements/{occurrence_id}`, not a repeated template key. Complete selection plus `/submit` creates a pending plan/proposal. Approval is a separate authenticated endpoint. Existing tests exercise accept/pass/undo/reset, multiple same-date/repeated workouts, stale drafts and duplicate requests. A failed resume read can still lose the only mobile locator. All-zero triathlon fails closed with current catalog/target constraints; that supported-input/product boundary needs an explicit beta scope, not an invented target.

**Active week.** The server validates the complete selected revision and same-week moves. Client warning cancellation does not mutate the plan; successful moves use the authoritative returned revision. Approvals/rejections are idempotent at the existing backend contract. An audit control verifies approval followed by a failed read can recover on an idempotent explicit retry. A fabricated mock that returned 409 after a successfully committed same-proposal approval was rejected as invalid evidence. Cross-week spacing is nevertheless absent from context; same-week correctness does not establish multi-week correctness.

**Activities.** Canonical create uses `Idempotency-Key`. The owner retains a logical create key/created ID across refresh failures in the same session. RPE is saved on choice, a per-activity synchronous lock blocks same-tick duplication, and retryable errors fetch the exact row before another PUT. Canonical activities without HR can preserve unavailable load; assigned RPE-guided workouts can require HR and safely reject completion without it. Missing swim duration is not synthesized. Public history stays load-free. Cached history/reminder entities and invalid success JSON expose real recovery gaps (010/013). A create key is not durably stored across process death; server pending-feedback recovery protects many restart cases, while delayed commits/process-death races still need real integration testing.

**Consecutive weeks.** Server history differentiates approved plan provenance from activity-only calendar rows; latest approved revision snapshots, sick-week exclusion, realized progression, recovery/taper and versioned load are explicit. Existing four-build-week tests are deterministic synthetic domain tests, not an executed persisted month-long journey. Check-in generates/attaches a pending next week, but mobile handoff and completed-call retry are broken. Starting/reopening check-in must not default an unreviewed active restriction to free. Lifting a restriction later and asymmetric multi-sport targets require clear accepted rules, not new coefficients invented by this audit.

**Formula implementation integrity.** No replacement formula is proposed. Reviewed fixtures exercise Decimal arithmetic, one-final-total HALF_UP rounding, all calibration anchors, integer boundary ownership, partial observation without extrapolation, mean-HR estimate provenance, disabled sRPE fallback, explicit zero/missing history, injury recipient caps, repeated occurrence identity, build Z5 position, spacing equalities/DST, recovery and exact Monday taper. The all-zero run case generated two workouts locally; the mixed-history triathlon case returned the explicitly approved `zero_history_discipline_baseline_unavailable`. No-availability returned `availability_required`. The full-catalog triathlon timings and zero-triathlon capacity failure are recorded, without asserting scientific desirability or production latency.

## Findings index

Details below include the exact source/function reference, reproduction, expected/actual behavior, evidence, impact, suggested remediation, regression coverage and confidence. Severity is application-specific; npm advisory labels are not automatically P0 application findings.

| ID | Severity | Component | Finding |
| --- | --- | --- | --- |
| WOMBO-001 | P1 | Release configuration | Production-designated backend reports local environment |
| WOMBO-002 | P1 | Physiology governance boundary | Production governance covers the load ruleset but not the active planning ruleset |
| WOMBO-003 | P1 | Planning and rescheduling | High-intensity spacing omits workouts across week boundaries |
| WOMBO-004 | P1 | Weekly check-in mobile state | Resuming a check-in resets saved restrictions to unrestricted |
| WOMBO-005 | P1 | Multi-week mobile integration | Check-in plans bypass the retained planning owner and resume locator |
| WOMBO-006 | P1 | Check-in backend retry contract | A committed check-in proposal cannot replay through its create endpoint |
| WOMBO-007 | P1 | Planner performance and availability | Ordinary multi-sport planning monopolizes the single async server worker |
| WOMBO-008 | P2 | Planning recovery | Transient resume reads destroy the saved plan or draft locator |
| WOMBO-009 | P2 | Mobile account lifetime | Plan locators are global across accounts and old mutations can write after account switch |
| WOMBO-010 | P2 | Activities and plan execution | Activity cache never refreshes on reentry and reminder rows cannot supply RPE context |
| WOMBO-011 | P2 | Authentication recovery | Offline session bootstrap discards a valid refresh token |
| WOMBO-012 | P2 | API transport | Mobile requests have no application deadline or cancellation |
| WOMBO-013 | P2 | API response handling | Malformed successful responses bypass ambiguous RPE-write recovery |
| WOMBO-014 | P2 | Privacy lifecycle | Account deletion and retention are not implemented as an end-to-end user operation |
| WOMBO-015 | P2 | Release verification | CI does not run the mobile quality and privacy suite |
| WOMBO-016 | P2 | Mobile test reliability | Active/pending integration tests fail as the real date advances |
| WOMBO-017 | P2 | Dependency/build supply chain | The locked mobile dependency tree contains current security advisories |
| WOMBO-018 | P3 | Profile data editing | Optional profile names cannot be cleared |
| WOMBO-019 | P2 | Deployment health and rollback confidence | Readiness proves process liveness rather than dependency or revision readiness |
| WOMBO-020 | P2 | Calendar date presentation | Week and Calendar disagree on Today when device and athlete timezones differ |

## Confirmed finding records

### WOMBO-001 — P1 — Production-designated backend reports local environment

**Status:** CONFIRMED. **Component:** Release configuration. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `backend/app/core/config.py:24 (Settings.environment)`; `backend/app/core/config.py:101 (require_production_physiology_governance)`; `scripts/start23-common.ps1:6 (production target)`

**Reproduction:** GET https://start23-production.up.railway.app/ready with TLS verification enabled. Compare to the staging /ready response.

**Expected:** A production-designated runtime enables its production validation and governance gates.

**Actual:** HTTP 200 reports environment=local. The physiology and enabled-Polar production validators run only for environment=production.

**Evidence:** evidence/public-health-windows-curl.json; original repository .runtime/start23-mode.json designates this URL production. Observation is live on 2026-10-26.

**User impact:** The public runtime can start without the review and Polar legal/privacy settings that production is supposed to require. No breach or enabled Polar connection was demonstrated.

**Suggested fix:** In a separately authorized release, validate the intended environment, require explicit deployed environment selection and satisfy all production gates before promotion. Make environment and source revision release assertions.

**Regression recommendation:** Deployment smoke must reject local/test environment at the production URL; test startup with omitted environment and missing review metadata.

### WOMBO-002 — P1 — Production governance covers the load ruleset but not the active planning ruleset

**Status:** CONFIRMED. **Component:** Physiology governance boundary. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `backend/app/core/config.py:101 (require_production_physiology_governance)`; `backend/app/modules/physiology/specification.py:179 (JOREN_PLANNING_RULESET_V2)`; `backend/app/modules/planning/service.py:1159 (_build_and_persist)`

**Reproduction:** Instantiate production Settings with a phase-13-only review record, owner and phase-13-joren-ruleset-1 version; inspect new plan payload planning_ruleset_version.

**Expected:** The review gate binds the exact material rules actually active, including joren-planning-ruleset-2 spacing and injury redistribution.

**Actual:** Settings accepts only the Phase 13 review version; the new planner is active unconditionally and has separate persisted provenance but no matching production review gate.

**Evidence:** test_audit_backend.py::test_production_accepts_only_old_load_review_while_new_planner_is_always_active passes. No scientific coefficient was changed.

**User impact:** An earlier review can technically authorize a runtime that uses later material rules without proving their review.

**Suggested fix:** Represent and validate review coverage for both active load and planning versions; retain historical versions. Record the external review, not an AI approval.

**Regression recommendation:** Old-load-only review must fail startup when the new planning policy is active; complete matching review coverage must succeed.

### WOMBO-003 — P1 — High-intensity spacing omits workouts across week boundaries

**Status:** CONFIRMED. **Component:** Planning and rescheduling. **Confidence:** HIGH. **Complexity:** LARGE.

**Exact references:** `backend/app/modules/planning/service.py:2522 (validate_layout)`; `backend/app/modules/planning/service.py:2572 (move_workout)`; `backend/app/modules/planning/domain.py:1132 (schedule_workouts)`; `backend/app/modules/physiology/anti_stack.py:56 (find_anti_stack_violations)`

**Reproduction:** Put a same-sport high workout on Sunday 2026-10-25 and another on Monday 2026-10-26 at the canonical local noon. Validate the Monday plan. Repeat for run, bike and swim.

**Expected:** The approved 72-hour run / 48-hour bike/swim invariant applies across the calendar boundary as well as inside a plan.

**Actual:** The pure validator rejects the combined pair, but the actual layout service receives only the current plan and reports valid. Generation and moves also construct only the selected week context.

**Evidence:** Three parameterized service probes pass in test_audit_backend.py. These test context omission using typed minimal projections, not database persistence. Current history inputs are weekly aggregates, not adjacent workouts.

**User impact:** Two individually valid adjacent weeks can violate the implemented hard spacing contract.

**Suggested fix:** Load the adjacent authoritative schedule horizon for generation, validation, approval and moves; include its version in stale-safe mutation checks. Preserve the existing spacing values.

**Regression recommendation:** Approve adjacent synthetic weeks with Sunday/Monday and Saturday/Monday pairs; reject sub-boundary gaps and concurrent changes to the neighboring week.

### WOMBO-004 — P1 — Resuming a check-in resets saved restrictions to unrestricted

**Status:** CONFIRMED. **Component:** Weekly check-in mobile state. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `mobile/src/screens/CheckInScreen.tsx:178 (restriction defaults)`; `mobile/src/screens/CheckInScreen.tsx:224 (begin)`; `mobile/src/screens/CheckInScreen.tsx:299 (save)`; `supabase/migrations/20260813105401_phase_8_structured_weekly_checkin.sql:678 (restriction clear loop)`

**Reproduction:** Save an unconfirmed context with run=self_reported_blocked. Leave the screen, start/resume that check-in and save another answer without reselecting the run restriction.

**Expected:** All saved context answers, including restrictions, professional advice and alarm acknowledgement, are restored. Clearing a restriction is an explicit athlete decision.

**Actual:** begin restores blocked dates, fatigue, reasons, recurrence and extra activities but omits restrictions and alarm acknowledgement. Run displays Vrij and save sends status=none/resume_unrestricted. SQL confirmation clears the existing restriction for that discipline.

**Evidence:** AUD-007 reproduces the wrong hydrated selection and exact outgoing unrestricted payload. SQL clear effect inspected; pgTAP execution remains a gate.

**User impact:** An interrupted check-in can propose lifting a restriction the athlete did not mean to change.

**Suggested fix:** Hydrate every saved field and load active restrictions when starting a new week; require attributable explicit review before clearing. Keep the separate context confirmation.

**Regression recommendation:** Resume all restriction states with advice/acknowledgement, change only fatigue, and assert restriction identity and provenance remain unchanged.

### WOMBO-005 — P1 — Check-in plans bypass the retained planning owner and resume locator

**Status:** CONFIRMED. **Component:** Multi-week mobile integration. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `mobile/src/screens/CheckInScreen.tsx:334 (makeProposal)`; `mobile/src/screens/CheckInScreen.tsx:351 (approve)`; `mobile/src/navigation/TrainingFlowHost.tsx:17 (retained host)`; `mobile/app/(authenticated)/check-in.tsx:13 (route return)`

**Reproduction:** Keep an approved week in PlanningFlowProvider, open check-in, generate the following week, approve it and return to Week.

**Expected:** Week and Calendar acquire the authoritative new plan/revision and store the new resume identity after the explicit approval.

**Actual:** The check-in screen owns proposalPlan locally, approves directly and calls onBack. It never hands the plan to the retained planning provider or rememberPlanId. That provider does not reload on route focus.

**Evidence:** AUD-008 confirms the old plan object and old saved ID survive successful check-in approval, with no follow-up plan read.

**User impact:** The next approved week can appear missing or the previous week stays visible. A new device has no server plan discovery in this flow either.

**Suggested fix:** Provide a shared authoritative plan handoff/invalidation path for check-in and other plan-changing task screens; persist the resulting locator by athlete.

**Regression recommendation:** Full shell -> check-in -> generate -> approve -> Week/Calendar -> restart test must show the same authoritative plan and revision.

### WOMBO-006 — P1 — A committed check-in proposal cannot replay through its create endpoint

**Status:** CONFIRMED. **Component:** Check-in backend retry contract. **Confidence:** HIGH (source); hosted reproduction pending. **Complexity:** MEDIUM.

**Exact references:** `backend/app/modules/checkins/service.py:263 (generate_plan_proposal)`; `supabase/migrations/20260915205627_r6_checkin_context_and_account_deletion.sql:11 (get_checkin_context_for_planning)`; `supabase/migrations/20260915205627_r6_checkin_context_and_account_deletion.sql:67 (open-only filter)`; `mobile/src/screens/CheckInScreen.tsx:334 (makeProposal)`

**Reproduction:** Generate a proposal, allow attach_plan_proposal to mark the check-in completed, and lose the HTTP response. Retry POST /api/v1/checkins/{checkin_id}/plan-proposals.

**Expected:** Retry returns the exact existing pending proposal and plan, without generating or approving another one.

**Actual:** The service always fetches planning context first; the latest RPC admits only status=open. Once attached/completed, this read raises PT409 before any idempotent plan replay. Resuming a completed check-in restores no proposalPlan in mobile.

**Evidence:** Confirmed control-flow/SQL predicate mismatch. No hosted mutation or PostgreSQL replay experiment was performed. Exact endpoint is listed in evidence/local-openapi.json and the E2E matrix.

**User impact:** A response lost after commit can strand a real pending next-week proposal outside the mobile review flow.

**Suggested fix:** Before generation, read and return an owned already-attached proposal; distinguish replay from a genuinely stale context. Restore completed check-in proposal identity in mobile.

**Regression recommendation:** Rollback-only SQL/API test: commit attach, drop response, retry twice and restart screen; assert identical proposal and occurrence IDs and no activation.

### WOMBO-007 — P1 — Ordinary multi-sport planning monopolizes the single async server worker

**Status:** CONFIRMED. **Component:** Planner performance and availability. **Confidence:** HIGH. **Complexity:** LARGE.

**Exact references:** `backend/app/modules/planning/domain.py:722 (_bounded_selection)`; `backend/app/modules/planning/service.py:544 (_prepare_swipe_context)`; `backend/app/modules/planning/service.py:1159 (_build_and_persist)`; `backend/Dockerfile:21 (single Uvicorn process command)`

**Reproduction:** Run audit_engine_matrix.py against the full 154-source-workout projection with zero-history triathlon and the 2/5/3-hour triathlon case, seven available days.

**Expected:** An ordinary request has bounded CPU cost and does not block unrelated health/auth/API requests while calculating.

**Actual:** Local pure generation took 19.4607 seconds before failing closed for tri_zero and 15.8413 seconds for tri_balanced. It runs synchronously inside async services. The shipped command has no worker/offload isolation.

**Evidence:** evidence/engine-matrix-results.json. Stable synthetic source IDs were used; no deployed benchmark or HTTP concurrency test is claimed.

**User impact:** One normal athlete request can stall the event loop; repeated full-catalog recomputation during swipe interactions compounds latency. Deployed timing depends on hardware.

**Suggested fix:** Profile and bound the existing search, avoid unnecessary recomputation, and isolate CPU execution from the event loop while preserving deterministic results and stale checks. Do not introduce new services.

**Regression recommendation:** Full-catalog triathlon performance budget and concurrent /health latency regression, including infeasible combinations, on deployment-class hardware.

### WOMBO-008 — P2 — Transient resume reads destroy the saved plan or draft locator

**Status:** CONFIRMED. **Component:** Planning recovery. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/features/planning/usePlanningController.ts:83 (resume effect)`; `mobile/src/features/planning/usePlanningController.ts:119 (draft locator deletion)`; `mobile/src/features/planning/usePlanningController.ts:142 (plan locator deletion)`

**Reproduction:** Persist a plan ID, reject its fetch with status=null/503, then restore network and remount or refresh the token.

**Expected:** Keep locators after transient failure and allow an explicit read retry; remove only a definitively absent or forbidden reference.

**Actual:** Every catch deletes the locator. The next attempt becomes ready with plan=null and no ID to fetch. The same pattern applies to a saved draft.

**Evidence:** AUD-001 proves the failed read, storage deletion, and no subsequent fetch after network recovery.

**User impact:** An intact server plan/draft appears lost after offline startup. There is no owner/week plan-discovery endpoint in the current mobile path.

**Suggested fix:** Preserve locators on retryable errors; add explicit resume retry and server discovery for a new/reinstalled device.

**Regression recommendation:** Offline/503 startup followed by retry and process restart retains and restores the same plan/draft.

### WOMBO-009 — P2 — Plan locators are global across accounts and old mutations can write after account switch

**Status:** CONFIRMED. **Component:** Mobile account lifetime. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `mobile/src/features/planning/planningResume.ts:4 (global keys)`; `mobile/src/features/planning/usePlanningController.ts:246 (generate)`; `mobile/src/features/planning/PlanningFlowProvider.tsx:45 (identity-keyed owner)`; `mobile/src/auth/AuthProvider.tsx:118 (sign-out)`

**Reproduction:** A saves a locator, signs out, B enters planning; B receives 404 for A's locator and deletes it. Separately resolve A's pending generate after the provider has switched to B.

**Expected:** Account-scoped locators and write lifetimes; old-account completions cannot change another account's resume metadata.

**Actual:** A and B share the same SecureStore keys; B destroys A's reference. An in-flight A generation still calls rememberSwipeDraftId after unmount and can overwrite the global key.

**Evidence:** AUD-002 and AUD-003. Backend ownership denial remains effective: no cross-account data disclosure was demonstrated.

**User impact:** Shared-device account switching loses valid planning references or leaves the wrong account's locator in storage.

**Suggested fix:** Namespace persistence by authenticated identity, gate storage/state side effects by owner lifetime and resolve account-specific locators without weakening server authorization.

**Regression recommendation:** A/B/A switching plus delayed A response and B mutation; assert separate references and no stale global writes.

### WOMBO-010 — P2 — Activity cache never refreshes on reentry and reminder rows cannot supply RPE context

**Status:** CONFIRMED. **Component:** Activities and plan execution. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `mobile/src/features/activities/useActivityController.ts:46 (historyLoaded)`; `mobile/src/features/activities/useActivityController.ts:86 (ensureActivitiesLoaded)`; `mobile/src/features/activities/useActivityController.ts:101 (refreshPendingRpe)`; `mobile/src/features/activities/useActivityController.ts:178 (history-only RPE lookup)`

**Reproduction:** Enter Activities once with empty history, create a pending activity on another synthetic device, refresh the route reminder and choose its RPE. Also approve a new plan after the first Activities entry.

**Expected:** New pending rows can be completed, history and planned-workout choices refresh after relevant mutations/focus.

**Actual:** Reminder rows update pendingRpe, but saveRpe searches only activities and fails with De activiteit is niet meer beschikbaar. historyLoaded suppresses further entry loads; planned-workout choices stay cached too.

**Evidence:** AUD-004 reproduces the rejected RPE path; AUD-005 proves later entry does not reread calendar/history.

**User impact:** A visible pending feedback banner can be unusable; new planned workouts and activities can be absent until relogin or process restart.

**Suggested fix:** Unify activity entities or fetch the selected pending row; invalidate history/calendar choices after relevant server changes and on explicit refresh/focus.

**Regression recommendation:** Two-device pending RPE plus new-plan approval while Activities is mounted; preserve unresolved local create identity during refresh.

### WOMBO-011 — P2 — Offline session bootstrap discards a valid refresh token

**Status:** CONFIRMED. **Component:** Authentication recovery. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/auth/AuthProvider.tsx:61 (bootstrap)`; `mobile/src/auth/AuthProvider.tsx:68 (unconditional error deletion)`

**Reproduction:** Keep a synthetic refresh token in SecureStore and make refreshSession return AuthRetryableFetchError during app startup.

**Expected:** Retain the refresh token on retryable connection errors and show a recoverable authentication read state.

**Actual:** Any error deletes the token and leaves the user signed out. The provider has no explicit bootstrap retry state.

**Evidence:** AUD-009 uses the real AuthProvider with a synthetic retryable Supabase error.

**User impact:** A normal offline launch forces a fresh login and can aggravate lost planning context.

**Suggested fix:** Separate invalid/revoked refresh credentials from transient transport errors; preserve secure material until invalidity is established and support retry.

**Regression recommendation:** Offline launch -> online retry and invalid-token launch must have different persistence outcomes.

### WOMBO-012 — P2 — Mobile requests have no application deadline or cancellation

**Status:** CONFIRMED. **Component:** API transport. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `mobile/src/api/client.ts:135 (request)`

**Reproduction:** Return a never-settling fetch promise and advance five minutes of fake time during an activity list/mutation request.

**Expected:** A bounded request deadline produces a recoverable error and releases the mutation UI, with safe committed-write reconciliation.

**Actual:** No AbortSignal/deadline is supplied. The promise stays unsettled; controller busy locks can remain held indefinitely.

**Evidence:** AUD-010. OS/network timeouts may eventually occur, but no bounded application guarantee exists.

**User impact:** Endless loading or a locked task on unstable networks.

**Suggested fix:** Add an application deadline and owner cancellation, treating timed-out writes as ambiguous rather than automatically repeating them.

**Regression recommendation:** Hung read and hung create/approval requests must release UI within the configured deadline while preserving idempotency keys and proposal identity.

### WOMBO-013 — P2 — Malformed successful responses bypass ambiguous RPE-write recovery

**Status:** CONFIRMED. **Component:** API response handling. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/api/client.ts:180 (response.json cast)`; `mobile/src/api/client.ts:821 (submitActivityRpeWithRefresh)`

**Reproduction:** Return HTTP 200 for RPE PUT but make response.json throw SyntaxError, simulating a truncated successful response.

**Expected:** Classify uncertain successful-write response failures for authoritative reconciliation, just like a transport failure.

**Actual:** The raw SyntaxError escapes request. RPE refresh recognizes only ApiRequestError, so it performs no GET reconciliation.

**Evidence:** AUD-011 confirms exactly one fetch and the raw parse error. A later explicit idempotent retry may recover; permanent corruption is not claimed.

**User impact:** The athlete sees a failed save even if the server committed, and initial recovery behavior differs by where a response was interrupted.

**Suggested fix:** Normalize response-decoding failures with operation-aware ambiguity metadata and reconcile using the existing exact activity identity. Validate public response shape at the boundary.

**Regression recommendation:** Truncated JSON after committed POST/PUT, invalid DTO shape and subsequent explicit retry must retain identity and accurately report stored state.

### WOMBO-014 — P2 — Account deletion and retention are not implemented as an end-to-end user operation

**Status:** CONFIRMED. **Component:** Privacy lifecycle. **Confidence:** HIGH (implementation gap); legal/operational facts unverified. **Complexity:** LARGE.

**Exact references:** `backend/app/modules/identity/router.py:16 (identity routes)`; `mobile/src/screens/ProfileScreen.tsx:85 (profile actions)`; `backend/app/modules/integrations/repository.py:357 (file upload)`; `backend/app/core/config.py:51 (retention configuration)`; `supabase/migrations/20260914180000_r6_preserve_account_deletion_cascades.sql:1 (cascade groundwork)`

**Reproduction:** Inspect registered routes and profile actions for account deletion/export, and search all uses of the Polar retention-day settings for purge execution.

**Expected:** Before inviting beta users, an approved, workable request/deletion/retention process exists for Auth, relational health data, provider access, raw Storage files and backups.

**Actual:** Relational deletion cascades exist, but there is no app account-deletion operation or established request channel in integrated source, and retention settings have no purge implementation. Disconnect retains imports/files.

**Evidence:** 69-path OpenAPI inventory and repository source. Untracked privacy drafts in the original workspace still contain owner placeholders and are not an integrated published policy. Legal compliance was not assessed.

**User impact:** Operators cannot demonstrate completion of a deletion/retention request using the application alone; Storage objects can outlive relational metadata.

**Suggested fix:** Define legal basis, health-data handling, retention and an operational request process with the owner; implement the authorized lifecycle later, including object-store purge and provider revocation.

**Regression recommendation:** Synthetic account with calibration, plans, activities and a Storage fixture: exercise the approved deletion process and verify every layer plus defined backup treatment.

### WOMBO-015 — P2 — CI does not run the mobile quality and privacy suite

**Status:** CONFIRMED. **Component:** Release verification. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `.github/workflows/backend-ci.yml:5 (backend-only paths)`; `.github/workflows/database-ci.yml:5 (database-only paths)`; `mobile/package.json: scripts`

**Reproduction:** Make a mobile-only change in a hypothetical PR and evaluate workflow path filters; list workflows in the audited revision.

**Expected:** Mobile source and lockfile changes trigger strict TypeScript, mobile tests and public/privacy checks before release.

**Actual:** Only backend-ci.yml and database-ci.yml are tracked. Neither runs mobile checks and neither is triggered by an isolated mobile change.

**Evidence:** Tracked workflow inspection; the actual mobile suite currently fails two date-sensitive tests.

**User impact:** Navigation/state/privacy regressions can merge without any configured mobile test gate.

**Suggested fix:** Add a mobile CI job using a clean locked dependency install and explicit SDK/Node version; run existing quality/privacy checks.

**Regression recommendation:** Demonstrate a mobile-only PR triggers the job and an intentional failing test/type error prevents its success.

### WOMBO-016 — P2 — Active/pending integration tests fail as the real date advances

**Status:** CONFIRMED. **Component:** Mobile test reliability. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/screens/PlanningProposalBoundary.test.tsx:183 (distinct schedule tests)`; `mobile/src/features/planning/planning.test-fixtures.ts:4 (October workout dates)`; `mobile/src/ui-v2/utils/weekHomeViewModel.ts:38 (today/future filtering)`

**Reproduction:** Run the canonical mobile suite on 2026-10-26. Rerun the failing suite with the audit-only clock set to 2026-10-05.

**Expected:** Tests specify time when asserting a next-session presentation and remain meaningful after fixture dates pass.

**Actual:** Two assertions cannot find Approved source workout because the fixture is now in the past. Full suite: 611 pass, 2 fail. Isolated repeat reproduces both; fixed-date diagnostic: 12/12 pass.

**Evidence:** mobile-jest-canonical-results.json; proposal-repeat-results.json; proposal-frozen-results.json. Existing tests were not changed.

**User impact:** False failures undermine the release signal and can hide real active/pending regressions.

**Suggested fix:** Set an explicit clock in time-dependent tests and separately cover past/current/future weeks. Do not remove the failing assertions.

**Regression recommendation:** Run the suite at multiple wall-clock dates with explicit scenario clocks and verify past-week expectations independently.

### WOMBO-017 — P2 — The locked mobile dependency tree contains current security advisories

**Status:** CONFIRMED. **Component:** Dependency/build supply chain. **Confidence:** HIGH (versions/advisories); exploitability REQUIRES VERIFICATION. **Complexity:** MEDIUM.

**Exact references:** `mobile/package-lock.json:11657 (shell-quote 1.10.0)`; `mobile/package-lock.json:9644 (node-forge 1.4.0); mobile/package-lock.json:6991 (image-size 1.2.1)`; `mobile/package.json:9 (Expo SDK dependency tree)`

**Reproduction:** Run npm audit --omit=dev --json against the audited lockfile; inspect the affected package versions and dependency paths.

**Expected:** Known applicable advisories are fixed compatibly or reviewed with an explicit reachability/acceptance decision before building a beta artifact.

**Actual:** npm reports 21 affected package entries: 1 critical, 9 high, 11 moderate. shell-quote 1.10.0 is in the affected range and upstream patches at 1.11.0. Many paths are Expo/Metro build tooling, not proven mobile runtime exposure.

**Evidence:** evidence/npm-audit-clean.json. Upstream shell-quote advisory lists high severity while npm reports critical; preserve both labels instead of upgrading the application finding to P0.

**User impact:** Build/tooling inputs may traverse vulnerable packages; exploitability in Wombo is not demonstrated.

**Suggested fix:** Trace reachable paths, apply compatible transitive updates in a separate change and rebuild/verify. Reject npm's suggested Expo 44 downgrade as an automatic remediation.

**Regression recommendation:** Fresh npm audit plus exact locked install, Expo diagnostics, native SVG build and full tests after any approved dependency update.

### WOMBO-018 — P3 — Optional profile names cannot be cleared

**Status:** CONFIRMED. **Component:** Profile data editing. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/ui-v2/components/ProfileForm.tsx:84 (nonempty-name payload)`; `mobile/src/api/client.ts:231 (saveProfile writes)`; `backend/app/modules/onboarding/schemas.py:62 (nullable identifying update)`

**Reproduction:** Start with an existing first/last name, erase it in Profile and save.

**Expected:** Clearing an optional stored name sends the API's explicit null/update semantics.

**Actual:** Both the form and client omit blank names; when both are blank, no identifying-profile PATCH is sent. The prior server value remains.

**Evidence:** Direct source path inspection. Backend identifying update allows explicit null; no physical-device experiment was run.

**User impact:** The athlete cannot remove optional identifying information through the form.

**Suggested fix:** Distinguish untouched from explicitly cleared fields and send null for removal; keep names optional.

**Regression recommendation:** Save a name, clear one/both, refetch and reopen: the cleared values must stay absent.

### WOMBO-019 — P2 — Readiness proves process liveness rather than dependency or revision readiness

**Status:** CONFIRMED. **Component:** Deployment health and rollback confidence. **Confidence:** HIGH. **Complexity:** MEDIUM.

**Exact references:** `backend/app/modules/health/service.py:16 (build_readiness_response)`; `backend/railway.toml:6 (healthcheckPath)`; `scripts/start-start23-backend.ps1:49 (ready check)`

**Reproduction:** Build a readiness response with a nonexistent Data API host and missing keys in local settings; inspect the release script's health assertion.

**Expected:** The release acceptance signal proves the intended revision can reach required dependencies/schema, or is clearly documented as liveness with separate functional gates.

**Actual:** /ready returns ready without any dependency/schema check. The release script checks only status=ready and cannot prove it reached the newly uploaded revision. Public version stays 0.1.0.

**Evidence:** test_audit_backend.py::test_ready_does_not_inspect_data_api_configuration_or_required_rpc; both live endpoints respond ready, exact Railway SHAs remain unknown.

**User impact:** A deployment with unavailable/mismatched RPCs can be called healthy; a successful old instance may satisfy the script's check.

**Suggested fix:** Separate liveness and bounded readiness/capability checks; attach nonsecret source revision and verify exact deployment success and required RPC compatibility in release validation.

**Regression recommendation:** Unavailable Data API/missing required RPC and old-revision responses must fail release acceptance without mutating athlete data.

### WOMBO-020 — P2 — Week and Calendar disagree on Today when device and athlete timezones differ

**Status:** CONFIRMED. **Component:** Calendar date presentation. **Confidence:** HIGH. **Complexity:** SMALL.

**Exact references:** `mobile/src/screens/PlanningScreen.tsx:881 (athlete-timezone today)`; `mobile/src/screens/PlanningScreen.tsx:895 (Calendar device-date today)`; `mobile/src/features/calendar/useCalendarNavigation.ts:29 (goToday)`

**Reproduction:** Use a plan timezone America/Los_Angeles and a device timezone Europe/Amsterdam at 2026-10-26T00:30Z. Compare Week's Today with Calendar's highlight and Vandaag navigation.

**Expected:** Both roots use the confirmed athlete-local date for the same plan context.

**Actual:** Week formats now with plan.timezone, but Calendar is passed isoDate(now) and goToday independently uses device-local date. In this scenario they select October 25 versus October 26.

**Evidence:** Explicit divergent code paths and deterministic timezone/date example. Native timezone-change execution remains a device gate.

**User impact:** The athlete can see different today/next-session context when traveling or after changing device timezone. Date-only prescriptions themselves are not rewritten.

**Suggested fix:** Pass the same authoritative today/date context into Calendar and its navigation; refresh that date on foreground/day changes.

**Regression recommendation:** Different device/athlete zones around midnight and a foreground timezone change must keep Week/Calendar dates consistent.

## Risks requiring verification — excluded from confirmed issue count

### U-001 — potential P1 — mixed available/unavailable activity measurements in weekly history

**Component/reference:** `get_plan_load_history_for_planning_v13`, `supabase/migrations/20260910215947_phase_13_joren_ruleset.sql:1719` and `:1723`; v14/v15 delegate to it; `PlanningService._load_samples` and `resolve_target` consume the result. **Status/confidence:** REQUIRES VERIFICATION, medium for contract impact, high for the inspected SQL behavior.

**Reproduction to authorize locally:** create an approved synthetic week with one processed measured activity plus one pending/no-load activity and one partial observation; fetch v15, then generate the next week. **Expected:** an explicitly approved completeness rule distinguishes known subtotal from complete weekly realized load. **Observed source:** SQL sums non-null known loads while counting activities; duration/classification coverage omits or ignores some missing rows. A known subtotal can therefore be returned without a full-week completeness marker. **Evidence:** direct SQL inspection, not executed pgTAP. **Impact:** progression/intensity decisions could treat an incomplete aggregate as reliable. **Suggested fix:** first confirm the intended completeness contract, then preserve an explicit unavailable/partial aggregate state through the repository. Do not invent a physiological imputation rule. **Regression:** PostgreSQL tests for all missing, mixed missing, partial, mean-HR estimated, pending RPE, and legacy-version activities. Pass the completeness question to Joren/product as appropriate.

### U-002 — potential P2 — long activity history may truncate at the Data API row cap

**Component/reference:** `supabase/migrations/20260811103726_phase_7_activity_rpe_feedback.sql:456` (`list_activities`), `backend/app/modules/activities/repository.py:255`, `mobile/src/features/activities/useActivityController.ts:58`, `supabase/config.toml:20` (`max_rows = 1000`). **Status/confidence:** REQUIRES VERIFICATION for actual hosted truncation, medium; absence of pagination/cursor in source is confirmed.

**Reproduction:** seed 1,001 synthetic rows in an isolated local database and query API/history plus a pending activity beyond the first page. **Expected:** complete paginated history or an explicit bounded window/cursor. **Observed source:** RPC sorts the entire owner history without pagination and the client treats one response as the complete list; local Data API config limits returned rows. **Evidence:** source/config, no current PostgreSQL execution or hosted row-cap read. **Impact:** older or pending entries may become unreachable and full-history reads grow with account age. **Suggested fix:** define a cursor/window contract and separately bounded pending-RPE query, then verify on the actual Data API. **Regression:** page boundaries, equal timestamps, concurrent inserts and pending rows outside the history page.

## Verification ledger

| Check executed in audit workspace | Result | Evidence / limit |
| --- | --- | --- |
| Backend `python -m pytest -p no:cacheprovider` from backend | **778 passed**, 235.80 s, one Starlette/httpx deprecation warning | `evidence/backend-pytest.log`; existing venv reused, no external data |
| `ruff check .` | Passed | `evidence/backend-ruff.log` |
| `ruff format --check .` | 141 files already formatted | `evidence/backend-format.log` |
| `mypy app tests` | Passed, 139 source files | `evidence/backend-mypy.log` |
| Strict TS `tsc --noEmit -p mobile/tsconfig.json` | Passed, exit 0 | `evidence/mobile-typecheck.log`; empty success output |
| Unused TS `tsc --noEmit --noUnusedLocals --noUnusedParameters -p mobile/tsconfig.json` | Passed, exit 0 | `evidence/mobile-unused.log` |
| Canonical Jest, from mobile cwd | **67 suites pass, 1 fails; 611 pass, 2 fail / 613 tests** | `evidence/mobile-jest-canonical-results.json`; not declared green |
| Isolated failing proposal suite | 10 pass, 2 fail | `evidence/proposal-repeat-results.json` |
| Same proposal suite with audit-only Date diagnostic | 12 pass | `evidence/proposal-frozen-results.json`; no product/test implementation modification |
| Additional mobile audit suite | 11 pass / 3 suites; 10 gap characterizations and 1 approval-retry control | `evidence/audit-mobile-results.json`; mocks' scope explicitly stated |
| Additional backend audit probes | 5 pass | `evidence/audit-backend.log`; three service context-omission probes, governance and readiness |
| Full 154-source synthetic domain matrix | Seven cases completed | `evidence/engine-matrix-results.json`; no database, synthetic stable IDs |
| OpenAPI/public DTO/private-load and architecture purity | Passed as part of backend suite; mobile source privacy test passed | Name/projection and selected runtime-response checks, not arbitrary server logs or final bundle |
| Privileged pattern/environment-file scan | No application pattern locations / no tracked non-example env files found | `evidence/secret-pattern-scan.json`; heuristic, not a complete history/binary secret scan |
| Current npm advisory database | Exit 1: 21 affected package entries | `evidence/npm-audit-clean.json`; no exploit proof, no automatic fixes |
| GitHub remote HEAD, public health/OpenAPI, EAS last 3 build metadata | Read successfully | `evidence/openapi-comparison.json`, `public-health-windows-curl.json`, `eas-build-metadata.json` |
| Railway authenticated release metadata | Blocked: invalid saved grant | `evidence/railway-release-metadata.json`; exact deployed SHA/auto-deploy configuration unknown |
| pgTAP/RLS/migration replay | **NOT RUN** | No Docker/psql/pg_prove runtime found. 27 suites exist; historical hosted reports are not a rerun |
| Current two-real-token API/Data API and Storage isolation | **NOT RUN** | No staging mutation authorized; no production athletes accessed |
| Fresh native build / physical devices / Play release configuration | **NOT RUN** | No native build, installation, signing, Store/OTA operation performed |

The first mobile invocation was launched from repository root and produced alias-resolution failures. It is retained only as diagnostic `mobile-jest.log` and **excluded** from the canonical result; mobile cwd resolves those aliases. PowerShell labels stderr as NativeCommandError even for Jest PASS; results above use actual process exits and structured Jest JSON. The first npm capture mixed stderr into JSON; `npm-audit-clean.json` is the valid separated-stream rerun. No failed check was silently reclassified as passing.

## Completion and acceptance

The source/security/product review, local safe checks, finding records and prioritized remediation outputs have been produced. No fixes were implemented. Fresh database authorization tests, exact deployed identity/configuration, native-device workflows and owner/scientific/privacy decisions remain open gates. A mobile build made from current source appears structurally compatible with the public deployed API surface, but actual functional compatibility and beta safety are **not established**.

**WOMBO FULL SYSTEM AUDIT INCOMPLETE — VERIFICATION GAPS REMAIN**
