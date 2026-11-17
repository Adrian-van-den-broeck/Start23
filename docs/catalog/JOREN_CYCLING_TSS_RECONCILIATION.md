# Joren cycling TSS reconciliation

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

## Actual engine facts and comparison definitions

The accepted cycling coefficients in `physiology/joren.py` are exactly
0.50/0.80/1.20/1.60/2.00 per minute for Z1–Z5. `zone_load(..., planned=True)`
returns their unquantized Decimal sum; Realized V2 did not modify them. For a
retained timed source template, `with_current_load` instead preserves predefined
source P: it does not independently recalculate that P with these coefficients.
No TR-BIKE row is currently imported, so the reference below is an actual
zone-function calculation on the new source structure, not a live catalog lookup.

H is a **reconstruction hypothesis**, not approved provenance:
`sum(zone_minutes × candidate_IF_zone² × 100 × sport_multiplier) / 60`.
Observed populated IF candidates are Z1=.55, Z2=.75, Z4=.98, Z5=1.15. All Z3
minutes are zero; no Z3 anchor can be identified or proposed from these data.
The numerator is formed exactly; division uses a 50-digit Decimal context for
reproducible recurring values and occurs last. This is a review numeric policy,
not an already accepted new planned-load method. Repeating results are context
values, not claims of infinite precision. Exact rational comparison was used as
an independent check where needed; no intermediate segment is rounded.

“Raw difference” = original stored source P − current zone-minute reference.
“Display difference” = one-decimal displayed source P − exact current reference.
H is shown before one-decimal HALF_EVEN. Finite values are exact; ellipses on
recurring values below denote the full context value retained in scratch evidence.

| ID | SOURCE TSS raw | CURRENT ZONE-MINUTE TSS | RECONSTRUCTED IF² TSS H | RAW DIFFERENCE | DISPLAY DIFFERENCE | LIKELY EXPLANATION | APPROVAL REQUIRED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR-BIKE-001 | 30.2 | 30.00 | 30.2500 | 0.20 | 0.20 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-002 | 45.4 | 45.00 | 45.3750 | 0.40 | 0.40 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-003 | 60.5 | 60.00 | 60.5000 | 0.50 | 0.50 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-004 | 84.40000000000001 | 72.00 | 84.3750 | 12.40000000000001 | 12.40 | H rounds to source; formula unconfirmed; numeric residue | A: formula, precision and operational P |
| TR-BIKE-005 | 112.5 | 96.00 | 112.5000 | 16.50 | 16.50 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-006 | 140.6 | 120.00 | 140.6250 | 20.60 | 20.60 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-007 | 168.8 | 144.00 | 168.7500 | 24.80 | 24.80 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-008 | 196.9 | 168.00 | 196.8750 | 28.90 | 28.90 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-009 | 225 | 192.00 | 225.0000 | 33.00 | 33.00 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-010 | 281.2 | 240.00 | 281.2500 | 41.20 | 41.20 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-011 | 309.4 | 264.00 | 309.3750 | 45.40 | 45.40 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-012 | 337.5 | 288.00 | 337.5000 | 49.50 | 49.50 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-013 | 393.8 | 336.00 | 393.7500 | 57.80 | 57.80 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-014 | 221.8 | 208.00 | 221.80333333333333333… | 13.80 | 13.80 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-015 | 139 | 128.00 | 139.02666666666666666… | 11.00 | 11.00 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-016 | 221.8 | 208.00 | 221.80333333333333333… | 13.80 | 13.80 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-017 | 285.8 | 272.00 | 285.8300 | 13.80 | 13.80 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-018 | 216.6 | 192.00 | 216.6250 | 24.60 | 24.60 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-019 | 134.3 | 118.40 | 134.28333333333333333… | 15.90 | 15.90 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-020 | 84.5 | 73.50 | 84.4875 | 11.00 | 11.00 | H rounds to source; formula unconfirmed | A: formula, precision and operational P |
| TR-BIKE-021 | 96.09999999999999 | 83.50 | 96.066666666666666666… | 12.59999999999999 | 12.60 | H rounds to source; formula unconfirmed; numeric residue | A: formula, precision and operational P |

