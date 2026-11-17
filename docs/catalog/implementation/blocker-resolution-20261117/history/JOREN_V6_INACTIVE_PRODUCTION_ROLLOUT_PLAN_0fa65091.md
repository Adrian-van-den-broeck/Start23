# WOMBO V6 inactive production rollout plan

16 November 2026, Europe/Amsterdam. **CONDITIONAL PLAN — DO NOT EXECUTE IN PRODUCTION.**

This package prepares exact ordered SQL for owner review. It does not authorize execution. The accepted chain is understood and locally rehearsed, but unchanged production compatibility, recovery and the strict client-permission requirement remain blocked. Outcome: **WOMBO V6 PRODUCTION MIGRATION READINESS PARTIAL — EXACT RISKS DOCUMENTED**.

## Immutable scope

Base `289280a5bddf6f0cc65eca1f562561e7df9a603c`; successor `release/joren-v6-hosted-migration-readiness`. Install only the 16 files/hash values in the [gap analysis](JOREN_V6_HOSTED_MIGRATION_GAP_ANALYSIS.md), in chronological order. Do not replay the first 47, edit accepted migrations, use migration repair, seed fixtures, include custom roles/seed switches, activate catalogs or change the default planner.

Target identity is `isfumhgqphieoayqahjv` / eu-west-1; its development name is not permission to bypass production gates. A separate approved hosted verification environment must be identified independently. Backend/mobile target routing currently disagrees locally, so the owner must resolve the actual traffic destination.

## Hard preconditions — all required before execution approval

| Gate | Concrete closure needed |
| --- | --- |
| Backup | Successful available checkpoint plus isolated hosted restore evidence, measured RPO/RTO, Storage/service scope and owner-approved write-loss/cost budget. Current backup list empty, PITR false |
| Old activity consumer | Identify deployed SHA and demonstrate migration-5 projection accepted; approve/rehearse a compatibility runtime or new forward versioned database projection. Current historical model fails |
| Client EXECUTE | Resolve 13 new authenticated signatures against the explicit no-new-EXECUTE rule. No exception is implied. A blanket helper revoke is unsafe for shared historical invoker reads |
| Existing drift | Owner disposition of two body differences, four catalog service ACL differences and hosted default ACLs; repeat fixed metadata comparison. Never fix by ledger repair |
| Hosted parity | Exact chain in an official isolated Supabase runtime with genuine two-account sessions and the approved verification adapter; portable PG17 is insufficient |
| Artifact/traffic ownership | Actual production backend/mobile SHA/builds, flags, service/environment, scheduled jobs/providers, immutable previous compatible backend artifact and approved window/operator |
| Prerequisite integrity | Current 47/63 ledger exactly matches reviewed versions/names/fingerprints, all 63 local file hashes match, no conflicting IDs/roles/source rows, dynamic replacement markers match |

The source changes needed to close gates are **not silently folded into these 16 migrations**. Any approved compatibility/ACL/disable change must be a new forward migration or separately reviewed application artifact, followed by renewed rehearsal and bundle review.

## Execution tooling and fail-closed review bundles

The cached Supabase CLI inspected here is **2.76.8**. Its `db push --help` has no atomic group flag. Do not assume per-migration transactions provide atomicity for an entire group. The repository's Wombo production start task automatically pushes migrations and deploys; **do not use it for this rollout**. No CLI upgrade was made; v3 changes target/confirmation semantics. [CLI change notice](https://supabase.com/changelog/supabase-cli-v3).

From `backend`, prepare offline review SQL with the existing Python environment:

```powershell
python -B -m scripts.prepare_v6_rollout_bundles `
  --output-directory ../.runtime/migration-readiness/owner-review-bundles-NEW
```

This generator has no connection/execute mode. It verifies all 63 accepted file hashes, embeds the exact migration SQL, enforces expected ledger boundaries and the original 47 statement fingerprints, and registers **only new versions** inside the same transaction as their DDL. It never updates/deletes/repairs an old ledger row. New ledger statement arrays contain the exact file SQL as one statement-array element; that representation is explicitly distinct from a historical CLI split-array fingerprint.

**Current bundles intentionally refuse COMMIT:** a transaction-end guard detects any new `anon`/`authenticated` EXECUTE permission and raises. The current accepted chain therefore fails the guard. This is the required safe outcome under the current instruction; do not remove the guard or run an unguarded CLI push to work around it. [Offline bundle manifest](migration-readiness-20261116/owner-bundle-manifest.json), [local guard proof](migration-readiness-20261116/strict-bundle-guard-results.json). The proof substituted only local fixture-ledger fingerprints; it is not a hosted-ledger execution claim.

After all gates and a separately reviewed permission design are closed, regenerate/review the final approved bundles and their hashes. An owner with the approved target's secret connection profile may then use the following **future operator recipe**, one group at a time:

```powershell
# OWNER ONLY, AFTER separate execution approval and all gates above.
# PGSERVICE entry is provisioned securely outside Git; credentials stay out of argv.
psql -X -v ON_ERROR_STOP=1 --dbname 'service=wombo-reviewed-production' `
  --file '<reviewed-bundle-directory>/group-1.review.sql'
if ($LASTEXITCODE -ne 0) { throw 'STOP: reconcile the exact group boundary' }
# Perform the G1 assertions/synthetic smoke acceptance below before G2.
psql -X -v ON_ERROR_STOP=1 --dbname 'service=wombo-reviewed-production' `
  --file '<reviewed-bundle-directory>/group-2.review.sql'
