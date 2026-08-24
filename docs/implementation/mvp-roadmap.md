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
- [Backend zone calculation and calibration](backend-zone-calculation.md)
- [Phase 8.5 and 9 business decision brief](phase-8-5-and-9-business-decisions.md)

## MVP outcome

The phase-one MVP should support a narrow, safe, end-to-end loop:

1. an athlete authenticates;
2. completes structured onboarding;
3. configures a primary race-oriented goal and, per discipline, enters known
   zones, follows a reviewed estimation route, or explicitly continues with
   RPE guidance while zones are unknown;
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
BR-010 are approved as `phase-3-ruleset-1`. BR-009 follow-up evidence adds
soft-range review, input conversion, boundary ownership, and unvalidated
Karvonen fallback in `phase-3-ruleset-2`. The twelve decisions accepted on
2026-08-11 are implemented in `phase-3-ruleset-3`. Amendments accepted on
2026-08-13 are recorded in the Phase 0-7 decision register but are not part of
ruleset 3 until explicitly implemented and tested. The separate Zone 1-5
conversion model from `Voorstel Start23 Zone 1-5 rekenmodel v1.0` is implemented
as `start23-zone-model-1.0` on 2026-08-24. On the same date, the product owner
confirmed completion of qualified physiological production review for the
active rules and zone model; reviewer identity and evidence remain in the
external product-governance record. Material rule changes reopen that gate.

### Scope

- Approve rule-precedence order. **Locked**
- Define all physiological formulas, canonical units, rounding, and equality
  boundaries. **Approved for ruleset 3; exact BR-003 ties are high intensity**
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
  ruleset 3; production use remains review-gated**
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

Implemented and verified for the pure calculation scope. BR-002, BR-003,
BR-004, BR-006, BR-007, BR-008, BR-009, and BR-010 run under
`phase-3-ruleset-3`. Persistence, plan/zone proposals, and athlete-facing APIs
belong to later phases.

### Scope

Implement pure Python value objects and approved portions of:

- BR-002 volume/intensity debt;
- BR-003 time-based intensity buckets;
- BR-004 progressive load and approved fallback;
- BR-006 anti-stack intervals;
- BR-007 recovery-week calculation;
- BR-008 A-race taper calculation;
- BR-009 zone value validation and estimated/unreviewed fallback;
- BR-010 functional injury restrictions and zero automatic redistribution.

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
- TSS-free dashboard/proposal design preview; the later Phase 3.5 transition
  upgraded and verified the Android development route on Expo SDK 57.
- Strict-above-110% volume debt and discipline-specific intensity debt.
- Current implementation: duration-based low/high classification with
  dominant-workout allocation. Decision 1 now supersedes this for the full
  catalog: the imported `Emmer (80/20)` value is authoritative for a complete
  training's weekly bucket, while interval zones remain authoritative for
  execution and private TSS.
- Available weekly-sample 42-day baseline, progression, and expected-RPE
  snapshot.
- Same-discipline 72/48-hour anti-stack validation using absolute instants.
- Forward and retrospective recovery cycles with taper precedence.
- A/B/C taper targets, athlete-local weeks, and race-priority overlap handling.
- Canonical discipline-zone value objects and versioned review outcomes.
- Soft-range review without hard rejection, strict pace input conversion,
  higher-intensity boundary ownership, and estimated/unreviewed
  Tanaka/Karvonen fallback. Cycling speed is activity telemetry only.
- Functional injury restrictions, seven-day recheck without auto-clear, and
  zero automatic redistribution. The historical 80% calculation is isolated
  as analytics only.
- Example, equality, invalid-input, missing-data, DST, purity, and precedence
  tests.

### Remaining Phase 3 operational gates

- Supply complete versioned BR-009 soft-range records if product wants
  configured plausibility warnings. Missing configuration remains an accepted
  warning state, never a hard rejection.
- Retain the completed production sign-off for the reviewed Start23 field-test
  protocols and `start23-zone-model-1.0` in the external governance dossier.
  The backend calculates pending FTP/CSS/LTHR/threshold-pace profiles
  deterministically, but it neither derives a threshold from submaximal
  calibration nor activates a calculated profile without the athlete's
  separate confirmation.

### Production review update: 2026-08-24

The product owner confirmed that qualified physiological review and production
sign-off of the active rules, field-test protocols, and
`start23-zone-model-1.0` are complete. This closes the named-reviewer gate for
those exact versions only; the source repository deliberately does not contain
the reviewer's personal identity or the external evidence dossier.

### Review record: 2026-07-26

Result: the isolated deterministic calculation scope passes the Phase 3 exit
criteria under historical `phase-3-ruleset-2`; the accepted 2026-08-11
follow-up decisions are implemented and verified in `phase-3-ruleset-3`.

- Formula tests cover approved examples, equality boundaries, invalid input,
  explicit zero versus missing data, both daylight-saving transitions, and
  unresolved cases through fail-closed or review outcomes.
- The physiology module remains framework- and I/O-independent; architecture
  tests reject FastAPI, database, Supabase, HTTP, Redis, Celery, and LLM client
  imports.
- Precedence and draft-specification failure are tested.
- Decision records and calculation results retain a stable ruleset version.
- The full backend tests, Ruff lint/format checks, and strict mypy checks pass.
- Phase 3 intentionally contains no persistence, Supabase access, route
  handlers, active plan/zone mutation, or athlete-facing TSS.

The remaining decisions above do not change the implemented result for already
approved inputs. They remain explicit gates for the affected application or
presentation paths.

## Phase 3.5: Expo development-build transition

### Status

Complete for the primary Android development route. On 2026-07-27, the project
was upgraded and validated incrementally on SDK 55, 56, and 57. The SDK 57
Android development build was compiled, installed, and launched on a local
Android 15 emulator. It connected to local Metro through an ADB port bridge and
rendered the existing TSS-free design preview.

Expo Doctor, dependency alignment, and strict TypeScript checks pass. VS Code
tasks are available to start the configured Android Virtual Device and run the
development client against local Metro. Physical-iPhone verification remains
pending because EAS reports no Apple team for `adrivdbs-team`; this is now a
later iOS compatibility check rather than a blocker for Phase 4 mobile work.

This phase does not block Phase 3 backend work. It is a gate before Phase 4
mobile implementation. Phase 4 backend work may proceed independently.

### Scope

- Use an Android emulator as the primary local development route.
- Retain the EAS development-build route for later physical-iPhone validation
  when an Apple Developer team and device registration are available.
- Add `expo-dev-client`.
- Upgrade Expo incrementally from SDK 54 to 55, 56, and then 57.
- At every upgrade step:
  - align Expo, React, React Native, and Expo-managed package versions;
  - run Expo's dependency repair and diagnostics;
  - run strict TypeScript compilation;
  - launch the application and verify the existing design preview.
- Create and install the SDK 57 Android development build.
- Verify that the development build connects to the local Metro server and can
  call the configured backend without exposing privileged credentials.
- Stop using Expo Go as the primary Start23 development runtime after this
  transition.

### Exit criteria

- `mobile/package.json` and the resolved Expo configuration report SDK 57.
- Expo dependency diagnostics pass.
- Strict TypeScript compilation passes.
- The SDK 57 development build is installed and launches on the local Android
  emulator.
- Local Metro updates load in the development build.
- The existing TSS-free design preview renders correctly.
- No service-role key, database password, or backend secret is present in the
  mobile bundle.

### Later iOS verification

Create and install an SDK 57 iOS development build after Apple signing and
physical-device registration are available. Expo Go compatibility on that
device is no longer the project SDK constraint.

## Phase 4: onboarding, goals, and zones

### Status

In progress. The Phase 4 database migration, FastAPI application slice, and
Expo onboarding client are implemented and locally verified at the unit,
contract, lint/type, and dependency-diagnostic levels.

