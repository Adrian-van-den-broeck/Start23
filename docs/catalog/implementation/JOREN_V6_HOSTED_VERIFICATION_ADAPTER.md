# Restricted hosted V6 verification adapter

Status: implemented and locally verified; **not executed against hosted GoTrue or production**. Successor of readiness SHA `0fa6509190d292d0c83e3076cda68c55624c202e`. Normal production startup and its loopback-only `install_local_v6` protection are unchanged.

## Separate process and target custody

`backend/app/verification_v6.py` exports a separate `create_verification_app` factory, without a module-level app. Normal `app.main` does not import it. The explicit launcher `backend/scripts/run_v6_hosted_verification_adapter.py` requires `--execute-approved-isolated-hosted-only`, an owner-approved manifest, private settings, a private journal directory and an independently managed enabling file. It listens on loopback, uses one worker and disables access logging. An owner may separately approve a controlled transport to that process for mobile testing; it must not become a public production feature flag.

The frozen, extra-forbidden manifest binds one isolated synthetic target to its exact 20-character project reference, HTTPS hostname, issuer, `authenticated` audience, run ID and approval reference. Production project `isfumhgqphieoayqahjv` is unconditionally rejected. Exactly two distinct manifested synthetic Auth subjects, opaque athlete UUIDs and `.invalid` email addresses are allowed. There is no account creation or general user enumeration.

Before serving requests, independent read-only checks establish the Management API target identity/status, fetch each exact Auth subject and compare the service-side subject-to-athlete mapping. Settings must independently match the same target, JWKS, issuer and audience. Polar/OpenAI integration configuration is rejected. Current credentials and real target identifiers belong in owner-protected local files, never this repository or mobile configuration. The launcher protects its journal directory; the operator must also verify the settings, manifest and enabling-file ACLs and use a dedicated directory without unrelated explicit grants.

Each request uses the existing real ES256 `SupabaseAccessTokenVerifier`. The verified JWT subject must be manifested, and the current owner map is checked again before any response replay. A valid token for another athlete, a changed opaque mapping, expired/forged token, alternate issuer/audience/host or changed manifest cannot be adopted.

## Routes, service authority and private data

The factory assembles an explicit operation allowlist from existing typed route modules and approved V6 services. It does not expose arbitrary routes, SQL, migrations, permission management, account provisioning, coach/provider integrations or an arbitrary V6 toggle. V6 repository/catalog wiring is explicit inside this factory only. Frequency controls retain their real authorization requirements: `allow_test_frequency_controls` stays false, no reviewer is fabricated, and the adapter does not grant weekly load or frequency authority.

The restricted outbound transport pins HTTPS host/port and exact RPC/table operations. A request context binds the verified subject and opaque athlete ID. It validates identity arguments, rejects credential substitution and injects/checks owner filters for reads. Reverse owner-map responses must match. Foreign resource IDs continue through the existing owner checks; they cannot switch transport ownership. The service credential stays inside the process.

Responses pass the existing typed public contracts and an additional recursive redaction boundary. Private planned/realized TSS, private load, evidence/provenance/frozen contexts, tokens and secrets are rejected, including suspicious keys, nested content and serialized text. Safe error handling prevents upstream private bodies or traceback data from becoming public error responses. This wrapper does not change normal production exception handling.

## Mutation journal, retries and stopping

The write-ahead journal uses an exclusive process lock and atomic, flushed replacement. It records manifest/run digest, subject, opaque owner, UUID idempotency key, exact method/path/query/body hash and relevant preconditions. A known successful response has an integrity hash and is replayed only after fresh authentication, owner-map and redaction checks. A reused key with different content is rejected.

An unknown mutation blocks new operations for that owner. Retrying its exact key enters **read-only reconciliation**; the transport rejects any attempted second write. Frequency preference reconciliation reads the existing owner receipt and requires the same operation ID, `expected_revision + 1` and exact preference content. Local tests simulate a lost acknowledgement, process restart and recovery without another write. Existing immutable receipt flows can reconcile through their typed read paths when no writer is needed. If an outcome cannot be proved, the operator must stop and reconcile the exact owner record under separately approved read access; changing the key, resetting the journal or guessing success is not permitted.

The independent enabling file contains the exact manifest digest. Removing/changing it disables ingress and is checked again before every outbound write. Stopping the exact recorded process is the second kill switch. The file is never created automatically. No automatic restart, migration, permission change or global cleanup is available.

## Restricted cleanup

`backend/scripts/cleanup_v6_verification_subjects.py` is a library without a generic deletion CLI. Separate execution approval is required. It requires the exact run, removed enabling file, stopped process, complete reconciled journals, both genuine verified tokens, and a fresh target/account/map preflight. It targets only the two manifested Auth IDs, globally logs out each, uses an exclusive per-subject attempt marker, deletes that exact subject and checks absence. An uncertain deletion stops rather than automatically retrying.

It never deletes broad table sets or modifies migrations/grants. Auth cascades are not a complete cleanup proof: the approved run must independently audit all manifested descendants, retained evidence, residual sessions/JWT expiry and orphaned test records. Provider-specific cleanup behavior remains a hosted execution gate. No hosted accounts were created or removed in this task.

## Local verification and execution gate

The new adapter tests cover target mismatch, production-target denial, real locally signed JWT verification, unlisted identities, owner-map drift before replay, foreign owner arguments and IDs, stale/conflicting requests, restricted transport, kill switch, private-data redaction, cleanup custody and restart reconciliation. Together with the activity tests, **49 targeted tests pass**; the final full backend run passes **2,940 tests**. These are local cryptographic and transport tests, not a GoTrue execution claim.

An independent process comparison proves unchanged normal startup: identical 73-path OpenAPI hash, no verification import, no dependency overrides, historical planning repository and both V2 controls false. See [verification register](blocker-resolution-20261117/verification.json) and [startup proof](blocker-resolution-20261117/startup-public-contract.json).

Before real execution: obtain an independently identified isolated target, explicit owner approval for its cost/configuration and exactly two synthetic accounts; install the reviewed candidate through a separately approved process; verify target bindings and actual owner map; protect credential/journal files; independently control process/enabling file; and run the existing [hosted post-migration plan](JOREN_V6_HOSTED_POST_MIGRATION_VERIFICATION_PLAN.md), including genuine GoTrue sign-in/refresh, two-account isolation, stale/retry/private-data checks and audited cleanup. A fresh schema-only target does not establish production recovery. Production credentials and athlete data must not be used for this synthetic adapter run.
