# Phase 13 and 14 remediation R1 decisions

Date: 2026-09-11
Decision owner: Start23 product and technical authority, through the explicit
R1 implementation approval dated 2026-09-11.
Status: approved for the MVP. The MVP roadmap and
`phase-13-joren-ruleset-1` remain authoritative if a conflict is found.

This record closes only the decisions required by remediation phase R1. It
does not approve the R2 upgrade flow, the R3 data cutover, the R4 remaining
onboarding fields, or the R5 correction implementation.

## R1-D1: average-HR correction after Phase 13 load calculation

Once an activity has a Phase 13 private-load/provenance record, the ordinary
RPE/feedback correction flow must reject an attempt to change the stored
average HR. Omitting average HR, or idempotently resubmitting the exact stored
value, does not constitute a measurement change.

The rejection must preserve the original average HR, originating zone-profile
ID and snapshot, ruleset, calculation inputs, private-load record, and append-
only revision provenance. Optimistic concurrency and retry idempotency remain
mandatory. R5 owns the atomic implementation and its original-HR, changed-HR,
duplicate, stale-write, privacy-leak, and audit tests.

A future measurement re-evaluation, if approved, must be a separately named,
versioned, atomic operation with audit history. R1 does not define or implement
that future workflow.

## R1-D2: version-aware onboarding state

The current implemented onboarding version is
`phase-13-onboarding-v1`; its associated ruleset is
`phase-13-joren-ruleset-1`. Version compatibility is an explicit equality
decision, never lexical or date-string comparison.

The R1 representation consists of:

- nullable `completed_onboarding_version` and `completed_ruleset_version` on
  `onboarding_sessions` while a session is incomplete;
- an append-only `onboarding_completion_records` history;
- `current_*` and `completed_*` version fields, `upgrade_required`, and
  `missing_upgrade_steps` in the owner-scoped onboarding state;
- the persistence-independent assessment in
  `backend/app/modules/onboarding/versioning.py`, which R2 must also use when
  it adds planner gating rather than recreating version logic.

All completions that predate this representation are backfilled as
`legacy-unversioned`. Their linked planning request's exact stored ruleset is
copied when present; no ruleset is inferred from current data. The immutable
history row retains completion time, completed steps, request ID, and session
revision. A new current completion records both current versions atomically.

A historical completion is current only when both stored versions equal the
current versions and all current implemented prerequisites remain satisfied.
Otherwise its public state is `upgrade_required`. The state contains only the
missing current steps; still-valid profile, history, goal, or active-zone data
is not requested again. A legacy RPE-only setup remains readable but never
satisfies the current `zones` step.

R2 owns the actual legacy-upgrade orchestration and the remaining parity work
across mobile, API, direct RPC, and planner. The old direct completion RPC is
retained for compatibility in R1; the backend current path uses the new
versioned entry point, and R2 must remove its ability to bypass upgrade rules.
R4 must introduce a new incompatible onboarding version when its additional
monitor and explicitly confirmed timezone requirements become enforceable.

## R1-D3: current run/bike calibration capability

The approved Phase 13 run/bike evaluator requires measured average HR. Current
MVP protocol discovery therefore exposes only the Phase 13 submaximal protocol
for run and bike. Run exposes `heart_rate`; bike exposes `heart_rate` and
`combined`, both of which require average HR in the existing observation UI.
Pace-only, power-only, and RPE-only Week-1 configurations are rejected.

Historical run/bike field-test protocols and their immutable definitions,
observations, evaluations, and provenance remain in the registry and remain
readable/evaluable for historical records, but cannot be selected or newly
scheduled through the current setup/assignment paths. Swim retains pace/CSS
protocols and never gains an HR requirement. No physiological formula changed.

R2 owns the complete mobile-to-API selectable-mode matrix, measured swim-time
contract, and user-facing capability copy.

## R1-D4: identity and physiology split for R3

### Target ownership model

R3 will create `private.athlete_identity_map` with:

- `athlete_id uuid primary key default gen_random_uuid()` as the opaque,
  immutable business identifier;
