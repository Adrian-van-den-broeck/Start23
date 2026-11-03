# Joren cycling catalog validation

Review date: 2026-11-03, Europe/Amsterdam. REVIEW ONLY; no activation.
Accepted engine: `feat/joren-realized-tss-v2`, exact SHA `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch `review/joren-new-workout-catalog`; worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
All private load numbers are developer review evidence, never athlete-facing data.

| Source | Original file | Bytes | SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_Optie1.xlsx | 7198 | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 |
| BIKE | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df |
| SWIM | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674 |
| SWIM spec | Specificatie Zwem TSS.pdf | 149021 | ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a |

RUN original is in `F:\Projecten Business\Start23\Code\docs\trainings`.
BIKE, SWIM and the swim PDF originals are in
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.
All four originals remain byte-identical and at those exact locations. Delivery
is verified; catalog versions and methodological acceptance are separate decisions.

## Source access, isolation and authority

The actual cycling file was found locally at
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Fietstrainingen_Definitief_Optie1.xlsx`.
It was not inferred from a different conversation. The accepted branch and review
HEAD match the exact SHA above. Initial review status contained only the nine
uncommitted prior reports. All were backed up to ignored
`.runtime/final/preexisting/`; the six RUN/SWIM findings reports remain byte-for-byte
unchanged. Three combined/plan reports receive marked continuation updates. No
reset/clean/discard or other worktree modification was performed.

Root `AGENTS.md` is the applicable instruction; recursive discovery found only it
and the unrelated mobile instruction file. The current roadmap/v2 amendment,
existing nine reports, approved v2 spec, implementation report and catalog/
selection/planning contracts supply the reference. A 3–A 9 ancestry and application
identity are preserved at the accepted commit, not reconstructed from the older
root checkout. No source file was edited or resaved.

## Entire workbook inspection

Exactly one visible worksheet, `Fietstrainingen Catalogus`, extent A 1:O25. All nine
OOXML parts and all 332 stored cells were inspected. Row 1 is the title, row 2
states the Option 1 structure and cycling multiplier 1.00, row 3 is empty, row 4
has 15 headers and rows 5–25 contain exactly 21 records. No hidden row/column or
additional worksheet, formula cell, defined name, macro or external-link part was
found. There are 189 numeric and 143 inline-string cells. Source workbook creator
`openpyxl` and generation timestamp `2026-11-03T21:17:01Z` are generation metadata,
not a formally supplied catalog/method revision.

Original headers, including embedded newlines, are preserved in the raw cell
snapshot: `Workout_ID`, `Sport`, `Titel Training`, `Expected RPE`, `Expected Zone`,
`Totale Duur\n(min)`, `Sport Multiplier`, `Z1\n(min)` through `Z5\n(min)`,
`Expected TSS (Berekend)`, `Interval Structuur (Volgorde voor Software)`,
`Trainingsfocus`. Here `\n` denotes the literal header line break.
F5:F25 uses `#,##0` (built-in 3), M5:M25 `#,##0.0`, other number formats General.
G stores numeric `1`. M8 stores `84.40000000000001`, M25 stores
`96.09999999999999`; displays are 84.4 and 96.1. Neither residue is repaired.
All 21 TSS cells are constants despite the “Berekend” header.

## All 21 results

IDs are unique, consecutive TR-BIKE-001–021. Every Sport is exactly `Fietsen`,
name/focus/source field is populated, total minutes positive and finite,
multiplier exactly one, and zone minutes nonnegative numeric. Every RPE pair is
within 1–10 and both endpoints map to Expected Zone under new
`joren-realized-tss-matrix-2` (1–2/3–4/5–6/7–8/9–10). Expected Zone is session focus,
not an override of interval zones. No Z3 allocation is present.

The parser consumes every ordered token using `(positive number)(m|s) Z[1-5]`.
Seconds convert to exact Decimal minutes before any summation. No segment is
rounded. Both total and every individual zone subtotal agree independently with
the aggregate source cells; no warm-up/cooldown/recovery block is fabricated.
The table's “Pass” includes those checks and new RPE mapping, not scientific
acceptance or selection readiness. Z minutes are Z1/Z2/Z3/Z4/Z5.

