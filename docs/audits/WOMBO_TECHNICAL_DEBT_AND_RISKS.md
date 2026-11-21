# WOMBO technical debt and risks

Date: 26 October 2026. Baseline: `aff74558d0a6511286a4a84a44ea25a03ca57549`. The [main audit](WOMBO_FULL_SYSTEM_AUDIT.md) owns the twenty confirmed findings and two explicitly uncertain finding records. This document separates demonstrated design debt from operational/product uncertainties. No remediation was implemented.

## Ownership and integration debt

| Area | Observed design / evidence | Consequence and recommendation |
| --- | --- | --- |
| Parallel plan owners | `CheckInScreen.makeProposal/approve` keeps its own plan, while `TrainingFlowHost` retains `PlanningFlowProvider` | Confirmed 005: establish one authoritative handoff/invalidation path for every task that changes a plan. Do not duplicate planner logic in mobile |
| Local-only discovery | Planning restores two global SecureStore IDs; API exposes get-by-ID but mobile does not discover active/draft plan by athlete/week | Confirmed 008/009: offline errors, account switch, reinstall or a second device can lose practical discoverability. Server history remains; add an authorized bounded discovery contract |
| Read cache lifetime | Activity `historyLoaded` never invalidates on task return; reminder has a separate row set; Calendar caches a range until explicit invalidation | Confirmed 010: define domain mutation -> owner invalidation events. Preserve unresolved local create/feedback during refetch |
| Inconsistent task state hydration | Check-in hydrates selected context fields, defaults restrictions/alarm acknowledgement | Confirmed 004: state reconstruction must be complete and tested by round-trip equality, not a subset of rendered labels |
| Supporting tasks outside shared owner | Calibration/ZoneProfile/CheckIn use independent local load/run patterns; ZoneProfile can approve integrated test-plan proposals (`ZoneProfileScreen.tsx:239`) | Check-in defect is proven. The equivalent integrated-test return path needs shell-level verification; do not assume plan mutation refresh propagates through navigation |
| Revision identity vocabulary | Template UUID, swipe occurrence UUID, planned-workout UUID, plan revision number and revision UUID coexist | Current occurrence contracts/tests are strong. Keep names precise; `placeDraftWorkout(templateId, ...)` is an occurrence path despite its local parameter name. Rename only in separately approved cleanup |
| Physiology version layers | Phase 3 historical calculations, Phase 10 historical spacing, Phase 13 load, Joren planning V2 are intentionally distinct | Preserve provenance. Production review coverage must bind both active policies (002), not collapse all version fields into one |
| Legacy owner adapter | Separate repositories cache opaque <-> legacy mappings in process-lifetime dictionaries | Bound/remove the compatibility cache after an approved cutover and deletion semantics. Memory growth and cache-after-deletion behavior were not profiled; no unauthorized access demonstrated |
| Stale diagnostics | Backend supplies request IDs and stable codes; mobile error type keeps status/code but not request ID | Support cannot reliably correlate a reported save failure. Add safe correlation metadata without logging athlete input or private load |

## Performance evidence and bounded-list risks

The synthetic matrix used the full 154 imported source workouts projected to their V2 eligibility and the current static catalog. Source workout names/loads/segments came from the tracked import; IDs were stable synthetic source identities, not hosted randomly generated successor IDs. Observations on this Windows Python 3.10 environment:

| Scenario, broad availability unless stated | Result | Local domain time |
| --- | --- | --- |
| Run, all history zero | Generated two-workout base plan input | 0.0065 s |
| Triathlon, all history zero | `catalog_capacity_unsatisfied` | 19.4607 s |
| Triathlon, only run history nonzero | Approved fail-closed `zero_history_discipline_baseline_unavailable` | <0.0001 s |
| Triathlon, 2/5/3 hours swim/bike/run | Generated seven-workout base plan input | 15.8413 s |
| Duathlon, 5 bike/3 run hours | Generated four-workout base plan input | 0.4167 s |
| Swim, two hours | Generated four-workout base plan input | 0.0065 s |
| Run with no available dates | `availability_required` | 0.5113 s |

These are domain timings, not network-inclusive or Railway hardware benchmarks. Candidate preparation rebuilds catalog/history/context and tests completability repeatedly; `create_swipe_draft` also asks for a next candidate. CPU work is synchronous inside async services and the Docker command runs one Uvicorn process. **007 is a confirmed event-loop-isolation problem**, even though actual production request latency is unverified. Profile selection state growth, feasibility scheduling, full-draft transitions and infeasible cases. Preserve deterministic ordering and exact target/cap rules when optimizing; avoid introducing Redis/Celery/services as a shortcut.

