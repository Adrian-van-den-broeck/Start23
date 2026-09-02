import { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { PlannedWorkout, RestDay } from '../api/types';
import { useLanguage } from '../i18n/LanguageProvider';
import { formatRpeZones } from '../lib/rpe';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';
import { StatusPill } from './StatusPill';

export type CalendarMode = 'week' | 'month';

type TrainingCalendarProps = {
  initialDate: string;
  loading: boolean;
  onRangeChange: (fromDate: string, toDate: string) => void;
  restDays: RestDay[];
  workouts: PlannedWorkout[];
};

const mondayFirstWeekdayIndexes = [1, 2, 3, 4, 5, 6, 0] as const;

function parseDate(value: string): Date {
  return new Date(`${value}T12:00:00`);
}

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function addDays(value: Date, amount: number): Date {
  const result = new Date(value);
  result.setDate(result.getDate() + amount);
  return result;
}

function startOfWeek(value: Date): Date {
  const result = new Date(value);
  const weekday = result.getDay() || 7;
  result.setDate(result.getDate() - weekday + 1);
  return result;
}

function visibleDates(anchor: Date, mode: CalendarMode): Date[] {
  if (mode === 'week') {
    const start = startOfWeek(anchor);
    return Array.from({ length: 7 }, (_, index) => addDays(start, index));
  }
  const firstOfMonth = new Date(anchor.getFullYear(), anchor.getMonth(), 1, 12);
  const gridStart = startOfWeek(firstOfMonth);
  const lastOfMonth = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0, 12);
  const gridEnd = addDays(startOfWeek(lastOfMonth), 6);
  const dayCount = Math.round((gridEnd.getTime() - gridStart.getTime()) / 86_400_000) + 1;
  return Array.from({ length: dayCount }, (_, index) => addDays(gridStart, index));
}

function sameDay(left: Date, right: Date): boolean {
  return isoDate(left) === isoDate(right);
}

