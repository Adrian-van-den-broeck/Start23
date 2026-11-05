# V6 strict-budget feasibility experiment

2026-11-05, Europe/Amsterdam. Private offline evidence; inactive.

## Convention and scope

CONFIRMED JOREN RULE: the existing zero-history baseline remains 45.0 and the
desired first triathlon week has one suitable workout per sport where feasible.
PROPOSED PRODUCT POLICY: treat an explicitly authorized weekly budget as a hard
ceiling. This experiment does not approve that operational change or apply 45
to experienced athletes, historical plans or every later week.

NUMERICALLY RECONSTRUCTED METHOD:
`hypothetical-v6-displayed-source-p-exact-decimal-1` constructs Decimal values
directly from `load.original_displayed_value` strings on the pinned V6 records.
For example `Decimal("15.1")`, not a binary float and not unrounded IF² output.
These displayed-source decimals are treated as exact **hypothetical inputs**.
This does not establish that workbook display precision is the authoritative
source-P precision, approve Z3=.88/swim reference paces, or set operational P.
Original raw numeric lexemes and every source/method version remain intact.

The evaluator sums aligned integer Decimal coefficients and constructs the exact
result without depending on the ambient Decimal precision/rounding/traps. Remaining
budget = authorized budget minus selected total; negative means exceeded. Shares
and deviations use exact Fraction arithmetic. No quantization or display rounding
is performed before comparisons. Labels and data are server-private.

## Actual selected outcomes versus witnesses

All rows below have the `TR-` source prefix. BIKE/RUN/SWIM is the column order.

| Origin | Source IDs | Exact private components | Total | Budget remaining | Result |
| --- | --- | --- | --- | --- | --- |
| Actual automatic unchanged planner | BIKE-022 / RUN-027 / SWIM-021 | 15.1 / 21.6 / 8.4 | 45.1 | -0.1 | LEGACY_VALID + PROSPECTIVE_BUDGET_EXCEEDED |
| Actual explicit manual submission | BIKE-023 / RUN-024 / SWIM-021 | 20.2 / 14.5 / 8.4 | 43.1 | 1.9 | LEGACY_VALID + PROSPECTIVE_BUDGET_WITHIN |
| Offline allocation-first witness, separately tested as explicit submission | BIKE-023 / RUN-023 / SWIM-021 | 20.2 / 11.6 / 8.4 | 40.2 | 4.8 | Mathematically feasible; not automatically selected by active planner |
| Offline utilization-first witness, separately tested as explicit submission | BIKE-023 / RUN-026 / SWIM-021 | 20.2 / 16.2 / 8.4 | 44.8 | 0.2 | Mathematically feasible; not automatically selected by active planner |
| Mathematical minimum | BIKE-022 / RUN-021 / SWIM-021 | 15.1 / 5.8 / 8.4 | 29.3 | 15.7 | Within budget; actual explicit legacy submission rejected |

TESTED OFFLINE BEHAVIOR: the automatic result is reproduced from the actual
77-workout projected deck, with no selected-template input. The manual 43.1
witness is reproduced using explicitly selected IDs. Neither is hardcoded as a
default. The two alternative ranking winners are output by complete enumeration,
and their explicit legacy submissions pass; this does not make them automatic
active-planner results.

ACTIVE PRODUCTION BEHAVIOR: historical fit is `abs(target-total) < minimum_load`.
Here the eligible minimum is 5.8, so a 0.1 overshoot passes legacy selection.
For under-budget candidates this gives the open lower boundary `total > 39.2`.
The 29.3 minimum fails; it is not a legacy valid plan just because it is under 45.
Other phase/high-load/scheduling/restriction rules are not replaced by this scalar
fit diagnostic. No change is made to the active predicate or long-session fallback.

UNAPPROVED ATHLETE METADATA: every real-row witness lacks approved suitability;
SWIM-021 has no active-time denominator and stays UNVERIFIED. None is an approved
beginner prescription or proof of physical readiness.

## Complete independent feasibility

The full actual provisional deck contains BIKE 27, RUN 28 and SWIM 22. Exactly
one occurrence per sport produces **16,632** combinations. Complete enumeration
finds **33** totals <=45. The separately filtered all-easy deck has **5,016**
combinations and finds exactly the same 33. Thus no mixed-zone combination adds
a within-budget witness under this candidate constraint. Of those 33, **23**
also pass the unchanged scalar legacy target-fit condition; ten underfill too far.
The maximum total is 44.8; no exactly-45 one-per-sport combination exists.

An independent nested-loop oracle reads source-display strings directly and sums
exact rational values. It does not call the sandbox sum, search, scoring or
legacy predicate. Full source-ID sets are equal in both all-77 and all-easy
experiments. This establishes mathematical feasibility without claiming that
every combination was automatically selected, scheduled or suitable. The complete
33-entry set, UUID tie identities and scores are in
[private experiments](policy-sandbox/experiments.json).

Supported-suitability mode finds no evidence-supported candidates, explicitly
UNRESOLVED. It never assigns beginner eligibility to the actual 77 workouts.
An empty supported set cannot be relabeled as physiological impossibility.
Tests use distinct synthetic identities to demonstrate supported three-sport
coverage and its loss when existing injury restrictions block RUN.

The 20,000 experiment bound exceeds the whole candidate space. If a future
candidate product exceeds the caller's bound, the evaluator returns
BOUND_EXCEEDED, zero examined and no partial winner. It never truncates the
production search or claims no solution from an incomplete enumeration.

## Reduced targets and other goal scopes

Recovery budget 25.86 and taper budget 15.085 have **zero** one-per-sport
combinations across all 77 rows: the mathematical minimum is 29.3. The independent
oracle agrees. The real planner also rejects the explicit 43.1 witness for
those two existing beginner phase fixtures. No baseline increase, altered
workout, new factor, redistribution or waiver is used to force coverage.
This does not prove every possible repeat/partial-sport plan or future catalog
infeasible; such policies are outside the candidate constraint and need approval.

Experienced-athlete examples retain their actual independently resolved targets:
BUILD 550, recovery 300 and taper 175, each returning exact hypothetical totals
through the unchanged planner. These are not evaluated against a universal 45.
Swimming remains UNVERIFIED and suitability unapproved despite exact totals.

Single-sport goals retain their own objective. Actual zero-history RUN 45.2,
BIKE 45.3 and SWIM 43.9 are diagnosed only against their explicitly supplied 45
fixture budget. The sandbox never applies the triathlon allocation objective to
them. A sole seven-hour BIKE-013 returns 393.8 under legacy fallback, but the
prospective 45-budget result exceeds by 348.8 and suitability remains unapproved.

## Required decisions

Owner/Joren must approve hard-budget scope, precision/method, incomplete-week
handling, safe no-solution behavior, one-suitable-per-sport precedence and actual
suitability metadata. Approval of arithmetic is distinct from scientific review,
plan confirmation and later catalog activation. The strict budget would remove
the observed automatic beginner result; selecting its replacement requires the
separate [allocation tradeoff decision](JOREN_V6_SPORT_ALLOCATION_TRADEOFFS.md).

Verification, exact commits and open external gates:
[sandbox delivery report](JOREN_V6_PROSPECTIVE_POLICY_SANDBOX.md).
