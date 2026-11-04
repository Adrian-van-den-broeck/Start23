# Joren V6 beginner and actual-planner validation

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

## Result: arithmetic capacity exists, full automatic policy readiness does not

Using source-display P as an **unapproved hypothetical** planner input, 33 all-easy
combinations provide exactly one workout per sport within 45. The unchanged actual
planner returns a pending three-session draft for BIKE-023/RUN-024/SWIM-021 at
43.1. It returns no completed automatic search for the full V6 beginner deck within
the unchanged 8-second diagnostic bound. These are separate findings.

The minimum 15.1 + 5.8 + 8.4 = **29.3** is arithmetically within 45, but the actual
explicit-selection policy rejects it as `swipe_selection_invalid`: the 15.7 gap
to target is at least the eligible minimum load 5.8. The example 20.2 + 14.5 +
8.4 = **43.1** has a 1.9 gap and passes that existing fit predicate. Neither fact
authorizes a baseline increase or a generic ten-minute running prescription.

## Fixture scope and approved policy

The actual unchanged `build_weekly_plan` is called, without monkeypatching,
timeouts or relaxed constraints. Monday 2026-10-26, Europe/Amsterdam; default
race 2027-03-15; zero reported history -> actual baseline **45.0**; all seven dates
and confirmed HR RUN/BIKE plus pace SWIM capabilities unless specified. These
are synthetic capable-athlete fixtures, not proof of any real athlete's readiness.
No per-date available-minute budget or individualized maximum session duration
exists in the current planner input. Those missing decisions are reported.

All 77 rows have isolated draft projections. Bucket/phases/capabilities/repeats
are proposals. The legacy segment type cannot represent stationary rests; exact
rest strings are appended to preceding instructions for simulation, with full
typed events in the immutable sidecar. No zone, RPE, meters or active seconds is
assigned to rest. This is not a production canonical import. Session source RPE
remains in the manifest; simulated aggregate block ranges are explicitly proposed.
Operational P remains null. The projection deliberately uses displayed source P
to test the requested examples, not silently approved precision or V2 compatibility.

Joren's current approved **triathlon weekly planned-P target** is BIKE 50%, RUN
30%, SWIM 20%. It is a target, not a hard equality or load overshoot allowance.
It does not override single-sport goals or injury restrictions. For the 43.1
candidate the shares are 46.8677 / 33.6427 / 19.4896%. Relative to the full 45
budget its sport loads are below 22.5 BIKE and 9 SWIM, above 13.5 RUN; those
target components are not established independent hard caps.

The diagnostic share-nearest candidate is BIKE-023/RUN-023/SWIM-021 = 40.2,
50.2488 / 28.8557 / 20.8955%. Its score orders absolute share deviation, then
distance to budget, then IDs. That **unapproved scoring choice** illustrates
tradeoffs only; it does not select a default or establish better athlete suitability.
The 43.1 candidate remains the requested concrete witness, not an adopted plan.

## Maximum high active time, independently per sport

The existing isolated C2.1 evaluator enforces **at most 20%**, including exactly
20% and all-easy 0%, from ordered active segment seconds. Z1/Z2 low, Z3-Z5 high
uses approved BR-003 taxonomy. Rests are excluded. Missing reliable time yields
UNVERIFIED and null ratio; absent sports yield NOT APPLICABLE. The 43.1 candidate
has BIKE 2400 low seconds and RUN 1500 low seconds, both 0% high. Its 500m Z2
swim is entirely low-zone, but has no prescribed time: numeric time compliance
remains UNVERIFIED. Reference paces do not fill that denominator.

For mixed BIKE-020 the six 30s sprints are 180 high / 5580 active seconds =
3.2258%, not a wholly high 93-minute workout. BIKE-021 gives 240 / 6240 = 3.8462%.
RUN-017 has 1800 high / 3600 active seconds = 50%, failing the per-sport ceiling
when alone. Existing interval spacing, injury, recovery, taper and progression
rules are unchanged. No whole-session high bucket substitutes for this check.

Current automatic selection still uses its historical whole-session high-load
budget/minimum and fit tolerance. It does not yet implement the approved per-sport
active-time maximum or the 50/30/20 target. The diagnostic wrapper rejects a
budget overshoot or a complete-time ceiling violation for V6-policy purposes;
it does not alter or persist a plan. A source-grid match is not a policy pass.

