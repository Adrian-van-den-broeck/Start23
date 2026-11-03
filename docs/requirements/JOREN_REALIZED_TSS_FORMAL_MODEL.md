# Joren realized-load formal model - version 2

Date: 2026-11-03. Product-approved authority: [approved v2 specification](JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md).
The former candidate-only model is retained in the [original review archive](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md).
Independent physiological validation/release review is not supplied by product approval.

For an eligible exact approved occurrence, q=(r+1)//2 after strict integer
validation of Session-RPE 1-10, F=max(0.600,min(1.250,1+0.125*(q-p))), and
E=P*A*F/T. All coefficients and inputs are Decimal. Version: `joren-realized-tss-matrix-2`.
The 25 literal expected factors are in `backend/tests/physiology/test_realized_v2.py`.

| Planned / reported | Z1 | Z2 | Z3 | Z4 | Z5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Z1 | 1.000 | 1.125 | 1.250 | 1.250 | 1.250 |
| Z2 | 0.875 | 1.000 | 1.125 | 1.250 | 1.250 |
| Z3 | 0.750 | 0.875 | 1.000 | 1.125 | 1.250 |
| Z4 | 0.625 | 0.750 | 0.875 | 1.000 | 1.125 |
| Z5 | 0.600 | 0.625 | 0.750 | 0.875 | 1.000 |

The old two difference=-3 cells at 0.600 are SUPERSEDED FOR THE NEW VERSION.
The linear rule gives 0.625, independently of the -4 floor. The unchanged PDF
and its source assertions remain historical evidence, not final v2 authority.

P/T/p and source method/version belong to the original approved occurrence and
revision. Only all-equal explicit planned segment zones qualify. Low/high, a
dominant interval, a current template and athlete RPE cannot supply p. Mixed-zone,
RPE-only/protocol, unplanned, brick and incompatible historical planned bases
are unavailable for this method. Reliable existing observations remain available.

A/T is uncapped. F bounds do not bound E/P. P100,T60,A90,F0.875 gives 131.25;
P120,T120,A60,p2,r3 gives 60; P120,T120,A120,p4,q1 gives 75.
No final cap, additional sport factor or one-decimal factor rounding is used.
Missing duration is unavailable; zero denominator/performed duration is rejected;
negative/nonfinite inputs fail safely. Zero planned-load arithmetic exists in the
pure helper but selection is disabled for zero planned basis.

Numeric policy `decimal-50-half-even-divide-last-1` fixes 50 significant digits,
ROUND_HALF_EVEN and default Decimal exponent/trap settings. Compute P*A*F/T once,
without intermediate quantization; store the context result without display
rounding. Store A/T's exact numerator and denominator as well as its context
quotient. New weekly consumers use 50 digits; historical helpers keep their
original conventions. Thresholds never consume display-rounded numbers.

Any changed duration A!=T retains its numeric estimate and exact provenance but
has automatic-use eligibility false (`duration_reliability_policy_missing`). No
reliability threshold was supplied, so the implementation does not invent one.

Observed complete/partial load and approved mean-HR estimates outrank RPE. Partial
and explicit all-zero evidence is never filled or replaced. RPE remains subjective
feedback with measured results; estimates are never called measured complete or
used for measurement-only matching thresholds. No new power/pace conversion exists.

`weekly-registration-2` separates known subtotal from nullable proven usable
weekly load. Unknown, pending, partial/unavailable, incompatible, source-conflicted
and orphaned-revision evidence withholds automatic growth/debt/reference use.
Explicit skipped means zero performed work; absence means unknown. Complete
mixed measured/eligible-estimated weeks may use existing planning coefficients.
No measured intensity minutes are derived from Session-RPE.

The RPE multiplier is a reasoned, unvalidated heuristic. Scientific/release review
and PostgreSQL/pgTAP execution remain open. All values here are private synthetic
developer fixtures; public APIs and mobile display no private loads or factors.
