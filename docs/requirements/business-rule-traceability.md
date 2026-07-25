# Business Rule Traceability

## Status and purpose

This document maps BR-001 through BR-010 to the modular-monolith
implementation. Foundation, authentication, and the Phase 3 pure calculation
layer exist. Business persistence and athlete-facing rule APIs do not yet
exist.

Status vocabulary:

- `Not implemented`: documented only; no application code exists.
- `In progress`: implementation has started but acceptance criteria are not met.
- `Implemented`: code and migrations exist.
- `Verified`: implemented and required tests pass.

BR-002, BR-003, BR-004, BR-006, BR-007, BR-008, BR-009, and BR-010 are `In
progress`: their Phase 3 calculation or validation structures exist, but
application, persistence, and public-contract acceptance criteria are not met.
BR-001 and BR-005 remain `Not implemented` until their application, database,
and contract-test requirements exist. Domain paths written as `/v1/...` are
historical shorthand for the authoritative `/api/v1/...` base path.

Related documents:

- [Backend architecture](../architecture/backend-architecture.md)
- [Domain model](../architecture/domain-model.md)
- [API contracts](../architecture/api-contracts.md)
- [Security model](../architecture/security-model.md)
- [MVP roadmap](../implementation/mvp-roadmap.md)
- [Physiological formula specification](physiology-formula-specification.md)

## Shared Phase 3 calculation layer

Status: `Verified` for the isolated calculation scope

The framework-independent `physiology` module provides stable BR identifiers,
server-internal load values, versioned specification records, fail-closed
approval checks, the locked Phase 0 precedence order, and ruleset-1
calculations. Architecture tests prevent FastAPI, database, Supabase, and LLM
imports. Rule tests cover examples, equality boundaries, invalid input,
missing data, timezones, and DST.

This does not implement application orchestration, persistence, plan
proposals, or athlete-facing responses. The per-rule status therefore remains
`In progress`, not `Verified`.

## Summary matrix

| Rule | Primary module | Current status |
|---|---|---|
| BR-001 Full autonomy | `proposals` | Not implemented |
| BR-002 Soft boundaries | `physiology`, `planning` | In progress |
| BR-003 80/20 principle | `physiology`, `goals` | In progress |
| BR-004 10% progression | `physiology`, `planning` | In progress |
| BR-005 Hidden TSS | `api`, `planning`, `activities` | Not implemented |
| BR-006 Anti-stack | `physiology`, `planning` | In progress |
| BR-007 4+1 mesocycle | `physiology`, `goals`, `planning` | In progress |
| BR-008 Tapering | `physiology`, `goals`, `planning` | In progress |
| BR-009 Discipline zones | `zones`, `physiology` | In progress, fail-closed |
| BR-010 Injury redistribution | `checkins`, `physiology`, `planning` | In progress |

## BR-001: Full autonomy

### Responsible backend modules

- Primary: `proposals`
- Supporting: `planning`, `zones`, `checkins`, `coach`

### Database entities

- `change_proposals`
- `weekly_plans`
- `plan_revisions`
- `planned_workouts`
- `zone_profile_versions`
- `decision_runs`

### API operations

- `POST /v1/weekly-plans/proposals`
- `POST /v1/weekly-plans/{plan_id}/schedule-proposals`
- `POST /v1/checkins/{checkin_id}/plan-proposals`
- `GET /v1/change-proposals`
- `GET /v1/change-proposals/{proposal_id}`
- `POST /v1/change-proposals/{proposal_id}/approve`
- `POST /v1/change-proposals/{proposal_id}/reject`
- Zone/test proposal operations through the same approval API

### Required validations

- Proposal belongs to the authenticated athlete.
- Proposal state is pending.
- Typed target revision is valid and complete.
- Expected base revision matches the current active revision.
- Proposal has not expired, been rejected, or already been applied.
- Approval is explicit and bound to one visible proposal.
- LLM output alone cannot authorize approval.
- Apply transaction promotes the revision and records the decision atomically.

### Required unit tests

- Generated plan change remains pending.
- Generated zone change remains pending.
- Approval applies the exact target revision.
- Rejection leaves the active target unchanged.
- Duplicate approval is idempotent or returns the defined conflict.
- Stale proposal cannot overwrite a newer revision.
- Another athlete cannot approve the proposal.
- Expired proposal cannot be applied.
- LLM/context candidate cannot invoke the apply path.
- Transaction failure leaves proposal and active target consistent.

