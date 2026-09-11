# Phase 13 implementation plan

Status: implementation and hosted Phase 13 migration present; remediation R1
implemented locally; full runtime, database, and external verification remain
open, 2026-09-11. Specification: phase-13-joren-ruleset-1.

See [executed checks, final review and remaining gates](phase-13-review.md).

## Consumer trace before implementation

| Area | Affected consumers and persistence |
| --- | --- |
| Phase 3 | physiology specification, progression, activity, taper, zones; immutable prior versions |
| Phase 4/14 | onboarding schemas/service/history RPC and planning snapshots; mobile history form/contracts; prior two-month rows |
| Phase 6 | planning resolve_target, catalog snapshots, proposal payload/revision provenance, history RPC |
| Phase 7 | activity summary/metrics, processing context, RPE completion/revision RPC, private.activity_loads and audit |
| Phase 8 | confirmed weekly context, illness/fatigue/missed flags, history filtering; restriction/rest precedence |
| Phase 8.5/11 | submaximal evaluator, threshold confirmation, calculated profiles, boundary classification, numeric visibility; protocol/evaluation versions |
| Phase 10/10.1 | swipe targets/catalog eligibility, plan revision snapshots, service-only draft RPC, coach public context |
| Provider input | Polar summary and observed metrics; observed zone time takes precedence; mean-HR-only uses its known HR zone for the full duration with estimated provenance (2026-09-11 amendment) |

## Remediation R1 decision and implementation trace

The dated, accountable decisions and the R3 forward-migration design are in
[the R1 decision record](phase-13-and-14-r1-decisions.md). R1 preserves the
approved Phase 13 formulas and all historical protocol/ruleset provenance.

| R1 decision | R1 implementation/evidence | Later-phase dependency intentionally retained |
| --- | --- | --- |
| Reject changed average HR after Phase 13 private load exists | Decision R1-D1 records the immutable inputs, originating profile/ruleset, atomicity, idempotency, and audit requirement | R5 implements and regression-tests the correction transaction |
| Version-aware onboarding | `onboarding/versioning.py`; state response version/upgrade fields; forward migration `20260911180631`; `test_onboarding_versioning.py`; R1 pgTAP structure test | R2 implements legacy upgrade orchestration and planner/direct-RPC parity; R4 adds a new version for its remaining mandatory fields |
| Run/bike calibration must supply average HR | Current protocol discovery/setup/scheduling filters in `calibration/service.py`; API matrix/rejection tests; immutable registry unchanged | R2 completes the mobile observation contract, swim elapsed-time path, and capability copy |
| Opaque identity/physiology split | R1-D4 fixes mapping, table ownership, RLS, staged dual-key backfill/cutover, value retention, and verification invariants | R3 executes the forward migrations, repository/API cutover, and two-user isolation tests |
| Reproducible Phase 13 artifact set | Versioned ruleset/source PDFs, domain module/tests, migrations/pgTAP, implementation/review/remediation records are explicitly tracked and checked | R6 repeats full release/database verification |

Existing load constraints require positive values and the old calculation method;
new unavailable/partial measurements need explicit private provenance and cannot
be represented as zero or silently compared to legacy load units. Current stored
zone profiles use the prior shared-boundary model; new inclusive discrete ranges
need model-aware validation, persistence, classification and display. Current
calibration confirmation recalculates profiles using the old model and must use
the evaluation's model version instead. Historical definitions remain unchanged.

## Increments

1. Archive old Phase 13; record new authoritative ruleset and rounding discrepancies.
2. Add deterministic pure rules and exhaustive source/boundary tests.
3. Wire onboarding, calibration, planned/observed load and weekly/taper consumers;
   use forward-only migrations with private provenance and unchanged approvals/RLS.
4. Update mobile contracts/presentation, roadmap and traceability.
5. Full backend/lint/format/mypy, public/privacy, mobile and available database
   verification; targeted stale-assumption review; report open release gates.
