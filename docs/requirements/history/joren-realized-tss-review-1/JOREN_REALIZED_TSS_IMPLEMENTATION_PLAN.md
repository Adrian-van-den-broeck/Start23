# Joren realized-load implementation plan

Date: 2026-11-03. Starting candidate: `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`, including A8/A9. **Plan only. No slice below is implemented or authorized by this specification.**

Use the [review/evidence index](JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md), [formal model](JOREN_REALIZED_TSS_FORMAL_MODEL.md), [decision register](JOREN_REALIZED_TSS_DECISION_REGISTER.md) and [fixtures](JOREN_REALIZED_TSS_TEST_MATRIX.md) together. Existing root checkout is older; start eventual implementation from the verified cumulative head after preserving unrelated work. Do not reset, switch over uncommitted root changes, merge into main, push or deploy as part of this task.

## Scope and decision boundary

Build only an approved deterministic estimate within the modular monolith. Do not modify existing zone coefficients, calibration anchors, progression/debt thresholds or historical results to match a new table. Keep pure Python independent of FastAPI, database, Supabase, provider and LLM clients. RPE estimation never becomes an LLM calculation.

Before coding an affected behavior, record exact choices for D01-D18. Critical prerequisites:

- D01 table versus formula authority, including both -3-zone exceptions.
- D02-D04 duration function, overrun caps and structured-session eligibility.
- D05/D09 baseline/measurement selection; D06 actual-duration, missing and zero semantics.
- D07/D08 score mapping scope and input compatibility.
- D10/D11 aggregate completeness and eligibility for subsequent decisions.
- D13 numeric context/rounding, D14 correction/history, D16 version/storage contract.

Explicitly leaving multi-sport, late evidence or estimate-driven matching disabled is a valid bounded choice for D12/D15/D17; inventing their behavior is not. D18 retains scientific review and privacy-safe wording as release gates. Acknowledging heuristic limitations does not approve any coefficients or release.

## Slice 0 - freeze decisions, sources and reproducible baseline

Deliver a signed/versioned approval record selecting options, fixture expectations and unsupported cases. Preserve the actual PDF by approved source custody/versioning, with reviewed SHA-256 from the review; do not claim it already belongs to A9. Record compatible planned-load methods and consumer policy.

Inventory the eventual implementation workspace, exact branch base and uncommitted work. Preserve A10/A3/A4/A5/A6/A7/A8/A9 ancestry. No squashing/rebasing/deleting prior remediations is needed.

Acceptance: D01 resolves M16/M22 explicitly; actual-duration inclusion is distinguished from ratio approval; U-001 has an approved typed quality/consumer contract; old versions' fixture expectations remain unchanged.

## Slice 1 - pure private estimate calculator

Add a small module near `backend/app/modules/physiology/joren.py` and typed private input/result dataclasses, following existing patterns. Do not change the meaning of `ZoneLoad` to make an estimate look like measured complete data.

Inputs: canonical discipline, private planned P/T/method/version, approved planned zone/structure facts, actual duration, strict Session-RPE, selected immutable policy version. Output: a typed estimated result/provenance or explicit unavailable reason.

Implement the approved25 factors as exact decimal strings or the approved formula, never a hybrid inferred from convenience. If the table is authoritative, retain all25 explicit reviewed fixtures even if some cells are derivable. If linear wins, preserve the PDF discrepancy fixtures as source history and document the approved replacement expectations.

Implement only the approved duration rule and structure eligibility. Validate finite/nonnegative inputs, positive denominator, exact zone/score domains and missing/zero dispositions. Fix Decimal context/input scales and rounding once as D13 decides. Do not add an extra sport multiplier to planned P.

Acceptance: M01-M25, R/U/S/N families; all25 parity plus properties and invalid-input fixtures. Existing `zone_load`, mean-HR, inactive sRPE and legacy functions retain their results. No I/O/import dependency on service frameworks.

## Slice 2 - versioned private context and explicit method dispatch

Current `get_activity_processing_context` exposes only planned load, expected RPE range and intensity bucket. Design a versioned private context with exact approved occurrence/revision/template references, original P/T/method/version, segment structure fingerprint and approved p source. Do not fetch a current catalog template and assume it represents an old accepted occurrence.

Update the internal repository/service parsing with typed contracts; keep route handlers thin. Resolve athlete identity through existing verified token and opaque identity mapping; never authorize a client user_id.

Replace the current binary new-versus-legacy correction assumption with an explicit registry/branch for recognized stored methods/versions. Unknown versions fail closed. Current `stored_version != VERSION` behavior must not classify the new estimator as retired RPE-times-hours.

