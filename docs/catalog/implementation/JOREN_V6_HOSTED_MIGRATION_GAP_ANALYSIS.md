# WOMBO V6 hosted migration gap analysis

Assessment: 15-16 November 2026, Europe/Amsterdam. **PARTIAL - production execution blocked.**

Accepted start: `verify/joren-v6-hosted-supabase-auth` at **289280a5bddf6f0cc65eca1f562561e7df9a603c**. Isolated successor: `release/joren-v6-hosted-migration-readiness`, `.worktrees/joren-v6-hosted-migration-readiness`. No existing worktree was checked out, reset, cleaned or committed by this work.

Read root/mobile AGENTS.md, current MVP roadmap and its frequency/V2 amendments, hosted authentication reports, persistence architecture/recovery and later PostgreSQL/lifecycle/evidence/frequency reports, immutable frequency approval, official-TSS acceptance/scientific gates and A3-A9/A5/A6 contracts. Later verified reports supersede older "not executed" statuses only within their stated scope.

## Actual hosted boundary

The existing authorized read-only Management connection identifies `start23-dev`, `isfumhgqphieoayqahjv`, eu-west-1, PostgreSQL 17.6. Development naming does not reduce production safeguards. Current ledger: **47 distinct accepted versions, 16 missing, zero extras**, contiguous through `20261004212750_first_plan_approved_provenance.sql`. The 47 names/statement fingerprints equal the accepted 14-November observation. All 63 local file SHA-256 values match that accepted inventory. No version collision or reordered gap was found. No ledger was repaired, rewritten or applied.

See [full inventory](migration-readiness-20261116/migration-inventory.json), [current preflight](migration-readiness-20261116/hosted-before.json) and [detailed metadata](migration-readiness-20261116/hosted-detail-final.json). File hashes identify exact worktree bytes; a hosted statement-array MD5 is a different representation and is not file-byte equivalence.

## Drift and prerequisites

- **Two function-body differences:** hosted `rls_auto_enable()` omits the fixture's rethrow after logging an auto-RLS exception. Hosted `save_zone_profile(...)` lacks redundant in-function manual/fallback metadata guards present in the clean accepted replay. The current downstream `private.require_trusted_zone_metadata` trigger still contains the relevant checks; this is not presented as a demonstrated authorization bypass. Exact diffs are in the evidence directory. The 16 missing files do not repair these differences.
- All **149 public/private function normalized-source hashes, signatures/results, SECURITY DEFINER flags, settings and ACLs** match after reproducing only those two observed definitions in a disposable local database. Public/private constraints, indexes, trigger definitions and normalized policies also match. Whitespace normalization is not semantic proof or historical statement-byte equality.
- `information_schema.role_table_grants` returns zero rows under the hosted read-only Management role; that is a visibility limit, **not absence of grants**. The assessment therefore separately uses `pg_class.relacl` and `has_table_privilege`. CRUD, schema-usage and RLS settings match across the 153 role/table combinations. Hosted service ACLs retain additional `Dxtm` (TRUNCATE/REFERENCES/TRIGGER/MAINTAIN) privileges on four historical catalog tables, and hosted default ACLs differ from the intentionally narrow portable bootstrap. These existing privileges/defaults require owner disposition and official hosted parity; no grant was weakened or repaired. See [comparison](migration-readiness-20261116/boundary-parity-comparison.json).
- V6/frequency tables and roles are currently absent hosted. No previously installed V6 catalog rows, frequency reviewer or test-role membership is claimed. Ordinary role metadata, extensions, signup trigger, existing policies and RPCs were inspected without athlete-row extraction.
- No cron/pg_net/queue job relations or callback-bearing application functions were found by the fixed inventory; none of the 16 introduces a scheduled job. Project webhook enumeration remains 403, so platform webhook absence is unverified. Account deletion continues through the existing Auth/opaque identity cascades, extended by new private FKs.

## Release-relevant findings

1. Migration 5 changes a shared activity projection. The historical strict backend model rejects the resulting synthetic response with `extra_forbidden(session_rpe_version)`. The published production/staging contract lacks this field. Unchanged deployed-backend compatibility is not demonstrated and is unsafe to assume.
2. The exact chain introduces **13 new authenticated EXECUTE signatures**, including owner reads, registration, preferences and one private invoker dependency. None grants generated-plan execution to athletes, but the literal no-new-client-EXECUTE requirement is not satisfied. No exception is inferred.
3. Actual backup listing is empty and PITR is false. No recoverable production checkpoint or restoration rehearsal is verified.
4. Portable execution is strong local evidence, not GoTrue/PostgREST/default-ACL/resource parity. A narrowly scoped hosted adapter and an official isolated runtime still need separate approval/implementation.

