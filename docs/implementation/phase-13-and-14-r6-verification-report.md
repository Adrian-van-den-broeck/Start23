# Phase 13/14 R6 runtime and release verification

## Software blocker closure — 2026-09-16

The final software-level R6 MVP blocker is closed in committed candidate
`0e0031120fb2f6f9d0482214a3ce7484cb527450`. Production and staging were not
deployed or otherwise modified.

When a brand-new athlete's first race-anchored week is a nominal recovery
position and no prior plan/load history exists, planning now creates a normal
base week from the existing private onboarding Start-TSS target. It does not
call the recovery calculation, invent a week-4 value, or apply the 60%
reduction. The race anchor is unchanged, and an established athlete with prior
history still receives the existing deterministic recovery target from the
latest approved planned-load snapshot.

No public contract, mobile code, database schema, migration, private-load
formula, progression factor, recovery factor, ruleset identifier, persistence
lifecycle, revision precondition, or idempotency behavior changed.

Verification from the committed software candidate:

- full backend: 635 passed, with the existing Starlette/httpx deprecation
  warning only; the optional coach key was explicitly disabled so the run used
  the deterministic hermetic fallback;
- targeted planning/progression/recovery: 116 passed;
- relevant migration/database static contract tests: 21 passed;
- Ruff lint passed and 136 Python files were already formatted;
- strict mypy passed for 132 app/test source files;
- `git diff --check` passed before the candidate commit.

Mobile tests/typecheck and database runtime tests were not rerun because this
change affects neither public/mobile contracts nor persistence. No migration
was required.

**Software outcome: SOFTWARE R6 MVP GATES PASSED.** Physical-device execution
and the accountable physiological-review record remain open release gates and
are not marked passed.

## Final recovery staging runtime gate — 2026-09-16

The final recovery software candidate
`0e0031120fb2f6f9d0482214a3ce7484cb527450`, with only evidence documentation
commit `2253c2c759ba1c345082f0a665d19f94317ba38f` after it, was pushed on `main`
and confirmed at `origin/main`. The backend directory at that HEAD was deployed
only to Railway environment `r6-staging`, service `r6-api`. Railway deployment
`eaf5001f-910e-410f-942e-c45a5aa6acb9` completed with status `SUCCESS`; its
deployment message records both the software candidate and deployed HEAD, and
its immutable image digest is
`sha256:6bb8df66d8e194c2957c53171c505c4b6911ddd811328731aaf3f01567b57d66`.
The staging `/health` and `/ready` endpoints returned `ok` and `ready` with
`environment=staging`. Startup logs for that bounded deployment showed a normal
application start. Production was not targeted or modified.

The deployed flow was exercised against development Supabase project
`start23-dev` (`isfumhgqphieoayqahjv`) with two newly created, tagged test
athletes:

- The fresh athlete completed normal profile, race, previous-month training
  history, run calibration, zone approval and onboarding steps. Their first
  race-anchored week landed on the nominal recovery position. Planning
  succeeded as a `base` week with `initial_catalog_baseline`; a private,
  read-only database check found target TSS `194.1`, derived by the existing
  Start-TSS rule from three weekly run hours. The athlete had zero prior weekly
  plans, so no historical week-4 value was present or fabricated, and no
  recovery reduction was applied.
- The established control first created and approved its ordinary build week,
  then completed and confirmed the next-week check-in. Its race-anchored next
  week produced the existing pending `recovery` / `recovery_factor` proposal.
  The private target exactly equalled 60% of the prior approved planned load,
  preserving the deterministic established-athlete recovery model.
- Every successful athlete-facing response in both flows was recursively
  checked and contained no private TSS/load key. Private values were inspected
  only through a guarded read-only development-database query and were not
  exposed through the public API.
- Cleanup deleted both temporary Auth users and their cascaded test data: 2/2.

**Final recovery runtime outcome: PASSED.** This evidence does not change the
open physical-device or accountable physiological-review gates and is not a
production-deployment authorization.

