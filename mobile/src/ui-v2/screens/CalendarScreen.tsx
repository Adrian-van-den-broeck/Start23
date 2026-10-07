import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, View, useWindowDimensions, type ScrollViewProps } from 'react-native';
import { ShellSafeArea } from '../components/ShellInsets';
import { HeaderAction, ProfileAction } from '../components/AppHeader';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { CalendarRangeNavigation } from '../components/CalendarRangeNavigation';
import { useLanguage } from '../../i18n/LanguageProvider';
import { parseCalendarDate, type CalendarMode } from '../../features/calendar/calendarDates';
import { addDays, isoDate } from '../../features/planning/planningDates';
import { DayHeader } from '../components/DayHeader';
import { MonthGrid } from '../components/MonthGrid';
import { CalendarDayList, WeekAgenda } from '../components/WeekAgenda';
import { Button } from '../primitives/Button';
import { Divider } from '../primitives/Divider';
import { Card } from '../primitives/Card';
import { SegmentedControl } from '../primitives/SegmentedControl';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { CalendarViewModel } from '../utils/calendarViewModel';

export function CalendarScreen({ model, mode, anchor, loading, error, onModeChange, onMove, onToday, onSelectDate, onRetry, onOpenWorkout, onMoveWorkout, onBack, onProfile, controls, scrollProps }: {
  model: CalendarViewModel; mode: CalendarMode; anchor: string; loading: boolean; error: string | null;
  onModeChange: (mode: CalendarMode) => void; onMove: (direction: -1 | 1) => void; onToday: () => void;
  onSelectDate: (date: string) => void; onRetry: () => void; onOpenWorkout: (id: string) => void; onBack: () => void;
  onMoveWorkout?: (id: string) => (() => void) | undefined;
  controls?: ReactNode; scrollProps?: ScrollViewProps;
  onProfile?: () => void;
}) {
  const { locale, t } = useLanguage();
  const fullDate = (date: string) => parseCalendarDate(date).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 393 || fontScale >= 1.5;
  return <ShellSafeArea style={styles.frame}>
    <ScrollView testID="calendar-scroll" {...scrollProps} style={styles.scroll} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={[styles.utility, stacked && styles.stackedUtility]}>
          <HeaderAction label={t('week.return')} onPress={onBack} />
          {onProfile ? <ProfileAction label={t('planning.profile')} onPress={onProfile} /> : null}
        </View>
        <View style={styles.titleRegion}>
          <View pointerEvents="none" style={styles.art}><HeaderLandscape variant={mode === 'week' ? 'ridges' : 'treesRiver'} behindText textStart={space[48] + space[16]} /></View>
          <View style={styles.titleCopy}>
            <Text variant="screenTitle" accessibilityRole="header">{t('calendar.title')}</Text>
            <Text variant="supporting" tone="textMuted">{t('calendar.approvedOnly')}</Text>
          </View>
        </View>
      </View>
      <SegmentedControl options={(['week', 'month'] as const).map(value => ({ value, label: t(`calendar.${value}`) }))}
        role="tab" value={mode} onChange={onModeChange} accessibilityLabel={t('calendar.title')} />
      <CalendarRangeNavigation model={model} mode={mode} anchor={anchor} onMove={onMove} onToday={onToday} />
      {loading ? <Text accessibilityLiveRegion="polite">{t('common.loading')}</Text> : null}
      {error ? <Card style={styles.notice}><Text accessibilityLiveRegion="polite" style={{ color: colors.destructive }}>{t('calendar.loadFailed')}</Text><Text>{error}</Text><Button label={t('calendar.retry')} onPress={onRetry} /></Card> : null}
      {mode === 'week' ? <WeekAgenda days={model.days} known={model.rangeKnown} onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} /> : <>
        <MonthGrid days={model.days} known={model.rangeKnown} onSelectDate={onSelectDate} />
        <View testID="calendar-selected-day" style={styles.notice}>
          <Card elevated style={styles.notice}>
            <DayHeader day={model.selectedDay} known={model.rangeKnown} />
            <Button variant="secondary" label={t('calendar.selectedWeek')} onPress={() => onModeChange('week')} />
            {!model.selectedDay.workouts.length ? <CalendarDayList day={model.selectedDay} known={model.rangeKnown} onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} /> : null}
          </Card>
          {model.selectedDay.workouts.length ? <CalendarDayList day={model.selectedDay} known={model.rangeKnown} onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} /> : null}
        </View>
      </>}
      {!model.rangeKnown && model.loadedRange ? <View testID="calendar-retained-range" style={styles.notice}>
        <Text variant="label">{t('calendar.retainedRange', { from: fullDate(model.loadedRange.fromDate), to: fullDate(isoDate(addDays(model.loadedRange.toDate, -1))) })}</Text>
        {model.retainedDays.length ? <WeekAgenda days={model.retainedDays} known onOpenWorkout={onOpenWorkout} onMoveWorkout={onMoveWorkout} /> : <Text>{t('calendar.retainedEmpty')}</Text>}
      </View> : null}
      {__DEV__ && controls ? <View style={styles.notice}><Divider />{controls}</View> : null}
    </ScrollView>
  </ShellSafeArea>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background }, scroll: { flex: 1 },
  content: { padding: layout.phoneGutter, paddingBottom: space[32], width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center', gap: space[24] },
  header: { gap: space[8] }, utility: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: space[8] },
  stackedUtility: { flexDirection: 'column', alignItems: 'stretch' },
  titleRegion: { minHeight: layout.artwork.compact }, art: { position: 'absolute', top: 0, left: -layout.phoneGutter, right: -layout.phoneGutter },
  titleCopy: { paddingTop: space[48] + space[16], gap: space[8] }, notice: { gap: space[16] },
});
