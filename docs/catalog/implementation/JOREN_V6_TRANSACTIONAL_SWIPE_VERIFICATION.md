# V6 transactional swipe verification

7 November 2026, Europe/Amsterdam. Exact base
`4b3a76d9d764567e7bb438ad7493953faed6dea2`, branch
`feat/joren-v6-persistence-hardening`. Implementation SHA is recorded in the
delivery addendum. The selector, official physiological method, historical
expected outcomes and computation deadlines are unchanged.

## Evidence categories

| Evidence | Actual status |
| --- | --- |
| Durable repository implementation | Explicit inactive Supabase adapter, lossless catalog reader, forward SQL writer, frozen context, occurrence mapping and immutable retry receipts implemented. |
| Pure serialization / transport | All 77 source revisions independently round-trip; exact rational-to-Decimal final conversion and aggregate comparisons checked. A new Python process restores all documents with workbook opening prohibited. Mock HTTP tests check caller/service credential separation, Decimal decoding and sanitized dependency errors. |
| Existing service/HTTP behavior | Real authenticated routes and spawned worker retain automatic selection, full-week alternatives, pending edits, exhaustion, restrictions, duplicate occurrences, cancellation/admission and separate approval coverage. Repository state in those tests is in memory. |
| Shared-service concurrency | An explicit two-athlete barrier interleaves catalog reads on one service instance. Occurrence IDs stay disjoint. This is an application/memory regression, not a database concurrency test. |
| Real SQL transactions, restart and RLS | **NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE**. No PostgreSQL pass is inferred from any preceding row. |

Final exact counts, command outcomes and artifact hashes are in
`persistence/verification.json` and its transcripts. The full-suite initial failure
was the collision scanner recognizing its own newly persisted IDs; the reviewed
hash-bound exception retains collision rejection for any other/modified import.
One historical dependency-boundary allowlist now explicitly permits the authorized
inactive codec to restore the phase-source dataclass. Startup/default dependency
assertions remain, and no historical expected result was modified.

Final software run: **2,583 passed**, one existing Starlette/httpx deprecation
warning; 96 new persistence regressions are included. Ruff lint and formatting
pass (208 files); strict mypy passes for 205 application/test/benchmark sources
and the separate SQL-runner source. The independent historical rerun preserves
all 40 canonical results and all 26 accepted reference completions: 29 returned
plans, ten fail-closed outcomes and the one retained diagnostic timeout. Its
canonical SHA-256 remains
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.

## Preserved functional regression fixtures

With identical source revisions, athlete context, phase and official method, the
45-budget BASE/BUILD automatic result remains BIKE-023, RUN-025, SWIM-021. The
existing independently validated RUN-025 → RUN-026, BIKE-023 → BIKE-022 and
SWIM-021 → SWIM-022 examples remain source-bound regression fixtures. None is
hardcoded into selection. Budget, phase, per-sport HIGH time, injury, capability,
repetition, retained occurrence/date and account checks continue to apply to the
complete replacement week. Empty alternatives do not mutate the proposal.

Restored controls preserve source-/athlete-/week-bound duration evidence and the
complete authorized target, including taper/replacement flags and caps. Current
restrictions can tighten those controls. Swipes do not obtain a new budget from
later history. A committed edit returns its immutable receipt rather than rereading
a mutable proposal that another request may already have replaced or approved.

## Prepared real-PostgreSQL scenarios

`backend/scripts/verify_v6_postgres.py` requires an explicit disposable-local flag
and a loopback DSN in `WOMBO_V6_DISPOSABLE_PG_DSN`. It never reads .env or applies
migrations. Each SQL call runs in an independent psql process/transaction. The
parent terminates the create-stage Python process before running resume and then
confirmed reload in fresh Python processes. The SQL adapter substitutes local
SQL for HTTP only; production repository methods and V6 service logic remain in use.
This tests SQL-role/JWT-GUC behavior, not real signed-token/PostgREST authentication.

| Scenario | Prepared assertion / transaction outcome required |
| --- | --- |
| Initial persistence | Two distinct synthetic athletes have their own pending plans, exact immutable template identities and disjoint logical occurrences. |
| Restart/resume | Fresh processes reload the complete initial public snapshot with identical ordering and identities, swipe, approve and reload the confirmed snapshot. |
| Two different edits | Exactly one same-revision write commits. The other conflicts. Retained workouts/dates remain equal. |
| Duplicate key/messages | Both identical requests recover one revision and the same immutable response. Mismatched payload reuse is rejected by SQL. |
| Swipe versus confirmation | Exactly one competing transition commits. The loser conflicts; there is no silent overwrite. |
| Terminal retry | Original edit receipt stays identical after another revision and confirmation. Repeated confirmation returns the applied receipt. |
| Cancellation | The second athlete rejects its proposal; persisted revision remains rejected. Existing request cancellation/admission tests also remain. |
| Tampered IDs/context | Foreign plan, revision/proposal, athlete evidence scope, week scope, occurrence, missing template and invalid source hash reject with the original week unchanged. |
| Interrupted write | A successful nested generation followed by rollback leaves no plan/proposal/occurrences in the next connection. |
| Immutable confirmation | Direct attempts to rewrite V6 workout snapshot or private load reject; confirmed read remains identical. |
| Failed dependency | Application transport tests preserve unavailable/unknown-outcome semantics and never expose database load diagnostics. Actual connection-loss timing remains a database gate. |

These are reproducible fixtures and required outcomes, **not observed database
results**. Run the SQL suites and record their actual transcripts before claiming
transactional durability or release readiness. Prepared check-in generation is
explicitly fail-closed; no A5 attachment/replay semantics were approximated.

## Regression and release isolation

Complete backend pytest includes the historical physiology/planner, A3–A9,
Realized V2, OpenAPI/public-contract and private-load leak suites. The separate
40-case unmodified-planner corpus must preserve all 26 accepted completions and
the full canonical outcomes; its existing eight-second `current:build_4` timeout
is retained. No test expectation or deadline was relaxed. The final verification
ledger records the independent rerun and canonical hash.

No mobile/DTO/release configuration changed. TypeScript/device tests are not
claimed as run for this backend/SQL change. Mobile occurrence resolution and
device confirmation/recovery remain explicit activation gates. The A5/A6 release
worktree remains at `cd3e2dd438031cfb565858d0a5929e9963f7b31f` and was not modified.
