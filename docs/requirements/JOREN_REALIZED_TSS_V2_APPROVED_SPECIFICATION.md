# Joren Realized TSS v2 - approved product specification

Effective calculation: `joren-realized-tss-matrix-2`.
Weekly consumer policy: `weekly-registration-2`.
Product authority: the owner's explicit WOMBO implementation instruction of
2026-11-03. This is product approval, not an independent scientific signature.
The multiplier is a reasoned, unvalidated heuristic. Qualified scientific and
release review remain open. All numerical examples in this document are private
synthetic developer fixtures, never athlete displays.

## Scope and activation

The software extends the accepted cumulative A9 head
`e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`. It does not change Phase 13
zone-minute coefficients, mean-HR evidence requirements, calibration anchors,
onboarding baseline, injury restrictions, planning coefficients or taper rules.
Historical interpretations, calculations and approved revisions remain under
their original method/version. There is no backfill or historical recalculation.

`START23_REALIZED_V2_STORAGE_READY=false` and
`START23_REALIZED_V2_SELECTION_ENABLED=false` are the defaults. Selection requires
the storage contract. Both are local/test preview settings; storage readiness is
rejected on staging and production while database/release gates remain open.
No environment is enabled by this implementation. With storage readers retained,
turning selection off prevents new selection and preserves corrections/readers
for existing v2 records. Do not remove storage readers after creating v2 data.

The original `Specificatie Realized TSS Matrix.pdf`, v1.0, is historical evidence.
Its SHA-256 remains
`b31f7fd72ebdda6f54f87fc5f25b69e53600f3476f5572d5e75af48615aef194`.
The [earlier review archive](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md)
retains the original discrepancy and unapproved-proposal history.

## D01/D02/D07/D13 - arithmetic and scale

Let P be the exact approved occurrence's private planned load, T its planned
minutes, A explicit confirmed performed minutes, p the approved single zone,
and r the integer Session-RPE. New reported zone q is:

| Session-RPE | Reported zone |
| --- | --- |
| 1-2 | Z1 |
| 3-4 | Z2 |
| 5-6 | Z3 |
| 7-8 | Z4 |
| 9-10 | Z5 |

`F = max(Decimal('0.600'), min(Decimal('1.250'), 1 + Decimal('0.125') * (q-p)))`

`E = P * A * F / T`

| Planned / reported | Z1 | Z2 | Z3 | Z4 | Z5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Z1 | 1.000 | 1.125 | 1.250 | 1.250 | 1.250 |
| Z2 | 0.875 | 1.000 | 1.125 | 1.250 | 1.250 |
| Z3 | 0.750 | 0.875 | 1.000 | 1.125 | 1.250 |
| Z4 | 0.625 | 0.750 | 0.875 | 1.000 | 1.125 |
| Z5 | 0.600 | 0.625 | 0.750 | 0.875 | 1.000 |

The PDF's Z4/Z1 and Z5/Z2 cells used 0.600 for a difference of -3.
Consistent additive steps give 0.625; the 0.600 floor applies only at -4.
Those cells are **SUPERSEDED FOR THE NEW VERSION**. The historical PDF is unchanged.

Arithmetic uses an explicit Decimal context of 50 significant digits,
ROUND_HALF_EVEN, default Decimal context exponent bounds/traps, exact decimal
coefficients and a divide-last expression. Policy identifier:
`decimal-50-half-even-divide-last-1`. This precision is an implementation
reproducibility choice under D13, not a physiological constant. Neither factor
nor ratio is quantized. Storage retains the context result as an unscaled
PostgreSQL numeric sent as a decimal string; repeating quotients are therefore
reproducible finite-context results, not claims of infinite precision.
The original A and T strings remain the exact ratio numerator/denominator.
New weekly aggregation/target consumers use 50-digit arithmetic; historical
consumer calls retain their prior context. No display rounding enters a
threshold comparison. No numeric private load is displayed in mobile.

The ratio is uncapped and no final load cap is added. Examples:

- A: P120, T120, A60, p2, r3 -> q2, F1.000, E60.
- B: P100, T60, A90, p2, q1 -> F0.875, E131.25.
- C: P120, T120, A120, p4, q1 -> F0.625, E75, not 72.
- P1, T3, A1, p1, r3 -> E0.375; no intermediate ratio rounding.

Missing P/A/T is unavailable, never neutral or zero. Nonfinite/negative values
are rejected; T=0 and A=0 do not enter the calculator. Pure zero-P arithmetic is
defined, but zero planned load is conservatively ineligible for selection.
Completed activity duration retains its existing positive, <=1440 minute,
max-eight-digit API contract. A skipped workout is a separate registration.
Distance-only swims retain distance; duration is never inferred.

## D03/D04/D06/D09 - evidence and exact identity

The private processing context snapshots plan ID, revision ID/number, exact
planned-workout row ID (occurrence), immutable template ID/version, source catalog
and workout ID, original P/T, planned method/version and ordered segments.
An already selected calculation retains its original planned snapshot on edits.
The current catalog is never used to replace the accepted prescription.

Eligibility requires every segment in that approved snapshot to have the same
explicit zone. Canonical `zone_target` and the historical explicit `zone` spelling
are recognized; contradictory fields fail closed. No zone is inferred from
low/high classification, expected/reported RPE, a maximum/longest interval,
weighted average, current template, RPE-only target or protocol target.
Compatible planned provenance is Phase 13 `planned_zone_minutes`, including
the existing persistence label for retained source loads. Historical
`source_catalog_predefined_tss` / `start23-source-catalog-v0.1` combinations
remain ineligible; no new method/version combination is invented.

Mixed sessions, warm-up-only/skipped-hard-block ambiguity, bricks, unmatched
plans and unsupported planned versions cannot use the whole-session matrix.
Observed methods remain available for these workouts when their own evidence
is sufficient. Each independently supported component retains its own identity.

Mobile leaves actual duration empty at initial entry, after selecting a plan or
outside activity, and after a saved activity. Entering performed minutes and
saving explicitly confirms them via `performed_duration_confirmed`. API callers
omitting that strict boolean remain compatible but do not establish confirmation.
Existing records are not backfilled as confirmed. No sport watch is required;
the existing onboarding monitor and assigned-workout HR requirements are retained.

Any A != T result is calculated/stored exactly but is **not automatically
planner-eligible**: reason `duration_reliability_policy_missing`. No numerical
reliability cutoff was supplied. This conservative disabled boundary covers
shortened as well as extended sessions; a future versioned policy is required
to relax it. Uniform confirmed A=T estimates can be eligible.

## D05/D12/D15/D17 - selection and subjective feedback

1. Use a reliable implemented sport measurement method if one exists. This
   repository has no validated power-/running-pace-/swim-pace-TSS converter.
2. Retain existing observed zone load, including partial observations, then
   approved mean-HR estimates under their existing run/bike/profile precedence.
3. Only otherwise unavailable, eligible planned occurrences may select v2 RPE.
4. Otherwise retain unavailable load and independent subjective feedback.

Explicit bins, including all-zero arrays, retain their existing semantics.
An RPE estimate never overwrites or fills a partial observation; measured and
estimated full-session results are never added. A measured 60 remains 60 when
RPE changes from 5 to 9. RPE remains recorded as an independent fatigue signal.
Mean-HR and RPE estimates are not measured-complete evidence. The existing
low-workout/high-RPE fatigue signal remains; measurement-only perfect-match and
overshoot thresholds do not consume RPE estimates. Every plan change is pending.

Automatic replacement by late better evidence is disabled. A conflicting numeric
observation and historical estimate block automatic weekly use, preserving their
records without addition. Unmatched provider imports cannot establish distinct
extra work; their known observed value remains private but weekly automatic use
is withheld until identity is resolved. No time-overlap threshold is invented.
Manual explicitly unplanned activities may contribute supported existing loads.
No Garmin/Strava/new Polar conversion or brick splitting is implemented.

## D08/D14/D16 - transport, persistence and corrections

Current Session-RPE submissions require a JSON integer 1-10; booleans, numeric
strings and floats are rejected. The former Pydantic coercions are not part of
the new canonical transport contract. This fail-closed validation choice changes
new submissions, not historical scores or calibration-block contracts. The
published integer contract and existing integer mobile clients remain compatible.

