# Joren V6 source differences and immutable lineage

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

The actual originals were found at `F:/Projecten Business/Start23/Code/docs/trainings`.
Their hashes were checked before OOXML parsing. Byte-identical custody copies are
in `docs/catalog/sources`; no workbook was resaved, recalculated or edited.

## Verified inventory

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

## Immediate predecessor and immutable relationships

RUN and BIKE compare to the accepted C1 Optie1 source hashes. SWIM compares to
the **C2 IF² workbook**, not the earlier Optie1 swim workbook. Its six erroneous
ordered blocks are also compared to the approved C2.1 derivative. The original
Optie1 swim/PDF, IF² workbook, corrected overlay, C1 manifest and C2 registry all
remain separate, preserved revisions.

| Sport | Immediate source parent | Parent SHA-256 | Candidate template version |
| --- | --- | --- | --- |
| run | Looptrainingen_Definitief_Optie1.xlsx | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 | 1 -> 2 existing; 1 new |
| bike | Fietstrainingen_Definitief_Optie1.xlsx | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df | 1 -> 2 existing; 1 new |
| swim | Zwemtrainingen_IF2.xlsx | 7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb | 2 -> 3 existing; 1 new |

SWIM template lineage is C1 v1 -> C2 proposed v2 -> V6 proposed v3.
C2.1 is a separately versioned prescription overlay and created no template ID.
The C2 registry retains its unapproved mapping status. V6 preserves logical TR
keys under explicitly new source records; every V6 revision UUID is distinct.
No existing occurrence, source version or template is updated. New rows have no
row predecessor; their containing source document still records its predecessor.
`accepted_predecessor_mapping` remains null: source continuity is not an accepted
replacement/retirement decision for the active catalog.

Deterministic identity remains UUID5 of the C1 `wombo:joren:optie1:{sport}:{TR-id}`
key, then UUID5(key, `source-sha256:{hash}|template-version:{version}`). Titles
never participate. All 77 keys and revision IDs are collision-free against the
336 offline migration UUIDs; revision IDs also differ from all C1/C2 proposed IDs.
Hosted uniqueness remains a later database gate, not queried here.

## All 16 new rows

| ID / row | Title | Source measure | Ordered prescription | Source RPE | Raw source P / display |
| --- | --- | --- | --- | --- | --- |
| TR-RUN-021 / 25 | Herstel 10min lopen in zone 1 | 10 minutes | 10m Z1 | 1, 2 | 5.8 / 5.8 |
| TR-RUN-022 / 26 | Herstel 15min lopen in zone 1 | 15 minutes | 15m Z1 | 1, 2 | 8.699999999999999 / 8.7 |
| TR-RUN-023 / 27 | Herstel 20min lopen in zone 1 | 20 minutes | 20m Z1 | 1, 2 | 11.6 / 11.6 |
| TR-RUN-024 / 28 | Herstel 25min lopen in zone 1 | 25 minutes | 25m Z1 | 1, 2 | 14.5 / 14.5 |
| TR-RUN-025 / 29 | LSD 10 min | 10 minutes | 10m Z2 | 3, 4 | 10.8 / 10.8 |
| TR-RUN-026 / 30 | LSD 15 min | 15 minutes | 15m Z2 | 3, 4 | 16.2 / 16.2 |
| TR-RUN-027 / 31 | LSD 20 min | 20 minutes | 20m Z2 | 3, 4 | 21.6 / 21.6 |
| TR-RUN-028 / 32 | LSD 25 min | 25 minutes | 25m Z2 | 3, 4 | 27 / 27.0 |
| TR-BIKE-022 / 26 | Herstel 30min | 30 minutes | 30m Z1 | 1, 2 | 15.1 / 15.1 |
| TR-BIKE-023 / 27 | Herstel 40min | 40 minutes | 40m Z1 | 1, 2 | 20.2 / 20.2 |
| TR-BIKE-024 / 28 | Herstel 50min | 50 minutes | 50m Z1 | 1, 2 | 25.2 / 25.2 |
| TR-BIKE-025 / 29 | LSD 30 min | 30 minutes | 30m Z2 | 3, 4 | 28.1 / 28.1 |
| TR-BIKE-026 / 30 | LSD 40 min | 40 minutes | 40m Z2 | 3, 4 | 37.5 / 37.5 |
| TR-BIKE-027 / 31 | LSD 50 min | 50 minutes | 50m Z2 | 3, 4 | 46.9 / 46.9 |
| TR-SWIM-021 / 25 | LSD 500m | 500 meters | 500m Z2 | 3, 4 | 8.4 / 8.4 |
| TR-SWIM-022 / 26 | LSD 800m | 800 meters | 800m Z2 | 3, 4 | 13.5 / 13.5 |

## Every changed existing source value

