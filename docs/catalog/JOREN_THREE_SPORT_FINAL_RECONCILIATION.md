# Joren three-sport final reconciliation

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

## Status and preserved evidence

All three actual workbooks are now supplied: RUN 20, BIKE 21, SWIM 20 = **61 rows**.
All source structure checks pass. Structural single-zone counts are 16/13/9 =38;
mixed counts4/8/11 =23. Source-specific RUN/SWIM reports are historical evidence
and remain byte-identical. The old combined register/readiness/import plan retain
their earlier sections with explicit current-stage addenda; earlier “cycling
absent” statements describe the prior intake, not present availability.

This is a complete source review and approval package, not accepted science,
activated catalog content or complete integration readiness. A–F approvals,
source-method compatibility, swim duration/rest semantics and performance gates
remain open. No silence or arithmetic match is recorded as approval.

## One comparison of source methods

| Aspect | Running | Cycling | Swimming |
| --- | --- | --- | --- |
| Planned source basis | Timed zone allocations, source P constants | Timed zone allocations including30s sprints, source P constants | Distance in each zone; fixed per 100m matrix explicitly published |
| Current independent coefficients | .58/.92/1.38/1.84/2.30 per min | .50/.80/1.20/1.60/2.00 per min | .45/.72/1.08/1.44/1.80 per min; cannot use without reliable time |
| Reconstructed/published constants | H populated IF=.55/.75/.98/1.15 forZ1/Z2/Z4/Z5; unconfirmed | Same H candidate values; unconfirmed; noZ3 evidence | Published .98/1.44/1.98/2.40/2.70 per 100m, stationary rest0 |
| Multiplier | Source1.15; H incorporates once, original methodology unconfirmed | Source1.00; H incorporates once, repeated unity is numerically unidentifiable | .90 already represented in sport-specific coefficients underlying matrix; no additional .90 |
| Precision evidence | Stored one-decimal values plus raw017 residue; H has exact/context result | Stored one-decimal values plus raw004/021 residues; H has exact/context result | Stored one-decimal values; published calculation can retain exact hundredths, e.g28.44 |
| Rounding | HALF_EVEN H hypothesis fits20 displays, including86.25→86.2; not accepted provenance | HALF_EVEN H hypothesis fits21 displays;30.25→30.2 and 281.25→281.2 distinguish HALF_UP | All 20 match one-decimal display; no observed tie identifies general mode; constants themselves are published rounded inputs |
| Athlete/reference inputs | Source prescription, not actual performance; no individualized H formula supplied | Source prescription, not actual performance; no individualized H formula supplied | CSS1:55 is representative reference for fixed matrix, not defined athlete-CSS scaling or performed time |
| Historical versions | Existing start23-v0.1 source v1/v2 and old occurrences retain original methods | Same; new TR IDs are distinct from BIK IDs | Same; original distance P retained historically while active projection withholds it |
| Proposed future import method | Separately accepted/versioned H or explicit retained-source decision; no scientific coefficient edits | Same, independently accepted with exact examples | Separately accepted/versioned published distance matrix; retain original source P and exact derived P separately |
| V2 compatibility | 16 structural timed candidates; actual approval/method/snapshot/A/report required | 13 structural timed candidates; same gates | Nine single but no source T; no present duration fallback;11 mixed excluded |

The current timed-source path preserves predefined P rather than recomputing it
with the zone-minute engine. The existing persisted Phase13 occurrence label can
carry retained timed source loads, as the approved V2 spec documents, but it does
not prove numerical zone-method parity. New load-origin/method evidence must be
preserved explicitly; any new method/version compatibility needs acceptance.
Historical source method/version pairs remain unsupported for v2 without relabel.

The 38 structural rows comprise29 timed RUN/BIKE candidates and nine distance-only
SWIM candidates. Actual new approved occurrences and completed evidence are absent:
**fully established new-source fallback eligibility =0 for every sport**. Favorable
synthetic existing-method probes yield29 conditional successes, not29 newly
approved load methods. All 23 mixed sessions remain excluded. A/T is never replaced
by distance ratio, and actual duration/intensity/distance is never inferred from RPE.

## All 61 numerical and structural results

Measure is minutes for RUN/BIKE and meters for SWIM. Source P is the raw original
cell. Current zone reference is the real engine function for timed rows; SWIM is
unavailable under its current distance-only projection. H is unapproved IF² for
RUN/BIKE; A is the explicitly published fixed-distance SWIM formula.
The last numeric column is raw source−zone reference for timed sports, and raw
source−published A for SWIM. These different comparison bases are explicit.
Long recurring H outputs are abbreviated here; 50-digit review values remain in
`.runtime/final/analysis.json` and the calculation recipe is in the cycling report.
Display differences are separated in the sport-specific reconciliations.

