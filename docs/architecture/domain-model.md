# Start23 Domain Model

## Status

This document defines the logical domain model for Start23. Phase 2 implements
the base athlete profile. The hosted Phase 4 base and hardening migrations
implement profile biometrics, onboarding sessions, triathlon history, the
primary A-race goal, versioned zones, zone proposals, and fingerprinted initial
planning requests. The hosted Phase 5 migration implements the immutable
workout catalog and private template load records. The local, not-yet-applied
Phase 6 migration implements weekly plans, immutable plan revisions, planned-
workout snapshots, qualitative warnings, typed plan proposals, and private
workout/revision load records. The local Phase 7 and Phase 8 migrations add
canonical activities/private realized load and the structured weekly context,
restriction, outside-activity, maintenance, rest-day, and RPE-audit entities
described below. These local migrations are not yet applied to hosted
Supabase; later entities remain subject to their phase-specific design.
The local Phase 8.5 migration adds explicit discipline setup choices,
activity-linked immutable calibration observations, and immutable generated
evaluations. It is not yet applied to hosted Supabase.

Related documents:

- [Backend architecture](backend-architecture.md)
- [API contracts](api-contracts.md)
- [Security model](security-model.md)
- [Business-rule traceability](../requirements/business-rule-traceability.md)

## Modelling principles

- Supabase Auth is the identity authority.
- Every user-owned entity carries an immutable `athlete_id` derived from the
  authenticated user.
- Critical objects are versioned so proposed changes can remain pending.
- TSS and provider credentials are server-only.
- Store canonical units and define conversion at input/output boundaries.
- State machines use constrained values and explicit transitions.
- Calculation and proposal records retain rule-set/version metadata for audit.
- Raw telemetry files are stored in private Supabase Storage; PostgreSQL stores
  metadata and useful summaries.

## Aggregate overview

```mermaid
erDiagram
    AUTH_USER ||--|| ATHLETE_PROFILE : has
    AUTH_USER ||--o{ GOAL : owns
    AUTH_USER ||--o{ TRAINING_HISTORY_ENTRY : reports
    AUTH_USER ||--o{ ZONE_PROFILE_VERSION : owns
    AUTH_USER ||--o{ PROVIDER_CONNECTION : owns
    AUTH_USER ||--o{ WEEKLY_CHECKIN : performs
    AUTH_USER ||--o{ CHANGE_PROPOSAL : owns

    GOAL ||--o{ RACE_EVENT : may_reference
    GOAL ||--o{ MACROCYCLE : drives
    MACROCYCLE ||--o{ MESOCYCLE : contains
    MESOCYCLE ||--o{ WEEKLY_PLAN : contains

    WEEKLY_PLAN ||--o{ PLAN_REVISION : has
    PLAN_REVISION ||--o{ PLANNED_WORKOUT : schedules
    WORKOUT_TEMPLATE ||--o{ PLANNED_WORKOUT : instantiates
    PLANNED_WORKOUT ||--o| ACTIVITY : matched_by

    ACTIVITY ||--o{ ACTIVITY_FILE : sourced_from
    ACTIVITY ||--o{ ACTIVITY_METRIC : summarizes
    WEEKLY_CHECKIN ||--o{ CONTEXT_CANDIDATE : extracts
    CHANGE_PROPOSAL ||--o| PLAN_REVISION : proposes
    CHANGE_PROPOSAL ||--o| ZONE_PROFILE_VERSION : proposes
```

## Identity and onboarding

### `auth.users`

Managed by Supabase Auth. Its UUID is the canonical athlete identity.

### `athlete_profiles`

One-to-one with `auth.users`.

Implemented Phase 6 fields:

- `athlete_id`;
- `date_of_birth` or a documented alternative;
- `height_cm`;
- `weight_kg`;
- `resting_heart_rate_bpm`;
- `motivation_text`;
- `motivation_tag`;
- `timezone`;
- `onboarding_status`;
- timestamps and revision.