### Current implementation status

`Not implemented`

Open decision: whether an explicit drag-and-drop calendar edit applies directly
with warnings or is represented as a user-authored revision.

## BR-002: Soft boundaries

### Responsible backend modules

- Primary: `physiology`, `planning`
- Supporting: `activities`, `proposals`

### Database entities

- `weekly_plans`
- `plan_revisions`
- `plan_warnings`
- `planned_workouts`
- `activities`
- `decision_runs`
- `change_proposals`

### API operations

- `POST /v1/weekly-plans/{plan_id}/validate`
- `PATCH /v1/planned-workouts/{workout_id}`
- `GET /v1/weekly-plans/{plan_id}`
- `GET /v1/calendar`
- Activity processing through UC-03
- Proposal approve/reject operations

### Required validations

- Calculate volume overshoot using approved thresholds and equality behavior.
- Calculate intensity deviation using time, not TSS.
- Record qualitative warnings without blocking an authorized athlete edit.
- Store internal physiological debt without returning its TSS value.
- Apply the approved minimum/floor and negative-result handling.
- Use explicit rule precedence for recovery, taper, injury, and debt.
- Generated compensating changes remain pending under BR-001.

### Required unit tests

- No overshoot below the approved threshold.
- Exact-threshold behavior.
- Overshoot above the threshold.
- Example 600 planned/680 realized produces the approved internal result.
- Intensity-debt examples produce 90/10 and floor behavior as specified.
- Injury exception permits the approved zero-high-intensity behavior.
- Negative and extreme debt inputs are safely bounded.
- Warning does not reject an explicit user edit.
- Corrective plan is a proposal rather than an active mutation.
- Public warning contains no TSS.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/debt.py`: strict-above-110%
activation, exact-threshold behavior, next-week debt, the 600/680 fixture,
planned-load projection, 5% intensity floor, injured-discipline zero exception,
and non-exceptional zero/negative-target review. Phase 6 still must persist
internal debt, place the correction, enforce rest-day scheduling, create a
pending revision, and expose only qualitative warnings.

## BR-003: 80/20 principle

### Responsible backend modules

- Primary: `physiology`, `goals`
- Supporting: `workouts`, `planning`

### Database entities

- `goals`
- `workout_templates`
- `workout_segments`
- `weekly_plans`
- `plan_revisions`
- `planned_workouts`
- `plan_warnings`
- `decision_runs`

### API operations

- `POST /v1/me/goals`
- `PUT /v1/me/goals/{goal_id}`
- `POST /v1/weekly-plans/proposals`
- `GET /v1/weekly-plans/{plan_id}/deck`
- `POST /v1/weekly-plans/{plan_id}/validate`
- `GET /v1/weekly-plans/{plan_id}`

### Required validations

- Classify Zone 1/2 and swim technique as low intensity.
- Classify Zone 3/4/5 as high intensity.
- Calculate the ratio from duration in minutes.
- Select only an approved deterministic goal-specific target ratio.
- Validate that every workout template has a valid bucket.
- Define handling for mixed-zone workouts and partial segments.
- Keep ratio corrections distinct from TSS volume calculations.

### Required unit tests

- Low/high classification for all supported zones.
- Swim-technique classification.
- Mixed-segment duration allocation.
- Standard 80/20 target.
- Deferred non-race 90/10 and swimrun 75/25 targets are not activated.
- Empty-week and zero-duration behavior.
- Rounding while preserving total minutes.
- Ratio warning boundaries.
- Workout-deck filtering uses remaining time bucket correctly.
- No TSS is needed or returned to display the time ratio.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/intensity.py`: all zone buckets,
swim technique, standard 80/20 target, dominant-workout allocation,
duration-based weekly ratios, empty-week `not_evaluated`, and the
strictly-above-30% intensive-duration warning. Exact dominant-duration ties
fail closed pending policy. Athlete-facing percentage precision and deck
integration remain pending.

## BR-004: 10% progressive load and predefined planned TSS

### Responsible backend modules

- Primary: `physiology`, `planning`
- Supporting: `workouts`, `activities`

