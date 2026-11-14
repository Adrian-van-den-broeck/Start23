# V6 exact search: before/after measurements

14 November 2026, Europe/Amsterdam. All frequency maxima/requests below are
synthetic TEST_ONLY fixtures, not training prescriptions or real authorization.
Baseline: `e85cbaa8b5e702c283186fc61fcadda74ad36faf`; branch
`perf/joren-v6-exact-multi-session-search`. No production activation.

All 15 original contexts now finish exactly under the unchanged resource limit.
All 15 full ranking tuples/UUID multisets match the separate exhaustive reference;
all 12 formerly completed plans retain their exact workouts, occurrence IDs,
dates and official totals. The independent reference visits 20,061,679 complete
products in total and uses no optimized ranking bounds or production scheduler.

## Measurement definitions

The original fixture probe was recovered read-only from the accepted worktree,
then reproduced before production changes. The final serial repeat also uses an
accepted Git archive for the baseline, including its original application modules.
Machine: Windows 10 build 19045, x64; Intel64 Family 6 Model 85 Stepping 4;
the same existing Python 3.10.10 venv and pinned installed packages for both sides.
Environment/package/source hashes are in [verification.json](search-optimization/verification.json).

Cold means a fresh interpreter with prebuilt inputs/catalog before the timed call;
it does not claim a flushed OS filesystem cache. `wall_seconds` and `cpu_seconds`
cover the planner plus small result projection; catalog preparation and JSON file
encoding are outside those call measurements. `cold_process_seconds` additionally
covers interpreter/import/catalog/child I/O/teardown. Warm first executes the same
request in that interpreter, then times a second call; no runtime cache is added.
Each measurement child is fresh. Peak working set is the OS high-water mark for
the whole process, including imports/catalog and warm preparation, in bytes.
Windows CPU-time granularity limits very short measurements.

Timing rows below are uninstrumented delivery samples. Profile rows separately
count sport expansion, original joins/new box admissions, scheduler recursion,
complete-week materialization and sorting/bound/scheduling time. Instrumentation
does not change decisions but adds overhead. It is not a production timing claim.
The two independent serial samples per condition are retained in
[distributions.json](search-optimization/distributions.json): n=2 is descriptive,
not a population latency estimate. Host scheduling/cache/load are uncontrolled.

## Original 15 contexts: search work

The failing 200,001st step signals exhaustion of the 200,000-node ceiling; it is
not an allowed completed node. The three baseline failures all occur during
cross-sport joining, with zero scheduling attempts and no published candidate.
Every optimized row below has one materialized week and one scheduler invocation.

| Context | Before nodes | After nodes | Before materialized | Sport options (BIKE/RUN/SWIM; RUN only for run cases) | Sport expansion nodes |
| --- | --- | --- | --- | --- | --- |
| base_221_100 | 21040 | 427 | 4892 | 54/83/12 | 321 |
| base_221_150 | 60789 | 1013 | 24512 | 73/136/12 | 405 |
| base_221_200 | 117838 | 1345 | 60943 | 95/199/12 | 467 |
| base_221_250 | 189609 | 1544 | 112698 | 114/234/12 | 524 |
| base_221_300 | 200001 incomplete | 1681 | 134569 | 131/246/12 | 535 |
| base_211_300 | 43005 | 677 | 32742 | 17/246/12 | 316 |
| base_321_150 | 191519 | 1648 | 59830 | 73/575/12 | 1323 |
| base_222_100 | 79141 | 593 | 9177 | 54/83/55 | 457 |
| base_222_200 | 200001 incomplete | 1149 | 72785 | 95/199/82 | 603 |
| run_3_200 | 2800 | 1784 | 1039 | 1039 | 1756 |
| run_4_300 | 20513 | 11903 | 8646 | 8646 | 11861 |
| build4_221_100 | 21374 | 469 | 4898 | 57/83/12 | 355 |
| build4_221_150 | 66640 | 1143 | 25271 | 92/134/12 | 477 |
| normal_baseline_35min | 21076 | 427 | 4915 | 54/83/12 | 321 |
| normal_baseline_105min | 200001 incomplete | 1681 | 134678 | 131/246/12 | 535 |

## Original 15 contexts: elapsed, CPU and memory

