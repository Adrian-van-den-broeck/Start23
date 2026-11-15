# WOMBO V6 hosted post-migration verification plan

16 November 2026, Europe/Amsterdam. **PLANNED, NOT EXECUTED. Zero new hosted V6 lifecycle passes claimed.**

Prerequisites: separately approved/applied migrations and compatibility/ACL decision; an official isolated hosted Supabase target; proven recovery checkpoint; exact backend/mobile artifacts; and the separately reviewed adapter described below. Database installation alone does not connect V6 to startup or authorize real athletes. No disposable fixture or portable SQL runner may target hosted production.

## Exact run identity and custody

Create a unique run ID and an ACL-protected ignored private directory. Record project ref, endpoint, complete 63-version/hash inventory, API/deployment SHA, source manifest and start time. Use **exactly two synthetic accounts A/B**, labelled by the run. Supported Auth administrative creation with `.invalid` addresses may avoid mail if separately approved; password login/refresh must still obtain genuine GoTrue tokens. Do not manually sign tokens or invent auth claims. Manifest both real Auth subjects and their separately resolved opaque athlete IDs; never infer equality.

Keep credentials only in the private directory/memory using owner/SYSTEM ACLs. Journal each mutation's owner, method, exact body hash, idempotency key, expected revision and resulting IDs **before dispatch**. No raw private-load/health payloads in public evidence, application logs or analytics. A lost response stops for same-key read reconciliation; never blindly recreate or switch keys. Retain unsanitized evidence only under approved restricted retention.

Existing `verify_v6_hosted_accounts`, `verify_v6_hosted_lifecycle` and `verify_v6_hosted_inventory` provide genuine-session/historical journal patterns. The current lifecycle runner deliberately uses the historical planner and is **not** an available V6 verifier. `verify_v6_postgres`, `install_local_v6`, fixture SQL, simulated verifier and TEST_ONLY frequency paths remain local-only.

## Separately proposed hosted verification adapter — no implementation authorization implied

The current `app/local_v6.py` requires `environment=test` and a loopback Supabase hostname. A hosted URL correctly fails that guard. **Do not change the hostname, lie about the environment, tunnel the target into a loopback alias, monkeypatch dependencies, or pass synthetic frequency controls to evade it.** A new narrow adapter is required before the full hosted V6 test can run.

Proposed security architecture for separate code/security review:

- A distinct verification-only application factory/process, absent from normal production startup/import paths and deployment configuration. No athlete-facing planner toggle, generic “enable V6” environment switch or mobile flag. It must not modify `install_local_v6` or relax its guard.
- Pin the approved isolated target's exact project ref, issuer/JWKS/audience and HTTPS hostname; reject production target unless a new explicit scope specifically authorizes those two manifested synthetic accounts there. Establish the target by metadata, not DNS aliasing. Disable provider/LLM/analytics integrations for the verification service.
- Reuse the unchanged real JWT verifier, identity-map lookup, typed API routes, services, immutable source repository and deterministic V6 domain. Authenticate every request first, then require the token subject and resolved opaque identity to match A or B in the signed/owner-held manifest. Client `user_id`/athlete hints never authorize access. Fail closed on mapping drift or unmanifested identity.
- Construct only the accepted inactive catalog/repository dependencies for this process. All 77 database sources stay INACTIVE. Keep the production app's historical dependency untouched. Server-side service credentials remain in protected process configuration; no token/client gets service-role authority. Public reads/approval use genuine caller tokens; narrow service RPCs receive only the verified mapped owner.
- Do not use `allow_test_frequency_controls=True`, TEST_ONLY SQL exceptions, privileged role membership, synthetic reviewer registrations or REAL maxima. Let the accepted policy resolve the existing safe default and denial cases from genuine database evidence. Positive real multi-session remains a separate gate.
- Enforce a fixed request/RPC allowlist, run/owner/locator scopes and original request/node/time limits. Redact credentials/private evidence at every logging/error boundary. Reject foreign/stale IDs before privileged writes and retain immutable operation receipts. An uncertain mutation stops the harness.
- Provide an independent kill switch that stops only this verifier process and prevents new V6 writes, with the approved expanded forward-disable procedure available if needed. Cleanup accepts only the two manifested synthetic Auth IDs and exact descendants. No arbitrary SQL endpoint, project creation/resume/restore, migration apply/repair, role management or broad deletion capability.

