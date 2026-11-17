# Joren running TSS reconciliation

Review date: 2026-11-03 (Europe/Amsterdam). REVIEW ONLY; no catalog activation.
Accepted source branch: `feat/joren-realized-tss-v2`, exact HEAD `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Review branch: `review/joren-new-workout-catalog`, isolated worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Input: `F:\Projecten Business\Start23\Code\docs\trainings\Looptrainingen_Definitief_Optie1.xlsx`.
Input SHA-256: `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3`; 7,198 bytes.
All numerical load values below are private developer review evidence, never athlete-facing data.

## Confirmed engine facts and comparison semantics

There is **no current engine catalog record for any TR-RUN ID**. “Current engine
expected TSS” cannot be a live lookup of those IDs. Two existing methods must be
kept distinct:

1. `joren.zone_load(..., planned=True)` multiplies authoritative minutes by exact
   running coefficients **0.58, 0.92, 1.38, 1.84, 2.30** for Z1–Z5. These remain
   approved under `phase-13-joren-ruleset-1`; Realized TSS V2 did not change them.
   The sum is Decimal, with no final quantization in `zone_load`. There is no
   extra sport multiplication. The table's computed engine reference is this
   exact function applied to each row's complete zone allocation.
2. `catalog.with_current_load` explicitly **retains predefined timed source loads**.
   It does not call `zone_load` for a timed source template. The importer copies
   original source TSS; source-v2 successors retain it. Existing catalog lineage
   is `source_catalog_predefined_tss` / `start23-source-catalog-v0.1`.
   If a future authorized import follows this retention path, P would equal
   Joren's supplied raw value (and retention difference would be zero by definition).
   That is preservation, not independent mathematical validation. This review has
   not imported the rows or authorized that method for this new source.

The Phase 13 approved-occurrence persistence path uses the existing
`planned_zone_minutes` / `phase-13-joren-ruleset-1` label even for retained timed
source P; see `20260910215947_phase_13_joren_ruleset.sql` and the v2 approved spec.
The new import must preserve the separate original source/load lineage rather
than claim a retained value was numerically recomputed using 0.92.
Historical occurrences with the original unsupported source method/version
remain ineligible for v2; there is no relabelling or backfill.

Consequently **0.92 applies to zone-minute computation, but does not automatically
recompute or override the specific predefined-source catalog method**. Treating
27.6 as the only possible current source-template P would misdescribe the engine.

The current RUN Z2–Z5 coefficients already equal the BIKE coefficients multiplied
by 1.15 (for example, 0.80 × 1.15 = 0.92). RUN Z1 is the explicitly supplied 0.58,
rather than substituting the unrounded 0.50 × 1.15 = 0.575. These are fixed
approved constants, not instructions to reapply a multiplier at import time.

## All 20 side-by-side results

`Difference = displayed Joren value minus exact zone-minute engine reference`.
Source M cells use one-decimal presentation; raw source values are shown without
alteration. The exceptional raw M21 difference is
`87.59999999999999 - 82.80 = 4.79999999999999`; its display difference is +4.80.
No one-decimal rounding is used to make engine threshold decisions.

Cause labels: **C0** = parity at source display precision, formula provenance still
unknown; **C2** = Z2 source rate differs from 0.92, source formula unconfirmed;
**CM** = mixed-zone difference, not explained by a universal multiplier;
**CM+R** additionally includes the stored binary residue.
Resolution **R0** = retain original and request J1/J2 source-method acceptance;
**R1** = retain original, ask Joren to choose/confirm the intended versioned source
method or issue a separately versioned corrected source; never tune coefficients.
Approval “Joren” includes exact formula/rounding/source version and subsequent
owner-approved prospective integration. A zero difference does not waive approval.

| Workout | JOREN EXPECTED TSS (raw) | CURRENT ENGINE EXPECTED TSS (zone method) | DIFFERENCE (display − engine) | CAUSE | PROPOSED RESOLUTION | APPROVAL REQUIRED |
| --- | --- | --- | --- | --- | --- | --- |
| TR-RUN-001 | 17.4 | 17.40 | 0.00 | C0 | R0 | Joren: J1/J2 |
| TR-RUN-002 | 23.2 | 23.20 | 0.00 | C0 | R0 | Joren: J1/J2 |
| TR-RUN-003 | 29 | 29.00 | 0.00 | C0 | R0 | Joren: J1/J2 |
| TR-RUN-004 | 32.3 | 27.60 | +4.70 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-005 | 43.1 | 36.80 | +6.30 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-006 | 53.9 | 46.00 | +7.90 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-007 | 64.7 | 55.20 | +9.50 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-008 | 75.5 | 64.40 | +11.10 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-009 | 86.2 | 73.60 | +12.60 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-010 | 97 | 82.80 | +14.20 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-011 | 107.8 | 92.00 | +15.80 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-012 | 118.6 | 101.20 | +17.40 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-013 | 129.4 | 110.40 | +19.00 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-014 | 140.2 | 119.60 | +20.60 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-015 | 150.9 | 128.80 | +22.10 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-016 | 161.7 | 138.00 | +23.70 | C2 | R1 | Joren: J1/J2 |
| TR-RUN-017 | 87.59999999999999 | 82.80 | +4.80 | CM+R | R1 | Joren: J1/J2 |
| TR-RUN-018 | 74.5 | 69.00 | +5.50 | CM | R1 | Joren: J1/J2 |
| TR-RUN-019 | 106.8 | 94.30 | +12.50 | CM | R1 | Joren: J1/J2 |
| TR-RUN-020 | 119.9 | 106.72 | +13.18 | CM | R1 | Joren: J1/J2 |

Confirmed totals: three display-parity rows and 17 positive differences. Raw M21
is not normalized in the workbook or a stored catalog. Across all rows, a future
retention-path result would be the raw source column, including M21's residue.

## Required examples

- **TR-RUN-001:** 30 × 0.58 = 17.40, matching 17.4. Applying 1.15 again would give
  20.01 and break this parity. The presence of a 1.15 column does not authorize it.
- **TR-RUN-004:** 30 × 0.92 = 27.60 versus source 32.3, difference +4.70.
  27.60 × 1.15 = 31.740, which still does not match 32.3.
- **TR-RUN-007:** 60 × 0.92 = 55.20 versus source 64.7, difference +9.50.
  55.20 × 1.15 = 63.480, which still does not match 64.7.

The latter two source values numerically agree with IF=0.75:
`minutes / 60 × 0.75² × 100 × 1.15` gives **32.34375** and **64.6875** before
one-decimal rounding. The 60-minute value also matches the existing onboarding
hourly coefficient. This is a numerical relationship, not proof that the
onboarding or inactive sRPE method is the intended catalog method.

## Inference tested, not an adopted formula

All 20 displayed source values can be reproduced by a zone-specific candidate:

`sum(zone_minutes / 60 × candidate_IF_zone² × 100 × 1.15)`, then one-decimal
ROUND_HALF_EVEN. Candidate IF values for populated zones are Z1 **0.55**, Z2
**0.75**, Z4 **0.98**, Z5 **1.15**. Z3 is unidentifiable because every Z3 cell is
zero; no Z3 value is proposed. The resulting effective rates are:

| Populated zone | Candidate exact/recurring TSS per minute | Current approved zone-minute rate |
| --- | --- | --- |
| Z1 | 0.579791666… | 0.58 |
| Z2 | 1.078125 | 0.92 |
| Z4 | 1.840766666… | 1.84 |
| Z5 | 2.534791666… | 2.30 |

Candidate mixed results before display rounding: 017 = 87.56675;
018 = 74.549708333…; 019 = 106.815833333…; 020 = 119.925833333….
These round to the workbook's 87.6, 74.5, 106.8 and 119.9.
TR-RUN-009 gives exactly 86.25 under that candidate: HALF_EVEN gives 86.2, whereas
HALF_UP gives 86.3. This exposes a rounding/provenance question. The approved
onboarding final-rounding policy is HALF_UP; it must not be silently replaced.
The v2 calculation's 50-digit HALF_EVEN policy is a different method, not authority
for this spreadsheet's original generation policy.

This is not the implemented per-score sRPE mapping: `SRPE_FACTORS` includes
RPE 7=0.94 and 8=1.00, not 0.98. Choosing range minimum, maximum or midpoint is
not an approved catalog rule. The candidate reproduces outputs but cannot prove
unique original inputs, arithmetic, multiplier placement or intent. The workbook
contains no formulas, methodological notes or IF table to settle those questions.
No external formula has been invented or activated as a Wombo requirement.

## Multiplier audit and decisions requiring Joren

| Question | Confirmed evidence / unresolved decision |
| --- | --- |
| Is 1.15 present? | Yes, numeric G5:G24 is 1.15, format 0.00. |
| Is it incorporated into source TSS? | Compatible with the IF reconstruction across all displayed values; not provable from constants alone. J1 remains open. |
| Does current source retention apply it separately? | No. Timed source P is retained unchanged. |
| Does current zone_load apply it separately? | No. It uses the sport-specific coefficient table once. |
| Can multiplying zone output by 1.15 fix parity? | No: Z1, 30-minute Z2 and 60-minute Z2 examples disprove it. |
| Could double-counting occur? | Yes, in a future importer that multiplies already-final source P again; current source retention does not do so. |
| Is original IF methodology confirmed? | No. Inactive per-score reference formula and onboarding explain numerical similarities but do not establish source provenance. |
| Is a newly intended catalog formula approved? | No explicit versioned formula/precision specification is supplied with this workbook. |

Engineering recommendation: quarantine mathematical differences without altering
Joren's values or approved coefficients. Obtain J1's signed/formally accepted
formula and precision examples (including 009 and raw 017). Then separately
approve one prospective path: retain accepted catalog P with honest source lineage,
or accept an explicitly revised source and new catalog revision based on approved
zone coefficients, or introduce an explicitly reviewed/versioned new catalog load
method. None is chosen here. Never reprocess historical plans under the new path.

## Precision and method boundaries

Current `zone_load` retains exact Decimal sums; the values here terminate exactly
and require no rounding. `starting_baseline` rounds the final weekly total to
0.1 HALF_UP. `srpe_formula` is inactive reference behavior and applies the sport
multiplier once. Realized V2 is `P*A*F/T`, 50 significant digits HALF_EVEN,
`decimal-50-half-even-divide-last-1`, without intermediate or display rounding.
Its factor is independent of the sport multiplier and does not reconcile an
incorrect or unapproved P. Treating estimated fallback as an additive measured
load would double-count a session and is prohibited by the approved hierarchy.

There is a practical prospective method difference to resolve: if retained source
P=32.3 for TR-RUN-004 is accepted into a supported occurrence, confirmed A=T and
reported Z2 can yield v2 E=32.3. Actual complete measured 30-minute Z2 bins instead
yield 27.60 and take precedence. For TR-RUN-007 the corresponding pair is 64.7
versus 55.20. The fallback must not change those measured results to force parity.
Even perfect zone execution can therefore have a source-versus-measurement gap;
selection, completion and next-week load outcomes can depend on the accepted
planned-load method and actual evidence. Source acceptance must explicitly
acknowledge that consequence rather than calling it a new coefficient bug.

Evidence: `backend/app/modules/physiology/joren.py`, `realized_v2.py`,
`backend/app/modules/workouts/catalog.py::with_current_load`,
`backend/scripts/generate_source_catalog_payload.py`, immutable source migrations
`20260903074359` and `20260929210000`, Phase 13 occurrence persistence
`20260910215947`, [approved V2 spec](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md).
All comparisons ran against the exact SHA above; workbook hash was checked before
and after review. Cross-sport formula reconciliation waits for the final cycling
and swimming files; no coefficients or IF assumptions transfer automatically.
