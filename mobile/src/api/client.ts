import type {
  CalibrationEvaluation,
  CalibrationObservation,
  CalibrationObservationInput,
  CalibrationProtocol,
  CalibrationStatus,
  CalendarResponse,
  AthletePhysiologyProfile,
  CheckInContextCandidateResponse,
  CheckInRestriction,
  ChangeProposal,
  CompletedActivity,
  Discipline,
  DisciplineSetup,
  DisciplineSetupInput,
  FieldTestSchedulingResponse,
  FatigueLevel,
  GoalPlanningOption,
  InjuryRestriction,
  OnboardingComplete,
  OnboardingState,
  PlanWarning,
  PlanningRecovery,
  PlannedExternalActivity,
  PendingWorkoutAlternatives,
  PolarConnection,
  PolarImportRun,
  PioneerRedemption,
  PrimaryRaceGoal,
  TrainingHistoryEntry,
  ThresholdDecision,
  WeeklyCheckIn,
  WeeklyPlan,
  WeeklyPlanProposal,
  SwipeWeekDraft,
  WorkoutDeck,
  ZoneBoundary,
  ZoneProfile,
  ZoneSetupOption,
  ZoneProfileState,
} from './types';
import { CancellationError, DeadlineError, withDeadline } from '../lib/deadline';
import { apiTokenRetired, registerApiRequest } from '../lib/apiCancellation';
import * as validate from './responseValidation';
import { uncertainWriteMessage, unreadableResponseMessage } from '../i18n/recoveryMessages';

export const API_DEADLINE_MS = 45_000;
export const PLANNING_DEADLINE_MS = 120_000;

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/$/, '');
// Only overlapping reads are shared. No completed snapshot or token is cached.
const onboardingReads = new Map<string, Promise<OnboardingState>>();

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    details?: {
      violations?: Array<{
        location?: string[];
        type?: string;
      }>;
    };
  };
};

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    readonly code: string | null,
    readonly outcome: 'rejected' | 'unknown' = 'rejected',
    readonly method: string = 'GET',
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }

  get retryable(): boolean {
    if (this.code === 'request_cancelled') return false;
    return (
      this.code === 'response_unreadable' || this.code === 'response_invalid' ||
      this.status === null ||
      this.status === 408 ||
      this.status === 429 ||
      (this.status >= 500 && this.status <= 599)
    );
  }
}

function validationMessage(body: ErrorEnvelope): string | null {
  if (body.error?.code !== 'validation_failed') return null;
  const violations = body.error.details?.violations ?? [];
  if (violations.length === 0) return null;
  if (violations.some((violation) => violation.type === 'extra_forbidden')) {
    return 'De app en de Wombo-server gebruiken verschillende versies. Probeer het later opnieuw.';
  }
  const fields = new Set(
    violations
      .flatMap((violation) => violation.location ?? [])
      .filter((part) => part !== 'body'),
  );
  if (fields.has('target_date')) {
    return 'Gebruik een toekomstige racedatum in het formaat JJJJ-MM-DD.';
  }
  if (fields.has('pool_length_meters')) {
    return 'Kies een zwembadlengte van 25 of 50 meter.';
  }
  if (fields.has('guidance_mode')) {
    return 'Kies een geldige begeleidingsvorm voor deze discipline.';
  }
  if (fields.has('setup_route')) {
    return 'Kies opnieuw hoe je de trainingszones wilt instellen.';
  }
  return 'Controleer de ingevulde velden en probeer opnieuw.';
}

function deterministicErrorMessage(code: string | undefined): string | null {
  switch (code) {
    case 'rest_or_anti_stack_unsatisfied':
    case 'swipe_draft_no_completion':
    case 'swipe_selection_invalid':
      return 'Deze trainingscombinatie past niet veilig op de gekozen dagen. Kies extra beschikbare dagen, liefst verder uit elkaar, of kies een andere training.';
    case 'availability_required':
      return 'Kies minstens één beschikbare trainingsdag.';
    case 'availability_outside_week':
    case 'swipe_date_unavailable':
    case 'fixed_date_unavailable':
      return 'Kies alleen beschikbare dagen binnen deze planweek.';
    case 'previous_week_availability_unavailable':
      return 'Er is geen bevestigde beschikbaarheid van vorige week. Kies de dagen voor deze week zelf.';
    case 'swipe_draft_stale':
    case 'swipe_draft_context_stale':
    case 'swipe_draft_base_stale':
    case 'proposal_stale':
      return 'Je weekplanning is intussen gewijzigd. Vernieuw de week en probeer opnieuw.';
    case 'swipe_selection_incomplete':
    case 'swipe_layout_incomplete':
      return 'Rond eerst alle trainingskeuzes en datums af.';
    case 'catalog_coverage_unsatisfied':
    case 'catalog_phase_coverage_unavailable':
    case 'taper_catalog_coverage_unavailable':
      return 'Voor deze week is nog geen volledige veilige trainingscombinatie beschikbaar. Pas je keuzes aan of probeer een andere week.';
    case 'catalog_capacity_unsatisfied':
      return 'De beschikbare trainingen vormen nog geen passend weekvoorstel voor je bevestigde trainingsgeschiedenis. Controleer je ingevulde uren of vraag om een beoordeeld trainingsvoorstel.';
    case 'average_heart_rate_immutable':
      return 'De gemiddelde hartslag kan niet meer worden gewijzigd nadat deze training is verwerkt.';
    default:
      return null;
  }
}

