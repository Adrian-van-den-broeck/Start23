# Joren V6 IF-squared and swimming precision

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

## Reproduction and authority are separate

All 28 RUN and 27 BIKE source displays reproduce using existing IF² candidate
arithmetic and the source multipliers. All 22 SWIM displays reproduce using
two-decimal **reference minutes/100m**, reconstructed Z3 IF .88 and one-decimal
HALF_EVEN display. This numerical fit does not prove the original source formula,
original rounding convention or approval of an operational planned-P method.

| Input / rule | Value | Actual authority |
| --- | --- | --- |
| IF² methodology | squared zone IF | Joren confirmed; V6 A2 notes also state IF^2 |
| Populated IF anchors | Z1 .55; Z2 .75; Z4 .98; Z5 1.15 | Confirmed in C2; preserved |
| Z3 IF | .88 | RECONSTRUCTED; not formally approved |
| SWIM reference minutes/100m | 2.17 / 2.00 / 1.83 / 1.67 / 1.50 | RECONSTRUCTED precision convention; not formally approved |
| Source sport multipliers | RUN 1.15; BIKE 1; SWIM .90 | Original numeric G cells retained; candidate uses exactly once |
| Candidate normalization | sum(minutes * IF²) * 100/60 * factor | Reproduced behavior; original full formula not supplied |
| Display | 0.1 HALF_EVEN | Diagnostic reconstruction; distinct from raw storage and operational P |
| Operational P | null / unavailable | No method/precision/storage/V2 acceptance supplied |

Versioned candidate arithmetic uses exact rational numerator/denominator plus
a 50-significant-digit Decimal HALF_EVEN value, without intermediate rounding.
`joren-v6-if2-rounded-reference-minutes-candidate-1` means the reference inputs
are already 2.17/2.00/1.83/1.67/1.50; this is not rounding a calculated athlete time.
The existing seconds-parameter engine receives 130.2/120/109.8/100.2/90 to encode
those exact minute inputs. These are calculation parameters only, never a planned
or performed duration. The exact-seconds experiment receives 130/120/110/100/90.

Timed quantities come independently from ordered segment seconds. Swimming uses
the reconciled meters by zone. Wall rest is zero-load. The candidate checks the
same aggregates and order, including all six corrected swim rows. Strict confirmed
IF verification rejects SWIM-010/011/014 with `missing_if_anchor`; no Z3 fallback
is supplied. All 55 timed rows reproduce without any populated Z3 quantity.

No workbook contains formula cells, caches, an IF table or reference-pace table.
The A2 statement establishes IF² direction but cannot establish missing coefficients,
normalization, source intermediate precision or the general rounding/storage rule.

## Precision-sensitive swims

| ID | Using exact seconds / 60 | Using two-decimal minutes | Source display |
| --- | --- | --- | --- |
| TR-SWIM-011 | 52.7 | 52.6 | 52.6 |
| TR-SWIM-012 | 58.1 | 58.2 | 58.2 |
| TR-SWIM-013 | 58.1 | 58.2 | 58.2 |
| TR-SWIM-014 | 61.7 | 61.6 | 61.6 |

Exactly these four displays differ. Exact seconds reproduce 18/22 SWIM
displays; rounded reference-minute inputs reproduce 22/22. No silent substitution
of exact seconds is permitted. Source binary-residue lexemes (for example
`69.59999999999999`) are retained rather than rewritten as exact candidate P.
BIKE-001 candidate 30.25 displays 30.2, RUN-009 86.25 displays 86.2, and
BIKE-004 84.375 displays 84.4; raw source and mathematical candidates stay separate.

## Complete mathematical ledger

Candidate values are exact rational evidence plus the explicit Decimal review
representation, not approved operational values. The manifest additionally retains
every source-minus-candidate difference and all three parameter experiments.

