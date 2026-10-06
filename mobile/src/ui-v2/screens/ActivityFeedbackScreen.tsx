import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import type { CanonicalRpe } from '../../lib/rpe';
import { ActivitySummary } from '../components/ActivitySummary';
import { RpeChoices } from '../components/RpeChoices';
import { Input } from '../primitives/Input';
import { Screen } from '../primitives/Screen';
import type { ActivityViewModel } from '../utils/activityViewModel';
import { ActivityStatus } from './ActivitiesScreen';

export function ActivityFeedbackScreen({ activity, heartRate, busy, error, controls, onHeartRate, onSelect, onBack }: {
  activity: ActivityViewModel; heartRate: string; busy: boolean; error: string | null; controls: ReactNode;
  onHeartRate: (value: string) => void; onSelect: (value: CanonicalRpe) => Promise<void>; onBack: () => void;
}) {
  const { t } = useLanguage();
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <Screen title={t('activities.feedback')} onBack={onBack} backLabel={t('activities.return')} backDisabled={busy}
      scrollProps={{ keyboardShouldPersistTaps: 'handled', testID: 'activity-feedback-scroll' }}>
      {controls}
      <ActivityStatus busy={busy} error={error} />
      <ActivitySummary activity={activity} />
      <Input label={t('activity.heartRate')} hint={t('activity.heartRateHint')} inputMode="numeric"
        value={heartRate} onChangeText={onHeartRate} disabled={busy} />
      <RpeChoices discipline={activity.discipline} selectedValue={activity.rpe} busy={busy} onSelect={onSelect} />
    </Screen>
  </KeyboardAvoidingView>;
}
