# Joren swimming catalog validation

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

## Result and workspace custody

All 20 supplied swimming records pass source-structure validation. All 20 source
TSS values match the published fixed-distance model at their one-decimal display
precision. This establishes source arithmetic compatibility, **not catalog
activation or complete integration readiness**. The current distance-only planned
load projection withholds P, and the duration-based RPE fallback lacks planned T.
Stationary rests also need a faithful future segment representation.

The root `AGENTS.md` applies to `docs/catalog`; recursive discovery found no
nearer instruction. The current roadmap/v2 amendment, all four running reports,
approved Realized TSS V2 specification, implementation report, catalog/domain/
repository and selection/planning contracts were read. Review HEAD and accepted
branch both resolve to the exact SHA above. The review worktree initially had
only the four untracked running reports. They were preserved; only the existing
import plan receives an evidence-based swimming addendum. The three other running
reports are byte-identical to their prior hashes. Source originals remain untouched
and untracked in their original worktree. No reset, discard, commit, push, merge,
application edit, hosted operation, migration or deployment occurred.

Cycling search checked known relevant `docs/trainings` and `docs/requirements`
directories in the older root, this review worktree and the accepted engine
worktree, including ignored files. It was then extended only to the known
`docs/trainings` locations across existing worktrees: 28 training-source
directories in total, including the root. No new cycling workbook was found.
The old multi-sport source CSV is historical evidence, not a newly supplied
cycling workbook. **CYCLING CATALOG — SOURCE NOT YET AVAILABLE**.

## Complete workbook inspection

One visible worksheet: `Zwemtrainingen Catalogus`; used extent `A1:O24`.
All nine OOXML parts and all 317 cells were read/parsed. There are 180 numeric
and 137 inline-string cells; zero formula cells, hidden rows/columns, extra
worksheets, external-link parts, defined names or macros. Rows 1/2 are title/note,
row 3 is empty, row 4 has 15 headers, and rows 5–24 are exactly 20 complete records.
The source note explicitly states that Z1–Z5 are meters, TSS is calculated per
100 m, and rest in seconds generates zero TSS. Workbook timestamps and the
`openpyxl` creator are generation metadata, not an accepted catalog version.

Headers in original order: `Workout_ID`, `Sport`, `Titel Training`, `Expected RPE`,
`Expected Zone`, `Totale Afstand`, `Sport Multiplier`, `Z1 (m)`, `Z2 (m)`, `Z3 (m)`,
`Z4 (m)`, `Z5 (m)`, `Expected TSS (Berekend)`,
`Interval Structuur (Volgorde voor Software)`, `Trainingsfocus`.
F5:F24 has built-in format 3 (`#,##0`); M5:M24 has `#,##0.0`; other cells have
General numeric format. G is stored as `0.9`, not a formula. Values A–D/N–O are
text; E–M are numeric. The label “Berekend” does not imply an Excel formula.

Every identifier is unique and matches TR-SWIM-001–020 consecutively. Every sport
is exactly `Zwemmen`; every total is a positive finite integer number of meters;
all five zone allocations are explicit nonnegative integers and sum to that total.
All supplied fields are populated. All source RPE pairs map exactly to Expected
Zone under `joren-realized-tss-matrix-2`: 3–4/Z2, 5–6/Z3, 7–8/Z4 or 9–10/Z5.
Source focus labels are retained as descriptive intent; no efficacy claim or
selection policy is inferred from those labels.

## All 20 results

Every full ordered string parses as `Nm Zk` swimming or `Ns Rust` stationary rest,
with literal ` | ` delimiters. Every token is consumed, with positive measure.
Swimming distances alone sum to Total Distance; their zone aggregates exactly
match H:L. A rest has zero swimming distance, no zone and explicit seconds.
There are 276 ordered events overall: 154 swimming events and 122 stationary
rests totaling 3,255 seconds. There are no unparsed/ambiguous source tokens.

