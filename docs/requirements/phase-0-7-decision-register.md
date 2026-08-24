# Phase 0-7 decision register

## Purpose and status

This is the consolidated list of decisions raised during Phases 0 through 7,
with the accepted Phase 8 delivery decisions appended so the existing register
remains the single decision source.
It distinguishes an accepted product/rules decision from later delivery or
production-verification work. Decisions 1 through 12 were accepted on
2026-08-11; decisions amended or added on 2026-08-13 are explicitly marked
below. The existing deterministic implementation remains
`phase-3-ruleset-3` until each amended rule is versioned, implemented, tested,
and covered by its applicable review. No accepted decision is described as
implemented merely because it appears in this register.

Qualified physiological production review of the active rules and
`start23-zone-model-1.0` was confirmed complete by the product owner on
2026-08-24. Reviewer identity and the evidence dossier remain in the external
product-governance record. The same review gate reopens for every later ruleset
or material model change.

## Resolved on 2026-08-11

### 1. Catalog-defined 80/20 bucket

Decision amended 2026-08-13: the workout catalog is authoritative for a
training's 80/20 classification. `Trainingen START23.v01` contains an explicit
`Emmer (80/20)` field: `20%` means the complete training belongs to the
intensive weekly bucket and `80%` means the complete training belongs to the
quieter weekly bucket. Weekly BR-003 duration arithmetic uses that declared
bucket and the training's total duration; it does not reclassify the training
from whichever interval-zone duration happens to dominate.

The separate interval fields (`Tijd`/`Afstand` and `Zone`) remain authoritative
for how the workout is executed and for the private physiological load/TSS
calculation per interval. They do not override the declared 80/20 bucket.

Delivery status: not implemented against the complete catalog. The current
code derives and validates a bucket from segment dominance. That behavior and
its tests/specification must be replaced when the `Trainingen START23.v01`
catalog is imported. The former exact-tie rule is no longer the source of a
catalog workout's weekly bucket.

### 2. BR-003 display precision

Decision: the primary UI shows complementary whole percentages using half-up
rounding of low intensity and `high = 100 - low`. Detail UI also shows exact
low/high minutes. Full decimal precision remains internal.

Implementation: weekly-plan responses expose stable display percentages and
exact detail minutes; the planning screen renders both.

### 3. Realized intensity feedback

Decision: realized intensity debt is the positive difference between realized
and planned high-intensity fractions. It affects only the first following
non-recovery week, never carries across multiple regular weeks, and never
overrides taper or recovery. At least 60% of realized activity duration must
have classified low/high data. Unknown time is excluded from the realized
ratio rather than counted as low. Swim technique is low only when an explicit
template segment identifies it.

Implementation: the private planning projection supplies planned, realized,
and classified minutes. The deterministic engine gates on 60% coverage,
applies the 5% configured floor, and uses the corrected fraction in deck
selection after load matching. Public output remains qualitative.

### 4. BR-009 soft ranges

Decision: format/unit and technically impossible values are hard validation;
plausibility is always a configurable soft review. Out-of-range values are
accepted with confirmation and provenance. A soft-range rule must identify
metric, discipline, unit, bounds, applicability, evidence, reviewer, validity
dates, and ruleset version. No concrete ranges are active until reviewed
records containing all metadata are supplied.

Implementation: `ZoneSoftRangeRule` enforces that metadata and
`assess_metric_with_soft_limits` accepts but flags missing, expired, or exceeded
configuration.

### 5. Calculated zone percentages

Decision refined 2026-08-13: before showing any threshold or zone fields, the
zone screen asks per discipline whether the athlete knows the relevant
threshold value, such as swim CSS. The flow then has two primary routes:

1. **Threshold known.** The athlete enters at least the threshold. Entering the
   five zone boundaries is optional. When the boundaries are left empty,
   Start23 calculates them from the threshold using the reviewed,
   discipline-specific deterministic protocol. When boundaries are supplied,
   Start23 validates and stores the athlete-entered values instead.
2. **Threshold and zones unknown.** The first training week supplies standard,
   safely executable calibration training through the normal training plan.
   After completion, the athlete enters the TSE feeling score. The prescribed
   training context, eligible realized measurements, and TSE feedback are
   evaluated together by a reviewed deterministic protocol to produce a
   pending threshold-and-zone proposal. A TSE score alone cannot be converted
   into a pace in seconds, watts, or BPM without such an explicit mapping and
   the required training/measurement context.

