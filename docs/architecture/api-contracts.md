# Start23 API Contracts

## Status

This document defines the client and integration API surface. Foundation,
identity, Phase 4 onboarding, the Phase 5 workout catalog, Phase 6 weekly
planning/calendar, and the Phase 7 canonical activity/RPE loop are implemented
locally. Phase 12 adds a TSS-free, fail-closed goal capability contract; later
non-race mutation and planning shapes remain proposals subject to the open
decisions listed below.

Related documents:

- [Backend architecture](backend-architecture.md)
- [Domain model](domain-model.md)
- [Security model](security-model.md)
- [Business-rule traceability](../requirements/business-rule-traceability.md)

## Contract principles

- Base path: `/api/v1`
- Media type: `application/json`, except file-upload flows.
- All mobile operations require a verified Supabase access token unless stated
  otherwise.
- The authenticated athlete is derived from the token; request bodies do not
  supply an authoritative `user_id`.
- Every route declares an explicit Pydantic response model.
- Planned and realized TSS are forbidden from all public response bodies.
- Generated critical changes return a pending proposal and do not mutate the
  active plan or zones.
- Dates use ISO 8601. Calendar operations include athlete timezone context.
- Mutating requests that may be retried support idempotency keys where
  appropriate.
- Concurrent critical mutations use revision/version preconditions.

## Authentication

Mobile requests:

```http
Authorization: Bearer <supabase-access-token>
```

FastAPI verifies the token signature, issuer, audience, expiry, and subject.
Expired or invalid tokens return `401`. A valid user attempting to access
another athlete's resource receives `404` or `403` according to the final
resource-disclosure policy.

Provider webhooks do not use athlete bearer tokens. Each provider endpoint uses
its signature/challenge scheme and an idempotent event identifier.

Implemented foundation operations:

| Operation | Authentication | Purpose |
|---|---|---|
| `GET /health` | Public | Process liveness |
| `GET /ready` | Public | Deployment readiness |
| `GET /api/v1/health` | Public | Versioned liveness |
| `GET /api/v1/ready` | Public | Versioned readiness |
| `GET /api/v1/me` | Bearer token | Verified token identity |

Implemented Phase 4 operations:

| Operation | Purpose |
|---|---|
| `GET/PATCH /api/v1/me/profile` | Read or update profile and biometrics |
| `GET /api/v1/onboarding` | Read resumable onboarding state |
| `PUT /api/v1/me/training-history` | Atomically replace swim/bike/run history |
| `POST /api/v1/me/goals` | Create the primary race-oriented A goal |
| `PUT /api/v1/me/goals/{goal_id}` | Update the owned primary goal |
| `PUT /api/v1/me/zones/{discipline}` | Save first active or later pending zones |
| `POST /api/v1/onboarding/complete` | Complete onboarding and queue initial planning |
| `POST /api/v1/change-proposals/{proposal_id}/approve` | Atomically apply an owned, stale-safe zone replacement |
| `POST /api/v1/change-proposals/{proposal_id}/reject` | Reject an owned zone replacement |

Implemented Phase 12 operation:

| Operation | Purpose |
|---|---|
| `GET /api/v1/onboarding/goal-options` | Distinguish available dated race/event planning from personal-goal families that are explicitly coming later |

The Phase 12 catalog is authenticated and contains only public capability
metadata. `race_event` is date-required and race-date anchored. General
fitness, weight loss, and muscle gain are cycle-week-1 modes but remain
`coming_later` with `deterministic_rules_not_approved`; there is no non-race
write or proposal endpoint. `POST /api/v1/me/goals` continues to accept only
the strict race-goal schema and rejects a supplied non-race `goal_type`.

Implemented Phase 5 operation:

| Operation | Purpose |
|---|---|
| `GET /api/v1/workout-catalog` | Return reviewed templates; each segment has exactly one `zone_target` or `protocol_target`, and no internal load |

All `/v1/...` domain paths retained in the proposal tables below are historical
shorthand and resolve under the authoritative `/api/v1/...` base path when
implemented.

## Standard error shape

Implemented error envelope:

