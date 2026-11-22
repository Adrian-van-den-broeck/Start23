# WOMBO prioritized remediation plan

Date: 26 October 2026. Baseline: `aff74558d0a6511286a4a84a44ea25a03ca57549`. **This is a plan for separately authorized fixes, not implementation authorization.** Production, schemas, formulas and application behavior were preserved by the audit.

The [main audit](WOMBO_FULL_SYSTEM_AUDIT.md) contains 20 confirmed issues: 7 P1, 12 P2, 1 P3; no P0 demonstrated. Every item below references its evidence-backed record. Unknown deployment/physical facts remain explicit gates, not green tasks.

Complexity is relative engineering scope, not a calendar commitment: **SMALL** = a narrow owner/validation/CI change; **MEDIUM** = a coordinated boundary/state/contract change; **LARGE** = transactional/context/performance/lifecycle work needing broader verification. Work can be split into smaller reviewable PRs. No instruction here authorizes parallel agents or broad refactoring.

## A. Must fix or close before real-user beta

| Order / reviewable change | Findings | Scope and acceptance | Complexity | Dependencies |
| --- | --- | --- | --- | --- |
| A1. Establish the intended production runtime and explicit active-rule review coverage | 001, 002 | Verify actual Railway service/source/environment; make production selection non-optional and fail closed on incomplete review coverage for both active versions. Record the real external reviewer evidence. Do not deploy merely to make the audit report green | MEDIUM | G1/G2 read-only deployment/ledger identity; D1 review record. Fix preparation can proceed before promotion |
| A2. Adjacent-week schedule context and concurrency | 003 | Add authoritative neighboring schedule horizon to generation, complete-layout validation and moves. Preserve 72/48 values and date-only convention. Include neighbor revisions in stale checks so two devices cannot each approve an individually valid but conflicting week | LARGE | G3 fresh local DB baseline; existing rules suffice, no new formula |
| A3. Lossless check-in restriction round trip | 004 | Restore every saved field, professional advice and alarm acknowledgement; present active restrictions on a new week; require explicit attributable clearance choice. Add round-trip tests before refactoring layout | MEDIUM | Existing restriction/status contract; product clarification only if clearance eligibility itself changes |
| A4. One authoritative task-to-plan handoff | 005 | Have check-in-generated/approved plan state and locator reach retained Week/Calendar; reuse the same path for other plan-mutating supporting tasks. Keep active/pending snapshots distinct | MEDIUM | Existing provider ownership; can be independent of A5 but verify together |
| A5. Idempotent completed-check-in proposal recovery | 006 | Return the exact existing owned attached proposal before requiring open-generation context; restore pending review after restart. Use forward-only SQL changes if needed; do not rewrite applied migrations | MEDIUM | G3 DB tests; coordinate with A4. Approval remains separate |
| A6. Account-scoped durable plan discovery and safe resume | 008, 009 | Preserve references on transient errors; expose explicit read retry; namespace per athlete; prevent old-owner persistent writes; define bounded server plan/draft discovery for new/reinstalled devices | MEDIUM | Existing token identity; optional new API must be owner-scoped. No dependence on visual redesign |
| A7. Activity identity/cache invalidation | 010 | Resolve banner-selected row from authoritative entity/fetch; refresh history and planned-workout choices after relevant task/remote changes. Keep unresolved create/RPE state stable | MEDIUM | A4 shared mutation invalidation pattern is useful, not a mandatory sequential blocker |
| A8. Retryable auth bootstrap and bounded transport | 011, 012, 013 | Keep valid refresh token on transient failure; add explicit retry; add request deadline/owner cancellation and JSON-decoding ambiguity classification. Reconcile committed writes with existing keys/preconditions rather than blind retries | MEDIUM | Preserve A6/A7 identity lifetimes; tests must cover timeout-after-commit |
| A9. Bound/isolate full-catalog CPU work | 007 | Profile full-source multi-sport feasible and impossible cases; stop event-loop monopolization, reduce repeated recomputation, preserve exact deterministic policy/output. Set a reviewed performance budget and test unrelated request latency | LARGE | G3 representative catalog; no physiological changes, no new infrastructure services |
| A10. Restore a trustworthy mobile verification gate | 015, 016 | Fix clock assumptions while preserving active/pending assertions; add mobile-only CI with locked install, strict TS, test and privacy checks. Existing failing tests must become meaningful, not deleted | SMALL | Independent; should land early so later remediation has a reliable signal |
| A11. Resolve applicable dependency advisories before the next release build | 017 | Trace build/runtime reachability, apply compatible patched transitives or explicit documented risk decision; run SDK diagnostics and native build. Do not accept the automatic Expo 44 downgrade | MEDIUM | G6 new binary; maintain current SDK instruction unless separately authorized |
| A12. Make release acceptance prove readiness and exact revision | 019 | Distinguish liveness from required dependency/schema readiness; validate intended source SHA/environment and exact deployment success; check mobile/backend/schema compatibility with safe synthetic probes | MEDIUM | A1, G1/G2/G3. Must not mutate production during verification preparation |
| A13. One athlete-local Today context | 020 | Use the same confirmed timezone/date in Week and Calendar/Today navigation; test foreground and midnight transitions | SMALL | Independent of layout; G6 device confirmation |
| A14. Establish a workable privacy/deletion/retention operation before collecting beta health data | 014 | Owner/legal decisions and a documented request process first; then separately authorize needed deletion/export/provider/Storage implementation. Validate whole-account deletion with synthetic data, including raw objects and backup treatment | LARGE | E1–E4 decisions and G4 synthetic isolated-account authorization. A policy draft alone is insufficient |

