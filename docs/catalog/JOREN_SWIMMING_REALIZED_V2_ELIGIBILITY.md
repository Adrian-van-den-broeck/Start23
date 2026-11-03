# Joren swimming Realized TSS V2 eligibility

Review date: 2026-11-03 (Europe/Amsterdam). Review and preparation only.
Accepted engine: `feat/joren-realized-tss-v2` at `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch/worktree: `review/joren-new-workout-catalog`,
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Swimming originals are in the accepted engine worktree's `docs/trainings`, not the older root checkout:

| Original | Bytes | SHA-256 |
| --- | --- | --- |
| `Zwemtrainingen_Definitief_Optie1.xlsx` | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` |
| `Specificatie Zwem TSS.pdf` | 149021 | `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a` |

Full original paths:
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Zwemtrainingen_Definitief_Optie1.xlsx`
and `F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Specificatie Zwem TSS.pdf`.
Private load numbers below are developer review evidence and must remain outside athlete-facing contracts.

## Classification: zero fully eligible swimming fallback occurrences

Nine rows have a single explicit swimming zone, all Z2. Eleven are mixed.
**All 20 are currently ineligible for duration-based RPE fallback.** The nine
single-zone distance prescriptions lack authoritative planned duration T. The
mixed eleven additionally violate the single-zone predicate and include rests
without an explicit swimming zone. No new approved occurrence, template version,
source-method version or confirmed actual completion was supplied or created.

Expected source distance and a published reference pace cannot be substituted
for T or actual performed A. A reported RPE does not establish distance, speed,
actual intensity or measured zone time. Source TSS is not a performed-load value.

| ID / row | Swimming structure | Rest events | Duration-based RPE classification | Current measured route |
| --- | --- | --- | --- | --- |
| TR-SWIM-001 / 5 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-002 / 6 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-003 / 7 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-004 / 8 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-005 / 9 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-006 / 10 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-007 / 11 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-008 / 12 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-009 / 13 | single Z2 | 0 | Ineligible: no authoritative T, method/version or occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-010 / 14 | mixed Z2/Z3 | 5 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-011 / 15 | mixed Z2/Z3 | 10 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-012 / 16 | mixed Z2/Z4 | 5 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-013 / 17 | mixed Z2/Z4 | 4 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-014 / 18 | mixed Z2/Z3 | 8 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-015 / 19 | mixed Z2/Z3/Z5 | 10 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-016 / 20 | mixed Z2/Z3/Z5 | 15 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-017 / 21 | mixed Z2/Z3/Z5 | 20 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-018 / 22 | mixed Z2/Z3/Z5 | 10 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-019 / 23 | mixed Z2/Z3/Z5 | 15 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |
| TR-SWIM-020 / 24 | mixed Z2/Z3/Z5 | 20 | Ineligible: mixed/rest structure; also no T/method/occurrence | Conditional on independent reliable actual zone minutes and total duration |

## Current approved contract and code verification

The [approved V2 specification](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md)
requires `E=P*A*F/T` on the exact original approved occurrence. Method/version
dispatch accepts `planned_zone_minutes` / `phase-13-joren-ruleset-1`, with original
P/T, ordered zones, plan/revision/occurrence and immutable template/source identity.
Unknown method/version pairs remain unsupported. New source IDs and a file hash
cannot establish an athlete-approved occurrence. The existing persistence label
for retained timed source loads does not grant distance-only swims a duration.

`workouts/catalog.py::with_current_load` explicitly sets planned load None for
distance-only sourced swims. `planning/domain.py::eligible_workouts` excludes
missing P. The source import retains distance and original predefined P privately,
but the current active projection does not make that P available for target fit.
No published fixed-distance load calculation is integrated into this engine SHA.

`activities/realized_context.py::single_planned_zone` checks every explicit approved
segment; no Expected Zone, source aggregate, focus label, dominant interval or
RPE-only projection can supply it. Stationary rest has no Z1 target. Current
segment contracts cannot natively encode an unzoned stationary rest; even after
future rest representation, mixed swimming zones remain excluded.

A read-only all-20 negative exercise supplied deliberately favorable **synthetic**
source P and supported method/version, confirmed actual A=30 min, but kept planned
T missing. Results:

| Fixture rows | Selected estimate | Planner eligible | Actual code reason |
| --- | --- | --- | --- |
| TR-SWIM-001–009 | None | false | `missing_duration` |
| TR-SWIM-010–020 | None | false | `unsupported_structure` |

The synthetic method label does not approve a distance-load method. These probes
isolate missing T and mixed structure despite favorable other assumptions. In the
actual unimported state the basis itself is absent (`missing_approved_occurrence`)
and the current projected P is unavailable. No planned time was fabricated.

Even if actual performed minutes are independently recorded, the single-zone
source still lacks planned T. A future independently prescribed, authoritative
time-based occurrence could be assessed under the existing V2 contract only if
it genuinely supplies compatible P/T/zone/method/version. Adding those minutes
would be a separately accepted prescription, not a conversion silently inferred
from this distance workbook. The present swimming source establishes no such
occurrence. A≠T calculations remain automatically withheld under
`duration_reliability_policy_missing`; unsupported method/version also withholds
selection. Defaults/readiness remain disabled; no configuration was changed.

## Supported observation precedence and rest

Existing actual observed-zone-minute loads retain their approved precedence for
both single and mixed swimming prescriptions when independent reliable evidence
exists. Swimming has no approved mean-HR route. There is no validated swim-pace,
athlete-CSS, distance or provider-TSS converter in the accepted realization path.

Observed/partial evidence must not be replaced, scaled or completed using an RPE
matrix. Complete observed 30 min Z2 gives 21.60 under current coefficients,
regardless of the source catalog's 1,000 m or its fixed reference P. This is an
independent synthetic actual-duration/zone fixture; no pace is inferred from RPE
or expected distance. If elapsed total instead includes five more minutes of
wall rest, current code records 30/35 coverage and `partial_observed`, not a
complete measured session. Original known observations are retained; omitted time
is not extrapolated, assigned Z1 or silently marked fully observed.

The PDF's zero-rest rule is explicit for its distance model. What remains absent
is an approved observation contract for rest identification, active versus elapsed
minutes and completeness. Until supplied, no special rest exemption from the
current weekly coverage policy exists. Explicit all-zero zone bins do not enable
a new fallback loophole. Stationary rest and active low-zone recovery are distinct.

## Future methodological choices, not implemented

The engine has no approved distance-ratio RPE fallback. A separately reviewed
alternative might relate actual to planned distance rather than A/T, but no formula,
actual-distance confirmation contract, eligibility/reliability policy, bounds,
measurement hierarchy or scientific validation is supplied here. Do not copy the
duration formula and substitute meters as if its approval transferred. Mixed
intervals would still require an independently reviewed method rather than a
whole-session correction. S04 in the unified register asks only whether such a
future specification is wanted; keeping it unavailable is a valid scope decision.

No fallback is needed to preserve/import source evidence as evidence. Making
fixed-distance P selectable in planning is a different prospective decision (S02)
from making a distance-based performed-load estimate eligible. Neither decision
can be hidden in a coefficient or source-version relabel.

## Registration completeness and continuation

The unchanged `weekly-registration-2` policy uses exact expected occurrence IDs.
Missing swimming completion is unknown; completed distance-only/unavailable load
is not zero; explicit skip is distinct. A source TSS value cannot be copied into
a completed registration just because that row was planned. Known subtotal remains
separate from nullable planner-usable total.

Four synthetic code fixtures use one supported RUN estimate of 32.3 and an
expected swimming occurrence. A prior plan has private P=60, week 2026-10-19,
phase build. Resolve next target for 2026-10-26, race 2026-12-27:

| Swimming evidence | Known subtotal | Usable weekly load | Next target / basis | Reason |
| --- | --- | --- | --- | --- |
| unknown | 32.3 | None | 60 / prior_planned_hold | unknown_workout_completion |
| unavailable | 32.3 | None | 60 / prior_planned_hold | partial_or_unavailable_load |
| skipped | 32.3 | 32.3 | 32.3 / realized_baseline | complete |
| independent_measured | 53.9 | 53.9 | 66.00 / realized_progression | complete |

The independent measured case supplies a separate complete actual 30-minute Z2
observation (21.6), not the partial 35-minute wall-rest fixture. No new catalog
plan was generated or approved for these fixtures. Complete evidence can feed
unchanged progression; unknown/unavailable evidence holds. A skip resolves status
but never adds load, while low completion uses the existing realized baseline.
RPE fallback contributes no observed intensity minutes. Pending proposals retain
stale evidence guards, owner isolation, athlete approval and correction provenance.

No genuine new-swim multi-week plan can be continued through the current projection
because the first required P is unavailable. The current-catalog and running-only
continuation evidence is in the [readiness report](JOREN_THREE_SPORT_CATALOG_IMPORT_READINESS.md).
Focused v2/catalog/privacy/A9 tests passed (395); PostgreSQL/pgTAP is
**DEFERRED BY OWNER — PRE-BETA**, not verified by these Python fixtures.
