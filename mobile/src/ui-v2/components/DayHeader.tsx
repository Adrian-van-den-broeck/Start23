import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Text } from '../primitives/Text';
import type { CalendarDay } from '../utils/calendarViewModel';

export function DayHeader({ day, known = true }: { day: CalendarDay; known?: boolean; }) {
  const { locale, t } = useLanguage();
  const date = parseCalendarDate(day.date).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const count = t(day.workouts.length === 1 ? 'week.sessionCount.one' : 'week.sessionCount.other', { count: day.workouts.length });
  const label = [date, day.today ? t('common.today') : '', known ? count : t('calendar.rangeUnknown'), day.restDays.length ? t('common.restDay') : ''].filter(Boolean).join(' · ');
  return <Text variant="cardTitle" accessibilityRole="header" accessibilityLabel={label}>{date}{day.today ? ` · ${t('common.today')}` : ''}</Text>;
}
