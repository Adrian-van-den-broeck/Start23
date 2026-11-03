# Joren swimming TSS reconciliation

Review date: 2026-11-03 (Europe/Amsterdam). Review and preparation only.
Accepted engine: `feat/joren-realized-tss-v2` at `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch/worktree: `review/joren-new-workout-catalog`,
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Swimming originals are in the accepted engine worktree's `docs/trainings`, not the older root checkout:

| Original | Bytes | SHA-256 |
| --- | --- | --- |
| `Zwemtrainingen_Definitief_Optie1.xlsx` | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` |
| `Specificatie Zwem TSS.pdf` | 149021 | `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a` |

Full original paths:
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Zwemtrainingen_Definitief_Optie1.xlsx`
and `F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Specificatie Zwem TSS.pdf`.
Private load numbers below are developer review evidence and must remain outside athlete-facing contracts.

## Published method A: verified source facts

Both pages of `Specificatie Zwem TSS.pdf` were read and rendered. Page 1 section 2
explicitly presents a fixed per-100 m software matrix; section 4 supplies the
sum-of-distance-times-constant formula. Page 1 section 3 defines wall rest as
stationary, distinct from active Z1 recovery, and assigns it exactly zero TSS.
Page 2 gives the exact 28.44 worked example.

| Zone | Published exact source constant per 100 m | PDF reference pace | Existing SWIM coefficient per minute |
| --- | --- | --- | --- |
| Z1 | 0.98 | 130 s / 100 m | 0.45 |
| Z2 | 1.44 | 120 s / 100 m | 0.72 |
| Z3 | 1.98 | 110 s / 100 m | 1.08 |
| Z4 | 2.40 | 100 s / 100 m | 1.44 |
| Z5 | 2.70 | 90 s / 100 m | 1.80 |
| Stationary wall rest | 0 | Explicit rest seconds, no swimming distance or zone | No separate rest event in current zone-minute API |

Method A is `sum(distance_in_zone / 100 * published_constant)`; stationary rests
add zero. The rounded constants are the explicit computation inputs in this PDF,
not instructions to recalculate them from rounded pace displays. No additional
sport multiplier appears in the formula. These facts resolve which method to use
for this workbook's source reconciliation; they do not activate a new Wombo method.

## Methods A, B and C are distinct

**A — Published fixed distance constants:** use the table above as exact decimal
inputs. This is the delivered document's software calculation and the method
verified across all 20 rows.

**B — Unrounded reference pace × existing coefficient:** compute
`distance/100 × reference_seconds/60 × existing_swim_TSS_per_minute` using exact
seconds, not rounded `2.17`, `1.83` or `1.67` minute display values. It is an
independent mathematical reconstruction of the representative reference, not
observed time and not an approved new duration source.

| Zone | A per 100 m | B per 100 m, exact | A − B |
| --- | --- | --- | --- |
| Z1 | 0.98 | 0.975 | +0.005 |
| Z2 | 1.44 | 1.44 | 0 |
| Z3 | 1.98 | 1.98 | 0 |
| Z4 | 2.40 | 2.40 | 0 |
| Z5 | 2.70 | 2.70 | 0 |

Thus A and B are not identical methods. All 20 delivered rows happen to have zero
Z1 distance, so their exact A and B totals agree. A 100 m Z1 arithmetic check
would distinguish 0.98 from 0.975; this is a coefficient check, not an invented
workout. Multiplying rounded minute displays gives 0.9765/1.44/1.9764/2.4048/2.70,
which is a third rounding artifact and is not the published formula.

**C — Athlete-specific CSS-adjusted load:** no supported converter exists in the
accepted engine and no complete scaling function is specified in the PDF. It
mentions the athlete's CSS of 1:55/100 m as the reference underlying the displayed
paces. It does not give per-zone pace multipliers for another CSS, an athlete-
parameter input contract, interpolation, bounds, rest handling for a duration
ratio, versioning or recalibration/correction policy. No C values can be calculated
authoritatively from this delivery. C is unavailable, not assumed equal to A/B.

## All 20 source results

Source column is the **raw stored M cell**, preserved unchanged. A is the exact
Decimal result from the fixed matrix. B is the exact result from reference seconds
and current coefficients; it is a comparison, not fabricated planned duration.
Difference is raw source minus exact A. Display matches use the workbook's one-
decimal presentation; all pass. No row is a rounding tie, so these rows cannot
distinguish HALF_UP from HALF_EVEN as a future general storage/display policy.
The source constants are exact inputs; private arithmetic remains unrounded until
an explicitly approved presentation/storage boundary.

| Workout / M cell | Raw workbook TSS | Exact published A | Exact reference B | Source − A | One-decimal result | Cause / resolution |
| --- | --- | --- | --- | --- | --- | --- |
| TR-SWIM-001 / M5 | 14.4 | 14.40 | 14.4 | 0.00 | 14.4 — Pass | exact parity; preserve source |
| TR-SWIM-002 / M6 | 21.6 | 21.60 | 21.6 | 0.00 | 21.6 — Pass | exact parity; preserve source |
| TR-SWIM-003 / M7 | 28.8 | 28.80 | 28.8 | 0.00 | 28.8 — Pass | exact parity; preserve source |
| TR-SWIM-004 / M8 | 36 | 36.00 | 36 | 0.00 | 36.0 — Pass | exact parity; preserve source |
| TR-SWIM-005 / M9 | 43.2 | 43.20 | 43.2 | 0.00 | 43.2 — Pass | exact parity; preserve source |
| TR-SWIM-006 / M10 | 50.4 | 50.40 | 50.4 | 0.00 | 50.4 — Pass | exact parity; preserve source |
| TR-SWIM-007 / M11 | 57.6 | 57.60 | 57.6 | 0.00 | 57.6 — Pass | exact parity; preserve source |
| TR-SWIM-008 / M12 | 64.8 | 64.80 | 64.8 | 0.00 | 64.8 — Pass | exact parity; preserve source |
| TR-SWIM-009 / M13 | 72 | 72.00 | 72 | 0.00 | 72.0 — Pass | exact parity; preserve source |
| TR-SWIM-010 / M14 | 28.4 | 28.44 | 28.44 | -0.04 | 28.4 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-011 / M15 | 48.2 | 48.24 | 48.24 | -0.04 | 48.2 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-012 / M16 | 56.6 | 56.64 | 56.64 | -0.04 | 56.6 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-013 / M17 | 56.6 | 56.64 | 56.64 | -0.04 | 56.6 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-014 / M18 | 56.7 | 56.70 | 56.7 | 0.00 | 56.7 — Pass | exact parity; preserve source |
| TR-SWIM-015 / M19 | 37.3 | 37.26 | 37.26 | 0.04 | 37.3 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-016 / M20 | 50.8 | 50.76 | 50.76 | 0.04 | 50.8 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-017 / M21 | 64.3 | 64.26 | 64.26 | 0.04 | 64.3 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-018 / M22 | 37.3 | 37.26 | 37.26 | 0.04 | 37.3 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-019 / M23 | 50.8 | 50.76 | 50.76 | 0.04 | 50.8 — Pass | presentation rounding only; preserve source and exact derived result separately |
| TR-SWIM-020 / M24 | 64.3 | 64.26 | 64.26 | 0.04 | 64.3 — Pass | presentation rounding only; preserve source and exact derived result separately |

Ten rows have exact stored-value parity; ten differ from their exact calculation
by −0.04 or +0.04 because they store the one-decimal result. There is no mathematical
source discrepancy at workbook display precision. Choosing exact A as a future
planned P instead of the stored one-decimal source P still requires an explicit
prospective precision/lineage decision (C04); do not silently replace source cells.

## TR-SWIM-010 and stationary rest

Z2: `(300+300)/100 × 1.44 = 8.64`.
Z3: `(5×200)/100 × 1.98 = 19.80`.
Five 30-second wall rests: **0.00**, not 150 minutes or active Z1 swimming.
Exact A total **28.44**; cell M14 stores **28.4**, matching its one-decimal display.
The PDF page-2 result and source N14 ordered execution agree independently.

The published rule makes stationary rest zero within the distance model. It does
not zero out active Z1 swimming, nor authorize assigning wall time to a Z1 bin.
The current observed minute-based method has no stationary-rest classification:
it sums only supported observed zone minutes and records coverage. If reliable
elapsed total is 35 min with 30 observed Z2 min and 5 min known wall rest, raw
current code gives **21.60**, 30/35 coverage and `partial_observed`. There is no
existing policy to certify those five omitted minutes as complete zero-load rest.
Do not relabel that result measured-complete or fill rest with Z1. The source
rest rule is explicit; the missing integration decision is observed rest evidence,
coverage and active-versus-elapsed duration semantics (S03), not the value zero.

## Multiplier handling: resolved for this source formula

G5:G24 stores 0.9. The PDF's SWIM minute coefficients match the approved engine
constants, and each equals BIKE's corresponding coefficient times 0.90:
0.50×0.90=0.45; 0.80×0.90=0.72; 1.20×0.90=1.08;
1.60×0.90=1.44; 2.00×0.90=1.80. The published distance constants use those already
sport-specific coefficients once, including the Z1 constant's presentation rounding.

There is no separate 0.90 multiplication in the published formula or worked
example. Applying it again to TR-SWIM-010 would produce **25.596**, contradicting
28.44. Dividing it out would also contradict the source. Therefore no extra
multiplier is required to reproduce the delivered model. Retain G as original
metadata; do not execute it again. This is stronger source evidence than the
running workbook's numerical IF hypothesis and must not be generalized to RUN.

## CSS interpretation and remaining approvals

Confirmed: CSS 1:55/100 m is the representative calculation reference for the
published paces; the delivered software formula uses fixed values. It supplies
neither actual performed swimming time nor an authoritative planned duration.
Unresolved: whether the owner intends this exact matrix to remain the prospective
catalog reference for all athletes/source versions or wants a separately specified
CSS-dependent model. Question S01 asks that scope once. Until answered, preserve
the fixed source evidence and withhold athlete-specific scaling. Do not treat
new source notes as approval to alter historical load calculations.

A catalog ID/version and accepted method identifier are not supplied. The PDF has
no explicit method revision/version. Its exact hash can bind the intake evidence
but is not itself an approved catalog/method version. C01/C04 cover formal identity,
precision and original-versus-derived load storage; S02 covers prospective planning
support for the distance method, currently withheld by `with_current_load`.

Evidence: PDF pp. 1–2, worksheet A1:O24, `physiology/joren.py::ZONE_COEFFICIENTS`,
`zone_load`, `workouts/catalog.py::with_current_load`,
[approved V2 specification](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md).
Original source values, formula evidence and running findings are preserved.
No coefficient, scientific formula, API, catalog or database was changed.