## Inventory and execution order

Ordinals below are the chronological accepted order. G1 = 1; G2 = 2-12 as one transaction; G3 = 13-16 as one transaction. Grouping reflects incomplete V2 approval/error behavior and later V6 custody/membership closures, not a chosen batch size. **Every migration is required for the complete inactive lifecycle verification requested**, although catalog seeding itself is not activation. Recovery for all groups is: abort/rollback before commit; after commit preserve provenance and use a separately reviewed forward correction or generation disable; actual backup restoration remains independently gated. Never use destructive down migrations or delete immutable sources.

| # | Group | Exact migration | SHA-256 |
| --- | --- | --- | --- |
| 1 | G1 | `20261026224844_wombo_a5_checkin_proposal_recovery.sql` | `605baca7b060a74dcd0804710a8547b662d76f0c5cb7c21a5aa4b72cfa305d02` |
| 2 | G2 | `20261103134520_joren_realized_tss_v2_private_provenance.sql` | `d5444ccbe28428e4101151c07c2f522ae213c2fd82190f5af8cc1ce1c2333231` |
| 3 | G2 | `20261103135735_realized_v2_weekly_registration.sql` | `2c3cd85f4ead27a37dd16330626cf8c57fe69baf44459b8fa8b9e9a92f59b346` |
| 4 | G2 | `20261103140959_realized_v2_planning_evidence_preconditions.sql` | `6358726af884ecb44e104ad9c0528d2ca7865c0dde8a37e1e8169fbd13ee896a` |
| 5 | G2 | `20261103142339_realized_v2_session_rpe_guidance.sql` | `4b3749757358d332df835b4abb945dc95769c4f7a5a14f9b3654874880d93d29` |
| 6 | G2 | `20261105120000_inactive_v6_persistence.sql` | `c3572d34ea784a6aba9ab7531cca34007f768ca79602b63d92dfcf0f491c8283` |
| 7 | G2 | `20261105120100_inactive_v6_catalog.sql` | `6e77d8d54650c7be554a90bb87cdf339b72a2db334be1a8dd98e82d6e22efe34` |
| 8 | G2 | `20261107182000_v6_segment_snapshot_compatibility.sql` | `ca38c97168eaf7d22d5b3508aa4bcdc78f4643044181bfe2ff3d5e699cf838c1` |
| 9 | G2 | `20261107182500_v6_frozen_snapshot_operator_precedence.sql` | `aab65809df7f6ebf5d2881fde680e2b169943eceb9d27e2ce53350afbf29efe8` |
| 10 | G2 | `20261107183000_realized_v2_internal_approval_custody.sql` | `1efa35afae3877ea80bde0edc03241e0dad1944dee7a217d40739da86fcbc93a` |
| 11 | G2 | `20261107183500_realized_v2_business_conflict_codes.sql` | `1fae47af0784194597bd783a53c22626a9951a16009e749df672b202309e4375` |
| 12 | G2 | `20261107184500_v6_insert_custody.sql` | `b5844a38a73da363642db6a99328e5358fd4ff72302b51434dd88333dc4a4140` |
| 13 | G3 | `20261108142454_inactive_v6_mobile_identity.sql` | `767e7c0f7badbebee9701b546f4666c8f0f72843334f5f8b0f3f7ab313c81008` |
| 14 | G3 | `20261108180000_inactive_v6_lifecycle_completion.sql` | `71f3b0388ac99ffae6bd76659eeba1fef84c1adecc004ebb37e8fa10010732c6` |
| 15 | G3 | `20261108210000_inactive_v6_evidence_memberships.sql` | `8428f54223108265c20ec87890b651aca4129ca1b5910c75439f6b691eeffb25` |
| 16 | G3 | `20261113154716_inactive_v6_approved_frequency_policy.sql` | `c0a43411f7db00d4d76cb8400d0b07e5081678aff280853a6a91b9b03ff6b2c4` |

## 1. 20261026224844_wombo_a5_checkin_proposal_recovery.sql

**Prerequisites/order:** Historical planning-v2, check-in attachment, opaque-owner/RLS prerequisites in the first 47 migrations.

**Athletes, existing data and historical functionality:** Atomic A5 creation/attachment and exact completed-check-in replay. No stored row is rewritten at installation. Historical v3 requests retain signatures; concurrent callers serialize on the check-in row.

**Permissions:** New authenticated get_checkin_plan_proposal; v3 remains service-only. This is one of the strict no-new-EXECUTE conflicts.

**Deployed backend/mobile consumer impact:** Existing v3 callers retain their request/response signature; A5-aware clients gain recovery. Deployed code SHA and installed mobile build still require verification.