Z meters below are Z1/Z2/Z3/Z4/Z5. “Pass” covers identity/sport, complete source
fields, total/zone/ordered-distance equality and new-version RPE mapping. Selection
and provenance gaps apply to every row, separately from these structural passes.

| ID / row | Original title | Meters / Z meters | RPE / expected zone | Rest count / seconds | Structure / validation | Original focus |
| --- | --- | --- | --- | --- | --- | --- |
| TR-SWIM-001 / 5 | LSD 1000m | 1000 / 0,1000,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-002 / 6 | LSD 1500m | 1500 / 0,1500,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-003 / 7 | LSD 2000m | 2000 / 0,2000,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-004 / 8 | LSD 2500m | 2500 / 0,2500,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-005 / 9 | LSD 3000m | 3000 / 0,3000,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-006 / 10 | LSD 3500m | 3500 / 0,3500,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-007 / 11 | LSD 4000m | 4000 / 0,4000,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-008 / 12 | LSD 4500m | 4500 / 0,4500,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-009 / 13 | LSD 5000m | 5000 / 0,5000,0,0,0 | 3, 4 / Z2 | 0 / 0 | single Z2 / Pass | Aerobe basis / LSD |
| TR-SWIM-010 / 14 | Race pace blokken | 1600 / 0,600,1000,0,0 | 5, 6 / Z3 | 5 / 150 | mixed / Pass | Tempo / Race Pace (Z3) |
| TR-SWIM-011 / 15 | Race pace blokken | 2600 / 0,600,2000,0,0 | 5, 6 / Z3 | 10 / 300 | mixed / Pass | Tempo / Race Pace (Z3) |
| TR-SWIM-012 / 16 | Lange interval | 2600 / 0,600,0,2000,0 | 7, 8 / Z4 | 5 / 300 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-SWIM-013 / 17 | Lange interval | 2600 / 0,600,0,2000,0 | 7, 8 / Z4 | 4 / 240 | mixed / Pass | Anaerobe Drempel (Z4) |
| TR-SWIM-014 / 18 | Piramide interval | 3000 / 0,500,2500,0,0 | 5, 6 / Z3 | 8 / 240 | mixed / Pass | Sweet Spot / Tempo (Z3) |
| TR-SWIM-015 / 19 | Snelheid | 1600 / 0,300,300,0,1000 | 9, 10 / Z5 | 10 / 300 | mixed / Pass | VO2max Snelheid (Z5) |
| TR-SWIM-016 / 20 | Snelheid | 2100 / 0,300,300,0,1500 | 9, 10 / Z5 | 15 / 450 | mixed / Pass | VO2max Snelheid (Z5) |
| TR-SWIM-017 / 21 | Snelheid | 2600 / 0,300,300,0,2000 | 9, 10 / Z5 | 20 / 600 | mixed / Pass | VO2max Snelheid (Z5) |
| TR-SWIM-018 / 22 | Weerstand | 1600 / 0,300,300,0,1000 | 9, 10 / Z5 | 10 / 150 | mixed / Pass | VO2max Weerstand (Z5) |
| TR-SWIM-019 / 23 | Weerstand | 2100 / 0,300,300,0,1500 | 9, 10 / Z5 | 15 / 225 | mixed / Pass | VO2max Weerstand (Z5) |
| TR-SWIM-020 / 24 | Weerstand | 2600 / 0,300,300,0,2000 | 9, 10 / Z5 | 20 / 300 | mixed / Pass | VO2max Weerstand (Z5) |

Exactly nine rows (001–009) are single-zone Z2, continuous distance prescriptions,
1,000–5,000 m in 500 m increments, with no explicit rests. Eleven (010–020) are
mixed. Rows 010/011/014 combine Z2/Z3, 012/013 Z2/Z4, and 015–020 Z2/Z3/Z5.
No source Z1 swimming distance occurs in this workbook.

## Original ordered strings

These are source strings, not rewritten instructions. Every rest remains in its
original position, including the final rest before cooldown where supplied.
No extra recovery, warm-up, rest or cooldown is inferred.

