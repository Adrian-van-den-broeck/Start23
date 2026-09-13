# Phase 13 and 14 remediation roadmap

Status: R1 complete locally on 2026-09-11. R3 foundation and R2 behavior were
implemented together locally on 2026-09-12, in that order. R4 and R5 were
implemented together locally on 2026-09-12. Database execution, real-token,
two-user, and device evidence remains open under R6; R6 has not begun.

This roadmap converts the read-only Phase 13 and Phase 14 implementation audit
into ordered remediation work. It is an implementation companion to
[the MVP roadmap](mvp-roadmap.md), not a replacement or a new source of product
or physiological rules. The current MVP roadmap and the approved versioned
Phase 13 ruleset remain authoritative.

Do not invent missing physiological, safety, migration, privacy, or product
behavior while carrying out this roadmap. Record and obtain an explicit
decision where a required behavior is still undefined.

## Mandatory MVP-roadmap synchronization

Completion in this document is not sufficient on its own. When a remediation
item or phase is implemented and verified, update the corresponding Phase 13 or
Phase 14 status, scope, exit criteria, and verification evidence in
`docs/implementation/mvp-roadmap.md` in the same reviewed change. Do not mark a
remediation phase complete while the MVP roadmap still describes the fixed item
as open, and do not mark Phase 13 or Phase 14 complete solely because this
follow-up roadmap says so.

Every completed remediation phase must retain links or references to its tests,
migration evidence, review record, and any approved decision that changed the
expected behavior.

## Delivery order and dependencies

1. Remediation Phase R1 establishes a reproducible audited baseline.
2. Remediation Phase R3 establishes the opaque identity and privacy-safe
   profile architecture used by all following work.
3. Remediation Phase R2 resolves the end-to-end Phase 13/14 blockers on that
   architecture.
4. Remediation Phase R4 completes the remaining onboarding and race inputs.
5. Remediation Phase R5 closes activity consistency and mobile-quality gaps.
6. Remediation Phase R6 performs database, security, integration, and release
   verification across the completed work.

R2 can begin after the affected artifacts are identified in R1. R3 and R4 may
be developed independently after their migration and compatibility decisions
are approved, but both must be complete before R6. R5 must not define a new
load-correction rule without explicit approval.

## Remediation Phase R1: baseline, provenance, and decision closure

Status: complete on 2026-09-11. This does not mark Phase 13 or Phase 14
complete.

### Objective

Make the audited Phase 13/14 implementation reproducible and resolve the design
questions that later remediation phases must not guess.

### Work

- Review and place the intended Phase 13 domain module, tests, migration,
  pgTAP tests, ruleset, review, and implementation documents under source
  control. Keep local notes and superseded material clearly separated.
- Confirm that a clean checkout contains every artifact imported or required by
  the Phase 13 implementation and can discover the full migration chain.
- Record the approved behavior for an average-HR correction after a Phase 13
  private load already exists: reject the HR change, or atomically recalculate
  using the originating profile while retaining immutable audit provenance.
- Approve the forward-only migration and backfill design for separating
  identifying and physiological profile data. Define retention of existing
  values and the opaque athlete-identifier lifecycle.
- Define an explicit onboarding/ruleset version and upgrade state for existing
  completed and RPE-only users.
- Confirm that all selectable run/bike calibration guidance modes must collect
  average HR, or explicitly remove unsupported modes. Do not change the
  approved Phase 13 physiological algorithm.

### Exit criteria

- A clean checkout contains all required Phase 13/14 artifacts.
- The three behavioral/migration decisions above have dated, accountable
  records and are traceable from the implementation plan.
- No applied migration has been rewritten.
- The MVP roadmap is updated in the same change with the resulting decisions
  and the current Phase 13/14 status.

### Required verification

- Clean-checkout backend import and test discovery.
- Migration-order and duplicate-version checks.
- Ruleset/provenance traceability review.
- `git diff --check`, Ruff, strict mypy, and mobile strict TypeScript.

### Completion evidence

- The dated [R1 decision record](phase-13-and-14-r1-decisions.md) is traced from
  the Phase 13 implementation plan.
- All 17 intended Phase 13/R1 artifacts are tracked. A clean `HEAD` export plus
  the complete binary diff imported the Phase 13 modules and discovered all
  556 backend tests.
- All 24 migrations have unique, increasing 14-digit versions; the two newest
  Phase 13/R1 migrations are forward-only and no applied migration changed.