## Current MVP continuation — 2026-09-15

This section supersedes the archived 2026-09-14 release assessment below.
Production was not modified. Leaked-password protection, non-critical advisors,
optional providers and legacy ownership cutover are explicitly outside this
MVP continuation. Retaining dual-key compatibility is not a failed MVP gate.

Original main baseline: `9c6be883918255a92644a8c69525a2d6cf14b071`.
Committed runtime/verification candidate:
`9f622db2511c14f805cd191cd793a8afe91de72c`.
Evidence documentation is committed separately and is not a new deployed
application candidate. All intended migrations, tests and scripts are tracked
in the candidate, whose worktree was clean before final deployment. The final
repository worktree is also clean. No environment files
or credential values were committed.

### Environments and runtime fixes

- Supabase: **start23-dev**, `isfumhgqphieoayqahjv`, explicitly non-production.
- Railway: project `c0cf7bc7-abe8-4db5-857a-85cc39850640`, new empty environment
  `r6-staging` (`875b7e64-0f3f-4e42-9efd-973dfb6e295b`), service `r6-api`
  (`6c2cb45b-43e1-43c1-983f-1ed154b2ac76`). No production environment was cloned.
  URL: `https://r6-api-r6-staging.up.railway.app`.
- Only development Supabase URL/publishable/secret keys and
  `START23_ENVIRONMENT=staging` were configured. Values were handled in memory,
  not printed. No production Auth credentials, Polar or LLM credentials copied.
- Production deployment remained `c51eb090-9e86-4773-a08b-d27eb14dbd34` at the
  read-only comparison. No production deploy, migration or configuration write.

Forward-only migrations applied to development:

1. `20260915081055_r6_mvp_nonretryable_business_conflicts.sql`: changes 28
   intentional MVP business-conflict functions from `40001` to `PT409` while
   retaining function signatures, grants, ownership and fixed search paths.
   Genuine PostgreSQL serialization errors are not caught or rewritten.
   The three optional Polar-only functions are excluded from this MVP audit.
2. `20260915082320_r6_onboarding_completion_step_vocabulary.sql`: permits the
   already-required monitor/timezone step names in immutable completion history.
   Real Railway onboarding exposed the old check constraint; no historical row
   or migration was rewritten to repair it.
3. `20260915205627_r6_checkin_context_and_account_deletion.sql`: carries current
   onboarding completion provenance into trusted check-in planning and makes all
   four initial-request dependents cascade deterministically on Auth account
   deletion. The retained plan-owning test user and both final flow users then
   deleted successfully.

Backend mappings accept `PT409` as conflict. Hosted Data API exact-key/exact-body
retries return the original activity; changed fingerprints return HTTP 409 with
`PT409` within the verifier's 10-second bound, not a timeout/retry loop. Stale
zone approval also returned HTTP 409 through Railway.

Railway additionally exposed the planner reading only the historical `metric`
field. It now consumes current calibration `metric_profiles`; run/bike HR and
swim CSS planning capability regression tests cover this boundary. Physiological
formulas were not changed.

### Current gate evidence