## All actual V6 scenarios

| Case | Engine outcome | Target -> selected P; sessions | Code / policy assessment |
| --- | --- | --- | --- |
| all_easy_build | PENDING_HYPOTHETICAL_PLAN | 47.410 -> 43.1; 3 | UNVERIFIED_SWIM_TIME |
| all_injured | PENDING_HYPOTHETICAL_PLAN | 0 -> 0; 0 | DIAGNOSTIC_PASS; SUITABILITY/OPERATIONAL_P UNAPPROVED |
| beginner_recovery | FAIL_CLOSED | unreturned -> unreturned; unreturned | swipe_selection_invalid |
| beginner_taper | FAIL_CLOSED | unreturned -> unreturned; unreturned | swipe_selection_invalid |
| bike_zero | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 45.3; 2 | FAIL_CLOSED_FOR_V6_POLICY |
| build_1 | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| build_2 | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| build_3 | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| build_4 | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| candidate | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 43.1; 3 | UNVERIFIED_SWIM_TIME |
| candidate_no_dates | FAIL_CLOSED | unreturned -> unreturned; unreturned | availability_required |
| candidate_one_day | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 43.1; 3 | UNVERIFIED_SWIM_TIME |
| candidate_shortage | FAIL_CLOSED | unreturned -> unreturned; unreturned | catalog_empty |
| injury_run | FAIL_CLOSED | unreturned -> unreturned; unreturned | restricted_zero_base_allocation_unavailable |
| limited_dates | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| long_bike_only | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 393.8; 1 | FAIL_CLOSED_FOR_V6_POLICY |
| minimum | FAIL_CLOSED | unreturned -> unreturned; unreturned | swipe_selection_invalid |
| missing_swim_capability | FAIL_CLOSED | unreturned -> unreturned; unreturned | catalog_coverage_unsatisfied |
| recovery | PENDING_HYPOTHETICAL_PLAN | 300.00 -> 300.0; 3 | UNVERIFIED_SWIM_TIME |
| repeat_bike | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 45.3; 3 | FAIL_CLOSED_FOR_V6_POLICY |
| repeat_explicit | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 40.4; 2 | DIAGNOSTIC_PASS; SUITABILITY/OPERATIONAL_P UNAPPROVED |
| run_zero | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 45.2; 2 | FAIL_CLOSED_FOR_V6_POLICY |
| swim_zero | PENDING_HYPOTHETICAL_PLAN | 45.0 -> 43.9; 3 | UNVERIFIED_SWIM_TIME |
| taper | PENDING_HYPOTHETICAL_PLAN | 175.00 -> 175.0; 3 | UNVERIFIED_SWIM_TIME |
| tri_zero | DIAGNOSTIC_TIMEOUT | unreturned -> unreturned; unreturned | no result within bound |
| unconfirmed_swim_capability | FAIL_CLOSED | unreturned -> unreturned; unreturned | catalog_coverage_unsatisfied |

`candidate_one_day` consolidates three sessions with
`workouts_consolidated_on_available_dates`; date placement does not prove available
minutes. No dates, missing/empty swim capability, zero-history injury allocation
and an empty deck fail closed. All-injured produces pending rest-only, target zero.
Single-sport fixtures retain only their goal sport; no 50/30/20 override occurs.
RUN-only 45.2 and BIKE-only 45.3 are historical planner fits above 45 and therefore
fail the requested budget ceiling in the V6 diagnostic; they are not accepted
beginner plans. SWIM-only has unknown time, not zero actual swimming time.

The broad unapproved deck exposes the old long-bike fallback: a lone BIKE-013
returns 393.8 / 420min against 45. The V6 policy assessment fails closed for that
overshoot; manifest metadata continues to hold it from automatic beginner use.
No universal duration threshold is invented. Repeated automatic BIKE-022 gives
45.3 and likewise fails the budget check. Explicit BIKE-023 twice gives 40.4
with distinct supplied occurrence UUIDs. Unallocated draft occurrence IDs are
reported as such; only persistence/explicit occurrence input supplies identities.

