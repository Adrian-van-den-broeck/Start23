# V6 official planned-TSS acceptance successor

2026-11-05, Europe/Amsterdam. Decision `joren-v6-official-tss-acceptance-1`.
Method `joren-v6-planned-if2-1`; parameter reference
`joren-v6-approved-if-reference-1`. Private implementation evidence.

The product owner explicitly accepts the complete proposal in
[the previous approval-intake report](JOREN_V6_OFFICIAL_TSS_METHOD_APPROVAL.md#concrete-proposal-requested-by-the-owner--no-implementation),
as preserved at `fc876f10b5eb779a7f3004b460744da899cc739b`. The proposal's former
"proposed / no implementation" status remains historical evidence. This successor
closes its precise P01 numerical-authority dependency prospectively. The current
owner instruction is the approval record; no signed Joren document, original
Joren answer date, reviewer credential or external scientific review is invented.

## Accepted arithmetic and implemented boundary

`SUM(zone_minutes × IF_zone²) × (100/60) × sport_multiplier`.

| Zone | IF | SWIM reference min/100m |
| --- | ---: | ---: |
| Z1 | .55 | 2.17 |
| Z2 | .75 | 2.00 |
| Z3 | .88 | 1.83 |
| Z4 | .98 | 1.67 |
| Z5 | 1.15 | 1.50 |

RUN factor 1.15, BIKE 1.00, SWIM .90. RUN/BIKE quantities come from ordered timed
segment seconds divided by 60. SWIM quantities are ordered prescribed meters
times the approved reference minutes/100m divided by 100. The sport factor applies
exactly once. Typed stationary wall rest contributes zero. No athlete performance,
actual duration, CSS scaling, historical load or one-decimal source value enters
the new arithmetic.

`physiology/planned_v6.py` uses exact Decimal inputs converted to rational operands,
no intermediate quantization, and one final numerator/denominator conversion in an
explicit 50-significant-digit HALF_EVEN context. That final Decimal is the official
per-template value. The exact rational remains independently attributable evidence.
Budget/ranking arithmetic uses exact sums/fractions of the **final official
Decimals**, rather than silently substituting the original infinite rational or
rounding a week down to a ceiling. Aggregated decimal sums retain every operand
digit, even when their exact sum needs more than 50 significant digits. Future
storage must preserve unscaled numeric decimal strings; no storage migration ran.

One-decimal HALF_EVEN remains private reconciliation only. None of these values
is returned in an athlete DTO, errors, normal logs, mobile labels or analytics.

| Workout | Official internal value | Private reconciliation |
| --- | ---: | ---: |
| TR-BIKE-001 | 30.25 | 30.2 |
| TR-BIKE-004 | 84.375 | 84.4 |
| TR-RUN-009 | 86.25 | 86.2 |
| TR-SWIM-011 | 52.63956 | 52.6 |
| TR-SWIM-012 / 013 | 58.24104 | 58.2 |
| TR-SWIM-014 | 61.5807 | 61.6 |

## Exact source custody

The official adapter accepts the existing immutable phase-source release
`joren-v6-phase-source-release-1`, preserving its logical keys and template UUIDs.
It adds an explicitly separate official view; older draft/phase records with null
official load are unchanged. It never changes the active catalog's legacy
`with_current_load`, planned-source dispatch, historical occurrences or accepted IDs.

| Source | SHA-256 |
| --- | --- |
| RUN, 28 rows | `7380c88ef8bccb3cb35b0f6416d9debba8342b9802fc716f0a99dcfcb8626d88` |
| BIKE, 27 rows | `6322d7f93b3e074c77c4efa28b2a95de3f04f0f5c6af226ce50e8c2ff716ddbc` |
| SWIM, 22 rows | `48a0f6448f003ef048f40e53fda74b5220f272ebd4300180c108777c6e0be3ba` |

All 77 official values reconcile independently against the ordered source
prescriptions, with exact numerator/denominator and Decimal results. Historical
and current numeric lexemes, workbook display, phase text, source RPE/focus and
ordered events remain separately available. The eight exact export differences
at RUN M21/M26, BIKE M8/M25 and SWIM M12/M13/M21/M24 remain exactly as documented
in [phase intake](JOREN_V6_PHASE_SOURCE_INTAKE.md). They are never overwritten by
the official computation. [Private ledger](automatic-selection/evidence.json)
retains all 77 source/template identities and numerical provenance.

## Planned versus Realized V2

Official planned IF² approval does not approve a Realized V2 compatibility mapping.
The unchanged Realized V2 selector accepts only its existing approved provenance.
`joren-v6-planned-if2-1` therefore returns `unsupported_planned_method_version`
for the Session-RPE fallback, including uniform-zone timed sessions. Distance-only
and mixed sessions gain no new eligibility. Measured observations keep priority
and their original ruleset. Tests verify both fail-closed fallback and retained
measured-data priority. No historical relabeling, backfill or recalculation occurs.

All new templates remain INACTIVE. Official numerical acceptance authorizes this
software implementation; it does not activate the catalog, approve estimated-time
operational safety checks, execute SQL or authorize a deployment.