| MVP gate | Status | Evidence |
| --- | --- | --- |
| Immutable code and environment safety | PASS | Tracked candidate above; development-only variables and separate Railway environment. |
| Hosted deterministic conflict | PASS | Real-token Data API same-key replay succeeds; changed fingerprint returns prompt HTTP 409/PT409; temporary users cleaned up. |
| Database regression | PASS | All 24 tracked SQL/pgTAP suites passed, zero failing assertions, including current calibration lifecycle and historical activation guards. Hosted dry-run reports up-to-date through `20260915205627`. |
| Real-token Data API isolation | PASS | Two real Auth password tokens; 30 accessible and 2 denied table surfaces per user; inverse read/mutation checks, split/operational profiles, goal/activity, identity authority, private schema/load and service-only boundaries passed; cleanup 2/2. |
| Railway complete MVP flow | PASS | Deployment `0208f093-9bf2-4fb1-9f4c-2def3ebaee18` identifies the exact candidate SHA. Health=`ok`, readiness=`ready`, environment=`staging`. A real client signup (development email confirmation followed by password token) and a representative legacy user passed profile/monitor/timezone/race/history, calibration, pending zone approval, onboarding/resume and inverse ownership. Initial plan stayed pending until approval; a planned partial-HR activity persisted observed-only private provenance; exact retry and stale revisions behaved deterministically; the next race-anchored recovery week produced a pending `recovery_factor` proposal. Cleanup 2/2. |
| Automated backend/mobile | PASS | 632 backend tests; Ruff check/format (including verifiers); strict mypy 132 files; mobile 6 suites/19 tests, TypeScript and unused checks. |
| Primary-platform real device | BLOCKED | ADB returned no attached Android device on 2026-09-15. No physical-device flow claimed. |
| iOS device | NOT EXECUTED | Windows environment; signing/device access unavailable. |
| Accountable physiological review | BLOCKED | Ruleset/source documents exist; no named qualified reviewer and identifiable approval record. No self-approval or fabricated evidence. |
| Legacy compatibility removal | NOT EXECUTED | Explicitly excluded; compatibility retained. |

The legacy Railway fixture is a newly created, tagged development Auth user
with a representative old completed onboarding session. It does not claim to
represent a migrated historical plan/activity corpus. The separate historical
upgrade evidence below is retained without redesigning that exercise.

Every successful public Railway response was recursively checked for private
load/TSS keys. A post-flow scan of 500 staging log lines found zero matches for
planned/realized TSS, private-load, secret-key or bearer-token patterns.

The first-plan race-anchored recovery edge recorded by this 2026-09-15 run is
closed by the approved 2026-09-16 product decision and candidate
`0e0031120fb2f6f9d0482214a3ce7484cb527450`, with the local evidence recorded
above. The older Railway trace remains valid evidence for the established-
athlete recovery path; no new deployment was performed for the software-only
closure.

### Remaining MVP release gates and production plan

Complete the primary-platform physical-device checklist and obtain the
accountable physiological reviewer identity and approval record for
`phase-13-joren-ruleset-1`. Do not mark Phase 13/14 complete from automated gates.

After those gates pass, request a **separate explicit production authorization**.
The production step must: record target IDs, current deployment and migration
ledger; confirm backup/recovery posture; compare the ledger with this candidate
and stop on divergence; dry-run and apply only missing forward migrations in
repository order; deploy the approved candidate with production-only secrets;
verify health/readiness and bounded token/ownership/idempotency smoke tests;
publish the verified signed mobile build; monitor errors and privacy signals.
No down-migration or ownership cutover is included. Keep the previous compatible
application available for rollback; database repairs remain forward-only.

**Current software outcome: SOFTWARE R6 MVP GATES PASSED. Overall release gates
remain incomplete because device execution and accountable physiological review
are still open.**

## Archived full-matrix assessment — 2026-09-14

The following is historical evidence, not the current MVP blocker list or
authorization to execute its older broader release plan.

Date: 2026-09-14

Baseline branch: `main`

Baseline SHA recorded before any R6 action:
`9c6be883918255a92644a8c69525a2d6cf14b071`

## Verdict

R6 is incomplete. Production was not mutated. The legacy dual-owner
compatibility layer was not removed.

The hosted historical upgrade, complete tracked database suite, calibration
runtime, local backend suite, and mobile static suite passed. Release remains
blocked by the absence of a disposable fresh-chain database, the absence of a
non-production Railway environment, a reproducible hosted PostgREST conflict
timeout, disabled leaked-password protection, incomplete real-token RPC and
device coverage, and the missing accountable physiological review.

The R6 fixes are an uncommitted working tree derived from the recorded baseline.
They are not yet an immutable deployable Git revision.

## Stage result