| ID | Cell | Previous | V6 |
| --- | --- | --- | --- |
| TR-RUN-004 | C8 | LSD 30 min lopen in zone 2 | LSD 30 min |
| TR-RUN-005 | C9 | LSD 40 min lopen in zone 2 | LSD 40 min |
| TR-RUN-006 | C10 | LSD 50 min lopen in zone 2 | LSD 50 min |
| TR-RUN-007 | C11 | LSD 60 min lopen in zone 2 | LSD 60 min |
| TR-RUN-008 | C12 | LSD 1u10 lopen in zone 2 | LSD 1u10 |
| TR-RUN-009 | C13 | LSD 1u20 lopen in zone 2 | LSD 1u20 |
| TR-RUN-010 | C14 | LSD 1u30 lopen in zone 2 | LSD 1u30 |
| TR-RUN-011 | C15 | LSD 1u40 lopen in zone 2 | LSD 1u40 |
| TR-RUN-012 | C16 | LSD 1u50 lopen in zone 2 | LSD 1u50 |
| TR-RUN-013 | C17 | LSD 2u00 lopen in zone 2 | LSD 2u00 |
| TR-RUN-014 | C18 | LSD 2u10 lopen in zone 2 | LSD 2u10 |
| TR-RUN-015 | C19 | LSD 2u20 lopen in zone 2 | LSD 2u20 |
| TR-RUN-016 | C20 | LSD 2u30 lopen in zone 2 | LSD 2u30 |
| TR-RUN-017 | C21 | Lange interval | Lange interval 1 |
| TR-RUN-017 | O21 | Anaerobe Drempel (Threshold) | Anaerobe Drempel |
| TR-BIKE-014 | C18 | Lange intervallen | Lange intervallen 4x20m |
| TR-BIKE-015 | C19 | Lange intervallen | Lange intervallen 4x10m |
| TR-BIKE-016 | C20 | Lange intervallen | Lange intervallen 8x10m |
| TR-BIKE-017 | C21 | Lange intervallen | Lange intervallen 4x30m |
| TR-BIKE-020 | C24 | HIIT Sprints | HIIT Sprints 6x30s |
| TR-BIKE-021 | C25 | HIIT Sprints | HIIT Sprints 8x30s |
| TR-SWIM-015 | N19 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |
| TR-SWIM-016 | N20 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |
| TR-SWIM-017 | N21 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |
| TR-SWIM-018 | N22 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |
| TR-SWIM-019 | N23 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |
| TR-SWIM-020 | N24 | 300m Z3 first block; all following tokens retained in full JSON | 300m Z2 first block; all following tokens identical |

There are 27 changed values in 26 existing rows: 20 titles, one focus
description and six ordered first-block corrections. No existing RPE, expected
zone, measure, sport multiplier, zone allocation or raw P cell changes relative
to its immediate source parent. In particular, the revised SWIM source loads are
not incorrectly reported as V6 changes from the older fixed-matrix workbook.

## All unchanged ordered source prescriptions

The following 55 N-cell strings are value-identical to their immediate predecessor.
All 61 existing rows retain A/B/D/E/F/G/H/I/J/K/L/M values. Outside the changed
C/O/N cells listed above, all row values are unchanged. The complete machine
artifact lists every unchanged coordinate and all XML/style/format changes.

