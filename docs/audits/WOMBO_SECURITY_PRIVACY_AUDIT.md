# WOMBO security and privacy audit

Audit date: 26 October 2026. Source: `aff74558d0a6511286a4a84a44ea25a03ca57549`. Read alongside [the main audit](WOMBO_FULL_SYSTEM_AUDIT.md), which contains the full finding records and evidence limits.

**Assessment:** useful defense in depth is present in source, but real-user beta security/privacy cannot be signed off. No P0 breach or cross-athlete disclosure was demonstrated. The production-designated runtime reports `environment: local` (WOMBO-001); exact hosted grants/settings and end-to-end two-user/Storage isolation were not rerun. This report is not a GDPR/legal-compliance opinion.

## Verified boundaries and limits

| Boundary | Source evidence / current design | Verification performed | Remaining gate |
| --- | --- | --- | --- |
| JWT verification | `backend/app/core/security.py:56`: ES256-only signing key verification; audience, issuer, exp, iat, optional nbf and required subject/role; service/anon role rejected | Existing locally signed-token authentication tests passed, including invalid signature/expiry; no real JWT printed | Current hosted key rotation, issuer/project pairing, unknown-key availability and revoked-session behavior |
| Athlete identity | `api/dependencies.py`: verified Auth subject -> `get_current_athlete_id`; `modules/identity/repository.py` resolves opaque identity | Identity/repository tests and owner tests passed | Real two-token opaque/legacy RPC path with different Auth UUID and opaque athlete UUID |
| Owner Data API | Owner JWT + publishable key on normal reads/owner RPCs; explicit owner predicates and RLS; no authoritative client user_id | Memory service/API and MockTransport tests passed; SQL owner policies/functions inspected | Fresh pgTAP for 27 suites and two-real-token negative access on a synthetic staging project |
| Privileged path | Separate secret-key repositories; private loads, catalog, calculations and provider operations through service-only RPCs with scoped athlete IDs | Existing tests verify headers/ownership and selected denial behavior; no secret pattern found in tracked application source | Hosted EXECUTE grants for every overload, owner parameter verification under service role and public/anon denial |
| Critical state | Explicit pending revision and proposal; expected base revision, draft revision and fingerprints; DB locks/transactions | Local stale/replay/duplicate/owner tests passed | Actual PostgreSQL races, adjacent-week dependency changes, concurrent onboarding mutation during approval |
| Mobile credentials | Refresh token in SecureStore with device-only unlock setting; access token in memory; no privileged mobile key found | Source scan and audit AuthProvider probe | Final AAB/static/native inspection; physical-device OS backup/keychain behavior; transient bootstrap fix (011) |
| Private load | `private.*` load tables; explicit public JSON projections and Pydantic DTOs; pure-domain representations hide internal load | Existing recursive schema/selected runtime-response tests and mobile privacy-source test passed | Real Data API projections, denied direct private access and raw error/log/observability verification |
| Storage | Private `activity-files` bucket, per-owner paths, explicit owner read policy; secret-only upload | Source and transport tests passed | Two real synthetic users: A cannot read B's object; metadata/object owner consistency; delete lifecycle |
| Polar | One-time OAuth state hash/expiry; server token; HMAC signature/time replay checks; deterministic entity validation; bounded historical retry | Existing domain/provider/webhook tests passed | Provider registration/callback/signature with test account, scheduling, durable background processing, terms/privacy approvals |
| LLM | Strict schema, no tools, timeout/output bounds, `store:false`, deterministic fallback and public facts only | Local context/coach schema, forbidden content and fallback tests passed | Configured provider/model, processor agreements, actual retention and logging; production review gate bypass must be resolved |

