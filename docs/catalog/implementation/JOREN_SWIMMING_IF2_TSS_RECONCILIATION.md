# Swimming IF² calculation reconciliation

Date: 2026-11-04, Europe/Amsterdam. Private developer review evidence; no activation.

All 20 new source values are preserved below. Source A2 states exactly: "Z1 t/m Z5 zijn in METERS. TSS berekend door meters om te zetten naar minuten * IF^2 * 0.90." This confirms the revised IF² direction but contains neither reference pace inputs, IF table, normalization nor rounding stages. No formula cells or hidden calculation sheet supply those details.

The experimental convention tested is `sum(meters[z]/100 * reference_seconds[z]/60 * IF[z]^2) * 100/60 * .90`, applying .90 once and adding zero for stationary rests. The 100/60 TSS normalization is independently required to reproduce the Z2 values under the confirmed IF=.75; literal minutes * IF^2 * .90 gives 10.125 rather than 16.875 for 1000m. Confirm this normalization explicitly rather than treating the abbreviated note as a full formula. These reference calculations never become planned or actual athlete minutes.

| Zone | Confirmed populated IF | Historical PDF exact reference seconds/100m | RECONSTRUCTED minutes candidate |
| --- | --- | --- | --- |
| Z1 | .55 | 130 | 2.17 |
| Z2 | .75 | 120 | 2.00 |
| Z3 | MISSING | 110 | 1.83 |
| Z4 | .98 | 100 | 1.67 |
| Z5 | 1.15 | 90 | 1.50 |

Column E below uses exact historical PDF seconds with **RECONSTRUCTED Z3 IF=.88** only for diagnostic comparison. Column R instead rounds reference minutes to two decimals first (equivalent seconds 130.2/120/109.8/100.2/90), again using .88 only as a reconstructed candidate. Neither assumption is an approved new method. Rounded-pace R reproduces 20/20 aggregate source displays; E reproduces 16/20. E fails TR-SWIM-011/012/013/014. Reproduction does not uniquely identify .88 or approve intermediate rounding. Source display acceptance intervals leave a range of possible Z3 anchors. Joren must supply original constants/calculation evidence and decide exact pace versus rounded minutes.

The pure calculator keeps the exact rational numerator/denominator and a local 50-significant-digit Decimal HALF_EVEN review result without intermediate quantization. These inputs happen to yield terminating exact decimals. One-decimal HALF_EVEN is a diagnostic rendering policy; none of these swim ties distinguishes the source author's rounding mode. Stored binary-export residues remain untouched. Difference means **raw stored source - R**, not an arithmetic correction. Every row has operational P unavailable and approval pending.

| ID / M cell | Source stored P (exact OOXML) | Source display | Exact E | Exact R | Difference stored-R | R display | Structure / approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR-SWIM-001 / M5 | 16.9 | 16.9 | 16.875 | 16.875 | 0.025 | 16.9 | method evidence pending |
| TR-SWIM-002 / M6 | 25.3 | 25.3 | 25.3125 | 25.3125 | -0.0125 | 25.3 | method evidence pending |
| TR-SWIM-003 / M7 | 33.8 | 33.8 | 33.75 | 33.75 | 0.05 | 33.8 | method evidence pending |
| TR-SWIM-004 / M8 | 42.2 | 42.2 | 42.1875 | 42.1875 | 0.0125 | 42.2 | method evidence pending |
| TR-SWIM-005 / M9 | 50.6 | 50.6 | 50.625 | 50.625 | -0.025 | 50.6 | method evidence pending |
| TR-SWIM-006 / M10 | 59.1 | 59.1 | 59.0625 | 59.0625 | 0.0375 | 59.1 | method evidence pending |
| TR-SWIM-007 / M11 | 67.5 | 67.5 | 67.5 | 67.5 | 0.0 | 67.5 | method evidence pending |
| TR-SWIM-008 / M12 | 75.90000000000001 | 75.9 | 75.9375 | 75.9375 | -0.03749999999999 | 75.9 | method evidence pending |
| TR-SWIM-009 / M13 | 84.40000000000001 | 84.4 | 84.375 | 84.375 | 0.02500000000001 | 84.4 | method evidence pending |
| TR-SWIM-010 / M14 | 31.4 | 31.4 | 31.421 | 31.38228 | 0.01772 | 31.4 | Z3 missing; pending |
| TR-SWIM-011 / M15 | 52.6 | 52.6 | 52.717 | 52.63956 | -0.03956 | 52.6 | Z3 missing; pending |
| TR-SWIM-012 / M16 | 58.2 | 58.2 | 58.145 | 58.24104 | -0.04104 | 58.2 | method evidence pending |
| TR-SWIM-013 / M17 | 58.2 | 58.2 | 58.145 | 58.24104 | -0.04104 | 58.2 | method evidence pending |
| TR-SWIM-014 / M18 | 61.6 | 61.6 | 61.6775 | 61.5807 | 0.0193 | 61.6 | Z3 missing; pending |
| TR-SWIM-015 / M19 | 39.9 | 39.9 | 39.88125 | 39.88125 | 0.01875 | 39.9 | SOURCE-CONFLICTED; withheld |
| TR-SWIM-016 / M20 | 54.8 | 54.8 | 54.759375 | 54.759375 | 0.040625 | 54.8 | SOURCE-CONFLICTED; withheld |
| TR-SWIM-017 / M21 | 69.59999999999999 | 69.6 | 69.6375 | 69.6375 | -0.03750000000001 | 69.6 | SOURCE-CONFLICTED; withheld |
| TR-SWIM-018 / M22 | 39.9 | 39.9 | 39.88125 | 39.88125 | 0.01875 | 39.9 | SOURCE-CONFLICTED; withheld |
| TR-SWIM-019 / M23 | 54.8 | 54.8 | 54.759375 | 54.759375 | 0.040625 | 54.8 | SOURCE-CONFLICTED; withheld |
| TR-SWIM-020 / M24 | 69.59999999999999 | 69.6 | 69.6375 | 69.6375 | -0.03750000000001 | 69.6 | SOURCE-CONFLICTED; withheld |