export async function request<T>(
  accessToken: string,
  path: string,
  options: RequestInit = {},
  valid?: (body: unknown) => boolean,
): Promise<T> {
  if (!apiBaseUrl) {
    throw new Error('Configureer EXPO_PUBLIC_API_BASE_URL.');
  }
  const method = (options.method ?? 'GET').toUpperCase();
  const mutation = !['GET', 'HEAD'].includes(method);
  // A read begun before/during a write cannot satisfy a post-write refresh.
  if (mutation) onboardingReads.delete(accessToken);
  const controller = new AbortController();
  const unregister = registerApiRequest(accessToken, controller);
  const cancel = () => controller.abort();
  options.signal?.addEventListener('abort', cancel, { once: true });
  if (options.signal?.aborted) cancel();
  let dispatched = false;
  let response: Response | undefined;
  const outcome = (): 'unknown' | 'rejected' => {
    if (!dispatched || !mutation) return 'rejected';
    return !response || response.ok || response.status === 408 || response.status >= 500
      ? 'unknown' : 'rejected';
  };
  const deadline = /(?:\/(?:swipe-drafts|proposals|schedule-proposals|plan-proposals|edit-proposals)|\/swipe-drafts\/[^/]+\/submit)$/.test(path) && mutation
    ? PLANNING_DEADLINE_MS : API_DEADLINE_MS;
  const expiresAt = Date.now() + deadline;
  try {
    if (apiTokenRetired(accessToken)) throw new CancellationError();
    return await withDeadline(async signal => {
      dispatched = true;
      const received = await fetch(`${apiBaseUrl}${path}`, {
        ...options,
        signal,
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      if (Date.now() >= expiresAt) throw new DeadlineError();
      response = received;
      if (!response.ok) {
        const body = validate.errorEnvelope(await response.json().catch(() => null));
        const message =
          validationMessage(body) ??
          deterministicErrorMessage(body.error?.code) ??
          (response.status === 401
            ? 'Je sessie is verlopen. Meld je opnieuw aan.'
            : response.status === 503
              ? 'De Wombo-server is tijdelijk niet beschikbaar. Probeer het zo opnieuw.'
              : response.status === 409
                ? 'Deze wijziging is niet meer actueel. Vernieuw het scherm en probeer opnieuw.'
                : 'De wijziging kon niet veilig worden opgeslagen. Probeer opnieuw.');
        throw new ApiRequestError(
          message,
          response.status,
          body.error?.code ?? null,
          outcome(), method,
        );
      }
      if (response.status === 204 && !valid) return undefined as T;
      let body: unknown;
      try { body = await response.json(); }
      catch {
        throw new ApiRequestError(
          mutation ? uncertainWriteMessage : unreadableResponseMessage,
          response.status, 'response_unreadable', outcome(), method,
        );
      }
      if (valid && !valid(body)) throw new ApiRequestError(
        mutation ? uncertainWriteMessage : unreadableResponseMessage,
        response.status, 'response_invalid', outcome(), method,
      );
      return body as T;
    }, deadline, controller.signal);
  } catch (caught) {
    if (caught instanceof ApiRequestError) throw caught;
    const code = caught instanceof DeadlineError ? 'request_timeout'
      : caught instanceof CancellationError ? 'request_cancelled' : 'network_unavailable';
    throw new ApiRequestError(
      mutation
        ? uncertainWriteMessage
        : 'De Wombo-server is niet bereikbaar. Controleer je verbinding en probeer opnieuw.',
      response?.status ?? null, code, outcome(), method,
    );
  } finally {
    if (mutation) onboardingReads.delete(accessToken);
    unregister(); options.signal?.removeEventListener('abort', cancel);
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export function getOnboarding(accessToken: string): Promise<OnboardingState> {
  const pending = onboardingReads.get(accessToken);
  if (pending) return pending;
  const read = fetchOnboarding(accessToken);
  onboardingReads.set(accessToken, read);
  const remove = () => { if (onboardingReads.get(accessToken) === read) onboardingReads.delete(accessToken); };
  void read.then(remove, remove);
  return read;
}

async function fetchOnboarding(
  accessToken: string,
): Promise<OnboardingState> {
  const retryDelays = [400, 1200];
  for (let attempt = 0; ; attempt += 1) {
    try {
      return await request(accessToken, '/api/v1/onboarding');
    } catch (caught) {
      const delay = retryDelays[attempt];
      if (
        !(caught instanceof ApiRequestError) ||
        !caught.retryable ||
        delay === undefined
      ) {
        throw caught;
      }
      await wait(delay);
    }
  }
}

export async function getPhysiologyProfile(
  accessToken: string,
): Promise<AthletePhysiologyProfile | null> {
  try {
    return await request<AthletePhysiologyProfile>(
      accessToken,
      '/api/v1/me/physiology-profile',
    );
  } catch (caught) {
    if (caught instanceof ApiRequestError && caught.status === 404) return null;
    throw caught;
  }
}

export async function saveProfile(
  accessToken: string,
  input: {
    first_name?: string;
    last_name?: string;
    date_of_birth: string;
    resting_heart_rate_bpm: number;
  },
): Promise<void> {
  const writes: Promise<unknown>[] = [
    request<unknown>(accessToken, '/api/v1/me/physiology-profile', {
      method: 'PATCH',
      body: JSON.stringify({
        date_of_birth: input.date_of_birth,
        resting_heart_rate_bpm: input.resting_heart_rate_bpm,
      }),
    }),
  ];
  if (input.first_name || input.last_name) {
    writes.push(
      request<unknown>(accessToken, '/api/v1/me/identifying-profile', {
        method: 'PATCH',
        body: JSON.stringify({
          ...(input.first_name ? { first_name: input.first_name } : {}),
          ...(input.last_name ? { last_name: input.last_name } : {}),
        }),
      }),
    );
  }
  await Promise.all(writes);
}

export function saveOperationalProfile(
  accessToken: string,
  input:
    | {
        timezone: string;
        timezone_source: 'device' | 'manual';
        timezone_confirmed: true;
      }
    | { heart_rate_monitor_confirmed: true },
): Promise<unknown> {
  return request(accessToken, '/api/v1/me/operational-profile', {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export function saveTrainingHistory(
  accessToken: string,
  entries: Array<{
    discipline: Discipline;
    average_hours_per_week: string;
  }>,
): Promise<TrainingHistoryEntry[]> {
  return request(accessToken, '/api/v1/me/training-history', {
    method: 'PUT',
    body: JSON.stringify({ entries }),
  });
}

export function getGoalPlanningOptions(
  accessToken: string,
): Promise<GoalPlanningOption[]> {
  return request(accessToken, '/api/v1/onboarding/goal-options');
}

export function savePrimaryGoal(
  accessToken: string,
  input: {
    race_type: import('./types').RaceType;
    race_name: string;
    race_date: string;
    swim_distance_meters?: number;
    bike_distance_meters?: number;
    run_distance_meters?: number;
    total_target_time_seconds: number;
    swim_target_time_seconds?: number;
    bike_target_time_seconds?: number;
    run_target_time_seconds?: number;
    specific_focus?: string;
  },
  goalId?: string,
): Promise<PrimaryRaceGoal> {
  return request(
    accessToken,
    goalId ? `/api/v1/me/goals/${goalId}` : '/api/v1/me/goals',
    {
      method: goalId ? 'PUT' : 'POST',
      body: JSON.stringify(input),
    },
  );
}

export function saveManualZones(
  accessToken: string,
  discipline: Discipline,
  input: {
    metric_kind: string;
    metric_value: string;
    boundaries: ZoneBoundary[];
  },
): Promise<{ profile: ZoneProfile; proposal_id: string | null }> {
  return request(accessToken, `/api/v1/me/zones/${discipline}`, {
    method: 'PUT',
    body: JSON.stringify({
      setup_method: 'manual',
      confirmed: true,
      ...input,
    }),
  });
}

export function saveFallbackZones(
  accessToken: string,
  discipline: Exclude<Discipline, 'swim'>,
): Promise<{ profile: ZoneProfile; proposal_id: string | null }> {
  return request(accessToken, `/api/v1/me/zones/${discipline}`, {
    method: 'PUT',
    body: JSON.stringify({
      setup_method: 'fallback',
      confirmed: true,
    }),
  });
}

export function saveCalculatedZones(
  accessToken: string,
  discipline: Discipline,
  input: {
    thresholds: Array<{ metric_kind: string; value: string }>;
    source_quality: 'athlete_entered' | 'measured_lab';
    boundary_overrides: Array<{
      metric_kind: string;
      boundaries: ZoneBoundary[];
    }>;
  },
): Promise<{ profile: ZoneProfile; proposal_id: string | null }> {
  return request(accessToken, `/api/v1/me/zones/${discipline}`, {
    method: 'PUT',
    body: JSON.stringify({
      setup_method: 'calculated',
      confirmed: true,
      ...input,
    }),
  });
}

export function getZoneSetupOptions(
  accessToken: string,
  discipline: Discipline,
): Promise<ZoneSetupOption[]> {
  return request(accessToken, `/api/v1/onboarding/zone-options/${discipline}`);
}

export function saveDisciplineSetup(
  accessToken: string,
  discipline: Discipline,
  input: DisciplineSetupInput,
): Promise<DisciplineSetup> {
  return request(
    accessToken,
    `/api/v1/onboarding/disciplines/${discipline}/setup`,
    {
      method: 'PUT',
      body: JSON.stringify(input),
    },
  );
}

export function listCalibrationProtocols(
  accessToken: string,
  discipline: Discipline,
): Promise<CalibrationProtocol[]> {
  return request(
    accessToken,
    `/api/v1/calibration/protocols/${discipline}`,
  );
}

export function saveCalibrationObservation(
  accessToken: string,
  input: CalibrationObservationInput,
): Promise<CalibrationObservation> {
  return request(accessToken, '/api/v1/calibration/observations', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function evaluateCalibration(
  accessToken: string,
  activityId: string,
  protocolId: string,
): Promise<CalibrationEvaluation> {
  return request(accessToken, '/api/v1/calibration/evaluate', {
    method: 'POST',
    body: JSON.stringify({
      activity_id: activityId,
      protocol_id: protocolId,
    }),
  });
}

export function confirmCalibrationThreshold(
  accessToken: string,
  evaluationId: string,
): Promise<ThresholdDecision> {
  return request(
    accessToken,
    `/api/v1/calibration/evaluations/${evaluationId}/threshold/confirm`,
    {
      method: 'POST',
      body: JSON.stringify({ confirmed: true }),
    },
  );
}

export function rejectCalibrationThreshold(
  accessToken: string,
  evaluationId: string,
): Promise<ThresholdDecision> {
  return request(
    accessToken,
    `/api/v1/calibration/evaluations/${evaluationId}/threshold/reject`,
    { method: 'POST' },
  );
}

export function getCalibrationStatus(
  accessToken: string,
): Promise<CalibrationStatus> {
  return request(accessToken, '/api/v1/calibration/status');
}

export function getZoneProfileState(
  accessToken: string,
): Promise<ZoneProfileState> {
  return request(accessToken, '/api/v1/me/zone-profile');
}

export function scheduleFieldTest(
  accessToken: string,
  input: {
    discipline: Discipline;
    protocol_id: string;
    scheduling_mode: 'standalone' | 'weekly_plan';
    scheduled_date: string;
    plan_id?: string;
    expected_plan_revision?: number;
  },
): Promise<FieldTestSchedulingResponse> {
  return request(accessToken, '/api/v1/calibration/test-assignments', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function approveTestAssignment(
  accessToken: string,
  proposalId: string,
  expectedRevision: number,
): Promise<{
  proposal_id: string;
  state: 'applied';
  test_assignment_id: string;
  test_assignment_state: 'scheduled';
}> {
  return request(
    accessToken,
    `/api/v1/calibration/test-assignments/${proposalId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify({ expected_revision: expectedRevision }),
    },
  );
}

export function rejectTestAssignment(
  accessToken: string,
  proposalId: string,
): Promise<{
  proposal_id: string;
  state: 'rejected';
  test_assignment_id: string;
  test_assignment_state: 'rejected';
}> {
  return request(
    accessToken,
    `/api/v1/calibration/test-assignments/${proposalId}/reject`,
    { method: 'POST' },
  );
}

export function completeOnboarding(
  accessToken: string,
  expectedOnboardingRevision: number,
): Promise<OnboardingComplete> {
  return request(accessToken, '/api/v1/onboarding/complete', {
    method: 'POST',
    body: JSON.stringify({
      expected_onboarding_revision: expectedOnboardingRevision,
    }),
  });
}

export function createWeeklyPlanProposal(
  accessToken: string,
  input: {
    week_start: string;
    available_dates?: string[];
    reuse_previous_week?: boolean;
    confirmed_injuries: Discipline[];
  },
): Promise<WeeklyPlanProposal> {
  return request(accessToken, '/api/v1/weekly-plans/proposals', {
    method: 'POST',
    body: JSON.stringify(input),
  }, validate.planProposalResponse);
}

export function createSwipeWeekDraft(
  accessToken: string,
  input: {
    week_start: string;
    available_dates?: string[];
    reuse_previous_week?: boolean;
    confirmed_injuries: Discipline[];
    low_only_disciplines?: Discipline[];
    cross_training_opt_ins?: Discipline[];
    plan_id?: string;
    expected_base_revision?: number;
  },
): Promise<SwipeWeekDraft> {
  return request(accessToken, '/api/v1/weekly-plans/swipe-drafts', {
    method: 'POST',
    body: JSON.stringify(input),
  }, validate.draftResponse);
}

export function getSwipeWeekDraft(
  accessToken: string,
  draftId: string,
): Promise<SwipeWeekDraft> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/swipe-drafts/${draftId}`, {}, body => validate.draftResponse(body) && validate.object(body) && body.id === draftId,
  );
}

export function transitionSwipeWeekDraft(
  accessToken: string,
  draftId: string,
  input: {
    expected_revision: number;
    action: 'accept' | 'pass' | 'undo' | 'reset_passed';
    candidate_template_id?: string;
    candidate_occurrence_id?: string;
  },
): Promise<SwipeWeekDraft> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/swipe-drafts/${draftId}/transitions`,
    { method: 'POST', body: JSON.stringify(input) }, validate.draftResponse,
  );
}

export function placeSwipeWeekWorkout(
  accessToken: string,
  draftId: string,
  occurrenceId: string,
  expectedRevision: number,
  scheduledDate: string,
): Promise<SwipeWeekDraft> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/swipe-drafts/${draftId}/placements/${occurrenceId}`,
    {
      method: 'PUT',
      body: JSON.stringify({
        expected_revision: expectedRevision,
        scheduled_date: scheduledDate,
      }),
    }, validate.draftResponse,
  );
}

export function submitSwipeWeekDraft(
  accessToken: string,
  draftId: string,
  expectedRevision: number,
  placementMode: 'automatic' | 'manual',
): Promise<WeeklyPlanProposal> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/swipe-drafts/${draftId}/submit`,
    {
      method: 'POST',
      body: JSON.stringify({
        expected_revision: expectedRevision,
        placement_mode: placementMode,
      }),
    }, validate.planProposalResponse,
  );
}

export function getWeeklyPlan(
  accessToken: string,
  planId: string,
  revision?: number,
): Promise<WeeklyPlan> {
  const query = revision === undefined ? '' : `?revision=${revision}`;
  return request(accessToken, `/api/v1/weekly-plans/${planId}${query}`, {}, body => validate.planResponse(body) && validate.object(body) && body.id === planId && (revision === undefined || body.revision === revision));
}

export function getWorkoutDeck(
  accessToken: string,
  planId: string,
  expectedRevision?: number,
  selectedTemplateIds: string[] = [],
): Promise<WorkoutDeck> {
  const query = new URLSearchParams();
  if (expectedRevision !== undefined) {
    query.append('expected_revision', String(expectedRevision));
  }
  selectedTemplateIds.forEach((id) => query.append('selected_template_ids', id));
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return request(accessToken, `/api/v1/weekly-plans/${planId}/deck${suffix}`);
}

export function createScheduleProposal(
  accessToken: string,
  planId: string,
  input: {
    expected_base_revision: number;
    available_dates: string[];
    confirmed_injuries: Discipline[];
    selected_template_ids: string[];
  },
): Promise<WeeklyPlanProposal> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/${planId}/schedule-proposals`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    }, validate.planProposalResponse,
  );
}

export function approvePlanProposal(
  accessToken: string,
  proposalId: string,
  expectedBaseRevision: number,
): Promise<{ state: 'applied'; plan_id: string; active_revision: number }> {
  return request(
    accessToken,
    `/api/v1/change-proposals/${proposalId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify({
        expected_base_revision: expectedBaseRevision,
      }),
    }, validate.approvalResponse,
  );
}

export function approveZoneProposal(
  accessToken: string,
  proposalId: string,
  expectedBaseZoneProfileId: string | null,
): Promise<{
  state: 'applied';
  active_zone_profile_id: string;
  superseded_zone_profile_id: string | null;
}> {
  return request(
    accessToken,
    `/api/v1/change-proposals/${proposalId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify({
        expected_base_zone_profile_id: expectedBaseZoneProfileId,
      }),
    },
  );
}

export function rejectZoneProposal(
  accessToken: string,
  proposalId: string,
): Promise<{
  state: 'rejected';
  active_zone_profile_id: string | null;
  superseded_zone_profile_id: null;
}> {
  return request(
    accessToken,
    `/api/v1/change-proposals/${proposalId}/reject`,
    { method: 'POST' },
  );
}

export function rejectPlanProposal(
  accessToken: string,
  proposalId: string,
): Promise<{ state: 'rejected'; plan_id: string }> {
  return request(
    accessToken,
    `/api/v1/change-proposals/${proposalId}/reject`,
    { method: 'POST' },
  );
}

export function listPlanProposals(
  accessToken: string,
  state?: ChangeProposal['state'],
): Promise<ChangeProposal[]> {
  const query = state === undefined ? '' : `?state=${state}`;
  return request(accessToken, `/api/v1/change-proposals${query}`);
}

export function getCalendar(
  accessToken: string,
  from: string,
  to: string,
): Promise<CalendarResponse> {
  const query = new URLSearchParams({ from, to });
  return request(accessToken, `/api/v1/calendar?${query.toString()}`);
}

export function createActivity(
  accessToken: string,
  idempotencyKey: string,
  input: {
    planned_workout_id?: string;
    planned_external_activity_id?: string;
    discipline: Discipline;
    started_at: string;
    timezone: string;
    duration_minutes: string | null;
    performed_duration_confirmed?: boolean;
    distance_meters?: number;
  },
): Promise<CompletedActivity> {
  return request(accessToken, '/api/v1/activities', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify(input),
  }, validate.activityResponse);
}

export function listPlannedExternalActivities(
  accessToken: string,
  weekStart?: string,
): Promise<PlannedExternalActivity[]> {
  const query = weekStart ? `?week_start=${weekStart}` : '';
  return request(accessToken, `/api/v1/planned-external-activities${query}`);
}

export function listActivities(
  accessToken: string,
  pendingRpe = false,
): Promise<CompletedActivity[]> {
  return request(
    accessToken,
    pendingRpe
      ? '/api/v1/activities/pending-rpe'
      : '/api/v1/activities', {}, validate.activityListResponse,
  );
}

export function getActivity(
  accessToken: string,
  activityId: string,
): Promise<CompletedActivity> {
  return request(accessToken, `/api/v1/activities/${activityId}`, {}, body => validate.activityResponse(body) && validate.object(body) && body.id === activityId);
}

export function submitActivityRpe(
  accessToken: string,
  activityId: string,
  rpe: number,
  averageHeartRateBpm?: number,
  expectedCurrentRpe?: number,
): Promise<CompletedActivity> {
  return request(accessToken, `/api/v1/activities/${activityId}/rpe`, {
    method: 'PUT',
    body: JSON.stringify({
      rpe,
      ...(expectedCurrentRpe === undefined
        ? {}
        : { expected_current_rpe: expectedCurrentRpe }),
      ...(averageHeartRateBpm === undefined
        ? {}
        : { average_heart_rate_bpm: averageHeartRateBpm }),
    }),
  }, body => validate.activityResponse(body) && validate.object(body) && body.id === activityId);
}

export async function submitActivityRpeWithRefresh(
  accessToken: string,
  activity: CompletedActivity,
  rpe: number,
  averageHeartRateBpm?: number,
): Promise<CompletedActivity> {
  try {
    return await submitActivityRpe(
      accessToken,
      activity.id,
      rpe,
      averageHeartRateBpm,
      activity.rpe ?? undefined,
    );
  } catch (caught) {
    const refreshable =
      caught instanceof ApiRequestError &&
      (caught.retryable ||
        caught.code === 'activity_state_conflict' ||
        caught.code === 'activity_correction_stale');
    if (!refreshable) throw caught;

    let refreshed: CompletedActivity;
    try { refreshed = await getActivity(accessToken, activity.id); }
    catch (readError) {
      // A failed verification read cannot turn a possibly committed write into
      // a definite rejection (nor erase its original HTTP context).
      if (caught.outcome === 'unknown') throw caught;
      throw readError;
    }
    const requestedAlreadyStored =
      refreshed.processing_state === 'complete' &&
      refreshed.rpe === rpe &&
      (averageHeartRateBpm === undefined ||
        refreshed.metrics?.average_heart_rate_bpm === averageHeartRateBpm);
    if (requestedAlreadyStored) return refreshed;

    // A snapshot of old state does not prove the first request stopped. Leave
    // any replay to an explicit action with the original payload/precondition.
    if (caught.outcome === 'unknown') throw caught;

    if (refreshed.rpe !== activity.rpe) {
      throw new ApiRequestError(
        'De activiteit is intussen gewijzigd. Vernieuw en controleer de opgeslagen RPE.',
        409,
        'activity_correction_stale',
      );
    }

    return submitActivityRpe(
      accessToken,
      activity.id,
      rpe,
      averageHeartRateBpm,
      refreshed.rpe ?? undefined,
    );
  }
}

export function confirmActivityMatch(
  accessToken: string,
  activityId: string,
  plannedWorkoutId: string,
): Promise<CompletedActivity> {
  return request(
    accessToken,
    `/api/v1/activities/${activityId}/planned-workout-match`,
    {
      method: 'PUT',
      body: JSON.stringify({ planned_workout_id: plannedWorkoutId }),
    }, body => validate.activityResponse(body) && validate.object(body) && body.id === activityId,
  );
}

export function getPioneerRedemption(
  accessToken: string,
): Promise<PioneerRedemption | null> {
  return request(accessToken, '/api/v1/pioneer-access/redemption');
}

export function redeemPioneerAccess(
  accessToken: string,
  idempotencyKey: string,
  code: string,
): Promise<PioneerRedemption> {
  return request(accessToken, '/api/v1/pioneer-access/redemptions', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({ code: code.trim().toUpperCase() }),
  });
}

export async function getPolarConnection(
  accessToken: string,
): Promise<PolarConnection | null> {
  try {
    return await request(accessToken, '/api/v1/integrations/polar');
  } catch (caught) {
    if (caught instanceof ApiRequestError && caught.status === 404) return null;
    throw caught;
  }
}

export function startPolarOAuth(
  accessToken: string,
): Promise<{ provider: 'polar'; authorization_url: string; expires_at: string }> {
  return request(accessToken, '/api/v1/integrations/polar/oauth/start', {
    method: 'POST',
  });
}

export function disconnectPolar(accessToken: string): Promise<void> {
  return request(accessToken, '/api/v1/integrations/polar', {
    method: 'DELETE',
  });
}

export function listPolarImports(
  accessToken: string,
): Promise<PolarImportRun[]> {
  return request(accessToken, '/api/v1/integrations/polar/imports');
}

export function importPolarHistory(
  accessToken: string,
  idempotencyKey: string,
  days: 7 | 14 | 30 = 14,
): Promise<PolarImportRun> {
  return request(accessToken, '/api/v1/integrations/polar/imports', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({ days }),
  });
}

export function retryPolarImport(
  accessToken: string,
  importId: string,
): Promise<PolarImportRun> {
  return request(
    accessToken,
    `/api/v1/integrations/polar/imports/${importId}/retry`,
    { method: 'POST' },
  );
}

export function startWeeklyCheckIn(
  accessToken: string,
  weekStart: string,
): Promise<WeeklyCheckIn> {
  return request(accessToken, '/api/v1/checkins', {
    method: 'POST',
    body: JSON.stringify({ week_start: weekStart }),
  }, validate.checkInResponse);
}

export function getWeeklyCheckIn(accessToken: string, checkInId: string): Promise<WeeklyCheckIn> {
  return request(accessToken, `/api/v1/checkins/${checkInId}`, {}, body =>
    validate.checkInResponse(body) && validate.object(body) && body.id === checkInId);
}

async function reconcileCheckInWrite(
  accessToken: string, checkInId: string, write: () => Promise<WeeklyCheckIn>,
  committed: (stored: WeeklyCheckIn) => boolean,
): Promise<WeeklyCheckIn> {
  try { return await write(); }
  catch (caught) {
    if (!(caught instanceof ApiRequestError) || !((caught.outcome === 'unknown' && caught.retryable) || caught.status === 409)) throw caught;
    try {
      const stored = await getWeeklyCheckIn(accessToken, checkInId);
      if (committed(stored)) return stored;
    } catch { /* Preserve the uncertain write, including its original status. */ }
    throw caught;
  }
}

// Compare submitted fields only. Response metadata is not part of the write;
// arrays in structured context are sets of answers, dates or activities.
function matchesSubmitted(stored: unknown, submitted: unknown): boolean {
  if (submitted === null || submitted === undefined) return stored === null || stored === undefined;
  if (Array.isArray(submitted)) return Array.isArray(stored) && stored.length === submitted.length &&
    submitted.every(item => stored.filter(value => matchesSubmitted(value, item)).length === submitted.filter(value => matchesSubmitted(value, item)).length);
  if (validate.object(submitted)) return validate.object(stored) && Object.entries(submitted).every(([key, value]) => matchesSubmitted(stored[key], value));
  return stored === submitted;
}

export function getInjuryRestrictions(accessToken: string): Promise<InjuryRestriction[]> {
  return request(accessToken, '/api/v1/me/injury-restrictions');
}

export function extractWeeklyCheckInContextCandidate(
  accessToken: string,
  checkInId: string,
  athleteText: string,
): Promise<CheckInContextCandidateResponse> {
  return request(
    accessToken,
    `/api/v1/checkins/${checkInId}/context-candidates`,
    {
      method: 'POST',
      body: JSON.stringify({ athlete_text: athleteText }),
    },
  );
}

export function saveWeeklyCheckInContext(
  accessToken: string,
  checkInId: string,
  input: {
    expected_revision: number;
    blocked_dates: string[];
    fatigue_level: FatigueLevel;
    missed_workout_reasons: string[];
    recurring_activities_confirmed: boolean;
    external_activities: Array<{
      name: string;
      discipline: Discipline;
      scheduled_at: string;
      duration_minutes: string;
      strenuous: boolean;
      recurring: boolean;
    }>;
    restrictions: CheckInRestriction[];
    alarm_symptoms_acknowledged: boolean;
  },
): Promise<WeeklyCheckIn> {
  const { expected_revision, ...answers } = input;
  return reconcileCheckInWrite(accessToken, checkInId, () => request(accessToken, `/api/v1/checkins/${checkInId}/context`, {
    method: 'PUT',
    body: JSON.stringify(input),
  }, body => validate.checkInResponse(body) && validate.object(body) && body.id === checkInId), stored =>
    stored.context_revision === expected_revision + 1 && matchesSubmitted(stored.context, answers));
}

export function confirmWeeklyCheckInContext(
  accessToken: string,
  checkInId: string,
  expectedRevision: number,
  contextFingerprint: string,
): Promise<WeeklyCheckIn> {
  return reconcileCheckInWrite(accessToken, checkInId, () => request(
    accessToken,
    `/api/v1/checkins/${checkInId}/context-confirmation`,
    {
      method: 'POST',
      body: JSON.stringify({
        expected_revision: expectedRevision,
        context_fingerprint: contextFingerprint,
      }),
    }, body => validate.checkInResponse(body) && validate.object(body) && body.id === checkInId,
  ), stored => stored.context?.state === 'confirmed' && stored.context.revision === expectedRevision && stored.context.fingerprint === contextFingerprint);
}

export function createCheckInPlanProposal(
  accessToken: string,
  checkInId: string,
): Promise<WeeklyPlanProposal> {
  return request(accessToken, `/api/v1/checkins/${checkInId}/plan-proposals`, {
    method: 'POST',
  }, validate.planProposalResponse);
}

export function movePlannedWorkout(
  accessToken: string,
  workoutId: string,
  expectedRevision: number,
  scheduledDate: string,
): Promise<WeeklyPlan> {
  return request(accessToken, `/api/v1/planned-workouts/${workoutId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      expected_revision: expectedRevision,
      scheduled_date: scheduledDate,
    }),
  }, validate.planResponse);
}

export function validatePlanLayout(
  accessToken: string,
  planId: string,
  expectedRevision: number,
  workouts: Array<{ workout_id: string; scheduled_date: string }>,
): Promise<{ valid_for_generated_schedule: boolean; warnings: PlanWarning[] }> {
  return request(accessToken, `/api/v1/weekly-plans/${planId}/validate`, {
    method: 'POST',
    body: JSON.stringify({
      expected_revision: expectedRevision,
      workouts,
    }),
  });
}


export function getPendingWorkoutAlternatives(
  accessToken: string,
  planId: string,
  workoutId: string,
  expectedRevision: number,
): Promise<PendingWorkoutAlternatives> {
  const query = new URLSearchParams({
    expected_revision: String(expectedRevision),
  });
  return request(
    accessToken,
    `/api/v1/weekly-plans/${planId}/pending-workouts/${workoutId}/alternatives?${query.toString()}`,
  );
}

export function editPendingWorkout(
  accessToken: string,
  planId: string,
  workoutId: string,
  input: {
    expected_revision: number;
    expected_proposal_id: string;
    replacement_template_id: string | null;
  },
): Promise<WeeklyPlanProposal> {
  return request(
    accessToken,
    `/api/v1/weekly-plans/${planId}/pending-workouts/${workoutId}/edit-proposals`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    }, validate.planProposalResponse,
  );
}

export function markGoalAchieved(
  accessToken: string,
  goalId: string,
  achievedAt: string,
): Promise<{ status: 'active'; achieved_at: string }> {
  return request(accessToken, `/api/v1/me/goals/${goalId}/achievement`, {
    method: 'POST',
    body: JSON.stringify({ achieved_at: achievedAt }),
  });
}

export async function discoverPlanning(accessToken: string): Promise<PlanningRecovery> {
  return request<PlanningRecovery>(accessToken, '/api/v1/weekly-plans/recovery', {}, validate.recoveryResponse);
}