| ID | Raw source P | Candidate rational P | Candidate Decimal P | Candidate/source display |
| --- | --- | --- | --- | --- |
| TR-RUN-001 | 17.4 | 2783/160 | 17.39375 | 17.4 / 17.4 |
| TR-RUN-002 | 23.2 | 2783/120 | 23.191666666666666666666666666666666666666666666667 | 23.2 / 23.2 |
| TR-RUN-003 | 29 | 2783/96 | 28.989583333333333333333333333333333333333333333333 | 29.0 / 29.0 |
| TR-RUN-004 | 32.3 | 1035/32 | 32.34375 | 32.3 / 32.3 |
| TR-RUN-005 | 43.1 | 345/8 | 43.125 | 43.1 / 43.1 |
| TR-RUN-006 | 53.9 | 1725/32 | 53.90625 | 53.9 / 53.9 |
| TR-RUN-007 | 64.7 | 1035/16 | 64.6875 | 64.7 / 64.7 |
| TR-RUN-008 | 75.5 | 2415/32 | 75.46875 | 75.5 / 75.5 |
| TR-RUN-009 | 86.2 | 345/4 | 86.25 | 86.2 / 86.2 |
| TR-RUN-010 | 97 | 3105/32 | 97.03125 | 97.0 / 97.0 |
| TR-RUN-011 | 107.8 | 1725/16 | 107.8125 | 107.8 / 107.8 |
| TR-RUN-012 | 118.6 | 3795/32 | 118.59375 | 118.6 / 118.6 |
| TR-RUN-013 | 129.4 | 1035/8 | 129.375 | 129.4 / 129.4 |
| TR-RUN-014 | 140.2 | 4485/32 | 140.15625 | 140.2 / 140.2 |
| TR-RUN-015 | 150.9 | 2415/16 | 150.9375 | 150.9 / 150.9 |
| TR-RUN-016 | 161.7 | 5175/32 | 161.71875 | 161.7 / 161.7 |
| TR-RUN-017 | 87.59999999999999 | 350267/4000 | 87.56675 | 87.6 / 87.6 |
| TR-RUN-018 | 74.5 | 1789193/24000 | 74.549708333333333333333333333333333333333333333333 | 74.5 / 74.5 |
| TR-RUN-019 | 106.8 | 128179/1200 | 106.81583333333333333333333333333333333333333333333 | 106.8 / 106.8 |
| TR-RUN-020 | 119.9 | 143911/1200 | 119.92583333333333333333333333333333333333333333333 | 119.9 / 119.9 |
| TR-RUN-021 | 5.8 | 2783/480 | 5.7979166666666666666666666666666666666666666666667 | 5.8 / 5.8 |
| TR-RUN-022 | 8.699999999999999 | 2783/320 | 8.696875 | 8.7 / 8.7 |
| TR-RUN-023 | 11.6 | 2783/240 | 11.595833333333333333333333333333333333333333333333 | 11.6 / 11.6 |
| TR-RUN-024 | 14.5 | 2783/192 | 14.494791666666666666666666666666666666666666666667 | 14.5 / 14.5 |
| TR-RUN-025 | 10.8 | 345/32 | 10.78125 | 10.8 / 10.8 |
| TR-RUN-026 | 16.2 | 1035/64 | 16.171875 | 16.2 / 16.2 |
| TR-RUN-027 | 21.6 | 345/16 | 21.5625 | 21.6 / 21.6 |
| TR-RUN-028 | 27 | 1725/64 | 26.953125 | 27.0 / 27.0 |
| TR-BIKE-001 | 30.2 | 121/4 | 30.25 | 30.2 / 30.2 |
| TR-BIKE-002 | 45.4 | 363/8 | 45.375 | 45.4 / 45.4 |
| TR-BIKE-003 | 60.5 | 121/2 | 60.5 | 60.5 / 60.5 |
| TR-BIKE-004 | 84.40000000000001 | 675/8 | 84.375 | 84.4 / 84.4 |
| TR-BIKE-005 | 112.5 | 225/2 | 112.5 | 112.5 / 112.5 |
| TR-BIKE-006 | 140.6 | 1125/8 | 140.625 | 140.6 / 140.6 |
| TR-BIKE-007 | 168.8 | 675/4 | 168.75 | 168.8 / 168.8 |
| TR-BIKE-008 | 196.9 | 1575/8 | 196.875 | 196.9 / 196.9 |
| TR-BIKE-009 | 225 | 225/1 | 225 | 225.0 / 225.0 |
| TR-BIKE-010 | 281.2 | 1125/4 | 281.25 | 281.2 / 281.2 |
| TR-BIKE-011 | 309.4 | 2475/8 | 309.375 | 309.4 / 309.4 |
| TR-BIKE-012 | 337.5 | 675/2 | 337.5 | 337.5 / 337.5 |
| TR-BIKE-013 | 393.8 | 1575/4 | 393.75 | 393.8 / 393.8 |
| TR-BIKE-014 | 221.8 | 66541/300 | 221.80333333333333333333333333333333333333333333333 | 221.8 / 221.8 |
| TR-BIKE-015 | 139 | 10427/75 | 139.02666666666666666666666666666666666666666666667 | 139.0 / 139.0 |
| TR-BIKE-016 | 221.8 | 66541/300 | 221.80333333333333333333333333333333333333333333333 | 221.8 / 221.8 |
| TR-BIKE-017 | 285.8 | 28583/100 | 285.83 | 285.8 / 285.8 |
| TR-BIKE-018 | 216.6 | 1733/8 | 216.625 | 216.6 / 216.6 |
| TR-BIKE-019 | 134.3 | 8057/60 | 134.28333333333333333333333333333333333333333333333 | 134.3 / 134.3 |
| TR-BIKE-020 | 84.5 | 6759/80 | 84.4875 | 84.5 / 84.5 |
| TR-BIKE-021 | 96.09999999999999 | 1441/15 | 96.066666666666666666666666666666666666666666666667 | 96.1 / 96.1 |
| TR-BIKE-022 | 15.1 | 121/8 | 15.125 | 15.1 / 15.1 |
| TR-BIKE-023 | 20.2 | 121/6 | 20.166666666666666666666666666666666666666666666667 | 20.2 / 20.2 |
| TR-BIKE-024 | 25.2 | 605/24 | 25.208333333333333333333333333333333333333333333333 | 25.2 / 25.2 |
| TR-BIKE-025 | 28.1 | 225/8 | 28.125 | 28.1 / 28.1 |
| TR-BIKE-026 | 37.5 | 75/2 | 37.5 | 37.5 / 37.5 |
| TR-BIKE-027 | 46.9 | 375/8 | 46.875 | 46.9 / 46.9 |
| TR-SWIM-001 | 16.9 | 135/8 | 16.875 | 16.9 / 16.9 |
| TR-SWIM-002 | 25.3 | 405/16 | 25.3125 | 25.3 / 25.3 |
| TR-SWIM-003 | 33.8 | 135/4 | 33.75 | 33.8 / 33.8 |
| TR-SWIM-004 | 42.2 | 675/16 | 42.1875 | 42.2 / 42.2 |
| TR-SWIM-005 | 50.6 | 405/8 | 50.625 | 50.6 / 50.6 |
| TR-SWIM-006 | 59.1 | 945/16 | 59.0625 | 59.1 / 59.1 |
| TR-SWIM-007 | 67.5 | 135/2 | 67.5 | 67.5 / 67.5 |
| TR-SWIM-008 | 75.90000000000001 | 1215/16 | 75.9375 | 75.9 / 75.9 |
| TR-SWIM-009 | 84.40000000000001 | 675/8 | 84.375 | 84.4 / 84.4 |
| TR-SWIM-010 | 31.4 | 784557/25000 | 31.38228 | 31.4 / 31.4 |
| TR-SWIM-011 | 52.6 | 1315989/25000 | 52.63956 | 52.6 / 52.6 |
| TR-SWIM-012 | 58.2 | 728013/12500 | 58.24104 | 58.2 / 58.2 |
| TR-SWIM-013 | 58.2 | 728013/12500 | 58.24104 | 58.2 / 58.2 |
| TR-SWIM-014 | 61.6 | 615807/10000 | 61.5807 | 61.6 / 61.6 |
| TR-SWIM-015 | 39.9 | 6381/160 | 39.88125 | 39.9 / 39.9 |
| TR-SWIM-016 | 54.8 | 17523/320 | 54.759375 | 54.8 / 54.8 |
| TR-SWIM-017 | 69.59999999999999 | 5571/80 | 69.6375 | 69.6 / 69.6 |
| TR-SWIM-018 | 39.9 | 6381/160 | 39.88125 | 39.9 / 39.9 |
| TR-SWIM-019 | 54.8 | 17523/320 | 54.759375 | 54.8 / 54.8 |
| TR-SWIM-020 | 69.59999999999999 | 5571/80 | 69.6375 | 69.6 / 69.6 |
| TR-SWIM-021 | 8.4 | 135/16 | 8.4375 | 8.4 / 8.4 |
| TR-SWIM-022 | 13.5 | 27/2 | 13.5 | 13.5 / 13.5 |

## Historical dispatch and operational guard

The old fixed swim PDF matrix, exact-seconds experiments, C2 rounded-reference
experiment, original source revisions and C2.1 overlay remain available under
their original versions. Existing `planned_source` methods remain experimental;
`require_operational_source` still rejects them. V6 adds explicit precision
provenance to its private evidence without changing any historical coefficients,
occurrence P, current zone-minute method or Realized V2 compatibility table.

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).