export function TrainingCalendar({
  initialDate,
  loading,
  onRangeChange,
  restDays,
  workouts,
}: TrainingCalendarProps) {
  const { locale, t } = useLanguage();
  const [mode, setMode] = useState<CalendarMode>('week');
  const [anchor, setAnchor] = useState(() => parseDate(initialDate));
  const [selectedDate, setSelectedDate] = useState(initialDate);
  const dates = useMemo(() => visibleDates(anchor, mode), [anchor, mode]);
  const today = isoDate(new Date());

  const workoutsByDate = useMemo(() => {
    const result = new Map<string, PlannedWorkout[]>();
    for (const workout of workouts) {
      const current = result.get(workout.scheduled_date) ?? [];
      current.push(workout);
      result.set(workout.scheduled_date, current);
    }
    return result;
  }, [workouts]);

  const restByDate = useMemo(
    () => new Map(restDays.map((restDay) => [restDay.date, restDay])),
    [restDays],
  );

  useEffect(() => {
    const first = dates[0];
    const last = dates[dates.length - 1];
    // Calendar API ranges use an exclusive end date, so include the final
    // visible Sunday by requesting the following day as the upper bound.
    if (first && last) onRangeChange(isoDate(first), isoDate(addDays(last, 1)));
  }, [dates, onRangeChange]);

  const move = (direction: -1 | 1) => {
    const next = new Date(anchor);
    if (mode === 'week') next.setDate(next.getDate() + direction * 7);
    else next.setMonth(next.getMonth() + direction, 1);
    setAnchor(next);
    setSelectedDate(isoDate(next));
  };

  const goToday = () => {
    const now = new Date();
    setAnchor(now);
    setSelectedDate(isoDate(now));
  };

  const changeMode = (nextMode: CalendarMode) => {
    setMode(nextMode);
    setSelectedDate(isoDate(anchor));
  };

  const periodLabel =
    mode === 'month'
      ? anchor.toLocaleDateString(locale, { month: 'long', year: 'numeric' })
      : `${dates[0]?.toLocaleDateString(locale, { day: 'numeric', month: 'short' })} – ${dates[6]?.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })}`;
  const selectedWorkouts = workoutsByDate.get(selectedDate) ?? [];
  const selectedRest = restByDate.get(selectedDate);

  const renderDayDetails = (date: Date, compact = false) => {
    const key = isoDate(date);
    const dayWorkouts = workoutsByDate.get(key) ?? [];
    const restDay = restByDate.get(key);
    return (
      <>
        {dayWorkouts.map((workout) => (
          <View key={workout.id} style={compact ? styles.compactEvent : styles.event}>
            <View style={styles.eventMarker} />
            <View style={styles.eventCopy}>
              <Text numberOfLines={compact ? 1 : 2} style={compact ? styles.compactEventTitle : styles.eventTitle}>
                {workout.name}
              </Text>
              {!compact ? (
                <Text style={styles.eventMeta}>
                  {t('common.durationMinutes', {
                    minutes: Number(workout.duration_minutes),
                  })}{' · '}{formatRpeZones(workout.rpe_zones)}
                </Text>
              ) : null}
            </View>
          </View>
        ))}
        {restDay ? (
          <View style={compact ? styles.compactRest : styles.restEvent}>
            <Text numberOfLines={1} style={compact ? styles.compactRestText : styles.restEventTitle}>
              {t('common.restDay')}
            </Text>
            {!compact ? (
              <Text style={styles.eventMeta}>
                {restDay.reason === 'restriction_rest'
                  ? t('calendar.restrictionRest')
                  : t('calendar.scheduledRest')}
              </Text>
            ) : null}
          </View>
        ) : null}
      </>
    );
  };

  return (
    <View style={styles.panel}>
      <View style={styles.heading}>
        <View style={styles.headingCopy}>
          <Text style={styles.title}>{t('calendar.title')}</Text>
          <Text style={styles.body}>{t('calendar.approvedOnly')}</Text>
        </View>
        {loading ? <Text style={styles.loading}>{t('common.loading')}</Text> : null}
      </View>

      <View accessibilityRole="tablist" style={styles.modeSwitch}>
        {(['week', 'month'] as const).map((value) => (
          <Pressable
            accessibilityRole="tab"
            accessibilityState={{ selected: mode === value }}
            key={value}
            onPress={() => changeMode(value)}
            style={[styles.modeButton, mode === value && styles.modeButtonActive]}
          >
            <Text style={[styles.modeText, mode === value && styles.modeTextActive]}>
              {t(value === 'week' ? 'calendar.week' : 'calendar.month')}
            </Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.navigation}>
        <Pressable accessibilityLabel={t('common.previous')} onPress={() => move(-1)} style={styles.navButton}>
          <Text style={styles.navButtonText}>‹</Text>
        </Pressable>
        <Pressable accessibilityRole="button" onPress={goToday} style={styles.periodButton}>
          <Text style={styles.periodLabel}>{periodLabel}</Text>
          <Text style={styles.todayLabel}>{t('common.today')}</Text>
        </Pressable>
        <Pressable accessibilityLabel={t('common.next')} onPress={() => move(1)} style={styles.navButton}>
          <Text style={styles.navButtonText}>›</Text>
        </Pressable>
      </View>

      <View style={styles.weekdayRow}>
        {mondayFirstWeekdayIndexes.map((weekday) => {
          const labelDate = new Date(2026, 7, 2 + weekday, 12);
          return (
            <Text key={weekday} style={styles.weekdayLabel}>
              {labelDate.toLocaleDateString(locale, { weekday: 'short' }).replace('.', '')}
            </Text>
          );
        })}
      </View>

      {mode === 'month' ? (
        <View style={styles.monthGrid}>
          {dates.map((date) => {
            const key = isoDate(date);
            const selected = selectedDate === key;
            const outsideMonth = date.getMonth() !== anchor.getMonth();
            return (
              <Pressable
                accessibilityLabel={t('calendar.viewDay', {
                  date: date.toLocaleDateString(locale, { dateStyle: 'long' }),
                })}
                accessibilityState={{ selected }}
                key={key}
                onPress={() => setSelectedDate(key)}
                style={styles.monthCellWrapper}
              >
                <View
                  style={[
                    styles.monthCell,
                    selected && styles.monthCellSelected,
                    key === today && !selected && styles.todayCell,
                  ]}
                >
                  <Text
                    style={[
                      styles.dayNumber,
                      outsideMonth && styles.outsideMonth,
                      selected && styles.dayNumberSelected,
                    ]}
                  >
                    {date.getDate()}
                  </Text>
                  <View style={styles.monthEvents}>{renderDayDetails(date, true)}</View>
                </View>
              </Pressable>
            );
          })}
        </View>
      ) : (
        <View style={styles.weekAgenda}>
          {dates.map((date) => {
            const key = isoDate(date);
            const hasContent = (workoutsByDate.get(key)?.length ?? 0) > 0 || restByDate.has(key);
            return (
              <View key={key} style={[styles.agendaDay, key === today && styles.agendaToday]}>
                <View style={styles.agendaDate}>
                  <Text style={styles.agendaWeekday}>
                    {date.toLocaleDateString(locale, { weekday: 'short' }).replace('.', '')}
                  </Text>
                  <Text style={styles.agendaDayNumber}>{date.getDate()}</Text>
                </View>
                <View style={styles.agendaEvents}>
                  {hasContent ? renderDayDetails(date) : <Text style={styles.emptyDay}>{t('calendar.emptyDay')}</Text>}
                </View>
              </View>
            );
          })}
        </View>
      )}

      {mode === 'month' ? (
        <View style={styles.selectedDay}>
          <View style={styles.selectedDayHeader}>
            <Text style={styles.selectedDayTitle}>
              {parseDate(selectedDate).toLocaleDateString(locale, {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              })}
            </Text>
            {selectedWorkouts.length > 0 ? (
              <StatusPill label={String(selectedWorkouts.length)} tone="brand" />
            ) : null}
          </View>
          {selectedWorkouts.length > 0 || selectedRest ? (
            renderDayDetails(parseDate(selectedDate))
          ) : (
            <Text style={styles.emptyDay}>{t('calendar.emptyDay')}</Text>
          )}
        </View>
      ) : null}

      {!loading && workouts.length === 0 ? (
        <Text style={styles.emptyPeriod}>{t('calendar.noWorkouts')}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: { gap: spacing.md },
  heading: { alignItems: 'flex-start', flexDirection: 'row', justifyContent: 'space-between' },
  headingCopy: { flex: 1, gap: spacing.xs },
  title: { color: colors.ink, fontSize: 23, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  loading: { color: colors.brand, fontSize: 11, fontWeight: '800' },
  modeSwitch: { backgroundColor: colors.surfaceMuted, borderRadius: radius.pill, flexDirection: 'row', padding: 3 },
  modeButton: { alignItems: 'center', borderRadius: radius.pill, flex: 1, paddingVertical: spacing.sm },
  modeButtonActive: { backgroundColor: colors.brand },
  modeText: { color: colors.inkMuted, fontSize: 12, fontWeight: '800' },
  modeTextActive: { color: colors.white },
  navigation: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  navButton: { alignItems: 'center', borderColor: colors.lineStrong, borderRadius: radius.pill, borderWidth: 1, height: 40, justifyContent: 'center', width: 40 },
  navButtonText: { color: colors.brand, fontSize: 25, lineHeight: 27 },
  periodButton: { alignItems: 'center', flex: 1 },
  periodLabel: { color: colors.ink, fontSize: 15, fontWeight: '900', textTransform: 'capitalize' },
  todayLabel: { color: colors.brand, fontSize: 10, fontWeight: '800', marginTop: 2 },
  weekdayRow: { flexDirection: 'row' },
  weekdayLabel: { color: colors.inkMuted, flex: 1, fontSize: 9, fontWeight: '800', textAlign: 'center', textTransform: 'uppercase' },
  monthGrid: { borderColor: colors.line, borderLeftWidth: 1, borderTopWidth: 1, flexDirection: 'row', flexWrap: 'wrap' },
  monthCellWrapper: { flexBasis: '14.2857%', maxWidth: '14.2857%' },
  monthCell: { borderBottomWidth: 1, borderColor: colors.line, borderRightWidth: 1, gap: 2, minHeight: 70, padding: 3 },
  monthCellSelected: { backgroundColor: colors.brandSoft },
  todayCell: { backgroundColor: colors.highlightSoft },
  dayNumber: { color: colors.ink, fontSize: 11, fontWeight: '900', textAlign: 'right' },
  dayNumberSelected: { color: colors.brand },
  outsideMonth: { color: colors.lineStrong },
  monthEvents: { gap: 2 },
  compactEvent: { alignItems: 'center', backgroundColor: colors.brandSoft, borderRadius: 3, flexDirection: 'row', gap: 2, paddingHorizontal: 2, paddingVertical: 2 },
  compactEventTitle: { color: colors.brandDeep, flex: 1, fontSize: 7, fontWeight: '800' },
  compactRest: { backgroundColor: colors.surfaceMuted, borderRadius: 3, padding: 2 },
  compactRestText: { color: colors.inkMuted, fontSize: 7, fontWeight: '700' },
  weekAgenda: { borderColor: colors.line, borderRadius: radius.md, borderWidth: 1, overflow: 'hidden' },
  agendaDay: { borderBottomColor: colors.line, borderBottomWidth: 1, flexDirection: 'row', minHeight: 72 },
  agendaToday: { backgroundColor: colors.highlightSoft },
  agendaDate: { alignItems: 'center', borderRightColor: colors.line, borderRightWidth: 1, justifyContent: 'center', padding: spacing.sm, width: 52 },
  agendaWeekday: { color: colors.inkMuted, fontSize: 9, fontWeight: '800', textTransform: 'uppercase' },
  agendaDayNumber: { color: colors.ink, fontSize: 20, fontWeight: '900' },
  agendaEvents: { flex: 1, gap: spacing.xs, justifyContent: 'center', padding: spacing.sm },
  event: { alignItems: 'center', backgroundColor: colors.brandSoft, borderRadius: radius.sm, flexDirection: 'row', gap: spacing.sm, padding: spacing.sm },
  eventMarker: { backgroundColor: colors.brand, borderRadius: radius.pill, height: 8, width: 8 },
  eventCopy: { flex: 1 },
  eventTitle: { color: colors.ink, fontSize: 12, fontWeight: '900' },
  eventMeta: { color: colors.inkMuted, fontSize: 10, marginTop: 2 },
  restEvent: { backgroundColor: colors.surfaceMuted, borderRadius: radius.sm, padding: spacing.sm },
  restEventTitle: { color: colors.ink, fontSize: 11, fontWeight: '800' },
  emptyDay: { color: colors.inkMuted, fontSize: 11, fontStyle: 'italic' },
  selectedDay: { backgroundColor: colors.surfaceMuted, borderRadius: radius.md, gap: spacing.sm, padding: spacing.md },
  selectedDayHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  selectedDayTitle: { color: colors.ink, flex: 1, fontSize: 14, fontWeight: '900', textTransform: 'capitalize' },
  emptyPeriod: { color: colors.inkMuted, fontSize: 12, textAlign: 'center' },
});