| R6 stage | Status | Evidence and reason |
| --- | --- | --- |
| 1. Environment / revision safety | **BLOCKED** | `main` and `HEAD` were both the recorded SHA before changes. Supabase `start23-dev` (`isfumhgqphieoayqahjv`) is non-production and its initial ledger matched the repository through `20260910215947`; the remaining repository migrations were pending in order. Railway has only its `production` environment, so there is no approved Railway target. Production was not touched. |
| 2. Database migration chain | **BLOCKED** | The representative historical hosted state upgraded successfully through all 18 R6-applied migrations and the final local/hosted ledger is aligned through `20260914180000`. Integrity queries found no unmapped, duplicate, orphan, or dual-owner mismatch. A fresh-chain run was not executed: Docker, Podman, `psql`, and `pg_prove` are absent and the linked project has no disposable branch. |
| 3. All pgTAP / database tests | **PASS** | All 23 tracked SQL test files executed against the fully migrated hosted development database with zero failing TAP assertions, SQL errors, or disabled-trigger dependencies. Eighteen planned suites produced 431 passing assertions; five SQL assertion/catalog suites completed without error. |
| 4. Real-token RLS / two-user security | **FAIL** | Two real confirmed Supabase Auth users and password access tokens passed inverse isolation across 32 owner-table surfaces, split profiles, operational RPCs, goals, activities, opaque identity, private schemas, and service-only identity/activity context. Temporary users/data were deleted. The run is not a complete every-material-RPC matrix and its final runtime conflict assertion failed, so this stage is not claimed complete. |
| 5. Hosted Supabase security | **FAIL** | Database lint has no error findings and only two unused-variable warnings. Direct SQL inspection found RLS on all public tables, no public table lacking RLS, no `anon` executable `SECURITY DEFINER` function, no client grants on `private` or the identity map, PostgreSQL function ownership, fixed function `search_path`, and no `private` exposed schema. Advisors still report 9 warnings: 8 reviewed authenticated boundary functions and leaked-password protection disabled. |
| 6. Railway integration | **BLOCKED** | The Railway project `shimmering-flexibility` has only environment `production` (`d6bfb972-262b-46d9-9274-a63f16fe6677`). Its running deployment is `c51eb090-9e86-4773-a08b-d27eb14dbd34` at commit `6abb9317...`, not the R6 baseline/candidate. No deployment or mutation was made. New-user and legacy-upgrade Railway traces were not executed. |
| 7. Calibration runtime | **PASS** | Hosted rollback-only suites passed for the Phase 13 lifecycle (20), historical activation guard (17), Joren ruleset (18), zone calibration (19), and zone model (20). They exercise persisted run/bike HR+RPE estimates, sub-140 warning, swim elapsed-time/distance/RPE CSS, pending confirmation, stale checks, and historical read-only rejection while preserving old rows. |
| 8. Load / activity runtime | **FAIL** | Hosted activity and ruleset suites passed observed-only zone load, coefficients, coverage provenance, distance-only swim absence, inactive sRPE, historical provenance, average-HR correction protection, and public-load secrecy. Real-token create/replay/get/list and service-only processing context passed, but reuse of an activity idempotency key with a different fingerprint reproducibly failed to return within 30 seconds and again within 10 seconds. Railway log/analytics evidence was unavailable. |
| 9. Mobile / device | **BLOCKED** | Jest passed 6 suites/19 tests, strict TypeScript and unused-code checks passed. ADB was available but reported no attached Android device. iOS device/signing execution is unavailable from this Windows environment. No physical-device result is claimed. |
| 10. Accountable physiological review | **BLOCKED** | The ruleset and three Joren source documents are present, but no reviewer identity or identifiable review record is configured. `START23_PHYSIOLOGY_REVIEW_RECORD_ID`, `START23_PHYSIOLOGY_ACCOUNTABLE_OWNER`, and `PHYSIOLOGY_REVIEW_RULESET_VERSION` were absent. |
| 11. Contract / cutover decision | **NOT EXECUTED** | Stages 1-10 did not all pass. No legacy column, FK, RPC alias, adapter, or storage prefix was removed. The compatibility layer and `private.athlete_identity_map` remain intact. |