| ID / source row | Measure | Raw source P | Current zone reference / active swim P | H hypothesis or published A | Raw difference (defined above) | Source structure / V2 boundary |
| --- | --- | --- | --- | --- | --- | --- |
| TR-RUN-001 / 5 | 30 min | 17.4 | 17.40 | 17.393750 | 0.00 | single; occurrence/method/actual gates |
| TR-RUN-002 / 6 | 40 min | 23.2 | 23.20 | 23.19166666666666666… | 0.00 | single; occurrence/method/actual gates |
| TR-RUN-003 / 7 | 50 min | 29 | 29.00 | 28.98958333333333333… | 0.00 | single; occurrence/method/actual gates |
| TR-RUN-004 / 8 | 30 min | 32.3 | 27.60 | 32.343750 | 4.70 | single; occurrence/method/actual gates |
| TR-RUN-005 / 9 | 40 min | 43.1 | 36.80 | 43.125000 | 6.30 | single; occurrence/method/actual gates |
| TR-RUN-006 / 10 | 50 min | 53.9 | 46.00 | 53.906250 | 7.90 | single; occurrence/method/actual gates |
| TR-RUN-007 / 11 | 60 min | 64.7 | 55.20 | 64.687500 | 9.50 | single; occurrence/method/actual gates |
| TR-RUN-008 / 12 | 70 min | 75.5 | 64.40 | 75.468750 | 11.10 | single; occurrence/method/actual gates |
| TR-RUN-009 / 13 | 80 min | 86.2 | 73.60 | 86.250000 | 12.60 | single; occurrence/method/actual gates |
| TR-RUN-010 / 14 | 90 min | 97 | 82.80 | 97.031250 | 14.20 | single; occurrence/method/actual gates |
| TR-RUN-011 / 15 | 100 min | 107.8 | 92.00 | 107.812500 | 15.80 | single; occurrence/method/actual gates |
| TR-RUN-012 / 16 | 110 min | 118.6 | 101.20 | 118.593750 | 17.40 | single; occurrence/method/actual gates |
| TR-RUN-013 / 17 | 120 min | 129.4 | 110.40 | 129.375000 | 19.00 | single; occurrence/method/actual gates |
| TR-RUN-014 / 18 | 130 min | 140.2 | 119.60 | 140.156250 | 20.60 | single; occurrence/method/actual gates |
| TR-RUN-015 / 19 | 140 min | 150.9 | 128.80 | 150.937500 | 22.10 | single; occurrence/method/actual gates |
| TR-RUN-016 / 20 | 150 min | 161.7 | 138.00 | 161.718750 | 23.70 | single; occurrence/method/actual gates |
| TR-RUN-017 / 21 | 60 min | 87.59999999999999 | 82.80 | 87.566750 | 4.79999999999999 | mixed; whole-session matrix excluded |
| TR-RUN-018 / 22 | 55 min | 74.5 | 69.00 | 74.54970833333333333… | 5.50 | mixed; whole-session matrix excluded |
| TR-RUN-019 / 23 | 68 min | 106.8 | 94.30 | 106.8158333333333333… | 12.50 | mixed; whole-session matrix excluded |
| TR-RUN-020 / 24 | 68 min | 119.9 | 106.72 | 119.9258333333333333… | 13.18 | mixed; whole-session matrix excluded |
| TR-BIKE-001 / 5 | 60 min | 30.2 | 30.00 | 30.2500 | 0.20 | single; occurrence/method/actual gates |
| TR-BIKE-002 / 6 | 90 min | 45.4 | 45.00 | 45.3750 | 0.40 | single; occurrence/method/actual gates |
| TR-BIKE-003 / 7 | 120 min | 60.5 | 60.00 | 60.5000 | 0.50 | single; occurrence/method/actual gates |
| TR-BIKE-004 / 8 | 90 min | 84.40000000000001 | 72.00 | 84.3750 | 12.40000000000001 | single; occurrence/method/actual gates |
| TR-BIKE-005 / 9 | 120 min | 112.5 | 96.00 | 112.5000 | 16.50 | single; occurrence/method/actual gates |
| TR-BIKE-006 / 10 | 150 min | 140.6 | 120.00 | 140.6250 | 20.60 | single; occurrence/method/actual gates |
| TR-BIKE-007 / 11 | 180 min | 168.8 | 144.00 | 168.7500 | 24.80 | single; occurrence/method/actual gates |
| TR-BIKE-008 / 12 | 210 min | 196.9 | 168.00 | 196.8750 | 28.90 | single; occurrence/method/actual gates |
| TR-BIKE-009 / 13 | 240 min | 225 | 192.00 | 225.0000 | 33.00 | single; occurrence/method/actual gates |
| TR-BIKE-010 / 14 | 300 min | 281.2 | 240.00 | 281.2500 | 41.20 | single; occurrence/method/actual gates |
| TR-BIKE-011 / 15 | 330 min | 309.4 | 264.00 | 309.3750 | 45.40 | single; occurrence/method/actual gates |
| TR-BIKE-012 / 16 | 360 min | 337.5 | 288.00 | 337.5000 | 49.50 | single; occurrence/method/actual gates |
| TR-BIKE-013 / 17 | 420 min | 393.8 | 336.00 | 393.7500 | 57.80 | single; occurrence/method/actual gates |
| TR-BIKE-014 / 18 | 180 min | 221.8 | 208.00 | 221.8033333333333333… | 13.80 | mixed; whole-session matrix excluded |
| TR-BIKE-015 / 19 | 120 min | 139 | 128.00 | 139.0266666666666666… | 11.00 | mixed; whole-session matrix excluded |
| TR-BIKE-016 / 20 | 180 min | 221.8 | 208.00 | 221.8033333333333333… | 13.80 | mixed; whole-session matrix excluded |
| TR-BIKE-017 / 21 | 220 min | 285.8 | 272.00 | 285.8300 | 13.80 | mixed; whole-session matrix excluded |
| TR-BIKE-018 / 22 | 150 min | 216.6 | 192.00 | 216.6250 | 24.60 | mixed; whole-session matrix excluded |
| TR-BIKE-019 / 23 | 100 min | 134.3 | 118.40 | 134.2833333333333333… | 15.90 | mixed; whole-session matrix excluded |
| TR-BIKE-020 / 24 | 93 min | 84.5 | 73.50 | 84.4875 | 11.00 | mixed; whole-session matrix excluded |
| TR-BIKE-021 / 25 | 104 min | 96.09999999999999 | 83.50 | 96.06666666666666666… | 12.59999999999999 | mixed; whole-session matrix excluded |
| TR-SWIM-001 / 5 | 1000 m | 14.4 | unavailable | 14.40 | 0.00 | single; T missing |
| TR-SWIM-002 / 6 | 1500 m | 21.6 | unavailable | 21.60 | 0.00 | single; T missing |
| TR-SWIM-003 / 7 | 2000 m | 28.8 | unavailable | 28.80 | 0.00 | single; T missing |
| TR-SWIM-004 / 8 | 2500 m | 36 | unavailable | 36.00 | 0.00 | single; T missing |
| TR-SWIM-005 / 9 | 3000 m | 43.2 | unavailable | 43.20 | 0.00 | single; T missing |
| TR-SWIM-006 / 10 | 3500 m | 50.4 | unavailable | 50.40 | 0.00 | single; T missing |
| TR-SWIM-007 / 11 | 4000 m | 57.6 | unavailable | 57.60 | 0.00 | single; T missing |
| TR-SWIM-008 / 12 | 4500 m | 64.8 | unavailable | 64.80 | 0.00 | single; T missing |
| TR-SWIM-009 / 13 | 5000 m | 72 | unavailable | 72.00 | 0.00 | single; T missing |
| TR-SWIM-010 / 14 | 1600 m | 28.4 | unavailable | 28.44 | -0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-011 / 15 | 2600 m | 48.2 | unavailable | 48.24 | -0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-012 / 16 | 2600 m | 56.6 | unavailable | 56.64 | -0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-013 / 17 | 2600 m | 56.6 | unavailable | 56.64 | -0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-014 / 18 | 3000 m | 56.7 | unavailable | 56.70 | 0.00 | mixed; whole-session matrix excluded |
| TR-SWIM-015 / 19 | 1600 m | 37.3 | unavailable | 37.26 | 0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-016 / 20 | 2100 m | 50.8 | unavailable | 50.76 | 0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-017 / 21 | 2600 m | 64.3 | unavailable | 64.26 | 0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-018 / 22 | 1600 m | 37.3 | unavailable | 37.26 | 0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-019 / 23 | 2100 m | 50.8 | unavailable | 50.76 | 0.04 | mixed; whole-session matrix excluded |
| TR-SWIM-020 / 24 | 2600 m | 64.3 | unavailable | 64.26 | 0.04 | mixed; whole-session matrix excluded |

