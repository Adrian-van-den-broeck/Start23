# Start23 MVP Roadmap

## Status

This roadmap tracks small, reviewable implementation phases. Phase 1 is
implemented and locally verified. Phase 2 authentication is verified; its
persistence and hosted RLS slice is intentionally pending. The roadmap assumes
the architecture and safety constraints in `AGENTS.md`.

Related documents:

- [Backend architecture](../architecture/backend-architecture.md)
- [Domain model](../architecture/domain-model.md)
- [API contracts](../architecture/api-contracts.md)
- [Security model](../architecture/security-model.md)
- [Business-rule traceability](../requirements/business-rule-traceability.md)
- [Phase 0 decision lock](../requirements/phase-0-decision-lock.md)
- [Database migration workflow](database-migrations.md)

## MVP outcome

The phase-one MVP should support a narrow, safe, end-to-end loop:

1. an athlete authenticates;
2. completes structured onboarding;
3. configures a primary race-oriented goal and discipline zones;
4. receives a deterministic, TSS-hidden weekly-plan proposal;
5. explicitly approves it;
6. schedules or moves workouts with qualitative warnings;
7. records a completed activity and RPE;
8. receives a pending corrective proposal when deterministic rules require one;
9. completes a structured weekly check-in for the next week.

The LLM and multiple wearable providers are not required to prove this loop.

## Phase 0: decision and requirements lock

### Status

Architecture and state semantics are locked in the Phase 0 decision document.
Physiological formulas for BR-002, BR-003, BR-004, BR-006, BR-007, BR-008, and
BR-010 are approved as `phase-3-ruleset-1`. BR-009 canonical units are known,
but clinical limits, zone-boundary policy, conversion precision, and fallback
formulas remain a hard gate for production zone validation.

### Scope

- Approve rule-precedence order. **Locked**
- Define all physiological formulas, canonical units, rounding, and equality
  boundaries. **Approved for the Phase 3 ruleset except BR-009 and the exact
  BR-003 dominant-category tie**
- Reconcile BR-001 approval with automatic changes described in UC-03.
  **Locked**
- Reconcile soft boundaries with filtering and blocking language. **Locked**
- Define weekly-plan, proposal, zone, and activity state machines. **Locked**
- Decide whether a validation-test approval also authorizes a later zone
  update. **Locked: separate approval**
- Select the phase-one activity input path. **Locked: canonical summary**
- Decide Expo SDK 54 pinning versus SDK 57 upgrade. **Locked: retain SDK 54
  temporarily for App Store Expo Go on a physical iPhone; transition
  incrementally to SDK 57 with a development build before Phase 4 mobile
  implementation**

### Exit criteria

- Reviewed rule decision table.
- Approved formula specification with example fixtures. **Complete for
  ruleset-1; BR-009 remains explicitly excluded**
- Approved public TSS prohibition.
- Approved phase-one provider/import choice.
- No unresolved contradiction that changes database or API state semantics.

## Phase 1: backend foundation

### Status

Implemented and locally verified. A hosted Railway deployment has not yet been
performed.

### Scope

- Establish Python project and FastAPI application.
- Add configuration and secret-loading conventions.
- Add health/readiness endpoints.
- Add formatting, linting, typing, and test configuration.
- Add Railway process definition.
- Add CI without application-domain behavior.

### Exit criteria

- FastAPI starts locally and in a minimal Railway environment.
- Tests run without external services.
- No secrets or `.env` files are committed.

## Phase 2: authentication and data isolation

### Status

In progress. Authentication and token-derived identity are verified. The
profile migration is applied to hosted Supabase, and its grants, RLS policies,
trigger, and rollback-only two-athlete isolation behavior are verified.
FastAPI profile persistence and end-to-end tests with two real Auth sessions
remain pending.

### Scope

- Verify Supabase tokens.
- Derive athlete identity from the token.
- Create profile persistence. **Database schema complete; FastAPI repository
  and endpoints pending**
- Define migration workflow. **Complete**
- Add RLS to user-owned tables. **Complete for `athlete_profiles`**
- Add cross-athlete integration tests. **SQL isolation verified; real-token
  FastAPI/Data API tests pending**

### Exit criteria

- Two test users cannot access one another's records.
- Invalid/expired tokens are rejected.
- No endpoint accepts an authoritative client `user_id`.
- Database access approach for RLS and atomic transactions is proven.

## Phase 3: deterministic physiology core

### Status

In progress. The pure Python calculation layer for BR-002, BR-003, BR-004,
BR-006, BR-007, BR-008, and BR-010 is implemented and verified under
`phase-3-ruleset-1`. BR-009 canonical metric and boundary structures are
implemented, but production clinical validation remains fail-closed because
its numeric limits and policy are not approved.

### Scope

Implement pure Python value objects and approved portions of:

- BR-002 volume/intensity debt;
- BR-003 time-based intensity buckets;
- BR-004 progressive load and approved fallback;
- BR-006 anti-stack intervals;
- BR-007 recovery-week calculation;
- BR-008 A-race taper calculation;
- BR-009 zone value validation (structural only until clinical approval);
- BR-010 injury redistribution.

