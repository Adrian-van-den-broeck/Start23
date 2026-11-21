from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/audits'
findings=json.loads((OUT/'evidence/findings.json').read_text(encoding='utf-8'))
intro='''# WOMBO full system audit

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
'''
for f in findings:intro+=f"| {f['id']} | {f['severity']} | {f['component']} | {f['title']} |\n"
intro+='\n## Confirmed finding records\n\n'
for f in findings:
 intro+=f"### {f['id']} — {f['severity']} — {f['title']}\n\n"
 intro+=f"**Status:** {f['status']}. **Component:** {f['component']}. **Confidence:** {f['confidence']}. **Complexity:** {f['complexity']}.\n\n"
 for title,key in [('Exact references','references'),('Reproduction','reproduction'),('Expected','expected'),('Actual','actual'),('Evidence','evidence'),('User impact','impact'),('Suggested fix','suggested_fix'),('Regression recommendation','regression_test')]:
  value=f[key]
  if isinstance(value,list): value='; '.join('`'+v+'`' for v in value)
  intro+=f'**{title}:** {value}\n\n'
intro+='''## Risks requiring verification — excluded from confirmed issue count

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
'''
(OUT/'WOMBO_FULL_SYSTEM_AUDIT.md').write_text(intro,encoding='utf-8')
print('main report words',len(intro.split()))
