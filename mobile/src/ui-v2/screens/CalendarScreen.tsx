import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, View, type ScrollViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate, type CalendarMode } from '../../features/calendar/calendarDates';
import { addDays, isoDate } from '../../features/planning/planningDates';
import { DayHeader } from '../components/DayHeader';
import { MonthGrid } from '../components/MonthGrid';
import { CalendarDayList, WeekAgenda } from '../components/WeekAgenda';
import { Button } from '../primitives/Button';
import { Divider } from '../primitives/Divider';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { CalendarViewModel } from '../utils/calendarViewModel';

export function CalendarScreen({ model, mode, anchor, loading, error, onModeChange, onMove, onToday, onSelectDate, onRetry, onOpenWorkout, onBack, onProfile, controls, scrollProps }: {
  model: CalendarViewModel; mode: CalendarMode; anchor: string; loading: boolean; error: string | null;
  onModeChange: (mode: CalendarMode) => void; onMove: (direction: -1 | 1) => void; onToday: () => void;
  onSelectDate: (date: string) => void; onRetry: () => void; onOpenWorkout: (id: string) => void; onBack: () => void;
  controls?: ReactNode; scrollProps?: ScrollViewProps;
  onProfile?: () => void;
}) {
  const { locale, t } = useLanguage();
  const fullDate = (date: string) => parseCalendarDate(date).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const period = mode === 'month' ? parseCalendarDate(anchor).toLocaleDateString(locale, { month: 'long', year: 'numeric' })
    : `${fullDate(model.days[0].date)} – ${fullDate(model.days[6].date)}`;
  return <SafeAreaView edges={['top', 'bottom']} style={styles.frame}>
    <ScrollView testID="calendar-scroll" {...scrollProps} style={styles.scroll} contentContainerStyle={styles.content}>
      {onProfile ? <Button variant="tertiary" label={t('planning.profile')} onPress={onProfile} /> : null}
      <Button variant="tertiary" label={t('week.return')} onPress={onBack} />
      <Text variant="screenTitle" accessibilityRole="header">{t('calendar.title')}</Text>
      <Text variant="supporting">{t('calendar.approvedOnly')}</Text>
      <View accessibilityRole="tablist" style={styles.toolbar}>
        {(['week', 'month'] as const).map((value) => <Button key={value} accessibilityRole="tab" accessibilityState={{ selected: mode === value }}
          label={t(`calendar.${value}`)} variant={mode === value ? 'primary' : 'secondary'} onPress={() => onModeChange(value)} />)}
      </View>
      <Text variant="cardTitle" accessibilityRole="header">{period}</Text>
      <View style={styles.toolbar}>
        <Button variant="tertiary" label={t('common.previous')} accessibilityLabel={t(mode === 'week' ? 'calendar.previousWeek' : 'calendar.previousMonth')} onPress={() => onMove(-1)} />
        <Button variant="tertiary" label={t('common.today')} onPress={onToday} />
        <Button variant="tertiary" label={t('common.next')} accessibilityLabel={t(mode === 'week' ? 'calendar.nextWeek' : 'calendar.nextMonth')} onPress={() => onMove(1)} />
      </View>
      {loading ? <Text accessibilityLiveRegion="polite">{t('common.loading')}</Text> : null}
      {error ? <View style={styles.notice}><Text accessibilityLiveRegion="polite" style={{ color: colors.destructive }}>{t('calendar.loadFailed')}</Text><Text>{error}</Text><Button label={t('calendar.retry')} onPress={onRetry} /></View> : null}
      {mode === 'week' ? <WeekAgenda days={model.days} known={model.rangeKnown} onOpenWorkout={onOpenWorkout} /> : <>
        <MonthGrid days={model.days} known={model.rangeKnown} onSelectDate={onSelectDate} />
        <View testID="calendar-selected-day" style={styles.notice}>
          <DayHeader day={model.selectedDay} known={model.rangeKnown} />
          <Button variant="secondary" label={t('calendar.selectedWeek')} onPress={() => onModeChange('week')} />
          <CalendarDayList day={model.selectedDay} known={model.rangeKnown} onOpenWorkout={onOpenWorkout} />
        </View>
      </>}
      {!model.rangeKnown && model.loadedRange ? <View testID="calendar-retained-range" style={styles.notice}>
        <Text variant="label">{t('calendar.retainedRange', { from: fullDate(model.loadedRange.fromDate), to: fullDate(isoDate(addDays(model.loadedRange.toDate, -1))) })}</Text>
        {model.retainedDays.length ? <WeekAgenda days={model.retainedDays} known onOpenWorkout={onOpenWorkout} /> : <Text>{t('calendar.retainedEmpty')}</Text>}
      </View> : null}
      {__DEV__ && controls ? <View style={styles.notice}><Divider />{controls}</View> : null}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background }, scroll: { flex: 1, overflow: 'hidden' },
  content: { padding: layout.phoneGutter, paddingBottom: space[32], width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center', gap: space[16] },
  toolbar: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] }, notice: { gap: space[12] },
});
