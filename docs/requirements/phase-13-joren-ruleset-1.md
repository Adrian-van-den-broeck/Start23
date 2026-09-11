# Phase 13 Joren ruleset 1

Version: `phase-13-joren-ruleset-1`. Product decisions accepted 2026-09-10;
implementation continued 2026-09-11. Production review remains open.

This version supersedes conflicting active behavior. Prior ruleset definitions,
activity calculations, zone profiles and applied migrations retain their meaning.
See [Deprecated Phase 13](deprecated-phase-13.md) for the previous roadmap.

Sources:
- [Zone load and textual RPE](<Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf>)
- [Onboarding](Triathlon_Onboarding_StartTSS.pdf)
- [Calibration](Triathlon_Zone_Calibratie_Voorbeelden.pdf)

Tracked source SHA-256 provenance:

| Source | SHA-256 |
| --- | --- |
| `Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf` | `747B65D071FFAFACA2DAD4FE07D21403D42669299E6DEEBB6F14C3A2CFB5CB69` |
| `Triathlon_Onboarding_StartTSS.pdf` | `94038EE66C0FA11E0EC13B71F83AFBB1477433BD80466BF77B40ACFC91C8B713` |
| `Triathlon_Zone_Calibratie_Voorbeelden.pdf` | `4EDD6CA3ABC0B1CD4E9F6DD346BB836E5EFF7D440330142171075FA949DF090E` |

## Implementation conventions and source discrepancies

- All authoritative arithmetic is Python Decimal. Weekly hours are collected as
  decimal strings; storage uses previous-month weekly minutes. Historical
  two-month distance/frequency and older weekly minutes are not converted.
- Start-TSS is private, including the rounded final baseline. The wording
  "athlete-facing/final" below prescribes rounding, not authorization to expose it.
- Full precision components are summed before final total rounding. PDF all-round
  swim uses a rounded hourly coefficient: exact 126.5625 rounds to 126.6, while
  the exact total 658.125 rounds to 658.1. Do not sum rounded components.
- The sRPE run example printed as 64.6 is exactly 64.6875 (64.7 half up).
- HR boundaries are inclusive integers. LTHR 165 yields <=134, 135-147,
  148-157, 158-165, >=166. Thresholds are rounded half up first.
- CSS is rounded to whole seconds first. From slow to fast the cutoffs use
  rounded 115%, 107%, 102%, 98%; adjacent inclusive integer bounds fill the
  display percentage gaps. CSS 107 yields >=124, 115-123, 110-114, 105-109,
  <=104. The PDF omits 123 seconds; it belongs to Z2 under the formula.
- Existing protocol definitions remain immutable. The first mandatory calibration
  observation block provides the RPE and objective metric; optional blocks and
  warm-up/cool-down cannot replace it. Missing, interrupted, insufficient-quality
  or unstable evidence fails closed. Swim uses explicitly measured elapsed swim
  time and distance, never HR or inferred duration.
- Historical shared-boundary profiles retain `start23-zone-model-1.0` classification.
  New calibration evaluations and confirmation retain their exact model version.
- Planned duration without authoritative zone time is unavailable, including
  protocol-only workouts. Catalog prescriptions are retained, but unavailable
  loads cannot enter load-target selection. No sRPE fallback is selected.
- New activity calculations preserve total duration, observed zone duration,
  coverage, method and status privately. Partial observations are not labelled a
  perfect full-session match. Revising old RPE retains its historical method and
  snapshots the prior private calculation in an append-only audit table.
- New planning history separates legacy calculation units instead of relabelling
  them. The original history RPC remains available for historical interpretation.
- A Monday race has an exact preceding Monday-Sunday taper week and can retain
  the reviewed A-race 35% target. For other race weekdays the weekly target
  fails closed: no approved daily reduction curve exists. All injury/rest-only
  precedence and pending approval requirements remain in place.

## Amendment accepted 2026-09-11: average heart rate

