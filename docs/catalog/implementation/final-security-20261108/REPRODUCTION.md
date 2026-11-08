# Local reproduction and evidence custody

Use the isolated branch `verify/joren-v6-final-auth-security`, starting at
`798e4a00d187474cefe00e8794f04c42422cf72b`. Tested implementation:
`479709f638aa97606bd6226e7b8b44b536b8a2ee`.

The previous [portable setup report](../JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md)
contains the exact PostgreSQL/pgTAP/PostgREST archive hashes and prerequisite
bootstrap provenance. This run reads those binaries from the previous verification
worktree and writes only new data/configuration/logs in this worktree's ignored
`.runtime/final-auth`. It installs no Windows service or system package.

The new cluster was initialized with `initdb -U postgres -A trust --encoding=UTF8
--locale=C` and binds **only `127.0.0.1:55442`**, with Europe/Amsterdam timezone.
Trust authentication is confined to this disposable, synthetic-only cluster.
`pg_ctl` required an approved sandbox escape because Windows restricted-token
startup failed; it starts an ordinary local process, not a service installation.
The runner checks the actual server data directory, loopback address, port and
PostgreSQL major before creating any database. `CREATE DATABASE` fails if its name
already exists. The runner never reads .env, resets a database, drops a database,
or falls back to a hosted target.

From `backend`, with the existing Python environment and the portable psql path:

```powershell
python -B -m scripts.verify_v6_final_sql `
  --execute-disposable-local-only `
  --psql '../../joren-v6-postgres-rls-verification/.runtime/v6-postgres/pgsql/bin/psql.exe' `
  --cluster-directory ../.runtime/final-auth/data --port 55442 `
  --database wombo_v6_final_reproduction_20261108_01 `
  --private-output ../.runtime/NEW_UNIQUE_OUTPUT
```

Use a new lowercase/digit/underscore database name for each reproduction.
The runner applies the stock-PG prerequisite fixture and all ordered migrations,
executes the untouched A5 at the pre-V6 boundary and final schema, then runs every
top-level SQL suite with only the explicit A5 data overlay. It validates complete
TAP plans, sequential assertion numbers and each actual assertion status. A
separate `--historical-only` run creates the independent 52-migration baseline.
No deployable migration contains the synthetic onboarding correction.

The final complete-chain database is
`wombo_v6_final_security_verified_20261108`. Its 59-file execution ledger is
[retained](final-migration-execution.json). The separate historical database is
`wombo_v6_final_historical_20261108`; [52 executions](historical-migration-execution.json).
The lifecycle database is `wombo_v6_final_security_clean_20261108`.
Both are newly created in this task's cluster, not reused/shared environments.
Earlier exploratory `security` and `security_clean` runs remain in ignored local
evidence; they do not replace the final ledgers.

For the lifecycle, put portable `pgsql/bin` on the **process-local** PATH, set
`WOMBO_V6_DISPOSABLE_PG_DSN` to that new database, and use the unchanged runner:

```text
python -B -m scripts.verify_v6_postgres --execute-disposable-local-only --private-output NEW_PRIVATE_DIRECTORY
```

It creates only its two synthetic users and executes separate processes for
create/resume/reload. It checks all 77 numerical/source round trips before the
transaction/concurrency/immutability matrix.

For HTTP, clone the empty fully migrated schema database into a new disposable
database. Apply `v6_persistence_users.sql`, run the existing lifecycle runner's
`--stage create`, and start portable PostgREST on `127.0.0.1:55441`, using a new
ignored random signing secret and its own private config. Set the DSN to that
same HTTP database. Run `verify_v6_commit_loss` before `verify_v6_postgrest` with
their existing `--execute-disposable-local-only`, `--url`,
`--signing-secret-file` and `--private-output` arguments. This run used
`wombo_v6_final_http_20261108`. This is direct PostgREST verification, not a gateway.

For rollback, clone only the completed disposable lifecycle database to a new
name matching `wombo_v6_rollback_<digits>`. Capture retained public reads and
private-table hashes, execute the unchanged disabling fixture, compare retained
data, actually call disabled RPCs, and run every suite with the explicit A5
overlay. Do not apply this fixture to a real Supabase project.

The A5 race run uses the original `verify_a5_local_concurrency.py` source with
two disclosed substitutions in an ignored copy: input fingerprint 64 -> 32,
and, immediately before its `ThreadPoolExecutor`, a query transaction executing
`a5_current_onboarding.sql` with its fixed A5 UUID replaced by that runner's
generated owner UUID. No synchronization or assertion is changed. The copy's
SHA-256 is in [the concurrency record](a5-concurrency.json).

Backend reproduction uses full pytest with no cache provider; Ruff check and
format check across app/tests/benchmarks and the four runners; strict mypy across
app/tests/benchmarks and `--explicit-package-bases` for runners. Full commands
and outcomes are [recorded](backend.json). The unchanged corpus command is:

```text
python -B -m benchmarks.v6_policy_sandbox --regression-output NEW_PRIVATE_JSON
```

All 40 case results and 26 accepted completions compare exactly to prior delivery;
SHA-256 `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.
Its existing eight-second deadline is unmodified. Numerical/planner output stays
in ignored private evidence; committed successor evidence records outcomes/hashes.

The full GoTrue/gateway recipe is separately [NOT EXECUTED](AUTHENTICATION.md).
After evidence capture, stop only the saved PostgREST PID and this exact cluster
directory. Keep the data and private transcripts. New reports/JSON/patches have
explicit LF Git attributes so their recorded SHA-256 identities survive Windows
checkout. The hash manifest excludes itself to avoid a self-referential digest.