For swim, the threshold is CSS. Equivalent discipline-specific flows may use
FTP or threshold heart rate for cycling and threshold pace or LTHR for running.
The UI tells an athlete who selects the unknown route that the first training
week will be used to determine the scores. Blank optional zone fields must not
be submitted as malformed manual boundaries and must not cause `422`.

Every calculated result is versioned and retains its source (`threshold_derived`,
`self_test`, or `calibration_workout`). A field-test or first-week calculation
creates a pending proposal and never changes active zones automatically. The
athlete must review and confirm it. Formula percentages, the definition and
scale of TSE and its relationship to the existing RPE field, minimum data
quality, valid calibration workouts, contraindications, and discipline mappings
require Physiology Rules Review Board approval before production use.

Source check: `Start23_Fysiologische_TSS_Logica.pdf` defines fixed IF values per
zone and private TSS/sTSS calculations per interval. It does not define a
TSE-to-CSS, TSE-to-FTP, or TSE-to-zone-boundary conversion. That missing
deterministic mapping must therefore be documented and approved separately; it
must not be invented during implementation.

Delivery status: the mobile zone intake now presents the three explicit pistes
per discipline: A manual known values, B automatic test/calibration, and C
biometric fallback. Piste A uses the implemented athlete-entered threshold plus
mandatory manual boundaries. Piste C uses the implemented heart-rate fallback
for bike/run; it is correctly unavailable as a CSS estimate for swim. Piste B
is visible but safely disabled. Threshold-only submission, reviewed boundary
calculation, standard Week-1 calibration persistence/training, TSE capture and
conversion, measurement evaluation, and the pending initial-zone proposal are
not yet delivered. Until they are, Piste B cannot complete onboarding and empty
manual boundaries can still block Piste A. Public zone provenance already
avoids the ambiguous `validated` boolean.

### 6. Inverse pace boundary ownership

Decision: a shared boundary always belongs to the physiologically more intense
zone. Ascending metrics therefore use the higher numeric interval at equality;
descending pace metrics use the lower/faster interval.

Implementation: zone classification branches on intensity direction and has
explicit equality fixtures for power and pace.

### 7. Cycling speed

Decision: cycling speed is not a persisted zone metric and cannot drive zone
validation or planning. Average and maximum speed may be stored as bike
activity telemetry. Raw speed series remain deferred with raw telemetry.

Implementation: the zone parser/type was removed; canonical bike activity
metrics accept bounded average/max speed and reject speed on swim/run.

### 8. Non-positive physiological-debt result

Decision: do not publish or clamp a non-positive regular target and do not
activate rest automatically. Stop regular generation and create a typed
pending recovery/manual-review proposal using the existing approved recovery
calculation. The athlete must approve or edit it. A repeated unsafe result
requires qualified human escalation and creates no further automatic
correction.

Implementation: `manual_review_recovery` is a target basis with a public
qualitative warning. Repetition raises
`physiological_debt_escalation_required`.

### 9. Sex or physiology input

Decision amended 2026-08-13: an optional physiological-sex field may be
collected separately from gender identity. It is not used to estimate FTP or
to change plan content directly. Its only computational use is the explicitly
chosen maximum-heart-rate fallback: `226 - age` for female and `220 - age` for
male. If the athlete does not provide the field, Start23 must not infer it and
must use a route that does not require this formula.

Although the product intent calls this field "for information", using it in a
maximum-heart-rate formula makes it a physiological input in technical and
privacy terms. The UI must therefore explain that purpose. The formula and its
applicability require clinical and privacy/legal review before production.
Known FTP, reviewed field tests, and RPE-guided workouts remain available
without this field.

Delivery status: not implemented. The current profile contract/schema omits
the field and the current estimated heart-rate fallback uses a different
age-only formula. A later ruleset and forward database migration must replace
that behavior without rewriting historical decisions.

### 10. Formal clinical-review ownership

Decision: use a Physiology Rules Review Board. Accountable is a qualified
sports physician or exercise physiologist; responsible is the product/ruleset
owner; qualified coach, engineering/data, and privacy/legal are consulted;
development and support are informed. Production approval requires evidence,
applicability, contraindications, tests, version, named approver, approval date,
and next review date. An LLM cannot own or approve a rule.