```json
{
  "error": {
    "code": "proposal_stale",
    "message": "This proposal is based on an older plan revision.",
    "details": {
      "proposal_id": "uuid"
    },
    "request_id": "uuid"
  }
}
```

Error details must not contain TSS, credentials, raw provider payloads, or
another athlete's identifiers.

Proposed status-code conventions:

| Code | Meaning |
|---|---|
| `200` | Successful read or idempotent update |
| `201` | Resource or proposal created |
| `202` | Import accepted for processing |
| `204` | Successful operation without response body |
| `400` | Malformed or unsupported request |
| `401` | Missing or invalid access token |
| `403` | Authenticated but operation is not permitted |
| `404` | Resource not found within athlete scope |
| `409` | Stale revision, duplicate active state, or state conflict |
| `422` | Valid JSON that fails domain validation |
| `429` | Rate limit |
| `503` | Temporary provider or processing dependency failure |

## Public representation rules

### Workout representation

May include:

- identity and catalog version;
- discipline;
- name and instructions;
- duration and distance;
- target zones;
- expected RPE;
- intensity bucket;
- schedule and status;
- qualitative warnings.

Must not include:

- `tss`;
- `tss_score`;
- `planned_tss`;
- `realized_tss`;
- pTSS/rTSS aliases;
- physiological debt values from which hidden TSS can be reconstructed.

### Plan representation

May include schedule, total duration, low/high time percentages, warnings,
recovery/taper labels, proposal state, and workout cards. It must not contain
planned or realized TSS totals.

Primary intensity display uses complementary whole percentages (low rounded
half-up, high derived as `100 - low`). The same response carries exact low/high
minutes for detail display; exact decimal ratios remain internal.

### Activity representation

May include duration, distance, safe metric summaries, RPE, match status,
qualitative result, and a pending-correction reference. It must not contain
realized or matched planned TSS.

## UC-01: onboarding and baseline

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/me/profile` | Read the athlete profile | Token-derived athlete |
| `PATCH /v1/me/profile` | Update confirmed profile fields | Validate biometrics and timezone |
| `GET /v1/onboarding` | Read resumable onboarding state | No internal calculations |
| `PUT /v1/me/training-history` | Replace confirmed weekly history entries | Canonical minutes |
| `POST /v1/me/goals` | Create a SMART goal | Validate priority, date, metric, feasibility |
| `PUT /v1/me/goals/{goal_id}` | Update an owned goal | Macrocycle impact may require a proposal |
| `PUT /v1/me/zones/{discipline}` | Submit explicit manual/fallback setup | Explicitly confirmed initial setup may create the first active version; calculated replacements may not |
| `POST /v1/onboarding/complete` | Validate completion and create initial planning proposal | Does not silently activate a plan |
| `POST /v1/integrations/polar/oauth/start` | Start provisional Polar connection | One-time state; returns provider authorization URL |
| `GET /v1/integrations/polar/oauth/callback` | Complete provider OAuth | Server-side code exchange, user registration, and token handling |
| `GET /v1/integrations/polar` | Read connection metadata | Owner-scoped; no token/provider secret |
| `DELETE /v1/integrations/polar` | Disconnect and revoke | Provider deregistration precedes local token removal |
| `POST /v1/integrations/polar/imports` | Import exactly 7, 14, or 30 days | 14 days is the default; UUID idempotency key required |
| `GET /v1/integrations/polar/imports` | List owned imports | Includes bounded retry state; no credentials or TSS |
| `POST /v1/integrations/polar/imports/{import_id}/retry` | Explicitly retry an owned failed import | Only while attempts remain; revoked credentials require OAuth instead |

`POST /v1/onboarding/complete` should return public onboarding state and, when
enough data exists, a reference to an initial pending plan proposal.
The underlying `initial_plan_requests` record retains a server-side canonical
input snapshot and content fingerprint. Phase 6 uses that fingerprint as the
input revision; neither the snapshot nor its physiological details need to be
added to the completion response.

## UC-02: weekly planning

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/weekly-plans/proposals` | Generate a pending weekly plan | Idempotent per athlete/week/input revision |
| `POST /v1/weekly-plans/swipe-drafts` | Create or resume a server-authoritative deck-first week | Exact context/base binding; fixed count and composition; TSS-free |
| `GET /v1/weekly-plans/swipe-drafts/{draft_id}` | Resume one owned swipe draft | RLS owner read; one current candidate only |
| `POST /v1/weekly-plans/swipe-drafts/{draft_id}/transitions` | Accept, pass, undo, or reset passed cards | Expected revision and exact current candidate; duplicate accept/pass retry is idempotent |
| `PUT /v1/weekly-plans/swipe-drafts/{draft_id}/placements/{template_id}` | Place one accepted workout on a local date | Full deterministic layout revalidation after every placement |
| `POST /v1/weekly-plans/swipe-drafts/{draft_id}/submit` | Submit automatic or complete manual placement | Creates only an immutable pending proposal |
| `GET /v1/weekly-plans/{plan_id}` | Read active or explicitly selected revision | Public fields only |
| `GET /v1/weekly-plans/{plan_id}/deck` | Get eligible workout cards | Expected revision and exact selected IDs drive authoritative recalculation |
| `POST /v1/weekly-plans/{plan_id}/schedule-proposals` | Auto-schedule selected workouts | Returns pending proposal |
| `POST /v1/weekly-plans/{plan_id}/validate` | Validate a draft or explicit user layout | Returns qualitative warnings |
| `GET /v1/weekly-plans/{plan_id}/pending-workouts/{workout_id}/alternatives` | Read valid replacement/removal options | Exact pending revision; server-authoritative recomputation |
| `POST /v1/weekly-plans/{plan_id}/pending-workouts/{workout_id}/edit-proposals` | Replace or remove one pending workout | Exact proposal/revision preconditions; creates a new pending revision |
| `PATCH /v1/planned-workouts/{workout_id}` | Explicit athlete schedule edit | Applies a new active revision; returns soft warnings |
| `GET /v1/calendar?from=...&to=...` | Read public workouts and intentional rest days | Athlete timezone; no private load |

