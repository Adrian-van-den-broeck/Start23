# V6 sport allocation tradeoffs

2026-11-05, Europe/Amsterdam. Private offline comparison; no adopted ranking.

CONFIRMED JOREN RULE: TRIATHLON target BIKE 50%, RUN 30%, SWIM 20%, as a soft
allocation target. It is not a set of sport caps, a required equality or authority
to exceed the weekly budget. Single-sport objectives are unchanged.

## Exact denominators

For sport s, share = selected sport P / selected total P. Signed deviation =
share - target share. These exact rational diagnostics include underfilled weeks.
The evaluator additionally reports budget component = authorized budget * target
share, and budget deviation = selected sport P - budget component. Budget
components are diagnostics, not independently enforced sport budgets.

At budget 45 the components are BIKE 22.5, RUN 13.5, SWIM 9.0. Selected-share
deviations sum to zero when total >0, while budget deviations sum to selected
total minus budget. Empty weeks have undefined selected shares (`None`), not
invented zero shares or perfect allocation. Non-triathlon goals have no target
allocation result. No tolerance percentage or rounding band is introduced.

NUMERICALLY RECONSTRUCTED METHOD: exact hypothetical source-display Decimal P,
version `hypothetical-v6-displayed-source-p-exact-decimal-1`. This comparison does
not approve source-P precision, IF² parameters or operational planned load.

## Competing concrete plans

BIKE/RUN/SWIM order. Every identifier has the `TR-` prefix.

| Origin | Source IDs | Total / remaining of 45 | Exact selected shares | L1 absolute share deviation |
| --- | --- | --- | --- | --- |
| Actual legacy automatic | BIKE-022 / RUN-027 / SWIM-021 | 45.1 / -0.1 | 151/451, 216/451, 84/451 | 807/2255 |
| Explicit manual witness | BIKE-023 / RUN-024 / SWIM-021 | 43.1 / 1.9 | 202/431, 145/431, 84/431 | 157/2155 |
| Offline allocation-first | BIKE-023 / RUN-023 / SWIM-021 | 40.2 / 4.8 | 101/201, 58/201, 14/67 | 23/1005 |
| Offline utilization-first | BIKE-023 / RUN-026 / SWIM-021 | 44.8 / 0.2 | 101/224, 81/224, 3/16 | 69/560 |

For the 43.1 manual witness, signed deviations are
BIKE `-27/862`, RUN `157/4310`, SWIM `-11/2155`. Budget deviations are
`-2.3`, `+1.0`, `-0.6`, summing to `-1.9`. A sport being above its budget
component does not cause hard rejection in this soft allocation experiment.

TESTED OFFLINE BEHAVIOR: complete enumeration across all 77 rows yields 33
budget-compliant one-each candidates, 23 scalar legacy fits. The two experimental
rankings return the 40.2 and 44.8 plans respectively, from those same 23 candidates.
Both are separately accepted by the actual planner as explicit submissions.
Neither is its automatic result; the 43.1 example is not chosen as a default.

The L1 measure `sum(abs(share-target))` is a PROPOSED PRODUCT POLICY diagnostic,
not a confirmed metric. It is reported exactly, not converted into a hard
tolerance. Allocation-first minimizes that error, then maximizes total;
utilization-first maximizes total, then minimizes error. Both use the actual
projected deck's sorted UUID identities for the remaining equal-count diagnostic
tie, preserving deterministic identities rather than inventing source-ID order.
This restricted experiment is not a claim to reproduce the active planner's
complete high-load/count/scheduling score or canonical path.

The 40.2 plan is much closer to 50/30/20 but leaves 4.8 unused. The 44.8 plan uses
4.6 more load and deviates more. Both remain below 45 with structural coverage.
The manual witness sits between them. Selecting either objective therefore changes
the proposed plan. No simulation can determine which preference Joren/owner wants.

## Proposed precedence, with unresolved conflicts

The requested order to investigate is:

1. Athlete safety and approved suitability.
2. Existing injury/recovery/progression restrictions.
3. Approved weekly budget.
4. Required sport coverage where feasible.
5. Closeness to 50/30/20.
6. Remaining budget utilization.
7. Existing deterministic tie-breaks.

This is a PROPOSED PRODUCT POLICY. The sandbox does not implement an authoritative
seven-stage selector. Its supported-evidence filter requires both suitability and
existing restriction permission; its finite ranking experiment starts only after
the budget and one-each structural constraint. Because real suitability is
unapproved, arithmetic ranking remains explicitly hypothetical.

Reasonable alternative: swap steps 5 and 6, producing the 44.8 plan instead of
40.2. Another unresolved choice is whether the legacy minimum-fill predicate
survives a strict ceiling. Of 33 within-budget candidates, ten fail that old
predicate; the current two winners happen to satisfy it. This agreement does not
approve minimum fill or a preference for additional training.

Coverage-first cannot override steps 1-3. At recovery 25.86/taper 15.085 no
one-per-sport combination fits; missing RUN suitability/injury permission also
eliminates supported three-sport coverage. No hard split, extra session, unsafe
fallback, new progression allowance or forced redistribution is introduced.
Whether a safe partial/rest plan, deferred selection or another approved source
is appropriate remains an owner/Joren decision, with existing rules retained.

The high-active-time maximum must be treated as an independent safety constraint,
not a low-priority allocation score. Existing BUILD high-session/private-load
requirements differ from the prospective segment-time maximum and no required
high minimum. A legacy-valid BUILD can satisfy its old objective while lacking
verified swimming time. Later integration must explicitly resolve coexistence or
supersession with versioned provenance; the sandbox changes neither.

## Approval responsibilities

Owner/Joren must choose scope and metric for soft allocation, priority versus
utilization, retained/retired legacy minimum-fill semantics, no-solution/coverage
handling, and precise deterministic tie behavior after the new hard gates.
Joren/accountable reviewer must supply appropriate suitability and intensity/phase
evidence. Owner must define permitted consumers of UNVERIFIED swimming time.
No numeric ranking, sensor capability or successful selection supplies those
approvals. UNAPPROVED ATHLETE METADATA applies to every real candidate here.

ACTIVE PRODUCTION BEHAVIOR remains the historical selector. The new diagnostics
are private, offline, and never added to athlete-facing APIs. Exact verification
and commit references: [sandbox report](JOREN_V6_PROSPECTIVE_POLICY_SANDBOX.md).
