# Joren running catalog validation

Review date: 2026-11-03 (Europe/Amsterdam). REVIEW ONLY; no catalog activation.
Accepted source branch: `feat/joren-realized-tss-v2`, exact HEAD `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Review branch: `review/joren-new-workout-catalog`, isolated worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Input: `F:\Projecten Business\Start23\Code\docs\trainings\Looptrainingen_Definitief_Optie1.xlsx`.
Input SHA-256: `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3`; 7,198 bytes.
All numerical load values below are private developer review evidence, never athlete-facing data.

## Outcome and source authority

The workbook is accessible and all 20 rows were inspected. Structural arithmetic passes.
Intake is **not migration-ready**: intended load formula/rounding, catalog version,
whole-workout buckets, phase eligibility and mixed-segment RPE metadata are unresolved.
No application, API, formula, migration or environment was changed. The original Excel
file remains at its original path, byte-for-byte unchanged. It was an untracked root
intake file and was deliberately not added to or edited in the accepted baseline.

`AGENTS.md` is the applicable instruction file for this review. Recursive discovery
found only the root and `mobile/AGENTS.md`; no narrower instruction applies to
`docs/catalog`. The current MVP roadmap and its 2026-11-03 v2 amendment, approved v2
specification and current Joren planning ruleset were read. Older September catalog
investigations are historical: their automatic-selection shortage is superseded by
the immutable source-v2 promotion in `20260929210000_joren_planning_ruleset_v2.sql`.

The accepted branch's existing worktree and the new review worktree both returned
empty `git status --porcelain=v1` before review. The older root checkout is dirty on
`fix/pre-ui-beta-blockers` at `6bb3a04`; none of its changes were used as implementation
or modified. `git merge-base --is-ancestor` confirms accepted A9
`e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` is an ancestor of the exact review baseline.
A3–A9 and Realized TSS V2 are preserved by keeping that tree unchanged.

## Confirmed workbook facts

The entire OOXML ZIP was read, including every stored cell, worksheet definition,
styles, workbook relationships and properties. One visible worksheet exists:
`Looptrainingen Catalogus`, used extent `A1:O24`, 317 stored cells. Row 1 is
`TRAININGSCATALOGUS (1 RIJ PER TRAINING)`, row 2 is
`Aangepast aan de gewenste 'Optie 1' tabelstructuur.`, row 3 is empty,
row 4 contains 15 headers, and rows 5–24 contain exactly 20 complete records.
There are no hidden additional worksheets, formula cells, defined names, external
link parts, macros, comment parts, charts or additional records outside that extent.
Workbook `fullCalcOnLoad=1` does not make constants into formulas.

Headers, in order: `Workout_ID`, `Sport`, `Titel Training`, `Expected RPE`,
`Expected Zone`, `Totale Duur`, `Sport Multiplier`, `Z1`, `Z2`, `Z3`, `Z4`, `Z5`,
`Expected TSS (Berekend)`, `Interval Structuur (Volgorde voor Software)`, `Trainingsfocus`.
Text is inline-string data in A–D and N–O; E–M are numeric. All cells use General
number format except G5:G24, built-in 2 (`0.00`), and M5:M24 (`#,##0.0`).
Thus multiplier 1.15 displays as 1.15 and stored M21
`87.59999999999999` displays as 87.6. That raw value is preserved, not repaired.

Every ID is present, unique and matches `TR-RUN-001` through `TR-RUN-020` without gaps.
Uniqueness in this file is verified; future stability across source revisions needs
an explicit catalog identity/version contract. Every Sport is exactly `Lopen` and
every Sport Multiplier is stored as `1.15`. Duration units are supported by all
ordered strings' explicit `m` tokens and title text; an import must declare canonical
minutes explicitly because `Totale Duur` alone has no unit suffix.

## All-row validation

In every row: positive whole-minute total, nonnegative numeric Z1–Z5, sum of zone
minutes equals the total, ordered segments parse completely as `Nm Zk` separated by
` | `, segment sum equals the same total, and each segment's zone subtotal equals
the corresponding Z1–Z5 cell. No warm-up, cooldown or rest was added. A single-zone
row remains exactly its one segment. All supplied RPE pairs are integer endpoints
within 1–10 and both endpoints map to the supplied Expected Zone under
`joren-realized-tss-matrix-2`. No supplied field is blank or invalid structurally.
Training-focus text is present in every row and its labels are consistent with the
stated target zone as descriptive metadata; physiological effectiveness is not
established by this review.

