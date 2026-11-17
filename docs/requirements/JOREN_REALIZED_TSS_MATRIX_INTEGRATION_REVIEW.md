# Joren Realized TSS/RPE Matrix integration review

Date: 2026-11-03 (Europe/Amsterdam). Review complete; implementation is not approved or started.

This pre-implementation review accompanies the [formal model](JOREN_REALIZED_TSS_FORMAL_MODEL.md), [decision register](JOREN_REALIZED_TSS_DECISION_REGISTER.md), [test matrix](JOREN_REALIZED_TSS_TEST_MATRIX.md) and [implementation plan](JOREN_REALIZED_TSS_IMPLEMENTATION_PLAN.md). No physiological behavior, coefficients, application contracts or historical calculations were changed.

## Verified baseline and source custody

The cumulative remediation head is **e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6**, branch `fix/wombo-end-to-end-performance`, at `.worktrees/wombo-end-to-end-performance`. The worktree was clean. Consecutive `git merge-base --is-ancestor` checks verify:

| Phase | Preserved SHA |
| --- | --- |
| A10 | `11591b9924ebfd3872314deecb82c57fc278126b` |
| A3 | `b65ea78be1db886586d793f721bb2910ddbc6a41` |
| A4 | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` |
| A5 | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` |
| A6 | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` |
| A7 | `75f172d4161f71a763247b04c027fd165901afbd` |
| A8 | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| A9 | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` |

`git log --all --ancestry-path A9..` found no descendants. This is the cumulative remediation head, not a merge into main. Root remains on `fix/pre-ui-beta-blockers` at `6bb3a047139d91c71ac065c35a8af595221b54c5`. All C-references below describe the **A9 tree**, not older root copies. Reproduce with `git show e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6:<path>`.

The requested PDF is absent from root and A9, but available in the Joren simulator worktree:

[Specificatie Realized TSS Matrix.pdf](<../../.worktrees/joren-training-engine-simulator/docs/requirements/Specificatie Realized TSS Matrix.pdf>)

- Absolute path: `F:/Projecten Business/Start23/Code/.worktrees/joren-training-engine-simulator/docs/requirements/Specificatie Realized TSS Matrix.pdf`.
- 180,537 bytes; SHA-256 `b31f7fd72ebdda6f54f87fc5f25b69e53600f3476f5572d5e75af48615aef194`.
- One page; "Realized TSS & RPE Matrix Uitleg", document version 1.0.
- Local untracked owner-supplied source, not part of committed A9. The hash identifies the reviewed bytes.
- Full text extracted and entire rendered page visually checked: all 25 factors and RPE column mappings match the user's transcription.
- Installed MiKTeX tools could not initialize in the sandbox. Temporary PyMuPDF and rendering artifacts were placed under ignored `tmp/joren-matrix-review/`. Application dependencies and the original PDF were untouched.

## Source authority and conversation traceability

| ID | Evidence | Status and exact scope |
| --- | --- | --- |
| P01 | PDF p.1 section 1 | Verified 5x5 lookup table: planned zone rows, reported perceived-zone columns; expected TSS multiplied by selected factor. |
| P02 | PDF p.1 headings/neutrality example | Z1=RPE1-2, Z2=3-4, Z3=5-6, Z4=7-8, Z5=9-10. Planned Z2/RPE4 and reported RPE3 stays unchanged. |
| P03 | PDF p.1 section 2 | Fixed 12.5% steps, +25% ceiling, 60% floor, diagonal 1. No duration formula, rounding, mixed-session algorithm, source precedence or weekly completeness contract. |
| P04 | PDF p.1 practice example | Expected bike load120: RPE3 ->120; RPE2 ->105; RPE8 ->150. Matrix-only fixtures, not existing-engine parity. |
| O01 | Owner discussion issue1 in this task | **CONFIRMED BY JOREN**, as relayed by owner: actual performed duration must be included. Exact ratio and caps are **PROPOSED BUT NOT APPROVED**. |
| O02 | Owner discussion issue2 | **CONFIRMED BY JOREN**, as relayed: RPE estimates in absence of measurements; subjective difficulty is not objective external workload. |
| O03 | Owner discussion issue3 | **SCIENTIFIC VALIDATION LIMITATION** acknowledged: correction percentages are reasoned heuristics, not established physiological conversions. |
| O04 | Owner discussion issue4 | Called a **DOCUMENTATION DISCREPANCY**; investigation also confirms an **IMPLEMENTATION CONFLICT**. |
| O05 | Owner database decision | PostgreSQL/pgTAP deferred to integration/release. No Docker/Podman/psql installation; deferral is not a pass. |