- `auth_user_id uuid not null unique references auth.users(id) on delete
  cascade` as the only direct authentication mapping;
- creation provenance/timestamps, with no authenticated table grants.

One mapping is created once per authenticated account. `auth_user_id` is never
accepted from a client payload. Owner resolution starts with the verified
access token's `auth.uid()` and resolves through the private mapping. A narrowly
scoped `private.current_athlete_id()` helper may be used by RLS: it must have an
empty fixed `search_path`, return no row for a null/unknown `auth.uid()`, expose
no other mapping, and have only the execution privilege needed by authenticated
RLS evaluation. The private schema is not exposed through the Data API.

All athlete-owned domain tables will ultimately join on the opaque athlete ID,
not `auth.users.id`. This includes onboarding/history/goals/zones/planning,
activities/private loads, check-ins/restrictions, calibration, integration
ownership, swipe drafts, and completion history. Provider credentials and
private load remain private regardless of the identifier migration.

### Split profile records

- `public.athlete_identifying_profiles`, keyed by opaque `athlete_id`, owns
  `first_name` and `last_name`.
- `public.athlete_physiology_profiles`, keyed by opaque `athlete_id`, owns
  `date_of_birth` and `resting_heart_rate_bpm`.
- Operational onboarding/timezone state remains separate from both records.

Each profile table receives independent explicit grants, forced RLS, owner
policies through the mapping, and separate mutation paths. Identifying-profile
writes may update only the two identifying columns. Physiology writes are a
critical RPC-only path using the token-derived athlete ID and a critical-write
trigger. Neither table grants anonymous access. Self-profile DTOs omit
`auth_user_id`; an opaque athlete ID is never treated as authentication even if
a resource contract needs to return it. The Expo application receives no
service or secret credential.

### Forward-only migration sequence

R3 must use new migrations; no applied migration is edited.

1. **Expand and map.** Create the private mapping and both profile tables with
   explicit grants/RLS. Backfill one random opaque ID for every existing
   `auth.users` account. Add nullable `internal_athlete_id` columns to every
   athlete-owned table whose current `athlete_id` is an auth UUID, populate
   them only by joining the private mapping, add indexes and foreign keys, then
   make them non-null where the old owner key is non-null.
2. **Copy without reinterpretation.** For every existing `athlete_profiles`
   row, copy `date_of_birth` and `resting_heart_rate_bpm` exactly into the
   physiology record. Store the source profile revision and backfill timestamp
   as migration provenance. Create the identifying record with null names when
   no historical name exists; do not synthesize names. Do not normalize,
   recalculate, round, or relabel physiological values.
3. **Cut over together.** Update owner-scoped repositories, RPCs, composite
   foreign keys, triggers, snapshots, and RLS policies to use
   `internal_athlete_id`. Public requests continue deriving the owner from the
   verified token. During the dual-key window, writes must populate both keys
   from the mapping in one transaction; no client supplies either owner key.
4. **Verify before contract.** Assert one mapping per auth user, no unmapped
   legacy owner, row-count parity, exact DOB/resting-HR equality, unchanged
   private-load/ruleset/profile IDs and calculation fingerprints, and two-real-
   user isolation for both profile tables and every affected RPC.
5. **Contract forward.** Only after the expand/cutover release and verification
   gates pass, add a later migration that removes legacy auth-UUID business
   foreign keys and renames `internal_athlete_id` to `athlete_id`. Retain the
   private mapping and backfill provenance. Any production discrepancy is fixed
   by another forward migration, never by editing or replaying an applied one.

Account deletion retains the existing cascade lifecycle through the private
mapping; this decision does not introduce a new archival or deletion policy.
Historical physiology/load/calibration/ruleset records retain their exact
values and version provenance throughout the identifier cutover.

## Verification responsibility split

R1 supplies the representation, migration foundation, deterministic state
tests, capability filtering, decision record, and traceability. R2 implements
the upgrade and complete calibration contract; R3 executes the identity split;
R4 adds remaining mandatory onboarding data; R5 implements activity correction;
R6 supplies the final database/security/integration/release evidence.