Four forward-only local migrations add private input confirmations, append-only
calculation revisions, append-only skipped/unknown events and immutable planning
evidence snapshots, plus versioned RPCs/readers. They leave existing Phase 13
load constraints and calculation rows intact. Owner-composite foreign keys,
opaque-owner synchronization, forced RLS, narrow grants, fixed search paths,
immutable guards and existing account-deletion cascades are preserved.

The atomic completion wrapper locks the canonical activity, invokes validated
existing observation/RPE operations and appends one separate fallback assessment.
Same-score response-loss retries append nothing. Corrections retain current-local-
week and expected-current-RPE checks, immutable HR evidence, prior snapshots and
the original occurrence basis. Unknown method/version combinations fail closed;
an unequal version is never automatically treated as retired RPE-times-hours.
The existing legacy and Phase 13 correction implementations remain readable.

## D10/D11 - complete weekly registration and planning

v16 supplies authoritative expected occurrence IDs from the exact approved
revision, activity evidence and explicit skip events. v13-v15 historical readers
remain available. Deterministic Python evaluates `weekly-registration-2`.
An activity is assigned to its own athlete-local week once. Wrong-revision or
cross-week occurrence mismatches withhold automatic use; they are not rematched.

Private `WeeklyCompleteness` contains known subtotal, planned count, performed
planned count, explicit skipped count, unknown count, pending feedback count,
usable measured/estimated counts, partial/unavailable count, supported extra
count, method/version distribution, immutable calculation/event IDs, nullable
planner-usable total, reason and separate consumer eligibility fields.
Performed count includes recorded planned activities awaiting feedback;
extras are counted separately. A null/partial/ineligible result never means zero.
The empty numeric subtotal is zero as an arithmetic identity, with eligibility
still false when registration is unknown. An approved rest-only week or an
explicitly all-skipped occurrence set can establish zero performed load.

For 60 measured + 50 eligible estimated + one unknown occurrence: known subtotal
110, unknown count 1, usable total NULL. Explicitly skipping the third occurrence
can make 110 usable, subject to other evidence checks. Missing feedback,
incompatible/partial evidence, unresolved source identity and unknown expected
occurrences withhold progression, volume debt, intensity debt and reference use.

Complete weeks may combine measured, approved mean-HR and eligible RPE estimates.
Incomplete weeks use the existing planned hold/fail-closed route; they cannot
grow from a low subtotal. Existing sickness exclusion, injury restrictions,
fatigue, maintenance, recovery, taper and athlete approval retain their priority
and constants. Intensity debt still requires existing observed/classified minute
evidence and its existing coverage rule; Session-RPE produces no zone minutes.
New pending plans freeze the exact v16 evidence and calculation IDs. Persistence
checks it against current evidence; activation rejects changed evidence as stale.
Already-approved plans and identical applied retries are not rewritten.

## Public/private contract and release gates

Athlete APIs expose only completed activity facts, qualitative outcomes,
`session_rpe_version` (`legacy` or `2`), public per-score zone labels, and
registration status/revision preconditions. GET/PUT
`/api/v1/planned-workouts/{workout_id}/registration` has no load fields.
No P/E, subtotal, factor, ratio, private evidence or eligibility details enter
public DTOs, UI/accessibility, logs, telemetry or LLM facts.

PostgreSQL/pgTAP is **DEFERRED BY OWNER - PRE-BETA**, not passed. Required gates
include upgrade/fresh replay, actual function/trigger compilation, owner/grant/RLS
and account-deletion behavior, RPC concurrency/idempotency, numeric storage parity,
stale planning approvals, real-token and device workflows, plus qualified
scientific/release review for the exact heuristic scope. No tooling is installed
solely for database testing, no migration is applied, and no push/merge/deployment
is part of this implementation. See the
[implementation report](../implementation/JOREN_REALIZED_TSS_V2_IMPLEMENTATION_REPORT.md)
and [129-fixture inventory](JOREN_REALIZED_TSS_TEST_MATRIX.md).