The MVP deliberately stores no sex/gender/physiology-category field and does
not estimate FTP from a binary coefficient. A later purpose-limited
physiological profile would require separate legal and clinical approval.

### `onboarding_sessions`

Allows onboarding to be resumed and records which steps have been confirmed.
It must not be treated as an active physiological configuration until
completion.

### `initial_plan_requests`

Queues Phase 6 plan generation after onboarding. Every pending request stores a
canonical JSON snapshot of the confirmed profile, training history, primary
goal, and active zone versions plus an MD5 content fingerprint used as the
input revision. Database triggers refresh the snapshot while the request is
pending whenever one of those inputs changes. Consuming or cancelling the
request preserves the captured snapshot and fingerprint for audit and
idempotency.

### `training_history_entries`

One row per athlete and activity category.

Proposed categories:

- swim;
- bike;
- run;
- other endurance;
- other sport.

Proposed fields include weekly minutes, source, confirmation timestamp, and
onboarding session. Whether non-triathlon categories influence phase-one load
is unresolved.

## Goals and periodization

### `goals`

Represents a SMART objective.

Proposed fields:

- `id`, `athlete_id`;
- priority `A`, `B`, or `C`;
- goal type;
- specific description;
- measurable metric type, value, and unit;
- feasibility score from 1 through 10;
- target date;
- status;
- optional race-event reference.

The A/B/C terminology is distinct from zone configuration paths A/B/C. API
enums should use unambiguous names such as `goal_priority` and
`zone_setup_method`.

### `race_events`

Represents an event date, discipline profile, and race priority. A race event
may support taper calculation. Non-race goals must not be forced into a race
entity.

### `macrocycles`

Defines a goal-specific training horizon and records the ruleset used to
construct it.

### `mesocycles`

Ordered blocks within a macrocycle. Proposed fields include sequence number,
start/end date, phase, and the planned recovery-week position.

How partial blocks are aligned when working backward from a race is unresolved.

## Zones

### `zone_profile_versions`

Represents a complete version of the athlete's configuration for one
discipline.

Proposed fields:

- `id`, `athlete_id`, `discipline`;
- `version`;
- setup method: `manual`, `test`, or `fallback`;
- lifecycle status: `pending`, `active`, `superseded`, or `rejected`;
- provenance source: `athlete_entered`, `field_test`, `wearable_import`, or
  `estimated`;
- validation state: `unreviewed`, `confirmed_by_athlete`, or
  `protocol_validated`;
- `fallback_active`;
- `needs_testing`;
- `needs_validation_test`;
- `effective_from`;
- proposal and calculation references.

At most one active zone profile may exist per athlete and discipline.

### `zone_metrics`

Typed metrics associated with a zone profile version.

Examples:

- swim CSS in seconds per 100 metres;
- cycling FTP in watts;
- cycling threshold heart rate in BPM;
- running threshold pace in seconds per kilometre;
- running LTHR in BPM;
- heart-rate zone lower/upper boundaries.

Ruleset 3 fixes the canonical units and whole-second pace precision. Exact
Cycling speed is not a zone metric. Average/maximum speed may be retained as
bike activity telemetry; it does not drive zone validation or planning.

### `discipline_zone_setups`

Stores exactly one resumable setup choice per athlete and discipline:
`known_values`, `field_test`, `calibration_week`, or `rpe_only`. It retains the
selected guidance mode, reviewed protocol identifier where applicable, swim
pool length, self-reported thresholds, and optional self-reported profiles.
The row is configuration state, not an active zone version. Complete
athlete-entered boundaries still use the normal versioned zone lifecycle.

### `calibration_observations`

Stores one immutable owner-scoped observation per activity, protocol, and
segment. It references the canonical activity and optionally a planned workout,
retains canonical RPE 1-10 plus approved objective summary fields, and rejects
changed retries while returning an identical retry idempotently.

