# Joren V6 all 77 workout structures

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

## Source validation result

All **77/77 source structures pass** using the unchanged C1 `read_document`,
`parse_events` and `normalize_row` functions, with a narrowly pinned V6 sheet/header
adapter. The intake verifies all three hashes before parsing any V6 XML. Invalid
hash/schema/row/identity/aggregate inputs fail closed; no partial active import exists.

| Sport | Exact supplied file | Bytes | Actual SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_v6.xlsx | 7731 | `f9efc53405ae80ea06b7c4f45c288d77e0572aabe0309ef17d29336562a5c46c` |
| BIKE | Fietstrainingen_Definitief_v6.xlsx | 7813 | `e291a6e40b193d279e1371032242972f4f940454b544832e04087aec6fec4b95` |
| SWIM | Zwemtrainingen_Definitief_v6.xlsx | 7551 | `acd05e0d02664a09320fc70a4519d518fb0103a34801823d04de1ac929c96348` |

| Sport | Previous rows | V6 rows | Added | Single / mixed |
| --- | --- | --- | --- | --- |
| RUN | 20 | 28 | 8 | 24 / 4 |
| BIKE | 21 | 27 | 6 | 19 / 8 |
| SWIM | 20 | 22 | 2 | 11 / 11 |
| Total | 61 | 77 | 16 | 54 / 23 |

Every row checks exact A:O coverage, source ID/order/sport, RPE and maximum
zone, complete token consumption, sequence/spans, positive measures, seconds versus
minutes versus meters, each zone subtotal and total. C1 raw numeric lexemes, cell
units/headers/XML/formats, source focus and interval text remain intact. Timed
half-minute blocks are exact 30-second events. Distance swims retain null active
duration. Stationary rests have seconds and no zone, distance or RPE.

## Six source corrections already present in V6

| ID / row | First block | Z2 / Z3 meters | Rest seconds | Source display P | Validation |
| --- | --- | --- | --- | --- | --- |
| TR-SWIM-015 / 19 | 300m Z2 | 600 / 0 | 300 | 39.9 | PASS; already corrected |
| TR-SWIM-016 / 20 | 300m Z2 | 600 / 0 | 450 | 54.8 | PASS; already corrected |
| TR-SWIM-017 / 21 | 300m Z2 | 600 / 0 | 600 | 69.6 | PASS; already corrected |
| TR-SWIM-018 / 22 | 300m Z2 | 600 / 0 | 150 | 39.9 | PASS; already corrected |
| TR-SWIM-019 / 23 | 300m Z2 | 600 / 0 | 225 | 54.8 | PASS; already corrected |
| TR-SWIM-020 / 24 | 300m Z2 | 600 / 0 | 300 | 69.6 | PASS; already corrected |

Each V6 ordered string equals the C2.1 approved derivative exactly. Only the
first 300m block differs from the erroneous IF² original. All subsequent blocks,
rest positions/durations, meters, RPE/focus and raw P are unchanged. Rests contribute
zero to candidate load and no active time. Aggregate and ordered IF² results agree.
No replacement overlay is applied to V6. All six are **STRUCTURES VALIDATED**,
**INACTIVE**, with swimming active time **UNVERIFIED**.

## Complete 77-row validation ledger

All rows below are structurally valid; P is source evidence, never operational P.
The JSON retains full original lexemes even when the display is rounded here.

