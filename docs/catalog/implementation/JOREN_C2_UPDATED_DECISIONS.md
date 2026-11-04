# C2 decision evidence and outstanding approval dependencies

## C2.1 approval

Current intake: 2026-11-04, Europe/Amsterdam. Authority: Joren's explicit
approvals relayed by the owner in **WOMBO C2.1 — FINAL JOREN 80/20 APPROVAL AND
SWIMMING CORRECTION FOLLOW-UP**. Original approval dates and independent scientific
review identifiers were not supplied. This entry supersedes the historical C2
open questions below within its exact scope.

| Decision | Confirmed scope | Implementation boundary |
| --- | --- | --- |
| C2.1-INTENSITY-1 | Maximum 20% high-intensity **planned active training time**, independently for RUN, BIKE and SWIM in each athlete-local Monday–Sunday week | Version `joren-planned-active-time-maximum-1`; pure isolated evaluator only; active planner unchanged |
| C2.1-SWIM-1 | TR-SWIM-015 through TR-SWIM-020: the ordered 300m Z3 block must be 300m Z2 | Six exact N19–N24 overlays in `joren-swim-if2-approved-prescription-overlay-1`; originals retained |
| C2.1-BEGINNER-1 | Joren will supply additional lighter sessions for easier weeks | Await actual sources and tests; beginner 45 versus 64.5 remains **OPEN** |

The intensity maximum is inclusive: 0% and exactly 20% pass; any proportion above
20% fails when coverage is complete. There is no required high-intensity minimum
in beginner, recovery, taper or other weeks. Aggregate planned **segment**
seconds, including low-intensity recovery blocks inside hard-focus sessions.
Stationary swim rest contributes no active time. Do not use TSS, workout counts,
session-focus RPE, distance or CSS as a substitute. No reference-pace minutes are
athlete prescription minutes. The approved BR-003 segment taxonomy is Z1/Z2 low,
Z3/Z4/Z5 high (`phase-3-ruleset-3`, `classify_segment`); Z3 classification is
resolved even though the separate IF² **Z3 coefficient** remains missing.

Complete zero-active-time sport/weeks, including absent sports, are **NOT
APPLICABLE** with no ratio. Any missing reliable planned active segment time or
classification makes that sport/week **UNVERIFIED**, with no compliance ratio;
known subtotals cannot establish satisfaction. All 20 distance-only swimming
prescriptions still lack active time, including the corrected six. The evaluator
does not approve a plan and cannot replace injury, load, recovery, taper, spacing,
pending-confirmation or stale/version safeguards. It is not imported by selection.

The separate proposed triathlon allocation remains BIKE 50%, RUN 30%, SWIM 20%
of weekly planned TSS. Target versus hard constraint, denominator details and
infeasible-allocation handling remain open. No automatic increase in load is
authorized to force those percentages. It is not an intensity rule.

Swimming status has three distinct meanings:

- **Original:** the pinned IF² workbook remains contradictory for the six rows;
  original hash `7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`
  (7405 bytes) and all source cells/XML are retained.
- **Derived candidate:** structurally **CONSISTENT**, all 20 row totals and zone
  aggregates agree after precisely six authorized replacements. The six IF²
  computations reconcile with their displayed values using confirmed populated
  anchors and explicit historical reference seconds. No structural blocker remains
  for them; preserved contradictory originals do not invalidate the derivative.
- **Operational:** **INACTIVE**. Approval of these prescriptions does not approve
  exact reference paces, missing Z3 IF for 010/011/014, normalization, intermediate
  rounding, numeric precision/storage, authoritative operational P, V2 compatibility,
  identity/replacement mapping or catalog release.

The corrected manifest retains original/derived ordered events and per-block
guidance separately. Its digest and reconciliation are recorded in the source
correction request and calculation report. Existing C1/C2 JSON artifacts and draft
registry remain historical and byte-identical; their six-conflict markers describe
the original source revision, not this corrected successor. No active entries exist
for either. No C3–C8 work or activation is authorized here.

