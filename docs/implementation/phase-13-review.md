# Phase 13 review - updated 2026-09-14

Status: implementation, R1-R5, the final R6-entry audit remediation, and the
bounded H-01/H-04 follow-up are present. R6 hosted execution on 2026-09-14
completed the historical migration upgrade and full tracked database suite, but
R6 remains incomplete because fresh-chain, Railway, hosted-conflict, security,
device, exhaustive real-token, and accountable-review gates remain open. The
[R6 verification report](phase-13-and-14-r6-verification-report.md) supersedes
the older unexecuted-runtime statements retained below as checkpoint history.

## 1. Version

`phase-13-joren-ruleset-1` is the new deterministic Decimal ruleset. The
2026-09-11 mean-heart-rate amendment was incorporated before this version was
released or persisted; existing released versions were not changed in place.

## 2. Implementation

Previous-month hours are validated across all three sports (combined maximum
168 hours), stored as canonical minutes, and converted to the supplied exact
starting coefficients. The final weekly baseline uses half-up one-decimal
rounding; total zero history uses the explicitly approved product value 45.0.
Legacy history cannot silently seed a new plan. Injury load is not redistributed;
missing discipline minima and restricted zero-base allocations fail closed.

Run/bike calibration uses the supplied HR/RPE anchors; swim uses measured
pace/CSS. New integer zone boundaries are contiguous and exclusive. A threshold
below 140 bpm produces a warning and a normal pending proposal. Confirmation
uses the evaluation's model version and retains stale/version preconditions.
The complete 30 textual RPE descriptions are available for Phase 15 presentation.

Planned load uses authoritative timed zone segments. Observed activity load
uses actual zone minutes. With the user's 60-minute run and 10/20/8/3/0 zone
minutes, only 41 minutes are observed; the other 19 minutes are not extrapolated.
If only average HR is available and confirmed HR zones are known, all reliable
training minutes use the zone containing that average. This is recorded as
`average_hr_zone_duration` / `estimated_from_average_hr`, with the exact source
profile, assigned zone and HR; it never pretends to be full observed coverage.
Observed partial times take precedence over this estimate. R5 now rejects an
ordinary correction that changes public average HR after this private snapshot
exists. The owner row is locked, a real RPE correction requires its expected
current value, and exact duplicates remain idempotent. The rejection preserves
the original observation, load, profile snapshot, ruleset, and audit history as
required by R1-D1. Without known HR zones, the estimate is unavailable. Swim
does not acquire an HR fallback.

Distance-only swim records retain distance and nullable duration without
inventing time or load; mobile can record/display them. New realized load does
not use the inactive sRPE formula. All private quantities and provenance remain
outside athlete responses. Planning retains 42-day fallback and 10% progression,
excludes sick weeks, and uses lower realized load for fatigue/missed training.
The taper window is exactly D-7 through D-1.

## 3. Documentation

The previous Phase 13 section was archived first in
`docs/requirements/deprecated-phase-13.md`. The roadmap, versioned specification,
business-rule traceability and physiological formula specification now point to
the active Joren decisions. The consumer trace and implementation sequence are
in `phase-13-implementation-plan.md`. Source-PDF rounding discrepancies and
product decisions are documented explicitly.

The dated [R1 decision record](phase-13-and-14-r1-decisions.md) fixes the
average-HR correction behavior, onboarding version model, current calibration
capability boundary, and R3 identity/physiology migration architecture. The
implementation-plan trace maps every decision to its R1 artifact and later
phase owner.

## 4. Migration

`supabase/migrations/20260910215947_phase_13_joren_ruleset.sql` is a new forward
migration. It adds canonical history, model-aware calculated-profile persistence,
zone-minute activity metrics, private coverage/method/source provenance, a private
load revision audit and a version-filtered planning history RPC. Existing
approval/idempotency/owner checks remain. Previously applied migrations were not
edited. The migration was applied to the linked hosted Supabase project on
2026-09-11; local and remote ledgers align through `20260910215947`.

R1 adds the new forward migration
`20260911180631_phase_r1_onboarding_versioning.sql`. It labels pre-existing
completion as `legacy-unversioned`, preserves the exact linked request ruleset,
adds append-only owner-scoped completion records, and supplies the current
versioned completion entry point. This migration has not been applied locally
or hosted; its pgTAP execution remains an open database gate.

R3 and R2 add the forward migration
`20260912072232_phase_r2_r3_identity_onboarding_calibration.sql`. It creates the
private opaque identity map, backfills and synchronizes dual owners, separates
identifying/physiology records, applies independent least-privilege RLS/RPC
paths, makes completion stale-safe, and adds direct planning and calibration
persistence gates. Legacy owner columns remain only as a documented expand/
cutover compatibility key pending R6 reader/writer proof. This migration has
not been executed against a database; no local or hosted migration success is
claimed.