In the table, Z minutes are ordered Z1/Z2/Z3/Z4/Z5. “Pass” verifies both independent
duration sums, per-zone agreement, identifier/sport, required supplied fields and
new-version RPE mapping. Every row still has the common provenance/integration gaps
listed below. Planned-load reconciliation is in the separate TSS report.

| ID / Excel row | Original title | RPE / expected zone | Total / Z minutes | Ordered sum / checks | Original training focus |
| --- | --- | --- | --- | --- | --- |
| TR-RUN-001 / 5 | Herstel 30min lopen in zone 1 | 1, 2 / Z1 | 30 / 30,0,0,0,0 | 30 / Pass | Actief herstel |
| TR-RUN-002 / 6 | Herstel 40min lopen in zone 1 | 1, 2 / Z1 | 40 / 40,0,0,0,0 | 40 / Pass | Actief herstel |
| TR-RUN-003 / 7 | Herstel 50 min lopen in zone 1 | 1, 2 / Z1 | 50 / 50,0,0,0,0 | 50 / Pass | Actief herstel |
| TR-RUN-004 / 8 | LSD 30 min lopen in zone 2 | 3, 4 / Z2 | 30 / 0,30,0,0,0 | 30 / Pass | Aerobe basis / LSD |
| TR-RUN-005 / 9 | LSD 40 min lopen in zone 2 | 3, 4 / Z2 | 40 / 0,40,0,0,0 | 40 / Pass | Aerobe basis / LSD |
| TR-RUN-006 / 10 | LSD 50 min lopen in zone 2 | 3, 4 / Z2 | 50 / 0,50,0,0,0 | 50 / Pass | Aerobe basis / LSD |
| TR-RUN-007 / 11 | LSD 60 min lopen in zone 2 | 3, 4 / Z2 | 60 / 0,60,0,0,0 | 60 / Pass | Aerobe basis / LSD |
| TR-RUN-008 / 12 | LSD 1u10 lopen in zone 2 | 3, 4 / Z2 | 70 / 0,70,0,0,0 | 70 / Pass | Aerobe basis / LSD |
| TR-RUN-009 / 13 | LSD 1u20 lopen in zone 2 | 3, 4 / Z2 | 80 / 0,80,0,0,0 | 80 / Pass | Aerobe basis / LSD |
| TR-RUN-010 / 14 | LSD 1u30 lopen in zone 2 | 3, 4 / Z2 | 90 / 0,90,0,0,0 | 90 / Pass | Aerobe basis / LSD |
| TR-RUN-011 / 15 | LSD 1u40 lopen in zone 2 | 3, 4 / Z2 | 100 / 0,100,0,0,0 | 100 / Pass | Aerobe basis / LSD |
| TR-RUN-012 / 16 | LSD 1u50 lopen in zone 2 | 3, 4 / Z2 | 110 / 0,110,0,0,0 | 110 / Pass | Aerobe basis / LSD |
| TR-RUN-013 / 17 | LSD 2u00 lopen in zone 2 | 3, 4 / Z2 | 120 / 0,120,0,0,0 | 120 / Pass | Aerobe basis / LSD |
| TR-RUN-014 / 18 | LSD 2u10 lopen in zone 2 | 3, 4 / Z2 | 130 / 0,130,0,0,0 | 130 / Pass | Aerobe basis / LSD |
| TR-RUN-015 / 19 | LSD 2u20 lopen in zone 2 | 3, 4 / Z2 | 140 / 0,140,0,0,0 | 140 / Pass | Aerobe basis / LSD |
| TR-RUN-016 / 20 | LSD 2u30 lopen in zone 2 | 3, 4 / Z2 | 150 / 0,150,0,0,0 | 150 / Pass | Aerobe basis / LSD |
| TR-RUN-017 / 21 | Lange interval | 7, 8 / Z4 | 60 / 0,30,0,30,0 | 60 / Pass | Anaerobe Drempel (Threshold) |
| TR-RUN-018 / 22 | Lange interval 2 | 7, 8 / Z4 | 55 / 0,35,0,20,0 | 55 / Pass | Korte Threshold intervallen |
| TR-RUN-019 / 23 | Piramide interval | 9, 10 / Z5 | 68 / 0,45,0,0,23 | 68 / Pass | VO2max Piramide |
| TR-RUN-020 / 24 | Seiler interval | 9, 10 / Z5 | 68 / 0,36,0,0,32 | 68 / Pass | VO2max Seiler intervallen |

