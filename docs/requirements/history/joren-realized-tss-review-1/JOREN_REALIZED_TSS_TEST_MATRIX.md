# Joren realized-load test matrix

Date: 2026-11-03. Baseline: `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`.

These are exact specification/characterization fixtures, not newly activated application tests. **No new production formula is implemented.** Source evidence is in the [review](JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md); acceptance choices are in the [register](JOREN_REALIZED_TSS_DECISION_REGISTER.md). Numeric examples are private synthetic audit data, never athlete DTO fields.

Test families: M=matrix, R=RPE, U=duration, S=structure, H=hierarchy, P=plan basis, W=weekly/planning, Q=qualitative/privacy, N=numeric, V=version/history. A fixture's Pxx ID here is a plan-basis test, distinct from PDF evidence Pxx in the review.

## Execution status

- PDF page rendered and visually checked; all25 transcription values confirmed.
- Decimal probe evaluated all25 table/linear comparisons; exactly M16/M22 differ. Both RPE values in each perceived-zone pair must select the same column.
- Current scalar mapping and API guidance directly characterized; current API accepts boolean true, integer string and integral float as described below.
- Existing A9 backend/contract tests: **169 passed**,15.49s, one existing Starlette/httpx warning. Command at end.
- Future scenarios below are specified, **not claimed executed** against a new engine or live SQL.
- PostgreSQL/pgTAP/RLS execution **DEFERRED BY OWNER** to integration/release. No database tools installed. Static SQL inspection is not database parity.

## All 25 cell fixtures

Fixture basis P=120,T=120. Full-duration column uses A=120. Half-duration column uses A=60 and the **unapproved** ratio candidate. L is the capped additive formula in the formal model. Values are exact decimal results before any final rounding.

| ID | Planned p | Reported q / both RPE inputs | PDF factor M | Linear factor L | P*M, full duration | P*0.5*M, candidate | Comparison |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| M01 | Z1 | Z1 / 1,2 | 1.000 | 1.000 | 120.000 | 60.000 | same |
| M02 | Z1 | Z2 / 3,4 | 1.125 | 1.125 | 135.000 | 67.500 | same |
| M03 | Z1 | Z3 / 5,6 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M04 | Z1 | Z4 / 7,8 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M05 | Z1 | Z5 / 9,10 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M06 | Z2 | Z1 / 1,2 | 0.875 | 0.875 | 105.000 | 52.500 | same |
| M07 | Z2 | Z2 / 3,4 | 1.000 | 1.000 | 120.000 | 60.000 | same |
| M08 | Z2 | Z3 / 5,6 | 1.125 | 1.125 | 135.000 | 67.500 | same |
| M09 | Z2 | Z4 / 7,8 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M10 | Z2 | Z5 / 9,10 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M11 | Z3 | Z1 / 1,2 | 0.750 | 0.750 | 90.000 | 45.000 | same |
| M12 | Z3 | Z2 / 3,4 | 0.875 | 0.875 | 105.000 | 52.500 | same |
| M13 | Z3 | Z3 / 5,6 | 1.000 | 1.000 | 120.000 | 60.000 | same |
| M14 | Z3 | Z4 / 7,8 | 1.125 | 1.125 | 135.000 | 67.500 | same |
| M15 | Z3 | Z5 / 9,10 | 1.250 | 1.250 | 150.000 | 75.000 | same |
| M16 | Z4 | Z1 / 1,2 | 0.600 | 0.625 | 72.000 | 36.000 | D01: 0.025 conflict |
| M17 | Z4 | Z2 / 3,4 | 0.750 | 0.750 | 90.000 | 45.000 | same |
| M18 | Z4 | Z3 / 5,6 | 0.875 | 0.875 | 105.000 | 52.500 | same |
| M19 | Z4 | Z4 / 7,8 | 1.000 | 1.000 | 120.000 | 60.000 | same |
| M20 | Z4 | Z5 / 9,10 | 1.125 | 1.125 | 135.000 | 67.500 | same |
| M21 | Z5 | Z1 / 1,2 | 0.600 | 0.600 | 72.000 | 36.000 | same |
| M22 | Z5 | Z2 / 3,4 | 0.600 | 0.625 | 72.000 | 36.000 | D01: 0.025 conflict |
| M23 | Z5 | Z3 / 5,6 | 0.750 | 0.750 | 90.000 | 45.000 | same |
| M24 | Z5 | Z4 / 7,8 | 0.875 | 0.875 | 105.000 | 52.500 | same |
| M25 | Z5 | Z5 / 9,10 | 1.000 | 1.000 | 120.000 | 60.000 | same |

