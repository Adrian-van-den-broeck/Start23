# Joren three-sport planning simulation

Review date: 2026-11-03, Europe/Amsterdam. REVIEW ONLY; no activation.
Accepted engine: `feat/joren-realized-tss-v2`, exact SHA `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch `review/joren-new-workout-catalog`; worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
All private load numbers are developer review evidence, never athlete-facing data.

| Source | Original file | Bytes | SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_Optie1.xlsx | 7198 | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 |
| BIKE | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df |
| SWIM | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674 |
| SWIM spec | Specificatie Zwem TSS.pdf | 149021 | ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a |

RUN original is in `F:\Projecten Business\Start23\Code\docs\trainings`.
BIKE, SWIM and the swim PDF originals are in
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.
All four originals remain byte-identical and at those exact locations. Delivery
is verified; catalog versions and methodological acceptance are separate decisions.

## What ran and what it establishes

The unchanged actual Python planner was used for **57 automatic attempts** (19
cases×3 modes), **eight explicit-selection build witnesses**, **six consecutive-
week explicit-selection proposals**, one seven-hour single-candidate probe,
six fixed-date high-spacing probes and five weekly registration/next-target cases.
All 61 rows also received structural/method/occurrence eligibility probes. A
successful draft is still pending. No athlete record, feature setting, catalog,
coefficient or planner function was mutated/monkeypatched.

There are 28 successful automatic pending drafts,21 actual fail-closed results and
**eight bounded diagnostic timeouts**, not eight engine errors or proven capacity
failures. Each automatic child process had an 8-second wall budget including import/catalog setup,
with at most two running; tests initially ran concurrently. Child processes were
terminated by their owned process handles. Timings are local diagnostics, not an
SLA or an uncontended benchmark. The final 57-result matrix contains no harness errors; bounded timeout outcomes
remain separate from returned engine results.

## Three catalog modes and explicit assumptions

**CURRENT**: `benchmarks.planning.full_catalog()` projects the accepted immutable
migration data plus current built-ins. It has 162 current templates (154 source
rows and 8 built-ins); current source swims are distance-only with P unavailable.
Source-v2 execution/eligibility matches its forward migration. Stable benchmark
UUIDs are fixture identities, not an inventory of hosted generated successor IDs.

**P 50**: 41 timed RUN/BIKE candidates plus nine rest-free single-zone SWIM rows.
It uses PROPOSED phase/bucket/capability/guidance metadata. All source session-focus
ranges remain in the source manifest; each explicit zone has proposed block RPE
range1–2/3–4/5–6/7–8/9–10. The lower endpoint populates the scalar domain field,
and normalized aggregate bounds span block ranges. This avoids assigning focus
RPE 9–10 to Z2, but it requires approval before import. Eleven rest-containing
mixed swims cannot be represented faithfully in the current typed segment model
and are omitted from P 50. Real `with_current_load` is called: nine distance-swim
P values become None, so the timed-only selectable population is41 before phase
filtering. This is the current distance policy, not a new combined activation.

**D61**: all 61 rows in memory, with the same proposed metadata and, deliberately,
distance source P retained directly as a **diagnostic counterfactual**. It passes
these arguments to the actual planner without the current swim P-removal projection.
No code is changed to permit this. Original swimming rest events remain in the
source sidecar; each rest's exact string is appended to its preceding swimming
block's instructions in original order. A rest gets no fabricated zone, RPE,
distance or planned minutes. This textual representation permits a diagnostic
but is not the proposed production typed rest contract. It must not be described
as a source-faithful canonical import or an approved distance method.

Both proposed modes explore the earlier broad automatic eligibility assumption,
including the seven-hour row. The final metadata proposal now holds that row
from automatic beginner use pending Joren scope.

Both proposed modes use a declared **one-decimal source presentation P grid**
(`Decimal(raw).quantize(.1, HALF_EVEN)`) to examine the supplied catalog's displayed
loads. This deliberately resolves binary residues only inside the diagnostic;
original raw values are preserved and no source correction is asserted. It is not
the recommended final operational precision choice: using exact accepted H/A
instead is an approval/implementation gate and needs its own regression/performance
run. UUIDs follow the reproducible proposed policy in the integration sequence.
None of these assumptions is recorded as an actual Joren approval.

## Reproducible scenario inputs

Start Monday2026-10-26, Europe/Amsterdam; default race2027-03-15; all seven dates
available; confirmed zone capabilities satisfy HR and pace; no injury unless
specified. Single-sport tests use only their goal sport; ordinary cases use all 3.
Onboarding baseline comes from the actual engine, not catalog-derived hours.

- `tri_zero`, `run_zero`, `bike_zero`, `swim_zero`: all relevant reported history0,
  no prior approved plan; engine zero-base target 45.0.
- `mixed_history`, `limited_dates`, `one_day`: previous-month minutes SWIM 60,
  BIKE 180, RUN 120; baseline348.8. Limited dates are Monday/Wednesday/Saturday;
  one-day is Monday only. There is no per-day minute budget in the current input.
- `build_1`–`build_4`: four earlier approved build weeks, each planned=realized500,
  sport planned components SWIM 100/BIKE 250/RUN 150. Race is9/8/7/6 weeks after START,
  respectively, giving actual build positions1–4; target 550.00. New Z5 rows enter
  only position 4. Other phase/capacity/high-budget rules remain untouched.
- `recovery`: same history, race10 weeks after START; target 300.00. `taper`: race
  the following Monday, full approved D-7…D-1 week; target 175.00. This does not
  invent a partial-week taper curve.
- `injury_run`, `injury_run_bike`: ordinary positive onboarding components above,
  confirmed injuries as named; bike/swim cross-training opt-ins supplied. Actual
  redistribution limits/caps determine the lower adjusted target.
- `repeat_bike`: goalBIKE, history180min; deck restricted to old BIK-001 or new
  TR-BIKE-001; target 168.8. Each accepted repeat needs a distinct occurrence UUID.
- `candidate_shortage`: empty deck. `no_dates`: ordinary deck, empty availability.
- `high_volume_bike`: goalBIKE, previous-month1200min/week (experienced synthetic
  fixture), target 1125.0. This does not establish beginner suitability.

Fixture scripts and full exact outputs remain in ignored `.runtime/final/`:
`experiment.py`, `run_simulations.py`, `simulations.json`, `witnesses.py/json`,
`continuation.py/json`, `registrations.py/json`, `eligibility_spacing.py` and
`eligibility-spacing.json`. Source hashes and formulas bind reproducibility.
The engineering gates require a committed reproducible harness in the future
implementation; these review scratch files are not new application code.

## All automatic comparisons

Each successful cell gives `eligible candidates; target→selected P; occurrence
count; known minutes`. “Known” never includes invented swimming time. Failure
cells include actual code; timeout cells preserve preflight counts/target only.
The preflight target is unadjusted for injury; successful actual target includes
injury caps. Candidate counts are phase/goal/injury-filtered from that mode's deck,
before any additional final injury-allocation filtering.

| Case | CURRENT | P 50 current distance policy | D61 diagnostic distance P |
| --- | --- | --- | --- |
| tri_zero | 39; catalog_capacity_unsatisfied | 29; catalog_coverage_unsatisfied | 38; target 45.0; TIMEOUT8s (no outcome) |
| run_zero | 21; 45.0→45; 2 sessions; 75 min known | 16; 45.0→46.4; 2 sessions; 80 min known | 16; 45.0→46.4; 2 sessions; 80 min known |
| bike_zero | 17; 45.0→42.00; 1 sessions; 60 min known | 13; 45.0→45.4; 1 sessions; 90 min known | 13; 45.0→45.4; 1 sessions; 90 min known |
| swim_zero | 1; 45.0→46.80; 2 sessions; 80 min known | 0; catalog_empty | 9; 45.0→43.2; 1 sessions; 0 min known |
| mixed_history | 39; 348.8→348.80; 5 sessions; 455 min known | 29; catalog_coverage_unsatisfied | 38; 348.8→348.8; 4 sessions; 310 min known |
| limited_dates | 39; 348.8→348.80; 5 sessions; 455 min known | 29; catalog_coverage_unsatisfied | 38; 348.8→348.8; 4 sessions; 310 min known |
| one_day | 39; 348.8→348.80; 5 sessions; 455 min known | 29; catalog_coverage_unsatisfied | 38; 348.8→348.8; 4 sessions; 310 min known |
| build_1 | 80; target 550.00; TIMEOUT8s (no outcome) | 35; catalog_coverage_unsatisfied | 49; target 550.00; TIMEOUT8s (no outcome) |
| build_2 | 80; target 550.00; TIMEOUT8s (no outcome) | 35; catalog_coverage_unsatisfied | 49; target 550.00; TIMEOUT8s (no outcome) |
| build_3 | 80; target 550.00; TIMEOUT8s (no outcome) | 35; catalog_coverage_unsatisfied | 49; target 550.00; TIMEOUT8s (no outcome) |
| build_4 | 105; target 550.00; TIMEOUT8s (no outcome) | 41; catalog_coverage_unsatisfied | 61; 550.00→550.0; 3 sessions; 510 min known |
| recovery | 39; 300.00→300.00; 5 sessions; 370 min known | 29; catalog_coverage_unsatisfied | 38; 300.00→300.0; 3 sessions; 270 min known |
| taper | 36; taper_catalog_coverage_unavailable | 29; catalog_coverage_unsatisfied | 38; 175.00→175.0; 4 sessions; 180 min known |
| injury_run | 18; 241.3125000000000000000000000→231.80; 4 sessions; 320 min known | 13; catalog_coverage_unsatisfied | 22; 241.3125000000000000000000000→232.0; 5 sessions; 360 min known |
| injury_run_bike | 1; 55.68750000000000000000000002→46.80; 2 sessions; 80 min known | 0; catalog_empty | 9; 55.68750000000000000000000002→50.4; 1 sessions; 0 min known |
| repeat_bike | 1; 168.8→180; 5 sessions; 300 min known | 1; 168.8→181.2; 6 sessions; 360 min known | 1; 168.8→181.2; 6 sessions; 360 min known |
| candidate_shortage | 0; catalog_empty | 0; catalog_empty | 0; catalog_empty |
| no_dates | 39; availability_required | 29; catalog_coverage_unsatisfied | 38; availability_required |
| high_volume_bike | 17; 1125.0→1125.00; 5 sessions; 1260 min known | 13; 1125.0→1125.0; 4 sessions; 1200 min known | 13; 1125.0→1125.0; 4 sessions; 1200 min known |

All proposed-triathlon P 50 attempts fail coverage because SWIM P is unavailable;
SWIM-only fails `catalog_empty`. Their failure precedes later phase/date checks,
so that code is not evidence that dates/phases would otherwise be adequate.

For zero-history D61, the automatic run timed out rather than returning a capacity
code. Independently, its actual candidate/predicate values establish infeasibility
under the unchanged target-fit condition: minimum RUN 17.4 + BIKE 30.2 + SWIM 14.4
=62.0; target 45 differs by17, while `abs(target−selection) < minimum_load14.4`
is required. Adding any positive-load workout only increases the difference.
No athlete-specific starting allocation or smaller workout is fabricated to fix
that gap. CURRENT independently returned `catalog_capacity_unsatisfied`.

## Successful draft sport/intensity coverage

Percentages below are report presentation rounded to two decimals; actual threshold
arithmetic used the unrounded domain values. A “partial time” result excludes all
unknown-duration swims. In swim-only D61 the domain's numeric0%/0min is an empty
known-time total, **not actual zero duration or a complete intensity assessment**.

| Case / mode | Candidates by sport | Selected sports | Low% / high% of known time | Time coverage | Warnings |
| --- | --- | --- | --- | --- | --- |
| run_zero / CURRENT | run:21 | run:2 | 100.00 / 0.00 | complete | none |
| run_zero / D61 | run:16 | run:2 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| run_zero / P 50 | run:16 | run:2 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| bike_zero / CURRENT | bike:17 | bike:1 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| bike_zero / D61 | bike:13 | bike:1 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| bike_zero / P 50 | bike:13 | bike:1 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| swim_zero / CURRENT | swim:1 | swim:2 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| swim_zero / D61 | swim:9 | swim:1 | 0.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio, target_outside_catalog_capacity |
| mixed_history / CURRENT | bike:17, run:21, swim:1 | bike:2, run:1, swim:2 | 100.00 / 0.00 | complete | none |
| mixed_history / D61 | bike:13, run:16, swim:9 | bike:1, run:2, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio |
| limited_dates / CURRENT | bike:17, run:21, swim:1 | bike:2, run:1, swim:2 | 100.00 / 0.00 | complete | workouts_consolidated_on_available_dates |
| limited_dates / D61 | bike:13, run:16, swim:9 | bike:1, run:2, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio, workouts_consolidated_on_available_dates |
| one_day / CURRENT | bike:17, run:21, swim:1 | bike:2, run:1, swim:2 | 100.00 / 0.00 | complete | workouts_consolidated_on_available_dates |
| one_day / D61 | bike:13, run:16, swim:9 | bike:1, run:2, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio, workouts_consolidated_on_available_dates |
| build_4 / D61 | bike:21, run:20, swim:20 | bike:1, run:1, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio |
| recovery / CURRENT | bike:17, run:21, swim:1 | bike:2, run:2, swim:1 | 100.00 / 0.00 | complete | none |
| recovery / D61 | bike:13, run:16, swim:9 | bike:1, run:1, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio |
| taper / D61 | bike:13, run:16, swim:9 | bike:1, run:2, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio |
| injury_run / CURRENT | bike:17, swim:1 | bike:2, swim:2 | 100.00 / 0.00 | complete | realized_intensity_debt_applied, target_outside_catalog_capacity, injured_disciplines_excluded, injury_replacement_capacity_limited |
| injury_run / D61 | bike:13, swim:9 | bike:4, swim:1 | 100.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio, realized_intensity_debt_applied, target_outside_catalog_capacity, injured_disciplines_excluded, injury_replacement_capacity_limited |
| injury_run_bike / CURRENT | swim:1 | swim:2 | 100.00 / 0.00 | complete | realized_intensity_debt_applied, target_outside_catalog_capacity, injured_disciplines_excluded, injury_replacement_capacity_limited |
| injury_run_bike / D61 | swim:9 | swim:1 | 0.00 / 0.00 | PARTIAL TIME | distance_only_swim_excluded_from_time_ratio, realized_intensity_debt_applied, target_outside_catalog_capacity, injured_disciplines_excluded, injury_replacement_capacity_limited |
| repeat_bike / CURRENT | bike:1 | bike:5 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| repeat_bike / D61 | bike:1 | bike:6 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| repeat_bike / P 50 | bike:1 | bike:6 | 100.00 / 0.00 | complete | target_outside_catalog_capacity |
| high_volume_bike / CURRENT | bike:17 | bike:5 | 100.00 / 0.00 | complete | none |
| high_volume_bike / D61 | bike:13 | bike:4 | 100.00 / 0.00 | complete | none |
| high_volume_bike / P 50 | bike:13 | bike:4 | 100.00 / 0.00 | complete | none |

D61 automatic build 4 fits source P 550 with TR-BIKE-012360min, TR-RUN-016150min
and TR-SWIM-0192100m high. It reports0% high over the 510 known timed minutes,
because the only high session is an unknown-duration swim. This is direct evidence
that numeric load fit and existing date scheduling do not establish complete
three-sport80/20 time coverage. C5 must preserve unknown time explicitly and have
approved consumer/reporting behavior; a fake CSS-derived duration is not a fix.

One available day consolidates multiple low workouts and warns; it does not check
whether the athlete can spend455 known minutes (CURRENT) or 310 plus unknown swim
minutes (D61) on that date. Availability is date-only. New and current build/
recovery/taper outcomes therefore cannot be called full athlete feasibility.
D61 recovery/taper have load-fit witnesses but incomplete swimming-time coverage;
CURRENT taper remains `taper_catalog_coverage_unavailable`.

## Build witnesses separate capacity from automatic search

An independent bounded witness generator proposed combinations; the actual
`build_weekly_plan` then validated those exact selections, immutable occurrence
IDs, original filters/caps/high budget and calendar placement. It does not replace
the actual automatic selector or establish its performance. All 8 accepted witness
drafts below are **explicit/swipe-style selections, not automatic successes**.

| Mode / build position | Eligible | Target / selected P | Sport counts | Known minutes | Low% / high% known | Time coverage |
| --- | --- | --- | --- | --- | --- | --- |
| CURRENT / 1 | 80 | 550.00 / 549.90 | bike:2, run:2, swim:1 | 665 | 85.71 / 14.29 | complete |
| CURRENT / 2 | 80 | 550.00 / 549.90 | bike:2, run:2, swim:1 | 665 | 85.71 / 14.29 | complete |
| CURRENT / 3 | 80 | 550.00 / 549.90 | bike:2, run:2, swim:1 | 665 | 85.71 / 14.29 | complete |
| CURRENT / 4 | 105 | 550.00 / 549.90 | bike:2, run:3, swim:1 | 650 | 85.38 / 14.62 | complete |
| D61 / 1 | 49 | 550.00 / 550.0 | bike:2, run:2, swim:1 | 540 | 88.89 / 11.11 | partial |
| D61 / 2 | 49 | 550.00 / 550.0 | bike:2, run:2, swim:1 | 540 | 88.89 / 11.11 | partial |
| D61 / 3 | 49 | 550.00 / 550.0 | bike:2, run:2, swim:1 | 540 | 88.89 / 11.11 | partial |
| D61 / 4 | 61 | 550.00 / 550.0 | bike:1, run:3, swim:2 | 490 | 100.00 / 0.00 | partial |

These witnesses show capacity under the supplied assumptions at build 1–4 despite
several automatic8s timeouts. D61 has 49 candidates (17BIKE/18RUN/14SWIM) in build 1–3
and 61 (21/20/20) in build 4; CURRENT80 and 105 respectively. Both have valid selections
under their own loads. They do not resolve missing source-method approvals,
unknown swimming duration or the difference between source session-focus RPE and
mixed-block guidance. Automatic search performance remains a release gate.

## Actual high-spacing, repeat and seven-hour probes

Fixed separate occurrences of the same high template were scheduled at the gaps
below; neither the original zones nor rest semantics was changed.

| Sport / source template | Gap hours | Actual result |
| --- | --- | --- |
| run / TR-RUN-017 | 48 | rest_or_anti_stack_unsatisfied |
| run / TR-RUN-017 | 72 | placed |
| bike / TR-BIKE-014 | 24 | rest_or_anti_stack_unsatisfied |
| bike / TR-BIKE-014 | 48 | placed |
| swim / TR-SWIM-010 | 24 | rest_or_anti_stack_unsatisfied |
| swim / TR-SWIM-010 | 48 | placed |

Thus RUN 48h fails/72h passes; BIKE/SWIM 24h fails/48h passes. These date-only noon
projections use the current Europe/Amsterdam calendar rule. Repeated source
identities remain separate occurrences. `repeat_bike` selects5 old BIK-001 cards
(P 180,300min) versus6 new TR-BIKE-001 cards (P 181.2,360min) at the same168.8 target;
the source load method changes count and calendar burden.

A single-candidate zero-history diagnostic intentionally retains only TR-BIKE-013.
The actual engine returns pending target 45→P 393.8, **420min**, capacity warning.
It has not approved novice suitability; the loose closest-fit rule uses this
large single candidate as its minimum. This exposes a material source-selection
scope gap. The final metadata proposal holds automatic beginner use of this row
pending Joren's decision. No new physiological cap or silent selector fix was made.

## Consecutive weeks with actual weekly consumers

For CURRENT and D61, three explicit-witness proposals were generated starting
build 1. Four initial P=R500 weeks anchor target 550. Week1 completion is synthetic
supported evidence: single-zone timed rows use favorable compatible-context RPE
at confirmed A=T; mixed timed rows have independent synthetic observed zone bins.
For swims, the supplied actual observation fixture is30min Z2, independently of
source distance, source P and RPE. It does not certify performance of prescribed
hard blocks or distance. Week2 deliberately omits one expected occurrence. Week3
restores complete registration. Original source time never fabricates swim A/T.

| Mode / week | Target / basis | Selected P / known min | Known subtotal / usable | Registration reason |
| --- | --- | --- | --- | --- |
| CURRENT / 2026-10-26 | 550.00 / realized_progression | 549.90 / 665 | 454.44 / 454.44 | complete |
| CURRENT / 2026-11-02 | 604.8900 / realized_progression | 604.90 / 725 | 242.640 / None | unknown_workout_completion |
| CURRENT / 2026-11-09 | 604.90 / prior_planned_hold | 604.90 / 725 | 521.640 / 521.640 | complete |
| D61 / 2026-10-26 | 550.00 / realized_progression | 550.0 / 540 | 545.2000 / 545.2000 | complete |
| D61 / 2026-11-02 | 605.000 / realized_progression | 605.0 / 520 | 404.4000 / None | unknown_workout_completion |
| D61 / 2026-11-09 | 605.0 / prior_planned_hold | 605.0 / 520 | 544.6000 / 544.6000 | complete |

Both week 3 targets hold prior planned load rather than grow from the incomplete
week 2 subtotal. A complete week alone does not mandate actual×1.10: existing
completion/baseline/fatigue conditions determine the unchanged basis, e.g D61
week 1 actual 545.2 still leads next target 605 from prior planned550 under this
fixture. Those consumer rules and coefficients were not modified. New-source
method compatibility in these favorable contexts is an assumption; a genuinely
new unsupported method/version must fail closed until explicitly accepted.

## Measured, estimated, unrecorded, skipped and mixed-incomplete evidence

An independent three-sport registration fixture has exact expected RUN/BIKE/SWIM
occurrences, prior approvedP150, next week 2026-10-26, race2026-12-27. Supplied
synthetic evidence is RUN measured27.6; BIKE supported RPE estimate84.4; SWIM,
when measured,21.6 from actual 30-minute Z2 bins. Partial bike is observed40,
not a whole-session estimate. No source-distance performance is inferred.

| Case | Known subtotal | Usable total | Next target / basis | Reason |
| --- | --- | --- | --- | --- |
| complete_mixed | 133.6 | 133.6 | 165.00 / realized_progression | complete |
| unrecorded | 112.0 | None | 150 / prior_planned_hold | unknown_workout_completion |
| explicit_skip | 112.0 | 112.0 | 112.0 / realized_baseline | complete |
| mixed_incomplete | 67.6 | None | 150 / prior_planned_hold | partial_or_unavailable_load |
| pending_feedback | 112.0 | None | 150 / prior_planned_hold | pending_feedback |

Explicit skip establishes a resolved occurrence without performed load; unknown
or pending feedback does not. Partial observations and mixed intervals without
supported measurement cannot be upgraded using Session-RPE. V2 is not added to or
multiplied into an existing measurement. The all 61 gate probes yield29 favorable
timed conditional estimates, nine missing-T singles and 23 mixed exclusions;
all actual new fully established source occurrences remain0.

## Calendar and per-session evidence

Below are all D61 automatic successful sessions, the CURRENT mixed-history
comparison and representative explicit build witnesses1/4. Minutes “unknown”
are preserved as unknown; distances remain meters. The original ordered source
and rest/guidance trace is retained in each fixture, not recast as focus zone.

| Case / mode | Source/template | Sport | Date | Minutes | Meters | Snapshot P / bucket |
| --- | --- | --- | --- | --- | --- | --- |
| run_zero / D61 | TR-RUN-001 | run | 2026-10-26 | 30 | not prescribed | 17.4 / low |
| run_zero / D61 | TR-RUN-003 | run | 2026-10-29 | 50 | not prescribed | 29.0 / low |
| bike_zero / D61 | TR-BIKE-002 | bike | 2026-10-29 | 90 | not prescribed | 45.4 / low |
| swim_zero / D61 | TR-SWIM-005 | swim | 2026-10-29 | unknown | 3000 | 43.2 / low |
| mixed_history / CURRENT | BIK-011 | bike | 2026-10-26 | 240 | not prescribed | 195 / low |
| mixed_history / CURRENT | Aerobic swim | swim | 2026-10-27 | 40 | 1600 | 23.40 / low |
| mixed_history / CURRENT | Aerobic endurance | bike | 2026-10-29 | 60 | not prescribed | 42.00 / low |
| mixed_history / CURRENT | RUN-016 | run | 2026-10-30 | 75 | not prescribed | 65 / low |
| mixed_history / CURRENT | Aerobic swim | swim | 2026-10-31 | 40 | 1600 | 23.40 / low |
| mixed_history / D61 | TR-RUN-003 | run | 2026-10-26 | 50 | not prescribed | 29.0 / low |
| mixed_history / D61 | TR-SWIM-008 | swim | 2026-10-27 | unknown | 4500 | 64.8 / low |
| mixed_history / D61 | TR-BIKE-007 | bike | 2026-10-29 | 180 | not prescribed | 168.8 / low |
| mixed_history / D61 | TR-RUN-009 | run | 2026-10-30 | 80 | not prescribed | 86.2 / low |
| limited_dates / D61 | TR-RUN-009 | run | 2026-10-26 | 80 | not prescribed | 86.2 / low |
| limited_dates / D61 | TR-SWIM-008 | swim | 2026-10-26 | unknown | 4500 | 64.8 / low |
| limited_dates / D61 | TR-BIKE-007 | bike | 2026-10-28 | 180 | not prescribed | 168.8 / low |
| limited_dates / D61 | TR-RUN-003 | run | 2026-10-31 | 50 | not prescribed | 29.0 / low |
| one_day / D61 | TR-BIKE-007 | bike | 2026-10-26 | 180 | not prescribed | 168.8 / low |
| one_day / D61 | TR-RUN-003 | run | 2026-10-26 | 50 | not prescribed | 29.0 / low |
| one_day / D61 | TR-RUN-009 | run | 2026-10-26 | 80 | not prescribed | 86.2 / low |
| one_day / D61 | TR-SWIM-008 | swim | 2026-10-26 | unknown | 4500 | 64.8 / low |
| build_4 / D61 | TR-BIKE-012 | bike | 2026-10-26 | 360 | not prescribed | 337.5 / low |
| build_4 / D61 | TR-SWIM-019 | swim | 2026-10-29 | unknown | 2100 | 50.8 / high |
| build_4 / D61 | TR-RUN-016 | run | 2026-10-30 | 150 | not prescribed | 161.7 / low |
| recovery / D61 | TR-RUN-001 | run | 2026-10-26 | 30 | not prescribed | 17.4 / low |
| recovery / D61 | TR-BIKE-009 | bike | 2026-10-29 | 240 | not prescribed | 225.0 / low |
| recovery / D61 | TR-SWIM-007 | swim | 2026-10-30 | unknown | 4000 | 57.6 / low |
| taper / D61 | TR-RUN-004 | run | 2026-10-26 | 30 | not prescribed | 32.3 / low |
| taper / D61 | TR-SWIM-008 | swim | 2026-10-27 | unknown | 4500 | 64.8 / low |
| taper / D61 | TR-BIKE-003 | bike | 2026-10-29 | 120 | not prescribed | 60.5 / low |
| taper / D61 | TR-RUN-001 | run | 2026-10-30 | 30 | not prescribed | 17.4 / low |
| injury_run / D61 | TR-BIKE-002 | bike | 2026-10-26 | 90 | not prescribed | 45.4 / low |
| injury_run / D61 | TR-BIKE-002 | bike | 2026-10-27 | 90 | not prescribed | 45.4 / low |
| injury_run / D61 | TR-BIKE-002 | bike | 2026-10-29 | 90 | not prescribed | 45.4 / low |
| injury_run / D61 | TR-BIKE-002 | bike | 2026-10-30 | 90 | not prescribed | 45.4 / low |
| injury_run / D61 | TR-SWIM-006 | swim | 2026-10-31 | unknown | 3500 | 50.4 / low |
| injury_run_bike / D61 | TR-SWIM-006 | swim | 2026-10-29 | unknown | 3500 | 50.4 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-26 | 60 | not prescribed | 30.2 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-27 | 60 | not prescribed | 30.2 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-28 | 60 | not prescribed | 30.2 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-29 | 60 | not prescribed | 30.2 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-30 | 60 | not prescribed | 30.2 / low |
| repeat_bike / D61 | TR-BIKE-001 | bike | 2026-10-31 | 60 | not prescribed | 30.2 / low |
| high_volume_bike / D61 | TR-BIKE-012 | bike | 2026-10-26 | 360 | not prescribed | 337.5 / low |
| high_volume_bike / D61 | TR-BIKE-010 | bike | 2026-10-27 | 300 | not prescribed | 281.2 / low |
| high_volume_bike / D61 | TR-BIKE-007 | bike | 2026-10-29 | 180 | not prescribed | 168.8 / low |
| high_volume_bike / D61 | TR-BIKE-012 | bike | 2026-10-30 | 360 | not prescribed | 337.5 / low |
| build_1 EXPLICIT / D61 | TR-BIKE-001 | bike | 2026-10-26 | 60 | not prescribed | 30.2 / low |
| build_1 EXPLICIT / D61 | TR-RUN-013 | run | 2026-10-27 | 120 | not prescribed | 129.4 / low |
| build_1 EXPLICIT / D61 | TR-RUN-017 | run | 2026-10-29 | 60 | not prescribed | 87.6 / high |
| build_1 EXPLICIT / D61 | TR-BIKE-010 | bike | 2026-10-30 | 300 | not prescribed | 281.2 / low |
| build_1 EXPLICIT / D61 | TR-SWIM-002 | swim | 2026-10-31 | unknown | 1500 | 21.6 / low |
| build_4 EXPLICIT / D61 | TR-SWIM-019 | swim | 2026-10-26 | unknown | 2100 | 50.8 / high |
| build_4 EXPLICIT / D61 | TR-RUN-004 | run | 2026-10-27 | 30 | not prescribed | 32.3 / low |
| build_4 EXPLICIT / D61 | TR-RUN-010 | run | 2026-10-28 | 90 | not prescribed | 97.0 / low |
| build_4 EXPLICIT / D61 | TR-SWIM-018 | swim | 2026-10-29 | unknown | 1600 | 37.3 / high |
| build_4 EXPLICIT / D61 | TR-BIKE-011 | bike | 2026-10-30 | 330 | not prescribed | 309.4 / low |
| build_4 EXPLICIT / D61 | TR-RUN-002 | run | 2026-10-31 | 40 | not prescribed | 23.2 / low |

Remaining beginner limitations: zero-history triathlon composition is not filled;
new swimmer distance P has no approved planning path; simple cycling can turn a
45 target into a90-minute session; dates lack minute budgets; sparse decks can
offer a seven-hour card absent athlete-scope policy. Recovery/taper numeric fit
is not full time/suitability evidence. Timeout cases need uncontended performance
analysis and bounded-search verification before release; no optimization or rule
change is implemented in this review.

Exact results above are prospective conditional fixtures. They are neither
production guarantees nor approvals of the proposed metadata/scientific methods.

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.

Focused reproduction command, from `backend` with the existing virtualenv:

```text
python -B -m pytest -q -p no:cacheprovider tests/test_workout_catalog.py tests/test_workout_catalog_seed_parity.py tests/test_workout_catalog_repository.py tests/test_training_source_catalog_audit.py tests/test_source_catalog_import_migration.py tests/test_realized_v2_catalog.py tests/test_realized_context.py tests/test_realized_v2_planning.py tests/test_realized_v2_migration.py tests/test_planning_domain.py tests/test_contracts.py tests/test_a9_planning_parity.py tests/test_mvp_catalog_coverage.py tests/physiology/test_joren.py tests/physiology/test_rpe_zones.py tests/physiology/test_realized_v2.py tests/physiology/test_weekly_registration.py
```

Ruff/format, strict mypy and mobile checks were not rerun in this documentation-only
continuation: no application or test files changed. Their prior accepted results
remain attributed to the implementation/running reports; implementation/release
gates in C8 still require relevant new checks.