The original Phase 4 migration and forward hardening migration
`20260728133728_phase_4_5_review_hardening.sql` are applied in hosted Supabase.
The linked database linter reports no schema errors, and anonymous Data API
probes confirm that owner data and service-only RPCs remain inaccessible. An
in-memory server-side secret-key probe confirms that the fallback RPC accepts
service authorization and rejects a nonexistent athlete without a write. The
updated pgTAP suite has not run because this workstation has no available
Docker/`pg_prove` runtime. Real two-session Auth/Data API isolation, Android
runtime rendering of the new flow, and an end-to-end completion against the
hardened hosted persistence therefore remain pending.

### Scope

- Begin mobile implementation only after the Phase 3.5 exit criteria pass.
  **Complete**
- Athlete profile and biometrics. **Implemented**
- Triathlon-discipline training history. **Implemented**
- One primary race-oriented A goal. **Implemented**
- Manual discipline-specific zones. **Implemented**
- Approved fallback-zone path clearly marked estimated/unreviewed. **Implemented for
  bike and run**
- Pre-question per discipline asking whether the athlete knows the relevant
  threshold, before rendering threshold/zone inputs. **Decided; implementation
  pending**
- Known-threshold route: accept the threshold alone or threshold plus five
  boundaries. Empty boundaries are calculated by a reviewed deterministic
  discipline protocol and must not produce `422`. **Decided; protocol/review
  and implementation pending**
- Unknown-threshold route: perform standard, safely executable calibration
  training through the Week-1 plan, then combine its eligible realized data
  with the athlete-entered TSE feeling score. The result creates a pending
  threshold/zone proposal for athlete confirmation. **Decided; exact TSE
  scale/RPE relationship, deterministic conversion protocol, review, and
  implementation pending**
- Three-piste mobile selector per discipline: A manual known values, B
  automatic calibration/test, C biometric fallback. **Selector implemented;
  A is functional, C is functional for bike/run, B and swim fallback fail
  visibly and safely until their reviewed contracts exist**
- Resumable onboarding state. **Implemented**
- Initial plan proposal trigger. **Implemented as a pending Phase 6 planning
  request; decision 42's reviewed standard Week-1 selection and CSS/zone
  personalization remain pending**

### Exit criteria

- Onboarding validates all required inputs. **Locally verified**
- One active zone version per discipline. **Migration constraint is hosted and
  API tests pass; hosted pgTAP behavior verification pending**
- Generated zone changes cannot bypass proposal approval. **Locally verified;
  first confirmed setup activates, later versions stay pending**
- Public responses contain no TSS. **OpenAPI contract verified**

### Implemented groundwork

- Extended owner profiles with date of birth, height, weight, resting heart
  rate, motivation, and IANA timezone input without accepting an authoritative
  request `user_id`.
- Added owner-scoped onboarding sessions, swim/bike/run history, one active
  race-oriented A goal, versioned zone profiles/metrics/boundaries,
  zone-update proposals, and pending initial-plan requests.
- Added explicit grants and forced RLS to every new public table.
- Added `SECURITY INVOKER` RPCs for atomic history replacement, goal writes,
  zone-version creation, and onboarding completion. Critical tables also use
  trigger-enforced RPC write context so ordinary Data API table writes cannot
  bypass lifecycle rules.
- Added a FastAPI Data API repository that forwards the verified user access
  token with the publishable key, retaining `auth.uid()` RLS context for normal
  athlete operations.
- Added a separate service-only fallback RPC and repository. Direct
  athlete-token fallback persistence is rejected; the trusted RPC forces the
  estimated/unreviewed state and ruleset around boundaries generated by
  deterministic Python.
- Initial planning requests now retain and fingerprint the complete confirmed
  profile, goal, history, and active-zone input. Pending requests refresh when
  those inputs change and preserve the snapshot after consumption.
- Resting-heart-rate transport validation now matches PostgreSQL's positive
  `smallint` range, so oversized input is rejected as `422` before persistence.
- The Phase 4 pgTAP suite now asserts only Phase 4 table presence instead of
  depending on later Phase 5 tables.
- Added TSS-free profile, onboarding, history, goal, zone, fallback, and
  completion endpoints under `/api/v1`.
- Reused `phase-3-ruleset-3` Python validation for discipline matching,
  contiguous boundaries, whole-second pace values, soft-range review, and
  Tanaka/Karvonen fallback generation.
- Added API tests for invalid input, resumability, two-athlete isolation,
  single-goal behavior, one active zone per discipline, pending replacement
  behavior, stale-safe atomic approval/rejection, fallback labeling, incomplete
  completion, and idempotent planning requests.
- Replaced the static mobile entry route with SDK 57 authentication and
  onboarding screens. Access tokens remain in memory; only the refresh token
  is persisted with `expo-secure-store`. The mobile client talks only to
  FastAPI for domain data.
- Added authenticated, server-resumed profile, history, primary-goal,
  discipline-zone, fallback, review, and completion screens.

### Phase 4 implementation differences and remaining work

- Phase 6 owns weekly plans and plan revisions, so Phase 4 completion creates
  an idempotent `initial_plan_requests` row rather than a prematurely typed
  `change_proposals` plan target. Phase 6 must consume this row and create the
  actual pending plan revision/proposal.
- The current active fallback formula is heart-rate based. It is available for
  bike and run and is explicitly estimated/unreviewed; no swim fallback was
  invented. Phase 8.5 now accepts CSS or another discipline threshold without
  requiring optional Zone 1-5 boundaries, exposes reviewed field tests, and
  evaluates their approved threshold formulas. `start23-zone-model-1.0` now
  converts confirmed FTP, bike threshold HR, run LTHR, threshold pace, or CSS
  into complete pending Zone 1-5 profiles. Threshold confirmation and zone
  activation are deliberately separate decisions. Week-1 calibration
  preserves same-block objective data plus canonical 1-10 RPE and never
  manufactures a threshold.
- Decision 42 supersedes the source `reported sport hours * 40` Week-1
  initialization. Week 1 uses a reviewed standard Start23 selection. Known
  CSS/thresholds and zones personalize its execution difficulty; unknown values
  use the safe calibration route above. Training history remains context and a
  safety input, not a direct Week-1 budget formula.
- The current profile does not collect sex/gender/physiology category. The
  2026-08-13 decision permits an optional physiological-sex input, separate
  from gender identity, solely for the chosen `226 - age` female / `220 - age`
  male maximum-heart-rate fallback. That formula requires clinical and
  privacy/legal review plus a new ruleset and forward migration before use. It
  is never used for an FTP estimate.
- Product soft-range thresholds remain unconfigured. Structurally valid manual
  values are accepted with `soft_range_not_configured` review, as locked in
  ruleset 3. Future ranges require full evidence/reviewer/version metadata.
- Athlete-facing manual zone input uses canonical units. Cycling speed is
  activity telemetry only and is not a zone or planning input.
- The zone form originally checked only each interval's width, so it allowed
  numerically ascending swim-pace zones that the deterministic inverse-pace
  rule correctly rejected with `422`. The client now validates direction,
  cross-zone continuity, and whole pace seconds before submission and explains
  that Z1 is slowest while values decrease toward Z5.
- Run the updated Phase 4 pgTAP suite when Docker/`pg_prove` is available, then
  verify the FastAPI flow with two real Auth sessions.
- Configure the mobile public Supabase/API environment values and run the new
  flow in a rebuilt Android SDK 57 development client that includes
  `expo-secure-store`. Physical-iPhone verification remains subject to the
  Phase 3.5 signing dependency.
- After aligning to Expo `57.0.11`, React Native `0.86.2`, and applying the
  available non-breaking audit fix, `npm audit --omit=dev` still reports 19
  Expo/Metro toolchain findings (11 high and 8 moderate) through `image-size`
  and `xcode -> uuid`. npm offers only forced fixes that downgrade or otherwise
  break the SDK 57 dependency set, so they were not applied. Recheck when Expo
  publishes compatible patched transitive dependencies.

## Phase 5: workout catalog