| ID / row | Original name | RPE / focus zone | Total / Z minutes | Structure / checks | Original training focus |
| --- | --- | --- | --- | --- | --- |
| TR-BIKE-001 / 5 | Herstel 60min | 1, 2 / Z1 | 60 / 60,0,0,0,0 | single / Pass | Actief herstel (Z1) |
| TR-BIKE-002 / 6 | Herstel 1u30 | 1, 2 / Z1 | 90 / 90,0,0,0,0 | single / Pass | Actief herstel (Z1) |
| TR-BIKE-003 / 7 | Herstel 2u00 | 1, 2 / Z1 | 120 / 120,0,0,0,0 | single / Pass | Actief herstel (Z1) |
| TR-BIKE-004 / 8 | LSD 1u30 | 3, 4 / Z2 | 90 / 0,90,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-005 / 9 | LSD 2u00 | 3, 4 / Z2 | 120 / 0,120,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-006 / 10 | LSD 2u30 | 3, 4 / Z2 | 150 / 0,150,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-007 / 11 | LSD 3u00 | 3, 4 / Z2 | 180 / 0,180,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-008 / 12 | LSD 3u30 | 3, 4 / Z2 | 210 / 0,210,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-009 / 13 | LSD 4u00 | 3, 4 / Z2 | 240 / 0,240,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-010 / 14 | LSD 5u00 | 3, 4 / Z2 | 300 / 0,300,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-011 / 15 | LSD 5u30 | 3, 4 / Z2 | 330 / 0,330,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-012 / 16 | LSD 6u00 | 3, 4 / Z2 | 360 / 0,360,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-013 / 17 | LSD 7u00 | 3, 4 / Z2 | 420 / 0,420,0,0,0 | single / Pass | Aerobe basis / LSD |
| TR-BIKE-014 / 18 | Lange intervallen | 7, 8 / Z4 | 180 / 0,100,0,80,0 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-BIKE-015 / 19 | Lange intervallen | 7, 8 / Z4 | 120 / 0,80,0,40,0 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-BIKE-016 / 20 | Lange intervallen | 7, 8 / Z4 | 180 / 0,100,0,80,0 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-BIKE-017 / 21 | Lange intervallen | 7, 8 / Z4 | 220 / 0,100,0,120,0 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-BIKE-018 / 22 | VO2max Piramide | 9, 10 / Z5 | 150 / 0,90,0,0,60 | mixed / Pass | VO2max / Maximale capaciteit (Z5) |
| TR-BIKE-019 / 23 | VO2max Seiler Intervallen | 9, 10 / Z5 | 100 / 0,68,0,0,32 | mixed / Pass | VO2max / Maximale capaciteit (Z5) |
| TR-BIKE-020 / 24 | HIIT Sprints | 9, 10 / Z5 | 93 / 15,75,0,0,3 | mixed / Pass | Sprint / Anaeroob (Z5) |
| TR-BIKE-021 / 25 | HIIT Sprints | 9, 10 / Z5 | 104 / 15,85,0,0,4 | mixed / Pass | Sprint / Anaeroob (Z5) |

Exactly 13 rows are single-zone: 001–003 Z1; 004–013 Z2. Eight rows 014–021
are mixed: four Z2/Z4, two Z2/Z5, two Z1/Z2/Z5. No single-zone Z4/Z5 fallback
eligibility is inferred from the Expected Zone column.