For M16/M22, linear full-duration result=75.000 and half-duration=37.500; table results=72.000/36.000. Neither expected set is selected as active until D01. Matrix tests must independently assert all25 cells, not regenerate expected values with the implementation's own formula.

Properties: every diagonal=1; bounds[0.600,1.250]; each row nondecreasing with perceived zone; each column nonincreasing with planned zone; upper plateaus at zone difference>=2; floor at -4; table-specific -3 exceptions. Do not assert an invertible matrix or reciprocal opposite factors: those are not promised. 1.125*0.875=0.984375, not1.

## RPE and validation

| ID | Input | Current characterization | New-model expectation |
| --- | --- | --- | --- |
| R01 | r1 | Z1 | Z1 |
| R02 | r2 | Z1 | Z1 |
| R03 | r3 | Z1 | PDF Z2; D07 conflict |
| R04 | r4 | Z2 | Z2 |
| R05 | r5 | Z3 | Z3 |
| R06 | r6 | Z3 | Z3 |
| R07 | r7 | Z4 | Z4 |
| R08 | r8 | Z4 | Z4 |
| R09 | r9 | Z5 | Z5 |
| R10 | r10 | Z5 | Z5 |
| R11 | r0 or11 | DTO rejects | Reject; never clamp |
| R12 | r3.5 | DTO rejects | Reject; never round to a zone |
| R13 | true | Current DTO coerces to1 | Proposed pure function rejects bool; DTO decision D08 |
| R14 | "3" | Current DTO coerces to3 | Pure function requires canonical integer; DTO decision D08 |
| R15 | 3.0 | Current DTO coerces to3 | Pure function type policy explicit; do not imply API is strict |
| R16 | missing/null/NaN/infinity | No valid completed rating | Reject/no estimate; no default score |
| R17 | planned target range(3,4) | Current range resolver rejects | Versioned mapping/guidance decision D07 |
| R18 | score3 segment / all disciplines | API emits old Z1, range2-3 | New estimate may mapZ2; do not rewrite old guidance implicitly |

Also test r1 target display lower bound (current public guidance minimum2), all three discipline text arrays, calibration-block score separation, and immutable old catalog/protocol rendering.

## Duration and missing-data fixtures

Unless noted, P120,T120,p2 and matching reportedZ2. Candidate numeric expectations are conditional on D02.

| ID | Inputs | Arithmetic / required distinction |
| --- | --- | --- |
| U01 | A120 | Matrix1 gives120 |
| U02 | A60 |60; matrix-only120 fails O01 duration requirement |
| U03 | A180,M1 |180 if ratio uncapped;120 if ratio capped1; D02 unresolved |
| U04 | A180,M1.25 |225 uncapped;150 ratio-capped; final cap is separate decision |
| U05 | A240,M1.25 |300 uncapped; factor ceiling does not cap final result at150 |
| U06 | A missing | Unavailable candidate; no substitution of planned duration |
| U07 | A0,T120 | Algebraic0; current completed-activity API rejects0; skipped state D06 |
| U08 | T0,A60 | Undefined; unavailable/reject; no division attempt |
| U09 | T missing,A60 | Unavailable; no inferred CSS/distance duration |
| U10 | A/T negative,NaN,infinity | Invalid; not clamped |
| U11 | A1440, then1440.01 | Preserve existing activity cap:1440 allowed, >1440 rejected |
| U12 | P missing | Unavailable; no retired/sRPE fallback |
| U13 | P0,T120,A60 | Algebraic0; D09 decides whether zero-plan context is eligible |
| U14 | Distance-only swim with no A | Preserve distance and processing; load unavailable |
| U15 | Planned duration prefilled but not confirmed | Must not claim it was measured/performed; D06 confirmation contract |

Zero versus NULL remain distinct across calculation storage, weekly subtotal, eligibility and public qualitative output.

## Structure / multi-sport fixtures

