export type Discipline = 'swim' | 'bike' | 'run';
export type OnboardingStep =
  | 'profile'
  | 'history'
  | 'goal'
  | 'zones'
  | 'review'
  | 'completed';

export type AthleteProfile = {
  athlete_id: string;
  date_of_birth: string | null;
  height_cm: string | null;
  weight_kg: string | null;
  resting_heart_rate_bpm: number | null;
  motivation_text: string | null;
  motivation_tag: string | null;
  timezone: string;
  onboarding_status: 'not_started' | 'in_progress' | 'completed';
  revision: number;
  created_at: string;
  updated_at: string;
};

export type TrainingHistoryEntry = {
  discipline: Discipline;
  weekly_minutes: number;
  experience_years: string;
  confirmed_at: string;
  updated_at: string;
};

export type PrimaryRaceGoal = {
  id: string;
  title: string;
  specific_description: string;
  measurable_outcome: string;
  feasibility_score: number;
  target_date: string;
  race_discipline_profile: Discipline[];
  priority: 'A';
  goal_type: 'race';
  status: 'active' | 'superseded';
  revision: number;
  created_at: string;
  updated_at: string;
};

export type ZoneBoundary = {
  zone_number: number;
  lower_value: string;
  upper_value: string;
};

export type CalculatedZoneBoundary = {
  zone_number: number;
  lower_value: string | null;
  upper_value: string | null;
};

export type ZoneMetricKind =
  | 'swim_css_seconds_per_100m'
  | 'bike_ftp_watts'
  | 'bike_threshold_heart_rate_bpm'
  | 'run_threshold_pace_seconds_per_km'
  | 'run_lthr_bpm';

export type ZoneSetupRoute =
  | 'known_values'
  | 'field_test'
  | 'calibration_week'
  | 'rpe_only';

export type GuidanceMode =
  | 'power'
  | 'heart_rate'
  | 'combined'
  | 'pace'
  | 'rpe_only';

export type KnownThreshold = {
  metric_kind: ZoneMetricKind;
  value: string;
};

export type KnownZoneProfile = {
  metric_kind: ZoneMetricKind;
  boundaries: ZoneBoundary[];
};

export type CalculatedZoneMetricProfile = {
  metric_kind: ZoneMetricKind;
  source_value: string;
  is_primary: boolean;
  boundary_source: 'model_derived' | 'athlete_entered';
  zone_model_version: 'start23-zone-model-1.0';
  boundaries: CalculatedZoneBoundary[];
};

export type DisciplineSetupInput =
  | {
      setup_route: 'known_values';
      guidance_mode: GuidanceMode;
      thresholds: KnownThreshold[];
      zone_profiles: KnownZoneProfile[];
      pool_length_meters?: 25 | 50;
    }
  | {
      setup_route: 'field_test';
      guidance_mode: GuidanceMode;
      protocol_id: string;
      pool_length_meters?: 25 | 50;
    }
  | {
      setup_route: 'calibration_week';
      guidance_mode: GuidanceMode;
      pool_length_meters?: 25 | 50;
    }
  | {
      setup_route: 'rpe_only';
      guidance_mode: 'rpe_only';
    };

export type DisciplineSetup = {
  discipline: Discipline;
  setup_route: ZoneSetupRoute;
  guidance_mode: GuidanceMode;
  setup_status: 'configured' | 'test_pending' | 'calibration_pending';
  protocol_id: string | null;
  pool_length_meters: 25 | 50 | null;
  threshold_status: 'unknown' | 'user_provided';
  zone_status:
    | 'unknown'
    | 'user_provided'
    | 'pending_protocol'
    | 'pending_athlete_confirmation';
  source: 'user_provided' | 'field_test' | 'week1_calibration' | 'none';
  validation_status: 'self_reported' | 'not_assessed';
  confidence: 'not_assessed' | 'low' | 'medium';
  known_thresholds: KnownThreshold[];
  known_zone_profiles: KnownZoneProfile[];
  revision: number;
  created_at: string;
  updated_at: string;
};

