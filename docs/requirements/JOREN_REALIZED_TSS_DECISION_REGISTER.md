# Joren realized-load decision register - v2

Date: 2026-11-03. Authority: [approved v2 specification](JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md). The owner's implementation instruction
supersedes the earlier unapproved proposals. The previous eighteen question
records are preserved in the [original review archive](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md). No independent reviewer is fabricated.

| Decision | OLD RULE | NEW RULE | EFFECTIVE VERSION | REASON | IMPACT ON HISTORICAL DATA | RELATED TESTS |
| --- | --- | --- | --- | --- | --- | --- |
| D01 | PDF has two -3 cells 0.600 | Additive clamp; -3=0.625; all 25 fixtures | matrix-2 / weekly-registration-2 where applicable | Owner chose consistent matrix | No backfill/reinterpretation; corrections keep original version | test_realized_v2.py |
| D02 | Duration formula/caps unresolved | P*A*F/T, uncapped ratio, no final cap | matrix-2 / weekly-registration-2 where applicable | Owner approved actual-duration adjustment | No backfill/reinterpretation; corrections keep original version | test_realized_v2.py |
| D03 | No unique mixed-session zone | Only all-equal explicit approved segment zones | matrix-2 / weekly-registration-2 where applicable | Owner excludes mixed sessions | No backfill/reinterpretation; corrections keep original version | test_realized_context.py |
| D04 | Changed structure/duration reliability unresolved | Mixed/ambiguous excluded; A!=T automatic use withheld | matrix-2 / weekly-registration-2 where applicable | No reliability cutoff supplied | No backfill/reinterpretation; corrections keep original version | test_realized_context.py; test_realized_v2_planning.py |
| D05 | Observed/HR only; fallback unapproved | Existing observations first, approved HR next, eligible RPE last | matrix-2 / weekly-registration-2 where applicable | Owner hierarchy; no new measurement converter | No backfill/reinterpretation; corrections keep original version | test_activities_v2.py; test_activities.py |
| D06 | Planned duration prefilled | Empty performed input, explicit confirmation, separate skip | matrix-2 / weekly-registration-2 where applicable | Prescription is not performed-time evidence | No backfill/reinterpretation; corrections keep original version | ActivityFlowProvider.test.tsx; networkRecovery.test.tsx |
| D07 | RPE 3->Z1; Z1 range2-3 | New sessions 1-2/3-4/5-6/7-8/9-10; explicit dispatch | matrix-2 / weekly-registration-2 where applicable | Owner explicitly requires RPE 3->Z2 | No backfill/reinterpretation; corrections keep original version | test_rpe_zones.py; ActivitiesScreens.test.tsx |
| D08 | Pydantic accepted bool/string/integral-float coercions | Current Session-RPE JSON integer only; historical values retained | matrix-2 / weekly-registration-2 where applicable | Engineering fail-closed canonical transport; no scientific policy inferred | No backfill/reinterpretation; corrections keep original version | test_activities_v2.py |
| D09 | Processing basis lacked exact P/T/segments | Exact original occurrence/revision/template/P/T/method/version snapshot | matrix-2 / weekly-registration-2 where applicable | Owner requires approved planned-load identity | No backfill/reinterpretation; corrections keep original version | test_realized_context.py; test_activities_v2.py |
| D10 | SUM could masquerade as complete weekly load | Expected occurrences, explicit skip vs unknown, subtotal plus nullable total | matrix-2 / weekly-registration-2 where applicable | Owner closes U-001 | No backfill/reinterpretation; corrections keep original version | test_weekly_registration.py; test_activities_v2.py |
| D11 | Any non-null subtotal could drive growth/debt | Complete eligible mixed weeks only; incomplete hold; evidence-bound pending plans | matrix-2 / weekly-registration-2 where applicable | Owner permits estimates only with complete registration | No backfill/reinterpretation; corrections keep original version | test_realized_v2_planning.py; test_a9_planning_parity.py |
| D12 | Measurement-only numeric match thresholds | RPE estimate remains distinct; subjective fatigue independent | matrix-2 / weekly-registration-2 where applicable | Owner forbids unsupported estimate-driven matching | No backfill/reinterpretation; corrections keep original version | test_activities_v2.py; physiology/test_activity.py |
| D13 | New precision unspecified; historical conventions vary | Decimal 50 half-even divide-last, unquantized storage, raw thresholds | matrix-2 / weekly-registration-2 where applicable | Reproducible implementation under owner precision requirements | No backfill/reinterpretation; corrections keep original version | test_realized_v2.py; test_realized_v2_planning.py |
| D14 | New version could misroute corrections to legacy | Explicit supported dispatch; original basis and append-only revisions | matrix-2 / weekly-registration-2 where applicable | Owner requires historical compatibility | No backfill/reinterpretation; corrections keep original version | test_activities_v2.py |
| D15 | Late replacement unspecified | No automatic replacement; preserve sources, block unresolved automatic use | matrix-2 / weekly-registration-2 where applicable | Owner leaves replacement outside approved policy | No backfill/reinterpretation; corrections keep original version | test_realized_v2_migration.py; test_weekly_registration.py |
| D16 | No new persistence/calculation version | matrix-2 + weekly-registration-2; four private forward migrations; local gates | matrix-2 / weekly-registration-2 where applicable | Owner approves prospective versioned implementation, not hosted activation | No backfill/reinterpretation; corrections keep original version | test_realized_v2_migration.py; test_activities_v2.py |
| D17 | Brick/provider conversions unspecified | Separate supported component identities; no new splits/converters | matrix-2 / weekly-registration-2 where applicable | Owner excludes unsupported scope | No backfill/reinterpretation; corrections keep original version | test_realized_context.py; test_activities.py |
| D18 | PDF wording suggested physiological authority | Reasoned unvalidated heuristic; private values; independent release review open | matrix-2 / weekly-registration-2 where applicable | Owner distinguishes product direction and scientific review | No backfill/reinterpretation; corrections keep original version | test_contracts.py; test_activities_v2.py; ActivitiesScreens.test.tsx |

## Remaining policy/release decisions

- A changed-duration reliability rule is absent. All A!=T estimates retain exact
  values/provenance but automatic eligibility is false. No numerical cutoff added.
- Automatic replacement after late evidence, brick allocation, new power/pace
  conversions and estimate-driven measurement-only matching remain disabled.
- Historical `source_catalog_predefined_tss` / `start23-source-catalog-v0.1` bases
  are incompatible; only actual Phase13 planned-zone snapshots qualify.
- Independent accountable scientific/release sign-off for the exact heuristic
  scope is open. Product approval is not that review.
- PostgreSQL/pgTAP is DEFERRED BY OWNER - PRE-BETA. Actual replay, function/trigger
  compilation, concurrency, numeric, grants/RLS and real-session/device gates are
  open. Local/test flags cannot activate staging or production.

These are bounded disabled cases/gates, not permission to invent physiology.