**Beta acceptance is conjunctive:** closing the above software issues does not close the database, exact deployment, external review or physical-device gates. A failed optional-provider gate can be handled by an explicit disabled-provider beta scope, verified in actual configuration; a UI notice alone is not disabling.

## B. Should fix shortly after a deliberately scoped beta launch

These can follow a controlled beta only if A and applicable gates are closed, and exclusions are explicit.

| Item | Source / rationale | Complexity | Dependencies |
| --- | --- | --- | --- |
| B1. Bounded history/current-zone read contracts | U-002; unpaginated activity history and all-history onboarding metrics | MEDIUM | Define cursor/window contract; first verify cap behavior with >1,000 synthetic rows |
| B2. Safe support observability | Request ID discarded by mobile; logs lack a demonstrated global scrubber; no measured request-volume dashboard | SMALL–MEDIUM | Approved log fields/retention/contact; no private load, free health text or credentials |
| B3. Reproducible backend dependency/image record | Unlocked ranges and production/local Decimal schema difference | SMALL–MEDIUM | Pin approved dependency set and attach image/source metadata to release record |
| B4. Supporting-task late-response and same-tick mutation guards | Profile, onboarding, zone/calibration and integrations use varied local run patterns | MEDIUM | Extend negative tests against actual task contracts; do not broaden state abstractions without evidence |
| B5. Optional Polar durability/file resource hardening | Background receipt processing, post-buffer size cap, separate object/metadata writes | MEDIUM–LARGE | Must move to A before Polar is enabled for beta; provider/legal/scheduler gates still apply |
| B6. Profile partial-success reconciliation | Two profile PATCH calls run concurrently; atomicity/recovery promise not specified | SMALL–MEDIUM | Product expectation and existing version constraints |

U-001 mixed-measurement weekly completeness is **not automatically deferred to B**. It must be resolved as an A decision/verification gate before claiming the feedback-driven next-week loop reliable. If a contract bug is confirmed, create a separate small correctness PR preserving original measurements/provenance.

## C. Can safely wait within a documented beta scope

| Item | Finding/risk | Complexity | Condition |
| --- | --- | --- | --- |
| C1. Optional name clearing UI | 018 | SMALL | A workable privacy/support deletion channel exists; no promise that blanking a name already removes it |
| C2. Reduce large screen/controller complexity | Source maintainability debt | MEDIUM, split by seam | Only after ownership/recovery fixes have behavioral regression coverage; no visual redesign |
| C3. Remove legacy owner adapter / historical protocol compatibility code | Historical cutover debt | LARGE | Separate forward migration decision and parity evidence; never discard historical provenance casually |
| C4. More catalog/event/multi-sport/brick capability | Product/scientific expansion | LARGE | Explicit new versioned decisions; outside this technical audit and MVP beta claims |
| C5. OTA/channel/rollback sophistication | No configured full OTA rollout scheme found | MEDIUM | A validated native-release rollback procedure is already available; never treat UI V1 toggle as schema rollback |

## D. Questions for Joren

Use [WOMBO_JOREN_REVIEW_QUESTIONS.md](WOMBO_JOREN_REVIEW_QUESTIONS.md). Priorities are: exact active-version review coverage (J-01), weekly measurement completeness (J-02), unsupported zero/asymmetric multi-sport beginner scope (J-03), non-Monday taper (J-04), explicit injury removal/reintroduction scope (J-05), date-only spacing interpretation (J-06), and repeated-source/session/multi-sport composition (J-07).

These questions do not authorize new coefficients. Missing neighboring-week context, lost restriction answers, broken state handoffs and slow synchronous execution are technical fixes against existing rules; they do not require Joren to invent a replacement engine.

## E. Product/owner decisions required