- Full backend tests passed (556), Ruff and formatting passed, full strict mypy
  including tests passed (125 files), mobile strict TypeScript passed, and
  `git diff --check` passed.
- All 42 migration/pgTAP SQL files passed PostgreSQL syntax parsing. Docker and
  Podman are unavailable, so the new R1 migration and pgTAP suite remain an
  explicit database verification gate for R6; R1 completion does not claim
  database execution.
- The synchronized Phase 13/14 status and still-open exit criteria are recorded
  in the MVP roadmap. No R2 work was started.

## Remediation Phase R2: unblock onboarding and calibration

Status: implementation complete locally on 2026-09-12 on top of the R3
foundation. Database/pgTAP, real-token, mobile-device, and release evidence is
still an R6 gate. This status does not mark Phase 13 or Phase 14 complete.

### Objective

Make both new-athlete and existing-athlete flows reach a valid, pending Phase 13
zone proposal and then planning without bypassing current prerequisites.

### Work

- Introduce a version-aware onboarding upgrade flow. A previously completed
  session must reopen only the requirements introduced after its stored
  onboarding/ruleset version.
- Preserve historical RPE-only records and provenance without accepting them as
  a current Phase 14 completion route.
- Enforce the same completion conditions in the mobile UI, API service,
  database RPC, and planner. Direct RPC use must not bypass the upgrade.
- Add measured elapsed swim time to the calibration observation flow and pass
  it through the mobile, API, service, and deterministic domain contracts.
  Derive elapsed time from repetitions only if an approved specification says
  to do so.
- Require measured average HR for every exposed run/bike Phase 13 calibration
  route. Remove or disable pace-only/power-only configurations that cannot
  satisfy the evaluator.
- Correct calibration capability metadata and user-facing copy so it accurately
  describes creation of a pending threshold/zone proposal and the separate
  athlete-confirmation step.

### Exit criteria

- A pre-Phase-13 completed user is directed through only the outstanding
  history and zone requirements, then can plan successfully.
- An existing RPE-only user cannot silently complete under the obsolete route
  and can upgrade without historical reinterpretation.
- A new swim user can submit the actual mobile payload and receive a pending CSS
  and zone proposal.
- Every calibration mode selectable in mobile can satisfy its evaluator when
  valid measurements are supplied.
- Zone activation remains pending, stale-safe, idempotent, and explicitly
  athlete-confirmed.
- Phase 13 and Phase 14 status/evidence in the MVP roadmap are updated in the
  same change.

### Required verification

- Mobile-to-API-to-domain contract tests for run, bike, and swim.
- Existing-completed and legacy-RPE-only upgrade tests at service and RPC level.
- Missing/malformed swim time and distance tests.
- A selectable-mode matrix proving no exposed configuration is guaranteed to
  fail.
- Pending approval, duplicate submission, stale version, and historical
  provenance tests.

### Completion evidence

- The version assessment now drives explicit fresh, current, incomplete, and
  `legacy-unversioned` resume states. Mobile shows the retained historical
  completion and only the derived missing steps; completion requires the
  session revision, is replay-idempotent, and appends current provenance
  without deleting the legacy completion record.
- One shared deterministic Python prerequisite assessment is used by
  onboarding and planning. A service-only eligibility-context RPC supplies the
  same current session/request versions to service planning contexts. Database
  triggers on weekly plans, plan revisions, and swipe drafts apply the SQL
  equivalent to all persistence/direct-RPC writes.
- Current protocol discovery keeps historical run/bike field tests and
  unsupported guidance out of selection. Current run/bike result observations
  require measured average HR and block RPE; swim requires measured elapsed
  time, distance, and block RPE. The mobile swim form sends elapsed time as an
  independent measurement. A new insert trigger applies the same contract to
  direct calibration-observation RPC persistence without changing old rows.
- Calculated field-test zones still enter the existing pending proposal flow;
  activation remains a separate stale-safe athlete decision. Capability
  metadata now states its observation, result, and pending lifecycle.
- The complete backend suite passed with 565 tests; Ruff, formatting, strict
  mypy including tests, OpenAPI/private-load contracts, and mobile strict
  TypeScript passed. All 44 migration/pgTAP SQL files passed local PostgreSQL
  syntax parsing. The R2/R3 pgTAP file was authored but not executed because
  Docker/Postgres is unavailable; that execution remains R6 evidence.

