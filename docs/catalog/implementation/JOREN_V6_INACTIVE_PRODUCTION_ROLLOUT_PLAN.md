# Inactive production rollout — execution prohibited

This replaces the readiness plan at `0fa6509190d292d0c83e3076cda68c55624c202e`; its [original bytes](blocker-resolution-20261117/history/JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN_0fa65091.md) remain archived. Candidate branch: `release/joren-v6-migration-blocker-resolution`. Git and the delivery message record the final commit.

**This plan supplies no production execution, deployment, activation or permission approval.** All 77 revisions remain INACTIVE; normal startup retains the historical planner.

## Required prerequisites

1. Establish actual Railway service/environment/API URL, immutable deployed backend artifact/SHA, mobile build routing, flags, jobs and integrations. Railway remains Unauthorized: owner runs `npx --yes @railway/cli login` and completes browser login, then permits read-only inventory. Healthy URLs/OpenAPI do not identify source. Compare the actual strict model and consumers with the proved historical source.
2. Verify a real production checkpoint and successful isolated restore, accepted RPO/RTO, recovery operator, secrets/Storage/integration scope and cost. Current Free project lists no backup and PITR is false. See [recovery options](JOREN_V6_REMOTE_BACKUP_AND_RECOVERY_OPTIONS_NL.md).
3. Explicitly approve the [exact 13-signature proposal](JOREN_V6_AUTHENTICATED_EXECUTE_ALLOWLIST.md), C1/C2 and [drift disposition](JOREN_V6_HOSTED_DRIFT_DISPOSITION.md). No reviewer/test-executor membership or frequency authority is authorized.
4. Approve an independently identified isolated synthetic hosted target, two manifested accounts, costs, credential custody and cleanup. Execute genuine GoTrue/PostgREST/V6 verification using the [restricted adapter](JOREN_V6_HOSTED_VERIFICATION_ADAPTER.md). Prepared code and portable SQL tests do not close this gate.
5. Review exact generated SQL/hashes and postflight/stop procedures, then obtain separate execution approval for an identified operator/window. Deployment and activation remain independent.

## Atomic installation boundaries

| Group | Membership in execution order | Ledger | Purpose |
|---|---|---|---|
| G1 | Original ordinal 1 | 47 → 48 | Atomic A5 attach/read |
| G2 | Original ordinals 2–12, then C1 | 48 → 60 | V2/V6 custody/approval and historical projection restored before commit |
| G3 | Original ordinals 13–16, then C2 | 60 → 65 | Mobile/evidence/frequency and NULL-CAS/ACL closure together |

C1 and C2 are forward-only. All accepted 63 files remain byte-identical. C1 has a later timestamp than originals 13–16 but is deliberately installed within G2; never substitute timestamp-sorted individual commits. Eighteen candidate migrations are absent at the observed 47 boundary.

No compatibility application deployment is required for the demonstrated historical model with atomic C1. It restores the exact shared contract; optional V2 guidance uses a service-only versioned metadata projection. Any intentional V2 backend enablement requires the new metadata consumer and C1 first. This is not approval to deploy the entire V6 application. Deployed artifacts differing from the proved historical source remain unverified.