| Decision | Why it matters | Required deliverable |
| --- | --- | --- |
| E1. Which Railway/Supabase/EAS projects actually constitute production and beta? | Local task state says production while the public host reports local; original mobile env selects staging; Railway SHA unknown | Named project/service/environment, source SHA/image/build, migration ledger, domains and variable-presence checklist without secret values |
| E2. Privacy/health-data purposes, eligibility and processors | No completed operational policy/consent/retention/deletion process is integrated | Approved controller/contact, purposes/legal conditions, age scope, health-data handling, region/processor agreements and retention schedule; legal review as needed |
| E3. Deletion/export/support and backup scope | Relational cascades do not perform Auth/provider/Storage deletion | Owner-approved process, response ownership, request channel, data-layer checklist, backup and third-party treatment |
| E4. Session and beta-access semantics | Logout is local; JWT revocation lag and Pioneer entitlement scope are not fully defined | Explicit local/all-device behavior, recovery channel, invite-only service expectation if any |
| E5. Unsupported athlete/race scope | All-zero triathlon, asymmetric history and non-Monday taper can intentionally fail closed | Truthful beta eligibility/exclusion or an approved reviewed coverage specification; never invent planning values |
| E6. Weekly aggregate measurement completeness | Missing/pending/partial activity data can change next-week interpretation | Explicit input-completeness contract plus SQL/API fixture (U-001) |
| E7. Which optional Polar/LLM features are enabled? | UI support and source adapters do not prove production approvals/configuration | Verified disabled state or complete provider/privacy/operational release evidence |
| E8. Performance and reliability acceptance | Current domain timings are too expensive for unisolated async execution; no deployed SLA was tested | Representative fixture set, agreed response/health budget, concurrency/load expectations and monitoring owner; these are engineering budgets, not physiological limits |

## F. Unverified database, physical-device and release gates

| Gate | Evidence required to close | Current state / authorization boundary |
| --- | --- | --- |
| G1 — Exact Railway source/configuration and auto-deploy | Read service/environment/root/repo/branch/CI-wait/latest deployment SHA/status, variable names/presence, intended URL and prior rollback revision | BLOCKED by expired saved Railway grant. No production changes authorized; read-only reauthentication/configuration inspection still needed |
| G2 — Database source compatibility | Compare all 47 tracked migrations through `20261004212750` to actual target ledger; inspect current grants/RLS/functions without athlete records | NOT VERIFIED. Do not apply hosted migrations as an audit check |
| G3 — Fresh local migration/pgTAP run | Start isolated DB from scratch, apply forward chain, run all 27 suites and new boundary/failure/race cases | NOT RUN: no Docker/psql/pg_prove runtime in this session. Existing historical reports do not close it |
| G4 — Two-token API/Data API/Storage isolation | Synthetic A/B sessions, distinct opaque/Auth IDs, foreign plan/activity/occurrence/calibration/test-assignment attempts, denied private load/RPC/table access and file ownership | NOT RUN; staging user/row/file writes require separate authorization. Never use production athletes |
| G5 — Persisted multi-week fault-injection journey | Setup -> first plan -> activity/RPE -> changed availability/injury -> next several weeks; duplicate/lost-response/expired-token/two-device faults | NOT RUN; local mocks/domain fixtures do not establish the complete transaction sequence |
| G6 — Fresh Android native candidate | Build from remediated exact SHA with SVG/icons, SDK 57/lockfile, intended public API/Auth URLs and UI V1/V2 flag; install/relaunch | Latest inspected EAS build 22 predates UI V2/native dependencies. Audit did not build or submit anything |
| G7 — Physical Android/iPhone | Keyboard/scroll/gestures, accessibility/font scale, rapid navigation, offline/foreground expiry, crash/restart, timezone changes and warning cancellation on synthetic account | NOT RUN; iOS signing/device availability remains external. No 117-screen redesign/comparison is needed |
| G8 — EAS/Play/OTA identity | Actual EAS production variable presence/project pairing, build SHA/artifact provenance, package/versionCode, native runtime compatibility and Play track | Only latest 3 EAS build records read. No artifact downloaded/installed, no store-track configuration proof |
| G9 — Rollback/recovery | Rehearse known prior backend/native app against forward-migrated isolated schema; restore evidence and operational owner | NOT VERIFIED; no rollback/redeploy/database reset executed |
| G10 — Optional provider/LLM | Approved provider/privacy settings, callback/reconnect, durable retries/scheduler, bounded files, retention/deletion, safe logs and real test-provider operation | Mocked tests only. Explicitly disable optional feature or obtain separate staging permission and evidence |
| G11 — Final privacy/secret/error/bundle review | Nested success/error/trace/bundle inspection without raw health data or private load; no privileged mobile keys; approved logs/retention | Source/schema tests pass; no final binary/hosted log certification |
| G12 — Final verification record | Canonical backend/mobile/format/types/privacy suites green at explicit clocks; CI triggered by relevant diffs; database and native gates attached to exact candidate | Current backend green; canonical mobile two date failures; remaining gates open |

## Suggested implementation sequencing and review discipline

First establish A10 verification and prepare A1 configuration/governance validation; do not promote production while its prerequisites remain absent. Fix A3–A8 as separate ownership/recovery changes, then exercise their combined multi-week path. A2 and A9 need deeper design/verification and can be developed as independently reviewable patches against fixed semantics. Review A11 before constructing the next native candidate. Close A14 owner decisions early because operational/legal work can take longer than a code patch.

Every PR should state its concrete before/after behavior, unchanged physiological rules, exact tests and remaining gate. Any SQL correction must be forward-only, maintain owner/service grants and retain history/provenance. No test should be weakened to preserve obsolete broken behavior. No finding should be auto-implemented from this plan.

**Release decision remains: WOMBO FULL SYSTEM AUDIT INCOMPLETE — VERIFICATION GAPS REMAIN.** The deliverables are ready for prioritized remediation review; they do not certify production safety.