The original discussion was not independently supplied as a signed transcript; O01-O04 record the owner's explicit account. The PDF makes physiological assertions but provides no validation study or calibration dataset for its factors. This review verifies source/arithmetic compatibility, not scientific validity or release authorization.

## Actual implemented behavior

| Area | A9 behavior | Sources |
| --- | --- | --- |
| Versions | Load `phase-13-joren-ruleset-1`; separate planning `joren-planning-ruleset-2`. | C01,C10,C19 |
| Observed load | Sum valid actual zone minutes times discipline coefficients. Five finite nonnegative Decimal bins; sum <= reliable total. No RPE multiplier. | C01 |
| Measurement availability | Positive bins covering total -> `complete`; less than total -> `partial_observed`; absent/all-zero bins -> `unavailable` and load None. Partial time is not extrapolated. | C01,C11 |
| Mean HR | Only if zone array is None, actual duration >0, confirmed run/bike HR zones and mean HR exist. Whole actual duration assigned to its mean-HR zone. Method `average_hr_zone_duration`; status `estimated_from_average_hr`; observed valid minutes/coverage zero. Swim does not use it. | C02,C12 |
| Precedence edge | Partial bins are authoritative. Even an explicitly supplied all-zero array prevents the service's mean-HR branch and stays unavailable. | C01,C02 |
| Ordinary RPE | Completes processing; affects expected-band comparison and low-workout/RPE>=7 hidden fatigue. Does not rescale current observed/mean-HR numeric load. | C02,C03 |
| Existing match matrix | Qualitative Phase7 behavior, not new numerical matrix. Noncomplete measurement -> deviation, except low/RPE>=7 hidden fatigue. Complete measurement: hidden-fatigue precedence; overshoot strictly >115%; perfect match inclusive90%-110% plus expected RPE band. Complete unplanned sessions have a separate proposal reason. | C03 |
| Other RPE calculations | Inactive reference sRPE is `hours*IF(RPE)^2*100*sport_multiplier`, with `SRPE_FALLBACK_ENABLED=False`. Old compatibility method is `RPE*actual_minutes/60`. Neither is this PDF matrix. | C01,C03,C11 |
| Duration | Activity summary already stores actual duration, positive <=1440 minutes; only distance-only swim may omit it. Zero is rejected through current completed-activity API. | C04 |
| UI duration semantics | Planned duration is prefilled in matched activity entry. An editable default is not independently measured performed time. | C16 |
| Completion | `awaiting_rpe`/`complete` indicate feedback processing, not proof every prescribed interval was performed. No per-segment completion state exists in this activity DTO. | C04,C16 |
| Other measurements | Normalized bike power, pace/speed and HR summaries can be accepted; current activity service selects no power-to-load/external-work conversion. | C02,C04 |

Existing coefficients, unchanged:

| Zone | Swim/minute | Bike/minute | Run/minute |
| --- | ---: | ---: | ---: |
| Z1 | 0.45 | 0.50 | 0.58 |
| Z2 | 0.72 | 0.80 | 0.92 |
| Z3 | 1.08 | 1.20 | 1.38 |
| Z4 | 1.44 | 1.60 | 1.84 |
| Z5 | 1.80 | 2.00 | 2.30 |

Planned load is not always reconstructed from one zone. `with_current_load` derives non-source timed templates from authoritative segment-zone minutes, retains reviewed predefined private load for timed source-catalog workouts, and makes distance-only source swims unavailable. Missing planned load is not inferred from distance/CSS or RPE (C05,C10). The matrix needs the accepted occurrence's immutable planned-load snapshot/method.

