# Joren cycling Realized TSS V2 eligibility

Review date: 2026-11-03, Europe/Amsterdam. REVIEW ONLY; no activation.
Accepted engine: `feat/joren-realized-tss-v2`, exact SHA `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch `review/joren-new-workout-catalog`; worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
All private load numbers are developer review evidence, never athlete-facing data.

| Source | Original file | Bytes | SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_Optie1.xlsx | 7198 | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 |
| BIKE | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df |
| SWIM | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674 |
| SWIM spec | Specificatie Zwem TSS.pdf | 149021 | ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a |

RUN original is in `F:\Projecten Business\Start23\Code\docs\trainings`.
BIKE, SWIM and the swim PDF originals are in
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.
All four originals remain byte-identical and at those exact locations. Delivery
is verified; catalog versions and methodological acceptance are separate decisions.

## Counts and true eligibility

Cycling has **13 structural single-zone candidates and eight mixed exclusions**.
All 21 have a reliable explicit source planned duration. This does not establish
an approved occurrence, accepted new planned method/version, actual duration or
valid reported Session-RPE. **Zero fully established new cycling occurrences**
exist in this review; none was created, imported or approved.

| ID | Source structure | Planned T minutes | Structural fallback status | Current full eligibility |
| --- | --- | --- | --- | --- |
| TR-BIKE-001 | Z1 | 60 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-002 | Z1 | 90 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-003 | Z1 | 120 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-004 | Z2 | 90 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-005 | Z2 | 120 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-006 | Z2 | 150 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-007 | Z2 | 180 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-008 | Z2 | 210 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-009 | Z2 | 240 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-010 | Z2 | 300 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-011 | Z2 | 330 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-012 | Z2 | 360 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-013 | Z2 | 420 | candidate | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-014 | Z2/Z4 | 180 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-015 | Z2/Z4 | 120 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-016 | Z2/Z4 | 180 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-017 | Z2/Z4 | 220 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-018 | Z2/Z5 | 150 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-019 | Z2/Z5 | 100 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-020 | Z1/Z2/Z5 | 93 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |
| TR-BIKE-021 | Z1/Z2/Z5 | 104 | excluded: mixed zones | No: method/version and exact occurrence/actual evidence not established |

## Required gates A–H

| Gate | Exact approved requirement | Cycling intake status |
| --- | --- | --- |
| A: structure | Every approved ordered segment has the same explicit zone; no inference from focus/dominance/RPE | 001–013 pass source structure;014–021 fail |
| B: occurrence | Exact athlete-owned plan/revision/occurrence/template/source snapshot | Not supplied; source row is not an occurrence |
| C: method/version | Supported authoritative original planned P method/version; unsupported combinations fail closed | New IF provenance not accepted; retained-source origin must remain honest |
| D: planned duration | Original authoritative positive T, separate from distance | All 21 source totals validated; not yet an approved snapshot |
| E: actual duration | Positive actual A explicitly confirmed, never planned prefill treated as performed | No activity evidence supplied |
| F: Session-RPE | Current transport JSON integer1–10 under v2 mapping | Expected source RPE pair is not an actual report |
| G: hierarchy | No higher-priority selected observed/approved estimated result; explicit bins retain semantics | Conditional on real activity; no RPE addition/multiplication |
| H: reliability / weekly use | A=T for automatic v2 use under current duration policy; exact weekly registrations complete | Actual evidence absent; A≠T estimate retained but withheld; unknown/partial holds |

The unchanged formula is `E=P*A*F/T`; F is the approved additive/clamped zone
factor, not an IF-derived physiological recalculation. Numeric policy remains
`decimal-50-half-even-divide-last-1`. No segment's performed execution can be
inferred from a whole-session RPE. A Z5 focus does not erase recovery Z2/Z1.

## Executed eligibility probes and cross-sport comparison

All 61 sources were assessed with actual `single_planned_zone`/`select_rpe_estimate`
code. Deliberately favorable synthetic contexts use sourceP, supported Phase13
`planned_zone_minutes` pair, exact IDs, confirmed A=T and lower source RPE endpoint:
RUN 16 and BIKE 13 produce conditional estimates; SWIM 9 single rows fail missing T;
all 23 mixed sessions fail structure. These fixtures do not approve the new source
method or assert that future method dispatch will accept it.

For every one of the 61 rows, the historical `source_catalog_predefined_tss` /
`start23-source-catalog-v0.1` pair returned `unsupported_planned_method_version`.
For each of 29 conditionally eligible timed rows, A=T/2 retained the mathematical
estimate but returned `duration_reliability_policy_missing` and no automatic use.
Thus total structural count 38 is not29 proven usable methods and certainly not38
fully eligible completions. New fully established occurrences remain zero in all
three sports. Supported observed zone measurements can still apply to single or
mixed performed sessions with independent actual evidence. Swim mean-HR, CSS/
distance conversions and distance-ratio RPE fallback remain unsupported.

Current specification permits the existing persisted planned label for genuinely
retained timed-source loads with lineage. Reusing that established compatibility
for an accepted new source must be explicit. If a new IF planned-method/version
is introduced, its compatibility must be accepted and dispatched separately;
unsupported versions cannot be relabelled to bypass the check. Corrections use
the original immutable snapshot, not today's source file or current template.

## Weekly and planning consequences

Known subtotal is distinct from planner-usable weekly load. An unrecorded workout
is unknown, not skipped or zero. Completed mixed intervals without supported
measurement remain unavailable; RPE does not fill their hard/recovery blocks.
Explicit skip can establish completeness without fabricating performed load.
Partial observations are not upgraded by matrix fallback. Existing intensity
coverage, fatigue, illness, injury, recovery/taper, caps and pending approval
remain unchanged. All source P/estimates/factors/ratios/provenance remain private.

[Simulations](JOREN_THREE_SPORT_PLANNING_SIMULATION.md) include measured/RPE mixes,
unknown and explicit-skip cases and three consecutive weeks. The unchanged engine
holds the next target when a week is incomplete; repeated templates keep separate
occurrences. Prospective cycling P differences can influence selection and later
references; they do not authorize historical recalculation. The seven-hour row's
single-zone predicate is not an athlete-suitability assessment.

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.