Strict experimental verification rejects all six conflicted rows before arithmetic. Of the 14 consistent rows, three (010/011/014) reject the missing Z3 IF; eleven can be calculated with the confirmed populated anchors and explicit historical reference pace parameters, still without operational approval. Zero Z1 source meters means no new row verifies the Z1 reference-pace rounding stage.

For the six conflicts, the two untouched source representations give different diagnostic loads:

| ID | Aggregate R | Ordered R | Ordered R display | Difference ordered-aggregate |
| --- | --- | --- | --- | --- |
| TR-SWIM-015 | 39.88125 | 41.195934 | 41.2 | 1.314684 |
| TR-SWIM-016 | 54.759375 | 56.074059 | 56.1 | 1.314684 |
| TR-SWIM-017 | 69.6375 | 70.952184 | 71.0 | 1.314684 |
| TR-SWIM-018 | 39.88125 | 41.195934 | 41.2 | 1.314684 |
| TR-SWIM-019 | 54.759375 | 56.074059 | 56.1 | 1.314684 |
| TR-SWIM-020 | 69.6375 | 70.952184 | 71.0 | 1.314684 |

Matching M with aggregates does not authorize those aggregates over execution. Both full originals are retained; no load/zone is overwritten. Stationary rests remain positive seconds with no zone, RPE, meters or load; TR-SWIM-010 has 150s rest, adding exactly zero under either IF² experiment. Active Z1 swimming is distinct.

RUN/BIKE support is separate `joren-timed-if2-experimental-1`: `sum(seconds[z]*IF[z]^2)*factor/36`, factors RUN1.15/BIKE1.00 from their source cells. All 41 source displays reproduce with the confirmed populated IF anchors; Z3 remains missing and fails if populated. BIKE020 has six 30s Z5 blocks (3min), exact84.4875; BIKE021 has eight (4min), exact1441/15. BIKE001 exact30.25 renders30.2 under HALF_EVEN, distinguishing a candidate display policy from HALF_UP30.3. Raw source residues, exact context results, rational evidence and original focus are independent in `timed_records`. Rounding/storage authority and V2 compatibility remain pending, so these methods are disabled too.

Historical `joren-swim-fixed-pdf-historical-1` dispatch preserves .98/1.44/1.98/2.40/2.70 per100m with explicit unity outer factor; it rejects multiplying .90 again. Historical TR-SWIM-010 remains28.44 exact /28.4 stored. New IF² is separately versioned and never reinterprets old plans or activities. Unknown method/source versions reject.

Reproduce privately from backend: `python -B -m app.jobs.joren_c2_dry_run --dry-run --private-output NEW_PATH`. Identical retries are read-only; conflicting existing outputs reject. Default stdout contains only status/counts/digest, with no private loads. Canonical evidence SHA-256: `4f9be3a86dbd5a41201116b4e203088de75bc9a63ef770537dbcc47c78e4feae`.
