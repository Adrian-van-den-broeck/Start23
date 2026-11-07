# V6 signed-token HTTP isolation ? 7 November 2026

**EXECUTED/PASS: 38 checks against real PostgREST 16.5 and PostgreSQL 17.11.**
The target was only `http://127.0.0.1:55431`, connected to the disposable
`wombo_v6_verify_final_20261107` database. Signing material was generated locally,
kept in ignored runtime files and never committed or printed. Two distinct fixture
subjects in `auth.users` received distinct HS256-signed bearer tokens.

`backend/scripts/verify_v6_postgrest.py` executed both directions of isolation:

- Own V6 reads, own confirmation, identical confirmation retry and confirmed reload succeed.
- Foreign V6 reads and confirmation reject with owner-safe P0002. Bare PostgREST maps P0002 to HTTP 500; FastAPI maps that repository condition to 404. The check requires the exact P0002 code, not arbitrary server failure.
- Foreign weekly-plan/revision/workout table reads return no rows. Updates affect no rows or fail permissions.
- Athlete calls to the generated-write RPC, spoofed athlete arguments and private catalog RPC reject.
- Catalog activation updates reject; inactive catalog reads return no rows.
- The private schema is inaccessible through the Data API.
- Missing, expired and incorrectly signed tokens reject.
- A valid locally signed service token can use the narrow private catalog RPC; all 77 documents return only to that privileged test client.

Athlete response keys are recursively checked for private load/source payloads.
The complete backend recursive confidentiality/OpenAPI suites also pass. Direct
SQL grants, forced RLS, SECURITY DEFINER behavior, immutable sources and composite
owner FKs were executed separately; SQL GUC simulation is not counted as signed-token evidence.
A real service-token HTTP write was additionally exercised by the lost-acknowledgement test.

[Per-request status ledger](postgres-verification-20261107/signed-token.json).
No JWT or private response body is in the committed evidence.

## NOT VERIFIED boundaries

GoTrue signup/password login, refresh/revocation/session lifecycle, hosted
Supabase's gateway and modern publishable/secret-key routing, and actual ES256
issuer/audience/JWKS integration were not run. No GoTrue service was installed.
The tests prove local PostgREST signature verification and database ownership
isolation for the two synthetic subjects; they do not claim those additional
Supabase/FastAPI authentication boundaries have passed. No production or staging
account, credential, token or connection was used.
