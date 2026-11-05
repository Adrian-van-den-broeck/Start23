# Joren V6 no-high-minimum BUILD policy

2026-11-05, Europe/Amsterdam. Private offline policy validation.
New policy version: `joren-v6-final-prospective-policy-1`.
Joren: **“We zullen het zonder ondergrens doen.”**
Full question and decision provenance: [decision update](JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md).

## Prospective semantics

There is no required minimum HIGH active planned time, including BUILD weeks 1–4.
Zero percent HIGH is allowed by this intensity rule. The unchanged approved maximum
is 20% per sport per athlete-local Monday–Sunday week: HIGH / (LOW + HIGH) <= 1/5.
Z1/Z2 are LOW; Z3/Z4/Z5 HIGH. Ordered low recovery segments count as LOW active
time. Stationary swimming rest counts as neither LOW nor HIGH. Sport denominators
are independent; easy cycling cannot dilute excessive running intensity.

The maximum is not an exact target. No Z5 selection is required merely to create
a high-intensity minimum. Phase suitability, injury, recovery/taper, progression,
long-session/repeat restrictions and confirmed availability retain authority.
Unknown active time or classification withholds a numeric compliance claim.
An absent sport has no manufactured zero-duration denominator.

## Exact historical supersession boundary

The active `backend/app/modules/planning/domain.py` is byte-for-byte unchanged.
Its `_selection_policy_valid` operates on the **private load of whole HIGH-bucket
sessions**, not HIGH active segment time. It currently:

- Preserves scalar target fit `abs(target-total) < minimum_load` and sport caps.
- Requires zero HIGH-bucket load outside BUILD.
- Computes BUILD high-load budget = target × existing desired-high fraction and
  rejects HIGH-bucket load above that budget.
- If no affordable HIGH option is available, permits zero HIGH-bucket load.
- With HIGH available, BUILD weeks 1–3 require 70%–90% of that high-load budget.
- In BUILD week 4, requires positive HIGH-bucket load and a Z5 workout when an
  affordable HIGH Z5 option is available.

`_bounded_selection`, `_short_exact_build_selection` and
`_build_high_reachability` preserve those historical terminal assumptions and
optimization guards; selection scoring also prefers closeness to the historical
high-load budget. `eligible_workouts` retains its historical phase/Z5 filtering.
No search path, minimum, predicate, score, eligibility filter or bound is changed.

For a **future explicitly activated version only**, the requirement for positive
HIGH load in BUILD, the weeks 1–3 lower bound, and the week-4 Z5 inclusion duty
cannot remain mandatory ways of enforcing a high minimum. Their historical
whole-session metrics cannot stand in for the segment-time maximum. The new
offline evaluator omits these minimum/inclusion duties and delegates maximum
arithmetic to unchanged `joren-planned-active-time-maximum-1`.

This decision does not approve an exact replacement selector, retire independent
phase suitability or decide the continued role of every historical upper cap,
minimum-fill predicate or scoring preference. Later integration must explicitly
version the changed terminal/search/scoring assumptions, preserve unrelated safety
constraints and old provenance, and validate against its approved specification.
Historical snapshots and decisions must never be reinterpreted under this version.

## Offline tests and witnesses

| Case | Evidence/result |
| --- | --- |
| 0% HIGH BUILD | Exact timed synthetic three-sport fixtures pass the maximum for BUILD contexts 1–4; all other permissions explicitly TEST_ONLY |
| HIGH/Z5 alternative available | Both all-easy and compliant mixed alternatives remain witnesses; no obligation to choose HIGH or Z5 |
| Exactly 20% | 240 LOW seconds + 60 HIGH seconds => 1/5, compliant |
| More than 20% | 239 LOW + 60 HIGH => 60/299, excluded |
| Mixed low recoveries | Three repeats of 60 Z5 seconds + 240 Z1 seconds => 1/5; recovery counts LOW |
| Catalog mixed BIKE | BIKE-020: 180 HIGH / 5,580 active seconds = 1/31, compliant |
| Catalog excessive RUN | RUN-017: 1,800 HIGH / 3,600 active seconds = 1/2, excluded |
| All-easy catalog BUILD | 33 three-sport arithmetic witnesses within 45; conditionally 0% HIGH, SWIM estimated; actual suitability unresolved |
| Missing suitability | Every one of the nine suitability dimensions is independently omitted in tests; all-easy remains unresolved |
| Missing/uncertain SWIM time | Unknown active segments remain UNVERIFIED, including low-only prescriptions |
| Stationary SWIM rest | Adding 999,999 stationary seconds does not dilute a 20% ratio |
| SWIM estimates | SWIM-021: 500m Z2 × 2.00 min/100m = 10 estimated active minutes, zero HIGH; original times remain absent |

Reference estimates retain `ESTIMATED_FROM_APPROVED_REFERENCE_PACE` and estimator
`joren-v6-swim-reference-active-time-offline-1`, with its original decision version
`joren-v6-partial-approval-1`. The new policy version does not rewrite that provenance.
Authoritative duration compliance stays UNVERIFIED and operational acceptance stays
false. Estimates cannot override already prescribed times. No performed swim
duration, Realized TSS or athlete-specific pace is inferred.

The retained partial-approval tests also cover exactly/above/below 20% swimming
reference estimates and the illustrative ±0.005 min/100m sensitivity scenario.
Nominal 20% estimates can cross the boundary under zone-specific perturbations.
This scenario is not an empirical uncertainty bound, safety margin or approved
waiver. See the unchanged [swimming-time report](JOREN_V6_SWIM_ESTIMATED_ACTIVE_TIME.md).

The new tests extend historical coverage without replacing old planner tests.
The full backend suite, focused tests and unchanged 40-case corpus validate that
prospective permission does not alter production behavior. Results are recorded
in [verification](final-policy/verification.json) and the
[decision update](JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md).
