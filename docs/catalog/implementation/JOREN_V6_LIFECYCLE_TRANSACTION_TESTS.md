# V6 lifecycle transaction verification

8 November 2026, Europe/Amsterdam. Accepted base
`31a8ed0cfad831780b405030121817df50e8fa2c`; implementation `bb4ac2c917780740551443380ef6fde7a4db4e09`.

## Actual local execution

| Check | Executed result |
| --- | --- |
| Fresh PostgreSQL | 17.11, disposable cluster under this worktree, IPv4 loopback port 55442 |
| Migration replay | 61 forward migrations, including one new lifecycle migration |
| pgTAP 1.3.4 | 35 suites / 666 assertions pass |
| A5 compatibility | 29 unchanged original assertions pass with explicit reviewed fixture overlay |
| Context guards | Draft/revision/foreign/source/budget rejection and reconfirmation history preservation pass |
| New HTTP/SQL journey | Nine assertion groups plus independent-process reload and rejected/superseded-locator checks pass |
| Existing V6 SQL lifecycle | All 77 exact source/numeric round trips, immutable snapshots, composite ownership, real retries, pending edits/confirmation races, rejection, cancellation and rollback pass |
| Existing calendar/activity probe | 14 groups pass; measured activity, exact physical FK, registration skip/undo and unsupported fallback rejection |
| TCP acknowledgement loss | Two real PostgREST 16.5 commits, two socket disconnects, exact A5 and move recovery, no duplicate revision |
| Full backend | 2,674 passed; A3?A9, Realized V2, privacy/OpenAPI/public contracts included |
| Backend lint/types | Ruff lint/format pass; strict mypy app/tests/benchmarks and six SQL/HTTP scripts pass |
| Mobile | 904 tests / 85 suites, strict TypeScript and unused-code checks pass |
| Historical planner | 40/40 inputs/outcomes identical; all 26 accepted reference results retained; unchanged `current:build_4` eight-second timeout |
| Android | Hermes export and offline x86_64 debug build pass; 497 Gradle tasks, no device installation |

The new SQL suite adds 12 permission, fixed-search-path, inactive-source and forced
RLS assertions. The conflict-function inventory now expects 37 implementations
because the new move writer adds one; no original guard or assertion was removed.
All previously applied migration files are unchanged. No tables or extra replay
ledger were added. The existing context-confirmation constraint now retains
confirmation timestamps on superseded contexts, and its existing confirmation RPC
atomically supersedes the previous confirmed row before activating the reviewed
new context. The writer rejects any older context behind a newer draft. Restrictive grants/RLS and immutable snapshot triggers remain.

[SQL summaries](lifecycle-completion/sql-summary.json),
[migration source hashes](lifecycle-completion/migration-ledger.json),
[functional assertion groups](lifecycle-completion/functional-checks.json),
[network fault results](lifecycle-completion/socket-loss.json) and
[full verification/source manifest](lifecycle-completion/verification.json).

## Reproduction

Use the existing portable PostgreSQL/pgTAP/PostgREST binaries documented in
[JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md](JOREN_V6_DISPOSABLE_POSTGRES_SETUP_20261107.md).
Initialize a new cluster inside this worktree, bind only loopback, then run from
`backend`, using the existing backend virtual environment:

```text
python -m scripts.verify_v6_final_sql --execute-disposable-local-only --psql <portable-psql.exe> --cluster-directory ../.runtime/pg-data --port 55442 --database wombo_v6_final_<new-name> --private-output ../.runtime/<new-sql-output>
```

Set `WOMBO_V6_DISPOSABLE_PG_DSN` explicitly to that disposable database and put the
portable PostgreSQL bin directory on the process-local PATH. No tool reads a hosted
`.env`. Run the new journey on its fresh database:

```text
python -m scripts.verify_v6_lifecycle_completion --execute-disposable-local-only --private-output ../.runtime/<new-journey-output>
```

Each adapter request opens a fresh psql connection and real transaction. Concurrency
barriers force both operations to finish Python validation before their competing
RPCs execute. Database triggers inject failure at attachment and after the move's
pointer update; comparisons prove all preceding writes rolled back. The runner
spawns a new Python process for calendar reload. This is real storage/transaction
verification, with simulated SQL JWT claims.

Run the inherited `scripts.verify_v6_postgres` all/create/resume/reload sequence and
`scripts.verify_v6_mobile_lifecycle --snapshot <snapshot.json> --output <result.json>`
on a **separate fresh database**. Its old move-blocker assertion was replaced with
the explicitly approved completed-occurrence rejection; other assertions remain.

Configure a new local PostgREST instance (the Windows verification uses `+RTS -N2 -RTS`) against the same disposable journey DB,
using a new ignored signing key. Pick a fresh synthetic week before its recorded
history for a nonzero automatic source week. Execute:

```text
python -m scripts.verify_v6_lifecycle_commit_loss --execute-disposable-local-only --week-start 2026-09-21 --url http://127.0.0.1:55444 --signing-secret-file ../.runtime/postgrest-key.txt --private-output ../.runtime/<new-socket-result>.json
```

Additional captured automatic payload guards run on a fresh synthetic week:

```text
python -m scripts.verify_v6_lifecycle_guards --execute-disposable-local-only --week-start 2026-09-28 --output ../.runtime/<new-guards>.json
```

These tests invoke actual SQL with stale confirmed context, a newer unconfirmed
draft, a foreign check-in, a tampered source hash and a tampered budget. Failed
transactions retain exact counts; explicit reconfirmation retains the old payload
and timestamp. A valid request then attaches and replays normally.

A proxy sends the write to real PostgREST, waits for its successful committed
response, then closes the client TCP socket before returning HTTP headers. The
ordinary FastAPI routes report unavailable; retries recover persisted authority.
Reads use the normal repository contracts over SQL. These signed synthetic claims
are **not** GoTrue-issued sessions or complete Supabase gateway verification.

## Verification boundaries

FastAPI tests execute actual ASGI/Pydantic handlers. The SQL adapter replaces Data
API transport with real psql, not storage mocks. Disabled coach explanation PATCH
is outside that adapter's transport subset; its safe persistence warning is not a
planning/attachment failure. The separate socket probe uses actual loopback HTTP.
No mocked repository is described as a verified database transaction.

Jest uses recorded public FastAPI/PostgreSQL responses with mocked transport,
secure storage and sessions. Android compilation is not device execution. No
GoTrue, complete Supabase gateway, Android/iOS device, Xcode/signing or hosted
migration verification was performed. Disposable services were stopped after
recording evidence; original worktrees and protected branches remain unchanged.
