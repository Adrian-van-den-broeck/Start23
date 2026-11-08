# WOMBO V6 final database and authentication verification

8 November 2026, Europe/Amsterdam.

**WOMBO V6 DATABASE VERIFIED — FULL AUTH STACK PENDING**

Branch: `verify/joren-v6-final-auth-security`.
Exact starting SHA: `798e4a00d187474cefe00e8794f04c42422cf72b`.
Verified implementation SHA: `479709f638aa97606bd6226e7b8b44b536b8a2ee`.
The subsequent evidence commit is reported in the delivery response. Reports
cannot embed their own future Git commit hash. [Report hashes](report-hashes.json)
identify the immutable evidence bytes; no earlier report was rewritten.

## Executed results

| Check | Status | Actual evidence |
| --- | --- | --- |
| Ordered project migrations | EXECUTED / PASS | All 59 in a newly created disposable PostgreSQL 17.11 database; no schema changes in this task. |
| Historical prerequisite schema | EXECUTED / PASS | Separate database with the first 52 migrations, ending at `20261103142339`; original and corrected A5 reproduced independently. |
| Complete final SQL directory | EXECUTED / PASS | **33/33 suites, 644/644 assertions**, zero failures, skips or TODOs, with the explicit A5 fixture overlay. Every original assertion executes. |
| Corrected A5 on historical schema | EXECUTED / PASS | **29/29**, including synthetic attachment PT409 and all later recovery/approval/ownership assertions. |
| A5 overlapping real creates | EXECUTED / PASS | Existing concurrency runner with the same two disclosed fixture corrections: one pending attachment, identical locators and exact replay. |
| PostgreSQL V6 lifecycle | EXECUTED / PASS | Actual separate-process create/resume/reload, synchronized competing swipes, duplicate keys, swipe/confirmation conflict, rollback, immutable terminal retries, confirmed inserts and three composite-owner FK rollback cases. |
| Official numerical/source persistence | EXECUTED / PASS | All 77 Decimal/rational/source/workbook round trips in the existing SQL runner; official method unchanged. |
| Historical catalog/load preservation | EXECUTED / PASS | 325 templates and 325 associated load rows retain every pre-existing value. Only the new schema column `inactive_v6=false` is excluded when comparing the old row shape. All 77 source revisions remain INACTIVE. |
| Five forward corrections | EXECUTED / PASS | Independent sequential before/after authority inventories plus existing behavioral regressions; no expanded execution grants, RLS, table grants or role memberships. |
| Actual committed HTTP response loss | EXECUTED / PASS | Write commits at PostgREST, downstream acknowledgement is withheld, same-key retries recover one immutable receipt and exactly one new revision. |
| Directly signed-token PostgREST | EXECUTED / PASS | **38 HTTP checks**, two SQL fixture subjects, PostgREST 16.5; signature verification and database ownership isolation. **Not GoTrue/gateway evidence.** |
| Forward disabling rehearsal | EXECUTED / PASS | Separate clone; confirmed public read and nine private-table hashes unchanged; generated-write/catalog calls denied with 42501. Complete **33/33 suites, 644/644 assertions** also pass after disabling. |
| Full backend pytest | EXECUTED / PASS | **2,586 passed**, zero errors/failures/skips; one existing Starlette/httpx warning, 243.53 seconds reported by pytest. Includes Realized V2, A3–A9, identity, OpenAPI and recursive confidentiality safeguards. |
| Ruff lint/format, strict mypy | EXECUTED / PASS | 211 formatted sources; 205 app/test/benchmark sources and four integration runners typecheck. |
| Unchanged historical corpus | EXECUTED / PASS | All **40** cases and **26** accepted reference completions preserved byte-for-byte; sole `current:build_4` diagnostic timeout retains its eight-second deadline. |
| GoTrue-issued accounts/sessions | BLOCKED — ENVIRONMENT | **Zero** genuine Auth accounts, issued sessions or real-auth checks. |
| Complete Supabase gateway | BLOCKED — ENVIRONMENT | **Zero** gateway checks; no Docker/Podman engine or WSL distribution, and Windows is unsupported by the official native runtime. |

Detailed records: [final pgTAP](pgtap-final.json),
[rollback pgTAP](pgtap-rollback.json), [exact migration ledger](migration-ledger.json),
[lifecycle](lifecycle.json), [backend](backend.json),
[historical corpus](historical-corpus.json), [environment](environment.json).
The [security/rollback assessment](SECURITY_AND_ROLLBACK.md) and
[reproduction guide](REPRODUCTION.md) describe their precise scopes.
The per-assertion pgTAP records enumerate the actually received TAP output,
check sequential assertion numbers and require a complete matching plan.
Prepared scenarios are never included in the executed totals.

## Failures retained as diagnostic evidence

The unchanged original A5 file still fails when run without its disclosed
overlay. Both historical and final schemas execute nine assertions: eight pass,
assertion 6 fails with onboarding 23514, then creation aborts. The remaining
20 original assertions are **NOT EXECUTED in those diagnostic runs**. They all
execute and pass in the corrected runs. [A5 root cause and separate proposal](A5.md)
explain the missing onboarding data and the second, previously masked,
64-versus-32-character input fingerprint defect. No business error was changed
and no application eligibility guard was bypassed.

The first onboarding-only overlay still failed at the fingerprint constraint.
An exploratory evidence query also referenced a nonexistent `is_active` column;
the inventory was corrected to the actual `inactive_v6` column. An early
historical comparison initially included that newly added column in the final
row shape. The verified comparison explicitly removes that one new key and
checks every pre-existing field. These harness failures are retained locally,
not counted as successful runs or application defects.

## Preserved boundaries and remaining gates

There is no production or staging connection, credential, migration, deployment,
push, merge, catalog activation, default-planner change or mobile implementation.
The protected A5/A6 worktree remains clean at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`; the requested starting worktree stays
unchanged. All existing migrations and historical A5 assertions remain unchanged.
The only implementation additions are verification tooling and synthetic fixture
data; the additional attributes preserve new evidence line endings.

[Authentication gaps](AUTHENTICATION.md) remain explicit release gates.
Hosted migration/advisor checks, full Supabase extension/default-role parity,
modern API-key routing, real issuer/JWKS integration and full Auth sessions are
**NOT EXECUTED** here. Mobile logical/physical occurrence consumers, calendar and
registration integration, actual Android/iOS/device checks and A5/A6 release
adoption remain **NOT EXECUTED**. Existing V6 check-in generation stays fail-closed.
No mobile implementation was started.

Independent accountable physiological review and its external record, operational
review of estimated swimming time and long durations, planned/realized mapping,
catalog activation and release approval remain separate gates. Passing these
software/database checks supplies no new physiological approval. V6 remains
inactive in production.
