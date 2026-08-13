import type {
  AthleteProfile,
  AvailabilityWindow,
  CalendarResponse,
  ChangeProposal,
  CompletedActivity,
  Discipline,
  OnboardingComplete,
  OnboardingState,
  PlannedExternalActivity,
  PrimaryRaceGoal,
  TrainingHistoryEntry,
  WeeklyCheckIn,
  WeeklyPlan,
  WeeklyPlanProposal,
  WorkoutDeck,
  ZoneBoundary,
  ZoneProfile,
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

function validationMessage(body: ErrorEnvelope): string | null {
  if (body.error?.code !== 'validation_failed') return null;
  const fields = new Set(
    body.error.details?.violations
      ?.flatMap((violation) => violation.location ?? [])
      .filter((part) => part !== 'body') ?? [],
  );
  if (fields.has('target_date')) {
    return 'Gebruik een toekomstige racedatum in het formaat JJJJ-MM-DD.';
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
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    throw new Error(
      validationMessage(body) ??
        body.error?.message ??
        'De wijziging kon niet worden opgeslagen.',
    );
  }
  return (await response.json()) as T;
}

export function getOnboarding(accessToken: string): Promise<OnboardingState> {
  return request(accessToken, '/api/v1/onboarding');
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