### Database entities

- `workout_templates`
- `planned_workouts`
- `weekly_plans`
- `activities`
- `activity_metrics`
- `decision_runs`
- `plan_warnings`

### API operations

- `POST /v1/weekly-plans/proposals`
- `POST /v1/weekly-plans/{plan_id}/validate`
- Activity import and processing operations
- `GET /v1/weekly-plans/{plan_id}` with public fields only

### Required validations

- Workout templates contain a valid server-internal planned TSS.
- Planned-workout snapshots preserve the applicable template value.
- Overshoot uses the prior planned load as the growth anchor.
- Regular/light-undershoot behavior follows approved boundaries.
- Heavy-undershoot fallback uses one approved CTL/baseline formula.
- Missing history and inactive weeks have defined behavior.
- Growth, precision, clamping, and rounding are deterministic.
- BR-002 debt is applied in the approved order.

### Required unit tests

- Prior planned load multiplied by 1.10 for approved regular scenarios.
- Overshoot remains anchored to planned rather than realized load.
- Exact 80% and 100% boundary behavior.
- Heavy undershoot invokes the approved fallback.
- Zero prior load and no-history behavior.
- Four-active-week or 42-day fixture, depending on the approved decision.
- Debt applied before/after other rules according to precedence.
- Template version change does not alter historical planned-workout TSS.
- Public plan and workout responses omit TSS.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/progression.py`: exact 80%
regular-growth boundary, planned-load anchor, available-sample 42-day
weekly arithmetic mean, explicit-zero-week inclusion, missing-week exclusion,
no-history failure, and expected-RPE-times-hours snapshots. Template persistence,
historical snapshots, decision orchestration, and public TSS contract coverage
remain for later phases.

## BR-005: Hidden TSS

### Responsible backend modules

- Primary: `api`, `planning`, `activities`
- Supporting: `workouts`, `coach`, `security`

### Database entities

- `workout_templates`
- `weekly_plans`
- `planned_workouts`
- `activities`
- `decision_runs`
- server-only load records or columns

### API operations

- Every client-facing operation
- In particular:
  - `GET /v1/weekly-plans/{plan_id}`
  - `GET /v1/weekly-plans/{plan_id}/deck`
  - `GET /v1/calendar`
  - `GET /v1/activities`
  - `GET /v1/activities/{activity_id}`
  - check-in/coach message operations
  - proposal reads and warnings

### Required validations

- Public Pydantic models contain no planned/realized TSS field or alias.
- ORM/internal models are never returned directly.
- Client-visible errors and warnings contain no TSS.
- LLM prompts intended to produce user text receive qualitative outcomes only.
- Exports, notifications, and observability capture follow the same boundary.
- Direct authenticated database access cannot read hidden load columns.

### Required unit tests

- Recursive forbidden-key test across every public response.
- OpenAPI schema contains no forbidden TSS property.
- Plan, deck, calendar, activity, proposal, and check-in contract snapshots.
- Error and warning serialization contains no TSS.
- LLM explanation input/output contains no TSS.
- Public database role cannot select hidden load data.
- No camelCase, abbreviation, or alias bypass such as `pTSS` or `rTSS`.

### Current implementation status

`Not implemented`

Open decision: whether a tightly controlled internal staff tool may ever
display TSS. The current safe default is no user-facing exposure.

## BR-006: Anti-stack rule

### Responsible backend modules

- Primary: `physiology`, `planning`
- Supporting: `workouts`

### Database entities

- `workout_templates`
- `plan_revisions`
- `planned_workouts`
- `plan_warnings`
- `decision_runs`

### API operations

- `POST /v1/weekly-plans/{plan_id}/schedule-proposals`
- `POST /v1/weekly-plans/{plan_id}/validate`
- `PATCH /v1/planned-workouts/{workout_id}`
- `GET /v1/weekly-plans/{plan_id}`
- `GET /v1/calendar`

### Required validations

- Identify high-intensity workouts by BR-003 classification.
- Enforce at least 72 hours between high-intensity run workouts in generated
  schedules.
- Enforce at least 48 hours between high-intensity bike workouts.
- Enforce at least 48 hours between high-intensity swim workouts.
- Define cross-discipline behavior and exact timestamp semantics.
- Manual athlete violations create warnings rather than silent rejection if
  soft-boundary interpretation is approved.
- Timezone and daylight-saving transitions are handled.

### Required unit tests

- Run workouts at 71:59, 72:00, and above.
- Bike/swim workouts at 47:59, 48:00, and above.
- Low-intensity workouts do not trigger the rule.
- Different-discipline combinations follow the approved policy.
- Week-boundary and daylight-saving cases.
- Generated scheduler chooses valid placements.
- Manual violation returns `anti_stack_violation`.
- Warning contains no hidden load.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/anti_stack.py`: same-discipline
start-to-start elapsed intervals, exact 72/48-hour boundaries, brick
participation, low-intensity exclusion, timezone-aware input, and absolute-time
DST handling. Phase 6 must reuse it for deck filtering, scheduler constraints,
and non-blocking manual-move warnings.

