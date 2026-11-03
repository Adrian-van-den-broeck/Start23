# Joren realized-load implementation plan - v2 execution record

Date: 2026-11-03. Approved scope: [approved v2 specification](JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md); detailed deltas:
[change log](JOREN_REALIZED_TSS_V2_CHANGELOG.md). Earlier conditional plan is kept
in the [original review archive](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md). Worktree `.worktrees/joren-realized-tss-v2`, branch
`feat/joren-realized-tss-v2`, accepted A9 base `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`.

## Reviewable implementation slices

1. Pure Decimal calculator, exact 25-cell fixtures, strict score mapping and
   duration arithmetic. Core examples 60/131.25/75 verified; old helpers retained.
2. Approved occurrence/revision snapshots and safe measurement selection;
   no inferred mixed-session zone or current-catalog substitution.
3. Separate private input/provenance/calculation records and atomic completion
   wrapper, forward-only unapplied migration, static and deferred SQL contracts.
4. Activity/RPE integration, explicit performed-duration entry, truthful qualitative
   feedback, local-only selection/readiness controls and stable historical paths.
5. Original-basis corrections, duplicate/response-loss/owner/stale regressions;
   A7/A8 recovery remains active. Late replacement is deliberately disabled.
6. Explicit skip/unknown ledger, revision-safe API/mobile confirmation and private
   weekly completeness. No zero-minute completed activity or zero-fill inference.
7. Progression/debt/reference/intensity consumer gates; preserve safety guards and
   coefficients. v16 evidence is frozen on pending plans and checked at activation.
8. Version-aware Python/range/API/mobile Session-RPE guidance; current integer
   transport; historical catalog/protocol/calibration semantics retained.
9. Current specification and five source documents versioned; 129-fixture inventory,
   full backend/mobile/static/privacy checks, multi-week/A9 parity, exact catalog
   coverage and local performance evidence. Final results belong to the report.

Local commits through slice 8:

```text
740008a feat(realized): add versioned Decimal matrix v2 calculator (slice 1)
dcffc59 feat(realized): preserve approved occurrence basis and evidence hierarchy (slice 2)
7841d09 feat(realized): append private v2 provenance and atomic RPC contracts (slice 3)
06dc572 feat(activities): integrate prospective estimates and explicit performed duration (slice 4)
11fd9dd test(realized): verify corrections, rollback reads and duplicate recovery (slice 5)
dab8777 feat(registration): distinguish explicit skipped, unknown and usable weekly evidence (slice 6)
fce4949 feat(planning): gate realized consumers on complete versioned evidence (slice 7)
f109856 feat(rpe): dispatch prospective session guidance without rewriting historical targets (slice 8)
```

## Verification and release boundary

See the [implementation report](../implementation/JOREN_REALIZED_TSS_V2_IMPLEMENTATION_REPORT.md)
for exact final source SHA, commands and counts. No phase is declared complete
from unit tests alone. New SQL remains unapplied; PostgreSQL/pgTAP is DEFERRED BY
OWNER - PRE-BETA, including actual RLS/grant/owner/concurrency/numeric/approval
execution. Existing CLI/parser/runtime dependencies were reused; no database
tooling was installed. Named scientific/release review and devices remain open.

Selection and storage flags default false. Staging/production activation is blocked
in configuration. Rollback is prospective selection-off with readers retained;
never delete data-bearing tables, relabel methods or rewrite approved plans.
Any future migration or eligibility relaxation requires its own explicit scope.
No push, merge or deployment is authorized/performed here.
