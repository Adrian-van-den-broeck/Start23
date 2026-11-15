# Readiness evidence and reproduction

This directory contains sanitized metadata, synthetic-only hashes/assertions and offline benchmark evidence. No credential, backup or production athlete row is included. The actual hosted write count is zero. The parent [gap analysis](../JOREN_V6_HOSTED_MIGRATION_GAP_ANALYSIS.md) and [verification register](verification.json) define scope and open gates.

## Files and interpretation

- `migration-inventory.json`: exact 16 files/SHA-256, direct declarations, trigger targets, grants/revokes and dynamic effects. The full accepted 63-file manifest and hosted 47-version ledger are in `hosted-before.json`.
- `hosted-before.json` / `hosted-after.json`: equal complete allowlisted preflight metadata/Auth settings. `hosted-detail-final.json` adds actual backup, function fingerprints, dynamic prerequisites, effective privileges/default ACL and role membership metadata. Earlier detail observations are retained for chronology.
- `boundary-d`: exact accepted clean 47-file boundary, persisted synthetic onboarding/historical plan/activity/evidence, then exact G1/G2/G3 upgrade. `boundary-hosted2`: same with the two observed hosted function definitions reproduced locally before generation. These runs do not reproduce full managed services/default ACLs.
- Both boundary folders include complete per-assertion TAP results, the **failing original A5** result, successful corrected-overlay results, six smoke suites after each group, schema snapshots and preservation hashes. The initial 27 current historical-suite attempts contain two final-schema-dependent failures; 25 pass. No failure is relabelled as an assertion pass.
- `activity-compatibility-probe.json`: historical strict-model rejection of an actual post-install synthetic activity response. This is not a deployed-write test.
- `atomic-rollback`, `disable-rehearsal`, `strict-bundle-guard-results.json`, `post-assertion-results.json`: independent transaction rollback, data-preserving generation disable, strict client-EXECUTE refusal and read-only post-assertion evidence. Restoration of a hosted backup did not run.
- `historical*.json`, `oracle*.json`: all 40 results/26 accepted non-timeout reference results and 15-context exhaustive oracle comparisons. Timing fields are not equality requirements; the original eight-second diagnostic deadline is unchanged.
- `lifecycle`, `evidence-rescheduling`, `frequency-checks.json`: nine/eleven/nine real portable SQL/HTTP orchestration groups. They use simulated SQL claims and existing local-only dependencies. Genuine GoTrue hosted evidence remains the earlier accepted report; no new V6 hosted success is inferred.
- `history`: exact previous Dutch release-gates bytes, preserved before replacing the current gate register.

## Existing tools; no Docker

Use the existing backend virtual environment (`F:/Projecten Business/Start23/Code/backend/.venv/Scripts/python.exe`), installed mobile dependencies read through the new worktree's junction, and the existing portable PG17.11 binaries under the protected PostgreSQL-verification worktree. Binaries are read only; **new** data/log/output paths are in this successor's ignored `.runtime/migration-readiness`. Never start/stop or modify an old cluster. The new cluster used only IPv4 loopback port 55442 and its own `pgdata` directory.

Recreate a fresh cluster following the accepted [portable setup](../JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md), substituting a new data directory and unused port. No system install, Docker, global PATH change, hosted .env or production dump is required. Then, from `backend`:

```powershell
$readinessPython = 'F:/Projecten Business/Start23/Code/backend/.venv/Scripts/python.exe'
$readinessPsql = 'F:/Projecten Business/Start23/Code/.worktrees/joren-v6-postgres-rls-verification/.runtime/v6-postgres/pgsql/bin/psql.exe'
& $readinessPython -B -m scripts.rehearse_v6_migration_boundary `
  --execute-disposable-local-only --psql $readinessPsql `
  --cluster-directory ../.runtime/migration-readiness/NEW-pgdata --port 55442 `
  --database wombo_v6_boundary_NEW `
  --hosted-preflight ../docs/catalog/implementation/migration-readiness-20261116/hosted-before.json `
  --private-output ../.runtime/migration-readiness/NEW-boundary