**Locking/type:** Function-catalog locks only at installation; runtime check-in row locks serialize duplicate generation. Additive RPC plus replacement of existing v3 behavior.

**Inactive verification and recovery:** Required for real A5 attachment/replay. Withdrawal must retain attached records and existing approval/rejection; fix v3 forward if needed.

- Declared/replaced functions: `public.get_checkin_plan_proposal`, `public.create_weekly_plan_proposal_v3`.

## 2. 20261103134520_joren_realized_tss_v2_private_provenance.sql

**Prerequisites/order:** First 47: activities, dual-owner map, legacy activity RPCs and load context.

**Athletes, existing data and historical functionality:** Prospective V2 inputs/calculation revisions only. Legacy rows acquire no invented duration consent or recalculated load. New wrappers preserve old activity RPC names.

**Permissions:** New authenticated create_activity_summary_v2; service SELECT/INSERT on two private forced-RLS tables and service-only V2 processing/completion. Explicit other-role revokes.

**Deployed backend/mobile consumer impact:** Old activity RPCs remain installed. V2 wrappers are opt-in, but the later shared projection in migration 5 requires consumer coordination; no mobile V6 switch occurs here.

**Locking/type:** New-table/index DDL and foreign-key parent relation locks; no existing-table data backfill. Additive.

**Inactive verification and recovery:** Required by complete V6 activity/V2 evidence. Leave records immutable; disable V2 use in compatible runtime and correct prospectively.

- New tables: `private.realized_v2_activity_inputs`, `private.realized_v2_calculations`.
- Direct ALTER TABLE targets: `private.realized_v2_activity_inputs`, `private.realized_v2_calculations`.
- Declared/replaced functions: `private.realized_v2_immutable`, `public.create_activity_summary_v2`, `public.get_activity_processing_context_v2`, `public.complete_activity_rpe_v2`.
- Direct trigger declarations: `r3_00_sync_opaque_athlete_owner`, `realized_v2_input_immutable`, `realized_v2_calculation_immutable`.
- Trigger targets: `private.realized_v2_activity_inputs` -> `r3_00_sync_opaque_athlete_owner`, `private.realized_v2_calculations` -> `r3_00_sync_opaque_athlete_owner`, `private.realized_v2_activity_inputs` -> `realized_v2_input_immutable`, `private.realized_v2_calculations` -> `realized_v2_calculation_immutable`.

## 3. 20261103135735_realized_v2_weekly_registration.sql

**Prerequisites/order:** Migration 2 immutable trigger and existing v15 history/activities/planned-workout relations.

**Athletes, existing data and historical functionality:** Explicit skipped/unknown append-only ledger and v16 raw weekly evidence. A new trigger affects ALL linked activity inserts/matches, including historical flows: inactive or skipped targets now conflict.

**Permissions:** New authenticated get/confirm registration RPCs; service SELECT/INSERT on private events and service-only v16. No client private-table read.

**Deployed backend/mobile consumer impact:** Historical linked-activity writes can now reject stale/skipped targets. New registration endpoints require compatible runtime/UI; an older app is not automatically upgraded.

**Locking/type:** Trigger installation on existing activities needs relation lock; runtime plan NO KEY UPDATE then workout locks add contention. Additive storage with changed historical write guards.

**Inactive verification and recovery:** Required for registration and evidence. Pair with 10/11 before exposing V2. Preserve events; no inference that missing activity means skipped.

- New tables: `private.workout_registration_events`.
- Direct ALTER TABLE targets: `private.workout_registration_events`.
- Declared/replaced functions: `public.get_workout_registration`, `public.confirm_workout_registration`, `private.guard_skipped_workout_activity`, `public.get_plan_load_history_for_planning_v16`.
- Direct trigger declarations: `r3_00_sync_opaque_athlete_owner`, `workout_registration_immutable`, `realized_v2_guard_skipped_activity`.
- Trigger targets: `private.workout_registration_events` -> `r3_00_sync_opaque_athlete_owner`, `private.workout_registration_events` -> `workout_registration_immutable`, `public.activities` -> `realized_v2_guard_skipped_activity`.

## 4. 20261103140959_realized_v2_planning_evidence_preconditions.sql

**Prerequisites/order:** Migrations 1-3: A5/v3, weekly history and immutable V2 evidence helpers.

**Athletes, existing data and historical functionality:** Freezes evidence for new v4 proposals; existing revisions without evidence retain ordinary approval. New approval trigger applies stale-evidence checking only to evidence-bearing revisions.

**Permissions:** Service SELECT/INSERT on private evidence and service-only v4; approval stays existing authenticated invoker/RLS RPC.