### `calibration_evaluations`

Stores immutable outputs generated by deterministic Python and persisted only
through a narrow service operation. Field tests may store pending threshold
estimates with `zone_status=pending_protocol`; submaximal protocols may store
provisional or RPE-only outcomes but never thresholds. These records are not
active zone versions.

## Athlete context

### `injury_restrictions`

Represents athlete-reported injury context by discipline.

Implemented Phase 8 fields:

- `athlete_id`, `discipline`;
- functional restriction status and allowed intensity;
- reported source;
- start and mandatory seven-day review timestamps;
- confirmation timestamp;
- optional attributable professional advice and its timestamp;
- explicit athlete plan choice (`keep_blocked`, `train_low_only`, or
  `resume_unrestricted`);
- cleared timestamp.

Start23 uses functional restriction status and allowed intensity, not diagnosis
or severity. The locked Phase 8 model is documented in the Phase 0-7 decision
register. A restriction is reviewed after seven days and never silently
cleared; automatic load redistribution is disabled.

### Check-in availability

Phase 8 snapshots blocked local dates inside a revisioned
`weekly_checkin_contexts.payload`. It deterministically derives availability
only for the requested athlete-local Monday-Sunday week. Strenuous planned
outside activities remove their local date from generated availability. Plan
revisions retain the exact derived window snapshot.

### Temporary athlete state

Confirmed check-in context stores fatigue, missed-workout reasons, blocked
dates, outside sport, and restrictions. Every version records source
`structured_form`, a fingerprint, and expiry at the end of its local week so
temporary context does not persist indefinitely.

## Workout catalog

### `workout_templates`

Immutable versioned catalog item. A stable `template_key` groups versions and
the highest version is current; published versions are never updated in place.

Proposed fields:

- discipline;
- name and instructions;
- duration and optional distance;
- intensity bucket;
- expected RPE minimum and maximum;
- training phase tags;
- required zone metrics;
- fallback compatibility;
- stable template key and positive version;
- server-internal precomputed planned TSS.

The public template structure is stored separately from
`private.workout_template_loads`. Authenticated athlete roles have read-only
access to the public tables and no access to the private schema. Public workout
representations omit the planned TSS field. A service-role-only RPC returns the
complete durable representation to the restricted backend planning repository;
the service role has no direct private-table access.

### `workout_segments`

Ordered workout instructions with positive duration, optional distance, zone
target, expected RPE, and technique metadata. Segment durations and distances
must reconcile to their immutable template version.

### `workout_tags`

Phase 5 implements normalized training-phase and zone-requirement tags plus an
explicit fallback-compatibility value. Broader goal, equipment, test, and
injury tags remain later catalog extensions.

## Plans and schedules

### `weekly_plans`

Stable identity for an athlete and ISO-like training week.

Proposed fields:

- `id`, `athlete_id`, `week_start`;
- active revision;
- lifecycle state;
- user timezone;
- timestamps.

A unique constraint prevents multiple stable weekly plans for the same athlete
and week. The active revision is a deferred composite foreign key.

### `plan_revisions`

Versioned content of a weekly plan. Phase, target basis, optional taper period,
input/generation fingerprints, check-in identity, confirmed blocked and
low-only disciplines, and availability are snapshotted with the revision.
Hidden target and planned load are stored in `private.plan_revision_loads`.

Proposed states:

- `draft`;
- `pending_approval`;
- `active`;
- `rejected`;
- `superseded`;
- `expired`.

Every generated critical change produces a new revision. Approval promotes the
revision rather than overwriting the active one in place.

### `planned_workouts`

Belongs to a plan revision and references a versioned workout template.

Proposed fields:

- scheduled start and timezone;
- discipline and presentation snapshot;
- expected duration, distance, zones, and RPE;
- status;
- source: athlete-selected, auto-planned, imported, or system-adjusted;
- server-internal planned TSS snapshot.