### Status

Implemented and locally verified for the Python domain, public FastAPI
contract, migration review, lint, typing, and automated backend tests. The
Supabase migration is applied in the hosted project and the linked database
linter reports no schema errors. Hosted table statistics confirm seven public
template versions, seven private load rows, 21 segments, 14 phase tags, and
seven zone requirements. A server-side secret-key probe confirms that the
restricted planning RPC returns all seven rows with their private load fields.
Its pgTAP suite has not run because this workstation has no available
Docker/`pg_prove` runtime.

### Scope

- Versioned swim, bike, and run templates. **Implemented**
- Workout segments, duration/distance, zones, and expected RPE. **Implemented**
- Low/high intensity classification. **Implemented with the approved BR-003
  classifier; an exact mixed-duration tie is high intensity**
- Training-phase and fallback compatibility tags. **Implemented**
- Server-internal precomputed planned TSS. **Implemented**
- Small reviewed seed set, not 500+ workouts. **Implemented as seven immutable
  versions representing six current templates**

### Exit criteria

- Catalog validation rejects incomplete or inconsistent templates. **Locally
  verified**
- Public workout models omit planned TSS. **OpenAPI and response verified**
- Historical planned-workout snapshots remain stable after catalog versioning.
  **Domain snapshot and immutable-version persistence verified locally;
  Phase 6 still owns planned-workout row persistence**

### Implemented groundwork

- Added an immutable workout domain with deterministic aggregate validation for
  segment ordering, totals, RPE ranges, discipline-specific technique,
  fallback compatibility, and declared intensity.
- Added two reviewed current templates per discipline and one retained earlier
  run-template version to exercise catalog versioning.
- Added normalized phase and zone-requirement tags and explicit unreviewed
  heart-rate-fallback compatibility.
- Precomputed internal load with the approved expected-RPE midpoint multiplied
  by duration in hours and retained the ruleset/calculation method in private
  persistence.
- Added `GET /api/v1/workout-catalog`, protected by verified bearer identity,
  with explicit TSS-free Pydantic response mapping.
- Added immutable snapshot creation for later Phase 6 plan revisions so a
  catalog version change does not alter captured duration, segments, RPE, or
  internal load.
- Added a migration with read-only authenticated access to public structure,
  forced RLS, immutable version triggers, and a private load table inaccessible
  to athlete-facing database roles.
- Added a service-role-only planning-catalog RPC and restricted backend
  repository. It exposes the durable catalog, including internal load, to
  server planning code without granting direct private-table access.
- Added an automated field-by-field parity test between every Python catalog
  version and the SQL seed. The test identified and corrected three rounded SQL
  load constants to the exact deterministic `Decimal` values.
- Added an intentionally empty `supabase/seed.sql`; reviewed immutable catalog
  data remains migration-owned while the configured reset seed path is valid.
- Added unit, API, OpenAPI, and pgTAP coverage proportional to the catalog and
  load-confidentiality risks.

### Phase 5 implementation differences and remaining work

- The roadmap did not prescribe how reviewed seed load values are calculated.
  Phase 5 uses the already approved BR-004 personalized snapshot formula with
  the midpoint of the template RPE range; it does not invent a separate TSS
  model.
- The runtime FastAPI catalog uses the validated reviewed Python catalog, while
  the matching SQL migration is the durable source intended for Phase 6
  planning queries. A field-by-field automated parity test now prevents these
  reviewed representations from drifting. Moving seed ingestion to a single
  build artifact can still be considered if the catalog grows.
- Run `phase_5_workout_catalog_test.sql` when Docker/`pg_prove` is available.
  The automated Python/SQL parity test already compares the complete reviewed
  hosted migration seed definition with the validated Python catalog.
- Phase 6 must persist the snapshot fields on planned workouts. Phase 5 proves
  the immutable snapshot behavior without prematurely creating Phase 6 plan
  tables.

## Phase 6: weekly planning and approval

### Status

Implemented and locally verified for the deterministic Python planning domain,
public FastAPI contract, owner-scoped repository transport, migration review,
lint, formatting, typing, and automated backend tests. A 2026-08-09 review
hardened decision retries, plan validation, public conflict codes, and the
athlete-facing Expo flow. The migration is now applied to hosted `start23-dev`
(`isfumhgqphieoayqahjv`). The rollback-only
hosted pgTAP suite passes all 30 assertions, including RLS, hidden-load access,
idempotency, stale decisions, owner isolation, and direct moves. Two confirmed
real Auth sessions also verified that each athlete can read exactly their own
Phase 6 fixture through the Data API and cannot read the other athlete's row.
A small forward migration, `20260809225626_phase_6_advisor_indexes.sql`, adds
the covering foreign-key indexes identified by the first hosted advisor run;
the subsequent run reports no remaining Phase 6 unindexed foreign keys.

### Scope

- Weekly-plan and revision persistence. **Implemented**
- Deterministic target and recovery/taper context. **Implemented with the
  pre-Phase-7 target limitation below**
- Workout-deck selection. **Implemented**
- Auto-schedule proposal. **Implemented**
- Anti-stack and soft-boundary warnings. **Implemented**
- Structured availability and injury exclusion. **Implemented as
  revision-scoped confirmed context**
- Pending proposal approval/rejection. **Implemented**
- Public calendar response. **Implemented**

### Exit criteria

- System-generated plan changes remain pending. **Locally verified**
- Approval is atomic, owner-scoped, and stale-safe. **Locally and hosted pgTAP
  verified**
- Manual schedule behavior follows the Phase 0 decision. **Locally and hosted
  pgTAP verified**
- All plan/calendar responses pass the TSS-leak contract tests. **Locally
  verified**

### Implemented groundwork

- Added a framework-independent `planning` domain that resolves base, build,
  recovery, and A-race T-2/T-1 context using the approved Phase 3 rules.
- Added strict workout-deck filtering by training phase, confirmed injury,
  active zone capability, and fallback compatibility.
- Added deterministic discipline-covering deck selection and availability-
  window scheduling with no more than three consecutive rest days. Generated
  schedules fail closed when catalog coverage, availability, rest-day, or
  anti-stack constraints cannot be satisfied.
- Added qualitative intensity-distribution, catalog-capacity, injury-
  exclusion, anti-stack, and availability warnings without exposing hidden
  load values.
- Added immutable `weekly_plans`, `plan_revisions`, `planned_workouts`, and
  `plan_warnings` persistence with forced owner RLS. Planned-workout
  presentation, segment, RPE, schedule, and catalog-version fields are
  snapshotted by value.
- Added separate `private.planned_workout_loads` and
  `private.plan_revision_loads` tables. Athlete-facing and general Data API
  roles receive no direct access.
- Added a narrowly granted service-only generated-plan RPC. It copies hidden
  load from the durable catalog, validates the Python result against that
  snapshot, consumes the fingerprinted onboarding request, and is idempotent
  for the same athlete/week/generation fingerprint.
- Added security-invoker owner approval and rejection RPCs. Approval locks the
  proposal, target revision, and stable plan, verifies the expected base,
  supersedes the old active revision, applies the exact pending revision, and
  marks the proposal applied in one transaction.
- Added direct athlete moves through the verified FastAPI path. A move applies
  immediately as a new immutable active revision, rejects stale revisions and
  confirmed-injury conflicts, and retains non-blocking qualitative warnings.
- Added TSS-free plan, eligible-deck, validation, proposal-list/detail,
  schedule-proposal, direct-move, and calendar endpoints under `/api/v1`.
- Plan layout validation now accepts only owned workout IDs and proposed
  timestamps against an expected revision. Discipline and intensity always
  come from the immutable server snapshot.
- Plan approval and rejection retries are idempotent for the same proposal and
  exact base precondition. Planning conflicts retain stable public error codes.
- Unified plan and zone decisions behind the existing typed
  `/change-proposals/{id}/approve|reject` endpoints without weakening the
  existing zone state machine.
