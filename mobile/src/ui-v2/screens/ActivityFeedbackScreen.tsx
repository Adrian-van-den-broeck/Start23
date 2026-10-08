import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import type { CanonicalRpe } from '../../lib/rpe';
import { ActivitySummary } from '../components/ActivitySummary';
import { RpeChoices } from '../components/RpeChoices';
import { Input } from '../primitives/Input';
import { Card } from '../primitives/Card';
import { space } from '../tokens';
import { Screen } from '../primitives/Screen';
import type { ActivityViewModel } from '../utils/activityViewModel';
import { ActivityStatus } from './ActivitiesScreen';

export function ActivityFeedbackScreen({ activity, heartRate, busy, error, controls, onHeartRate, onSelect, onBack }: {
  activity: ActivityViewModel; heartRate: string; busy: boolean; error: string | null; controls: ReactNode;
  onHeartRate: (value: string) => void; onSelect: (value: CanonicalRpe) => Promise<void>; onBack: () => void;
}) {
  const { t } = useLanguage();
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <Screen title={t('activities.feedback')} titleVariant="screenTitle" onBack={onBack} backLabel={t('activities.return')} backDisabled={busy}
      scrollProps={{ keyboardShouldPersistTaps: 'handled', testID: 'activity-feedback-scroll' }}>
      <ActivityStatus busy={busy} error={error} />
      <Card elevated><ActivitySummary activity={activity} /></Card>
      <Card elevated padding="form">
        <Input icon="heartRate" label={t('activity.heartRate')} hint={t('activity.heartRateHint')} inputMode="numeric"
          value={heartRate} onChangeText={onHeartRate} disabled={busy} />
      </Card>
      <Card elevated padding="form">
        <RpeChoices discipline={activity.discipline} selectedValue={activity.rpe} busy={busy} onSelect={onSelect} />
      </Card>
      <View style={{ gap: space[24] }}>{controls}</View>
    </Screen>
  </KeyboardAvoidingView>;
}
