# Joren V6 planner optimization report

2026-11-05, Europe/Amsterdam. Local performance remediation; no release.

## Scope and isolation

Start: `99c03b10f3f373d0756ee01b0cb2ebac944fcfae` on accepted
`feat/joren-v6-catalog`. New isolated branch `perf/joren-v6-planner`, worktree
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-planner-performance`.
Final implementation/delivery SHAs are recorded in the delivery addendum.

The only runtime change is two overshoot-pruning conditions and a Decimal-trap
fallback inside the existing deterministic `_bounded_selection`. Frozen oracle,
profiling/checking harness, regression fixtures and these reports are offline
support. No new source intake, accepted method, athlete scope or selection policy
is introduced. No automatic C3–C8 continuation occurs.

The A5/A6 release branch/worktree is excluded. Railway configuration, Supabase,
mobile release gates, source workbooks, immutable V6 intake, historical planned
or realized loads, RPE mappings and calculation versions are untouched. No push,
merge, deploy, migration, publish or database access is performed.

## Exact change and preservation argument

Let T be the unchanged target, m the unchanged smallest eligible load, L a prefix
total and B the first score component of an already found feasible incumbent.
`InternalLoad` validates finite nonnegative values; appending workouts cannot
decrease the running total under the caller's fixed Decimal context.

1. If L > T and the **original terminal subtraction/comparison**
   `abs(T - L) >= m` is true, no extension can satisfy `abs(T - total) < m`.
   Such prefixes and all descendants are invalid for the existing fit predicate.
2. If L > T and the **original score expression** `abs(L - T) > B` is true,
   no extension can beat the existing feasible incumbent's first score component.
   B can only improve. Strict inequality retains equal-score candidates for every
   later high-load/count/UUID tie-break.

The subtraction directions are deliberately different: directed Decimal rounding
can distinguish `L-T` from `T-L`. Each bound uses the exact expression of the
predicate/score it proves. No rounded additive threshold or quantized load grid
is substituted. Callers trapping Inexact/Rounded/Subnormal/Underflow/Clamped
keep the original search, so these extra observations introduce no new trapped
rounding/underflow exceptions. Original arithmetic and physiological calculations
are otherwise unchanged.

The old `max_total` guard remains. Options, grouping, prefix handling, state keys,
path replacement comparisons, count limits, all terminal constraints, feasibility
callbacks, scheduling and score ordering remain unchanged. The first bound only
removes states with no valid extension. The second only removes states whose
extensions cannot win. A pruned total cannot merge into a better-total state:
exact total is part of the existing key, and extensions cannot reduce its error.
Canonical representatives of surviving competitive states are therefore unchanged.
The existing pure scheduling callback is still applied before accepting an
incumbent. No actor/athlete, revision, occurrence, persistence or retry path changes.

This establishes preservation of the search's existing returned optimum/tie-break,
including existing early-exact-fit stopping semantics. It does not repair historical
policy gaps or make the hypothetical V6 deck operationally approved.

## Correctness evidence

The exact accepted function is the reference oracle. Seeded differential cases
cover reversed input order, mixed buckets/sports, prefixes, repeats, maximum uses,
sport caps, fixed composition/count, infeasible decks and pure feasibility rejection.
Additional tests cover strict boundaries, UUID ties, Decimal precisions and four
rounding directions, zero loads, trapped arithmetic, observer transparency and
deterministically reduced transition counts. Full-plan comparisons preserve
snapshots, dates, warnings, private values and occurrence identities.

Existing A9 historical output/intermediate fingerprints and consecutive-week
parity remain unchanged. For all completed 40-case reference outcomes, full
canonical plan or fail-closed code/message hashes must match exactly. Timeout
slots are compared as timeout slots, not assigned fictitious oracle plans.

Newly returned plans receive direct independent checks without calling the
planner's selection-policy or schedule predicates: source/version/segment/load
identity, sums, goal/injury scope, capabilities, dates, phase/Z5, legacy fit and
build high-load budget, sport caps, rest feasibility and absolute high-spacing.
Prospective budget/one-per-sport/segment-active-time diagnostics are separate.
Missing swimming time remains UNVERIFIED; no reference pace creates athlete minutes.

| Mode | Attempts | Before timeouts | After timeouts | Before/after pending | Before/after fail-closed |
| --- | --- | --- | --- | --- | --- |
| v6 | 26 | 6 | 4 | 12 / 14 | 8 / 8 |
| previous61 | 5 | 4 | 3 | 1 / 1 | 0 / 1 |
| historical61 | 5 | 4 | 3 | 1 / 1 | 0 / 1 |
| current | 4 | 4 | 4 | 0 / 0 | 0 / 0 |

Overall: **18 -> 14 timeouts**, **14 -> 16 hypothetical pending returns**, **8 -> 10 fail-closed returns**. All 22 reference completions have exact full-output parity. All 40 input fingerprints match. All 16 returned optimized plans pass the direct legacy constraint checks. This is not prospective V6 policy approval.

All eight earlier historical timeout slots reproduce in the reference; seven remain after pruning. The resolved historical slot returns fail-closed, not a hypothetical valid training plan.

| Previously timed-out case | New returned result | Load / target | Independent assessment |
| --- | --- | --- | --- |
| historical61:tri_zero | catalog_capacity_unsatisfied | No plan returned | not applicable |
| previous61:tri_zero | catalog_capacity_unsatisfied | No plan returned | not applicable |
| v6:limited_dates | TR-SWIM-021, TR-BIKE-022, TR-RUN-027 | 45.1 / target 45.0 | legacy PASS; budget False; swim UNVERIFIED |
| v6:tri_zero | TR-RUN-027, TR-BIKE-022, TR-SWIM-021 | 45.1 / target 45.0 | legacy PASS; budget False; swim UNVERIFIED |



The newly returned automatic V6 beginner plan uses BIKE-022/RUN-027/SWIM-021
and totals **45.1 against 45**. It passes the unchanged legacy fit tolerance but
fails the prospective hard budget diagnostic. Its all-Z2 swim has unknown active
time. This is a faster returned **hypothetical pending** result, not an approved
beginner recommendation. The manually selected 43.1 proposal remains a distinct
successful explicit-selection witness, not proof of automatic selection readiness.

## Remaining gates and result

The prospective 50/30/20 planned-load target, per-sport maximum 20% high active
time with no high minimum, 45 starting budget and suitable one-per-sport beginner
experience remain diagnostic only. The old selector's tolerance/high-load rules
are preserved; they are not represented as implementing those new policies.
Source-P authority/precision, swim Z3 coefficient/reference convention, athlete
suitability, distance-time coverage and formal selection metadata remain separate
approval gates. No operational P or metadata is activated.

The build-search state explosion remains. Resolving it needs further bounded
algorithm work and parity proofs, not larger timeouts or weaker constraints.
Returning a plan does not settle scientific suitability, policy approval or an
unreturned search's feasibility. PostgreSQL/pgTAP for Realized V2 remains deferred;
no database or mobile/release gate is claimed passed by local unit tests.

## Verification

Using the existing project virtualenv with this worktree's backend as cwd:

| Gate | Actual result |
| --- | --- |
| Complete backend `python -B -m pytest -q -p no:cacheprovider` | **1,507 passed**, 162.69s; one existing Starlette/httpx deprecation warning |
| Added performance/correctness regressions | 129 new tests; no existing test changed or weakened |
| Earlier focused differential + A9 run | 122 passed, 16.74s; final full suite additionally includes the 22 completed-corpus replay tests and corpus/beginner-work assertions |
| Ruff check | PASS: app, tests, existing C2/V6 benchmarks and new performance harness |
| Ruff formatting | PASS: 172 files |
| Strict mypy | PASS: 172 source files; strict=true |
| Complete cold matrix | 40 original inputs per variant; all 40 input fingerprints match; all 22 reference completions have exact full-output parity |
| Preloaded comparison | Nine cases per variant, separately labeled; all sampled build timeouts remain |
| Direct independent checks | All 16 returned optimized plans pass legacy checks; prospective budget/swim-time gaps remain explicit |
| Deterministic work regression | Former V6 beginner timeout completes in 46,170 observed transitions; test bounds work below 100,000 without a machine-dependent latency assertion |
| Historical A9, Realized V2, API/OpenAPI/privacy, identity/retry/stale safeguards | Included in passing complete backend suite |
| Sources and protected runtime paths | Final diff/custody checks in delivery addendum; no source intake or scientific-rule changes |
| PostgreSQL/pgTAP | Deferred for Realized V2; no database access, installation or migration |
| Mobile/release checks | Not changed or reopened by this backend search optimization; no mobile/API contract changes |

The full suite was run after the final runtime change, including the Decimal-trap
fallback. The final serial cold/preloaded/profile matrix also uses that final
runtime code. Subsequent changes are report/evidence assembly only.

Delivered evidence under `performance/`: `reference_cold_verified.json`,
`optimized_cold_verified.json`, `reference_preloaded.json`,
`optimized_preloaded.json`, `reference_profile_verified.json` and
`optimized_profile_verified.json`. Early exploratory measurements and scratch
checkpoints are excluded from these deliverables.

Reproduce from backend, serially, with fresh explicit private output paths:

```text
python -B -m benchmarks.v6_planner_performance --variant reference --output NEW_REFERENCE_COLD
python -B -m benchmarks.v6_planner_performance --variant optimized --output NEW_OPTIMIZED_COLD
python -B -m benchmarks.v6_planner_performance --variant reference --preloaded --only v6:tri_zero v6:candidate v6:limited_dates v6:recovery v6:build_1 v6:build_2 v6:build_3 v6:build_4 current:build_1 --output NEW_REFERENCE_PRELOADED
python -B -m benchmarks.v6_planner_performance --variant optimized --preloaded --only v6:tri_zero v6:candidate v6:limited_dates v6:recovery v6:build_1 v6:build_2 v6:build_3 v6:build_4 current:build_1 --output NEW_OPTIMIZED_PRELOADED
python -B -m benchmarks.v6_planner_performance --variant reference --instrument --only v6:tri_zero v6:candidate v6:recovery v6:build_1 current:build_1 --output NEW_REFERENCE_PROFILE
python -B -m benchmarks.v6_planner_performance --variant optimized --instrument --only v6:tri_zero v6:candidate v6:recovery v6:build_1 current:build_1 --output NEW_OPTIMIZED_PROFILE
```

No shell/source checksum override enables a different reference; its pinned digest
must match. Private benchmark output is never an athlete-facing API payload.
Identical immutable output retries are read-only; different timing samples require
new output paths. Timing differences on future hosts are expected and do not
permit changed deterministic plan fingerprints.

## Local delivery

Exact verified implementation SHA will be recorded after local commit, followed
by a documentation-only addendum commit. Its final tip SHA is supplied in the
delivery response because a commit cannot embed its own hash. Resolve the delivered
tip with `git rev-parse perf/joren-v6-planner`.

WOMBO V6 PLANNER PERFORMANCE INVESTIGATED — FURTHER WORK REQUIRED
