# Joren Realized TSS v2 implementation report

Date: 2026-11-03. Product authority: the owner's explicit WOMBO implementation
instruction and the [approved v2 specification](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md).

**WOMBO JOREN REALIZED TSS V2 IMPLEMENTED — SOFTWARE VERIFIED, DATABASE/RELEASE GATES OPEN**

This is a prospective, locally gated software implementation. The multiplier is
a reasoned, unvalidated heuristic. Passing software tests does not establish
scientific validity, PostgreSQL compatibility or release readiness. PostgreSQL/
pgTAP is **DEFERRED BY OWNER — PRE-BETA**. No hosted database was changed.

## Exact baseline, isolation and commits

- Start: `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` (accepted cumulative A9).
- Final tested implementation: `a0096135814c474ed667adcb957b99a66b54b769`.
- Branch: `feat/joren-realized-tss-v2`.
- Worktree: `F:/Projecten Business/Start23/Code/.worktrees/joren-realized-tss-v2`.
- This report is committed in a subsequent documentation-only commit. The final
  implementation SHA above identifies all tested code, migrations, specifications
  and benchmark evidence; the delivery HEAD additionally includes this report.

Consecutive Git ancestry checks confirmed:

| Remediation | Exact SHA |
| --- | --- |
| A10 | `11591b9924ebfd3872314deecb82c57fc278126b` |
| A3 | `b65ea78be1db886586d793f721bb2910ddbc6a41` |
| A4 | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` |
| A5 | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` |
| A6 | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` |
| A7 | `75f172d4161f71a763247b04c027fd165901afbd` |
| A8 | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| A9 | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` |

The older root checkout, root changes, other worktrees and untracked visual
evidence were preserved. Root/mobile AGENTS and the current MVP roadmap were
read. No main push, merge, deployment, production or staging mutation occurred.

| Slice | Local commit | Result and focused verification |
| --- | --- | --- |
| 1 | `740008a` | Pure Decimal calculator, independent matrix fixtures, new/legacy mapping and duration edge cases. |
| 2 | `dcffc59` | Exact approved basis and measurement hierarchy; structure/context tests. |
| 3 | `7841d09` | Private append-only contracts, atomic RPC design and migration static tests. |
| 4 | `06dc572` | Activity integration, explicit performed duration, qualitative feedback and API/mobile tests. |
| 5 | `11fd9dd` | Original-basis corrections, duplicate/response-loss recovery and selection-off readers. |
| 6 | `dab8777` | Explicit skip/unknown, weekly completeness and stale-safe API/mobile confirmation. |
| 7 | `fce4949` | Planning consumer contracts, evidence-bound proposals, multi-week and A9 parity tests. |
| 8 | `f109856` | Versioned Python/API/mobile guidance; historical catalog/calibration compatibility. |
| 9 | `a009613` | Final regressions, catalog inventory, SQL refinements, specification and performance evidence. |

## Approved decisions D01–D18

| Decision | Implemented behavior |
| --- | --- |
| D01 | Exact additive clamp, 25 literal factor fixtures; both -3 cells become 0.625. |
| D02 | P*A*F/T with uncapped duration ratio and no final cap; exact context result retained. |
| D03 | Every segment in the approved occurrence must have the same explicit zone. |
| D04 | Mixed/ambiguous structures excluded; changed-duration numeric results retained but automatic use withheld without a reliability policy. |
| D05 | Existing observed/partial and approved mean-HR methods precede RPE; no new sport conversion, multiplication of measurements or full-session addition. |
| D06 | Actual duration starts empty and must be entered/confirmed; missing/zero/invalid time cannot create an estimate. Separate skip registration. |
| D07 | Explicit new mapping 1–2/3–4/5–6/7–8/9–10; RPE 3 becomes Z2 only in the new path. |
| D08 | Canonical current Session-RPE JSON integer validation; historical values and calibration input semantics retained. This is an engineering validation choice, not an additional owner scientific decision. |
| D09 | Original occurrence/revision/catalog/P/T/zone/method/version snapshot; corrections reuse that basis. |
| D10 | Authoritative occurrence completeness, explicit skip versus unknown, private subtotal distinct from nullable usable total. |
| D11 | Complete eligible mixed weeks may feed existing coefficients; incomplete evidence holds/fails closed for progression, debt and references. |
| D12 | Subjective RPE/fatigue remains independent; estimates cannot spoof measured-complete match/overshoot rules or approve a plan. |
| D13 | Explicit Decimal 50-digit half-even divide-last policy; no intermediate quantization or display-rounded threshold decisions. |
| D14 | Explicit method/version dispatch and immutable history; unsupported combinations fail closed. |
| D15 | No automatic late replacement; preserve source records and withhold unresolved weekly use. |
| D16 | New calculation and weekly consumer versions, separate private records, four forward-only unapplied migrations. |
| D17 | No provider load conversion or arbitrary brick splitting; unsupported source identities remain ineligible. |
| D18 | Unvalidated heuristic wording, private numeric boundary and independent scientific/release gates recorded accurately. |