Implementation: rulesets carry evidence/applicability/test metadata and expose
a fail-closed production-review check. Appointment and sign-off for the active
rules and zone model were confirmed complete on 2026-08-24; changed rules still
fail closed until separately reviewed.

### 11. Injury semantics

Decision: Start23 represents functional restrictions, not diagnoses or medical
severity. States are `none`, `self_reported_limited`,
`self_reported_blocked`, `professional_restricted`, `clearance_required`, and
`expired`; allowed intensity is `none`, `low_only`, or `unrestricted`.
Restrictions are discipline-specific, attributable, time-bounded for review,
and never silently cleared. Every active restriction is re-evaluated weekly.
The athlete records the current situation and makes the plan choice; where a
physician has supplied restrictions or clearance, that advice and its date are
recorded and shown during the choice rather than silently overridden.
Resumption requires an explicit athlete action; alarm symptoms receive general
professional-assessment guidance.

Implementation: immutable domain types and validation implement these states
and the seven-day recheck without auto-clear. Durable weekly capture,
physician-advice attribution, athlete choice, and clearance UI remain Phase 8
delivery work, not undecided policy.

### 12. BR-010 injury redistribution

Decision: automatic injury-load redistribution is disabled in the MVP.
Blocked-discipline load is removed, the weekly budget may fall, and existing
eligible low-intensity workouts in other disciplines may be selected manually.
The historical 80% calculation may remain analytical but cannot drive a plan
until separate clinical approval.

Implementation: `apply_mvp_injury_policy` always redistributes zero; Phase 6
planning already removes blocked disciplines without replacement. Tests keep
the analytical 80% calculation separate from the active MVP policy.

## Resolved on 2026-08-24

13. The product owner confirmed appointment of the qualified accountable
reviewer and production sign-off for the active physiology rules and
`start23-zone-model-1.0`. Personal identity and the evidence dossier are kept
in the external product-governance record.

## Still open after these decisions

14. Define and review any concrete BR-009 soft-range records.

15. Define and clinically review the deterministic mapping from the planned and
realized calibration training plus athlete-entered TSE feedback to CSS, bike
FTP/heart rate, run pace/heart rate, and Zone 1-5 boundaries. Define the TSE
scale and its relationship to existing RPE, eligible measurements, minimum
data quality, contraindications, and percentages before using
`protocol_validated` or calculating complete zones. The physiological/TSS PDF
does not yet contain this mapping.

16. Deliver Phase 8 persistence, API, expiry, weekly re-evaluation,
physician-advice attribution, athlete choice, clearance, alarm-symptom copy,
and UI for the now-locked functional injury-restriction model.

17. Deliver the accepted race-date cycle alignment from decision 43. A race
always anchors backward planning; a non-race goal starts at cycle week 1.

18. Deliver the accepted weekly recurring-activity confirmation from decision
30 as part of Phase 8.

19. Review, classify, import, and verify Phase 8 taper coverage from the
available `Trainingen START23.v01` catalog export, as specified by decision 41.

20. Deliver non-race macrocycles and goal-specific intensity targets in the
new final phase. The product option must remain available; it is not part of
the current race-only MVP implementation.

21. Define automatic activity matching for proximity, ambiguous matches,
bricks, and multisport activities.

22. Define the exact missing-RPE fallback. The statement "RPE = TSS" is not an
implementable rule: RPE is a 1-10 perception score while TSS/load is a derived
quantity with a time component, and planned/realized TSS may not be exposed to
the athlete. Until clarified and clinically reviewed, missing RPE remains
missing and no RPE-dependent realized-load rule is applied.

23. Define richer correction behavior beyond the current pending cancellation
of eligible future high-intensity workouts.

24. Standardize cross-owner resource disclosure (`403` versus `404`).

25. Complete health-data legal basis, consent, minimization, retention,
deletion, export, backup, regional-processing, incident-response, age, and
medical-disclaimer policy.

26. Decide full physiological input/audit retention and any specially
authorized staff access to hidden TSS.

27. Select the first Phase 9 wearable provider and approve its OAuth, webhook,
storage, parser, and security protocol.

28. Select the Phase 10 LLM provider and approve its DPA and retention policy.

## Additional decisions accepted on 2026-08-13

