import { StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Button } from '../primitives/Button';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';
import { DayHeader } from './DayHeader';
import { WorkoutSummary } from './WorkoutSummary';

export function CalendarDayList({ day, known, onOpenWorkout, onMoveWorkout }: { day: CalendarDay; known: boolean; onOpenWorkout: (id: string) => void; onMoveWorkout?: (id: string) => (() => void) | undefined; }) {
  const { t } = useLanguage();
  return <View style={styles.rows}>
    {!known ? <Text tone="textMuted">{t('calendar.rangeUnknown')}</Text> : null}
    {day.workouts.map(({ id, summary }) => {
      const move = onMoveWorkout?.(id);
      return <View key={id} testID={`calendar-workout-${id}`}>
        <WorkoutSummary summary={summary} footer={<View style={styles.actions}>
          <Button label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })}
            trailingIcon="forward" onPress={() => onOpenWorkout(id)} />
          {move ? <Button variant="secondary" label={t('move.entry')} accessibilityLabel={t('move.entryLabel', { name: summary.name })} onPress={move} /> : null}
        </View>} />
      </View>;
    })}
    {day.restDays.map((rest, index) => <View key={`${rest.reason}-${index}`} style={styles.rest}>
      <Text variant="label">{t('common.restDay')}</Text>
      <Text variant="supporting" tone="textMuted">{t(rest.reason === 'restriction_rest' ? 'calendar.restrictionRest' : 'calendar.scheduledRest')}</Text>
    </View>)}
    {known && !day.workouts.length && !day.restDays.length ? <Text tone="textMuted" style={styles.empty}>{t('calendar.emptyDay')}</Text> : null}
  </View>;
}

export function WeekAgenda({ days, known, onOpenWorkout, onMoveWorkout }: { days: readonly CalendarDay[]; known: boolean; onOpenWorkout: (id: string) => void; onMoveWorkout?: (id: string) => (() => void) | undefined; }) {
  const { locale } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 360 || fontScale >= 1.5;
  return <View testID="calendar-week-agenda">
    {!stacked && days.length === 7 ? <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.weekdays}>
      {days.slice(0, 7).map(day => <Text key={day.date} variant="supporting" tone="textMuted" style={styles.weekday}>
        {parseCalendarDate(day.date).toLocaleDateString(locale, { weekday: 'short' })}
      </Text>)}
    </View> : null}
    {days.map((day) => <View key={day.date} testID={`calendar-day-${day.date}`} style={[styles.day, stacked && styles.stacked]}>
      <View style={!stacked && styles.date}><DayHeader day={day} known={known} rail={!stacked} /></View>
      {!stacked && days.length === 7 ? <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.rail}>
        <View style={styles.line} /><View style={styles.node} />
      </View> : null}
      <View style={[styles.dayContent, stacked && styles.stackedContent]}>
        <CalendarDayList day={day} known={known} onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} />
      </View>
    </View>)}
  </View>;
}
const styles = StyleSheet.create({
  weekdays: { flexDirection: 'row', paddingBottom: space[16] }, weekday: { flex: 1, textAlign: 'center', textTransform: 'uppercase', fontWeight: '600' },
  day: { flexDirection: 'row', borderTopWidth: layout.decorativeLine, borderColor: colors.border },
  stacked: { flexDirection: 'column', paddingVertical: space[16], gap: space[16] },
  date: { width: 64, paddingVertical: space[16] },
  rail: { width: space[16], alignSelf: 'stretch', alignItems: 'center' },
  line: { width: layout.decorativeLine, flex: 1, backgroundColor: colors.border },
  node: { position: 'absolute', top: space[32], width: 12, height: 12, borderRadius: radius.pill,
    borderWidth: layout.decorativeLine, borderColor: colors.borderControl, backgroundColor: colors.surfaceSubtle },
  dayContent: { flex: 1, paddingLeft: space[12], paddingVertical: space[16], justifyContent: 'center', minHeight: 96 },
  stackedContent: { flex: 0, paddingLeft: 0, paddingVertical: 0, minHeight: 0 },
  rows: { gap: space[16] }, actions: { gap: space[12] }, rest: { gap: space[4] }, empty: { fontStyle: 'italic' },
});