R4 and R5 add the forward migration
`20260912180000_phase_r4_r5_onboarding_race_activity.sql`. It expands the
versioned onboarding session vocabulary, adds explicit operational
confirmations and structured race fields, replaces current completion/planning
eligibility with onboarding v2, and guards Phase 13 average HR at both the
metric trigger and service-only correction RPC. Generic goal columns and the
R2/R3 dual-owner compatibility key remain for historical/expand-cutover use.
This migration has not been executed against a database; no local or hosted
migration success is claimed. A rollback-only R4/R5 pgTAP suite is present for
R6 execution.

The final audit adds forward migration
`20260913130000_phase_13_14_r6_entry_audit_remediation.sql`. It removes broad
legacy operational table privileges, adds narrow owner-derived operational
RPCs, centralizes the five-race SQL mapping, requires active race-relevant zone
profiles for readiness, hardens structured-race validation, and persists
submaximal calibration estimates with distinct provenance. It retains the
identity map, compatibility columns, historical rows, and old implementation
behind a revoked compatibility function. The rollback-only pgTAP suite is
authored but has not been executed; no database/RLS success is claimed.

## 5. Deprecated and historical behavior

New paths retire two-month distance/frequency baseline assumptions, the Week-2
numeric calibration delay, and RPE-times-duration activity load. sRPE remains a
tested reference capability that is disabled. New planning rejects legacy
RPE-only setup until known zones or calibration are selected.

Historical phase-3/phase-10 calculation versions, old zone/calibration model IDs,
old history columns and persisted load/profile records remain interpretable.
Historical RPE revisions retain their original ruleset label and calculation
method; prior values are audited. No migration recalculates historical load.

## 6. Tests and verification actually executed

- Complete backend suite after R1: **556 passed**. Includes deterministic source fixtures,
  all anchors/coefficients, integer equality and inverse swim boundaries,
  warning equality, observed/mean-HR precedence, missing-duration behavior,
  baseline/injury safeguards, progression/sickness/taper, public contracts,
  pending/stale approval and recursive private-load confidentiality coverage.
- Ruff: passed. Formatting: **126 files already formatted**.
- Full strict mypy, including tests: passed, **125 source files**.
- Mobile strict TypeScript (`npx --offline tsc --noEmit`): passed.
- `git diff --check`: passed; only repository LF/CRLF normalization notices.
- Clean-checkout reconstruction from `HEAD` plus the complete binary diff:
  Phase 13 imports succeeded and **556 tests were discovered**.
- Source-control inspection: all **17** required Phase 13/R1 code, test,
  migration, ruleset, PDF, implementation, review, and remediation artifacts
  are tracked. The unrelated local notes remain untracked.
- Migration chain: **24** timestamped migrations, no duplicate version, with
  `20260911180631` last. PostgreSQL syntax parsing passed for all **42**
  migration/test SQL files. This is syntax verification only.
- Hosted Phase 13 pgTAP SQL: executed through `supabase db query --linked` and
  completed through its rollback and `finish()` statement (`1..18`). A separate
  error-raising hosted verification confirmed the migration ledger, new activity
  schema, private grants, audit trigger, canonical previous-month write and
  cross-owner RLS isolation. Its test rows were rolled back.
- Supabase hosted advisors: completed with no error-level finding. Six warnings
  remain: five existing authenticated `SECURITY DEFINER` API functions and
  project-level leaked-password protection. The owner-scoped activity functions
  are intentional APIs; the warnings were not silently treated as resolved.
- Hosted `supabase db lint` could not authenticate its direct Postgres connection
  because `SUPABASE_DB_PASSWORD` is unavailable. The migration nevertheless ran
  successfully on PostgreSQL, and its SQL/PLpgSQL parser checks passed.
- One existing Starlette/httpx deprecation warning occurred in backend tests.
  Dependencies were not upgraded as part of this work.

New pgTAP coverage checks canonical duration, atomic invalid input rejection,
owner isolation, private grants/RLS and audit/provenance structure; older
onboarding fixtures now express the superseding input contract.

The 2026-09-12 R2/R3 repository verification passed the complete backend suite
with **565 tests**, Ruff, formatting across **128 files**, strict mypy across
app and tests (**128 source files**), OpenAPI and recursive private-load
contracts, mobile strict TypeScript, and `git diff --check`. A new R2/R3 pgTAP
suite covers identity uniqueness/backfill, split-profile grants and owner
isolation, direct-write denial, opaque-owner orphans, planner enforcement, and
calibration persistence enforcement. All **44** migration/pgTAP SQL files pass
local PostgreSQL syntax parsing, but the suite remains unexecuted because no
Docker/Postgres runner is available. At that R2/R3 checkpoint no mobile test
script was configured.

