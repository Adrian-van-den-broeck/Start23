import type { CompletedActivity, Discipline } from '../../api/types';
import type { AppLanguage } from '../../i18n/LanguageProvider';
import { hasPartialObservedZoneTime } from '../../lib/onboardingForms';
import { rpeDescription } from '../../lib/rpe';
import { formatRunPace, observedRunPace } from '../../lib/runPace';

export type ActivityViewModel = Readonly<{
  id: string; discipline: Discipline; date: string;
  durationMinutes: string | null; distanceMeters: number | null; pace: string | null;
  source: 'canonical_summary' | null; rpe: number | null; rpeDescription: string | null;
  averageHeartRate: number | null; result: CompletedActivity['qualitative_result'];
  publicMessage: string | null; pending: boolean; correctionProposal: boolean;
  distanceOnly: boolean; partialCoverage: boolean;
  rpeGuidance?: CompletedActivity['session_rpe_guidance'];
}>;

// Only explicit public display fields cross the presentation boundary.
export function activityViewModel(activity: CompletedActivity, locale: string, language: AppLanguage): ActivityViewModel {
  return {
    id: activity.id, discipline: activity.discipline,
    date: new Date(activity.started_at).toLocaleString(locale, {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit', timeZone: activity.timezone,
    }),
    durationMinutes: activity.duration_minutes === null ? null : String(Number(activity.duration_minutes)),
    distanceMeters: activity.distance_meters,
    pace: activity.discipline !== 'run' ? null : activity.metrics?.average_pace_seconds_per_km != null
      ? formatRunPace(activity.metrics.average_pace_seconds_per_km)
      : observedRunPace(activity.duration_minutes, activity.distance_meters),
    source: activity.source === 'canonical_summary' ? activity.source : null,
    rpe: activity.rpe,
    rpeGuidance: activity.session_rpe_guidance?.map(row => ({ rpe: row.rpe, zone_number: row.zone_number, display_label: row.display_label })),
    rpeDescription: activity.rpe === null ? null : rpeDescription(activity.discipline, activity.rpe),
    averageHeartRate: activity.metrics?.average_heart_rate_bpm ?? null,
    result: activity.qualitative_result,
    publicMessage: language === 'nl' || activity.qualitative_result === 'awaiting_rpe' ? activity.public_message : null,
    pending: activity.processing_state === 'awaiting_rpe',
    correctionProposal: !!activity.correction_proposal_id,
    distanceOnly: activity.duration_minutes === null && !!activity.distance_meters,
    partialCoverage: hasPartialObservedZoneTime(activity.duration_minutes, activity.metrics?.zone_minutes),
  };
}
