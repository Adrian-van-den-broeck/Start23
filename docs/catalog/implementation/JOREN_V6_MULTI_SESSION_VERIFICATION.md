# Multi-session verification

12 November 2026, Europe/Amsterdam. Base
`b87d0e4f82702e168ec16441bbe7661fd0d10cb2`; branch
`feat/joren-v6-multi-session-planning`. Exact tested implementation identity and
execution/source hashes are in [verification.json](multi-session/verification.json).
The final report-inclusive commit is reported separately to avoid a self-hash.

## Executed checks

| Check | Result |
| --- | --- |
| Full backend pytest | 2,727 tests; accepted baseline 2,675 plus 52 new cases |
| Multi-session source/selector tests | 51 cases, including 30 independent exhaustive-oracle seeds |
| Real HTTP/spawned-worker multi-session draft | One additional five-card, duplicate-template, distinct-date, undo/manual-submit regression |
| Full mobile Jest | 911 tests, 87 suites; baseline 908 plus three new component/controller cases |
| Strict TypeScript and unused locals/parameters | Both passed |
| Ruff lint and full formatting | Passed; 230 backend files formatted |
| Strict mypy | App/tests/benchmarks and both changed verification scripts passed |
| Real PostgreSQL migrations | All 62 replayed on new disposable PG 17.11 databases |
| pgTAP | All 680 assertions in 36 suites passed |
| Multi-session PostgreSQL lifecycle | Seven groups passed, using normal onboarding, real RPCs, real transactions and spawned planning |
| Multi-session concurrency/rejection | Four groups passed: duplicate generation, competing swipes, move/edit/confirmation races, rejection replay |
| Unknown commit outcome | Two actual TCP disconnects after successful PostgREST commits; exact A5/move receipt recovery |
| Process and database restart | Fresh Python reload plus real PostgreSQL stop/start; exact five-member mapping and unchanged evidence hash |
| Independent identity audit | Zero orphaned activity FKs, missing active memberships, duplicate logical/physical memberships or activity attachments |
| Historical planner corpus | All 40 input fingerprints, outcomes and existing independent checks equal accepted final-policy evidence |
| Accepted reference outputs | All 26 retained; original regression artifact SHA-256 `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` unchanged |
| Known legacy timeout | `current:build_4`, unchanged 8-second corpus bound |
| Android debug | Offline x86_64 build passed, 692 actionable tasks; no install/device test |
| Catalog preservation | Historical 325 templates/loads unchanged across V6 migration boundary; all 77 V6 revisions INACTIVE |

One intermediate full Jest run had a pre-existing navigation test exceed its
unchanged 5-second timeout while the Android native build was running. The final
full run, without that build, passed all 911 tests. No timeout, assertion or
golden was relaxed. Initial SQL harness assumptions of 409 for expired/obsolete
locators were corrected to the existing 404 contract; application behavior was
not changed to fit the harness.

The performance corpus emits a different report envelope from the final-policy
report (including null metadata and no prospective annotations). Verification
compared actual outcomes, input hashes and independent checks across all 40
cases, rather than rewriting those historical annotations to manufacture a
byte-identical report. All actual planner results remain equal.

## Scenario coverage

The new tests exercise the legacy maximum-only/default path; 2/2/1 and 2/1/1
requests; actual RUN-, BIKE- and SWIM-only goals with two sessions; partial and
rest weeks; exact Decimal equality and a 1e-60 over-budget boundary; allowed and
forbidden repeats including a retained prefix; appending an occurrence beside a
retained same-template occurrence; per-sport HIGH aggregation, exactly 20% and
strict excess; limited/same-day dates; existing HIGH spacing conflicts; injury,
capability and sport caps; deterministic reruns and bounded exhaustion.

HTTP and durable SQL cover duplicate-template pending replacement, sibling/date
preservation, pending-only submit, separate confirmation, stale/foreign rejection,
idempotent retry, check-in attachment, exact physical activity registration,
completed same-sport sibling preservation, rollback, real concurrent operations,
terminal rejection replay and process/database restart. Existing A3–A9 and
Realized V2 suites remain in the full backend/mobile/SQL runs, including measured
priority, unsupported fallback rejection, cancellation and authorization behavior.
No existing test is weakened or superseded.

## Commands and environment

From `backend`, using the existing pinned development environment without .env:

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests benchmarks
python -m mypy --explicit-package-bases scripts/verify_v6_multi_session.py scripts/verify_v6_evidence_network.py
python -m benchmarks.v6_planner_performance --variant optimized --output <private-file>
python -m benchmarks.v6_multi_session_evidence --private-output <private-file>
```

From `mobile`, lockfile-installed offline dependencies:

```text
npm test -- --json --outputFile=<private-file>
npm run typecheck
npm run check:unused
```

The existing `scripts.verify_v6_final_sql` created fresh databases, checked their
loopback PG17/cluster identity, replayed migrations and parsed every TAP plan and
assertion. Its explicitly documented A5 onboarding/fingerprint fixture overlay
was used; the original A5 SQL and protected worktree remain unchanged. The
original uncorrected fixture failure is still distinguished from the passing
overlay, as in accepted evidence.

After an empty migrated database, execute:

```text
python -m scripts.verify_v6_multi_session --execute-disposable-local-only --private-output <trace>
python -m scripts.verify_v6_multi_session --execute-disposable-local-only --concurrency-output <checks>
python -m scripts.verify_v6_multi_session --execute-disposable-local-only --reload <trace>
```

These runners require an explicit loopback-only `WOMBO_V6_DISPOSABLE_PG_DSN`.
The second runner uses the second synthetic athlete after the first runner.
The trace's TEST_ONLY history overlay supplies 35 minutes per sport through
normal onboarding. It must not be applied to an existing athlete database.

The real network probe uses a separate fresh migrated database with that same
explicit synthetic history and a locally generated signing key:

```text
python -m scripts.verify_v6_evidence_network --execute-disposable-local-only --multi-session-test-only --url <loopback-postgrest> --week-start 2026-10-26 --signing-secret-file <local-test-key> --private-output <file>
```

PostgreSQL/PostgREST binaries were reused read-only from the existing portable
runtime. New cluster data, logs and keys stayed in this worktree's ignored
`.runtime`. The Android source copy/dependencies/generated native project stayed
in a separate temporary directory with a short Windows junction and existing
local SDK/Gradle caches. No hosted environment file or credentials were copied.
The successful command was `gradlew.bat assembleDebug --offline --no-daemon
-PreactNativeArchitectures=x86_64`. Generated path/setup failures before that
successful build are retained in private logs; no product code was modified to
work around them.

## Open decisions and release gates

No approved real-athlete frequency resolver exists. The safe one-per-sport
default remains active in the inactive V6 adapter unless a private explicit
authorization is supplied. All new frequency examples are TEST_ONLY. The
budget-300 example deliberately demonstrates honest bounded search exhaustion;
it does not publish a suboptimal arbitrary week or claim no feasible week exists.

Operational swim-time acceptance, individual exceptional-duration suitability,
named scientific review, official Planned/Realized fallback compatibility,
GoTrue-issued sessions/full gateway isolation, actual Android/iOS device flows,
hosted migration/release authorization and final V6 activation remain open.
SQL GUC claims and local signed PostgREST tokens are not GoTrue/gateway proof.
Jest controllers and an APK are not device verification. See the
[Dutch release register](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).

No push, merge, deploy, hosted migration, staging/production connection, source
activation or protected A5/A6 change was performed. All task changes are local.
