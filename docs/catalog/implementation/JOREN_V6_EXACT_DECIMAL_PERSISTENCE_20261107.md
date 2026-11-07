# V6 exact Decimal persistence ? 7 November 2026

**EXECUTED/PASS on real PostgreSQL 17.11: all 77 official values.**
Official method remains `joren-v6-planned-if2-1`, reference
`joren-v6-approved-if-reference-1`, acceptance `joren-v6-official-tss-acceptance-1`.
No formula, coefficient, selection rule or comparison convention changed.

`verify_numeric_round_trips` in the real database runner independently loads the
hash-pinned workbook catalog and checks every persisted row against it:

- Canonical Decimal strings equal the official final 50-significant-digit HALF_EVEN results.
- Unconstrained PostgreSQL numeric values equal those final Decimals; the stored column has typmod -1.
- Rational numerator and denominator strings, method/reference identifiers, source hashes and INACTIVE status match exactly.
- The tagged durable document, complete source snapshot and public prescription snapshot equal the independently constructed originals. Ordered source events, original workbook cells/lexemes/display and predecessor evidence survive separately.
- PostgreSQL's aggregate equals the exact Python sum of the final official Decimals, preserving operand digits beyond the default 28-digit context.
- A value `45.000000000000000000000000000000000000000000000001` remains strictly over 45 after SQL serialization, storage representation and reload.
- Inserting a numerically mismatched Decimal/numeric pair into the real constrained source table fails with 23514 before a duplicate-key conflict. No fixed-scale rounding was introduced.

The official final Decimal remains the comparison authority; no rational total or
rounded workbook display substitutes for it. Full source comparisons also cover
non-ASCII text, which exposed and motivated the runner's explicit UTF-8 correction.

The before-V6 historical catalog/load snapshot equals the final and rollback
snapshots, retaining all 325 historical template/load rows. The disposable dataset
contains no real athletes or historical activity calculations; no claim is made
about migrating real production history. No migration recalculates Realized V2,
and the complete unchanged Realized V2 backend suite and 22/22 SQL assertions pass.
