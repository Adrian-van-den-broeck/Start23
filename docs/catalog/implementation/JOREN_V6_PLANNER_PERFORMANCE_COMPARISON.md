# Joren V6 planner before/after performance comparison

2026-11-05, Europe/Amsterdam. Private offline evidence.

Start SHA: `99c03b10f3f373d0756ee01b0cb2ebac944fcfae`.
Final verified implementation/delivery SHAs: [optimization report](JOREN_V6_PLANNER_OPTIMIZATION_REPORT.md).

## Measurement interpretation

All 40 original scenarios run against both the frozen accepted reference and
the optimized existing engine. Each cold attempt has the original eight-second
total wall deadline, including startup and setup. Timeout means **no returned
result within this bound**, not infeasibility or planner correctness failure.
No limit is raised. Measurements are serial local diagnostics, not an SLA.

Separate preloaded comparisons exclude module/catalog setup and give a separately
labeled eight-second planner-call budget. Prepared success is not substituted for
cold success. Instrumented profiles carry observer overhead and are not mixed
into uninstrumented speed comparisons. All input fingerprints must match across
variants. Reference completions require exact full-output fingerprint parity.
Previously timed-out newly returned outcomes get independent constraint checks.

| Mode | Attempts | Before timeouts | After timeouts | Before/after pending | Before/after fail-closed |
| --- | --- | --- | --- | --- | --- |
| v6 | 26 | 6 | 4 | 12 / 14 | 8 / 8 |
| previous61 | 5 | 4 | 3 | 1 / 1 | 0 / 1 |
| historical61 | 5 | 4 | 3 | 1 / 1 | 0 / 1 |
| current | 4 | 4 | 4 | 0 / 0 | 0 / 0 |

Overall: **18 -> 14 timeouts**, **14 -> 16 hypothetical pending returns**, **8 -> 10 fail-closed returns**. All 22 reference completions have exact full-output parity. All 40 input fingerprints match. All 16 returned optimized plans pass the direct legacy constraint checks. This is not prospective V6 policy approval.

All eight earlier historical timeout slots reproduce in the reference; seven remain after pruning. The resolved historical slot returns fail-closed, not a hypothetical valid training plan.


## Every one of the 40 cold scenarios

Times are wall seconds and, where a result returned, planner-call seconds. A
timeout cell retains its bound; it does not invent a plan, selected total or search
duration. The private JSON contains full plans, snapshots, warnings, dates,
input/output hashes and independent diagnostic results.

| Catalog / case | Reference outcome | Reference wall / planner sec | Optimized outcome | Optimized wall / planner sec | Parity / independent legacy check |
| --- | --- | --- | --- | --- | --- |
| current:build_1 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| current:build_2 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| current:build_3 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| current:build_4 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| historical61:build_1 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| historical61:build_2 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| historical61:build_3 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| historical61:build_4 | pending hypothetical | 0.9929 / 0.2758 | pending hypothetical | 0.8828 / 0.2510 | EXACT |
| historical61:tri_zero | TIMEOUT | TIMEOUT (8s) | catalog_capacity_unsatisfied | 0.6567 / 0.0027 | returned fail-closed |
| previous61:build_1 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| previous61:build_2 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| previous61:build_3 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| previous61:build_4 | pending hypothetical | 4.5494 / 3.8981 | pending hypothetical | 4.3476 / 3.6912 | EXACT |
| previous61:tri_zero | TIMEOUT | TIMEOUT (8s) | catalog_capacity_unsatisfied | 0.6894 / 0.0032 | returned fail-closed |
| v6:all_easy_build | pending hypothetical | 0.8620 / 0.0057 | pending hypothetical | 0.8893 / 0.0064 | EXACT |
| v6:all_injured | pending hypothetical | 0.8790 / 0.0002 | pending hypothetical | 0.8754 / 0.0002 | EXACT |
| v6:beginner_recovery | swipe_selection_invalid | 0.8629 / 0.0013 | swipe_selection_invalid | 0.9091 / 0.0010 | EXACT |
| v6:beginner_taper | swipe_selection_invalid | 0.9158 / 0.0007 | swipe_selection_invalid | 0.8751 / 0.0008 | EXACT |
| v6:bike_zero | pending hypothetical | 2.1379 / 1.3000 | pending hypothetical | 0.9740 / 0.0066 | EXACT |
| v6:build_1 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| v6:build_2 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| v6:build_3 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| v6:build_4 | TIMEOUT | TIMEOUT (8s) | TIMEOUT | TIMEOUT (8s) | unreturned |
| v6:candidate | pending hypothetical | 0.8455 / 0.0057 | pending hypothetical | 1.0117 / 0.0066 | EXACT |
| v6:candidate_no_dates | availability_required | 0.8728 / 0.0007 | availability_required | 0.9066 / 0.0007 | EXACT |
| v6:candidate_one_day | pending hypothetical | 0.8869 / 0.0080 | pending hypothetical | 0.9638 / 0.0066 | EXACT |
| v6:candidate_shortage | catalog_empty | 0.8403 / 0.0000 | catalog_empty | 0.9180 / 0.0000 | EXACT |
| v6:injury_run | restricted_zero_base_allocation_unavailable | 0.8736 / 0.0002 | restricted_zero_base_allocation_unavailable | 0.8869 / 0.0002 | EXACT |
| v6:limited_dates | TIMEOUT | TIMEOUT (8s) | pending hypothetical | 0.9704 / 0.0379 | PASS |
| v6:long_bike_only | pending hypothetical | 0.8270 / 0.0052 | pending hypothetical | 0.8651 / 0.0048 | EXACT |
| v6:minimum | swipe_selection_invalid | 0.8498 / 0.0010 | swipe_selection_invalid | 0.9265 / 0.0007 | EXACT |
| v6:missing_swim_capability | catalog_coverage_unsatisfied | 0.8991 / 0.0003 | catalog_coverage_unsatisfied | 0.8957 / 0.0002 | EXACT |
| v6:recovery | pending hypothetical | 1.2252 / 0.3511 | pending hypothetical | 1.1833 / 0.2407 | EXACT |
| v6:repeat_bike | pending hypothetical | 0.8355 / 0.0052 | pending hypothetical | 0.8418 / 0.0052 | EXACT |
| v6:repeat_explicit | pending hypothetical | 0.9051 / 0.0058 | pending hypothetical | 0.9127 / 0.0055 | EXACT |
| v6:run_zero | pending hypothetical | 1.7214 / 0.8851 | pending hypothetical | 0.9769 / 0.0093 | EXACT |
| v6:swim_zero | pending hypothetical | 0.9045 / 0.0221 | pending hypothetical | 0.9380 / 0.0064 | EXACT |
| v6:taper | pending hypothetical | 1.2046 / 0.3239 | pending hypothetical | 1.1156 / 0.1866 | EXACT |
| v6:tri_zero | TIMEOUT | TIMEOUT (8s) | pending hypothetical | 0.9843 / 0.0365 | PASS |
| v6:unconfirmed_swim_capability | catalog_coverage_unsatisfied | 0.8753 / 0.0003 | catalog_coverage_unsatisfied | 0.8975 / 0.0003 | EXACT |