export type ZoneProfile = {
  id: string;
  discipline: Discipline;
  version: number;
  setup_method: 'manual' | 'fallback' | 'calculated';
  status: 'pending' | 'active' | 'superseded' | 'rejected' | 'expired';
  source: 'athlete_entered' | 'estimated' | 'reviewed_field_threshold';
  validation_status:
    | 'confirmed_by_athlete'
    | 'unreviewed'
    | 'pending_athlete_confirmation'
    | 'rejected_by_athlete';
  fallback_active: boolean;
  needs_testing: boolean;
  requires_review: boolean;
  review_reason:
    | 'within_soft_range'
    | 'outside_soft_range'
    | 'soft_range_not_configured'
    | 'fallback_unvalidated'
    | 'athlete_confirmation_required';
  ruleset_version: string;
  zone_model_version: string | null;
  source_method: string | null;
  source_quality: string | null;
  calculated_at: string | null;
  review_status: string | null;
  reviewer_id: string | null;
  reviewed_at: string | null;
  evidence_version: string | null;
  effective_from: string | null;
  created_at: string;
  metric: {
    metric_kind: string;
    value: string;
  } | null;
  boundaries: CalculatedZoneBoundary[];
  metric_profiles: CalculatedZoneMetricProfile[];
  proposal_id: string | null;
  base_zone_profile_id: string | null;
};

export type OnboardingState = {
  status: 'not_started' | 'in_progress' | 'completed';
  current_step: OnboardingStep;
  completed_steps: OnboardingStep[];
  profile: AthleteProfile | null;
  training_history: TrainingHistoryEntry[];
  primary_goal: PrimaryRaceGoal | null;
  zones: ZoneProfile[];
  discipline_setups: DisciplineSetup[];
  can_complete: boolean;
  initial_plan_request_id: string | null;
};

export type ZoneSetupOption = {
  setup_route: ZoneSetupRoute;
  label: string;
  creates_threshold: boolean;
  creates_zones: boolean;
};

export type CalibrationProtocolSegment = {
  order: number;
  segment_id: string;
  purpose: string;
  duration_seconds: number | null;
  distance_meters: number | null;
  target_rpe_min: number;
  target_rpe_max: number;
  optional: boolean;
};

export type CalibrationProtocol = {
  protocol_id: string;
  discipline: Discipline;
  protocol_type: 'field_test' | 'submaximal_calibration';
  version: number;
  review_status: 'approved_active';
  result_status_on_success:
    | 'threshold_estimated'
    | 'provisionally_calibrated';
  guidance_modes: GuidanceMode[];
  segments: CalibrationProtocolSegment[];
};

export type SwimRepetition = {
  distance_meters: number;
  elapsed_time_seconds: string;
  rest_time_seconds: number;
  completed: boolean;
};

export type CalibrationObservationInput = {
  activity_id: string;
  planned_workout_id?: string;
  protocol_id: string;
  discipline: Discipline;
  segment_id: string;
  performed_at: string;
  completed: boolean;
  interrupted: boolean;
  quality_status: 'missing' | 'insufficient' | 'sufficient';
  target_rpe: number;
  reported_block_rpe?: number;
  reported_session_rpe?: number;
  steady_execution?: 'yes' | 'mostly' | 'no';
  duration_seconds?: number;
  distance_meters?: number;
  average_heart_rate_bpm?: string;
  ending_heart_rate_bpm?: string;
  average_heart_rate_last_20min_bpm?: string;
  average_power_watts?: string;
  average_power_last_20min_watts?: string;
  average_pace_seconds_per_km?: string;
  elapsed_time_seconds?: string;
  pool_length_meters?: 25 | 50;
  stroke?: 'freestyle';
  equipment?: 'none';
  rest_time_seconds?: number;
  data_completeness?: string;
  stable_segment?: boolean;
  power_source_calibrated?: boolean;
  repetitions?: SwimRepetition[];
};

export type CalibrationObservation = CalibrationObservationInput & {
  id: string;
  fingerprint: string;
  created_at: string;
};

export type ThresholdEstimate = {
  metric_kind: ZoneMetricKind;
  value: string;
};