**Deployed backend/mobile consumer impact:** Legacy v3 proposals without V2 evidence retain approval behavior. Any deployed v4/V2 consumer must be kept unavailable until migration 10 closes internal owner approval.

**Locking/type:** Trigger lock on plan_revisions and FK parent locks; no historical scan/backfill. Additive table; changed transition guard.

**Inactive verification and recovery:** Required for pending/confirmation custody. Must include migration 10 in same exposure boundary: otherwise owner approval reaches service-only v13-v15 guards and fails.

- New tables: `private.realized_v2_plan_evidence`.
- Direct ALTER TABLE targets: `private.realized_v2_plan_evidence`.
- Declared/replaced functions: `private.realized_v2_history_evidence`, `public.create_weekly_plan_proposal_v4`, `private.guard_realized_v2_plan_approval`.
- Direct trigger declarations: `r3_00_sync_opaque_athlete_owner`, `realized_v2_plan_evidence_immutable`, `realized_v2_guard_plan_approval`.
- Trigger targets: `private.realized_v2_plan_evidence` -> `r3_00_sync_opaque_athlete_owner`, `private.realized_v2_plan_evidence` -> `realized_v2_plan_evidence_immutable`, `public.plan_revisions` -> `realized_v2_guard_plan_approval`.

## 5. 20261103142339_realized_v2_session_rpe_guidance.sql

**Prerequisites/order:** Migration 2 inputs table and existing private.activity_public_json.

**Athletes, existing data and historical functionality:** Replaces the SHARED activity projection, adding session_rpe_version to every legacy and V2 response. No saved load changes, but old strict backend models reject the added field. This is a demonstrated compatibility blocker.

**Permissions:** Helper remains ungranted; no new direct client grant. Existing activity RPCs transitively return changed JSON.

**Deployed backend/mobile consumer impact:** Demonstrated historical strict backend consumer break; published deployed schema lacks the field. Requires separate compatibility decision; existing mobile receives only the backend projection and cannot repair backend rejection.

**Locking/type:** Function replacement only; no data rewrite. Behaviorally breaking for a strict old consumer despite additive JSON.

**Inactive verification and recovery:** Required for accepted Session-RPE presentation. Before G2 choose a reviewed historical-projection compatibility forward change or proven compatible backend rollout. Do not edit this accepted migration.

- Declared/replaced functions: `private.activity_public_json`.

## 6. 20261105120000_inactive_v6_persistence.sql

**Prerequisites/order:** Migrations 2-4 plus all historical catalog/draft/revision prerequisites.

**Athletes, existing data and historical functionality:** Adds inactive_v6 DEFAULT false to templates; restrictive SELECT hides V6. Replaces draft constraints/trigger dispatch and expands zero-duration distribution only for versioned V6. Four private tables hold sources, frozen plans, logical/physical mappings and edit receipts.

**Permissions:** Forced private RLS and explicit revokes including service_role; narrow service RPCs mediate storage. Authenticated get_v6_weekly_plan is a new EXECUTE conflict. Existing owner policies remain.

**Deployed backend/mobile consumer impact:** Historical defaults remain false/hidden and version-dispatch predicates retain old paths. New V6 RPCs are not a mobile/planner rollout; actual deployed compatibility is still gated by migration 5.

**Locking/type:** ACCESS EXCLUSIVE risk on templates, swipe_week_drafts and plan_revisions; constraint replacement validates existing rows. Fast default may avoid a rewrite, but locks/scans still matter. Replaces constraints/triggers, no row deletion.

**Inactive verification and recovery:** Required. Must include 7-9 and 12 before any V6 exposure; retain all snapshots on disable. Missing grants or constraint failure stops the transaction.

- New tables: `private.v6_source_revisions`, `private.v6_plan_snapshots`, `private.v6_occurrence_snapshots`, `private.v6_edit_results`.
- Direct ALTER TABLE targets: `public.workout_templates`, `public.swipe_week_drafts`, `private.v6_source_revisions`, `public.plan_revisions`.
- Declared/replaced functions: `public.get_inactive_v6_catalog_for_planning`, `private.v6_public_plan`, `public.get_v6_weekly_plan`, `public.get_v6_edit_retry`, `public.get_v6_plan_context_for_planning`, `public.create_v6_weekly_plan_proposal`, `private.guard_v6_plan_approval`, `private.guard_v6_frozen_snapshot_mutation`.
- Direct trigger declarations: `swipe_week_drafts_validate`, `swipe_week_drafts_validate_v2`, `v6_source_revisions_immutable`, `v6_guard_plan_approval`, `v6_frozen_snapshot_immutable`.
- Trigger targets: `public.swipe_week_drafts` -> `swipe_week_drafts_validate`, `public.swipe_week_drafts` -> `swipe_week_drafts_validate_v2`, `private.v6_source_revisions` -> `v6_source_revisions_immutable`, `public.plan_revisions` -> `v6_guard_plan_approval`, `public.planned_workouts` -> `v6_frozen_snapshot_immutable`, `public.plan_revisions` -> `v6_frozen_snapshot_immutable`, `private.planned_workout_loads` -> `v6_frozen_snapshot_immutable`, `private.plan_revision_loads` -> `v6_frozen_snapshot_immutable`.
- Policies: `workout_templates_hide_inactive_v6`.
- Dynamic DDL additionally installs dual-owner/immutable triggers and forced RLS/revokes on all three owner snapshot/receipt tables. Frozen mutation triggers cover existing plan/workout/load evidence.

