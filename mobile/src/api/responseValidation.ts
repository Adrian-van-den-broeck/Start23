// Runtime checks at commit/recovery boundaries. These validate wire structure,
// identities and states; the server remains the authority for training rules.
type ObjectValue = Record<string, unknown>;
export const object = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === 'string';
const id = (value: unknown): value is string => text(value) && value.trim().length > 0;
const number = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const integer = (value: unknown): value is number => number(value) && Number.isInteger(value);
const nullable = (value: unknown, check: (value: unknown) => boolean) => value === null || check(value);
const array = (value: unknown, check: (value: unknown) => boolean) => Array.isArray(value) && value.every(check);
const oneOf = (value: unknown, values: readonly unknown[]) => values.includes(value);
const strings = (value: unknown) => array(value, text);
const discipline = (value: unknown) => oneOf(value, ['run', 'bike', 'swim']);
const fields = (value: ObjectValue, names: string[], check: (item: unknown) => boolean) => names.every(name => check(value[name]));

export function workoutRegistration(value: unknown): boolean {
  return object(value) && fields(value, ['planned_workout_id', 'plan_revision_id'], id) &&
    integer(value.registration_revision) && value.registration_revision >= 0 &&
    oneOf(value.status, ['unknown', 'skipped']);
}

export function activityResponse(value: unknown): boolean {
  if (!object(value)) return false;
  return fields(value, ['id', 'started_at', 'timezone', 'created_at', 'updated_at'], id) &&
    fields(value, ['planned_workout_id', 'rpe_submitted_at', 'correction_proposal_id'], v => nullable(v, text)) &&
    discipline(value.discipline) && value.source === 'canonical_summary' &&
    nullable(value.duration_minutes, text) && nullable(value.distance_meters, number) && nullable(value.elevation_gain_meters, number) &&
    nullable(value.rpe, integer) && oneOf(value.match_status, ['matched', 'unmatched']) &&
    oneOf(value.processing_state, ['awaiting_rpe', 'complete']) &&
    (value.processing_state !== 'complete' || (integer(value.rpe) && id(value.rpe_submitted_at))) &&
    oneOf(value.qualitative_result, ['awaiting_rpe', 'perfect_match', 'overshoot', 'hidden_fatigue', 'deviation', 'unplanned']) &&
    text(value.public_message) && nullable(value.metrics, item => object(item) &&
      fields(item, ['average_heart_rate_bpm', 'max_heart_rate_bpm', 'normalized_power_watts'], v => nullable(v, number)) &&
      fields(item, ['average_speed_kmh', 'max_speed_kmh', 'average_pace_seconds_per_km', 'low_intensity_minutes', 'high_intensity_minutes'], v => nullable(v, text)) &&
      nullable(item.zone_minutes, v => Array.isArray(v) && v.length === 5 && v.every(text)));
}
function warning(value: unknown): boolean {
  return object(value) && nullable(value.id, text) && fields(value, ['rule_id', 'code', 'message'], text) &&
    oneOf(value.severity, ['info', 'warning', 'conflict']) && nullable(value.planned_workout_id, text);
}
function segment(value: unknown): boolean {
  return object(value) && integer(value.sequence) && fields(value, ['name', 'instructions'], text) &&
    nullable(value.duration_minutes, text) && nullable(value.distance_meters, number) && nullable(value.zone_target, number) &&
    number(value.expected_rpe) && typeof value.is_swim_technique === 'boolean' &&
    nullable(value.protocol_target, v => object(v) && fields(v, ['protocol_id', 'segment_id'], id) &&
      fields(v, ['target_rpe_min', 'target_rpe_max'], number) && oneOf(v.intensity_bucket, ['low', 'high']) && typeof v.optional === 'boolean') &&
    nullable(value.rpe_target, v => object(v) && fields(v, ['target_rpe_min', 'target_rpe_max'], number) &&
      oneOf(v.intensity_bucket, ['low', 'high']) && v.heart_rate_observation_required === true);
}
function deckItem(value: unknown): boolean {
  return object(value) && id(value.id) && id(value.template_key) &&
    ('template_version' in value ? integer(value.template_version) : integer(value.version)) &&
    discipline(value.discipline) && fields(value, ['name', 'description'], text) &&
    nullable(value.duration_minutes, text) && nullable(value.distance_meters, number) && oneOf(value.intensity_bucket, ['low', 'high']) &&
    fields(value, ['expected_rpe_min', 'expected_rpe_max'], number) && array(value.segments, segment) &&
    array(value.rpe_zones, v => object(v) && fields(v, ['zone_number', 'target_rpe_min', 'target_rpe_max'], number) && fields(v, ['display_label', 'training_type', 'description'], text));
}
function workout(value: unknown): boolean {
  return object(value) && deckItem(value) && fields(value, ['template_id', 'template_key', 'scheduled_date'], id) && integer(value.template_version) &&
    oneOf(value.source, ['auto_planned', 'athlete_selected', 'athlete_moved', 'system_adjusted']) &&
    oneOf(value.status, ['scheduled', 'completed', 'cancelled']) && array(value.warnings, warning);
}
function proposal(value: unknown): boolean {
  return object(value) && id(value.id) && oneOf(value.kind, ['plan_revision', 'zone_update', 'validation_test']) &&
    oneOf(value.state, ['pending', 'approved', 'rejected', 'expired', 'applied']) &&
    strings(value.reason_codes) && fields(value, ['public_explanation', 'ruleset_version', 'created_at'], text) &&
    fields(value, ['decided_at', 'applied_at', 'decision_actor', 'target_plan_revision_id', 'target_zone_profile_id', 'base_zone_profile_id', 'target_test_assignment_id'], v => nullable(v, text)) && nullable(value.base_plan_revision, integer);
}
export function planResponse(value: unknown): boolean {
  return object(value) && fields(value, ['id', 'revision_id', 'week_start', 'timezone'], id) && integer(value.revision) && nullable(value.active_revision, integer) &&
    oneOf(value.state, ['pending_approval', 'active', 'superseded', 'rejected', 'expired']) &&
    oneOf(value.revision_state, ['draft', 'pending_approval', 'active', 'rejected', 'superseded', 'expired']) &&
    oneOf(value.phase, ['base', 'build', 'recovery', 'taper']) &&
    oneOf(value.target_basis, ['initial_catalog_baseline', 'prior_planned_hold', 'realized_progression', 'realized_baseline', 'inactive_restart', 'maintenance_hold', 'physiological_debt', 'manual_review_recovery', 'activity_correction', 'recovery_factor', 'taper_factor', 'injury_rest_only']) &&
    nullable(value.taper_period, v => oneOf(v, ['a_t_minus_2', 'a_t_minus_1'])) &&
    oneOf(value.availability_source, ['explicit', 'previous_week', 'checkin']) &&
    fields(value, ['total_duration_minutes', 'low_intensity_percent', 'high_intensity_percent', 'low_intensity_minutes', 'high_intensity_minutes'], text) &&
    fields(value, ['display_low_intensity_percent', 'display_high_intensity_percent'], number) &&
    array(value.confirmed_injuries, discipline) && array(value.low_only_disciplines, discipline) && strings(value.available_dates) &&
    array(value.workouts, workout) && array(value.rest_days, v => object(v) && id(v.date) && oneOf(v.reason, ['planned_rest', 'restriction_rest'])) &&
    array(value.warnings, warning) && nullable(value.proposal, proposal) &&
    (value.proposal === null || !object(value.proposal) || value.proposal.target_plan_revision_id === value.revision_id);
}
export function planProposalResponse(value: unknown): boolean {
  return object(value) && planResponse(value.plan) && proposal(value.proposal) && object(value.plan) && object(value.proposal) &&
    value.proposal.kind === 'plan_revision' && value.proposal.target_plan_revision_id === value.plan.revision_id && object(value.plan.proposal) &&
    value.plan.proposal.id === value.proposal.id && value.plan.proposal.state === value.proposal.state && value.plan.proposal.base_plan_revision === value.proposal.base_plan_revision;
}
export function approvalResponse(value: unknown): boolean {
  return object(value) && value.state === 'applied' && id(value.plan_id) && integer(value.active_revision);
}
export function draftResponse(value: unknown): boolean {
  return object(value) && fields(value, ['id', 'week_start', 'ruleset_version'], id) && integer(value.revision) &&
    oneOf(value.state, ['collecting', 'placement', 'submitted']) && strings(value.available_dates) &&
    array(value.cross_training_opt_ins, discipline) && integer(value.target_workout_count) && object(value.target_composition) &&
    fields(value.target_composition, ['run', 'bike', 'swim'], integer) &&
    array(value.accepted_workouts, v => object(v) && deckItem(v) && id(v.occurrence_id)) &&
    nullable(value.current_candidate, v => object(v) && deckItem(v) && id(v.occurrence_id)) &&
    array(value.placements, v => object(v) && id(v.occurrence_id) && id(v.scheduled_date)) && array(value.warnings, warning) &&
    integer(value.passed_count) && fields(value, ['exhausted', 'can_undo'], v => typeof v === 'boolean') &&
    nullable(value.plan_id, text) && nullable(value.proposal_id, text);
}
function restriction(value: unknown): boolean {
  return object(value) && discipline(value.discipline) && oneOf(value.status, ['none', 'self_reported_limited', 'self_reported_blocked', 'professional_restricted', 'clearance_required', 'expired']) &&
    oneOf(value.source, ['athlete', 'physiotherapist', 'physician', 'other_professional']) &&
    oneOf(value.athlete_plan_choice, ['resume_unrestricted', 'keep_blocked', 'train_low_only']) &&
    (value.professional_advice === undefined || nullable(value.professional_advice, text)) &&
    (value.professional_advice_at === undefined || nullable(value.professional_advice_at, text));
}
export function checkInResponse(value: unknown): boolean {
  return object(value) && fields(value, ['id', 'week_start', 'timezone', 'started_at'], id) && oneOf(value.status, ['open', 'completed']) &&
    integer(value.context_revision) && nullable(value.plan_proposal_id, text) && nullable(value.completed_at, text) &&
    nullable(value.context, v => object(v) && integer(v.revision) && fields(v, ['expires_at', 'fingerprint'], id) &&
      oneOf(v.state, ['draft', 'confirmed', 'superseded']) && v.source === 'structured_form' && strings(v.blocked_dates) &&
      oneOf(v.fatigue_level, ['none', 'low', 'moderate', 'high']) && strings(v.missed_workout_reasons) &&
      typeof v.recurring_activities_confirmed === 'boolean' && typeof v.alarm_symptoms_acknowledged === 'boolean' && nullable(v.confirmed_at, text) &&
      array(v.restrictions, restriction) && array(v.external_activities, a => object(a) && fields(a, ['name', 'scheduled_at', 'duration_minutes'], text) &&
        discipline(a.discipline) && typeof a.strenuous === 'boolean' && typeof a.recurring === 'boolean'));
}
export function recoveryResponse(value: unknown): boolean {
  return object(value) && nullable(value.active, planResponse) && nullable(value.pending, planResponse) &&
    nullable(value.draft, v => object(v) && id(v.id) && integer(v.revision) && id(v.week_start) && oneOf(v.state, ['collecting', 'placement']));
}
export const activityListResponse = (value: unknown): boolean => array(value, activityResponse);

// Error bodies are untrusted too. Retain only safe codes and field locations;
// never copy arbitrary server messages or values into a public exception.
export function errorEnvelope(value: unknown): { error?: { code?: string; details?: { violations?: Array<{ location?: string[]; type?: string }> } } } {
  if (!object(value) || !object(value.error)) return {};
  const code = typeof value.error.code === 'string' && /^[a-z_]{1,100}$/.test(value.error.code) ? value.error.code : undefined;
  const details = value.error.details;
  const violations = object(details) && Array.isArray(details.violations) ? details.violations.filter(object).map(item => ({
    location: Array.isArray(item.location) ? item.location.filter(text) : [], type: text(item.type) ? item.type : undefined,
  })) : [];
  return { error: { code, details: { violations } } };
}