export type CalibrationEvaluation = {
  id: string;
  activity_id: string;
  protocol_id: string;
  discipline: Discipline;
  ruleset_version: string;
  status:
    | 'insufficient_data'
    | 'rpe_only'
    | 'provisionally_calibrated'
    | 'threshold_estimated'
    | 'insufficient_protocol';
  threshold_status: 'unknown' | 'threshold_estimated';
  zone_status:
    | 'unknown'
    | 'provisionally_calibrated'
    | 'pending_protocol'
    | 'pending_athlete_confirmation';
  confidence: 'not_assessed' | 'low' | 'medium';
  reason_codes: string[];
  thresholds: ThresholdEstimate[];
  zone_model_version: 'start23-zone-model-1.0' | null;
  zone_profiles: CalculatedZoneMetricProfile[];
  requires_athlete_confirmation: boolean;
  review_status: 'pending_athlete_confirmation' | 'not_applicable';
  fingerprint: string;
  created_at: string;
};

export type ThresholdDecision = {
  evaluation_id: string;
  state: 'accepted' | 'rejected';
  zone_profile_id: string | null;
  zone_proposal_id: string | null;
  base_zone_profile_id: string | null;
  decided_at: string;
  zone_proposal_state:
    | 'pending'
    | 'approved'
    | 'rejected'
    | 'expired'
    | 'applied'
    | null;
};

export type CalibrationStatus = {
  setups: DisciplineSetup[];
  evaluations: CalibrationEvaluation[];
  threshold_decisions: ThresholdDecision[];
};

export type OnboardingComplete = {
  onboarding: OnboardingState;
  initial_plan_request_id: string;
  initial_plan_request_status: 'pending';
};

export type AvailabilityWindow = {
  starts_at: string;
  ends_at: string;
};

export type WorkoutSegment = {
  sequence: number;
  name: string;
  instructions: string;
  duration_minutes: string;
  distance_meters: number | null;
  zone: number;
  expected_rpe: number;
  is_swim_technique: boolean;
};

export type PlanWarning = {
  id: string | null;
  rule_id: string;
  code: string;
  severity: 'info' | 'warning' | 'conflict';
  message: string;
  planned_workout_id: string | null;
};

export type PlannedWorkout = {
  id: string;
  template_id: string;
  template_key: string;
  template_version: number;
  discipline: Discipline;
  name: string;
  description: string;
  duration_minutes: string;
  distance_meters: number | null;
  intensity_bucket: 'low' | 'high';
  expected_rpe_min: number;
  expected_rpe_max: number;
  segments: WorkoutSegment[];
  scheduled_at: string;
  timezone: string;
  source:
    | 'auto_planned'
    | 'athlete_selected'
    | 'athlete_moved'
    | 'system_adjusted';
  status: 'scheduled' | 'completed' | 'cancelled';
  warnings: PlanWarning[];
};

export type RestDay = {
  date: string;
  reason: 'planned_rest' | 'restriction_rest';
};

export type ChangeProposal = {
  id: string;
  kind: 'zone_update' | 'plan_revision';
  state: 'pending' | 'approved' | 'rejected' | 'expired' | 'applied';
  reason_codes: string[];
  public_explanation: string;
  ruleset_version: string;
  created_at: string;
  decided_at: string | null;
  applied_at: string | null;
  decision_actor: string | null;
  target_plan_revision_id: string | null;
  base_plan_revision: number | null;
  target_zone_profile_id: string | null;
  base_zone_profile_id: string | null;
};

export type WeeklyPlan = {
  id: string;
  week_start: string;
  timezone: string;
  state: 'pending_approval' | 'active' | 'superseded' | 'rejected' | 'expired';
  active_revision: number | null;
  revision_id: string;
  revision: number;
  revision_state:
    | 'draft'
    | 'pending_approval'
    | 'active'
    | 'rejected'
    | 'superseded'
    | 'expired';
  phase: 'base' | 'build' | 'recovery' | 'taper';
  target_basis:
    | 'initial_catalog_baseline'
    | 'prior_planned_hold'
    | 'realized_progression'
    | 'realized_baseline'
    | 'inactive_restart'
    | 'maintenance_hold'
    | 'physiological_debt'
    | 'manual_review_recovery'
    | 'activity_correction'
    | 'recovery_factor'
    | 'taper_factor'
    | 'injury_rest_only';
  taper_period: 'a_t_minus_2' | 'a_t_minus_1' | null;
  total_duration_minutes: string;
  low_intensity_percent: string;
  high_intensity_percent: string;
  display_low_intensity_percent: number;
  display_high_intensity_percent: number;
  low_intensity_minutes: string;
  high_intensity_minutes: string;
  confirmed_injuries: Discipline[];
  low_only_disciplines: Discipline[];
  workouts: PlannedWorkout[];
  rest_days: RestDay[];
  warnings: PlanWarning[];
  proposal: ChangeProposal | null;
};

