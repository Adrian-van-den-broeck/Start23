# Joren V6 BUILD search benchmarks

2026-11-05, Europe/Amsterdam. Private synthetic diagnostics; no activation.

Start: `12fde3bd542b42e8259b130be797f673a8c2ded6`. Implementation/delivery lineage: [optimization report](JOREN_V6_BUILD_SEARCH_OPTIMIZATION.md).

All six matrices use the complete unchanged 40-case corpus and digest-pinned accepted Phase 1 oracle. Every input fingerprint matches. Completed comparisons use full canonical result dictionaries and output hashes (all fields, errors/messages, ordered snapshots, dates, warnings, and identities). Every returned plan passes the independent legacy checks. A timeout supplies no expected plan.

Runs were serial, with no concurrent benchmark variants or test/typecheck load. Cold wall time starts before process creation and retains the eight-second total deadline. Preloaded runs separately bound setup, then give the planner call eight seconds; their wall column excludes setup. They do not replace a cold timeout. Profile timing includes observer overhead and is never used as uninstrumented speed evidence. Host load is uncontrolled and these are local single samples, not an SLA.

| Mode | Accepted timeouts | Optimized timeouts | Exact accepted completions |
| --- | --- | --- | --- |
| cold | 14 | 1 | 26 |
| preloaded | 14 | 1 | 26 |
| profile | 14 | 1 | 26 |

## All 40 cold outcomes

