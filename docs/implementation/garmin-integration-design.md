# Garmin integration design for the Start23/Wombo MVP

Status: architecture and implementation plan only, 2026-09-26. No runtime code,
migration, provider account, or production setting is changed by this document.
Repository basis: local `main` at `8fe4f44`, after `git fetch origin main` (fetched
`origin/main` at `3f35146`). The checkout is two local commits ahead and has an
unrelated existing edit to `backend/app/modules/coach/weekly_plan.py`; this
design does not alter that edit. Root and mobile `AGENTS.md` and the current
[`mvp-roadmap.md`](mvp-roadmap.md) govern the proposal. The Garmin-first product
direction in this task supersedes the roadmap's historical Polar-first choice;
the implemented Polar integration remains historical/conditional, not a Garmin
contract.

## 1. Current repository integration points

| Area | Current behavior | G1 implication |
| --- | --- | --- |
| Activity | `backend/app/modules/activities/{schemas,service,repository,router}.py` and `public.activities` / `public.activity_metrics` accept a validated canonical summary for swim, bike, or run. `source` remains `canonical_summary`. Required: discipline, aware start instant, confirmed IANA athlete timezone, and positive duration except a distance-only swim. Optional distance, swim-free elevation, average/max HR, bike power/speed, run/swim pace, and validated zone or low/high minutes. | Map Garmin to `ActivitySummaryInput` first. Keep `public.activities` and its public DTO unchanged. A provider ID belongs in private provenance, not the Activity API. |
| Feedback/load | An import starts `awaiting_rpe`. `ActivityService.submit_rpe` and its private processing-context/completion RPCs perform the Phase 13 versioned realized-load calculation, qualitative result, correction proposal, and audit. `GET /activities/pending-rpe` plus `mobile/src/screens/ActivityScreen.tsx` provide the existing prompt. Phase 8 permits stale-safe RPE correction in the current athlete-local week. | Import must never write `private.activity_loads` itself, guess RPE, or bypass the existing RPE endpoint. Missing HR remains missing; where the existing feedback contract requires HR, the athlete supplies it there. Historical calculation provenance remains unchanged. |
| Provider code | `backend/app/modules/integrations/{polar,domain,service,repository,router,schemas}.py` implements Polar-specific OAuth, verified notification intake, canonical mapping, import retries, and a scheduled retry job in the monolith. | Keep Polar-specific parsing, signatures, URL rules, registration, 30-day limit, and FIT behavior isolated. Extract only provider-neutral orchestration/typed boundaries when implementing Garmin. No Garmin field or endpoint may be copied from Polar. |
| Provider persistence | Phase 9 has `public.provider_connections`, `public.import_runs`, `private.provider_tokens`, `private.integration_oauth_states`, `private.webhook_receipts`, `private.provider_activity_imports`, and `public.activity_files`. Existing checks/RPCs largely allow **Polar only**; `provider_user_id` is currently in an athlete-readable public connection row and tokens are stored as text in a private table. | Use forward-only expansion, preserve Polar rows and RPCs, keep Garmin external identity and encrypted token material backend-private, and do not use `activity_files` for G1. |
| Identity/security | FastAPI verifies Supabase JWTs, then resolves an opaque athlete UUID through `get_current_athlete_id`. The R3 database cutover retains legacy Auth UUID owner columns plus `internal_athlete_id` and restrictive owner checks. Service RPCs adapt opaque to legacy only at the boundary. `private.activity_loads` has no athlete grant. Account deletion cascade hardening exists in R6. | Bind OAuth state to the resolved opaque identity and its matching Auth subject. For new rows use both owner keys only as the current R3 compatibility model requires. No client `user_id`; force RLS and explicit grants on any public data. |
| Plans/workouts | `public.weekly_plans.active_revision`, `public.plan_revisions.state`, and immutable `public.planned_workouts` snapshots define the approved schedule. A workout has discipline, scheduled local date, status, template version, total duration or distance, ordered JSON segments, and one of zone/protocol/RPE targets. Pending/rejected/superseded revisions coexist. See `planning/schemas.py`, `workouts/{catalog,schemas}.py`. | G2 reads only the active revision of an active plan and eligible future `scheduled` workout. `planned_workout_id` or a time-near suggestion is never an automatic import match. |
| Existing idempotency | Manual Activity creation uses `(athlete_id, idempotency_key)` plus SHA-256 canonical-request fingerprint; same request replays, changed payload conflicts. Polar imports use a deterministic provider-ID-derived UUID, `(provider, provider_entity_id)` provenance, atomic import RPC, unique notification receipts, and bounded retries. Plan revisions use generation fingerprints and revision preconditions. | Retain exact provider identity uniqueness and activity create semantics. Add a conservative manual/import review state; never conflate an event receipt, provider entity, and canonical Activity. |

