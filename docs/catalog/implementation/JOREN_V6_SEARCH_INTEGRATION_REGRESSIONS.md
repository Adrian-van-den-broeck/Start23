# V6 exact search: integration and regression evidence

14 November 2026, Europe/Amsterdam. Accepted base
`e85cbaa8b5e702c283186fc61fcadda74ad36faf`; isolated branch
`perf/joren-v6-exact-multi-session-search`. Tested source/evidence hashes are in
[verification.json](search-optimization/verification.json). This is local software
verification; all V6 revisions remain inactive and release gates remain open.

## Executed gates

| Check | Executed result |
| --- | --- |
| Full backend pytest | **2,876 passed**, one existing Starlette/httpx deprecation warning; 282.13 s. Accepted 2,759 plus 117 new tests. |
| Final source custody | 260 selector/oracle/worker/HTTP checks pass again after canonical LF normalization; scoped attributes preserve source/evidence hashes across Windows checkouts. |
| Existing/new selector oracles | Original 30 independent seeded cases unchanged; 113 new bound/order/restricted-week cases plus four new HTTP/worker cases pass in the full suite. |
| Independent full-catalog exhaustive reference | All 15 original cases, **20,061,679** complete products visited; every full rank and immutable UUID multiset matches. No shared production bounds/ranking/scheduler. |
| Completed baseline parity | All 12 originally completed cases preserve exact totals, rank, selected sources, occurrence UUIDs and dates. Additional previously completed contexts also preserve their exact results. |
| Ruff lint/format | Passed; 240 Python files formatted. |
| Strict mypy | App/tests/benchmarks: 222 files; four verification scripts also pass with explicit package bases. No strictness reduction. |
| Actual workers and FastAPI routes | All three formerly incomplete requests return pending proposals; baseline returns 409 without persistence. Cold/warm worker, HTTP CPU/wall and process-memory evidence retained. |
| A9 ownership/admission/cancellation | Existing event-loop/read and cancelled-owner no-write tests pass. A new optimized V6 worker proves separate PID, two admitted requests, rejection of the third, cancellation without early capacity release, and subsequent recovery. |
| PostgreSQL 17.11 | New owned IPv4 loopback cluster; all **63 unchanged migrations** replayed. |
| pgTAP/grants/ownership/RLS | **722 assertions in 37 suites**, every TAP plan complete, no skipped assertions. Existing explicit A5 fixture overlay distinguished below. |
| Original synthetic multi-session SQL | Seven lifecycle groups plus four concurrency/rejection groups pass, with original TEST_ONLY controls and normal 35-minute onboarding. |
| Formerly incomplete normal onboarding in SQL | Ten new groups pass with **105 minutes/sport, normal resolved budget 300.2, no target override**, real spawned planner, actual RPC transactions and exact pending snapshots. |
| Regular frequency preference/revocation SQL | Nine existing groups pass without real reviewer enrollment or fabricated numerical decisions. |
| Real PostgREST/TCP | Two actual committed replies dropped for the high-budget five-session context; four more for regular frequency/suspension/atomic swipe. Exact original receipts recovered in all six. |
| Restart | Full stop/start of this task's PostgreSQL cluster; three fresh Python runners restore exact multi-session identities, high-budget plan/receipt/activity evidence and regular-policy suspended receipts. |
| Historical planner corpus | All 40 actual outcomes and independent checks unchanged; all 40 input hashes separately reconstructed and equal accepted canonical evidence. All 26 accepted reference completions retained. |
| Original diagnostic | `current:build_4` still times out at the unchanged eight-second including-imports corpus bound. No V6 timeout is inferred from it. |
| Catalog/history | 325 historical template/load records preserved; 77 V6 source revisions and **zero activated revisions**. No source prescription/membership or historical calculation change. |

The original historical regression artifact remains byte-identical, SHA-256
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.
[historical-comparison.json](search-optimization/historical-comparison.json),
[historical-inputs.json](search-optimization/historical-inputs.json) and the full
[new historical run](search-optimization/historical.json) preserve the checks.

Full pytest retains A3–A9, public/OpenAPI/recursive private-load contracts,
frequency preference/authorization/revocation, Realized V2 priority and fallback
restrictions, exact Decimal/HIGH boundaries, explicit/partial/rest selection,
manual placement/swiping, immutable revisions, retention, stale CAS, account
isolation and retry behavior. No existing test, golden or fixture was weakened.

## Durable high-budget path

`scripts.verify_v6_exact_search` seeds an empty migrated disposable database with
the original ordinary synthetic onboarding fixture, changing only its explicit
TEST_ONLY historical minutes to 105 for each sport. No private budget override,
real reviewer or numerical authorization is supplied. The normal Python resolver
and SQL target-evidence guards accept the same 300.2 budget as the original probe.

The trace first lowers the private node budget to one and verifies no plan,
revision, occurrence, receipt or snapshot is written. With the original resource
ceiling restored, check-in generation creates the exact five-session pending
week and original A5 attachment; retries recover it, and the second owner cannot
read it. A pending swipe keeps every unrelated source, logical ID and date.
The original snapshot remains immutable. A separate confirmation activates the
week. A physical RUN occurrence is registered with measured activity data;
moving its unfinished same-sport sibling preserves the completed row, physical
FK, status and all realized activity evidence. Lost move acknowledgement recovers
the original immutable receipt. Calendar reads five occurrences after completion.

