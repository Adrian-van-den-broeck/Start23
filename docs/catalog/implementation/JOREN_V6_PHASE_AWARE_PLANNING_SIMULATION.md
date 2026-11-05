# V6 phase-aware planning simulation

2026-11-05, Europe/Amsterdam. Private source arithmetic and synthetic review
evidence. No actual athlete suitability, automatic recommendation or activation.

Actual inputs are the 77 revisions in [source intake](JOREN_V6_PHASE_SOURCE_INTAKE.md).
[simulation.json](phase-tss/simulation.json) records all one-per-sport combinations
and disabled review results. [phase-search.json](phase-tss/phase-search.json) records
20 serial bounded runs of the existing validated planner/search with the real new
phase projection. Both preserve source load as explicitly hypothetical while the
official authority binding is open. No modified search score or larger deadline.

## Source-only arithmetic, independently recomputed

| Phase | Authorized budget | Phase-allowed RUN/BIKE/SWIM rows | One-per-sport combinations at/below budget |
| --- | ---: | --- | ---: |
| Base | 45 | 22 / 23 / 16 | 10 |
| Build | 45 | 22 / 27 / 22 | 10 |
| Recovery | 25.86 | 18 / 13 / 8 | 0 |
| Taper | 15.085 | 18 / 19 / 8 | 0 |

Membership comes only from column P. Combinations include all phase-allowed rows,
not a title/intensity-inferred subset. Results use source-display exact rational
sums; they are not official-method, duration, injury, capability or schedule proofs.
The minimum phase-allowed Base/Build triple is BIKE-022 + RUN-025 + SWIM-021 = 34.3.
Recovery/Taper permit lighter RUN-021 but their budgets remain independently lower.
No recovery/taper comparison uses a universal 45 ceiling.

## Required witnesses and actual phase eligibility

All source IDs below carry the `TR-` prefix. Row-specific full phase text is in
the source artifact; no label is changed to preserve an old witness.

| Witness | BIKE / RUN / SWIM | Base | Build | Recovery | Taper |
| --- | --- | --- | --- | --- | --- |
| Manual 43.1 | 023 / 024 / 021 | disallowed | disallowed | allowed | allowed |
| Allocation-oriented 40.2 | 023 / 023 / 021 | disallowed | disallowed | allowed | allowed |
| Utilization-oriented 44.8 | 023 / 026 / 021 | allowed | allowed | allowed | allowed |
| Legacy automatic 45.1 | 022 / 027 / 021 | allowed | allowed | allowed | allowed |

“Allowed” means source phase membership only. None is a suitable approved plan.
43.1 and 40.2 still exceed the actual recovery/taper budgets. 45.1 fails the
prospective 45 ceiling by .1. Exact-budget tests pass at 45.1 when that is explicitly
the authorized budget, and fail at an arbitrarily smaller exact finite decimal.
The retained-week test deducts a 20.2 occurrence before additions: 24.8 remains,
and the complete 44.8 source-display witness leaves .2 of the 45 budget.

## Disabled integration scenarios

| Scenario | Verified property / boundary |
| --- | --- |
| Zero-history triathlon, 45 | Source arithmetic has ten Base and ten Build triples; existing phase-projected legacy engine returns 45.1; new review rejects the overshoot |
| Source-filtered Base/Build | Exact new phase tuples enter the diagnostic projection; RUN-017/018 stay Base-only; RUN-021:024 excluded from Base/Build |
| All-easy BUILD | Supplied 44.8 phase-valid witness has zero HIGH and passes the maximum; no minimum or Z5 mandate in the new review |
| Historical all-easy fixture | Existing fixture used RUN-024, so the new phase projection rejects it as `template_not_eligible`; old corpus retains its original outcome |
| Exactly 20% / above 20% | Independently prescribed synthetic SWIM segment times pass exactly 20%, reject 20.0001/(80+20.0001); source reference estimate remains separate |
| Mixed zones | RUN-017 preserves all mixed segments, 1800/3600 HIGH active seconds and rejects its single-session 50% week; whole-session focus never substitutes |
| Estimated distance-only SWIM | All 22 retain source meters, missing individualized T, full rest events and estimator provenance; authoritative compliance stays UNVERIFIED |
| Three/two/one/zero disciplines | Separate conditional contract tests; 44.8 Build triple, 20.9 recovery BIKE-022/RUN-021 pair, 5.8 taper RUN-021 singleton and empty zero-budget/rest week |
| No safe candidate | Empty/zero outcome carries no recommendation; blocked safeguards cannot be converted to permission; historical all-injured diagnostic returns zero workouts |
| Injury/recovery/progression/capability | Each dimension separately tested missing and blocked, using scope-bound TEST_ONLY evidence; actual injury and missing-swim-capability diagnostics retain fail-closed results |
| Availability/scheduling | Unavailable dates reject; scheduling evidence is independently required, not inferred from date membership; no minute capacity is invented |
| Repeat-limited templates | Distinct occurrence IDs retained; supplied revision-specific maximum-use limit rejects excess; duplicate occurrence identity rejects |
| Long-duration risk | Seven-hour BIKE-013 fits a hypothetical 500 budget but missing duration-distance evidence stays unresolved; legacy long-only fallback remains observable, never endorsed |
| Single-sport goals | Existing run/bike/swim diagnostics use actual phase projection; new review rejects outside-goal sport, and triathlon allocation is not imposed on single-sport scope |
| Existing history/future weeks | Four BUILD diagnostic weeks retain the existing history/target resolver. Full historical A9 adjacent-week and V6 registration/progression tests retain their original assertions; no new official-load progression is claimed |
| Athlete/revision isolation | Guard-evidence fingerprints reject changes to athlete, revision, budget, week, phase, dates, occurrence or prescribed-time provenance |
| Partial alternatives | Permission is implemented as a review contract; no arbitrary sport-removal order, renormalized target, ranking winner or automatic partial recommendation |

The conditional 3/2/1 tests assume individually scoped safety/scheduling evidence
marked TEST_ONLY. They test software contracts, not physical readiness or actual
safe scheduling. New real catalog rows lack that individual evidence. The zero
case and blocked cases remain fail-closed with no selected recommendation.

## Legacy-search evidence with actual phases

The existing optimized search is invoked unchanged, using the same eight-second
including-imports subprocess bound. The new projection changes only source phase
tuples and revision identity, while full source/rest/guidance stays in the sidecar.
The legacy template type folds rest text into instructions for diagnostic use;
it is not the prepared C3 typed-rest snapshot or an operational ingestion format.

All four V6 phase-projected BUILD searches complete. First three select 550.0
with SWIM-010/RUN-003/SWIM-014/BIKE-011/RUN-012; week four selects 550.0 with
BIKE-011/SWIM-006/BIKE-020/RUN-010. This proves execution of existing search,
not compliance with the prospective active-time policy or individual suitability.
Legacy bike-only/repeat examples can exceed 45, and the long-only fallback can
return 393.8. Those observations demonstrate why historical search outcomes must
not be published as prospective recommendations.

P01 and allocation/tie authority prevent an automatic prospective selection.
The owner has requested a TSS proposal **without implementation**; see the
[concrete proposal](JOREN_V6_OFFICIAL_TSS_METHOD_APPROVAL.md#concrete-proposal-requested-by-the-owner--no-implementation).
No mathematical combination, conditional review result or diagnostic plan is
declared athlete-suitable or automatically scheduled by the new integration.
