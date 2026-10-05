import { useState } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';

export function MonthGrid({ days, known, onSelectDate }: { days: readonly CalendarDay[]; known: boolean; onSelectDate: (date: string) => void; }) {
  const { locale, t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const [focusedDate, setFocusedDate] = useState<string | null>(null);
  const list = (Math.min(width, layout.readingWidth) - layout.phoneGutter * 2) / 7 < layout.touch || fontScale > 1.2;
  return <View testID={list ? 'calendar-month-day-list' : 'calendar-month-grid'} style={styles.container}>
    {list ? <Text variant="label">{t('calendar.chooseDay')}</Text> : <View style={styles.weekdays}>
      {days.slice(0, 7).map((day) => <Text key={day.date} variant="supporting" accessible={false} style={styles.weekday}>
        {parseCalendarDate(day.date).toLocaleDateString(locale, { weekday: 'short' })}
      </Text>)}
    </View>}
    <View style={list ? styles.list : styles.grid}>
      {days.map((day) => {
        const date = parseCalendarDate(day.date);
        const dateLabel = date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        const count = t(day.workouts.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: day.workouts.length });
        const sports = [...new Set(day.workouts.map((workout) => workout.summary.discipline))];
        const info = [known ? count : t('calendar.rangeUnknown'), ...sports.map((sport) => t(`common.${sport}`)), day.restDays.length ? t('common.restDay') : '', day.today ? t('common.today') : ''].filter(Boolean).join(' · ');
        return <Pressable key={day.date} testID={`calendar-date-${day.date}`} accessibilityRole="button"
          accessibilityLabel={`${dateLabel} · ${info}`} accessibilityState={{ selected: day.selected }} onPress={() => onSelectDate(day.date)}
          onFocus={() => setFocusedDate(day.date)} onBlur={() => setFocusedDate(null)}
          style={[styles.date, list ? styles.listDate : styles.gridDate, day.selected && styles.selected, day.today && styles.today, focusedDate === day.date && styles.focused]}>
          <Text accessible={false} importantForAccessibility="no" variant={list ? 'body' : 'label'} tone={day.inMonth ? 'text' : 'textMuted'}>
            {list ? dateLabel : date.getDate()}{list && day.today ? ` · ${t('common.today')}` : ''}
          </Text>
          <Text accessible={false} importantForAccessibility="no" variant="supporting">{list ? info : known ? String(day.workouts.length) : '—'}</Text>
          {!list && (sports.length || day.restDays.length || day.today) ? <Text accessible={false} importantForAccessibility="no" variant="supporting">
            {[...sports.map((sport) => t(`calendar.sportShort.${sport}`)), day.restDays.length ? t('calendar.restShort') : '', day.today ? t('common.today') : ''].filter(Boolean).join(' · ')}
          </Text> : null}
        </Pressable>;
      })}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  container: { gap: space[8] }, weekdays: { flexDirection: 'row' }, weekday: { flex: 1, textAlign: 'center' },
  list: { gap: space[4] }, grid: { flexDirection: 'row', flexWrap: 'wrap' },
  date: { minWidth: layout.touch, minHeight: layout.touch, borderWidth: layout.focusOutline, borderColor: colors.border, padding: space[4], gap: space[4] },
  listDate: { width: '100%', padding: space[12] }, gridDate: { width: '14.285714%' },
  selected: { backgroundColor: colors.primarySoft, borderColor: colors.primary }, today: { borderColor: colors.focus },
  focused: { borderColor: colors.focus },
});