## Environments and revision evidence

1. Git SHA tested as the R6 baseline:
   `9c6be883918255a92644a8c69525a2d6cf14b071`.
2. Supabase environment: project `start23-dev`, ref
   `isfumhgqphieoayqahjv`, region `eu-west-1`, PostgreSQL
   `17.6.1.147`, status `ACTIVE_HEALTHY`.
3. Railway environment: no non-production environment exists. The only linked
   environment is `production`; it was inspected read-only and not changed.
4. Secret/configuration inspection checked names and presence only. No secret,
   password, token, email address, or private response body was printed or
   added to this report.

## Migration evidence

The historical hosted state initially ended at `20260910215947`. These 18
forward migrations were applied in repository order:

1. `20260911180631_phase_r1_onboarding_versioning.sql`
2. `20260912070000_r6_allow_opaque_owner_backfill_for_immutable_calibration.sql`
3. `20260912072232_phase_r2_r3_identity_onboarding_calibration.sql`
4. `20260912180000_phase_r4_r5_onboarding_race_activity.sql`
5. `20260913130000_phase_13_14_r6_entry_audit_remediation.sql`
6. `20260914080000_close_historical_calibration_writes.sql`
7. `20260914090000_block_historical_zone_profile_activation.sql`
8. `20260914162430_r6_preserve_critical_context_for_submaximal_zone_provenance.sql`
9. `20260914162711_r6_order_plan_revision_owner_before_eligibility.sql`
10. `20260914163325_r6_restore_activity_idempotency_preflight.sql`
11. `20260914170134_r6_increment_structured_race_goal_revision.sql`
12. `20260914172000_r6_refresh_planning_snapshot_after_input_change.sql`
13. `20260914172500_r6_refresh_extended_planning_snapshot_after_input_change.sql`
14. `20260914173000_r6_refresh_planning_snapshot_after_goal_rpc.sql`
15. `20260914173500_r6_force_distinct_post_rpc_snapshot_refresh.sql`
16. `20260914174000_r6_disambiguate_activity_processing_load_source.sql`
17. `20260914175000_r6_cover_foreign_key_access_paths.sql`
18. `20260914180000_r6_preserve_account_deletion_cascades.sql`

The first attempt exposed a transactional failure in the R2/R3 backfill because
an existing immutable-calibration guard rejected the new opaque owner. No
historical migration was edited; migration `20260912070000` was added before
R2/R3 and the chain was rerun. Later runtime defects were also repaired only by
new forward migrations.

Final `supabase migration list --linked` reports identical local and hosted
versions for all 41 migrations. Final `supabase db push --linked --dry-run`
reports `upToDate: true` and an empty migration list.

Post-upgrade integrity aggregates:

- Auth users / identity rows: 21 / 21;
- unmapped Auth identities, duplicate Auth keys, duplicate opaque keys, and
  identity-to-Auth orphans: all 0;
- operational / identifying / physiology profiles: 17 / 21 / 21, with 0
  owner orphans;
- goal, zone, activity, and plan dual-owner mismatches: all 0;
- calibration observations/evaluations missing opaque ownership: 0.

Historical records retained their provenance: four Phase 3 realized-load rows,
51 legacy training-history rows, 13 `legacy-unversioned` onboarding records,
four preserved Phase 13 private-history snapshots, and two active historical
zone profiles remained interpretable. pgTAP-created current rows were rolled
back after verification.

## Database test evidence

All tracked files under `supabase/tests` ran against the linked fully migrated
database. Planned assertion counts were:

- athlete profiles/RLS 37; Phase 10.1 drafts 18; R6-entry remediation 37;
- Phase 13 lifecycle 20; historical guard 17; Joren ruleset 18;
- Phase 14 inputs 15; Phase 4 onboarding/RLS 35; Phase 6 planning 30;
- Phase 7 activity 22; Phase 8.5 decisions 9; calibration 19; zone model 20;
- Phase 8 check-in 24; Phase 9 Polar 23; R1 10; R2/R3 48; R4/R5 29.

The five remaining SQL assertion/catalog files also ran without a SQL or
harness error. The runner treated any `not ok`, TAP failure summary, CLI error
tag, or SQL `ERROR` as a failure rather than trusting the CLI process code.

## Real-token security evidence

The verifier in `scripts/r6_real_token_security.py`:

- created two tagged, confirmed Auth users and obtained real password-grant
  access tokens;
- resolved distinct opaque athlete IDs that differ from the Auth UUIDs;
- wrote identifying, physiological, operational, previous-month history,
  structured goal, and activity data through owner-derived RPCs;
- scanned 32 materially affected owner tables for both users; 30 were readable
  only within owner RLS, while the two split profile tables correctly reject
  broad `select=*` because they use column-level grants;
- proved inverse profile/goal/activity reads return no foreign rows and a
  foreign goal mutation changes nothing;
- proved client-supplied authoritative athlete identity is rejected;
- blocked direct `athlete_profiles`, identity-map enumeration, private load,
  and service-only RPC use by both users;
- proved service credentials can resolve the opaque identity and obtain the
  private activity processing context separately;
- recursively scanned every successful public table/RPC response for TSS and
  private-load keys;
- deleted both temporary Auth users and their cascaded data.

The latest run passed all of those checks before failing the separate hosted
idempotency-conflict latency assertion. The script intentionally exits nonzero
until that runtime defect is fixed.

## Hosted security/advisor assessment

Final database lint contains no error finding. The remaining warnings are two
unused PL/pgSQL variables in `reject_calibration_threshold` and the superseded,
externally revoked `save_calculated_zone_profile_r5`.

Final advisors report 9 warnings and 57 informational findings:

- leaked-password protection is disabled: unresolved release security defect;
- eight authenticated `SECURITY DEFINER` functions are externally callable:
  `complete_current_onboarding`, `confirm_activity_planned_workout_match`,
  `create_activity_summary`, `get_activity`, `list_activities`,
  `get_operational_athlete_profile`, `save_operational_athlete_profile`, and
  `start_polar_oauth`;
- these eight are intentional narrow boundary functions: they derive the owner
  from the verified token, validate inputs, use a fixed `search_path`, and need
  to cross revoked-table or critical-write boundaries. The real-token run
  directly covered the profile and activity functions, but not every branch of
  onboarding, match confirmation, or Polar OAuth;
- `private.phase_13_activity_load_history` has RLS and no policy intentionally,
  with no client grant;
- 56 unused-index informational findings are expected on a low-traffic
  development project and immediately after adding covering indexes. They are
  not a reason to remove referential indexes before representative load;
- unindexed-foreign-key findings are now 0.

Direct catalog inspection additionally found zero public tables without RLS,
zero client privileges on the identity map or private tables, zero
authenticated privileges on `athlete_profiles`, zero anonymous-executable
public definer functions, only PostgreSQL-owned public functions, fixed
`search_path` on all definer functions, and exposed schemas limited to
`public` and `graphql_public`.

## Backend and mobile evidence

- Backend: 629 tests passed with one existing Starlette deprecation warning.
- Ruff: passed for backend and the R6 verifier.
- Strict mypy: passed for 132 app/test source files.
- Mobile Jest: 6 suites and 19 tests passed.
- Mobile strict TypeScript: passed.
- Mobile unused-code check: passed.
- `git diff --check`: passed; Git emitted only expected LF/CRLF notices.

These checks cover OpenAPI/public-contract and recursive TSS/private-load leak
assertions, but cannot substitute for the missing Railway logs and device runs.

## Reproducible hosted runtime defect

