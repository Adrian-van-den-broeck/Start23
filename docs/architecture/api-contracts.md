# Start23 API Contracts

## Status

This document defines the client and integration API surface. Foundation and
identity operations are implemented; later domain endpoint shapes remain
proposals subject to the open decisions listed below.

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

### Activity representation

May include duration, distance, zones, RPE, provider, match status, and
qualitative result. It must not contain realized or matched planned TSS.

## UC-01: onboarding and baseline

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/me/profile` | Read the athlete profile | Token-derived athlete |
| `PATCH /v1/me/profile` | Update confirmed profile fields | Validate biometrics and timezone |
| `GET /v1/onboarding` | Read resumable onboarding state | No internal calculations |
| `PUT /v1/me/training-history` | Replace confirmed weekly history entries | Canonical minutes |
| `POST /v1/me/goals` | Create a SMART goal | Validate priority, date, metric, feasibility |
| `PUT /v1/me/goals/{goal_id}` | Update an owned goal | Macrocycle impact may require a proposal |
| `PUT /v1/me/zones/{discipline}` | Submit explicit manual/fallback setup | Direct user confirmation semantics are open |
| `POST /v1/onboarding/complete` | Validate completion and create initial planning proposal | Does not silently activate a plan |
| `POST /v1/integrations/{provider}/oauth/start` | Start provider connection | Returns provider authorization information |
| Provider callback | Complete provider OAuth | Server-side secret handling |

`POST /v1/onboarding/complete` should return public onboarding state and, when
enough data exists, a reference to an initial pending plan proposal.

## UC-02: weekly planning

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/weekly-plans/proposals` | Generate a pending weekly plan | Idempotent per athlete/week/input revision |
| `GET /v1/weekly-plans/{plan_id}` | Read active or explicitly selected revision | Public fields only |
| `GET /v1/weekly-plans/{plan_id}/deck` | Get eligible workout cards | Filtering happens server-side |
| `PUT /v1/weekly-plans/{plan_id}/selections` | Save athlete selections to a draft revision | Must not modify an active revision in place |
| `POST /v1/weekly-plans/{plan_id}/schedule-proposals` | Auto-schedule selected workouts | Returns pending proposal |
| `POST /v1/weekly-plans/{plan_id}/validate` | Validate a draft or explicit user layout | Returns qualitative warnings |
| `PATCH /v1/planned-workouts/{workout_id}` | Explicit athlete schedule edit | Warning-versus-proposal semantics unresolved |
| `GET /v1/calendar?from=...&to=...` | Read public calendar events | Athlete timezone |

Workout-deck responses may return low/high time-bucket information but no hidden
TSS budget.

## UC-03: activity execution and feedback

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/activity-imports` | Submit a direct FIT/TCX or supported import | Prefer signed upload for large files |
| `GET /v1/activity-imports/{import_id}` | Read import status | Sanitized parsing errors |
| `GET /v1/activities` | List owned activities | Public fields only |
| `GET /v1/activities/{activity_id}` | Read activity summary | No realized TSS |
| `GET /v1/activities/pending-rpe` | List completed activities awaiting RPE | Does not block unrelated reads by default |
| `PUT /v1/activities/{activity_id}/rpe` | Record RPE from 1 through 10 | Idempotent replacement policy must be defined |
| Provider webhook endpoints | Receive provider events | Signature verification and idempotency |

After an activity is processed, the service may create a pending correction
proposal. The activity response can link to the proposal and include a
qualitative explanation, but cannot disclose internal TSS values.

## UC-04: weekly check-in

| Operation | Purpose | Critical notes |
|---|---|---|
| `POST /v1/checkins` | Start or resume the athlete's weekly check-in | One open check-in per week |
| `PUT /v1/checkins/{checkin_id}/context` | Submit structured availability, fatigue, and injuries | Preferred phase-one path |
| `POST /v1/checkins/{checkin_id}/messages` | Add a coach conversation turn | LLM extraction/explanation only |
| `GET /v1/checkins/{checkin_id}/context-candidate` | Read extracted structured candidate | Candidate is not active |
| `POST /v1/checkins/{checkin_id}/context-confirmation` | Confirm or correct candidate context | Required before critical effects |
| `POST /v1/checkins/{checkin_id}/plan-proposals` | Generate next plan from confirmed context | Deterministic engine |

LLM output cannot itself represent approval. Approval must be an authenticated,
unambiguous operation linked to a specific proposal and revision.

## UC-05: zone evaluation

The trigger is an internal scheduled command using the same application
services as the FastAPI app. It does not need a public mobile endpoint.

Client operations:

| Operation | Purpose | Critical notes |
|---|---|---|
| `GET /v1/change-proposals?kind=zone_update` | List pending zone revisions | Public explanation only |
| `GET /v1/change-proposals?kind=validation_test` | List pending test-scheduling proposals | No automatic calendar mutation |
| Proposal approve/reject operations | Decide the proposal | Separate zone confirmation policy unresolved |

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

- activity import initiation;
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

## Versioning and concurrency

Plan and zone responses include public revision numbers. Critical writes submit
the expected revision. The backend never uses last-write-wins for an approval.

Direct user schedule edits also need a revision precondition:

```http
If-Match: "plan-revision-4"
```

The exact HTTP precondition mechanism may instead be a request-body revision,
but only one consistent approach should be selected.

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

- Whether RPE is editable and whether the prompt can be dismissed.
- Exact resource-disclosure behavior: `403` versus `404`.
- First provider and its callback/webhook paths.
- Whether ratios and warnings are returned as plan fields or dedicated
  validation resources.

Resolved for MVP:

- weekly-plan, proposal, zone, and activity state names follow the Phase 0
  decision lock;
- direct athlete calendar edits apply with qualitative soft warnings;
- Phase 7 accepts a canonical activity summary, so FIT/TCX upload is deferred;
- test scheduling and a calculated zone update require separate approvals.