- Added domain, API, owner-isolation, stale-approval, rejection, direct-move,
  repository-transport, OpenAPI, seed-parity, and pgTAP coverage.

### Phase 6 implementation differences and remaining work

- Before Phase 7, canonical realized weekly load did not exist. The first plan
  therefore used the closest eligible reviewed catalog deck as its
  deterministic hidden baseline and later regular weeks held prior planned
  load. Phase 7 now supplies canonical realized load and replaces that hold
  whenever realized history exists; the safe hold remains the intentional
  missing-history fallback. Recovery and taper factors remain unchanged.
- The documented separate `PUT /weekly-plans/{plan_id}/selections` draft step
  is consolidated into `POST /weekly-plans/{plan_id}/schedule-proposals`,
  whose request contains explicit eligible template IDs and availability.
  The resulting system schedule is still a typed pending revision.
- Availability is retained as explicit per-revision windows rather than a
  cross-week `availability_blocks` aggregate. This is sufficient for Phase 6
  scheduling and manual-move warnings; Phase 8 still owns durable check-in
  context, source, and expiry semantics.
- Confirmed blocked disciplines are hard-excluded and automatic BR-010
  redistribution is now explicitly disabled for the MVP. Removed load is not
  replaced; Phase 8 will persist the locked functional restriction states and
  explicit clearance flow.
- The Phase 5 catalog did not contain a base/recovery bike workout compatible
  with the FTP setup used by the Phase 4 mobile flow. Phase 6 adds one reviewed
  immutable power-guided aerobic bike template, bringing the pending migrated
  catalog to eight versions across seven logical templates, with complete
  Python/SQL parity coverage.
- The current small runtime catalog cannot produce a complete multi-discipline
  taper and a taper-week triathlon request therefore fails closed with
  `catalog_coverage_unsatisfied`; taper generation also fails closed without a
  prior build-load baseline. Decision 41 requires Phase 8 to reassess taper
  coverage from the available 160-row `Trainingen START23.v01` export before
  concluding that new training definitions are needed. That file has no
  explicit taper flag, so taper eligibility, import validation, and a full
  runtime fixture remain pending.
- The runtime planner still selects forward cycle position from the number of
  prior plans. Decision 43 supersedes that behavior for a race: the event date
  always anchors backward cycle alignment. A non-race goal begins at cycle week
  1 and uses only its own later Phase 12 rules.
- Hosted `start23-dev` now contains both the main Phase 6 migration and the
  advisor-index follow-up. The hosted pgTAP suite passes 30/30, and two real
  Auth sessions pass owner/cross-owner Data API isolation. The test accounts
  and one minimal owned weekly-plan fixture per account remain in the
  development project; their credentials are handed off outside the repository.
- Athlete-facing Expo plan generation/review, explicit approval/rejection,
  eligible-deck selection, replacement schedule proposals, and active calendar
  screens are implemented and pass strict TypeScript checks. Runtime Android
  verification against the hosted Phase 6 migration remains pending.

### Phase 6 review record: 2026-08-09 through 2026-08-10

- Backend tests cover idempotent repeated decisions, stable stale-conflict
  codes, owner-scoped deck reads, and validation that rejects client-supplied
  discipline/intensity classifications or incomplete workout sets.
- The migration returns the original public result for repeated approval or
  rejection without another state transition; pgTAP covers both retries.
- Public HTTP errors can retain allowlisted domain codes without echoing raw
  database messages or hidden load values.
- Ruff lint/format, strict mypy, the complete backend suite, and mobile strict
  TypeScript are the local completion gate for this repair.
- Hosted migration history, pgTAP execution, and two-real-session Data API
  isolation are verified. The advisor's Phase 6 foreign-key findings were
  resolved by a forward migration. The project-level leaked-password
  protection warning and two pre-existing Phase 4 foreign-key index notices
  remain outside this Phase 6 schema repair. Android runtime verification
  remains an external gate.
- The first real-account Android login reached the intake route but could not
  load it because no local FastAPI process or API reverse bridge was active.
  The VS Code Android task now starts FastAPI as a process task with a separate
  argument array, which also handles workspace paths containing spaces, waits
  for application startup, and configures both the Metro `8081` and API `8000`
  reverse bridges before opening the development client. This is local runtime
  orchestration; the mobile client continues to send the verified Supabase
  access token only to FastAPI and receives no backend secret.

## Phase 7: activity and RPE feedback

### Status

Implemented and verified locally on 2026-08-11. The FastAPI activity contract,
deterministic match matrix, private realized-load persistence, BR-002/BR-004
planning integration, pending correction revisions, and mobile capture/RPE
flow are complete. The migration and rollback-only pgTAP suite are prepared
but have not been applied to hosted Supabase or executed locally because this
workstation has no Docker/PostgreSQL test runtime. Real-account Android
verification therefore remains open.

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

### Implemented

- Added authenticated canonical-summary create/list/read endpoints and an
  immutable first-RPE endpoint under `/api/v1/activities`.
- Added owner-scoped `activities` and `activity_metrics` persistence with
  forced RLS and explicit authenticated grants. Internal realized load is
  isolated in `private.activity_loads`; public database helpers, Pydantic
  models, OpenAPI, messages, and mobile types omit planned and realized TSS.
- Activity creation uses an athlete-scoped UUID idempotency key plus a canonical
  request fingerprint. Replaying the same request returns the original record;
  reusing the key for different content is a conflict.
- Supported matching is intentionally explicit: the athlete chooses an owned,
  active planned workout, or records the activity as extra/unmatched. A
  planned workout can be matched only once and its discipline must agree.
- Realized session load is calculated deterministically as actual RPE times
  actual duration in hours. Classification implements the reviewed matrix:
  hidden fatigue for RPE 7+ on a low-intensity workout, strict-above-115%
  overshoot, inclusive +/-10% plus expected-RPE perfect match, deviation, and
  unplanned load.
- Qualifying hidden-fatigue, overshoot, and unplanned outcomes can create a
  typed pending plan revision which cancels only eligible future
  high-intensity workouts. The current active plan remains unchanged until the
  existing proposal approval endpoint is called.
- Weekly planning now consumes private realized weekly history. BR-002 debt is
  evaluated first; otherwise BR-004 uses the available-sample 42-day realized
  baseline and its approved 80% progression boundary. Missing realized history
  retains the Phase 6 planned-load hold.
- Reliable realized low/high activity minutes now drive BR-003 intensity debt
  at 60% or greater classified coverage. Unknown time is excluded, recovery
  and taper take precedence, and the correction is used only for the first
  following non-recovery week.
- Added a mobile activity screen for explicit planned/extra selection,
  duration/distance capture, retry-safe idempotency, pending RPE prompts,
  qualitative outcomes, and pending-correction notices.
- Added pure calculation, API, repository transport, cross-owner, idempotency,
  immutable-RPE, recursive hidden-TSS, planning-integration, and pgTAP tests.
  The complete backend suite passes 235 tests; Ruff, strict mypy, and mobile
  strict TypeScript are completion gates.

### Implementation differences and remaining work

- Direct FIT/TCX upload, raw telemetry/file persistence, provider identity,
  webhooks, and automatic imports remain deferred to Phase 9 as locked in the
  Phase 0 input decision. Phase 7 accepts only a validated canonical summary.
- Automatic proximity matching, bricks, multisport activities, and ambiguous
  discipline matching remain deferred because no reviewed policy exists.
  Omitting `planned_workout_id` is therefore safely and visibly unmatched.
- Hidden fatigue is evaluated before load overshoot. With the approved
  session-RPE load proxy, evaluating overshoot first would make the distinct
  high-RPE-on-easy-session safety outcome unreachable.
- Phase 8 supersedes Phase 7's first-score immutability: RPE may be corrected,
  with an audit trail, during the activity's current athlete-local
  Monday-Sunday week and becomes immutable when that week ends. A missing RPE
  remains missing until the proposed but dimensionally invalid `RPE = TSS`
  statement is replaced by a precise, reviewed rule.