| ID | Original ordered interval string |
| --- | --- |
| TR-SWIM-001 | 1000m Z2 |
| TR-SWIM-002 | 1500m Z2 |
| TR-SWIM-003 | 2000m Z2 |
| TR-SWIM-004 | 2500m Z2 |
| TR-SWIM-005 | 3000m Z2 |
| TR-SWIM-006 | 3500m Z2 |
| TR-SWIM-007 | 4000m Z2 |
| TR-SWIM-008 | 4500m Z2 |
| TR-SWIM-009 | 5000m Z2 |
| TR-SWIM-010 | 300m Z2 \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 300m Z2 |
| TR-SWIM-011 | 300m Z2 \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 300m Z2 |
| TR-SWIM-012 | 300m Z2 \| 400m Z4 \| 60s Rust \| 400m Z4 \| 60s Rust \| 400m Z4 \| 60s Rust \| 400m Z4 \| 60s Rust \| 400m Z4 \| 60s Rust \| 300m Z2 |
| TR-SWIM-013 | 300m Z2 \| 500m Z4 \| 60s Rust \| 500m Z4 \| 60s Rust \| 500m Z4 \| 60s Rust \| 500m Z4 \| 60s Rust \| 300m Z2 |
| TR-SWIM-014 | 300m Z2 \| 100m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 300m Z3 \| 30s Rust \| 400m Z3 \| 30s Rust \| 500m Z3 \| 30s Rust \| 400m Z3 \| 30s Rust \| 300m Z3 \| 30s Rust \| 200m Z3 \| 30s Rust \| 100m Z3 \| 200m Z2 |
| TR-SWIM-015 | 300m Z3 \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 300m Z2 |
| TR-SWIM-016 | 300m Z3 \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 300m Z2 |
| TR-SWIM-017 | 300m Z3 \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 100m Z5 \| 30s Rust \| 300m Z2 |
| TR-SWIM-018 | 300m Z3 \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 300m Z2 |
| TR-SWIM-019 | 300m Z3 \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 300m Z2 |
| TR-SWIM-020 | 300m Z3 \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 100m Z5 \| 15s Rust \| 300m Z2 |

TR-SWIM-012 and 013 share 2,600 m, zone totals, focus and source load but have
5×400 m with five 60 s rests versus 4×500 m with four 60 s rests. They are distinct
prescriptions. Likewise 015/018, 016/019 and 017/020 share swimming distances/zones
and TSS but use 30 s versus 15 s rests. A TSS/zone-total match must not deduplicate
these source IDs or erase execution differences.

## Existing catalog: active and historical inspection

The accepted active projection contains 56 swimming templates: 54 source-v2 rows
`SWI-007`–`SWI-060` and two built-ins. All 54 original source-v1 payload rows were
inspected too; migration `20260929210000` clones their ordered execution/load
into v2 and changes selection metadata while preserving v1. All current/historical
swim built-ins in `CURRENT_CATALOG` were also inspected:

| Template / retained version | Original prescription | Current projected P / historical stored lineage | Selection/guidance |
| --- | --- | --- | --- |
| Technique foundation v1 | 1600 m, 40 min; 400 Z1, 800 Z2, 400 Z2, technique flags | Legacy midpoint-hours 1.666666… retained historically; superseded | RPE 2–3; pace; base/recovery; incompatible fallback |
| Aerobic swim v2 | 1600 m, 40 min; 400 Z1, 800 Z2, 400 Z1 | Current zone-minute P 23.40; original template load 2 under its older method remains historical | RPE 2–4; pace; low; base/recovery |
| Threshold repeats v1 | 2000 m, 50 min; 400 Z2, 1200 Z4, 400 Z1 | Current zone-minute P 54.90; original midpoint-hours 4.166666… retains its method | RPE 2–8; pace; high; build |

