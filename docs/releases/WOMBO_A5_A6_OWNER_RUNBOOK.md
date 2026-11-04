# WOMBO A5/A6 owner verification and deployment runbook

Prepared 2026-11-04; **not an execution approval**. Start at `abcc800d594e9e46784148cc799c51834daed329`. Backend component `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`. Keep the four deferred Realized TSS V2 migrations, new 61-workout catalog, new beginner policies and C3–C8 activation outside this scope.

Final verified review/mobile source: `5e990ccb831f03926ea35b722eaa4ec4493bcdbe`. Later commits contain only reports/evidence. This SHA identifies the UI/tools tree, not the conditional A9 backend component or any running deployment.

## 1. Identify production before using any CLI link

In the already-authorized Railway dashboard, locate the service whose domain is exactly `start23-production.up.railway.app`. Read only. Record:

- Workspace/project ID and name; service ID and name; environment ID and name.
- Active successful deployment ID, timestamp, full source Git SHA and image/artifact digest. If uploaded source has no verifiable SHA, record unknown and obtain source-manifest evidence; a deployment message alone does not prove source.
- Repository, connected branch, backend root directory, watch paths, auto-deploy settings, pending deployments and promotion behavior.
- Build, pre-deploy and start overrides; Dockerfile selection; health path; provider/plugin/service ownership of the public domain.
- Previous known-good deployment/image and its configuration snapshot; whether Railway rollback rebuilds or reuses it and which current variables it will receive.
- Actual Supabase project/ref used by this service and mobile; record only safe identity and variable names/presence, never credentials.

Stop if this evidence is unavailable or points to r6-staging. Existing local IDs in the gate report must not be substituted. Current CLI session is unauthorized; no new login/link is authorized. Auto-deploy settings must be understood before any later approved push. No push is part of this task.

## 2. Review production settings without changing them

`Settings` reads `START23_` names and defaults to local. A Railway environment label does not set application mode. Public `local` is consistent with an absent/explicitly local variable or a different deployed implementation; actual cause is unknown until source and variables are inspected.

Required reviewed configuration:

| Variable | Required evidence |
| --- | --- |
| `START23_ENVIRONMENT` | `production`, only after startup requirements below are satisfied |
| `START23_SUPABASE_URL` | Actual intended project HTTPS URL; matches mobile/Auth issuer |
| `START23_SUPABASE_PUBLISHABLE_KEY` | Genuine correct project's public key present |
| `START23_SUPABASE_SECRET_KEY` | Genuine server-only secret present; never copied to mobile |
| `START23_PHYSIOLOGY_REVIEW_RULESET_VERSION` | Exactly `phase-13-joren-ruleset-1` |
| `START23_PHYSIOLOGY_REVIEW_RECORD_ID` | Genuine qualified review reference, independently confirmed |
| `START23_PHYSIOLOGY_ACCOUNTABLE_OWNER` | Genuine accountable qualified owner |

The production validators reject missing keys or governance evidence. Do not invent approvals or weaken validators. The default JWT audience is authenticated, algorithm ES256, issuer/JWKS derived from the actual Supabase URL; verify real token/project compatibility and expired-token rejection. An unprefixed `PHYSIOLOGY_REVIEW_RULESET_VERSION` does not satisfy settings.

If Polar is configured, review `START23_POLAR_CLIENT_ID`, `...CLIENT_SECRET`, `...WEBHOOK_SECRET`, `...OAUTH_REDIRECT_URL`, `...LEGAL_APPROVED`, `...PRIVACY_APPROVED`, `...PROVIDER_TERMS_APPROVED`, `...OPERATIONAL_OWNER`, `...RAW_FIT_RETENTION_DAYS`, `...CANONICAL_ACTIVITY_RETENTION_DAYS`. Client ID requires both secrets; production additionally requires genuine approvals, final nonlocal HTTPS callback and raw retention shorter than canonical. Do not disable an existing provider simply to pass startup. LLM/provider secrets remain server-only; LLM is not required to compute plans.

On newer code keep `START23_REALIZED_V2_STORAGE_READY=false` and `START23_REALIZED_V2_SELECTION_ENABLED=false`; storage activation is deliberately rejected in production while its gates are open. The selected older component has no V2 code at all. Check hosted hooks: repository Dockerfile installs Python and starts Uvicorn, with no migration hook. Root's existing production task runs `supabase db push` before `railway up`: **do not use that task**. Hosted command overrides remain unknown.