| ID / source row | Unchanged exact N value |
| --- | --- |
| TR-RUN-001 / 5 | 30m Z1 |
| TR-RUN-002 / 6 | 40m Z1 |
| TR-RUN-003 / 7 | 50m Z1 |
| TR-RUN-004 / 8 | 30m Z2 |
| TR-RUN-005 / 9 | 40m Z2 |
| TR-RUN-006 / 10 | 50m Z2 |
| TR-RUN-007 / 11 | 60m Z2 |
| TR-RUN-008 / 12 | 70m Z2 |
| TR-RUN-009 / 13 | 80m Z2 |
| TR-RUN-010 / 14 | 90m Z2 |
| TR-RUN-011 / 15 | 100m Z2 |
| TR-RUN-012 / 16 | 110m Z2 |
| TR-RUN-013 / 17 | 120m Z2 |
| TR-RUN-014 / 18 | 130m Z2 |
| TR-RUN-015 / 19 | 140m Z2 |
| TR-RUN-016 / 20 | 150m Z2 |
| TR-RUN-017 / 21 | 10m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 10m Z2 |
| TR-RUN-018 / 22 | 10m Z2 &#124; 5m Z4 &#124; 5m Z2 &#124; 5m Z4 &#124; 5m Z2 &#124; 5m Z4 &#124; 5m Z2 &#124; 5m Z4 &#124; 10m Z2 |
| TR-RUN-019 / 23 | 10m Z2 &#124; 3m Z5 &#124; 10m Z2 &#124; 5m Z5 &#124; 5m Z2 &#124; 7m Z5 &#124; 5m Z2 &#124; 5m Z5 &#124; 5m Z2 &#124; 3m Z5 &#124; 10m Z2 |
| TR-RUN-020 / 24 | 15m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 15m Z2 |
| TR-BIKE-001 / 5 | 60m Z1 |
| TR-BIKE-002 / 6 | 90m Z1 |
| TR-BIKE-003 / 7 | 120m Z1 |
| TR-BIKE-004 / 8 | 90m Z2 |
| TR-BIKE-005 / 9 | 120m Z2 |
| TR-BIKE-006 / 10 | 150m Z2 |
| TR-BIKE-007 / 11 | 180m Z2 |
| TR-BIKE-008 / 12 | 210m Z2 |
| TR-BIKE-009 / 13 | 240m Z2 |
| TR-BIKE-010 / 14 | 300m Z2 |
| TR-BIKE-011 / 15 | 330m Z2 |
| TR-BIKE-012 / 16 | 360m Z2 |
| TR-BIKE-013 / 17 | 420m Z2 |
| TR-BIKE-014 / 18 | 30m Z2 &#124; 20m Z4 &#124; 10m Z2 &#124; 20m Z4 &#124; 10m Z2 &#124; 20m Z4 &#124; 10m Z2 &#124; 20m Z4 &#124; 10m Z2 &#124; 30m Z2 |
| TR-BIKE-015 / 19 | 30m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 30m Z2 |
| TR-BIKE-016 / 20 | 30m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 10m Z4 &#124; 5m Z2 &#124; 30m Z2 |
| TR-BIKE-017 / 21 | 30m Z2 &#124; 30m Z4 &#124; 10m Z2 &#124; 30m Z4 &#124; 10m Z2 &#124; 30m Z4 &#124; 10m Z2 &#124; 30m Z4 &#124; 10m Z2 &#124; 30m Z2 |
| TR-BIKE-018 / 22 | 20m Z2 &#124; 10m Z5 &#124; 10m Z2 &#124; 5m Z5 &#124; 10m Z2 &#124; 20m Z5 &#124; 10m Z2 &#124; 15m Z5 &#124; 10m Z2 &#124; 10m Z5 &#124; 30m Z2 |
| TR-BIKE-019 / 23 | 30m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 8m Z5 &#124; 2m Z2 &#124; 30m Z2 |
| TR-BIKE-020 / 24 | 30m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 15m Z2 &#124; 15m Z1 |
| TR-BIKE-021 / 25 | 30m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 30s Z5 &#124; 5m Z2 &#124; 15m Z2 &#124; 15m Z1 |
| TR-SWIM-001 / 5 | 1000m Z2 |
| TR-SWIM-002 / 6 | 1500m Z2 |
| TR-SWIM-003 / 7 | 2000m Z2 |
| TR-SWIM-004 / 8 | 2500m Z2 |
| TR-SWIM-005 / 9 | 3000m Z2 |
| TR-SWIM-006 / 10 | 3500m Z2 |
| TR-SWIM-007 / 11 | 4000m Z2 |
| TR-SWIM-008 / 12 | 4500m Z2 |
| TR-SWIM-009 / 13 | 5000m Z2 |
| TR-SWIM-010 / 14 | 300m Z2 &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 300m Z2 |
| TR-SWIM-011 / 15 | 300m Z2 &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 300m Z2 |
| TR-SWIM-012 / 16 | 300m Z2 &#124; 400m Z4 &#124; 60s Rust &#124; 400m Z4 &#124; 60s Rust &#124; 400m Z4 &#124; 60s Rust &#124; 400m Z4 &#124; 60s Rust &#124; 400m Z4 &#124; 60s Rust &#124; 300m Z2 |
| TR-SWIM-013 / 17 | 300m Z2 &#124; 500m Z4 &#124; 60s Rust &#124; 500m Z4 &#124; 60s Rust &#124; 500m Z4 &#124; 60s Rust &#124; 500m Z4 &#124; 60s Rust &#124; 300m Z2 |
| TR-SWIM-014 / 18 | 300m Z2 &#124; 100m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 300m Z3 &#124; 30s Rust &#124; 400m Z3 &#124; 30s Rust &#124; 500m Z3 &#124; 30s Rust &#124; 400m Z3 &#124; 30s Rust &#124; 300m Z3 &#124; 30s Rust &#124; 200m Z3 &#124; 30s Rust &#124; 100m Z3 &#124; 200m Z2 |

## Workbook/schema and formatting differences

Complete document/cell records retain type, numeric lexeme, number format,
style index, serialized XML, formula/cache fields, coordinates, sheet name,
visibility and extent. These are preserved alongside source bytes; value equality
does not assert XML/style equality. V6 contains one visible sheet per sport and
no formula cells. RUN/BIKE sheet names lose ` Catalogus`. BIKE F4 changes from
`Totale Duur\n(min)` to `Totale Duur`, and H4:L4 from `Zk\n(min)` to `Zk (min)`.
Source notes now explicitly mention IF² for timed sports. All non-row cell record
differences and exact before/after values are in `source_differences.documents`.
Only this pinned V6 schema is accepted; the historical C1 parser is unchanged.

Exact row lineage, provisional UUIDs/versions, full changed and unchanged values,
all documents/events and arithmetic are in [the immutable private manifest](joren_v6_manifest_v1.json).

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).