None of the 54 old source templates has an explicit stationary-rest segment in
its structured prescription or an explicit rest mention in the inspected payload.
This does not establish that athletes never rested. Each old distance-only source
P is retained in immutable source records, but `with_current_load` yields None in
the current planning projection. Its original RPE ranges span its segment targets,
not the new workbook's narrower session-focus pair. Source-v2 phase tags are
build-only if any execution zone exceeds Z2, otherwise base/build/recovery/taper;
old source capability list is empty and ordinary selection is enabled. These
existing metadata approvals do not transfer automatically to new TR-SWIM IDs.

Exact ordered distance/zone/rest signatures, swimming-only signatures, coalesced
adjacent equal-zone signatures and zone-distance allocations were compared for
every new row against all 56 current templates and historical built-ins. V1 source
execution is identical to its preserved v2 successor. **No exact/coalesced
execution or zone-allocation equivalence exists for any of the 20 new rows.**
Total-distance overlaps below are only candidates for human comparison; their
loads, ordered zones, RPE and rest semantics differ. All 20 IDs are new and have
no collision with old SWI IDs. No replacement mapping, retirement or ID reuse is
approved. No current or historical template was deleted or rewritten.

| New ID | Total-distance overlap only | Old equal-distance source P values (not current usable P) | New source P | Execution / zone allocation |
| --- | --- | --- | --- | --- |
| TR-SWIM-001 | SWI-043, SWI-044, SWI-046, SWI-048, SWI-049, SWI-050 | 11, 19 | 14.4 | No match / no match |
| TR-SWIM-002 | SWI-025, SWI-026, SWI-027, SWI-041, SWI-042 | 18, 19 | 21.6 | No match / no match |
| TR-SWIM-003 | SWI-009, SWI-011, SWI-014, SWI-018, SWI-020, SWI-022, SWI-024, SWI-028, SWI-029, SWI-030, Threshold repeats | 21, 27, 39 | 28.8 | No match / no match |
| TR-SWIM-004 | SWI-007, SWI-008, SWI-013, SWI-015, SWI-016, SWI-017, SWI-019, SWI-021, SWI-023 | 28, 53 | 36 | No match / no match |
| TR-SWIM-005 | SWI-010, SWI-012 | 35 | 43.2 | No match / no match |
| TR-SWIM-006 | none | none | 50.4 | No match / no match |
| TR-SWIM-007 | SWI-051, SWI-056, SWI-060 | 49, 71, 88 | 57.6 | No match / no match |
| TR-SWIM-008 | SWI-054, SWI-059 | 60, 80 | 64.8 | No match / no match |
| TR-SWIM-009 | SWI-052, SWI-057 | 63, 91 | 72 | No match / no match |
| TR-SWIM-010 | Aerobic swim | none | 28.4 | No match / no match |
| TR-SWIM-011 | none | none | 48.2 | No match / no match |
| TR-SWIM-012 | none | none | 56.6 | No match / no match |
| TR-SWIM-013 | none | none | 56.6 | No match / no match |
| TR-SWIM-014 | SWI-010, SWI-012 | 35 | 56.7 | No match / no match |
| TR-SWIM-015 | Aerobic swim | none | 37.3 | No match / no match |
| TR-SWIM-016 | none | none | 50.8 | No match / no match |
| TR-SWIM-017 | none | none | 64.3 | No match / no match |
| TR-SWIM-018 | Aerobic swim | none | 37.3 | No match / no match |
| TR-SWIM-019 | none | none | 50.8 | No match / no match |
| TR-SWIM-020 | none | none | 64.3 | No match / no match |

## Selection proposal for Joren review

The workbook supplies no phase tags, whole-workout low/high bucket, capability/
fallback rules, auto/explicit flag, repeat policy, stable catalog revision or
per-segment RPE target. Names, Expected Zone and focus alone do not authorize
normalization. The following is a concrete **proposal**, not source metadata:

| IDs | Proposed whole-workout bucket | Proposed phase scope under unchanged filters | Proposed execution capability / selection |
| --- | --- | --- | --- |
| TR-SWIM-001 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-002 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-003 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-004 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-005 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-006 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-007 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-008 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-009 | low | base, build, recovery, taper | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-010 | high | build | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-011 | high | build | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-012 | high | build | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-013 | high | build | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-014 | high | build | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-015 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-016 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-017 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-018 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-019 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |
| TR-SWIM-020 | high | build; Z5 only in build position 4 | confirmed swim pace/CSS; HR fallback incompatible; automatic/swipe only after method approval |

This proposal classifies mixed sessions using their complete reviewed prescription
including high work, not a distance-dominance shortcut. It needs explicit Joren
acceptance (C02). Repeats would use the existing maximum 24 occurrences, separate
occurrence IDs and fixed-draft constraints, with no new per-row physiological cap.
High swim spacing remains 48 elapsed hours, available dates remain authoritative,
and injury/low-only restrictions keep precedence. Date availability supplies no
per-day minute budget; rest seconds do not establish total swimming time. Low-
only base/recovery/taper still excludes any Z3+ prescription. Z5 is excluded in
build 1–3 by the current engine regardless of the proposed row metadata.

For mixed rows, source session RPE does not prescribe Z2/Z3 recovery blocks;
current aggregate range validation would reject a scalar outside the session
range. For stationary rests, current WorkoutSegment requires one zone/protocol/
RPE target and a distance or duration; a faithful unzoned rest is not supported.
Assigning Z1, fake distance, or fabricated exertion would corrupt the source.
A future explicit ordered rest representation and guidance mapping are required.
No schema/API/domain change was made to solve this in the review.

## Verification and deferred gates

All original bytes were hashed before/after reading; all XML parts, all rows,
full interval strings and formula/number-format presence were inspected. Both
PDF pages were text-extracted and visually reviewed via rendered PNGs. Existing
MiKTeX Poppler wrappers required unfinished setup; existing local PyMuPDF was
reused instead, without installing anything. Source arithmetic was independently
checked with Decimal and exact rational pace-derived comparisons. All-20 v2
negative cases, current/historical catalog comparisons, 20 planner calls and four
weekly registration/next-target cases ran against the accepted source.

Focused backend command (from `backend`, existing virtualenv):

```text
python -B -m pytest -q -p no:cacheprovider tests/test_workout_catalog.py tests/test_workout_catalog_seed_parity.py tests/test_workout_catalog_repository.py tests/test_training_source_catalog_audit.py tests/test_source_catalog_import_migration.py tests/test_realized_v2_catalog.py tests/test_realized_context.py tests/test_realized_v2_planning.py tests/test_realized_v2_migration.py tests/test_planning_domain.py tests/test_contracts.py tests/test_a9_planning_parity.py tests/physiology/test_joren.py tests/physiology/test_rpe_zones.py tests/physiology/test_realized_v2.py tests/physiology/test_weekly_registration.py
```

**395 passed, one existing Starlette/httpx deprecation warning, 33.94 seconds.**
This includes unchanged A9 parity/intermediate fingerprints and ten adjacent
historical weeks, v2 hierarchy/completeness, privacy/OpenAPI, catalog and migration
static contracts. These old-catalog regression fixtures are not a simulation of
the new combined catalog. Previous running review's 1,013-test full suite and
Ruff/format/strict-mypy results remain historical results at the same source SHA.
No application/type changes warrant a new mobile, full-suite or typecheck claim.
Document links, counts, hashes, whitespace and unchanged application diff are
checked separately. PostgreSQL/pgTAP remains **DEFERRED BY OWNER — PRE-BETA**;
real-token/device, actual storage/concurrency, scientific/release and deployed
performance gates remain open. No database tooling was installed.

The [TSS reconciliation](JOREN_SWIMMING_TSS_RECONCILIATION.md),
[V2 eligibility](JOREN_SWIMMING_REALIZED_V2_ELIGIBILITY.md),
[unified decisions](JOREN_THREE_SPORT_CATALOG_DECISION_REGISTER.md) and
[import readiness](JOREN_THREE_SPORT_CATALOG_IMPORT_READINESS.md) record unresolved
integration choices without reopening source facts established by the PDF.