## Remediation Phase R3: privacy-safe identity and physiology profiles

Status: foundation and application cutover complete locally on 2026-09-12.
Database/pgTAP execution and two-real-user proof remain open under R6. This
status does not mark Phase 13 or Phase 14 complete.

### Objective

Implement the Phase 14 data separation and access boundaries without exposing
identifying or physiological data across athletes or to the mobile service-key
boundary.

### Work

- Add separate identifying and physiological profile records linked through an
  opaque internal athlete identifier.
- Store first name and last name in the identifying profile. Keep date of birth
  and resting heart rate in the physiological profile.
- Apply least-privilege grants and RLS independently to both records. Use
  RPC-only writes where the Phase 14 design identifies a critical write.
- Derive the athlete from the verified access token; never accept a client
  `user_id` as authority.
- Forward-migrate existing records according to the approved R1 retention and
  backfill decision. Preserve historical provenance and do not reinterpret old
  physiological values.
- Update typed API contracts and the mobile profile flow without exposing
  service credentials or private-load data.

### Exit criteria

- Identity and physiology are independently stored and protected.
- First name, last name, date of birth, and resting heart rate are retained in
  the approved records and exposed only through intended contracts.
- Two real users cannot read or mutate each other's identity or physiology
  through tables, views, or RPCs.
- Existing athletes migrate without loss or unintended reinterpretation.
- The Phase 14 profile status, migration decision, and RLS evidence are updated
  in the MVP roadmap in the same change.

### Required verification

- Forward-migration and backfill tests from representative historical states.
- pgTAP grants, ownership, search-path, RLS, and direct-table/RPC tests.
- Two-real-user isolation tests for reads and mutations.
- OpenAPI/public-contract and recursive private-load/TSS leak tests.
- Mobile secret and accessibility-label inspection.

### Completion evidence

- Forward migration
  `20260912072232_phase_r2_r3_identity_onboarding_calibration.sql` adds the
  private one-to-one Auth-user/opaque-athlete map, deterministic existing-user
  backfill, fresh-user trigger, and immutable dual-owner synchronization.
  Thirty-nine existing owner-bearing tables receive indexed opaque FKs; 38 are
  non-null and the webhook receipt keeps its intentional paired-null PING state.
  The legacy Auth key remains an explicitly bounded compatibility key pending
  the R6 contract-removal proof.
- First/last name and DOB/resting-HR are stored in independently forced-RLS
  identifying and physiological tables. Operational timezone/onboarding state
  remains in the bounded legacy operational profile. Backfill copies existing
  physiological values exactly and records source metadata without exposing
  that migration provenance in athlete grants or RPC responses.
- Athlete-facing code resolves the opaque ID from the verified token and never
  accepts an authoritative client owner ID. New owner-aware repositories query
  opaque columns; service-only adapters translate only at stored procedures
  that still require the legacy key. Token-scoped calls that do not pass an
  owner remain authentication-boundary compatibility paths.
- Split-profile table grants are column-limited, writes are owner-derived RPC
  paths, and independent RLS policies prevent cross-owner access. Public
  `/me` returns only the opaque athlete ID. No service credential was added to
  Expo and recursive public-contract tests remain private-load/TSS free.
- Static migration and application tests cover mapping uniqueness, fresh and
  existing users, idempotent backfill, split data contracts, old-record resume,
  owner filtering, direct-write denial, and representative orphan checks. The
  new pgTAP scenarios require execution in R6 before hosted isolation or
  migration success may be claimed.

## Remediation Phase R4: complete onboarding prerequisites and race goals

Status: implementation complete locally on 2026-09-12. The forward migration
and pgTAP suite are authored but unexecuted; their runtime proof remains an R6
gate. This does not mark Phase 13 or Phase 14 complete.

### Objective

Complete the remaining approved Phase 14 onboarding inputs and enforce them at
every boundary that can complete onboarding or start planning.

### Work

- Add explicit, persisted confirmation of heart-rate-monitor access. Enforce it
  in mobile, API, database completion, and planning. Manual average-HR entry
  remains supported as already specified.
- Replace silent timezone defaults and free text with device-reported IANA
  resolution and a validated explicit IANA-timezone fallback. Require explicit
  confirmation and retain the relevant source/audit state where approved.
- Replace the generic/hardcoded triathlon goal with typed run, bike, swim,
  triathlon, and duathlon configurations.
