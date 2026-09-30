# Joren planning ruleset 2 implementation

The final Joren answers in the implementation request supersede the open
questions in `docs/requirements/joren-workout-selection-phase-2026-09-28.md`.
New planning decisions use `joren-planning-ruleset-2`. Phase 13 retains the
Start-TSS and realized-load calculation version `phase-13-joren-ruleset-1`;
a separate plan-revision column records the new planning version. The
reviewed source workouts keep their predefined private source load in immutable
catalog provenance. For distance-only swims, the active Phase 13 projection
has no planned load: it cannot infer duration or calculate new TSS from the
old source value, so these swims do not enter private target-fit or a new plan.
They also remain outside time-based 80/20 percentages. No historical plan or
source workout row is rewritten.

## Selection and phases

- The 154 reviewed source workouts receive immutable version-2 successors
  eligible for the ordinary athlete swipe deck. Field tests remain explicitly
  scheduled. Event words in source descriptions are not eligibility filters.
- The selector fits a finite multiset of at most 24 occurrences to the private
  weekly target, composition and high budget. It may repeat an immutable
  template, but every swipe card has a distinct UUID and every accepted
  occurrence creates a distinct planned-workout row. The fixed draft count,
  context fingerprint, revision precondition, idempotent accept retry and
  pending approval lifecycle remain in force.
- Base, recovery and taper offer only complete workouts whose source segments
  use Z1/Z2 and whose reviewed whole-workout bucket is low. The race date
  anchors the four-build/one-recovery rhythm. Build weeks 1–3 exclude Z5 and
  fit Z3/Z4 work to 70–90% of the nominal high budget without exceeding that
  budget. Build week 4 permits Z5 and requires one when a safe high allocation
  and compatible Z5 card exist. Z5 does not change the weekly target.
- The workout's reviewed complete classification owns the low/high bucket.
  Z3 is high. The existing recovery and taper target calculations remain.

## Injury allocation

Only newly generated proposals use the new redistribution rule. The current
weekly target is calculated before injury adjustment. The latest approved
per-sport planned-load snapshot, or the Phase 13 onboarding sport components
for the first week, supplies the pre-injury proportions. Those proportions
project the current weekly target onto each sport. The blocked sport is
removed. At most 80% of its projected budget may move to a non-blocked bike
or swim recipient with a positive prior/current basis and an eligible low
workout. Each recipient is capped at the larger of its normal projected target
and 110% of its approved prior/onboarding sport basis. This is a narrow use of
the existing 10% progression boundary, not permission to fill all blocked
load. Any excess is discarded. The selector enforces those per-sport caps and
keeps replacement recipient workouts at Z1/Z2. Running never receives
replacement load. The high budget is based on unblocked normal load, so a
transfer cannot create additional high work.

Bike/swim cross-training opt-ins are structured athlete choices stored on the
swipe draft and pending plan revision. A zero-basis sport still has no reviewed
nonzero safe capacity, so an opt-in alone does not prescribe it. If no safe
work remains, the pending rest-only behavior applies. The athlete still
approves or rejects the proposal.

## Spacing and verification

High sessions of the same sport require 72 elapsed hours for running and 48
for cycling or swimming. Auto placement, swipe feasibility, manual placement
and direct moves use the same hard validator. Date-only schedules retain the
existing athlete-local noon projection for elapsed-hour comparisons.

The run-only Marathon Gent 0/1/3/6/15-hour matrix, the uninterrupted
four-week build progression/Z5 fixture, repeat occurrence API flow, private
injury allocation, spacing boundaries and the existing backend/mobile suites
are covered by deterministic tests. The 3/6/15-hour run selections place all
2/9/11 occurrences, including repeated immutable templates, under broad
availability while preserving anti-stack rules.

Migration `20260929210000` was applied only to `start23-dev` after all prior
local and remote migration versions matched. It creates 154 version-2 source
successors and leaves the 19 historical plan revisions and their existing load
ruleset values intact; the new planning version column remains null for those
historical rows. All 26 hosted rollback-only pgTAP suites passed, including
catalog successor, owner isolation, service-only mutation and private-load
access checks. A rollback-only hosted Joren fixture also confirmed distinct
repeat occurrence IDs, owner-scoped cross-training consent and cross-owner
draft isolation. Linked error-level database lint found no errors. Railway
`r6-staging` could not accept a candidate upload because its trial has expired,
so hosted application smoke remains unavailable.

Broader asymmetric triathlon, swimrun, brick and goal-specific methodology
remain future product decisions. No new formula for those areas was added.
