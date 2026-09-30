# Joren workout selection and phase decision record

Date: 2026-09-28. Source: `AI Trainingsalgoritme Overzicht.pdf` (three pages)
and the explicit approval supplied with this implementation task. This record
describes the next planning ruleset; it does not change historical Phase 13
calculations or authorize production activation.

## Approved behavior

- All 154 reviewed START23 v0.1 source workouts can be swipe candidates after
  deterministic phase, intensity, injury, capability, availability, spacing,
  and budget filtering. The athlete still accepts or passes each card.
- An immutable template can be accepted more than once in a week. Every accept
  creates a distinct planned occurrence. Revision and retry idempotency remain.
- Z1 and Z2 belong to the low bucket; Z3, Z4, and Z5 belong to the high bucket.
  The reviewed source `Emmer (80/20)` value owns the classification of a
  complete mixed-zone workout. Its segments still own execution guidance.
- Base and recovery admit Z1/Z2 candidates. Recovery has no automatic high
  candidate. Taper admits only Z1/Z2 candidates during the existing D-7 to D-1
  window, with the existing reduction factors.
- Build retains a 20% private-load high budget. About 75% of that high budget
  uses Z3/Z4; Z5 is limited to the final part of a build block.
- Descriptive event labels such as Halve, Volledige, Sprint, Fitheid, and Fondo
  impose no goal-match eligibility restriction.
- High-bucket sessions of the same sport require 72 elapsed hours for running
  and 48 elapsed hours for cycling and swimming. Automatic and manual placement
  must enforce these limits without disclosing private load.
- The Phase 13 Start-TSS coefficients, one-decimal HALF_UP rounding, 45.0
  zero-base result, recovery reduction, and taper factors are unchanged.

## Prior behavior superseded by this decision

- `athlete_selection_only` on the imported source rows prevents their use in
  `select_workouts` when deriving a swipe draft's count and composition. This
  restriction is superseded; `explicit_scheduling_only` remains for tests.
- The once-per-draft check on template IDs is superseded. A template ID remains
  immutable catalog identity, not occurrence identity.
- Phase 10's two-complete-local-rest-date interpretation for cycling and
  swimming is superseded by the specified 48 elapsed hours. The prior
  nonblocking manual spacing warning is superseded by server rejection.

## Final decision addendum, 2026-09-29

The later explicit Joren answers supplied with the implementation request
resolve the open items below. Base is Z1/Z2 only. Build weeks 1–3 fit Z3/Z4
work to 70–90% of the nominal private high budget; week 4 releases Z5.
Recovery and taper are Z1/Z2 only. Injury redistribution explicitly supersedes
Phase 13 zero redistribution for new proposals: at most 80% of blocked sport
load may move to safe, positive-basis bike/swim capacity under the existing
10% progression boundary. The implementation and provenance are recorded in
`docs/implementation/joren-planning-ruleset-v2.md`.

## Historical open decisions and preserved behavior

1. **Base high budget:** the current 80/20 model includes a 20% high target,
   while the new base description admits Z1/Z2 and puts Z3 in review. Decide
   whether the high budget is intentionally unused in base or whether a
   separately reviewed base high exception exists. Until then, do not offer
   Z3/Z4/Z5 automatically in base.
2. **Build high composition:** define the permitted private-load range for
   "about 75%" Z3/Z4 of the build high bucket. Session counts are not a
   substitute.
3. **Build Z5 position:** the code derives a four-build/one-recovery rhythm
   from the race date, but no current decision defines which week or workouts
   are the final part of a build block for Z5 release. Fail closed for Z5
   candidates until this is specified.
4. **Injury redistribution requires explicit supersession decision.** Phase
   13 mandates zero automatic redistribution. The new PDF requests a 0.8
   multiplier and transfer to alternative low-impact sports but does not
   resolve its conflict with Phase 13 or specify allocation among multiple
   alternatives. Keep zero redistribution and blocked-sport exclusion.
5. **Multi-discipline allocation:** the current baseline calculates each
   reported sport independently, while planning requires every uninjured goal
   sport and has no approved asymmetric, triathlon, swimrun, or brick load
   allocation. The current goal model supports run, bike, swim, duathlon, and
   triathlon; swimrun is not a configured race type. No new percentages or
   load formulas are approved here.

## Provenance and implementation gate

Any activated planner change needs a new version in plan revisions and swipe
drafts while existing Phase 13 onboarding and load calculations retain their
own version. The existing `create_weekly_plan_proposal` RPC uses its one
`ruleset_version` field to choose the Phase 13 load snapshot method, so a new
planning version needs a forward-only persistence change that keeps the Phase
13 load calculation and records the new planning policy separately. Historical
rows must remain attributable to the versions that produced them.

## Repository audit for implementation

- The applied source import inserts `athlete_selection_only = true` for every
  source row. Its phase tags are low: base/build/recovery and high: base/build;
  none has a taper tag. A forward-only migration is needed for any persisted
  eligibility metadata change. The source SQL JSON retains the reviewed
  whole-workout bucket and each segment's zone.
- `select_workouts` excludes athlete-selection-only rows when deriving the
  automatic count. It enumerates all combinations of the remaining distinct
  IDs and has a capacity guard based on their one-use summed load. Simply
  removing the flag would make this enumeration impractical on the full source
  catalog. A bounded deterministic selector and swipe completion check are
  required together.
- Swipe state currently stores `accepted_template_ids uuid[]`; its SQL trigger
  requires accepted IDs to be unique, counts composition using `WHERE id = ANY`,
  and keys placements by template UUID. The Python state and public placement
  URL use the same identity. Repeats therefore need an occurrence ID across
  draft history, placement, API, mobile, and persistence. `planned_workouts`
  already has a separate row UUID per inserted occurrence.
- The 50 reviewed run rows comprise 20 low and 30 high templates. The 20 low
  source templates alone have more total reviewed private load than the
  15-hour run Start-TSS target. A read-only subset calculation finds these
  closest distinct low-template sums: 45 for 0 h, 65 for 1 h, 194 for 3 h,
  388 for 6 h, and 971 for 15 h. These are capacity evidence, not generated
  plans or an approved workout-count policy.
- Source event labels are currently description text. `eligible_workouts`
  filters discipline, injury, phase, capability, and private-load availability;
  it does not compare those descriptions with race-goal labels.
- `classify_segment` already maps Z1/Z2 to low and Z3/Z4/Z5 to high. Imported
  mixed-zone rows retain the reviewed `Emmer (80/20)` bucket as the complete
  workout classification.
- Automatic placement calls `find_anti_stack_violations`. Direct plan moves
  currently return nonblocking warnings, and Phase 10 cycling/swimming uses
  two complete local rest dates instead of the newly approved 48 elapsed
  hours. Both paths need the new versioned policy.
- Injury zero redistribution is enforced by `apply_mvp_injury_policy` and by
  `build_weekly_plan`, which sums only uninjured onboarding components for a
  first target and returns a pending rest-only draft when all goal disciplines
  are blocked. `test_injury.py`, `test_planning_domain.py`, and
  `test_planning.py` cover that behavior. The Phase 13 proposal RPC also
  rejects any planned workout in `confirmed_injuries`. No current migration
  implements the new 0.8 transfer.
