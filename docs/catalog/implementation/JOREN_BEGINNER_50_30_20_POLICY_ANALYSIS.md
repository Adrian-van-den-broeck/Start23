# Beginner composition and sport-distribution policy analysis

2026-11-04, Europe/Amsterdam. Private developer review; all loads are server-private.
These are synthetic local planner probes and policy comparisons, not training
advice, scientific suitability approval or activated rules.

## The concrete conflict

The actual `starting_baseline` returns45.0 for explicit zero history. The easiest
new displayed-source combination is BIKE00130.2 + RUN00117.4 + SWIM00116.9 =64.5,
three occurrences. That is19.5 (43.33%) above the existing target, with60+30 known
timed minutes and1000m swimming whose time remains unknown. “Suitable” still
requires confirmed capabilities, restrictions and individual scope; lowest load
alone does not establish suitability.

The actual planner rejects the three-row zero-history deck at45 automatically
(`catalog_capacity_unsatisfied`) and explicitly (`swipe_selection_invalid`).
An isolated counterfactual input of64.5 allows exactly the three sessions as a
pending draft. It does not approve a new baseline or progression exception.
Even using unrounded experimental values would give64.51875, not a solution at45.

| Denominator | BIKE | RUN | SWIM | Result |
| --- | --- | --- | --- | --- |
| Proposed shares of target45 |22.5|13.5|9.0|Every minimum source session exceeds its quota |
| Actual starter selected64.5 |46.8217%|26.9767%|26.2016%|Does not satisfy exact50/30/20 |
| Proposed shares of64.5 |32.25|19.35|12.90|Minimum swim16.9 exceeds swim quota |

Exact20% swimming with at least16.9 requires total≥84.5 purely algebraically.
This is not a recommendation to raise load, evidence of a feasible workout
combination or authorization to fill up to that total. Hard weekly percentages
may produce no solution even after increasing a ceiling. Rounding percentages
cannot eliminate the missing19.5 budget or replace an approved tolerance.

## What the unchanged planner actually ran

Committed harness: `backend/benchmarks/joren_c2.py`. Reproduce from backend with
`python -B -m benchmarks.joren_c2 --private-output NEW_PATH`; outputs are exclusive,
private local artifacts. The golden JSON records exact target, selected load,
counts, shares, dates, warnings and outcomes. No network, database or application
setting is used. No source-conflicted swim row enters the synthetic deck.

The deck consists only of the three easiest rows plus a separate long-bike
hazard witness. Displayed P is explicitly assumed for diagnosis. Source swim
distance P is retained directly in that isolated input, bypassing the current
distance-P exclusion only in the fixture. This is not a new catalog adapter.
Automatic searches here are small and bounded by the existing planner; this
does not close the older eight full-deck diagnostic timeouts or C7.

| Probe | Actual result | Safety/capacity implication |
| --- | --- | --- |
| Triathlon baseline45, automatic | Rejected | No three-sport solution from these minima |
| Triathlon baseline45, explicit three | Rejected | Explicit selection does not waive load fit |
| Synthetic starter64.5 |3 sessions,64.5 pending;46.82/26.98/26.20% | Unknown swim time warning; no scientific ceiling approval |
| Same starter, one available date |3 sessions on that date;90 known minutes plus unknown swim | Date availability does not prove time capacity; consolidation warning |
| No available dates |availability_required | No invented schedule/date availability |
| Run injury, zero history |restricted_zero_base_allocation_unavailable | No guessed starting allocation or automatic redistribution |
| All three injured |Rest-only pending draft,0 sessions/0 load | Restriction precedence survives |
| Swim capability absent or unconfirmed |catalog_coverage_unsatisfied | Missing discipline is not silently treated as feasible |
| Build after independently complete synthetic week64.5 |Target70.950, three sessions64.5 accepted with fit warning | Current selector permits low-only when no eligible high candidate fits; exact per-sport80/20 is not implemented |
| Recovery after prior64.5 |Target38.700; three-session selection rejected | Starter exception would need phase scope; cannot repeat automatically |
| Full taper after prior64.5 |Target22.575; three-session selection rejected | Taper has precedence; no blanket starter waiver |
| Sole BIKE013, target45 |One420min session393.8 pending with capacity warning | Current closest-fit tolerance can admit a huge sole minimum; target is not a hard ceiling |

The last hazard witness deliberately removes the proposed beginner hold in an
isolated fixture to expose the existing behavior. It does not activate BIKE013
or claim novice suitability. There is no per-session minute budget in the input;
no arbitrary time cap was added. A target split alone cannot protect athletes
from long sessions: even exact50% bike can allow393.8 when weekly load is787.6,
and a flexible split gives still less assurance. Athlete-specific eligibility
and capability/availability policy must be approved independently for long rows.

Single-sport goals, using only that sport's easiest synthetic row at45, give
BIKE one30.2/60min; RUN three repeats52.2/90min; SWIM three repeats50.7/unknown
minutes. Each has100% of its goal sport and capacity warnings; these are actual
closest-fit diagnostics, not hard-budget successes. Applying nonzero quotas for
absent goal sports is infeasible. Do not silently introduce triathlon or renormalize
quotas; the owner must define goal-specific scope. Repeats remain distinct
occurrences under existing identity/scheduling rules.

## Denominators and enforcement still needing a decision

The supplied statement specifically proposes **weekly planned TSS** for sport
distribution. That supports selection intent based on planned work; performed
load is separate retrospective evidence. Still define whether percentages divide
by selected planned total, desired weekly target, eligible/uninjured subtotal or
another approved denominator, and how incomplete actual registration influences
later selection. Do not substitute performed load into planning quotas implicitly.