export type WeeklyPlanProposal = {
  proposal: ChangeProposal;
  plan: WeeklyPlan;
};

export type WorkoutDeckItem = {
  id: string;
  template_key: string;
  version: number;
  discipline: Discipline;
  name: string;
  description: string;
  duration_minutes: string;
  distance_meters: number | null;
  intensity_bucket: 'low' | 'high';
  expected_rpe_min: number;
  expected_rpe_max: number;
  segments: WorkoutSegment[];
};

export type WorkoutDeck = {
  plan_id: string;
  revision: number;
  phase: WeeklyPlan['phase'];
  templates: WorkoutDeckItem[];
};

export type CalendarResponse = {
  from_datetime: string;
  to_datetime: string;
  workouts: PlannedWorkout[];
  rest_days: RestDay[];
};

export type FatigueLevel = 'none' | 'low' | 'moderate' | 'high';
export type RestrictionStatus =
  | 'none'
  | 'self_reported_limited'
  | 'self_reported_blocked'
  | 'professional_restricted'
  | 'clearance_required'
  | 'expired';
export type AthletePlanChoice =
  | 'keep_blocked'
  | 'train_low_only'
  | 'resume_unrestricted';

export type CheckInRestriction = {
  discipline: Discipline;
  status: RestrictionStatus;
  source: 'athlete' | 'physician' | 'physiotherapist' | 'other_professional';
  athlete_plan_choice: AthletePlanChoice;
  professional_advice?: string;
  professional_advice_at?: string;
};

export type ExternalActivity = {
  name: string;
  discipline: Discipline;
  scheduled_at: string;
  duration_minutes: string;
  strenuous: boolean;
  recurring: boolean;
};

export type PlannedExternalActivity = ExternalActivity & {
  id: string;
  week_start: string;
  status: 'planned' | 'completed' | 'cancelled';
  completed_activity_id: string | null;
  created_at: string;
};

export type WeeklyCheckInContext = {
  revision: number;
  state: 'draft' | 'confirmed' | 'superseded';
  source: 'structured_form';
  expires_at: string;
  fingerprint: string;
  blocked_dates: string[];
  fatigue_level: FatigueLevel;
  missed_workout_reasons: string[];
  recurring_activities_confirmed: boolean;
  external_activities: ExternalActivity[];
  restrictions: CheckInRestriction[];
  alarm_symptoms_acknowledged: boolean;
  confirmed_at: string | null;
};

export type WeeklyCheckIn = {
  id: string;
  week_start: string;
  timezone: string;
  status: 'open' | 'completed';
  context_revision: number;
  plan_proposal_id: string | null;
  started_at: string;
  completed_at: string | null;
  context: WeeklyCheckInContext | null;
};

export type ActivityMetrics = {
  average_heart_rate_bpm: number | null;
  max_heart_rate_bpm: number | null;
  normalized_power_watts: number | null;
  average_speed_kmh: string | null;
  max_speed_kmh: string | null;
  average_pace_seconds_per_km: string | null;
  low_intensity_minutes: string | null;
  high_intensity_minutes: string | null;
};

export type CompletedActivity = {
  id: string;
  planned_workout_id: string | null;
  discipline: Discipline;
  source: 'canonical_summary';
  started_at: string;
  timezone: string;
  duration_minutes: string;
  distance_meters: number | null;
  elevation_gain_meters: number | null;
  rpe: number | null;
  rpe_submitted_at: string | null;
  match_status: 'matched' | 'unmatched';
  processing_state: 'awaiting_rpe' | 'complete';
  qualitative_result:
    | 'awaiting_rpe'
    | 'perfect_match'
    | 'overshoot'
    | 'hidden_fatigue'
    | 'deviation'
    | 'unplanned';
  public_message: string;
  correction_proposal_id: string | null;
  metrics: ActivityMetrics | null;
  created_at: string;
  updated_at: string;
};