Required adapter tests: an unlisted genuine user denied; forged/expired/issuer/audience-invalid credentials denied; A/B both directions; target mismatch and mapping drift denied; no default production dependency change; no client EXECUTE elevation; secret/private-load redaction; same-key reconciliation; safe frequency default; and exact cleanup. Review and approve its source SHA before the following lifecycle. This task only proposes the design.

## Ordered test cases and required outcomes

Run each owner-local flow for A and B; run every foreign attack in **both directions**. Record per-case status, exact safe response identity, pre/post state fingerprints and gate status. “RPC absent” is BLOCKED, not a passed authorization denial.

| ID | Action | Required assertion |
| --- | --- | --- |
| H00 | Read-only target/ledger/config/advisor preflight | Exact approved target/63 files, approved ACL disposition, 77 INACTIVE; no reviewer/decision or frequency-role membership; historical default unchanged |
| H01 | Genuine password login, `/user`, backend identity, refresh A/B | Actual GoTrue session pairs and verified signatures; distinct token subjects and opaque IDs; refreshed identity stable; no synthetic JWT |
| H02 | Normal synthetic onboarding and zones | Existing public flow and separate confirmations; no direct SQL fixture or fabricated eligibility/completion |
| H03 | Frequency preference GET/save/CAS/retry | Null/default, explicit zero, optional wish above safe default persist by owner; exact operation retry equals first receipt; stale revision conflicts; foreign preference/operation cannot be adopted |
| H04 | No genuine reviewer/maxima | Reviewer registry and authority decisions stay empty; ordinary/service athlete path cannot register REAL authority; requested extra sessions grant no authority; default remains accepted one-per-sport boundary |
| H05 | V6 automatic proposal generation | Actual accepted source/phase/method, target/context/evidence custody; pending only; generation does not activate calendar or change historical users; honest `v6_search_incomplete` when bounded search is exhausted |
| H06 | A5 confirmed context → proposal attachment | One check-in → one authoritative revision/proposal, correct owner/week/context fingerprint; retry after completed check-in returns exact stored snapshot without regeneration |
| H07 | A5 acknowledgement loss / terminal replay | Suppress only the harness acknowledgement after real hosted commit; retry original key/locator recovers exact IDs; separate rejected/applied replay preserves terminal state; no replacement proposal or retry loop |
| H08 | Swipe alternatives and accepts/passes | Valid alternatives match frozen restrictions/source; duplicate template occurrences remain distinct; stale/foreign edits rejected; no implicit plan apply |
| H09 | Pending submission / submit replay | Exact draft CAS and immutable submit receipt; interrupted/duplicate submit converges to one pending proposal; active week remains unchanged |
| H10 | Separate athlete confirmation | Correct owner/base/evidence/authority activates only after explicit approval; foreign/stale/changed preference/context rejects without partial state; already-applied retry returns same result |
| H11 | Calendar + source prescription | Logical occurrence ID and physical_workout_id mapping correct; source instructions/segment order/dates and method version unchanged; only active approved plan drives calendar |
| H12 | Real supported synthetic activity | Link exact physical FK; record average HR/zone data through supported public flow and RPE separately; same idempotency key recovers original activity; foreign occurrence denied; no private planned/realized evidence returned |
| H13 | Registration | Read unknown, explicit skipped/unknown CAS/retry where supported; missing is not skipped; activity-vs-registration contention yields an allowed single winner; foreign/stale registration denied |
| H14 | Move unfinished sibling after one/multiple completions | Completed siblings keep original physical activity FK, date/source/prescription/metrics/private evidence. Append-only membership includes each exactly once; only permitted unfinished target changes |
| H15 | Bounded move/confirm/edit concurrency | Two moves, same-key duplicates, move-vs-activity/registration and move-vs-pending-confirmation have one authoritative permitted result, no last-write-wins or evidence loss. Small authorized synthetic concurrency only |
| H16 | Logout/login + verifier restart | Logout revokes refresh/session per observed provider contract; fresh login of same accounts restores own persisted plan/draft/receipts; independent verifier process/new connections return exact same state; account switch never adopts foreign locators |
| H17 | Credential negatives / actual expiry | Missing/tampered/API-key-only denied. Do not assert immediate universal JWT revocation: prior hosted Data API accepted signed access until expiry. If repeated, wait for genuine expiry without clock/lifetime changes |
| H18 | Foreign/stale IDs across all surfaces | A→B and B→A: check-in, plan/proposal/revision, draft/receipt/key, logical/physical workout, activity, registration, preference and private frequency/evidence. Owner-safe 404/409 or RLS-empty as contract defines; victim state identical |
| H19 | Recursive confidentiality | Inspect every successful/error DTO, nested arrays, mobile state/log/accessibility output for forbidden private-load/TSS/evidence/method payloads. Direct private schema denied, service generated-write RPCs denied to genuine athlete credentials; no raw internal error detail |
| H20 | Historical coexistence | A separately approved synthetic historical proposal remains historical; existing historical onboarding/A3–A9/A5/A6 workflows pass with unchanged source/value snapshots and public error semantics. No real athlete reads/writes |
| H21 | Source/authority postflight | Still 77 INACTIVE; zero unexpected historical-load joins, reviewer enrollments, REAL authorizations or test/registrar memberships; ledger/schema/Auth config equals approved post-install boundary |
| H22 | Exact cleanup and clean restart | Supported logout + Auth deletion for only manifested A/B, owner-scoped descendant audit zero; original synthetic tokens/refresh unusable as contract permits; no generic DELETE/reset fixture |