Established-athlete build fixtures contain four prior approved BUILD weeks, each
planned=realized 500 with 250/150/100 sport components, and an independently
positive onboarding baseline. Race weeks 9/8/7/6 give build 1-4, target 550; Z5
eligibility remains restricted to build 4. All four V6 automatic searches time out.
Established recovery target 300 and taper 175 have exact source-grid witnesses,
both with unknown swim time. The 43.1 beginner candidate is rejected at reduced
recovery 25.86 and taper 15.085 targets; easier V6 rows do not prove all future
low-budget weeks feasible. A separately all-low build-deck fixture accepts 43.1
at target 47.410, showing no required high minimum when no high candidates exist;
the unchanged full-deck selector still needs later policy integration.

## Consecutive weeks and registration evidence

Hypothetical independent observed loads BIKE 20, RUN 14, SWIM 8 are supplied
solely as registration fixtures. No observed swimmer minutes are asserted, and
no source P is relabeled as measured load. The weekly registration and target
engine receives its real supported method/version semantics.

| SWIM registration | Known subtotal | Next target / basis | Progression evidence |
| --- | --- | --- | --- |
| measured | 42 | 47.410 / realized_progression | complete hypothetical measured registration |
| partial_observed | 37 | 43.1 / prior_planned_hold | partial_or_unavailable_load |
| skipped | 34 | 34 / realized_baseline | complete hypothetical registration including explicit skip |
| unknown | 34 | 43.1 / prior_planned_hold | unknown_workout_completion |

Complete 42 versus prior planned 43.1 follows the existing progression band
and yields 47.410, not an invented new formula. Unknown and partial observations
hold the prior approved planned 43.1. Explicit swim skip yields complete realized
34 and target 34; the 43.1 candidate then fails fit. Week three after an incomplete
second week holds the second approved selected 43.1. Partial 37 is a known subtotal,
not a complete weekly realized load. Realized V2 regression tests cover measured
priority, version dispatch, unsupported/mixed fallback, immutable P, correction,
partial observations, skips, unknowns and stale evidence independently.

## Search performance and historical timeout replay

| Mode | Attempts | Timeouts | Returned pending | Returned fail-closed |
| --- | --- | --- | --- | --- |
| v6 | 26 | 6 | 12 | 8 |
| previous61 | 5 | 4 | 1 | 0 |
| historical61 | 5 | 4 | 1 | 0 |
| current | 4 | 4 | 0 | 0 |

The 40-case run uses separate serial processes, an unchanged **8s wall
budget including imports/setup**, and owned subprocess termination. No planner
timeout or algorithm was modified. Historical CURRENT builds 1-4 and original
D61 tri_zero/builds 1-3 reproduce all **eight** prior timeout slots. Original
61-row D61 uses its original fixed-matrix source P; `previous61` instead uses
accepted C2 IF² P and C2.1 corrected structures. V6 uses all 77 new source rows.
Original source IDs and ordering are retained. These different source-method
fixtures are explicitly separated, not portrayed as one unchanged data set.

V6 tri_zero, limited_dates and all builds 1-4 time out: six V6 automatic gaps.
Previous61 tri_zero/builds 1-3 time out, while build4 returns; V6 build4 also
times out, an additional V6 performance gap at the same bound. This does not
prove infeasibility or a precise slowdown. Explicit witnesses are not automatic
search-performance passes. The first preliminary v1 run used incomplete returning-
athlete fixture flags and is retained as exploratory evidence, superseded by v2;
its CURRENT fail-closed results are not used as historical timeout comparisons.

The final independent repeat is archived as v3 and reproduces all 40 v2 outcome
payloads byte-for-byte, including every returned selection and all 18 timeouts.
It ran after the full backend suite and static checks, with no overlapping agent
test/typecheck processes. Timings are local diagnostics, not an SLA or a controlled
host-load experiment. The v3 timing metadata explicitly records serial workers
and uncontrolled host load; the preliminary v1/v2 `serial_uncontended_workers`
label overstated host control and must not be interpreted as measured idle-host
evidence. Earlier files remain preserved. No claim about production latency,
exact optimality, or unreturned selection is made. Complete automatic search and
future accepted exact-P precision performance remain open gates.

Reproduce from backend:

```text
python -B -m benchmarks.joren_v6 --private-output NEW_PRIVATE_PATH --timings NEW_TIMING_PATH
```

[Final scenario evidence](joren_v6_planner_probes_v3.json) and
[separate wall timings](joren_v6_planner_timings_v3.json) contain all returned
source IDs, dates, shares, warnings, input fingerprints and coverage statuses.

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).
