# Real authentication and gateway gate

**BLOCKED — ENVIRONMENT: no GoTrue-issued session or Supabase gateway request
was executed.** There are zero real Auth accounts, zero issued sessions and zero
gateway checks in this delivery. Directly inserting synthetic `auth.users` rows
does not create genuine GoTrue accounts or sessions.

## Actual environment inspection

The workstation has the previous workspace-local PostgreSQL 17.11, pgTAP 1.3.4
and PostgREST 16.5. They were reused read-only, with fresh data/configuration/logs
in this task's ignored runtime directory. Docker, Podman and the Supabase CLI
were absent from PATH; standard Docker/Podman installation directories and
matching services were absent. Initial WSL enumeration was denied by the sandbox.
The approved read-only `wsl --list --quiet` then exited 0 with empty output:
**no installed distribution**. No system-wide installation was attempted.

Current official documentation describes native local-stack operation on Linux
and Apple-silicon macOS, and explicitly excludes Windows. This prevents treating
the presence of Go and portable PostgreSQL as a ready complete Supabase stack.
See [Supabase runtime requirements](https://supabase.com/docs/guides/local-development/docker-and-native-runtimes)
and [the official Docker stack](https://supabase.com/docs/guides/self-hosting/docker).
No custom reverse proxy, manually minted token, SQL role simulation or auth-table
fixture is substituted for the missing gateway/GoTrue PASS.

## Verification boundaries

| Requested scenario | SQL / direct signed-token evidence | GoTrue through actual gateway |
| --- | --- | --- |
| Signup, password login, real session creation | NOT EXECUTED | BLOCKED — ENVIRONMENT |
| Authenticated public API access | EXECUTED / PASS: direct PostgREST owner reads | BLOCKED — ENVIRONMENT |
| User-to-opaque-athlete mapping | EXECUTED / PASS: actual SQL identity mapping and unchanged backend identity tests | BLOCKED — ENVIRONMENT |
| Cross-user reads | EXECUTED / PASS: both directions of HTTP/table isolation | BLOCKED — ENVIRONMENT |
| Cross-user proposal creation | EXECUTED / PASS: generated-write/spoofed-owner RPC denies athlete | BLOCKED — ENVIRONMENT |
| Cross-user swipe/edit and foreign references | EXECUTED / PASS: SQL lifecycle tamper and composite-owner FK checks; HTTP foreign table writes denied | BLOCKED — ENVIRONMENT |
| Cross-user confirmation | EXECUTED / PASS: both directions over PostgREST | BLOCKED — ENVIRONMENT |
| Missing token | EXECUTED / PASS: direct PostgREST rejects | BLOCKED — ENVIRONMENT |
| Invalid signature / expired token | EXECUTED / PASS: direct PostgREST rejects local HS256 tokens | BLOCKED — ENVIRONMENT |
| Token refresh, session renewal/revocation | NOT EXECUTED | BLOCKED — ENVIRONMENT |
| Service/server authorization boundaries | EXECUTED / PASS: narrow service RPC allowed, athlete generated-write/catalog denied | BLOCKED — ENVIRONMENT |
| RLS over HTTP | EXECUTED / PASS: direct PostgREST | BLOCKED — ENVIRONMENT |
| Recursive public private-load exclusion | EXECUTED / PASS: direct HTTP response checks and full backend public-contract suite | BLOCKED — ENVIRONMENT |
| Immutable catalog/confirmed snapshots | EXECUTED / PASS: HTTP catalog denial and real SQL update/insert custody | BLOCKED — ENVIRONMENT |
| Actual issuer/audience/JWKS and modern gateway API-key routing | NOT EXECUTED | BLOCKED — ENVIRONMENT |

The **38** independently repeated directly signed-token requests are enumerated
in [the per-request ledger](signed-token-postgrest.json). Two SQL fixture subjects
use distinct manually signed HS256 tokens. Signing material is newly generated,
local-only, ignored, and absent from committed reports. No production/staging key,
account or credential was used. The actual committed-response-loss probe has its
[own result](commit-loss.json); it proves one real transaction and retry, not Auth.

Bare PostgREST maps owner-safe P0002 to HTTP 500; the checks require that exact
code, not an arbitrary failure. Existing FastAPI handling maps it to 404. This
task does not change the authorization model or error mapping.

## Smallest missing reproducible setup

Supply a supported isolated Linux environment (glibc 2.35+, non-root PostgreSQL
owner) for the official native runtime, or an owner-authorized working local
Docker/Podman engine. Installing a WSL distribution, virtualization components or
Docker system-wide on this Windows workstation needs separate authorization;
none is implied by an executed PASS here. No hosted fallback is required.

On that environment, pin and record the CLI/service versions and archive/image
digests. Discover the CLI commands with `--help` before use. Create a fresh local
project and unique ports; retain all generated secrets in ignored files. With
the official full Supabase auth/gateway/schema prerequisites running, apply all
59 project migrations in order, and run the disclosed A5 overlay plus all suites.
Do **not** use the stock-PostgreSQL auth/storage subset bootstrap in a real
Supabase installation.

Create A and B via the gateway's real signup/password flow, obtain their
GoTrue-issued tokens and refresh tokens, then execute every scenario in the
table through that gateway and the unchanged FastAPI identity boundary. Use
authenticated RPCs to establish normal owner mappings and onboarding. Exercise
session refresh/revocation, issuer/audience/JWKS, modern publishable/secret routing
and service-role boundaries explicitly. Record safe status/code/count ledgers,
never credentials or private response bodies. Keep failures and unexecuted cases
separate. This is a **NOT EXECUTED** follow-up recipe, not prepared-test PASS evidence.
