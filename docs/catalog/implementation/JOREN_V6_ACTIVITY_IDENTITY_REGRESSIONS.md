# V6 physical activity identity regression evidence

2026-11-08. Branch `feat/joren-v6-evidence-safe-rescheduling`.
Base `1dbe10b1a419c689f189faf077f4178eaa4f6310`.
The final result ledger is `evidence-rescheduling/verification.json`.

Final evidence review: 2026-11-12, Europe/Amsterdam. Full application, network,
restart and Android runs were executed on 2026-11-08. The final migration replay
and complete post-activity route/SQL workflow were repeated on 2026-11-12. The
last schema review added an owner index for membership reads and account cascades;
this changes no lifecycle semantics.

| Check | Executed result |
| --- | --- |
| Full backend pytest | 2,675 passed; no skips/failures; one existing Starlette deprecation warning |
| Full mobile Jest | 908 passed in 86 suites; no skips/failures |
| TypeScript | Strict typecheck and unused-local/parameter checks pass |
| Ruff | Lint passes; 224 files already formatted |
| Strict mypy | 210 app/test/benchmark sources and five SQL/network verification scripts pass |
| PostgreSQL 17.11 / pgTAP 1.3.4 | 62 migration candidates replayed; 36 suites / 680 assertions pass |
| Post-activity route/SQL workflow | 11 preservation, rollback and concurrency groups pass; separate-process reload passes |
| Original V6 lifecycle route/SQL workflow | All nine groups pass with effective membership enumeration |
| PostgREST 16.5 connection loss | Two actual committed-response disconnects recover exact A5/move results |
| Independent identity queries and PostgreSQL restart | Zero orphaned FKs, missing active evidence memberships or duplicate logical/physical/activity mappings; unchanged evidence hash |
| Historical planner | All 40 outcomes/input fingerprints and all 26 accepted references retained; identical canonical hash below |
| Android | Offline x86_64 debug APK build passes; 497 tasks, 4m59s; no installation/device test |

The historical planner result SHA-256 remains
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.
The eight-second `current:build_4` diagnostic timeout and bounds remain unchanged.
Historical catalog preservation checks retain 325 template/load pairs with hash
`eca6cacd0a2639d197ca84c9952065ceb0890d394a23e05f63f10ab56a678818`.
All 77 V6 source revisions remain INACTIVE.

Initial incomplete sparse checkout runs lacked tracked CSV/JSON fixtures. Those
fixtures were restored without edits. Existing five-second mobile tests timed out
under concurrent native-build load; the final full run passed without changing
timeouts. Android retries corrected cache access, the Windows path limit and a
temporary-copy omission. The historical SQL probe was adapted to enumerate
carried load rows and qualify a joined column. These failed invocations are not
counted as successful verification.

## Actual SQL and route execution

`backend/scripts/verify_v6_evidence_rescheduling.py` exercises actual FastAPI
routes with real PostgreSQL transactions. Its local transport starts a separate
psql connection per request and supplies synthetic SQL JWT claims. It does not
mock persistence. It does not establish GoTrue-issued sessions or a complete
Supabase gateway. Only explicitly selected disposable loopback databases are
accepted; no `.env` or hosted connection is used.

The runner proves:

- A completed RUN retains its physical FK, prescription and all recorded evidence
  when an unfinished BIKE moves; only one new physical row is inserted.
- Multiple completed siblings survive repeated later revisions. A held scheduled
  sibling can subsequently receive activity on its original physical row.
- A linked sibling awaiting RPE can be carried without manufacturing completion.
- Measured observations retain priority; the Realized V2 result remains
  `observation_selected`, with no new Session-RPE fallback.
- V16 expected physical occurrences include the retained rows once. Original
  activity and calculation/source versions remain reachable.
- Independent queries compare activities, metrics, observed loads, Realized V2
  inputs/calculations and registration events before/after each preservation
  operation. Original physical prescription rows are separately compared.
- Direct membership update/delete and late insertion into a confirmed revision
  reject. SQL rollback retains all original evidence.
- Injected failure at the receipt insertion, after target/membership/pointer
  writes, rolls the whole operation back.
- Two competing moves commit one revision. Duplicate concurrent operation keys
  return the same response and create one revision.
- Move versus registration/activity attachment has one winner; a winning target
  attachment blocks movement even before RPE completion.
- Move versus pending creation has one authoritative transition. An incompatible
  pending approval and a move both reject without losing evidence; rejecting the
  proposal restores permitted sibling movement.
- Completed, explicitly registered, stale, foreign and cross-week requests reject.
- A new Python process retrieves the same latest plan, calendar and activities;
  the calendar contains three distinct logical occurrences and no duplicates.

`verify_v6_evidence_network.py` separately uses actual PostgREST 16.5 commits and
a loopback proxy that closes the TCP connection after the upstream 200 response
but before forwarding headers. A5 attachment and post-activity date-move requests
surface 503, then retries recover the same original receipt. Exactly two plan
revisions exist after proposal confirmation and one move; completed sibling
evidence is unchanged. Local signed service JWTs are synthetic, not GoTrue tokens.

## Reproduction

Use PostgreSQL 17.11, pgTAP 1.3.4 and PostgREST 16.5 with explicitly disposable
local data. `verify_v6_final_sql` creates a new uniquely named database and replays
all migrations plus pgTAP. It checks the cluster path, host and server identity.
The A5 fixture overlay supplies complete synthetic onboarding and the previously
reviewed 32-character fingerprint; no original A5 assertion or production
eligibility rule is weakened. The protected fixture and release branch are intact.

```text
python -m scripts.verify_v6_final_sql --execute-disposable-local-only --psql <local-psql> --cluster-directory <disposable-cluster> --port 55452 --database wombo_v6_final_<unique> --private-output <new-directory>
python -m scripts.verify_v6_evidence_rescheduling --execute-disposable-local-only --output <new-directory>
python -m scripts.verify_v6_evidence_rescheduling --execute-disposable-local-only --output <same-directory> --reload
python -m scripts.verify_v6_evidence_network --execute-disposable-local-only --week-start <unused-monday> --url http://127.0.0.1:55453 --signing-secret-file <ignored-local-key> --private-output <new-file>
```

The SQL transport requires `WOMBO_V6_DISPOSABLE_PG_DSN` and rejects non-loopback
hosts. Private runtime data, signing keys and detailed SQL transcripts stay
ignored. The committed fixture contains only synthetic public route responses.

## Mobile and historical regressions

`V6EvidenceRescheduling.test.tsx` consumes the recorded real PostgreSQL/FastAPI
responses using the existing planning/calendar providers. It checks retained
completed identity/status/date, replacement of the moved active date, source
details, physical activity locator, remount after multiple completions, no calendar
duplicates, conflict/reload messaging and unknown-outcome recovery. Mobile
transport, tokens and secure storage are simulated; these are component tests,
not actual Android/iOS-device tests.

The final ledger records full backend/Jest totals, strict TypeScript/unused-code,
Ruff/formatting/mypy results, all applicable SQL suites, 40 planner cases, all 26
accepted references, unchanged `current:build_4` timeout, source hashes and the
Android build result. Initial sparse-checkout fixture omissions and resource/path
failures are recorded separately from successful final invocations. No timeout or
historical expected result is weakened.

Implementation commit: `057d88bb41aa8f73c1e1e66b0e7d0059754ca527`.
Evidence reviewed 2026-11-12; the documentation-only successor records the
verification manifest and source hashes. V6 remains inactive.