The beginner decision is specifically **await lighter supplied sources**, not a
baseline, duration, progression or 20% exception. No workouts or placeholders are
invented. The intake preparation and required checks for real new revisions are
in [the C1 manifest addendum](JOREN_C1_SOURCE_MANIFEST.md#c21-next-source-intake).

## Historical C2 intake — retained evidence

Intake date: 2026-11-04, Europe/Amsterdam. Developer-only evidence; activation disabled.
Authority: owner's task “WOMBO — C1.1 / C2: JOREN APPROVAL INTAKE, SWIM IF²
REVISION AND PLANNING POLICY VALIDATION”, supplied in this conversation. These
are owner-relayed Joren statements, not independently obtained email or a signed
scientific review. Joren's original decision date/review identifier is unspecified.
No missing attribution or acceptance is fabricated.

The root AGENTS.md and current MVP roadmap, including the Realized V2 amendment,
apply. No nearer backend/docs instruction exists. The complete C1 report, A–F
brief, final reconciliation, planning simulation and C1–C8 sequence were read.
Their old “A–F all open” statements remain historical; this intake refines the
current decision state without rewriting those reports or the immutable C1 JSON.

| Evidence ID | Actual statement supplied by owner | Accepted scope | Still required |
| --- | --- | --- | --- |
| C2-A-1 | “Joren confirms the same IF coefficient values are intended.” “Running and cycling use an IF-squared source method.” | IF² direction and previously identified populated Z1=.55/Z2=.75/Z4=.98/Z5=1.15; no global coefficient change | Missing Z3, precise source arithmetic/rounding/storage authority and approved method/version compatibility |
| C2-A-2 | “Joren states that he forgot to square IF in swimming and has supplied a corrected swimming workbook” | Separate prospective IF² source; byte identity verified | Exact reference paces, normalization, intermediate rounding, Z3 anchor and six contradictory rows |
| C2-C-1 | “BIKE 50% RUN 30% SWIM 20%” and “the existing 80/20 low/high intensity principle PER SPORT” | Proposed selection intent, based on weekly planned TSS for sport distribution | Final denominator, hard versus flexible enforcement, tolerance/rounding, infeasibility, phase and goal scope, multi-week behavior and exact intensity measure |
| C2-D-1 | “Expected RPE is based on its MOST INTENSE workout block.” | Preserve source session-focus independently of per-zone execution; no false hard RPE on recovery blocks | Prospective template/public snapshot integration and compatibility belong to later approved slices |
| C2-E-1 | “Joren agrees with distance-based planned load, stationary-rest zero-load semantics and not fabricating duration-based realized load.” | Distance source basis, rest=0 with no zone/RPE; no CSS-derived planned or actual duration | Revised IF² exact method evidence; time/intensity coverage and observed-rest completeness policy; V2 compatibility |
| C2-BEGINNER-1 | “One easiest suitable BIKE workout. One easiest suitable RUN workout. One easiest suitable SWIM workout.” “Three training occurrences in total, one per sport.” | Explicit desired first-week composition | 64.5 displayed source load conflicts with existing zero-history45; no ceiling/progression exception authorized |

The new workbook independently states in A2: “Z1 t/m Z5 zijn in METERS. TSS
berekend door meters om te zetten naar minuten * IF^2 * 0.90.” It has no formula
cells, IF table or reference-pace sheet. Its exact verified hash is
`7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`
(7405 bytes). The original swim workbook hash
`bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674`
and PDF hash `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a`
remain historical source/method evidence. Supersession is prospective only,
conditional on reproducible accepted provenance; it does not activate a method.

The new method is `joren-swim-if2-experimental-1`, separate from
`joren-swim-fixed-pdf-historical-1`. Timed source support is
`joren-timed-if2-experimental-1`. All three are review dispatch identifiers,
with **no operational approval**. Existing zone-minute coefficients and historical
method/RPE dispatch remain unchanged. Decimal precision50/HALF_EVEN and rational
evidence are explicit engineering verification choices, not invented Joren
rounding decisions. Reconstructed Z3=.88 and rounded reference minutes are confined
to labeled diagnostic inputs; strict confirmed-anchor verification never fills Z3.

TR-SWIM-015 through020 are **SOURCE-CONFLICTED**: I/J says600/0 while ordered N
prescribes300 Z3 and300 Z2. Exact values survive in the new private artifact and
original archive. Strict verification rejects these rows even when diagnostic
candidate parameters reproduce the displayed aggregate load. No representation
is selected as authoritative. The Dutch correction request is prepared, not sent.

Per-block guidance uses existing `joren-realized-tss-matrix-2` ranges
Z1 1–2, Z2 3–4, Z3 5–6, Z4 7–8, Z5 9–10, as versioned private guidance attached
to each ordered block. Rest has no zone or RPE. The exact original source focus
field is retained separately. No current template validator, historical RPE3
meaning, catalog projection or athlete contract is changed to integrate these rows.

Decision B remains open: catalog release, replacement/identity approval and
predecessor mapping. The new draft registry preserves all C1 IDs/version1 and
proposes distinct swim successor IDs/version2 under the same provisional keys;
it records no approved predecessor or active release. C4 athlete/long-session
scope, C5 coverage, C6 method compatibility, C7 broader performance verification
and C8 database/release gates remain separate. Decision F activation is absent.

Concrete owner/Joren choices now required:

1. Correct each of the six source conflicts; provide a new hashed revision.
2. Supply complete revised IF² method evidence, Z3 anchor, paces, normalization,
   precision and authoritative operational P (exact versus stored/displayed).
3. Set 50/30/20 and per-sport80/20 denominators, enforcement/tolerance, sparse-week,
   phase, missing-sport/injury and single-sport policies. Safety constraints retain
   precedence; there is no automatic redistribution or higher beginner ceiling.
4. Resolve beginner45 versus64.5 through a separately reviewed exception or genuinely
   easier supplied workouts; phased introduction requires explicit product change.
5. Approve catalog scope, provenance/V2 compatibility and eventual release separately.

No C3–C8 progression, athlete state change, production/staging operation, push,
merge or deployment is authorized or performed by this implementation.
