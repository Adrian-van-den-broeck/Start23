import { useMemo, useRef, useState } from 'react';
import {
  Animated,
  PanResponder,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import type { PlannedWorkout } from '../api/types';
import { useLanguage } from '../i18n/LanguageProvider';
import { workoutCardDescription } from '../lib/workoutPresentation';
import { colors, radius, shadows, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';
import { StatusPill } from './StatusPill';

const DAY_ROW_HEIGHT = 116;

function parseDate(value: string): Date {
  return new Date(`${value}T12:00:00`);
}

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function addDays(value: string, amount: number): string {
  const result = parseDate(value);
  result.setDate(result.getDate() + amount);
  return isoDate(result);
}

export function isDateInWeek(dateValue: string, weekStart: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) return false;
  const parsed = parseDate(dateValue);
  if (Number.isNaN(parsed.getTime()) || isoDate(parsed) !== dateValue) return false;
  const start = parseDate(weekStart);
  const difference = Math.round(
    (parsed.getTime() - start.getTime()) / 86_400_000,
  );
  return difference >= 0 && difference <= 6;
}

export function resolveWeekDragDate(
  weekStart: string,
  currentDate: string,
  verticalDistance: number,
): string {
  if (!isDateInWeek(currentDate, weekStart)) {
    throw new Error('The workout date is outside the active week.');
  }
  const start = parseDate(weekStart);
  const current = parseDate(currentDate);
  const currentIndex = Math.round(
    (current.getTime() - start.getTime()) / 86_400_000,
  );
  const targetIndex = Math.max(
    0,
    Math.min(6, currentIndex + Math.round(verticalDistance / DAY_ROW_HEIGHT)),
  );
  return addDays(weekStart, targetIndex);
}

function DraggableWorkout({
  busy,
  onMove,
  weekDates,
  weekStart,
  workout,
}: {
  busy: boolean;
  onMove: (workout: PlannedWorkout, scheduledDate: string) => void;
  weekDates: string[];
  weekStart: string;
  workout: PlannedWorkout;
}) {
  const { locale } = useLanguage();
  const [showDateChoices, setShowDateChoices] = useState(false);
  const dragY = useRef(new Animated.Value(0)).current;
  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_, gesture) =>
          !busy && Math.abs(gesture.dy) > 7,
        onPanResponderGrant: () => dragY.setValue(0),
        onPanResponderMove: (_, gesture) => dragY.setValue(gesture.dy),
        onPanResponderRelease: (_, gesture) => {
          const target = resolveWeekDragDate(
            weekStart,
            workout.scheduled_date,
            gesture.dy,
          );
          Animated.spring(dragY, {
            friction: 7,
            tension: 55,
            toValue: 0,
            useNativeDriver: true,
          }).start();
          if (target !== workout.scheduled_date) onMove(workout, target);
        },
        onPanResponderTerminate: () => {
          Animated.spring(dragY, {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        },
      }),
    [busy, dragY, onMove, weekStart, workout],
  );

  const moveOneDay = (amount: -1 | 1) => {
    const target = resolveWeekDragDate(
      weekStart,
      workout.scheduled_date,
      amount * DAY_ROW_HEIGHT,
    );
    if (target !== workout.scheduled_date) onMove(workout, target);
  };

  return (
    <View style={styles.workoutBlock}>
      <Animated.View
        accessibilityActions={[
          { name: 'decrement', label: 'Een dag eerder' },
          { name: 'increment', label: 'Een dag later' },
        ]}
        accessibilityHint="Sleep verticaal naar een andere datum in deze week."
        accessibilityLabel={`${workout.name}, gepland op ${workout.scheduled_date}`}
        accessibilityRole="adjustable"
        accessible
        onAccessibilityAction={(event) => {
          if (event.nativeEvent.actionName === 'decrement') moveOneDay(-1);
          if (event.nativeEvent.actionName === 'increment') moveOneDay(1);
        }}
        style={[styles.draggable, { transform: [{ translateY: dragY }] }]}
        {...panResponder.panHandlers}
      >
        <View style={styles.workoutHeader}>
          <StatusPill
            label={workout.intensity_bucket === 'high' ? 'Intensief' : 'Rustig'}
            tone={workout.intensity_bucket === 'high' ? 'accent' : 'neutral'}
          />
          <Text style={styles.dragHint}>↕ Sleep</Text>
        </View>
        <Text style={styles.workoutTitle}>{workout.name}</Text>
        <Text numberOfLines={2} style={styles.workoutDescription}>
          {workoutCardDescription(workout.description)}
        </Text>
      </Animated.View>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: showDateChoices }}
        disabled={busy}
        onPress={() => setShowDateChoices((current) => !current)}
        style={styles.chooseDateButton}
      >
        <Text style={styles.chooseDateText}>Andere datum kiezen</Text>
      </Pressable>
      {showDateChoices ? (
        <View accessibilityLabel="Datum kiezen" style={styles.dateChoices}>
          {weekDates.map((date) => {
            const selected = date === workout.scheduled_date;
            const label = parseDate(date).toLocaleDateString(locale, {
              day: 'numeric',
              weekday: 'short',
            });
            return (
              <Pressable
                accessibilityLabel={`Verplaats ${workout.name} naar ${label}`}
                accessibilityRole="button"
                accessibilityState={{ disabled: selected }}
                disabled={busy || selected}
                key={date}
                onPress={() => onMove(workout, date)}
                style={[styles.dateChoice, selected && styles.dateChoiceSelected]}
              >
                <Text style={[styles.dateChoiceText, selected && styles.dateChoiceTextSelected]}>
                  {label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}

export function WeekSchedule({
  busy,
  onMove,
  weekStart,
  workouts,
}: {
  busy: boolean;
  onMove: (workout: PlannedWorkout, scheduledDate: string) => void;
  weekStart: string;
  workouts: PlannedWorkout[];
}) {
  const { locale } = useLanguage();
  const weekDates = useMemo(
    () => Array.from({ length: 7 }, (_, index) => addDays(weekStart, index)),
    [weekStart],
  );

  return (
    <View style={styles.board}>
      <Text style={styles.boardTitle}>Weekplanning</Text>
      <Text style={styles.boardHint}>
        Sleep een trainingsblok naar een andere dag. Alleen de datum verandert;
        Wombo controleert de volledige week eerst op de server.
      </Text>
      {weekDates.map((date) => {
        const dayWorkouts = workouts.filter(
          (workout) => workout.scheduled_date === date,
        );
        return (
          <View accessibilityLabel={`Planning voor ${date}`} key={date} style={styles.dayRow}>
            <View style={styles.dayDate}>
              <Text style={styles.dayWeekday}>
                {parseDate(date)
                  .toLocaleDateString(locale, { weekday: 'short' })
                  .replace('.', '')}
              </Text>
              <Text style={styles.dayNumber}>{parseDate(date).getDate()}</Text>
            </View>
            <View style={styles.dayContent}>
              {dayWorkouts.length ? (
                dayWorkouts.map((workout) => (
                  <DraggableWorkout
                    busy={busy}
                    key={workout.id}
                    onMove={onMove}
                    weekDates={weekDates}
                    weekStart={weekStart}
                    workout={workout}
                  />
                ))
              ) : (
                <Text style={styles.empty}>Geen training</Text>
              )}
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  board: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  boardTitle: { color: colors.ink, fontSize: 20, fontWeight: '900' },
  boardHint: { color: colors.inkMuted, fontSize: 12, lineHeight: 18 },
  dayRow: {
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: 'row',
    minHeight: DAY_ROW_HEIGHT,
  },
  dayDate: {
    alignItems: 'center',
    borderRightColor: colors.line,
    borderRightWidth: 1,
    justifyContent: 'center',
    width: 52,
  },
  dayWeekday: {
    color: colors.inkMuted,
    fontSize: 9,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  dayNumber: { color: colors.ink, fontSize: 20, fontWeight: '900' },
  dayContent: { flex: 1, gap: spacing.sm, justifyContent: 'center', padding: spacing.sm },
  empty: { color: colors.inkMuted, fontSize: 11, fontStyle: 'italic' },
  workoutBlock: { gap: spacing.xs },
  draggable: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: 3,
    padding: spacing.sm,
    ...shadows.card,
  },
  workoutHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  dragHint: { color: colors.brand, fontSize: 10, fontWeight: '900' },
  workoutTitle: { color: colors.ink, fontSize: 13, fontWeight: '900' },
  workoutDescription: { color: colors.inkMuted, fontSize: 11, lineHeight: 16 },
  chooseDateButton: { alignSelf: 'flex-start', paddingVertical: spacing.xs },
  chooseDateText: { color: colors.brand, fontSize: 11, fontWeight: '900' },
  dateChoices: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  dateChoice: {
    borderColor: colors.brand,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  dateChoiceSelected: { backgroundColor: colors.brand },
  dateChoiceText: { color: colors.brand, fontSize: 10, fontWeight: '800' },
  dateChoiceTextSelected: { color: colors.white },
});
