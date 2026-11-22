# Questions for Joren's independent review

Date: 26 October 2026. Source: `aff74558d0a6511286a4a84a44ea25a03ca57549`. These are review questions, not scientific findings or recommendations. The technical audit did not change or independently endorse any training formula, anchor, coefficient, taper factor, progression value, recipient cap or safety threshold.

The pure engine's implemented arithmetic matches the selected approved fixtures and boundary tests. Passing fixtures establishes implementation parity, not scientific appropriateness. Joren's independent methodology review remains the right authority for that assessment.

## J-01 — identify the complete review scope and record

**Type:** review provenance / release decision. **Priority:** before beta release.

Does the external review explicitly cover both `phase-13-joren-ruleset-1` (baseline/calibration/activity-load behavior) and `joren-planning-ruleset-2` (phase eligibility, repeated occurrences, high-budget policy, 72/48-hour spacing and injury redistribution), plus the actual current field-test protocols?

The code stores both load and planning versions, but startup checks only a Phase 13 review version (WOMBO-002). Please supply the accountable qualified reviewer identity, immutable review-record reference, exact versions covered and any exclusions. An LLM or a nonempty configuration string cannot supply the review itself. This question does not reopen already accepted constants.

Sources: `backend/app/core/config.py:101`; `physiology/specification.py:179`; `docs/requirements/phase-13-joren-ruleset-1.md`; `docs/requirements/joren-workout-selection-phase-2026-09-28.md` including the final addendum; `docs/implementation/joren-planning-ruleset-v2.md`.

## J-02 — define reliability of a weekly aggregate with missing activity measurements

**Type:** measurement/decision-input contract; possible technical completeness bug U-001. **Priority:** before claiming the next-week loop reliable.

The individual-activity implementation distinguishes observed complete, observed partial, estimated-from-average-HR and unavailable load, and preserves provenance. The weekly SQL sums known rows, while activities with missing calculation/load can contribute differently to count and duration/coverage.

For a week with one measured processed session, one awaiting RPE/no-load session and one partially observed session, what completeness information must be carried into progression and intensity-debt decisions? Is a known subtotal usable under a specified contract, or must the aggregate remain unavailable/partial until a required condition is met?

Please define the interpretation of missing evidence, not a new imputation formula. The audit does not propose treating missing load as zero, scaling partial observations, or enabling sRPE. Technical follow-up should preserve the chosen completeness state and test it in PostgreSQL.

Sources: `supabase/migrations/20260910215947_phase_13_joren_ruleset.sql:1719`, `:1723`; `PlanningService._load_samples`; `resolve_target`; `physiology/joren.py::zone_load` and `average_hr_zone_load`.

## J-03 — scope all-zero and asymmetric-history multi-sport beginners

**Type:** product/catalog coverage decision with scientific review if new prescriptions are needed. **Priority:** before inviting affected athletes.

The existing accepted decision fixes the all-zero baseline at 45.0 privately and forbids inventing sport-specific minimum targets for a partly untrained required discipline. Do not change those values to make tests pass.

In the full-catalog synthetic matrix, all-zero run generates a two-workout base prescription; all-zero triathlon returns `catalog_capacity_unsatisfied`. A triathlete with only run history returns the explicitly intended `zero_history_discipline_baseline_unavailable`.

Should beta eligibility clearly exclude those unsupported compositions for now, or will reviewed beginner catalog/goal coverage be supplied under an explicit versioned decision? If coverage is expanded, specify the supported fixture and prescriptions rather than asking engineering to infer an allocation or coefficient.

Sources: `docs/requirements/phase-13-joren-ruleset-1.md` zero/asymmetric-history decisions; `planning/domain.py::build_weekly_plan`; `evidence/engine-matrix-results.json`.

## J-04 — non-Monday races and the partial-week taper boundary

**Type:** already documented scientific/product decision gap. **Priority:** before advertising a complete race lifecycle for these dates.

The implementation preserves the exact D-7 through D-1 taper window. An exact Monday race can use the preceding Monday–Sunday weekly target; other race weekdays fail closed with `partial_week_taper_rule_required`, because no approved partial-week reduction/coverage rule is present.

What supported race-week behavior should beta promise? Either define an explicit beta exclusion/limitation or supply a reviewed target/calendar/catalog specification with boundary fixtures and provenance. The audit does not suggest a daily curve, duration, reduction percentage or extra taper factor.