## 7. 20261105120100_inactive_v6_catalog.sql

**Prerequisites/order:** Migration 6 tables/column/constraints; 77 source IDs must be absent, not conflicting preexisting rows.

**Athletes, existing data and historical functionality:** Inserts exactly 77 public inactive templates and 77 private source documents/exact official values. Adds ZERO rows to historical private.workout_template_loads; 325 existing seed templates/loads remain identical locally.

**Permissions:** No GRANT or policy changes. Existing restrictive policy hides new public templates from athlete catalog selection.

**Deployed backend/mobile consumer impact:** Historical server catalog inner join and restrictive client SELECT exclude the imported sources. Existing apps do not automatically discover or enroll in V6.

**Locking/type:** Insert/index/FK/WAL work for a 2.8 MB reviewed file; temporary import table ON COMMIT DROP REQUIRES an explicit transaction encompassing the whole file. Additive catalog data, no retirement.

**Inactive verification and recovery:** Required. Source-coverage assertion rejects extra/missing rows. Never delete immutable sources to roll back; leave INACTIVE and remove generation dependency.


## 8. 20261107182000_v6_segment_snapshot_compatibility.sql

**Prerequisites/order:** Migration 6 private source snapshots plus existing historical segment-setting trigger.

**Athletes, existing data and historical functionality:** Restores V6 segments after the legacy INSERT trigger would otherwise rebuild an empty segment set. Historical template IDs fall through unchanged.

**Permissions:** Private trigger function explicitly ungranted.

**Deployed backend/mobile consumer impact:** Historical inserts miss the V6 source lookup and preserve their existing segments. No client contract change.

**Locking/type:** Trigger installation lock on planned_workouts; indexed source lookup on each insert. Additive V6-only trigger.

**Inactive verification and recovery:** Required. Paired with 12 for insert custody; rollback retains source prescriptions and uses forward disable.

- Declared/replaced functions: `private.set_v6_planned_workout_segments`.
- Direct trigger declarations: `v6_set_planned_workout_segments`.
- Trigger targets: `public.planned_workouts` -> `v6_set_planned_workout_segments`.

## 9. 20261107182500_v6_frozen_snapshot_operator_precedence.sql

**Prerequisites/order:** Migration 6 exact create_v6_weekly_plan_proposal definition, with two expected operator-precedence markers.

**Athletes, existing data and historical functionality:** Rewrites ONLY two JSON extraction/subtraction expressions using pg_get_functiondef; missing markers abort. Repairs 42725 pending-edit runtime ambiguity.

**Permissions:** No new privileges, signatures or policies.

**Deployed backend/mobile consumer impact:** Only V6 pending-edit writer behavior changes; no historical/mobile DTO field or signature changes.

**Locking/type:** Function replacement/catalog locking, no row scan. Corrective behavior, not data transformation.

**Inactive verification and recovery:** Required for pending edits. Do not run after the writer has already been replaced by migration 14; retain chronological execution order.

- Dynamic replacement: `public.create_v6_weekly_plan_proposal(uuid,jsonb)`; exact markers fail closed.

## 10. 20261107183000_realized_v2_internal_approval_custody.sql

**Prerequisites/order:** Existing historical v13-v15 functions and their exact service-role guard marker; migration 4 makes the internal owner-approval path reachable.

**Athletes, existing data and historical functionality:** Allows the authenticated SAME owner through internal v13-v15 guard evaluation. Direct EXECUTE remains service-only; foreign identifiers stay denied.

**Permissions:** No grant/RLS change. Internal ownership guard extends; it is not a new public client endpoint.

**Deployed backend/mobile consumer impact:** Existing public approval remains invoker/RLS and service-only history EXECUTE is unchanged. V2-capable runtime gets a working internal approval path; no mobile permission expansion.

**Locking/type:** Three function replacements; no data or schema rewrite. Review owner-path authorization rather than describing all changes as additive.