- The current correction policy removes future high-intensity work only; it
  does not invent replacement workouts or change zones. Phase 8 can add richer
  corrections after structured availability, fatigue, and injury context is
  confirmed.
- Hosted migration application, database advisors, rollback-only pgTAP, two
  real-token isolation checks, and emulator/device end-to-end verification are
  still required. No production or hosted change was applied automatically.

## Phase 8: structured weekly check-in

### Status

Core application work was implemented and locally verified on 2026-08-13.
The structured FastAPI/mobile flow, deterministic planning amendments, and
Supabase migration/pgTAP suite are prepared, and the migration is recorded in
the linked hosted project. Phase 8 is still `in progress`, because the reviewed
standard Week-1/TSE conversion protocol and reviewed taper labels do not exist,
the Phase 8 pgTAP/real-token flows have not run, the local SQL runtime is
unavailable, and no device verification was performed. Phase 8 now also owns
the explicitly accepted planning-completion work below.

### Scope

- Blocked days.
- Confirmed injury disciplines.
- Weekly re-evaluation of every active injury restriction, with attributable
  physician advice and an explicit athlete plan choice; never auto-clear.
- Fatigue and missed-workout reasons.
- Start-of-week confirmation of recurring sports or strenuous activities
  outside the Start23 plan.
- Add an extra planned activity to the current week and later record its actual
  duration and RPE; only private realized load may influence the next proposal.
- Detect a completely inactive completed week and base the restart proposal on
  the most recent four complete local weeks, including the zero week, without
  10% progression for that restart week.
- Explicit achieved-goal maintenance state: no 10% load progression, while the
  four-build/one-recovery rhythm and reviewed 80/20 distribution remain.
- When every goal discipline is blocked, create a safe, TSS-free, pending
  rest-only revision. Do not return a normal planning error, redistribute load,
  or activate it without athlete confirmation.
- Add an athlete-facing move/reschedule action. It must stay within the existing
  athlete-local Monday-Sunday week, carry the expected revision, fail stale
  changes safely, and show qualitative recovery/restriction/spacing warnings.
- Represent each intentionally empty plan date explicitly as a public rest day
  in the API and mobile calendar, distinct from missing planning data and with
  no private load value.
- Recalculate the remaining workout deck after each selection against the exact
  selected set and expected revision. The server is authoritative; a dedicated
  endpoint or an updated pending-plan response may provide the recalculation.
- Generate weekly proposals using athlete-local Monday-Sunday semantics. The
  local-Monday trigger and post-check-in trigger must be idempotent for the same
  athlete and local week; the final behavior must not use a blind UTC week.
- For race goals, align every partial training horizon backward from the event
  date. For non-race goals, retain a cycle-week-1 start and leave goal-specific
  execution to Phase 12.
- Use a reviewed standard Week-1 training selection. Known CSS/thresholds and
  zones personalize execution difficulty; unknown values use safe calibration
  training and athlete-entered TSE feedback to create only a pending zone
  proposal. Do not use reported hours multiplied by 40 as the Week-1 target.
- On app open, show a prominent but non-blocking reminder for completed
  activities missing required RPE/TSE feedback. Keep it visible and deep-link
  it to the activity until feedback or an explicit terminal state exists.
- Reassess taper coverage from the available 160-row
  `Trainingen START23.v01` export. Define reviewed taper eligibility for
  existing rows, validate their bucket/discipline/duration/zone data, and add no
  new training definitions unless that review proves coverage is insufficient.
  A full triathlon taper remains unsupported until catalog coverage and a
  runtime fixture pass.
- Next-week plan proposal.
- No natural-language LLM dependency.

### Exit criteria

- Confirmed context has source and expiry.
- Injury and availability affect only pending plan revisions.
- An all-disciplines-blocked case produces a pending rest-only revision and no
  public TSS.
- An athlete can move a workout within the same local week with revision
  preconditions and qualitative warnings; cross-week and stale moves fail.
- Approved plan calendars expose explicit rest days without exposing load.
- Deck eligibility changes deterministically after selection and cannot be
  bypassed with a stale revision.
- Weekly generation is idempotent and tested around athlete-local week and
  timezone boundaries.
- Race fixtures prove that the event date, rather than prior-plan count,
  determines cycle position; non-race fixtures begin at week 1 without race
  rules.
- Week-1 fixtures prove the known-zone and unknown-zone calibration routes. A
  TSE-derived proposal cannot activate zones and cannot be implemented until
  the reviewed conversion protocol and TSE/RPE definition exist.
- Missing-feedback reminders are visible on app open, non-blocking, persistent,
  and TSS-free.
- Reviewed existing-catalog taper rows pass validation and a full swim/bike/run
  taper planning fixture before taper support is called complete.
- Check-in can be completed without an external AI provider.

### Implemented

- Added a no-LLM structured weekly check-in with one idempotent record per
  athlete/local week. Context edits are immutable revisions with source
  `structured_form`, bounded local-week expiry, a canonical fingerprint, and
  a separate exact-fingerprint confirmation step.
- Added blocked dates, fatigue, missed-workout reasons, explicit recurring
  sport confirmation, and planned outside activities. A strenuous outside
  activity blocks its local planning date. It can later be linked atomically
  to a canonical activity with actual duration and the existing RPE flow; only
  private realized load reaches later planning.
- Added durable functional restrictions with a seven-day review timestamp,
  allowed intensity (`none` or `low_only`), attributable professional advice,
  and an explicit athlete choice. Every active discipline must be reviewed;
  time passing never clears a restriction and removed load is never
  redistributed.
- Added deterministic low-only catalog filtering and a safe all-goal-
  disciplines-blocked result. That result is a zero-load, TSS-free, pending
  rest-only revision with seven explicit restriction-rest days; athlete
  approval is still required.
- Added exact inactive-restart behavior: when the immediately preceding
  completed local week has zero activities, the target is the mean of the most
  recent four complete local weeks including explicit zero weeks, with no 10%
  progression. Persistence now projects up to six consecutive completed local
  weeks after the athlete's earliest plan/activity evidence, including weeks
  without a plan.
- Added explicit achieved-goal maintenance persistence and mobile confirmation.
  Build weeks hold the latest approved load, the 4+1 recovery rhythm remains,
  and catalog selection retains the reviewed weekly low/high policy without
  progression.
- Race cycle position is now derived backward from the event-date week and no
  longer from the number of prior plans. The current public goal contract
  remains race-only and does not apply race rules to a disguised non-race goal.
- Fixed catalog bucket ownership in weekly 80/20 allocation: the immutable
  template bucket now classifies the complete workout, while segment zones
  remain execution detail. Added deterministic selection-aware deck
  recalculation against exact selected IDs and an expected plan revision.
- Added public intentional rest days to plan/calendar responses. They are
  distinguished from missing data and contain no load values.
- Exposed the existing stale-safe, same-local-week move behavior in mobile.
  The app validates the entire proposed layout first, displays qualitative
  recovery/restriction/spacing warnings, and then requires an explicit move
  action with the expected revision.
- Added an app-open, non-blocking, TSS-free missing-RPE reminder that deep-links
  to activity feedback. RPE can now be corrected with an audit trail only
  during the activity's athlete-local Monday-Sunday week; later corrections
  fail closed.
- Added a service-only local-Monday entrypoint that opens due check-ins from
  each athlete's IANA timezone and is retry-idempotent. Confirmed-context plan
  generation is independently idempotent by athlete, week, check-in, input,
  availability, restriction, and selection fingerprint.
- Added forced-RLS tables, explicit grants, RPC-only write enforcement,
  owner-scoped athlete operations, narrow service-only planning operations,
  repository/OpenAPI/privacy tests, and a rollback-only Phase 8 pgTAP suite.
  The complete backend suite passes 254 tests; Ruff, formatting, strict mypy,
  the source-catalog audit, and mobile strict TypeScript pass locally.