| ID | Scenario | Exact evidence / expected gate |
| --- | --- | --- |
| S01 | Bike15Z1+30Z5+15Z1 plan | P75,T60; no uniquely approved p |
| S02 | Only first15Z1 completed | Observed7.50; if illustrative p5,q1, candidate11.25; do not claim parity |
| S03 | Hard30min skipped,30easy completed | Observed15.00; illustrative candidate22.50 |
| S04 | Only30Z5 performed | Observed60.00; uniform time-share37.50 before matrix; no inferred full structure |
| S05 | One90min bike/run brick, one score | No arbitrary leg split or one sport coefficient |
| S06 | Independently matched bike/run legs | Preserve separate P,T,A,p,r and occurrence IDs; sum only approved comparable methods |
| S07 | Swim distance plus uncertain transitions | No assumed swim time or load; transitions policy unresolved |
| S08 | Other sport / changed discipline | Existing unsupported domain remains unsupported; no invented conversion |

## Measurement hierarchy and late evidence

| ID | Inputs / event | Preservation requirement |
| --- | --- | --- |
| H01 | Complete observed bins + RPE + meanHR | Exact existing zone sum selected; no matrix multiplication |
| H02 | Run partial[10,20,8,3,0],A60 |40.76, valid41, coverage41/60; no missing19min imputation |
| H03 | No bins, active run profile, meanHR inZ2,A60 |55.20; estimated_from_average_hr; valid/coverage0; existing source retained |
| H04 | Pending/no HR profile, no bins | Current unavailable; new fallback only after approved eligibility |
| H05 | All-zero bins + active HR profile | Current unavailable; do not silently reinterpret as absent array |
| H06 | Swim meanHR only | No HR-derived swim load; duration/RPE do not activate inactive sRPE |
| H07 | Late observed result after estimate | Append distinct result/selection only under D15; never add overlapping loads |
| H08 | Repeated provider import / HTTP retry | One canonical activity/selected result per approved identity key |
| H09 | Normalized power present without approved converter | Metric stored; no invented load method |
| H10 | Raw FIT stored / future provider label | File availability/brand does not imply parsed zone-time or authoritative TSS |

## Plan basis and identity

| ID | Scenario | Expected preservation |
| --- | --- | --- |
| P01 | Timed source-catalog workout | Retain exact reviewed P/method; no automatic recomputation from p |
| P02 | Distance-only source swim | Existing unavailable planned load stays unavailable |
| P03 | Repeated immutable template | Distinct planned occurrence IDs; select exact matched revision |
| P04 | Legacy planned-load version | No unit relabelling; explicit compatible/ineligible policy |
| P05 | Plan changed after activity basis captured | Original approved P,T,p snapshot retained; no current-template substitution |
| P06 | Unmatched/planned external activity | No matrix baseline invented; preserve other current calculations |
| P07 | Wrong athlete/stale match | Reject through owner/version checks; no client user_id authority |

## Weekly U-001 and planning fixtures

The current SQL expectations below are source-derived, **not executed PostgreSQL results**. New aggregate eligibility and consumer outcomes are D10/D11 approval fixtures, not an imputation policy.

| ID | Week / consumer case | Current source implication / required future assertion |
| --- | --- | --- |
| W01 | Two complete bike60Z2 sessions | Known sum96; count2; completeness still needs explicit contract |
| W02 | Complete48 +partial34.20 +pending no row | Known subtotal82.20,count3; never call complete180-minute load |
| W03 | All activities pending / no numeric rows | SUM NULL with activity_count>0; not0 |
| W04 | All processed but unavailable | SUM NULL; processing_complete does not prove measurement_complete |
| W05 | Mixed observed +meanHR estimate | Keep numeric subtotal and separate method/coverage classes; no measured100% claim |
| W06 | Mixed observed +new RPE estimate | Current v13 would omit new-version load; new aggregate must explicitly admit or exclude |
| W07 | Partial observed only | Keep exact subtotal/coverage; no whole-week extrapolation |
| W08 | Legacy and current records | Legacy load excluded by v13 version join; preserve incompatible count, not silent zero |
| W09 | No saved activity rows in eligible week | Current realized0,count0; separate absent evidence from confirmed missed-session semantics |
| W10 | Missing activity duration / distance swim | Count uncertainty separately; do not claim denominator completeness |
| W11 | P100,R80 at normal eligible build | Current >=80% path ->110 if no higher rule; new quality may gate eligibility |
| W12 | P100,R79.999, baseline70 | Current lower-completion path ->70; no rounding to80 before policy approved |
| W13 | P100,R110 | Debt not activated; normal target110 |
| W14 | P100,R110.001 | Debt active; corrected109.999 before other constraints |
| W15 | Fatigue/missed flag,P100,R60 | Current reduced realized target66; new-source eligibility unresolved |
| W16 | R NULL with prior approved plan | Hold previous planned basis; do not reseed or infer missed training |
| W17 | Sick week | Retained in history but excluded from baseline/progression; no zone mutation |
| W18 |42-day history with missing/estimated samples | Preserve sample versions, known denominator and eligibility; no zero-fill weeks |
| W19 | Classified intensity59.999% /60% | Existing debt quality boundary must remain; RPE zone cannot manufacture classified minutes |
| W20 | Recovery/taper/injury/returning-athlete contexts | Preserve higher precedence, prior-approved-plan references and pending approval; estimates cannot bypass them |