Before approving a configuration restart, load the exact component's Settings in a protected validation environment with the real reviewed inputs. Do not log secret values. Expected outcome: production validation succeeds with genuine evidence; missing evidence intentionally fails. `/ready` alone does not exercise DB/RLS and is not sufficient.

## 3. Read-only A5 SQL on the confirmed database

Generate a new kit from the review tree; this command only writes local review files:

```powershell
python scripts/prepare_a5_a6_release_kit.py --output .runtime/a5-a6-owner-kit
```

After confirming the actual production Supabase project, an owner with existing database permission can run the generated `a5-catalog-readonly.sql` in that project's SQL editor. It explicitly starts READ ONLY and rolls back. Do not call service-only generation or read athlete payloads as a metadata check. Lack of SQL-editor permission is an open gate; do not broaden grants.

Expected results:

1. Exactly two function rows, both present, body hash and security-mode matches true; role grant matches true; PUBLIC/anon denied true.
2. Replay is invoker/stable (`provolatile=s`), generation is definer/volatile (`v`); both have an explicitly empty search_path. Replay execute: authenticated yes, service_role no. Generation: service_role yes, authenticated no. JSONB returns are defined in the pinned migration.
3. All five named tables have RLS enabled/forced and `internal_athlete_id`; FK is the expected composite plan/athlete relationship. All prerequisite RPC-presence booleans true.
4. No missing required migration versions, no unexplained later versions and no V2 objects. A5 may be the only missing migration **only if** the preceding 47 are verified. Any other gap needs a separate plan. Do not repair the ledger to simulate execution.

Catalog/body/ledger checks do not prove behavior. Inspect authenticated-role API metadata using an existing tester session locally if permitted; never disclose tokens in chat. A service-role OpenAPI snapshot omitting replay is expected under the deliberate grants. Do not add service_role execute. A production authenticated replay execution is optional read-only evidence after privacy review; use only an existing owned check-in and preserve its exact state. Do not create verification data on production.

Exact Data API checks, after confirming the actual project URL and pinned stable function body: authenticated metadata is `GET <VERIFIED_SUPABASE_URL>/rest/v1/` with `Accept: application/openapi+json`, `apikey: <PUBLIC_PROJECT_KEY>` and `Authorization: Bearer <EXISTING_TESTER_ACCESS_TOKEN>`. Expect `/rpc/get_checkin_plan_proposal` in that role's schema. The read RPC is `POST <VERIFIED_SUPABASE_URL>/rest/v1/rpc/get_checkin_plan_proposal`, same headers plus JSON content type, body `{"p_checkin_id":"<EXISTING_OWNED_CHECKIN_UUID>"}`. HTTP POST here invokes the verified STABLE read function; it is not permission to invoke generation. Do not print/store returned athlete payloads. Open/unattached returns JSON null; attached returns exact persisted plan/proposal; foreign or missing is not found, inconsistent completed state conflicts. Missing-RPC/schema-cache errors, permission failures and network errors are **unknown/unavailable**, not no-plan. If catalog is correct but metadata is stale, have the database owner review a schema-cache refresh as a separate configuration action; do not change grants or silently fall back to generation. Prefer executing all behavioral cases on the disposable database, not production.

## 4. Isolated PostgreSQL A5 validation — owner authorization required

No database tools were installed and no SQL was executed in this task. Owner must authorize disposable local DDL and provision approved Docker/Supabase CLI tools. Record exact tool/container versions and image digests. Verify Docker context is the local machine and no remote `DOCKER_HOST` is configured. The kit has no hosted link/credentials, project ID `wombo-a5-a6-verify`, PostgreSQL 17, DB port 55322, disabled seed, and exactly 48 selected migrations. Do not use `--linked`, a remote URI, hosted `.temp`, `db push`, or production reset.

Fresh replay, using a **new** kit and no pre-existing same-named local container:

```powershell
$kit = (Resolve-Path .runtime/a5-a6-owner-kit).Path
supabase --version
docker context show
docker context inspect
# Inspect output; confirm local Docker and no existing wombo-a5-a6-verify database.
supabase db start --workdir "$kit/isolated-db"
supabase migration list --local --workdir "$kit/isolated-db"
# If needed, apply only pending selected LOCAL migrations, then confirm all 48.
supabase migration up --local --workdir "$kit/isolated-db"
supabase test db --local --workdir "$kit/isolated-db"
```