Workout-deck responses may return low/high time-bucket information but no hidden
TSS budget.

Phase 6 consolidated explicit template selection into `schedule-proposals`.
Phase 10.1 adds the separate bounded draft above: its state is derived from an
immutable accept/pass decision history, every write is stale-safe and
server-calculated, and it never becomes an active plan directly.

Phase 10 proposal input contains either non-empty `available_dates` or the
explicit `reuse_previous_week=true` action, never both. Plans and calendars
return `scheduled_date`, not a planned instant or training hour. Layout
validation submits the expected plan revision plus only owned workout IDs and
proposed dates. Discipline and intensity are read from the
immutable server snapshot; client-supplied classifications are rejected.

## UC-03: activity execution and feedback

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/activities` | Submit a canonical completed-activity summary | UUID `Idempotency-Key`; optional owned planned-workout or planned-outside-activity ID |
| `GET /v1/activities` | List owned activities | Public fields only |
| `GET /v1/activities/{activity_id}` | Read activity summary | No realized TSS |
| `GET /v1/activities/pending-rpe` | List completed activities awaiting RPE | Does not block unrelated reads by default |
| `PUT /v1/activities/{activity_id}/rpe` | Record or correct RPE from 1 through 10 | Correction is audited only during the activity's athlete-local week; exact retry is idempotent |
| `PUT /v1/activities/{activity_id}/planned-workout-match` | Confirm one suggested planned-workout link | Explicit athlete action; owner, discipline and open match state are checked server-side |

Phase 9 adds the Polar import/retry operations above and the signed
`POST /v1/webhooks/polar` callback. Imported summaries are validated as the
same `ActivitySummaryInput` and persisted in the existing canonical activity
tables. Available raw FIT files are stored separately and never become a
second physiological calculation path. Import never automatically links a
planned workout; a UI suggestion is inert until the athlete confirms it.

After an activity is processed, the service may create a pending correction
proposal. The activity response can link to the proposal and include a
qualitative explanation, but cannot disclose internal TSS values.

## UC-04: weekly check-in

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/checkins` | Start or resume the athlete's weekly check-in | One open check-in per week |
| `GET /v1/checkins/{checkin_id}` | Resume owned check-in state | Owner-scoped; source/expiry included |
| `POST /v1/checkins/{checkin_id}/context-candidates` | Extract an inert structured candidate and clarifying questions | Bounded free text; no persistence, confirmation, plan, or zone mutation |
| `PUT /v1/checkins/{checkin_id}/context` | Submit structured availability, fatigue, and injuries | Preferred phase-one path |
| `POST /v1/checkins/{checkin_id}/context-confirmation` | Confirm or correct candidate context | Required before critical effects |
| `POST /v1/checkins/{checkin_id}/plan-proposals` | Generate next plan from confirmed context | Deterministic engine |
| `GET /v1/me/injury-restrictions` | Read active functional restrictions and review dates | Never auto-clears |
| `GET /v1/planned-external-activities` | List planned outside sport and completion state | Actual duration/RPE are canonical activity fields |
| `POST /v1/me/goals/{goal_id}/achievement` | Explicitly enter achieved-goal maintenance | No automatic goal inference |