RUN has 17 positive zone-reference differences and three display-parity rows. BIKE
has 21 positive differences. SWIM has 20/20 display matches; ten stored values equal
exact A and ten differ by±.04 from storing one decimal. Numerical reconstruction
does not identify original formula intent, calibrate athletes or establish safety.
Z3 IF is unidentifiable in both timed workbooks and must stay undefined.

## All 61 proposed selection/guidance values

Every value in this table is **PROPOSED**, with automatic/swipe activation withheld
until A–F acceptance. L=low; H=high. B/Bu/R/Ta=base/build/recovery/taper. HR means
confirmed run/bike HR capability, compatible unvalidated HR fallback only under
existing rules; PACE means confirmed swim pace/CSS, HR fallback incompatible.
All allow repeated immutable templates only with separate occurrence IDs and the
existing automatic bound24; no unlimited repeat, cross-sport redistribution,
novice capacity or new threshold is inferred.

For intervals, preserve original session-focus RPE separately and propose per-zone
block ranges1–2/3–4/5–6/7–8/9–10. The diagnostic uses each block's lower endpoint
and a normalized aggregate range spanning the block ranges, rather than assigning
session-focus9–10 to a Z2 block. This is a candidate representation requiring D,
not a silent rewrite of the source focus pair or legacy RPE 3 semantics.
All source catalog/method versions are missing; all technical IDs follow the
explicit collision-checked UUID5 policy in the integration sequence. Row source
identity, file hash, sheet/row/cells, raw values and ordered tokens remain immutable.

