# Joren running Realized TSS V2 eligibility

Review date: 2026-11-03 (Europe/Amsterdam). REVIEW ONLY; no catalog activation.
Accepted source branch: `feat/joren-realized-tss-v2`, exact HEAD `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Review branch: `review/joren-new-workout-catalog`, isolated worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Input: `F:\Projecten Business\Start23\Code\docs\trainings\Looptrainingen_Definitief_Optie1.xlsx`.
Input SHA-256: `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3`; 7,198 bytes.
All numerical load values below are private developer review evidence, never athlete-facing data.

## Confirmed classification

**16 structural candidates, four mixed exclusions, zero presently established fully
eligible new occurrences.** All 20 rows are missing an accepted source catalog
version, authoritative planned-load method decision and approved occurrence
identity/snapshot. No imported template, approved plan or activity was created.
This is a source-intake assessment, not a claim about any athlete's stored data.

Existing measured-load methods can process all 20 running prescriptions when actual
completion evidence meets those methods' independent requirements. Spreadsheet
planned zone allocations are not actual measured zone minutes. The workbook itself
therefore proves zero completed measured activities as well.

In the all-row table, **M** means conditional measured-route support: complete
reliable observed zone minutes can establish measured load; approved mean-HR-zone
estimation may also apply under its existing run/confirmed-profile requirements,
with estimated provenance. **P** means source-version/load-method and exact approved
occurrence provenance remain absent in this intake. Every row has P. For a single
row **S** means structurally eligible for prospective RPE fallback; it is not
currently fully eligible. Mixed intervals have **X**, an additional hard exclusion.

| Workout / source row | Explicit zone structure | RPE fallback structure | Existing measured route | Missing provenance / present full eligibility |
| --- | --- | --- | --- | --- |
| TR-RUN-001 / 5 | Z1 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-002 / 6 | Z1 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-003 / 7 | Z1 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-004 / 8 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-005 / 9 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-006 / 10 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-007 / 11 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-008 / 12 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-009 / 13 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-010 / 14 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-011 / 15 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-012 / 16 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-013 / 17 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-014 / 18 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-015 / 19 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-016 / 20 | Z2 | S — structural candidate | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-017 / 21 | Z2 + Z4 | X — mixed intervals excluded | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-018 / 22 | Z2 + Z4 | X — mixed intervals excluded | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-019 / 23 | Z2 + Z5 | X — mixed intervals excluded | M — conditional on actual evidence | P — missing; fully eligible: no |
| TR-RUN-020 / 24 | Z2 + Z5 | X — mixed intervals excluded | M — conditional on actual evidence | P — missing; fully eligible: no |

## Current engine facts

Authority is the [approved V2 specification](../requirements/JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md),
`activities/realized_context.py`, `physiology/realized_v2.py`, `rpe_zones.py` and
`physiology/weekly_registration.py`. The current implementation uses:

- Mapping version `joren-realized-tss-matrix-2`: RPE 1–2→Z1, 3–4→Z2,
  5–6→Z3, 7–8→Z4, 9–10→Z5. All 20 source pairs match their Expected Zone.
  The historical catalog helper still defaults to 2–3/4/5–6/7–8/9–10. Source
  agreement with the new reporting mapping does not migrate prescription guidance.
- A single planned zone is established only when **every ordered approved segment**
  carries the same explicit zone. `zone_target` and historical explicit `zone`
  are recognized; conflicting fields, protocol targets and RPE-only targets fail
  closed. No dominant zone, Expected Zone, focus label or RPE range can substitute.
- Compatible planned method/version is `planned_zone_minutes` /
  `phase-13-joren-ruleset-1`. Historical `source_catalog_predefined_tss` /
  `start23-source-catalog-v0.1` is unsupported by v2. New/unknown combinations fail
  closed. The approved spec explicitly recognizes the existing occurrence
  persistence label for retained timed source P; matching the label does not prove
  P equals a fresh zone-minute recomputation.
- Only when no higher-priority supported observation is selected may an eligible
  occurrence use `E=P*A*F/T`, with the approved additive/clamped zone factor.
  This does not activate the old IF-squared reference sRPE formula.
- Decimal policy is 50 significant digits HALF_EVEN, divide last, no intermediate
  quantization. Realized TSS V2 never applies workbook sport multiplier 1.15 again.

## Can the approved occurrence carry an authoritative snapshot?

**The existing contract can carry it, but this workbook does not supply or create
it.** Code review found an exact private occurrence projection in
`20261103134520_joren_realized_tss_v2_private_provenance.sql::get_activity_processing_context_v2`.
It joins the athlete-owned activity to the exact planned-workout occurrence,
active/superseded approved revision, private planned-workout load and immutable
matching template ID/version. It carries:

| Required basis | Existing contract | New workbook/intake status |
| --- | --- | --- |
| Plan ID, revision ID/number, occurrence ID | Exact owner-linked joins | Absent; not plan data |
| Immutable template ID/version | Matching occurrence and retained template | Absent; TR ID alone is insufficient |
| Source catalog/workout ID and original file binding | Source IDs in snapshot; file/version intake manifest must bind them | TR ID and review hash exist; accepted catalog version missing |
| P and original planned method/version | Exact private occurrence-load row | Source P exists; intended method/precision acceptance unresolved |
| T | Exact occurrence duration snapshot | Positive complete source minutes exist; not yet an occurrence |
| Planned zone / ordered segments | Original occurrence segments, all same explicit zone | 16 source candidates; four mixed exclusions |
| A | Explicit actual duration confirmation on activity | No actual activity/duration confirmation supplied |
| Reported Session-RPE | Canonical integer 1–10 on new submission | Expected source pair is not a report |

A future accepted import and athlete-approved plan may use this existing
occurrence path for the 16 candidates if the planned method/version is genuinely
the approved supported pair and original source provenance remains honest.
If the accepted new catalog instead uses a new planned method/version not
supported by current v2, eligibility remains withheld until an explicitly
approved/versioned compatibility change; never relabel to bypass dispatch.
No schema/API change is made or presumed necessary by this review.

A synthetic all-20 code exercise constructed in-memory approved-basis-shaped
fixtures with source P/T, explicit source segments and the existing supported
pair. With confirmed A=T, no measurement and reported lower source RPE endpoint,
`select_rpe_estimate` returned planner-eligible estimates for exactly 001–016.
For 017–020 it returned `unsupported_structure` with no estimate. This proves
conditional contract compatibility, **not authoritative source approval or
actual occurrence eligibility**. Supplying no basis returns
`missing_approved_occurrence`; that is the present missing-evidence boundary.

Corrections retain the original occurrence/revision/catalog/P/T/zone/method/version
basis, including when current catalog selection later changes. A repeated template
must have distinct occurrence identities. A newer template, title match or today's
zone profile cannot replace the approved snapshot. Selection defaults/storage
readiness remain disabled and all database/release gates remain open.

## Measurement and completion hierarchy

Reliable observed zone bins win, including partial observations. No unobserved
minutes are extrapolated. Explicit all-zero bins do not open the RPE path through
a missing-data loophole. Only when independently permitted by the existing run
method may reliable duration and average HR with a confirmed matching profile
produce `average_hr_zone_duration`; it is estimated, not measured-complete.
There is no new power, running-pace, swimming-pace or provider TSS conversion.

For mixed 017–020, actual measured bins may therefore produce a valid load even
though whole-session RPE fallback is excluded. A warm-up-only completion, skipped
hard block or missing intervals never becomes a corrected full-session estimate.
The source planned minutes must not be mistaken for observation evidence. Actual
load, RPE feedback and fatigue signals retain separate provenance.

Additional explicit reasons that can withhold eligibility after a future import:

| Condition | Current reason or rule |
| --- | --- |
| No exact approved occurrence | `missing_approved_occurrence` |
| Unsupported original P method/version | `unsupported_planned_method_version` |
| Mixed, projected RPE-only or ambiguous segment structure | `unsupported_structure` |
| Missing/zero P | `missing_or_zero_planned_basis` |
| Unconfirmed actual minutes | `performed_duration_unconfirmed` |
| Missing A/T or zero duration | `missing_duration` / `zero_duration` |
| A differs from T | Exact estimate retained; `duration_reliability_policy_missing`; automatic use withheld |
| Observation already selected | `observation_selected`; no RPE addition or multiplication |
| Wrong revision, unresolved source conflict, partial/unavailable load | Weekly usable total withheld |
| Unknown completion or awaiting feedback | Weekly usable total withheld; never count as skipped/zero |

## Weekly planning implications and decisions

An all-single-zone plan could achieve 100% conditional RPE structural coverage,
but it is not guaranteed: projected RPE-only execution strips explicit zones;
source-method provenance may be unsupported; actual duration may differ; or a
completion may be unknown. Calendar/swipe repeats must preserve distinct occurrence
snapshots. RPE-only onboarding remains unsupported; the existing HR-monitor and
calibration/zone-readiness rules remain intact.

With all expected occurrences resolved, complete measured/approved-estimated
mixtures may feed existing volume progression/reference/debt rules. Missing,
partial, unknown or conflicting evidence holds/fails closed. No RPE estimate
supplies measured intensity minutes, and measurement-only overshoot/perfect-match
rules do not consume these estimates. In-memory rolling and mixed-week results
are recorded in the [validation report](JOREN_RUNNING_CATALOG_VALIDATION.md).

Joren/owner decisions J1–J4 are required before claiming new-source eligibility:
planned load authority and precision, versioned source identity, approved selection
metadata and versioned prescription representation. No approval to apply a
whole-session matrix to mixed intervals is implied or requested as a workaround.
Any future rule change would need its own explicit versioned specification.

PostgreSQL/pgTAP remains **DEFERRED BY OWNER — PRE-BETA**. Snapshot/identity/RLS/
concurrency/numeric storage assertions here are code/static-contract findings and
synthetic Python results, not executed hosted guarantees. Full cross-sport and
new-source occurrence verification waits for cycling/swimming and accepted metadata.
