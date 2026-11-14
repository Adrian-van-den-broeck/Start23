# WOMBO V6 authenticated lifecycle and A5 boundary review

14 November 2026. Base `dbeb9596f42f0504e428afbf5eddc75eaa7d20da`.

**Genuine-session lifecycle: BLOCKED — ENVIRONMENT.** No real signup/login,
gateway-backed onboarding or logout/login restoration was performed. Passing
ASGI/SQL or mobile mock tests are not relabeled as an authenticated lifecycle.

## Required lifecycle on the supplied full stack

Every real-session step below is **NOT EXECUTED / BLOCKED — ENVIRONMENT**.

| Step | Required proof |
| --- | --- |
| 1. Signup/login | Real password signup/login through gateway; distinct Auth/opaque athlete identities |
| 2. Complete onboarding | Current monitor, timezone, physiology/history, structured race and active required-discipline zone prerequisites; complete via normal RPC/API and preserve onboarding fingerprint |
| 3. Optional preference | Save null/one/zero preference via existing revision/operation contract; above-one preference never creates a maximum |
| 4. A5 check-in | Start/resume, save current context and confirm its fingerprint/revision normally |
| 5. Generate V6 proposal | Explicit `install_local_v6` test application with loopback Supabase URL, real verifier and gateway repositories; unchanged default controls, no TEST_ONLY numerical authority |
| 6. Swipe/select | Existing server-curated draft, exact occurrence IDs and dates, stale/foreign reference denials |
| 7. Pending submission | Proposal/draft locator persisted atomically; active plan/calendar unchanged |
| 8. Separate confirmation | Explicit athlete approval with expected base revision; no automatic activation |
| 9. Calendar reload | Same active logical/physical occurrences after an independent read |
| 10. Activity attachment | Supported measurements attached to the exact owned physical occurrence; no reinterpreted historical evidence |
| 11. Move unfinished workout | Versioned move preserves completed occurrence/activity evidence and immutable receipt |
| 12. Logout/login | Refresh invalidated according to supported scope; login returns owned saved state; account switch clears foreign client state |
| 13. Retry/stale revision | Exact retry returns original receipt; changed payload/stale locator fails; concurrent overlap creates no duplicate write |

Default request is at most one new session per required sport with no individual
maximum; retained occurrences continue to count under existing policy. No real
reviewer/operator is available, so this task does not attempt positive real
multi-session authorization. Production startup remains disconnected from V6;
all 77 catalog revisions remain INACTIVE.

## Software and SQL evidence actually executed

The complete backend suite passes **2,876 tests** including V6 selection/oracles,
spawned workers, pending/confirmation, account isolation, A5 replay-before-generation,
loss/retry, stale revisions and private-load contracts. The complete mobile suite
passes **929 tests / 88 suites**, including account-scoped restore and transport.
Neither uses genuine GoTrue credentials for the lifecycle.

Fresh stock PostgreSQL runs all 63 migrations and 37 suites (722 assertions with
the explicit A5 test overlay). The existing regular frequency runner passes nine
SQL/ASGI groups and a fresh-process reload. It retains the default envelope,
tests null/zero preferences and concurrency around suspension, attachment,
replacement, swipe and approval, with no reviewer or decision rows. Its lost-reply
injections are software/SQL harness behavior, not an actual gateway TCP-loss run.

Historical source evidence remains in
[the accepted search report](JOREN_V6_SEARCH_INTEGRATION_REGRESSIONS.md).
Today's historical rerun preserves **all 40 input fingerprints, outcomes and
independent checks**, with zero differences from the accepted search evidence.
All **26 completed reference results** in `performance/optimized_cold_verified.json`
match exactly as well. The original `current:build_4` diagnostic timeout recurs.
The comparison is recorded in [verification.json](real-auth-20261114/verification.json).
The corpus keeps the original **8-second
including-imports** bound, the **200,000 worknode / 24 occurrence** limits and
exact Decimal/rational methods. No timeout, golden or historical result was
changed. The original accepted regression artifact and all migration/SQL-test
bytes remain unchanged. Actual GoTrue/gateway, device and scientific gates stay open.

## A5 error-boundary finding

`PlanningConstraintError` subclasses `ValueError`. The ordinary planning adapter
handles that typed exception first and returns structured HTTP **409** with
`error.code=v6_search_incomplete`. The check-in adapter delegates repository and
computation-unavailable errors but then catches the same constraint as a generic
`ValueError`, yielding HTTP **422**, `error.code=validation_failed` and the
bounded-search message. This confirms the previously recorded limitation.

The public `ErrorResponse` already supports optional `details`, whereas A5
consumers can observe the existing status and top-level code. The mobile client
knows `v6_search_incomplete`, but current response validation only retains its
known details fields. Simply routing every `PlanningConstraintError` to the
ordinary mapper would change existing A5 status/code behavior and other A5
constraint errors. No contract version or accepted consumer migration is present.

## Compatible normalization proposal — NOT IMPLEMENTED

Preserve A5's **422**, **validation_failed**, existing message and request ID.
For the specifically typed `v6_search_incomplete` error only, populate the existing
optional details map with a constant public discriminator:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "<existing bounded-search message>",
    "details": { "planning_code": "v6_search_incomplete" },
    "request_id": "<existing request ID>"
  }
}
```

This is an additive proposal, not a new envelope, automatic retry or change to
success/replay behavior. A later client can explicitly allowlist that one details
value for the existing qualitative message while preserving status/top-level
code, rejected outcome and no automatic retry. Never forward arbitrary internal
error attributes, numeric budgets, node counters or frozen context.

Before implementing, demonstrate old clients tolerate the additive details and
new clients preserve their validation-error handling; test typed exhaustion
separately from infeasibility and untyped ValueError. Verify no proposal, snapshot,
occurrence, draft mutation or attachment remains after exhaustion. Keep an existing
committed A5 receipt readable before generation even when a later computation
would fail. Repeat owner denial, concurrent attachment/replay, rollback, stale CAS,
separate confirmation and recursive privacy tests on real Supabase.

Because consumer compatibility and the real-runtime safety/replay proof cannot
be established in the missing environment, this delivery leaves the adapter,
mobile client, public contracts and protected A5/A6 worktrees unchanged. Direct
409/code parity is a separate contract evolution, not an assumed compatible fix.