Onboarding `fetch_state` fans out eleven owner-scoped Data API calls in parallel (`onboarding/repository.py:319`), including metrics/boundaries for all historical profiles. The Activity load calls onboarding plus history, calendar and external activities. Parallel I/O avoids a sequential N+1 loop, but it does not make the total query volume free. Many route/profile refreshes can rebuild the same context. No complete end-to-end request-count or mobile render profile was captured, so do not claim a measured render/memory fix.

Activity history lacks a cursor and is treated as a complete list; local Supabase `max_rows=1000` can bound returned rows (U-002). Historical zone metrics/boundaries and proposals likewise merit bounded-current-context queries rather than ever-growing account histories. Calendar API requests are limited to 93 days and FlashList is used for Activities; these protections should be retained. Large component size alone is maintainability evidence, not proof of a slow render.

## Transactions, retries and failure domains

- Atomic plan/zone approval uses database locks and expected revisions; local tests demonstrate replay/stale behavior. Do not replace this with unconditional writes.
- Check-in generation and `attach_plan_proposal` are separate effects; latest context SQL only accepts open check-ins. Response-loss after attach cannot replay (006). Add recovery around the actual transaction boundary, not a wider blind retry.
- Activity create keys and RPE read-before-retry are useful existing protections. Preserve the key and exact payload/row identity on ambiguous outcomes. HTTP 200 with unreadable JSON currently bypasses recovery (013).
- Mobile fetch has no deadline (012); a busy flag without a settling promise is not recoverability.
- Profile `saveProfile` issues physiology and identifying PATCH requests via Promise.all. One can commit while the other fails; no cross-record transaction or partial-success reconciliation is implemented. No existing explicit all-or-nothing profile requirement was found, so this is a recoverability/product-contract risk, not a confirmed transactional-integrity violation. Test partial success before promising atomic profile saves.
- Calendar has a latest-request guard and returned-authoritative-plan replacement. A move confirmed against an old revision is rejected; cancellation is nonmutating. Cross-week context and concurrent neighbor changes remain missing (003).
- Some supporting-screen run handlers rely on rendered busy state, while core planning/activity paths use synchronous refs. Same-tick double invocation and overlapping different controls in onboarding/check-in/calibration need negative tests. Existing native Button promises are sometimes discarded by `void` wrappers, so do not infer complete deduplication from its local lock alone.

## Optional Polar activation risks — not demonstrated production incidents

| Risk and exact source | Evidence level / next verification |
| --- | --- |
| Accepted webhook work runs in FastAPI `BackgroundTasks`, `modules/integrations/router.py` final webhook handler; `service.py:310` deduplicates receipt before scheduling | Source risk: process death after receipt acceptance but before work may leave a duplicate that does not reschedule. Verify persisted queued/failed receipt claiming before enabling; the historical-import retry job does not establish webhook recovery |
| `PolarAccessLinkClient.get_fit`, `polar.py:178`, checks bytes after buffering | Confirmed buffering order; no memory-pressure exploit run. Stream with an enforced cap if Polar activation is authorized |
| Webhook handler reads `await request.body()` before an application size check | Application body cap not found; actual Railway/proxy limits unknown. Verify the effective ingress limit without sending abusive production traffic |
| File upload and metadata RPC are separate operations, `integrations/repository.py:357` | A successful object write followed by metadata failure can orphan an object. Existing 409 retry tolerance helps retry, not abandoned-account purge. Test cleanup/reconciliation in synthetic Storage |
| Retention settings appear only in settings validation; no purge use | Confirmed implementation gap captured by 014. Approval of days alone does not enforce deletion |
| OAuth callback consumes one-time state before provider exchange/registration finishes | A failed exchange requires reconnect/new state. Verify clear recovery UX and provider consistency; no duplicate real OAuth calls performed |
| Production legal/privacy gates are conditional on environment=production | Live local mode defeats that condition (001); enabled credentials/provider state unknown |

## Release and dependency debt

Backend `pyproject.toml` uses version ranges and Docker builds run pip install without a committed lockfile or image digest. The audit venv uses FastAPI 0.139.2/Pydantic 2.13.4; production OpenAPI differs in Decimal pattern metadata while staging matches local. This is evidence of a reproducibility/verification gap, not proof of a version-induced runtime failure. Pin an approved reproducible dependency set and record it in release evidence.

