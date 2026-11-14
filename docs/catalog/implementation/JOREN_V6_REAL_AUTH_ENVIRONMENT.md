# WOMBO V6 real Auth: environment and reproduction

14 November 2026, Europe/Amsterdam. Branch
`verify/joren-v6-real-supabase-auth`, created in a new worktree from
`dbeb9596f42f0504e428afbf5eddc75eaa7d20da` on
`perf/joren-v6-exact-multi-session-search`.

**WOMBO V6 AUTHENTICATION VERIFICATION BLOCKED — EXACT ENVIRONMENT REQUIREMENTS DOCUMENTED**

Zero genuine GoTrue accounts, issued sessions or gateway requests were executed.
No production/staging credentials, hosted infrastructure, system installation,
Windows feature change, custom Auth proxy or catalog activation was used.
The independent software/SQL results below do not close that boundary.

## Observed environment

| Item | Actual observation |
| --- | --- |
| Host | Windows 10, build 19045; PowerShell; no supported native Linux runtime available |
| Docker / Podman | Neither command on PATH; standard installation directories absent; no matching running/installed service found |
| WSL | `wsl.exe` exists. Sandboxed enumeration returned `Wsl/E_ACCESSDENIED`; approved read-only enumeration exited 0 with no distributions |
| Supabase CLI / GoTrue / gateway | No `supabase`, `gotrue` or `kong` executable on PATH; no complete running local stack found |
| Initial standard listeners | None found on 5432, 54321, 54322, 54323, 8000, 8001, 9999 or 3000 |
| Relevant environment variables | No Supabase/JWT/database/container environment variable names found; no environment values were printed or copied |
| PostgreSQL / pgTAP | Not on PATH. Existing workspace-portable PostgreSQL **17.11** and pgTAP **1.3.4** found and reused as read-only tools |
| PostgREST | Portable **16.5** found; version inspected only. No direct PostgREST HTTP tests run in this task |
| New SQL cluster | Only this worktree's `.runtime/real-auth/pg-data`, IPv4 loopback **127.0.0.1:55564**; disposable SQL fixture runtime, not Supabase |

The first sandboxed `initdb` failed creating its restricted token (error 87).
Approved execution then initialized only the new disposable cluster; no service
was installed. No protected worktree's data directory was started or modified.
The new cluster was stopped after the checks.