| Case | Accepted outcome | Wall / planner sec | Optimized outcome | Wall / planner sec | Check |
| --- | --- | --- | --- | --- | --- |
| current:build_1 | DIAGNOSTIC_TIMEOUT | 8.009501 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 3.589134 / 2.996294 | independent legacy PASS |
| current:build_2 | DIAGNOSTIC_TIMEOUT | 8.004013 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 3.444609 / 2.872666 | independent legacy PASS |
| current:build_3 | DIAGNOSTIC_TIMEOUT | 8.009656 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 3.474330 / 2.897106 | independent legacy PASS |
| current:build_4 | DIAGNOSTIC_TIMEOUT | 8.016668 / TIMEOUT (8s) | DIAGNOSTIC_TIMEOUT | 8.010131 / TIMEOUT (8s) | unreturned |
| historical61:build_1 | DIAGNOSTIC_TIMEOUT | 8.008538 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.636620 / 0.034119 | independent legacy PASS |
| historical61:build_2 | DIAGNOSTIC_TIMEOUT | 8.011411 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.614477 / 0.027237 | independent legacy PASS |
| historical61:build_3 | DIAGNOSTIC_TIMEOUT | 8.004797 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.665432 / 0.030951 | independent legacy PASS |
| historical61:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.809931 / 0.224049 | PENDING_HYPOTHETICAL_PLAN | 0.678966 / 0.036434 | EXACT |
| historical61:tri_zero | catalog_capacity_unsatisfied | 0.580047 / 0.001987 | catalog_capacity_unsatisfied | 0.627700 / 0.001952 | EXACT |
| previous61:build_1 | DIAGNOSTIC_TIMEOUT | 8.014636 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.620261 / 0.025894 | independent legacy PASS |
| previous61:build_2 | DIAGNOSTIC_TIMEOUT | 8.007444 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.629475 / 0.027464 | independent legacy PASS |
| previous61:build_3 | DIAGNOSTIC_TIMEOUT | 8.006222 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.615796 / 0.026963 | independent legacy PASS |
| previous61:build_4 | PENDING_HYPOTHETICAL_PLAN | 3.585523 / 2.964618 | PENDING_HYPOTHETICAL_PLAN | 0.671549 / 0.040793 | EXACT |
| previous61:tri_zero | catalog_capacity_unsatisfied | 0.582613 / 0.002031 | catalog_capacity_unsatisfied | 0.605531 / 0.001888 | EXACT |
| v6:all_easy_build | PENDING_HYPOTHETICAL_PLAN | 0.768288 / 0.005291 | PENDING_HYPOTHETICAL_PLAN | 0.781174 / 0.005709 | EXACT |
| v6:all_injured | PENDING_HYPOTHETICAL_PLAN | 0.775679 / 0.000246 | PENDING_HYPOTHETICAL_PLAN | 0.792015 / 0.000157 | EXACT |
| v6:beginner_recovery | swipe_selection_invalid | 0.782510 / 0.000722 | swipe_selection_invalid | 0.781373 / 0.000688 | EXACT |
| v6:beginner_taper | swipe_selection_invalid | 0.765956 / 0.000699 | swipe_selection_invalid | 0.754535 / 0.000685 | EXACT |
| v6:bike_zero | PENDING_HYPOTHETICAL_PLAN | 0.775406 / 0.005145 | PENDING_HYPOTHETICAL_PLAN | 0.814627 / 0.005651 | EXACT |
| v6:build_1 | DIAGNOSTIC_TIMEOUT | 8.016327 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.828248 / 0.053144 | independent legacy PASS |
| v6:build_2 | DIAGNOSTIC_TIMEOUT | 8.015359 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.848419 / 0.053477 | independent legacy PASS |
| v6:build_3 | DIAGNOSTIC_TIMEOUT | 8.006372 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.822327 / 0.057002 | independent legacy PASS |
| v6:build_4 | DIAGNOSTIC_TIMEOUT | 8.013198 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.782192 / 0.014454 | independent legacy PASS |
| v6:candidate | PENDING_HYPOTHETICAL_PLAN | 0.768250 / 0.005028 | PENDING_HYPOTHETICAL_PLAN | 0.788432 / 0.005518 | EXACT |
| v6:candidate_no_dates | availability_required | 0.820744 / 0.000854 | availability_required | 0.801380 / 0.000721 | EXACT |
| v6:candidate_one_day | PENDING_HYPOTHETICAL_PLAN | 0.771069 / 0.004916 | PENDING_HYPOTHETICAL_PLAN | 0.820460 / 0.005158 | EXACT |
| v6:candidate_shortage | catalog_empty | 0.751006 / 0.000044 | catalog_empty | 0.764651 / 0.000032 | EXACT |
| v6:injury_run | restricted_zero_base_allocation_unavailable | 0.780543 / 0.000222 | restricted_zero_base_allocation_unavailable | 0.789043 / 0.000203 | EXACT |
| v6:limited_dates | PENDING_HYPOTHETICAL_PLAN | 0.805977 / 0.031523 | PENDING_HYPOTHETICAL_PLAN | 0.831857 / 0.048700 | EXACT |
| v6:long_bike_only | PENDING_HYPOTHETICAL_PLAN | 0.743802 / 0.004093 | PENDING_HYPOTHETICAL_PLAN | 0.767623 / 0.004461 | EXACT |
| v6:minimum | swipe_selection_invalid | 0.782218 / 0.000685 | swipe_selection_invalid | 0.802449 / 0.000670 | EXACT |
| v6:missing_swim_capability | catalog_coverage_unsatisfied | 0.777161 / 0.000209 | catalog_coverage_unsatisfied | 0.798238 / 0.000194 | EXACT |
| v6:recovery | PENDING_HYPOTHETICAL_PLAN | 0.981688 / 0.199989 | PENDING_HYPOTHETICAL_PLAN | 0.960195 / 0.191662 | EXACT |
| v6:repeat_bike | PENDING_HYPOTHETICAL_PLAN | 0.751310 / 0.004517 | PENDING_HYPOTHETICAL_PLAN | 0.764143 / 0.004699 | EXACT |
| v6:repeat_explicit | PENDING_HYPOTHETICAL_PLAN | 0.761003 / 0.004571 | PENDING_HYPOTHETICAL_PLAN | 0.778510 / 0.004611 | EXACT |
| v6:run_zero | PENDING_HYPOTHETICAL_PLAN | 0.814695 / 0.010468 | PENDING_HYPOTHETICAL_PLAN | 0.799652 / 0.008369 | EXACT |
| v6:swim_zero | PENDING_HYPOTHETICAL_PLAN | 0.780077 / 0.005674 | PENDING_HYPOTHETICAL_PLAN | 0.779067 / 0.005139 | EXACT |
| v6:taper | PENDING_HYPOTHETICAL_PLAN | 0.907461 / 0.125426 | PENDING_HYPOTHETICAL_PLAN | 0.910665 / 0.115174 | EXACT |
| v6:tri_zero | PENDING_HYPOTHETICAL_PLAN | 0.858856 / 0.030271 | PENDING_HYPOTHETICAL_PLAN | 0.828327 / 0.031728 | EXACT |
| v6:unconfirmed_swim_capability | catalog_coverage_unsatisfied | 0.773423 / 0.000254 | catalog_coverage_unsatisfied | 0.801313 / 0.000251 | EXACT |

## All 40 preloaded outcomes

