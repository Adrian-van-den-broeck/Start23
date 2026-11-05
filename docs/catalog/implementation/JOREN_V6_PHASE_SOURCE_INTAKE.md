# V6 phase source intake

2026-11-05, Europe/Amsterdam. Decision `joren-v6-phase-tss-owner-intake-1`;
adapter `joren-v6-shared-strings-phase-adapter-1`;
release `joren-v6-phase-source-release-1`. Private backend review material.

## Custody

Located originals, read-only, in
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-partial-approval/docs/trainings`.
Byte-identical custody copies are in `docs/catalog/sources/joren-v6-phase-1`.
No workbook was opened for writing, recalculated or resaved. Historical source
archives, C1/C2/C2.1 overlays, V6 artifacts and earlier approval reports are retained.

| Sport | Exact filename | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| RUN | Looptrainingen_Definitief_v6 (1) (1).xlsx | 11912 | `7380c88ef8bccb3cb35b0f6416d9debba8342b9802fc716f0a99dcfcb8626d88` |
| BIKE | Fietstrainingen_Definitief_v6 (1) (1).xlsx | 12772 | `6322d7f93b3e074c77c4efa28b2a95de3f04f0f5c6af226ce50e8c2ff716ddbc` |
| SWIM | Zwemtrainingen_Definitief_v6 (2) (1).xlsx | 12387 | `48a0f6448f003ef048f40e53fda74b5220f272ebd4300180c108777c6e0be3ba` |

Immediate historical V6 source hashes remain RUN
`f9efc53405ae80ea06b7c4f45c288d77e0572aabe0309ef17d29336562a5c46c`, BIKE
`e291a6e40b193d279e1371032242972f4f940454b544832e04087aec6fec4b95`, SWIM
`acd05e0d02664a09320fc70a4519d518fb0103a34801823d04de1ac929c96348`.

## A:O preservation finding

All 77 IDs, row order, titles, source RPE, focus, zone quantities, total measures
and exact ordered interval/rest strings retain their values. Numeric cells compare
as exact Decimals, text as exact decoded strings. There is **one qualification to
the intake assertion of identical A:O values**: eight M-column stored numerical
lexemes changed during the supplied export. Their displayed values are equal;
their exact stored numbers are not. Neither representation is silently replaced.

| Sport / ID | Cell | Historical exact lexeme | New exact lexeme |
| --- | --- | --- | --- |
| RUN-017 | M21 | 87.59999999999999 | 87.6 |
| RUN-022 | M26 | 8.699999999999999 | 8.7 |
| BIKE-004 | M8 | 84.40000000000001 | 84.4 |
| BIKE-021 | M25 | 96.09999999999999 | 96.1 |
| SWIM-008 | M12 | 75.90000000000001 | 75.9 |
| SWIM-009 | M13 | 84.40000000000001 | 84.4 |
| SWIM-017 | M21 | 69.59999999999999 | 69.6 |
| SWIM-020 | M24 | 69.59999999999999 | 69.6 |

The adapter permits only these exact hash-bound pairs; it introduces no epsilon,
generic rounding acceptance or choice of official load. Any other A:O value
change rejects. The artifact retains complete original and new cells, numeric
lexemes, XML, formatting and lineage independently. Original numeric `1` versus
new `1.0` also remains recorded despite exact numeric equality.

## Strict phase adapter

The new export uses shared strings and lacks an OOXML dimension element. The
historical C1 reader is unchanged. A separately versioned reader verifies all
three archive hashes/lengths before parsing, retains full shared-string cell text
and XML, and validates every required A:P workout coordinate. Extra populated
rows, missing rows/cells, duplicate coordinates/IDs, changed IDs/order, conflicting
source specs, formulas and unsupported cells reject. Exported empty formatting
cells P32 in BIKE and P27:P32 in SWIM are preserved as non-workout cells.

P4 must equal the exact string `Trainingsfase `, including its trailing space.
P5 onward is **phase metadata**, unrelated to the internal planned-load symbol P.
Comma-separated `Base`, `Build`, `Recovery`, `Taper` labels normalize after trimming
token whitespace into the canonical typed order Base/Build/Recovery/Taper. Unknown,
missing, empty-token and duplicate labels reject. Original text remains untouched.
No title, RPE, intensity, duration or load infers a phase.

| Phase | RUN | BIKE | SWIM |
| --- | ---: | ---: | ---: |
| Base | 22 | 23 | 16 |
| Build | 22 | 27 | 22 |
| Recovery | 18 | 13 | 8 |
| Taper | 18 | 19 | 8 |

These Joren-supplied labels supersede the unapproved historical phase proposals
only for this new inactive revision. TR-BIKE-013 includes Taper and retains 420
minutes; individual duration suitability is unresolved. TR-RUN-021 through 024
allow Recovery/Taper only. TR-RUN-017/018 are Base only despite containing HIGH
intervals; source phase permission does not waive the per-sport weekly maximum or
any independently approved occurrence restriction. No label is corrected.

## Identity and complete custody artifact

Logical keys retain the existing C1 UUID5 mapping. New revision UUIDs use the
existing `uuid5(key, source-sha256:{hash}|template-version:{version})` convention.
Each version increments its immediate V6 predecessor once. RUN-001:020 and
BIKE-001:021 become v3, SWIM-001:020 become v4; new V6 RUN-021:028,
BIKE-022:027 and SWIM-021:022 become v2. All prior IDs remain unchanged.
Accepted historical-active replacement mapping remains unestablished; no active
catalog entry, duplicate active logical key, retirement or historical update is emitted.

[catalog.json](phase-tss/catalog.json) contains all 77 exact logical/revision UUIDs,
source rows, phase cells, predecessor revisions, complete ordered timed/distance/
stationary-rest events, raw source RPE/focus and independent calculation evidence.
It is an immutable private preparation payload, not executable SQL or public JSON.
The [integration report](JOREN_V6_C3_C5_INTEGRATION_REPORT.md) records verification
and exact local delivery commits.

## Exact 77-row phase ledger

Full UUIDs, raw cells and event order remain in the linked artifact.

| Source ID | Excel row | Source document | New version | Canonical phases |
| --- | ---: | --- | ---: | --- |
| TR-RUN-001 | 5 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-002 | 6 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-003 | 7 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-004 | 8 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-005 | 9 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-006 | 10 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-007 | 11 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-008 | 12 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-009 | 13 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-010 | 14 | run phase-1 | 3 | base, build, recovery, taper |
| TR-RUN-011 | 15 | run phase-1 | 3 | base, build |
| TR-RUN-012 | 16 | run phase-1 | 3 | base, build |
| TR-RUN-013 | 17 | run phase-1 | 3 | base, build |
| TR-RUN-014 | 18 | run phase-1 | 3 | base, build |
| TR-RUN-015 | 19 | run phase-1 | 3 | base, build |
| TR-RUN-016 | 20 | run phase-1 | 3 | base, build |
| TR-RUN-017 | 21 | run phase-1 | 3 | base |
| TR-RUN-018 | 22 | run phase-1 | 3 | base |
| TR-RUN-019 | 23 | run phase-1 | 3 | build |
| TR-RUN-020 | 24 | run phase-1 | 3 | build |
| TR-RUN-021 | 25 | run phase-1 | 2 | recovery, taper |
| TR-RUN-022 | 26 | run phase-1 | 2 | recovery, taper |
| TR-RUN-023 | 27 | run phase-1 | 2 | recovery, taper |
| TR-RUN-024 | 28 | run phase-1 | 2 | recovery, taper |
| TR-RUN-025 | 29 | run phase-1 | 2 | base, build, recovery, taper |
| TR-RUN-026 | 30 | run phase-1 | 2 | base, build, recovery, taper |
| TR-RUN-027 | 31 | run phase-1 | 2 | base, build, recovery, taper |
| TR-RUN-028 | 32 | run phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-001 | 5 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-002 | 6 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-003 | 7 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-004 | 8 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-005 | 9 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-006 | 10 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-007 | 11 | bike phase-1 | 3 | base, build, recovery, taper |
| TR-BIKE-008 | 12 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-009 | 13 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-010 | 14 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-011 | 15 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-012 | 16 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-013 | 17 | bike phase-1 | 3 | base, build, taper |
| TR-BIKE-014 | 18 | bike phase-1 | 3 | base, build |
| TR-BIKE-015 | 19 | bike phase-1 | 3 | base, build |
| TR-BIKE-016 | 20 | bike phase-1 | 3 | base, build |
| TR-BIKE-017 | 21 | bike phase-1 | 3 | base, build |
| TR-BIKE-018 | 22 | bike phase-1 | 3 | build |
| TR-BIKE-019 | 23 | bike phase-1 | 3 | build |
| TR-BIKE-020 | 24 | bike phase-1 | 3 | build |
| TR-BIKE-021 | 25 | bike phase-1 | 3 | build |
| TR-BIKE-022 | 26 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-023 | 27 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-024 | 28 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-025 | 29 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-026 | 30 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-BIKE-027 | 31 | bike phase-1 | 2 | base, build, recovery, taper |
| TR-SWIM-001 | 5 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-002 | 6 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-003 | 7 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-004 | 8 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-005 | 9 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-006 | 10 | swim phase-1 | 4 | base, build, recovery, taper |
| TR-SWIM-007 | 11 | swim phase-1 | 4 | base, build |
| TR-SWIM-008 | 12 | swim phase-1 | 4 | base, build |
| TR-SWIM-009 | 13 | swim phase-1 | 4 | base, build |
| TR-SWIM-010 | 14 | swim phase-1 | 4 | base, build |
| TR-SWIM-011 | 15 | swim phase-1 | 4 | base, build |
| TR-SWIM-012 | 16 | swim phase-1 | 4 | base, build |
| TR-SWIM-013 | 17 | swim phase-1 | 4 | base, build |
| TR-SWIM-014 | 18 | swim phase-1 | 4 | base, build |
| TR-SWIM-015 | 19 | swim phase-1 | 4 | build |
| TR-SWIM-016 | 20 | swim phase-1 | 4 | build |
| TR-SWIM-017 | 21 | swim phase-1 | 4 | build |
| TR-SWIM-018 | 22 | swim phase-1 | 4 | build |
| TR-SWIM-019 | 23 | swim phase-1 | 4 | build |
| TR-SWIM-020 | 24 | swim phase-1 | 4 | build |
| TR-SWIM-021 | 25 | swim phase-1 | 2 | base, build, recovery, taper |
| TR-SWIM-022 | 26 | swim phase-1 | 2 | base, build, recovery, taper |