If the installed CLI requires the full local stack for pgTAP, use `supabase start --workdir "$kit/isolated-db"` on that same **local** kit, not a hosted connection. Review its generated config/provider requirements before starting. The CLI docs describe local migration and test behavior: [migration up](https://supabase.com/docs/reference/cli/supabase-migration-up), [test db](https://supabase.com/docs/reference/cli/supabase-test-db). Commands have not been exercised here; a tool/version/config failure leaves the gate open.

Also test **upgrade from the preceding 47 migrations**, not just fresh replay: generate another new kit, change only its local project ID/ports to unused values, move the A5 file out of that disposable kit's migrations folder, start the local DB and verify 47 entries. Restore the byte-identical A5 file to that kit, run `migration up --local`, confirm exactly one new A5 entry and run its pgTAP suite. Do not edit the source migration or existing local databases. Use the correct newly named container for that second kit.

The accepted A5 pgTAP suite covers role grants, invoker behavior, null/open replay, owner vs foreign/missing, exact repeat IDs, injected attachment failure with rollback, terminal rejection/application and single legacy orphan recovery. Its `FOR UPDATE` assertion is only structural. Capture TAP results and failing assertions; do not claim a pass from process completion alone. Add/execute isolated cases for ambiguous multiple legacy revisions, inconsistent closed attachments, stale/conflicting requests, cross-owner legacy relationships and unchanged history/private values. Existing backend mocks are not substitutes for those cases.

Real concurrency on the first fresh kit, **after** its rollback-only pgTAP suite, uses only synthetic accepted rest-only fixtures. The setup commits fixture rows solely in this disposable container; never use it against hosted data:

```powershell
Get-Content -Raw "$kit/local-sql/isolated-concurrency-setup.sql" |
  docker exec -i supabase_db_wombo-a5-a6-verify psql -X -v ON_ERROR_STOP=1 -h 127.0.0.1 -U postgres -d postgres
```

In terminal A run the same pipe with `isolated-session-a.sql`. When it prints `A_GENERATED_START_SESSION_B_NOW`, immediately run `isolated-session-b.sql` in terminal B. During A's 15-second sleep use a third terminal with `isolated-observe-lock.sql`; its boolean **must be true**, demonstrating B actually waited on a lock. After both commits pipe `isolated-concurrency-check.sql`; all four booleans must be true: two receipts, identical locator, one revision, exact completed attachment. If no wait was observed the race test is **NOT VERIFIED**, even if replay matches. Retain timing/output. Repeat equivalent races for separate owners and a deliberately failed attachment, with no duplicate/orphan revisions. Do not rerun setup in a used database; arrange a separately approved new disposable instance.

None of this tests or authorizes the four V2 migrations. Full PostgreSQL integration for those remains deferred.

## 5. A6 and backward compatibility acceptance

The contract is `GET /api/v1/weekly-plans/recovery`, bearer token, no body/client owner field, 200 `{active: WeeklyPlanResponse|null, pending: WeeklyPlanResponse|null, draft: RecoveryDraftLocator|null}`. It discovers existing RLS-visible locators and hydrates exact revisions without generation or mutation. It preserves unscheduled/rest-only plans, pending/active separation and open drafts. Missing/broken dependencies, auth failures and transient I/O must retain their errors, never `{null,null,null}`.

On the isolated database exercise authenticated owner A/B plus anon, expired tokens and missing/malformed schema responses. Verify null only after successful authoritative discovery, exact plan/proposal/revision/occurrence identity, foreign resource 404, no private load, no new rows on repeated GET, stale revision conflict, retry after lost generation response, shared V1/V2 state, calendar and injury restrictions. Test a previously distributed client and the new UI V2 candidate against both the verified old backend and candidate. Old routes must remain accepted; new UI must retain unknown/unavailable state on the old backend and never regenerate silently. Verify supported activity create/feedback and omission of deferred fields.

After an **approved** deployment and confirmed domain/project identity, a GET-only owner probe is prepared:

```powershell
# Supply the two existing tester access tokens through a protected local environment.
# WOMBO_TESTER_A_ACCESS_TOKEN and WOMBO_TESTER_B_ACCESS_TOKEN; never paste here.
python scripts/verify_a6_readonly.py
```

It stops before account requests unless readiness says production and OpenAPI advertises A6. It verifies two token-derived identities and recovery reads, checks foreign owned plan access gives 404 where plans exist, refuses redirects and prints no payload/token/identity. No existing plan fixtures means isolation is not fully exercised and it returns NOT VERIFIED. This probe does not certify all states, DB behavior or deployment SHA.

## 6. Safe deployment order — separate explicit approval at each mutation

1. Finish production identity/source/config review; select A9 only if actual deployed behavior/history is compatible. Capture rollback artifact/config and inspect auto-deploy/pre-deploy hooks. Stop on unknown identity, unreviewed later history, missing approvals or schema mismatch.
2. Pass isolated A5 upgrade/fresh pgTAP, RLS/grants, atomic failure and real concurrency tests; pass protected production Settings validation and compatibility tests. Build and inventory a tested Linux image from the pinned backend. Current Python dependency ranges and host overrides require review; record the immutable artifact.
3. If A5 is already present and verified, **no migration**. If A5 alone is missing, obtain a distinct owner-approved migration/backup/lock-timeout/recovery plan for **only that exact forward migration**, after prerequisites and isolated results pass. Do not deploy before completion/catalog verification. This document does not authorize or provide a bulk pending-migration command.
4. Obtain explicit approval for the exact backend artifact, production IDs, configuration diff and restart. Correct production mode coherently with genuine approvals/keys. An owner may execute this template **only after replacing and independently checking all IDs** and confirming current CLI authorization (otherwise stop; no automatic login):

```powershell
# NOT EXECUTED. Backend source worktree must be clean at the exact pinned SHA.
git -C .worktrees/wombo-a5-a6-min-backend rev-parse HEAD
git -C .worktrees/wombo-a5-a6-min-backend status --porcelain
railway up .worktrees/wombo-a5-a6-min-backend/backend --path-as-root `
  --project <VERIFIED_PRODUCTION_PROJECT_ID> `
  --environment <VERIFIED_PRODUCTION_ENVIRONMENT_ID> `
  --service <VERIFIED_PRODUCTION_SERVICE_ID> `
  --message "Reviewed A5/A6 backend e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6"
```

The CLI 5.45.10 `up --help` confirms these flags, but `up` can initiate OAuth/project creation when unauthorized. Thus verified authorization/context is a **precondition**, never a login workaround. If using the immutable tar instead, verify its manifest hash and arrange verifiable source identity; do not let the surrounding review/mobile Git SHA be presented as the backend SHA. Never upload the review root or rely on the saved staging link.

5. Confirm exact successful deployment/image, source manifest, actual production environment and `/ready`; authenticate both owners, run A6/legacy API/read-only checks and then the approved two-device smoke tests. Readiness alone does not prove DB health. If approval/config fails, stop; do not set local to hide it.
6. Only then authorize the separate signed EAS verification build and later Internal Testing submission as described in the decoder report. Do not publish merely because a build succeeds.

## 7. Rollback and explicit NO-GO conditions

Backend rollback needs a **known compatible** previous image/revision and production-valid configuration. A5 is forward-only: retain it and all historical data. Prove the previous backend's v3 caller/payload/legacy attachment remains compatible with the A5 wrapper before calling rollback safe. Do not drop functions, rewrite migrations, reset data or recalculate history. If the previous backend or production-valid rollback artifact cannot be identified, rollback readiness is NO-GO. Disabling a feature does not remove dependencies of stored data.

Android recovery uses the same package/signing with a **higher versionCode** carrying reviewed prior UI source; installed apps cannot be forced to downgrade through Play. Keep backend old-client contracts during rollout because testers may update at different times. The new UI on an old backend fails closed on unavailable A6; that is safe degradation, not full supported recovery. Do not claim both revisions are fully compatible until the matrix passes. Feature/config rollback retains data and restores only reviewed safe values; never restore `local` to bypass production governance.

Remaining NO-GO conditions: unknown real production identity/SHA/branch/auto-deploy/rollback; production URL reporting local; unverified genuine governance/keys/providers; any A5/prerequisite/RLS/grant/concurrency gap; any later history incompatible with A9; unsupported legacy/client payload or unsafe recovery; unresolved security review; unverified signed AAB/Play identity/version/tester-device checks. No production change is authorized or performed.
