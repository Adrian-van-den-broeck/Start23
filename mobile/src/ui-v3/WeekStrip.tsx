import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useLanguage } from '../i18n/LanguageProvider';
import { parseCalendarDate } from '../features/calendar/calendarDates';
import { Icon } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, radius } from '../ui-v2/tokens';
import type { WeekDay } from '../ui-v2/utils/weekHomeViewModel';
import { identity } from './tokens';

// The approved week at a glance. One target opens the calendar, so the
// strip replaces the separate progress bar, count sentence and week row.
export function WeekStrip({ days, progress, disabled, onOpen }: {
  days: readonly WeekDay[]; progress: Readonly<{ completed: number; planned: number }>; disabled: boolean; onOpen: () => void;
}) {
  const { t, locale } = useLanguage();
  const [pressed, setPressed] = useState(false);
  const [focused, setFocused] = useState(false);
  const summary = t(progress.planned === 1 ? 'week.progress.one' : 'week.progress', progress);
  return <Pressable testID="week-strip" accessibilityRole="button" accessibilityLabel={t('week.action.calendar')}
    accessibilityHint={summary} accessibilityState={{ disabled }} disabled={disabled} onPress={onOpen}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={[styles.strip, pressed && styles.pressed, disabled && styles.disabled, focused && styles.focused]}>
    <View style={styles.header} accessible={false} importantForAccessibility="no-hide-descendants">
      <Text variant="label">{t('week.progressShort', progress)}</Text>
      <View style={styles.link}>
        <Text variant="label" tone="primary">{t('week.action.calendar')}</Text>
        <Icon name="chevron" size={20} color={colors.primary} />
      </View>
    </View>
    <View style={styles.days} accessible={false} importantForAccessibility="no-hide-descendants">
      {days.map((day) => {
        const date = parseCalendarDate(day.date);
        const done = day.planned > 0 && day.completed === day.planned;
        return <View key={day.date} testID={`week-strip-${day.date}`} style={styles.day}>
          <Text variant="caption" tone={day.today ? 'warning' : 'textMuted'} style={styles.weekday}>
            {date.toLocaleDateString(locale, { weekday: 'short' }).replace('.', '')}
          </Text>
          <View style={[styles.date, day.next && styles.next, day.today && !day.next && styles.today]}>
            <Text variant="label" tone={day.next ? 'textInverse' : 'text'}>{date.getDate()}</Text>
          </View>
          <View style={styles.marks}>
            {done ? <Icon name="check" size={20} color={colors.success} />
              : day.disciplines.slice(0, 2).map((sport) => <Icon key={sport} name={sport} size={20} color={colors.sport[sport].text} />)}
            {!done && day.disciplines.length > 2 ? <Text variant="caption" tone="primary">+</Text> : null}
            {day.planned === 0 && day.rest ? <Icon name="minus" size={20} color={colors.textMuted} /> : null}
          </View>
        </View>;
      })}
    </View>
  </Pressable>;
}

const styles = StyleSheet.create({
  strip: { gap: 12, paddingVertical: 14, paddingHorizontal: 12, borderRadius: 20, backgroundColor: colors.surface,
    borderWidth: layout.focusOutline, borderColor: 'transparent', minHeight: layout.touch },
  pressed: { backgroundColor: colors.primarySoft },
  disabled: { opacity: 0.6 },
  focused: { borderColor: colors.focus },
  header: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8, paddingHorizontal: 4 },
  link: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  days: { flexDirection: 'row' },
  day: { flex: 1, alignItems: 'center', gap: 6 },
  weekday: { textTransform: 'uppercase' },
  date: { width: 36, height: 36, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center',
    borderWidth: layout.focusOutline, borderColor: 'transparent' },
  next: { backgroundColor: colors.primary },
  today: { borderColor: identity.orange },
  marks: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', minHeight: 20, gap: 2 },
});