Official [runtime documentation](https://supabase.com/docs/guides/local-development/docker-and-native-runtimes)
supports Linux amd64/arm64 with glibc >=2.35 for the native runtime and excludes
Windows. Its experimental flags must be discovered for the selected CLI version.
An installed Go toolchain and portable Windows database alone do not supply this
runtime. The [official container stack](https://supabase.com/docs/guides/self-hosting/docker)
is the preferred alternative on an already authorized Linux/container host.

## Tested versions and independent checks

| Check | Fresh execution in this worktree |
| --- | --- |
| Python / Node / npm | **3.10.10 / 24.18.0 / 11.16.0** |
| FastAPI / httpx / PyJWT / Pydantic | **0.139.2 / 0.28.1 / 2.13.0 / 2.13.4** |
| pytest / Ruff / mypy | **8.4.2 / 0.16.0 / 1.20.2** |
| TypeScript / Jest | **6.0.3 / 29.7.0** |
| Expo / React Native / supabase-js | **57.0.24 / 0.86.3 / 2.110.8** |
| Backend pytest | **2,876 passed**, 1 existing Starlette/httpx deprecation warning, **301.16 s**; no failures/skips |
| Mobile Jest | **929 passed, 88 suites**, **173.533 s**; no failed/skipped/todo tests |
| Mobile dependency preparation | Fresh `npm ci --offline --ignore-scripts --no-audit --no-fund`; 952 packages from unchanged lockfile, no package upgrade |
| Ruff / formatting | PASS; **240 files** already formatted |
| Strict mypy | PASS: **222** app/test/benchmark files and **4** existing verification scripts |
| TypeScript / unused checks | Both PASS |
| Local PostgreSQL schema | **63/63 accepted migrations**, in filename order, no new or edited migration |
| Local pgTAP | **722 assertions / 37 suites**, complete plans, no skipped assertions, using the explicitly disclosed existing A5 overlay |
| Original A5 SQL fixture | Separately EXECUTED / FAIL: **8 passed, 1 failed**, then aborted; remaining **20 not executed** |
| Frequency SQL/ASGI concurrency runner | **9 groups PASS**, plus fresh-process receipt read; SQL roles and injected identity, no GoTrue |

The full backend run includes existing V6 search/oracle/worker tests, A5/A6
replay and recovery, OpenAPI contracts, recursive private-load exclusion,
identity, stale revisions, idempotency and concurrent operations. Historical
corpus results and the preserved resource bounds are recorded in
[the lifecycle report](JOREN_V6_AUTHENTICATED_LIFECYCLE.md).

The [source custody ledger](real-auth-20261114/source-custody.json) checks the raw
bytes of all 63 migrations and 37 SQL suites against the accepted worktree.
The original release register is archived byte-for-byte under
`real-auth-20261114/history`. The [SQL migration ledger](real-auth-20261114/migration-ledger.json),
[per-assertion results](real-auth-20261114/pgtap-results.json),
[original A5 failure](real-auth-20261114/a5-final-original.json),
[permissions](real-auth-20261114/sql-permissions.json) and
[catalog preservation](real-auth-20261114/catalog-preservation.json) are fresh
local SQL evidence. They do not describe actual Supabase runtime permissions.

## Exact missing prerequisites

Provide an owner-authorized disposable Linux environment with an already working
Docker/Podman engine, or a supported official native Supabase runtime. No Linux
host, container endpoint or WSL distribution was supplied here. Installing Docker,
WSL, virtualization or Windows features, or allocating hosted infrastructure,
requires separate owner authorization and was not attempted.

The environment needs Git, a pinned official Supabase CLI, PostgreSQL 17 runtime,
pgTAP, psql and the complete official Auth/PostgREST/API-gateway stack, including
Supabase-owned Auth/Storage schemas, extension distribution and bootstrap roles.
For a full container stack, reserve at least 2 CPUs, 4 GB RAM and 40 GB disk;
record actual host, engine/CLI/service versions and image digests. Permit downloads
from the selected official release/registry hosts. A native environment also needs
`tar`, glibc >=2.35 and a non-root PostgreSQL owner.

Use a unique local project ID and unused loopback ports. Configure email/password
signup, local email capture or local-only unconfirmed signup, refresh rotation,
and **GoTrue ES256 signing with a public JWKS**. The existing backend accepts
ES256, audience `authenticated`, and issuer exactly `<local-supabase-url>/auth/v1`.
Use the same gateway URL for signup, JWKS and backend Data API requests. An
HS256-only stack cannot prove this unchanged verifier. Supply locally generated
publishable/secret API keys supported by the actual gateway; legacy JWT API keys
alone do not prove modern key routing. Record expiry, refresh-reuse and logout
configuration without serializing secrets.

## Full-stack setup recipe — NOT EXECUTED

On that authorized Linux host, export a clean Git archive of the verification
commit into a fresh directory. Do not copy `.env`, `.temp` linked-project state,
another worktree's runtime, hosted credentials or an existing database. Give
`supabase/config.toml` a unique disposable project ID in that exported copy only.
Check the local ports are free. Keep all generated secrets under ignored `.runtime`
with owner-only permissions; turn off shell tracing and do not print CLI status
output containing keys.

The [4 November CLI change](https://supabase.com/changelog/supabase-cli-v3)
changes command defaults, so pin the chosen CLI release and use its own help.
For a v3 container run, after verifying the target is the new local project:

```sh
supabase --version
supabase --help
supabase start --help
supabase db reset --help
supabase test db --help
docker version
docker compose version
supabase start > .runtime/start.private.log 2>&1
supabase db reset --no-seed > .runtime/migrations.private.log 2>&1
supabase test db > .runtime/pgtap-original.private.log 2>&1
```

These are local commands in CLI v3; never add `--remote`, link, login, db push or
hosted credentials. Stop on any unsupported flag or unresolved target. See the
[CLI reference](https://supabase.com/docs/reference/cli/supabase-start).
For native execution discover the official runtime flags first; do not build a
replacement gateway. No CLI or service version is claimed tested here.

Reconcile all **63** migration entries and byte hashes. Do not run
`v6_disposable_supabase_bootstrap.sql` or `scripts.verify_v6_final_sql` on the real
stack: that runner installs the stock-Postgres SQL subset. Run the original 37
suites first and keep the original A5 result. Render only the already documented
onboarding/32-character-fingerprint A5 overlay into a separate test copy, then
run every suite and parse every TAP plan/finish result. Keep original SQL bytes
unchanged. The existing overlay is documented in
[the A5 investigation](final-security-20261108/A5.md).

Verify extension/grant/RLS/function/service permissions against the real runtime,
including gateway requests; do not relax policies when a check fails. Check 77 V6
source revisions, zero active revisions, and unchanged historical catalog/load
records. Create A/B only through real signup/password endpoints, then execute
[the Auth matrix](JOREN_V6_GOTRUE_GATEWAY_VERIFICATION.md),
[isolation matrix](JOREN_V6_TWO_ACCOUNT_SECURITY_RESULTS.md) and
[lifecycle](JOREN_V6_AUTHENTICATED_LIFECYCLE.md).

## Independent checks: reproduction

From `backend`, with the existing development environment and no copied `.env`:

```text
python -B -m pytest -q -p no:cacheprovider
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests benchmarks
python -m mypy --explicit-package-bases scripts/verify_v6_exact_search.py scripts/verify_v6_multi_session.py scripts/verify_v6_frequency_policy.py scripts/verify_v6_evidence_network.py
python -B -m benchmarks.v6_planner_performance --variant optimized --output ../.runtime/real-auth/historical-new.json
```

From `mobile`, run `npm ci --offline --ignore-scripts --no-audit --no-fund`,
`npm test -- --watchman=false`, `npm run typecheck`, and `npm run check:unused`.
Use `TZ=UTC` for Jest. CPU historical measurements run after other test/build work.
For the distinct stock-PostgreSQL proof, follow the
[existing disposable setup](JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md), use a
new owned cluster and `scripts.verify_v6_final_sql` with explicit local port,
cluster directory, `wombo_v6_final_<unique>` database and private output. Clone
only that empty migrated disposable database for `scripts.verify_v6_frequency_policy`;
set process-local psql PATH and `WOMBO_V6_DISPOSABLE_PG_DSN`. Do not use those
SQL-role fixtures as genuine Auth accounts.