| Context | Before wall/CPU seconds | After wall/CPU seconds | Before peak MiB | After peak MiB |
| --- | --- | --- | --- | --- |
| base_221_100 | 0.4801 / 0.4688 | 0.0221 / 0.0156 | 26.48 | 23.51 |
| base_221_150 | 2.3636 / 2.3594 | 0.0746 / 0.0781 | 43.82 | 23.37 |
| base_221_200 | 5.7568 / 5.7500 | 0.1048 / 0.1094 | 77.08 | 23.80 |
| base_221_250 | 11.0520 / 10.9688 | 0.1353 / 0.1406 | 124.47 | 23.66 |
| base_221_300 | 1.1331 / 1.1250 | 0.1426 / 0.1406 | 34.94 | 23.73 |
| base_211_300 | 2.7155 / 2.7188 | 0.0473 / 0.0469 | 49.05 | 23.34 |
| base_321_150 | 6.5684 / 6.5781 | 0.0608 / 0.0625 | 79.98 | 23.35 |
| base_222_100 | 1.2544 / 1.2500 | 0.0278 / 0.0312 | 30.09 | 23.39 |
| base_222_200 | 1.4238 / 1.4062 | 0.0755 / 0.0625 | 29.59 | 23.48 |
| run_3_200 | 0.0926 / 0.0938 | 0.0376 / 0.0312 | 23.61 | 23.67 |
| run_4_300 | 0.7619 / 0.7500 | 0.2861 / 0.2812 | 29.02 | 26.60 |
| build4_221_100 | 0.4925 / 0.4844 | 0.0249 / 0.0312 | 26.72 | 23.60 |
| build4_221_150 | 2.4855 / 2.4844 | 0.0816 / 0.0781 | 44.43 | 23.51 |
| normal_baseline_35min | 0.4836 / 0.4844 | 0.0241 / 0.0312 | 26.67 | 23.68 |
| normal_baseline_105min | 1.1368 / 1.1250 | 0.1399 / 0.1406 | 34.08 | 23.33 |

Exact bytes, CPU/wall values, process totals, all node stages, candidate counts,
scheduler calls, original ranking/sort costs and new bound/sport-sort costs are
in [before-profile.json](search-optimization/before-profile.json) and
[after-profile.json](search-optimization/after-profile.json). Raw timing samples
are in the cold/warm and repeat JSON files beside them. Heap comparison cost is
part of total time; it is not separately attributed to the bound timer.

## Exact completed selections

All dates are in the week 2026-10-26 through 2026-11-01. Full source UUIDs,
distinct occurrence UUIDs, exact official totals and the **entire five-part
ranking tuple**, including exact fractional L1 and load operands, are recorded
per case in [after-profile.json](search-optimization/after-profile.json).
[oracle.json](search-optimization/oracle.json) independently repeats every rank
and sorted UUID multiset, with complete product counts and date checks.
The table below preserves exact official Decimal totals without display rounding.

