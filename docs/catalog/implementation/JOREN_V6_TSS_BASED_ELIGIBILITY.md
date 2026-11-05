# V6 TSS-based eligibility contract

2026-11-05, Europe/Amsterdam. Decision `joren-v6-phase-tss-owner-intake-1`;
inactive review path `joren-v6-phase-tss-review-1`.

## Owner-confirmed product decisions

Eligibility uses Joren's new source phases, official planned load when its exact
authority is bound, and the athlete's existing authorized weekly budget. There
are no beginner/intermediate/advanced categories or required source labels.
The example 45-TSS starting week is a budget, not an athlete category. Historical
draft fields remain only inside explicitly provisional predecessor evidence;
the new eligibility contract never consumes them.

The authorized weekly budget is a hard ceiling, compared without presentation
rounding. Existing retained occurrences consume capacity before additions and
participate in the per-sport weekly intensity denominator. No per-sport cap is
inferred from the soft BIKE/RUN/SWIM 50/30/20 target. No full-budget utilization
is required. Recovery at 25.86 and taper at 15.085 use their own budgets.

Prospective priority: safety/restrictions, hard weekly ceiling, suitable coverage
where feasible, allocation closeness, utilization, deterministic tie-breaking.
Three, two, one and zero sports are distinguished. Permission for partial weeks
does not choose a sport to omit or authorize a ranking between safe alternatives.

There is **no HIGH minimum**, including BUILD and Z5. The per-sport athlete-local
Monday–Sunday maximum is exactly 20% HIGH active time. Z1/Z2 LOW; Z3–Z5 HIGH.
Rest has zero active time. All-easy BUILD is permitted by this rule. Historical
whole-workout minima, Z5 requirements, score, tolerances and search remain unchanged.

## Implemented inactive seam

`app/modules/planning/v6_phase_review.py` reviews an explicitly supplied complete
week. It has no FastAPI route, repository, settings flag, activation argument,
winner or persistence operation. All results have `operational_approval = false`
and `selected_recommendation = null`. Missing official numerical authority is a
fixed gate that callers cannot clear with an approval boolean.

While P01 is open, arithmetic is explicitly labeled
`hypothetical-source-display-exact-rational-1`. It never pretends to be the official
method or changes active loads. Exact rational sums/comparisons reject 45.1 at 45,
including in a low caller Decimal context; exact equality passes.

Each occurrence retains its distinct occurrence ID, exact immutable source/template
revision and local date. Phase filtering uses only column P on new proposals;
historical retained occurrences are not reclassified. Missing dates, outside-goal
sports and supplied repeat-limit violations reject. Duplicate occurrence IDs
reject while valid repeated templates remain distinct occurrences.

Required safeguard dimensions are injury, recovery, progression, duration/distance,
sport capability, scheduling and occurrence restrictions. Evidence must identify
the rule/reference and match a SHA-256 scope covering athlete identity, expected
revision, exact budget, local week/phase, goal sports, dates, retained/proposed
occurrences and independent prescription provenance. Missing evidence stays
unresolved; blocked evidence rejects. These are review evidence contracts, not
a claim that the new seam computes or approves the existing safeguards.

Existing verified-token identity, pending proposal/athlete confirmation, optimistic
concurrency, idempotency, isolation and existing restrictions remain owned by the
unchanged application/persistence path. No new unverified writes bypass them.
The future adapter to those existing safety results remains a concrete integration
gate. Tests use explicitly `TEST_ONLY` scoped evidence and never establish real
individual readiness for catalog workouts.

## Allocation metric and selection gate

The review-only diagnostic `review-only-selected-total-share-l1-1` is
`SUM_s ABS(selected_load_s / selected_total - target_share_s)` with exact fractions,
BIKE .50/RUN .30/SWIM .20. It is undefined at total zero, and not applicable to
single-sport goals. Missing sports contribute share zero; targets are not
renormalized. No fitness, scoring weight, allowance or safety threshold follows.

This explicit metric is an engineering review candidate, **not approved selection
authority**. No option is sorted by it into a recommendation. Metric choice,
residual ties and ranking among competing partial plans remain open. The existing
validated optimized search is reused only in labeled legacy diagnostics with the
real new phase projection; its historical scoring cannot silently become the
prospective selector. A new automatic selector is intentionally blocked here.

## Duration and swimming boundaries

A fitting TSS total does not establish readiness for a duration/distance.
TR-BIKE-013 retains 420 minutes and source Taper permission. Even at budget 500,
missing `duration_distance` evidence is unresolved. No medical rule, arbitrary
duration cap or athlete-level label substitutes for that evidence.

C5 shares the unchanged versioned reference estimator with the prior offline
import path. Original source meters, estimated active minutes, independently
prescribed segment seconds and actual observations remain distinct. The review
reports both reference-estimated compliance and authoritative-duration compliance.
Supplying separately attributable prescribed times does not overwrite the source.
Estimated compliance never becomes authoritative verification; operational use
requires an explicit acceptance decision. No estimated time enters Realized V2.
