# Hosted authentication verification environment

14 November 2026. Successor branch `verify/joren-v6-hosted-supabase-auth`, from exact `980e015b5e6546e1259c8585c3ca42c271add9f5`. The owner's later hosted authorization supersedes the earlier local-only restriction. No deployment, migration, activation or global configuration change was authorized or performed.

## Identity and preflight

The existing backend/mobile configuration and CLI link independently identify project `start23-dev`, reference `isfumhgqphieoayqahjv`, endpoint `https://isfumhgqphieoayqahjv.supabase.co`, region `eu-west-1`. Despite the development name, this project was treated with the requested production safeguards. It initially reported INACTIVE. The owner explicitly chose to resume it personally; the verifier subsequently observed ACTIVE_HEALTHY. No resume API was called by this work.

The Management API's dedicated read-only query endpoint inspected migration versions, extensions, RLS, grants, RPC signatures/ACLs, triggers and foreign keys. It found **47 of 63 accepted migrations**, no extra migration versions, and **16 missing migrations**. V6 tables/RPCs are absent. No migrations or disposable SQL suites were executed. The metadata and full Auth configuration compare equal before and after the synthetic run; hashes and permission metadata are in [the sanitized evidence](hosted-auth-20261114/preflight.json).

The sole `auth.users` trigger calls `private.ensure_athlete_identity_map()`: it inserts only the new subject's opaque identity mapping. Its complete function definition was inspected. All inspected Auth hooks and mailer notifications were disabled. Email authentication, automatic confirmation and refresh rotation were enabled; access lifetime was 3,600 seconds, refresh reuse interval 10 seconds. No cron/queue/network-job relations or callback-bearing public/private functions were found; no log drains were configured. Project-management webhook enumeration returned 403, so their absence is **not** claimed. This limitation concerns platform lifecycle hooks; the actual signup trigger and enabled Auth hook settings were inspected directly.

Exactly two confirmed administrative test-account creations used unique run-labelled `.invalid` email addresses. This avoids sending signup email and is the expressly permitted administrative creation alternative; public signup/email delivery was not tested. No provider integrations, analytics events, external activities or LLM calls were enabled. Supabase necessarily retains its ordinary infrastructure request logs; no application logging drain was present. No unrelated athlete rows were queried.

## Runtime and evidence boundaries

Actual hosted PostgreSQL: **17.6**, Linux; GoTrue health reported **v2.197.0** through the API-key gateway. Extensions: `pg_stat_statements 1.11`, `pgcrypto 1.3`, `plpgsql 1.0`, `supabase_vault 0.3.1`, `uuid-ossp 1.1`. [Postflight evidence](hosted-auth-20261114/postflight.json) records health and unchanged configuration; unexposed managed gateway/PostgREST versions are not inferred from cached CLI files. CLI **2.76.8** was already cached; nothing was installed.

The backend ran locally on IPv4 loopback with its real HTTP repositories and real ES256/JWKS access-token verifier against this endpoint. No V6 helper was injected and its loopback restriction remains unchanged. The production planner/dependency was never changed. Local settings kept unavailable Realized V2 integration disabled and supplied no LLM key. This exercised the deployed **historical** schema through a local backend, not a deployed replacement backend.

Local software versions and exact checks are recorded in [verification.json](hosted-auth-20261114/verification.json). Historical local evidence remains distinct: 722 pgTAP assertions in 37 suites with the explicit existing A5 fixture overlay; the original A5 fixture's known failure is preserved. None were rerun against hosted production.

## Reproduction without unsafe test runners

Review current owner authorization and repeat the read-only preflight before allowing writes. Use the existing authorized URL/publishable/secret credentials through an ignored private file; never put credentials in command arguments, reports or mobile code. The preflight uses the existing CLI Management credential in memory, reading only the CLI's documented credential targets on Windows. Protect the private run directory with an owner/SYSTEM ACL before account creation.

From `backend`, using the existing Python environment:

```powershell
python -m scripts.verify_v6_hosted_auth --preflight-output ../.runtime/hosted-auth/preflight-reviewed.json
python -m scripts.verify_v6_hosted_accounts --execute-two-synthetic-accounts --preflight ../.runtime/hosted-auth/preflight-reviewed.json --credential-file <private-env-file> --private-directory ../.runtime/hosted-auth/<new-run> --phase authenticate
```

Use the same exact directory for `auth-checks` and `security-reads`; never substitute an old manifest for a new run. The lifecycle runner uses `--execute-synthetic-lifecycle`, the same credential/private-directory arguments, and phases `prefix`, `finish`, `audit`, `gates`, `swipe`, `restore`, `auth-negatives`. `restore` follows account `logout` then `authenticate` on those same two users. Read the observed historical move limitation before interpreting results. A failed/uncertain mutation stops for journal inspection; do not retry creations or reset the journal blindly.

Inventory with `python -m scripts.verify_v6_hosted_inventory --private-directory <same-directory> --stage before-cleanup`; then account phases `logout`, `cleanup`; then inventory `after-cleanup`. Wait for the original GoTrue-issued tokens' real expiry before phase `expiry`. That phase never changes the clock, lifetime or token. Finish with a new read-only preflight and compare metadata/configuration. The runner has no project-resume, migration, role-grant, arbitrary-SQL, account-enumeration or broad-delete mode.

Branch listing succeeded with no existing branches. Provisioning entitlement/capacity was not established and no branch was created. A separate hosted branch requires owner approval of cost and isolation/copy behavior. Published Micro branch compute starts at **$0.01344/hour**, without compute credits, with possible additional usage charges; recheck current pricing before provisioning. See [Supabase branching usage](https://supabase.com/docs/guides/platform/manage-your-usage/branching) and the [unexecuted deployment plan](JOREN_V6_HOSTED_MIGRATION_DEPLOYMENT_PLAN.md).

## Local regression commands and results

| Command (existing environment, from indicated directory) | Result |
| --- | --- |
| Backend: `python -m pytest -q` | 2,891 passed; one existing Starlette/httpx deprecation; 354.77 seconds |
| Backend: `python -m ruff check .` and `python -m ruff format --check .` | PASS; 245 files formatted |
| Backend: `python -m mypy --strict app tests benchmarks` | PASS; 223 source files |
| Backend: `python -m mypy --strict --explicit-package-bases scripts/verify_v6_hosted_auth.py scripts/verify_v6_hosted_accounts.py scripts/verify_v6_hosted_lifecycle.py scripts/verify_v6_hosted_inventory.py` | PASS; four scripts |
| Backend: `python -m pytest -q tests/test_hosted_verification_guards.py` | Final runner guard recheck: 11 passed; mocked network only |
| Mobile: `npm test -- --runInBand` | 935 passed in 89 suites; 159.314 seconds |
| Mobile: `npx tsc --noEmit --strict` and `npx tsc --noEmit --strict --noUnusedLocals --noUnusedParameters` | PASS, using already installed dependencies |
| Backend: `python -B -m benchmarks.v6_planner_performance --variant optimized --output <new-local-output.json>` | 40/40 historical cases unchanged; 26/26 accepted completed reference results unchanged; original eight-second `current:build_4` diagnostic timeout retained |
| Backend: `python -B -m benchmarks.v6_search_oracle --output <new-local-output.json>` | 15 contexts, 20,061,679 products; all result fields except timing equal to accepted oracle |

The historical benchmark ran after the full test run; no parallel CPU benchmark altered its original resource bounds. Corpus and oracle JSON, comparisons and source custody are included in the evidence directory. Source migrations, SQL fixtures, planner/domain code and benchmarks are unchanged from the accepted base. The earlier 722 local SQL assertions were not repeated here.
