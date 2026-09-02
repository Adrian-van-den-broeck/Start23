import {
  BottomSheetBackdrop,
  BottomSheetModal,
  BottomSheetView,
} from '@gorhom/bottom-sheet';
import * as SecureStore from 'expo-secure-store';
import * as Haptics from 'expo-haptics';
import {
  type ComponentProps,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  KeyboardAvoidingView,
  PanResponder,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import {
  SafeAreaView,
  useSafeAreaInsets,
} from 'react-native-safe-area-context';
import {
  Carousel,
  type CarouselRef,
} from 'react-native-reanimated-carousel';

import {
  approvePlanProposal,
  createSwipeWeekDraft,
  editPendingWorkout,
  getCalendar,
  getOnboarding,
  getPendingWorkoutAlternatives,
  getSwipeWeekDraft,
  getWeeklyPlan,
  markGoalAchieved,
  movePlannedWorkout,
  placeSwipeWeekWorkout,
  rejectPlanProposal,
  submitSwipeWeekDraft,
  transitionSwipeWeekDraft,
  validatePlanLayout,
} from '../api/client';
import type {
  Discipline,
  PendingWorkoutAlternatives,
  PlanWarning,
  PlannedWorkout,
  PrimaryRaceGoal,
  RestDay,
  SwipeWeekDraft,
  WeeklyPlan,
  WorkoutDeckItem,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { FormField } from '../components/FormField';
import { LanguageSelector } from '../components/LanguageSelector';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import { TrainingCalendar } from '../components/TrainingCalendar';
import { useLanguage } from '../i18n/LanguageProvider';
import { formatIsoDateInput } from '../lib/dateInput';
import { formatRpeZones } from '../lib/rpe';
import { colors, radius, shadows, spacing } from '../theme/tokens';

type PlanningScreenProps = {
  accessToken: string;
  onSignOut: () => Promise<void>;
  onBackToOnboarding: () => void;
  onOpenActivities: () => void;
  onOpenCheckIn: () => void;
  onOpenIntegrations: () => void;
  onOpenZoneProfile: (planId?: string, revision?: number) => void;
};

type ViewName = 'plan' | 'deck' | 'calendar';

const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
};
const disciplineTrainingLabels: Record<Discipline, string> = {
  swim: 'zwemtraining',
  bike: 'fietstraining',
  run: 'looptraining',
};
const latestPlanIdKey = 'start23.latest-plan-id';
const latestSwipeDraftIdKey = 'start23.latest-swipe-draft-id';

const warningCopy: Record<string, { message: string; title: string }> = {
  all_disciplines_blocked_rest_only: {
    title: 'Rustweek voorgesteld',
    message:
      'Alle disciplines zijn momenteel geblokkeerd. Daarom bevat dit voorstel alleen rust.',
  },
  anti_stack_violation: {
    title: 'Meer herstel nodig',
    message:
      'Tussen deze intensieve trainingen is extra herstel nodig. Kies een andere datum.',
  },
  injured_disciplines_excluded: {
    title: 'Blessure verwerkt',
    message:
      'Trainingen voor de bevestigde geblesseerde disciplines zijn niet opgenomen.',
  },
  manual_review_required: {
    title: 'Extra controle nodig',
    message:
      'Er was geen veilig regulier weekdoel beschikbaar. Controleer dit herstelvoorstel extra zorgvuldig.',
  },
  outside_confirmed_availability: {
    title: 'Datum niet beschikbaar',
    message:
      'Een training valt buiten je bevestigde beschikbare dagen. Kies een beschikbare datum.',
  },
  realized_intensity_debt_applied: {
    title: 'Rustiger weekdoel',
    message:
      'Je recente trainingsgegevens verlagen de intensieve tijd voor deze week.',
  },
  restricted_disciplines_low_only: {
    title: 'Alleen rustige training',
    message:
      'Voor een beperkte discipline zijn alleen rustige trainingen opgenomen.',
  },
  target_outside_catalog_capacity: {
    title: 'Weekdoel nog niet compleet',
    message:
      'De beschikbare trainingen sluiten nog niet volledig aan op het weekdoel.',
  },
  workouts_consolidated_on_available_dates: {
    title: 'Trainingen gecombineerd',
    message:
      'Er staan meerdere trainingen op dezelfde beschikbare dag. Plan voldoende herstel tussen de sessies.',
  },
};

function warningPresentation(warning: PlanWarning): {
  message: string;
  title: string;
} {
  return warningCopy[warning.code] ?? {
    title: 'Aandachtspunt',
    message: warning.message,
  };
}

function coachExplanation(value: string): string {
  if (value === 'A deterministic weekly plan is ready for review.') {
    return 'Je persoonlijke weekvoorstel staat klaar om te controleren.';
  }
  if (value === 'A rest-only weekly revision is ready for review.') {
    return 'Je herstelvoorstel met alleen rust staat klaar om te controleren.';
  }
  return value;
}

async function rememberPlanId(planId: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (planId === null) {
    await SecureStore.deleteItemAsync(latestPlanIdKey);
  } else {
    await SecureStore.setItemAsync(latestPlanIdKey, planId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }
}

async function rememberSwipeDraftId(draftId: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (draftId === null) {
    await SecureStore.deleteItemAsync(latestSwipeDraftIdKey);
  } else {
    await SecureStore.setItemAsync(latestSwipeDraftIdKey, draftId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }
}

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function nextMonday(): string {
  const value = new Date();
  value.setHours(12, 0, 0, 0);
  const daysUntilMonday = (8 - value.getDay()) % 7 || 7;
  value.setDate(value.getDate() + daysUntilMonday);
  return isoDate(value);
}

function addDays(dateValue: string, days: number): Date {
  const value = new Date(`${dateValue}T12:00:00`);
  value.setDate(value.getDate() + days);
  return value;
}

function availableDatesFor(
  weekStart: string,
  selectedDays: ReadonlySet<number>,
): string[] {
  return [...selectedDays]
    .sort((left, right) => left - right)
    .map((dayOffset) => isoDate(addDays(weekStart, dayOffset)));
}

function dayOffsetsFor(weekStart: string, dates: string[]): Set<number> {
  const start = new Date(`${weekStart}T12:00:00`);
  return new Set(
    dates.map((value) =>
      Math.round(
        (new Date(`${value}T12:00:00`).getTime() - start.getTime()) /
          86_400_000,
      ),
    ),
  );
}

function validDateInWeek(dateValue: string, weekStart: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) return false;
  const parsed = new Date(`${dateValue}T12:00:00`);
  if (Number.isNaN(parsed.getTime()) || isoDate(parsed) !== dateValue) return false;
  const offset = dayOffsetsFor(weekStart, [dateValue]).values().next().value;
  return typeof offset === 'number' && offset >= 0 && offset <= 6;
}

function ActionButton({
  disabled = false,
  label,
  onPress,
  secondary = false,
}: {
  disabled?: boolean;
  label: string;
  onPress: () => void;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      haptic={secondary ? undefined : 'light'}
      onPress={onPress}
      style={[
        styles.action,
        secondary && styles.actionSecondary,
        disabled && styles.actionDisabled,
      ]}
    >
      <Text
        style={[
          styles.actionText,
          secondary && styles.actionSecondaryText,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

function WorkoutCard({ workout }: { workout: PlannedWorkout }) {
  const { language, locale, t } = useLanguage();
  const scheduled = new Date(`${workout.scheduled_date}T12:00:00`);
  const localizedDisciplines: Record<Discipline, string> =
    language === 'nl'
      ? disciplineLabels
      : { swim: 'Swimming', bike: 'Cycling', run: 'Running' };
  return (
    <View style={styles.workoutCard}>
      <View style={styles.cardHeader}>
        <StatusPill
          label={localizedDisciplines[workout.discipline]}
          tone={workout.intensity_bucket === 'high' ? 'accent' : 'neutral'}
        />
        <Text style={styles.cardMeta}>
          {scheduled.toLocaleDateString(locale, {
            weekday: 'short',
            day: 'numeric',
          })}
        </Text>
      </View>
      <Text style={styles.cardTitle}>{workout.name}</Text>
      <Text style={styles.cardDescription}>{workout.description}</Text>
      <Text style={styles.cardMeta}>
        {t('common.durationMinutes', {
          minutes: Number(workout.duration_minutes),
        })}{' · '}{formatRpeZones(workout.rpe_zones)}
      </Text>
    </View>
  );
}

function deckItemFor(workout: PlannedWorkout): WorkoutDeckItem {
  return {
    id: workout.template_id,
    template_key: workout.template_key,
    version: workout.template_version,
    discipline: workout.discipline,
    name: workout.name,
    description: workout.description,
    duration_minutes: workout.duration_minutes,
    distance_meters: workout.distance_meters,
    intensity_bucket: workout.intensity_bucket,
    expected_rpe_min: workout.expected_rpe_min,
    expected_rpe_max: workout.expected_rpe_max,
    segments: workout.segments,
    rpe_zones: workout.rpe_zones,
  };
}

function PendingWorkoutEditor({
  accessToken,
  busy,
  onEdited,
  onError,
  plan,
  slotIndex,
  workout,
}: {
  accessToken: string;
  busy: boolean;
  onEdited: (updated: WeeklyPlan) => void;
  onError: (message: string) => void;
  plan: WeeklyPlan;
  slotIndex: number;
  workout: PlannedWorkout;
}) {
  const [options, setOptions] = useState<PendingWorkoutAlternatives | null>(null);
  const [optionIndex, setOptionIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const carouselRef = useRef<CarouselRef>(null);
  const candidates = useMemo(
    () => [
      deckItemFor(workout),
      ...(options?.alternatives.filter(
        (candidate) => candidate.id !== workout.template_id,
      ) ?? []),
    ],
    [options?.alternatives, workout],
  );
  const selected = candidates[optionIndex] ?? candidates[0];
  const selectedIsCurrent = selected.id === workout.template_id;

  const moveSelection = (direction: -1 | 1) => {
    if (direction === -1) carouselRef.current?.prev({ animated: true });
    else carouselRef.current?.next({ animated: true });
  };

  const load = useCallback(async () => {
    setLoading(true);
    onError('');
    try {
      const result = await getPendingWorkoutAlternatives(
        accessToken,
        plan.id,
        workout.id,
        plan.revision,
      );
      setOptions(result);
      setOptionIndex(0);
    } catch (caught) {
      onError(
        caught instanceof Error
          ? caught.message
          : 'De vervangingen konden niet worden geladen.',
      );
    } finally {
      setLoading(false);
    }
  }, [accessToken, onError, plan.id, plan.revision, workout.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const apply = async (replacementTemplateId: string | null) => {
    if (!options) return;
    setLoading(true);
    onError('');
    try {
      const result = await editPendingWorkout(
        accessToken,
        plan.id,
        workout.id,
        {
          expected_revision: options.revision,
          expected_proposal_id: options.proposal_id,
          replacement_template_id: replacementTemplateId,
        },
      );
      onEdited(result.plan);
      void Haptics.notificationAsync(
        Haptics.NotificationFeedbackType.Success,
      ).catch(() => undefined);
    } catch (caught) {
      onError(
        caught instanceof Error
          ? caught.message
          : 'De wijziging kon niet als nieuw voorstel worden opgeslagen.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.editPanel}>
      <View style={styles.slotHeading}>
        <View>
          <Text style={styles.slotEyebrow}>
            Training {slotIndex + 1} van {plan.workouts.length}
          </Text>
          <Text style={styles.fieldLabel}>
            Kies je {disciplineTrainingLabels[workout.discipline]}
          </Text>
        </View>
        {loading ? <ActivityIndicator color={colors.brand} size="small" /> : null}
      </View>
      <Text style={styles.hint}>
        Veeg horizontaal door de geldige opties. Na iedere keuze controleert
        Wombo de volledige weekcombinatie opnieuw.
      </Text>
      <Carousel
        animation={{ type: 'spring', damping: 18, stiffness: 190 }}
        data={candidates}
        keyExtractor={(item) => item.id}
        layout={{
          type: 'parallax',
          adjacentScale: 0.92,
          offset: 34,
          scale: 0.96,
        }}
        onConfigurePanGesture={(gesture) => gesture.activeOffsetX([-12, 12])}
        onSnapToItem={(index) => {
          setOptionIndex(index);
          void Haptics.selectionAsync().catch(() => undefined);
        }}
        ref={carouselRef}
        renderItem={({ item, index }) => {
          const isCurrent = item.id === workout.template_id;
          return (
            <View
              accessibilityLabel={`Training ${index + 1} van ${candidates.length}: ${item.name}`}
              style={[styles.swipeCard, isCurrent && styles.swipeCardCurrent]}
            >
              <View style={styles.cardHeader}>
                <StatusPill
                  label={item.intensity_bucket === 'high' ? 'Intensief' : 'Rustig'}
                  tone={item.intensity_bucket === 'high' ? 'accent' : 'neutral'}
                />
                {isCurrent ? (
                  <Text style={styles.selectedLabel}>Gekozen</Text>
                ) : null}
              </View>
              <Text style={styles.cardTitle}>{item.name}</Text>
              <Text numberOfLines={2} style={styles.cardDescription}>
                {item.description}
              </Text>
              <Text style={styles.cardMeta}>
                {Number(item.duration_minutes)} min · {formatRpeZones(item.rpe_zones)} ·{' '}
                {index + 1}/{candidates.length}
              </Text>
            </View>
          );
        }}
        style={styles.carousel}
      />
      {candidates.length > 1 ? (
        <View style={styles.decisionRow}>
          <View style={styles.decisionButton}>
            <ActionButton label="Vorige" onPress={() => moveSelection(-1)} secondary />
          </View>
          <View style={styles.decisionButton}>
            <ActionButton label="Volgende" onPress={() => moveSelection(1)} secondary />
          </View>
        </View>
      ) : null}
      <ActionButton
        disabled={busy || loading || selectedIsCurrent || !options}
        label={selectedIsCurrent ? 'Deze training is gekozen' : 'Kies deze training'}
        onPress={() => void apply(selected.id)}
      />
      {options && candidates.length === 1 ? (
        <Text style={styles.hint}>
          Voor dit trainingsslot is momenteel geen andere combinatie geldig.
        </Text>
      ) : null}
    </View>
  );
}

function SwipeDraftPanel({
  busy,
  draft,
  onPlace,
  onSubmit,
  onTransition,
}: {
  busy: boolean;
  draft: SwipeWeekDraft;
  onPlace: (templateId: string, scheduledDate: string) => void;
  onSubmit: (mode: 'automatic' | 'manual') => void;
  onTransition: (
    action: 'accept' | 'pass' | 'undo' | 'reset_passed',
  ) => void;
}) {
  const candidate = draft.current_candidate;
  const { width: windowWidth } = useWindowDimensions();
  const swipePosition = useRef(new Animated.ValueXY()).current;
  const swipeAnimation = useRef<Animated.CompositeAnimation | null>(null);
  const animatingSwipe = useRef(false);
  const [swipeInFlight, setSwipeInFlight] = useState(false);
  const useNativeDriver = Platform.OS !== 'web';

  const resetSwipePosition = useCallback(
    (animated = true) => {
      swipeAnimation.current?.stop();
      const animation = Animated.spring(swipePosition, {
        damping: 18,
        mass: 0.7,
        stiffness: 220,
        toValue: { x: 0, y: 0 },
        useNativeDriver,
      });
      swipeAnimation.current = animation;
      if (animated) {
        animation.start(() => {
          swipeAnimation.current = null;
        });
        return;
      }
      swipePosition.setValue({ x: 0, y: 0 });
      swipeAnimation.current = null;
    },
    [swipePosition, useNativeDriver],
  );

  const completeSwipe = useCallback(
    (action: 'accept' | 'pass', velocityX = 0, exitY = 0) => {
      if (busy || !candidate || animatingSwipe.current) return;
      const direction = action === 'accept' ? 1 : -1;
      const exitDistance = Math.max(windowWidth * 1.25, 480);
      const duration = Math.max(
        160,
        Math.min(260, 230 - Math.abs(velocityX) * 55),
      );

      animatingSwipe.current = true;
      setSwipeInFlight(true);
      swipeAnimation.current?.stop();
      const animation = Animated.timing(swipePosition, {
        duration,
        easing: Easing.out(Easing.cubic),
        toValue: {
          x: direction * exitDistance,
          y: exitY,
        },
        useNativeDriver,
      });
      swipeAnimation.current = animation;
      animation.start(({ finished }) => {
        swipeAnimation.current = null;
        if (!finished) {
          animatingSwipe.current = false;
          setSwipeInFlight(false);
          return;
        }
        onTransition(action);
      });
    },
    [busy, candidate, onTransition, swipePosition, useNativeDriver, windowWidth],
  );

  useEffect(() => {
    animatingSwipe.current = false;
    setSwipeInFlight(false);
    resetSwipePosition(false);
  }, [candidate?.id, resetSwipePosition]);

  useEffect(() => {
    if (!busy && animatingSwipe.current) {
      animatingSwipe.current = false;
      setSwipeInFlight(false);
      resetSwipePosition();
    }
  }, [busy, resetSwipePosition]);

  useEffect(
    () => () => {
      swipeAnimation.current?.stop();
    },
    [],
  );

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_, gesture) =>
          !busy &&
          !swipeInFlight &&
          candidate !== null &&
          Math.abs(gesture.dx) > 14 &&
          Math.abs(gesture.dx) > Math.abs(gesture.dy),
        onPanResponderGrant: () => {
          swipeAnimation.current?.stop();
          swipePosition.setValue({ x: 0, y: 0 });
        },
        onPanResponderMove: (_, gesture) => {
          swipePosition.setValue({ x: gesture.dx, y: gesture.dy * 0.18 });
        },
        onPanResponderRelease: (_, gesture) => {
          if (gesture.dx <= -86 || gesture.vx <= -0.55) {
            completeSwipe('pass', gesture.vx, gesture.dy * 0.18);
            return;
          }
          if (gesture.dx >= 86 || gesture.vx >= 0.55) {
            completeSwipe('accept', gesture.vx, gesture.dy * 0.18);
            return;
          }
          resetSwipePosition();
        },
        onPanResponderTerminate: () => {
          resetSwipePosition();
        },
      }),
    [
      busy,
      candidate,
      completeSwipe,
      resetSwipePosition,
      swipeInFlight,
      swipePosition,
    ],
  );
  const cardRotation = swipePosition.x.interpolate({
    inputRange: [-windowWidth, 0, windowWidth],
    outputRange: ['-11deg', '0deg', '11deg'],
    extrapolate: 'clamp',
  });
  const acceptOpacity = swipePosition.x.interpolate({
    inputRange: [20, 100],
    outputRange: [0, 1],
    extrapolate: 'clamp',
  });
  const passOpacity = swipePosition.x.interpolate({
    inputRange: [-100, -20],
    outputRange: [1, 0],
    extrapolate: 'clamp',
  });
  const placementByTemplate = useMemo(
    () =>
      new Map(
        draft.placements.map((placement) => [
          placement.template_id,
          placement.scheduled_date,
        ]),
      ),
    [draft.placements],
  );
  const manualComplete =
    draft.placements.length === draft.accepted_workouts.length;
  const weekDates = useMemo(
    () =>
      Array.from({ length: 7 }, (_, dayOffset) =>
        isoDate(addDays(draft.week_start, dayOffset)),
      ),
    [draft.week_start],
  );

  return (
    <View style={styles.panel}>
      <StatusPill
        label={draft.state === 'collecting' ? 'Kiezen' : 'Inplannen'}
        tone="brand"
      />
      <Text style={styles.title}>Stel je week samen</Text>
      <View style={styles.selectionProgress}>
        <Text style={styles.selectionProgressValue}>
          {draft.accepted_workouts.length} van {draft.target_workout_count} gekozen
        </Text>
        <Text style={styles.selectionProgressLabel}>
          Doel: {draft.target_composition.swim} zwemmen ·{' '}
          {draft.target_composition.bike} fietsen · {draft.target_composition.run}{' '}
          lopen
        </Text>
      </View>

      {draft.state === 'collecting' && candidate ? (
        <>
          <Animated.View
            accessible
            accessibilityLabel={`${candidate.name}. Swipe links om over te slaan of rechts om te kiezen.`}
            {...panResponder.panHandlers}
            style={[
              styles.swipeDecisionCard,
              {
                transform: [
                  { translateX: swipePosition.x },
                  { translateY: swipePosition.y },
                  { rotate: cardRotation },
                ],
              },
            ]}
          >
            <Animated.View
              pointerEvents="none"
              style={[
                styles.swipeDecisionBadge,
                styles.swipeAcceptBadge,
                { opacity: acceptOpacity },
              ]}
            >
              <Text
                style={[styles.swipeDecisionBadgeText, styles.swipeAcceptText]}
              >
                KIEZEN
              </Text>
            </Animated.View>
            <Animated.View
              pointerEvents="none"
              style={[
                styles.swipeDecisionBadge,
                styles.swipePassBadge,
                { opacity: passOpacity },
              ]}
            >
              <Text
                style={[styles.swipeDecisionBadgeText, styles.swipePassText]}
              >
                OVERSLAAN
              </Text>
            </Animated.View>
            <View style={styles.cardHeader}>
              <StatusPill
                label={disciplineLabels[candidate.discipline]}
                tone={
                  candidate.intensity_bucket === 'high' ? 'accent' : 'neutral'
                }
              />
              <Text style={styles.cardMeta}>
                {Number(candidate.duration_minutes)} min
              </Text>
            </View>
            <Text style={styles.cardTitle}>{candidate.name}</Text>
            <Text style={styles.cardDescription}>{candidate.description}</Text>
            <Text style={styles.cardMeta}>
              {formatRpeZones(candidate.rpe_zones)}
            </Text>
            <Text style={styles.swipeInstruction}>
              ← overslaan · kiezen →
            </Text>
          </Animated.View>
          <View style={styles.decisionRow}>
            <View style={styles.decisionButton}>
              <ActionButton
                disabled={busy || swipeInFlight}
                label="Overslaan"
                onPress={() => completeSwipe('pass')}
                secondary
              />
            </View>
            <View style={styles.decisionButton}>
              <ActionButton
                disabled={busy || swipeInFlight}
                label="Kiezen"
                onPress={() => completeSwipe('accept')}
              />
            </View>
          </View>
        </>
      ) : null}

      {draft.state === 'collecting' && !candidate ? (
        <View style={styles.warning}>
          <Text style={styles.warningTitle}>Geen nieuwe geldige kaarten</Text>
          <Text style={styles.warningText}>
            Zet overgeslagen kaarten terug of maak je laatste keuze ongedaan.
          </Text>
        </View>
      ) : null}

      {draft.state === 'collecting' ? (
        <View style={styles.decisionRow}>
          <View style={styles.decisionButton}>
            <ActionButton
              disabled={busy || !draft.can_undo}
              label="Ongedaan maken"
              onPress={() => onTransition('undo')}
              secondary
            />
          </View>
          <View style={styles.decisionButton}>
            <ActionButton
              disabled={busy || draft.passed_count === 0}
              label="Opnieuw bekijken"
              onPress={() => onTransition('reset_passed')}
              secondary
            />
          </View>
        </View>
      ) : null}

      {draft.state === 'placement' ? (
        <>
          <Text style={styles.body}>
            Laat Wombo de trainingen spreiden over je beschikbare dagen, of
            kies zelf per training een datum. Je mag dezelfde datum voor
            meerdere trainingen kiezen.
          </Text>
          {draft.warnings.map((warning) => {
            const presentation = warningPresentation(warning);
            return (
              <View key={warning.id ?? warning.code} style={styles.warning}>
                <Text style={styles.warningTitle}>{presentation.title}</Text>
                <Text style={styles.warningText}>{presentation.message}</Text>
              </View>
            );
          })}
          <ActionButton
            disabled={busy}
            label="Verspreid over beschikbare dagen"
            onPress={() => onSubmit('automatic')}
          />
          {draft.accepted_workouts.map((workout) => (
            <View key={workout.id} style={styles.placementCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{workout.name}</Text>
                <StatusPill
                  label={disciplineLabels[workout.discipline]}
                  tone="neutral"
                />
              </View>
              <Text style={styles.cardMeta}>
                {formatRpeZones(workout.rpe_zones)}
              </Text>
              <ScrollView
                contentContainerStyle={styles.dateChoiceRow}
                horizontal
                showsHorizontalScrollIndicator={false}
              >
                {weekDates.map((scheduledDate) => {
                  const selected =
                    placementByTemplate.get(workout.id) === scheduledDate;
                  const available = draft.available_dates.includes(scheduledDate);
                  return (
                    <Pressable
                      accessibilityRole="radio"
                      accessibilityState={{ checked: selected }}
                      disabled={busy || !available}
                      key={scheduledDate}
                      onPress={() => onPlace(workout.id, scheduledDate)}
                      style={[
                        styles.dateChoice,
                        selected && styles.choiceActive,
                        !available && styles.actionDisabled,
                      ]}
                    >
                      <Text
                        style={[
                          styles.choiceText,
                          selected && styles.choiceTextActive,
                        ]}
                      >
                        {new Date(`${scheduledDate}T12:00:00`).toLocaleDateString(
                          'nl-NL',
                          { day: 'numeric', weekday: 'short' },
                        )}
                      </Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>
          ))}
          <ActionButton
            disabled={busy || !manualComplete}
            label="Controleer handmatige planning"
            onPress={() => onSubmit('manual')}
            secondary
          />
          <ActionButton
            disabled={busy || !draft.can_undo}
            label="Terug naar kiezen"
            onPress={() => onTransition('undo')}
            secondary
          />
        </>
      ) : null}
    </View>
  );
}

export function PlanningScreen({
  accessToken,
  onBackToOnboarding,
  onOpenActivities,
  onOpenCheckIn,
  onOpenIntegrations,
  onOpenZoneProfile,
  onSignOut,
}: PlanningScreenProps) {
  const { language, locale, t } = useLanguage();
  const safeAreaInsets = useSafeAreaInsets();
  const [view, setView] = useState<ViewName>('plan');
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileSheetRef = useRef<BottomSheetModal>(null);
  const [weekStart, setWeekStart] = useState(nextMonday);
  const [reusePreviousWeek, setReusePreviousWeek] = useState(false);
  const [selectedDays, setSelectedDays] = useState<Set<number>>(
    () => new Set([0, 2, 5]),
  );
  const [injuries, setInjuries] = useState<Set<Discipline>>(() => new Set());
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const [swipeDraft, setSwipeDraft] = useState<SwipeWeekDraft | null>(null);
  const [calendarWorkouts, setCalendarWorkouts] = useState<PlannedWorkout[]>([]);
  const [calendarRestDays, setCalendarRestDays] = useState<RestDay[]>([]);
  const [moveDates, setMoveDates] = useState<Record<string, string>>({});
  const [primaryGoal, setPrimaryGoal] = useState<PrimaryRaceGoal | null>(null);
  const [maintenanceMarked, setMaintenanceMarked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dayLabels = useMemo(
    () =>
      Array.from({ length: 7 }, (_, index) =>
        new Date(2026, 7, 3 + index, 12)
          .toLocaleDateString(locale, { weekday: 'short' })
          .replace('.', ''),
      ),
    [locale],
  );

  const renderProfileBackdrop = useCallback(
    (props: ComponentProps<typeof BottomSheetBackdrop>) => (
      <BottomSheetBackdrop
        {...props}
        appearsOnIndex={0}
        disappearsOnIndex={-1}
        opacity={0.35}
        pressBehavior="close"
      />
    ),
    [],
  );

  const toggleProfileSheet = () => {
    if (profileMenuOpen) {
      profileSheetRef.current?.dismiss();
      return;
    }
    profileSheetRef.current?.present();
  };

  const closeProfileSheetThen = (action: () => void) => {
    profileSheetRef.current?.dismiss();
    action();
  };

  const availableDates = useMemo(
    () => availableDatesFor(weekStart, selectedDays),
    [selectedDays, weekStart],
  );

  useEffect(() => {
    if (Platform.OS === 'web') return;
    let mounted = true;
    SecureStore.getItemAsync(latestSwipeDraftIdKey)
      .then(async (draftId) => {
        if (!draftId) return false;
        try {
          const restored = await getSwipeWeekDraft(accessToken, draftId);
          if (restored.state === 'submitted' && restored.plan_id) {
            const submittedPlan = await getWeeklyPlan(
              accessToken,
              restored.plan_id,
            );
            await Promise.all([
              rememberPlanId(submittedPlan.id),
              rememberSwipeDraftId(null),
            ]);
            if (mounted) {
              setPlan(submittedPlan);
              setWeekStart(submittedPlan.week_start);
              setView('plan');
            }
            return true;
          }
          if (mounted) {
            setSwipeDraft(restored);
            setWeekStart(restored.week_start);
            setReusePreviousWeek(
              restored.availability_source === 'previous_week',
            );
            setSelectedDays(
              dayOffsetsFor(restored.week_start, restored.available_dates),
            );
            setView('deck');
          }
          return true;
        } catch {
          await rememberSwipeDraftId(null);
          return false;
        }
      })
      .then(async (draftRestored) => {
        if (draftRestored) return;
        const planId = await SecureStore.getItemAsync(latestPlanIdKey);
        if (!planId) return;
        try {
          const restored = await getWeeklyPlan(accessToken, planId);
          if (mounted) {
            setPlan(restored);
            setWeekStart(restored.week_start);
            setReusePreviousWeek(
              restored.availability_source === 'previous_week',
            );
            setSelectedDays(
              dayOffsetsFor(restored.week_start, restored.available_dates),
            );
            setInjuries(new Set(restored.confirmed_injuries));
          }
        } catch {
          await rememberPlanId(null);
        }
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  useEffect(() => {
    getOnboarding(accessToken)
      .then((state) => setPrimaryGoal(state.primary_goal))
      .catch(() => undefined);
  }, [accessToken]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De planningsactie is niet gelukt.',
      );
    } finally {
      setBusy(false);
    }
  };

  const toggleDay = (day: number) => {
    setReusePreviousWeek(false);
    setSelectedDays((current) => {
      const next = new Set(current);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  };

  const toggleInjury = (discipline: Discipline) => {
    setInjuries((current) => {
      const next = new Set(current);
      if (next.has(discipline)) next.delete(discipline);
      else next.add(discipline);
      return next;
    });
  };

  const generate = () =>
    run(async () => {
      const dates = availableDatesFor(weekStart, selectedDays);
      if (!reusePreviousWeek && dates.length === 0) {
        throw new Error('Kies minstens één beschikbare trainingsdag.');
      }
      const boundPlan = plan?.revision_state === 'active' ? plan : null;
      const result = await createSwipeWeekDraft(accessToken, {
        week_start: weekStart,
        ...(reusePreviousWeek
          ? { reuse_previous_week: true }
          : { available_dates: dates }),
        confirmed_injuries: [...injuries],
        ...(boundPlan
          ? {
              plan_id: boundPlan.id,
              expected_base_revision: boundPlan.active_revision ?? 0,
            }
          : {}),
      });
      await rememberSwipeDraftId(result.id);
      setSwipeDraft(result);
      setView('deck');
    });

  const approve = () => {
    if (!plan?.proposal) return;
    void run(async () => {
      await approvePlanProposal(
        accessToken,
        plan.proposal!.id,
        plan.proposal!.base_plan_revision ?? 0,
      );
      setPlan(await getWeeklyPlan(accessToken, plan.id));
    });
  };

  const reject = () => {
    if (!plan?.proposal) return;
    void run(async () => {
      await rejectPlanProposal(accessToken, plan.proposal!.id);
      setPlan(await getWeeklyPlan(accessToken, plan.id, plan.revision));
    });
  };

  const openDeck = () => {
    setView('deck');
  };

  const transitionDraft = useCallback(
    (action: 'accept' | 'pass' | 'undo' | 'reset_passed') => {
      if (!swipeDraft) return;
      const candidateId = swipeDraft.current_candidate?.id;
      if ((action === 'accept' || action === 'pass') && !candidateId) return;
      void run(async () => {
        const updated = await transitionSwipeWeekDraft(
          accessToken,
          swipeDraft.id,
          {
            expected_revision: swipeDraft.revision,
            action,
            ...(candidateId && (action === 'accept' || action === 'pass')
              ? { candidate_template_id: candidateId }
              : {}),
          },
        );
        setSwipeDraft(updated);
        void Haptics.selectionAsync().catch(() => undefined);
      });
    },
    [accessToken, swipeDraft],
  );

  const placeDraftWorkout = (templateId: string, scheduledDate: string) => {
    if (!swipeDraft) return;
    void run(async () => {
      const updated = await placeSwipeWeekWorkout(
        accessToken,
        swipeDraft.id,
        templateId,
        swipeDraft.revision,
        scheduledDate,
      );
      setSwipeDraft(updated);
    });
  };

  const submitDraft = (placementMode: 'automatic' | 'manual') => {
    if (!swipeDraft) return;
    void run(async () => {
      const result = await submitSwipeWeekDraft(
        accessToken,
        swipeDraft.id,
        swipeDraft.revision,
        placementMode,
      );
      await Promise.all([
        rememberPlanId(result.plan.id),
        rememberSwipeDraftId(null),
      ]);
      setSwipeDraft(null);
      setPlan(result.plan);
      setView('plan');
      void Haptics.notificationAsync(
        Haptics.NotificationFeedbackType.Success,
      ).catch(() => undefined);
    });
  };

  const moveWorkout = (workout: PlannedWorkout) => {
    if (!plan?.active_revision) return;
    const scheduledDate = moveDates[workout.id] ?? workout.scheduled_date;
    if (!validDateInWeek(scheduledDate, plan.week_start)) {
      setError('Gebruik een geldige datum binnen deze planweek (JJJJ-MM-DD).');
      return;
    }
    void run(async () => {
      const workouts = plan.workouts.map((item) => ({
        workout_id: item.id,
        scheduled_date:
          item.id === workout.id ? scheduledDate : item.scheduled_date,
      }));
      const validation = await validatePlanLayout(
        accessToken,
        plan.id,
        plan.active_revision!,
        workouts,
      );
      const apply = async () => {
        const updated = await movePlannedWorkout(
          accessToken,
          workout.id,
          plan.active_revision!,
          scheduledDate,
        );
        setPlan(updated);
        setMoveDates((current) => ({
          ...current,
          [workout.id]: scheduledDate,
        }));
      };
      if (validation.warnings.length === 0) {
        await apply();
        return;
      }
      Alert.alert(
        'Let op bij verplaatsen',
        validation.warnings.map((warning) => warning.message).join('\n\n'),
        [
          { text: 'Annuleren', style: 'cancel' },
          { text: 'Toch verplaatsen', onPress: () => void run(apply) },
        ],
      );
    });
  };

  const confirmGoalAchievement = () => {
    if (!primaryGoal) return;
    Alert.alert(
      'Doel behaald?',
      'Nieuwe voorstellen gaan naar onderhoud: geen opbouw, wel het 4+1-ritme en de rustige/intensieve verdeling.',
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Bevestigen',
          onPress: () =>
            void run(async () => {
              await markGoalAchieved(accessToken, primaryGoal.id, isoDate(new Date()));
              setMaintenanceMarked(true);
            }),
        },
      ],
    );
  };

  const openCalendar = () => {
    setView('calendar');
  };

  const loadCalendarRange = useCallback(
    (fromDate: string, toDate: string) => {
      setBusy(true);
      setError(null);
      getCalendar(accessToken, fromDate, toDate)
        .then((result) => {
          setCalendarWorkouts(result.workouts);
          setCalendarRestDays(result.rest_days);
        })
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : language === 'nl'
                ? 'De kalender kon niet worden geladen.'
                : 'The calendar could not be loaded.',
          ),
        )
        .finally(() => setBusy(false));
    },
    [accessToken, language],
  );

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.header}>
        <View style={styles.brandLockup}>
          <View style={styles.logoMark}>
            <Text style={styles.logoMarkText}>23</Text>
          </View>
          <View>
            <Text style={styles.logo}>Wombo</Text>
            <Text style={styles.headerCaption}>{t('planning.headerCaption')}</Text>
          </View>
        </View>
        <Pressable
          accessibilityLabel="Profielmenu"
          accessibilityRole="button"
          accessibilityState={{ expanded: profileMenuOpen }}
          haptic="selection"
          onPress={toggleProfileSheet}
          style={({ pressed }) => [
            styles.profileControl,
            pressed && styles.pressed,
          ]}
        >
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>JIJ</Text>
          </View>
          <View style={styles.profileControlCopy}>
            <Text style={styles.profileControlTitle}>{t('planning.profile')}</Text>
            <Text style={styles.profileControlMeta}>
              {profileMenuOpen ? t('common.close') : t('planning.profileMenu')}
            </Text>
          </View>
          <Text style={styles.profileChevron}>{profileMenuOpen ? '-' : '+'}</Text>
        </Pressable>
      </View>

      <BottomSheetModal
        backdropComponent={renderProfileBackdrop}
        backgroundStyle={styles.profileSheetBackground}
        bottomInset={safeAreaInsets.bottom}
        enableDynamicSizing
        handleIndicatorStyle={styles.profileSheetHandle}
        onChange={(index) => setProfileMenuOpen(index >= 0)}
        onDismiss={() => setProfileMenuOpen(false)}
        ref={profileSheetRef}
      >
        <BottomSheetView style={styles.profileSheet}>
          <View style={styles.profileMenuHeading}>
            <View>
              <Text style={styles.profileMenuEyebrow}>{t('planning.profilePersonal')}</Text>
              <Text style={styles.profileMenuTitle}>{t('planning.profileSetup')}</Text>
            </View>
            <View style={styles.profileStatus}>
              <View style={styles.profileStatusDot} />
              <Text style={styles.profileStatusText}>{t('common.active')}</Text>
            </View>
          </View>
          <View style={styles.profileMenuGrid}>
            <Pressable
              accessibilityRole="button"
              haptic="selection"
              onPress={() => closeProfileSheetThen(onBackToOnboarding)}
              style={({ pressed }) => [
                styles.profileMenuItem,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.profileMenuItemCode}>P</Text>
              <Text style={styles.profileMenuItemTitle}>Intakeprofiel</Text>
              <Text style={styles.profileMenuItemMeta}>{t('planning.profileData')}</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              haptic="selection"
              onPress={() => closeProfileSheetThen(onOpenIntegrations)}
              style={({ pressed }) => [
                styles.profileMenuItem,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.profileMenuItemCode}>I</Text>
              <Text style={styles.profileMenuItemTitle}>Integraties</Text>
              <Text style={styles.profileMenuItemMeta}>{t('planning.profileIntegrations')}</Text>
            </Pressable>
          </View>
          <LanguageSelector />
          <Pressable
            accessibilityRole="button"
            onPress={() => {
              profileSheetRef.current?.dismiss();
              void onSignOut();
            }}
            style={({ pressed }) => [
              styles.signOutButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.signOutText}>{t('planning.safeSignOut')}</Text>
          </Pressable>
        </BottomSheetView>
      </BottomSheetModal>

      <View style={styles.quickActions}>
        <Pressable
          accessibilityRole="button"
          onPress={onOpenCheckIn}
          style={({ pressed }) => [
            styles.quickAction,
            pressed && styles.quickActionPressed,
          ]}
        >
          <View style={styles.quickActionIcon}>
            <Text style={styles.quickActionIconText}>C</Text>
          </View>
          <Text style={styles.quickActionText}>Check-in</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={onOpenActivities}
          style={({ pressed }) => [
            styles.quickAction,
            pressed && styles.quickActionPressed,
          ]}
        >
          <View style={[styles.quickActionIcon, styles.quickActionIconAccent]}>
            <Text style={styles.quickActionIconText}>R</Text>
          </View>
          <Text style={styles.quickActionText}>{t('planning.trainingRpe')}</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() =>
            onOpenZoneProfile(plan?.id, plan?.active_revision ?? undefined)
          }
          style={({ pressed }) => [
            styles.quickAction,
            pressed && styles.quickActionPressed,
          ]}
        >
          <View style={[styles.quickActionIcon, styles.quickActionIconGold]}>
            <Text style={styles.quickActionIconText}>Z</Text>
          </View>
          <Text style={styles.quickActionText}>{t('planning.myZones')}</Text>
        </Pressable>
      </View>

      <View accessibilityRole="tablist" style={styles.tabs}>
        <Pressable
          accessibilityRole="tab"
          accessibilityState={{ selected: view === 'plan' }}
          onPress={() => setView('plan')}
          style={[styles.tab, view === 'plan' && styles.tabActive]}
        >
          <Text style={[styles.tabText, view === 'plan' && styles.tabTextActive]}>
            {t('planning.week')}
          </Text>
        </Pressable>
        <Pressable
          accessibilityRole="tab"
          accessibilityState={{ selected: view === 'deck' }}
          onPress={openDeck}
          style={[styles.tab, view === 'deck' && styles.tabActive]}
        >
          <Text style={[styles.tabText, view === 'deck' && styles.tabTextActive]}>
            {t('planning.choose')}
          </Text>
        </Pressable>
        <Pressable
          accessibilityRole="tab"
          accessibilityState={{ selected: view === 'calendar' }}
          onPress={openCalendar}
          style={[styles.tab, view === 'calendar' && styles.tabActive]}
        >
          <Text
            style={[styles.tabText, view === 'calendar' && styles.tabTextActive]}
          >
            {t('planning.calendar')}
          </Text>
        </Pressable>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboard}
      >
        <ScrollView
          automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}
          contentContainerStyle={styles.content}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          style={styles.scroll}
        >
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}

        <FadeInView key={view} style={styles.viewContent}>
        {view === 'plan' ? (
          <>
            {!plan ? (
              <View style={styles.panel}>
                <StatusPill label="Jij bevestigt" tone="brand" />
                <Text style={styles.title}>Wanneer kun je trainen?</Text>
                <Text style={styles.body}>
                  Kies één dag om alle trainingen op die dag te plannen, of
                  meerdere dagen om ze zo gelijk mogelijk te spreiden. Het
                  resultaat blijft een voorstel totdat jij het goedkeurt.
                </Text>
                <FormField
                  autoCapitalize="none"
                  inputMode="numeric"
                  label="Week start op maandag"
                  maxLength={10}
                  onChangeText={(value) =>
                    setWeekStart(formatIsoDateInput(value))
                  }
                  placeholder="JJJJ-MM-DD"
                  value={weekStart}
                />
                <View style={styles.dayRow}>
                  {dayLabels.map((label, index) => (
                    <Pressable
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: selectedDays.has(index) }}
                      key={label}
                      onPress={() => toggleDay(index)}
                      style={[
                        styles.choice,
                        selectedDays.has(index) && styles.choiceActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.choiceText,
                          selectedDays.has(index) && styles.choiceTextActive,
                        ]}
                      >
                        {label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                <Pressable
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: reusePreviousWeek }}
                  onPress={() => setReusePreviousWeek((current) => !current)}
                  style={[
                    styles.reuseChoice,
                    reusePreviousWeek && styles.choiceActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.choiceText,
                      reusePreviousWeek && styles.choiceTextActive,
                    ]}
                  >
                    Zelfde beschikbare dagen als vorige week
                  </Text>
                </Pressable>
                <Text style={styles.hint}>
                  Hergebruik gebeurt alleen na deze expliciete keuze; ontbrekende
                  vorige-weekdata wordt niet geraden.
                </Text>
                <Text style={styles.fieldLabel}>Bevestigde blessure</Text>
                <View style={styles.choiceRow}>
                  {(['swim', 'bike', 'run'] as const).map((discipline) => (
                    <Pressable
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: injuries.has(discipline) }}
                      key={discipline}
                      onPress={() => toggleInjury(discipline)}
                      style={[
                        styles.disciplineChoice,
                        injuries.has(discipline) && styles.injuryChoice,
                      ]}
                    >
                      <Text style={styles.choiceText}>
                        {disciplineLabels[discipline]}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                <ActionButton
                  disabled={
                    busy || (!reusePreviousWeek && availableDates.length === 0)
                  }
                  label="Maak weekvoorstel"
                  onPress={() => void generate()}
                />
                <ActionButton
                  label="Terug naar intake"
                  onPress={onBackToOnboarding}
                  secondary
                />
              </View>
            ) : (
              <>
                <View style={styles.panel}>
                  <View style={styles.cardHeader}>
                    <StatusPill
                      label={
                        plan.revision_state === 'active'
                          ? 'Actief'
                          : plan.revision_state === 'pending_approval'
                            ? 'Wacht op jou'
                            : plan.revision_state
                      }
                      tone={
                        plan.revision_state === 'active' ? 'brand' : 'accent'
                      }
                    />
                    <Text style={styles.cardMeta}>Revisie {plan.revision}</Text>
                  </View>
                  <Text style={styles.title}>Week van {plan.week_start}</Text>
                  <Text style={styles.body}>
                    {Number(plan.total_duration_minutes)} minuten ·{' '}
                    {plan.workouts.length} trainingen · fase {plan.phase}
                  </Text>
                  <Text style={styles.body}>
                    {plan.display_low_intensity_percent}% rustig /{' '}
                    {plan.display_high_intensity_percent}% intensief
                  </Text>
                  <Text style={styles.hint}>
                    {Number(plan.low_intensity_minutes)} min rustig ·{' '}
                    {Number(plan.high_intensity_minutes)} min intensief
                  </Text>
                  <View style={styles.selectionProgress}>
                    <Text style={styles.selectionProgressValue}>
                      {plan.workouts.length} van {plan.workouts.length} gekozen
                    </Text>
                    <Text style={styles.selectionProgressLabel}>
                      {plan.warnings.some(
                        (warning) =>
                          warning.code ===
                          'target_outside_catalog_capacity',
                      )
                        ? 'Weekdoel vraagt aandacht'
                        : 'Weekcombinatie compleet'}
                    </Text>
                  </View>
                  <Text style={styles.hint}>
                    Beschikbare datums: {plan.available_dates.join(', ')} · bron:{' '}
                    {plan.availability_source === 'previous_week'
                      ? 'expliciet hergebruikt'
                      : plan.availability_source === 'checkin'
                        ? 'bevestigde check-in'
                        : 'zelf gekozen'}
                  </Text>
                  {primaryGoal ? (
                    <ActionButton
                      disabled={busy || maintenanceMarked}
                      label={
                        maintenanceMarked
                          ? 'Onderhoudsmodus bevestigd'
                          : `Markeer “${primaryGoal.title}” als behaald`
                      }
                      onPress={confirmGoalAchievement}
                      secondary
                    />
                  ) : null}
                  {plan.warnings.map((warning) => {
                    const presentation = warningPresentation(warning);
                    return (
                      <View key={warning.id ?? warning.code} style={styles.warning}>
                        <Text style={styles.warningTitle}>
                          {presentation.title}
                        </Text>
                        <Text style={styles.warningText}>
                          {presentation.message}
                        </Text>
                      </View>
                    );
                  })}
                  {plan.proposal ? (
                    <View style={styles.warning}>
                      <Text style={styles.warningTitle}>Coachuitleg</Text>
                      <Text style={styles.warningText}>
                        {coachExplanation(plan.proposal.public_explanation)}
                      </Text>
                    </View>
                  ) : null}
                  {['rejected', 'expired'].includes(plan.revision_state) ? (
                    <ActionButton
                      label="Nieuw voorstel voorbereiden"
                      onPress={() => {
                        setPlan(null);
                        void rememberPlanId(null);
                      }}
                      secondary
                    />
                  ) : null}
                </View>
                {plan.revision_state === 'pending_approval' &&
                plan.proposal?.state === 'pending' ? (
                  <View style={styles.swipeIntro}>
                    <Text style={styles.swipeIntroTitle}>
                      Stel je week samen
                    </Text>
                    <Text style={styles.body}>
                      Swipe per training door de geldige opties. Fietsen, lopen
                      en zwemmen blijven aparte keuzes; de totale combinatie
                      wordt na elke wijziging opnieuw gecontroleerd.
                    </Text>
                  </View>
                ) : null}
                {plan.workouts.map((workout, index) => (
                  <View key={workout.id} style={styles.workoutStack}>
                    {plan.revision_state === 'pending_approval' &&
                    plan.proposal?.state === 'pending' ? (
                      <PendingWorkoutEditor
                        accessToken={accessToken}
                        busy={busy}
                        onEdited={(updated) => {
                          setPlan(updated);
                        }}
                        onError={setError}
                        plan={plan}
                        slotIndex={index}
                        workout={workout}
                      />
                    ) : (
                      <WorkoutCard workout={workout} />
                    )}
                    {plan.revision_state === 'active' ? (
                      <View style={styles.movePanel}>
                        <FormField
                          autoCapitalize="none"
                          inputMode="numeric"
                          label="Nieuwe datum (JJJJ-MM-DD)"
                          maxLength={10}
                          onChangeText={(value) =>
                            setMoveDates((current) => ({
                              ...current,
                              [workout.id]: formatIsoDateInput(value),
                            }))
                          }
                          value={moveDates[workout.id] ?? workout.scheduled_date}
                        />
                        <ActionButton
                          disabled={busy}
                          label="Controleer en verplaats"
                          onPress={() => moveWorkout(workout)}
                          secondary
                        />
                      </View>
                    ) : null}
                  </View>
                ))}
                {plan.proposal?.state === 'pending' ? (
                  <View style={styles.approvalPanel}>
                    <Text style={styles.approvalTitle}>Klaar met kiezen?</Text>
                    <Text style={styles.body}>
                      Controleer de combinatie hierboven. Je week wordt pas
                      actief nadat je dit voorstel uitdrukkelijk goedkeurt.
                    </Text>
                    <View style={styles.decisionRow}>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label="Week goedkeuren"
                          onPress={approve}
                        />
                      </View>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label="Afwijzen"
                          onPress={reject}
                          secondary
                        />
                      </View>
                    </View>
                  </View>
                ) : null}
              </>
            )}
          </>
        ) : null}

        {view === 'deck' ? (
          swipeDraft ? (
            <SwipeDraftPanel
              busy={busy}
              draft={swipeDraft}
              onPlace={placeDraftWorkout}
              onSubmit={submitDraft}
              onTransition={transitionDraft}
            />
          ) : (
            <View style={styles.panel}>
              <StatusPill label="Nieuwe week" tone="brand" />
              <Text style={styles.title}>Nog geen open keuzeronde</Text>
              <Text style={styles.body}>
                Start op de Week-tab. Daarna toont Wombo telkens precies één
                server-gecontroleerde training.
              </Text>
              <ActionButton label="Naar Week" onPress={() => setView('plan')} />
            </View>
          )
        ) : null}

        {view === 'calendar' ? (
          <View style={styles.panel}>
            <TrainingCalendar
              initialDate={plan?.week_start ?? weekStart}
              loading={busy}
              onRangeChange={loadCalendarRange}
              restDays={calendarRestDays}
              workouts={calendarWorkouts}
            />
          </View>
        ) : null}
        </FadeInView>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  keyboard: { flex: 1 },
  scroll: { flex: 1 },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    paddingTop: spacing.sm,
  },
  brandLockup: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  logoMark: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.sm,
    height: 40,
    justifyContent: 'center',
    transform: [{ rotate: '-4deg' }],
    width: 40,
  },
  logoMarkText: { color: colors.white, fontSize: 12, fontWeight: '900' },
  logo: {
    color: colors.brand,
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  headerCaption: { color: colors.inkMuted, fontSize: 11, marginTop: 1 },
  profileControl: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.line,
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.sm,
    padding: 5,
    paddingRight: spacing.sm,
  },
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.accentSoft,
    borderRadius: radius.pill,
    height: 34,
    justifyContent: 'center',
    width: 34,
  },
  avatarText: { color: colors.accentDark, fontSize: 9, fontWeight: '900' },
  profileControlCopy: { display: 'flex' },
  profileControlTitle: { color: colors.ink, fontSize: 11, fontWeight: '900' },
  profileControlMeta: { color: colors.inkMuted, fontSize: 9, marginTop: 1 },
  profileChevron: { color: colors.brand, fontSize: 16, fontWeight: '700' },
  pressed: { opacity: 0.72, transform: [{ scale: 0.98 }] },
  profileMenu: {
    ...shadows.floating,
    backgroundColor: colors.brandDeep,
    borderRadius: radius.lg,
    gap: spacing.md,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  profileSheetBackground: { backgroundColor: colors.brandDeep },
  profileSheetHandle: { backgroundColor: colors.brandSoft, width: 42 },
  profileSheet: {
    backgroundColor: colors.brandDeep,
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  profileMenuHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  profileMenuEyebrow: {
    color: colors.highlight,
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  profileMenuTitle: {
    color: colors.white,
    fontSize: 19,
    fontWeight: '900',
    marginTop: 3,
  },
  profileStatus: {
    alignItems: 'center',
    backgroundColor: colors.brandMid,
    borderRadius: radius.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  profileStatusDot: {
    backgroundColor: colors.highlight,
    borderRadius: radius.pill,
    height: 6,
    width: 6,
  },
  profileStatusText: { color: colors.white, fontSize: 9, fontWeight: '800' },
  profileMenuGrid: { flexDirection: 'row', gap: spacing.sm },
  profileMenuItem: {
    backgroundColor: colors.brandMid,
    borderRadius: radius.md,
    flex: 1,
    gap: 2,
    padding: spacing.md,
  },
  profileMenuItemCode: {
    color: colors.highlight,
    fontSize: 11,
    fontWeight: '900',
    marginBottom: spacing.xs,
  },
  profileMenuItemTitle: { color: colors.white, fontSize: 13, fontWeight: '900' },
  profileMenuItemMeta: { color: colors.brandSoft, fontSize: 10, marginTop: 2 },
  signOutButton: {
    alignItems: 'center',
    borderColor: colors.brandMid,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingVertical: spacing.sm,
  },
  signOutText: { color: colors.brandSoft, fontSize: 11, fontWeight: '800' },
  quickActions: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  quickAction: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    flex: 1,
    gap: spacing.xs,
    minHeight: 70,
    justifyContent: 'center',
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.sm,
  },
  quickActionPressed: { backgroundColor: colors.brandSoft, transform: [{ scale: 0.98 }] },
  quickActionIcon: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    height: 26,
    justifyContent: 'center',
    width: 26,
  },
  quickActionIconAccent: { backgroundColor: colors.accentSoft },
  quickActionIconGold: { backgroundColor: colors.highlightSoft },
  quickActionIconText: { color: colors.brand, fontSize: 10, fontWeight: '900' },
  quickActionText: { color: colors.ink, fontSize: 10, fontWeight: '800', textAlign: 'center' },
  tabs: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: 'row',
    marginHorizontal: spacing.lg,
    marginTop: spacing.sm,
    padding: 4,
  },
  tab: {
    alignItems: 'center',
    borderRadius: radius.pill,
    flex: 1,
    justifyContent: 'center',
    minHeight: 40,
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.sm,
  },
  tabActive: { ...shadows.card, backgroundColor: colors.brand },
  tabText: { color: colors.inkMuted, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  tabTextActive: { color: colors.white, fontWeight: '900' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: 80 },
  viewContent: { gap: spacing.md },
  panel: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.white,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: { color: colors.ink, fontSize: 23, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 14, lineHeight: 21 },
  fieldLabel: { color: colors.ink, fontSize: 13, fontWeight: '700' },
  selectionProgress: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: 2,
    padding: spacing.md,
  },
  selectionProgressValue: {
    color: colors.brand,
    fontSize: 15,
    fontWeight: '900',
  },
  selectionProgressLabel: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 17,
  },
  dayRow: { flexDirection: 'row', gap: 4, justifyContent: 'space-between' },
  choice: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  choiceActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  choiceText: { color: colors.ink, fontSize: 12, fontWeight: '700' },
  choiceTextActive: { color: colors.white },
  reuseChoice: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    padding: spacing.md,
  },
  choiceRow: { flexDirection: 'row', gap: spacing.sm },
  disciplineChoice: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    flex: 1,
    padding: spacing.sm,
  },
  injuryChoice: { backgroundColor: colors.dangerSoft },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    padding: 14,
    ...shadows.card,
  },
  actionSecondary: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderWidth: 1,
  },
  actionDisabled: { opacity: 0.45 },
  actionText: { color: colors.white, fontSize: 14, fontWeight: '900' },
  actionSecondaryText: { color: colors.brand },
  workoutCard: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.white,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  workoutStack: { gap: spacing.xs },
  movePanel: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  editPanel: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  slotHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  slotEyebrow: {
    color: colors.accent,
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
  },
  swipeCard: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.lineStrong,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    minHeight: 170,
    padding: spacing.md,
  },
  swipeCardCurrent: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
  },
  swipeDecisionCard: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.brand,
    borderRadius: radius.lg,
    borderWidth: 2,
    gap: spacing.sm,
    minHeight: 220,
    padding: spacing.lg,
  },
  swipeDecisionBadge: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.xs,
    borderWidth: 3,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    position: 'absolute',
    top: spacing.lg,
    zIndex: 2,
  },
  swipeAcceptBadge: {
    borderColor: colors.success,
    left: spacing.lg,
    transform: [{ rotate: '-10deg' }],
  },
  swipePassBadge: {
    borderColor: colors.accent,
    right: spacing.lg,
    transform: [{ rotate: '10deg' }],
  },
  swipeDecisionBadgeText: {
    fontSize: 18,
    fontWeight: '900',
    letterSpacing: 1.4,
  },
  swipeAcceptText: { color: colors.success },
  swipePassText: { color: colors.accent },
  swipeInstruction: {
    color: colors.brand,
    fontSize: 12,
    fontWeight: '900',
    marginTop: 'auto',
    textAlign: 'center',
  },
  selectedLabel: {
    color: colors.brand,
    fontSize: 11,
    fontWeight: '900',
  },
  carousel: { height: 190, width: '100%' },
  swipeIntro: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  swipeIntroTitle: { color: colors.ink, fontSize: 18, fontWeight: '900' },
  approvalPanel: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.brand,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  approvalTitle: { color: colors.ink, fontSize: 19, fontWeight: '900' },
  restDay: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  cardHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
    justifyContent: 'space-between',
  },
  cardTitle: {
    color: colors.ink,
    flexShrink: 1,
    fontSize: 17,
    fontWeight: '900',
  },
  cardDescription: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  cardMeta: { color: colors.inkMuted, fontSize: 12 },
  warning: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.sm,
    gap: spacing.xs,
    padding: spacing.md,
  },
  warningTitle: { color: colors.accent, fontSize: 12, fontWeight: '900' },
  warningText: { color: colors.ink, fontSize: 13, lineHeight: 18 },
  decisionRow: { flexDirection: 'row', gap: spacing.sm },
  decisionButton: { flex: 1 },
  placementCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  dateChoiceRow: { gap: spacing.sm, paddingVertical: spacing.xs },
  dateChoice: {
    alignItems: 'center',
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    minWidth: 72,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  hint: { color: colors.inkMuted, fontSize: 12, lineHeight: 18 },
  error: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.sm,
    color: colors.danger,
    padding: spacing.md,
  },
});