The [decision register](../requirements/JOREN_REALIZED_TSS_DECISION_REGISTER.md)
and [change log](../requirements/JOREN_REALIZED_TSS_V2_CHANGELOG.md) distinguish
old/new rules, effective version, reason, historical impact and related tests.

## Arithmetic, mapping and duration

`backend/app/modules/physiology/realized_v2.py` has no FastAPI, database, Supabase
or LLM dependency. `rpe_zones.py` explicitly dispatches new Session-RPE mapping
by `joren-realized-tss-matrix-2`; historical default helpers keep RPE 3 in Z1.
Calibration-block RPE and existing catalog/protocol prescriptions are unchanged.

`F = max(0.600, min(1.250, 1 + 0.125*(reported_zone-planned_zone)))`

`E = planned_load * actual_minutes * F / planned_minutes`

| Planned / reported | Z1 | Z2 | Z3 | Z4 | Z5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Z1 | 1.000 | 1.125 | 1.250 | 1.250 | 1.250 |
| Z2 | 0.875 | 1.000 | 1.125 | 1.250 | 1.250 |
| Z3 | 0.750 | 0.875 | 1.000 | 1.125 | 1.250 |
| Z4 | 0.625 | 0.750 | 0.875 | 1.000 | 1.125 |
| Z5 | 0.600 | 0.625 | 0.750 | 0.875 | 1.000 |

All 25 values are independent literal test fixtures, with independent full/half
load expectations and both scores for each reported zone. Tests cover all ten
RPE scores, historical RPE 3, invalid input, half/equal/longer durations, uncapped
results and ambient Decimal context independence. The three required synthetic
private examples return **60, 131.25 and 75**. P1/T3/A1/F1.125 returns 0.375
without intermediate ratio rounding. No numeric value here is an athlete display.

Numeric policy is `decimal-50-half-even-divide-last-1`. Coefficients are exact
Decimals, final storage is unquantized context output, and original duration
numerator/denominator strings remain in provenance. PostgreSQL uses unscaled
numeric by design; actual storage parity remains a database execution gate.

The existing positive <=1440-minute duration API limit is preserved. Missing
planned/actual duration, zero denominator, invalid/nonfinite/negative values,
distance-only activities and unconfirmed planned prefills cannot fabricate an
estimate. The pure zero-P result is defined, but zero-P selection is disabled.
Any A!=T estimate is mathematically retained and marked
`duration_reliability_policy_missing` for automatic consumers. No reliability
cutoff or physiological threshold was invented.

## Catalog eligibility and source hierarchy

The actual accepted A9 full catalog was inspected using the same explicit-zone
predicate as the occurrence path. These are **structural candidates**, not a
claim that every persisted occurrence or performed workout is eligible:

| Sport | All current templates | Candidates | Immutable source rows / candidates |
| --- | ---: | ---: | ---: |
| Swim | 56 | 0 | 54 / 0 |
| Bike | 54 | 5 | 50 / 5 |
| Run | 52 | 5 | 50 / 5 |