| Case | Accepted outcome | Wall / planner sec | Optimized outcome | Wall / planner sec | Check |
| --- | --- | --- | --- | --- | --- |
| current:build_1 | DIAGNOSTIC_TIMEOUT | 8.008113 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 2.969049 / 2.913456 | independent legacy PASS |
| current:build_2 | DIAGNOSTIC_TIMEOUT | 8.007401 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 2.966194 / 2.914468 | independent legacy PASS |
| current:build_3 | DIAGNOSTIC_TIMEOUT | 8.005261 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 2.968529 / 2.914984 | independent legacy PASS |
| current:build_4 | DIAGNOSTIC_TIMEOUT | 8.014429 / TIMEOUT (8s) | DIAGNOSTIC_TIMEOUT | 8.015840 / TIMEOUT (8s) | unreturned |
| historical61:build_1 | DIAGNOSTIC_TIMEOUT | 8.007411 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.176886 / 0.040453 | independent legacy PASS |
| historical61:build_2 | DIAGNOSTIC_TIMEOUT | 8.006361 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.085731 / 0.030733 | independent legacy PASS |
| historical61:build_3 | DIAGNOSTIC_TIMEOUT | 8.005736 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.094637 / 0.029860 | independent legacy PASS |
| historical61:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.275053 / 0.222976 | PENDING_HYPOTHETICAL_PLAN | 0.090197 / 0.036273 | EXACT |
| historical61:tri_zero | catalog_capacity_unsatisfied | 0.049228 / 0.001949 | catalog_capacity_unsatisfied | 0.052447 / 0.002022 | EXACT |
| previous61:build_1 | DIAGNOSTIC_TIMEOUT | 8.006300 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.084547 / 0.028555 | independent legacy PASS |
| previous61:build_2 | DIAGNOSTIC_TIMEOUT | 8.014153 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.092005 / 0.030632 | independent legacy PASS |
| previous61:build_3 | DIAGNOSTIC_TIMEOUT | 8.017412 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.078553 / 0.026772 | independent legacy PASS |
| previous61:build_4 | PENDING_HYPOTHETICAL_PLAN | 2.944905 / 2.888707 | PENDING_HYPOTHETICAL_PLAN | 0.090837 / 0.038096 | EXACT |
| previous61:tri_zero | catalog_capacity_unsatisfied | 0.056580 / 0.001869 | catalog_capacity_unsatisfied | 0.051838 / 0.002103 | EXACT |
| v6:all_easy_build | PENDING_HYPOTHETICAL_PLAN | 0.059307 / 0.005283 | PENDING_HYPOTHETICAL_PLAN | 0.057866 / 0.005051 | EXACT |
| v6:all_injured | PENDING_HYPOTHETICAL_PLAN | 0.049500 / 0.000162 | PENDING_HYPOTHETICAL_PLAN | 0.056059 / 0.000151 | EXACT |
| v6:beginner_recovery | swipe_selection_invalid | 0.062276 / 0.000768 | swipe_selection_invalid | 0.060572 / 0.000770 | EXACT |
| v6:beginner_taper | swipe_selection_invalid | 0.050086 / 0.000714 | swipe_selection_invalid | 0.054526 / 0.000761 | EXACT |
| v6:bike_zero | PENDING_HYPOTHETICAL_PLAN | 0.056487 / 0.005203 | PENDING_HYPOTHETICAL_PLAN | 0.061193 / 0.005424 | EXACT |
| v6:build_1 | DIAGNOSTIC_TIMEOUT | 8.007484 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.109306 / 0.054121 | independent legacy PASS |
| v6:build_2 | DIAGNOSTIC_TIMEOUT | 8.009296 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.111203 / 0.059928 | independent legacy PASS |
| v6:build_3 | DIAGNOSTIC_TIMEOUT | 8.010814 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.116171 / 0.059346 | independent legacy PASS |
| v6:build_4 | DIAGNOSTIC_TIMEOUT | 8.009698 / TIMEOUT (8s) | PENDING_HYPOTHETICAL_PLAN | 0.063422 / 0.014238 | independent legacy PASS |
| v6:candidate | PENDING_HYPOTHETICAL_PLAN | 0.070758 / 0.005399 | PENDING_HYPOTHETICAL_PLAN | 0.067735 / 0.006912 | EXACT |
| v6:candidate_no_dates | availability_required | 0.053154 / 0.000696 | availability_required | 0.057583 / 0.000674 | EXACT |
| v6:candidate_one_day | PENDING_HYPOTHETICAL_PLAN | 0.054790 / 0.004650 | PENDING_HYPOTHETICAL_PLAN | 0.059807 / 0.005322 | EXACT |
| v6:candidate_shortage | catalog_empty | 0.062967 / 0.000041 | catalog_empty | 0.049891 / 0.000034 | EXACT |
| v6:injury_run | restricted_zero_base_allocation_unavailable | 0.056621 / 0.000237 | restricted_zero_base_allocation_unavailable | 0.049292 / 0.000217 | EXACT |
| v6:limited_dates | PENDING_HYPOTHETICAL_PLAN | 0.092446 / 0.031947 | PENDING_HYPOTHETICAL_PLAN | 0.080862 / 0.029521 | EXACT |
| v6:long_bike_only | PENDING_HYPOTHETICAL_PLAN | 0.056787 / 0.004674 | PENDING_HYPOTHETICAL_PLAN | 0.057962 / 0.004449 | EXACT |
| v6:minimum | swipe_selection_invalid | 0.074029 / 0.000849 | swipe_selection_invalid | 0.050822 / 0.000708 | EXACT |
| v6:missing_swim_capability | catalog_coverage_unsatisfied | 0.049125 / 0.000214 | catalog_coverage_unsatisfied | 0.056915 / 0.000242 | EXACT |
| v6:recovery | PENDING_HYPOTHETICAL_PLAN | 0.267920 / 0.214483 | PENDING_HYPOTHETICAL_PLAN | 0.270049 / 0.214073 | EXACT |
| v6:repeat_bike | PENDING_HYPOTHETICAL_PLAN | 0.055278 / 0.004683 | PENDING_HYPOTHETICAL_PLAN | 0.064369 / 0.005333 | EXACT |
| v6:repeat_explicit | PENDING_HYPOTHETICAL_PLAN | 0.056763 / 0.004790 | PENDING_HYPOTHETICAL_PLAN | 0.061446 / 0.004701 | EXACT |
| v6:run_zero | PENDING_HYPOTHETICAL_PLAN | 0.069044 / 0.008858 | PENDING_HYPOTHETICAL_PLAN | 0.059754 / 0.008610 | EXACT |
| v6:swim_zero | PENDING_HYPOTHETICAL_PLAN | 0.056079 / 0.005149 | PENDING_HYPOTHETICAL_PLAN | 0.065411 / 0.005443 | EXACT |
| v6:taper | PENDING_HYPOTHETICAL_PLAN | 0.174460 / 0.124318 | PENDING_HYPOTHETICAL_PLAN | 0.183450 / 0.122855 | EXACT |
| v6:tri_zero | PENDING_HYPOTHETICAL_PLAN | 0.104074 / 0.045704 | PENDING_HYPOTHETICAL_PLAN | 0.079414 / 0.029046 | EXACT |
| v6:unconfirmed_swim_capability | catalog_coverage_unsatisfied | 0.059816 / 0.000268 | catalog_coverage_unsatisfied | 0.050308 / 0.000264 | EXACT |