Exactly 16 rows (001–016) are single-zone: three Z1 and thirteen Z2. Rows 017–020
are mixed; none is a single-zone Z4/Z5 prescription despite its Expected Zone.
There is no Z3 allocation anywhere in the new workbook.

| ID | Original ordered interval string | Low minutes Z1/Z2 | High minutes Z3–Z5 | Existing duration-dominance classifier |
| --- | --- | --- | --- | --- |
| TR-RUN-017 | 10m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 10m Z2 | 30 | 30 | high (exact tie) |
| TR-RUN-018 | 10m Z2 \| 5m Z4 \| 5m Z2 \| 5m Z4 \| 5m Z2 \| 5m Z4 \| 5m Z2 \| 5m Z4 \| 10m Z2 | 35 | 20 | low |
| TR-RUN-019 | 10m Z2 \| 3m Z5 \| 10m Z2 \| 5m Z5 \| 5m Z2 \| 7m Z5 \| 5m Z2 \| 5m Z5 \| 5m Z2 \| 3m Z5 \| 10m Z2 | 45 | 23 | low |
| TR-RUN-020 | 15m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 15m Z2 | 36 | 32 | low |

This last column is a diagnostic, **not an approved bucket assignment**. Current
source planning uses the reviewed whole-workout bucket; it does not infer that
bucket from Expected Zone or a VO2/threshold title. Rows 018–020 would be low by
duration dominance even though their work blocks are high. Joren must supply the
whole-workout classification and phase policy. No 80/20 field is present.

## Source gaps and decisions requiring Joren

- **J1 — Load authority:** identify the actual catalog calculation, coefficients or
  IF anchors, whether 1.15 is included, exact rounding stage/mode and authoritative
  unrounded values. The label “Berekend” is not formula provenance. Resolve M21's
  raw binary residue without overwriting the original. See the reconciliation.
- **J2 — Version/identity:** assign an immutable source catalog/revision, owner
  acceptance record and exact file-hash binding. Confirm whether TR-RUN IDs replace
  old IDs or form new logical templates; no replacement list was supplied.
- **J3 — Selection:** approve each row's whole-workout bucket, base/build/recovery/
  taper eligibility, zone/fallback capabilities and automatic/athlete-selection
  status. Focus text does not encode these decisions. Existing deterministic
  selection rules can then filter the approved metadata unchanged.
- **J4 — Prescription mapping:** confirm how the new expected-RPE mapping is
  versioned in catalog guidance and supply per-segment RPE prescriptions for
  intervals. A session range 7–8/9–10 does not prescribe the Z2 recovery segments.
  Current WorkoutTemplate validation requires every segment's scalar RPE to fall
  within the template's aggregate range; a lossless mapping needs an explicit
  approved representation, not a fabricated RPE for recovery blocks.
- **J5 — Historical cutover:** approve replacement/equivalence/deprecation mapping
  and prospective selection date after cycling/swimming arrive. Retain original
  templates, revisions and historical planned/realized snapshots.

## Running-only planner experiments

The unchanged actual Python `build_weekly_plan` was called 27 times: nine cases
against three in-memory running decks. No repository override, persisted catalog,
API or feature setting was changed. These are conditional capacity experiments,
not an import or a final catalog simulation.

`current_52` is the 50 immutable source-v2 RUN rows plus two active built-ins,
using `benchmarks.planning.full_catalog()`'s deterministic migration projection
filtered to RUN. The 154-row JSON comes from migration `20260903074359`; source-v2
eligibility matches `20260929210000`. Projected IDs are stable original source IDs,
not an assertion about hosted randomly generated successor UUIDs. The source
planned loads are retained. Single-sport filtering is passed directly to the
planner; `active_catalog`'s all-three-sports coverage invariant is not weakened.

`conditional_16_source` contains only the 16 complete single-zone new rows, with
raw source P values. `conditional_16_zone` contains those same prescriptions with
P from the actual `zone_load(..., planned=True)` result. They replace all current
running rows **only in the call argument**. Both assume, solely for comparison,
low bucket; all four phase tags; known HR requirements; compatible fallback;
automatic selection; synthetic UUIDs `UUID(int=1001+i)` and keys `2001+i`; and
review-only source namespace `REVIEW-ONLY-NOT-APPROVED`. One segment uses the lower
of the row's supplied RPE pair to satisfy the scalar domain field. None of this
missing metadata is presented as an accepted import decision. The four mixed
rows are withheld because bucket/phase/per-segment RPE decisions are missing.
Consequently build high-work coverage of the full 20-row catalog is unresolved.