Exact eligible source IDs are BIK-001..005 and RUN-001..005. The remaining
templates are mixed/non-zone prescriptions; distance-only swims also lack
duration. The corpus has 154 immutable source rows plus eight built-in templates.
An approved RPE-only projection does not acquire a zone from today's catalog.
Compatible planned provenance is the existing Phase 13 `planned_zone_minutes`
pair; historical `source_catalog_predefined_tss` /
`start23-source-catalog-v0.1` remains unsupported, without relabelling.

No validated power-/running-pace-/swim-pace-TSS converter exists in this codebase.
Existing observed zone bins, including partial/all-zero evidence, and the
existing approved mean-HR estimate keep their precedence/evidence requirements.
RPE fallback is separate, never added to or multiplied into those results.
Warm-up-only/skipped-hard-block and mixed-session tests preserve original
partial provenance. A measured result of 60 remains 60 despite reported RPE 9;
subjective exertion remains recorded independently.

## Weekly completeness and next-week consumers

Private v16 history supplies exact approved occurrence identities, recorded
activities, immutable calculation IDs and explicit skipped/unknown events.
Deterministic `weekly-registration-2` returns known subtotal, planned/completed/
skipped/unknown/pending/usable-measured/usable-estimated/partial-unavailable/extra
counts, method/version distribution, nullable planner-usable load, reason and
separate progression/volume-debt/intensity-debt/reference eligibility.

For 60 measured + 50 eligible estimated + one unknown, subtotal is 110 but usable
weekly load is NULL. Explicitly skipping the third can establish 110 when all
other evidence is eligible. Completed unavailable is never zero; missing is
never skipped. Unknown, pending, partial, wrong revision, source conflict and
unsupported method/version withhold automatic use. Activities belong to one
athlete-local week. Supported explicitly unplanned work is separate; unmatched
provider imports retain known observations but cannot prove distinct extra work.

Complete measured/eligible-estimated weeks may use the existing progression
rules. Incomplete evidence uses the existing planned hold/fail-closed behavior,
and ineligible weeks do not enter reference baselines or debts. RPE provides no
measured intensity minutes. Existing intensity coverage checks, injury, illness,
fatigue, recovery/taper guards, coefficients and athlete approval remain intact.
New pending plans freeze evidence; changed evidence is rejected at persistence
and activation rather than silently approving a stale recommendation.

Tests cover three consecutive new-policy weeks, ten adjacent historical planning
weeks, mixed complete/incomplete weeks, raw threshold boundaries, fatigue,
injury, sickness/recovery/taper precedence and unchanged A9 outputs/intermediates.

## Private persistence, corrections and API/mobile compatibility

New migrations, none applied:

1. `20261103134520_joren_realized_tss_v2_private_provenance.sql`: private input
   confirmations, append-only calculation revisions, original approved snapshots,
   versioned creation/context/completion RPCs.
2. `20261103135735_realized_v2_weekly_registration.sql`: append-only skipped/unknown
   events, caller/revision-safe confirmation, canonical activity conflict guard
   and v16 private history. Plan serialization uses NO KEY UPDATE to remain
   compatible with existing foreign-key KEY SHARE locks; concurrency is untested
   on PostgreSQL.
3. `20261103140959_realized_v2_planning_evidence_preconditions.sql`: immutable
   proposal evidence, v4 proposal precondition and activation stale guard.
4. `20261103142339_realized_v2_session_rpe_guidance.sql`: safe public version
   marker; Python supplies public exertion labels.

Existing Phase 13 load rows/constraints and applied migrations are not rewritten.
New tables use owner-composite foreign keys, forced RLS, no athlete table grants,
narrow service grants, fixed search paths, immutable guards and existing
account-deletion cascade conventions. These are design/static findings, not
executed security guarantees. The deferred pgTAP file prepares 22 assertions.

Corrections retain original planned basis, current-week/expected-score and HR
immutability rules. Same-score retry appends nothing. Unknown methods fail closed.
Selection-off retains readers/corrections for existing v2 records. Late-source
replacement is disabled; numeric conflicts preserve records without double count
and block automatic weekly use. Backend mocks and mobile response-loss tests
exercise stale revision, wrong owner, duplicates and recovery; live RPC atomicity
and races remain open gates.