### Implementation differences and remaining work

- Phase 8.5 implements the reviewed field-test and Week-1 protocol registry,
  canonical 1-10 RPE/TSE meaning, immutable observations, deterministic
  threshold formulas, and safe provisional/RPE-only outcomes. The existing
  regular planned-workout DTO still requires Zone 1-5 segments, so normal-plan
  selection of the zone-independent calibration protocols remains a separate
  exit gate. The implementation does not use reported hours multiplied by 40.
  Phase 8.5 now uses the separately versioned `start23-zone-model-1.0` for
  complete, pending Zone 1-5 conversion from an accepted threshold.
- A non-race cycle-week-1 runtime fixture is not implemented because the public
  goal model is intentionally still race-only. Goal-type selection and
  non-race execution remain Phase 12 work; Phase 8 only removes prior-plan
  count from race anchoring and does not invent a non-race macrocycle.
- The 160-row source-catalog audit is recorded in
  `phase-8-taper-catalog-review.md`. All IDs, disciplines, buckets, RPE values,
  zones, segment order, and supplied totals validate, but all 60 swim rows omit
  total duration and the export contains no reviewed taper marker. Treating
  `Herstel` or `Techniek` as taper approval would invent physiology. No rows
  were imported or relabelled, no new workouts were added, and full triathlon
  taper remains fail-closed.
- The local-Monday database entrypoint opens the structured check-in; it cannot
  create a plan before the athlete confirms context. A deployed
  Railway/Supabase schedule still has to invoke it. Post-confirmation plan
  generation is user-triggered in the current mobile flow and idempotent.
- Correcting RPE expires any stale pending correction revision and updates the
  private realized load/audit row. It does not automatically manufacture a
  replacement current-week correction proposal after the corrected score;
  richer automatic correction policy still lacks a reviewed rule.
- The migration was created through Supabase CLI and is applied in the linked
  hosted project. `supabase db reset --local --no-seed` was attempted and failed
  because Docker and Podman are absent. The current linked schema passes
  error-level lint and advisors ran, but the Phase 8 pgTAP suite,
  two-real-token isolation, and Android/iOS runtime flows remain external
  verification gates.
- The RPE reminder has no explicit terminal/dismissed state because no such
  product rule exists. It remains visible until RPE is supplied, which is the
  safe Phase 8 behavior.
- Qualified clinical/physiology production approval of the active versions was
  confirmed complete on 2026-08-24. Local deterministic tests remain separate
  implementation evidence and do not approve future rule changes.

## Phase 8.5: zone intake, field tests, and Week-1 calibration

Detailed decisions, implemented actions, formulas, and remaining gates are in
[Backend zone calculation, field tests, and Week-1 calibration](backend-zone-calculation.md).

### Status

Backend and Expo functional cores, including `start23-zone-model-1.0`, are
implemented and locally verified. The original Phase 8.5 migration remains
applied in the linked Supabase project. The forward-only zone-model migration
was also applied there on 2026-08-24; its 19-assertion rollback-only pgTAP suite
passes against the linked database and remote error-level lint is clean. A local
Supabase reset could not run because Docker and Podman are unavailable.
The mobile flow passes strict TypeScript, but the new confirmation lifecycle
has not been exercised in an Android/iOS development build. No provider or
other production runtime was enabled by this implementation.

### Scope

- Four explicit per-discipline setup routes: known values, field test,
  calibration week, and RPE-only. **Implemented in FastAPI and persistence**
- Partial known thresholds with optional Zone 1-5 profiles; empty optional
  boundaries do not produce `422`. **Implemented**
- Reviewed run threshold, bike FTP, bike threshold-HR, and swim CSS field-test
  evaluation. **Implemented for threshold estimates**
- Reviewed submaximal Week-1 protocols with same-block objective metrics,
  block RPE, and session RPE. **Implemented for immutable observations and
  safe status evaluation**
- Immutable owner-scoped observations and service-only generated evaluation
  persistence. **Implemented locally**
- Threshold and zone changes remain separate pending lifecycles. **Implemented:
  a confirmed field-test threshold creates a still-pending calculated profile;
  a second stale-safe athlete decision is required to activate it**
- Five-zone conversion for bike FTP, bike threshold HR, run LTHR, run threshold
  pace, and swim CSS with canonical whole-unit `ROUND_HALF_UP` boundaries,
  higher-intensity equality ownership, inverse pace/speed handling, and an
  FTP-only `>120%` supramaximal marker. **Implemented as
  `start23-zone-model-1.0`**
- Multi-metric discipline profiles, primary/secondary metric ordering, open
  outer bounds, evidence/source/review provenance, immutable prior versions,
  and explicit calculated-profile proposals. Swim RPE remains separate
  execution feedback/context because v1.0 defines no numeric RPE-to-zone
  boundary table. **Implemented locally**
- Zone-independent calibration protocol selection in the normal weekly plan.
  **Pending because the current planned-workout segment contract requires a
  Zone 1-5 value and the approved fixtures define no internal planned-load rule
  for inserting these protocols into normal target selection**
- Android setup, protocol execution, feedback, and result screens.
  **Implemented in strict TypeScript; emulator/device runtime pending**

### Exit criteria

- The seven approved CSV protocols and every segment match the Python registry.
  **Verified against the seven individually committed CSV fixtures by
  fixture-parity tests**
- CSS/FTP/LTHR/threshold pace are produced only by their own valid reviewed
  field tests. **Verified**
- Submaximal calibration cannot produce a threshold. **Verified**
- Missing session RPE blocks evaluation but not observation/activity storage.
  **Verified in domain/API tests and hosted pgTAP**
- RPE-only is a valid onboarding configuration and creates no zone profile.
  **Implemented and hosted-persistence verified; real-token/mobile flow pending**
- Public APIs and tables contain no TSS/private-load fields. **OpenAPI/backend
  tests and hosted pgTAP pass**
- Complete Zone 1-5 candidates are deterministic and versioned, and never
  auto-activate. **Implemented and covered by calculation/API tests; qualified
  production review is complete, while hosted migration/pgTAP remains a
  release gate**

### Implementation notes and remaining work

- The approved ZIP named in the original decision record is not present in the
  repository. The parity test now reads the committed protocol index and seven
  committed CSV files directly; it still compares every protocol, segment,
  duration/distance, and RPE range and does not weaken fixture coverage.
- The mobile known-values route accepts one or both discipline thresholds and
  optional boundary overrides. A confirmed known threshold is converted by the
  model into a pending multi-metric profile and proposal; model-derived ranges
  remain distinguishable from athlete overrides. The first profile also stays
  pending, with an explicit null base-version precondition. No direct
  active-zone write was added.
- Field-test results store their versioned calculated candidates immutably.
  Accepting the threshold records a separate decision and creates a pending
  profile/proposal; rejecting it creates no profile. Approval then atomically
  supersedes any active version. The mobile calibration screen exposes all
  three choices without merging them into one action.
- Provenance includes source metric/value/method and quality, model and evidence
  version, calculated timestamp, athlete review state/timestamps, optional
  reviewer identity, evaluation link, and deterministic input fingerprint.
  Planned and realized TSS are absent from every new public DTO/table.
- The mobile execution flow creates an owned canonical activity, records its
  canonical 1-10 session RPE, writes immutable protocol observations, and only
  then requests deterministic evaluation. Until the planner gate above is
  resolved, this is an explicit standalone protocol execution and has no
  fabricated `planned_workout_id`.
- Expo SDK 57 patch dependencies were aligned to `expo ~57.0.14`,
  `expo-dev-client ~57.0.13`, and `expo-splash-screen ~57.0.7`; Expo Doctor now
  passes 20/21 checks because it now expects the newer compatible patches
  `expo ~57.0.16`, `expo-dev-client ~57.0.15`, and
  `expo-splash-screen ~57.0.8`. Updating those packages is kept outside this
  zone-model change. `npm audit` previously reported 8 moderate and 11 high
  upstream/transitive advisories with no critical finding. No breaking
  `audit fix` was applied; this needs an upstream-compatible SDK 57 resolution
  or a separately reviewed upgrade.