| Context | Dated source IDs (day of October; Nov 1 written 11-01) | Exact official total |
| --- | --- | --- |
| base_221_100 | 10-26: TR-BIKE-022; 10-27: TR-RUN-025; 10-29: TR-BIKE-023; 10-30: TR-RUN-025; 10-31: TR-SWIM-022 | 70.354166666666666666666666666666666666666666666667 |
| base_221_150 | 10-26: TR-BIKE-024; 10-27: TR-RUN-026; 10-29: TR-BIKE-026; 10-30: TR-RUN-027; 10-31: TR-SWIM-002 | 125.755208333333333333333333333333333333333333333333 |
| base_221_200 | 10-26: TR-BIKE-026; 10-27: TR-RUN-003; 10-29: TR-BIKE-027; 10-30: TR-RUN-027; 10-31: TR-SWIM-003 | 168.677083333333333333333333333333333333333333333333 |
| base_221_250 | 10-26: TR-BIKE-026; 10-27: TR-RUN-003; 10-29: TR-BIKE-027; 10-30: TR-RUN-027; 10-31: TR-SWIM-003 | 168.677083333333333333333333333333333333333333333333 |
| base_221_300 | 10-26: TR-BIKE-026; 10-27: TR-RUN-003; 10-29: TR-BIKE-027; 10-30: TR-RUN-027; 10-31: TR-SWIM-003 | 168.677083333333333333333333333333333333333333333333 |
| base_211_300 | 10-26: TR-RUN-027; 10-27: TR-SWIM-003; 10-29: TR-BIKE-004; 10-30: TR-RUN-003 | 168.677083333333333333333333333333333333333333333333 |
| base_321_150 | 10-26: TR-BIKE-024; 10-27: TR-RUN-025; 10-28: TR-SWIM-002; 10-29: TR-BIKE-026; 10-30: TR-RUN-026; 10-31: TR-RUN-025 | 125.755208333333333333333333333333333333333333333333 |
| base_222_100 | 10-26: TR-BIKE-025; 10-27: TR-RUN-025; 10-28: TR-SWIM-021; 10-29: TR-BIKE-022; 10-30: TR-RUN-026; 10-31: TR-SWIM-021 | 87.078125 |
| base_222_200 | 10-26: TR-BIKE-026; 10-27: TR-RUN-003; 10-28: TR-SWIM-002; 10-29: TR-BIKE-027; 10-30: TR-RUN-027; 10-31: TR-SWIM-021 | 168.677083333333333333333333333333333333333333333333 |
| run_3_200 | 10-26: TR-RUN-011; 10-29: TR-RUN-018; 10-30: TR-RUN-001 | 199.755958333333333333333333333333333333333333333333 |
| run_4_300 | 10-26: TR-RUN-027; 10-27: TR-RUN-003; 10-29: TR-RUN-017; 10-30: TR-RUN-016 | 299.837583333333333333333333333333333333333333333333 |
| build4_221_100 | 10-26: TR-BIKE-022; 10-27: TR-RUN-025; 10-29: TR-BIKE-023; 10-30: TR-RUN-025; 10-31: TR-SWIM-022 | 70.354166666666666666666666666666666666666666666667 |
| build4_221_150 | 10-26: TR-BIKE-024; 10-27: TR-RUN-026; 10-29: TR-BIKE-026; 10-30: TR-RUN-027; 10-31: TR-SWIM-002 | 125.755208333333333333333333333333333333333333333333 |
| normal_baseline_35min | 10-26: TR-BIKE-022; 10-27: TR-RUN-025; 10-29: TR-BIKE-023; 10-30: TR-RUN-025; 10-31: TR-SWIM-022 | 70.354166666666666666666666666666666666666666666667 |
| normal_baseline_105min | 10-26: TR-BIKE-026; 10-27: TR-RUN-003; 10-29: TR-BIKE-027; 10-30: TR-RUN-027; 10-31: TR-SWIM-003 | 168.677083333333333333333333333333333333333333333333 |

For A (BASE 2/2/1, 300) and C (normal 105-minute onboarding, resolved 300.2), the
week is BIKE-026 Monday, RUN-003 Tuesday, BIKE-027 Thursday, RUN-027 Friday,
SWIM-003 Saturday. B (BASE 2/2/2, 200) uses SWIM-002 Wednesday and SWIM-021
Saturday alongside the same four run/bike sessions. These have the same exact
total 168.677083333333333333333333333333333333333333333333. The approved L1
distance outranks load utilization; unused budget is not a defect or a new rule.

## Additional bounded contexts

| Context | Before | After | After wall/CPU seconds | After peak MiB | Failure stage |
| --- | --- | --- | --- | --- | --- |
| base_332_300 | 200001 incomplete | 7075 | 0.4682 / 0.4688 | 24.82 | complete |
| base_444_500 | 200001 incomplete | 54421 | 3.8278 / 3.8281 | 39.77 | complete |
| base_888_1000 | 200001 incomplete | 200001 incomplete | 2.9563 / 2.9531 | 79.38 | extend |
| base_221_300_retained | 2010 | 296 | 0.0164 / 0.0156 | 23.57 | complete |
| base_221_300_two_dates | 200001 incomplete | 1681 | 0.1528 / 0.1562 | 23.62 | complete |
| base_221_300_same_day | 200001 incomplete | 1681 | 0.1448 / 0.1406 | 23.55 | complete |
| base_221_300_repeat_limits | 200001 incomplete | 1533 | 0.1354 / 0.1406 | 23.42 | complete |
| base_221_300_injury | 2099 | 1554 | 0.1528 / 0.1562 | 23.61 | complete |
| base_221_300_low_only | 200001 incomplete | 1734 | 0.1604 / 0.1719 | 23.56 | complete |
| base_221_300_capability | 52003 | 6537 | 0.6744 / 0.6875 | 24.59 | complete |
| base_221_300_sport_caps | 2528 | 347 | 0.0169 / 0.0156 | 23.42 | complete |
| build1_221_300 | 200001 incomplete | 1784 | 0.1636 / 0.1719 | 23.66 | complete |
| recovery_221_150 | 83607 | 1318 | 0.1371 / 0.1406 | 23.41 | complete |
| taper_221_100 | 36381 | 712 | 0.0577 / 0.0625 | 23.56 | complete |

