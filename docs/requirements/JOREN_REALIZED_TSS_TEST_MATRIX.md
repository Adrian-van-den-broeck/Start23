# Joren realized-load test matrix - v2

Date: 2026-11-03. Authority: [approved v2 specification](JOREN_REALIZED_TSS_V2_APPROVED_SPECIFICATION.md). All 129 original fixture identities are
retained below. Exact original input descriptions and old expected proposals are
preserved in [test inventory v1](history/joren-realized-tss-review-1/JOREN_REALIZED_TSS_TEST_MATRIX.md).
This inventory maps requirements to executable test families/disabled guards;
it does not claim one test per row or that every SQL scenario ran on PostgreSQL.
Final commands, counts and named gaps are in the implementation report.

M01-M25 use 25 independently written literal Decimal expectations, not the tested
formula to generate expected values. M16/M22 are now 0.625. New scores 1..10 and
historical score 3 are explicitly covered. Core A/B/C yield 60/131.25/75. New storage
does not use the former proposed one-decimal quantization. The A!=T automatic-use
guard is distinct from the exact uncapped mathematical calculation.

| ID | Approved v2 expectation | Verification disposition | Executable family / guard |
| --- | --- | --- | --- |
| M01 | p1/q1: exact factor 1.000; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M02 | p1/q2: exact factor 1.125; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M03 | p1/q3: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M04 | p1/q4: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M05 | p1/q5: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M06 | p2/q1: exact factor 0.875; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M07 | p2/q2: exact factor 1.000; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M08 | p2/q3: exact factor 1.125; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M09 | p2/q4: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M10 | p2/q5: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M11 | p3/q1: exact factor 0.750; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M12 | p3/q2: exact factor 0.875; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M13 | p3/q3: exact factor 1.000; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M14 | p3/q4: exact factor 1.125; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M15 | p3/q5: exact factor 1.250; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M16 | p4/q1: exact factor 0.625; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M17 | p4/q2: exact factor 0.750; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M18 | p4/q3: exact factor 0.875; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M19 | p4/q4: exact factor 1.000; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M20 | p4/q5: exact factor 1.125; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M21 | p5/q1: exact factor 0.600; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M22 | p5/q2: exact factor 0.625; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M23 | p5/q3: exact factor 0.750; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M24 | p5/q4: exact factor 0.875; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| M25 | p5/q5: exact factor 1.000; full/half-duration arithmetic in calculator fixtures. | Automated software family; see exact tests | physiology/test_realized_v2.py: all 25 independent factor fixtures |
| R01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R03 | New r3->Z2; legacy r3 remains Z1. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R04 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R05 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R08 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R09 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R10 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R11 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R12 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R13 | Current JSON bool rejected; pure helper rejects bool. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R14 | Current numeric-string feedback rejected. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R15 | Current integral-float feedback rejected. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R16 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R17 | (3,4) accepted only with new mapping version; old resolver rejects. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| R18 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_rpe_zones.py; physiology/test_realized_v2.py; test_activities_v2.py; ActivitiesScreens.test.tsx |
| U01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U03 | Uncapped exact180; automatic use withheld for changed duration. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U04 | Uncapped exact225; automatic use withheld for changed duration. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U05 | Uncapped exact300; no finalcap; automatic eligibility withheld. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U08 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U09 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U10 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U11 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U12 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U13 | Pure arithmetic0, but zero-P selection unavailable. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U14 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| U15 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_context.py; test_activities.py; ActivityFlowProvider.test.tsx |
| S01 | Mixed zones: unavailable RPE fallback; observations still supported. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S02 | Warm-up-only: retain actual observation, no inferred single planned zone. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S03 | Skipped hard block: no whole-session matrix for mixed prescription. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S04 | Hard block only: observations retained; no uniform interval estimate. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S05 | Combined brick allocation disabled; no split policy. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S07 | Swim transition/duration inference disabled. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| S08 | Other-sport/new conversion disabled. | Disabled boundary / software guard | test_realized_context.py; test_activities.py; test_weekly_registration.py |
| H01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H03 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H04 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H05 | Explicit zero bins retain unavailable semantics; no HR/RPE replacement. | Disabled boundary / software guard | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H07 | Late automatic replacement disabled; numeric source conflicts withhold weekly eligibility. | Disabled boundary / software guard | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H08 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H09 | No power-TSS converter; metric presence does not activate one. | Disabled boundary / software guard | test_activities.py; test_activities_v2.py; test_realized_context.py |
| H10 | FIT/provider availability is not a validated load converter. | Disabled boundary / software guard | test_activities.py; test_activities_v2.py; test_realized_context.py |
| P01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P02 | Distance-only planned load/duration unavailable; no estimate. | Disabled boundary / software guard | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P03 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P04 | Historical incompatible planned method/version rejected for selection. | Disabled boundary / software guard | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P05 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| P07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_realized_context.py; test_activities_v2.py; test_realized_v2_migration.py |
| W01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W03 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W04 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W05 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W06 | Complete eligible mixed week accepted; source/version distribution retained. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W08 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W09 | No activities is unknown registration unless explicitly all skipped/rest-only. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W10 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W11 | Complete eligible weeks retain original80%/10% rule. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W12 | Below80% remains baseline branch, never rounded up. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W13 | Original strict-above110% debt boundary retained. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W14 | Original strict-above110% debt boundary retained with raw values. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W15 | Only complete eligible weekly load enters existing fatigue/missed rule. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W16 | Incomplete/null holds previous planned basis; no reseeding. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W17 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W18 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W19 | Original measured classification coverage rule retained; no RPE-derived minutes. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| W20 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_weekly_registration.py; test_realized_v2_planning.py; test_planning.py; test_a9_planning_parity.py |
| Q01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| Q02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| Q03 | RPE estimates excluded from measurement-only matching thresholds. | Disabled boundary / software guard | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| Q04 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| Q05 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| Q06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_activity.py; test_activities_v2.py; test_contracts.py; mobile activity/privacy/recovery tests |
| N01 | Stored0.375; no final one-decimal storage rounding. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N02 | Stored0.0375; positive small load is not missing/zero. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N03 | Decimal 50; retain numerator/denominator; no ratio quantization. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N04 | No display rounding is used for storage; historical rounding retained. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N05 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N06 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| N08 | Raw/new-context thresholds; no display-rounding drift. | Automated software family; see exact tests | physiology/test_realized_v2.py; test_realized_v2_planning.py; typed activity schemas |
| V01 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V02 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V03 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V04 | Explicit v2 assessment/correction path; no unequal-version legacy fallback. | Automated software family; see exact tests | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V05 | Append-only revisions and original planned basis; SQL execution deferred. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V06 | Separate private v2 records coexist with untouched old load tables. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V07 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V08 | Apply the approved v2 specification; preserve historical expected behavior where versioned. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V09 | Automatic late replacement disabled; records retained and ambiguous use withheld. | Disabled boundary / software guard | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V10 | New pending plan freezes exact v16 evidence; changed evidence blocks activation. | Automated software family; see exact tests; PostgreSQL atomicity/RLS/runtime deferred | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V11 | New selection disabled by default; storage readers retained on prospective rollback. | Disabled boundary / software guard | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |
| V12 | Hosted activation blocked pending database and independent release review. | Disabled boundary / software guard | test_activities_v2.py; test_realized_v2_migration.py; test_activities.py; A7/A8 mobile recovery suites |

## Additional implementation regressions

Tests also cover explicit performed entry/reset, strict JSON feedback, public
server-authoritative score 3 Zone2 guidance, skipped/unknown stale preconditions,
lost skip-response reconciliation, immutable logical activity retries, identity
replacement, fully recorded mixed weeks, the owner's110 unknown-third example,
no zero-fill, separate intensity evidence, three new-policy consecutive weeks,
raw sub-80% precision, original-source corrections and default deployment gates.
A9 fixtures retain exact catalog/input/output/intermediate hashes, process-worker
results and ten adjacent weeks. Catalog coverage and synthetic timing evidence
are generated by `backend/benchmarks/realized_v2.py`.

## Open verification gates

PostgreSQL/pgTAP is DEFERRED BY OWNER - PRE-BETA. The prepared SQL suite checks
private table/grant/RLS contracts; actual fresh/upgrade replay, function/trigger
compilation, numeric storage, complete RPC/correction/skip/approval concurrency,
two-owner isolation and account-deletion behavior still require database execution.
Static parser/string and in-memory tests do not establish those results. Real-token,
device and accountable scientific/release review remain open. No green arithmetic
or regression suite is labelled physiological validation.