The snapshot protects historical plans from later catalog edits. Hidden load
is stored separately in `private.planned_workout_loads`; public planned-workout
rows contain no TSS column.

### `plan_warnings`

Records rule validation results such as:

- volume overshoot;
- intensity-ratio deviation;
- anti-stack violation;
- injury conflict;
- unavailable-day conflict;
- stale zones.

Warnings include a BR code, severity, affected object, and public qualitative
message. They do not include TSS.

## Activity execution

### `activities`

Canonical completed activity. Phase 7 persists:

- `id`, `athlete_id`;
- optional `planned_workout_id`; a Phase 8 planned outside activity links to
  its canonical completion from `planned_external_activities`;
- canonical source and athlete-scoped idempotency key/fingerprint;
- discipline;
- start time and timezone;
- duration, distance, and elevation;
- RPE and RPE submission time;
- match status;
- processing state;
- qualitative result/message and an optional pending-correction reference.

An activity may be unmatched. In Phase 7, matching is only an explicit owned,
active `planned_workout_id`; discipline must agree and one planned workout can
be matched only once. Automatic time-proximity, brick, and multisport matching
are deferred. Canonical request fingerprinting prevents duplicate creation.

Server-internal realized TSS is stored separately in
`private.activity_loads`, with no direct Data API grant. It is calculated from
actual RPE and actual duration and is available only to bounded service
operations and the planning engine. RPE can be corrected only during the
activity's athlete-local Monday-Sunday week. `activity_rpe_revisions` stores
the previous/new value and result; after that local week the score is
immutable.

### `activity_metrics`

Stores optional safe summaries such as average/max heart rate, normalized
power, average pace, and low/high intensity minutes. Raw samples and interval
telemetry are not accepted by the Phase 7 canonical-summary contract.

### `activity_files`

Stores private Storage bucket/path, content type, checksum, parser version, and
retention metadata for FIT/TCX or related files.

Phase 9 implements bucket/path, content type, byte size, and SHA-256 metadata
for available Polar FIT files. Parser version and retention metadata remain
pending because the MVP imports the provider's validated summary through
UC-03 and stores the raw file without parsing it.

Per-sample telemetry should remain in compressed private objects unless a
defined query requires normalized PostgreSQL storage. TimescaleDB is explicitly
out of scope.

## Integrations

### `provider_connections`

One connection per athlete/provider. Phase 9 currently permits only the
provisional `polar` provider.

The public owner-scoped record contains provider identity, status, and
connection/import timestamps. Access tokens are held separately in
`private.provider_tokens`, with no Data API table grant, and never enter client
models.

### `webhook_receipts`

Private records retain a SHA-256 event key and payload fingerprint, minimal
provider event identifiers, receipt/processing state, and sanitized failure
code. A provider/event-key uniqueness constraint supplies idempotency after
FastAPI verifies Polar's HMAC and timestamp.

### `import_runs`

Owner-readable records track historical/webhook attempts, the bounded date
window, safe counts, sanitized failure code, and completion state. Private
`provider_activity_imports` maps a provider exercise ID to the canonical
activity and prevents duplicate imports.

## Check-ins and coach

### `weekly_checkins`

One idempotent check-in per athlete/local Monday week, with athlete timezone,
current context revision, lifecycle state, and eventual pending plan proposal.

### `weekly_checkin_contexts`

Immutable revisioned structured-form context. A draft is superseded on edit;
the exact fingerprint must be explicitly confirmed before it can affect a
pending plan. Confirmed versions persist source and expiry.

### `planned_external_activities`

An outside sport confirmed during check-in, with planned local time, duration,
discipline, strenuous/recurring flags, and an optional later canonical
activity completion. Actual duration and RPE live only on that activity.

### `goal_maintenance_states`

An explicit achieved-goal state. While active, deterministic planning holds
load on build weeks, retains the four-build/one-recovery rhythm, and never
applies normal progression.

### `context_candidates`

