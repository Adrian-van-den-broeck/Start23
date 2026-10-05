import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { WeekHomeViewModel } from '../utils/weekHomeViewModel';
import { SportIndicator } from './SportIndicator';
import { QuickActionRow } from './QuickActionRow';
export function NextSession({ model, onOpenWorkout }: { model: WeekHomeViewModel; onOpenWorkout: (id: string) => void; }) {
  const { t, locale } = useLanguage();
  if (!model.sessionDate || !model.sessions.length) return null;
  const date = new Date(model.sessionDate + 'T12:00:00').toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' });
  const count = t(model.sessions.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: model.sessions.length });
  return <View style={styles.group}>
    {model.sessions.map(({ id, summary }, index) => {
      const focus = index === 0;
      const measures = [summary.measures.durationMinutes !== null ? t('common.durationMinutes', { minutes: summary.measures.durationMinutes }) : null,
      summary.measures.distanceMeters !== null ? t('detail.meters', { value: summary.measures.distanceMeters.toLocaleString(locale) }) : null].filter((value): value is string => value !== null);
      const content = <>
        {focus ? <View style={styles.context}>
          <Text variant="label" tone="textInverse">{t(model.isToday ? 'week.todayLabel' : 'week.nextDay')}{model.isToday ? ` · ${count}` : ''}</Text>
          {!model.isToday ? <><Text variant="body" tone="textInverse">{date}</Text><Text variant="supporting" tone="textInverse">{count}</Text></> : null}
        </View> : <Divider />}
        <SportIndicator discipline={summary.discipline} />
        <Text variant={focus ? 'sectionTitle' : 'cardTitle'} tone={focus ? 'textInverse' : 'text'} accessibilityRole="header">{summary.name}</Text>
        {measures.map((measure, measureIndex) => <Text key={measureIndex} variant={focus && measureIndex === 0 ? 'numeric' : 'supporting'} tone={focus ? 'textInverse' : 'text'}>{measure}</Text>)}
        <Text variant="supporting" tone={focus ? 'textInverse' : 'text'}>{t(`detail.intensity.${summary.intensity}`)} · {t(`detail.status.${summary.status}`)}</Text>
        {summary.description ? <Text variant="supporting" tone={focus ? 'textInverse' : 'text'}>{summary.description}</Text> : null}
        {focus ? <View style={styles.action}><Button variant="secondary" label={t('week.viewWorkoutLabel')}
          accessibilityLabel={t('week.viewWorkout', { name: summary.name })} onPress={() => onOpenWorkout(id)} /></View>
          : <QuickActionRow label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })} onAction={() => onOpenWorkout(id)} />}
      </>;
      return focus ? <Card key={id} testID="week-session-hero" style={styles.focus}>{content}</Card>
        : <View key={id} testID="week-session-sibling" style={styles.sibling}>{content}</View>;
    })}
  </View>;
}
const styles = StyleSheet.create({
  group: { gap: space[12] }, context: { gap: space[4] },
  focus: { backgroundColor: colors.primary, padding: layout.focusPadding, gap: space[8] },
  sibling: { gap: space[8] }, action: { marginTop: space[8] },
});