Public activity DTOs gain safe version/guidance fields; caller-owned registration
GET/PUT carries only status and revision preconditions. Existing callers may omit
performed-duration confirmation, which means unconfirmed. Current Session-RPE
transport requires canonical integers; historical stored interpretations and
calibration remain unchanged. Mobile V1/V2 preserve their design, ask for actual
performed time, offer skipped/unknown actions and display server-owned new-version
labels. RPE 3 explicitly renders Zone 2 for v2. Old responses remain supported.
Previously prefill-dependent tests now enter actual minutes explicitly and retain
their original recovery/idempotency assertions.

Private numeric load, factor, ratio, subtotal and provenance are absent from
public DTOs, error details, UI/accessibility and LLM facts. OpenAPI/recursive
public-contract tests, private representation/validation regression and existing
mobile boundary tests pass. Internal numeric-bearing models suppress diagnostic
repr/input leakage. No secret or .env file was added.

## Complete software verification

Existing Python 3.10.10 virtualenv and installed mobile dependencies were reused.
No database tooling was installed. Verification was run against the final source
tree before its slice 9 commit; that commit changed no tested content afterwards.

| Check | Result |
| --- | --- |
| `python -m ruff check app tests benchmarks` | Passed |
| `python -m ruff format --check app tests benchmarks` | Passed, 161 files |
| `python -m mypy app tests` with repository strict configuration | Passed, 155 source files |
| `python -B -m pytest -q -p no:cacheprovider` | **1013 passed**, 160.46 s |
| `npm run typecheck` | Passed, strict TypeScript |
| `npm run check:unused` | Passed |
| `npm test -- --silent` | **83 suites / 892 tests passed**, 136.599 s |
| Four new migrations, SQL-language bodies and pgTAP syntax via existing pglast | Parsed; not PostgreSQL compilation/execution |
| Migration/grant/immutability/static contracts | Passed in backend suite |
| Original 129 fixture IDs and D01–D18 documentation rows | Retained and checked |
| Historical PDF SHA-256 and five archived review files | Original content preserved |

The backend emits one existing Starlette/httpx test-client deprecation warning.
The full suites cover OpenAPI/private-load boundaries and A3–A9 injury, Week/
Calendar, proposal/account recovery, activity/RPE synchronization, auth/network/
idempotency and performance-parity regressions. Unit/mocked integration tests do
not replace real-token/device or database verification. Historical archived files
retain their original trailing blank lines; they were not reformatted for lint.

Machine-readable summary: [software-verification.json](evidence/joren-realized-v2/software-verification.json).

## Performance compared with A9

Benchmarks ran sequentially on this Windows machine, three samples per case,
using the same full catalog. Baseline was exact accepted A9 in its existing
worktree; after was the final v2 implementation tree. Catalog, scenario input,
output and intermediate trace hashes are identical in all five historical cases.
The benchmark serializer omits only the newly additive, absent registration field
for historical fixtures; populated new evidence remains part of fingerprints.

| Historical scenario | A9 median ms | V2 median ms | Difference |
| --- | ---: | ---: | ---: |
| run_history | 94.781 | 96.002 | +1.29% |
| tri_balanced | 3475.799 | 3607.629 | +3.79% |
| build_week | 11.628 | 11.050 | -4.97% |
| restriction | 0.094 | 0.092 | -1.39% |
| recovery_week | 3.265 | 3.679 | +12.65% |

These small local samples show timing variation, including a 0.413 ms recovery
increase; they do not establish a production SLA or statistically exclude
regression. The pure calculator takes approximately 7.43/8.37/8.14 microseconds
per call across three 10,000-call samples. It does no catalog search or I/O.
The existing planning process worker and bounded planning algorithm remain.

Authenticated Calendar reads while a real ASGI proposal ran, concurrency one:

| Measure (three samples) | A9 | V2 |
| --- | ---: | ---: |
| Calendar wait median / maximum ms | 25.010 / 27.062 | 24.933 / 28.980 |
| Scheduler delay maximum ms | 10.481 | 10.569 |
| Proposal duration median s | 5.279 | 5.468 |
| HTTP outcomes | 3x201 proposal; 3x200 read | 3x201 proposal; 3x200 read |

This exercises the existing event-loop isolation with synthetic repositories,
not hosted SQL latency or production traffic. Reproduction from each backend:

```text
python -B -m benchmarks.planning --runs 3 --output ../.runtime/a9.json
python -B -m benchmarks.responsiveness --operation proposal --counts 1 --runs 3 --output ../.runtime/responsive.json
python -B -m benchmarks.realized_v2 --iterations 10000 --output ../.runtime/v2.json
```

Evidence: [A9 before](evidence/joren-realized-v2/a9-before.json),
[after](evidence/joren-realized-v2/a9-after.json),
[responsive before](evidence/joren-realized-v2/a9-responsive-before.json),
[responsive after](evidence/joren-realized-v2/a9-responsive-after.json),
[calculator/catalog](evidence/joren-realized-v2/realized-v2-benchmark.json).

## Documentation custody and updates

Current authoritative documents are the new approved specification and updated
[formal model](../requirements/JOREN_REALIZED_TSS_FORMAL_MODEL.md),
[integration review](../requirements/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md),
[decision register](../requirements/JOREN_REALIZED_TSS_DECISION_REGISTER.md),
[implementation plan](../requirements/JOREN_REALIZED_TSS_IMPLEMENTATION_PLAN.md),
[129-fixture matrix](../requirements/JOREN_REALIZED_TSS_TEST_MATRIX.md) and
[change log](../requirements/JOREN_REALIZED_TSS_V2_CHANGELOG.md).

Scoped v2 amendments and top-level authority notices were added to the MVP
roadmap, Phase 13 ruleset, physiology formula specification, business traceability,
Decisions, Vereisten, API contracts, domain model, backend architecture, security
model, database migrations, backend zone calculation, Joren planning ruleset v2
and backend README. They explicitly retain historical-version material while
linking the effective v2 behavior and gates.

The unchanged v1.0 PDF is 180537 bytes, SHA-256
`b31f7fd72ebdda6f54f87fc5f25b69e53600f3476f5572d5e75af48615aef194`.
All five original review documents are preserved in
`docs/requirements/history/joren-realized-tss-review-1/`. Old -3 cells at 0.600
and old RPE 3 semantics are **SUPERSEDED FOR THE NEW VERSION**, not erased from
historical evidence. The 129 original IDs remain an inventory mapped to executable
families/disabled boundaries; this is not a claim that 129 PostgreSQL fixtures ran.

## Disabled boundaries and open gates

- Changed-duration automatic use has no approved reliability policy. Exact
  estimates remain private, with ineligible provenance. No cutoff was invented.
- Mixed/ambiguous, protocol/RPE-only, unmatched or unsupported planned bases,
  zero-P selection, distance-only duration fabrication, brick splitting, new
  provider/power/pace conversions and automatic late replacement remain disabled.
- Estimates do not drive existing measurement-only overshoot/perfect-match rules.
- Storage readiness and selection default false; selection requires readiness.
  Configuration rejects staging/production readiness while release gates are open.
- **PostgreSQL/pgTAP DEFERRED BY OWNER — PRE-BETA**: fresh/upgrade replay, function/
  trigger compilation, forced-RLS/grants/owner separation, account deletion,
  actual numeric storage, RPC retries/concurrency, skip/activity serialization,
  and evidence-bound stale activation must run on PostgreSQL before release.
  Prepared pgTAP assertions and parser checks are not substitutes.
- Qualified scientific review and accountable release sign-off remain open for
  this exact heuristic/version; no reviewer signature or validation is fabricated.
- Real-token hosted integration and real-device visual/workflow verification,
  plus representative deployed SQL/performance assessment, remain release gates.

No push, merge, deployment or hosted schema activation was performed.