Sources: `planning/domain.py::resolve_target`; current roadmap remaining release gates; `backend/tests/test_planning_domain.py::test_partial_week_taper_requires_approved_curve`.

## J-05 — injury review, removal and reintroduction scope

**Type:** scientific/product scope beyond the confirmed software defects. **Priority:** clarify before testing injury removal across weeks.

Current approved redistribution is limited to the existing eligible bike/swim recipients with positive basis and safe caps; running is not a recipient. Technical tests exercise those caps and no automatic zone activation.

Once an athlete explicitly removes an old restriction, is the existing latest-approved per-sport basis sufficient for the intended next-week behavior, including a sport absent from the restricted plan? Are any professional-clearance statuses or later reintroduction behaviors intentionally outside beta scope? If a new rule is required, provide it explicitly with review/provenance and fixtures.

This does **not** delay the purely technical fixes: saved restriction answers must be hydrated, a seven-day due review must not silently mean clearance, and a new plan must reach the shared owner (004/005). No clinical clearance rule should be invented by engineering.

Sources: `physiology/injury.py`; `planning/domain.py::_injury_adjusted_target`; `checkins/domain.py`; final Joren addendum.

## J-06 — date-only scheduling and actual elapsed spacing

**Type:** scientific review of an existing explicit scheduling convention, not a formula defect. **Priority:** review communication before beta.

The accepted planner uses athlete-local **noon** as an internal projection for date-only workouts. This supports deterministic elapsed-hour comparisons without prescribing a training time. An athlete can actually train at different times of day, so a projected 72/48-hour gap is not necessarily the actual elapsed gap.

Is that convention and its athlete-facing explanation acceptable for the intended beta? If actual-time enforcement is desired later, it needs a new explicit product/data contract. The technical audit's cross-week omission (003) must be fixed using the unchanged existing rule regardless of this answer.

Sources: `planning/domain.py:1117` (`canonical_schedule_instant`); `physiology/anti_stack.py`; date-only planning decision and V2 final addendum.

## J-07 — repeated source workouts, session count and multi-sport composition

**Type:** methodology confirmation / future scope. **Priority:** before expanding beyond tested goal compositions.

Repeated immutable templates and multiple sessions on one date are intentionally allowed. The engine fits a finite multiset up to its implemented occurrence bound. It retains whole-workout source low/high buckets and source prescriptions; segments remain execution guidance. Some normal high-volume run fixtures intentionally repeat source templates.

Does the reviewed methodology accept these resulting repeated-session compositions for the supported beta profiles? If there should be a different session-frequency/duration, brick/asymmetric allocation or goal-specific limitation, please supply an explicit versioned rule. The audit proposes no daily/session cap and does not treat repetition alone as a technical bug.

Sources: V2 decision record; `docs/requirements/workout-distribution-decision.md`; `backend/tests/test_mvp_catalog_coverage.py`; full-source phase/occurrence fixtures.

## Already-approved behavior to assess within the independent scientific review

These are implemented-as-designed facts, not newly reopened missing specifications:

- Decimal baseline components and one final HALF_UP total; zero differs from missing.
- Joren's current calibration anchors and contiguous discrete HR/CSS boundary ownership, including documented source-example discrepancies.
- The accepted mean-HR full-duration estimate amendment with separate private method/profile provenance; partial observed zone time remains unscaled and takes precedence.
- Whole-workout low/high classification from the reviewed source bucket, with segment zones preserved for execution.
- Build weeks 1–3 high-budget range and week-4 Z5 eligibility; recovery/base/taper low-only eligibility.
- Latest approved plan provenance, illness exclusion, missing-data hold/fallback, recovery and exact taper behavior.
- Existing injury redistribution and recipient caps under planning V2.

If Joren changes any of these materially, engineering must receive the exact new decision, version and migration/historical-treatment instructions. Historical calculations must not be silently reinterpreted.

## Technical defects that do not require Joren to invent a new rule

WOMBO-003 (missing neighboring-week schedule context), 004 (restriction answers lost on resume), 005/006 (next-week state handoff/retry), 007 (CPU isolation/performance), 008–013 (mobile recovery), and release/auth/privacy safeguards can be remediated against existing contracts. None is justification to alter a physiological coefficient during technical cleanup.