All 21 stored/displayed source values differ positively from the zone reference.
All 21 displays equal H rounded to one decimal HALF_EVEN. No coefficient was
tuned and no source cell was changed. If future approved source-retention behavior
is used, operational P may equal original source P by preservation; that zero
retention difference is not independent zone-method parity.

## Required examples and rounding ties

- TR-BIKE-001: 60×.50 = 30.00; source 30.2. H=.55²×100 = 30.25;
  HALF_EVEN gives 30.2, HALF_UP 30.3.
- TR-BIKE-004: 90×.80 = 72.00; source raw 84.40000000000001/display84.4.
  H=90/60×.75²×100 = 84.375; displayed difference +12.40.
- TR-BIKE-012: 360×.80 = 288.00; source 337.5. H=6×.75²×100 = 337.5;
  difference +49.50.

All four one-decimal midpoint cases, including ties where both modes agree:

| ID | H | HALF_EVEN | HALF_UP | Discriminating evidence |
| --- | --- | --- | --- | --- |
| TR-BIKE-001 | 30.25 | 30.2 | 30.3 | Yes |
| TR-BIKE-007 | 168.75 | 168.8 | 168.8 | No |
| TR-BIKE-010 | 281.25 | 281.2 | 281.3 | Yes |
| TR-BIKE-013 | 393.75 | 393.8 | 393.8 | No |

TR-BIKE-006's 140.625 is not a midpoint at one-decimal precision; it rounds to
140.6. Do not mistake a midpoint at a different decimal place for a one-decimal
tie. The related running TR-RUN-009 H86.25/display86.2 reinforces the hypothesis
without proving generation provenance or general scientific acceptance.

The 30-second cases are also independently reconciled:
020: 15×.50 +75×.80 +3×2 =73.50; H84.4875→84.5.
021: 15×.50 +85×.80 +4×2 =83.50; H96.066666…→96.1.
Raw 021 − reference is 12.59999999999999, not silently normalized to 12.6.

## Multiplier, methodology and provenance conflicts

Workbook G is one and its note states cycling multiplier1.00. The candidate H
uses it once. Multiplying by one twice has no numerical effect, so constants
alone cannot prove how often the original generator applied it. No additional
multiplier is required by the review and no rounding/formula provenance is
fabricated. This differs from swimming, whose PDF explicitly supplies a fixed
matrix already incorporating sport-specific coefficients; another0.90 would be
wrong. RUN's1.15 placement remains unconfirmed source intent despite numerical fit.

H rates for populated cycling zones would be .504166666…/.9375/1.600666666…/
2.204166666… per minute, not the approved .50/.80/1.60/2.00. This explains the
numerical difference under the hypothesis. H uses a zone anchor .98 that is not
the implemented per-score sRPE factors (RPE 7=.94,8=1.00). It must not activate the
inactive per-score sRPE reference or alter measured zone loads.

A new planned-source method/version requires Joren's accepted formula and exact
precision examples. Preserve original raw P, displayed P and reconstructed H as
separate evidence. Proposed operational exact H versus stored rounded source P is
an explicit decision under A; no new operational P is selected in this review.
A supported future occurrence must retain original P/T/zone/method/version.
At T=A=90, planned sourceP 84.4 could yield v2 estimate84.4, while independently
measured90-minute Z2 remains72.0. RPE must never force the measured result to 84.4.
Any new method compatibility must be explicitly accepted, never disguised by a
`planned_zone_minutes` label or a historical source-version rewrite.

See [all-sport methods](JOREN_THREE_SPORT_FINAL_RECONCILIATION.md) and
[the six Dutch approval questions](JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md).

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.