Reserved for the later constrained-LLM phase. Phase 8 does not use an external
AI provider; its structured form writes `weekly_checkin_contexts` directly and
still requires separate context confirmation.

### `coach_messages`

Stores conversation messages only if retention and consent are approved.
Messages must not expose TSS. Sensitive-data minimization and deletion policy
remain open requirements.

## Proposals and audit

### `change_proposals`

Envelope for a critical pending change.

Proposed fields:

- `id`, `athlete_id`;
- kind: plan revision, zone revision, or validation-test scheduling;
- typed target revision reference;
- base revision;
- state: pending, approved, rejected, expired, applied;
- deterministic reason codes;
- public explanation;
- created, decided, and applied timestamps;
- decision actor;
- ruleset version.

Generic arbitrary mutation JSON should not be executable. A proposal points to a
typed, already validated revision.

### `decision_runs`

Audit record for deterministic evaluation:

- rule-set/version;
- calculation name;
- input snapshot hash;
- non-secret result summary;
- warning and proposal references;
- timestamps.

Whether full inputs can be retained depends on health-data retention policy.

## Internal versus public data

Internal-only examples:

- planned TSS;
- realized TSS;
- physiological debt values;
- raw provider tokens;
- raw telemetry and GPS files;
- rule-engine input snapshots containing hidden values.

Public examples:

- workout duration and distance;
- target zones and RPE;
- intensity distribution percentages based on time;
- qualitative warnings;
- proposal rationale;
- plan and activity status.

Public database views are not a substitute for explicit API response models. If
views are introduced, they must obey RLS and omit hidden fields.

## Open domain decisions

- Concrete versioned BR-009 soft-range records and a complete reviewed Zone
  1-5 model. Phase 8.5 now has official Start23 field-test and submaximal
  calibration protocols, but their threshold formulas do not define percentage
  bands or all pace-rounding rules; calculated boundaries remain fail-closed.
- Automatic activity-to-plan matching rules, including proximity, bricks, and
  multisport activities.
- Non-race macrocycles and goal-specific intensity ratios.
- Retention, deletion, export, and consent requirements for health and GPS data.
- Production approval of provisional Polar AccessLink processing and its
  retention/brand obligations.

Resolved for MVP:

- weekly-plan, proposal, activity, and zone state machines are defined in the
  Phase 0 decision lock;
- orchestration precedence is injury, taper, recovery, debt, progression,
  intensity/anti-stack, then availability;
- validation-test approval never authorizes a later zone update.
- Phase 7 matching is explicit planned-workout selection or unmatched; one
  planned workout can be matched once and the discipline must agree.
- Phase 8 allows auditable RPE correction only during the activity's current
  athlete-local week; identical values remain idempotent and later weeks are
  immutable.
- Exact mixed-workout ties classify as high intensity while exact segment
  minutes remain available for BR-003 arithmetic.
- Athlete UI uses complementary half-up whole percentages plus exact minutes.
- Shared zone boundaries belong to the physiologically more intense zone.
- Cycling speed is bike activity telemetry only, never a zone/planning metric.
- The MVP collects no sex/gender/physiology category and performs no binary FTP
  estimate.
- Functional injury restrictions replace medical severity, and automatic
  injury-load redistribution is disabled.
- canonical zone units are CSS seconds/100 m, FTP watts, threshold heart rate
  BPM, run threshold pace seconds/km, and run LTHR BPM;
- `phase-3-ruleset-1` approves calculation policy for BR-002, BR-003, BR-004,
  BR-006, BR-007, BR-008, and BR-010.
- `phase-3-ruleset-2` historically added BR-009 soft-range review, input
  conversion, contiguous boundaries, and unreviewed Karvonen fallback.
- `phase-3-ruleset-3` records the accepted Phase 0-7 decisions; qualified
  production approval of the active rules and `start23-zone-model-1.0` was
  confirmed complete on 2026-08-24. Changed rules require a new review.
