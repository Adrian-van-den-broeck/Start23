import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { colors, space } from '../tokens';
import type { WeekHomeViewModel } from '../utils/weekHomeViewModel';
import { SportIndicator } from './SportIndicator';
export function NextSession({ model, onOpenWorkout }: { model: WeekHomeViewModel; onOpenWorkout: (id: string) => void; }) {
  const { t, locale } = useLanguage();
  if (!model.sessionDate || !model.sessions.length) return null;
  const date = new Date(model.sessionDate + 'T12:00:00').toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' });
  return <View style={styles.group}>
    <Text variant="sectionTitle" accessibilityRole="header">{t(model.isToday ? 'week.today' : 'week.nextDate', { date, count: model.sessions.length })}</Text>
    {model.sessions.map(({ id, summary }, index) => <Card key={id} style={[styles.session, index === 0 && styles.focus]}>
      <SportIndicator discipline={summary.discipline} />
      <Text variant={index === 0 ? 'screenTitle' : 'cardTitle'} tone={index === 0 ? 'textInverse' : 'text'}>{summary.name}</Text>
      <Text variant={index === 0 ? 'numeric' : 'supporting'} tone={index === 0 ? 'textInverse' : 'text'}>
        {[summary.measures.durationMinutes !== null ? t('common.durationMinutes', { minutes: summary.measures.durationMinutes }) : null,
        summary.measures.distanceMeters !== null ? t('detail.meters', { value: summary.measures.distanceMeters.toLocaleString(locale) }) : null].filter(Boolean).join(' · ')}
      </Text>
      <Text variant="supporting" tone={index === 0 ? 'textInverse' : 'text'}>{t(`detail.intensity.${summary.intensity}`)} · {t(`detail.status.${summary.status}`)}</Text>
      {summary.description ? <Text variant="supporting" tone={index === 0 ? 'textInverse' : 'text'}>{summary.description}</Text> : null}
      <Button variant="secondary" label={t('week.viewWorkout', { name: summary.name })} onPress={() => onOpenWorkout(id)} />
    </Card>)}
  </View>;
}
const styles = StyleSheet.create({ group: { gap: space[12] }, session: { gap: space[12] }, focus: { backgroundColor: colors.primary } });