Include weeks straddling athlete timezone/Monday/DST, feedback corrected during current week, approved plan superseded, and a previous approved plan outside the six-week window. Historical v15 approval provenance must remain independent of measurement availability.

## Qualitative, numeric and version fixtures

| ID | Fixture | Required assertion / open choice |
| --- | --- | --- |
| Q01 | Low planned bucket,r7/r8, measurements absent | Existing hidden-fatigue signal independent of numeric estimate |
| Q02 | Complete measurement at90%,110%,115%,>115% | Existing inclusivity/strictness preserved |
| Q03 | New estimated result at125% | D12 decides comparison eligibility; never relabel measured_complete |
| Q04 | Correction proposal exists then RPE changes | Preserve pending/expiry/revision semantics; no automatic plan apply |
| Q05 | Retry after response loss | Same authoritative result, stale-safe reconciliation and no duplicate correction |
| Q06 | Public DTO/errors/logs/analytics/accessibility/LLM | No TSS/private load, factors or private plan context; no "objectively measured" heuristic claim |
| N01 | P1,A1,T3,M1.125 | Exact0.375; proposed one-decimal half-up0.4 |
| N02 | P0.1,A1,T3,M1.125 | Exact0.0375; proposed one-decimal0.0, still not missing |
| N03 | Repeating ratio1/3, then2/3 | Fixed approved Decimal context; no intermediate ratio quantization |
| N04 | Half-up ties, e.g.0.25 atone decimal | Proposed0.3; alternative rounding requires changed explicit fixture |
| N05 | Tiny positive value rounds0 | Do not treat as no data or confirmed no workload |
| N06 | Input scales / max supported duration | No undocumented precision loss/overflow; D13 numeric context |
| N07 | Negative/nonfinite/binary float source | Reject or canonicalize only through approved contracts |
| N08 | Around80%,110%,115% after rounding | Approved raw/stored comparison policy explicit; no threshold drift |
| V01 | Old RPE-times-hours correction | Retains old method/version; no matrix recomputation |
| V02 | Phase13 observed correction | Exact load/profile snapshot preserved |
| V03 | Phase13 meanHR correction | Original profile/meanHR immutable; newer zones cannot reinterpret |
| V04 | New-version correction | Explicit version dispatch; never treated as legacy by unequal VERSION |
| V05 | New estimate revised | Append prior calculation, original P/T/p and revised feedback provenance |
| V06 | Old/current/new records coexist | Readers select by method/version; constraints discriminate all supported cases |
| V07 | Stale expected_current_rpe / closed local-week window | Reject without partial mutation |
| V08 | Same score retry | Preserve existing idempotence; no duplicate selected estimate/audit event |
| V09 | Late better observation | Preserve old estimate plus new selection event; no silent historical rewrite |
| V10 | New estimate affected next-week proposal | Proposal input calculation IDs/versions frozen; athlete confirms changes |
| V11 | Activation disabled/rollback | No new calculations selected; existing new-version history remains readable |
| V12 | Activation without decision/review/gate record | Fail closed; fixture parity is not physiological validation |

## Verification commands and acceptance

Executed existing checks, from A9 backend with existing venv:

`python -B -m pytest -q -p no:cacheprovider tests/physiology/test_joren.py tests/physiology/test_activity.py tests/physiology/test_rpe_zones.py tests/physiology/test_progression.py tests/test_activities.py tests/test_contracts.py`

Implementation must later run relevant backend tests, Ruff/format, strict mypy, OpenAPI/public-contract and recursive leak tests; strict TypeScript/mobile tests for changed consumers. New forward-only migrations require PostgreSQL/pgTAP/owner-RLS verification at the owner-deferred integration/release stage. A mock repository does not prove RPC atomicity, numeric storage or grants.

Every active expected new behavior must cite the chosen decision ID and version. Retain old fixtures for old versions; replace only explicitly superseded prospective fixtures with documented reason. No weakening of existing tests, privacy checks or A3-A9 retry/account/concurrency coverage.