Acceptance: P01-P07,V01-V06; old contexts/readers remain supported; unsupported methods do not silently convert; repeated templates preserve distinct occurrence IDs.

## Slice 3 - forward-only private persistence and audit contract

Prepare a **new forward-only migration** only after D14/D16 schema approval. Do not edit an applied migration or execute schema changes during this specification task.

Proposed design for review: append private calculation records with immutable input/formula/source snapshots, and an explicit selected-result relation. Extend existing private audit history rather than adding duplicate unversioned state. A separate estimate table or versioned extension of current load storage is D16; names in the formal model describe concepts, not a committed schema.

Must handle:

- Existing `private.activity_loads` and append-only `private.phase_13_activity_load_history` without historical rewrites.
- A25-cell table/version source hash, raw r/q, P/T/A, structure/p source, duration policy and numeric/rounding policy.
- Previous/result revision IDs, selection history, observed measurement/profile references where real, and unavailable reasons.
- Existing completion SQL's assumption that a non-Phase13 method equals retired formula.
- Existing method/version and provenance CHECK constraints: explicitly allow approved new combinations and reject cross-method contradictions. Do not weaken constraints to accept arbitrary strings.
- New estimates do not populate measured valid minutes or coverage100%; missing/zero/partial states remain distinct.
- Owner-scoped composite references, RLS, restricted private grants, explicit service-only RPC authorization and fixed search paths. No broader public/athlete grants to make reads work.
- Idempotent unique calculation identities for retries and atomic correction/selection updates.

Acceptance now: migration design and static contracts reviewed. **Execution acceptance deferred**: rollback-only PostgreSQL/pgTAP owner-isolation, constraint, concurrency, audit and numeric-storage tests at integration/release. Deferral is not permission to activate unverified persistence.

## Slice 4 - integrate calculation selection with activity completion

Insert selection inside `ActivityService.submit_rpe` after authoritative observations/context are available and before building the private completion payload. Preserve:

1. Complete/partial observed-zone results and exact existing coefficients.
2. Approved mean-HR estimate under current eligible conditions.
3. Newly approved fallback only for otherwise unavailable qualifying planned sessions.
4. Explicit unavailable outcome when required data/decision is absent.

Do not multiply an existing observed/HR result, add an overlapping full estimate to a partial subtotal, activate inactive sRPE, infer swim duration or overwrite originating zone profiles.

Keep storing subjective RPE even when no reliable estimate exists. `processing_state=complete` need not mean measurement complete. Current required-HR behavior for assigned RPE-guided workouts cannot silently disappear because an estimate is available; changing that contract needs explicit D05/D06 approval.

If D06 requires performed-duration confirmation, make a narrowly scoped compatible form/contract change; the existing planned-duration prefill must not be labelled measured evidence. No unrelated UI V1/V2 work.

Acceptance: H01-H06,U06-U15, API validation, exact private payload, unchanged public response schema and recursive leak checks.

## Slice 5 - corrections, response loss and qualitative matching

New-method RPE corrections use the approved original P/T/p snapshot and method-specific version; append prior calculation and recompute only the estimate allowed by D14. Existing observed/HR results retain their original load/profile semantics. No hidden migration occurs on an old RPE edit.

Preserve the current local-week correction window, `expected_current_rpe`, duplicate-same-score replay, HR immutability and pending correction expiry/revision behavior. Late better evidence is disabled unless D15 approves a separate append/selection path.

D12 decides whether estimates participate in numeric qualitative matching. Do not set status complete merely to pass `measurement.status != "complete"` logic. Preserve low-workout/RPE>=7 hidden-fatigue feedback independently. Any system-generated plan change remains a pending, version-preconditioned athlete proposal.

Acceptance: Q01-Q05,V01-V10, injected response loss/retry, stale/wrong-owner/closed-window rejection with no partial mutation. Existing A7/A8 cache and authoritative reconciliation tests remain intact.

## Slice 6 - U-001 private weekly aggregation contract

Version the aggregate interface explicitly; do not silently change historical v13/v14/v15 interpretation. Existing v13 filters Phase13 and has no quality marker, so merely persisting new rows is insufficient.

Implement approved typed fields for known subtotal, selected numeric/method/version counts, pending/missing/partial counts, total-duration availability, observed-zone coverage, classified-intensity coverage, expected/matched occurrence counts and nullable planner-usable load/eligibility reasons.

Rules must distinguish no activity rows, activity rows awaiting RPE, all-unavailable processed rows, partial observations, whole-duration estimates and legacy/incompatible methods. SUM's NULL omission cannot imply complete-week evidence. No imputation, zero-fill, partial-time extrapolation, numeric confidence score or fabricated intensity minutes.