Common input: week Monday 2026-10-26, Europe/Amsterdam, RUN goal only, no injury,
known capabilities, all seven available dates, no prior approved plan unless
specified. Default race 2027-03-15. Zero-history baseline is the actual 45.0;
3 h/week and 15 h/week onboarding histories produce 194.1 and 970.3 respectively.
The case labelled history below is prior-month training history, **not** a prior
approved-plan history. Build/recovery cases have four prior approved build weeks,
each P=R=100, with per-RUN planned load 100. Race is 2026-12-14 (build position 3)
or 2027-01-04 (recovery). These are actual benchmark fixture inputs.

Each successful cell is `planned load / minutes / occurrences`; all results are
pending drafts. A capacity warning means nearest fit, not exact target fulfillment.

| Case / target | Current 52 | Conditional 16 source loads | Conditional 16 zone loads |
| --- | --- | --- | --- |
| run_zero / 45.0 | 45 / 75 / 2 | 46.4 / 80 / 2 [gap] | 45.00 / 60 / 2 |
| beginner_one_day / 45.0 | 45 / 75 / 2 | 46.4 / 80 / 2 [gap] | 45.00 / 60 / 2 |
| run_history / 194.1 | 194 / 240 / 2 [gap] | 194.1 / 180 / 2 | 194.00 / 270 / 5 [gap] |
| build_week / 110.00 | 110 / 150 / 2 | 110.2 / 130 / 4 [gap] | 109.80 / 160 / 4 [gap] |
| recovery_week / 60.00 | 60 / 75 / 1 | 60.5 / 70 / 2 [gap] | 60.00 / 80 / 2 |
| high_volume / 970.3 | 970.30 / 1185 / 11 | 970.3 / 900 / 7 | 970.20 / 1110 / 10 [gap] |
| no_days | availability_required | availability_required | availability_required |
| repeat_one_template / 194.1 | 198 / 330 / 11 [gap] | 191.4 / 330 / 11 [gap] | 191.40 / 330 / 11 [gap] |
| exhausted_25_occurrences | swipe_selection_invalid | swipe_selection_invalid | swipe_selection_invalid |

Zero-history current choice is RUN-002 + RUN-001; conditional source choice is
TR-RUN-003 + TR-RUN-001; conditional zone choice is TR-RUN-004 + TR-RUN-001.
The unchanged target therefore does not imply the same duration or exercise mix.
The one-day beginner case restricts availability to 2026-10-26: each deck places
both low workouts on that date and emits `workouts_consolidated_on_available_dates`.
Availability is date-based here, with no per-day minute budget. An 80-minute
same-day draft is not evidence of suitability for a beginner with a 30-minute
limit; no such limit or new safety threshold was invented.

High-volume source-load selection repeats TR-RUN-014 twice and TR-RUN-016 four
times plus TR-RUN-005 once. The zone-load alternative repeats TR-RUN-003 three
times, TR-RUN-016 six times plus TR-RUN-007 once. Repeats preserve template identity
and require distinct occurrence identities at approval. Current repeat/swipe API
coverage passed in the backend suite. The single-candidate experiment retains
only RUN-001 or TR-RUN-001: all decks use 11 occurrences rather than exhausting
a deck after one use. An explicit 25-occurrence selection of that single template
fails `swipe_selection_invalid` in each deck; this case also violates target-fit,
so it is not an isolated proof of the 24-occurrence bound. The source code's
bounded selector independently establishes the automatic 24 limit. Empty dates
fail `availability_required`; withholding all rows pending metadata would leave
no usable deck (`catalog_empty`), not authorize inventing replacements.

Single samples ranged from 0.078 to 3459.888 ms across these cases. The conditional
zone-load high-volume search took 3459.888 ms versus 626.423 ms for current and
280.339 ms for conditional source loads. These are one-run local timings with
concurrent backend regression work, not an SLA or a reliable speed comparison.
Fewer catalog rows do not guarantee faster exact-fit search; changed load grids
can expand states. Full-catalog performance verification is deferred.

## Multi-week and completion implications

An additional three-week conditional running-only experiment used the 16 source-load
rows and unchanged planner plus `aggregate_week`. Every completed occurrence was
assigned a synthetic, supported v2 estimate on confirmed A=T with reported zone
matching the single planned zone. Synthetic approval/provenance is an assumption;
no real occurrence was created. Week two deliberately omitted one occurrence:

