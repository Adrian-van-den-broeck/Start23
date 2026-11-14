# WOMBO V6 GoTrue and gateway verification

14 November 2026. Base `dbeb9596f42f0504e428afbf5eddc75eaa7d20da`.

**BLOCKED — ENVIRONMENT. Zero GoTrue-created accounts, GoTrue-issued sessions,
refreshes or actual Supabase gateway requests were executed.** The environment
inspection and reproducible prerequisites are in
[the environment report](JOREN_V6_REAL_AUTH_ENVIRONMENT.md).

## Required real-credential matrix

Every row below is **NOT EXECUTED / BLOCKED — ENVIRONMENT** in this delivery.
These are required follow-up checks, not automated tests claimed ready or passing.

| Scenario | Required observation on the actual disposable stack |
| --- | --- |
| Signup A and B | Gateway `POST /auth/v1/signup`; distinct real Auth users and persisted GoTrue sessions; no direct inserts into `auth.users` |
| Password login | Gateway `POST /auth/v1/token?grant_type=password`; real access/refresh pairs for both accounts |
| Gateway identity | Authenticated `/auth/v1/user`, actual `/rest/v1` owner reads and unchanged FastAPI protected routes succeed for their owner |
| Opaque identity | Auth subject differs from opaque athlete ID; supported identity resolution/RPCs derive the same owner; body/query owner overrides do not select another athlete |
| Onboarding | All current prerequisites are completed through the supported athlete routes, including monitor, timezone, structured race, history and confirmed zones; incomplete onboarding fails closed |
| Refresh | Real refresh grant rotates the credential pair; current access works. Check old refresh behavior against the recorded reuse window rather than assuming immediate rejection |
| Expiry | Retain an actually issued token until its real expiry; it is rejected by gateway and FastAPI afterward. Do not replace this with a freshly signed expired fixture or a clock patch |
| Logout/revocation | Revoke a real session with supported logout scope; its refresh fails. Measure access-token behavior before and after expiry separately |
| Tampering | Change an issued token's bytes and prove signature rejection; no replacement signing |
| Issuer/audience/key | Check real issued claims privately, ES256 and advertised kid/JWKS, configured issuer and audience. Use another isolated real issuer/key or supported isolated Auth configuration for negative issuer/audience/key cases; no manually signed account credential |
| API-key routing | Missing/invalid API key denial where required; publishable key with A/B access tokens enforces their RLS. A publishable key alone must not grant athlete ownership |
| Backend secret routing | The server-only secret enables only the intended service operations; it is not accepted as an athlete JWT. No secret is sent to mobile |
| Reviewer boundary | User metadata, publishable/authenticated/service credentials cannot designate reviewers or execute the restricted registrar; no real operator or maximum is invented |
| Concurrency | A/B requests overlap across reads/writes, preference CAS, check-in attachment, submission, confirmation and authorization suspension; one receipt and stale rejection remain authoritative |

Use the actual official gateway for every Auth/Data API call and set the backend's
Supabase URL to it. A direct PostgREST URL proves neither API-key conversion nor
GoTrue routing. FastAPI requests must use the production verifier class against
the local JWKS; do not inject `Verifier`, `PlanningTokenVerifier`, `MockTransport`
or SQL JWT GUCs into the real-auth run. Only the existing explicit local V6
dependency seam may be installed; normal startup remains unchanged.

Keep password, key, JWT, decoded claim payload, refresh/session IDs and response
bodies in ignored owner-only files. Publish only case labels, status/code,
counts and pass/fail observations. The issued credentials must originate in the
real password flow; do not mint credentials for either synthetic account.

## Revocation is two distinct tests

Supabase documents that logout destroys refresh credentials while already issued
access JWTs can remain usable until expiry. Record logout scope and refresh
rejection, then record the remaining access window and eventual rejection.
See [Supabase signout](https://supabase.com/docs/guides/auth/signout) and
[sessions](https://supabase.com/docs/guides/auth/sessions).

Source inspection finds the existing FastAPI verifier validates signature,
ES256, issuer, audience, required claims, expiry and authenticated role against
cached JWKS. It does **not** query `auth.sessions` on each request. Immediate
access invalidation after session logout must therefore not be claimed. If
immediate rejection is a release requirement, its policy and implementation
remain a separate unresolved decision; no session proxy, new rule or identity
redesign is introduced here. Key revocation/cache behavior also needs real
measurements; the backend's default JWKS-set cache is 300 seconds. The official
[signing-key documentation](https://supabase.com/docs/guides/auth/signing-keys)
explains why gateway and custom backend revocation observations can differ.

## Evidence actually available

Fresh backend tests pass for missing/malformed/expired/bad-signature tokens,
authenticated-role enforcement and token-derived identity. Those use controlled
unit credentials/verifiers. Fresh local PostgreSQL checks validate database
roles, grants, RLS and constraints under SQL-set claims. No new directly signed
PostgREST-token test was run here. Earlier direct-token evidence remains
[historical evidence](final-security-20261108/AUTHENTICATION.md), explicitly
separate from both today's checks and a full-stack PASS.

The real Auth/gateway release gate remains open, regardless of the passing
software/SQL checks. No real user/session cleanup was necessary because no real
accounts were created.