if ($LASTEXITCODE -ne 0) { throw 'STOP: reconcile the exact group boundary' }
# Perform G2 assertions/smoke acceptance and recovery checkpoint before G3.
psql -X -v ON_ERROR_STOP=1 --dbname 'service=wombo-reviewed-production' `
  --file '<reviewed-bundle-directory>/group-3.review.sql'
if ($LASTEXITCODE -ne 0) { throw 'STOP: reconcile the exact group boundary' }
```

The profile name is a required operator-created credential binding, not an existing connection asserted by this report. Verify its server/project/database identity using the owner-approved metadata process before opening a write transaction. Direct/session connection and lock/statement budgets need operator acceptance; transaction-pool behavior is not assumed. No production invocation occurred.

## Group 1 — historical A5 recovery (47 → 48)

**Exact migration:** ordinal 1, `20261026224844_wombo_a5_checkin_proposal_recovery.sql`.

**Preconditions/checkpoint:** every global gate, recoverable pre-G1 checkpoint, current A5 attachment/approval contracts and exact ledger boundary. The new A5 authenticated read itself conflicts with strict no-new-EXECUTE, so G1 is also blocked until permission disposition.

**Changes:** owner-derived exact replay RPC; replace v3 with atomic check-in row-lock/create/attachment behavior. No athlete row is migrated or regenerated. Historical pending/applied/rejected attachments remain authoritative.

**Read-only assertions:** ledger 48 exact versions, original 47 fingerprints unchanged; `get_checkin_plan_proposal(uuid)` invoker/owner boundary and approved ACL; v3 remains service-only; no V6 table/source or frequency-role creation yet; existing constraints/policies/triggers unchanged apart from the two function definitions.

**Historical smoke acceptance:** in the approved isolated hosted environment, create/confirm normal synthetic onboarding, save/confirm a check-in, generate pending A5 proposal, repeat exact request, reject another pending proposal and recover terminal replay, separately approve the first, reload via A6 account namespace, and verify foreign IDs fail identically. Original fixture is not a production test; the local corrected 29-assertion overlay is distinct evidence.

**Stop:** any inconsistent attachment, duplicate revision, altered existing row/provenance, foreign read, missing/misgranted RPC, ledger drift, lock budget failure or unknown commit. Do not continue to G2.

**Recovery:** failed transaction rolls back both DDL and new ledger entry; after commit retain attachments and use a reviewed forward A5 fix/compatible runtime. Backup restoration requires incident-specific approval. V6 remains absent/inactive and historical planner remains default.

## Group 2 — V2 evidence and inactive V6 core with correctness/security closures (48 → 59)

**Exact migrations:** ordinals **2–12**, inclusive. Exact names/hashes are embedded in the generator/manifest and gap inventory. This is one atomic transaction, not eleven exposed intermediate deployments.

**Dependency rationale:** 4 installs an owner-approval trigger whose v13-v15 internal authorization is corrected only by 10; 3/4 business failures use the wrong retry classification until 11. V6 core 6/7 needs segment correction 8, operator-precedence correction 9 and insert custody 12. File 7 uses an ON COMMIT DROP import table. No traffic or generation is permitted through these incomplete states.

**Preconditions/checkpoint:** accepted G1 and successful smoke; pre-G2 recovery point covers G1; migration-5 old-consumer compatibility resolved with proven compatible runtime ready; no source UUID/version collisions or preexisting V6 relations; accepted active draft/distribution rows satisfy replacement constraints. Assess counts/constraint compatibility on the authorized hosted recovery clone, not by copying athletes here.

**Changes:** four V2 private evidence/registration tables, four V6 private tables, 77 inactive source/template rows, restrictive catalog policy, replacement draft/distribution constraints and shared activity projection, plus approval/activity/segment/custody guards and narrow RPCs. No new source enters historical private catalog load projection; no old planned/realized value is recalculated.

**Read-only assertions:** ledger exactly 59; 77 source revisions INACTIVE, 77 `inactive_v6=true` public counterparts, zero V6 historical-load joins; original catalog ID/hash manifest unchanged; forced RLS/private ACLs expected; V2 approval path owner-bound internally, direct v13-v16 generation/history remain service-only; four V2 guards now use PT409; no reviewer/test-role membership. Compare deployment's activity schema/response behavior after the compatibility gate, including existing activities.

**Historical smoke acceptance:** synthetic ordinary onboarding/plan proposal/independent confirmation, A5 atomic attachment/replay and A6 recovery; legacy create/get/list/RPE/match path; registration unknown→skipped→retry/stale rejection where the verified runtime exposes it; prior historical source/prescription and private evidence remain equal. Exercise failures and unknown outcomes in the isolated hosted target before any production window. A live production smoke, if later authorized, uses only the two explicitly manifested synthetic accounts.