## Instrumented work and memory

DP transitions and exact half construction/join attempts are separate operations, not interchangeable timings. Expanded/evaluated counts refer to DP states; exact representatives evaluated are separate. Repeated counts distinguish DP destination collisions from exact representative collisions. Peak DP residency includes the current and next dictionaries; exact residency is the representative dictionary plus separately reported constructed half entries. RSS is the process lifetime peak working set, including imports, catalog, observer, and helper tables, measured through Windows GetProcessMemoryInfo. It is not incremental planner-only allocation. Timeout checkpoints are partial lower bounds, including resident peaks; elapsed active search is an open-stage observation.

| Variant / case | Outcome | Search sec | DP transitions | Halves / joins | Expanded / evaluated DP | Evaluated exact | Repeated DP / exact | Peak DP / exact states | Peak RSS MiB | Scheduling calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted / current:build_1 | DIAGNOSTIC_TIMEOUT | 7.311261 partial | 2621440 | 0 / 0 | 63938 / 72998 | 0 | 980904 / 0 | 63948 / 0 | 87.11 | 4 |
| accepted / current:build_2 | DIAGNOSTIC_TIMEOUT | 7.237465 partial | 2752512 | 0 / 0 | 67135 / 72998 | 0 | 1027085 / 0 | 67167 / 0 | 89.93 | 4 |
| accepted / current:build_3 | DIAGNOSTIC_TIMEOUT | 7.401818 partial | 2818048 | 0 / 0 | 68733 / 72998 | 0 | 1049253 / 0 | 68409 / 0 | 91.02 | 4 |
| accepted / current:build_4 | DIAGNOSTIC_TIMEOUT | 7.373430 partial | 3080192 | 0 / 0 | 58117 / 67606 | 0 | 959529 / 0 | 95327 / 0 | 110.48 | 6 |
| accepted / historical61:build_1 | DIAGNOSTIC_TIMEOUT | 7.388373 partial | 1572864 | 0 / 0 | 33466 / 60123 | 0 | 1004308 / 0 | 168090 / 0 | 162.68 | 4 |
| accepted / historical61:build_2 | DIAGNOSTIC_TIMEOUT | 7.266520 partial | 1703936 | 0 / 0 | 36254 / 60123 | 0 | 1084140 / 0 | 181322 / 0 | 172.04 | 4 |
| accepted / historical61:build_3 | DIAGNOSTIC_TIMEOUT | 7.264254 partial | 1703936 | 0 / 0 | 36254 / 60123 | 0 | 1084140 / 0 | 181322 / 0 | 171.74 | 4 |
| accepted / historical61:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.308180 | 62496 | 0 / 0 | 1116 / 13551 | 0 | 35388 / 0 | 13500 / 0 | 48.80 | 5 |
| accepted / historical61:tri_zero | catalog_capacity_unsatisfied | 0.013243 | 2394 | 0 / 0 | 63 / 63 | 0 | 52 / 0 | 47 / 0 | 39.85 | 0 |
| accepted / previous61:build_1 | DIAGNOSTIC_TIMEOUT | 7.169650 partial | 1638400 | 0 / 0 | 34860 / 68728 | 0 | 1040630 / 0 | 182673 / 0 | 172.97 | 4 |
| accepted / previous61:build_2 | DIAGNOSTIC_TIMEOUT | 7.155184 partial | 1638400 | 0 / 0 | 34860 / 68728 | 0 | 1040630 / 0 | 182673 / 0 | 172.78 | 4 |
| accepted / previous61:build_3 | DIAGNOSTIC_TIMEOUT | 7.033340 partial | 1638400 | 0 / 0 | 34860 / 68728 | 0 | 1040630 / 0 | 182673 / 0 | 172.57 | 4 |
| accepted / previous61:build_4 | PENDING_HYPOTHETICAL_PLAN | 3.712259 | 836080 | 0 / 0 | 14930 / 110054 | 0 | 463042 / 0 | 108890 / 0 | 120.55 | 10 |
| accepted / previous61:tri_zero | catalog_capacity_unsatisfied | 0.011169 | 2204 | 0 / 0 | 58 / 58 | 0 | 40 / 0 | 47 / 0 | 40.13 | 0 |
| accepted / v6:all_easy_build | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.01 | 1 |
| accepted / v6:all_injured | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 39.89 | 0 |
| accepted / v6:beginner_recovery | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.55 | 0 |
| accepted / v6:beginner_taper | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.68 | 0 |
| accepted / v6:bike_zero | PENDING_HYPOTHETICAL_PLAN | 0.009496 | 323 | 0 / 0 | 17 / 17 | 0 | 5 / 0 | 15 / 0 | 40.52 | 1 |
| accepted / v6:build_1 | DIAGNOSTIC_TIMEOUT | 6.914215 partial | 1526931 | 0 / 0 | 24237 / 24237 | 0 | 1154135 / 0 | 162756 / 0 | 157.49 | 1 |
| accepted / v6:build_2 | DIAGNOSTIC_TIMEOUT | 7.031374 partial | 1507328 | 0 / 0 | 23926 / 24237 | 0 | 1141624 / 0 | 162556 / 0 | 157.07 | 1 |
| accepted / v6:build_3 | DIAGNOSTIC_TIMEOUT | 7.168140 partial | 1526931 | 0 / 0 | 24237 / 24237 | 0 | 1154135 / 0 | 162756 / 0 | 157.38 | 1 |
| accepted / v6:build_4 | DIAGNOSTIC_TIMEOUT | 7.175968 partial | 1441792 | 0 / 0 | 20025 / 32896 | 0 | 981128 / 0 | 207577 / 0 | 196.50 | 3 |
| accepted / v6:candidate | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.71 | 1 |
| accepted / v6:candidate_no_dates | availability_required | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.73 | 1 |
| accepted / v6:candidate_one_day | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.66 | 1 |
| accepted / v6:candidate_shortage | catalog_empty | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 39.38 | 0 |
| accepted / v6:injury_run | restricted_zero_base_allocation_unavailable | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.60 | 0 |
| accepted / v6:limited_dates | PENDING_HYPOTHETICAL_PLAN | 0.071634 | 46170 | 0 / 0 | 855 / 855 | 0 | 1858 / 0 | 563 / 0 | 40.58 | 1 |
| accepted / v6:long_bike_only | PENDING_HYPOTHETICAL_PLAN | 0.004477 | 2 | 0 / 0 | 2 / 2 | 0 | 0 / 0 | 2 / 0 | 39.62 | 1 |
| accepted / v6:minimum | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.42 | 0 |
| accepted / v6:missing_swim_capability | catalog_coverage_unsatisfied | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.60 | 0 |
| accepted / v6:recovery | PENDING_HYPOTHETICAL_PLAN | 0.291233 | 62748 | 0 / 0 | 1162 / 11373 | 0 | 40735 / 0 | 11321 / 0 | 47.33 | 1 |
| accepted / v6:repeat_bike | PENDING_HYPOTHETICAL_PLAN | 0.008344 | 4 | 0 / 0 | 4 / 4 | 0 | 0 / 0 | 2 / 0 | 39.18 | 1 |
| accepted / v6:repeat_explicit | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.27 | 1 |
| accepted / v6:run_zero | PENDING_HYPOTHETICAL_PLAN | 0.025714 | 4008 | 0 / 0 | 167 / 167 | 0 | 367 / 0 | 93 / 0 | 40.72 | 1 |
| accepted / v6:swim_zero | PENDING_HYPOTHETICAL_PLAN | 0.012999 | 374 | 0 / 0 | 34 / 34 | 0 | 23 / 0 | 21 / 0 | 40.29 | 1 |
| accepted / v6:taper | PENDING_HYPOTHETICAL_PLAN | 0.171681 | 49788 | 0 / 0 | 922 / 6988 | 0 | 23980 / 0 | 6939 / 0 | 44.71 | 1 |
| accepted / v6:tri_zero | PENDING_HYPOTHETICAL_PLAN | 0.068582 | 46170 | 0 / 0 | 855 / 855 | 0 | 1858 / 0 | 563 / 0 | 40.37 | 1 |
| accepted / v6:unconfirmed_swim_capability | catalog_coverage_unsatisfied | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.46 | 0 |
| optimized / current:build_1 | PENDING_HYPOTHETICAL_PLAN | 4.680730 | 1808857 | 13244 / 200001 | 203964 / 204179 | 0 | 160979 / 0 | 32975 / 0 | 66.49 | 7 |
| optimized / current:build_2 | PENDING_HYPOTHETICAL_PLAN | 4.653179 | 1808857 | 13244 / 200001 | 203964 / 204179 | 0 | 160979 / 0 | 32975 / 0 | 66.65 | 7 |
| optimized / current:build_3 | PENDING_HYPOTHETICAL_PLAN | 4.708310 | 1808857 | 13244 / 200001 | 203964 / 204179 | 0 | 160979 / 0 | 32975 / 0 | 65.63 | 7 |
| optimized / current:build_4 | DIAGNOSTIC_TIMEOUT | 7.389187 partial | 3080192 | 27720 / 200001 | 306754 / 337964 | 0 | 208078 / 0 | 145555 / 0 | 153.59 | 7 |
| optimized / historical61:build_1 | PENDING_HYPOTHETICAL_PLAN | 0.032495 | 0 | 19600 / 4227 | 0 / 0 | 102 | 0 / 202 | 0 / 91 | 40.97 | 3 |
| optimized / historical61:build_2 | PENDING_HYPOTHETICAL_PLAN | 0.032367 | 0 | 19600 / 4227 | 0 / 0 | 102 | 0 / 202 | 0 / 91 | 40.95 | 3 |
| optimized / historical61:build_3 | PENDING_HYPOTHETICAL_PLAN | 0.031119 | 0 | 19600 / 4227 | 0 / 0 | 102 | 0 / 202 | 0 / 91 | 41.49 | 3 |
| optimized / historical61:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.036796 | 0 | 32509 / 3 | 0 / 0 | 1 | 0 / 0 | 0 / 1 | 42.37 | 2 |
| optimized / historical61:tri_zero | catalog_capacity_unsatisfied | 0.014398 | 2394 | 0 / 0 | 63 / 63 | 0 | 52 / 0 | 47 / 0 | 40.21 | 0 |
| optimized / previous61:build_1 | PENDING_HYPOTHETICAL_PLAN | 0.032224 | 0 | 19600 / 3081 | 0 / 0 | 95 | 0 / 129 | 0 / 84 | 41.34 | 3 |
| optimized / previous61:build_2 | PENDING_HYPOTHETICAL_PLAN | 0.029520 | 0 | 19600 / 3081 | 0 / 0 | 95 | 0 / 129 | 0 / 84 | 41.49 | 3 |
| optimized / previous61:build_3 | PENDING_HYPOTHETICAL_PLAN | 0.030768 | 0 | 19600 / 3081 | 0 / 0 | 95 | 0 / 129 | 0 / 84 | 41.70 | 3 |
| optimized / previous61:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.041540 | 0 | 32509 / 327 | 0 / 0 | 17 | 0 / 7 | 0 / 16 | 42.48 | 3 |
| optimized / previous61:tri_zero | catalog_capacity_unsatisfied | 0.011258 | 2204 | 0 / 0 | 58 / 58 | 0 | 40 / 0 | 47 / 0 | 40.34 | 0 |
| optimized / v6:all_easy_build | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 39.75 | 1 |
| optimized / v6:all_injured | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.72 | 0 |
| optimized / v6:beginner_recovery | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.86 | 0 |
| optimized / v6:beginner_taper | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.74 | 0 |
| optimized / v6:bike_zero | PENDING_HYPOTHETICAL_PLAN | 0.008956 | 323 | 0 / 0 | 17 / 17 | 0 | 5 / 0 | 15 / 0 | 41.04 | 1 |
| optimized / v6:build_1 | PENDING_HYPOTHETICAL_PLAN | 0.068034 | 0 | 45760 / 11027 | 0 / 0 | 158 | 0 / 505 | 0 / 143 | 44.12 | 4 |
| optimized / v6:build_2 | PENDING_HYPOTHETICAL_PLAN | 0.069186 | 0 | 45760 / 11027 | 0 / 0 | 158 | 0 / 505 | 0 / 143 | 43.91 | 4 |
| optimized / v6:build_3 | PENDING_HYPOTHETICAL_PLAN | 0.072494 | 0 | 45760 / 11027 | 0 / 0 | 158 | 0 / 505 | 0 / 143 | 44.07 | 4 |
| optimized / v6:build_4 | PENDING_HYPOTHETICAL_PLAN | 0.014767 | 0 | 2701 / 579 | 0 / 0 | 25 | 0 / 9 | 0 / 24 | 41.21 | 2 |
| optimized / v6:candidate | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.36 | 1 |
| optimized / v6:candidate_no_dates | availability_required | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 41.01 | 1 |
| optimized / v6:candidate_one_day | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.96 | 1 |
| optimized / v6:candidate_shortage | catalog_empty | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 39.69 | 0 |
| optimized / v6:injury_run | restricted_zero_base_allocation_unavailable | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.77 | 0 |
| optimized / v6:limited_dates | PENDING_HYPOTHETICAL_PLAN | 0.077906 | 46170 | 0 / 0 | 855 / 855 | 0 | 1858 / 0 | 563 / 0 | 40.84 | 1 |
| optimized / v6:long_bike_only | PENDING_HYPOTHETICAL_PLAN | 0.004452 | 2 | 0 / 0 | 2 / 2 | 0 | 0 / 0 | 2 / 0 | 39.49 | 1 |
| optimized / v6:minimum | swipe_selection_invalid | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.60 | 0 |
| optimized / v6:missing_swim_capability | catalog_coverage_unsatisfied | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.73 | 0 |
| optimized / v6:recovery | PENDING_HYPOTHETICAL_PLAN | 0.272630 | 62748 | 0 / 0 | 1162 / 11373 | 0 | 40735 / 0 | 11321 / 0 | 47.50 | 1 |
| optimized / v6:repeat_bike | PENDING_HYPOTHETICAL_PLAN | 0.009289 | 4 | 0 / 0 | 4 / 4 | 0 | 0 / 0 | 2 / 0 | 39.32 | 1 |
| optimized / v6:repeat_explicit | PENDING_HYPOTHETICAL_PLAN | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.73 | 1 |
| optimized / v6:run_zero | PENDING_HYPOTHETICAL_PLAN | 0.023218 | 4008 | 0 / 0 | 167 / 167 | 0 | 367 / 0 | 93 / 0 | 40.94 | 1 |
| optimized / v6:swim_zero | PENDING_HYPOTHETICAL_PLAN | 0.014353 | 374 | 0 / 0 | 34 / 34 | 0 | 23 / 0 | 21 / 0 | 41.10 | 1 |
| optimized / v6:taper | PENDING_HYPOTHETICAL_PLAN | 0.175888 | 49788 | 0 / 0 | 922 / 6988 | 0 | 23980 / 0 | 6939 / 0 | 44.75 | 1 |
| optimized / v6:tri_zero | PENDING_HYPOTHETICAL_PLAN | 0.073689 | 46170 | 0 / 0 | 855 / 855 | 0 | 1858 / 0 | 563 / 0 | 40.88 | 1 |
| optimized / v6:unconfirmed_swim_capability | catalog_coverage_unsatisfied | n/a | 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | 0 / 0 | 40.93 | 0 |

