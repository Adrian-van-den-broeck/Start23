# Five forward corrections and database regression

**EXECUTED / PASS. No new schema defect was found and no migration was added.**
The five existing corrections were replayed independently, one at a time, after
cloning only this task's disposable 52-migration historical database and applying
the original two V6 migrations. The resulting 54-to-59 migration audit is separate
from the normal complete-chain database.

For each correction, SQL inventories before and after compare existing function
ACLs, owner, SECURITY DEFINER status, search path/configuration and actual execute
rights for anon/authenticated/service_role. They also compare relation grants,
ENABLE/FORCE RLS, policies, database role properties and memberships. All those
existing authority properties remain identical. The two newly introduced private
trigger functions are noncallable by all three external roles. The function-body
changes are exactly the expected ones in [the audit ledger](forward-corrections.json).

| Correction | Independent assessment and executed behavioral evidence |
| --- | --- |
| Segment compatibility | Canonical immutable source segments replace caller content after the historical trigger. The segment suite checks all 77 rows and no athlete EXECUTE grant; actual lifecycle writes also succeed. |
| Frozen snapshot precedence | Only the two JSON-extraction expressions gain parentheses. The existing writer's authority is identical. Pending edits, source/context tampering, competing swipes, immutable receipt replay and confirmation conflicts execute in the real lifecycle. |
| Nested V2 approval custody | Only v13/v14/v15 internal identity guards change; direct execution stays service-only. The internal chain permits the owner and rejects a foreign subject; authenticated direct history calls still reject. Own confirmation succeeds in real SQL and signed-token HTTP. |
| PT409 business errors | Only four established deterministic business guards' SQLSTATE changes from 40001 to PT409. Their conditions and calculations are unchanged. The exact 36-function business-conflict inventory passes, as does the full 22-assertion Realized V2 suite. |
| V6 insert custody | Direct authenticated revision/workout insertion with spoofed `critical_write` rejects 42501. The workout trigger uses PostgreSQL's protected ROLE state, and frozen revisions reject added workouts even administratively with 55000. Historical dispatch remains usable. No new callable SECURITY DEFINER grant is introduced. |

The sequential audit confirms the corrections do not change existing policies
or role memberships; the full A3–A9 / historical suites and byte-identical corpus
provide separate compatibility evidence. These checks establish the stated
boundaries, not a general proof against every possible security defect.

## Historical retention and exact values

All 59 migration files have the same Git content as the requested baseline.
[The exact ledger](migration-ledger.json) records the baseline Git blob SHA-256,
executed filesystem SHA-256, LF-normalized executed-text SHA-256 and prior report
hash for every file. The first 54 filesystem hashes match the prior ledger.
The five correction files had LF in the prior worktree and CRLF after this
Windows checkout; their LF execution text matches the original Git blob and
prior hash exactly. No historical migration edit is concealed by that distinction.

Before/after comparison retains 325 historical templates and 325 corresponding
private load rows without recalculation. The only row-shape normalization removes
the new `inactive_v6` key from final template JSON; it changes no old field and
does not exclude an old row. The existing numerical runner verifies all 77
official values, source documents and rational provenance, unscaled PostgreSQL
numeric precision, strict over-budget preservation, aggregate equality and the
real numeric-equality constraint. All 77 new revisions remain INACTIVE.

## Rollback rehearsal

Although this task adds no schema migration, the disabling rehearsal was repeated
on **`wombo_v6_rollback_2026110801`**, cloned only from this task's completed
disposable lifecycle database. The unchanged fixture
`supabase/tests/fixtures/v6_disposable_forward_rollback.sql` requires an explicit
disposable database name before revoking the four V6 service generation/context/
catalog/retry RPCs. It does not delete or rewrite data.

**EXECUTED / PASS:** exact confirmed public read equality and unchanged hashes for
all nine private source/snapshot/occurrence/receipt/load/V2-evidence tables.
Actual service calls to generation and the catalog fail with 42501. Historical
RPCs and authenticated retained-locator reads remain available.
[Retention hashes](rollback-retention.json) preserve the before/after result.

The complete SQL directory then passes **33/33 suites and 644/644 assertions**,
including all 29 A5 assertions with the same explicit overlay. The final
[per-assertion rollback ledger](pgtap-rollback.json) contains no skip or TODO.
Three actual composite-owner FK violations and full rollback of their preceding
synthetic revision/workout writes also pass in the unchanged lifecycle runner.
No shared or unknown database was reset, dropped or cleaned.

This proves the local disabling-and-retention scenario. Hosted application
deployment, migration/advisors, actual user-data migration and execution of a
rollback in production remain **NOT EXECUTED** and unauthorized.
