# V6 PostgreSQL and RLS test results

7 November 2026, Europe/Amsterdam. Branch `feat/joren-v6-persistence-hardening`.
Base `4b3a76d9d764567e7bb438ad7493953faed6dea2`.

**NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE**

There is no configured authorized disposable database. `psql`, `postgres`,
`pg_ctl`, Docker, Podman and Supabase CLI were unavailable in the inspected local
tooling. No test DSN was configured. No production/staging connection was made,
no linked cloud project was used, and no infrastructure/dependency was installed.
The runner's no-execution path was checked; it reports the unavailable gate.

## What actually ran locally

- Complete backend tests, including in-memory V6 service/HTTP tests and new
  lossless serialization/MockTransport tests; final counts are in the ledger.
- Ruff lint/format and strict mypy.
- `pglast.parse_sql` on both new migrations, pgTAP suite and committed-user
  fixture. It parses outer SQL syntax; it does not resolve schema names,
  type-check PL/pgSQL bodies or execute grants, triggers, policies or constraints.
  Its separate PL/pgSQL parser cannot resolve this project's private composite
  types, so no PL/pgSQL-runtime validation is claimed.
- Independent source/hash/official-value evidence and historical regressions.

**Verified real PostgreSQL behavior: none.**

## Files ready for an isolated run

| File | Purpose |
| --- | --- |
| `supabase/migrations/20261105120000_inactive_v6_persistence.sql` | Forward-only private storage, composite ownership, locks/CAS, immutable snapshots, narrow RPCs and inactive catalog visibility. |
| `supabase/migrations/20261105120100_inactive_v6_catalog.sql` | Generated immutable 77-source import; canonical hash in architecture/ledger. |
| `supabase/tests/v6_persistence_security_test.sql` | Rollback-only pgTAP: actual table/function grants, forced RLS, inactive visibility, source immutability, numerical equality and denied direct execution. |
| `supabase/tests/fixtures/v6_persistence_users.sql` | Two synthetic accounts with current complete onboarding; commits deliberately for process-boundary durability tests. No trigger is disabled. |
| `backend/scripts/verify_v6_postgres.py` | Separate-process durable resume, real concurrent RPC transactions, duplicate retries, stale/tampered inputs, rejection, confirmation and rollback. |

Both migrations are **created but not executed**. The candidate also depends on
all four existing Realized V2 migrations from 20261103, which remain subject to
their own migration/release gates. Historical migrations are unchanged.

## Reproduction commands

Use a fresh, explicitly disposable local Supabase/PostgreSQL 17 environment with
Supabase auth roles/functions and pgTAP. It must contain no real athlete data.
This delivery does not authorize a production/staging reset, migration or test.
Do not reuse a production tunnel or a linked remote project.

First inspect the installed CLI's supported commands:

```text
supabase --help
supabase start --help
supabase db reset --help
supabase test db --help
```

Create/reset only that disposable local environment using the verified local-only
CLI options and apply the entire migration directory in order, including both
20261105 candidates. Inspect migration history and advisors locally. No hosted
credentials are needed. Then, from the repository root, with the local DSN supplied
privately in `WOMBO_V6_DISPOSABLE_PG_DSN`:

```powershell
psql --no-psqlrc --set=ON_ERROR_STOP=1 --dbname $env:WOMBO_V6_DISPOSABLE_PG_DSN --file supabase/tests/v6_persistence_security_test.sql
```

Run every existing pgTAP suite through the installed CLI's local test runner as
well. From `backend`, using the project's existing Python environment:

```text
python -B -m scripts.verify_v6_postgres --execute-disposable-local-only --private-output .runtime/v6-postgres-fresh-run
```

The runner creates the two fixture accounts itself, so start from a fresh
disposable database for each full run. It refuses non-loopback DSNs and does not
read repository .env files. Store transcripts privately, record database/version,
migration ledger, exact tested Git SHA, assertion counts, commit/rollback outcomes,
and actor identities. Destroy only that disposable environment afterward.

Also run actual signed-token/PostgREST two-user verification separately before
activation; SQL role/GUC tests alone do not prove that HTTP authentication boundary.
Do not convert the prepared expected outcomes into PASS entries before execution.

## Open database gates

Actual migration/PL/pgSQL execution; numeric and JSON round trips; grants/forced
RLS and all cross-account/cross-athlete cases; complete-week CAS under competing
swipes/approval/rejection; duplicate keys; connection interruption and worker
reconciliation; persisted source/method/version consistency; source retention;
restart/resume and immutable confirmation; complete existing pgTAP regression set;
advisors; and a rehearsal of the forward-only rollback plan all remain open.

## Local delivery provenance

Verified implementation, tests, prepared SQL and evidence commit:
`5482524f49e5c2684df0a756c60b619ba9a128ef`, directly after accepted base
`4b3a76d9d764567e7bb438ad7493953faed6dea2`. A documentation-only successor
records this immutable SHA; resolve the final branch tip with
`git rev-parse feat/joren-v6-persistence-hardening`.

Final backend: 2,583 passed; 96 new persistence tests included. Ruff lint/format
and strict mypy pass. All 40 historical cases and 26 accepted reference results
are byte-identical to the accepted corpus; canonical SHA-256
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.

PostgreSQL/RLS: **NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE**.
Both new migrations are unexecuted. Default planner, production/staging and A5/A6
remain untouched. No push, merge, deployment, activation or next release stage.

**WOMBO V6 PERSISTENCE IMPLEMENTED — DATABASE VERIFICATION PENDING**
