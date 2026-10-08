# Brontraceerbaarheid

INTERNAL BUSINESS / ENGINE REVIEW
NOT FOR END-USER DISTRIBUTION

Bronbranch: fix/catalog-capacity-fresh-athlete
Volledige SHA: 6b1189b70a6505726fef70c4616a2f3d6dd4c94a
Auditbranch: docs/joren-training-engine-simulator
Datum: 8 oktober 2026

Gebruik de gepinde werkboom voor lijnnummers. Source manifest bevat SHA256 per bestand; geen .env of persoonsgegevens zijn gelezen voor deze bijlagen.

| RULE ID | Bron | Functie | Van | Tot | Excel |
| --- | --- | --- | --- | --- | --- |
| INIT-01 | backend/app/modules/physiology/joren.py | starting_baseline | 106 | 129 | 01_ATHLETE_INPUTS!F6:F8 |
| INIT-02 | backend/app/modules/physiology/joren.py | starting_baseline | 106 | 129 | 01_ATHLETE_INPUTS!F9 |
| INIT-03 | backend/app/modules/planning/service.py | _onboarding_baseline | 444 | 473 | 01_ATHLETE_INPUTS |
| INIT-04 | backend/app/modules/planning/domain.py | build_weekly_plan | 1342 | 1789 | NOT IMPLEMENTED: complete proposal gate ontbreekt; numeriek target is geen geldig plan |
| GOAL-01 | backend/app/modules/onboarding/eligibility.py | required_disciplines_for_race_type | 18 | 22 | 02_GOAL |
| CAL-01 | backend/app/modules/physiology/joren.py | calibrate | 189 | 205 | 03_CALIBRATION!E7:E8 (CURRENT), F7:F8 (JOREN) |
| CAL-02 | backend/app/modules/physiology/joren.py | calibrate | 189 | 205 | 03_CALIBRATION!E6 (CURRENT), F6 (JOREN) |
| CAL-03 | backend/app/modules/calibration/domain.py | _evaluate_submaximal_calibration | 905 | 983 | NOT IMPLEMENTED: protocolsegment evaluator |
| CAL-04 | backend/app/modules/calibration/domain.py | _observation_map | 601 | 627 | NOT IMPLEMENTED |
| CAL-05 | backend/app/modules/calibration/domain.py | _evaluate_run_test | 673 | 740 | NOT IMPLEMENTED: complete test gating |
| CAL-06 | backend/app/modules/calibration/domain.py | _evaluate_bike_ftp_test | 743 | 783 | NOT IMPLEMENTED |
| CAL-07 | backend/app/modules/calibration/domain.py | _evaluate_bike_hr_test | 786 | 822 | NOT IMPLEMENTED |
| CAL-08 | backend/app/modules/calibration/domain.py | _evaluate_swim_css_test | 825 | 890 | NOT IMPLEMENTED |
| CAL-09 | backend/app/modules/calibration/domain.py | validate_test_schedule | 468 | 505 | NOT IMPLEMENTED |
| ZONE-01 | backend/app/modules/physiology/joren.py | threshold_zones | 156 | 186 | 04_ZONES |
| ZONE-02 | backend/app/modules/physiology/joren.py | threshold_zones | 156 | 186 | 04_ZONES |
| ZONE-03 | backend/app/modules/physiology/zones.py | calculate_zone_profile | 450 | 523 | NOT IMPLEMENTED: legacy model sheet |
| ZONE-04 | backend/app/modules/physiology/zones.py | classify_calculated_zone_value | 553 | 592 | 18_ACTUAL_LOAD!G6:G405; alleen CURRENT Phase13 HR-classificatie |
| ZONE-05 | backend/app/modules/physiology/zones.py | classify_zone_value | 697 | 725 | NOT IMPLEMENTED |
| ZONE-06 | backend/app/modules/physiology/zones.py | calculate_karvonen_fallback | 762 | 776 | NOT IMPLEMENTED: historical fallback |
| ZONE-07 | backend/app/modules/physiology/zones.py | assess_heart_rate_tolerance | 170 | 201 | NOT IMPLEMENTED |
| LOAD-01 | backend/app/modules/physiology/joren.py | zone_load | 222 | 269 | 18_ACTUAL_LOAD |
| LOAD-02 | backend/app/modules/physiology/joren.py | zone_load | 222 | 269 | 18_ACTUAL_LOAD |
| LOAD-03 | backend/app/modules/physiology/joren.py | average_hr_zone_load | 296 | 322 | 18_ACTUAL_LOAD |
| LOAD-04 | backend/app/modules/physiology/joren.py | srpe_formula | 272 | 284 | NOT IMPLEMENTED: reference only |
| LOAD-05 | backend/app/modules/physiology/activity.py | calculate_legacy_phase7_rpe_duration_load | 56 | 67 | NOT IMPLEMENTED: historical record path |
| ACT-01 | backend/app/modules/physiology/activity.py | classify_activity_match | 70 | 183 | 16_RPE_AND_OBSERVATIONS |
| ACT-02 | backend/app/modules/activities/service.py | submit_rpe | 135 | 392 | NOT IMPLEMENTED: immutable activity event log |
| CAT-01 | backend/app/modules/workouts/catalog.py | active_catalog | 985 | 1018 | 08_TRAINING_CATALOG |
| CAT-02 | backend/app/modules/workouts/catalog.py | with_current_load | 1021 | 1043 | 08_TRAINING_CATALOG |
| CAT-03 | backend/app/modules/planning/domain.py | eligible_workouts | 533 | 625 | 10_ELIGIBLE_WORKOUTS |
| CAT-04 | backend/app/modules/workouts/catalog.py | as_rpe_guided_template | 325 | 377 | NOT IMPLEMENTED: segment projection |
| PLAN-01 | backend/app/modules/planning/domain.py | resolve_target | 211 | 394 | 19_NEXT_WEEK |
| PLAN-02 | backend/app/modules/planning/domain.py | _race_anchored_phase | 195 | 201 | 09_WEEK_SETUP |
| PLAN-03 | backend/app/modules/planning/domain.py | resolve_target | 211 | 394 | 19_NEXT_WEEK |
| PLAN-04 | backend/app/modules/physiology/progression.py | calculate_42_day_average | 53 | 79 | 19_NEXT_WEEK |
| PLAN-05 | backend/app/modules/physiology/recovery.py | calculate_recovery_target | 78 | 95 | 19_NEXT_WEEK |
| PLAN-06 | backend/app/modules/physiology/taper.py | calculate_taper_target | 87 | 113 | 19_NEXT_WEEK |
| PLAN-07 | backend/app/modules/planning/domain.py | resolve_target | 211 | 394 | 19_NEXT_WEEK |
| PLAN-08 | backend/app/modules/physiology/debt.py | calculate_volume_debt | 54 | 81 | 19_NEXT_WEEK |
| PLAN-09 | backend/app/modules/physiology/progression.py | calculate_progressive_target | 82 | 108 | 19_NEXT_WEEK |
| PLAN-10 | backend/app/modules/planning/domain.py | resolve_target | 211 | 394 | 19_NEXT_WEEK |
| PLAN-11 | backend/app/modules/planning/domain.py | resolve_target | 211 | 394 | NOT IMPLEMENTED: maintenance selector |
| INT-01 | backend/app/modules/planning/domain.py | _workout_intensity | 1300 | 1317 | 17_PLANNED_LOAD |
| INT-02 | backend/app/modules/physiology/debt.py | calculate_reliable_intensity_debt | 108 | 154 | NOT IMPLEMENTED: downstream intensity debt |
| INT-03 | backend/app/modules/physiology/intensity.py | display_time_distribution | 180 | 200 | 17_PLANNED_LOAD |
| INT-04 | backend/app/modules/physiology/intensity.py | intensive_duration_warning | 203 | 213 | NOT IMPLEMENTED |
| SEL-01 | backend/app/modules/planning/domain.py | _selection_policy_valid | 666 | 713 | NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie |
| SEL-02 | backend/app/modules/planning/domain.py | _bounded_selection | 722 | 978 | NOT IMPLEMENTED: automatic search |
| SEL-03 | backend/app/modules/planning/service.py | _prepare_swipe_context | 544 | 664 | NOT IMPLEMENTED: exact swipe composition |
| SEL-04 | backend/app/modules/planning/service.py | _selection_has_completion | 692 | 783 | NOT IMPLEMENTED |
| SEL-05 | backend/app/modules/planning/swipe.py | apply_swipe_decision | 67 | 111 | NOT IMPLEMENTED: immutable action history |
| PLACE-01 | backend/app/modules/physiology/anti_stack.py | find_anti_stack_violations | 56 | 90 | 12_PLACEMENT |
| PLACE-02 | backend/app/modules/planning/domain.py | schedule_workouts | 1132 | 1297 | NOT IMPLEMENTED: automatic placement |
| PLACE-03 | backend/app/modules/planning/domain.py | validate_manual_schedule | 1792 | 1809 | 12_PLACEMENT |
| INJ-01 | backend/app/modules/checkins/domain.py | confirmed_restriction_sets | 89 | 105 | 09_WEEK_SETUP |
| INJ-02 | backend/app/modules/planning/domain.py | _injury_adjusted_target | 438 | 530 | NOT IMPLEMENTED: injury allocation |
| INJ-03 | backend/app/modules/physiology/injury.py | redistribute_confirmed_injury_load | 132 | 226 | NOT IMPLEMENTED: injury allocation |
| INJ-04 | backend/app/modules/planning/domain.py | _injury_adjusted_target | 438 | 530 | NOT IMPLEMENTED |
| INJ-05 | backend/app/modules/planning/domain.py | build_weekly_plan | 1342 | 1789 | NOT IMPLEMENTED: full precedence |
| STATE-01 | backend/app/modules/planning/service.py | approve_plan_proposal | 2727 | 2739 | 14_PLAN_APPROVAL: illustrative only |
| STATE-02 | backend/app/modules/planning/service.py | reject_plan_proposal | 2741 | 2751 | 14_PLAN_APPROVAL: illustrative only |
| STATE-03 | backend/app/modules/planning/repository.py | fetch_load_history | 75 | 80 | 05_HISTORY: explicit manual snapshots |
| WARN-01 | backend/app/modules/planning/domain.py | build_weekly_plan | 1342 | 1789 | NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie |
| VAL-01 | backend/app/modules/physiology/models.py | InternalLoad.__post_init__ | 88 | 90 | input validations; detailed contracts NOT IMPLEMENTED |
| PREC-01 | backend/app/modules/physiology/precedence.py | build_decision_run | 35 | 50 | NOT IMPLEMENTED: 07_RULES_AND_FORMULAS bevat alleen referentie of onvolledige proposalinformatie |

## Volledige ontdekkingslijst

Deze functies zijn gevonden, niet allemaal inhoudelijk geaudit. Handmatige reachability, test-to-branch-koppeling en SQL-conditionanalyse blijven open.

