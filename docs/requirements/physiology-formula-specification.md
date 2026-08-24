# Physiological Formula Specification

## Status

`Approved and implemented for local MVP development - phase-3-ruleset-3;
production review pending`

The evidence supplied on 2026-07-25 approves deterministic calculation policy
for BR-002, BR-003, BR-004, BR-006, BR-007, BR-008, and BR-010. The follow-up
evidence supplied on 2026-07-26 approves BR-009 policy. All Phase 3 rules are
remain historical in `phase-3-ruleset-2`. The decisions accepted on
2026-08-11 are implemented in `phase-3-ruleset-3` and linked from the
[Phase 0-7 decision register](phase-0-7-decision-register.md).

`phase-3-ruleset-1` remains immutable for historical decisions and excludes
BR-009.

Evidence:

- [BR-002 and BR-003](../BR-002%20&%20BR-003.pdf)
- [BR-004, BR-006, and BR-007](../BR-004%20,%20BR-006%20&%20BR-007.pdf)
- [BR-008, BR-009, and BR-010](../BR-008%20,%20BR-009%20&%20BR-010.pdf)
- [BR-009 follow-up](../BR-009%20FB.pdf)

The Phase 0 precedence, pending-proposal requirement, and TSS confidentiality
remain authoritative. This specification approves calculations only. It does
not authorize a calculation to mutate an active plan or zone version.

## Shared calculation conventions

- Use `Decimal` for internal load, duration ratios, factors, and thresholds.
- Preserve exact values internally; do not apply unapproved rounding or clamps.
- Reject non-finite, negative, structurally invalid, or missing required input.
- Treat threshold equality exactly as specified for each rule.
- Include explicit zero samples where the rule says zero is meaningful.
- Exclude missing samples rather than synthesizing zero.
- Record the active ruleset version with every decision result. New Phase 3
  calculations default to `phase-3-ruleset-3`.
- Keep load values server-internal and return only qualitative information at
  later API boundaries.
- All generated critical changes remain pending until owner approval.

## BR-002: volume and intensity debt

Approved calculation:

- Activate weekly volume debt only when realized load is strictly greater than
  `planned * 1.10`; exact 110% does not activate debt.
- Calculate debt as `realized - planned`.
- Calculate the regular next-week projection from prior planned load:
  `planned * 1.10`.
- Calculate the corrected target as
  `regular projection - debt`.
- Apply the debt to the immediately following week. Preferred placement in the
  first half of that week belongs to Phase 6 scheduling.
- A non-exceptional target that would reach zero or below stops regular plan
  generation and produces only a typed pending recovery/manual-review
  proposal. Repetition requires qualified human escalation.
- Injury, illness, or an equivalent confirmed exception may produce zero.
- Calculate high-intensity debt as the positive difference between realized
  and planned high-intensity time fraction.
- The normal corrected high-intensity floor is 5%.
- Zero high intensity is allowed only for the confirmed injured discipline.
- The maximum-three-consecutive-rest-days requirement belongs to scheduling,
  not this isolated calculation.

Approved fixtures include exact 110%, immediately above 110%, the
`600 planned / 680 realized` example, and a negative-target fail-safe.

## BR-003: time-based intensity distribution

Approved calculation:

- The imported workout's explicit `Emmer (80/20)` is authoritative: `80%`
  means the complete workout duration belongs to the quieter weekly bucket and
  `20%` means the complete workout duration belongs to the intensive weekly
  bucket.
- Zone 1, Zone 2, and swim technique are lower-intensity interval content;
  Zone 3, Zone 4, and Zone 5 are higher-intensity interval content. These
  interval classifications drive execution detail and private per-interval
  TSS, not reassignment of the declared workout bucket.
- The standard race-oriented target is 80% low and 20% high.
- Assign the full workout duration to its declared catalog bucket. Do not derive
  or validate that declaration by dominant interval duration. The former
  dominant-category and exact-tie rules are superseded for catalog workouts.
- Calculate weekly distribution from duration, never TSS.
- An empty week is `not_evaluated`; it does not return a `0/0` ratio.
- Warn only when realized intensive duration is strictly greater than 130% of
  planned intensive duration. Exact 130% does not warn.
- Ratio-deviation warnings do not apply.
- Non-race 90/10 and swimrun 75/25 are deferred.
- Exact duration and ratios remain `Decimal`. Athlete-facing display rounds
  low percentage half-up to a whole number, derives high as `100 - low`, and
  also shows exact low/high minutes.
