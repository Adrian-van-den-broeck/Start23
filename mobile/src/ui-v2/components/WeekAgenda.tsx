import { studioPresentation } from '../../ui-v3/presentation';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Icon } from '../primitives/Icon';
import { Button } from '../primitives/Button';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';
import { DayHeader } from './DayHeader';
import { WorkoutSummary } from './WorkoutSummary';

export function CalendarDayList({ day, known, onOpenWorkout, onMoveWorkout, hideEmpty = false }: { day: CalendarDay; known: boolean; onOpenWorkout: (id: string) => void; onMoveWorkout?: (id: string) => (() => void) | undefined; hideEmpty?: boolean; }) {
  const { t } = useLanguage();
  return <View style={styles.rows}>
    {!known ? <Text tone="textMuted">{t('calendar.rangeUnknown')}</Text> : null}
    {day.workouts.map(({ id, summary }) => {
      const move = onMoveWorkout?.(id);
      return <View key={id} testID={`calendar-workout-${id}`}>
        {studioPresentation ? <>
          <Pressable accessibilityRole="button" accessibilityLabel={t('week.viewWorkout', { name: summary.name })}
            accessibilityHint={[t(`common.${summary.discipline}`), t(`detail.status.${summary.status}`),
              summary.measures.durationMinutes !== null && t('detail.minutesSpoken', { value: summary.measures.durationMinutes }),
              summary.measures.distanceMeters !== null && t('detail.metersSpoken', { value: summary.measures.distanceMeters }),
              t(`detail.intensity.${summary.intensity}`)].filter(Boolean).join(', ')}
            onPress={() => onOpenWorkout(id)} style={styles.sessionRow}>
            <View style={[styles.sportTile, { backgroundColor: colors.sport[summary.discipline].soft }]}>
              <Icon name={summary.discipline} color={colors.sport[summary.discipline].text} />
            </View>
            <View style={styles.sessionText}>
              <Text variant="caption" tone="textMuted">{t(`common.${summary.discipline}`)} {'\u00b7'} {t(`detail.status.${summary.status}`)}</Text>
              <Text variant="label">{summary.name}</Text>
              <View style={styles.measures}>
                {summary.measures.durationMinutes !== null && <Text variant="supporting">{t('common.durationMinutes', { minutes: summary.measures.durationMinutes })}</Text>}
                {summary.measures.distanceMeters !== null && <Text variant="supporting">{t('detail.meters', { value: summary.measures.distanceMeters })}</Text>}
                <Text variant="supporting" tone="textMuted">{t(`detail.intensity.${summary.intensity}`)}</Text>
              </View>
            </View>
            <Icon name="chevron" size={20} color={colors.textMuted} />
          </Pressable>
          {move && <Button variant="tertiary" label={t('move.entry')} accessibilityLabel={t('move.entryLabel', { name: summary.name })} onPress={move} />}
        </> : <WorkoutSummary summary={summary} footer={<View style={styles.actions}>
          <Button label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })}
            trailingIcon="forward" onPress={() => onOpenWorkout(id)} />
          {move ? <Button variant="secondary" trailingIcon="calendar" label={t('move.entry')} accessibilityLabel={t('move.entryLabel', { name: summary.name })} onPress={move} /> : null}
        </View>} />}
      </View>;
    })}
    {day.restDays.map((rest, index) => <View key={`${rest.reason}-${index}`} style={styles.rest}>
      <Text variant="label">{t('common.restDay')}</Text>
      <Text variant="supporting" tone="textMuted">{t(rest.reason === 'restriction_rest' ? 'calendar.restrictionRest' : 'calendar.scheduledRest')}</Text>
    </View>)}
    {/* The day header already announces zero workouts; V3's week agenda drops the repeated sentence. */}
    {known && !hideEmpty && !day.workouts.length && !day.restDays.length ? <Text tone="textMuted" style={styles.empty}>{t('calendar.emptyDay')}</Text> : null}
  </View>;
}

export function WeekAgenda({ days, known, onOpenWorkout, onMoveWorkout }: { days: readonly CalendarDay[]; known: boolean; onOpenWorkout: (id: string) => void; onMoveWorkout?: (id: string) => (() => void) | undefined; }) {
  const { locale } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 360 || fontScale >= 1.5;
  return <View testID="calendar-week-agenda">
    {!studioPresentation && !stacked && days.length === 7 ? <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.weekdays}>
      {days.slice(0, 7).map(day => <Text key={day.date} variant="supporting" tone="textMuted" style={styles.weekday}>
        {parseCalendarDate(day.date).toLocaleDateString(locale, { weekday: 'short' })}
      </Text>)}
    </View> : null}
    {days.map((day) => { const quiet = studioPresentation && known && !day.workouts.length && !day.restDays.length;
      return <View key={day.date} testID={`calendar-day-${day.date}`} style={[styles.day, stacked && styles.stacked, quiet && stacked && styles.quietStacked]}>
      <View style={[!stacked && styles.date, quiet && !stacked && styles.quietDate]}><DayHeader day={day} known={known} rail={!stacked} /></View>
      {!studioPresentation && !stacked && days.length === 7 ? <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.rail}>
        <View style={styles.line} /><View style={styles.node} />
      </View> : null}
      <View style={[styles.dayContent, stacked && styles.stackedContent, quiet && styles.quietContent]}>
        <CalendarDayList day={day} known={known} onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} hideEmpty={studioPresentation} />
      </View>
    </View>; })}
  </View>;
}
const styles = StyleSheet.create({
  sessionRow: { flexDirection: 'row', gap: 8, minHeight: 48, alignItems: 'center' },
  sportTile: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  sessionText: { flex: 1, gap: 2 }, measures: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 8 },
  weekdays: { flexDirection: 'row', paddingBottom: space[16] }, weekday: { flex: 1, textAlign: 'center', textTransform: 'uppercase', fontWeight: '600' },
  day: { flexDirection: 'row', borderTopWidth: layout.decorativeLine, borderColor: colors.border },
  stacked: { flexDirection: 'column', paddingVertical: space[16], gap: space[16] },
  date: { width: 64, paddingVertical: space[16] },
  rail: { width: space[16], alignSelf: 'stretch', alignItems: 'center' },
  line: { width: layout.decorativeLine, flex: 1, backgroundColor: colors.border },
  node: { position: 'absolute', top: space[32], width: 12, height: 12, borderRadius: radius.pill,
    borderWidth: layout.decorativeLine, borderColor: colors.borderControl, backgroundColor: colors.surfaceSubtle },
  dayContent: { flex: 1, paddingLeft: space[12], paddingVertical: space[16], justifyContent: 'center', minHeight: studioPresentation ? 64 : 96 },
  stackedContent: { flex: 0, paddingLeft: 0, paddingVertical: 0, minHeight: 0 },
  quietDate: { paddingVertical: space[8] }, quietContent: { minHeight: 0, paddingVertical: space[8] }, quietStacked: { paddingVertical: space[8] },
  rows: { gap: space[16] }, actions: { gap: space[12] }, rest: { gap: space[4] }, empty: { fontStyle: 'italic' },
});
