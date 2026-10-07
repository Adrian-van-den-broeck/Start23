import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { WeekHomeViewModel } from '../utils/weekHomeViewModel';
import { WorkoutSummary } from './WorkoutSummary';

export function NextSession({ model, onOpenWorkout }: { model: WeekHomeViewModel; onOpenWorkout: (id: string) => void; }) {
  const { t, locale } = useLanguage();
  if (!model.sessionDate || !model.sessions.length) return null;
  const date = new Date(model.sessionDate + 'T12:00:00').toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' });
  const count = t(model.sessions.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: model.sessions.length });
  return <View style={styles.group}>
    {model.sessions.map(({ id, summary }, index) => <View key={id} testID={index === 0 ? 'week-session-hero' : 'week-session-sibling'}>
      <WorkoutSummary summary={summary} variant="focus" context={index === 0 ? <View style={styles.context}>
        <Text variant="label">{t(model.isToday ? 'week.todayLabel' : 'week.nextDay')}{model.isToday ? ` · ${count}` : ''}</Text>
        {!model.isToday ? <><Text tone="textMuted">{date}</Text><Text variant="supporting" tone="textMuted">{count}</Text></> : null}
      </View> : null} footer={<Button label={t('week.viewWorkoutLabel')}
        accessibilityLabel={t('week.viewWorkout', { name: summary.name })} trailingIcon="forward" onPress={() => onOpenWorkout(id)} />} />
    </View>)}
  </View>;
}
const styles = StyleSheet.create({ group: { gap: space[12] }, context: { gap: space[4] } });
