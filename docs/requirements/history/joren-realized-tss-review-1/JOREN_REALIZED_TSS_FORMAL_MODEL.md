# Joren realized-load formal model

Date: 2026-11-03. Baseline: `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`. **Specification only: the duration-adjusted model is not approved.**

Evidence IDs P01-P04/O01-O05/C01-C19 resolve through the [integration review](JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md#evidence-index). Decisions D01-D18 resolve through the [register](JOREN_REALIZED_TSS_DECISION_REGISTER.md).

## Variables and ownership

| Symbol | Meaning / canonical representation | Source and availability |
| --- | --- | --- |
| d | One component discipline: swim, bike, run | Existing Discipline enum; no combined triathlon/brick scalar. |
| P | Expected/planned private load, finite nonnegative Decimal | Exact approved planned-workout occurrence/revision snapshot, including load method/version and catalog provenance. Never athlete-supplied TSS. May be unavailable. |
| T | Planned duration, Decimal minutes | Same immutable planned snapshot as P. Positive denominator required for ratio candidate. Distance-only plans can lack T. |
| A | Actual performed duration, Decimal minutes | Saved canonical activity summary, not inferred from distance, prescription, RPE or CSS. Its reliability/confirmation is D06. |
| p | Planned zone, integer1-5 | Explicit versioned planned-session interpretation. Current context's low/high bucket is insufficient. Mixed segments do not establish a unique p (D03). |
| r | Reported Session-RPE, integer1-10 | One subjective session score. Current API accepts numeric coercion; proposed pure function requires exact integer type excluding bool (D08). |
| q=g(r) | Perceived-zone index | PDF mapping:1-2->1,3-4->2,5-6->3,7-8->4,9-10->5. Equivalent `(r+1)//2` only after validation. Distinct from current shared resolver at r=3 (D07). |
| M[p,q] | Matrix factor | PDF decimal table below; authority against linear wording is D01. |
| D(A,T) | Duration adjustment | Required concept confirmed O01; exact function unresolved D02/D04/D06. Candidate A/T only. |
| E | Estimated realized private load | Candidate P*D*M. It is an RPE/plan-derived estimate, not external work or measured time-in-zone. |
| v | Calculation/policy version | Proposed `joren-realized-tss-matrix-1`, reserved descriptive name only; not an active ruleset. |

P is not automatically recomputed as T times a chosen coefficient. Timed source workouts retain reviewed source loads (C05,C10); other templates can use segment-zone sums. No second sport multiplier is appended to P: its source already incorporates its approved sport semantics.

## PDF matrix, verified from page 1

| p \ q | Z1 / RPE1-2 | Z2 / RPE3-4 | Z3 / RPE5-6 | Z4 / RPE7-8 | Z5 / RPE9-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Z1 | 1.000 | 1.125 | 1.250 | 1.250 | 1.250 |
| Z2 | 0.875 | 1.000 | 1.125 | 1.250 | 1.250 |
| Z3 | 0.750 | 0.875 | 1.000 | 1.125 | 1.250 |
| Z4 | 0.600 | 0.750 | 0.875 | 1.000 | 1.125 |
| Z5 | 0.600 | 0.600 | 0.750 | 0.875 | 1.000 |

P01-P04 define matrix-only `E_pdf=P*M[p,g(r)]`. This model omits performed duration. Matching zones preserve P even if half the planned time was performed. O01 requires addressing that omission; it does not approve a particular correction.

The comparison model is:

`L(p,q)=max(0.600,min(1.250,1+0.125*(q-p)))`.

M=L in23 cells. At (4,1) and (5,2), M=0.600 versus L=0.625. At difference=-4, uncapped0.500 floors to0.600. At +2,+3,+4, ceiling is1.250. Both models are bounded and monotone in reported zone with diagonal1, but the table's 0.750->0.600 step is15 percentage points. Neither monotonicity nor the floor resolves D01. Multiplicative step compounding is a different unapproved alternative.

## Duration-adjusted candidate, not approved

For P available, T>0, A>0, approved p and valid r:

`E_candidate=P*(A/T)*M[p,g(r)]`.

This assumes that the performed portion has the plan's average expected load per minute, then applies one session-level subjective factor. It is a modeling assumption, not evidence that intensity distribution or work was retained.

For the owner's P=120,T=120,A=60,p=q=2 example, the candidate yields60 versus matrix-only120. For p=2,r=2, it yields52.5; for p=2,r=8,75. These are conditional mathematical examples, not new physiological constants or recalculations of current records.

If D=A/T and P>0, 0.600*(A/T)<=E/P<=1.250*(A/T). The60% floor applies to the matrix multiplier, not necessarily E/P. Half duration can yield0.300P; double duration can yield2.500P. Applying a final floor0.600P would defeat the purpose of reducing short-session load; applying a final1.250P ceiling changes overrun semantics. Neither final cap is approved.

Even p=q does not imply E=P unless A=T. Zone neutrality applies to M only once duration correction is introduced. A=0 algebraically yields0 when T>0, but that arithmetic is not permission to record a skipped session as a completed workout.

## Structure and boundary analysis

| Case | Candidate implication / limitation | Required disposition before implementation |
| --- | --- | --- |
| Uniform, unchanged single-zone session | Average-rate assumption is explicit; actual HR/zone evidence can still differ. | Approve narrow eligibility and hierarchy, D02/D05. |
| Multiple planned zones/intervals | No unique p; duration ratio loses interval distribution. Low/high bucket is not a zone. | D03 chooses explicit field, segment method or unavailable; no inferred dominant/maximum/rounded zone. |
| Warm-up only | Can overstate performed load even after ratio and floor. | Preserve actual observations; D04 may make fallback ineligible. |
| Hardest segment skipped | Same remaining duration can carry much less load than planned average. | No claim uniform ratio proves actual load. Require approved execution context or unavailable fallback. |
| A>T | Ratio can exceed1; PDF ceiling constrains only M. | D02 chooses uncapped ratio, cap, or ineligibility; no new safety limit invented. |
| Missing A | Ratio undefined. | Unavailable candidate; preserve feedback/distance. No A=T substitution. |
| A=0 | Algebraic0, current completion API rejects zero. | D06 decides skipped/not-started semantics separately. Do not floor to60% or create a completed row. |
| Missing/zero T | Undefined denominator. | Unavailable; no divide-by-zero, epsilon, P-only fallback or inferred duration. |
| Missing P | No approved planned baseline. | Unavailable; no RPE-duration reference activation. |
| P=0 with T>0 | Algebraic0 for any factor; may be rest-only/non-workout context. | D09 confirms eligibility. Observed unplanned work remains observed work. |
| Changed session structure | Old P/p may no longer represent activity. | D04/D09: keep original plan provenance; do not rewrite it to explain actual work. |
| Distance-only swim | A and possibly T unavailable; CSS is not permission to infer performed time. | Preserve current unavailable-load behavior. |
| Multi-sport / brick | One P,p,r across components is ambiguous. | Calculate only independently matched component sessions if approved; no invented cross-sport allocation. |
| Unplanned / external activity | No qualifying planned occurrence/zone baseline. | Keep current observed/HR path; matrix unavailable unless explicit new model approved. |

Exact interval counterexample, analytical illustration using **existing bike coefficients**:

Plan15minZ1 +30minZ5 +15minZ1: T=60, P=30*0.50+30*2.00=75. Suppose p=5 is explicitly supplied for this illustration, not inferred by the review.

- Only first15minZ1 performed: observed load7.50. Uniform time share=18.75; matrix factor0.600 would give11.25.
- Hard30min skipped, all30 easy minutes performed: observed15.00; ratio37.50; factor0.600 gives22.50.

Both estimates exceed the known observed value by50% in these examples, even at the matrix floor. Conversely, performing only the hard30min gives observed60.00 while the uncorrected time share is37.50. Session duration does not identify the portion completed. Do not derive segment-specific RPE or completed-zone minutes from the one session score.

## Precision and validation proposal

D13 must approve the final numeric policy. Proposed arithmetic:

- Construct coefficients from decimal strings, not binary floats.
- Keep P, A and T snapshots in canonical Decimal representations; retain numerator/denominator for reproducibility.
- Calculate one `P*A*M/T` expression under explicitly fixed Decimal precision/context and a specified maximum supported input scale. A/T may repeat; "exact Decimal" is not proof every quotient is exact.
- Do not quantize the time ratio or intermediate estimates. If an approved stored final value is one decimal, propose ROUND_HALF_UP once at output; preserve inputs and the unrounded/context result privately.
- Keep threshold comparisons consistent with an approved raw-versus-rounded policy. Existing load calculations are not generally rounded to one decimal; the current one-decimal Start-TSS convention does not automatically govern this new method.
- Reject nonfinite/negative P,A,T, invalid types and out-of-domain p/r. Do not clamp invalid input into a valid zone.
- Preserve the existing API's positive-duration1440-minute limit and HR bounds20-260 as **existing contracts**, not new medically endorsed caps.
- Do not add a numeric maximum final load, overrun ratio, confidence threshold or minimum effective duration without approval.

Suggested outcome is a private discriminated result: available estimated value plus provenance, or unavailable with stable reason such as missing_duration, missing_plan_basis, unsupported_structure, unsupported_version or invalid_input. Reasons and their DTO projection need review; private inputs/numeric load must never appear in errors. Missing, explicit zero, partial observation and full estimate are distinct states.

## Selection, quality and weekly semantics

Current `zone_load` computes `sum(c[d,z]*observed_minutes[z])` and preserves partial coverage. Mean-HR estimate uses `A*c[d,assigned_zone]` with observed coverage0. The new matrix is a third independent method, not an RPE factor added to either one.

Proposed selection: current observed results first, including partial observations; approved current mean-HR next when eligible; only then an approved RPE fallback for otherwise unavailable qualifying planned activities. Keep subjective feedback independent throughout. Explicit all-zero bins and partial-versus-separate-full-estimate selection remain D05 questions, not silent exception paths.

Weekly draft contract:

- `known_subtotal` is the sum of selected available values with method/version labels; not automatically a complete total.
- Count all relevant sessions and distinguish pending RPE, unavailable, partial-observed, mean-HR estimated, RPE estimated, legacy/incompatible and complete-observed.
- Record activity-duration availability, observed-zone duration and intensity-classification duration separately; do not turn estimate duration into observed time.
- Record expected/matched planned occurrences and actually saved sessions separately. Absence of a saved row alone cannot prove a planned session was not performed.
- `planner_usable_load` remains nullable and requires an approved quality/compatibility rule, D10/D11. No imputation or aggregate eligibility percentage is defined here.
- Keep current no-activity-week zero interpretation visible as existing behavior; do not conflate it with all-unavailable data or new proof-of-nonperformance.
- Sickness, injury, taper, recovery and explicit athlete plan approval keep their existing precedence.

## Proposed immutable provenance

Proposed version `joren-realized-tss-matrix-1` is separate from existing load/planning versions. Snapshot:

| Group | Private provenance |
| --- | --- |
| Identity | Athlete owner, activity ID, calculation/revision ID, activity-input revision/fingerprint. |
| Plan | Planned-workout occurrence ID, approved revision ID/number, template version, original P/T, planned-load method/version, p and its selection rule/version, ordered structure fingerprint. |
| Feedback | Raw r, mapping version, derived q; actual A, duration source/confirmation, session completion/structure eligibility. |
| Formula | Selected table/formula version, all coefficient source hash, factor, duration-policy ID, A/T inputs, numeric context/rounding policy, raw and stored estimate. |
| Evidence | Origin manual/provider/device, metric kinds and units, available observed result IDs/coverage/profile versions; selection reason and uncertainty class. |
| Governance | PDF hash, approved decision IDs/record reference, calculator build SHA, creation time, selected/superseded relation. |
| Weekly use | Aggregate-policy version, input-calculation IDs and exact approved-plan references, quality/eligibility state and resulting planning decision snapshot. |

Do not invent observed-zone-profile provenance for a pure RPE estimate. Preserve existing profile IDs when actual HR methods use them. New evidence can append a new calculation and selection event only under an approved replacement policy; neither old records nor already-approved plans are rewritten automatically.

Activation needs resolved D01-D18 as applicable, versioned approval/reviewer record, implementation/contract checks and integration gates. Existing records retain original methods and correction semantics; default historical migration policy is **no recalculation**. Rollback disables new selection prospectively, retaining new-method records and readers; it must not relabel them as Phase13 or retired RPE-times-hours.

Proposed athlete wording, for approval and privacy review: "Je ervaren inspanning en uitgevoerde duur zijn opgeslagen. De beoordeling is een schatting." No TSS, numeric estimate, correction factor or private weekly target is displayed. Completion must not claim a measured workload or imply zones/plan were changed.