## BR-007: 4+1 mesocycle

### Responsible backend modules

- Primary: `physiology`, `goals`, `planning`

### Database entities

- `goals`
- `macrocycles`
- `mesocycles`
- `weekly_plans`
- `plan_revisions`
- `decision_runs`

### API operations

- `POST /v1/onboarding/complete`
- `POST /v1/weekly-plans/proposals`
- `GET /v1/weekly-plans/{plan_id}`
- Proposal approve/reject operations

### Required validations

- Mesocycle weeks 1 through 4 are build weeks.
- Week 5 is marked as a recovery-week proposal.
- Approved recovery target uses 60% of week 4 planned load.
- Week 4 planned rather than realized load is the anchor.
- Partial macrocycles and race alignment follow a defined algorithm.
- A recovery proposal does not overwrite an active plan without approval.
- Rule precedence with taper, injury, and debt is explicit.

### Required unit tests

- Correct week numbering across multiple mesocycles.
- Week 5 recovery flag.
- Week 4 planned load × 0.60.
- Week 4 realized overshoot does not change the anchor.
- Partial block before a race.
- Recovery coinciding with taper or injury.
- Calendar/year boundary.
- Recovery plan remains pending until approved.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/recovery.py`: forward 4+1 cycles,
the supplied eight-week retrospective fixture, taper override, default 60%
target, and allowed 40%-60% constrained factor. Phase 6 must supply a valid
week-4 snapshot, apply higher-precedence constraints, schedule at most three
consecutive rest days, and keep generated revisions pending.

## BR-008: Tapering

### Responsible backend modules

- Primary: `physiology`, `goals`, `planning`

### Database entities

- `goals`
- `race_events`
- `macrocycles`
- `mesocycles`
- `weekly_plans`
- `plan_revisions`
- `planned_workouts`
- `decision_runs`

### API operations

- `POST /v1/me/goals`
- `PUT /v1/me/goals/{goal_id}`
- `POST /v1/weekly-plans/proposals`
- `POST /v1/weekly-plans/{plan_id}/validate`
- Proposal approve/reject operations

### Required validations

- A-race T-2 target is 60% of the approved average build load.
- A-race T-1 target is 35% of the approved average build load.
- A-race intensity-time target remains as approved while workouts shorten.
- B-race uses a full taper week at 50% of the approved 42-day baseline.
- C-race is classified as the regular high-intensity stimulus.
- Race date, priority, timezone, and discipline profile are valid.
- Taper precedence over recovery, debt, and injury is defined.

### Required unit tests

- A-race T-2 and T-1 calculations.
- Definition of average build load with missing weeks.
- Race-week date and timezone boundaries.
- B-race full-week 50% target.
- C-race no-taper classification.
- Multiple races in overlapping windows.
- Taper plan remains a pending revision.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/taper.py`: available 42-day
build-only baseline, A-race 60%/35%, B-race full-week 50%, C-race no taper,
Monday-Sunday athlete-local weeks, goal-priority overlap, and taper-over-
recovery precedence. Phase 6 must persist race/load history, account for race
load internally without exposing TSS, and create pending taper revisions.

## BR-009: Discipline-specific zone management

### Responsible backend modules

- Primary: `zones`, `physiology`
- Supporting: `onboarding`, `activities`, `proposals`

### Database entities

- `zone_profile_versions`
- `zone_metrics`
- `change_proposals`
- `decision_runs`
- `activity_metrics`

