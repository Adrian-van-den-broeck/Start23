# Physiological Formula Specification

## Status

`Partially approved and implemented - phase-3-ruleset-1`

The requirements evidence supplied on 2026-07-25 approves deterministic
calculation policy for BR-002, BR-003, BR-004, BR-006, BR-007, BR-008, and
BR-010. Those rules are allow-listed by the stable
`phase-3-ruleset-1` specification.

BR-009 is not allow-listed. Canonical zone units and structural value objects
exist, but clinical validation fails closed until numeric ranges and the
remaining zone policy are approved.

Evidence:

- [BR-002 and BR-003](../BR-002%20&%20BR-003.pdf)
- [BR-004, BR-006, and BR-007](../BR-004%20,%20BR-006%20&%20BR-007.pdf)
- [BR-008, BR-009, and BR-010](../BR-008%20,%20BR-009%20&%20BR-010.pdf)

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
- Record `phase-3-ruleset-1` with every decision result.
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
- A non-exceptional target that would reach zero or below requires review and
  does not produce a target.
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

- Zone 1, Zone 2, and swim technique are low intensity.
- Zone 3, Zone 4, and Zone 5 are high intensity.
- The standard race-oriented target is 80% low and 20% high.
- Assign the full workout duration to its dominant low/high category.
- Calculate weekly distribution from duration, never TSS.
- An empty week is `not_evaluated`; it does not return a `0/0` ratio.
- Warn only when realized intensive duration is strictly greater than 130% of
  planned intensive duration. Exact 130% does not warn.
- Ratio-deviation warnings do not apply.
- Non-race 90/10 and swimrun 75/25 are deferred.
- Exact duration and ratios remain `Decimal`; display rounding is deferred to
  an athlete-facing contract.

Unresolved edge: the evidence does not say which category owns an exact
low/high duration tie in a mixed workout. The implementation raises an
explicit fail-closed error for this case.

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
- For a partial horizon ending at an A-race, align retrospectively. The
  supplied eight-week fixture yields recovery weeks 3 and 8.
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

Approved canonical units only:

- swim CSS: seconds per 100 metres;
- bike FTP: watts;
- bike threshold heart rate: beats per minute;
- run threshold pace: seconds per kilometre;
- run LTHR: beats per minute.

Implemented structural safeguards:

- a metric must belong to its discipline;
- values must be finite and positive;
- clinical ranges, when approved, are represented explicitly;
- a complete profile contains ordered Zones 1 through 5;
- overlaps are rejected;
- missing clinical limits fail closed;
- the production Phase 3 ruleset cannot activate BR-009.

### Precise approval request

For each of the five metrics above, provide:

1. the minimum and maximum valid value in the canonical unit, and whether each
   endpoint is inclusive;
2. the exact formula or direct-entry format for Zones 1-5;
3. which zone owns an exact shared boundary, for example whether intervals are
   `[lower, upper)` with only the final upper bound inclusive;
4. accepted UI input formats and conversions, such as `mm:ss/100 m` or
   `mm:ss/km`, plus stored decimal precision;
5. any fallback formula, all required inputs, and whether that fallback is in
   MVP scope.

Also confirm that every calculated replacement remains pending. No clinical
range or fallback formula will be inferred by engineering.

## BR-010: confirmed-injury redistribution

Approved calculation:

- Only explicit confirmed injury context has an effect.
- Remove load for each blocked discipline from the proposed current/next-week
  scope.
- Redistribute exactly 80% of removed load.
- Allocate it proportionally to existing planned-load shares of the remaining
  disciplines.
- With two blocked disciplines, the one remaining discipline receives all of
  the redistributable amount.
- With all disciplines blocked, produce rest and no redistribution.
- If multiple remaining disciplines all have zero existing share, require
  review rather than inventing an allocation.
- Explicit athlete clearance is sufficient to change confirmed injury
  context.
- All resulting plan changes remain pending.

The calculation accepts already-confirmed blocked disciplines. Injury
severity, source, expiry, volume-only reduction, intensity-only disabling, and
context lifecycle are application-layer inputs for Phase 8 and cannot be
inferred by this calculation.

## Approval record

- Evidence supplied: 2026-07-25
- Evidence owner: repository user; formal clinical-review role not supplied
- Stable ruleset: `phase-3-ruleset-1`
- Approved: BR-002, BR-003, BR-004, BR-006, BR-007, BR-008, BR-010
- Partially specified and excluded from ruleset: BR-009
- Deferred scenarios: non-race 90/10, swimrun 75/25, BR-009 fallback zones,
  BR-009 calculated replacements, and athlete-facing percentage formatting
- Implementation: deterministic Python modules with ruleset, boundary,
  invalid-input, precedence, purity, timezone, and DST tests