This amendment is part of this unreleased version before its first deployment.
Observed time in zones, including partial coverage, remains authoritative. If
only average heart rate is available and the athlete has known, confirmed HR
zones, assign the reliable full activity duration to the zone containing that
average. Use the discipline's zone coefficient. Store the method separately as
`average_hr_zone_duration`, status `estimated_from_average_hr`, observed zone
minutes/coverage zero, the average, assigned zone and exact zone-profile ID.
Do not represent this estimate as measured time in zone. Pending zones cannot
supply it, swim remains pace/CSS based, and sRPE remains inactive. RPE corrections
retain the originating profile, even if newer zones have since been activated.
The original observed-only/missing-HR wording below is qualified by this explicit
later amendment. Partial observed time is not scaled to the entire session.

## Authoritative product decisions

1. ONBOARDING / START-TSS

Use Joren's Triathlon_Onboarding_StartTSS.pdf model as the new official
onboarding baseline model.

Do NOT use the previous roadmap proposal based on two months of metres/km plus
session frequency.

The new onboarding input is the athlete's average training hours per week over
the previous month, separately for:

- swimming
- cycling
- running

Use the PDF formula:

StartTSS_discipline =
    average_hours_per_week
    × (0.75² × 100)
    × sport_multiplier

Sport multipliers:

- swim = 0.90
- bike = 1.00
- run = 1.15

Therefore the exact unrounded coefficients are:

- swim = 50.625 TSS/hour
- bike = 56.25 TSS/hour
- run = 64.6875 TSS/hour

Use Decimal/fixed precision rather than binary floating point for authoritative
calculations.

Keep full precision during calculation.

Round athlete-facing/final weekly Start-TSS values to one decimal using
ROUND_HALF_UP. Do not repeatedly round intermediate values.

The examples in Joren's PDF must become deterministic fixtures.

Input rules:
- zero is valid;
- negative values are invalid;
- NaN/infinity are invalid;
- values must represent a physically possible weekly duration;
- the combined average training duration across disciplines may not exceed
  168 hours/week.

Prefer storing a canonical duration representation such as minutes/week rather
than depending on floating-point hours internally.

ZERO-BASE RULE

Joren's document specifies approximately 40-50 total TSS for a complete
beginner but does not select one exact value.

For this ruleset, use:

    zero_base_start_tss = 45.0

This is a Start23 product decision selecting the midpoint of Joren's proposed
40-50 range. Record it as such; do not falsely attribute the exact 45.0 value
to Joren's PDF.

Use it only when the athlete has zero previous-month training hours across all
relevant disciplines.

Do not invent additional discipline-specific minimum TSS values when only one
discipline has zero history. Preserve safe planner/fail-closed behavior where
the catalog cannot satisfy the requested composition without inventing load.

2. TEXTUAL RPE

Use the complete discipline-specific RPE 1-10 descriptions from:

docs/requirements/Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf

The canonical internal values remain integers 1-10.

Athlete-facing flows should use the textual discipline-specific descriptions
where Phase 15/UI work requires them.

Triathlon and duathlon use their component discipline descriptions.

3. RUN AND BIKE CALIBRATION

Use the same HR/LTHR reverse-engineering algorithm for running and cycling.

Use Joren's RPE anchor factors:

RPE 1  = 0.70
RPE 2  = 0.78
RPE 3  = 0.84
RPE 4  = 0.88
RPE 5  = 0.91
RPE 6  = 0.94
RPE 7  = 0.97
RPE 8  = 1.00
RPE 9  = 1.03
RPE 10 = 1.06

Formula:

    estimated_LTHR = average_HR / RPE_anchor_factor

Round the calculated LTHR to the nearest whole bpm using ROUND_HALF_UP.

Derive the five HR zones using Joren's percentages:

- Z1: <82% LTHR
- Z2: 82-89%
- Z3: 90-95%
- Z4: 96-100%
- Z5: >100%

Because bpm is represented as discrete whole numbers, the persisted/public
zone boundaries MUST be contiguous and mutually exclusive:

- every whole bpm belongs to exactly one zone;
- there may be no overlap;
- there may be no unassigned bpm between adjacent zones.