### API operations

- `PUT /v1/me/zones/swim`
- `PUT /v1/me/zones/bike`
- `PUT /v1/me/zones/run`
- `GET /v1/change-proposals?kind=zone_update`
- Proposal approve/reject operations
- Activity/test processing through UC-03

### Required validations

- Swim CSS uses canonical seconds per 100 metres.
- Cycling FTP uses watts and cycling threshold heart rate uses BPM.
- Running threshold pace and LTHR use canonical units.
- Discipline-specific required fields cannot be mixed.
- Manual, test, and fallback setup methods are explicit.
- Numeric ranges and zone ordering are physiologically reviewed.
- Only one active version exists per athlete/discipline.
- Generated updates remain pending.

### Required unit tests

- Valid/invalid CSS.
- Valid/invalid FTP and threshold heart rate.
- Valid/invalid run threshold pace and LTHR.
- Unit conversion and rounding.
- Zone boundary ordering.
- Manual setup produces the approved active/pending behavior.
- Fallback profile remains flagged unvalidated.
- Generated zone revision does not replace the active version.
- Approval supersedes the prior version atomically.
- Cross-athlete access is rejected.

### Current implementation status

`In progress, fail-closed`

Implemented in `physiology/zones.py`: canonical metric kinds, discipline
matching, positive finite values, explicit clinical-range structures, complete
Zones 1-5 ordering, overlap checks, and missing-limit errors. Tests prove the
production ruleset cannot activate BR-009. Numeric ranges, endpoint ownership,
input conversion, stored precision, fallback formulas/inputs, and calculated
replacement approval remain blocking.

## BR-010: Injury rules and redistribution

### Responsible backend modules

- Primary: `checkins`, `physiology`, `planning`
- Supporting: `proposals`, `coach`, `zones`

### Database entities

- `injuries`
- `athlete_state`
- `weekly_checkins`
- `context_candidates`
- `weekly_plans`
- `plan_revisions`
- `planned_workouts`
- `change_proposals`
- `decision_runs`

### API operations

- `PUT /v1/checkins/{checkin_id}/context`
- `POST /v1/checkins/{checkin_id}/messages`
- `POST /v1/checkins/{checkin_id}/context-confirmation`
- `POST /v1/checkins/{checkin_id}/plan-proposals`
- `POST /v1/weekly-plans/{plan_id}/validate`
- Proposal approve/reject operations

### Required validations

- Injury discipline and state are confirmed.
- All affected-discipline workouts are removed from the proposed current/next
  week scope.
- Redistribution uses the approved 0.8 coefficient.
- Remaining disciplines and capacity are valid.
- Multiple or all-discipline injuries have safe defined behavior.
- Injury can expire or be explicitly cleared.
- High-intensity floor exception follows the approved interpretation.
- LLM extraction creates a candidate, not an active injury or plan mutation.
- Generated plan revision remains pending.

### Required unit tests

- Single run injury removes run workouts from proposed scope.
- Bike and swim injury variants.
- Redistributed internal load uses coefficient 0.8.
- No remaining discipline results in no redistribution.
- Multiple injuries follow the approved safe policy.
- Injury plus recovery/taper/debt precedence.
- Injury start/end date boundaries.
- Unconfirmed LLM candidate has no planning effect.
- Confirmed injury creates a pending revision.
- Rejection leaves the existing plan active.
- Public proposal explanation contains no TSS.

### Current implementation status

`In progress`

Implemented and unit-tested in `physiology/injury.py`: confirmed-context gate,
fixed 0.80 coefficient, proportional existing-share allocation, one remaining
discipline, all-discipline rest, and ambiguous zero-share review. The function
has no side effects and returns a calculation for a later pending revision.
Phase 8 must define and persist severity/state, scope, expiry, intensity-only
restrictions, explicit clearance, and proposal lifecycle.

## Traceability maintenance

This document must be updated in the same change whenever:

- a business rule is clarified or changed;
- a responsible module changes;
- a table or endpoint is renamed;
- an implementation phase starts or completes;
- a required validation or test is added or removed;
- a rule receives a versioned formula specification.

No rule may be marked `Verified` until its implementation, database behavior,
API contracts, and required tests all agree.
