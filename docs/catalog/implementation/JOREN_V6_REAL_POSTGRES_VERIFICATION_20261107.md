# V6 real PostgreSQL verification successor ? 7 November 2026

**WOMBO V6 DATABASE VERIFICATION PARTIAL ? EXACT BLOCKERS DOCUMENTED**

Branch `verify/joren-v6-postgres-rls-20261107`, isolated from exact base
`45b8bb8deb6a7c30e224a9472a28345940141f35`. This supersedes the earlier reports'
?database environment unavailable? status without rewriting their historical evidence.
The delivery commit is recorded in `postgres-verification-20261107/delivery.json`.

## Executed environment and migration results

A real workspace-local PostgreSQL **17.11** (Windows x64, MSVC 19.44.35229)
served only `127.0.0.1:55432`. pgTAP **1.3.4** and portable PostgREST **16.5**
provided SQL tests and real signed-token HTTP checks. No system installation,
Windows service, Docker/WSL installation, remote database or real athlete data was used.
The auth/storage SQL prerequisite subset is documented in the [setup report](JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md).
This is a stock PostgreSQL/Supabase-compatible SQL harness, not a full Supabase stack.

**EXECUTED/PASS:** all **59** project migrations applied, transactionally and in
filename order, to the new `wombo_v6_final_gate_20261107` database. The exact
[ordered migration ledger and file hashes](postgres-verification-20261107/migration-ledger.json)
include all four `20261103` Realized V2 prerequisites, then the unchanged:

- `20261105120000_inactive_v6_persistence.sql`
- `20261105120100_inactive_v6_catalog.sql`

Five new forward corrections follow them:

| Migration | Defect demonstrated by real execution |
| --- | --- |
| `20261107182000_v6_segment_snapshot_compatibility.sql` | Historical segment trigger replaced V6 segments with NULL, violating the planned-workout NOT NULL constraint. |
| `20261107182500_v6_frozen_snapshot_operator_precedence.sql` | First pending edit evaluated `unknown - unknown` (42725) before JSON extraction. |
| `20261107183000_realized_v2_internal_approval_custody.sql` | Authenticated owner approval reached nested service-only history guards and failed 42501. Direct EXECUTE grants and ownership checks remain protected. |
| `20261107183500_realized_v2_business_conflict_codes.sql` | Four deterministic V2 business guards used retryable 40001 instead of the established PT409 contract. Guards and calculations are unchanged. |
| `20261107184500_v6_insert_custody.sql` | A real authenticated SQL owner could spoof `critical_write` and append a workout to a confirmed V6 snapshot. New revision/workout insert custody closes this path. |

No original migration was edited, including the two previously unexecuted V6
candidates. Their original versioned evidence remains in the base commit. All
77 revisions remain INACTIVE. Historical catalog/load rows compare exactly with
the snapshot taken before V6: **325 rows retained**, no replacement or recalculation.

The V6 adapter also needed the existing V2 empty-history evidence default. Its
new regression failed before the one-line fix. The SQL runner needed explicit
UTF-8 on Windows; default pipe decoding corrupted non-ASCII source text. Race
barriers now hold both validated requests before competing writes, rather than
allowing confirmation to finish before the edit reaches SQL.

## pgTAP and security results

**EXECUTED/PASS:** 32 of 33 complete suites. **624 assertions observed: 623 passed,
1 failed**; the failing suite then aborts, leaving later A5 assertions NOT EXECUTED.
The V6 persistence/security suite passes 21/21; added segment, approval-custody
and insert-custody suites pass 3/3, 4/4 and 3/3. Realized V2 passes 22/22.
See the [per-suite results](postgres-verification-20261107/pgtap-final-results.json).

**EXECUTED/FAIL:** unchanged `wombo_a5_checkin_proposal_recovery_test.sql`:
assertion 6 expects its synthetic attachment PT409 but gets 23514, ?current
onboarding completion is required for planning.? It then aborts during normal
creation. The same failure was reproduced on the historical prerequisite database
**before either V6 migration**. The fixture does not establish current onboarding.
No A5/A6 file, eligibility guard or release worktree was changed to hide this failure.

Four Realized V2 pgTAP schema checks needed the unambiguous three-argument
`has_table(schema, table, description)` overload, and its suite now sets its own
extension search path. Four Phase 5 assertions retain their original historical
325-row scope by excluding the new inactive archive. The R6 exact inventory now
includes its eight later A5/V2/V6 additions; no original conflict guard was removed.

## Remaining evidence and isolation

[Transactions](JOREN_V6_REAL_TRANSACTION_VERIFICATION_20261107.md),
[signed tokens](JOREN_V6_SIGNED_TOKEN_ISOLATION_20261107.md),
[exact numerical persistence](JOREN_V6_EXACT_DECIMAL_PERSISTENCE_20261107.md),
and [rollback](JOREN_V6_REAL_ROLLBACK_REHEARSAL_20261107.md) have actual executed results.

Complete backend: **2,586 passed**, one existing Starlette/httpx warning.
Ruff passes; 210 files pass formatting. Strict mypy passes 205 app/test/benchmark
sources and all three SQL/HTTP runners. All 40 unchanged historical cases and
26 accepted reference completions are byte-identical; SHA-256
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.
The sole `current:build_4` diagnostic timeout and its eight-second bound remain unchanged.

Production/staging untouched. No push, merge, deployment, activation, mobile work,
planner selection redesign, official-method change or A5/A6 release change.
The source worktree remains clean at the requested base; A5/A6 remains clean at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`.

The final assembled runner was rerun successfully in
`wombo_v6_final_repeatable_20261107`, including all three actual composite-FK
rollback probes. The 99 persistence regressions pass. Test setup now reverses
and reapplies the actual race winner through authoritative alternatives, avoiding
legitimate exhaustion of an unrelated hardcoded sport. Both disposable server
processes were stopped after verification; their data and private transcripts
remain ignored under this worktree runtime directory.