## Remaining timeout

`current:build_4` remains a timeout, not a proof of infeasibility. Its profile shows the short exact join reaching its work ceiling followed by ongoing DP combination expansion. The unchanged required swimming template has high load 54.9, all other eligible loads are integers, and the high budget is 110. A valid plan can contain one or two swims; its fractional total is therefore .9 or .8, so exact 550 is unavailable. The exact shortcut correctly falls back. The larger week-four high/Z5 option space then requires a nonexact optimum across the original count bound. No new nonexact lattice-bound strategy is claimed or activated. Counters above bound the actual remaining expansion; scheduling calls remain a small fraction of elapsed search. No timeout or rule was relaxed.

All four V6 BUILD cases now return. Previous61 and historical61 BUILD 1-3 now return; their already-completed BUILD 4 outcomes remain exact. Current BUILD 1-3 now return. Beginner, zero-history, recovery, taper, restriction, capability, explicit-repeat, and availability cases remain regression checks with full-output equality where the accepted engine returned.

The prospective budget/sport-time/suitability diagnostics are separate from legacy validity. In particular a returned legacy plan can fail the prospective per-sport active-time policy; missing swim time remains UNVERIFIED. See [policy gap](JOREN_V6_BUDGET_POLICY_GAP.md).

## Reproduction and custody

