# WOMBO V6 production compatibility matrix

16 November 2026, Europe/Amsterdam. **Unchanged production compatibility is NOT cleared.**
Starting commit: `289280a5bddf6f0cc65eca1f562561e7df9a603c`. Migration ordinals and hashes refer to the [gap inventory](JOREN_V6_HOSTED_MIGRATION_GAP_ANALYSIS.md). No production functional mutations were performed.

## Actual deployed-version evidence

Public GETs to `https://start23-production.up.railway.app` and `https://r6-api-r6-staging.up.railway.app` returned 200 for `/health`, `/ready` and `/openapi.json`. Both advertise version `0.1.0` and 69 API paths. The first reports environment **local**, the second **staging**. These labels do not establish source SHA or production safety. Local mode-state points at the first URL while the current mobile environment points at the second. The owner must identify the actual service/environment and mobile audience before execution.

Read-only Railway status for the existing project `c0cf7bc7-abe8-4db5-857a-85cc39850640`, production environment, returned **Unauthorized; login required**. No login, deployment, variable read/change or relink was performed. Exact deployed backend commit, runtime flags, scheduled Railway processes, installed Android/iOS builds and current store rollout are **unverified**. A generic healthy endpoint does not close these gates.

The published contracts lack the accepted branch's frequency-preference, interruption, workout-registration and weekly-plan-recovery paths. Common path declarations match, but response/request component definitions differ. Production `ActivityResponse` has `additionalProperties: false` and no `session_rpe_version`/guidance. Staging has the same omissions. [Observed metadata](migration-readiness-20261116/backend-public-metadata.json), [contract differences](migration-readiness-20261116/public-contract-comparison.json).

## Demonstrated activity compatibility failure

Migration **5** replaces `private.activity_public_json` for all existing create/get/list/match/completion callers. Its new `session_rpe_version` is emitted even for historical activities (`legacy`). A real synthetic PostgreSQL response was validated with the strict historical `ActivityResponse` from `5d71c688deb610bf5ec79c0f6fac77c835be6b51`: **extra_forbidden at session_rpe_version**. Removing only that field validates. That historical service passes repository rows directly to `ActivityResponse.model_validate`; its error path is a stored-activity domain error, not silent field filtering. This reproduces a concrete historical-consumer incompatibility, **not a claimed production write test or exact deployed-code identification**. [Probe](migration-readiness-20261116/activity-compatibility-probe.json).

Before G2, require the deployed source and either (a) a separately reviewed compatibility backend that accepts the new projection while retaining historical behavior and leaving V2/V6 disabled, or (b) a separately authored forward database compatibility design retaining the historical projection and exposing V2 metadata through an explicitly versioned path. Reverting to an older backend after migration 5 is not automatically safe. Do not edit the accepted migration or assume the whole newer branch can be deployed without its own review.

## Workflow matrix

“Local PASS” below means real portable PG17 SQL with synthetic subjects/simulated claims and the accepted local backend where stated. It never means a deployed backend, real GoTrue or physical-device result.

