# Simulator-dekkingsmatrix

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

| Regel | Rekenplaats | Status |
| --- | --- | --- |
| INIT-01 | 01_ATHLETE_INPUTS!F6:F8 | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INIT-02 | 01_ATHLETE_INPUTS!F9 | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INIT-03 | 01_ATHLETE_INPUTS | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INIT-04 | NOT IMPLEMENTED: complete proposal gate ontbreekt; numeriek target is geen geldig plan | NOT IMPLEMENTED |
| GOAL-01 | 02_GOAL | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAL-01 | 03_CALIBRATION!E7:E8 (CURRENT), F7:F8 (JOREN) | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAL-02 | 03_CALIBRATION!E6 (CURRENT), F6 (JOREN) | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAL-03 | NOT IMPLEMENTED: protocolsegment evaluator | NOT IMPLEMENTED |
| CAL-04 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| CAL-05 | NOT IMPLEMENTED: complete test gating | NOT IMPLEMENTED |
| CAL-06 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| CAL-07 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| CAL-08 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| CAL-09 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| ZONE-01 | 04_ZONES | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| ZONE-02 | 04_ZONES | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| ZONE-03 | NOT IMPLEMENTED: legacy model sheet | NOT IMPLEMENTED |
| ZONE-04 | 18_ACTUAL_LOAD!G6:G405; alleen CURRENT Phase13 HR-classificatie | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| ZONE-05 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| ZONE-06 | NOT IMPLEMENTED: historical fallback | NOT IMPLEMENTED |
| ZONE-07 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| LOAD-01 | 18_ACTUAL_LOAD | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| LOAD-02 | 18_ACTUAL_LOAD | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| LOAD-03 | 18_ACTUAL_LOAD | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| LOAD-04 | NOT IMPLEMENTED: reference only | NOT IMPLEMENTED |
| LOAD-05 | NOT IMPLEMENTED: historical record path | NOT IMPLEMENTED |
| ACT-01 | 16_RPE_AND_OBSERVATIONS | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| ACT-02 | NOT IMPLEMENTED: immutable activity event log | NOT IMPLEMENTED |
| CAT-01 | 08_TRAINING_CATALOG | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAT-02 | 08_TRAINING_CATALOG | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAT-03 | 10_ELIGIBLE_WORKOUTS | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| CAT-04 | NOT IMPLEMENTED: segment projection | NOT IMPLEMENTED |
| PLAN-01 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-02 | 09_WEEK_SETUP | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-03 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-04 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-05 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-06 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-07 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-08 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-09 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-10 | 19_NEXT_WEEK | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLAN-11 | NOT IMPLEMENTED: maintenance selector | NOT IMPLEMENTED |
| INT-01 | 17_PLANNED_LOAD | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INT-02 | NOT IMPLEMENTED: downstream intensity debt | NOT IMPLEMENTED |
| INT-03 | 17_PLANNED_LOAD | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INT-04 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| SEL-01 | NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie | NOT IMPLEMENTED |
| SEL-02 | NOT IMPLEMENTED: automatic search | NOT IMPLEMENTED |
| SEL-03 | NOT IMPLEMENTED: exact swipe composition | NOT IMPLEMENTED |
| SEL-04 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| SEL-05 | NOT IMPLEMENTED: immutable action history | NOT IMPLEMENTED |
| PLACE-01 | 12_PLACEMENT | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PLACE-02 | NOT IMPLEMENTED: automatic placement | NOT IMPLEMENTED |
| PLACE-03 | 12_PLACEMENT | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INJ-01 | 09_WEEK_SETUP | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| INJ-02 | NOT IMPLEMENTED: injury allocation | NOT IMPLEMENTED |
| INJ-03 | NOT IMPLEMENTED: injury allocation | NOT IMPLEMENTED |
| INJ-04 | NOT IMPLEMENTED | NOT IMPLEMENTED |
| INJ-05 | NOT IMPLEMENTED: full precedence | NOT IMPLEMENTED |
| STATE-01 | 14_PLAN_APPROVAL: illustrative only | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| STATE-02 | 14_PLAN_APPROVAL: illustrative only | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| STATE-03 | 05_HISTORY: explicit manual snapshots | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| WARN-01 | NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie | NOT IMPLEMENTED |
| VAL-01 | input validations; detailed contracts NOT IMPLEMENTED | PARTIAL; alleen expliciete parity assertions zijn bewijs |
| PREC-01 | NOT IMPLEMENTED: 07_RULES_AND_FORMULAS bevat alleen referentie of onvolledige proposalinformatie | NOT IMPLEMENTED |

## Beslispunten

fixtures/decision_inventory.json bevat ieder syntactisch gevonden if/if-expression/while/assert/comprehension-filter van de gekozen Python-modules. Alle records starten NOT VERIFIED. Niet gepromoveerd naar PASS op basis van algemene backendtests. SQL en mobiele beslispunten ontbreken nog.

## Volledigheidsgates

Automatische search, exacte swipe-completion, injury-waterfill, volledige approval/revision/idempotencyhistorie, historical-loadcompatibiliteit, protocolkwaliteit, intensiteitschuld en algemene IANA/DST-dekking zijn niet volledig geport. Zestien targetregels betekenen niet zestien volledig gesimuleerde trainingsweken.