| Week | Target / basis | Selected P / minutes | Known subtotal / usable load | Completion reason |
| --- | --- | --- | --- | --- |
| 2026-10-26 | 45.0 / initial_catalog_baseline | 46.4 / 80 | 46.4 / 46.4 | complete |
| 2026-11-02 | 51.040 / realized_progression | 52.2 / 90 | 29 / None | unknown_workout_completion |
| 2026-11-09 | 52.2 / prior_planned_hold | 52.2 / 90 | 52.2 / 52.2 | complete |

Thus week three holds the prior plan at 52.2 instead of progressing from the
incomplete subtotal 29. RPE-only coverage can support volume progression only
when every expected occurrence is resolved with compatible evidence. It supplies
no measured intensity minutes and does not enable RPE-only onboarding.

A separate mixed-completion fixture has TR-RUN-004's eligible estimate 32.3,
TR-RUN-017's complete observed load 82.8 and an expected TR-RUN-020 occurrence.
Prior approved P is the synthetic 239.8, week 2026-10-26, race 2026-12-27:

| Third occurrence | Known subtotal | Planner-usable | Next target / basis | Reason |
| --- | --- | --- | --- | --- |
| unknown | 115.1 | None | 239.8 / prior_planned_hold | unknown_workout_completion |
| explicit_skip | 115.1 | 115.1 | 115.1 / realized_baseline | complete |
| mixed_unavailable | 115.1 | None | 239.8 / prior_planned_hold | partial_or_unavailable_load |

An explicit skip resolves completion but does not create performed load. At this
low completion, the existing baseline rule produces 115.1, not automatic 10% growth.
Mixed intervals without supported observation remain unavailable for RPE fallback.
Recovery/taper, illness, injury and fatigue retain precedence; regression coverage
includes these boundaries, three consecutive v2 weeks and historical planning.
No new mixed-workout correction or whole-session RPE scaling was introduced.

## Verification and deferred scope

Read-only OOXML inspection, all-20 arithmetic/mapping checks, all-20 conditional
occurrence eligibility checks, exact/coalesced old/new execution comparisons,
27 running-only planner calls, three rolling weeks and three mixed-completion
cases ran successfully. Full accepted backend suite rerun from this isolated
worktree: **1013 passed, 1 existing Starlette/httpx deprecation warning, 156.65 s**.
This includes OpenAPI, recursive private-load/public-contract, catalog parity,
source-migration static, v2 arithmetic/occurrence/weekly/planning and A3–A9 backend
regressions. No test was edited. Local scratch extraction/experiment scripts and
JSON are in ignored `.runtime/`; only the four requested Markdown reports are
review deliverables.

Ruff `check --no-cache app tests benchmarks` passed; Ruff
`format --check --no-cache app tests benchmarks` passed for 161 files; strict
`mypy app tests` passed for 155 source files. `git diff --check` passed, and
`git diff --exit-code HEAD -- backend mobile supabase` confirmed no changes in
those application trees. Only the four requested reports are untracked changes;
HEAD remains the exact baseline above. The original workbook SHA-256 is unchanged.
Mobile TypeScript and mobile suites were not rerun: no mobile/application files changed; baseline
historical results remain attributed to the v2 implementation report. They remain
required in the future implementation gate, not newly passed by this review.
PostgreSQL/pgTAP remains **DEFERRED BY OWNER — PRE-BETA**. No migrations, RPCs,
hosted data, production/staging, push, merge or deployment were executed.

Cycling and swimming intake, full replacement and full cross-sport/multi-week/
performance simulation await both final workbooks and resolved running decisions.
No placeholders were made and no claim about complete triathlon coverage is made.

## Repository evidence

- [Current roadmap](../implementation/mvp-roadmap.md), especially Phase 13 and v2 amendment.
- [Approved Realized TSS V2](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md).
- [Current selection rules](../implementation/joren-planning-ruleset-v2.md).
- `backend/app/modules/physiology/joren.py`: exact coefficients and load methods.
- `backend/app/modules/workouts/catalog.py`: immutable validation, snapshots, source-load retention.
- `backend/app/modules/planning/domain.py`: eligible_workouts, resolve_target, bounded selection, scheduling.
- `backend/benchmarks/planning.py`: immutable source-v2 projection and scenario inputs.
- `backend/tests/test_mvp_catalog_coverage.py`, `test_realized_context.py`, `test_realized_v2_planning.py`.
- Companion [reconciliation](JOREN_RUNNING_TSS_RECONCILIATION.md),
  [eligibility](JOREN_RUNNING_REALIZED_V2_ELIGIBILITY.md) and
  [import plan](JOREN_WORKOUT_CATALOG_IMPORT_PLAN.md).