The same readback and hashes survive a real database restart and fresh Python
process. [lifecycle.json](search-optimization/lifecycle.json) records checks and
original-snapshot/activity-evidence digests. The two real TCP losses for this
high-budget context cover A5 creation and the completed-sibling move through
actual local PostgREST commits, not an in-memory exception simulation.

The original five-session SQL trace additionally preserves duplicate RUN-025
templates as separate logical/physical occurrences, retains distinct dates through
swipe, manual placement and replacement, checks injected rollback, concurrent
same-sport edits/moves, stale locators and rejection/confirmation races.

## Authorization and failure boundaries

The approved real resolver, database guards and revocation/expiry/confirmation
mechanism are unchanged. The regular-policy runner and four-loss network runner
use ordinary synthetic accounts with no real positive authorization. Its registry
still contains zero reviewers and zero numerical decisions. It proves suspension
during generation/commit, lock ordering, rollback, immutable A5 attachment,
pending replacement and atomic swipe submission/recovery without renewed authority.

Legacy positive multi-session SQL controls require the pre-existing ungranted
`v6_frequency_test_executor` role. An initial run without its explicit harness
membership correctly failed closed. The accepted isolated test procedure was
then applied temporarily to synthetic service/authenticated test roles, separately
from regular-policy testing. Membership was revoked before the final regular
network test and restart audit. Application migrations/grants/RLS were not changed
to work around the rejection. The final audit records both memberships false,
zero reviewers/decisions and zero active V6 revisions.

Domain and spawned-worker exhaustion retains `v6_search_incomplete`; ordinary
planning routes retain HTTP 409 with that code. The existing A5 check-in error
adapter normalizes a forced low-node failure to HTTP 422 `validation_failed`,
with the explicit bounded-search/no-optimum message. This inherited envelope is
recorded rather than relabeled as a 409 test pass; no A5 transport code is changed
in this algorithm-only work. Structured A5 error-code parity remains an existing
transport limitation for release review. Both paths write nothing and distinguish
the failure from a valid rest or an impossible week. No arbitrary incumbent is
persisted and no request is silently reduced.

The unmodified original A5 pgTAP file still has its previously documented missing
onboarding/fingerprint prerequisite failure. `postgresql.json` retains that actual
failure separately. The 722 passing assertions use only the existing explicit
onboarding and 32-character fingerprint fixture overlay, exactly as the accepted
baseline verification does. Neither protected A5/A6 worktree nor original SQL is
edited to manufacture a pass.

Early harness attempts also exposed the existing A5 422 envelope and Decimal
serialization in the new private evidence writer. The writer was corrected to
record actual transport behavior and exact Decimal strings; final runs use fresh
databases. Intermediate private transcripts remain in this task's ignored runtime.
No application policy or production validation was relaxed to fit the harness.

## Applicability and open gates

No mobile application, public schema, shared TypeScript contract or migration
changes. Full mobile Jest, TypeScript/unused checks and Android build are therefore
not rerun for this Python-only change. The accepted 929-test/APK evidence is
inherited source context, not claimed as a new execution. Actual Android/iOS
device flows and GoTrue/full gateway verification remain open independently.

The measured 8/8/8 fixture still exhausts during per-sport multiset expansion
within bounded memory. No universal frequency/latency guarantee is claimed.
The three requested failures are independently solved; larger ranges,
representative target-hardware latency acceptance, real reviewer/operator,
individual decisions, positive issuance/revocation, scientific review, swim-time
and exceptional-duration acceptance, Planned/Realized compatibility, gateway,
devices, hosted migration parity and final activation remain separate gates.
See [the release register](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).

No push, merge, hosted/staging/production connection, deployment, activation,
historical-plan reinterpretation or protected A5/A6 modification occurred. The
owned PostgreSQL and PostgREST processes were stopped after verification.

## Reproduction

From `backend`, using the existing development venv and no `.env`:

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests benchmarks
python -m mypy --explicit-package-bases scripts/verify_v6_exact_search.py scripts/verify_v6_multi_session.py scripts/verify_v6_frequency_policy.py scripts/verify_v6_evidence_network.py
python -m benchmarks.v6_planner_performance --variant optimized --output <new-file>
```

Use the existing `scripts.verify_v6_final_sql` with a new owned cluster/database,
explicit loopback port/psql/data directory and `--execute-disposable-local-only`.
Run the regular frequency runner in a fresh migrated database. Synthetic
multi-session runners use separate fresh clones plus only the existing temporary
test-role membership; revoke it afterwards. The new high-budget command is:

```text
python -m scripts.verify_v6_exact_search --execute-disposable-local-only --private-output <new-trace>
python -m scripts.verify_v6_exact_search --execute-disposable-local-only --reload <trace>
```

These require an explicit loopback `WOMBO_V6_DISPOSABLE_PG_DSN` and local `psql`.
The normal network runner is `scripts.verify_v6_evidence_network`, with its
existing `--frequency-suspension-retry` flag; the high-budget network fixture
uses 105-minute synthetic history and its existing `--multi-session-test-only`
flag. Create only local synthetic signing keys; never copy hosted credentials.