# Repeat with another NEW database/output and:
# --reproduce-hosted-drift ../docs/catalog/implementation/migration-readiness-20261116/hosted-detail-final.json
```

Use lowercase actual database suffixes matching the runner's guard. The literal `NEW` above is a placeholder for a unique lowercase suffix, not an existing target. Failed runs are preserved; the runner never resets/reuses an existing database.

For independent lifecycle/evidence/frequency runners, first use accepted `scripts.verify_v6_final_sql` to create a **new empty-user fully migrated database** and pass all 37 TAP suites. Create three new synthetic-only template clones from that empty database, one for each runner. This avoids clearing any existing accounts. Set process-local `PATH` to the portable bin and `WOMBO_V6_DISPOSABLE_PG_DSN` to each exact new loopback database, then run:

```powershell
python -B -m scripts.verify_v6_lifecycle_completion --execute-disposable-local-only --private-output <new-private-lifecycle-directory>
python -B -m scripts.verify_v6_evidence_rescheduling --execute-disposable-local-only --output <new-private-evidence-directory>
python -B -m scripts.verify_v6_frequency_policy --execute-disposable-local-only --private-output <new-private-frequency-file.json>
```

The last two runners enforce their own fixture preconditions. Do not point them at a hosted URL or production-tunnel alias. They automatically test new-process recovery. No genuine reviewer or individual REAL maximum is issued by the frequency runner.

## Recovery proof reproduction

Clone only a database created by the above local run; verify loopback server/data-directory identity before DDL. To reproduce atomic rollback, use the same ordered 11 G2 bodies inside one transaction, inject a deliberate exception immediately before COMMIT, then compare `metadata()`/`snapshots()` from `rehearse_v6_migration_boundary` in a **new** psql connection. Every 51-table hash and function/constraint/policy snapshot must equal the pre-G2 values. Retain failure transcript; no down migration is used.

For generation disable, clone the completed local evidence-rescheduling database to a new `wombo_v6_rollback_<digits>` database. Record all 64 table hashes and the owned confirmed `get_v6_mobile_weekly_plan` projection. Apply only `supabase/tests/fixtures/v6_readiness_forward_disable.sql` to this clone. Compare hashes/projection from new connections; test service calls to the revoked V6/frequency/move/catalog RPCs for 42501, and attempt a synthetic new V6 revision insert for PT409 from the persistence guard. Re-run historical Phase-6/7/8 and the explicit A5-overlay suites. Do not run V6 generation-success tests after intentionally disabling generation. This fixture rejects hosted/non-loopback database names and is not a production migration.

For strict bundle refusal, prepare bundles offline. In a new synthetic boundary clone, create a local test migration ledger for the 47 already executed source files. Substitute only those **local fixture** statement fingerprints in a copy of G1's review SQL. Its new authenticated RPC must trigger the permission exception; a fresh connection must find ledger count 47 and no A5 RPC. Never substitute live fingerprints to suppress real drift. The committed report clearly distinguishes this test adaptation from the unchanged exact migration bodies.

## Routine regression commands

From `backend`: `python -m pytest -q`; `python -m ruff check .`; `python -m ruff format --check .`; `python -m mypy --strict app tests benchmarks`; strict explicit-package-bases mypy on the three new readiness scripts. From `mobile`: installed Jest with runInBand and cache/output under this worktree; installed TypeScript with `--noEmit --strict --noUnusedLocals --noUnusedParameters`.

Run serial benchmark commands after CPU-heavy tests: `python -B -m benchmarks.v6_planner_performance --variant optimized --output <new.json>` and `python -B -m benchmarks.v6_search_oracle --output <new.json>`. Compare full case results/output hashes and independent checks with the accepted hosted-auth corpus, plus all 26 non-timeout cases from `build-search/accepted_cold.json`; compare non-timing oracle fields. Do not relax the eight-second or search-node bounds.

The wrong system-Python collection attempt and early seed/separator harness corrections are recorded in `verification.json`; fresh corrected runs provide the passing evidence. Ruff/style mistakes were corrected without application changes. No disposable fixture or production migration was executed hosted.
