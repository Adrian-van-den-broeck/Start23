# V6 remaining gates after real database verification ? 7 November 2026

**WOMBO V6 DATABASE VERIFICATION PARTIAL ? EXACT BLOCKERS DOCUMENTED**

| Gate | Actual status |
| --- | --- |
| PostgreSQL migrations and V6 runtime | EXECUTED/PASS: 59 migrations on stock PostgreSQL 17.11; original candidates preserved plus five forward corrections. |
| V6 grants/RLS/source/numeric/transaction tests | EXECUTED/PASS, including synchronized races, process restart, lost commit acknowledgement, exact retries, insert custody and composite ownership FKs. |
| Entire SQL directory | EXECUTED/FAIL: 32/33 suites pass. The unchanged A5 fixture lacks current onboarding completion; assertion 6 fails and later assertions do not run. The same failure exists before V6. No A5/A6 changes were made. |
| Local two-subject signed-token HTTP | EXECUTED/PASS: 38 checks, actual local PostgREST signatures/RLS and own confirmation. |
| GoTrue / Supabase gateway / ES256-JWKS sessions | NOT VERIFIED. Requires an explicitly disposable full Supabase stack and actual session issuance; local HS256 tokens do not substitute for it. |
| Exact official numerical persistence | EXECUTED/PASS: all 77 canonical final Decimals, rationals, source/workbook evidence and exact comparisons. |
| Forward-only disabling rehearsal | EXECUTED/PASS for retained snapshots, private provenance, denied new generation and historical operations; the same A5 SQL gate remains failed. |
| Backend / strict typing / historical corpus | EXECUTED/PASS: 2,586 tests, Ruff, strict mypy; 40 byte-identical cases and 26 accepted completions; only the unchanged allowed diagnostic timeout remains. |
| Hosted migration/advisors and complete Supabase extension parity | NOT EXECUTED. No hosted credentials or connection was used. The local subset does not certify the intended hosted role/extension deployment. |
| Mobile/device and logical/physical occurrence consumers | NOT EXECUTED. No mobile integration, calendar/activity/registration translation or device release was started. |
| V6 check-in / A5-A6 release | V6 check-in generation stays fail-closed; separate integration/release work is not authorized here. Existing release worktree is unchanged. |
| Estimated swim time, long-duration evidence, future planned/realized mapping | Existing operational review/fail-closed gates remain. No new physiological or safety decision was invented. |
| Independent accountable review, catalog activation and release | Remain separate approvals. All 77 revisions are INACTIVE; startup/default planner unchanged. |

The precise SQL blocker is a stale A5 test fixture under current onboarding
eligibility, not proof that the A5 production implementation is defective. Its
remaining assertions cannot be claimed as passing. Resolving that fixture needs
a separately scoped A5 verification change, respecting the explicit exclusion
in this task. No eligibility requirement or test assertion was weakened.

The five corrective migrations remain local candidates awaiting review; passing
this harness does not apply them to any hosted environment. No push, merge,
deployment, activation, mobile release or A5/A6 release modification occurred.