- Require race name, date, every selected discipline's distance, and total
  target time. Support optional per-discipline target times and a specific
  focus.
- Remove the standalone generic goal fields from new public/mobile writes as
  required, while applying the approved historical retention decision.
- Ensure structured race inputs enter planning without hardcoded disciplines or
  silent defaults.

### Exit criteria

- Onboarding and planning reject missing monitor confirmation or unconfirmed
  timezone, including direct RPC attempts.
- Automatic device resolution and the unavailable/declined fallback both reach
  an explicitly confirmed valid IANA zone without guessing.
- All five race types validate their conditional required and optional fields.
- Standalone and multisport goals produce correct discipline-specific planning
  inputs.
- Phase 14 scope, status, exit criteria, and verification evidence are updated
  in the MVP roadmap in the same change.

### Required verification

- Monitor prerequisite tests at mobile, API, RPC, and planner boundaries.
- Timezone detection, denial, invalid-zone, confirmation, and DST-sensitive
  tests.
- Valid/invalid schema matrices for all race types.
- Migration compatibility for historical generic goals.
- Planning snapshot and locked-personal-goal regression tests.

### Completion evidence

- Onboarding version `phase-14-onboarding-v2` adds independent derived monitor
  and timezone steps. Fresh, legacy-completed, partially upgraded,
  interrupted/replayed, already-populated, and current-state tests prove that
  only missing evidence is requested and current completion remains stale-safe
  and idempotent.
- The API and operational-profile RPC persist an explicit monitor assertion
  without requiring a provider. A default/legacy timezone remains unconfirmed;
  device resolution is shown for explicit acceptance, and the manual fallback
  is validated against IANA data in Python and PostgreSQL. Planning re-derives
  both prerequisites, the R3 direct-write triggers call the replaced SQL
  eligibility function, calibration rejects an unconfirmed schedule timezone,
  and activity writes must match the confirmed persisted profile timezone.
- Current onboarding accepts only separate previous-month hours/week for swim,
  bike, and run. Structured race writes cover run, bike, swim, triathlon, and
  duathlon with conditional distances, total time, optional discipline times,
  race name, and focus. The old generic RPC loses authenticated execution while
  old columns and rows remain stored for compatibility/history.
- Forward migration
  `20260912180000_phase_r4_r5_onboarding_race_activity.sql` expands the current
  session constraints, operational confirmation state, structured goal shape,
  v2 completion, planning snapshot, and SQL eligibility checks without removing
  the R2/R3 dual-owner compatibility contract.
- Local service/schema/planner tests, static migration tests, strict TypeScript,
  and seven configured mobile logic/source-contract tests pass. Existing local
  week and DST suites continue to pass. Database execution and real-device
  permission/fallback behavior remain R6 evidence.

## Remediation Phase R5: activity consistency and mobile regression coverage

Status: implementation complete locally on 2026-09-12. The database trigger,
correction wrapper, and pgTAP scenarios are unexecuted pending R6. This does not
mark Phase 13 or Phase 14 complete.

### Objective

Close the remaining Phase 13 activity inconsistency and prevent mobile/domain
contract drift from recurring.

### Work

- Implement the approved R1 average-HR correction behavior atomically. Preserve
  the originating ruleset, zone profile, input snapshot, old value, and audit
  history as required by that decision.
- Preserve optimistic-concurrency and idempotency semantics for activity
  corrections; do not use unconditional last-write-wins behavior.
- Correct pending distance-only swim presentation so a missing duration is not
  rendered as zero minutes.
- Remove the superseded inline onboarding zone-step implementation after
  confirming the active `ZoneSetupStep` is the sole path.
- Add automated mobile component/contract coverage for profile, goal, zone
  setup, calibration, pending approval, upgrade, and activity rendering.

### Exit criteria

- Public average HR and private load provenance cannot silently disagree after
  a correction.
- Distance-only observations are shown without fabricated duration.
- There is one authoritative mobile zone-setup implementation.
- Critical Phase 13/14 mobile flows have automated regression coverage.
- Corresponding Phase 13/14 implementation and verification notes are updated
  in the MVP roadmap in the same change.

### Required verification

- Original-HR, changed-HR, duplicate, and stale-correction tests.
- Recursive TSS/private-load leak tests after every activity-contract change.
- Mobile component tests for nullable duration/distance presentation.
- End-to-end mocked-contract tests using the exact serialized mobile payloads.
- Full strict TypeScript and unused-code checks.

