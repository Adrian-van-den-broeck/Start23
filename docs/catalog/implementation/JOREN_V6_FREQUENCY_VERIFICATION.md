# Frequency policy verification

13–14 November 2026, Europe/Amsterdam. Base
`6745c903ae045b3c3215e928fb53c36cb119a741`; isolated branch
`feat/joren-v6-approved-frequency-policy`. Final report-inclusive SHA is supplied
in the delivery message. [Verification manifest](frequency-policy/verification.json)
records execution/source hashes without a self-referential commit hash.

| Executed check | Result |
| --- | --- |
| Full backend pytest | 2,759 passed; original 2,727 plus 32 new resolver/transport cases |
| Full mobile Jest | 929 passed in 88 suites; original 911 plus 18 card/transport cases |
| Strict TypeScript and unused checks | Passed |
| Ruff and formatting | Passed; 234 Python files |
| Strict mypy | App/tests/benchmarks: 217 files; both changed verification scripts also pass |
| Real PostgreSQL 17.11 | All 63 migrations replayed into a new owned loopback cluster |
| pgTAP / ownership / grants / RLS | 722 assertions in 37 suites pass, including 42 new policy assertions |
| Actual policy RPC/HTTP races | Nine groups pass, including independent connections waiting on frequency locks |
| Lost network acknowledgement | Four actual TCP disconnects after successful PostgREST commits; exact recovery after suspension |
| PostgreSQL restart and fresh Python processes | Original A5 receipt, immutable snapshot hash and five-occurrence identity mapping retained |
| Historical corpus | All 40 input fingerprints, outcomes and independent checks match accepted evidence |
| Accepted reference outputs | All 26 retained; original regression SHA-256 `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` unchanged |
| Search proposal matrix | All 15 contexts repeated; same three honest incomplete outcomes |
| Android debug | Offline x86_64 build succeeds; 692 actionable tasks; no install/device verification |
| Catalog | 325 historical templates/loads preserved; all 77 V6 revisions remain INACTIVE |

Resolver coverage includes null, zero, requested-above-maximum, maximum-only,
M=0, absent/revoked/suspended/expired/superseded decisions, missing evidence,
disabled reviewer, wrong timezone, changed assessment evidence, reconfirmation,
retained counts, unmatched activities, frozen restoration and TEST_ONLY rejection.
Positive numerical examples are explicitly hypothetical in-memory value inputs;
they are not enrolled reviewers or issued database authorizations.

The real-path SQL tests prove no operator enrollment, no application issuance
permission, owner isolation, immutable preference history, exact committed retry,
CAS conflicts, explicit illness/injury/interruption and reconfirmation without
creating a maximum. Explicit account deletion preserves the existing cascade
contract. No real authorization/reviewer row was manufactured to make these pass.

The RPC/HTTP runner holds a completed worker before persistence, invalidates its
context and proves full rollback, including an open A5 check-in. It tests pending
replacement and swipe races, then starts approval while another connection holds
an uncommitted suspension. Approval waits and rejects after that suspension commits.
Another test blocks A5 attachment after the writer owns the frequency lock:
invalidation waits, creation commits first, the original attachment remains readable,
and subsequent activation rejects. No second approval state machine is introduced.

Swipe submission creates the proposal and finalizes the existing draft locator
in one database transaction. An injected late draft-write failure rolls both back;
a committed response loss recovers the original proposal after suspension without
new generation. Occurrence/template pairing is validated independently of schedule
order. SQL-backed zero preferences generate no new sessions; clearing them to null
restores the default request. Retained sessions above a tightened valid maximum
cause an explicit conflict in Python and SQL, without removing occurrences.

The TCP proxy receives actual successful local PostgREST transactions and closes
the client socket before returning response headers. A completed sibling's physical
identity, activity evidence and measurements survive the moved-workout retry after
suspension. A second athlete's committed A5 creation is recovered after illness;
new approval rejects. The fourth disconnect covers atomic swipe submission and
its original receipt replay after suspension. Tokens are locally signed synthetic
claims, not GoTrue. An explicit full stop/start of this task's PostgreSQL cluster
was followed by fresh-process A5/snapshot and five-occurrence reload checks.

The inherited five-occurrence SQL lifecycle uses only explicit TEST_ONLY controls
and temporary harness-role permissions. It exercises duplicate-template identities,
pending replacement, completed same-sport siblings and immutable move receipts.
It is separate from the regular resolver; it issues no real frequency decision.
The application migration grants none of those test permissions.

Original A5 SQL is unchanged. Its previously reviewed onboarding and 32-character
input-fingerprint overlay is used explicitly by the SQL runner. The uncorrected
historical fixture's known prerequisite failure is not claimed as passing.
Only two existing inventories change: the OpenAPI allowlist adds the two new
paths, and the SQL business-conflict inventory includes the new preference CAS.
No physiological assertion, timeout, historical output or protected A5/A6 source
is weakened or rewritten.

An initial Android source copy hit Windows path/CMake problems. The final build
uses a fresh shorter temporary copy, unchanged lockfile and existing offline
SDK/Gradle caches. It contains no copied environment/hosted credentials. Jest
exposed that the existing error-code regex discarded version digits; admitting
safe lowercase versioned codes fixed the actual incomplete-search presentation.
No deadline was extended. Intermediate failures remain in ignored local logs.

Reproduction, from `backend`, with explicit loopback-only disposable PG settings:

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests benchmarks
python -m mypy --explicit-package-bases scripts/verify_v6_frequency_policy.py scripts/verify_v6_evidence_network.py
python -m scripts.verify_v6_final_sql --execute-disposable-local-only --psql <binary> --cluster-directory <owned-cluster> --port <port> --database wombo_v6_final_<unique> --private-output <new-output>
python -m scripts.verify_v6_frequency_policy --execute-disposable-local-only --private-output <new-output>
python -m scripts.verify_v6_evidence_network --execute-disposable-local-only --frequency-suspension-retry --url <loopback-postgrest> --week-start 2026-10-26 --signing-secret-file <local-test-key> --private-output <new-output>
python -m benchmarks.v6_planner_performance --variant optimized --output <new-private-output>
```

The policy runner requires an empty migrated database and seeds ordinary synthetic
onboarding through the existing fixture. Network and historical multi-session
runners use separate fresh clones of that migrated empty database. Mobile commands
are `npm test -- --runInBand`, `npm run typecheck` and `npm run check:unused`.
Android uses `gradlew.bat assembleDebug --offline --no-daemon -PreactNativeArchitectures=x86_64`.

**Open verification/operational gates:** end-to-end issuance and revocation of a
genuinely reviewed numerical maximum cannot be executed without the actual
designated reviewer/operator, permission evidence and individual decisions.
That route intentionally remains unavailable; pure inputs and TEST_ONLY examples
do not close this gate. GoTrue/full gateway, real Android/iOS devices, hosted
advisors/migration parity and external scientific/operational review were not
executed. The known search-performance failures remain release blockers.

No push, merge, hosted/staging/production connection, deployment or V6 activation
was performed. See [remaining gates](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).