**Inactive verification and recovery:** Required for V2/V6 approval, not optional merely because V6 is inactive. No externally usable intermediate between 4 and 10.

- Dynamic replacement: service-only `get_plan_load_history_for_planning_v13/v14/v15(uuid,date)`.

## 11. 20261107183500_realized_v2_business_conflict_codes.sql

**Prerequisites/order:** Migrations 3/4 exact four guard functions and their 40001 marker.

**Athletes, existing data and historical functionality:** Changes business-precondition SQLSTATE from serialization 40001 to nonretryable PT409 in confirm registration, skipped-activity guard, v4 creation and V2 approval. Conditions and stale semantics stay.

**Permissions:** No grants/RLS change; application error/retry classification changes.

**Deployed backend/mobile consumer impact:** Compatible repository error mapping sees terminal PT409 instead of retryable serialization. Verify actual deployed mapping; do not treat new business conflicts as network retries.

**Locking/type:** Four function replacements, no data rewrite.

**Inactive verification and recovery:** Required to preserve existing terminal HTTP 409 semantics. Cannot expose new V2 paths before this correction; corrective migration only for recovery.

- Dynamic replacements: `confirm_workout_registration`, `guard_skipped_workout_activity`, `create_weekly_plan_proposal_v4`, `guard_realized_v2_plan_approval`.

## 12. 20261107184500_v6_insert_custody.sql

**Prerequisites/order:** Migration 8 segment trigger function plus 6 V6 snapshot tables.

**Athletes, existing data and historical functionality:** Blocks client-authored V6 revisions and inserts into frozen V6 snapshots even if a caller spoofs the historical critical_write GUC. Uses protected PostgreSQL ROLE state for segment insertion.

**Permissions:** New private guard function remains ungranted; no ordinary-client generation authority.

**Deployed backend/mobile consumer impact:** Client SQL cannot create V6 state through legacy GUC trust. Genuine historical calls stay on the same code path; no mobile DTO changes.

**Locking/type:** Trigger lock on plan_revisions plus segment-function replacement; no backfill.

**Inactive verification and recovery:** Required security closure before G2 commit. Retain custody triggers during disable; do not replace with GUC-based trust.

- Declared/replaced functions: `private.guard_v6_generated_revision_insert`, `private.set_v6_planned_workout_segments`.
- Direct trigger declarations: `v6_generated_revision_insert`.
- Trigger targets: `public.plan_revisions` -> `v6_generated_revision_insert`.

## 13. 20261108142454_inactive_v6_mobile_identity.sql

**Prerequisites/order:** Migrations 6-12 occurrence mapping, private projections and immutable edit receipts.

**Athletes, existing data and historical functionality:** Adds separate logical ID / physical_workout_id mobile projections and calendar/edit-read helpers. Existing historical RPC DTOs are not changed by this file.

**Permissions:** New authenticated mobile plan/calendar reads; service-only mobile edit retry. These client reads conflict with strict no-new-EXECUTE.

**Deployed backend/mobile consumer impact:** Only explicit V6 mobile projections add physical_workout_id. Historical public RPC shapes are retained; older apps remain on their historical routes.

**Locking/type:** Function-catalog changes and PostgREST schema reload notification only. Additive read projections.

**Inactive verification and recovery:** Required for hosted calendar/source/activity identity verification. Preserve retained owner reads on disable.

- Declared/replaced functions: `private.v6_mobile_workout`, `private.v6_mobile_plan`, `public.get_v6_mobile_weekly_plan`, `public.get_v6_mobile_calendar`, `public.get_v6_mobile_edit_retry`.

## 14. 20261108180000_inactive_v6_lifecycle_completion.sql

**Prerequisites/order:** Migrations 1-13 plus exact confirm_weekly_checkin_context replacement marker.

**Athletes, existing data and historical functionality:** Replaces shared A5 v3/replay and check-in planning context; V6 dispatch sits inside existing attachment lock/replay. Introduces move/context RPCs. Replaces check-in confirmation constraint and supersedes prior confirmed contexts while preserving confirmation provenance.

**Permissions:** Existing A5 authenticated/service boundaries remain; new authenticated V6 move-context read, service-only generated/move writers, private core writer ungranted.

**Deployed backend/mobile consumer impact:** Shared A5/check-in functions change for all current callers and context reconfirmation retains old provenance. Historical signature parity passed locally; actual artifacts and migration-5 bridge remain open.

**Locking/type:** ACCESS EXCLUSIVE/constraint-validation risk on weekly_checkin_contexts, function replacements and notify. No installation-time user-row transformation; future historical reconfirmation behavior changes.