Phase 10 optionally uses a schema-constrained provider to assist filling the
Phase 8 structured form. Its result is ephemeral and cannot represent
confirmation or approval. A possible injury mention is never translated into
a restriction without the athlete's explicit structured choice. Confirmation
and approval must be authenticated and unambiguously linked to exact
context/proposal revisions.

## Phase 8.5: zone setup and calibration

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/onboarding/zone-options` | List known values, field test, calibration week, and RPE-only | Authenticated; no physiological mutation |
| `PUT /v1/onboarding/disciplines/{discipline}/setup` | Save one resumable setup route | Owner derived from token; optional boundaries may be empty |
| `GET /v1/calibration/protocols/{discipline}` | List reviewed active test/calibration segments | Versioned RPE, duration, and distance contract |
| `POST /v1/calibration/observations` | Save a segment observation | Immutable; exact retry idempotent; conflicting retry returns `409` |
| `POST /v1/calibration/evaluate` | Evaluate owned observations | Pure deterministic engine; generated persistence is service-only |
| `GET /v1/calibration/status` | Resume setup and evaluation state | Owner-scoped; no TSS/private load |

A valid field test may return pending threshold estimates, but it returns
`zone_status=pending_protocol` and no calculated boundaries until a complete
reviewed Zone 1-5 model exists. Submaximal Week-1 calibration cannot return a
threshold. See
[backend-zone-calculation.md](../implementation/backend-zone-calculation.md).

`POST /v1/calibration/observations` requires an owned canonical activity. The
Expo flow therefore creates the activity through UC-03, records the same
canonical 1-10 session RPE, writes immutable protocol segments, and only then
requests evaluation. Until planner eligibility and load treatment are
approved, standalone protocol execution omits `planned_workout_id` instead of
fabricating a normal planned workout.

## Phase 11: discipline profile and test scheduling

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/me/zone-profile` | Read current, pending, and immutable prior versions per discipline | TSS-free; calibration values remain hidden until the reviewed Week-2 gate permits a complete proposal |
| `POST /v1/calibration/test-assignments` | Create a standalone or weekly-plan test proposal on an athlete-local date | Standalone supports all reviewed field tests; plan integration is fail-closed for distance-only swim CSS |
| `POST /v1/calibration/test-assignments/{proposal_id}/approve` | Confirm a standalone test date | Exact assignment revision required |
| `POST /v1/calibration/test-assignments/{proposal_id}/reject` | Reject a standalone test date | Does not schedule or change a plan |

An integrated run/bike request creates a normal pending plan-revision proposal,
fixes the selected test template to the exact requested date, and returns that
proposal with the test assignment. The athlete uses the existing plan approval
operation; applying or rejecting the plan synchronizes the test assignment.
The route never prescribes an hour.