### Completion evidence

- The API requires an expected-current-RPE precondition for a real correction,
  accepts exact duplicates idempotently, and returns a typed conflict for stale
  writes. Changed average HR is rejected once the Phase 13 private-load record
  exists, before any RPE/load mutation; omission or the exact stored value is
  allowed. Existing load, originating profile/HR snapshot, ruleset, and audit
  provenance therefore remain aligned under approved decision R1-D1.
- The forward migration adds a direct-table HR guard and a service-only,
  owner-scoped, row-locking correction wrapper around the existing atomic
  revision operation. The original operation remains private compatibility
  implementation rather than being removed in this expand/cutover phase.
- Run/bike calibration retains measured average HR plus textual block RPE;
  swim retains measured elapsed time/distance and pace/CSS. Pending threshold,
  separate zone proposal approval, stale-safe activation, warnings, and
  ruleset/model provenance remain unchanged. Mobile now uses only the persisted
  confirmed profile timezone and omits historical protocols absent from current
  discovery.
- Distance-only swim cards render distance rather than `0 min`, and explanatory
  copy states that duration/zone time were not inferred. Partial-HR copy states
  that only observed zone time was used. Neither representation exposes private
  load/TSS. The superseded inline zone step is removed; `ZoneSetupStep` is the
  sole implementation.
- Original/same/changed HR, duplicate and stale correction, unavailable swim
  load, partial observed coverage, pending/stale zone approval, disabled
  calibration mode, no-auto-activation, public-contract, and recursive privacy
  checks pass locally. The new pgTAP scenarios remain unexecuted until R6.

## Remediation Phase R6: database, security, integration, and release closure

### Objective

Verify the complete remediated implementation across real persistence,
privilege, device, and historical-upgrade boundaries before changing either
Phase 13 or Phase 14 to complete.

### Work

- Run the entire forward migration chain in a disposable database from both a
  fresh state and representative pre-Phase-13/14 states.
- Expand and run pgTAP coverage for calibration persistence, pending approvals,
  previous-month history, activity load/amendment provenance, illness/fatigue,
  planning proposals, idempotency, stale versions, grants, RLS, and function
  ownership/search paths.
- Execute two-real-user isolation tests against the real Supabase data path.
- Run the complete new-user and existing-user flows through mobile, API,
  database, pending confirmation, and planning.
- Complete iOS and Android real-device checks.
- Obtain the qualified accountable physiology review and retain its dated
  review record.
- Run hosted migration-ledger, lint, RLS/advisor, privilege, and key-boundary
  checks before release.

### Exit criteria

- All required backend, Ruff, formatting, strict mypy, OpenAPI, privacy-leak,
  strict TypeScript/mobile, migration, pgTAP, RLS, integration, and real-device
  checks pass.
- No blocker or high-severity finding in this roadmap remains open.
- The qualified reviewer has approved the active Phase 13 ruleset evidence.
- Hosted and repository migration ledgers agree.
- The MVP roadmap is updated in the same reviewed change with final Phase 13
  and Phase 14 status, executed evidence, external review, and any remaining
  release gates. Only the MVP roadmap may declare those phases complete.

### Required verification record

Record exact commands, environments, pass/fail counts, migration versions,
device/platform results, real-user RLS scenarios, hosted advisor results, and
the accountable reviewer/date. An unavailable check remains an explicit open
gate; local unit-test success alone is not completion.

## Finding-to-remediation mapping

| Audit finding | Remediation phase |
| --- | --- |
| Existing-user onboarding/planning dead end | R1, R2 |
| Swim calibration payload cannot satisfy evaluator | R2 |
| Invalid exposed run/bike calibration modes and misleading metadata | R1, R2 |
| Missing identity/physiology split and name fields | R1, R3 |
| Missing heart-rate-monitor prerequisite | R4 |
| Missing structured race configuration | R4 |
| Unsafe timezone default/free text | R4 |
| Insufficient database/RLS execution and two-user coverage | R3, R6 |
| Untracked Phase 13 release artifacts | R1 |
| Full strict-mypy failures | R1, R6 |
| Average-HR/private-load correction divergence | R1, R5 |
| Missing mobile automated coverage | R2, R4, R5 |
| Distance-only pending swim display | R5 |
| Superseded inline onboarding zone code | R5 |
