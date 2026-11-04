# A6 recovery compatibility remediation

2026-11-04, Europe/Amsterdam. Start: `f5831d3cbde04f60053402eb3083a1f1e6ade7a8` plus the eight byte-verified audit-overlay files. Final software SHA: `8f75140169e074111e868d48bcf67e82aed8f899`. **Complete mobile-only recovery is not possible with the observed older API. Mobile-only remains NO-GO.**

## Evidence and limits

The refreshed public OpenAPI contains 69 paths and no `GET /api/v1/weekly-plans/recovery`. The captured, reduced contract is [observed-live-contract.json](evidence/remediation/observed-live-contract.json), with the raw response fingerprint. No athlete records were requested.

Available legacy plan/draft reads require an exact ID. Calendar is date bounded and cannot enumerate unscheduled drafts, all pending revisions, or prove absence of an approved rest-only plan. Proposal envelopes contain revision identity but do not supply a complete inventory of active plans and drafts or a global proof of absence. Onboarding completion does not provide that inventory. Calling a create/complete/check-in endpoint as a discovery probe would mutate state and risk duplication. No such fallback was added. Mobile never queries Supabase tables directly or accepts a client owner ID as authorization.

A verified local locator can recover that exact owned resource with the existing authenticated GET, and the existing A6 controller does this before discovery. This is partial knowledge, not proof that no other active/pending/draft state exists. Without device locators (reinstall/second device), full recovery requires the backend capability. We preserve the known snapshot and keep the recovery gate closed rather than report success.

## Implemented states and behavior

| Situation | Result |
| --- | --- |
| New backend returns validated active/pending/draft snapshots | Existing A6 behavior is retained, including exact IDs/revisions, pending handoff and owner-scoped persistence. No capability request is added to successful recovery. |
| New backend returns all three fields as null | Authoritative no-plan state, `resumeState=ready`; no creation occurs automatically. |
| Recovery GET returns 404/405/422 | A bounded authenticated GET of the same backend's `/openapi.json` checks whether the recovery GET is advertised. Older FastAPI can interpret `recovery` as the UUID plan parameter and return 422. The error code alone is never proof of capability absence or no plan. |
| Valid OpenAPI 3 schema does not advertise the GET | Typed `PlanningRecoveryEndpointUnavailableError`; controller reason `endpoint_unavailable`, recovery remains failed. No fabricated empty response. |
| Schema missing/malformed/unreadable, or GET still advertised | Original failure retained as unknown. A schema read failure cannot erase the original failure. |
| Network timeout/HTTP 408/429/5xx | `transient`; retain locators and known state, explicit retry. No schema fallback on these failures. |
| HTTP 401 / 403 | Separate `authentication` / `authorization` states. No capability fallback, cross-owner discovery or replacement plan. |
| Invalid response, cancellation, ambiguous 404/422 | `unknown`; do not infer absence. |
| Known approved/pending plan plus unavailable discovery | Retain the exact verified plan/revision and locator, show recovery limitation in both presentations. Known state is not complete recovery. |
| Account switch | Existing keyed owner provider retires the old owner; no old plan/failure continuation is copied to the new account. |

Safe localized messages describe recovery/session state without exposing raw server messages or implementation details. `generate()` refuses before network activity when recovery is not ready or a classified failure remains. `clearPlan()` cannot discard the known locator during failed recovery. Existing local operations cannot turn a classified recovery failure into proof of successful discovery. Stale write preconditions, pending approval, original retry input and account lifetimes remain intact.

The audit's fixed-off registration gate is retained: no skip/unknown controls in either UI, registration helpers reject before fetch, V2-only activity confirmation is omitted before serialization, and actual duration remains blank until manually supplied. No catalog/V2 activation was introduced.

## Verification

The focused run before the final additional guards passed **105 tests in four suites**. Final full-candidate results are in [the remediation report](WOMBO_INTERNAL_TESTING_REMEDIATION_REPORT.md). New cases cover successful new-server empty/known recovery, observed old-server schema, 404 versus 422, failed capability reads, malformed schema, auth/transient errors, known/pending retention, generation/locator protection, retry back to A6, account switching and exact older activity-input fields. Existing A3–A9, shared V1/V2, Calendar, activity/RPE and privacy regressions remain enabled.

An OpenAPI capability hint is only used to classify a failure; it never authorizes a mutation or replaces a server snapshot. Even a stale schema cannot cause this code to manufacture absence or create a plan.

## Remaining backend requirement

Provide and verify the accepted owner-scoped A6 GET with its complete active/pending/draft contract. Its existing repository uses authenticated RLS reads, verified opaque owner filtering, bounded deterministic selection and exact snapshot rereads; it introduces no new migration itself. Test real two-user isolation, rest-only and unscheduled state, stale/racing revisions, reinstall/second device and terminal proposals against the actual deployed historical schema. A deployment of the cumulative backend also carries the independent A5 database gate. Do not remove A5 or bypass production validation to obtain A6.

No complete legacy fallback is claimed. No replacement plan, database write, login, push or deployment was performed.