`PUT /v1/activities/{activity_id}/rpe` additionally accepts optional
`average_heart_rate_bpm`. It is required when the owned planned-workout snapshot
contains an RPE target marked `heart_rate_observation_required`. The backend
stores bpm as activity telemetry before completing RPE; it does not derive a
threshold, zone, or plan mutation from that observation.

Known-value setup and calculated-zone submission accept `source_quality` as
`athlete_entered` or `measured_lab`. Measured provenance is persisted only by
a narrow service-only calculated-profile RPC and still creates a pending zone
proposal. The client cannot directly label a stored row or activate it.

## UC-05: zone evaluation

The trigger is an internal scheduled command using the same application
services as the FastAPI app. It does not need a public mobile endpoint.

Client operations:

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/change-proposals` | List typed pending zone revisions | Filter by `state`; the profile projection supplies discipline detail |
| `GET /v1/change-proposals` | List typed zone, plan, and standalone validation-test proposals | Optional state filter; no automatic calendar mutation |
| Proposal approve/reject operations | Decide the proposal | Test scheduling and a calculated zone revision require separate approvals |

## Proposal operations

| Operation | Purpose |
|---|---|
| `GET /v1/change-proposals` | List athlete-owned proposals |
| `GET /v1/change-proposals/{proposal_id}` | Read proposal, target summary, warnings, and state |
| `POST /v1/change-proposals/{proposal_id}/approve` | Approve and atomically apply a current typed revision |
| `POST /v1/change-proposals/{proposal_id}/reject` | Reject without mutating the active target |

Approval request:

```json
{
  "expected_base_revision": 4
}
```

The response contains the applied public target representation and proposal
state. A mismatched base revision returns `409 proposal_stale`.

## Idempotency

Idempotency is required for:

- canonical activity creation;
- provider webhook processing;
- plan generation for a week/input revision;
- proposal approval and rejection;
- scheduled weekly and recovery-week evaluation.

For mobile operations, a proposed header is:

```http
Idempotency-Key: <client-generated-uuid>
```

The backend scopes the key to athlete, operation, and a bounded retention
period. Reusing a key with a different payload returns a conflict.

Phase 6 plan generation additionally has content-fingerprint idempotency.
Plan approval and rejection are naturally idempotent by proposal ID and exact
base precondition: retrying the same completed decision returns the original
public result without another state transition.

## Versioning and concurrency

Plan and zone responses include public revision numbers. Critical writes submit
the expected revision. The backend never uses last-write-wins for an approval.

Direct user schedule edits use a request-body revision precondition:

```json
{
  "expected_revision": 4,
  "scheduled_date": "2026-08-05"
}
```

## Contract validation requirements

- Pydantic rejects unknown enum values and invalid units.
- Cross-field validation checks date ranges and discipline-specific zone input.
- Public response schemas have no internal calculation model inheritance.
- Contract tests recursively check forbidden TSS keys.
- OpenAPI snapshots detect accidental public-schema expansion.
- Authorization tests attempt cross-athlete access for every resource family.
- Approval tests cover stale, repeated, rejected, expired, and already-applied
  proposals.

## Open API decisions

- Whether a pending RPE prompt can reach an explicit terminal/dismissed state;
  until then the Phase 8 app-open reminder remains visible.
- Exact resource-disclosure behavior: `403` versus `404`.
- Production approval and final public callback domain for the provisional
  Polar provider.

Resolved for MVP:

- weekly-plan, proposal, zone, and activity state names follow the Phase 0
  decision lock;
- direct athlete calendar edits apply with qualitative soft warnings;
- Phase 7 accepts a canonical activity summary, so FIT/TCX upload is deferred;
- Phase 9's provisional Polar adapter uses explicit OAuth and webhook paths,
  a one-to-30-day history request, and the existing canonical activity model;
- RPE is correctable with an audit trail only during its athlete-local week;
  after that week it is immutable and exact retry remains idempotent;
- Phase 7 matching is an explicit owned planned-workout selection; automatic
  proximity, brick, and multisport matching are deferred;
- ratios, exact intensity minutes, and qualitative warnings are fields on the
  weekly-plan representation;
- test scheduling and a calculated zone update require separate approvals.
