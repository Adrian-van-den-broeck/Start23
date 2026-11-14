# Real hosted GoTrue and gateway results

Two genuine synthetic Auth users, A and B, were created through the approved administrative endpoint and authenticated through `/auth/v1/token?grant_type=password`. No manually signed account credentials were used. Sanitized individual HTTP outcomes, including intermediate attempts, are in [auth-results.json](hosted-auth-20261114/auth-results.json).

| Check | Observed result |
| --- | --- |
| Administrative creation, password login, authenticated `/user` | 200 for both; public signup/email confirmation delivery not exercised |
| Real access and refresh credentials | Issued by hosted GoTrue; kept only in ACL-protected ignored storage during execution |
| Signature and identity | Actual ES256 JWKS key, issuer, audience, subject and authenticated role verified by the unchanged backend verifier |
| Opaque mapping through actual gateway RPC | 200; two distinct opaque athlete IDs, different from Auth subjects |
| Refresh rotation and refreshed identity | 200 for both; rotated credential pairs and correct user |
| Missing/invalid API key, publishable key without user, missing access token | 401 for both |
| Tampered genuine access token | GoTrue 403 for both; local FastAPI 401 |
| Wrong expected issuer/audience/public key | Rejected locally using genuine issued tokens and actual JWKS; not claimed as separate gateway negative issuer tests |
| Athlete calling service-only generation RPC | 403 for both |
| Athlete calling exact other synthetic Auth admin user endpoint | 403 for both |
| Global logout | 204 for both; refresh subsequently 400, GoTrue `/user` 403 |
| Residual signed access after logout | Data API still 200 before expiration; immediate universal JWT invalidation is not supported by this observed contract |
| Password login after logout | Successful for the same two users; persisted own plans/draft restored |
| Real time expiry | Both original issued tokens rejected by native PyJWT, unchanged backend verifier, and gateway 401/PGRST303 with explicit expiry; lifetime and clocks never patched |
| Supported deletion | Exact two test users deleted; subsequent admin GET 404 each |

Initial immediate login verification exposed a subsecond local clock lag relative to GoTrue `iat` and raised `ImmatureSignatureError`. The harness subsequently waited until that genuine timestamp, without altering tokens, verifier or leeway. The failed attempts remain recorded; successful later verification is not presented as an immediate-first-attempt pass.

After the actual one-hour lifetime, A's first gateway expiry probe returned 401; B's first returned **500**, which did not satisfy the expiry assertion. Narrow read-only rechecks returned explicit 401/PGRST303 expiry for both; the unfinished B assertion then passed. The one-off 500 is retained without an invented root cause or a first-attempt success claim. There was no accepted expired-token operation.

The publishable key routes requests through the hosted gateway; it grants no user identity by itself. The modern secret key remained server-side and was used only for the reviewed administrative creation/deletion and the normal backend service RPCs scoped to these synthetic identities. This does not prove every possible service-role permission safe: a service credential is privileged and must remain private. Both browser-facing roles were denied the exercised service/admin operations.

Logout revokes refresh/session state while already issued JWTs can remain accepted by services until expiry. This matches [Supabase's sign-out contract](https://supabase.com/docs/guides/auth/signout). Direct per-request session-store revocation is not newly added to the backend. Any requirement for immediate access-token invalidation needs an explicit operational decision.

## Local A5 compatibility fix

Only typed `PlanningConstraintError(code='v6_search_incomplete')` gains the existing optional `details.planning_code` field. HTTP 422, top-level `validation_failed`, existing message, request ID and rejected/nonretryable semantics remain intact. Other validation and planning errors are unchanged; the ordinary planning route retains its structured response. Mobile retains only this constant discriminator and uses its existing qualitative message. Arbitrary detail fields are not propagated.

Local route, replay, mobile allowlist/no-retry, public contract and full regression tests cover this additive behavior. It does not alter onboarding, pending approval, activity attachment or recovery orchestration. It was **not deployed**, and hosted V6 search exhaustion could not be exercised because its migrations/dependency are unavailable. Protected A5/A6 worktrees were not modified.
