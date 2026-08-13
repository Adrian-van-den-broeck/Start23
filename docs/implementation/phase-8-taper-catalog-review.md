# Phase 8 taper source-catalog review

Reviewed on 2026-08-13 against
`docs/trainings/Trainingen START23.v01.xlsx - Sheet1.csv`.

## Result

The export contains exactly 160 unique rows: 50 cycling, 50 running, and 60
swimming. The declared 80/20 buckets contain 73 low-intensity (`80%`) and 87
high-intensity (`20%`) rows. All identifiers match their discipline prefix;
RPE values are within 1-10 and agree with the declared bucket boundary; zones
are within 1-5; segments are contiguous; and every supplied segment duration
or distance adds up to its supplied row total.

The file is not yet safe to import as the runtime catalog:

- all 60 swimming rows omit `Totale Duur (min)` and supply distance only;
- no column or row value identifies reviewed taper eligibility, taper period,
  or phase applicability;
- a training type such as `Herstel` or `Techniek` is not treated as a taper
  approval, because doing so would invent a physiological classification that
  is absent from the reviewed source.

The source therefore proves broad discipline and bucket coverage but does not
prove a complete swim/bike/run taper fixture. Full triathlon taper support
remains fail-closed. No new training definition and no guessed taper marker was
added.

## Reproducible validation

`backend.app.modules.workouts.source_catalog_audit.audit_source_catalog`
performs the read-only structural audit. Its repository test asserts the
current facts: 160 rows, the discipline and bucket counts above, no taper
marker, and exactly 60 missing-duration findings. The audit never emits or
places the source TSS field in a public contract.

## Required review before import

1. A qualified reviewer must explicitly label taper-eligible rows and their
   supported taper period/goal scope.
2. Every swimming candidate needs a reviewed planned duration, or the runtime
   catalog contract must be deliberately extended to support distance-only
   scheduling with deterministic duration/capacity rules.
3. The labelled candidates must pass the existing immutable catalog validator
   and a full swim/bike/run taper planning fixture before taper is advertised
   as supported.
