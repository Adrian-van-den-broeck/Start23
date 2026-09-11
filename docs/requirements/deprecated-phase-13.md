# Deprecated Phase 13

HISTORICAL ONLY. This is not an active source of requirements.
Deprecated on 2026-09-10 by the explicit Phase 13 product decisions and
`phase-13-joren-ruleset-1` (implementation and verification tracked separately).

Sources: [load and textual RPE](<Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf>),
[onboarding](Triathlon_Onboarding_StartTSS.pdf),
[calibration](Triathlon_Zone_Calibratie_Voorbeelden.pdf).

## Replacement decisions

- Two-month distance/frequency baseline -> previous-month average weekly hours,
  canonical minutes, exact Decimal coefficients, final half-up one-decimal rounding.
- Unselected beginner minimum -> total 45.0, a Start23 midpoint product decision.
- Awaiting RPE scales/anchors -> supplied discipline-specific ten-point descriptions.
- Week-2 withholding/submaximal no-threshold -> single-session HR/LTHR run/bike,
  pace/CSS swim; a below-140 LTHR warning does not reject a pending proposal.
- RPE times duration -> zone minutes times discipline coefficients; observed-only
  partial coverage, unavailable distance-only swim load, inactive sRPE fallback.
- Unlocked progression -> retain 10%, lower realized load for fatigue/missed
  training, retain 42-day missing-history fallback, exclude sick weeks from planning.
- Adaptive 7-10 days/whole-week timing -> exact D-7 through D-1, with unresolved
  partial-week reduction curves fail-closed and deferred.
- All pending approvals, stale checks, privacy and external review gates remain.

## Historical persisted interpretation

Do not rewrite applied migrations, catalog versions, activity snapshots, or
prior decisions. `phase-3-ruleset-1`, `phase-3-ruleset-2`, `phase-3-ruleset-3`,
`phase-10-ruleset-1`, `start23-calibration-ruleset-v1`,
`start23-calibration-ruleset-v2`, and `start23-zone-model-1.0` retain their original
meaning. `actual_rpe_times_duration_hours` and prior expected-RPE duration/catalog
load snapshots must never be relabelled as zone-time measurements. Prior Phase
4 history and Phase 14 two-month history do not establish a previous-month
baseline without fresh athlete input. Production physiological review, database
verification and real-device gates are not closed by these new product decisions.

## Previous roadmap section (verbatim)

## Phase 13: physiological ruleset and load-model alignment

### Status

Not started. Implementation is gated on Joren's reviewed sport-science
deliverables from the 5 November minutes. The recorded deadline is Saturday at
09:00; the calendar date and the eventual accountable-review record still need
to be attached to the ruleset.

### Scope

- Define ten concrete textual RPE/feeling descriptions for swim, bike, and run;
  triathlon and duathlon use their component discipline's scale. The UI may
  retain canonical values 1-10 internally, but athletes select descriptions
  such as conversational pace, acidification, and breathless/exhausted rather
  than unexplained numbers.
- Define the deterministic single-session calibration formula that derives five
  heart-rate zones from the prescribed calibration workout, its discipline,
  the selected textual RPE, and average heart rate. Specify anchor ownership,
  bpm offsets, equality boundaries, rounding, valid inputs, missing-data
  behavior, and outlier/data-quality rules.
- Define versioned private load multipliers per heart-rate zone so planned and
  realized load is calculated from time in zone. Specify treatment of missing
  or partial zone-time data and distance-only swimming without inventing load.
- Define the two-month onboarding baseline formula per discipline from average
  weekly meters/kilometres and session frequency, using the approved Zone 2
  assumption. Specify combination across disciplines, canonical units,
  rounding, minimum/maximum guards, and insufficient-history behavior.
- Replace the old fatigue/restart policy: a week marked sick is retained for
  audit/history but excluded from all planning and load calculations and never
  changes zones; fatigue or missed training lowers realized private load, and
  the next week progresses from that lower realized value. Lock the exact
  progression factor—the `+10%` in the minutes is an example, not yet a
  complete boundary specification.
- Replace the old week-based taper interpretation with a deterministic 7-10 day
  taper immediately preceding race day. Define how the exact duration is
  selected, the private-load reduction curve/factors, partial-week behavior,
  race priority overlap, and athlete-local date boundaries.
- Keep cycling zone and load decisions heart-rate based when no power meter is
  available. Do not require FTP/power-meter data for the MVP cycling route.
- Enforce the AI boundary in services and tests: no AI recalculation of zones,
  no direct plan mutation, and only deterministic pending volume/intensity
  proposals within the athlete's active zones.
- Version the new ruleset, record Joren's evidence and the accountable reviewer,
  update business-rule traceability, and add deterministic example, boundary,
  invalid-input, precedence, and privacy tests.

### Exit criteria

- Joren's four deliverables—textual RPE scales, calibration formula, zone load
  multipliers, and two-month baseline formula—are complete, versioned, and
  reviewed.
- Sick, fatigued, missed-training, and normal-week fixtures prove the new
  baseline/progression behavior without changing zones automatically.
- Taper fixtures cover 7- and 10-day boundaries, partial local weeks, and the
  race-day edge; taper-catalog eligibility is reviewed separately and remains
  fail-closed until complete swim/bike/run coverage passes.
- All calculated zone profiles and plan changes are pending and require athlete
  confirmation; planned and realized TSS remain absent from public APIs, the
  mobile UI, logs, and LLM prompts.
