# Joren V6 partial-week feasibility

2026-11-05, Europe/Amsterdam. Private, offline, inactive.
Policy: `joren-v6-final-prospective-policy-1`.
Authority: [exact decision intake](JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md).

## Finite experiment and evidence meaning

Use the existing 77 V6 records (27 BIKE, 28 RUN, 22 SWIM), their original displayed
load strings and ordered segments. Budget inputs use the unchanged
`hypothetical-v6-displayed-source-p-exact-decimal-1` convention. This is not
official operational planned-P or approval of IF² precision/compatibility.
No workout, duration, factor or source value is changed.

The experiment enumerates every nonempty sport subset, with exactly one supplied
occurrence per present sport: 77 singles + 1,966 pairs + 16,632 triples = **18,675**
possibilities. Enumeration completes or returns `BOUND_EXCEEDED`, zero examined,
and no winner. A 20,000 diagnostic bound covers this entire finite space and is
not a production search limit. This says nothing about all possible repetitions,
other schedules or future catalogs. No partial week is hardcoded as the default.

Every candidate retains its supplied athlete-local date. Explicit available dates
are required; unavailable dates exclude candidates. The catalog experiments retain
the existing synthetic Monday 2026-10-26 fixture and its seven confirmed dates.
The caller must separately provide evidence for plan-level phase, injury, recovery,
taper, progression and scheduling safeguards. Date membership and arithmetic do
not establish those permissions. The evaluator does not invent a scheduler or
weaken the active scheduling rules.

`arithmetic_witnesses` checks the budget and structural scope only.
`supported_witnesses` additionally requires every suitability dimension and
restriction to be explicitly supported, known compliant active time (or separately
labelled conditional SWIM estimates), and allowed plan-level safeguards.
Missing evidence retains `UNRESOLVED_FAIL_CLOSED`. A complete three-sport witness
reports `FULL_WEEK_WITNESSES`; partial witnesses do not displace it. When no full
witness exists and evidence is resolved in this finite scope, one/two-sport
witnesses report `PARTIAL_WEEK_WITNESSES`. This is permission evidence, not a
selection. No suitable candidate gives `NO_PLAN_REST_FAIL_CLOSED`.

An unknown potentially suitable sport cannot be silently treated as infeasible to
authorize a partial prescription. Arithmetic and already-supported alternatives
remain inspectable while the result stays unresolved. Source-method and operational
approval remain false for every outcome.

## Required simulations

Numbers in the two count columns mean one-/two-/three-sport alternatives. Conditional
support uses explicitly synthetic `TEST_ONLY` suitability and safeguard assumptions;
none establishes Joren's pending actual athlete/workout approval. SWIM estimates
remain non-authoritative even in that conditional column.

| Requested case | Arithmetic counts | Conditional/evidence-supported counts and outcome |
| --- | --- | --- |
| 1. Beginner triathlon, budget 45 | 28 / 101 / 33 | Actual suitability unknown: 0 / 0 / 0; unresolved fail-closed |
| 2. Safe three-sport candidate | 28 / 101 / 33 | Assumed individual suitability/safeguards: 25 / 97 / 33; full-week witnesses, SWIM conditional estimates |
| 3. Safe two-sport when three infeasible | 16 / 16 / 0 at 25.86 | 16 / 16 / 0 under test assumptions; partial permission in finite scope, no selected winner |
| 4. Safe one-sport candidate | 7 / 1 / 0 at 15.085 | Only RUN individually permitted in this supplied fixture: 5 / 0 / 0; no sport omission order inferred |
| 5. No suitable workout | 28 / 101 / 33 | All explicitly blocked: 0 / 0 / 0; no-plan/rest/fail-closed |
| 6. Recovery 25.86 | 16 / 16 / 0 | Same finite two-sport experiment as case 3; actual recovery suitability is still pending |
| 7. Taper 15.085 | 7 / 1 / 0 | 7 / 1 / 0 conditionally; taper-specific permissions remain assumptions |
| 8. All-easy BUILD, zero HIGH | 25 / 97 / 33 | Same counts under assumptions; no high minimum, phase suitability not inferred |
| 9. Compliant mixed intensity | BIKE-020 alone under supplied 550 budget | HIGH ratio 1/31; conditional one-sport witness |
| 10. Above 20% HIGH | RUN-017 alone under supplied 550 budget | HIGH ratio 1/2; excluded; fail-closed |
| 11. Missing capability | Full arithmetic counts at 45 unchanged | SWIM blocked: 19 / 39 / 0; conditional partial witnesses, no forced SWIM |
| 12. Injury | Full arithmetic counts at 45 unchanged | RUN blocked: 12 / 15 / 0; conditional partial witnesses, no load redistribution |
| 13. Unknown athlete suitability | Same actual-metadata evaluation as case 1 | Unresolved; sensor capability and easy zones do not approve suitability |
| 14. Approved SWIM reference estimate | SWIM-021 alone under supplied 550 budget | Estimated 0% HIGH, 10 estimated active minutes, authoritative time UNVERIFIED; no operational acceptance |

Missing SWIM-time coverage is also simulated with the test-supported catalog but
without estimates: 19 / 39 / 0 known-time alternatives remain inspectable; full
coverage is unresolved. No whole-week or swimming-time compliance is claimed.

The minimum three-sport total remains 29.3, above both reduced supplied budgets.
Recovery has multiple different sport pairs: e.g. BIKE-022 + RUN-021 = 20.9 and
BIKE-022 + SWIM-021 = 23.5. At taper 15.085 the sole arithmetic pair is RUN-021 +
SWIM-021 = 14.2. These are witnesses, not prescriptions or defaults. There are
also single-sport alternatives; neither sport count nor omitted sport is ranked.
All identifiers carry `TR-` in the artifact.

The 50/30/20 target never imposes missing-sport coverage, increases the budget or
forces an unsuitable workout. Allocation closeness remains ahead of utilization
in the approved priorities. The precise comparison metric and ranking of competing
safe partial plans require further evidence/approval; the code implements neither
an omission order nor an automatic target renormalization.

## Verification and limits

An independent oracle enumerates source-record subsets and compares full ID sets
using rational source-display values at 45, 25.86 and 15.085. It does not call the
new enumeration/arithmetic function. Tests also cover deterministic output under
input permutation, hostile Decimal contexts, exact budgets, full versus partial
permission, empty/blocked catalogs, unknown evidence, confirmed availability,
unverified plan safeguards, capability/injury exclusions and bound exhaustion.

[Machine-readable evidence](final-policy/evidence.json) retains complete witness
sets, input scopes/references, exclusions, unknowns and per-sport intensity
provenance. The code carries no ranking field other than `UNRESOLVED_NO_DEFAULT`.
Source records and historical reports remain unchanged. Final test results and
remaining release gates are in the [decision update](JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md).