An exact activity retry with the same key and fingerprint returns the original
row. Reusing that key with a different fingerprint deliberately raises SQLSTATE
`40001`. Against the hosted Data API, that request timed out twice: once after
30 seconds and once after 10 seconds, rather than returning a conflict response.

PostgREST upstream documents automatic retry of `40001` serialization failures
and has removed that behavior in newer code because an intentionally repeated
failure can retry indefinitely. Start23 currently uses `40001` for numerous
business-state conflicts, so the activity reproduction is evidence of a wider
risk. Before release, either the hosted PostgREST behavior must be upgraded and
verified or deliberate business conflicts must use a non-retryable application
SQLSTATE in a new forward migration, with repository error mapping and full
stale/idempotency regression coverage updated together.

## Physiological review evidence

Ruleset `phase-13-joren-ruleset-1` and the three provenance-hashed Joren sources
`Hoe TSS berekenen zones gekend (z) en zones onbekend (rpe).pdf`,
`Triathlon_Onboarding_StartTSS.pdf`, and
`Triathlon_Zone_Calibratie_Voorbeelden.pdf` are present. Calibration formulas,
textual RPE, Start-TSS, private coefficients, progression, sickness/fatigue,
and taper behavior are documented and tested. This is not the accountable
review required by the roadmap. No qualified reviewer identity, dated
approval, or external record/reference exists, so the gate remains open.

## Compatibility cutover

Deferred. Although current aggregate checks show one-to-one mappings and no
owner orphans/mismatches, prerequisite stages did not pass and the exhaustive
backend/mobile/storage dependency inventory was not proven. No final contract
migration was created. Legacy ownership columns, adapters, aliases, and storage
prefix compatibility remain for a safe later cutover.

## Unresolved risks

1. No fresh database migration-chain execution.
2. No non-production Railway environment and no exact-candidate Railway deploy.
3. Hosted `40001` conflict requests may retry until client timeout.
4. Supabase leaked-password protection is disabled.
5. Real-token coverage is representative but not exhaustive for every material
   public RPC branch.
6. No complete new-user or legacy-upgrade flow through Railway.
7. No Railway response/log/analytics leak inspection.
8. No attached Android device and no executable iOS signing/device path.
9. No qualified accountable physiological reviewer or review record.
10. The remediated candidate is not yet an immutable Git commit.
11. The compatibility cutover and required full post-cutover rerun are deferred.

## Production release plan

No production step is authorized by this report. After the blockers are closed:

1. Commit and review the R6 remediation as one immutable candidate SHA.
2. Provision a Railway staging environment connected only to `start23-dev` and
   configure required variable names without copying values into source or logs.
3. Run the full migration chain from fresh state and from a representative
   historical snapshot; repeat all 23 database tests.
4. Fix or eliminate hosted business-conflict retries, enable leaked-password
   protection in development/staging, and rerun lint, advisors, catalog audits,
   and the complete real-token RPC matrix.
5. Deploy that exact SHA to Railway staging and run both end-to-end user flows,
   including calibration, pending confirmations, planning, activity processing,
   next-week progression, retries/stale transitions, and log/API privacy scans.
6. Complete Android and iOS physical-device passes and attach evidence.
7. Obtain the named qualified reviewer approval and identifiable record for
   `phase-13-joren-ruleset-1`.
8. Reassess every legacy owner row and backend/mobile/storage dependency. Only
   if all prerequisites pass, author a new forward-only cutover migration and
   rerun the complete R6 matrix post-cutover.
9. Request separate explicit production authorization. Then record the
   production ledger/backup posture, run a production dry run, apply only the
   reviewed forward migrations, deploy the exact approved Railway SHA, publish
   the signed mobile build, execute bounded smoke checks, and monitor errors,
   privacy signals, and database health. Keep the compatible application path
   available until the production cutover is verified.

R6 INCOMPLETE — NOT READY FOR PRODUCTION RELEASE PROCESS
