import type {
  AthleteProfile,
  AvailabilityWindow,
  CalibrationEvaluation,
  CalibrationObservation,
  CalibrationObservationInput,
  CalibrationProtocol,
  CalibrationStatus,
  CalendarResponse,
  ChangeProposal,
  CompletedActivity,
  Discipline,
  DisciplineSetup,
  DisciplineSetupInput,
  OnboardingComplete,
  OnboardingState,
  PlannedExternalActivity,
  PrimaryRaceGoal,
  TrainingHistoryEntry,
  ThresholdDecision,
  WeeklyCheckIn,
  WeeklyPlan,
  WeeklyPlanProposal,
  WorkoutDeck,
  ZoneBoundary,
  ZoneProfile,
  ZoneSetupOption,
} from './types';

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/$/, '');

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

class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    readonly code: string | null,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }

  get retryable(): boolean {
    return (
      this.status === null ||
      this.status === 429 ||
      (this.status >= 500 && this.status <= 599)
    );
  }
}

function validationMessage(body: ErrorEnvelope): string | null {
  if (body.error?.code !== 'validation_failed') return null;
  const violations = body.error.details?.violations ?? [];
  if (violations.length === 0) return null;
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

async function request<T>(
  accessToken: string,
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (!apiBaseUrl) {
    throw new Error('Configureer EXPO_PUBLIC_API_BASE_URL.');
  }
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    throw new ApiRequestError(
      'De Start23-server is niet bereikbaar. Controleer je verbinding en probeer opnieuw.',
      null,
      'network_unavailable',
    );
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    const message =
      validationMessage(body) ??
      (response.status === 401
        ? 'Je sessie is verlopen. Meld je opnieuw aan.'
        : response.status === 503
          ? 'De Start23-server is tijdelijk niet beschikbaar. Probeer het zo opnieuw.'
          : body.error?.message ?? 'De wijziging kon niet worden opgeslagen.');
    throw new ApiRequestError(
      message,
      response.status,
      body.error?.code ?? null,
    );
  }
  return (await response.json()) as T;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export async function getOnboarding(
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

export function saveProfile(
  accessToken: string,
  input: {
    date_of_birth: string;
    height_cm: string;
    weight_kg: string;
    resting_heart_rate_bpm: number;
    motivation_text: string;
    motivation_tag?: string;
    timezone: string;
  },
): Promise<AthleteProfile> {
  return request(accessToken, '/api/v1/me/profile', {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export function saveTrainingHistory(
  accessToken: string,
  entries: Array<{
    discipline: Discipline;
    weekly_minutes: number;
    experience_years: string;
  }>,
): Promise<TrainingHistoryEntry[]> {
  return request(accessToken, '/api/v1/me/training-history', {
    method: 'PUT',
    body: JSON.stringify({ entries }),
  });
}

export function savePrimaryGoal(
  accessToken: string,
  input: {
    title: string;
    specific_description: string;
    measurable_outcome: string;
    feasibility_score: number;
    target_date: string;
    race_discipline_profile: Discipline[];
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
): Promise<ZoneSetupOption[]> {
  return request(accessToken, '/api/v1/onboarding/zone-options');
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

export function completeOnboarding(
  accessToken: string,
): Promise<OnboardingComplete> {
  return request(accessToken, '/api/v1/onboarding/complete', {
    method: 'POST',
  });
}

export function createWeeklyPlanProposal(
  accessToken: string,
  input: {
    week_start: string;
    availability: AvailabilityWindow[];
    confirmed_injuries: Discipline[];
  },
): Promise<WeeklyPlanProposal> {
  return request(accessToken, '/api/v1/weekly-plans/proposals', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function getWeeklyPlan(
  accessToken: string,
  planId: string,
  revision?: number,
): Promise<WeeklyPlan> {
  const query = revision === undefined ? '' : `?revision=${revision}`;
  return request(accessToken, `/api/v1/weekly-plans/${planId}${query}`);
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
    availability: AvailabilityWindow[];
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
    },
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
    },
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
    duration_minutes: string;
    distance_meters?: number;
  },
): Promise<CompletedActivity> {
  return request(accessToken, '/api/v1/activities', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify(input),
  });
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
      : '/api/v1/activities',
  );
}

export function submitActivityRpe(
  accessToken: string,
  activityId: string,
  rpe: number,
): Promise<CompletedActivity> {
  return request(accessToken, `/api/v1/activities/${activityId}/rpe`, {
    method: 'PUT',
    body: JSON.stringify({ rpe }),
  });
}

export function startWeeklyCheckIn(
  accessToken: string,
  weekStart: string,
): Promise<WeeklyCheckIn> {
  return request(accessToken, '/api/v1/checkins', {
    method: 'POST',
    body: JSON.stringify({ week_start: weekStart }),
  });
}

export function saveWeeklyCheckInContext(
  accessToken: string,
  checkInId: string,
  input: {
    expected_revision: number;
    blocked_dates: string[];
    fatigue_level: string;
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
    restrictions: Array<{
      discipline: Discipline;
      status: string;
      source: string;
      athlete_plan_choice: string;
      professional_advice?: string;
      professional_advice_at?: string;
    }>;
    alarm_symptoms_acknowledged: boolean;
  },
): Promise<WeeklyCheckIn> {
  return request(accessToken, `/api/v1/checkins/${checkInId}/context`, {
    method: 'PUT',
    body: JSON.stringify(input),
  });
}

export function confirmWeeklyCheckInContext(
  accessToken: string,
  checkInId: string,
  expectedRevision: number,
  contextFingerprint: string,
): Promise<WeeklyCheckIn> {
  return request(
    accessToken,
    `/api/v1/checkins/${checkInId}/context-confirmation`,
    {
      method: 'POST',
      body: JSON.stringify({
        expected_revision: expectedRevision,
        context_fingerprint: contextFingerprint,
      }),
    },
  );
}

export function createCheckInPlanProposal(
  accessToken: string,
  checkInId: string,
): Promise<WeeklyPlanProposal> {
  return request(accessToken, `/api/v1/checkins/${checkInId}/plan-proposals`, {
    method: 'POST',
  });
}

export function movePlannedWorkout(
  accessToken: string,
  workoutId: string,
  expectedRevision: number,
  scheduledAt: string,
): Promise<WeeklyPlan> {
  return request(accessToken, `/api/v1/planned-workouts/${workoutId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      expected_revision: expectedRevision,
      scheduled_at: scheduledAt,
    }),
  });
}

export function validatePlanLayout(
  accessToken: string,
  planId: string,
  expectedRevision: number,
  workouts: Array<{ workout_id: string; scheduled_at: string }>,
): Promise<{ valid_for_generated_schedule: boolean; warnings: Array<{ message: string }> }> {
  return request(accessToken, `/api/v1/weekly-plans/${planId}/validate`, {
    method: 'POST',
    body: JSON.stringify({
      expected_revision: expectedRevision,
      workouts,
    }),
  });
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