**Stop:** any old activity response rejected; authenticated generated-write success; constraints/trigger/function marker mismatch; catalog visibility leak; non-77 source count; existing plan/activity/private evidence mutation; lock/statement budget failure; missing compatible rollback artifact. Do not expose intermediate V2/V6 paths or continue to G3.

**Recovery:** abort whole G2 before commit. After commit, do not downgrade blindly across migration 5; use approved compatible runtime/forward correction. Keep V6 disconnected, preserve source/evidence, and use the expanded disable architecture if required. No destructive inverse SQL. G2 local transaction durations were about 0.3 seconds on tiny synthetic data; they are **not** a production lock/downtime estimate.

## Group 3 — mobile identity, shared lifecycle/membership and approved frequency (59 → 63)

**Exact migrations:** ordinals **13–16**, inclusive, one transaction.

**Dependency rationale:** mobile identity 13 feeds lifecycle 14; moves need 15 to retain completed physical evidence in successor revisions; 16 installs frequency custody and renames/wraps a helper used by these paths. Commit only the final coherent state; never enable V6 at a pre-membership/frequency intermediate.

**Preconditions/checkpoint:** G2 accepted and pre-G3 checkpoint covers it; current check-in contexts satisfy the replacement constraint; confirm-context rewrite marker matches; frequency roles/renamed helper/tables absent, no unexpected membership or enrollment; hosted public/private default ACLs and trigger install rights reviewed for the actual execution owner.

**Changes:** one private membership table/view and four private policy tables, logical/physical mobile projections, shared plan/calendar/history/activity/registration replacements, revised check-in supersession, source/approval/draft frequency invalidation, service-only frequency wrappers and NOLOGIN registrar/test-executor roles. No reviewer/operator or individual maximum inserted, no role membership granted.

**Read-only assertions:** ledger exactly 63 and hashes unchanged; run [post-migration-readonly.sql](migration-readiness-20261116/post-migration-readonly.sql) and inspect **every boolean/ACL row**, not just psql exit status. Check zero authority records/memberships, exact 77 INACTIVE sources and absence from historical load joins. Diff shared function signatures, policies/RLS, new grant allowlist and existing Auth trigger/configuration. No application injection/default-setting change is part of SQL installation.

**Historical smoke acceptance:** repeat G2 historical workflow; reconfirm a synthetic check-in context while preserving the earlier confirmation timestamp; read/replay through A5/A6; matched historical activity and calendar; exact synthetic account deletion cascade in the isolated hosted environment. Then run the separate full [post-migration verification plan](JOREN_V6_HOSTED_POST_MIGRATION_VERIFICATION_PLAN.md), only after its adapter/security gates.

**Stop:** prior confirmed context/evidence lost, physical evidence reassigned, duplicate active member IDs, unexpected RPC/public private-load key, extra roles/membership/reviewer, automatic multisession authority, implicit V6 enrollment, failed historical flow, stale/foreign acceptance, backup no longer available or unrecognized runtime artifact.

**Recovery:** failed transaction returns to coherent G2. After commit preserve all memberships/policies/evidence and owner read/approval contracts; disable only new generation through approved runtime/forward guards. Do not revoke `private.v6_revision_workouts` in isolation. Existing old four-RPC fixture is insufficient; the new **local-only** [disable fixture](../../../supabase/tests/fixtures/v6_readiness_forward_disable.sql) models the broader closure and is not deployable as-is.

## Operational budgets, lock strategy and reconciliation

Proposed transaction-local budgets are lock timeout **5 seconds**, statement timeout **120 seconds**; they are operational proposals, not physiological limits or measured production guarantees. G2 constraint changes can require ACCESS EXCLUSIVE/validation scans; G3 replaces a check-in constraint and installs multiple triggers. Existing-table DDL locks may be retained until the whole group commits. Inspect traffic/long transactions and recoverable capacity in the approved window, serialize the operator with the bundle advisory lock, and stop on timeout rather than raise limits automatically.

Never kill athlete transactions, disable RLS/triggers, use unrestricted cleanup or grant more rights to force success. Coordinate traffic/providers/actual scheduled jobs under owner-approved maintenance. Functions and ledger must commit together. On a lost acknowledgement, reconnect read-only and inspect exact versions and fingerprints; do not retry by changing operation/version identity. Record UTC start/commit/checkpoint times and private operator evidence without tokens, health rows or private-load payloads.

## Independent activation boundary

Installation may leave all 77 revisions INACTIVE while historical generation remains default; local tests prove that design. It does not make the unmodified chain safe for the current deployed consumer or satisfy the no-new-EXECUTE rule. After installation, no automatic reviewer/operator enrollment, test-executor membership, synthetic REAL authorization, startup injection, mobile V6 flag, catalog activation or real-athlete rollout is authorized. Scientific, reviewer/maxima, performance, device and deployment gates remain independent.