| Ordinal | Migration file | SHA-256 |
|---|---|---|
| 1 | `20261026224844_wombo_a5_checkin_proposal_recovery.sql` | `605baca7b060a74dcd0804710a8547b662d76f0c5cb7c21a5aa4b72cfa305d02` |
| 2 | `20261103134520_joren_realized_tss_v2_private_provenance.sql` | `d5444ccbe28428e4101151c07c2f522ae213c2fd82190f5af8cc1ce1c2333231` |
| 3 | `20261103135735_realized_v2_weekly_registration.sql` | `2c3cd85f4ead27a37dd16330626cf8c57fe69baf44459b8fa8b9e9a92f59b346` |
| 4 | `20261103140959_realized_v2_planning_evidence_preconditions.sql` | `6358726af884ecb44e104ad9c0528d2ca7865c0dde8a37e1e8169fbd13ee896a` |
| 5 | `20261103142339_realized_v2_session_rpe_guidance.sql` | `4b3749757358d332df835b4abb945dc95769c4f7a5a14f9b3654874880d93d29` |
| 6 | `20261105120000_inactive_v6_persistence.sql` | `c3572d34ea784a6aba9ab7531cca34007f768ca79602b63d92dfcf0f491c8283` |
| 7 | `20261105120100_inactive_v6_catalog.sql` | `6e77d8d54650c7be554a90bb87cdf339b72a2db334be1a8dd98e82d6e22efe34` |
| 8 | `20261107182000_v6_segment_snapshot_compatibility.sql` | `ca38c97168eaf7d22d5b3508aa4bcdc78f4643044181bfe2ff3d5e699cf838c1` |
| 9 | `20261107182500_v6_frozen_snapshot_operator_precedence.sql` | `aab65809df7f6ebf5d2881fde680e2b169943eceb9d27e2ce53350afbf29efe8` |
| 10 | `20261107183000_realized_v2_internal_approval_custody.sql` | `1efa35afae3877ea80bde0edc03241e0dad1944dee7a217d40739da86fcbc93a` |
| 11 | `20261107183500_realized_v2_business_conflict_codes.sql` | `1fae47af0784194597bd783a53c22626a9951a16009e749df672b202309e4375` |
| 12 | `20261107184500_v6_insert_custody.sql` | `b5844a38a73da363642db6a99328e5358fd4ff72302b51434dd88333dc4a4140` |
| 13 | `20261108142454_inactive_v6_mobile_identity.sql` | `767e7c0f7badbebee9701b546f4666c8f0f72843334f5f8b0f3f7ab313c81008` |
| 14 | `20261108180000_inactive_v6_lifecycle_completion.sql` | `71f3b0388ac99ffae6bd76659eeba1fef84c1adecc004ebb37e8fa10010732c6` |
| 15 | `20261108210000_inactive_v6_evidence_memberships.sql` | `8428f54223108265c20ec87890b651aca4129ca1b5910c75439f6b691eeffb25` |
| 16 | `20261113154716_inactive_v6_approved_frequency_policy.sql` | `c0a43411f7db00d4d76cb8400d0b07e5081678aff280853a6a91b9b03ff6b2c4` |
| C1 (G2) | `20261116231106_v6_activity_projection_compatibility.sql` | `d0fba80a54cd263ae9ef4b5bf2efd48b8a6375507c0e1763c12bf9c8a8af73bb` |
| C2 (G3) | `20261116231107_v6_reviewed_privilege_closure.sql` | `e37c3c09bf71c1373de8c924c5dbdcb63094f4b445a7cd485f44056d65c72a98` |

Accepted-chain hashes are retained in `migration-readiness-20261116/hosted-before.json`; [forward-migrations.json](blocker-resolution-20261117/forward-migrations.json) pins C1/C2. The [owner bundle manifest](blocker-resolution-20261117/owner-bundle-manifest.json) pins exact group SQL hashes, migration order, ledger boundaries, baseline and allowlist hashes. Regenerate from the committed candidate and compare before approval.

## Offline preparation and permission enforcement

From `backend`, run `python -m scripts.prepare_v6_rollout_bundles --output-directory <private-review-directory> --proposed-authenticated-allowlist ../docs/catalog/implementation/blocker-resolution-20261117/authenticated-execute-allowlist.json` to prepare review artifacts only. The generator has no network/SQL execution mode. Without the allowlist it still rejects every new client EXECUTE. The option accepts only the exact pinned proposal and is not execution approval; `production_execution_approved` stays false.

G1 pins reviewed actual hosted function fingerprints, effective function/table privileges and default ACLs. Refresh read-only metadata immediately before approval; stop if different instead of changing the baseline to pass. All unexpected signatures/overloads, anonymous authority, service writers, private-table privileges, default-ACL expansion, grant options, role powers/memberships and schema authority stop the transaction. Missing historical EXECUTE dependencies also stop, including the private membership helper. C2 removes only named catalog Dxtm service privileges and app-owned `postgres/public` Dxtm defaults; provider defaults remain pinned and unchanged.