### 29. Maintenance after the goal has already been achieved

Decision: when the active goal is explicitly marked achieved, regular weekly
load no longer increases under the 10% progression rule. Start23 maintains a
safe baseline, preserves the four-training-weeks/one-recovery-week rhythm, and
continues to target the reviewed 80/20 intensity distribution. This is a
maintenance state; it must not be inferred from a single successful activity.

Delivery status: not implemented. Goal-achievement state, athlete confirmation,
maintenance baseline selection, and exit conditions require a versioned rule
and persistence/API/UI work.

### 30. Weekly recurring outside activities

Decision: at the start of each week, ask whether the athlete will still do the
usual sports or strenuous activities outside the Start23 plan. The answer is
confirmed context for that week and may affect only a pending plan proposal.

Delivery status: assigned to Phase 8.

### 31. Extra sport in the week plan

Decision: the athlete can add sport outside the normal Start23 plan to the
current week and later record its actual duration and RPE. It contributes to
private realized weekly load and can influence the next pending proposal. The
mobile UI and public API never expose the resulting TSS/load number.

Delivery status: Phase 7 already supports an unmatched/extra completed
activity with duration and RPE and includes its private load in realized
history. Pre-scheduling an extra activity inside the week plan remains Phase 8
work.

### 32. RPE correction window

Decision: an activity RPE may be corrected during the athlete's current local
Monday-Sunday week. Once that week has ended, the RPE is immutable. Every
accepted correction must retain an audit trail; recalculated private load and
any resulting correction proposal must be deterministic and stale-safe.

Delivery status: not implemented. Phase 7 currently makes the first accepted
RPE immutable.

### 33. Manual workout movement boundary

Decision: a workout may be dragged only within its existing local training
week. It cannot be dragged to the following week. A comparable workout in a
later week is assigned by that later week's deterministic planning process,
not by carrying the prior database row forward.

Delivery status: implemented in Phase 6 in both the service and database RPC.

### 34. Restart after a completely inactive week

Decision: if a completed local training week has zero realized training, the
next proposal uses the most recent four complete local weeks as its baseline,
including the zero week. It does not apply automatic 10% progression to that
restart week. Recovery, taper, injury, and manual-review safety rules still
take precedence.

Delivery status: not implemented; the current Phase 7 regular baseline uses
available samples from 42 days and therefore does not yet express this exact
four-calendar-week rule.

## Audit resolution accepted on 2026-08-13

### 35. Risk acceptance for README test credentials

Decision: the email/password examples currently present in the root `README.md`
are deliberately fake, non-production credentials used only for testing. Their
presence is an explicitly accepted test-environment risk and is not treated as
a leaked production secret.

This acceptance is narrowly scoped. The values must never be reused for a
production, privileged, or real-data account, and it does not relax the rule
that real credentials and secrets stay outside the repository.

Delivery status: risk accepted; no credential removal or product-code change is
required by this decision.

## Phase 8 delivery decisions accepted on 2026-08-13

Decisions 36 through 44 define Phase 8 behavior or a related later-phase
boundary. They do not claim that the
behavior is already present in the application.

### 36. Rest-only result when every goal discipline is blocked

Decision: when all goal disciplines are blocked by active restrictions, the
application creates a safe, TSS-free, pending rest-only plan revision. It must
not return an ordinary planning failure, redistribute blocked load, or activate
the revision automatically. The athlete must confirm the pending revision
before it becomes active.

The public response and UI show only qualitative rest and restriction
information. They never expose planned or realized TSS.

Delivery status: assigned to Phase 8; not implemented.

### 37. Athlete-facing move and reschedule action

Decision: the mobile application provides an athlete-facing action to move or
reschedule a planned workout. Decision 33 remains the boundary: a workout may
move only within its existing athlete-local Monday-Sunday training week.

The request must carry the expected plan revision so stale changes fail safely.
Before confirmation, the UI shows qualitative warnings for relevant spacing,
recovery, restriction, or schedule consequences. Warnings contain no TSS and
do not silently change another workout.

Delivery status: assigned to Phase 8. The backend same-week move boundary
exists; the athlete-facing mobile flow and its full revision-aware contract are
not implemented.

### 38. Explicit public rest-day representation