- The rollback-only pgTAP suite shares one transaction across simulated API
  calls, while PostgREST gives each RPC or table request its own transaction.
  The direct-write assertion therefore clears the RPC's transaction-local
  critical-write guard before probing the table, and the evaluation
  immutability assertion expects the stricter table-permission rejection that
  occurs before the trigger.
- The zone-model calculation, calibration, onboarding, repository, AI coach,
  and mobile changes pass the complete backend suite (348 tests), Ruff, strict
  mypy, and mobile strict TypeScript. Expo Doctor passes 20/21 checks with the three
  patch-version differences above. The original hosted Phase 8.5
  migration and 18-assertion pgTAP suite remain verified. The zone-model
  migration and 19-assertion pgTAP suite are now hosted-verified as well.
  Two-real-token isolation, Android/iOS runtime, and dependency-advisory
  resolution remain open gates. Qualified physiology
  production review of the active versions was confirmed complete on
  2026-08-24.

## Phase 9: one wearable integration

### Status

Backend functional core implemented locally on 2026-08-17 with Polar
AccessLink v3 as the provisional first-provider candidate. The choice is based
on its documented OAuth user lifecycle, HMAC-SHA256 webhook signatures,
30-day post-registration exercise feed, and FIT/TCX export support. This is a
technical implementation choice, not the still-required product, legal,
privacy, and provider-terms approval for production.

The Phase 9 migration was applied to the linked Supabase project on 2026-08-17.
The linked ledger is aligned, the database linter reports no schema errors, and
the rollback-only Phase 9 pgTAP suite passes all 23 assertions. This installs
inactive schema, RPC, RLS, and private-bucket groundwork only; no Polar client,
webhook, credential, athlete connection, or provider data processing was
enabled.

The local slice adds one-time OAuth state, server-confined provider tokens,
provider user registration/deregistration, strict signed webhook intake,
timestamp replay bounds and receipt idempotency, owner-scoped import status,
a maximum 30-day historical import, canonical UC-03 activity creation, and a
private size/content-type-bounded Supabase Storage bucket for available FIT
files. Provider-specific mapping, HTTP-contract, failure-isolation, ownership,
and TSS-confidentiality tests are included.

### Scope

- One approved provider. **Polar AccessLink implemented provisionally;
  production approval pending**
- OAuth/token lifecycle. **Implemented for Polar's authorization-code,
  registration, long-lived access-token, and deregistration/revocation model**
- Webhook verification and idempotency. **Implemented with Polar HMAC-SHA256,
  a ten-minute timestamp window, unique payload receipts, and duplicate
  suppression**
- Historical import limited to approved range. **Implemented with a hard
  one-to-30-day request bound; using Polar's provider-enforced rolling 30-day
  availability remains product-approval-gated**
- Private activity-file storage. **Implemented for available FIT files in a
  non-public 25 MiB bucket with owner read RLS and server-only writes**
- Provider-specific contract fixtures. **Implemented**

### Exit criteria

- Disconnect/revocation behavior is tested. **Locally verified**
- Invalid/replayed webhooks are rejected. **Invalid events are rejected and
  valid duplicates are acknowledged without reprocessing; locally verified**
- Imported activities use the same canonical UC-03 path. **Locally verified**
- Provider failure does not corrupt plan or activity state. **Locally
  verified**

### Phase 9 implementation differences and remaining work

- Polar AccessLink is not yet an approved production processor. Before hosted
  use, approve its terms, health/GPS legal basis, consent copy, retention and
  deletion policy, regional-processing position, and brand/attribution
  requirements; then register the real client and webhook.
- The maximum historical window is 30 days because the selected AccessLink v3
  exercise endpoint exposes only exercises uploaded after client registration
  and within the last 30 days. Start23 additionally filters the athlete's
  requested one-to-30-day window. No older backfill or automatic 30-day
  calibration was invented.
- Polar AccessLink v3 documents access tokens as long-lived until explicit
  deregistration rather than a refresh-token rotation. The persistence model
  accepts a provider expiry when supplied, but no unsupported refresh flow was
  added. Disconnect first asks Polar to deregister/revoke; local token removal
  occurs only after success or an already-revoked response so a transient
  provider failure remains safely retryable.
- A valid duplicate webhook is acknowledged as `duplicate` and excluded from
  processing, rather than returning an error that would cause the provider to
  retry it. Invalid signatures, stale timestamps, unsupported events, and
  provider-controlled fetch URLs are rejected.
- Webhook work is persisted before a FastAPI background task processes it.
  The receipt/import state is retry-safe and failures are recorded, but a
  deployed scheduled retry command is not yet configured. No Redis, Celery, or
  second service was introduced.
- FIT files are stored when Polar makes one available. A missing FIT export
  does not invalidate the canonical summary. Storage metadata is owner-scoped;
  a signed-download API, raw-file UI, maps, and telemetry analytics remain out
  of MVP scope.
- No Expo connection/import UI was added in this backend-first slice. The
  OAuth start/callback, connection, disconnect, import, and import-status APIs
  are ready for a later small mobile surface after provider approval.
- The migration is applied to hosted Supabase and the 23-assertion rollback-only
  pgTAP suite, owner policies, explicit grants, private 25 MiB bucket, and
  linked error-level lint are verified. Real OAuth callback, webhook delivery,
  two-session RLS, Storage transfer, Railway background execution, and
  Android/iOS runtime verification still require provider credentials and
  hosted rollout approval.
- The linked Security Advisor has no error-level finding. It reports expected
  warnings for the authenticated `start_polar_oauth`, `get_polar_connection`,
  and `list_polar_imports` `SECURITY DEFINER` RPCs. Each revokes public/anonymous
  execution, derives and checks `auth.uid()`, and returns owner-scoped data; a
  production security review must either accept that deliberate boundary or
  refactor the read-only RPCs. The project-level leaked-password protection
  warning also remains open. Newly installed indexes are reported as unused
  before production traffic, and the composite `activity_files` foreign key is
  already covered by its unique `activity_id` lookup plus owner index, so no
  redundant advisor-only index was added.
- Local verification passes the complete 303-test backend suite, strict mypy,
  and Ruff. Local Supabase lint still cannot run because the configured
  PostgreSQL service at `127.0.0.1:54322` is unavailable; the linked hosted lint
  passes with no schema errors.

## Phase 10: constrained LLM coach

### Status

Pulled-forward slice implemented on 2026-08-24 so AI-assisted weekly-plan
explanations are available before the rest of Phase 10. Phase 6 remains solely
responsible for deterministic workout selection, physiology, placement, and
creation of a pending schedule. After that pending proposal exists, the backend
may call the OpenAI Responses API with a closed Pydantic schema containing only
public plan facts and ask for a bounded Dutch explanation.

The adapter uses Structured Outputs, `store: false`, a server-only
`START23_OPENAI_API_KEY`, configurable `START23_OPENAI_MODEL` (default
`gpt-5.6-luna`), and a bounded timeout. The provider receives no planned or
realized TSS, other private load values, free athlete text, database tools, or
mutation capability. Refusal, invalid output, timeout, provider failure, or a
missing key produces a deterministic local explanation without failing plan
creation. A service-only Supabase RPC can fill the public explanation exactly
once while the proposal is pending; it cannot update workouts, zones, plan
state, or approval state. The mobile planning screen shows the explanation next
to the existing explicit approve/reject actions.