- Realized intensity debt is evaluated only with at least 60% classified
  activity duration. Unknown time is excluded from the realized ratio. The
  correction applies once to the first next non-recovery week; taper and
  recovery take precedence and there is no multi-week carry-over in the MVP.

## BR-004: progressive load and planned-load snapshots

Approved calculation:

- Use prior planned load, not realized overshoot, as the growth anchor.
- At realized load greater than or equal to 80% of planned, use
  `planned * 1.10`. Exact 80% is regular.
- Below 80%, use the available 42-day baseline.
- The 42-day baseline is the arithmetic mean of explicit Monday-starting
  weekly load snapshots whose starts fall in the inclusive latest 42 calendar
  days (normally six athlete weeks).
- Include explicit zero-load weeks and exclude missing weeks.
- With less history, use all available weekly samples.
- Without an available baseline, fail closed.
- Apply no additional rounding or min/max clamp.
- Snapshot a shortened or personalized planned load as
  `expected RPE * duration in hours`, with RPE constrained to 1 through 10.

Week-1 initialization is an orchestration decision, not the progressive-load
formula above. A reviewed standard Start23 training selection is used. Known
CSS/thresholds and zones personalize execution difficulty. Unknown values use
safe calibration training. Reported sport hours remain context but are not
multiplied by 40 to create the Week-1 target.

## BR-006: anti-stack intervals

Approved calculation:

- Require 72 elapsed hours between starts of high-intensity run workouts.
- Require 48 elapsed hours between starts of high-intensity bike workouts.
- Require 48 elapsed hours between starts of high-intensity swim workouts.
- Exact equality is allowed; any shorter interval is a violation.
- Compare only workouts sharing the same discipline.
- A brick participates in every discipline it contains.
- Generated deck filtering and generated scheduling use the same rule.
- Low-intensity workouts do not participate.

Technical time interpretation:

- Compare timezone-aware starts as absolute UTC instants, while later APIs
  display athlete-local times. This makes 48/72 mean actual elapsed hours and
  prevents daylight-saving transitions from silently adding or removing an
  hour.
- Manual athlete moves remain allowed with a qualitative warning in Phase 6.

## BR-007: build and recovery cycle

Approved calculation:

- In a forward cycle, weeks 1-4 are build and each fifth week is recovery.
- A dated race always anchors the cycle retrospectively, including a partial
  horizon. The supplied eight-week fixture yields recovery weeks 3 and 8.
- A non-race goal without an event date starts at forward-cycle week 1 and must
  use its own reviewed Phase 12 goal rules.
- Taper overrides recovery.
- Use week 4 planned load as the recovery anchor.
- Default target is exactly 60% of that load.
- Higher-precedence constraints may reduce the factor, but it must remain in
  the inclusive 40%-60% range.
- Apply no additional rounding.
- Maximum three consecutive rest days belongs to Phase 6 scheduling.

A missing week-4 value is rejected by requiring an explicit `InternalLoad`
input. Handling a valid explicit zero alongside non-zero-week policy belongs
to orchestration, where injury/illness context is available.

## BR-008: race taper

Approved calculation:

- Use the available weekly-snapshot 42-day baseline, excluding recovery weeks.
- Include explicit zero-load build weeks and exclude missing weeks.
- A-race T-2 target is 60% of that baseline.
- A-race T-1 target is 35% of that baseline.
- A B-race now uses a full taper week at 50% of the baseline; this replaces the
  earlier four-day/15% wording.
- A C-race has no taper.
- Athlete weeks run Monday-Sunday in the athlete's IANA timezone.
- Overlap is resolved by goal priority `A > B > C`; same-priority ties use the
  earliest event and then stable identifier.
- Apply no additional rounding or clamps.
- Taper overrides recovery.

Race load contributes to build-history calculations but not to the taper-week
target. Its persistence and hidden-load accounting belong to Phase 6 and must
continue to obey BR-005.

## BR-009: discipline-zone validation

Approved canonical storage units:

- swim CSS: seconds per 100 metres;
- bike FTP: watts;
- bike threshold heart rate: beats per minute;
- run threshold pace: seconds per kilometre;
- run LTHR: beats per minute.

Approved input and review policy:

- run pace input uses `minutes:seconds/km`;
- swim CSS input uses `minutes:seconds/100 m`;
- cycling speed is activity telemetry only, not a zone input;
- pace values are stored as exact whole seconds in the canonical unit;
- FTP watts and heart-rate BPM remain positive canonical numeric values;
- clinical limits are soft: values outside a configured range are accepted but
  require confirmation or review;
- if no soft range is configured, the metric is accepted but review is
  required rather than inventing a threshold;
- manual profiles may contain athlete-supplied Zone 1-5 boundaries;
- when thresholds/zones are unknown, standard calibration training plus
  eligible realized measurements and athlete-entered TSE feeling feedback may
  create only a pending calculated threshold/zone proposal;
- the TSE scale, its relationship to the existing RPE field, and the
  deterministic mapping to CSS/FTP/LTHR/pace and Zone 1-5 must be explicitly
  specified and reviewed before use;
- `Start23_Fysiologische_TSS_Logica.pdf` defines zone IF and private TSS/sTSS
  calculations but does not contain that TSE conversion, so the backend must
  not infer or invent it;
- a shared boundary belongs to the physiologically more intense zone,
  independent of numeric direction;
- all five zones must be present, ordered, contiguous, and non-overlapping;
- pace metrics are explicitly descending because faster pace has fewer
  seconds; watts and heart-rate metrics are ascending.

Approved fallback:

- estimate maximum heart rate with Tanaka:
  `HRmax = 208 - (0.7 * age)`;
- require positive age and resting heart rate, with estimated maximum heart
  rate greater than resting heart rate;
- calculate target heart rate with Karvonen:
  `THR = resting HR + ((HRmax - resting HR) * intensity fraction)`;
- use HRR bands 50%-60%, 60%-70%, 70%-80%, 80%-90%, and 90%-100% for Zones
  1-5;
- preserve exact `Decimal` results without rounding;
- mark every fallback result explicitly `estimated` and `unreviewed`;
- require confirmation before later persistence or activation.

Implementation notes:

- BR-009 is active in rulesets 2 and 3; new evaluations use ruleset 3.
- Pure calculations do not create or activate a database zone version.
- System-calculated replacements remain subject to BR-001 pending-proposal
  semantics in the application layer.
- Numeric soft-range thresholds are versioned, attributable product
  configuration, not hard rejection limits. Each record requires metric,
  discipline, unit, applicability, evidence, reviewer, validity dates, and
  ruleset version. No values are inferred in code.

## BR-010: functional injury restrictions

Approved calculation:

- Only explicit confirmed injury context has an effect.
- Remove load for each blocked discipline from the proposed current/next-week
  scope.
- Redistribute zero removed load automatically in the MVP. The historical 80%
  calculation is analytical only and cannot drive plan generation.
- Let the weekly budget fall. Existing low-intensity workouts in another
  discipline may be selected explicitly, subject to normal progression.
- With all disciplines blocked, produce rest and no redistribution.
- If multiple remaining disciplines all have zero existing share, require
  review rather than inventing an allocation.
- Explicit athlete clearance is sufficient to change confirmed injury
  context.
- All resulting plan changes remain pending.

Use functional restrictions rather than diagnosis/severity. The locked states,
allowed intensity, seven-day review, explicit clearance, source, and time
semantics are defined in the decision register. Phase 8 owns persistence and
UI; a due review never silently clears a restriction.

## Approval record

- Evidence supplied: 2026-07-25
- Evidence owner: repository user
- Follow-up evidence supplied: 2026-07-26
- Stable rulesets:
  - `phase-3-ruleset-1`: BR-002, BR-003, BR-004, BR-006, BR-007, BR-008,
    BR-010;
  - `phase-3-ruleset-2`: ruleset 1 plus BR-009.
- `phase-3-ruleset-3`: ruleset 2 plus the twelve decisions accepted on
  2026-08-11.
- Production governance: qualified physiological review of the active ruleset
  and `start23-zone-model-1.0` was confirmed complete by the product owner on
  2026-08-24. Reviewer identity and the evidence dossier are retained in the
  external product-governance record; changed rules require a new review.
- Deferred scenarios: non-race 90/10, swimrun 75/25, calculated zone
  replacement persistence
- Implementation: deterministic Python modules with ruleset, boundary,
  invalid-input, precedence, purity, timezone, and DST tests