Use deterministic rounding and boundary ownership that reproduces Joren's
examples where possible.

A suitable implementation is to derive rounded integer boundary points and
make the next zone begin immediately after the previous zone's inclusive upper
bound.

For example, Joren's LTHR=165 fixture must resolve to:

- Z1: <135
- Z2: 135-147
- Z3: 148-157
- Z4: 158-165
- Z5: >165

Add explicit equality/boundary tests.

4. SUSPICIOUS CALIBRATION RESULTS

Use Option A.

A suspicious result does NOT block calculation.

If the calculated run/bike LTHR is below 140 bpm:

- calculate the zones normally;
- create the normal pending calculated zone profile;
- attach/display an explicit warning that the calculated threshold appears
  unusually low and should be reviewed;
- do not auto-activate the profile;
- do not require a second calibration session automatically.

The athlete must still explicitly approve the pending zone proposal according
to the existing stale-safe approval lifecycle.

Treat <140 bpm as the current ruleset warning boundary.

This is a warning boundary, not a hard physiological rejection boundary.

5. SWIM CALIBRATION

Swimming deliberately does NOT use heart rate for calibration.

This is an explicit Start23 decision.

Use pace per 100 metres and CSS according to Joren's
Triathlon_Zone_Calibratie_Voorbeelden.pdf.

Formula:

    estimated_CSS_seconds_per_100m =
        observed_pace_seconds_per_100m / RPE_anchor_multiplier

Use Joren's swim RPE multipliers:

RPE 1  = 1.25
RPE 2  = 1.18
RPE 3  = 1.12
RPE 4  = 1.08
RPE 5  = 1.06
RPE 6  = 1.04
RPE 7  = 1.01
RPE 8  = 1.00
RPE 9  = 0.96
RPE 10 = 0.92

Use the Joren swim zones:

- Z1: >115% CSS
- Z2: 108-114% CSS
- Z3: 103-107% CSS
- Z4: 98-102% CSS
- Z5: <98% CSS

Use whole seconds/100m for canonical athlete-facing pace boundaries.

Apply deterministic nearest-value rounding and make the resulting integer
pace intervals contiguous and mutually exclusive.

Every whole-second pace must belong to exactly one zone.

Where a PDF display example and the mathematical percentage formula differ by
one second because of presentation rounding, treat the formula as
authoritative, do not create a gap, and document the discrepancy in the test
or ruleset notes.

Preserve the inverse nature of pace: lower seconds = higher intensity.

Swim calibration also creates only a pending zone proposal and never
automatically activates zones.

6. NEW OFFICIAL PRIVATE TSS / LOAD FORMULA

The zone-based formula in:

docs/requirements/Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf

becomes the new official active private-load formula.

Use:

    TSS = Σ(minutes_in_zone × discipline_zone_TSS_per_minute)

Official values:

             Swim    Bike    Run
Z1           0.45    0.50    0.58
Z2           0.72    0.80    0.92
Z3           1.08    1.20    1.38
Z4           1.44    1.60    1.84
Z5           1.80    2.00    2.30

Use these for planned and realized private load where the required duration /
time-in-zone information exists.

For planned workouts:
- use authoritative planned time in zones when present.

For completed activities:
- use observed valid time in zones.

Keep these values private exactly as the project currently requires.
Planned/realized TSS must never leak into public APIs, mobile UI, logs,
analytics, accessibility labels, or LLM prompts.

This replaces the existing active RPE × duration realized-load behavior for the
new ruleset.

Historical calculations must remain attributable to the ruleset/calculation
method that originally produced them.

Do not silently reinterpret an old historical value as if the new formula had
created it.

7. PARTIAL HEART-RATE / TIME-IN-ZONE DATA

Do NOT extrapolate missing HR time.

Example:

- activity duration = 60 minutes
- valid zone time = 41 minutes

Calculate realized private load only from the observed 41 valid minutes.

Do NOT multiply or scale those 41 minutes to estimate the missing 19 minutes.

