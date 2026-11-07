# V6 persistence rollback plan

7 November 2026, Europe/Amsterdam. Branch `feat/joren-v6-persistence-hardening`.
Exact accepted base: `4b3a76d9d764567e7bb438ad7493953faed6dea2`.

No production/staging migration, activation or deployment has occurred. There is
nothing to roll back in those environments. The two forward SQL candidates are
unexecuted. Existing historical migrations, planner default and A5/A6 are unchanged.

## Before any migration is applied

Withdraw the candidate branch or stop injecting the inactive adapter in local
tests. Do not reset another worktree or alter the separate A5/A6 release branch.
Preserve the local commit, source hashes and verification evidence for review.

## Disposable verification database

Keep failing transaction transcripts private and record the tested SHA/migration
ledger. A failed function call must leave old pending state and every prior
snapshot intact. Repeat read-after-write/rollback assertions from a new connection.
For an unknown connection outcome, reconcile using the original operation key and
revision; never regenerate an earlier proposal or issue a new identity blindly.

Reset/destroy only the specifically created disposable database/container after
capturing evidence. The runner's synthetic auth users and committed snapshots are
not permission to delete anything in a shared development, staging or production
database. No automatic cleanup against a guessed target is provided.

## If a future authorized migration has been applied

Use a reviewed **new forward migration** and an explicitly approved application
rollout/rollback. Never edit an already applied migration, rewrite historical P,
drop source revisions/snapshots, change UUIDs or map V6 values onto an older method.

1. Remove/withdraw V6 dependency injection. The historical default already remains
   installed; no exposed V6 enable flag was added.
2. Revoke execution of the new generated-write/private-catalog RPCs in a forward
   migration if necessary. Preserve existing authenticated historical approval,
   rejection, recovery and read RPCs. Decide how existing preview locators should
   be surfaced before revoking their new read projection.
3. Leave all 77 revisions INACTIVE and keep the restrictive catalog visibility
   policy. Retain private exact values, source documents, occurrence mappings,
   frozen input/registration evidence and immutable idempotency receipts.
4. Preserve already confirmed snapshots and their original method/version. Do
   not reinterpret or recompute planned/Realized values. Existing pending plans
   require their defined athlete rejection/expiry semantics; no bulk silent
   activation, deletion or replacement is authorized.
5. Verify least-privilege grants, RLS, historical planner output and A3–A9/V2
   regressions. Rehearse new-connection retry/confirmation/cancellation outcomes
   in a disposable clone before any separately authorized rollout.

The V6 occurrence mapping cannot be discarded while a retained logical ID is
referenced. Before eventual mobile activation, calendar/activity/registration
translation and rollback-compatible locator recovery need explicit integration
and device evidence. V6 check-in attachment/replay is currently fail-closed and
must not be substituted with a second approval model.

## Success criteria and authority

Historical catalog/planner behavior remains identical; private data is never
exposed; all source and confirmed-snapshot provenance survives; stale writes
conflict; exact retries recover the same result; and no other account/worktree is
modified. A rollback rehearsal has **not** run against PostgreSQL here. Database,
scientific, mobile/device and release gates remain independent. No push, merge,
deployment, production migration or activation is authorized by this document.

## Local delivery provenance

Verified implementation, tests, prepared SQL and evidence commit:
`5482524f49e5c2684df0a756c60b619ba9a128ef`, directly after accepted base
`4b3a76d9d764567e7bb438ad7493953faed6dea2`. A documentation-only successor
records this immutable SHA; resolve the final branch tip with
`git rev-parse feat/joren-v6-persistence-hardening`.

Final backend: 2,583 passed; 96 new persistence tests included. Ruff lint/format
and strict mypy pass. All 40 historical cases and 26 accepted reference results
are byte-identical to the accepted corpus; canonical SHA-256
`3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.

PostgreSQL/RLS: **NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE**.
Both new migrations are unexecuted. Default planner, production/staging and A5/A6
remain untouched. No push, merge, deployment, activation or next release stage.

**WOMBO V6 PERSISTENCE IMPLEMENTED — DATABASE VERIFICATION PENDING**