| ID | Original full ordered string |
| --- | --- |
| TR-BIKE-001 | 60m Z1 |
| TR-BIKE-002 | 90m Z1 |
| TR-BIKE-003 | 120m Z1 |
| TR-BIKE-004 | 90m Z2 |
| TR-BIKE-005 | 120m Z2 |
| TR-BIKE-006 | 150m Z2 |
| TR-BIKE-007 | 180m Z2 |
| TR-BIKE-008 | 210m Z2 |
| TR-BIKE-009 | 240m Z2 |
| TR-BIKE-010 | 300m Z2 |
| TR-BIKE-011 | 330m Z2 |
| TR-BIKE-012 | 360m Z2 |
| TR-BIKE-013 | 420m Z2 |
| TR-BIKE-014 | 30m Z2 \| 20m Z4 \| 10m Z2 \| 20m Z4 \| 10m Z2 \| 20m Z4 \| 10m Z2 \| 20m Z4 \| 10m Z2 \| 30m Z2 |
| TR-BIKE-015 | 30m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 30m Z2 |
| TR-BIKE-016 | 30m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 10m Z4 \| 5m Z2 \| 30m Z2 |
| TR-BIKE-017 | 30m Z2 \| 30m Z4 \| 10m Z2 \| 30m Z4 \| 10m Z2 \| 30m Z4 \| 10m Z2 \| 30m Z4 \| 10m Z2 \| 30m Z2 |
| TR-BIKE-018 | 20m Z2 \| 10m Z5 \| 10m Z2 \| 5m Z5 \| 10m Z2 \| 20m Z5 \| 10m Z2 \| 15m Z5 \| 10m Z2 \| 10m Z5 \| 30m Z2 |
| TR-BIKE-019 | 30m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 2m Z2 \| 8m Z5 \| 2m Z2 \| 30m Z2 |
| TR-BIKE-020 | 30m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 15m Z2 \| 15m Z1 |
| TR-BIKE-021 | 30m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 30s Z5 \| 5m Z2 \| 15m Z2 \| 15m Z1 |

TR-BIKE-020 has six 30 s Z5 sprints: 6×0.5 = 3 min; Z1/Z2/Z5 = 15/75/3,
total 93. TR-BIKE-021 has eight: 8×0.5 = 4 min; 15/85/4, total 104.
Their current zone-minute references are 73.50 and 83.50, respectively.
Interpreting each sprint as 30 minutes would be a structural rejection; it did
not occur in this review. Each original token/unit remains in source lineage.

## Existing cycling comparison and historical retention

The current projection has 54 cycling templates: 50 source-v2 rows and four
built-in/protocol templates, including unavailable/protocol-only entries. Original
source-v1 prescriptions and their immutable v2 successors remain historical/current
versions; no version or source ID is repurposed. Exact ordered duration/zone
signatures were compared with the current catalog. All new IDs are distinct.

| New ID | Exact old execution matches | Relationship / action |
| --- | --- | --- |
| TR-BIKE-001 | BIK-001, BIK-002, BIK-003, BIK-004 | Execution-only match; RPE/load/provenance differ; no replacement approval |
| TR-BIKE-002 | BIK-005 | Execution-only match; RPE/load/provenance differ; no replacement approval |
| TR-BIKE-003 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-004 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-005 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-006 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-007 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-008 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-009 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-010 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-011 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-012 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-013 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-014 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-015 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-016 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-017 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-018 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-019 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-020 | none | New ordered prescription; no replacement assigned |
| TR-BIKE-021 | none | New ordered prescription; no replacement assigned |

TR-BIKE-001 matches 60-minute Z1 execution of BIK-001–004; 002 matches BIK-005's
90-minute Z1 execution. Those are not complete equivalents: new RPE is 1–2,
old source guidance is 2–3; source P differs and IDs/revisions remain distinct.
For example old BIK-001 P=36 versus new 30.2. TR-BIKE-014 and 016 share zone
aggregates/P but have different repetitions; do not merge them. Names, numeric
suffixes or equal load totals never determine identity. None is confirmed obsolete.

## Missing selection and provenance metadata

No source catalog/method revision, accepted formula/precision policy, whole-workout
bucket, phase/capability/auto/explicit/repeat policy or separate mixed-block RPE
prescription is supplied. All 21 need the A–F decisions in the Dutch brief; their
concrete proposed metadata is in the final reconciliation's all-61 table.
Mixed Z2 recovery blocks must use their own reviewed guidance, not session 7–8
or 9–10 merely to pass the current aggregate-range validator.

The seven-hour TR-BIKE-013 is not established as beginner-eligible. A deliberately
single-candidate, zero-history diagnostic shows the unchanged planner returns a
pending 420-minute/P 393.8 draft at target 45 with a capacity warning. It has no
approved individual novice-duration filter for this source. This is a suitability
and selection-policy gap, not a justification to auto-promote the row. No new
physiological duration cap or formula was invented to hide that result.

See [cycling TSS reconciliation](JOREN_CYCLING_TSS_RECONCILIATION.md),
[cycling V2 eligibility](JOREN_CYCLING_REALIZED_V2_ELIGIBILITY.md),
[combined simulations](JOREN_THREE_SPORT_PLANNING_SIMULATION.md) and
[approval brief](JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md).

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.
