# MVP run catalog coverage investigation

2026-09-24. Read-only catalog and planning investigation; no production catalog,
physiology, schema, or athlete data changed. Private values below are engineering
evidence and must not enter athlete-facing contracts.

## Decision

The current evidence does not authorize promoting any imported source workout
to automatic planning. The [Phase 8 source review](phase-8-taper-catalog-review.md)
concludes that the 154-row export is structurally safe **as athlete-selected
runtime content**. The forward import marks all 154 rows
`athlete_selection_only = true`; its pgTAP test asserts that exact status.
Phase 0-7 decision 42 calls for a reviewed standard Week-1 selection but does
not identify that set. The source has no reviewed phase or taper field, and
its event labels are descriptive text rather than enforced goal eligibility.
Changing these rows to automatic base prescriptions would therefore select a
new training policy without approval.

The available reviewed automatic RUN prescriptions are one active base workout
and one build-only workout. The 40-minute aerobic run is version 1 of the same
logical template as the active 45-minute version; activating both as independent
workouts would undo catalog versioning. The historical run field-test versions
are explicit-scheduling protocols and are excluded from current ordinary
planning, with no authoritative planned load.

## Current RUN inventory

The source rows below are imported from
`Trainingen START23.v01.xlsx - Sheet1.csv` by the 2026-09-03 migration. All
50 are structurally validated, athlete-selectable, compatible with known
run zones, and projectable to reviewed textual RPE while calibration is pending.
None is approved for automatic selection. Every row has numeric zone segments,
textual RPE, a complete duration, and no explicit zone requirement. The import
tags every row `base, build`; its 20 low-bucket rows additionally get
`recovery`. These generic tags establish swipe eligibility; the source review
does not establish automatic phase or race-goal suitability.

| ID | Source type | Source event | Minutes | Bucket | Expected zone/RPE |
| --- | --- | --- | ---: | --- | --- |
| RUN-001 | Herstel | Fitheid | 30 | low | Z1 / RPE 2-3 |
| RUN-002 | Herstel | Fitheid | 45 | low | Z1 / RPE 2-3 |
| RUN-003 | Herstel | Fitheid | 30 | low | Z1 / RPE 2-3 |
| RUN-004 | Herstel | Fitheid | 30 | low | Z1 / RPE 2-3 |
| RUN-005 | Herstel | Fitheid | 30 | low | Z1 / RPE 2-3 |
| RUN-006 | Duur | Halve | 60 | low | Z2 / RPE 4 |
| RUN-007 | Duur | Halve | 75 | low | Z2 / RPE 4 |
| RUN-008 | Duur | Halve | 90 | low | Z2 / RPE 4 |
| RUN-009 | Duur | Volledige | 120 | low | Z2 / RPE 4 |
| RUN-010 | Duur | Volledige | 150 | low | Z2 / RPE 4 |
| RUN-011 | Wisselduur | Halve | 90 | low | Z2 / RPE 4 |
| RUN-012 | Wisselduur | Halve | 60 | low | Z2 / RPE 4 |
| RUN-013 | Wisselduur | Halve | 90 | low | Z2 / RPE 4 |
| RUN-014 | Wisselduur | Halve | 60 | low | Z2 / RPE 4 |
| RUN-015 | Wisselduur | Halve | 60 | low | Z2 / RPE 4 |
| RUN-016 | Progressie | Halve | 75 | low | Z3 / RPE 5-6 |
| RUN-017 | Progressie | Halve | 60 | low | Z3 / RPE 5-6 |
| RUN-018 | Progressie | Halve | 60 | low | Z3 / RPE 5-6 |
| RUN-019 | Progressie | Halve | 60 | low | Z3 / RPE 5-6 |
| RUN-020 | Progressie | Halve | 60 | low | Z3 / RPE 5-6 |
| RUN-021 | Fartlek | Sprint | 45 | high | Z4 / RPE 7-8 |
| RUN-022 | Fartlek | Sprint | 45 | high | Z4 / RPE 7-8 |
| RUN-023 | Fartlek | Sprint | 45 | high | Z4 / RPE 7-8 |
| RUN-024 | Fartlek | Sprint | 60 | high | Z4 / RPE 7-8 |
| RUN-025 | Fartlek | Sprint | 60 | high | Z4 / RPE 7-8 |
| RUN-026 | Drempel | Halve | 60 | high | Z4 / RPE 7-8 |
| RUN-027 | Drempel | Halve | 90 | high | Z4 / RPE 7-8 |
| RUN-028 | Drempel | Halve | 75 | high | Z4 / RPE 7-8 |
| RUN-029 | Drempel | Halve | 90 | high | Z4 / RPE 7-8 |
| RUN-030 | Drempel | Halve | 60 | high | Z4 / RPE 7-8 |
| RUN-031 | Over-Under | Halve | 75 | high | Z4 / RPE 7-8 |
| RUN-032 | Over-Under | Halve | 60 | high | Z4 / RPE 7-8 |
| RUN-033 | Over-Under | Halve | 75 | high | Z4 / RPE 7-8 |
| RUN-034 | Over-Under | Halve | 75 | high | Z4 / RPE 7-8 |
| RUN-035 | Over-Under | Halve | 75 | high | Z4 / RPE 7-8 |
| RUN-036 | VO2-Max | Sprint | 45 | high | Z5 / RPE 9-10 |
| RUN-037 | VO2-Max | Sprint | 45 | high | Z5 / RPE 9-10 |
| RUN-038 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-039 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-040 | VO2-Max | Sprint | 45 | high | Z5 / RPE 9-10 |
| RUN-041 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-042 | VO2-Max | Sprint | 45 | high | Z5 / RPE 9-10 |
| RUN-043 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-044 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-045 | VO2-Max | Sprint | 60 | high | Z5 / RPE 9-10 |
| RUN-046 | Duur+ | Volledige | 120 | high | Z4 / RPE 7-8 |
| RUN-047 | Duur+ | Volledige | 90 | high | Z4 / RPE 7-8 |
| RUN-048 | Duur+ | Volledige | 90 | high | Z4 / RPE 7-8 |
| RUN-049 | Duur+ | Volledige | 90 | high | Z4 / RPE 7-8 |
| RUN-050 | Duur+ | Volledige | 120 | high | Z4 / RPE 7-8 |