**Inactive verification and recovery:** Required for A5/swipe/move lifecycle. Include 15 before exposing post-activity moves; old disable fixture no longer covers shared A5 dispatch into the private writer.

- Direct ALTER TABLE targets: `public.weekly_checkin_contexts`.
- Declared/replaced functions: `public.get_checkin_context_for_planning`, `private.write_v6_weekly_plan_proposal`, `public.create_weekly_plan_proposal_v3`, `public.create_v6_weekly_plan_proposal`, `public.get_checkin_plan_proposal`, `public.get_v6_move_workout_context`, `public.move_v6_planned_workout`, `public.get_v6_plan_context_for_planning`.
- Dynamic replacement: `public.confirm_weekly_checkin_context(uuid,integer,text)`; confirmation constraint replaced in the same file.

## 15. 20261108210000_inactive_v6_evidence_memberships.sql

**Prerequisites/order:** Migrations 3/6/13/14: registration events, snapshots, mobile projections and move writer.

**Athletes, existing data and historical functionality:** Append-only memberships retain original physical evidence across successor revisions. Replaces shared get_weekly_plan/calendar/rest/history, activity creation/matching, registration and skip guard. Historical rows use the same path without V6 memberships.

**Permissions:** New authenticated/service EXECUTE on owner-checked private.v6_revision_workouts is needed by existing invoker reads; private view and membership table remain ungranted. This is a strict EXECUTE conflict even though private is unexposed.

**Deployed backend/mobile consumer impact:** Shared historical plan/calendar/activity/registration implementations are replaced. Physical identity is extended for V6 memberships while historical projections pass locally. The new private authenticated helper must remain callable by existing invoker reads.

**Locking/type:** New table/view/index/FKs, trigger locks on snapshots/revisions, many function replacements. No evidence reassignment or copied historical recalculation.

**Inactive verification and recovery:** Required for unfinished-sibling rescheduling after activities/registrations. Do not revoke its helper alone: that would break historical reads. Keep it installed and use generation guards for disable.

- New tables: `private.v6_revision_memberships`.
- Direct ALTER TABLE targets: `private.v6_revision_memberships`.
- Declared/replaced functions: `private.guard_v6_membership_scope`, `private.guard_v6_native_membership`, `private.v6_revision_workouts`, `private.v6_active_workout_member`, `private.guard_v6_evidence_preservation`, `public.get_weekly_plan`, `public.get_calendar`, `public.get_calendar_rest_days`, `public.get_plan_load_history_for_planning_v14`, `public.get_plan_load_history_for_planning_v16`, `public.get_v6_move_workout_context`, `private.v6_public_plan`, `private.v6_mobile_workout`, `public.create_activity_summary_r6_pre_idempotency`, `public.confirm_activity_planned_workout_match`, `public.get_workout_registration`, `private.guard_skipped_workout_activity`, `public.move_v6_planned_workout`, `public.get_plan_load_history_for_planning_v13`.
- Views: `private.v6_revision_occurrences`.
- Direct trigger declarations: `r3_00_sync_opaque_athlete_owner`, `v6_membership_immutable`, `v6_membership_scope`, `v6_native_membership_scope`, `v6_evidence_preservation`.
- Trigger targets: `private.v6_revision_memberships` -> `r3_00_sync_opaque_athlete_owner`, `private.v6_revision_memberships` -> `v6_membership_immutable`, `private.v6_revision_memberships` -> `v6_membership_scope`, `private.v6_occurrence_snapshots` -> `v6_native_membership_scope`, `public.plan_revisions` -> `v6_evidence_preservation`.

## 16. 20261113154716_inactive_v6_approved_frequency_policy.sql

**Prerequisites/order:** Migrations 6/14/15; exact V6 public-plan helper must not already be renamed; no preexisting conflicting roles/reviewer records.

**Athletes, existing data and historical functionality:** Creates four private policy stores, preference/reconfirmation/invalidation machinery, source and approval guards, frequency-aware swipe wrappers and summary/receipt. Adds two NOLOGIN roles, with ZERO memberships/reviewers/individual maxima seeded.

**Permissions:** New authenticated preference read/save/interruption and receipt; service-only frequency-context/swipe RPCs. Registrar gets private schema usage and register_frequency_decision only; nobody is enrolled. Test executor is NEVER granted in production.

**Deployed backend/mobile consumer impact:** Optional owner preference RPCs become callable at the database boundary, without a production planner switch. Existing apps get no automatic UI/REAL authority; deployed API currently lacks preference routes.

**Locking/type:** Trigger locks on snapshots/revisions/drafts/checkin contexts/injury/goals/zones/profile; function rename/wrapper must commit together. New indexes/tables. No automatic V6 enrollment, but optional-preference writes become callable without an ACL closure.