Frequency interruption/reconfirmation cases may suspend a preexisting authority only if a genuine designated reviewer/operator has separately issued an individually reviewed athlete/sport/week/timezone maximum. Without that evidence, test safe-default preferences, interruption persistence and denied issuance; mark positive multisession tests **BLOCKED — NO GENUINE AUTHORIZATION**. Do not fabricate authority to improve coverage.

## Cleanup protocol

1. Before cleanup inventory only exact manifested A/B descendants and operation IDs, capturing counts and source/catalog fingerprints. Include auth subjects, opaque map, profile/physiology/history/goal/zone/calibration/onboarding requests and sessions, check-in/context, plan/revision/proposal/workout/warning/load, drafts/receipts, activities/metrics/files/provider rows, V2 evidence/registration, V6 snapshots/memberships/edit receipts, frequency preferences/decisions/draft contexts and any storage object keys actually created.
2. Stop the verifier; logout/revoke the two exact sessions through supported Auth routes. Keep uncertainty journal until known writes are reconciled. Never enumerate or delete other Auth users.
3. Supported administrative deletion targets only the two exact manifested subjects. Verify both admin GETs are 404 and inspect their opaque identities/descendants through fixed owner-filtered read-only queries. Never rely solely on successful Auth deletion or guessed cascades. Global immutable source revisions remain; catalog rows are never cleanup targets.
4. If a retained descendant exists, STOP and report its exact run-owned table/ID relationship for a separately reviewed narrow correction. No broad cleanup, constraint disabling or synthetic-ID pattern delete.
5. Compare target schema/ledger/Auth configuration, historical source manifest and membership/authority invariants before/after; publish only sanitized case outcomes/counts/hashes. Protect then expire private credentials/health evidence under approved retention. No completion claim if cleanup is uncertain.

## Acceptance boundary

Full hosted integration passes only when H00–H22 have individual evidence, unchanged historical contracts, exact cleanup and no unapproved grants/default activation. Positive multisession, scientific accountability, performance on approved target contexts and actual Android/iOS device evidence remain independent. Portable local claims/simulated sessions do not satisfy them.
