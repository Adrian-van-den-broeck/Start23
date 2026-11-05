# V6 budget policy gap — not activated

2026-11-05, Europe/Amsterdam. Synthetic offline evaluation only.
Accepted start: `12fde3bd542b42e8259b130be797f673a8c2ded6`.

The separate fixture is
`backend/tests/fixtures/planner_performance/v6_budget_policy.json`, verified by
`test_isolated_prospective_beginner_policy_fixture`. It is not imported by the
runtime planner. The tests call the real planner for the automatic example and
the explicit manual witness and check their source identities and sport loads.

| Assessment | Automatic legacy selection | Explicit manual witness |
| --- | --- | --- |
| Source IDs | BIKE-022 + RUN-027 + SWIM-021 | BIKE-023 + RUN-024 + SWIM-021 |
| Planned load / existing starting target | 45.1 / 45.0 | 43.1 / 45.0 |
| Legacy selection validity | VALID | VALID |
| Proposed strict weekly-budget compliance | EXCEEDED by 0.1 | WITHIN by 1.9 |
| Individual athlete suitability | UNAPPROVED | UNAPPROVED |
| Three-sport coverage | Yes | Yes |
| One session per sport | Yes | Yes |
| BIKE / RUN / SWIM load | 15.1 / 21.6 / 8.4 | 20.2 / 14.5 / 8.4 |
| Exact planned sport shares | 151/451, 216/451, 84/451 | 202/431, 145/431, 84/431 |
| Per-sport high active time, BIKE / RUN | PASS, zero high / PASS, zero high | PASS, zero high / PASS, zero high |
| Swimming active-time compliance | UNVERIFIED | UNVERIFIED |
| Swimming-duration evidence | Missing; distance-prescribed | Missing; distance-prescribed |
| Approved beginner training plan | No | No |

The automatic classification is exactly:
**LEGACY_VALID / PROSPECTIVE_BUDGET_EXCEEDED**.

The source identifiers have the `TR-` prefix in the actual hypothetical catalog.
Its displayed source P remains an unapproved simulation input, not an activated
operational method. Neither example approves athlete capacity, long-session
suitability, repetition metadata, or beginner prescription. The manual witness
does not establish which workouts automatic selection should always choose.

The active historical predicate remains `abs(target - total) < minimum_load`.
The minimum eligible V6 load is 5.8 in this fixture, so both the 0.1 overshoot
and the 1.9 undershoot pass that predicate. This task does not replace it with a
hard budget, raise the beginner target, or introduce a universal 45-TSS cap.

The confirmed prospective Joren decisions remain separate:

- BIKE 50%, RUN 30%, SWIM 20% of weekly planned load as a target distribution.
- At most 20% HIGH active training time independently per sport and athlete-local
  week; no mandatory high minimum.
- One suitable session per sport for a zero-history triathlete where safely
  feasible, with the beginner starting target still 45.
- Authoritative injury, recovery, capacity, and progression rules continue to
  take precedence.

No distribution tolerance or new selection priority is invented. The numeric
target components 22.5 / 13.5 / 9.0 are not newly approved sport caps. The legacy
BUILD whole-session high-load requirements remain operationally unchanged even
though the prospective active-time policy has no high minimum.

Swimming remains distance-prescribed. All-Z2 describes its prescribed zones;
it does not supply a measured or prescribed active-time denominator. No CSS,
reference pace, standing rest, or assumed speed is converted into athlete minutes.
Missing duration is **UNVERIFIED**, including when known high seconds are zero.

Remaining independent gates: explicit scope/version of any hard-budget policy;
selection priorities relative to suitability/coverage/distribution; Source-P
authority and exact IF² precision; Z3 coefficient and source method acceptance;
approved athlete suitability and repetition metadata; permitted consumers of
UNVERIFIED swim time; and scientific/release approvals. This performance change
settles none of them and activates none of C3–C8, the catalog, or production.