RPE also supplies exact discipline text and reviewed calibration HR/LTHR or swim pace/CSS anchors. A new perceived-zone mapping does not authorize changing these anchors or activating zones (C01,C06,C07).

### Adjacent active and historical rules kept separate

The starting baseline is not a realized-session estimate. Current Phase13 computes each previous-month weekly sport's minutes/60 *56.25*multiplier (swim0.90,bike1.00,run1.15), sums exact components, and rounds the total once to one decimal half-up. All-zero history uses the approved private45.0 product choice; partly zero disciplines do not receive invented minima. Total weekly history is bounded by168hours. The new matrix must not alter this seeding logic (C01,C10).

Calibration is a separate pending-zone lifecycle. Run/bike estimate LTHR as observedHR divided by the RPE anchor; swim estimates CSS seconds/100m as measured pace divided by its anchor. Both round the threshold half-up to an integer before contiguous integer zone construction. Current HR anchor sequence for scores1-10 is0.70,0.78,0.84,0.88,0.91,0.94,0.97,1.00,1.03,1.06. Swim anchors are1.25,1.18,1.12,1.08,1.06,1.04,1.01,1.00,0.96,0.92. These anchors are neither matrix factors nor the inactive sRPE IF sequence0.45,0.55,0.65,0.75,0.82,0.88,0.94,1.00,1.05,1.15. Ordinary activity feedback cannot automatically calibrate or activate zones.

HR zone boundaries use rounded82%,89%,95% and the LTHR endpoint, with adjacent integer ownership; swim uses rounded98%,102%,107%,115% CSS and inverse pace ownership. Current suspicious run/bike threshold<140bpm attaches a warning to a pending proposal rather than blocking calculation. Historical zone profiles keep their own zone-model version and boundary interpretation. No threshold or anchor is changed here.

Planning-v2 separately governs source-workout selection, repetitions/occurrence IDs, phase eligibility, injury redistribution and spacing (72hours run,48hours bike/swim). Existing ordinary progression is10%; default recovery uses60% of the prior relevant planned basis (approved factor range40%-60%). Active taper is the seven local dates D-7 through D-1; the supported exact preceding full-week A-race target uses35% of non-recovery planned baseline, while unsupported partial-week targets fail closed. These are existing reviewed constants and constraints, not approvals for a new estimate (C10,C15).

Legacy Phase3/7 RPE-times-hours values, inactive sRPE IF-squared reference values, active zone-minute values, source-catalog private planned values and the proposed matrix estimate must retain distinct provenance. Similar field names do not establish numerical comparability.

## RPE compatibility: implementation conflict

`zone_for_rpe_value(3)` currently returns Z1. Current ranges are Z1=2-3, Z2=4, Z3=5-6, Z4=7-8, Z5=9-10; the scalar resolver additionally maps RPE1 to Z1. PDF scalar mapping differs at RPE3; range/display contracts also change at Z1/Z2.

- Public workout/planned-workout guidance uses the old helper and emits `Zone 1 · RPE 2-3` for expected RPE3.
- Tests assert all old discipline ranges; `test_noncanonical_rpe_range_is_rejected` requires (3,4) to fail.
- Calibration domain validates targets through this exact range resolver.
- Mobile stores scores1-10 and discipline descriptions without calculating load/zones, but consumes API guidance; calibration mobile tests contain the old label.
- Current Pydantic integer field is bounded, not strict: characterization accepted true->1, "3"->3, 3.0->3; rejected3.5,0,11. A proposed strict calculator must not silently accept booleans. API compatibility is D08.

D07 must decide estimate-only mapping versus versioned migration of shared guidance/catalog/calibration consumers. Updating the shared helper globally would reinterpret existing targets.

## Mathematical finding

The described capped linear candidate is `L(p,q)=max(0.600,min(1.250,1.000+0.125*(q-p)))`. It agrees with 23/25 PDF cells. For Z4->Z1 and Z5->Z2, difference=-3 gives0.625; table gives0.600. At P=120 this is75 versus72; at half duration37.5 versus36. The floor explains Z5->Z1(-4), not the two -3 exceptions. Compounding0.875 per downward step would be another model.

