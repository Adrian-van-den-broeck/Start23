import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';
import type { CalendarDay } from '../utils/calendarViewModel';

export function DayHeader({ day, known = true, rail = false }: { day: CalendarDay; known?: boolean; rail?: boolean; }) {
  const { locale, t } = useLanguage();
  const value = parseCalendarDate(day.date);
  const date = value.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const count = t(day.workouts.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: day.workouts.length });
  const label = [date, day.today ? t('common.today') : '', known ? count : t('calendar.rangeUnknown'), day.restDays.length ? t('common.restDay') : ''].filter(Boolean).join(' \u00b7 ');
  return <View accessible accessibilityRole="header" accessibilityLabel={label} style={[styles.header, rail && styles.rail]}>
    {rail ? <>
      <Text accessible={false} variant="supporting" tone="textMuted" style={styles.weekday}>{value.toLocaleDateString(locale, { weekday: 'short' })}</Text>
      <Text accessible={false} variant="numeric" style={styles.number}>{value.getDate()}</Text>
    </> : <Text accessible={false} variant="cardTitle">{date}</Text>}
    {day.today ? <View style={styles.today}><Text accessible={false} variant="caption" tone="warning">{t('common.today')}</Text></View> : null}
  </View>;
}
const styles = StyleSheet.create({
  header: { gap: space[8], alignItems: 'flex-start' }, rail: { alignItems: 'center' },
  weekday: { textTransform: 'uppercase', fontWeight: '600' }, number: { fontWeight: '700' },
  today: { paddingHorizontal: space[4], paddingVertical: space[4], borderRadius: radius.inset, backgroundColor: colors.warningSoft },
});