| Surface | G1: A5 (1) | G2: V2 + inactive V6 core/corrections (2–12) | G3: lifecycle/memberships/frequency (13–16) | Evidence / remaining gate |
| --- | --- | --- | --- | --- |
| Historical onboarding / A3 restrictions | No schema change | Identity/eligibility unchanged; new V6 constraints apply by version | New source-invalidation triggers touch profiles/goals/zones/injury; no preference/authority means no extra session issuance | Local R2/R3/R4/R5 and history suites PASS; installed mobile/source SHA and hosted authentic workflow remain open |
| A4 check-in handoff | Existing context semantics | Preserved | Shared context includes current completion provenance; confirmation supersedes prior confirmed row while retaining its timestamp | Phase-8 and A5 overlay PASS after every group; migration 14 has historical behavior impact |
| A5 creation/attachment/replay | New owner read; v3 serializes and attaches atomically | v3 retained; V2 v4 evidence optional by caller | V6 dispatch remains inside same check-in lock/replay boundary | Local 29/29 overlay; lifecycle nine groups; untouched original fixture FAIL remains separate |
| A6 account-scoped recovery | No local-storage namespace change | No mobile deployment needed to retain historical locators | Additional V6 logical/physical projections; existing public plan/calendar reused | Existing mobile 935 tests PASS. Deployed API lacks recovery endpoint, so A6 deployment cannot be assumed |
| A7 network/auth recovery | No Auth changes | No Auth changes | No Auth changes | Prior genuine GoTrue refresh/logout/expiry evidence retained; no new session behavior claim |
| A8 activity/cache synchronization | No change | Registration trigger affects all linked activity writes; migration 5 breaks strict older row consumer | Shared activity/match/registration readers use effective membership | Local SQL/core/mobile PASS; old deployed consumer compatibility remains blocked |
| A9 planner/UI parity | Historical planner stays default | V6 catalog hidden; legacy constraints equivalent for historical ruleset | Existing paths gain V6 dispatch/projections only when explicitly injected | All 40 historical cases, 26 accepted completed outcomes unchanged; no default switch |
| Approval / reject RPCs | Existing authenticated invoker contracts | Evidence-bearing approvals need 10; PT409 fix 11 must accompany V2 guards | Membership/frequency guards recheck evidence and authority; historical rows without V6 snapshot use historical path | Local approval/rejection/retry/stale/foreign cases PASS. Do not expose 4 without 10 |
| Realized TSS V2 | Absent | Private prospective inputs/calculations/registration/evidence; measured evidence has priority; no historical recomputation | Membership preserves original activity/load provenance | Full accepted suites PASS; runtime enablement and scientific acceptance remain separate |
| Existing activity registration | Existing manual activity paths | New skipped/unknown CAS ledger and trigger; absent evidence stays unknown | Expected IDs include retained physical siblings exactly once | Eleven evidence-rescheduling groups PASS, including concurrent activity/registration/move |
| Opaque athlete identity | Same verified subject → opaque map → legacy owner adapter | Dual-owner triggers and composite FKs extended | Frequency records use opaque identity, activity FKs retain original physical IDs | Two distinct synthetic subjects in local tests; actual hosted signup trigger unchanged |
| RLS / grants | New A5 read EXECUTE | Private forced-RLS tables; service-only generated writers | Private helper needed by existing invoker reads; preferences are owner-scoped | 13 new authenticated signatures violate literal no-new-EXECUTE. No generated-write grant to athlete; no new anon EXECUTE |
| Jobs / triggers | No scheduled job | Activity/approval/segment/custody triggers added | Profile/goal/zone/injury/check-in/draft invalidation triggers added | No hosted cron/net/queue relations found; platform webhooks 403; Railway schedules unverified |
| Deletion / cascades | No new table FK | All new owner data links to existing user/map/revision/activity cascades | Membership and policy records retain deletion paths; source catalog is global/immutable | Accepted SQL deletion inventory PASS; no real account deletion this task; exact synthetic cleanup planned separately |
| Public API / mobile | Existing response shapes retained | Shared activity JSON field changes even with V6 off | Separate mobile projections add physical ID/frequency summary only on V6 paths | Current backend/mobile contract tests PASS; actual old backend/app versions not certified |

## Exact permission conflict

The final local effective catalog adds these authenticated signatures relative to the observed 47-migration boundary:

| Migration | New EXECUTE signature |
| --- | --- |
| 1 | `public.get_checkin_plan_proposal(uuid)` |
| 2 | `public.create_activity_summary_v2(uuid,text,jsonb)` |
| 3 | `public.get_workout_registration(uuid)`; `public.confirm_workout_registration(uuid,uuid,integer,text)` |
| 6 | `public.get_v6_weekly_plan(uuid,integer)` |
| 13 | `public.get_v6_mobile_weekly_plan(uuid,integer)`; `public.get_v6_mobile_calendar(date,date)` |
| 14 | `public.get_v6_move_workout_context(uuid)` |
| 15 | `private.v6_revision_workouts(uuid)` — dependency of existing invoker RPCs |
| 16 | `public.get_frequency_preferences()`; `public.save_frequency_preferences(integer,uuid,jsonb)`; `public.report_frequency_interruption(uuid,text,text)`; `public.get_v6_frequency_swipe_receipt(uuid)` |

Owner-scoped reads/preferences are distinct from generated-plan authority, but the current instruction prohibits **new execution permission**, not just new generation. No permission exception is assumed. A blanket revoke of the private membership helper would break shared historical invoker reads; a privilege closure needs design and regression review. The offline owner bundles enforce the literal restriction and refuse commit. No new production membership in either frequency role is authorized.

## Separate A5 normalization assessment

At the accepted starting commit, only typed `PlanningConstraintError('v6_search_incomplete')` receives optional `details.planning_code`. HTTP 422, top-level `validation_failed`, request ID, qualitative message, no automatic retry and exact replay stay. The mobile parser allowlists the constant discriminator and does not forward arbitrary private detail. Backend/mobile tests cover these boundaries.

This is an **application-code change, not one of the 16 migrations**. The deployed SHA is unknown; the OpenAPI contract cannot prove exception-normalization code deployed. Treat this fix as local-only until deployment artifact evidence and an authorized safe synthetic exhaustion check exist. Database installation does not deploy it. Protected A5/A6 worktrees were unchanged.

## Verdict

Local schema/data compatibility is demonstrated within the tested portable scope. **It is not established that existing deployed backend and mobile can operate unchanged after G2/G3.** The activity-projection failure, unverified deployed artifacts, hosted/default-ACL parity, new client-EXECUTE conflict and missing recoverable backup keep production execution blocked.