Other RUN definitions:

| Definition | Provenance/status | Phases | Minutes | Bucket | Eligibility |
| --- | --- | --- | ---: | --- | --- |
| Easy aerobic run v1 | Phase 5 reviewed, superseded by v2 | base, recovery, taper | 40 | low | historical; same template key |
| Easy aerobic run v2 | reviewed active automatic | base, recovery, taper | 45 | low | known HR and RPE projection |
| Tempo intervals v1 | Phase 5 reviewed active automatic | build | 45 | high | excluded from base by phase; known HR can use RPE projection |
| Run threshold field-test v1/v2 | historical, superseded current protocol | base, build | 60 | high | explicit scheduling only; inactive current protocol and no current planned load |

## Private first-week reproduction

Run-only Marathon Gent; no prior plan history; Monday 2026-08-03; normal base
phase; available Monday, Wednesday, Saturday. The eligible base swipe deck is
51 RUN rows for known zones and calibration-pending RPE guidance: 50 source
choices plus one automatic aerobic run. Its automatic capacity is 36.30.

| Previous-month run hours/week | Canonical minutes | Phase 13 private target | Automatic selected count | Private gap or capacity gap | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 45.0 | 1 | 8.70 | closest-catalog pending plan |
| 1 | 60 | 64.7 | 1 | 28.40 | closest-catalog pending plan |
| 3 | 180 | 194.1 | none | 157.80 | explicit `catalog_capacity_unsatisfied` |
| 6 | 360 | 388.1 | none | 351.80 | explicit `catalog_capacity_unsatisfied` |
| 15 | 900 | 970.3 | none | 934.00 | explicit `catalog_capacity_unsatisfied` |

Freshly approved Phase 13 run calibration and athlete-entered known run zones
have the same HR capability. Calibration pending projects reviewed zone segments
to textual RPE; the eligible deck and automatic capacity remain the same. The
LTHR-below-140 warning and its separate approval lifecycle are unaffected.

The same structural shortage appears outside run-only planning. With the
current small automatic catalog, first-week bike-only 3 h/week targets 168.8
against automatic capacity 84.00. A duathlon with 3 h bike and 2 h run targets
298.1 against capacity 120.30. A triathlon with 1 h swim, 3 h bike, and 2 h run
targets 348.8 against capacity 143.70. All fail explicitly; none silently
substitutes a smaller one-workout plan.

## Review needed to make ordinary volumes plannable

An accountable product/physiology reviewer must identify specific immutable
source workout IDs, or another existing reviewed prescription set, that may be
used automatically in a base week; confirm race-goal applicability, phase and
intensity scope, and whether repeated instances of one template are permitted.
The reviewed choice must then be versioned and implemented with forward-only
catalog changes, Python/SQL parity, target/count/composition and swipe
feasibility tests, and database/runtime verification. No such choice is made
by this investigation.