The 2026-09-12 R4/R5 repository verification passes the complete backend suite
with **588 tests**, Ruff, formatting across **129 files**, strict mypy across
app and tests (**129 source files**), targeted OpenAPI/recursive private-load
contracts, mobile strict TypeScript, and **7 configured mobile tests**. Static
migration checks cover v2 prerequisites, structured race constraints,
compatibility retention, direct planner enforcement, owner locking, stale
correction, and HR immutability. The new pgTAP suite covers runtime grants,
invalid/valid timezone and race writes, direct metric protection, duplicate,
changed-HR, successful, and stale correction cases, but remains unexecuted
because no Docker/Postgres/`pg_prove` runner is available.

Targeted final searches covered old duration/RPE load, two-month history,
Week-2/RPE-only state, taper timing, model labels and private response fields.
Historical definitions remain intentionally labeled as historical. No new
physiological formulas were placed in mobile or LLM logic.

## 7. Final R6-entry audit remediation

The 2026-09-13 final audit remediation aligns current calibration discovery
through stale-safe zone activation, gives submaximal estimates distinct
provenance, applies the exact five-race discipline rule across every current
consumer, and makes approved active zone profiles—not setup intent—the only
zone-readiness evidence. It also removes the combined profile mutation,
hardens the retained operational compatibility table behind narrow owner-derived
RPCs, adds explicit SQL/FastAPI race-validation parity, adopts explicit
device-IANA acceptance with manual fallback and no GPS, and labels retired
RPE-times-duration calculations as legacy-only.

Repository verification passes 618 backend tests, Ruff lint, Ruff formatting
across 133 files, strict mypy across 132 source files, strict TypeScript,
unused-code checks, and 19 Jest/RNTL mobile tests in six suites. Static contracts
cover the new forward migration and rollback-only pgTAP suite. The pgTAP suite,
full migration chain, real-token RLS checks, and real-device flows were not run
locally and remain R6 gates.

The 2026-09-14 read-only re-audit follow-up closes the two remaining repository
entry defects without beginning R6. H-01 classifies the retained run/bike field
tests as historical/read-only across discovery, planning catalog, setup,
observation, evaluation, scheduling, confirmation, pending-zone persistence,
and pending-to-active transitions. The approval RPC and an independent database
transition trigger both reject historical calibration activation while leaving
already-active historical provenance unchanged. H-04 reconciles the complete
executable pgTAP directory with the final narrow owner-derived profile contract
and keeps opaque-owner and profile-integrity triggers enabled in fixtures.
Current Phase 13 run/bike submaximal and swim CSS profiles retain normal pending,
stale-safe athlete approval and activation.

The updated repository passes 629 backend tests, Ruff lint/formatting across
132 files, strict mypy across 132 source files, mobile strict/unused TypeScript,
and 19 mobile tests. Static migration and pgTAP contract checks pass. No local
PostgreSQL, Supabase CLI, `psql`, `pg_prove`, Docker, or Podman runtime is
available, so migration execution and the complete pgTAP run remain explicit
R6-only proof; no database runtime success is claimed.

## 8. Open gates

- Run the complete database test directory through a TAP-aware runner and the
  direct hosted schema lint when a database password or suitable runner is
  available. Complete real-token/two-real-user isolation, pending approval and
  activity revision persistence checks remain release evidence.
- Apply and execute the R1, coupled R2/R3, and R4/R5 migrations/pgTAP suites.
  Docker and Podman are unavailable on this workstation, so no local database
  runner was available; the hosted project was not mutated by this local task.
- Device/runtime verification of onboarding resume, timezone detection/fallback,
  calibration warning and approval, and distance-only activity display/input.
  Jest/RNTL now covers executable component interaction and transport behavior,
  but it does not replace physical-device execution.
- Accountable external physiological reviewer and review record for this exact
  version. Production configuration now requires the matching ruleset version
  in addition to the reviewer/record, so an older review cannot authorize it.
- Existing legal/privacy and other production/release gates remain unchanged.

## 9. Deferred rules and future work

Partial-week taper targets remain fail-closed: the retained full-week reduction
is applicable when the seven-day window aligns with a whole planning week.
No new curve is invented for other race weekdays. Adaptive 7-10 day taper,
discipline-specific taper, recovery interaction and advanced race overlap remain
future work. Distance/protocol-only templates without authoritative timed zones
cannot enter private-load-target selection; their distance/protocol content is
preserved. Additional starting allocations/minima require an explicit decision.
Phase 15 may consume the supplied textual RPE catalog in its broader UI work.

## 10. Exit criteria

**Remediation R1, the local R3-then-R2 and R4/R5 implementations, and the final
R6-entry audit remediation are complete; Phase 13 is not marked complete.**
Local domain, API, type, artifact, source-control, and clean-archive verification
and the earlier hosted Phase 13 checks pass. R6, execution of all unexecuted
remediation migration/database suites, runtime/device evidence, and accountable
external review are still open. This report does not represent release approval.