## Cold versus preloaded calls

| Case | Cold before wall / call | Cold after wall / call | Preloaded before wall / call | Preloaded after wall / call |
| --- | --- | --- | --- | --- |
| current:build_1 | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) |
| v6:build_1 | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) |
| v6:build_2 | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) |
| v6:build_3 | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) |
| v6:build_4 | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) | TIMEOUT (8s) |
| v6:candidate | 0.8455 / 0.0057 | 1.0117 / 0.0066 | 0.0634 / 0.0059 | 0.0727 / 0.0060 |
| v6:limited_dates | TIMEOUT (8s) | 0.9704 / 0.0379 | TIMEOUT (8s) | 0.1032 / 0.0343 |
| v6:recovery | 1.2252 / 0.3511 | 1.1833 / 0.2407 | 0.4047 / 0.3419 | 0.2803 / 0.2159 |
| v6:tri_zero | TIMEOUT (8s) | 0.9843 / 0.0365 | TIMEOUT (8s) | 0.0926 / 0.0312 |



## New returns and remaining timeouts

| Previously timed-out case | New returned result | Load / target | Independent assessment |
| --- | --- | --- | --- |
| historical61:tri_zero | catalog_capacity_unsatisfied | No plan returned | not applicable |
| previous61:tri_zero | catalog_capacity_unsatisfied | No plan returned | not applicable |
| v6:limited_dates | TR-SWIM-021, TR-BIKE-022, TR-RUN-027 | 45.1 / target 45.0 | legacy PASS; budget False; swim UNVERIFIED |
| v6:tri_zero | TR-RUN-027, TR-BIKE-022, TR-SWIM-021 | 45.1 / target 45.0 | legacy PASS; budget False; swim UNVERIFIED |



The new V6 automatic zero-history and limited-date returns select 45.1 against
the 45 budget. Legacy constraint validity and prospective budget validity are
different findings; those outputs are not accepted V6 training plans. Unknown swim
time is never filled. The prior/historical 61-row beginner cases now return an
actual `catalog_capacity_unsatisfied` under their existing strict fit policy;
their preceding timeouts alone did not prove that outcome.

| Remaining cold timeout | Preloaded measurement |
| --- | --- |
| current:build_1 | TIMEOUT at 8s also preloaded |
| current:build_2 | not sampled preloaded |
| current:build_3 | not sampled preloaded |
| current:build_4 | not sampled preloaded |
| historical61:build_1 | not sampled preloaded |
| historical61:build_2 | not sampled preloaded |
| historical61:build_3 | not sampled preloaded |
| previous61:build_1 | not sampled preloaded |
| previous61:build_2 | not sampled preloaded |
| previous61:build_3 | not sampled preloaded |
| v6:build_1 | TIMEOUT at 8s also preloaded |
| v6:build_2 | TIMEOUT at 8s also preloaded |
| v6:build_3 | TIMEOUT at 8s also preloaded |
| v6:build_4 | TIMEOUT at 8s also preloaded |



The original 43.1 explicit proposal still returns, unchanged. A faster automatic
legacy fit does not turn that manual witness into an automatic optimum or approve
its athlete suitability. The new prospective distributions, intensity ceiling,
P precision/method and source metadata remain outside active selection.

Final backend/lint/type/custody results and exact local commits are in the
[optimization report](JOREN_V6_PLANNER_OPTIMIZATION_REPORT.md). There is no catalog
activation, source rewrite, historical load recalculation or production change.

Exact verified implementation SHA: `c7c1b43a5db354d2abea4e128f42ca050179d2ad`,
based on accepted `99c03b10f3f373d0756ee01b0cb2ebac944fcfae`. The subsequent
documentation-only delivery commit records that reference; its final tip SHA is
supplied in the delivery response and resolves with `git rev-parse perf/joren-v6-planner`.
