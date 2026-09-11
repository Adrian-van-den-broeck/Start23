# Phase 13 review ? 2026-09-11

Status: implementation and hosted Phase 13 migration present; remediation R1
complete locally; runtime, R1 database, and external exit gates remain open.

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
Observed partial times take precedence over this estimate. The R1 audit found
that the ordinary RPE correction path can currently change public average HR
after this private snapshot exists. R1-D1 requires that change to be rejected;
R5 owns the atomic correction fix. Without known HR zones, this estimate is
unavailable. Swim does not acquire an HR fallback.

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

## 5?6. Deprecated and historical behavior

New paths retire two-month distance/frequency baseline assumptions, the Week-2
numeric calibration delay, and RPE-times-duration activity load. sRPE remains a
tested reference capability that is disabled. New planning rejects legacy
RPE-only setup until known zones or calibration are selected.

Historical phase-3/phase-10 calculation versions, old zone/calibration model IDs,
old history columns and persisted load/profile records remain interpretable.
Historical RPE revisions retain their original ruleset label and calculation
method; prior values are audited. No migration recalculates historical load.

## 7?8. Tests and verification actually executed

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

Targeted final searches covered old duration/RPE load, two-month history,
Week-2/RPE-only state, taper timing, model labels and private response fields.
Historical definitions remain intentionally labeled as historical. No new
physiological formulas were placed in mobile or LLM logic.

## 9. Open gates

- Run the complete database test directory through a TAP-aware runner and the
  direct hosted schema lint when a database password or suitable runner is
  available. Complete real-token/two-real-user isolation, pending approval and
  activity revision persistence checks remain release evidence.
- Apply and execute the R1 onboarding-version migration/pgTAP suite. Docker and
  Podman are unavailable on this workstation, so no local database runner was
  available during R1; the hosted project was not mutated by this local task.
- Device/runtime verification of onboarding resume, calibration warning and
  approval, and distance-only activity display/input. No mobile test runner is
  configured in `mobile/package.json`; typechecking does not replace this gate.
- Accountable external physiological reviewer and review record for this exact
  version. Production configuration now requires the matching ruleset version
  in addition to the reviewer/record, so an older review cannot authorize it.
- Existing legal/privacy and other production/release gates remain unchanged.

## 10. Deferred rules and future work

Partial-week taper targets remain fail-closed: the retained full-week reduction
is applicable when the seven-day window aligns with a whole planning week.
No new curve is invented for other race weekdays. Adaptive 7?10 day taper,
discipline-specific taper, recovery interaction and advanced race overlap remain
future work. Distance/protocol-only templates without authoritative timed zones
cannot enter private-load-target selection; their distance/protocol content is
preserved. Additional starting allocations/minima require an explicit decision.
Phase 15 may consume the supplied textual RPE catalog in its broader UI work.

## 11. Exit criteria

**Remediation R1 is complete; Phase 13 is not marked complete.** Local domain,
API, type, artifact, and source-control verification and the earlier hosted
Phase 13 checks pass. R2-R6, the R1 migration/database suite, runtime/device
evidence, and accountable external review are still open. This report does not
represent release approval.
