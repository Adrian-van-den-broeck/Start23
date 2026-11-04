# A5 database gate and production configuration procedure

2026-11-04. Start `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`; final software `8f75140169e074111e868d48bcf67e82aed8f899`. **Backend + mobile NO-GO. PostgreSQL/pgTAP remains DEFERRED BY OWNER — PRE-BETA.** No database tool was installed and no SQL, migration, database RPC or athlete-data write was executed.

## A5 is separate from Realized V2

Exact migration: `supabase/migrations/20261026224844_wombo_a5_checkin_proposal_recovery.sql`. Its SHA-256 and the unchanged migration inventory are included in remediation evidence. The four November Realized V2 migrations are not prerequisites for off-gated UI/A6 recovery and remain deferred. C1/C2/C2.1 add no migration.

`CheckInService.generate_plan_proposal` unconditionally reads `get_checkin_plan_proposal` before generation, repeats it after a context conflict, and rereads the authoritative attached snapshot after persistence. `SupabaseCheckInRepository` sends the caller token for this read. It does not use a feature flag or assume that an ambiguous POST failed.

**Correction to the audit's interpretation:** the A5 migration explicitly revokes execute from `service_role`, PUBLIC and anon and grants it to `authenticated`. It is `SECURITY INVOKER` and delegates initial ownership checking to `get_weekly_checkin`, then matches check-in/proposal/revision owners and identities. Therefore absence from service-key Data API metadata is consistent with the intended grants; it does not establish that A5 is absent. Presence, migration ledger, authenticated execution and RLS are still unverified. Do not grant service-role access merely to make schema metadata list it.

The generation RPC remains service-only. Its `create_weekly_plan_proposal_v3` wrapper locks the owned check-in row before persistence and attachment, returns an existing exact attached proposal, and can recover exactly one unambiguously owned pre-A5 persisted revision. More than one candidate, inconsistent attachment, or a closed unrecoverable check-in fails closed. Provenance checks remain in place. Creation and attachment must commit/roll back atomically. The backend derives the legacy owner through its established identity adapter; a client `user_id` is not authority.

Legacy generation/attachment behavior may have a lost-response gap. A mobile-only release must not claim A5's atomic replay guarantees merely because the older POST path exists. The candidate does not downgrade server dispatch, regenerate on missing replay, or retry with a new logical identity to conceal an unknown result.

## Minimal independently testable A5 integration gate

When the owner lifts the database deferral, test A5 independently of the four V2 migrations on a disposable historical-schema upgrade and fresh replay. Do not run these cases against current athlete data.

1. Compile the migration on the exact preceding schema. Verify the migration ledger, v2/v3 generation dependencies, attachment function, check-in/revision/proposal keys, invoker RLS and original owner adapters.
2. Authenticated owner A can read only A's attached exact snapshot. B and anon cannot read it. Foreign/missing IDs disclose no other athlete's state. `service_role` cannot call the invoker replay function; authenticated cannot call service-only generation. Confirm PUBLIC revocations, search_path and no broad grant changes.
3. Open/no-attachment returns null; completed/attached returns exact original plan/proposal/revision, including terminal decisions. Completed/inconsistent, ambiguous multiple pre-A5 revisions and mismatched owner/target identity fail closed without creating a replacement.
4. Same logical request and response-loss retry returns the same IDs and one persisted proposal. Reused conflicting fingerprints/stale bases retain conflicts. Exercise two real concurrent sessions on the same check-in and separate athletes: one committed generation/attachment, no orphan or duplicate. A static `FOR UPDATE` string assertion is not this race test.
5. Inject failure between persistence and attachment: all changes roll back. Exercise pre-A5 single-existing-revision recovery and missing/unrecoverable attachment; do not regenerate silently.
6. Verify original grants/RLS/privacy, pending-only application, stale approval, preserved history and old mobile contracts. Verify read-only replay cannot activate a plan or expose private load.

The existing `supabase/tests/wombo_a5_checkin_proposal_recovery_test.sql` is only a prepared starting suite. Its row-lock assertion is explicitly structural, not actual concurrency proof. Full backend unit/mocked tests remain necessary but insufficient. No execution result is claimed in this task.