BR-001 and BR-005 are enforced by application and API layers but receive their
own tests.

### Exit criteria

- Every included formula has example, boundary, and invalid-input tests.
- No physiology function imports FastAPI, a database package, or an LLM client.
- Rule precedence is covered by tests.
- Rule-set versions can be recorded with decisions.

### Implemented groundwork

- Framework-independent `physiology` module.
- Locked Phase 0 precedence ordering and highest-priority conflict selection.
- Versioned decision-run records.
- Draft specifications cannot activate any physiological rule.
- Internal load values reject invalid input and are hidden from object
  representations.
- Purity test forbids FastAPI, database, Supabase, and LLM imports.
- TSS-free dashboard/proposal design preview. The source still declares Expo
  SDK 54, so the locked SDK 57 upgrade remains pending before further mobile
  implementation.
- Strict-above-110% volume debt and discipline-specific intensity debt.
- Duration-based low/high classification with dominant-workout allocation.
- Available weekly-sample 42-day baseline, progression, and expected-RPE
  snapshot.
- Same-discipline 72/48-hour anti-stack validation using absolute instants.
- Forward and retrospective recovery cycles with taper precedence.
- A/B/C taper targets, athlete-local weeks, and race-priority overlap handling.
- Fail-closed zone validation scaffolding with canonical units.
- Confirmed-injury 80% proportional redistribution calculation.
- Example, equality, invalid-input, missing-data, DST, purity, and precedence
  tests.

### Remaining Phase 3 decisions

- Approve BR-009 numeric clinical ranges, exact zone boundaries, equality
  ownership, input conversions, stored precision, and fallback formulas.
- Define which category owns an exact low/high duration tie in a mixed workout;
  the current implementation fails closed.
- Confirm the formal clinical-review role for the supplied rule evidence.

## Phase 3.5: Expo development-build transition

### Status

Pending. The mobile project remains on Expo SDK 54 so the current design
preview can run in the App Store version of Expo Go on a physical iPhone.

This phase does not block Phase 3 backend work. It is a gate before Phase 4
mobile implementation. Phase 4 backend work may proceed independently.

### Scope

- Continue using SDK 54 and Expo Go only for the current UI prototype and basic
  API experiments.
- Choose the iOS development-build route:
  - EAS development build for a physical iPhone with Apple signing; or
  - wait until the App Store Expo Go version supports the target SDK.
- Add `expo-dev-client` when the development-build route is available.
- Upgrade Expo incrementally from SDK 54 to 55, 56, and then 57.
- At every upgrade step:
  - align Expo, React, React Native, and Expo-managed package versions;
  - run Expo's dependency repair and diagnostics;
  - run strict TypeScript compilation;
  - launch the application and verify the existing design preview.
- Create and install the SDK 57 iOS development build.
- Verify that the development build connects to the local Metro server and can
  call the configured backend without exposing privileged credentials.
- Stop using Expo Go as the primary Start23 development runtime after this
  transition.

### Exit criteria

- `mobile/package.json` and the resolved Expo configuration report SDK 57.
- Expo dependency diagnostics pass.
- Strict TypeScript compilation passes.
- The SDK 57 development build is installed and launches on the physical
  iPhone.
- Local Metro updates load in the development build.
- The existing TSS-free design preview renders correctly.
- No service-role key, database password, or backend secret is present in the
  mobile bundle.

### Contingency

If an iOS development build cannot yet be installed, keep the mobile project
on SDK 54 and continue backend work. Do not partially upgrade the project to an
SDK that the available iPhone runtime cannot open.

## Phase 4: onboarding, goals, and zones

### Scope

- Begin mobile implementation only after the Phase 3.5 exit criteria pass.
- Athlete profile and biometrics.
- Triathlon-discipline training history.
- One primary race-oriented A goal.
- Manual discipline-specific zones.
- Approved fallback-zone path clearly marked unvalidated.
- Resumable onboarding state.
- Initial plan proposal trigger.

### Exit criteria

- Onboarding validates all required inputs.
- One active zone version per discipline.
- Generated zone changes cannot bypass proposal approval.
- Public responses contain no TSS.

## Phase 5: workout catalog

### Scope

- Versioned swim, bike, and run templates.
- Workout segments, duration/distance, zones, and expected RPE.
- Low/high intensity classification.
- Training-phase and fallback compatibility tags.
- Server-internal precomputed planned TSS.
- Small reviewed seed set, not 500+ workouts.

### Exit criteria

- Catalog validation rejects incomplete or inconsistent templates.
- Public workout models omit planned TSS.
- Historical planned-workout snapshots remain stable after catalog versioning.

## Phase 6: weekly planning and approval

### Scope

- Weekly-plan and revision persistence.
- Deterministic target and recovery/taper context.
- Workout-deck selection.
- Auto-schedule proposal.
- Anti-stack and soft-boundary warnings.
- Structured availability and injury exclusion.
- Pending proposal approval/rejection.
- Public calendar response.

