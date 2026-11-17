import { useState } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';

export function MonthGrid({ days, known, onSelectDate }: { days: readonly CalendarDay[]; known: boolean; onSelectDate: (date: string) => void; }) {
  const { locale, t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const [focusedDate, setFocusedDate] = useState<string | null>(null);
  // Include the real grid-card inset and perimeter when choosing the accessible list.
  const list = (Math.min(width, layout.readingWidth) - layout.phoneGutter * 2 - space[8] * 2 - layout.decorativeLine * 2) / 7 < layout.touch || fontScale > 1.2;
  const rows = Array.from({ length: Math.ceil(days.length / 7) }, (_, index) => days.slice(index * 7, index * 7 + 7));
  function dateCell(day: CalendarDay) {
    const date = parseCalendarDate(day.date);
    const dateLabel = date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    const count = t(day.workouts.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: day.workouts.length });
    const sports = [...new Set(day.workouts.map(workout => workout.summary.discipline))];
    const info = [known ? count : t('calendar.rangeUnknown'), ...sports.map(sport => t(`common.${sport}`)), day.restDays.length ? t('common.restDay') : '', day.today ? t('common.today') : ''].filter(Boolean).join(' \u00b7 ');
    const shortInfo = [...sports.map(sport => t(`calendar.sportShort.${sport}`)), day.restDays.length ? t('calendar.restShort') : ''].filter(Boolean).join(' \u00b7 ');
    return <Pressable key={day.date} testID={`calendar-date-${day.date}`} accessibilityRole="button"
      accessibilityLabel={`${dateLabel} \u00b7 ${info}`} accessibilityState={{ selected: day.selected }} onPress={() => onSelectDate(day.date)}
      onFocus={() => setFocusedDate(day.date)} onBlur={() => setFocusedDate(null)}
      style={[styles.date, list ? styles.listDate : styles.gridDate, day.selected && styles.selected, day.today && styles.today, focusedDate === day.date && styles.focused]}>
      <Text accessible={false} importantForAccessibility="no" variant="label" tone={day.inMonth ? 'text' : 'textMuted'}>
        {list ? date.toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' }) : date.getDate()}
      </Text>
      <Text accessible={false} importantForAccessibility="no" variant={list ? 'supporting' : 'caption'} tone="textMuted">{list ? info : known ? String(day.workouts.length) : '\u2014'}</Text>
      {!list && shortInfo ? <Text accessible={false} importantForAccessibility="no" variant="caption" tone="textMuted">{shortInfo}</Text> : null}
    </Pressable>;
  }
  return <Card testID={list ? 'calendar-month-day-list' : 'calendar-month-grid'} elevated style={[styles.container, !list && styles.gridCard]}>
    {list ? <>
      <Text variant="label">{t('calendar.chooseDay')}</Text>
      <View style={styles.list}>{days.map(dateCell)}</View>
    </> : <>
      <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.weekdays}>
        {days.slice(0, 7).map(day => <Text key={day.date} variant="supporting" tone="textMuted" style={styles.weekday}>
          {parseCalendarDate(day.date).toLocaleDateString(locale, { weekday: 'short' })}
        </Text>)}
      </View>
      <View style={styles.grid}>{rows.map((row, index) => <View key={index} style={styles.gridRow}>{row.map(dateCell)}</View>)}</View>
      <View style={styles.legend}>
        <Text variant="caption" tone="textMuted">{t('calendar.countKey')}</Text>
        <Text variant="caption" tone="textMuted">{(['run', 'bike', 'swim'] as const).map(sport => `${t(`calendar.sportShort.${sport}`)} = ${t(`common.${sport}`)}`).join(' \u00b7 ')}{` \u00b7 ${t('calendar.restShort')} = ${t('common.restDay')}`}</Text>
        {days.some(day => day.today) ? <Text variant="caption" tone="warning" style={styles.todayLegend}>{t('common.today')}: {parseCalendarDate(days.find(day => day.today)!.date).toLocaleDateString(locale, { day: 'numeric', month: 'short' })}</Text> : null}
      </View>
    </>}
  </Card>;
}
const styles = StyleSheet.create({
  container: { gap: space[12] }, gridCard: { padding: space[8] },
  weekdays: { flexDirection: 'row', paddingVertical: space[8] }, weekday: { flex: 1, textAlign: 'center', textTransform: 'uppercase', fontWeight: '600' },
  list: { gap: space[4] }, grid: { borderWidth: layout.decorativeLine, borderColor: colors.border, borderRadius: radius.control, overflow: 'hidden' },
  gridRow: { flexDirection: 'row' },
  date: { minWidth: layout.touch, minHeight: layout.touch, borderWidth: layout.focusOutline, borderColor: 'transparent', padding: space[4], gap: space[4], justifyContent: 'center' },
  listDate: { width: '100%', padding: space[12], borderRadius: radius.control, borderBottomColor: colors.border },
  gridDate: { flex: 1, alignItems: 'center', minHeight: 64, borderRightWidth: layout.decorativeLine, borderBottomWidth: layout.decorativeLine, borderRightColor: colors.border, borderBottomColor: colors.border },
  selected: { backgroundColor: colors.primarySoft, borderColor: colors.primary, borderRightColor: colors.primary, borderBottomColor: colors.primary, borderRadius: radius.control, borderRightWidth: layout.focusOutline, borderBottomWidth: layout.focusOutline },
  today: { backgroundColor: colors.warningSoft, borderRadius: radius.control }, focused: { borderColor: colors.focus, borderRightColor: colors.focus, borderBottomColor: colors.focus, borderRightWidth: layout.focusOutline, borderBottomWidth: layout.focusOutline },
  legend: { gap: space[4], paddingHorizontal: space[4], paddingBottom: space[4] },
  todayLegend: { alignSelf: 'flex-start', backgroundColor: colors.warningSoft, borderRadius: radius.inset, paddingHorizontal: space[4] },
});