The Phase 0 decision chose canonical summary before files. The Phase 9 Polar
implementation later added optional permanent FIT storage, but that is a
provider-specific decision with unresolved formal retention. The current
[`phase-8-taper-catalog-review.md`](phase-8-taper-catalog-review.md) and Phase 11
catalog preserve all 54 source swims as **distance-driven**, with no inferred
planned duration. The open automatic-workout-catalog review concerns selection
eligibility; G1 imports completed sessions independently of it.

## 2. Official Garmin capability boundary

Garmin's [Connect Developer Program overview](https://developer.garmin.com/gc-developer-program/overview/)
calls these cloud-to-cloud APIs. The [Activity API](https://developer.garmin.com/gc-developer-program/activity-api/)
lists running, cycling, and swimming; offers REST, ping/pull or push integration,
customized feeds, developer backfill tools, and detailed FIT/GPX/TCX activity
files after the athlete consents and syncs to Garmin Connect. The
[Training API](https://developer.garmin.com/gc-developer-program/training-api/)
publishes structured workouts and plans to the Garmin Connect calendar for
compatible devices to sync. The [program FAQ](https://developer.garmin.com/gc-developer-program/program-faq/)
states that the Developer Program APIs use OAuth 2.0 and that portal access
follows program approval. These public pages do **not** establish endpoint
paths, exact payload fields, callback authentication, OAuth scopes, token
refresh/lifetime, activity identifiers, backfill limits, Training API mutation
semantics, or rate limits. Every such item below is **GARMIN PORTAL
DOCUMENTATION REQUIRED**. Garmin Health API all-day metrics are outside G1/G2.
Neither Connect IQ nor a device SDK is required by the present cloud use cases.

## 3. G1: account link and completed-activity import

1. An authenticated athlete starts “Garmin koppelen” from Profile → Connections.
   FastAPI creates a one-time, short-lived, high-entropy OAuth state bound to
   the verified opaque athlete identity and connection generation, then returns
   an authorization URL for the system browser. The backend receives Garmin's
   callback over allowlisted HTTPS, consumes state atomically, exchanges the
   authorization result server-side, obtains the stable Garmin account identity
   by the documented method, and saves the connection and encrypted credentials
   atomically. **GARMIN PORTAL DOCUMENTATION REQUIRED** for the exact flow,
   identity source, redirect rules, PKCE requirement, and consent permissions.
2. A Garmin adapter authenticates provider delivery using the portal's actual
   mechanism. Choose **ping/pull** if the approved Activity API contract offers
   authenticated notifications plus bounded activity fetch and backfill; it
   minimizes incoming health data. If only push meets the approved contract,
   validate and minimize its payload before persistence. No assumed webhook
   signature or Garmin-controlled fetch URL is trusted. Persist a receipt/work
   claim before acknowledging delivery; then process in the FastAPI monolith.
3. The adapter converts one verified Garmin activity to a typed provider-neutral
   candidate, then `ActivitySummaryInput`. A service-only atomic import
   transaction checks the owner/connection generation, claims the global Garmin
   activity ID, checks manual candidates, and either creates the existing
   canonical Activity plus optional metric row, links an existing manual
   Activity after athlete confirmation, or leaves a private review/failure
   state. `public.activities.source` remains `canonical_summary`; imported
   provenance is a separate private row. This transaction must reuse the
   canonical validation, ownership, idempotency, and R6 preflight guarantees
   rather than copy Polar's SQL blindly. The existing Activity/RPE service is
   the sole route to private realized load.
4. On success the existing activity list and pending-RPE prompt refresh.
   Garmin consent/link completion itself never implies a completed Start23
   feedback record.

### Canonical field mapping and absence policy

The public Garmin page confirms access to detailed activity data, but does not
name summary JSON/FIT fields. The source column here describes evidence the
adapter must prove from the approved contract or a portal fixture, **not** a
claimed Garmin field name.

| Start23 value | Required mapping rule | If absent or unclear |
| --- | --- | --- |
| Private `(provider, provider_entity_id)` | Stable Garmin activity identifier, scoped and checked against the verified Garmin account. **GARMIN PORTAL DOCUMENTATION REQUIRED.** | Hold; no import without an authoritative ID. Never use a timestamp as the provider ID. |
| `discipline` | Explicit reviewed Garmin sport/type mapping to exactly `run`, `bike`, or `swim`. **GARMIN PORTAL DOCUMENTATION REQUIRED** for type vocabulary and multisport handling. | Mark unsupported; no guessed substring or multisport split. |
| `started_at` | Aware absolute instant from documented source time; preserve the instant. **GARMIN PORTAL DOCUMENTATION REQUIRED** for time/offset representation. | Hold for user completion; never attach UTC or an offset to a naive local time by guess. |
| `timezone`, athlete-local date | Use the *confirmed Start23 profile IANA timezone*, enforced by the R4/R5 Activity trigger; derive local date/week from the instant in that timezone. | Hold if profile timezone is unconfirmed. A Garmin/device timezone must not silently replace the confirmed Start23 timezone; travel behavior needs a separate product decision. |
| `duration_minutes` | Proposed source is an authoritative measured **elapsed** duration if the approved Garmin summary supplies it, converting units exactly. Moving duration is only transient comparison data, not a second canonical field. **GARMIN PORTAL DOCUMENTATION REQUIRED** for availability/units. | Do not substitute moving time or infer from distance. Run/bike cannot be inserted without duration; hold for the existing manual completion/create flow. Swim may be distance-only under the current contract. Confirm elapsed-versus-moving against Start23's “actual duration” meaning before enabling import; otherwise hold the candidate. |
| `distance_meters` | Convert documented distance units without invented precision. Required only for duration-free swim. | Omit when optional; hold a duration-free swim without distance. |
| `metrics.average_heart_rate_bpm` | Use a documented activity mean HR, if present and valid under current Pydantic limits. | Omit. Do not estimate from samples or RPE. Existing feedback may ask the athlete for HR where its current contract requires it. |
| Other existing optional canonical metrics | Max HR, bike normalized power/speed, run/swim pace, elevation, and zone/low/high minutes only when their source meaning and units match the existing contracts. For zone minutes, Garmin time buckets may not be Start23's confirmed zone boundaries. | Omit any unproven metric. G1 does not need these for a useful summary; do not calculate zones or change private-load rules in the adapter. |
| `rpe`, planned match | Garmin data provides no authoritative Start23 athlete-selected textual RPE or plan approval. | Always leave RPE missing and `planned_workout_id` empty on initial import. Use the existing prompt and explicit planned-workout match confirmation. |

The adapter must reject malformed required data before a public Activity write.
Optional bad values are omitted only if the entire provider record remains
trustworthy and this does not conceal a contradiction (for example mean HR
greater than max HR); otherwise quarantine the record for review. Store no
provider payload in athlete-facing errors.

### FIT/raw file decision for G1

G1 does **not** download, parse, or permanently store FIT/GPX/TCX when the
approved Activity API summary suffices for the table above. In particular,
raw heart-rate samples are not required to invent zone minutes: the current
Phase 13 path already handles a documented mean-HR observation when allowed.
The existing Polar `activity-files` bucket and `activity_files` table remain
Polar behavior; G1 adds no Garmin object. If portal evidence proves summary
data cannot supply required ID, sport, aware start, or duration/distance, a
separate reviewed FIT slice must define an untrusted-file parser boundary,
bounded size/CPU, exact field provenance, temporary encrypted processing and
deletion, no default permanent retention, failure quarantine, privacy notice,
and fixture/fuzz tests before it is authorized. **GARMIN PORTAL DOCUMENTATION
REQUIRED** for whether this branch is necessary.

## 4. Import, idempotency, and synchronization

| Case | Deterministic treatment |
| --- | --- |
| Same Garmin activity again via notification, retry, backfill, or reconnect | Unique `(provider, provider_entity_id)` claim and deterministic provider-ID-derived Activity idempotency key return the existing mapping. Never create a second Activity or private load. Different normalized content for an already claimed ID is a conflict/quarantine, not a silent rewrite of historical data. |
| Duplicate delivery | Unique authenticated receipt key (portal event ID if guaranteed; otherwise canonical authenticated payload fingerprint) suppresses identical delivery. Entity uniqueness remains the final guard when two distinct deliveries describe one activity. Receipt success is recorded only after durable import/review state. |
| Manual Activity exists before import | Query the owner for **unprovenanced manually entered** activities of the same discipline and confirmed athlete-local date. This deliberately broad candidate rule has no invented time/distance tolerance. Hold the Garmin record for explicit review; show start, duration, distance and current Activity summary. Athlete can link provenance to one owned manual Activity, retaining its RPE, metrics, load version, and plan link unchanged, or affirm that these are separate sessions and import a new Activity. Multiple candidates remain unresolved until selected. |
| Genuinely separate sessions | Distinct provider IDs remain distinct. After explicit “separate” decision, create the Garmin Activity despite same-day manual activity. Do not use a unique date/sport constraint. |
| Manual/import race | Use one owner/local-date/discipline transaction lock in the existing manual-create RPC and new import RPC, then recheck the provider claim and manual candidates. A narrow pre-insert integration guard on the manual side routes an overlapping already-imported Garmin Activity to explicit duplicate review; genuinely separate sessions remain creatable after confirmation. This changes duplicate orchestration, not Activity/RPE/load rules. The G1 concurrency test must prove both lock orders cannot quietly create two realized-load paths for one intended session. If the guard cannot be made stale-safe, hold the Garmin candidate for reconciliation rather than auto-creating it. |
| Planned workout | Existing Phase 9 time-near suggestion may be shown, but only an explicit athlete confirmation can set the planned-workout link; its active-revision and single-match preconditions still apply. A manual/import identity match is a separate decision from a planned-workout match. |

Initial backfill begins only after consent, using the officially documented
window and method (**GARMIN PORTAL DOCUMENTATION REQUIRED**); do not reuse
Polar's 7/14/30-day limit. Persist progress/cursor only if Garmin's contract
defines one. New deliveries use the same import transaction. The existing
bounded monolith retry pattern can retry durable failed work and provider
outages with backoff; a scheduled retry is for queued work, **not** generic
polling of every Garmin account. A portal-supported reconciliation/backfill
operation handles missed delivery and reconnect catch-up. If Garmin offers no
documented way to recover missed activities, automatic completeness is an
explicit G1 release blocker, not an excuse to invent polling. On disconnect,
stop intake/claims for that connection generation. Unsupported sport and
malformed records are isolated per entity; valid peers continue. Partial data
uses the absence rules above. Provider outage leaves durable work retryable;
authorization failure sets `reconnect_required` and stops token use.

## 5. OAuth, security, and privacy lifecycle

- **Owner binding:** Start is authenticated by FastAPI's verified Supabase
  token; the state row records opaque athlete ID, matching Auth UUID, provider,
  connection generation, expiry, and a hash of state. Callback consumes it
  once, checks exact redirect/client configuration, and rejects missing,
  expired, reused, cross-provider, or stale-generation state. No callback
  accepts a client `user_id`. The backend may redirect to an allowlisted app
  deep link carrying only a completion/status marker; mobile re-reads status
  with its own Start23 access token. PKCE is used if required/supported by the
  approved Garmin OAuth contract. **GARMIN PORTAL DOCUMENTATION REQUIRED.**
- **Secrets:** Garmin client secret and encryption keys live only in backend
  secret configuration; Garmin access/refresh material is encrypted before
  private database persistence and decrypted only in the provider adapter.
  No token, Garmin user ID, Supabase secret key, or private load appears in
  Expo config, deep links, public RPC/DTO, analytics, or logs. Record key ID for
  rotation and use an authenticated encryption scheme; keep the encryption
  key outside the database. Token refresh/expiry fields are used only if the
  official contract defines them. **GARMIN PORTAL DOCUMENTATION REQUIRED.**
- **Consent and reassociation:** Request only Activity API permission for G1;
  Training API permission is a later G2 consent/update if needed. The exact
  scope names are **GARMIN PORTAL DOCUMENTATION REQUIRED**. Global private
  identity uniqueness prevents a Garmin account already associated with one
  Start23 athlete from being linked to another. Reconnect of the *same* Garmin
  identity to the *same* opaque athlete rotates credentials/generation and
  keeps imported provenance. A different Garmin identity cannot silently
  replace it; require explicit disconnect and a reviewed transfer/relink flow.
- **Disconnect/revoke:** Stop new sync immediately and invalidate queued work
  by generation, then use Garmin's documented revocation/disconnection method
  if available (**GARMIN PORTAL DOCUMENTATION REQUIRED**). Do not claim remote
  revocation succeeded if it failed; retain only the minimum encrypted
  credential needed for a bounded retry, show `sync issue`, and prohibit new
  import. On confirmed remote revocation/already-revoked response, erase tokens
  and ephemeral state. Existing canonical Activities, RPE, private load, and
  provenance remain for the user's history; disconnect copy must say so.
- **Deletion:** Account erasure removes queued work, state, token material,
  private identity/provenance, and owned Activities via the existing Auth
  cascade, plus any provider-side revoke and external storage/log cleanup
  required by policy. Test the R3 dual-owner and R6 cascade paths. A failed
  remote revoke must not prevent local credential/data erasure; record a safe
  operational retry without retaining erased health data. Exact backup,
  receipt, tombstone, and provider-retention periods require a documented
  privacy decision before rollout. Disconnect keeps a minimal private identity
  binding while retained imported history exists to prevent accidental
  cross-account reassociation; account erasure removes it.

Garmin user identity is sensitive linkage data. Activities, HR and any raw
telemetry are health data. Audit only provider type, opaque owner, connection
generation, operation/status, hash/reference, and timestamps; no raw provider
body, HR, GPS, token, or TSS in general logs. Public status projections must
exclude provider user ID. Preserve forced RLS on public owner rows, restrictive
opaque-owner policy during R3, no `anon` access, and no direct athlete/service
grants to private token/identity/receipt data. New service-only RPCs must
validate both owner keys and connection generation inside the transaction.
Supabase's [RLS guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
separates table grants from row policies; both need review in the migration.

## 6. Minimum proposed persistence (future forward-only migration)

These are proposed **Start23 internal fields**, not Garmin payload claims.
`owner` means the opaque athlete plus current R3 Auth UUID compatibility key;
all records delete with account erasure. “Private” means unexposed `private`
schema with no `anon`/`authenticated` table grant and only narrow guarded
backend RPC access. Exact migrations are a later implementation slice.

| Existing/new structure and field group | Purpose; sensitivity | Owner, access, uniqueness, retention |
| --- | --- | --- |
| Extend `public.provider_connections`: `provider='garmin'`, `id`, dual owner, status, `connected_at`, `disconnected_at`, `last_import_at`, `updated_at`, new `generation`; Garmin `provider_user_id` null. | Public connection *status* and stale-work generation; no external ID or token. | Forced RLS, owner-only safe projection, service-only mutation. Unique `(athlete_id, provider)` already exists. Retain status while account/history exists; erase on account deletion. Preserve existing Polar rows/constraints via provider-specific checks. |
| New `private.provider_external_identities`: `connection_id`, dual owner, `provider`, keyed `external_id_digest`, optional encrypted external ID if a documented Garmin request needs it, first/last verified times. | Stable Garmin account binding; high-sensitivity linkage. | Backend only. Unique `(provider, external_id_digest)` and one identity per connection; same-owner reconnect only. Retain minimal binding while imported history exists, remove on erasure; time-limited disconnected retention needs policy. **GARMIN PORTAL DOCUMENTATION REQUIRED** for identity representation. |
| Extend `private.provider_tokens`: `connection_id`, dual owner, encrypted access material, optional encrypted refresh material, `encryption_key_id`, provider-supplied expiry metadata when available, `updated_at`; preserve Polar legacy fields. | Secret credential. | Backend only; existing unique connection key. Erase on successful disconnect or account deletion; rotate/re-encrypt by key ID. No plaintext Garmin token column. **GARMIN PORTAL DOCUMENTATION REQUIRED** for token types/lifecycle. |
| Extend `private.integration_oauth_states`: existing `state_hash`, dual owner, `provider`, `expires_at`; add `generation`, optional encrypted PKCE verifier and allowlisted return target identifier only if needed. | CSRF/link binding; secret ephemeral verifier. | Backend-only consume; unique state hash and at most one live attempt per owner/provider. Remove on use, expiry, disconnect, erasure. |
| Extend `public.import_runs`: existing `id`, dual owner, connection, idempotency key, status/counts, retry timestamps; provider-specific kind/window fields after portal review. | Operational progress, not raw health data. | Owner-safe DTO only, service writes; existing `(athlete_id, idempotency_key)` unique. Retention decision must preserve linked provenance; Polar's 30-day check remains Polar-only. |
| Extend `private.webhook_receipts`: provider, authenticated event key or payload digest, connection/generation, normalized internal event type, status, timestamps/failure code. | Delivery dedupe and audit; hashes may be linkable. | Backend only; existing unique `(provider, event_key)`. Expire after approved retry/audit period, only when completed and no dependent work. **GARMIN PORTAL DOCUMENTATION REQUIRED** for delivery authentication and event fields. |
| Extend `private.provider_activity_imports`: provider, stable entity ID or keyed digest plus encrypted ID if fetching requires it, dual owner, import ID, nullable Activity ID, status (`pending`, `needs_review`, `imported`, `unsupported`, `malformed`), optional manual candidate ID/version, minimal normalized canonical candidate while unresolved, payload fingerprint, timestamps. | Provider provenance, retry state, and temporary health data. | Existing global `(provider, provider_entity_id)` claim (or equivalent keyed unique digest) prevents cross-owner reuse. Backend-only; owner-safe review DTO via FastAPI. Unique mapping to a chosen Activity as required; retain imported provenance with the Activity, purge unresolved candidate summary after decision/approved timeout, erase on account deletion. Preserve Polar completed rows without rewriting history. |
| **G2 only**, new private workout-export mapping: connection/owner/generation, planned workout ID, plan revision ID and number, immutable payload fingerprint, local schedule date, remote reference if returned, send/update/cancel state, attempt timestamps. | Export provenance and remote lifecycle; may expose training schedule. | Backend only; unique `(connection, planned_workout_id, revision_id)` and an active remote mapping uniqueness rule; retain for audit per approved policy, erase on account deletion. **GARMIN PORTAL DOCUMENTATION REQUIRED** for remote identity/idempotency/update capabilities. |

No new public Activity field, private load table, permanent raw-file object, or
generic polling table is required. If the portal documents a provider cursor or
outbox acknowledgement, add only that provider-private state after review.

Field-level access/retention detail for the **new or changed** fields (existing
unchanged fields retain their present constraints):

| Field(s) | Purpose and sensitivity | Owner/schema, access and retention/constraint |
| --- | --- | --- |
| `provider_connections.generation` | Revokes stale callbacks/work; operational. | Dual owner, `public`; safe owner status projection only; monotone per connection, retained with connection, erased with account. |
| `provider_connections.provider_user_id = null` for Garmin | Avoid a readable external identifier; sensitive identity is elsewhere. | Dual owner, `public`; Garmin-specific null check, preserving Polar's present value/check; existing owner uniqueness remains. |
| `provider_external_identities.connection_id`, `.provider` | One identity per linked connection; linkage sensitive. | Dual owner, `private`, backend-only; unique connection and referential integrity; retained with connection/history, erased with account. |
| `provider_external_identities.external_id_digest` | Deterministic account lookup/reassociation guard; pseudonymous but linkable. | Dual owner, `private`, backend-only; keyed digest with unique `(provider, digest)`; retain while history is retained, erase with account. |
| `provider_external_identities.external_id_ciphertext` (conditional) | Reuse raw external ID only if a documented request needs it; secret linkage. | Dual owner, `private`, backend-only; authenticated encryption, nullable; same identity retention/erasure. |
| `provider_external_identities.first_verified_at`, `.last_verified_at` | Audit link/reconnect; operational linkage. | Dual owner, `private`, backend-only; update only after verified identity; same identity retention/erasure. |
| `provider_tokens.encrypted_access_material`, `.encrypted_refresh_material` (conditional) | Garmin credentials; secret. | Dual owner, `private`, backend-only; one row per connection, no plaintext Garmin token, refresh nullable; erase after disconnect/revoke or account deletion. |
| `provider_tokens.encryption_key_id`, provider expiry metadata (conditional) | Key rotation and documented credential validity; sensitive operational data. | Dual owner, `private`, backend-only; key ID required for encrypted Garmin token, expiry nullable unless documented; erased with token. |
| `integration_oauth_states.generation`, optional encrypted PKCE verifier, return-target identifier | Bind link attempt and callback; PKCE verifier secret. | Dual owner, `private`, backend-only; state hash stays unique and one active attempt per owner/provider; consume once or expire, erase on disconnect/deletion. |
| `import_runs` Garmin kind/window or cursor (conditional) | Backfill/retry progress; operational, possibly linkable. | Dual owner, `public` safe projection, service-only writes; existing owner/idempotency uniqueness; retain while referenced by provenance, then approved policy. No Polar limit copied. |
| `webhook_receipts.connection_id`, `.generation`, normalized event type | Authenticated delivery routing/stale exclusion; linkable metadata. | Dual owner when resolved, `private`, backend-only; unique provider/event key still applies; purge after approved retry/audit window and no dependency. |
| `provider_activity_imports.activity_id` nullable, `.status` | Pending/review/import terminal state; health-data linkage. | Dual owner, `private`, backend-only; one global provider entity claim, owner FK, valid status transition, retained with imported Activity or until unresolved expiry. |
| `provider_activity_imports.candidate_activity_id`, `.candidate_version` | Stale-safe explicit manual link; health-data linkage. | Dual owner, `private`, backend-only; owner-paired Activity FK/version, clear after resolution; no cross-owner candidate. |
| `provider_activity_imports.normalized_candidate`, `.payload_fingerprint` | Minimal temporary canonical values and change detection; health data/hash. | Dual owner, `private`, backend-only; strict typed shape/hash, purge candidate values after resolution/approved timeout, preserve only minimal fingerprint/provenance with Activity. |
| `provider_activity_imports` review/processed timestamps | Audit/retention clock; linkable metadata. | Dual owner, `private`, backend-only; immutable event timestamps where appropriate; erase with account. |
| G2 export connection/generation, workout ID, revision ID/number | Bind export to one approved snapshot; training data. | Dual owner, `private`, backend-only; owner-paired FKs and unique connection/workout/revision, erase with account. |
| G2 export payload fingerprint, local date, remote reference, state, attempts/timestamps | Idempotency, desired remote state and audit; training/schedule data. | Dual owner, `private`, backend-only; unique active remote mapping when supported, bounded retries, approved retention and account erasure. |

## 7. Minimal mobile UX

Place one Garmin entry under Profile → Connections → Garmin with states: not
connected, connecting, connected, sync issue, reconnect required. Connect opens
the system browser consent flow; callback returns a status-only deep link and
the app refreshes backend status. Connected shows the last successful import
time, a brief automatic-import explanation, and Disconnect. Sync issue offers
one safe retry/status refresh; reconnect required offers consent again. No
large integrations dashboard, raw-file UI, TSS, provider ID, or token. The
current `IntegrationsScreen.tsx` is Polar-focused and linked from the week view;
G1 should add the small Garmin route from `ProfileScreen.tsx` without copying
Polar's 7/14/30 selector or claiming its limits. Imported Activities appear in
the existing Activity screen; its current missing-RPE reminder opens the same
textual RPE flow. A likely manual/import match opens a concise explicit
same-session/separate-session decision without editing the original Activity.

## 8. G2 design only: approved Start23 workouts to Garmin

The Training API's published ability is structured workout/plan delivery to
Garmin Connect's calendar, followed by compatible-device sync. The exact
workout schema, target types, step limits, update/delete/query behavior,
idempotency support, remote state, and scheduling semantics are **GARMIN PORTAL
DOCUMENTATION REQUIRED**. No G2 API call or migration belongs in G1.

| Start23 source | Proposed export gate or mapping |
| --- | --- |
| Plan/workout eligibility | In a service-only read immediately before every send, require `weekly_plans.state='active'`, `active_revision` equals the workout's `plan_revisions.revision_number`, revision `state='active'`, workout `status='scheduled'`, future athlete-local scheduled date, same owner, and connected Garmin generation. Pending, draft, rejected, expired and superseded revisions are never exported. |
| Structure | Use immutable workout snapshot discipline, name/instructions, ordered segments, each segment's duration **or** distance, and exactly one zone, protocol or RPE target. Map to Garmin only where the documented Training API expresses the same meaning. **GARMIN PORTAL DOCUMENTATION REQUIRED** for every actual field, zone metric/range, RPE/qualitative target, repeats, technique, and device compatibility. No private planned TSS in payload. |
| Create/send and retry | Create a local fingerprint from approved revision/workout snapshot, schedule date, target/profile version, and connection generation. Persist a pending export claim before network send. At success store remote reference and payload hash. A retry of identical claim returns/reconciles the same mapping. If a timeout leaves remote creation uncertain, query/reconcile by documented remote identity before retry; if impossible, stop automatic retry and surface a sync issue rather than risk duplicate workouts. |
| Reschedule/edit/supersede | Re-evaluate the active revision before each operation. New active revision supersedes old export intent; revoke/update old future remote workout and create/update the new one only with portal-supported semantics. Keep an auditable old/new mapping and deterministic desired state. A rejected proposal produces no new export; an existing active export stays until its plan actually changes. Cancelled/deleted future workout queues a remote removal if supported. If remote removal/update cannot be guaranteed, block automatic G2 export for those structures and surface repair; never treat a failed remote operation as a Start23 plan approval. |
| Garmin-side edits | If Garmin exposes a readable remote state, reconcile it without mutating Start23's approved plan. If not, Start23 remains source of truth and reports only confirmed send state. **GARMIN PORTAL DOCUMENTATION REQUIRED.** |
| Unsupported structure | Mark not exportable with a safe explanation; leave the approved Start23 workout untouched. No silent target conversion, duration invention, or fallback to private TSS. |

**Swim gate:** `workouts/catalog.py`, `planning/schemas.py`, and the source
catalog hold distance-only swim totals and blocks with `duration_minutes=None`.
G2 must prove with portal docs and a compatible-device fixture that the
Training API can represent each required distance step, target, technique and
schedule without inserting time. **GARMIN PORTAL DOCUMENTATION REQUIRED.** If
it cannot, those swims remain Start23-only. The current automatic-catalog
physiology review is independent of G1; for G2 it affects *which* workouts may
enter an active plan, while the export gate itself follows the already
approved/active plan revision and does not promote catalog eligibility.

## 9. Tests and verification gates

**G1 adapter/service:** official portal fixture contract tests for sport, time,
units, missing/contradictory fields, unsupported multisport, missing HR and RPE,
and distance-only swim; OAuth state expiry/replay/owner binding, wrong account,
cross-user access, disconnect/revoke failure and reconnect generation; provider
outage, malformed event, authenticated delivery and duplicate notification;
initial backfill, missed delivery recovery, partial-page retry, and repeat
backfill; same provider entity with changed payload and with a second Start23
owner; manual-before-import match, multiple candidates, separate-session
confirmation, and concurrent manual/import race. Prove imported Activity enters
the existing pending-RPE route and that one RPE submission enters the existing
versioned realized-load path, with no adapter-side load write.

**Database/API/mobile:** pgTAP/RLS two-real-user tests on connection, review
candidate, Activity and private tables; anonymous/direct-write rejection;
one-time OAuth state and global entity uniqueness; account deletion cascade
and no orphaned token/receipt; OpenAPI and recursive TSS/private-load leak
tests across response, error, logs and accessibility labels; strict mypy,
Ruff/format, backend tests, strict TypeScript and targeted navigation/RPE tests.
Use the repository's existing hosted/staging and physical-device gates before
release; no production test connection is implied here.

**G2 later:** only active approved revision exports; pending/rejected proposal
never exports; supersede/reschedule/cancel desired-state transitions; duplicate
send/retry and uncertain timeout; owner/connection isolation; unsupported
structure and distance-only swim; payload redaction and no private TSS.

## 10. Migration and rollout plan

1. Obtain Garmin Connect Developer Program approval and Activity API portal
   reference, terms, branding, consent and retention requirements. Record the
   exact official contract/fixture versions. Resolve the explicit unknowns
   below; revise this design before coding against them.
2. In a later G1 change, create **forward-only** migration(s) expanding Phase 9
   checks/owner policies and adding only the private identity, encrypted-token,
   receipt/review state described above. Do not edit applied migrations or
   rewrite Polar history. Verify grants, forced RLS, opaque-owner compatibility,
   pgTAP and deletion cascades before deploying any adapter.
3. Implement a Garmin provider client and typed mapper against portal fixtures;
   keep FastAPI handlers thin and domain validation shared. Add authenticated
   linking and private credentials, then a single-activity import transaction,
   then authenticated delivery and durable retry/backfill. Verify each slice
   before enabling the next.
4. Add the minimal Profile connection screen, status/deep-link handling and
   existing Activity/RPE handoff. Test with two real accounts in development,
   including same-Garmin-account reassociation refusal and duplicate delivery.
5. Run a small consented beta behind a backend feature gate after provider,
   legal/privacy, retention, observability, hosted RLS, callback, and device
   evidence are accepted. Monitor redacted failed-import counts and retries;
   disable new intake without deleting user history if a provider issue occurs.
6. Treat G2 as a separate approval/design-validation cycle: obtain Training API
   portal docs, verify complete target and swim mapping plus mutation semantics,
   then add the export mapping/outbox and tests. Do not couple G1 to Joren's
   open automatic-workout-catalog eligibility review.

### Exact implementation slices in recommended order (future work)

1. **G1.0 Contract lock:** approved portal fixtures and written decisions for
   identity, OAuth, delivery authentication, field/units/time mapping,
   backfill/recovery, elapsed duration, consent, and retention. No adapter code
   before this gate.
2. **G1.1 Persistence:** forward-only provider checks, private identity and
   encrypted-token layout, state/receipt/claim extensions, owner-safe status
   projection; pgTAP/RLS/cascade tests. Preserve Polar behavior.
3. **G1.2 Link:** typed Garmin client for only OAuth/identity/revoke, state and
   generation binding, server-side encryption, reassociation protection, and
   owner/cross-user tests.
4. **G1.3 One activity:** official fixture mapper, canonical validation,
   provider claim/Activity transaction, deterministic replay, missing-field and
   unsupported-sport tests. No notification dependency for this slice.
5. **G1.4 Duplicate review:** same-day manual candidate hold, explicit
   link/separate actions, shared lock/pre-insert guard, planned-match separation,
   concurrency and stale-version tests.
6. **G1.5 Delivery/recovery:** authenticated ping/pull or push adapter selected
   from portal evidence, durable receipts, initial backfill, catch-up and bounded
   failed-work retry using the existing monolith pattern; outage/reconnect
   tests. No account-wide generic polling.
7. **G1.6 Mobile:** Profile connection route, status-only deep-link return,
   disconnect, duplicate review, Activity refresh and existing textual RPE
   handoff; strict TypeScript/navigation/privacy tests.
8. **G1.7 Hosted beta gate:** two-user real-token RLS, OAuth/webhook/catch-up
   and deletion E2E, privacy/terms approval, device smoke, redacted monitoring,
   then a small consented backend-gated beta. Production remains a separate
   release decision.
9. **G2.0–G2.2 later:** portal Training API/swim contract and consent review;
   private export mapping/outbox plus approved-only reconciliation tests; then
   limited workout export and device verification. No G2 migration in G1.

### Known unknowns that block executable G1/G2 contracts

**GARMIN PORTAL DOCUMENTATION REQUIRED:** OAuth authorization/token/identity
contract, scopes/consent granularity, PKCE/redirect and refresh/revoke rules;
Activity API delivery authentication, event identity/schema, ping/pull or push
selection, stable activity ID, summary fields/units/time semantics, backfill
range/cursor and gap recovery, error/retry/rate limits, data use/attribution and
retention terms. G1 also needs the Start23 elapsed-versus-moving duration
decision confirmed against the actual Garmin fields and a formal health-data
retention/deletion policy. For G2: Training API workout/step/target/swim schema,
calendar schedule format, remote create/update/delete/read and idempotency,
device behavior, and any separate consent. No endpoint, Garmin payload field,
webhook schema, FIT metadata, limit, or token lifetime is inferred here.

## 11. Explicitly out of scope

No code, migration, production operation, historical recalculation, new
physiology or planning rule, automatic plan/zone approval, all-day Garmin
Health metrics, permanent Garmin FIT storage, raw telemetry analytics, GPS
maps, generic polling service, microservice, Celery, Redis, Connect IQ, Garmin
Health SDK, or broad Phase 13–16 reopening. Polar's historical adapter is not
deleted or silently repurposed. G2 export is design-only.

**BLOCKED ON GARMIN PROGRAM DOCUMENTATION**