D01 must choose authoritative lookup, corrected linear formula, or an explicitly supplied alternative. The [25-cell fixtures](JOREN_REALIZED_TSS_TEST_MATRIX.md#all-25-cell-fixtures) retain both results.

Actual duration inclusion is confirmed, but `P*(A/T)*M[p,q]` is only a candidate. Uniform load/minute is unsupported for warm-up-only, skipped hard intervals, changed structure and bricks. The matrix ceiling is not a final-session ceiling: A/T=1.5 and M=1.25 yields1.875P. No silent clipping is approved.

## Measurement hierarchy proposed for approval

1. Preserve external-work, HR/pace, zone-time and subjective observations separately, with origin and units. Provider-reported TSS is not automatically commensurable.
2. Preserve current complete/partial zone-minute results; never multiply these by the matrix factor.
3. Keep the approved mean-HR estimate only under current conditions, with distinct estimated provenance.
4. Consider a separately versioned RPE estimate only where no selected current result is available, and approved planned context, reliable performed duration and structure eligibility exist.
5. Otherwise keep unavailable plus subjective feedback.

This is D05/D10/D15, not active policy. Partial observed load remains distinct; never add a full-session RPE estimate to its subtotal or fill unobserved minutes. Selecting a separate estimate instead of partial evidence would need a further explicit decision. Measured coverage, duration availability and feedback completeness are different axes.

Actual external workload is an evidence category, not an already implemented TSS method. Power summaries alone do not authorize inventing an external-work conversion. The existing Polar adapter imports canonical swim/bike/run duration and HR summaries and stores raw FIT when available; its inspected path does not parse FIT into zone-time/power-derived load (C14). No Garmin/Strava provider adapter exists in A9's integrations module. A root Garmin design document is not implementation.

## Weekly aggregation, U-001 and next-week impact

Flow: activity create -> actual duration/metrics -> RPE completion -> private load -> qualitative result/optional pending correction -> v15 history -> v14 -> v13 -> `PlanningService._load_samples` -> `PlanLoadSample` -> `resolve_target` -> pending next-week proposal.

The v13 RPC generates up to six Monday-starting weeks after earliest evidence, groups activities by their own local date/timezone, and joins the plan's active approved revision pointer. It counts all activity rows. With none, realized=0; with activities, SUM includes only non-null Phase13 loads. Pending RPE, unavailable values, legacy methods and partial measurement quality are not accompanied by an aggregate quality marker. All-null load rows yield NULL. Activity-only weeks have planned0. v14 adds per-sport planned values; v15 adds prior-approved-plan provenance, without fixing completeness (C08,C09,C18).

Example: 60-minute bike Z2 complete=48; another60-minute bike with observed10Z1+20Z2+11Z3=34.20, coverage41/60; a third60-minute session awaits RPE. SQL can return **82.20** and count3. That is a known subtotal, not a verified180-minute total. Duration/intensity denominators can omit the no-load row, overstating aggregate coverage. This is the source-level U-001 concern, not an executed PostgreSQL reproduction (C17).

Current target resolution excludes sickness and preserves injury/identity, taper and recovery precedence. Flagged fatigue/missed-training (or zero-activity) undershoot can use realized*1.10; >110% debt is separate. Otherwise >=80% completion permits prior planned*1.10; lower completion uses non-recovery42-day realized history. NULL realized holds prior planned. Prior-approved-plan provenance prevents reseeding returning athletes. Intensity debt needs existing classified-minute coverage>=60%; Session-RPE cannot fabricate those minutes (C09,C15).

Proposed U-001 contract: expose known subtotal, method/version and pending/missing/partial counts, total/observed/classified durations, and evidence/eligibility state privately, alongside separately nullable planner-usable load. A full-duration mean-HR/RPE estimate is not100% measured coverage. D10/D11 must decide whether each quality class permits growth, debt, baseline use, hold or fail-closed behavior. No imputation, zero-fill or new quality threshold is invented.

## Integration points and concrete contract hazards

| Boundary | Required future work; not implemented |
| --- | --- |
| Pure Python | New versioned calculator/outcome type; no FastAPI/database/provider/LLM dependencies; preserve coefficients. |
| Private processing context | Current planned context has load, RPE range and low/high bucket; lacks planned duration, segments, one planned zone and planned-load version. Add immutable occurrence/revision facts privately. Low/high is not one of five zones. |
| Version dispatch | Any corrected stored version unequal to current VERSION is treated as legacy by `submit_rpe`. A new version alone would route later correction through retired RPE-times-hours behavior. Require explicit supported-method dispatch. |
| Correction history | Current Phase13 corrections preserve originating HR profile/load and append prior private snapshots. New RPE corrections may affect their own estimate only under approved snapshot/window/concurrency policy. |
| Match semantics | Noncomplete `ZoneLoad` bypasses numeric matching. Do not falsely label an RPE estimate complete measured data to reuse matching. D12 decides qualitative semantics. |
| SQL constraints | Method/version checks permit only legacy or two Phase13 methods. Non-Phase13 completion logic assumes retired formula. New method needs forward-only constraint/RPC changes. |
| Weekly history | v13 filters Phase13 exactly. New-version rows would be excluded until a versioned aggregate interface deliberately admits them. |
| Public contracts | Retain actual-duration and score input compatibility. Private estimate, factor, planned/realized load and method internals must stay out of mobile DTOs/UI/logs/analytics/accessibility/LLM prompts. No V1/V2 redesign. |

## Evidence index

All C01-C16/C18-C19 paths are pinned to A9. Links intentionally point into that worktree.

| ID | Source / symbols |
| --- | --- |
| C01 | [physiology/joren.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/joren.py): VERSION, coefficients, `zone_load`, `average_hr_zone_load`, `srpe_formula`, calibration anchors/rounding. |
| C02 | [activities/service.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/activities/service.py): `_expectation`:113, `submit_rpe`:135, version dispatch:197, observed precedence:225, preservation:286, private payload:311. |
| C03 | [physiology/activity.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/activity.py): `classify_activity_match`, legacy compatibility function. |
| C04 | [activities/schemas.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/activities/schemas.py): summary:77, response:153, RPE:184; [router.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/activities/router.py) verified identity dependencies. |
| C05 | [workouts/catalog.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/workouts/catalog.py): `with_current_load`:1021, `require_planned_load`, template segment/duration invariants. |
| C06 | [physiology/rpe_zones.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/rpe_zones.py): ranges, range resolver:101, scalar resolver:109; [mobile rpe.ts](../../.worktrees/wombo-end-to-end-performance/mobile/src/lib/rpe.ts). |
| C07 | [workouts/schemas.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/workouts/schemas.py): `rpe_zone_responses`:58; planning derived guidance and calibration domain/service range consumers. |
| C08 | [Phase13 migration](../../.worktrees/wombo-end-to-end-performance/supabase/migrations/20260910215947_phase_13_joren_ruleset.sql): history function:1623, aggregation:1718, method checks:1009, provenance checks:2158. |
| C09 | [planning/service.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/planning/service.py): `_load_samples`:487; [domain.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/planning/domain.py): `PlanLoadSample`:102, `resolve_target`:211; repository v15 call:447. |
| C10 | [Phase13 approved ruleset](../../.worktrees/wombo-end-to-end-performance/docs/requirements/phase-13-joren-ruleset-1.md), average-HR amendment and sections6-10; [planning-v2 decisions](../../.worktrees/wombo-end-to-end-performance/docs/implementation/joren-planning-ruleset-v2.md); current MVP roadmap final decision review. |
| C11 | [test_joren.py](../../.worktrees/wombo-end-to-end-performance/backend/tests/physiology/test_joren.py): coefficients, partial, missing, inactive sRPE; [test_rpe_zones.py](../../.worktrees/wombo-end-to-end-performance/backend/tests/physiology/test_rpe_zones.py): old ranges and new-range rejection. |
| C12 | [test_activities.py](../../.worktrees/wombo-end-to-end-performance/backend/tests/test_activities.py): mean-HR:650+, partial:680+, distance-only:712+, preservation:731+, immutable HR/stale checks. |
| C13 | Phase13 migration:1110 `private.phase_13_activity_load_history` and before-update snapshots; [R4/R5 migration](../../.worktrees/wombo-end-to-end-performance/supabase/migrations/20260912180000_phase_r4_r5_onboarding_race_activity.sql): immutable HR trigger:592 and stale-safe RPE wrapper:626. |
| C14 | [integrations/domain.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/integrations/domain.py): `polar_exercise_to_activity`; [service.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/integrations/service.py): `_import_one`. |
| C15 | [progression.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/progression.py), [debt.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/debt.py), `models.ConstraintStage`, recovery/taper modules. |
| C16 | [activity controller](../../.worktrees/wombo-end-to-end-performance/mobile/src/features/activities/useActivityController.ts): planned-duration prefill:254, owner/cache/retry reconciliation; mobile API activity types around:797. |
| C17 | [Original U-001 audit](../../.worktrees/audit-wombo-full-system-review/docs/audits/WOMBO_FULL_SYSTEM_AUDIT.md):534; [Joren J-02](../../.worktrees/audit-wombo-full-system-review/docs/audits/WOMBO_JOREN_REVIEW_QUESTIONS.md). Separate audit worktree at `aff74558d0a6511286a4a84a44ea25a03ca57549`; local audit artifacts. |
| C18 | [v14](../../.worktrees/wombo-end-to-end-performance/supabase/migrations/20260929210000_joren_planning_ruleset_v2.sql):300; [v15](../../.worktrees/wombo-end-to-end-performance/supabase/migrations/20261004212750_first_plan_approved_provenance.sql):3; [current processing context](../../.worktrees/wombo-end-to-end-performance/supabase/migrations/20260914174000_r6_disambiguate_activity_processing_load_source.sql):4. |
| C19 | [physiology/specification.py](../../.worktrees/wombo-end-to-end-performance/backend/app/modules/physiology/specification.py): separate Phase13/planning-v2 evidence, `production_review=None`; Phase0 decision lock and root/mobile AGENTS.md. |

## Verification and limits

Executed at A9 with the existing backend venv:

`python -B -m pytest -q -p no:cacheprovider tests/physiology/test_joren.py tests/physiology/test_activity.py tests/physiology/test_rpe_zones.py tests/physiology/test_progression.py tests/test_activities.py tests/test_contracts.py`

**169 passed**,15.49s, one existing Starlette/httpx deprecation warning. These existing backend/contract tests do not validate the new model physiologically or execute SQL. Independent Decimal probes checked all25 table/linear cells, ten current scalar mappings and public guidance/API input behavior.

Full backend/mobile/Ruff/mypy/TypeScript suites were not rerun for documentation-only changes; earlier owner-reported A9 totals remain historical reports. PostgreSQL/pgTAP/RLS execution is **DEFERRED BY OWNER**, not passed. No database tools installed, database queried or migration applied.

No application/test source changed. Existing root changes and worktrees were preserved. No push, merge, deployment, branch switch, new commit or history rewrite occurred. Review completion means decisions are concrete and reviewable, not that unresolved options became approved behavior.

Final document checks directly parsed all 25 factors from the PDF's extracted table and matched them to all 25 documented fixture rows; full/half-duration arithmetic and the two linear exceptions passed independent assertions. All local document/source links resolve. There are 18 decision records, each with all nine requested fields, and 129 distinct planned fixture IDs. These structural/arithmetic checks do not constitute execution of the future implementation fixtures.

Before/after content manifests across backend app/tests, mobile source, migrations and database tests were unchanged: root 269 files, SHA-256 `9aa21028b05c3f6149d737f2210a0202f2c06d386ed3741c66913e19286843ca`; A9 449 files, SHA-256 `0f1391b2f0c7b36a4320531b13a8722fe67905bc0945a631b3bd929ae4f10f3d`. Existing root tracked-diff hash, all refs and the worktree/HEAD inventory matched their initial snapshots; A9 remains clean. The PDF hash remains unchanged.