Supabase distinguishes grants from RLS: both need verification. Service-role access is not protected by ordinary user RLS. Owner checks remain necessary on every service-only RPC. These are platform semantics, supported by the [Supabase RLS documentation](https://supabase.com/docs/guides/database/postgres/row-level-security), and are not inferred solely from tests.

## Cross-account adversarial review

The backend suite ran owner-denial paths for plans/proposals/activities and other resources with synthetic A/B identities. Source functions derive owner identity from `auth.uid()` or accept a server-scoped athlete ID only on explicitly restricted service paths. Normal endpoints do not authorize based on a body/query `user_id`. No authorization decision based on mutable `user_metadata` was identified in the inspected core path.

The mobile A/B/A audit found **local locator contamination, not a data-access bypass** (009). Planning/activity providers remount by identity, and delayed activity results use an alive guard. Plan generation lacks the equivalent guard around persisted locator writes. B's owner request is denied, but B deletes A's global locator. The security recommendation is to scope local metadata and side effects, not weaken RLS or suppress ownership errors.

Database tests were not executed in this session: Docker, psql and pg_prove were absent. Existing database suites and earlier hosted reports are not fresh proof. No real users were created, impersonated, queried, updated or deleted. No hosted SQL, migration, Storage write, OAuth connect or provider import was run.

The opaque-owner Storage migration was inspected through its latest definition. The old policy compared the first folder to Auth UUID; the R3 migration `20260912072232` replaces it with a policy allowing the current opaque athlete prefix or legacy Auth prefix. Therefore the old-policy mismatch is **not** reported as an unfixed bug. A transport test reuses the same identifier for opaque and legacy identity, so a distinct-ID database test is still necessary.

## Session lifecycle

- Login/signup is through Supabase password auth; confirmation-required signup returns an explicit email notice.
- Access JWT validity is checked cryptographically, not by calling Auth for every request. The backend does not independently check `session_id` against `auth.sessions`.
- Logout requests Supabase `scope: local`, clears secure refresh material and unmounts authenticated content. Other-device sessions are intentionally not globally signed out by that call.
- Supabase access tokens and refresh sessions have different lifecycles. Immediate revocation of every already-issued access JWT is not established. Decide any stricter requirement and verify it against [Supabase sessions](https://supabase.com/docs/guides/auth/sessions) and [sign-out scopes](https://supabase.com/docs/guides/auth/signout); do not label ordinary JWT expiry behavior an exploit without a product requirement.
- Offline bootstrap incorrectly deletes a credential on a retryable refresh error (011). SecureStore read/refresh exceptions also lack an explicit retry UI.
- Complete password-recovery, all-device revocation and account-deletion journeys are not present in the integrated mobile app. A support/reset process must be defined before relying on them during beta.

## Sensitive-data flow and lifecycle

| Data | Origin and storage | Exposure/control | Retention/deletion assessment |
| --- | --- | --- | --- |
| Email, password, Auth session | Supabase Auth; mobile memory/SecureStore | Backend receives access token, not password; refresh material device-secured | Auth settings/session policy unverified. No integrated account-deletion operation |
| Names | Identifying profile separated from physiology | Owner-scoped DTO/profile API | Optional names cannot be cleared through mobile (018); API supports nullable identifying fields |
| DOB, resting HR, monitor/timezone, sport history | Split physiological/operational profiles and versioned onboarding | Owner token/RLS, immutable calculation provenance | Current readiness requires DOB/resting HR. An untracked draft saying resting HR optional conflicts with implementation; owner must reconcile |
| Race goal, available days, plans and execution | Owner tables; immutable revisions and public snapshots | Public API excludes private load; explicit approvals | Historical retention intentional while account exists. A precise policy and deletion procedure remain undecided/unverified |
| RPE, activity measurements, zones, injuries, fatigue | Activities/calibration/check-in records; private derived load separate | Owner APIs, service-only deterministic processing | Health-related data handling and any consent/legal basis require owner/legal decision; no legal conclusion here |
| Polar token and identifiers | Server-only private tables and integration RPCs | No token in public connection DTO; database/platform controls rather than demonstrated app-layer encryption | Disconnect revokes provider and removes token, retains imported activities/files; final processor settings not verified |
| Raw FIT files | Server downloads to private Supabase Storage | Potential location/health content even though summary request disables route; file path owner RLS | Configurable retention days exist but no purge job/use was found. Relational FK cascades alone do not remove Storage objects |
| Check-in helper text | Backend -> optional OpenAI extractor | Bounded text, schema validation, no persistence by that endpoint, no mutation authority | `store:false` does not prove zero provider/security-log retention. DPA, enabled state and backup/log policy remain unknown |
| Generated explanation | Qualitative plan facts -> optional OpenAI -> pending proposal text | Forbidden private-load language guard, no free athlete text in explanation facts | Proposal text is retained with history; provider-side handling unverified |
| Logs/request IDs | Railway stdout; structured formatter and exception handler | Requests get independent correlation IDs; no request-body echo in validation responses | General exception formatter emits traceback text and arbitrary extra fields; no blanket secret/private-load scrubber. No actual sensitive log leak was demonstrated; test this boundary before logging new payloads |

WOMBO-014 records the implementation gap. Operational/privacy sign-off requires an identified controller/contact, approved purposes/legal conditions, age eligibility, health-data handling, processor/region arrangements, per-entity retention, access/export/deletion channel, provider revocation, Storage purge, backup treatment and incident ownership. The audit does not invent these decisions or authorize data deletion. Original-worktree privacy drafts contain placeholders and were not treated as published commitments.

## Error, log and secret handling

Pydantic request errors return only locations/types, not submitted values. Repository adapters translate database/provider failures to stable safe errors; private physiology values are excluded from public models. `X-Request-ID` is generated independently of incoming user headers. The client discards it rather than offering it for support correlation, which limits investigation of real device failures.

The pattern scan found no tracked non-example `.env` file or privileged credential pattern in the inspected application source. Dummy backend test keys were excluded deliberately. No environment contents, database password, service secret, Auth refresh token or provider token were printed by release metadata probes. This is a heuristic current-source scan, not a secret-history, PDF or final-binary certification. Earlier documentation records a historical CLI key-output incident; whether rotation/legacy-key disablement occurred remains an owner verification gate.

There is no broad application rate limiter in the core router/main configuration; Pioneer has a specific database-backed attempt limit. External platform limits are unknown. The measured synchronous planner hotspot (007) warrants availability protection independent of whether an external limiter exists. Webhook raw request bodies are read before an application body-size check, and `get_fit` buffers the response before checking size; these are optional-integration hardening risks, not demonstrated hosted denial-of-service incidents.

## Dependency evidence

The valid current registry result is [npm-audit-clean.json](evidence/npm-audit-clean.json): 21 affected package entries, 1 critical/9 high/11 moderate according to npm. Locked `shell-quote` is 1.10.0, affected by the upstream [shell-quote advisory](https://github.com/ljharb/shell-quote/security/advisories/GHSA-pqg4-j6r4-53mv), patched at 1.11.0. The upstream page calls the advisory high; the npm snapshot calls it critical. Wombo's application finding remains P2 because reachability/exploitability was not established. Most reported paths involve build tooling. Do not apply a forced Expo downgrade; trace the exact call path and validate compatible updates separately.

## Required closure evidence

Before real-user beta, resolve 001–004/011/014/017 and execute fresh synthetic A/B authorization checks over API, Data API and Storage with the exact candidate schema. Verify revoked/expired sessions, negative direct RPC access, owner/foreign occurrence relationships, stale/duplicate approvals, correction preconditions and forbidden private fields in nested success/error output. Inspect the actual build and production configuration without revealing secret values. Keep these tests in an isolated local/staging project; creating users, Storage files or rows in staging requires separate authorization. No such mutation was performed here.