Mobile has a lockfile and current Expo 57.0.24/React Native 0.86.3 source dependencies. The last inspected EAS build predates native SVG additions. `eas.json` has no explicit runtimeVersion/channel/updates rollout; no configured OTA rollback scheme was established. Source V1/V2 switches remain selectable in release and V1 is the default unless an explicit flag chooses V2. A UI switch is presentation rollback only; it cannot undo backend schema or physiology changes.

Production auto-deploy branch/root/CI-wait settings were not read because Railway credentials are invalid. Source scripts apply pending migrations to the currently linked Supabase project and then upload the directory to a production-designated Railway service. They do not independently prove mobile/backend/database project pairing, clean source SHA or exact deployment identity. Do not execute these scripts as a verification step; review/fix their release checks separately.

Current npm advisories (017) require compatible transitive updates/reachability triage. The registry's automated fix suggestion includes an Expo 44 downgrade, which conflicts with the project's SDK 57 instruction and is not an authorized or sensible automatic fix. React Native SVG/icon inclusion must be checked in a fresh native build after dependencies are resolved.

## Test-quality assessment

Strong tests exercise behavior: exact public API contracts; pure-domain anchors/rounding/units/DST; occurrence versus template identity; repeated requests; server revision ownership; warning cancellation; latest calendar reads; RPE correction preconditions; current versus historical versions. Existing tests correctly require explicit approval and no private-load projection.

Material limitations:

1. Many API tests use in-memory repositories that implement the expected database semantics themselves; they do not prove locks, grants, RLS or migration compatibility.
2. SQL-text contract tests prove specific strings exist, not that PostgreSQL executes the intended statement/trigger order. All 27 pgTAP suites need a fresh execution.
3. Ordinary multi-sport tests use the small static catalog, while broad full-source coverage is heavily run-focused. The full-source triathlon timing/capacity behavior was missed.
4. UI tests mock transport, navigation, animations and native surfaces. They cannot establish keyboard/scroll gesture reliability, physical lifecycle, native SVG linking or real token refresh.
5. Check-in tests restore only a subset of answers; no restriction-preserving round trip or shared-host next-week approval test existed. Added audit probes expose both failures.
6. Two active/pending assertions depend on October fixture dates and currently fail (016). A fixed clock diagnoses the tests; it does not make the actual canonical suite green.
7. The first approval-failure audit mock contradicted the backend's idempotent contract. It was corrected to a protected control and **not** counted as a defect. More mocks are not automatically stronger evidence.
8. There is no mobile CI job (015), no proven persisted multi-week test across adjacent-week spacing and no fresh two-token Storage test.
9. Existing private-load tests check selected keys/projections/source text, not every dynamic exception string, telemetry SDK or compiled asset. No actual private-load leak was found.
10. No recovery test currently establishes a delayed server create committing after process death on another device. Required before claiming crash-safe exactly-once creation across process lifetimes.

## Product decisions and release risk register

- **Taper scope:** non-Monday races intentionally fail closed in the pre-race week; an approved partial-week target/catalog rule or explicit beta restriction is required. No curve was invented.
- **Zero/asymmetric history:** zero-run works; all-zero triathlon currently cannot fit the catalog; a single nonzero discipline with zero required peers intentionally fails closed. Decide truthful onboarding/beta messaging or reviewed coverage; do not allocate invented load.
- **Rest/injury:** starting a new check-in must present active restrictions, not assume clearance. Define the intended explicit review UX and whether professional-clearance states can be self-cleared; do not invent clinical clearance rules.
- **Weekly measurement completeness:** U-001 needs an explicit aggregate completeness contract and PostgreSQL test before interpreting missing data as full adherence.
- **Health-data lifecycle:** owner/legal decisions are needed for the implemented collection and optional processors; no generic compliance claim follows from RLS.
- **Beta access:** a code redemption screen exists, but the public API authority is authenticated ownership. Decide whether invitations are a commercial UI entitlement or mandatory service access boundary; do not assume a code makes every route private to invitees.
- **Account recovery and support:** define reset/deletion/contact channels, expected logout/revocation behavior and support use of request IDs.
- **Observability:** define safe operational metrics (latency/error code/revision/mutation outcome), alert ownership, redaction, retention and incident recovery. No general production log/metric audit was possible.

All risk items retain their uncertainty. Only the twenty main finding records are included in the confirmed issue count. The prioritized plan distinguishes code changes, owner decisions and runtime gates.
