# V6 estimated planned swimming active time

2026-11-05, Europe/Amsterdam. Private offline evidence; no activation.
Decision version `joren-v6-partial-approval-1`; estimator version
`joren-v6-swim-reference-active-time-offline-1`.

Joren's exact question/answer and narrow approval scope are in the
[partial approval register](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md#4-estimated-planned-swimming-active-time).
He permits the confirmed two-decimal reference paces to estimate planned active
swimming duration. This does not provide individualized prescribed or performed
time and does not approve an operational safety gate or planned-P method.

## Pure estimator and preserved source

`backend/benchmarks/v6_partial_approval.py` contains deterministic, I/O-free
functions operating on immutable source records. The separate evidence writer
reads pinned workbooks and writes private artifacts; no application module imports
the new estimator. No FastAPI, database, Supabase, LLM or planner is invoked by
the estimator. It is outside the application package and never changes the
existing C2.1 authoritative-duration evaluator.

For each original ordered `SwimDistance` event in zone z:

`estimated active minutes = exact prescribed meters / 100 * reference minutes[z]`

Z1–Z5 reference minutes/100m: **2.17 / 2.00 / 1.83 / 1.67 / 1.50**.
All operands become exact fractions before arithmetic. No Decimal-context or
intermediate rounding affects sums or comparisons. No IF, sport factor, load,
session focus, CSS, pace capability or athlete-specific pace enters this estimate.
Z1/Z2 contribute LOW; Z3–Z5 contribute HIGH. Each stationary `WallRest` retains
its original seconds, token, source cell and segment identity but adds **zero**
active minutes. Repeated blocks are retained individually in order.

The result retains the entire original immutable workout, including all raw cell
values/XML, source hash, template version, exact distance, event objects, sequence,
token and character spans. Original `planned_duration_seconds` and individual
`duration_seconds` remain **None**. Estimated minutes are separate fields with
`ESTIMATED_FROM_APPROVED_REFERENCE_PACE` provenance. No original cell or duration
is filled or overwritten. No performed-duration or Realized TSS field is created.

Inputs must be distance-only swimming with ordered, positive whole-meter zone
segments whose totals reconcile with the preserved distance and zone aggregates.
Unsupported/missing prescriptions, mismatched totals and invalid times/zones fail
closed. No fallback to aggregate focus or an assumed zero-duration segment exists.

## Sport-week diagnostic; no operational acceptance

The SWIM evaluator receives a local Monday and explicitly dated occurrences;
all occurrences must fall Monday–Sunday and have distinct supplied IDs. Repeated
sources are counted as separate occurrences for arithmetic only; this grants no
workout repetition eligibility. Empty input is `NOT_APPLICABLE`, ratio None.

Sum ordered estimated LOW/HIGH minutes across those swim occurrences. The result
is `ESTIMATED_COMPLIANT` exactly when `5 * HIGH <= LOW + HIGH`, including exactly
20% and zero HIGH; otherwise `ESTIMATED_EXCEEDED`. This is a weekly **per-sport**
ratio. Bike/run time never dilutes swimming HIGH. Individual-workout diagnostics
below treat each workout as the only swim in an illustrative week; they are not
per-workout eligibility rules. A mixed workout can be combined with LOW swimming
to change the weekly ratio, subject to still-open suitability/repetition policy.

`authoritative_duration_compliance` remains **UNVERIFIED** and
`operational_safety_gate_approved` remains **false** on all estimated results.
The unchanged C2.1 evaluator still returns UNVERIFIED for these original swims.
Run and bike retain their separate authoritative-duration checks. No estimate is
converted into a C2.1 ACCEPTED result or passed into an operational planner gate.

For the hypothetical 43.1 witness, BIKE-023/RUN-024 retain 40/25 authoritative
LOW minutes. SWIM-021 adds a separate **estimated** 10 LOW minutes, zero HIGH.
That does not approve the witness, supply individual time availability or close
its source-method/suitability gates.

## All 22 original V6 swims

Minutes are exact at the precision shown; percentages are review displays only.
`C` means ESTIMATED_COMPLIANT and `E` means ESTIMATED_EXCEEDED for the single-swim
week diagnostic. The range uses the illustrative sensitivity scenario below.
Every row retains missing individualized duration and UNVERIFIED authoritative
compliance, regardless of C/E.

| Source ID | LOW min | HIGH min | Active min | HIGH % | Sensitivity HIGH % range | Estimated result |
| --- | --- | --- | --- | --- | --- | --- |
| TR-SWIM-001 | 20 | 0 | 20 | 0 | 0–0 | C |
| TR-SWIM-002 | 30 | 0 | 30 | 0 | 0–0 | C |
| TR-SWIM-003 | 40 | 0 | 40 | 0 | 0–0 | C |
| TR-SWIM-004 | 50 | 0 | 50 | 0 | 0–0 | C |
| TR-SWIM-005 | 60 | 0 | 60 | 0 | 0–0 | C |
| TR-SWIM-006 | 70 | 0 | 70 | 0 | 0–0 | C |
| TR-SWIM-007 | 80 | 0 | 80 | 0 | 0–0 | C |
| TR-SWIM-008 | 90 | 0 | 90 | 0 | 0–0 | C |
| TR-SWIM-009 | 100 | 0 | 100 | 0 | 0–0 | C |
| TR-SWIM-010 | 12 | 18.3 | 30.3 | 60.3960 | 60.2708–60.5211 | E |
| TR-SWIM-011 | 12 | 36.6 | 48.6 | 75.3086 | 75.2112–75.4058 | E |
| TR-SWIM-012 | 12 | 33.4 | 45.4 | 73.5683 | 73.4613–73.6750 | E |
| TR-SWIM-013 | 12 | 33.4 | 45.4 | 73.5683 | 73.4613–73.6750 | E |
| TR-SWIM-014 | 10 | 45.75 | 55.75 | 82.0628 | 81.9856–82.1397 | E |
| TR-SWIM-015 | 12 | 15 | 27 | 55.5556 | 55.4114–55.6995 | E |
| TR-SWIM-016 | 12 | 22.5 | 34.5 | 65.2174 | 65.0849–65.3495 | E |
| TR-SWIM-017 | 12 | 30 | 42 | 71.4286 | 71.3093–71.5474 | E |
| TR-SWIM-018 | 12 | 15 | 27 | 55.5556 | 55.4114–55.6995 | E |
| TR-SWIM-019 | 12 | 22.5 | 34.5 | 65.2174 | 65.0849–65.3495 | E |
| TR-SWIM-020 | 12 | 30 | 42 | 71.4286 | 71.3093–71.5474 | E |
| TR-SWIM-021 | 10 | 0 | 10 | 0 | 0–0 | C |
| TR-SWIM-022 | 16 | 0 | 16 | 0 | 0–0 | C |

Eleven C and eleven E, with no single-workout boundary crossing in this scenario.
SWIM-010's 150 seconds stationary rest remain separate from 30.3 active minutes.
The six authorized C2.1 corrections remain Z2: SWIM-015–020 retain 600m Z2 and
zero Z3. Their remaining Z5 segments still contribute HIGH. Nothing reverts those
corrections or changes source/history.

## Borderline sensitivity and limitations

No empirical pace-uncertainty interval was supplied or approved. The caller must
explicitly supply a sensitivity scenario; there is no default physiological
uncertainty limit. This report uses **±0.005 min/100m** (half the last decimal
step) as an illustrative quantization-scale perturbation. The confirmed inputs
remain exactly the supplied decimal-minute constants; this scenario neither
changes them nor asserts the unknown underlying pace lies inside that interval.

For each ordered distance, compute a sensitivity contribution
`meters/100 * half_width`. Let their LOW/HIGH sums be dL/dH. The exact envelope is:

- Minimum HIGH ratio: `(H-dH)/(H-dH+L+dL)`.
- Maximum HIGH ratio: `(H+dH)/(H+dH+L-dL)`.
- Boundary sensitive: minimum <= 0.20 and maximum > 0.20.

This permits independent adverse changes across zones. A common proportional
pace error would cancel in the ratio, but zone-specific errors need not. The
scenario assumes identical zone references across occurrences; it is not a
model of within-zone athlete variability, fatigue, technique or measurement error.

Independent synthetic fixtures demonstrate why nominal acceptance is insufficient:

| Prescribed synthetic segments | Exact LOW/HIGH min | Nominal HIGH % | Sensitivity |
| --- | --- | --- | --- |
| 300m Z2 + 100m Z5 | 6 / 1.5 | 20 exactly | Crosses 20% under the scenario |
| 366m Z2 + 100m Z3 | 7.32 / 1.83 | 20 exactly | Crosses 20% under the scenario |
| 334m Z2 + 100m Z4 | 6.68 / 1.67 | 20 exactly | Crosses 20% under the scenario |
| 299m Z2 + 100m Z5 | 5.98 / 1.5 | 20.0535 | Can cross below 20% |
| 301m Z2 + 100m Z5 | 6.02 / 1.5 | 19.9468 | Can cross above 20% |
| 300m Z2 + 999999s wall rest + 100m Z5 | 6 / 1.5 | 20 exactly | Rest has zero effect |

These fixtures are not athlete prescriptions. All-Z2 remains numerically 0%
HIGH on this estimated basis but has no authoritative active-time denominator.
No claim of robustness outside the supplied sensitivity scenario is possible.
Future week combinations may be borderline even when each source-only diagnostic
is far from 20%. An approved operational consumer must separately decide how to
treat uncertainty; this work chooses no margin, waiver or safety gate.

## Evidence and verification

[Independent fixtures](../../../backend/tests/fixtures/v6_partial_approval.json)
were computed by direct OOXML H:L/M/N extraction and independent rational arithmetic,
without the importer, new estimator or experimental source calculator. They pin
all 77 IF² candidate rationals and every one of the 22 swims' original prescription,
zone distances, ordered segment estimates, LOW/HIGH totals and expected status.
Tests compare the existing calculator with the new confirmed parameters to those
rationals; they do not approve that complete formula or its operational use.

Tests also cover all five individual paces, mixed zones, exact/above/below 20%,
wall rest, repeated occurrences, weekly aggregation, sport isolation, missing
authoritative durations, invalid inputs, hostile Decimal contexts and the absence
of runtime imports. Historical method guards and all earlier tests are retained.

Private reproducible results: [evidence.json](partial-approval/evidence.json).
The artifact preserves full original execution-cell evidence, ordered events and
explicit estimate/authority distinctions. It is never an athlete/API serializer.
From `backend`, using the existing project virtualenv and a fresh output path:

```text
python -B -m benchmarks.v6_partial_approval_evidence --private-output EXISTING_PRIVATE_DIRECTORY/NEW_FILE.json
python -B -m pytest -q -p no:cacheprovider tests/test_v6_partial_approval.py tests/test_v6_policy_sandbox.py tests/test_joren_c21.py
python -B -m pytest -q -p no:cacheprovider
python -m ruff check app tests benchmarks
python -m ruff format --check app tests benchmarks
python -m mypy app tests benchmarks
python -B -m benchmarks.v6_policy_sandbox --regression-output EXISTING_PRIVATE_DIRECTORY/NEW_REGRESSION.json
```

No application/API/database/mobile changes, performed-duration estimation,
Realized TSS calculation, historical reinterpretation, planner integration or
activation. Final verification results and remaining gates are in the
[approval register](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md#implementation-and-verification-custody).