Decision: every date intentionally left without a workout in a generated plan
has an explicit public rest-day representation in the API and mobile calendar.
This distinguishes a planned rest day from missing or not-yet-loaded planning
data. The representation may include a qualitative reason, but never TSS or a
private load budget.

Delivery status: assigned to Phase 8; not implemented.

### 39. Selection-aware remaining workout deck

Decision: after the athlete changes the selected workouts for a pending plan,
the remaining workout deck is recalculated against that exact selection and
expected plan revision. Ineligible cards are removed or clearly disabled when
the remaining duration, intensity, restriction, recovery, or scheduling budget
no longer permits them.

The server remains authoritative. The behavior may be exposed through a
dedicated endpoint or through recalculation in the existing pending-plan
response; that transport choice is an implementation detail. Public responses
and explanations remain qualitative and TSS-free.

Delivery status: assigned to Phase 8; not implemented.

### 40. Athlete-local weekly planning semantics

Decision: automatic weekly planning and post-check-in generation use the
athlete's local Monday-Sunday week, not a global UTC week. A scheduled trigger
is evaluated at the start of the athlete's local Monday and generation is
idempotent for that athlete and local week. A completed check-in may trigger the
same pending proposal without creating a duplicate.

Delivery status: assigned to Phase 8; not implemented. Exact job scheduling is
an engineering choice, but UTC-only week boundaries are not acceptable final
behavior.

### 41. Reassess taper coverage from the available training catalog

Decision: "taper templates" means reviewed workout/training definitions for
taper weeks, not an automatically activated plan. Phase 8 must first reassess
taper coverage using the available
`docs/trainings/Trainingen START23.v01.xlsx - Sheet1.csv` catalog export. No new
training is to be invented or imported before that review.

The reviewed export currently contains 160 swim, bike, and run trainings with
an explicit 80/20 bucket, expected RPE, training type, event target, and up to
30 distance/time/zone segments. It contains no explicit `taper` or `afbouw`
field. Phase 8 must therefore define and review how existing rows become
taper-eligible, validate discipline/duration/zone data and catalog coverage,
and prove a complete triathlon taper with a runtime fixture. The generated plan
still follows the normal deterministic, pending, athlete-confirmation workflow,
and public API/UI models remain TSS-free.

Delivery status: assigned to Phase 8; source catalog available, review and
implementation not started.

### 42. Standard first training week instead of a history-derived budget

Decision: the first week receives a standard Start23 training selection rather
than calculating a user-facing or internal starting budget as reported weekly
sport hours multiplied by 40. When valid CSS/thresholds and zones are already
known, they personalize the prescribed pace, power, heart rate, or other
difficulty within the selected training. Training history remains safety and
context input but does not itself set the Week-1 load through `hours * 40`.

When CSS or zones are unknown, the first week uses the safe calibration route
from decision 5. The standard training must not require an unknown zone to be
executed, and its result may only create a pending CSS/zone proposal.

Delivery status: decision accepted; not implemented completely. The current
planner bootstraps from the cheapest eligible catalog items, but it does not
select the reviewed `Trainingen START23.v01` Week-1 set or implement the
known-versus-unknown CSS/zone personalization described here.

### 43. Goal type and training-cycle anchor

Decision: onboarding lets the athlete identify whether the goal is a dated
race/event or a non-race personal goal. For every race/event goal, the event
date always anchors the training cycle and the planner works backward from that
date, including partial-cycle alignment. It must not restart a race plan at
cycle week 1 merely because no earlier plan rows exist.

A non-race goal without an event date starts normally at cycle week 1. Goal
families such as weight loss require their own reviewed deterministic planning
rules and catalog coverage in Phase 12; until then they may be selected only as
planned/coming later and cannot silently use race rules.

Delivery status: not implemented. The current application supports one
race-oriented A goal but runtime planning uses the number of prior plans rather
than the race date for cycle alignment. Non-race goal execution remains Phase
12.

### 44. Persistent non-blocking missing-feedback reminder

Decision: when a completed activity still needs athlete feedback, app open
shows a prominent but non-blocking reminder. The athlete may continue using the
app, but the reminder remains visible until the required RPE/TSE feedback is
submitted or the activity receives an explicitly defined terminal state. The
reminder must deep-link to the relevant activity and must not expose TSS.

Delivery status: assigned to Phase 8; not implemented. Pending RPE currently
appears only after navigating to the activity screen.