Full selections, exact rank/totals, source UUIDs/dates and stage counters for these
contexts are in [extra-after.json](search-optimization/extra-after.json), with
the same-input baseline in [extra-before.json](search-optimization/extra-before.json).
Every previously completed additional context retains its exact plan/rank.
The retained fixture fixes two separate RUN-025 occurrences to Tuesday/Friday;
completed physical-session preservation is additionally verified by real SQL.
One-date/two-date cases use the unchanged same-day placement policy. Injury,
LOW-only, missing-capability, per-sport caps, distinct-template limits and source
phases are explicit fixture inputs, never inferred training authorizations.

The 8/8/8 case still exhausts during the original sport-multiset expansion at the
200,001st attempted step, before any complete-week candidate or scheduler call.
Its memory is bounded by visited metadata and measured explicitly. Larger
authorized requests are not universally solved. No limit/deadline was increased,
no incumbent returned and no rest/partial proposal persisted for exhaustion.

## Real spawned worker and HTTP

The following paired samples use real `PlanningComputation`, existing FastAPI
routes and owner-scoped pending storage. Baseline application/catalog/test
sources are an exact accepted Git archive; children run that original code too.
Cold includes process creation/import; warm prepares the actual worker without
replaying or warming the measured HTTP request. The HTTP samples below use
in-memory persistence; PostgreSQL and TCP commit recovery are measured separately.

| Context/condition | Worker roundtrip before/after seconds | HTTP before/after seconds | Status before/after | HTTP worker peak before/after MiB |
| --- | --- | --- | --- | --- |
| base_221_300 / cold | 3.9846 / 1.7333 | 2.8016 / 1.7934 | 409 / 201 | 91.07 / 80.26 |
| base_221_300 / warm | 1.7822 / 0.4189 | 1.3592 / 0.3266 | 409 / 201 | 92.16 / 80.74 |
| base_222_200 / cold | 3.2394 / 1.7295 | 2.9494 / 1.5499 | 409 / 201 | 85.32 / 80.32 |
| base_222_200 / warm | 1.8483 / 0.3434 | 1.6244 / 0.2405 | 409 / 201 | 86.82 / 80.66 |
| normal_baseline_105min / cold | 2.9353 / 1.7430 | 2.7428 / 1.6177 | 409 / 201 | 90.30 / 79.98 |
| normal_baseline_105min / warm | 1.6740 / 0.4148 | 1.4726 / 0.3776 | 409 / 201 | 92.66 / 81.18 |

Raw child CPU, call wall, nodes, parent/child peaks and full HTTP plans are in
[transport-before.json](search-optimization/transport-before.json) and
[transport-after.json](search-optimization/transport-after.json). Baseline errors
write no plan; optimized results remain pending until separate confirmation.
For the three optimized HTTP cases, cold observed wall spans
1.550–1.793 s;
warm spans 0.240–0.378 s
(three distinct cases per condition, not repeated percentile evidence).

The real SQL 105-minute A5 creation measured 2.381 s
with worker peak 76.65 MiB. Its normal
resolver and SQL budget-evidence guards accepted 300.2; no target override was
used. Subsequent swipe, confirmation, physical activity, same-sport sibling move,
lost-ack retry and restart readback pass. SQL runners use real PostgreSQL RPCs
through a local SQL transport; two additional actual PostgREST/TCP commits for
that high-budget context and four regular-frequency commits prove network loss
recovery. Their synthetic tokens are not GoTrue/gateway verification.

## Proposed acceptance criteria, requiring separate approval

No quantitative V6 latency SLA is present in the accepted authority. A proposed
engineering gate is: preserve all exact outputs/certificates; keep all original
15 fixtures below 20,000 shared nodes; then measure at least 100 serial cold and
warm representative HTTP requests on agreed target hardware, proposing p95
below 3 seconds cold and 1 second warm for these three fixtures. These numbers
are **proposals only**, not activated timeouts or claimed measured percentiles.
Large/restricted athlete context coverage and CPU/memory admission must be
reviewed independently. The historical eight-second diagnostic remains unchanged.

Reproduction: `python -m benchmarks.v6_exact_search --output <new-file>`;
add `--warm`, `--instrument` or `--extended` separately. Run the same script
against an accepted archive (or `--reference`, which reinstalls only exact Git
blobs in its fresh measurement child; its cold process overhead includes Git).
Run `python -m benchmarks.v6_search_oracle --output <new-file>` independently.
For transport run `python -m benchmarks.v6_search_transport --output <new-file>`,
and baseline `--source-root <accepted-archive-root>`. Copy the benchmark modules
into that archive's backend/benchmarks; application and test sources stay exact.
No environment files, external accounts, hosted services or activation are used.