The new migration was applied to linked Supabase on 2026-08-24. Remote
error-level lint is clean; the rollback-only pgTAP suite executes successfully,
and a separate read-only query confirms that only `service_role` can execute
the explanation RPC. The Git-ignored backend environment contains a working
OpenAI key, and a live non-personal Responses smoke test passed with
`gpt-5.6-luna` and `store: false`. Privacy/DPA/retention approval remains a
production gate. The local environment still lacks
`START23_SUPABASE_SECRET_KEY`, so local FastAPI service-only planning calls need
that separate secret before a complete weekly-plan E2E run can succeed.

### Scope

- Structured context extraction. **Pending beyond this pulled-forward slice**
- Clarifying questions. **Pending beyond this pulled-forward slice**
- Explanation of deterministic recommendations. **Implemented for weekly-plan
  proposals with deterministic fallback**
- Confirmation UI bound to a specific proposal. **Implemented by reusing the
  existing pending proposal approval flow**

### Exit criteria

- LLM output cannot invoke plan or zone mutation. **Implemented and tested**
- Extracted context is schema-validated. **Not yet applicable; free-text
  extraction remains pending**
- Required context is confirmed before critical effects. **Implemented: the AI
  runs only after deterministic proposal creation and cannot apply it**
- Prompts and responses contain no TSS. **Implemented and contract-tested**
- Privacy and retention configuration is approved. **Pending production gate;
  API requests already set `store: false` and minimize disclosed data**

## Phase 11: zone progress evaluation

### Scope

- Implement UC-05 only after statistical thresholds are approved.
- Produce validation-test or zone-update proposals.
- Reuse existing activity and approval workflows.

### Exit criteria

- Minimum sample and data-quality requirements are tested.
- Outlier behavior is deterministic.
- No zone is changed without the approved confirmation sequence.

## Phase 12: non-race planning modes

This is the new final functional phase requested on 2026-08-13. The product
option remains visible as planned/coming later until its deterministic rules
are approved; it must not masquerade as a supported race plan before then.

### Scope

- Goal-type selection clearly distinguishes a dated race/event from a non-race
  personal goal. Race goals are date-anchored and handled by the race planner;
  non-race goals start their own cycle at week 1.
- Non-race goal selection, including general fitness, weight loss, and other
  explicitly approved goal families.
- Goal-specific macrocycles, maintenance rules, intensity targets, progression
  and recovery behavior.
- Workout-catalog coverage and deterministic eligibility for each supported
  goal family.
- Pending proposal and athlete-confirmation flow identical in safety semantics
  to race planning.

### Exit criteria

- Every exposed goal family has a reviewed deterministic rule table and catalog
  coverage.
- Unsupported goals are shown as unavailable/coming later, not silently mapped
  onto race rules.
- Public plan responses continue to omit planned and realized TSS.
- No plan becomes active without athlete confirmation.

### Final deployment and security handoff

These are end-of-MVP deployment gates, not blockers for continuing Phase 6 and
later development locally:

- Railway is not required during local development. When a local backend flow
  first calls either service-only Supabase RPC, configure the modern
  `sb_secret_...` value only in the Git-ignored `backend/.env` as
  `START23_SUPABASE_SECRET_KEY`. Never add it to a mobile environment or commit
  it.
- Before the first Railway deployment, open the FastAPI service's
  **Variables** tab, add `START23_SUPABASE_SECRET_KEY` with the modern Supabase
  secret key, review the staged change, and deploy it. Keep the existing
  `START23_SUPABASE_URL` and `START23_SUPABASE_PUBLISHABLE_KEY` scoped to that
  backend service as well.
- Security note: during the Phase 4/5 hosted review, the Supabase CLI printed
  the legacy `service_role` JWT in local command output even though secret
  reveal was not requested. The value was not committed or copied into
  application configuration, but retained execution logs must be treated as a
  possible disclosure. Before production release, confirm that no component
  still uses the legacy `anon` or `service_role` keys, disable the legacy keys
  under **Supabase Dashboard -> Settings -> API Keys**, and verify the backend,
  mobile client, and integrations use only the modern publishable/secret keys.
  Do not rotate JWT signing keys without a separate rollout plan because that
  can invalidate active credentials.

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
- Weight-loss, muscle-gain, and general-fitness plan generation before the new
  Phase 12 rule/catalog gates are satisfied.
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
- Phase 0 physiological specification: `ruleset-3 implemented; qualified
  production review of active versions confirmed complete 2026-08-24`
- Phase 1 backend foundation: `implemented; locally verified`
- Phase 2 authentication: `verified`
- Phase 2 persistence and hosted RLS: `hosted schema/RLS verified; FastAPI
  persistence and real-token integration pending`
- Phase 3 deterministic core: `ruleset-3 pure calculations implemented and
  verified`
- Phase 3.5 mobile development-build transition: `SDK 57 Android development
  build installed, launched, and connected to local Metro`
- Phase 4 onboarding, goals, and zones: `implemented and review-hardened
  locally and migrated in hosted Supabase; pgTAP, real-token isolation, and
  mobile runtime verification pending`
- Phase 5 workout catalog: `implemented locally and migrated in hosted
  Supabase; pgTAP verification pending`
- Phase 6 weekly planning and approval: `implemented, migrated, and verified
  locally plus hosted pgTAP/real-token isolation; taper-catalog and Android
  runtime verification pending`
- Phase 7 activity and RPE feedback: `implemented and verified locally; hosted
  migration applied; pgTAP, real-token isolation, and Android runtime pending`
- Phase 8 structured weekly check-in: `core implemented and verified locally;
  hosted migration applied; taper review plus pgTAP/real-token/device gates
  remain`
- Phase 8.5 zone intake, field tests, and Week-1 calibration: `backend and
  mobile functional cores, approved-fixture parity, and Zone 1-5 model v1.0
  implemented; original and zone-model hosted migrations/pgTAP/lint verified;
  planner, dependency-advisory, real-token, and device-runtime gates remain;
  physiology review is complete`
- Phase 9: `Polar backend functional core and hosted migration/pgTAP/lint
  verified; provider/legal approval, real OAuth/webhook/storage, retry
  scheduling, security-review choices, and mobile runtime remain pending`
- Phase 10 constrained LLM coach: `weekly-plan explanation slice pulled
  forward and implemented with Structured Outputs, TSS-free facts,
  deterministic fallback, pending-only hosted persistence, mobile display, and
  a successful live provider smoke test; privacy approval, local Supabase
  backend-secret configuration, and context extraction remain`
- Phase 11 and Phase 12: `not started`

## Unresolved roadmap decisions

- BR-009 persistence, ownership, active-version constraints, pending
  replacement behavior, and atomic decisions are implemented and migrated;
  hosted real-token behavior verification remains open.
- Physical-iPhone SDK 57 validation depends on Apple signing and device
  registration, but no longer blocks Android-led Phase 4 mobile development.
- The phase-one activity input is a canonical authenticated summary. Polar
  AccessLink v3 is the provisional Phase 9 adapter and maps into that same
  path; production provider/legal approval remains unresolved.
- Non-race goals are assigned to the new final Phase 12 and require separate
  deterministic rules and catalog coverage before becoming selectable as
  supported plans.
- The functional injury policy, zero-redistribution MVP rule, durable Phase 8
  persistence, weekly review UI, low-only filtering, and rest-only pending plan
  are implemented; qualified clinical production approval of the active rules
  was confirmed complete on 2026-08-24.
- Current-week RPE correction/audit, achieved-goal maintenance, and the exact
  four-complete-week restart baseline are implemented. Phase 8.5 defines RPE
  in this flow as canonical 1-10 RPE and implements reviewed field-test
  threshold formulas plus safe submaximal calibration. The complete
  deterministic conversion from confirmed thresholds to Zone 1-5 is now
  implemented as `start23-zone-model-1.0`, with separate pending threshold and
  zone decisions. Zone-independent normal-plan selection, real-token and mobile
  device verification, and upstream-compatible dependency-advisory resolution
  remain open; deployment and pgTAP verification of the zone-model migration
  are complete.
  Qualified clinical production approval is complete. The original Phase 8.5
  hosted migration, pgTAP, and error-level lint remain verified.
