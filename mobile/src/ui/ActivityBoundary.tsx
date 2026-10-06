import { useEffect, type ComponentProps } from 'react';
import { View } from 'react-native';
import { useActivityFlow } from '../features/activities/ActivityFlowProvider';
import { localWeekKey, suggestedWorkout } from '../features/activities/activityPresentation';
import { useLanguage } from '../i18n/LanguageProvider';
import { ActivityScreen } from '../screens/ActivityScreen';
import { ActivitiesScreen } from '../ui-v2/screens/ActivitiesScreen';
import { ActivityEntryScreen } from '../ui-v2/screens/ActivityEntryScreen';
import { ActivityFeedbackScreen } from '../ui-v2/screens/ActivityFeedbackScreen';
import { activityViewModel } from '../ui-v2/utils/activityViewModel';
import { UiVersionControl } from './UiVersionControl';
import type { UiVersion } from './uiVersion';

export type ActivityView = 'history' | 'entry' | 'feedback';
export function ActivityBoundary(props: ComponentProps<typeof ActivityScreen> & {
  version: UiVersion; view: ActivityView; onView: (view: ActivityView) => void;
  correctionId: string | null; onCorrection: (id: string | null) => void;
  onVersion: (version: UiVersion) => void; switchLocked: boolean;
}) {
  const flow = useActivityFlow();
  const { language, locale } = useLanguage();
  useEffect(() => { if (props.version === 'v2') void flow.ensureActivitiesLoaded(); }, [props.version, flow.ensureActivitiesLoaded]);
  useEffect(() => {
    props.onNavigationBusyChange?.(flow.busy);
    return () => props.onNavigationBusyChange?.(false);
  }, [flow.busy, props.onNavigationBusyChange]);
  // Presentation transition only; no API call or local pending-feedback copy.
  useEffect(() => {
    if (props.version !== 'v2' || flow.busy) return;
    if (props.view === 'entry' && flow.feedbackActivity) props.onView('feedback');
    if (props.view === 'feedback' && !flow.feedbackActivity && !props.correctionId) props.onView('history');
  }, [props.version, props.view, props.correctionId, props.onView, flow.busy, flow.feedbackActivity]);
  const controls = <UiVersionControl disabled={props.switchLocked || flow.busy} onSelect={props.onVersion} />;
  if (props.version === 'v1') return <View style={{ flex: 1 }}>{controls}<ActivityScreen
    onBack={props.onBack} onOpenProfile={props.onOpenProfile} onSignOut={props.onSignOut} /></View>;
  const correction = props.correctionId ? flow.activities.find(activity => activity.id === props.correctionId) : undefined;
  const feedback = correction ?? (props.view === 'feedback' || props.view === 'entry' ? flow.feedbackActivity : undefined);
  if (feedback) return <ActivityFeedbackScreen activity={activityViewModel(feedback, locale, language)}
    heartRate={flow.heartRateByActivity[feedback.id] ?? ''} busy={flow.busy} error={flow.error} controls={controls}
    onBack={() => { if (!flow.busy) { props.onCorrection(null); props.onView('history'); } }}
    onHeartRate={value => flow.setHeartRateByActivity(current => ({ ...current, [feedback.id]: value }))}
    onSelect={value => { if (correction) props.onCorrection(null); return flow.saveRpe(feedback.id, value); }} />;
  if (props.view === 'entry') return <ActivityEntryScreen
    discipline={flow.discipline} duration={flow.duration} distance={flow.distance} startedAt={flow.startedAt}
    timezone={flow.athleteTimezone} selectedId={flow.selectedWorkout?.id ?? flow.selectedExternal?.id ?? null}
    selectedName={flow.selectedWorkout?.name ?? flow.selectedExternal?.name ?? null}
    choices={[
      ...flow.workouts.map(workout => ({
        id: workout.id, kind: 'workout' as const, name: workout.name, discipline: workout.discipline,
        date: new Date(`${workout.scheduled_date}T12:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
      })),
      ...flow.externalActivities.map(activity => ({
        id: activity.id, kind: 'external' as const, name: activity.name, discipline: activity.discipline,
        date: new Date(activity.scheduled_at).toLocaleString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
      })),
    ]} busy={flow.busy} error={flow.error} blocked={flow.pendingRpe.length > 0} controls={controls}
    onBack={() => { if (!flow.busy) props.onView('history'); }}
    onDiscipline={flow.setDiscipline} onDuration={flow.setDuration} onDistance={flow.setDistance} onStartedAt={flow.setStartedAt}
    onChoose={choice => {
      if (!choice) flow.selectWorkout(null);
      else if (choice.kind === 'workout') { const workout = flow.workouts.find(item => item.id === choice.id); if (workout) flow.selectWorkout(workout); }
      else { const activity = flow.externalActivities.find(item => item.id === choice.id); if (activity) flow.selectExternal(activity); }
    }} onSave={flow.save} />;
  const now = new Date();
  return <ActivitiesScreen rows={flow.activities.map(activity => {
    const match = activity.match_status === 'unmatched' && activity.processing_state === 'awaiting_rpe' ? suggestedWorkout(activity, flow.workouts) : null;
    return {
      activity: activityViewModel(activity, locale, language),
      canCorrect: activity.rpe !== null && localWeekKey(new Date(activity.started_at), activity.timezone) === localWeekKey(now, activity.timezone),
      match: match ? { id: match.id, name: match.name } : null
    };
  })} pending={flow.feedbackActivity ? activityViewModel(flow.feedbackActivity, locale, language) : null}
    busy={flow.busy} error={flow.error} controls={controls} onBack={props.onBack}
    onProfile={props.onOpenProfile ?? (() => { void props.onSignOut(); })}
    onAdd={() => { if (!flow.busy && flow.pendingRpe.length === 0) props.onView('entry'); }}
    onFeedback={() => props.onView('feedback')} onCorrect={props.onCorrection} onMatch={flow.confirmMatch} />;
}