### Exit criteria

- System-generated plan changes remain pending.
- Approval is atomic, owner-scoped, and stale-safe.
- Manual schedule behavior follows the Phase 0 decision.
- All plan/calendar responses pass the TSS-leak contract tests.

## Phase 7: activity and RPE feedback

### Scope

- Implement the selected phase-one activity input.
- Canonical activity and metric persistence.
- Planned-workout matching for the supported scope.
- Internal realized-load calculation.
- RPE submission.
- Match-matrix classification.
- Pending correction proposal after qualifying outcomes.

### Exit criteria

- Duplicate activity imports are idempotent.
- Supported calculations are deterministic and tested.
- Unmatched and invalid activities are handled safely.
- Public activity responses and messages omit realized and planned TSS.
- No correction is applied without approval.

## Phase 8: structured weekly check-in

### Scope

- Blocked days.
- Confirmed injury disciplines.
- Fatigue and missed-workout reasons.
- Next-week plan proposal.
- No natural-language LLM dependency.

### Exit criteria

- Confirmed context has source and expiry.
- Injury and availability affect only pending plan revisions.
- Check-in can be completed without an external AI provider.

## Phase 9: one wearable integration

### Scope

- One approved provider.
- OAuth/token lifecycle.
- Webhook verification and idempotency.
- Historical import limited to approved range.
- Private activity-file storage.
- Provider-specific contract fixtures.

### Exit criteria

- Disconnect/revocation behavior is tested.
- Invalid/replayed webhooks are rejected.
- Imported activities use the same canonical UC-03 path.
- Provider failure does not corrupt plan or activity state.

## Phase 10: constrained LLM coach

### Scope

- Structured context extraction.
- Clarifying questions.
- Explanation of deterministic recommendations.
- Confirmation UI bound to a specific proposal.

### Exit criteria

- LLM output cannot invoke plan or zone mutation.
- Extracted context is schema-validated.
- Required context is confirmed before critical effects.
- Prompts and responses contain no TSS.
- Privacy and retention configuration is approved.

## Phase 11: zone progress evaluation

### Scope

- Implement UC-05 only after statistical thresholds are approved.
- Produce validation-test or zone-update proposals.
- Reuse existing activity and approval workflows.

### Exit criteria

- Minimum sample and data-quality requirements are tested.
- Outlier behavior is deterministic.
- No zone is changed without the approved confirmation sequence.

## Phase-one MVP inclusion

Included:

- authentication and RLS;
- structured onboarding;
- one primary race-oriented goal;
- swim/bike/run history;
- manual and approved fallback zone configuration;
- small curated workout catalog;
- deterministic planning rules required for the selected scope;
- pending plan revision and approval;
- calendar and athlete rescheduling;
- qualitative rule warnings;
- selected activity input;
- RPE and limited feedback loop;
- structured weekly check-in;
- TSS privacy and security tests.

## Explicitly deferred

- Multiple wearable integrations.
- Full Garmin, Strava, and Apple Health parity.
- Automatic UC-05 zone upgrades.
- LLM-led onboarding or unrestricted coaching.
- Gamification, XP, and Pacing Points.
- 500+ workout catalog.
- Other-sport load modelling.
- Weight-loss, muscle-gain, and general-fitness plan generation.
- Fasted-training recommendations.
- Advanced swimrun redistribution.
- Rich GPS maps and telemetry analytics.
- Push notifications and background mobile synchronization.
- Social, coach, team, and admin features.
- Microservices, Redis, Celery, TimescaleDB, and Kubernetes.

## Cross-phase quality gates

Every phase must:

- preserve strict module boundaries;
- add tests proportional to new risk;
- include migrations without executing production changes automatically;
- maintain RLS on user-owned tables;
- exclude TSS from all public response models;
- keep critical system changes pending;
- document new decisions and update traceability;
- avoid unrelated mobile or backend changes.

## Current status

- Phase 0 architecture/state decisions: `locked`
- Phase 0 physiological specification: `ruleset-1 approved except BR-009`
- Phase 1 backend foundation: `implemented; locally verified`
- Phase 2 authentication: `verified`
- Phase 2 persistence and hosted RLS: `hosted schema/RLS verified; FastAPI
  persistence and real-token integration pending`
- Phase 3 deterministic core: `ruleset-1 calculations verified; BR-009
  clinical validation blocked`
- Phase 3.5 mobile development-build transition: `pending; SDK 54 retained for
  physical-iPhone Expo Go until the SDK 57 development build is available`
- Phase 4 through 11: `not started`

## Unresolved roadmap decisions

- BR-009 clinical limits and policy remain a hard gate before zone-validation
  activation.
- The SDK 57 transition depends on an installable iOS development build or a
  compatible App Store Expo Go release. Until then, SDK 54 is the intentional
  physical-iPhone development version.
- The phase-one activity input is a canonical authenticated summary; the first
  wearable provider for Phase 9 remains unresolved.
- Non-race goals require separate deterministic rules before entering scope.
- Injury redistribution requires clinical and product-policy review.
