# Joren realized matrix integration review - v2 implementation

Date: 2026-11-03. Current authority: [approved v2 specification](JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md). The earlier finding/approval-question
record is preserved unchanged in the [original review archive](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md). Its unapproved options are not
the current product decision. Product direction is approved; qualified independent
review and release evidence remain separate open gates.

## Baseline and custody

Started from `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`, branch
`feat/joren-realized-tss-v2`, worktree `.worktrees/joren-realized-tss-v2`.
Consecutive ancestry checks verified A10 `11591b9`, A3 `b65ea78`, A4 `4bb0cde`,
A5 `044ecfb`, A6 `24b27eb`, A7 `75f172d`, A8 `d0e726d`, A9 `e2d450b`.
The older root checkout and existing worktrees/visual evidence were preserved.

`Specificatie Realized TSS Matrix.pdf` is copied byte-for-byte into this branch:
180537 bytes, SHA-256
`b31f7fd72ebdda6f54f87fc5f25b69e53600f3476f5572d5e75af48615aef194`.
Its single rendered page and full extracted text were inspected. Original source:
the Joren simulator worktree. The PDF is not rewritten or treated as v2 authority.

## Resolved integration findings

- D01: consistent additive formula selected; Z4/Z1 and Z5/Z2 become 0.625.
- D02/D13: actual/planned duration ratio, uncapped, Decimal 50 divide-last;
  no intermediate/display rounding in stored values or thresholds.
- D03/D09: exact approved occurrence/revision snapshots; only uniform explicit
  zones qualify. No current-catalog substitution or inferred interval zone.
- D05: complete/partial observed and existing mean-HR provenance retain priority;
  no invented power/pace converter, estimate rescaling or full-session addition.
- D06: performed duration is explicitly entered/confirmed; no planned prefill.
- D07: versioned helpers, new API/mobile Session-RPE 3->Z2; old catalog/calibration
  and historical RPE 3->Z1 remain attributable to their original versions.
- D08: current Session-RPE transport is canonical JSON integer only. This is
  fail-closed input validation, not a change to stored historical interpretations.
- D10/U-001: v16 raw evidence plus deterministic weekly completeness; a subtotal
  is never automatically a proven total. Explicit skip and unknown have distinct
  owner-/revision-safe API/mobile confirmation actions and append-only events.
- D11: separate progression/debt/intensity/reference contracts. Complete mixed
  weeks are allowed; incomplete evidence holds. New pending plans freeze evidence
  and reject changed evidence on persistence/activation. Existing guards/constants
  and pending athlete confirmation remain in force.
- D14/D16: existing activity loads/constraints stay intact; separate append-only
  calculations and planning snapshots, explicit method/version dispatch, four
  unapplied forward migrations, no historical recalculation.

## Actual catalog coverage

The accepted A9 full-source projection contains 162 current templates: the 154
immutable source prescriptions plus 8 built-in templates. The v2 source versions
retain those prescriptions. The same actual segment rules used for occurrence
eligibility were inspected; these counts are structural candidates, not proof of
performed-session eligibility or a hosted database query.

| Sport | Current templates | Eligible candidates | Source rows / eligible |
| --- | ---: | ---: | ---: |
| Swim | 56 | 0 | 54 / 0 |
| Bike | 54 | 5 | 50 / 5 |
| Run | 52 | 5 | 50 / 5 |

Eligible stable source IDs: BIK-001..005 and RUN-001..005. Remaining rows have
mixed/non-zone structures; distance-only swims additionally lack planned duration.
An approved RPE-only projection without explicit zones is still ineligible even
if its original source template was uniform. No new workouts/zones were invented.

## Deliberately disabled boundaries

A!=T automatic use lacks a reliability policy, although the exact estimate is
stored. Zero-P selection, mixed/protocol/RPE-only prescriptions, unmatched or
incompatible planned methods, brick splitting, new provider conversions and
automatic late-measurement replacement are disabled. Numeric source conflicts and
unmatched imports are withheld from automatic weekly planning, retaining source
records and known values. Measurement-only overshoot/perfect-match rules do not
use RPE estimates. All restrictions are prospective; historical readers remain.

## Verification boundary

See the [implementation report](../implementation/JOREN_REALIZED_TSS_V2_IMPLEMENTATION_REPORT.md)
for exact source SHA, commands, final suites, privacy, catalog and A9 timing data.
Arithmetic/software verification is not physiological validation. PostgreSQL/pgTAP
is DEFERRED BY OWNER - PRE-BETA; syntax/static/mock checks do not establish runtime
RPC, concurrency, numeric, grant or RLS correctness. No database was changed,
no tools installed solely for database testing, and no push/merge/deploy occurred.
