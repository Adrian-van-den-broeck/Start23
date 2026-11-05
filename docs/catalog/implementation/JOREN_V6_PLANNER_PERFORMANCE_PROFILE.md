# Joren V6 automatic planner performance profile

2026-11-05, Europe/Amsterdam. Offline developer evidence; no activation.

## Baseline and measurement boundaries

Accepted start: `99c03b10f3f373d0756ee01b0cb2ebac944fcfae`, branch
`feat/joren-v6-catalog`. Performance branch `perf/joren-v6-planner`, worktree
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-planner-performance`.
Root/worktree AGENTS.md and current MVP roadmap apply; no nearer backend/docs
AGENTS.md exists. The V6 integration, simulation and remaining-decisions reports
were read. Existing source validation is accepted, not reopened or repeated as a
new source review. Benchmark construction necessarily reads the immutable intake.

The exact accepted `_bounded_selection` body is frozen at
`backend/tests/fixtures/planner_performance/bounded_selection_99c03b1.py.txt`,
SHA-256 `ebff78029d9fdad5314fb8846072fff31dd07967940c0f9de91c1f00509f8d30`.
The harness verifies that digest before installing the reference in a child
process. All other planner functions and all 40 V6 fixture definitions remain
unchanged. This is an offline oracle, not a second runtime engine.

`benchmarks/v6_planner_performance.py` reuses `benchmarks/joren_v6.py` for all
26 V6, five immediately preceding 61-row, five historical 61-row and four current
catalog scenarios. Inputs retain their immutable values, UUIDs and dates.
Hypothetical source-display P and selection metadata remain unapproved and offline.

Cold runs keep the original **eight-second total wall deadline**, starting before
process creation. A ready handshake separates process/stdlib/harness setup, Python
application imports, catalog construction and fixture preparation. Remaining time
after readiness is the original deadline minus setup, never a fresh eight seconds.
The residual setup category includes interpreter/stdlib startup, reference-function
installation, input fingerprinting and pipe/ready-protocol overhead; it is not
misrepresented as a pure interpreter-only measurement.

Preloaded runs separately bound setup at eight seconds, then measure one planner
call and serialization with an eight-second deadline after the ready handshake.
They use already imported modules and a constructed catalog in that same child.
They are labeled **preloaded**, not a completed cold attempt or a production cache
benchmark. A cold timeout is never relabeled successful because a prepared call
returns. The optimization adds no process-wide or cross-athlete cache.

Final timing runs are serial, without simultaneous agent tests/typechecks. Host
load is not controlled and single local wall samples are not an SLA. Initial
exploratory/overlapping runs are excluded from the delivered comparison.

## Instrumentation

Stage wrappers observe initial candidate/capability filtering, target resolution,
existing injury allocation, phase/sport/capability filtering, selection, combination
search, selection-policy checks, schedule feasibility, date placement and anti-stack
checks. Initial inline filtering is measured to the first target-resolution call.
It is combined because the existing implementation performs those predicates in
one comprehension, not separate independently timed sport/capability passes.

Optional AST observers count generated candidate transitions, state evaluations,
state expansions, layer sizes/options, rejected branches, repeated dictionary
states, scheduler recursion and attempted dates. They never change expressions,
branch decisions, option order, dictionary keys or returned values. Instrumented
results are checked against uninstrumented reference/optimized results in tests.
The observers run only in benchmark children; production has no instrumentation.

Partial private checkpoints survive a timeout. Counters are lower bounds at the
last checkpoint, not a claim that an incomplete search explored its whole space.
Layer size counts resident unique states at that depth; evaluation and expansion
counters distinguish the two visits. Repeated states count attempted transitions
whose exact destination key already exists. They include permutations and distinct
load-equivalent paths, not merely repeated workout identities.

Stage times are inclusive/exclusive and nested, so inclusive rows must not be
summed. Active open-stage elapsed values are retained when a timeout prevents a
normal return. Profile timing includes observer overhead and is kept separate
from the uninstrumented cold/preloaded timing comparison. Result JSON serialization
is timed separately from `build_weekly_plan`; independent checking and final pipe
encoding/teardown remain outside the reported planner-call duration but inside
the cold process deadline.

### Cold setup versus actual planner call

| Optimized V6 case | Process/stdlib/harness ready overhead sec | Application imports sec | Catalog sec | Scenario prep sec | Planner call sec | Result JSON encoding sec | Total wall sec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v6:candidate | 0.135760 | 0.453118 | 0.343303 | 0.000104 | 0.006629 | 0.000079 | 1.011663 |
| v6:limited_dates | 0.133222 | 0.409115 | 0.317876 | 0.000086 | 0.037920 | 0.000075 | 0.970410 |
| v6:recovery | 0.137046 | 0.404497 | 0.336096 | 0.000157 | 0.240732 | 0.000073 | 1.183344 |
| v6:tri_zero | 0.134444 | 0.420744 | 0.326964 | 0.000079 | 0.036467 | 0.000077 | 0.984292 |

### Instrumented expansion work

Counters at a timeout are **partial lower bounds**. Profile elapsed times include observer overhead.

| Variant / case | Outcome | Options | Peak layer states | States evaluated / expanded | Transitions | Repeated states | Rejected branches observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference / current:build_1 | TIMEOUT | 41 | 36998 | 55824 / 52749 | 2162688 | 1054701 | 1049313 |
| reference / v6:build_1 | TIMEOUT | 63 | 23487 | 25193 / 21846 | 1376256 | 1104248 | 120872 |
| reference / v6:candidate | pending hypothetical | explicit selection | 0 | 0 / 0 | 0 | 0 | 0 |
| reference / v6:recovery | pending hypothetical | 54 | 15022 | 16389 / 1367 | 73818 | 56739 | 17020 |
| reference / v6:tri_zero | TIMEOUT | 54 | 40732 | 55156 / 31555 | 1703936 | 1345704 | 306057 |
| optimized / current:build_1 | TIMEOUT | 41 | 32525 | 72998 / 57544 | 2359296 | 897904 | 1433098 |
| optimized / v6:build_1 | TIMEOUT | 63 | 22543 | 24237 / 19765 | 1245184 | 948486 | 167484 |
| optimized / v6:candidate | pending hypothetical | explicit selection | 0 | 0 / 0 | 0 | 0 | 0 |
| optimized / v6:recovery | pending hypothetical | 54 | 10211 | 11373 / 1162 | 62748 | 40735 | 21954 |
| optimized / v6:tri_zero | pending hypothetical | 54 | 375 | 855 / 855 | 46170 | 1858 | 44260 |

### Stage timing and date branches

| Variant / case | Initial candidate/capability sec | Phase/sport/capability sec | Target resolution sec | Combination search sec | Policy checks sec | Date placement sec / calls | Anti-stack sec / calls | Date branches / recursion calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference / current:build_1 | 0.000422 | 0.000485 | 0.000116 | 7.304290 (open/partial) | 0.020695 | 0.007437 / 4 | 0.000374 / 19 | 19 / 23 |
| reference / v6:build_1 | 0.000309 | 0.000410 | 0.000113 | 7.070402 (open/partial) | 0.012750 | 0.004498 / 1 | 0.000040 / 3 | 3 / 4 |
| reference / v6:candidate | 0.000325 | 0.000327 | 0.000044 | 0.000000 | 0.000017 | 0.004511 / 1 | 0.000035 / 3 | 3 / 4 |
| reference / v6:recovery | 0.000362 | 0.000327 | 0.000088 | 0.376334 | 0.007370 | 0.004340 / 1 | 0.000033 / 3 | 3 / 4 |
| reference / v6:tri_zero | 0.000285 | 0.000322 | 0.000058 | 7.057680 (open/partial) | 0.034628 | 0.000000 / 0 | 0.000000 / 0 | 0 / 0 |
| optimized / current:build_1 | 0.000418 | 0.000471 | 0.000117 | 7.362248 (open/partial) | 0.028538 | 0.005943 / 4 | 0.000243 / 19 | 19 / 23 |
| optimized / v6:build_1 | 0.000314 | 0.000354 | 0.000120 | 6.854880 (open/partial) | 0.013016 | 0.004443 / 1 | 0.000061 / 3 | 3 / 4 |
| optimized / v6:candidate | 0.000342 | 0.000488 | 0.000053 | 0.000000 | 0.000019 | 0.004528 / 1 | 0.000046 / 3 | 3 / 4 |
| optimized / v6:recovery | 0.000641 | 0.000505 | 0.000093 | 0.329620 | 0.009865 | 0.006445 / 1 | 0.000059 / 3 | 3 / 4 |
| optimized / v6:tri_zero | 0.000297 | 0.000331 | 0.000061 | 0.080677 | 0.000311 | 0.006050 / 1 | 0.000039 / 3 | 3 / 4 |

### Actual filtered candidate counts

| Variant / case | Phase | Count | By sport |
| --- | --- | --- | --- |
| reference / current:build_1 | build | 80 | {"bike": 38, "run": 41, "swim": 1} |
| reference / v6:build_1 | build | 65 | {"bike": 23, "run": 26, "swim": 16} |
| reference / v6:candidate | base | 54 | {"bike": 19, "run": 24, "swim": 11} |
| reference / v6:recovery | recovery | 54 | {"bike": 19, "run": 24, "swim": 11} |
| reference / v6:tri_zero | base | 54 | {"bike": 19, "run": 24, "swim": 11} |
| optimized / current:build_1 | build | 80 | {"bike": 38, "run": 41, "swim": 1} |
| optimized / v6:build_1 | build | 65 | {"bike": 23, "run": 26, "swim": 16} |
| optimized / v6:candidate | base | 54 | {"bike": 19, "run": 24, "swim": 11} |
| optimized / v6:recovery | recovery | 54 | {"bike": 19, "run": 24, "swim": 11} |
| optimized / v6:tri_zero | base | 54 | {"bike": 19, "run": 24, "swim": 11} |

The beginner profile drops from at least **1,703,936** attempted transitions before timeout to **46,170** for a completed search. Resident peak layer size drops from **40,732** to **375**. The former is incomplete work, so this is not a ratio of two completed searches. Build1 still visits more than a million transitions before its profile timeout. Date checks do not explain that residual cost.


## Root causes and alternatives examined

The dominant cost is the dynamic-programming combination expansion, not Python
startup, workbook construction, target allocation, sport-share diagnostics or date
placement. The old bound admits totals up to target plus the largest eligible
workout, although a terminal plan must satisfy the much narrower strict fit
predicate based on the smallest eligible load. Above-target prefixes continue
expanding even after no valid or competitive extension remains.

The added workouts increase eligible options and combinations. Existing grouping
already chooses the smallest UUID for equal sport/load/bucket/Z5 facts; ordering
already uses load, sport and UUID. Existing state merging keeps the lexicographically
smallest path for each total/high-load/sport-count/high-count/limited-use/Z5 state,
but many permutations still reach those states and cost a full transition first.
Repeated templates are intentional; they cannot simply be removed.

Build weeks retain many combinations below target, with per-sport count dimensions,
high-load counts, required build intensity/Z5 conditions and a 24-occurrence bound.
The new overshoot bounds do not eliminate that combinatorial cost. Those searches
still have diagnostic timeouts. A failed-to-return search is not a proof of
mathematical impossibility.

In sampled builds only a few feasible candidates reach the scheduler; measured
date placement and anti-stack work are small beside millions of transitions.
Filtering and injury checks remain early; no evidence supports weakening them.
The prospective 50/30/20 target is diagnostic only and contributes no active
sport-allocation score in this search. The historical score remains load error,
build high-load error, count and UUID path.

No new equivalence/dominance elimination, permutation reordering, integer-grid
quantization, scientific coefficient change, schedule-cache policy, timeout
increase or constraint relaxation is introduced. Broader state compression would
need a separate proof covering prefixes, limited uses, sport caps, Decimal
arithmetic and deterministic canonical paths. It is not assumed safe here.

Final verification and commit lineage: [optimization report](JOREN_V6_PLANNER_OPTIMIZATION_REPORT.md).
