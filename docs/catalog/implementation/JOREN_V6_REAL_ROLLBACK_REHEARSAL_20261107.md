# V6 forward rollback rehearsal ? 7 November 2026

**EXECUTED/PASS for disabling V6 generation and retaining data.**
A separate database, `wombo_v6_rollback_20261107`, was cloned only from the disposable
final-gate database after real create/swipe/confirmation/rejection/restart tests.
It contained only the historical catalog seed and synthetic fixture accounts.
No shared, hosted, staging or production environment was reset or cleaned.

The rehearsal executed
`supabase/tests/fixtures/v6_disposable_forward_rollback.sql`. Its explicit disposable
name guard precedes the revocations. This is a test fixture, not an automatic
deployment migration. It models the documented forward strategy:

1. The app retains its historical default and does not inject the V6 adapter.
2. Revoke service execution of the V6 generated-write, private catalog, context and edit-retry RPCs.
3. Preserve authenticated `get_v6_weekly_plan` for retained locators and preserve every historical approval/rejection/read/write RPC.
4. Preserve all inactive source revisions, exact values, mappings, frozen evidence, confirmed snapshots and immutable receipts. Do not expire, replace or reinterpret any plan.

Observed results:

- Exact confirmed public read is identical before and after revocation.
- Hashes of all source/snapshot/occurrence/receipt/private-load/V2-evidence tables are identical.
- Historical catalog/load data equals the pre-V6 snapshot: all 325 rows retained.
- Actual service calls to disabled generation and catalog RPCs reject with 42501.
- Historical planning and the supported SQL suites still execute: **32/33 suites pass**, with 623 passing assertions and the same one failing assertion in the unchanged A5 fixture. The remaining A5 assertions are NOT EXECUTED after its abort.

[Data-retention results](postgres-verification-20261107/rollback-results.json) and
[SQL results](postgres-verification-20261107/pgtap-rollback-results.json).
This closes the local rehearsal slice, not the A5 test gate, future mobile locator
integration, or authorization to apply a rollback in any hosted environment.