Persist enough private provenance to know:

- total activity duration;
- valid zone-time duration;
- coverage ratio;
- that the load was based on partial observed data.

Example:

    coverage_ratio = 41 / 60 = 0.6833...

The resulting load may be used only as the actually observed private load; it
must never be represented as a complete 60-minute measurement.

This conservative observed-only behavior is intentional.

8. DISTANCE-ONLY SWIMMING

If a swim has distance but no reliable duration/time-in-zone information:

- preserve the distance and workout/activity normally;
- do not infer duration from distance;
- do not infer TSS from CSS or assumed pace;
- do not fabricate zone time;
- mark private load as unavailable/incomplete for that workout/activity;
- exclude the nonexistent load value from calculations that require an actual
  load value;
- preserve existing fail-closed/fallback behavior where required.

If reliable duration/time-in-zone data later exists for an actual completed
swim, the normal active load formula may be applied.

9. sRPE FALLBACK

Implement/preserve the sRPE fallback formula from Joren's PDF correctly, but
keep it INACTIVE for the current MVP ruleset.

Formula:

    TSS =
      (duration_hours × IF² × 100) × sport_multiplier

RPE → IF:

1  = 0.45
2  = 0.55
3  = 0.65
4  = 0.75
5  = 0.82
6  = 0.88
7  = 0.94
8  = 1.00
9  = 1.05
10 = 1.15

Sport multipliers:

- swim = 0.90
- bike = 1.00
- run = 1.15

The implementation must have deterministic unit tests proving the formula and
Joren's examples.

However:

- no normal MVP production/application path may select this fallback;
- it must not silently activate when HR or zone-time data is missing;
- partial HR data must use the observed-only rule above;
- distance-only swimming must remain unavailable rather than automatically
  using sRPE;
- activation requires a later explicit product/ruleset decision.

Prefer an explicit ruleset/config capability flag rather than dead or
unreachable duplicate logic.

10. 42-DAY BASELINE AND PROGRESSION

Retain the existing 42-day baseline fallback.

Do not remove it globally.

For normal missing-history behavior where the existing rules currently use
the 42-day baseline, preserve it unless the new onboarding Start-TSS provides
the required starting baseline.

Retain 10% as the current progression factor.

For fatigue/missed-training behavior that uses the lower realized private load,
the provisional rule is:

    next_target = lower_realized_private_load × 1.10

Use the new official private-load calculation as the realized-load source when
the new ruleset applies.

A sick week remains retained for audit/history but excluded from planning/load
baseline calculations and must not automatically change zones.

Do not remove existing injury restriction, zero-redistribution, weekly-review,
low-only filtering, or rest-only pending-plan precedence.

11. TAPER

For the current MVP ruleset, use a fixed 7-day taper.

The taper window is:

    race_date - 7 days
    through
    race_date - 1 day

Race day itself is not one of the seven pre-race taper days.

Do not dynamically choose 8, 9 or 10 days.

Do not lengthen, shorten or reposition the taper because of recovery-week
alignment.

Preserve the existing reviewed taper reduction/target behavior where it can be
applied to this fixed seven-day window without inventing new physiological
values.

If an existing whole-week reduction rule cannot be applied correctly to the
new exact-date window without inventing a new physiological reduction curve,
keep that part fail-closed and document the missing deeper rule rather than
inventing one.

Record as FUTURE WORK:
- adaptive 7-10 day taper selection;
- new taper reduction curves;
- discipline-specific taper adaptation;
- recovery/taper interaction refinements;
- more advanced multiple-race overlap behavior.

Do not implement those future refinements in this task.

12. AI / APPROVAL BOUNDARIES

Preserve the existing architecture:

- physiological decisions are deterministic Python;
- AI cannot recalculate zones;
- AI cannot directly mutate plans;
- calculated zone profiles remain pending;
- generated plan changes remain pending where required;
- athlete confirmation remains required;
- stale-safe/version-precondition behavior must remain intact;
- TSS/private load remains private.
