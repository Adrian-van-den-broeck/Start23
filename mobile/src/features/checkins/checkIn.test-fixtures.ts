import type { CheckInRestriction, InjuryRestriction, WeeklyCheckIn, WeeklyCheckInContext } from '../../api/types';

export const alarmLabel = 'Ik begrijp dat alarmsymptomen medische beoordeling vragen en niet door dit plan worden beoordeeld.';
export const recurringLabel = 'Ik heb mijn terugkerende sportactiviteiten voor deze week gecontroleerd.';
export const none = (discipline: CheckInRestriction['discipline']): CheckInRestriction => ({
  discipline, status: 'none', source: 'athlete', athlete_plan_choice: 'resume_unrestricted',
});
export const restrictedAnswers: CheckInRestriction[] = [
  { discipline: 'run', status: 'professional_restricted', source: 'physician', athlete_plan_choice: 'keep_blocked', professional_advice: 'Arts: lopen geblokkeerd tot herbeoordeling.', professional_advice_at: '2026-10-01T09:15:00+02:00' },
  { discipline: 'swim', status: 'self_reported_blocked', source: 'athlete', athlete_plan_choice: 'keep_blocked', professional_advice: null, professional_advice_at: null },
  { discipline: 'bike', status: 'self_reported_limited', source: 'athlete', athlete_plan_choice: 'train_low_only' },
];
export const savedCheckIn: WeeklyCheckIn = {
  id: 'check-in-a', week_start: '2026-10-26', timezone: 'Europe/Amsterdam', status: 'open', context_revision: 4,
  plan_proposal_id: null, started_at: '2026-10-25T12:00:00Z', completed_at: null,
  context: {
    revision: 4, state: 'draft', source: 'structured_form', expires_at: '2026-11-01T23:00:00Z',
    fingerprint: 'a'.repeat(64), confirmed_at: null, blocked_dates: ['2026-10-28', '2026-10-30'],
    fatigue_level: 'moderate', missed_workout_reasons: ['injury', 'time_constraint'], recurring_activities_confirmed: true,
    external_activities: [{ name: 'Clubtraining', discipline: 'bike', scheduled_at: '2026-10-29T18:00:00+01:00', duration_minutes: '75.5', strenuous: false, recurring: true }],
    restrictions: restrictedAnswers, alarm_symptoms_acknowledged: true,
  },
};
export function activeRestriction(decision = restrictedAnswers[0]): InjuryRestriction {
  return { ...decision, id: `active-${decision.discipline}`, allowed_intensity: decision.status === 'self_reported_limited' ? 'low_only' : 'none',
    start_at: '2026-10-01T12:00:00Z', review_at: '2026-10-08T12:00:00Z', confirmed_at: '2026-10-01T12:00:00Z', cleared_at: null };
}
export function answers(context: WeeklyCheckInContext) {
  const { blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged } = context;
  return { blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged };
}