## Production configuration evidence

The configured production public URL still returns `{status: ready, version: 0.1.0, environment: local}`. Railway CLI access remains unauthorized. No new login/link was attempted. A read of existing local linkage shows project `c0cf7bc7-abe8-4db5-857a-85cc39850640`, environment `875b7e64-0f3f-4e42-9efd-973dfb6e295b` named **r6-staging**, service `6c2cb45b-43e1-43c1-983f-1ed154b2ac76`. These are local link identifiers, **not verified production identity**. Current production Git SHA, connected branch, auto-deploy triggers, variables, optional providers and rollback artifact remain unknown.

Settings defaults to local and reads `START23_`-prefixed names. It does not infer deployment mode from Railway's environment name. Thus the response is consistent with absent `START23_ENVIRONMENT` or an explicitly local value; the actual hosted cause cannot be established without authorized variable inspection. `/ready` does no schema, revision or credential probe. A ready response does not show production validation succeeded.

The example file's incorrectly unprefixed `PHYSIOLOGY_REVIEW_RULESET_VERSION` has been corrected to `START23_PHYSIOLOGY_REVIEW_RULESET_VERSION`, with both V2 flags explicitly false. This is a local template correction only. No hosted setting or validation logic changed.

## Owner-only correction procedure — prepared, not executed

1. In the existing Railway dashboard, identify the service owning `start23-production.up.railway.app`. Record verified project/service/environment IDs, current successful deployment ID/full Git SHA, source branch/root/watch paths, auto-deploy and predeploy/start command overrides. Do not substitute the local r6-staging link. Capture a safe configuration inventory; never paste secrets into chat or public logs.
2. Inspect actual variable **names and presence** first. Required names are `START23_ENVIRONMENT`, `START23_SUPABASE_URL`, `START23_SUPABASE_PUBLISHABLE_KEY`, `START23_SUPABASE_SECRET_KEY`, `START23_PHYSIOLOGY_REVIEW_RECORD_ID`, `START23_PHYSIOLOGY_REVIEW_RULESET_VERSION`, `START23_PHYSIOLOGY_ACCOUNTABLE_OWNER`. Review issuer/JWKS/audience/ES256 against the actual Supabase Auth project, without weakening verified-token identity.
3. Verify genuine review evidence for `phase-13-joren-ruleset-1` with its qualified accountable owner and record. Without it, correctly setting production will deliberately fail startup. Empty keys also fail startup. Do not manufacture IDs, use the example as approval, or leave the app in local mode to bypass the gate.
4. Inspect optional Polar configuration. A configured client ID requires its client/webhook secrets; in production it additionally requires genuine legal/privacy/provider-terms approvals, operational owner, final HTTPS callback and shorter raw than canonical retention. Missing or inconsistent values can prevent startup. Do not fabricate approval or disable an existing provider merely to evade validation. LLM/provider secrets remain server-only.
5. Confirm `START23_REALIZED_V2_STORAGE_READY=false` and `START23_REALIZED_V2_SELECTION_ENABLED=false`. Storage true is prohibited for production while release gates remain open. Compare actual historical schema/A5 requirements and the deferred migration list. Do not run the local production “Start backend” task: it pushes every pending migration before deployment.
6. After the owner explicitly approves a complete configuration correction and restart/deployment scope, apply the coherent reviewed configuration, then read back that exact deployment's success and revision, `/ready` environment **production**, authentication behavior and required dependency checks. Before approval, predict startup failures using the exact settings validators and protected inputs in an authorized environment; never expose secret values in the result.
7. Preserve a known-good production-valid rollback artifact/configuration. Restoring `local` to bypass missing review is not an acceptable rollback. No destructive migration, data reset, down migration or historical recalculation is required or permitted.

This procedure requires dashboard access and genuine approval evidence from the owner. It is not authorization to execute it. Current variable values and whether production startup would pass remain **unknown**; deployment remains NO-GO.
