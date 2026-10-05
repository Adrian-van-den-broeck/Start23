import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Divider } from '../primitives/Divider';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';
import { DayHeader } from './DayHeader';
import { SportIndicator } from './SportIndicator';

export function CalendarDayList({ day, known, onOpenWorkout }: { day: CalendarDay; known: boolean; onOpenWorkout: (id: string) => void; }) {
  const { t, locale } = useLanguage();
  return <View style={styles.rows}>
    {!known ? <Text tone="textMuted">{t('calendar.rangeUnknown')}</Text> : null}
    {day.workouts.map(({ id, summary }) => <View key={id} testID={`calendar-workout-${id}`} style={styles.workout}>
      <SportIndicator discipline={summary.discipline} />
      <Text variant="cardTitle">{summary.name}</Text>
      {summary.measures.durationMinutes !== null ? <Text accessibilityLabel={t('detail.minutesSpoken', { value: summary.measures.durationMinutes })}>{t('common.durationMinutes', { minutes: summary.measures.durationMinutes })}</Text> : null}
      {summary.measures.distanceMeters !== null ? <Text accessibilityLabel={t('detail.metersSpoken', { value: summary.measures.distanceMeters })}>{t('detail.meters', { value: summary.measures.distanceMeters.toLocaleString(locale) })}</Text> : null}
      <Text variant="supporting">{t(`detail.intensity.${summary.intensity}`)} · {t(`detail.status.${summary.status}`)}</Text>
      {summary.description ? <Text variant="supporting">{summary.description}</Text> : null}
      <Button variant="tertiary" label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })} onPress={() => onOpenWorkout(id)} />
      <Divider />
    </View>)}
    {day.restDays.map((rest, index) => <View key={`${rest.reason}-${index}`} style={styles.rows}>
      <Text variant="label">{t('common.restDay')}</Text>
      <Text variant="supporting">{t(rest.reason === 'restriction_rest' ? 'calendar.restrictionRest' : 'calendar.scheduledRest')}</Text>
    </View>)}
    {known && !day.workouts.length && !day.restDays.length ? <Text tone="textMuted">{t('calendar.emptyDay')}</Text> : null}
  </View>;
}

export function WeekAgenda({ days, known, onOpenWorkout }: { days: readonly CalendarDay[]; known: boolean; onOpenWorkout: (id: string) => void; }) {
  return <View testID="calendar-week-agenda" style={styles.days}>
    {days.map((day) => <View key={day.date} testID={`calendar-day-${day.date}`} style={styles.day}>
      <DayHeader day={day} known={known} />
      <CalendarDayList day={day} known={known} onOpenWorkout={onOpenWorkout} />
      <Divider />
    </View>)}
  </View>;
}
const styles = StyleSheet.create({
  days: { gap: space[16] }, day: { gap: space[8] }, rows: { gap: space[8] }, workout: { gap: space[8] },
});