**Inactive verification and recovery:** Required for the accepted frequency defaults/denials and complete hosted verification. Preserve soft preferences and authority evidence; positive real multi-session remains blocked by genuine designation and reviewed individual maxima.

- New tables: `private.frequency_reviewers`, `private.frequency_preferences`, `private.frequency_decisions`, `private.frequency_draft_contexts`.
- Direct ALTER TABLE targets: `private.frequency_draft_contexts`.
- Declared/replaced functions: `private.lock_frequency`, `private.frequency_preference`, `public.get_frequency_preferences`, `public.save_frequency_preferences`, `private.frequency_basis`, `private.invalidate_frequency`, `public.report_frequency_interruption`, `private.register_frequency_decision`, `private.frequency_context`, `public.get_v6_frequency_context`, `private.assert_frequency_context`, `private.frequency_test_caller`, `private.guard_frequency_snapshot`, `private.guard_frequency_approval`, `private.frequency_checkin_invalidation`, `private.guard_frequency_draft`, `public.create_v6_frequency_swipe_draft`, `public.update_v6_frequency_swipe_draft`, `public.create_v6_frequency_swipe_proposal`, `private.frequency_source_invalidation`, `private.frequency_reviewer_invalidation`, `private.v6_public_plan`, `public.get_v6_frequency_swipe_receipt`.
- Direct trigger declarations: `v6_frequency_snapshot_guard`, `frequency_approval_guard`, `frequency_checkin_invalidation`, `frequency_draft_immutable`, `v6_frequency_draft_guard`, `frequency_restriction_invalidation`, `frequency_goal_invalidation`, `frequency_zone_invalidation`, `frequency_profile_invalidation`, `frequency_reviewer_invalidation`.
- Trigger targets: `private.v6_plan_snapshots` -> `v6_frequency_snapshot_guard`, `public.plan_revisions` -> `frequency_approval_guard`, `public.weekly_checkin_contexts` -> `frequency_checkin_invalidation`, `private.frequency_draft_contexts` -> `frequency_draft_immutable`, `public.swipe_week_drafts` -> `v6_frequency_draft_guard`, `public.injury_restrictions` -> `frequency_restriction_invalidation`, `public.goals` -> `frequency_goal_invalidation`, `public.zone_profile_versions` -> `frequency_zone_invalidation`, `public.athlete_profiles` -> `frequency_profile_invalidation`, `private.frequency_reviewers` -> `frequency_reviewer_invalidation`.
- Dynamic DDL: NOLOGIN registrar/test-executor roles, forced RLS and revoke-all for three policy tables, immutable preference/decision triggers; rename `private.v6_public_plan` to `v6_public_plan_without_frequency`, then install wrapper. No role membership or reviewer INSERT.

## Local rehearsal evidence and limits

Both the clean accepted 47-migration boundary and a boundary with the two actual hosted function definitions were upgraded with the exact 16 file contents, in G1/G2/G3 transactions. Each final database passed **722/722 assertions in 37 suites using the explicit A5 overlay**. The untouched A5 fixture separately reproduced 8 passing assertions, 1 failing assertion and a 23514 abort before the remaining 20 assertions; it is not a passing original fixture.

All **51 preexisting tables** retained equal canonical row hashes after EACH group, including 325 historical templates/loads, four physical workouts/private planned snapshots, two activities and one realized private-load record. Persisted synthetic ordinary onboarding, a separately approved historical plan and namespaced historical activity evidence existed before installation. Six historical/A5 smoke suites passed after each group. Before installation, 25/27 attempted current historical suites passed; the current Phase-5 suite references the not-yet-existing inactive_v6 column, and the current 39-function conflict inventory includes missing V2/V6 functions. These two pre-boundary failures are retained as unavailable final-schema tests, not hidden or counted as passing. No test was weakened.

A deliberately injected failure after all 11 G2 migration bodies, before commit, restored equal schema and data from a fresh connection. The expanded local disable fixture retained equal hashes for all 64 final tables and equal confirmed mobile-plan projection; direct V6/frequency/move/catalog calls were denied and historical/A5 smoke suites still passed. The older four-RPC fixture is insufficient for later wrappers/shared A5 dispatch.

See [compatibility matrix](JOREN_V6_PRODUCTION_COMPATIBILITY_MATRIX.md), [recovery readiness](JOREN_V6_BACKUP_AND_RECOVERY_READINESS.md), [conditional rollout](JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN.md) and [Dutch release decisions](JOREN_V6_REMAINING_RELEASE_GATES_NL.md). No hosted migration, hosted fixture, backup restore, catalog activation or deployment occurred.
