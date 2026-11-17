# WOMBO Internal Testing database compatibility

2026-11-04. Exact cumulative base `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`. **Backend NO-GO.** PostgreSQL/pgTAP is **DEFERRED BY OWNER — PRE-BETA**, not successful verification. No SQL, migration, database RPC, athlete query or hosted mutation ran in this audit.

## Observed configuration and schema evidence

EAS production points at `https://start23-production.up.railway.app`, Supabase `isfumhgqphieoayqahjv.supabase.co`. The existing local server credential points to the same Supabase host. One authenticated **GET of Data API OpenAPI schema metadata only** returned HTTP 200. This is the linked project historically named start23-dev; a name is not proof that it is separate from the database used by current internal testers. No new database or service was created.

| RPC | Advertised by the inspected hosted Data API schema |
| --- | --- |
| `get_weekly_checkin`, `get_weekly_plan`, `create_activity_summary`, `get_activity`, `list_activities` | Yes |
| `get_plan_load_history_for_planning_v15` | Yes |
| `create_weekly_plan_proposal_v3`, `attach_checkin_plan_proposal` | Yes |
| `get_checkin_plan_proposal` | **No** |
| `get_plan_load_history_for_planning_v16`, `create_weekly_plan_proposal_v4` | **No** |
| `get_activity_processing_context_v2`, `create_activity_summary_v2`, `complete_activity_rpe_v2` | **No** |
| `get_workout_registration`, `confirm_workout_registration` | **No** |

Visibility depends on the inspected role/schema cache. “Not advertised” is not proof of an absent SQL object or an applied migration ledger. Even advertised RPCs are not proven compiled, authorized for real users, or transactionally correct by this GET. No grant was altered to improve visibility. The deployed backend SHA and migration ledger remain unknown.

The public backend `/ready` returned `environment=local`. In candidate `app/core/config.py`, environment defaults to local; production must explicitly set `START23_ENVIRONMENT=production`. There is no automatic inference from `RAILWAY_ENVIRONMENT_NAME`. Production review/key/Polar/V2 checks exist, but are conditional on this explicit setting. `modules/health/service.py` returns configured status/version/environment without dependency checks. Neither `/health` nor `/ready` proves deployed revision, schema parity or eligibility for production.

## Required versus optional migrations

The accepted UI integration through `aff74558...` already requires its historical migration chain, including identity/privacy cutover, source catalog and approved first-plan provenance. Do not presume those applied records from source history alone. Compare the hosted ledger and contracts before a backend rollout. The only new migration between that UI baseline and A9 is A5; the subsequent four belong to Realized V2. C1/C2/C2.1 add **no database migrations**.

| Migration | Required by the current off-gated candidate? | Reason / decision |
| --- | --- | --- |
| `20261026224844_wombo_a5_checkin_proposal_recovery.sql` | **Yes**, for its enabled A5 backend behavior. | Adds `get_checkin_plan_proposal` and atomically changes v3 creation/attachment. `CheckInService.generate_plan_proposal` calls the new read before the existing planning path. V2 flags do not protect it. Hosted verification is missing; do not deploy. |
| `20261103134520_joren_realized_tss_v2_private_provenance.sql` | **No**, while storage and selection remain false and no V2 history must be read/corrected. | Private append-only inputs/calculations and V2 create/context/completion RPCs. Required before any future V2 storage/selection. Unverified. |
| `20261103135735_realized_v2_weekly_registration.sql` | **No**, with storage false and mobile registration hard-gated. | Private registration events, registration RPCs, guards and v16 history. Unverified. |
| `20261103140959_realized_v2_planning_evidence_preconditions.sql` | **No**, with storage false. | v4 proposal/evidence persistence and stale approval guards. Unverified. |
| `20261103142339_realized_v2_session_rpe_guidance.sql` | **No**, with all V2 activity paths inactive. | Versioned public qualitative RPE guidance projection. Unverified. |