| Discovery ID | Bron | Functie | Regels | Reviewstatus |
| --- | --- | --- | --- | --- |
| FN-0001 | backend/app/modules/physiology/activity.py | calculate_legacy_phase7_rpe_duration_load | 56-67 | OPEN |
| FN-0002 | backend/app/modules/physiology/activity.py | classify_activity_match | 70-183 | OPEN |
| FN-0003 | backend/app/modules/physiology/activity.py | PlannedActivityExpectation.__post_init__ | 41-43 | OPEN |
| FN-0004 | backend/app/modules/physiology/anti_stack.py | find_anti_stack_violations | 56-90 | OPEN |
| FN-0005 | backend/app/modules/physiology/anti_stack.py | ScheduledWorkout.__post_init__ | 33-39 | OPEN |
| FN-0006 | backend/app/modules/physiology/debt.py | calculate_volume_debt | 54-81 | OPEN |
| FN-0007 | backend/app/modules/physiology/debt.py | calculate_intensity_debt | 84-105 | OPEN |
| FN-0008 | backend/app/modules/physiology/debt.py | calculate_reliable_intensity_debt | 108-154 | OPEN |
| FN-0009 | backend/app/modules/physiology/injury.py | redistribute_confirmed_injury_load | 132-226 | OPEN |
| FN-0010 | backend/app/modules/physiology/injury.py | redistribute_injury_load | 229-318 | OPEN |
| FN-0011 | backend/app/modules/physiology/injury.py | apply_mvp_injury_policy | 321-351 | OPEN |
| FN-0012 | backend/app/modules/physiology/injury.py | DisciplineRestriction.__post_init__ | 58-80 | OPEN |
| FN-0013 | backend/app/modules/physiology/injury.py | DisciplineRestriction.self_reported_limited | 83-101 | OPEN |
| FN-0014 | backend/app/modules/physiology/injury.py | DisciplineRestriction.requires_recheck | 103-107 | OPEN |
| FN-0015 | backend/app/modules/physiology/intensity.py | classify_segment | 93-106 | OPEN |
| FN-0016 | backend/app/modules/physiology/intensity.py | classify_workout | 109-134 | OPEN |
| FN-0017 | backend/app/modules/physiology/intensity.py | calculate_time_distribution | 137-177 | OPEN |
| FN-0018 | backend/app/modules/physiology/intensity.py | display_time_distribution | 180-200 | OPEN |
| FN-0019 | backend/app/modules/physiology/intensity.py | intensive_duration_warning | 203-213 | OPEN |
| FN-0020 | backend/app/modules/physiology/intensity.py | IntensitySegment.__post_init__ | 31-41 | OPEN |
| FN-0021 | backend/app/modules/physiology/intensity.py | WorkoutIntensity.__post_init__ | 50-54 | OPEN |
| FN-0022 | backend/app/modules/physiology/joren.py | _nonnegative | 81-83 | OPEN |
| FN-0023 | backend/app/modules/physiology/joren.py | _rpe_index | 86-89 | OPEN |
| FN-0024 | backend/app/modules/physiology/joren.py | rounded | 92-93 | OPEN |
| FN-0025 | backend/app/modules/physiology/joren.py | starting_baseline | 106-129 | OPEN |
| FN-0026 | backend/app/modules/physiology/joren.py | threshold_zones | 156-186 | OPEN |
| FN-0027 | backend/app/modules/physiology/joren.py | calibrate | 189-205 | OPEN |
| FN-0028 | backend/app/modules/physiology/joren.py | zone_load | 222-269 | OPEN |
| FN-0029 | backend/app/modules/physiology/joren.py | srpe_formula | 272-284 | OPEN |
| FN-0030 | backend/app/modules/physiology/joren.py | taper_window | 287-288 | OPEN |
| FN-0031 | backend/app/modules/physiology/joren.py | is_taper_day | 291-293 | OPEN |
| FN-0032 | backend/app/modules/physiology/joren.py | average_hr_zone_load | 296-322 | OPEN |
| FN-0033 | backend/app/modules/physiology/joren.py | IntegerZone.contains | 140-143 | OPEN |
| FN-0034 | backend/app/modules/physiology/models.py | RulesetVersion.__post_init__ | 77-79 | OPEN |
| FN-0035 | backend/app/modules/physiology/models.py | InternalLoad.__post_init__ | 88-90 | OPEN |
| FN-0036 | backend/app/modules/physiology/models.py | DurationMinutes.__post_init__ | 99-101 | OPEN |
| FN-0037 | backend/app/modules/physiology/models.py | Fraction.__post_init__ | 110-112 | OPEN |
| FN-0038 | backend/app/modules/physiology/models.py | RuleEvaluation.__post_init__ | 124-126 | OPEN |
| FN-0039 | backend/app/modules/physiology/precedence.py | order_evaluations | 14-18 | OPEN |
| FN-0040 | backend/app/modules/physiology/precedence.py | first_conflict | 21-32 | OPEN |
| FN-0041 | backend/app/modules/physiology/precedence.py | build_decision_run | 35-50 | OPEN |
| FN-0042 | backend/app/modules/physiology/progression.py | calculate_42_day_average | 53-79 | OPEN |
| FN-0043 | backend/app/modules/physiology/progression.py | calculate_progressive_target | 82-108 | OPEN |
| FN-0044 | backend/app/modules/physiology/progression.py | calculate_legacy_phase3_expected_rpe_duration_load | 111-125 | OPEN |
| FN-0045 | backend/app/modules/physiology/progression.py | WeeklyLoad.__post_init__ | 39-41 | OPEN |
| FN-0046 | backend/app/modules/physiology/recovery.py | forward_mesocycle_phase | 35-46 | OPEN |
| FN-0047 | backend/app/modules/physiology/recovery.py | retrospective_mesocycle_phase | 49-62 | OPEN |
| FN-0048 | backend/app/modules/physiology/recovery.py | resolve_week_phase | 65-75 | OPEN |
| FN-0049 | backend/app/modules/physiology/recovery.py | calculate_recovery_target | 78-95 | OPEN |
| FN-0050 | backend/app/modules/physiology/rpe_zones.py | rpe_zone | 88-98 | OPEN |
| FN-0051 | backend/app/modules/physiology/rpe_zones.py | zone_for_rpe_range | 101-106 | OPEN |
| FN-0052 | backend/app/modules/physiology/rpe_zones.py | zone_for_rpe_value | 109-121 | OPEN |
| FN-0053 | backend/app/modules/physiology/rpe_zones.py | rpe_description | 166-170 | OPEN |
| FN-0054 | backend/app/modules/physiology/rpe_zones.py | RpeZoneDefinition.rpe_label | 19-24 | OPEN |
| FN-0055 | backend/app/modules/physiology/rpe_zones.py | RpeZoneDefinition.display_label | 27-28 | OPEN |
| FN-0056 | backend/app/modules/physiology/specification.py | PhysiologyProductionReview.__post_init__ | 35-41 | OPEN |
| FN-0057 | backend/app/modules/physiology/specification.py | PhysiologySpecification.require_approved | 57-66 | OPEN |
| FN-0058 | backend/app/modules/physiology/specification.py | PhysiologySpecification.require_production_review | 68-81 | OPEN |
| FN-0059 | backend/app/modules/physiology/taper.py | calculate_taper_baseline | 70-84 | OPEN |
| FN-0060 | backend/app/modules/physiology/taper.py | calculate_taper_target | 87-113 | OPEN |
| FN-0061 | backend/app/modules/physiology/taper.py | select_controlling_race | 116-132 | OPEN |
| FN-0062 | backend/app/modules/physiology/taper.py | athlete_week_bounds | 135-147 | OPEN |
| FN-0063 | backend/app/modules/physiology/taper.py | RaceEvent.__post_init__ | 53-57 | OPEN |
| FN-0064 | backend/app/modules/physiology/zones.py | assess_heart_rate_tolerance | 170-201 | OPEN |
| FN-0065 | backend/app/modules/physiology/zones.py | _karvonen_result | 356-392 | OPEN |
| FN-0066 | backend/app/modules/physiology/zones.py | metric_direction | 395-397 | OPEN |
| FN-0067 | backend/app/modules/physiology/zones.py | round_zone_boundary | 400-404 | OPEN |
| FN-0068 | backend/app/modules/physiology/zones.py | validate_calculated_zone_profile | 407-447 | OPEN |
| FN-0069 | backend/app/modules/physiology/zones.py | calculate_zone_profile | 450-523 | OPEN |
| FN-0070 | backend/app/modules/physiology/zones.py | calculate_zone_profiles | 526-550 | OPEN |
| FN-0071 | backend/app/modules/physiology/zones.py | classify_calculated_zone_value | 553-592 | OPEN |
| FN-0072 | backend/app/modules/physiology/zones.py | classify_calculated_zone_speed | 595-613 | OPEN |
| FN-0073 | backend/app/modules/physiology/zones.py | assess_metric_with_soft_limits | 616-650 | OPEN |
| FN-0074 | backend/app/modules/physiology/zones.py | validate_zone_boundaries | 653-674 | OPEN |
| FN-0075 | backend/app/modules/physiology/zones.py | validate_zone_profile | 677-694 | OPEN |
| FN-0076 | backend/app/modules/physiology/zones.py | classify_zone_value | 697-725 | OPEN |
| FN-0077 | backend/app/modules/physiology/zones.py | parse_pace_metric | 728-748 | OPEN |
| FN-0078 | backend/app/modules/physiology/zones.py | format_pace_metric | 751-759 | OPEN |
| FN-0079 | backend/app/modules/physiology/zones.py | calculate_karvonen_fallback | 762-776 | OPEN |
| FN-0080 | backend/app/modules/physiology/zones.py | calculate_age_220_karvonen_fallback | 779-797 | OPEN |
| FN-0081 | backend/app/modules/physiology/zones.py | ZoneMetric.__post_init__ | 212-218 | OPEN |
| FN-0082 | backend/app/modules/physiology/zones.py | ClinicalRange.__post_init__ | 228-235 | OPEN |
| FN-0083 | backend/app/modules/physiology/zones.py | ZoneBoundary.__post_init__ | 256-265 | OPEN |
| FN-0084 | backend/app/modules/physiology/zones.py | CalculatedZoneBoundary.__post_init__ | 276-290 | OPEN |
| FN-0085 | backend/app/modules/physiology/zones.py | ZoneSoftRangeRule.__post_init__ | 327-341 | OPEN |
| FN-0086 | backend/app/modules/planning/domain.py | _training_phase | 187-192 | OPEN |
| FN-0087 | backend/app/modules/planning/domain.py | _race_anchored_phase | 195-201 | OPEN |
| FN-0088 | backend/app/modules/planning/domain.py | _build_week | 204-208 | OPEN |
| FN-0089 | backend/app/modules/planning/domain.py | resolve_target | 211-394 | OPEN |
| FN-0090 | backend/app/modules/planning/domain.py | _desired_high_fraction | 397-435 | OPEN |
| FN-0091 | backend/app/modules/planning/domain.py | _injury_adjusted_target | 438-530 | OPEN |
| FN-0092 | backend/app/modules/planning/domain.py | eligible_workouts | 533-625 | OPEN |
| FN-0093 | backend/app/modules/planning/domain.py | _selection_key | 628-663 | OPEN |
| FN-0094 | backend/app/modules/planning/domain.py | _selection_policy_valid | 666-713 | OPEN |
| FN-0095 | backend/app/modules/planning/domain.py | _has_zone_five | 716-719 | OPEN |
| FN-0096 | backend/app/modules/planning/domain.py | _bounded_selection | 722-978 | OPEN |
| FN-0097 | backend/app/modules/planning/domain.py | select_workouts | 981-1081 | OPEN |
| FN-0098 | backend/app/modules/planning/domain.py | remaining_workout_deck | 1084-1114 | OPEN |
| FN-0099 | backend/app/modules/planning/domain.py | canonical_schedule_instant | 1117-1129 | OPEN |
| FN-0100 | backend/app/modules/planning/domain.py | schedule_workouts | 1132-1297 | OPEN |
| FN-0101 | backend/app/modules/planning/domain.py | _workout_intensity | 1300-1317 | OPEN |
| FN-0102 | backend/app/modules/planning/domain.py | _schedule_is_feasible | 1320-1339 | OPEN |
| FN-0103 | backend/app/modules/planning/domain.py | build_weekly_plan | 1342-1789 | OPEN |
| FN-0104 | backend/app/modules/planning/domain.py | validate_manual_schedule | 1792-1809 | OPEN |
| FN-0105 | backend/app/modules/planning/domain.py | as_utc | 1812-1816 | OPEN |
| FN-0106 | backend/app/modules/planning/domain.py | PlanningConstraintError.__init__ | 68-70 | OPEN |
| FN-0107 | backend/app/modules/planning/domain.py | schedule_workouts.maximum_consecutive_rest_days | 1193-1202 | OPEN |
| FN-0108 | backend/app/modules/planning/domain.py | schedule_workouts.rest_limit_is_feasible | 1204-1219 | OPEN |
| FN-0109 | backend/app/modules/planning/domain.py | schedule_workouts.find_schedule | 1228-1289 | OPEN |
| FN-0110 | backend/app/modules/planning/repository.py | PlanningRepositoryConflictError.__init__ | 30-36 | OPEN |
| FN-0111 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_initial_request | 46-51 | OPEN |
| FN-0112 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_plan_context | 53-58 | OPEN |
| FN-0113 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_plan_revision_context | 60-66 | OPEN |
| FN-0114 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_previous_available_dates | 68-73 | OPEN |
| FN-0115 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_load_history | 75-80 | OPEN |
| FN-0116 | backend/app/modules/planning/repository.py | PlanningRepository.create_plan_proposal | 82-87 | OPEN |
| FN-0117 | backend/app/modules/planning/repository.py | PlanningRepository.create_swipe_draft | 89-94 | OPEN |
| FN-0118 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_swipe_draft | 96-101 | OPEN |
| FN-0119 | backend/app/modules/planning/repository.py | PlanningRepository.update_swipe_draft | 103-110 | OPEN |
| FN-0120 | backend/app/modules/planning/repository.py | PlanningRepository.set_plan_proposal_explanation | 112-118 | OPEN |
| FN-0121 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_plan | 120-126 | OPEN |
| FN-0122 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_proposal | 128-133 | OPEN |
| FN-0123 | backend/app/modules/planning/repository.py | PlanningRepository.list_proposals | 135-140 | OPEN |
| FN-0124 | backend/app/modules/planning/repository.py | PlanningRepository.approve_plan_proposal | 142-148 | OPEN |
| FN-0125 | backend/app/modules/planning/repository.py | PlanningRepository.reject_plan_proposal | 150-155 | OPEN |
| FN-0126 | backend/app/modules/planning/repository.py | PlanningRepository.move_planned_workout | 157-165 | OPEN |
| FN-0127 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_workout_context | 167-172 | OPEN |
| FN-0128 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_calendar | 174-180 | OPEN |
| FN-0129 | backend/app/modules/planning/repository.py | PlanningRepository.fetch_calendar_rest_days | 182-188 | OPEN |
| FN-0130 | backend/app/modules/planning/repository.py | PlanningRepository.aclose | 190-191 | OPEN |
| FN-0131 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.__init__ | 197-210 | OPEN |
| FN-0132 | backend/app/modules/planning/repository.py | SupabasePlanningRepository._rpc_athlete_id | 212-216 | OPEN |
| FN-0133 | backend/app/modules/planning/repository.py | SupabasePlanningRepository._planning_eligibility_context | 218-230 | OPEN |
| FN-0134 | backend/app/modules/planning/repository.py | SupabasePlanningRepository._headers | 232-243 | OPEN |
| FN-0135 | backend/app/modules/planning/repository.py | SupabasePlanningRepository._request | 245-319 | OPEN |
| FN-0136 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_initial_request | 321-370 | OPEN |
| FN-0137 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_plan_context | 372-390 | OPEN |
| FN-0138 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_plan_revision_context | 392-412 | OPEN |
| FN-0139 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_previous_available_dates | 414-431 | OPEN |
| FN-0140 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_load_history | 433-454 | OPEN |
| FN-0141 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.create_plan_proposal | 456-473 | OPEN |
| FN-0142 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.create_swipe_draft | 475-492 | OPEN |
| FN-0143 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_swipe_draft | 494-524 | OPEN |
| FN-0144 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.update_swipe_draft | 526-547 | OPEN |
| FN-0145 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.set_plan_proposal_explanation | 549-568 | OPEN |
| FN-0146 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_plan | 570-587 | OPEN |
| FN-0147 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_proposal | 589-611 | OPEN |
| FN-0148 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.list_proposals | 613-637 | OPEN |
| FN-0149 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.approve_plan_proposal | 639-656 | OPEN |
| FN-0150 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.reject_plan_proposal | 658-671 | OPEN |
| FN-0151 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.move_planned_workout | 673-696 | OPEN |
| FN-0152 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_workout_context | 698-711 | OPEN |
| FN-0153 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_calendar | 713-730 | OPEN |
| FN-0154 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.fetch_calendar_rest_days | 732-749 | OPEN |
| FN-0155 | backend/app/modules/planning/repository.py | SupabasePlanningRepository.aclose | 751-753 | OPEN |
| FN-0156 | backend/app/modules/planning/router.py | get_planning_repository | 64-67 | OPEN |
| FN-0157 | backend/app/modules/planning/router.py | get_planning_catalog_provider | 70-73 | OPEN |
| FN-0158 | backend/app/modules/planning/router.py | get_weekly_plan_coach | 76-79 | OPEN |
| FN-0159 | backend/app/modules/planning/router.py | get_planning_service | 82-94 | OPEN |
| FN-0160 | backend/app/modules/planning/router.py | raise_planning_error | 97-133 | OPEN |
| FN-0161 | backend/app/modules/planning/router.py | create_initial_weekly_plan_proposal | 142-156 | OPEN |
| FN-0162 | backend/app/modules/planning/router.py | create_swipe_week_draft | 165-205 | OPEN |
| FN-0163 | backend/app/modules/planning/router.py | get_swipe_week_draft | 213-228 | OPEN |
| FN-0164 | backend/app/modules/planning/router.py | transition_swipe_week_draft | 236-253 | OPEN |
| FN-0165 | backend/app/modules/planning/router.py | place_swipe_week_workout | 261-280 | OPEN |
| FN-0166 | backend/app/modules/planning/router.py | submit_swipe_week_draft | 289-306 | OPEN |
| FN-0167 | backend/app/modules/planning/router.py | get_weekly_plan | 314-325 | OPEN |
| FN-0168 | backend/app/modules/planning/router.py | get_weekly_plan_deck | 333-349 | OPEN |
| FN-0169 | backend/app/modules/planning/router.py | create_schedule_proposal | 358-374 | OPEN |
| FN-0170 | backend/app/modules/planning/router.py | get_pending_workout_alternatives | 382-400 | OPEN |
| FN-0171 | backend/app/modules/planning/router.py | edit_pending_workout | 409-427 | OPEN |
| FN-0172 | backend/app/modules/planning/router.py | validate_weekly_plan | 435-446 | OPEN |
| FN-0173 | backend/app/modules/planning/router.py | move_planned_workout | 454-470 | OPEN |
| FN-0174 | backend/app/modules/planning/router.py | get_calendar | 478-493 | OPEN |
| FN-0175 | backend/app/modules/planning/router.py | list_change_proposals | 501-514 | OPEN |
| FN-0176 | backend/app/modules/planning/router.py | get_change_proposal | 522-532 | OPEN |
| FN-0177 | backend/app/modules/planning/schemas.py | WeeklyPlanProposalRequest.validate_week_and_selection | 52-87 | OPEN |
| FN-0178 | backend/app/modules/planning/schemas.py | ScheduleProposalRequest.validate_selection | 108-136 | OPEN |
| FN-0179 | backend/app/modules/planning/schemas.py | PlannedWorkoutResponse.derive_rpe_zones | 178-180 | OPEN |
| FN-0180 | backend/app/modules/planning/schemas.py | WeeklyPlanResponse.add_stable_intensity_display | 255-290 | OPEN |
| FN-0181 | backend/app/modules/planning/schemas.py | WorkoutDeckItemResponse.derive_rpe_zones | 336-338 | OPEN |
| FN-0182 | backend/app/modules/planning/schemas.py | SwipeDraftCreateRequest.validate_draft_context | 360-380 | OPEN |
| FN-0183 | backend/app/modules/planning/schemas.py | SwipeDraftTransitionRequest.validate_candidate_binding | 392-401 | OPEN |
| FN-0184 | backend/app/modules/planning/schemas.py | PlanValidationRequest.require_unique_workouts | 474-478 | OPEN |
| FN-0185 | backend/app/modules/planning/schemas.py | ProposalApprovalRequest.require_one_precondition | 530-539 | OPEN |
| FN-0186 | backend/app/modules/planning/service.py | PlanningCatalogProvider.fetch_catalog | 115-116 | OPEN |
| FN-0187 | backend/app/modules/planning/service.py | PlanningCatalogProvider.aclose | 118-119 | OPEN |
| FN-0188 | backend/app/modules/planning/service.py | SupabasePlanningCatalogProvider.__init__ | 125-126 | OPEN |
| FN-0189 | backend/app/modules/planning/service.py | SupabasePlanningCatalogProvider.fetch_catalog | 128-129 | OPEN |
| FN-0190 | backend/app/modules/planning/service.py | SupabasePlanningCatalogProvider.aclose | 131-132 | OPEN |
| FN-0191 | backend/app/modules/planning/service.py | PlanningService.__init__ | 172-180 | OPEN |
| FN-0192 | backend/app/modules/planning/service.py | PlanningService._deck_item | 183-246 | OPEN |
| FN-0193 | backend/app/modules/planning/service.py | PlanningService._coach_facts | 249-276 | OPEN |
| FN-0194 | backend/app/modules/planning/service.py | PlanningService._planning_input | 279-337 | OPEN |
| FN-0195 | backend/app/modules/planning/service.py | PlanningService._context_values | 340-441 | OPEN |
| FN-0196 | backend/app/modules/planning/service.py | PlanningService._onboarding_baseline | 444-473 | OPEN |
| FN-0197 | backend/app/modules/planning/service.py | PlanningService._load_samples | 476-542 | OPEN |
| FN-0198 | backend/app/modules/planning/service.py | PlanningService._prepare_swipe_context | 544-664 | OPEN |
| FN-0199 | backend/app/modules/planning/service.py | PlanningService._swipe_history | 667-690 | OPEN |
| FN-0200 | backend/app/modules/planning/service.py | PlanningService._selection_has_completion | 692-783 | OPEN |
| FN-0201 | backend/app/modules/planning/service.py | PlanningService._next_swipe_candidate | 785-809 | OPEN |
| FN-0202 | backend/app/modules/planning/service.py | PlanningService._swipe_update_payload | 812-850 | OPEN |
| FN-0203 | backend/app/modules/planning/service.py | PlanningService._swipe_response | 852-1009 | OPEN |
| FN-0204 | backend/app/modules/planning/service.py | PlanningService._generation_fingerprint | 1012-1065 | OPEN |
| FN-0205 | backend/app/modules/planning/service.py | PlanningService._proposal_payload | 1068-1157 | OPEN |
| FN-0206 | backend/app/modules/planning/service.py | PlanningService._build_and_persist | 1159-1295 | OPEN |
| FN-0207 | backend/app/modules/planning/service.py | PlanningService.generate_initial_proposal | 1297-1356 | OPEN |
| FN-0208 | backend/app/modules/planning/service.py | PlanningService._load_swipe_draft_context | 1358-1458 | OPEN |
| FN-0209 | backend/app/modules/planning/service.py | PlanningService.create_swipe_draft | 1460-1575 | OPEN |
| FN-0210 | backend/app/modules/planning/service.py | PlanningService.get_swipe_draft | 1577-1588 | OPEN |
| FN-0211 | backend/app/modules/planning/service.py | PlanningService.transition_swipe_draft | 1590-1735 | OPEN |
| FN-0212 | backend/app/modules/planning/service.py | PlanningService.place_swipe_workout | 1737-1823 | OPEN |
| FN-0213 | backend/app/modules/planning/service.py | PlanningService.submit_swipe_draft | 1825-1958 | OPEN |
| FN-0214 | backend/app/modules/planning/service.py | PlanningService.generate_schedule_proposal | 1960-2005 | OPEN |
| FN-0215 | backend/app/modules/planning/service.py | PlanningService.generate_integrated_field_test_proposal | 2007-2113 | OPEN |
| FN-0216 | backend/app/modules/planning/service.py | PlanningService.generate_checkin_proposal | 2115-2167 | OPEN |
| FN-0217 | backend/app/modules/planning/service.py | PlanningService.get_plan | 2169-2177 | OPEN |
| FN-0218 | backend/app/modules/planning/service.py | PlanningService.get_deck | 2179-2243 | OPEN |
| FN-0219 | backend/app/modules/planning/service.py | PlanningService._pending_revision_edit_state | 2245-2297 | OPEN |
| FN-0220 | backend/app/modules/planning/service.py | PlanningService._candidate_edit_is_valid | 2299-2340 | OPEN |
| FN-0221 | backend/app/modules/planning/service.py | PlanningService.get_pending_workout_alternatives | 2342-2438 | OPEN |
| FN-0222 | backend/app/modules/planning/service.py | PlanningService.edit_pending_workout | 2440-2520 | OPEN |
| FN-0223 | backend/app/modules/planning/service.py | PlanningService.validate_layout | 2522-2570 | OPEN |
| FN-0224 | backend/app/modules/planning/service.py | PlanningService.move_workout | 2572-2670 | OPEN |
| FN-0225 | backend/app/modules/planning/service.py | PlanningService.get_calendar | 2672-2701 | OPEN |
| FN-0226 | backend/app/modules/planning/service.py | PlanningService.proposal_kind | 2703-2706 | OPEN |
| FN-0227 | backend/app/modules/planning/service.py | PlanningService.list_proposals | 2708-2716 | OPEN |
| FN-0228 | backend/app/modules/planning/service.py | PlanningService.get_proposal | 2718-2725 | OPEN |
| FN-0229 | backend/app/modules/planning/service.py | PlanningService.approve_plan_proposal | 2727-2739 | OPEN |
| FN-0230 | backend/app/modules/planning/service.py | PlanningService.reject_plan_proposal | 2741-2751 | OPEN |
| FN-0231 | backend/app/modules/planning/service.py | PlanningService.get_pending_workout_alternatives.candidate_is_valid | 2391-2410 | OPEN |
| FN-0232 | backend/app/modules/planning/swipe.py | apply_swipe_decision | 67-111 | OPEN |
| FN-0233 | backend/app/modules/planning/swipe.py | undo_last_swipe | 114-122 | OPEN |
| FN-0234 | backend/app/modules/planning/swipe.py | reset_passed_cards | 125-134 | OPEN |
| FN-0235 | backend/app/modules/planning/swipe.py | discipline_composition | 137-145 | OPEN |
| FN-0236 | backend/app/modules/planning/swipe.py | composition_can_extend | 148-157 | OPEN |
| FN-0237 | backend/app/modules/planning/swipe.py | composition_is_complete | 160-167 | OPEN |
| FN-0238 | backend/app/modules/planning/swipe.py | SwipeSelectionState.accepted_template_ids | 35-40 | OPEN |
| FN-0239 | backend/app/modules/planning/swipe.py | SwipeSelectionState.accepted_occurrence_ids | 43-48 | OPEN |
| FN-0240 | backend/app/modules/planning/swipe.py | SwipeSelectionState.passed_template_ids | 51-56 | OPEN |
| FN-0241 | backend/app/modules/planning/swipe.py | SwipeSelectionState.passed_occurrence_ids | 59-64 | OPEN |
| FN-0242 | backend/app/modules/calibration/domain.py | numeric_zone_visibility | 286-303 | OPEN |
| FN-0243 | backend/app/modules/calibration/domain.py | _segment | 306-326 | OPEN |
| FN-0244 | backend/app/modules/calibration/domain.py | validate_test_schedule | 468-505 | OPEN |
| FN-0245 | backend/app/modules/calibration/domain.py | protocols_for_discipline | 508-518 | OPEN |
| FN-0246 | backend/app/modules/calibration/domain.py | is_current_protocol | 521-535 | OPEN |
| FN-0247 | backend/app/modules/calibration/domain.py | pace_seconds_per_100m | 538-548 | OPEN |
| FN-0248 | backend/app/modules/calibration/domain.py | _result | 551-598 | OPEN |
| FN-0249 | backend/app/modules/calibration/domain.py | _observation_map | 601-627 | OPEN |
| FN-0250 | backend/app/modules/calibration/domain.py | _common_reasons | 630-665 | OPEN |
| FN-0251 | backend/app/modules/calibration/domain.py | _whole_seconds | 668-670 | OPEN |
| FN-0252 | backend/app/modules/calibration/domain.py | _evaluate_run_test | 673-740 | OPEN |
| FN-0253 | backend/app/modules/calibration/domain.py | _evaluate_bike_ftp_test | 743-783 | OPEN |
| FN-0254 | backend/app/modules/calibration/domain.py | _evaluate_bike_hr_test | 786-822 | OPEN |
| FN-0255 | backend/app/modules/calibration/domain.py | _evaluate_swim_css_test | 825-890 | OPEN |
| FN-0256 | backend/app/modules/calibration/domain.py | _has_objective_metrics | 893-902 | OPEN |
| FN-0257 | backend/app/modules/calibration/domain.py | _evaluate_submaximal_calibration | 905-983 | OPEN |
| FN-0258 | backend/app/modules/calibration/domain.py | evaluate_protocol | 986-1020 | OPEN |
| FN-0259 | backend/app/modules/calibration/domain.py | ProtocolSegment.__post_init__ | 147-148 | OPEN |
| FN-0260 | backend/app/modules/calibration/domain.py | SwimRepetition.__post_init__ | 175-181 | OPEN |
| FN-0261 | backend/app/modules/calibration/domain.py | CalibrationObservation.__post_init__ | 216-248 | OPEN |
| FN-0262 | backend/app/modules/calibration/repository.py | CalibrationRepository.save_setup | 40-45 | OPEN |
| FN-0263 | backend/app/modules/calibration/repository.py | CalibrationRepository.save_observation | 47-53 | OPEN |
| FN-0264 | backend/app/modules/calibration/repository.py | CalibrationRepository.list_observations | 55-62 | OPEN |
| FN-0265 | backend/app/modules/calibration/repository.py | CalibrationRepository.save_evaluation | 64-70 | OPEN |
| FN-0266 | backend/app/modules/calibration/repository.py | CalibrationRepository.get_evaluation | 72-78 | OPEN |
| FN-0267 | backend/app/modules/calibration/repository.py | CalibrationRepository.save_calculated_zone_profile | 80-85 | OPEN |
| FN-0268 | backend/app/modules/calibration/repository.py | CalibrationRepository.reject_threshold | 87-92 | OPEN |
| FN-0269 | backend/app/modules/calibration/repository.py | CalibrationRepository.fetch_status | 94-99 | OPEN |
| FN-0270 | backend/app/modules/calibration/repository.py | CalibrationRepository.fetch_athlete_timezone | 101-106 | OPEN |
| FN-0271 | backend/app/modules/calibration/repository.py | CalibrationRepository.create_test_assignment | 108-113 | OPEN |
| FN-0272 | backend/app/modules/calibration/repository.py | CalibrationRepository.save_integrated_test_assignment | 115-120 | OPEN |
| FN-0273 | backend/app/modules/calibration/repository.py | CalibrationRepository.approve_test_assignment | 122-128 | OPEN |
| FN-0274 | backend/app/modules/calibration/repository.py | CalibrationRepository.reject_test_assignment | 130-135 | OPEN |
| FN-0275 | backend/app/modules/calibration/repository.py | CalibrationRepository.fetch_zone_profile_state | 137-142 | OPEN |
| FN-0276 | backend/app/modules/calibration/repository.py | CalibrationRepository.aclose | 144-145 | OPEN |
| FN-0277 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.__init__ | 151-164 | OPEN |
| FN-0278 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository._rpc_athlete_id | 166-170 | OPEN |
| FN-0279 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository._headers | 172-180 | OPEN |
| FN-0280 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository._service_headers | 182-189 | OPEN |
| FN-0281 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository._request | 191-241 | OPEN |
| FN-0282 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository._select | 243-262 | OPEN |
| FN-0283 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.save_setup | 264-277 | OPEN |
| FN-0284 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.save_observation | 279-293 | OPEN |
| FN-0285 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.list_observations | 295-320 | OPEN |
| FN-0286 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.save_evaluation | 322-342 | OPEN |
| FN-0287 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.get_evaluation | 344-358 | OPEN |
| FN-0288 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.save_calculated_zone_profile | 360-378 | OPEN |
| FN-0289 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.reject_threshold | 380-398 | OPEN |
| FN-0290 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.fetch_status | 400-439 | OPEN |
| FN-0291 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.fetch_athlete_timezone | 441-459 | OPEN |
| FN-0292 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.create_test_assignment | 461-474 | OPEN |
| FN-0293 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.save_integrated_test_assignment | 476-489 | OPEN |
| FN-0294 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.approve_test_assignment | 491-508 | OPEN |
| FN-0295 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.reject_test_assignment | 510-523 | OPEN |
| FN-0296 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.fetch_zone_profile_state | 525-606 | OPEN |
| FN-0297 | backend/app/modules/calibration/repository.py | SupabaseCalibrationRepository.aclose | 608-610 | OPEN |
| FN-0298 | backend/app/modules/calibration/router.py | get_calibration_repository | 61-63 | OPEN |
| FN-0299 | backend/app/modules/calibration/router.py | get_calibration_service | 66-72 | OPEN |
| FN-0300 | backend/app/modules/calibration/router.py | _raise_public_error | 75-101 | OPEN |
| FN-0301 | backend/app/modules/calibration/router.py | get_zone_options | 109-115 | OPEN |
| FN-0302 | backend/app/modules/calibration/router.py | save_discipline_setup | 123-134 | OPEN |
| FN-0303 | backend/app/modules/calibration/router.py | get_calibration_protocols | 142-148 | OPEN |
| FN-0304 | backend/app/modules/calibration/router.py | save_calibration_observation | 157-167 | OPEN |
| FN-0305 | backend/app/modules/calibration/router.py | evaluate_calibration | 175-189 | OPEN |
| FN-0306 | backend/app/modules/calibration/router.py | confirm_calibration_threshold | 197-213 | OPEN |
| FN-0307 | backend/app/modules/calibration/router.py | reject_calibration_threshold | 221-230 | OPEN |
| FN-0308 | backend/app/modules/calibration/router.py | get_calibration_status | 238-247 | OPEN |
| FN-0309 | backend/app/modules/calibration/router.py | schedule_field_test | 256-302 | OPEN |
| FN-0310 | backend/app/modules/calibration/router.py | approve_field_test | 310-325 | OPEN |
| FN-0311 | backend/app/modules/calibration/router.py | reject_field_test | 333-343 | OPEN |
| FN-0312 | backend/app/modules/calibration/router.py | get_zone_profile_state | 351-360 | OPEN |
| FN-0313 | backend/app/modules/calibration/schemas.py | KnownBoundaryInput.validate_width | 50-53 | OPEN |
| FN-0314 | backend/app/modules/calibration/schemas.py | KnownValuesSetup.require_at_least_one_value | 74-77 | OPEN |
| FN-0315 | backend/app/modules/calibration/schemas.py | CalibrationObservationCreate.require_timezone | 229-232 | OPEN |
| FN-0316 | backend/app/modules/calibration/schemas.py | FieldTestSchedulingRequest.require_exact_plan_reference | 342-350 | OPEN |
| FN-0317 | backend/app/modules/calibration/service.py | _current_mvp_guidance_modes | 87-105 | OPEN |
| FN-0318 | backend/app/modules/calibration/service.py | is_current_mvp_setup_values | 108-140 | OPEN |
| FN-0319 | backend/app/modules/calibration/service.py | is_current_mvp_setup | 143-150 | OPEN |
| FN-0320 | backend/app/modules/calibration/service.py | _require_current_mvp_field_test | 153-166 | OPEN |
| FN-0321 | backend/app/modules/calibration/service.py | _fingerprint | 169-176 | OPEN |
| FN-0322 | backend/app/modules/calibration/service.py | _decimal | 1110-1111 | OPEN |
| FN-0323 | backend/app/modules/calibration/service.py | CalibrationService.__init__ | 182-183 | OPEN |
| FN-0324 | backend/app/modules/calibration/service.py | CalibrationService.validate_test_scheduling_request | 186-200 | OPEN |
| FN-0325 | backend/app/modules/calibration/service.py | CalibrationService.zone_options | 203-239 | OPEN |
| FN-0326 | backend/app/modules/calibration/service.py | CalibrationService.protocols | 242-290 | OPEN |
| FN-0327 | backend/app/modules/calibration/service.py | CalibrationService._validate_known_values | 293-339 | OPEN |
| FN-0328 | backend/app/modules/calibration/service.py | CalibrationService._setup_values | 342-437 | OPEN |
| FN-0329 | backend/app/modules/calibration/service.py | CalibrationService.save_setup | 439-447 | OPEN |
| FN-0330 | backend/app/modules/calibration/service.py | CalibrationService._discipline_setup_response | 450-453 | OPEN |
| FN-0331 | backend/app/modules/calibration/service.py | CalibrationService._evaluation_response | 456-464 | OPEN |
| FN-0332 | backend/app/modules/calibration/service.py | CalibrationService._threshold_decision_response | 467-474 | OPEN |
| FN-0333 | backend/app/modules/calibration/service.py | CalibrationService._zone_profile_values | 477-501 | OPEN |
| FN-0334 | backend/app/modules/calibration/service.py | CalibrationService._observation_response | 504-507 | OPEN |
| FN-0335 | backend/app/modules/calibration/service.py | CalibrationService._domain_observation | 510-559 | OPEN |
| FN-0336 | backend/app/modules/calibration/service.py | CalibrationService._validate_observation_protocol | 562-625 | OPEN |
| FN-0337 | backend/app/modules/calibration/service.py | CalibrationService.save_observation | 627-640 | OPEN |
| FN-0338 | backend/app/modules/calibration/service.py | CalibrationService.evaluate | 642-706 | OPEN |
| FN-0339 | backend/app/modules/calibration/service.py | CalibrationService.confirm_threshold | 708-776 | OPEN |
| FN-0340 | backend/app/modules/calibration/service.py | CalibrationService.reject_threshold | 778-788 | OPEN |
| FN-0341 | backend/app/modules/calibration/service.py | CalibrationService._test_assignment_response | 791-810 | OPEN |
| FN-0342 | backend/app/modules/calibration/service.py | CalibrationService.schedule_standalone_test | 812-852 | OPEN |
| FN-0343 | backend/app/modules/calibration/service.py | CalibrationService.save_integrated_test | 854-884 | OPEN |
| FN-0344 | backend/app/modules/calibration/service.py | CalibrationService.approve_test_assignment | 886-897 | OPEN |
| FN-0345 | backend/app/modules/calibration/service.py | CalibrationService.reject_test_assignment | 899-908 | OPEN |
| FN-0346 | backend/app/modules/calibration/service.py | CalibrationService._profile_snapshot | 911-968 | OPEN |
| FN-0347 | backend/app/modules/calibration/service.py | CalibrationService.zone_profile_state | 970-1080 | OPEN |
| FN-0348 | backend/app/modules/calibration/service.py | CalibrationService.status | 1082-1107 | OPEN |
| FN-0349 | backend/app/modules/calibration/service.py | CalibrationService.zone_profile_state.snapshot | 1040-1052 | OPEN |
| FN-0350 | backend/app/modules/activities/repository.py | ActivityRepositoryConflictError.__init__ | 29-31 | OPEN |
| FN-0351 | backend/app/modules/activities/repository.py | ActivityRepository.create_activity | 41-47 | OPEN |
| FN-0352 | backend/app/modules/activities/repository.py | ActivityRepository.fetch_activity | 49-51 | OPEN |
| FN-0353 | backend/app/modules/activities/repository.py | ActivityRepository.list_activities | 53-58 | OPEN |
| FN-0354 | backend/app/modules/activities/repository.py | ActivityRepository.fetch_processing_context | 60-64 | OPEN |
| FN-0355 | backend/app/modules/activities/repository.py | ActivityRepository.save_rpe_heart_rate_observation | 66-71 | OPEN |
| FN-0356 | backend/app/modules/activities/repository.py | ActivityRepository.complete_activity_rpe | 73-78 | OPEN |
| FN-0357 | backend/app/modules/activities/repository.py | ActivityRepository.revise_activity_rpe | 80-85 | OPEN |
| FN-0358 | backend/app/modules/activities/repository.py | ActivityRepository.confirm_planned_workout_match | 87-92 | OPEN |
| FN-0359 | backend/app/modules/activities/repository.py | ActivityRepository.aclose | 94-94 | OPEN |
| FN-0360 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.__init__ | 100-113 | OPEN |
| FN-0361 | backend/app/modules/activities/repository.py | SupabaseActivityRepository._rpc_athlete_id | 115-119 | OPEN |
| FN-0362 | backend/app/modules/activities/repository.py | SupabaseActivityRepository._headers | 121-134 | OPEN |
| FN-0363 | backend/app/modules/activities/repository.py | SupabaseActivityRepository._request | 136-192 | OPEN |
| FN-0364 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.create_activity | 194-224 | OPEN |
| FN-0365 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.save_rpe_heart_rate_observation | 226-242 | OPEN |
| FN-0366 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.fetch_activity | 244-253 | OPEN |
| FN-0367 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.list_activities | 255-269 | OPEN |
| FN-0368 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.fetch_processing_context | 271-288 | OPEN |
| FN-0369 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.complete_activity_rpe | 290-309 | OPEN |
| FN-0370 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.revise_activity_rpe | 311-330 | OPEN |
| FN-0371 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.confirm_planned_workout_match | 332-349 | OPEN |
| FN-0372 | backend/app/modules/activities/repository.py | SupabaseActivityRepository.aclose | 351-353 | OPEN |
| FN-0373 | backend/app/modules/activities/router.py | get_activity_repository | 45-47 | OPEN |
| FN-0374 | backend/app/modules/activities/router.py | get_activity_service | 50-53 | OPEN |
| FN-0375 | backend/app/modules/activities/router.py | _raise_public_error | 56-114 | OPEN |
| FN-0376 | backend/app/modules/activities/router.py | create_activity | 123-134 | OPEN |
| FN-0377 | backend/app/modules/activities/router.py | list_activities | 142-150 | OPEN |
| FN-0378 | backend/app/modules/activities/router.py | list_pending_rpe | 158-166 | OPEN |
| FN-0379 | backend/app/modules/activities/router.py | get_activity | 174-183 | OPEN |
| FN-0380 | backend/app/modules/activities/router.py | submit_activity_rpe | 191-200 | OPEN |
| FN-0381 | backend/app/modules/activities/router.py | confirm_activity_planned_workout_match | 208-218 | OPEN |
| FN-0382 | backend/app/modules/activities/schemas.py | ActivityMetricInput.validate_metric_relationships | 38-75 | OPEN |
| FN-0383 | backend/app/modules/activities/schemas.py | ActivitySummaryInput.validate_summary | 92-146 | OPEN |
| FN-0384 | backend/app/modules/activities/service.py | ActivityCorrectionConflictError.__init__ | 55-57 | OPEN |
| FN-0385 | backend/app/modules/activities/service.py | ActivityService.__init__ | 63-64 | OPEN |
| FN-0386 | backend/app/modules/activities/service.py | ActivityService._response | 67-71 | OPEN |
| FN-0387 | backend/app/modules/activities/service.py | ActivityService._fingerprint | 74-76 | OPEN |
| FN-0388 | backend/app/modules/activities/service.py | ActivityService.create | 78-91 | OPEN |
| FN-0389 | backend/app/modules/activities/service.py | ActivityService.get | 93-96 | OPEN |
| FN-0390 | backend/app/modules/activities/service.py | ActivityService.list | 98-110 | OPEN |
| FN-0391 | backend/app/modules/activities/service.py | ActivityService._expectation | 113-133 | OPEN |
| FN-0392 | backend/app/modules/activities/service.py | ActivityService.submit_rpe | 135-392 | OPEN |
| FN-0393 | backend/app/modules/activities/service.py | ActivityService.confirm_match | 394-407 | OPEN |
| FN-0394 | backend/app/modules/checkins/domain.py | athlete_local_week_start | 81-86 | OPEN |
| FN-0395 | backend/app/modules/checkins/domain.py | confirmed_restriction_sets | 89-105 | OPEN |
| FN-0396 | backend/app/modules/checkins/domain.py | available_dates_from_blocked_dates | 108-121 | OPEN |
| FN-0397 | backend/app/modules/checkins/domain.py | context_fingerprint | 124-127 | OPEN |
| FN-0398 | backend/app/modules/checkins/domain.py | RestrictionDecision.__post_init__ | 57-74 | OPEN |
| FN-0399 | backend/app/modules/checkins/domain.py | RestrictionDecision.allowed_intensity | 77-78 | OPEN |
| FN-0400 | backend/app/modules/checkins/repository.py | CheckInRepositoryConflictError.__init__ | 30-32 | OPEN |
| FN-0401 | backend/app/modules/checkins/repository.py | CheckInRepository.start_or_resume | 40-44 | OPEN |
| FN-0402 | backend/app/modules/checkins/repository.py | CheckInRepository.fetch | 46-46 | OPEN |
| FN-0403 | backend/app/modules/checkins/repository.py | CheckInRepository.save_context | 48-55 | OPEN |
| FN-0404 | backend/app/modules/checkins/repository.py | CheckInRepository.confirm_context | 57-63 | OPEN |
| FN-0405 | backend/app/modules/checkins/repository.py | CheckInRepository.fetch_planning_context | 65-69 | OPEN |
| FN-0406 | backend/app/modules/checkins/repository.py | CheckInRepository.attach_plan_proposal | 71-76 | OPEN |
| FN-0407 | backend/app/modules/checkins/repository.py | CheckInRepository.list_restrictions | 78-81 | OPEN |
| FN-0408 | backend/app/modules/checkins/repository.py | CheckInRepository.list_external_activities | 83-87 | OPEN |
| FN-0409 | backend/app/modules/checkins/repository.py | CheckInRepository.mark_goal_achieved | 89-94 | OPEN |
| FN-0410 | backend/app/modules/checkins/repository.py | CheckInRepository.aclose | 96-96 | OPEN |
| FN-0411 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.__init__ | 102-115 | OPEN |
| FN-0412 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository._rpc_athlete_id | 117-121 | OPEN |
| FN-0413 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository._headers | 123-141 | OPEN |
| FN-0414 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository._request | 143-192 | OPEN |
| FN-0415 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.start_or_resume | 194-207 | OPEN |
| FN-0416 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.fetch | 209-218 | OPEN |
| FN-0417 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.save_context | 220-241 | OPEN |
| FN-0418 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.confirm_context | 243-262 | OPEN |
| FN-0419 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.fetch_planning_context | 264-281 | OPEN |
| FN-0420 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.attach_plan_proposal | 283-302 | OPEN |
| FN-0421 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.list_restrictions | 304-324 | OPEN |
| FN-0422 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.list_external_activities | 326-348 | OPEN |
| FN-0423 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.mark_goal_achieved | 350-367 | OPEN |
| FN-0424 | backend/app/modules/checkins/repository.py | SupabaseCheckInRepository.aclose | 369-371 | OPEN |
| FN-0425 | backend/app/modules/checkins/router.py | get_checkin_repository | 53-55 | OPEN |
| FN-0426 | backend/app/modules/checkins/router.py | get_checkin_service | 58-72 | OPEN |
| FN-0427 | backend/app/modules/checkins/router.py | _raise_public_error | 75-111 | OPEN |
| FN-0428 | backend/app/modules/checkins/router.py | start_weekly_checkin | 119-128 | OPEN |
| FN-0429 | backend/app/modules/checkins/router.py | get_weekly_checkin | 136-145 | OPEN |
| FN-0430 | backend/app/modules/checkins/router.py | extract_weekly_checkin_context_candidate | 153-168 | OPEN |
| FN-0431 | backend/app/modules/checkins/router.py | save_weekly_checkin_context | 176-186 | OPEN |
| FN-0432 | backend/app/modules/checkins/router.py | confirm_weekly_checkin_context | 194-204 | OPEN |
| FN-0433 | backend/app/modules/checkins/router.py | generate_checkin_plan_proposal | 212-225 | OPEN |
| FN-0434 | backend/app/modules/checkins/router.py | list_injury_restrictions | 233-241 | OPEN |
| FN-0435 | backend/app/modules/checkins/router.py | list_planned_external_activities | 249-258 | OPEN |
| FN-0436 | backend/app/modules/checkins/router.py | mark_goal_achieved | 266-276 | OPEN |
| FN-0437 | backend/app/modules/checkins/schemas.py | CheckInStartRequest.require_monday | 43-46 | OPEN |
| FN-0438 | backend/app/modules/checkins/schemas.py | ExternalActivityInput.require_aware_start | 58-61 | OPEN |
| FN-0439 | backend/app/modules/checkins/schemas.py | InjuryRestrictionResponse.review_due | 155-158 | OPEN |
| FN-0440 | backend/app/modules/checkins/schemas.py | GoalAchievementRequest.achievement_is_not_future | 179-182 | OPEN |
| FN-0441 | backend/app/modules/checkins/service.py | CheckInService.__init__ | 48-56 | OPEN |
| FN-0442 | backend/app/modules/checkins/service.py | CheckInService._response | 59-65 | OPEN |
| FN-0443 | backend/app/modules/checkins/service.py | CheckInService.start | 67-75 | OPEN |
| FN-0444 | backend/app/modules/checkins/service.py | CheckInService.current | 77-88 | OPEN |
| FN-0445 | backend/app/modules/checkins/service.py | CheckInService.get | 90-95 | OPEN |
| FN-0446 | backend/app/modules/checkins/service.py | CheckInService.extract_context_candidate | 97-137 | OPEN |
| FN-0447 | backend/app/modules/checkins/service.py | CheckInService._restriction | 140-148 | OPEN |
| FN-0448 | backend/app/modules/checkins/service.py | CheckInService.save_context | 150-187 | OPEN |
| FN-0449 | backend/app/modules/checkins/service.py | CheckInService.confirm_context | 189-202 | OPEN |
| FN-0450 | backend/app/modules/checkins/service.py | CheckInService._planning_inputs | 205-261 | OPEN |
| FN-0451 | backend/app/modules/checkins/service.py | CheckInService.generate_plan_proposal | 263-289 | OPEN |
| FN-0452 | backend/app/modules/checkins/service.py | CheckInService.list_restrictions | 291-298 | OPEN |
| FN-0453 | backend/app/modules/checkins/service.py | CheckInService.list_external_activities | 300-311 | OPEN |
| FN-0454 | backend/app/modules/checkins/service.py | CheckInService.mark_goal_achieved | 313-325 | OPEN |
| FN-0455 | backend/app/modules/onboarding/eligibility.py | required_disciplines_for_race_type | 18-22 | OPEN |
| FN-0456 | backend/app/modules/onboarding/eligibility.py | _structured_goal_is_current | 25-40 | OPEN |
| FN-0457 | backend/app/modules/onboarding/eligibility.py | satisfied_onboarding_steps | 43-99 | OPEN |
| FN-0458 | backend/app/modules/onboarding/repository.py | OnboardingRepository.fetch_state | 44-45 | OPEN |
| FN-0459 | backend/app/modules/onboarding/repository.py | OnboardingRepository.fetch_identifying_profile | 47-50 | OPEN |
| FN-0460 | backend/app/modules/onboarding/repository.py | OnboardingRepository.fetch_physiology_profile | 52-55 | OPEN |
| FN-0461 | backend/app/modules/onboarding/repository.py | OnboardingRepository.fetch_operational_profile | 57-60 | OPEN |
| FN-0462 | backend/app/modules/onboarding/repository.py | OnboardingRepository.upsert_identifying_profile | 62-65 | OPEN |
| FN-0463 | backend/app/modules/onboarding/repository.py | OnboardingRepository.upsert_physiology_profile | 67-70 | OPEN |
| FN-0464 | backend/app/modules/onboarding/repository.py | OnboardingRepository.upsert_operational_profile | 72-75 | OPEN |
| FN-0465 | backend/app/modules/onboarding/repository.py | OnboardingRepository.replace_training_history | 77-82 | OPEN |
| FN-0466 | backend/app/modules/onboarding/repository.py | OnboardingRepository.save_primary_goal | 84-90 | OPEN |
| FN-0467 | backend/app/modules/onboarding/repository.py | OnboardingRepository.save_zone_profile | 92-97 | OPEN |
| FN-0468 | backend/app/modules/onboarding/repository.py | OnboardingRepository.save_fallback_zone_profile | 99-104 | OPEN |
| FN-0469 | backend/app/modules/onboarding/repository.py | OnboardingRepository.save_calculated_zone_profile | 106-111 | OPEN |
| FN-0470 | backend/app/modules/onboarding/repository.py | OnboardingRepository.complete_onboarding | 113-118 | OPEN |
| FN-0471 | backend/app/modules/onboarding/repository.py | OnboardingRepository.approve_zone_proposal | 120-126 | OPEN |
| FN-0472 | backend/app/modules/onboarding/repository.py | OnboardingRepository.reject_zone_proposal | 128-133 | OPEN |
| FN-0473 | backend/app/modules/onboarding/repository.py | OnboardingRepository.aclose | 135-136 | OPEN |
| FN-0474 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.__init__ | 142-155 | OPEN |
| FN-0475 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._headers | 157-173 | OPEN |
| FN-0476 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._service_headers | 175-182 | OPEN |
| FN-0477 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._request | 184-247 | OPEN |
| FN-0478 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._select | 249-272 | OPEN |
| FN-0479 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._select_optional | 274-298 | OPEN |
| FN-0480 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository._read_operational_profile | 300-315 | OPEN |
| FN-0481 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.fetch_state | 317-440 | OPEN |
| FN-0482 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.fetch_identifying_profile | 442-454 | OPEN |
| FN-0483 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.fetch_physiology_profile | 456-471 | OPEN |
| FN-0484 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.fetch_operational_profile | 473-484 | OPEN |
| FN-0485 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.upsert_identifying_profile | 486-499 | OPEN |
| FN-0486 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.upsert_physiology_profile | 501-514 | OPEN |
| FN-0487 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.upsert_operational_profile | 516-529 | OPEN |
| FN-0488 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.replace_training_history | 531-544 | OPEN |
| FN-0489 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.save_primary_goal | 546-567 | OPEN |
| FN-0490 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.save_fallback_zone_profile | 569-591 | OPEN |
| FN-0491 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.save_calculated_zone_profile | 593-619 | OPEN |
| FN-0492 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.save_zone_profile | 621-634 | OPEN |
| FN-0493 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.complete_onboarding | 636-650 | OPEN |
| FN-0494 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.approve_zone_proposal | 652-673 | OPEN |
| FN-0495 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.reject_zone_proposal | 675-688 | OPEN |
| FN-0496 | backend/app/modules/onboarding/repository.py | SupabaseOnboardingRepository.aclose | 690-693 | OPEN |
| FN-0497 | backend/app/modules/onboarding/router.py | get_onboarding_repository | 61-64 | OPEN |
| FN-0498 | backend/app/modules/onboarding/router.py | get_onboarding_service | 67-74 | OPEN |
| FN-0499 | backend/app/modules/onboarding/router.py | _raise_public_error | 77-103 | OPEN |
| FN-0500 | backend/app/modules/onboarding/router.py | get_profile | 111-123 | OPEN |
| FN-0501 | backend/app/modules/onboarding/router.py | get_identifying_profile | 131-145 | OPEN |
| FN-0502 | backend/app/modules/onboarding/router.py | update_identifying_profile | 153-163 | OPEN |
| FN-0503 | backend/app/modules/onboarding/router.py | get_physiology_profile | 171-185 | OPEN |
| FN-0504 | backend/app/modules/onboarding/router.py | update_physiology_profile | 193-203 | OPEN |
| FN-0505 | backend/app/modules/onboarding/router.py | get_operational_profile | 211-225 | OPEN |
| FN-0506 | backend/app/modules/onboarding/router.py | update_operational_profile | 233-243 | OPEN |
| FN-0507 | backend/app/modules/onboarding/router.py | get_onboarding | 251-260 | OPEN |
| FN-0508 | backend/app/modules/onboarding/router.py | get_goal_planning_options | 268-273 | OPEN |
| FN-0509 | backend/app/modules/onboarding/router.py | replace_training_history | 281-291 | OPEN |
| FN-0510 | backend/app/modules/onboarding/router.py | create_primary_goal | 300-310 | OPEN |
| FN-0511 | backend/app/modules/onboarding/router.py | update_primary_goal | 318-333 | OPEN |
| FN-0512 | backend/app/modules/onboarding/router.py | save_zone_profile | 341-357 | OPEN |
| FN-0513 | backend/app/modules/onboarding/router.py | complete_onboarding | 365-379 | OPEN |
| FN-0514 | backend/app/modules/onboarding/router.py | approve_change_proposal | 387-417 | OPEN |
| FN-0515 | backend/app/modules/onboarding/router.py | reject_change_proposal | 425-453 | OPEN |
| FN-0516 | backend/app/modules/onboarding/schemas.py | AthleteIdentifyingProfileUpdate.at_least_one_field | 69-72 | OPEN |
| FN-0517 | backend/app/modules/onboarding/schemas.py | AthletePhysiologyProfileUpdate.date_of_birth_must_be_past | 94-97 | OPEN |
| FN-0518 | backend/app/modules/onboarding/schemas.py | AthletePhysiologyProfileUpdate.at_least_one_field | 100-103 | OPEN |
| FN-0519 | backend/app/modules/onboarding/schemas.py | AthleteOperationalProfileUpdate.validate_confirmation | 126-144 | OPEN |
| FN-0520 | backend/app/modules/onboarding/schemas.py | TrainingHistoryReplace.require_all_disciplines | 175-184 | OPEN |
| FN-0521 | backend/app/modules/onboarding/schemas.py | PrimaryRaceGoalInput.race_date_must_be_future | 221-225 | OPEN |
| FN-0522 | backend/app/modules/onboarding/schemas.py | PrimaryRaceGoalInput.validate_race_shape | 228-257 | OPEN |
| FN-0523 | backend/app/modules/onboarding/schemas.py | ZoneBoundaryInput.upper_exceeds_lower | 301-305 | OPEN |
| FN-0524 | backend/app/modules/onboarding/schemas.py | ZoneProfileResponse.expose_unambiguous_provenance | 404-432 | OPEN |
| FN-0525 | backend/app/modules/onboarding/service.py | OnboardingService.__init__ | 66-67 | OPEN |
| FN-0526 | backend/app/modules/onboarding/service.py | OnboardingService.goal_planning_options | 70-109 | OPEN |
| FN-0527 | backend/app/modules/onboarding/service.py | OnboardingService._profile | 112-117 | OPEN |
| FN-0528 | backend/app/modules/onboarding/service.py | OnboardingService._goal | 120-125 | OPEN |
| FN-0529 | backend/app/modules/onboarding/service.py | OnboardingService._history | 128-131 | OPEN |
| FN-0530 | backend/app/modules/onboarding/service.py | OnboardingService._history_is_complete | 134-142 | OPEN |
| FN-0531 | backend/app/modules/onboarding/service.py | OnboardingService._discipline_setup | 145-148 | OPEN |
| FN-0532 | backend/app/modules/onboarding/service.py | OnboardingService._zone_profiles | 151-245 | OPEN |
| FN-0533 | backend/app/modules/onboarding/service.py | OnboardingService._profile_is_complete | 248-255 | OPEN |
| FN-0534 | backend/app/modules/onboarding/service.py | OnboardingService._state | 258-342 | OPEN |
| FN-0535 | backend/app/modules/onboarding/service.py | OnboardingService.get_state | 344-350 | OPEN |
| FN-0536 | backend/app/modules/onboarding/service.py | OnboardingService.get_profile | 352-358 | OPEN |
| FN-0537 | backend/app/modules/onboarding/service.py | OnboardingService.get_identifying_profile | 360-368 | OPEN |
| FN-0538 | backend/app/modules/onboarding/service.py | OnboardingService.update_identifying_profile | 370-379 | OPEN |
| FN-0539 | backend/app/modules/onboarding/service.py | OnboardingService.get_physiology_profile | 381-389 | OPEN |
| FN-0540 | backend/app/modules/onboarding/service.py | OnboardingService.update_physiology_profile | 391-400 | OPEN |
| FN-0541 | backend/app/modules/onboarding/service.py | OnboardingService.get_operational_profile | 402-410 | OPEN |
| FN-0542 | backend/app/modules/onboarding/service.py | OnboardingService.update_operational_profile | 412-430 | OPEN |
| FN-0543 | backend/app/modules/onboarding/service.py | OnboardingService.replace_training_history | 432-442 | OPEN |
| FN-0544 | backend/app/modules/onboarding/service.py | OnboardingService.save_primary_goal | 444-460 | OPEN |
| FN-0545 | backend/app/modules/onboarding/service.py | OnboardingService._manual_zone_values | 463-501 | OPEN |
| FN-0546 | backend/app/modules/onboarding/service.py | OnboardingService._calculated_profile_payload | 504-567 | OPEN |
| FN-0547 | backend/app/modules/onboarding/service.py | OnboardingService._calculated_zone_values | 570-616 | OPEN |
| FN-0548 | backend/app/modules/onboarding/service.py | OnboardingService._age_on | 619-624 | OPEN |
| FN-0549 | backend/app/modules/onboarding/service.py | OnboardingService._fallback_zone_values | 627-666 | OPEN |
| FN-0550 | backend/app/modules/onboarding/service.py | OnboardingService.save_zone_profile | 668-708 | OPEN |
| FN-0551 | backend/app/modules/onboarding/service.py | OnboardingService.complete | 710-731 | OPEN |
| FN-0552 | backend/app/modules/onboarding/service.py | OnboardingService.approve_zone_proposal | 733-745 | OPEN |
| FN-0553 | backend/app/modules/onboarding/service.py | OnboardingService.reject_zone_proposal | 747-757 | OPEN |
| FN-0554 | backend/app/modules/onboarding/versioning.py | assess_onboarding_version | 59-109 | OPEN |
| FN-0555 | backend/app/modules/workouts/catalog.py | snapshot_template | 308-322 | OPEN |
| FN-0556 | backend/app/modules/workouts/catalog.py | as_rpe_guided_template | 325-377 | OPEN |
| FN-0557 | backend/app/modules/workouts/catalog.py | _template_rpe_range | 380-404 | OPEN |
| FN-0558 | backend/app/modules/workouts/catalog.py | _segment | 407-426 | OPEN |
| FN-0559 | backend/app/modules/workouts/catalog.py | _protocol_segment | 429-457 | OPEN |
| FN-0560 | backend/app/modules/workouts/catalog.py | _template | 460-531 | OPEN |
| FN-0561 | backend/app/modules/workouts/catalog.py | _canonical_protocol_version | 891-937 | OPEN |
| FN-0562 | backend/app/modules/workouts/catalog.py | active_catalog | 985-1018 | OPEN |
| FN-0563 | backend/app/modules/workouts/catalog.py | with_current_load | 1021-1043 | OPEN |
| FN-0564 | backend/app/modules/workouts/catalog.py | require_planned_load | 1046-1052 | OPEN |
| FN-0565 | backend/app/modules/workouts/catalog.py | ProtocolTarget.__post_init__ | 74-78 | OPEN |
| FN-0566 | backend/app/modules/workouts/catalog.py | RpeTarget.__post_init__ | 90-92 | OPEN |
| FN-0567 | backend/app/modules/workouts/catalog.py | WorkoutSegment.__post_init__ | 110-144 | OPEN |
| FN-0568 | backend/app/modules/workouts/catalog.py | WorkoutSegment.zone | 147-151 | OPEN |
| FN-0569 | backend/app/modules/workouts/catalog.py | WorkoutTemplate.__post_init__ | 180-288 | OPEN |
| FN-0570 | backend/app/modules/workouts/repository.py | parse_planning_catalog | 33-154 | OPEN |
| FN-0571 | backend/app/modules/workouts/repository.py | SupabaseWorkoutCatalogRepository.__init__ | 160-171 | OPEN |
| FN-0572 | backend/app/modules/workouts/repository.py | SupabaseWorkoutCatalogRepository.fetch_for_planning | 173-200 | OPEN |
| FN-0573 | backend/app/modules/workouts/repository.py | SupabaseWorkoutCatalogRepository.aclose | 202-205 | OPEN |
| FN-0574 | backend/app/modules/workouts/router.py | get_workout_catalog | 21-30 | OPEN |
| FN-0575 | backend/app/modules/workouts/schemas.py | rpe_zone_responses | 58-82 | OPEN |
| FN-0576 | backend/app/modules/workouts/schemas.py | WorkoutSegmentResponse.require_exactly_one_target | 103-112 | OPEN |
| FN-0577 | backend/app/modules/workouts/schemas.py | WorkoutTemplateResponse.from_domain | 136-169 | OPEN |
| FN-0578 | backend/app/modules/workouts/source_catalog_audit.py | _positive_integer | 34-35 | OPEN |
| FN-0579 | backend/app/modules/workouts/source_catalog_audit.py | audit_source_catalog | 38-135 | OPEN |
| FN-0580 | backend/app/modules/workouts/source_catalog_audit.py | SourceCatalogAudit.structurally_importable | 30-31 | OPEN |
| FN-0581 | backend/app/modules/integrations/domain.py | validate_polar_entity_id | 31-36 | OPEN |
| FN-0582 | backend/app/modules/integrations/domain.py | verify_polar_webhook | 39-82 | OPEN |
| FN-0583 | backend/app/modules/integrations/domain.py | webhook_event_key | 85-87 | OPEN |
| FN-0584 | backend/app/modules/integrations/domain.py | _duration_minutes | 90-103 | OPEN |
| FN-0585 | backend/app/modules/integrations/domain.py | _discipline | 106-118 | OPEN |
| FN-0586 | backend/app/modules/integrations/domain.py | _started_at | 121-131 | OPEN |
| FN-0587 | backend/app/modules/integrations/domain.py | polar_exercise_to_activity | 134-171 | OPEN |
| FN-0588 | backend/app/modules/integrations/polar.py | PolarProvider.authorization_url | 32-32 | OPEN |
| FN-0589 | backend/app/modules/integrations/polar.py | PolarProvider.exchange_code | 33-33 | OPEN |
| FN-0590 | backend/app/modules/integrations/polar.py | PolarProvider.register_user | 34-34 | OPEN |
| FN-0591 | backend/app/modules/integrations/polar.py | PolarProvider.list_exercises | 35-35 | OPEN |
| FN-0592 | backend/app/modules/integrations/polar.py | PolarProvider.get_exercise | 36-36 | OPEN |
| FN-0593 | backend/app/modules/integrations/polar.py | PolarProvider.get_fit | 37-37 | OPEN |
| FN-0594 | backend/app/modules/integrations/polar.py | PolarProvider.revoke | 38-38 | OPEN |
| FN-0595 | backend/app/modules/integrations/polar.py | PolarProvider.aclose | 39-39 | OPEN |
| FN-0596 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.__init__ | 49-62 | OPEN |
| FN-0597 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient._configured | 64-66 | OPEN |
| FN-0598 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.authorization_url | 68-79 | OPEN |
| FN-0599 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient._basic | 81-84 | OPEN |
| FN-0600 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient._check | 87-91 | OPEN |
| FN-0601 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.exchange_code | 93-121 | OPEN |
| FN-0602 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.register_user | 123-141 | OPEN |
| FN-0603 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.list_exercises | 143-159 | OPEN |
| FN-0604 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.get_exercise | 161-176 | OPEN |
| FN-0605 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.get_fit | 178-194 | OPEN |
| FN-0606 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.revoke | 196-205 | OPEN |
| FN-0607 | backend/app/modules/integrations/polar.py | PolarAccessLinkClient.aclose | 207-209 | OPEN |
| FN-0608 | backend/app/modules/integrations/repository.py | IntegrationRepository.create_oauth_state | 30-32 | OPEN |
| FN-0609 | backend/app/modules/integrations/repository.py | IntegrationRepository.consume_oauth_state | 33-33 | OPEN |
| FN-0610 | backend/app/modules/integrations/repository.py | IntegrationRepository.save_connection | 34-40 | OPEN |
| FN-0611 | backend/app/modules/integrations/repository.py | IntegrationRepository.get_connection | 41-41 | OPEN |
| FN-0612 | backend/app/modules/integrations/repository.py | IntegrationRepository.get_credentials | 42-42 | OPEN |
| FN-0613 | backend/app/modules/integrations/repository.py | IntegrationRepository.disconnect | 43-43 | OPEN |
| FN-0614 | backend/app/modules/integrations/repository.py | IntegrationRepository.start_import | 44-46 | OPEN |
| FN-0615 | backend/app/modules/integrations/repository.py | IntegrationRepository.finish_import | 47-49 | OPEN |
| FN-0616 | backend/app/modules/integrations/repository.py | IntegrationRepository.list_imports | 50-50 | OPEN |
| FN-0617 | backend/app/modules/integrations/repository.py | IntegrationRepository.prepare_import_retry | 51-53 | OPEN |
| FN-0618 | backend/app/modules/integrations/repository.py | IntegrationRepository.claim_due_import_retries | 54-56 | OPEN |
| FN-0619 | backend/app/modules/integrations/repository.py | IntegrationRepository.get_import_retry_context | 57-59 | OPEN |
| FN-0620 | backend/app/modules/integrations/repository.py | IntegrationRepository.import_activity | 60-68 | OPEN |
| FN-0621 | backend/app/modules/integrations/repository.py | IntegrationRepository.upload_activity_file | 69-76 | OPEN |
| FN-0622 | backend/app/modules/integrations/repository.py | IntegrationRepository.record_webhook | 77-79 | OPEN |
| FN-0623 | backend/app/modules/integrations/repository.py | IntegrationRepository.get_webhook_context | 80-80 | OPEN |
| FN-0624 | backend/app/modules/integrations/repository.py | IntegrationRepository.finish_webhook | 81-83 | OPEN |
| FN-0625 | backend/app/modules/integrations/repository.py | IntegrationRepository.aclose | 84-84 | OPEN |
| FN-0626 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.__init__ | 92-107 | OPEN |
| FN-0627 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository._rpc_athlete_id | 109-113 | OPEN |
| FN-0628 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository._opaque_athlete_id | 115-119 | OPEN |
| FN-0629 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository._headers | 121-134 | OPEN |
| FN-0630 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository._rpc | 136-172 | OPEN |
| FN-0631 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.create_oauth_state | 174-181 | OPEN |
| FN-0632 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.consume_oauth_state | 183-192 | OPEN |
| FN-0633 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.save_connection | 194-214 | OPEN |
| FN-0634 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.get_connection | 216-220 | OPEN |
| FN-0635 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.get_credentials | 222-231 | OPEN |
| FN-0636 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.disconnect | 233-239 | OPEN |
| FN-0637 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.start_import | 241-256 | OPEN |
| FN-0638 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.finish_import | 258-273 | OPEN |
| FN-0639 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.list_imports | 275-279 | OPEN |
| FN-0640 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.prepare_import_retry | 281-292 | OPEN |
| FN-0641 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.claim_due_import_retries | 294-316 | OPEN |
| FN-0642 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.get_import_retry_context | 318-329 | OPEN |
| FN-0643 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.import_activity | 331-355 | OPEN |
| FN-0644 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.upload_activity_file | 357-393 | OPEN |
| FN-0645 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.record_webhook | 395-409 | OPEN |
| FN-0646 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.get_webhook_context | 411-424 | OPEN |
| FN-0647 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.finish_webhook | 426-437 | OPEN |
| FN-0648 | backend/app/modules/integrations/repository.py | SupabaseIntegrationRepository.aclose | 439-441 | OPEN |
| FN-0649 | backend/app/modules/integrations/router.py | get_integration_repository | 56-58 | OPEN |
| FN-0650 | backend/app/modules/integrations/router.py | get_polar_provider | 61-63 | OPEN |
| FN-0651 | backend/app/modules/integrations/router.py | get_integration_service | 66-71 | OPEN |
| FN-0652 | backend/app/modules/integrations/router.py | _raise | 74-95 | OPEN |
| FN-0653 | backend/app/modules/integrations/router.py | start_polar_oauth | 104-112 | OPEN |
| FN-0654 | backend/app/modules/integrations/router.py | complete_polar_oauth | 120-128 | OPEN |
| FN-0655 | backend/app/modules/integrations/router.py | get_polar_connection | 136-144 | OPEN |
| FN-0656 | backend/app/modules/integrations/router.py | disconnect_polar | 152-160 | OPEN |
| FN-0657 | backend/app/modules/integrations/router.py | import_polar_history | 169-180 | OPEN |
| FN-0658 | backend/app/modules/integrations/router.py | list_polar_imports | 188-196 | OPEN |
| FN-0659 | backend/app/modules/integrations/router.py | retry_polar_import | 205-214 | OPEN |
| FN-0660 | backend/app/modules/integrations/router.py | polar_webhook | 227-243 | OPEN |
| FN-0661 | backend/app/modules/integrations/service.py | retry_at | 33-43 | OPEN |
| FN-0662 | backend/app/modules/integrations/service.py | IntegrationService.__init__ | 49-57 | OPEN |
| FN-0663 | backend/app/modules/integrations/service.py | IntegrationService._fingerprint | 60-62 | OPEN |
| FN-0664 | backend/app/modules/integrations/service.py | IntegrationService.start_oauth | 64-76 | OPEN |
| FN-0665 | backend/app/modules/integrations/service.py | IntegrationService.complete_oauth | 78-98 | OPEN |
| FN-0666 | backend/app/modules/integrations/service.py | IntegrationService.get_connection | 100-103 | OPEN |
| FN-0667 | backend/app/modules/integrations/service.py | IntegrationService.disconnect | 105-115 | OPEN |
| FN-0668 | backend/app/modules/integrations/service.py | IntegrationService._import_response | 118-119 | OPEN |
| FN-0669 | backend/app/modules/integrations/service.py | IntegrationService.list_imports | 121-125 | OPEN |
| FN-0670 | backend/app/modules/integrations/service.py | IntegrationService._import_one | 127-159 | OPEN |
| FN-0671 | backend/app/modules/integrations/service.py | IntegrationService.import_historical | 161-184 | OPEN |
| FN-0672 | backend/app/modules/integrations/service.py | IntegrationService._run_historical_import | 186-289 | OPEN |
| FN-0673 | backend/app/modules/integrations/service.py | IntegrationService.retry_historical | 291-297 | OPEN |
| FN-0674 | backend/app/modules/integrations/service.py | IntegrationService.retry_due_imports | 299-309 | OPEN |
| FN-0675 | backend/app/modules/integrations/service.py | IntegrationService.receive_webhook | 311-337 | OPEN |
| FN-0676 | backend/app/modules/integrations/service.py | IntegrationService.process_webhook | 339-372 | OPEN |
