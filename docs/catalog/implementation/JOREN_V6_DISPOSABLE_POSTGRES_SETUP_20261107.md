# Disposable PostgreSQL setup and reproduction — 7 November 2026

The workstation inspection found no PostgreSQL, Docker, Podman or Supabase CLI.
WSL2 was present with **no distributions** (confirmed outside the sandbox after
its initial access-denied result). There was no test DSN or database listener on
the inspected standard ports. A workspace-local portable PostgreSQL setup was
the smallest working path; no system installation, service registration,
administrative setting, global PATH change or WSL distribution was needed.

## Actual components and boundaries

| Component | Download and SHA-256 |
| --- | --- |
| PostgreSQL 17.11 Windows x64 | [EDB portable archive](https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip), 381,531,864 bytes; `80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f` |
| pgTAP 1.3.4 | [Official release](https://github.com/theory/pgtap/releases/download/v1.3.4/pgTAP-1.3.4.zip); `5de16455e3e29898813f05cc9f396a31f878309a94d8adb34e80f423a5841736` |
| PostgREST 16.5 Windows x64 | [Official release](https://github.com/PostgREST/postgrest/releases/download/v16.5/postgrest-v16.5-windows-x86-64.zip); `17f595b0d8dd37473d0231417dea07c5ac9f791282ff5b017fae51ff29e5de2f` |

All files were unpacked only under this worktree's ignored `.runtime/v6-postgres`.
PostgREST needs the portable PostgreSQL `bin` directory on its **process-local**
PATH for `libpq.dll`. No DLL or extension was installed into Windows/system paths.

The checked and executed
[`v6_disposable_supabase_bootstrap.sql`](../../../supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql)
contains the required Supabase-compatible SQL subset: auth users/schema/helpers,
anon/authenticated/service/authenticator roles, pgcrypto/uuid-ossp, minimal Storage
schema/folder helper/bucket limits, the documented RLS event trigger and pgTAP.
Its database-name, loopback-address and PostgreSQL-major guards reject other
targets. It is a fresh-database **fixture**, outside the deployable migrations.
It was independently replayed with all 59 migrations in
`wombo_v6_bootstrap_replay_20261107`.

Upstream definitions came from:

- [Supabase auth schema](https://github.com/supabase/postgres/blob/develop/migrations/db/init-scripts/00000000000001-auth-schema.sql), plus the four auth helper migrations from 20211124214934 through 20220531120530 in [Supabase Auth](https://github.com/supabase/auth/tree/master/migrations).
- [Supabase Storage tenant migrations](https://github.com/supabase/storage/tree/master/migrations/tenant): 0002, 0008, 0013 and 0014; storage role installation is disabled because roles/grants are installed explicitly.
- [Supabase RLS event-trigger example](https://supabase.com/docs/guides/database/postgres/event-triggers).

The fixture includes adapted upstream SQL; accompanying PostgreSQL, MIT and
Apache notices are in `supabase/tests/fixtures/licenses`.

The [downloaded-source hash manifest](postgres-verification-20261107/bootstrap-sources.json)
preserves the exact fetched content identities. This does not apply the full old
Supabase initial defaults: no broad public default grants or authenticator
membership in an administrator role were added. The auth/storage service
processes, full extension distribution and hosted advisors are **NOT VERIFIED**.
The test bootstrap is not a substitute for a full Supabase release gate.

## Reproduce without a system installation

Use an ordinary owner PowerShell session in this isolated worktree. Verify the
three archive hashes above after downloading. Keep archives, data, logs and
locally generated signing material under `.runtime`; never copy a hosted .env.
The PostgreSQL project explicitly supports a [Windows binary archive](https://www.postgresql.org/download/windows/).

Extract `pgsql/bin`, `pgsql/lib` and `pgsql/share` from the PostgreSQL zip into
`.runtime/v6-postgres` (the archive contains the `pgsql` directory). Extract
pgTAP into `.runtime/v6-postgres/pgtap` and PostgREST into
`.runtime/v6-postgres/postgrest`. Prepare pgTAP's portable extension exactly as its
Makefile substitutions do:

```powershell
@'
from pathlib import Path
import shutil
p = Path('.runtime/v6-postgres')
src = p / 'pgtap/pgTAP-1.3.4'
dest = p / 'pgsql/share/extension'
sql = (src/'sql/pgtap.sql.in').read_text(encoding='utf-8')
sql = sql.replace('__OS__', 'MSWin32').replace('__VERSION__', '1.3')
sql = sql.replace('MODULE_PATHNAME', 'pgtap')
(dest/'pgtap--1.3.4.sql').write_text(sql, encoding='utf-8')
shutil.copyfile(src/'pgtap.control', dest/'pgtap.control')
'@ | python -B -
```

Create a **new** cluster directory; do not reuse another application's cluster:

```powershell
$v6Runtime = Join-Path (Get-Location) '.runtime/v6-postgres'
$v6Bin = Join-Path $v6Runtime 'pgsql/bin'
$v6Data = Join-Path $v6Runtime 'reproduction-data'
& "$v6Bin/initdb.exe" -D $v6Data -U postgres -A trust --encoding=UTF8 --locale=C
if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
Add-Content (Join-Path $v6Data 'postgresql.conf') @"
listen_addresses = '127.0.0.1'
port = 55432
timezone = 'Europe/Amsterdam'
max_connections = 40
shared_buffers = '64MB'
"@
& "$v6Bin/pg_ctl.exe" -D $v6Data -l "$v6Runtime/reproduction-server.log" -w start
```

Choose a free port if the original verification server is still running. The
cluster uses local trust authentication only for this disposable dataset and
binds exclusively to IPv4 loopback. Inspect its version, address/port and
`SHOW data_directory` before setting the verification DSN. Never use a tunnel.

```powershell
$v6Psql = Join-Path $v6Bin 'psql.exe'
$env:PATH = $v6Bin + ';' + $env:PATH
$env:PGCLIENTENCODING = 'UTF8'
& $v6Psql -X -h 127.0.0.1 -p 55432 -U postgres -d postgres -v ON_ERROR_STOP=1 `
  -c 'select version(),inet_server_addr(),inet_server_port(); show data_directory;'
& $v6Psql -X -h 127.0.0.1 -p 55432 -U postgres -d postgres -v ON_ERROR_STOP=1 `
  -c 'create database wombo_v6_reproduction_20261107'
$env:WOMBO_V6_DISPOSABLE_PG_DSN = 'postgresql://postgres@127.0.0.1:55432/wombo_v6_reproduction_20261107'
& $v6Psql -X -v ON_ERROR_STOP=1 -1 -d $env:WOMBO_V6_DISPOSABLE_PG_DSN `
  -f supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql
foreach ($v6Migration in (Get-ChildItem supabase/migrations/*.sql | Sort-Object Name)) {
  & $v6Psql -X -v ON_ERROR_STOP=1 -1 -d $env:WOMBO_V6_DISPOSABLE_PG_DSN -f $v6Migration.FullName
  if ($LASTEXITCODE -ne 0) { throw "Migration failed: $($v6Migration.Name)" }
}
```

Run every `supabase/tests/*.sql` with `psql -X -At -v ON_ERROR_STOP=1`. **Parse TAP
and the plan/finish output:** psql can exit zero while TAP assertions fail. Do not
count a truncated/aborted suite as passing. Actual results and the A5 blocker are
in the main report. Then, from `backend`, using the existing backend Python venv:

```text
python -B -m scripts.verify_v6_postgres --execute-disposable-local-only --private-output ../.runtime/reproduction-lifecycle
```

## Reproduce HTTP and unknown-outcome checks

Use a second fresh disposable database with the same bootstrap/migrations. Apply
`v6_persistence_users.sql`, then run the SQL runner's `--stage create` with a
new private output **file**. This leaves both synthetic plans pending. The full
SQL lifecycle intentionally rejects the second subject's proposal, so it is not
the input fixture for the lost-acknowledgement scenario.

Generate a new random 32-byte-or-longer HS256 signing secret into an ignored file.
Use a private PostgREST config pointing only to that second database:

```text
db-uri = "postgresql://authenticator@127.0.0.1:55432/wombo_v6_http_reproduction_20261107"
db-schemas = "public"
db-anon-role = "anon"
server-host = "127.0.0.1"
server-port = 55431
jwt-secret = "<new locally generated test secret>"
```

Launch portable PostgREST with the portable PostgreSQL bin on its process PATH;
use `Start-Process -WindowStyle Hidden -PassThru` and redirect logs under
`.runtime`. Store its PID. Verify that the config's database and the verification
DSN name the **same** disposable database. Then run, in this order, from backend:

```text
python -B -m scripts.verify_v6_commit_loss --execute-disposable-local-only --url http://127.0.0.1:55431 --signing-secret-file ../.runtime/local-signing-secret.txt --private-output ../.runtime/commit-loss.json
python -B -m scripts.verify_v6_postgrest --execute-disposable-local-only --url http://127.0.0.1:55431 --signing-secret-file ../.runtime/local-signing-secret.txt --private-output ../.runtime/signed-token.json
```

The first test commits one real synthetic swipe while withholding its HTTP
acknowledgement, then recovers it by the same key. The second confirms both own
plans and tests cross-subject denial and signatures. It does not run GoTrue.
A full disposable Supabase stack is a separate setup requiring an owner-approved
container/runtime installation on this workstation; see the
[official local-development prerequisites](https://supabase.com/docs/guides/local-development).

For rollback, clone only the completed disposable SQL lifecycle database into a
new `wombo_v6_rollback_<digits>` database, record snapshot hashes, and execute
`v6_disposable_forward_rollback.sql`. Repeat snapshot reads and the SQL suites.
Never reset or drop a shared database. After recording results, stop only the
PostgREST PID created here and `pg_ctl -D <this exact disposable data path> -m fast -w stop`.
Keep evidence; no cleanup of another worktree, service or database is authorized.