From backend, run each command to completion before the next, using new output paths:

```text
python -B -m benchmarks.v6_planner_performance --variant accepted --output NEW_ACCEPTED_COLD
python -B -m benchmarks.v6_planner_performance --variant optimized --output NEW_OPTIMIZED_COLD
python -B -m benchmarks.v6_planner_performance --variant accepted --preloaded --output NEW_ACCEPTED_PRELOADED
python -B -m benchmarks.v6_planner_performance --variant optimized --preloaded --output NEW_OPTIMIZED_PRELOADED
python -B -m benchmarks.v6_planner_performance --variant accepted --instrument --output NEW_ACCEPTED_PROFILE
python -B -m benchmarks.v6_planner_performance --variant optimized --instrument --output NEW_OPTIMIZED_PROFILE
python -B -m benchmarks.build_search_report
```

Exploratory attempts are preserved under `build-search/exploratory/`; they are excluded from all delivered timing comparisons. Some early exploratory runs overlapped briefly and are not performance evidence. Historical Phase 1 files were not overwritten. The report generator asserts parity/fingerprints and observer transparency before rendering these tables.

| Verified evidence | SHA-256 |
| --- | --- |
| accepted_cold.json | 952b37c611b0e913e793f1ed8f6f32ba970c0be33c8acdbf5417532b25c72cfb |
| accepted_preloaded.json | acd9c2285a0e65f5590dc1d9f90bf016e165387d9ad19254652181037d5ee38c |
| accepted_profile.json | e1a45f93b3e1171a8418d2f27e88eba7d28193fab8c3249fcf6b125cbbeb5697 |
| optimized_cold.json | aec9909e54aa524291b7b4ca53b516e6e33b0d784b993bc0b4e83c2f05a80b1a |
| optimized_preloaded.json | ba9f1071a3d760b76919d0831ffdbd3cf8d76a9de181538a6cddf57b4b85942b |
| optimized_profile.json | 5c99898270670d155061a7ffbe1d8489f85506468667ba57a24a9e417c8d4da5 |
| verification.json | f67d3954e41147021387ce17b038b4eb3e5fd9ce849ca0b9875caeb7a2119062 |