Only a separately approved direct SQL operator session may execute an exact reviewed group. Never use unrestricted `supabase db push`, ledger repair or the existing startup task that automatically migrates/deploys. Generated SQL requires `current_user = postgres`, advisory lock, `lock_timeout = 5s` and `statement_timeout = 120s`. DDL, assertions and new ledger INSERTs share one transaction. It never UPDATEs/DELETEs existing entries. Original 47 version/name/statement fingerprints remain exact; new statements are registered from exact migration bodies and earlier groups are checked.

## Postflight, stop conditions and unknown commit

After each approved group, use a fresh connection to compare full expected ledger, function/effective grants/default ACLs, RLS, no-enrollment state and all 77 INACTIVE revisions when installed. Compare historical row fingerprints and run all six historical SQL smoke suites before proceeding. At 47 and each group exercise activity create/read/list/match/complete/delete; check-in context/confirmation/proposal attach/replay/decision; confirmed plan reads and the actual deployed strict model/mobile consumers against actual PostgreSQL output. Probe V2 server metadata separately; no private load/evidence may escape.

Connection loss around COMMIT means **stop retries**. On a fresh approved read connection compare exact version sets/names, original-47 statement fingerprints, each new statement-array body against reviewed SQL, schema/function/ACL fingerprints and historical state. Entire group absent with exact pre-state permits consideration of an explicitly authorized retry of the same artifact. Entire group and exact post-state means committed success without rerunning. Mixed/mismatching ledger/schema or uncertain data requires incident review. Never repair history, guess from health, blindly repeat, or change operation keys. The local unknown-commit test proves an already committed group is refused.

Stop for missing recovery, target/source mismatch, unexpected authority/defaults/RLS, active V6 revision, extra/missing ledger entry, lock/statement failure, unknown commit, historical smoke failure, private leak, foreign-owner access or stale mutation acceptance. Preserve existing resource limits; do not increase them to pass.

At 65 repeat pgTAP/RLS/permission checks and genuine hosted A/B authentication/owner isolation. Check no anonymous additions, athlete service writer, preference-to-authority path, enrollment or private TSS. Hosted adapter checks include sign-in/refresh, current owner map, foreign IDs, stale/conflicting retries, kill switch, journal reconciliation and audited manifested cleanup. Follow the existing [hosted verification plan](JOREN_V6_HOSTED_POST_MIGRATION_VERIFICATION_PLAN.md). No hosted V6 execution is claimed here.

## Generation disable and recovery

Remove the independent adapter enabling file and stop its exact recorded process; verify in-flight writes have ended. Normal production startup stays historical with V2 controls off. Preserve plans, decisions, receipts, evidence, catalog rows and migration history.

The expanded **local-only** forward-disable fixture was rehearsed on a populated clone. It blocks V6 service generation/writer entry points and the shared private A5 persistence path, retains all 64 table hashes and confirmed reads, denies three actual service RPCs with 42501, rejects a V6 A5 insert with PT409 `V6 generation disabled`, and passes four historical smokes. See [disable evidence](blocker-resolution-20261117/disable-final--results.json).

This fixture is not approved production SQL or a backup restore. Before future V6 runtime enablement, prepare a separately reviewed target-specific forward-only incident correction using that coverage, rechecking exact service/A5 signatures and grants on the final hosted schema. Stop generation first; retain existing read/decision/evidence behavior; run historical smokes. No downgrade, historical rewrite or ledger repair.

## Executed evidence and limits

Backend 2,940 tests; mobile 935 tests/89 suites; strict TS, Ruff/format and strict mypy pass. Clean accepted 47 and reproduced hosted drift each upgrade through all groups with 752 assertions/38 suites and unchanged hashes for 51 historical tables after each group. Fresh final schema also passes 752. Both bundle rehearsals pass all 14 guard cases. Historical planner 40 outcomes and 26 accepted references remain exact; known eight-second `current:build_4` diagnostic timeout and 200,000-node ceiling remain.

Original A5 remains 8 pass/1 fail/abort before 20; only the explicit corrected overlay passes 29/29. Portable PG17.11 is not hosted Supabase17.6/Linux/GoTrue. The [verification register](blocker-resolution-20261117/verification.json) records scope and harness corrections. No physiology, workout, mobile implementation, accepted migration or protected A5/A6 worktree changed.