Keep local-week/timezone behavior and exact approved revision references. Preserve v15 prior-approved-plan provenance independently of the six-week load window; activity-only history must not turn into an approved plan baseline.

Acceptance: W01-W10 and mixed-method/version cases in SQL/API/service/domain fixtures. Static/source and mock tests can be completed first; deferred PostgreSQL execution remains a named gate.

## Slice 7 - subsequent-week consumer integration

Carry approved eligibility into `PlanLoadSample` and `resolve_target`/intensity-debt consumers. Do not just pass a new numeric subtotal into the old `realized_load` field.

D11 must explicitly permit each quality class for normal progression, fatigue/missed progression, volume debt,42-day baseline and intensity debt. Preserve existing constants and rule precedence, injury restrictions, sickness exclusion, race taper/recovery and first-plan/returning-athlete decisions. Unsupported evidence follows the approved hold/fail-closed behavior; the review does not invent one.

Include aggregate policy and selected calculation IDs in new proposal input fingerprints/snapshots so a feedback correction or changed selection cannot silently apply a stale proposal. Preserve A3 restrictions, A4 check-in handoff, A5 durable proposal recovery, A6 owner-scoped restoration, A7 synchronization, A8 network reconciliation and A9 deterministic worker/result parity.

Acceptance: W11-W20, target/phase/selection parity for unchanged historical inputs, private target privacy, pending-only plan change and stale approval tests.

## Slice 8 - RPE guidance and public compatibility

If D07 chooses estimate-only mapping, keep old shared guidance/calibration consumers versioned and unchanged. If a broader migration is approved, introduce explicit prospective template/protocol/guidance versions and test all consumers before replacing old fixtures.

Cover Python shared helper, workout/planned-workout/deck public guidance, calibration range validation and labels, mobile consumers and discipline descriptions. Explain why a future old-range test is superseded for new versions while retaining historical coverage.

D08 governs strict API compatibility. D18 governs qualitative wording. Existing public DTOs must not gain planned/realized private load, factor, private estimate details or internal snapshots. Apply the same boundary to errors, HTTP debug logs, analytics, accessibility, provider diagnostics and LLM prompts. No provider SDK or secret enters mobile.

Acceptance: public/OpenAPI contracts, recursive private-load leak tests and relevant mobile/strict TypeScript tests; no unrelated layout or V1/V2 redesign.

## Slice 9 - review, integration gates and prospective activation

Collect explicit new ruleset/calculation and aggregate-policy identifiers, named accountable physiological reviewer and immutable review record with scope/exclusions. Keep existing load/calibration/planning versions distinct; do not change `phase-13-joren-ruleset-1` in place.

Before enabling new selection:

- All enabled behavior has approval and independent expected fixtures.
- Relevant backend suites, Ruff/format, strict mypy, OpenAPI/contracts and private-load leak checks pass.
- Changed mobile consumers pass strict TypeScript, unused-code and relevant mobile tests.
- At owner-designated integration/release stage, forward-only migration replay, PostgreSQL/pgTAP/RLS, numeric parity, RPC idempotency and two-owner isolation are executed and pass.
- Approved scientific/release review is attached. Arithmetic fixture parity alone is insufficient.

No deployment/push/merge occurs under this plan. Activation is a future authorized operation with explicit effective boundary and eligibility. New behavior is prospective; old activities, approved plan references and result histories remain untouched unless a separately approved migration policy explicitly says otherwise.

## Rollback and historical compatibility

Stop new-method selection prospectively without deleting new records or relabelling them as Phase13/legacy. Retain readers for already-created new-version records and proposal snapshots. Do not revert storage by removing data-bearing columns/tables. Any corrective SQL is another forward-only migration.

Already-approved plans are not rewritten when a calculation version is disabled or better observations arrive. Any reconsideration uses the existing pending proposal/athlete approval flow and stale precondition. Historical recalculation requires its own approved scope, provenance and comparison record; it is not part of this plan.

## Documentation and acceptance record

After an eventual approved implementation, update ruleset evidence, formula specification, current roadmap/traceability, actual-duration/Session-RPE semantics, measurement hierarchy, private schema/RPC contracts, weekly quality interpretation, historical correction policy and release gates. Preserve this review's source discrepancy and unapproved-option history.

This specification task delivered only the five Markdown files. Existing A9 source characterization passed169 tests. No claim is made that this plan, future fixtures, database gates or physiological validation has been implemented/passed.