The existing80/20 reporting denominator is known prescribed duration, assigning
the complete workout to its catalog bucket. Execution block zones remain separate.
The current build selector also enforces a private high-load budget (and phase/
build-position conditions), rather than an exact time ratio. Moving “the existing
principle” per sport therefore does not identify one unambiguous mathematical
policy. Define whether to retain both existing measures, use time or load, allow
100% easy sparse weeks, and whether20% high is a ceiling or required quota.

Three easy sessions are100/0 per sport by prescribed focus/load. RUN/BIKE known
time is also100/0. Complete swim time is unavailable; it must not be reported as
proven zero-duration or full time coverage. Three easy sessions satisfy a proposed
“at most20% high” rule but cannot satisfy exact80/20 or a required minimum20% high
in each sport. Adding hard sessions would contradict the confirmed three easiest
sessions and could violate existing high-load, injury, spacing and phase rules.

Explicit decisions required: hard ratio versus flexible optimization; allowable
deviation and rounding stage; infeasible quotas and no-solution behavior; which
sports are required for each goal; missing capabilities/contraindications and
consent/caps; low-only restrictions; recovery/taper precedence; single-week versus
rolling multi-week enforcement and carry-forward/reset behavior. No quota debt
or catch-up mechanism is approved, so deficits must not automatically increase a
later week or redistribute injury load.

## Four policy alternatives, none enabled

| Alternative | Planned load / sport percentages / count | Safety/capacity | Following weeks | Required approval |
| --- | --- | --- | --- | --- |
|1. Hard budget45 and safe no-solution |No feasible three-session plan; no applied load or new occurrences. Demanded combination64.5 at46.82/26.98/26.20% is rejected |Retain ceiling and constraints; surface qualitative no-solution/review rather than selecting an unsafe fallback |No synthetic completed week or increased baseline; preserve existing approved state and registration holds |Owner defines hard-ceiling semantics and no-solution UX; scientific rules remain unchanged |
|2. Explicit beginner starter exception |64.5 displayed,46.82/26.98/26.20%,3 workouts,90 known min+1000m unknown time |Separate reviewed ceiling, individual scope and phase applicability required; does not meet exact50/30/20 |Complete independent evidence can resolve next target70.95; incomplete holds64.5; recovery38.7/taper22.575 cannot fit this same starter |Owner/Joren and accountable scientific reviewer approve exception ceiling, duration/capability scope, progression basis, ceiling after week1 and exit/hold rules; precision decision first |
|3. Genuinely easier workouts supplied by Joren |Not supplied: actual P/shares/count cannot be certified. For3 exact50/30/20 sessions at45, limits are22.5/13.5/9.0 |No scaling, truncation or invented prescriptions/formulas; new source rows need complete verification, rest/focus guidance and suitability |A45 plan with independently complete realized45 would normally target49.5 in build; recovery27 and taper15.75 from a45 baseline require suitable smaller sessions too |Joren supplies approved exact workouts and method evidence; owner approves release/scope; scientific review of novice fit and multi-week coverage |
|4. Controlled phased introduction |Example only: RUN+SWIM34.3,0/50.73/49.27%,2 workouts; BIKE alone30.2,100/0/0%,1 workout. BIKE+RUN47.6 and BIKE+SWIM47.1 exceed45 |Breaks confirmed one-per-sport first-week intent; no actual triathlon plan with a missing sport was generated or enabled |Alternating those two illustrative weeks averages32.25/week, with combined46.82/26.98/26.20%—still not50/30/20. Later untrained-sport introduction needs an approved baseline; no implicit catch-up |Explicit owner product change, Joren sequence and scientific progression/intro criteria; goal and zero-history-discipline rules need new approved specification |

Option3's next-target numbers are unchanged deterministic factor consequences
conditional on the specified independently complete history and phase, not
newly supplied workouts or a promise of feasible future catalog selections.

## Consecutive-week evidence after a hypothetical approved exception

The harness supplies independently hypothetical measured load30.2/17.4/16.9
and method provenance for a complete week; these are **not** inferred from source
prescriptions, CSS or session RPE. Missing swim registration is absent, not zero;
explicit skip is separately recorded. This isolates consumer behavior.

| Week1 evidence after hypothetical64.5 plan | Week2 resolved target / basis | Same three-session selection |
| --- | --- | --- |
|Complete independent observations total64.5 |70.950 / realized_progression |64.5 accepted with capacity warning; target does not force exact selected load |
|Swim unrecorded; known subtotal47.6 |64.5 / prior_planned_hold |64.5 pending; no progression from incomplete subtotal |
|Swim explicitly skipped; usable47.6 |47.6 / realized_baseline |64.5 rejected; skip is not unknown |

After a complete week1 and incomplete week2 whose actual selected plan remains64.5,
the real week3 planner holds64.5. It does not grow automatically from the larger
week2 target70.95. Conversely, a future approved selection exactly70.95 with
fully supported completion could produce78.045 under regular10% progression;
that arithmetic is conditional, not an executed-plan outcome or safety approval.
Approving only a one-off64.5 ceiling leaves these subsequent-week questions open.

All existing high-spacing, injury/consent/caps, build/recovery/taper, registration,
identity and approval protections remain unchanged and are regression-tested.
No alternative is enabled. Source-method, six-row correction, beginner policy,
sport/intensity allocation and long-session suitability approvals remain pending.
