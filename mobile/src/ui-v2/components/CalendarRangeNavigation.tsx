import { useState } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate, type CalendarMode } from '../../features/calendar/calendarDates';
import { Button } from '../primitives/Button';
import { Icon } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { CalendarViewModel } from '../utils/calendarViewModel';

function RangeArrow({ direction, label, onPress }: { direction: -1 | 1; label: string; onPress: () => void; }) {
  const [focused, setFocused] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} style={[styles.arrow, focused && styles.focused]}>
    <Icon name={direction === -1 ? 'chevronLeft' : 'chevron'} />
  </Pressable>;
}
export function CalendarRangeNavigation({ model, mode, anchor, onMove, onToday }: {
  model: CalendarViewModel; mode: CalendarMode; anchor: string; onMove: (direction: -1 | 1) => void; onToday: () => void;
}) {
  const { locale, t } = useLanguage();
  const { fontScale } = useWindowDimensions();
  const first = parseCalendarDate(model.days[0].date);
  const last = parseCalendarDate(model.days[model.days.length - 1].date);
  const fullDate = (date: Date) => date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const period = mode === 'month' ? parseCalendarDate(anchor).toLocaleDateString(locale, { month: 'long', year: 'numeric' })
    : `${first.toLocaleDateString(locale, { day: 'numeric', month: 'short', ...(first.getFullYear() !== last.getFullYear() ? { year: 'numeric' as const } : {}) })} \u2013 ${last.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })}`;
  const heading = <Text variant="cardTitle" accessibilityRole="header" accessibilityLabel={mode === 'week' ? `${fullDate(first)} \u2013 ${fullDate(last)}` : period} style={styles.period}>{period}</Text>;
  const previous = <RangeArrow direction={-1} label={t(mode === 'week' ? 'calendar.previousWeek' : 'calendar.previousMonth')} onPress={() => onMove(-1)} />;
  const next = <RangeArrow direction={1} label={t(mode === 'week' ? 'calendar.nextWeek' : 'calendar.nextMonth')} onPress={() => onMove(1)} />;
  return <View testID="calendar-range-navigation" style={styles.container}>
    {fontScale >= 1.5 ? <>{heading}<View style={styles.row}>{previous}<Button variant="tertiary" label={t('common.today')} onPress={onToday} />{next}</View></> :
      <View style={styles.row}>{previous}<View style={styles.center}>{heading}<Button variant="tertiary" label={t('common.today')} onPress={onToday} /></View>{next}</View>}
  </View>;
}
const styles = StyleSheet.create({
  container: { gap: space[8] }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: space[8] },
  center: { flex: 1, alignItems: 'center' }, period: { textAlign: 'center' },
  arrow: { width: layout.iconButton, height: layout.iconButton, alignItems: 'center', justifyContent: 'center',
    backgroundColor: colors.surface, borderRadius: radius.pill, borderWidth: layout.controlEdge, borderColor: colors.borderControl },
  focused: { borderWidth: layout.focusOutline, borderColor: colors.focus },
});
