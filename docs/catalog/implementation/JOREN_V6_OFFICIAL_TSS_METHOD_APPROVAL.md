# Official planned-TSS approval intake

2026-11-05, Europe/Amsterdam. Decision `joren-v6-phase-tss-owner-intake-1`.
Authority is the owner's current mission, relaying Joren's approval. Original
Joren answer date, signed document and independent review record were not supplied.

## Newly accepted evidence

The owner explicitly confirms that Joren approved the previously proposed official
planned-TSS approach. This is recorded as **OWNER_CONFIRMED_JOREN_APPROVAL**. Older
reports saying the method was pending are historical status, not a reason to
discard this approval. The unresolved issue is the exact binding of that approval
to a numerical proposal, not whether the owner relayed approval.

## Located earlier proposals and their exact scope

1. [Final decision brief, A](../JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md#a-geplande-tss-en-afronding)
   recommends exact operational calculation under an explicit Decimal policy,
   retaining original source P separately and rounding only at the presentation
   boundary. It offers rounded source P and a revised zone-minute source as
   alternatives, requiring an explicit choice. Its RUN/BIKE IF² proposal is paired
   with a **fixed SWIM matrix**, not the later all-sport IF² reconstruction.
2. [Integration sequence, C2](../JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md#c2--approved-planned-source-methods-and-precision)
   recommends 50-significant-digit HALF_EVEN, divide last, no intermediate
   quantization, with exact numerator/denominator where applicable. It separately
   identifies source displays and operational values. The general SWIM rounding
   boundary is explicitly unresolved. Its SWIM method is again the old matrix.
3. [V6 IF² reconciliation](JOREN_V6_IF2_RECONCILIATION.md) records the candidate
   `joren-v6-if2-rounded-reference-minutes-candidate-1` using
   `SUM(minutes × IF²) × 100/60 × sport_multiplier`, with SWIM meters converted
   using two-decimal reference minutes/100m. It preserves exact rational evidence
   and a 50-digit HALF_EVEN context result, with one-decimal HALF_EVEN display.
   It labels operational P unavailable, without selecting source-display versus
   exact-context authority.
4. [Partial approval register, question 1](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md#1-numerical-values-complete-calculation-method-still-open)
   explicitly asks both whether the full formula/display convention is correct
   **and** whether source or exact recomputation should be official. Its recorded
   answer confirms numerical inputs only. The final-policy update does not select
   either alternative. The current approval supersedes the old approval status,
   but does not uniquely identify which earlier proposal/convention it adopts.

The evidence therefore identifies a concrete earlier recommendation for exact
internal arithmetic, but cannot unambiguously bind a complete **77-row all-sport
IF² official method**, including its storage/comparison authority, to the owner's
unspecified reference to the earlier approach. It would be an invented decision
to choose rounded source display, exact mathematical rational, or 50-digit context
result merely because all reproduce the same one-decimal displays.

## Precise dependency P01

Bind the newly confirmed approval to an exact proposal/version and specify its
official numerical value: source-display decimal, exact rational recomputation,
50-digit HALF_EVEN recomputation, or another identified proposal. If the intended
proposal is the V6 rounded-reference IF² candidate, identify it explicitly and
confirm its comparison/storage and display conventions. No reconfirmation of the
already approved coefficients or beginner/intermediate/advanced classification
is requested. This one missing binding prevents official load assignment.

All 77 new template records consequently have `official_planned_load = null` and
`official_method = null`. The disabled C4 review uses an explicitly hypothetical
source-display exact-rational basis only; it cannot emit operational load rows.
`require_operational_source` remains fail-closed. No new compatibility entry is
added to Realized V2, and no historical method/version or athlete load changes.

## Preserved arithmetic and precision

Confirmed IF Z1–Z5: .55/.75/.88/.98/1.15. Confirmed SWIM min/100m:
2.17/2.00/1.83/1.67/1.50. Source multipliers RUN 1.15, BIKE 1.00, SWIM .90
apply once in the candidate; stationary wall rest contributes zero.
Input-reference version remains `joren-v6-partial-approval-1`.

Every row retains historical and revised source numeric lexemes, source format/
display, exact candidate numerator/denominator, 50-digit Decimal candidate,
candidate method/version, input-reference version, candidate display rounding and
the separately null official storage/comparison policy. The eight export residue
changes are recorded in the [source intake](JOREN_V6_PHASE_SOURCE_INTAKE.md).

| Precision fixture | Exact candidate | Candidate display | Alternative / significance |
| --- | --- | --- | --- |
| TR-SWIM-011 | 52.63956 | 52.6 | exact reference seconds would display 52.7 |
| TR-SWIM-012 | 58.24104 | 58.2 | exact reference seconds would display 58.1 |
| TR-SWIM-013 | 58.24104 | 58.2 | exact reference seconds would display 58.1 |
| TR-SWIM-014 | 61.5807 | 61.6 | exact reference seconds would display 61.7 |
| TR-BIKE-001 | 30.25 | 30.2 | HALF_UP would display 30.3 |
| TR-BIKE-010 | 281.25 | 281.2 | HALF_UP would display 281.3 |
| TR-RUN-009 | 86.25 | 86.2 | HALF_UP would display 86.3 |
| TR-BIKE-004 | 84.375 | 84.4 | old raw source 84.40000000000001 retained |

All 77 candidate displays reconcile. Reproduction is evidence, not authority.
Historical fixed-matrix, exact-reference-second, C2.1 and Realized V2 results
retain their original provenance; none is recalculated under this decision.

## Concrete proposal requested by the owner — no implementation

In response to P01, the owner instructed: **“Doe een voorstel zonder implenteren”**.
This requests a proposal and does not approve a numerical convention or authorize
its implementation. The following is explicitly **PROPOSED**, not operational.

Recommended future method identifier: `joren-v6-planned-if2-1`.

1. Use the approved zone IF² calculation for all three sports:
   `SUM(zone_minutes × IF_zone²) × (100/60) × sport_multiplier`.
   RUN/BIKE zone minutes come from the exact ordered timed segments. SWIM zone
   minutes use exact source meters × approved reference min/100m ÷ 100. Apply
   the source sport factor once; stationary rest contributes zero.
2. Make the **recomputed internal value** official, rather than the rounded
   workbook display. Perform the calculation as an exact rational from exact
   decimal inputs, then convert the final numerator/denominator once into a
   **50-significant-digit HALF_EVEN Decimal**. No intermediate quantization.
   This matches the existing V6 candidate arithmetic, with a new future approved
   method identifier rather than relabeling historical candidate results.
3. Compare budgets and store the official 50-digit result without rounding to a
   fixed decimal scale. Retain exact numerator/denominator, original numeric
   lexeme, original display, source revision, input-reference version and method
   version independently. One-decimal HALF_EVEN is a developer reconciliation
   display only; TSS remains absent from athlete APIs/UI/logs.
4. Apply only to newly created occurrences of explicitly approved future template
   revisions. Keep historical loads, source archives, occurrence snapshots and
   existing method dispatch unchanged. Do not infer Realized TSS from reference
   pace. Planned-method/Realized-V2 compatibility remains a separate contract.
5. Rerun phase-aware budget/allocation/partial-week examples under that exact
   official basis after approval: source-display witnesses are not guaranteed to
   keep their exact totals or ranking. No release or catalog activation follows
   from approving this numerical proposal alone.

Examples: BIKE-001 would have internal 30.25 and review display 30.2; RUN-009
internal 86.25/display 86.2; SWIM-011 internal 52.63956/display 52.6. A 45-TSS
weekly ceiling would compare the sum of internal values directly with 45.

**Not implemented:** no official method dispatch, operational value assignment,
database migration, planner selection or historical recalculation was added for
this proposal. P01 remains awaiting approval of this concrete proposal (or a
specific alternative). The generic owner-relayed Joren approval remains recorded
above without being used to imply acceptance of this newly written proposal.