| ID | Focus RPE (source) | PROPOSED bucket / phases | PROPOSED capability | PROPOSED block ranges by zone | PROPOSED selection / specific hold |
| --- | --- | --- | --- | --- | --- |
| TR-RUN-001 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-002 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-003 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-004 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-005 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-006 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-007 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-008 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-009 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-010 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-011 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-012 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-013 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-014 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-015 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-016 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-017 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-018 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-019 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-RUN-020 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-001 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-002 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-003 | 1, 2 | low / base,build,recovery,taper | HR / fallback compatible | Z1:1-2 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-004 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-005 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-006 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-007 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-008 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-009 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-010 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-011 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-012 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-013 | 3, 4 | low / base,build,recovery,taper | HR / fallback compatible | Z2:3-4 | archive/explicit-only pending individual scope; do not auto-offer to beginner |
| TR-BIKE-014 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-015 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-016 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-017 | 7, 8 | high / build | HR / fallback compatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-018 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-019 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-020 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z1:1-2, Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-BIKE-021 | 9, 10 | high / build (Z5 only build 4) | HR / fallback compatible | Z1:1-2, Z2:3-4, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-001 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-002 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-003 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-004 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-005 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-006 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-007 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-008 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-009 | 3, 4 | low / base,build,recovery,taper | PACE / fallback incompatible | Z2:3-4 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-010 | 5, 6 | high / build | PACE / fallback incompatible | Z2:3-4, Z3:5-6 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-011 | 5, 6 | high / build | PACE / fallback incompatible | Z2:3-4, Z3:5-6 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-012 | 7, 8 | high / build | PACE / fallback incompatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-013 | 7, 8 | high / build | PACE / fallback incompatible | Z2:3-4, Z4:7-8 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-014 | 5, 6 | high / build | PACE / fallback incompatible | Z2:3-4, Z3:5-6 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-015 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-016 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-017 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-018 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-019 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |
| TR-SWIM-020 | 9, 10 | high / build (Z5 only build 4) | PACE / fallback incompatible | Z2:3-4, Z3:5-6, Z5:9-10 | auto + swipe only after approvals; repeat via distinct occurrence IDs |

The single-candidate seven-hour diagnostic deliberately used the earlier broad
all-low automatic assumption to expose its limitation. The final proposal above
holds TR-BIKE-013 from automatic beginner use pending specific Joren scope; this
hold is not active code. Other long sessions also have no newly invented novice
eligibility thresholds. Joren must accept the intended athlete scope, not merely
a broad phase tag. A selection proposal is not a guarantee that a first-week
catalog has suitable short sessions: shortest new RUN 30min, BIKE 60min, SWIM 1000m.

Mixed source labels are not interpreted as one homogeneous zone. Full swimming
rests remain separate zero-distance/zero-load source events; diagnostic folding
into preceding instructions is not the production canonical rest representation.
Published A's rest0 is resolved; observed rest completeness and total active/
elapsed-time semantics remain unapproved.

## Required decisions and execution gates

The [Dutch brief](JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md) asks six grouped
questions A–F once. Technical UUID/lineage/adapter choices are engineering
recommendations; scientific formula/athlete-scope decisions are not inferred.
No actual new approvals have been received. [Simulations](JOREN_THREE_SPORT_PLANNING_SIMULATION.md)
separate current behavior, P 50 current-distance exclusion and D61 diagnostic
retained-distance P, including timed-out automatic searches, verified explicit
witnesses, three-week registration holds and seven-hour beginner limitation.
[Integration slices C1–C8](JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md) are a plan only.

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.