Do not apply all pending migrations “for safety.” The four V2 migrations are forward-only activation dependencies, not prerequisites for shipping UI assets. A5 is a separate blocker even when all V2 features are disabled. Static SQL/pglast parsing and mocked tests do not close PostgreSQL compilation, forced RLS/grants, owner separation, numeric round-trip, concurrent retries, account deletion or stale activation gates.

## Runtime dispatch and failure behavior

* Settings default both Realized V2 flags to false. Selection without storage raises a configuration error. Storage true in staging/production is rejected while release gates are open. Local/test activation remains possible for software tests; this is why the observed hosted local environment is a material concern.
* `SupabasePlanningRepository` selects v15 history and v3 proposal creation with storage false; it neither requests v16 nor attaches V2 evidence. Storage true switches to v16/v4.
* `SupabaseActivityRepository` uses legacy create/context when selection/storage are off. Registration GET/PUT refuse before any database request when storage is false; a MockTransport probe verified zero outbound calls. Safe failure is an unavailable error, not success or skipped state.
* V2 correction dispatch also depends on stored original provenance. After a future activation, merely setting selection false cannot guarantee removal of all V2 database dependencies. Preserve those historical objects/readers; never reinterpret old records under legacy rules.
* A5 recovery is unconditional on its enabled check-in proposal path. Missing its function causes an error; it does not safely recover by regenerating the plan. Do not bypass that behavior.

## Mobile/backend and older-client compatibility

Live backend OpenAPI was retrieved with public GET only. Candidate-only operations are `GET /api/v1/weekly-plans/recovery` and registration GET/PUT. No existing path disappeared. Activity input adds `performed_duration_confirmed`; current hosted `ActivitySummaryInput.additionalProperties=false`. Original C2.1 mobile sends that field and would be rejected by the observed contract. The preparation overlay omits it in both the shared builder and transport, blocks registration before network and hides its controls. New optional activity guidance/version fields are handled compatibly with older responses.

**Mobile-only remains NO-GO:** A6 calls the unavailable recovery route at startup/foreground reconciliation. It is not safe to call unknown state empty, discard owner-scoped state, or create duplicate plans. A smaller reviewed compatibility scope is needed; none is asserted to pass hosted flows here.

Candidate backend continues to accept old activity requests without confirmation, keeps existing API routes and private method/version dispatch, and adds no required fields to common public response schemas in the inspected comparison. This supports a design expectation of old-client compatibility, not a verified statement about the unidentified currently distributed app. Test build 22 and the actual installed build against both backend revisions before approval, including activity retries and current-week RPE correction. The older backend and proposed new mobile are **not currently compatible as a complete workflow** because of A6.

## Migration execution and recovery boundaries

`backend/Dockerfile` installs the Python package and starts Uvicorn; `backend/railway.toml` defines `/ready` health checking with no predeploy migration command. Application startup does not invoke migrations. Hosted Railway dashboard overrides are unknown.

Backend dependencies use version ranges in `pyproject.toml`, and the Dockerfile upgrades pip/installs from those ranges. The tests reused the existing Python 3.10.10 virtual environment; a clean production Docker rebuild was not performed. Exact deployed package parity is therefore unverified in addition to the database blockers.

**Dangerous local deployment path:** `scripts/start-start23-backend.ps1` in production mode executes `supabase db push --linked --yes` before `railway up`. The existing local mode state says production. The “Start backend” VS Code task is therefore not a read-only check and could apply A5 and all four deferred V2 migrations. It was not run. The mobile build helper also synchronizes EAS public variables; that helper was not run.

Backend rollback should restore a recorded prior deployment artifact and its verified configuration, leaving schema/history intact. Do not drop new tables, undo applied forward migrations, reset production data or recalculate history. Because neither prior revision nor applied ledger is established, rollback readiness is itself open. If V2 is activated in future, retain its storage and version-aware readers/correction paths even when new selection is disabled.

Required next evidence, under separate approval: exact hosted deployment/config and migration ledger; compiled fresh/upgrade PostgreSQL and grants/RLS tests when owner lifts deferral; A5 atomic replay/concurrency and two-token checks; old/new app compatibility; explicit production governance records. No release gate was bypassed to get green local tests.