| ID / row | Measure | Z1 / Z2 / Z3 / Z4 / Z5 | Events / rest sec | Source RPE | Raw P | Single/mixed |
| --- | --- | --- | --- | --- | --- | --- |
| TR-RUN-001 / 5 | 30 minutes | 30 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 17.4 | single |
| TR-RUN-002 / 6 | 40 minutes | 40 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 23.2 | single |
| TR-RUN-003 / 7 | 50 minutes | 50 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 29 | single |
| TR-RUN-004 / 8 | 30 minutes | 0 / 30 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 32.3 | single |
| TR-RUN-005 / 9 | 40 minutes | 0 / 40 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 43.1 | single |
| TR-RUN-006 / 10 | 50 minutes | 0 / 50 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 53.9 | single |
| TR-RUN-007 / 11 | 60 minutes | 0 / 60 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 64.7 | single |
| TR-RUN-008 / 12 | 70 minutes | 0 / 70 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 75.5 | single |
| TR-RUN-009 / 13 | 80 minutes | 0 / 80 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 86.2 | single |
| TR-RUN-010 / 14 | 90 minutes | 0 / 90 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 97 | single |
| TR-RUN-011 / 15 | 100 minutes | 0 / 100 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 107.8 | single |
| TR-RUN-012 / 16 | 110 minutes | 0 / 110 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 118.6 | single |
| TR-RUN-013 / 17 | 120 minutes | 0 / 120 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 129.4 | single |
| TR-RUN-014 / 18 | 130 minutes | 0 / 130 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 140.2 | single |
| TR-RUN-015 / 19 | 140 minutes | 0 / 140 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 150.9 | single |
| TR-RUN-016 / 20 | 150 minutes | 0 / 150 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 161.7 | single |
| TR-RUN-017 / 21 | 60 minutes | 0 / 30 / 0 / 30 / 0 | 7 / 0 | 7, 8 | 87.59999999999999 | mixed |
| TR-RUN-018 / 22 | 55 minutes | 0 / 35 / 0 / 20 / 0 | 9 / 0 | 7, 8 | 74.5 | mixed |
| TR-RUN-019 / 23 | 68 minutes | 0 / 45 / 0 / 0 / 23 | 11 / 0 | 9, 10 | 106.8 | mixed |
| TR-RUN-020 / 24 | 68 minutes | 0 / 36 / 0 / 0 / 32 | 9 / 0 | 9, 10 | 119.9 | mixed |
| TR-RUN-021 / 25 | 10 minutes | 10 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 5.8 | single |
| TR-RUN-022 / 26 | 15 minutes | 15 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 8.699999999999999 | single |
| TR-RUN-023 / 27 | 20 minutes | 20 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 11.6 | single |
| TR-RUN-024 / 28 | 25 minutes | 25 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 14.5 | single |
| TR-RUN-025 / 29 | 10 minutes | 0 / 10 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 10.8 | single |
| TR-RUN-026 / 30 | 15 minutes | 0 / 15 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 16.2 | single |
| TR-RUN-027 / 31 | 20 minutes | 0 / 20 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 21.6 | single |
| TR-RUN-028 / 32 | 25 minutes | 0 / 25 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 27 | single |
| TR-BIKE-001 / 5 | 60 minutes | 60 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 30.2 | single |
| TR-BIKE-002 / 6 | 90 minutes | 90 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 45.4 | single |
| TR-BIKE-003 / 7 | 120 minutes | 120 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 60.5 | single |
| TR-BIKE-004 / 8 | 90 minutes | 0 / 90 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 84.40000000000001 | single |
| TR-BIKE-005 / 9 | 120 minutes | 0 / 120 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 112.5 | single |
| TR-BIKE-006 / 10 | 150 minutes | 0 / 150 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 140.6 | single |
| TR-BIKE-007 / 11 | 180 minutes | 0 / 180 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 168.8 | single |
| TR-BIKE-008 / 12 | 210 minutes | 0 / 210 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 196.9 | single |
| TR-BIKE-009 / 13 | 240 minutes | 0 / 240 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 225 | single |
| TR-BIKE-010 / 14 | 300 minutes | 0 / 300 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 281.2 | single |
| TR-BIKE-011 / 15 | 330 minutes | 0 / 330 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 309.4 | single |
| TR-BIKE-012 / 16 | 360 minutes | 0 / 360 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 337.5 | single |
| TR-BIKE-013 / 17 | 420 minutes | 0 / 420 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 393.8 | single |
| TR-BIKE-014 / 18 | 180 minutes | 0 / 100 / 0 / 80 / 0 | 10 / 0 | 7, 8 | 221.8 | mixed |
| TR-BIKE-015 / 19 | 120 minutes | 0 / 80 / 0 / 40 / 0 | 10 / 0 | 7, 8 | 139 | mixed |
| TR-BIKE-016 / 20 | 180 minutes | 0 / 100 / 0 / 80 / 0 | 18 / 0 | 7, 8 | 221.8 | mixed |
| TR-BIKE-017 / 21 | 220 minutes | 0 / 100 / 0 / 120 / 0 | 10 / 0 | 7, 8 | 285.8 | mixed |
| TR-BIKE-018 / 22 | 150 minutes | 0 / 90 / 0 / 0 / 60 | 11 / 0 | 9, 10 | 216.6 | mixed |
| TR-BIKE-019 / 23 | 100 minutes | 0 / 68 / 0 / 0 / 32 | 10 / 0 | 9, 10 | 134.3 | mixed |
| TR-BIKE-020 / 24 | 93 minutes | 15 / 75 / 0 / 0 / 3 | 15 / 0 | 9, 10 | 84.5 | mixed |
| TR-BIKE-021 / 25 | 104 minutes | 15 / 85 / 0 / 0 / 4 | 19 / 0 | 9, 10 | 96.09999999999999 | mixed |
| TR-BIKE-022 / 26 | 30 minutes | 30 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 15.1 | single |
| TR-BIKE-023 / 27 | 40 minutes | 40 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 20.2 | single |
| TR-BIKE-024 / 28 | 50 minutes | 50 / 0 / 0 / 0 / 0 | 1 / 0 | 1, 2 | 25.2 | single |
| TR-BIKE-025 / 29 | 30 minutes | 0 / 30 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 28.1 | single |
| TR-BIKE-026 / 30 | 40 minutes | 0 / 40 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 37.5 | single |
| TR-BIKE-027 / 31 | 50 minutes | 0 / 50 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 46.9 | single |
| TR-SWIM-001 / 5 | 1000 meters | 0 / 1000 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 16.9 | single |
| TR-SWIM-002 / 6 | 1500 meters | 0 / 1500 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 25.3 | single |
| TR-SWIM-003 / 7 | 2000 meters | 0 / 2000 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 33.8 | single |
| TR-SWIM-004 / 8 | 2500 meters | 0 / 2500 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 42.2 | single |
| TR-SWIM-005 / 9 | 3000 meters | 0 / 3000 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 50.6 | single |
| TR-SWIM-006 / 10 | 3500 meters | 0 / 3500 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 59.1 | single |
| TR-SWIM-007 / 11 | 4000 meters | 0 / 4000 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 67.5 | single |
| TR-SWIM-008 / 12 | 4500 meters | 0 / 4500 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 75.90000000000001 | single |
| TR-SWIM-009 / 13 | 5000 meters | 0 / 5000 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 84.40000000000001 | single |
| TR-SWIM-010 / 14 | 1600 meters | 0 / 600 / 1000 / 0 / 0 | 12 / 150 | 5, 6 | 31.4 | mixed |
| TR-SWIM-011 / 15 | 2600 meters | 0 / 600 / 2000 / 0 / 0 | 22 / 300 | 5, 6 | 52.6 | mixed |
| TR-SWIM-012 / 16 | 2600 meters | 0 / 600 / 0 / 2000 / 0 | 12 / 300 | 7, 8 | 58.2 | mixed |
| TR-SWIM-013 / 17 | 2600 meters | 0 / 600 / 0 / 2000 / 0 | 10 / 240 | 7, 8 | 58.2 | mixed |
| TR-SWIM-014 / 18 | 3000 meters | 0 / 500 / 2500 / 0 / 0 | 19 / 240 | 5, 6 | 61.6 | mixed |
| TR-SWIM-015 / 19 | 1600 meters | 0 / 600 / 0 / 0 / 1000 | 22 / 300 | 9, 10 | 39.9 | mixed |
| TR-SWIM-016 / 20 | 2100 meters | 0 / 600 / 0 / 0 / 1500 | 32 / 450 | 9, 10 | 54.8 | mixed |
| TR-SWIM-017 / 21 | 2600 meters | 0 / 600 / 0 / 0 / 2000 | 42 / 600 | 9, 10 | 69.59999999999999 | mixed |
| TR-SWIM-018 / 22 | 1600 meters | 0 / 600 / 0 / 0 / 1000 | 22 / 150 | 9, 10 | 39.9 | mixed |
| TR-SWIM-019 / 23 | 2100 meters | 0 / 600 / 0 / 0 / 1500 | 32 / 225 | 9, 10 | 54.8 | mixed |
| TR-SWIM-020 / 24 | 2600 meters | 0 / 600 / 0 / 0 / 2000 | 42 / 300 | 9, 10 | 69.59999999999999 | mixed |
| TR-SWIM-021 / 25 | 500 meters | 0 / 500 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 8.4 | single |
| TR-SWIM-022 / 26 | 800 meters | 0 / 800 / 0 / 0 / 0 | 1 / 0 | 3, 4 | 13.5 | single |

## Operational and Realized V2 boundaries

All source release/selection metadata remains proposed; operational P and method
are null, operational accessors reject, activation is INACTIVE. Source structure
validation does not approve athlete suitability, planned-P authority, scientific
review, catalog replacement or release. There are 43 timed single-zone candidates
and 11 distance-only single-zone swims; all 23 mixed workouts remain outside the
whole-session Realized V2 matrix. **New operationally eligible occurrences: zero.**
No distance-based actual load or swimmer minutes are invented. Historical Realized
V2 method dispatch, occurrence snapshots, measured-data priority, completeness,
correction and stale/idempotent semantics remain unchanged.

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).
