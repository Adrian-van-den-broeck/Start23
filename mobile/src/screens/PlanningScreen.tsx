import { PlanningWorkoutMoveTask } from './PlanningWorkoutMoveTask';
import {
  BottomSheetBackdrop,
  BottomSheetModal,
  BottomSheetScrollView,
} from '@gorhom/bottom-sheet';
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
  BackHandler,
  Alert,
  Animated,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  type ScrollViewProps,
  StatusBar,
  StyleSheet,
  Text,
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

import type {
  Discipline,
  PlannedWorkout,
  SwipeWeekDraft,
  WeeklyPlan,
  WorkoutDeckItem,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { FormField } from '../components/FormField';
import { SupportingProfileMenu } from '../ui-v2/components/SupportingProfileMenu';
import { colors as finalColors, layout as finalLayout, radius as finalRadius, space as finalSpace } from '../ui-v2/tokens';
import {
  MoveWarningPanel,
  warningPresentation,
} from '../components/MoveWarningPanel';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import { TrainingCalendar } from '../components/TrainingCalendar';
import { WeekSchedule } from '../components/WeekSchedule';
import { WorkoutDetailBoundary } from '../ui/WorkoutDetailBoundary';
import { effectiveUiVersion } from '../ui/uiVersion';
import { useUiVersion } from '../ui/UiVersionProvider';
import { Button as V2Button } from '../ui-v2/primitives/Button';
import { WeekScreen } from '../ui-v2/screens/WeekScreen';
import { CalendarScreen } from '../ui-v2/screens/CalendarScreen';
import { useWorkoutSwipe } from '../components/useWorkoutSwipe';
import { AvailabilityScreen, PlacementScreen, SelectionScreen } from '../ui-v2/screens/PlanningCreationScreens';
import { PlanningProposalTask } from './PlanningProposalTask';
import { planningCreationViewModel } from '../ui-v2/utils/planningCreationViewModel';
import { calendarViewModel } from '../ui-v2/utils/calendarViewModel';
import { type CalendarNavigation } from '../features/calendar/useCalendarNavigation';
import { weekHomeViewModel, type WeekAction } from '../ui-v2/utils/weekHomeViewModel';
import { showUiVersionControl, UiVersionControl } from '../ui/UiVersionControl';
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
import { formatIsoDateInput } from '../lib/dateInput';
import { workoutCardDescription } from '../lib/workoutPresentation';
import { createDeferredDismissAction } from '../lib/navigation';
import { colors, radius, shadows, spacing } from '../theme/tokens';
import { addDays, isoDate } from '../features/planning/planningDates';
import { PlanningFlowProvider, usePlanningFlow, usePlanningCalendar } from '../features/planning/PlanningFlowProvider';

import { PlanningPresentationProvider, usePlanningPresentation } from '../navigation/PlanningPresentationProvider';

type PlanningScreenProps = {
  accessToken: string;
  athleteIdentity?: string;
  onSignOut: () => Promise<void>;
  onBackToOnboarding: () => void;
  onOpenActivities: () => void;
  onOpenCheckIn: () => void;
  onOpenIntegrations: () => void;
  onOpenProfile: () => void;
  onOpenZoneProfile: (planId?: string, revision?: number) => void;
};

const disciplineLabels: Record<Discipline, TranslationKey> = {
  swim: 'common.swim',
  bike: 'common.bike',
  run: 'common.run',
};
const disciplineChooseLabels: Record<Discipline, TranslationKey> = {
  swim: 'planning.editor.choose.swim',
  bike: 'planning.editor.choose.bike',
  run: 'planning.editor.choose.run',
};
type Translate = (key: TranslationKey, values?: Record<string, string | number>) => string;
// Only the two known server sentences get local copy; any other explanation is shown as sent.
function coachExplanation(value: string, t: Translate): string {
  if (value === 'A deterministic weekly plan is ready for review.') {
    return t('planning.coach.weeklyReady');
  }
  if (value === 'A rest-only weekly revision is ready for review.') {
    return t('planning.coach.restOnlyReady');
  }
  return value;
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
  const { locale, t } = useLanguage();
  const scheduled = new Date(`${workout.scheduled_date}T12:00:00`);
  return (
    <View style={styles.workoutCard}>
      <View style={styles.cardHeader}>
        <StatusPill
          label={t(disciplineLabels[workout.discipline])}
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
      <Text style={styles.cardDescription}>
        {workoutCardDescription(workout.description)}
      </Text>
      <Text style={styles.cardMeta}>
        {workout.duration_minutes !== null
          ? t('common.durationMinutes', {
              minutes: Number(workout.duration_minutes),
            })
          : t('planning.distanceBased', { distance: String(workout.distance_meters?.toLocaleString(locale)) })}
      </Text>
    </View>
  );
}

function deckItemFor(workout: PlannedWorkout): WorkoutDeckItem {
  const calibration = workout.segments.some((segment) =>
    segment.protocol_target?.protocol_id.includes('calibration'),
  );
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
    workout_kind: calibration ? 'calibration' : 'standard',
    contributes_to_zone_calibration: false,
  };
}

function WorkoutSignals({ workout }: { workout: WorkoutDeckItem }) {
  const { t } = useLanguage();
  if (
    workout.workout_kind !== 'calibration' &&
    !workout.contributes_to_zone_calibration
  ) {
    return null;
  }

  return (
    <View style={styles.workoutSignals}>
      {workout.workout_kind === 'calibration' ? (
        <View
          accessibilityLabel={t('planning.signal.calibration')}
          style={styles.calibrationSignal}
        >
          <View style={styles.calibrationLogo}>
            <Text style={styles.calibrationLogoText}>CAL</Text>
          </View>
          <Text style={styles.calibrationSignalText}>{t('planning.signal.calibration')}</Text>
        </View>
      ) : null}
      {workout.contributes_to_zone_calibration ? (
        <View style={styles.zoneEvidenceSignal}>
          <Text style={styles.zoneEvidenceSignalText}>
            {t('planning.signal.zoneEvidence')}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

function PendingWorkoutEditor({
  busy,
  plan,
  slotIndex,
  workout,
}: {
  busy: boolean;
  plan: WeeklyPlan;
  slotIndex: number;
  workout: PlannedWorkout;
}) {
  const { locale, t } = useLanguage();
  const { pendingWorkouts } = usePlanningFlow();
  const { load, apply, release } = pendingWorkouts;
  const { options, loading } = pendingWorkouts.editors[workout.id] ?? { options: null, loading: false };
  const [optionIndex, setOptionIndex] = useState(0);
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

  useEffect(() => {
    void load(workout.id, () => setOptionIndex(0));
  }, [load, workout.id]);

  useEffect(() => () => release(workout.id), [release, workout.id]);

  return (
    <View style={styles.editPanel}>
      <View style={styles.slotHeading}>
        <View>
          <Text style={styles.slotEyebrow}>
            {t('planning.editor.slot', { index: slotIndex + 1, total: plan.workouts.length })}
          </Text>
          <Text style={styles.fieldLabel}>
            {t(disciplineChooseLabels[workout.discipline])}
          </Text>
        </View>
        {loading ? <ActivityIndicator color={colors.brand} size="small" /> : null}
      </View>
      <Text style={styles.hint}>{t('planning.editor.hint')}</Text>
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
              accessibilityLabel={t('planning.editor.option', { index: index + 1, total: candidates.length, name: item.name })}
              style={[styles.swipeCard, isCurrent && styles.swipeCardCurrent]}
            >
              <View style={styles.cardHeader}>
                <StatusPill
                  label={t(item.intensity_bucket === 'high' ? 'detail.intensity.high' : 'detail.intensity.low')}
                  tone={item.intensity_bucket === 'high' ? 'accent' : 'neutral'}
                />
                {isCurrent ? (
                  <Text style={styles.selectedLabel}>{t('planning.editor.selected')}</Text>
                ) : null}
              </View>
              <WorkoutSignals workout={item} />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <Text numberOfLines={2} style={styles.cardDescription}>
                {workoutCardDescription(item.description)}
              </Text>
              <Text style={styles.cardMeta}>
                {item.duration_minutes !== null
                  ? t('common.durationMinutes', { minutes: Number(item.duration_minutes) })
                  : t('planning.distanceBased', { distance: String(item.distance_meters?.toLocaleString(locale)) })}{' · '}
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
            <ActionButton label={t('common.previous')} onPress={() => moveSelection(-1)} secondary />
          </View>
          <View style={styles.decisionButton}>
            <ActionButton label={t('common.next')} onPress={() => moveSelection(1)} secondary />
          </View>
        </View>
      ) : null}
      <ActionButton
        disabled={busy || loading || selectedIsCurrent || !options}
        label={t(selectedIsCurrent ? 'planning.editor.isSelected' : 'planning.editor.select')}
        onPress={() => void apply(workout.id, selected.id)}
      />
      {options && candidates.length === 1 ? (
        <Text style={styles.hint}>{t('planning.editor.noAlternatives')}</Text>
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
  ) => void | Promise<void>;
}) {
  const { locale, t } = useLanguage();
  const { setTransientBusy } = usePlanningPresentation();
  const swipe = useWorkoutSwipe(draft.state === 'collecting' ? draft.current_candidate : null,
    busy, onTransition, setTransientBusy);
  const candidate = swipe.card;
  const locked = busy || !!swipe.action;
  const placementByOccurrence = useMemo(() => new Map(
    draft.placements.map(placement => [placement.occurrence_id, placement.scheduled_date]),
  ), [draft.placements]);
  const manualComplete = draft.placements.length === draft.accepted_workouts.length;
  const zoneCalibrationWeek =
    candidate?.contributes_to_zone_calibration === true ||
    draft.accepted_workouts.some(
      (workout) => workout.contributes_to_zone_calibration,
    );
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
        label={t(draft.state === 'collecting' ? 'planning.choose' : 'planning.draft.placing')}
        tone="brand"
      />
      <Text style={styles.title}>{t('planning.composeWeek')}</Text>
      <View style={styles.selectionProgress}>
        <Text style={styles.selectionProgressValue}>
          {t('planning.chosenProgress', { accepted: draft.accepted_workouts.length, target: draft.target_workout_count })}
        </Text>
        <Text style={styles.selectionProgressLabel}>
          {t('planning.draft.target', {
            swim: draft.target_composition.swim,
            bike: draft.target_composition.bike,
            run: draft.target_composition.run,
          })}
        </Text>
      </View>

      {zoneCalibrationWeek ? (
        <View style={styles.calibrationNotice}>
          <Text style={styles.calibrationNoticeTitle}>
            {t('planning.draft.calibrationTitle')}
          </Text>
          <Text style={styles.calibrationNoticeText}>
            {t('planning.draft.calibrationText')}
          </Text>
        </View>
      ) : null}

      {candidate ? (
        <>
          <View style={styles.swipeWindow}>
            <Animated.View pointerEvents="none" accessibilityElementsHidden={!swipe.action}
              importantForAccessibility={swipe.action ? 'auto' : 'no-hide-descendants'}
              style={[StyleSheet.absoluteFill, styles.swipeLoading, { opacity: swipe.loadingOpacity }]}>
              <Text style={styles.body} accessibilityLiveRegion="polite">{t('creation.nextCard')}</Text>
            </Animated.View>
            <Animated.View
              accessible
              accessibilityLabel={t('planning.draft.swipeLabel', { name: candidate.name })}
              {...swipe.panHandlers}
              style={[styles.swipeDecisionCard, { transform: swipe.transform, opacity: swipe.opacity }]}
            >
              <Animated.View
                pointerEvents="none"
                style={[
                  styles.swipeDecisionBadge,
                  styles.swipeAcceptBadge,
                  { opacity: swipe.acceptOpacity },
                ]}
              >
                <Text
                  style={[styles.swipeDecisionBadgeText, styles.swipeAcceptText]}
                >
                  {t('planning.draft.badgeChoose')}
                </Text>
              </Animated.View>
              <Animated.View
                pointerEvents="none"
                style={[
                  styles.swipeDecisionBadge,
                  styles.swipePassBadge,
                  { opacity: swipe.passOpacity },
                ]}
              >
                <Text
                  style={[styles.swipeDecisionBadgeText, styles.swipePassText]}
                >
                  {t('planning.draft.badgePass')}
                </Text>
              </Animated.View>
              <View style={styles.cardHeader}>
                <StatusPill
                  label={t(disciplineLabels[candidate.discipline])}
                  tone={
                    candidate.intensity_bucket === 'high' ? 'accent' : 'neutral'
                  }
                />
                <Text style={styles.cardMeta}>
                  {candidate.duration_minutes !== null
                    ? t('common.durationMinutes', { minutes: Number(candidate.duration_minutes) })
                    : t('planning.distanceShort', { distance: String(candidate.distance_meters?.toLocaleString(locale)) })}
                </Text>
              </View>
              <WorkoutSignals workout={candidate} />
              <Text style={styles.cardTitle}>{candidate.name}</Text>
              <Text style={styles.cardDescription}>
                {workoutCardDescription(candidate.description)}
              </Text>
              <Text style={styles.swipeInstruction}>
                {t('planning.draft.swipeInstruction')}
              </Text>
            </Animated.View>
          </View>
          <View style={styles.decisionRow}>
            <View style={styles.decisionButton}>
              <ActionButton
                disabled={locked}
                label={t('creation.pass')}
                onPress={() => { void swipe.decide('pass'); }}
                secondary
              />
            </View>
            <View style={styles.decisionButton}>
              <ActionButton
                disabled={locked}
                label={t('creation.choose')}
                onPress={() => { void swipe.decide('accept'); }}
              />
            </View>
          </View>
        </>
      ) : null}

      {draft.state === 'collecting' && !candidate ? (
        <View style={styles.warning}>
          <Text style={styles.warningTitle}>{t('planning.draft.exhaustedTitle')}</Text>
          <Text style={styles.warningText}>
            {t('planning.draft.exhaustedText')}
          </Text>
        </View>
      ) : null}

      {draft.state === 'collecting' ? (
        <View style={styles.decisionRow}>
          <View style={styles.decisionButton}>
            <ActionButton
              disabled={locked || !draft.can_undo}
              label={t('creation.undo')}
              onPress={() => onTransition('undo')}
              secondary
            />
          </View>
          <View style={styles.decisionButton}>
            <ActionButton
              disabled={locked || draft.passed_count === 0}
              label={t('planning.draft.reviewPassed')}
              onPress={() => onTransition('reset_passed')}
              secondary
            />
          </View>
        </View>
      ) : null}

      {draft.state === 'placement' && !swipe.action ? (
        <>
          <Text style={styles.body}>{t('planning.draft.placementBody')}</Text>
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
            label={t('planning.draft.spread')}
            onPress={() => onSubmit('automatic')}
          />
          {draft.accepted_workouts.map((workout) => (
            <View key={workout.occurrence_id} style={styles.placementCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{workout.name}</Text>
                <StatusPill
                  label={t(disciplineLabels[workout.discipline])}
                  tone="neutral"
                />
              </View>
              <WorkoutSignals workout={workout} />
              <ScrollView
                contentContainerStyle={styles.dateChoiceRow}
                horizontal
                showsHorizontalScrollIndicator={false}
              >
                {weekDates.map((scheduledDate) => {
                  const selected =
                    placementByOccurrence.get(workout.occurrence_id) === scheduledDate;
                  const available = draft.available_dates.includes(scheduledDate);
                  return (
                    <Pressable
                      accessibilityRole="radio"
                      accessibilityState={{ checked: selected }}
                      disabled={busy || !available}
                      key={scheduledDate}
                      onPress={() => onPlace(workout.occurrence_id, scheduledDate)}
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
                          locale,
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
            label={t('planning.draft.reviewManual')}
            onPress={() => onSubmit('manual')}
            secondary
          />
          <ActionButton
            disabled={busy || !draft.can_undo}
            label={t('planning.draft.backToChoosing')}
            onPress={() => onTransition('undo')}
            secondary
          />
        </>
      ) : null}
    </View>
  );
}

export function PlanningScreen({ accessToken, athleteIdentity, ...presentation }: PlanningScreenProps) {
  return (
    <PlanningFlowProvider accessToken={accessToken} athleteIdentity={athleteIdentity}>
      <PlanningPresentationProvider><PlanningBoundary {...presentation} /></PlanningPresentationProvider>
    </PlanningFlowProvider>
  );
}

// Presentation host remains inside the one provider across root/task/detail switches.
export function PlanningBoundary(props: Omit<PlanningScreenProps, 'accessToken' | 'athleteIdentity'> & { destination?: 'week' | 'calendar'; active?: boolean; onCalendarRoot?: () => void; onWeekRoot?: () => void; }) {
  const flow = usePlanningFlow();
  const calendar = usePlanningCalendar();
  const { effectiveVersion, requested } = useUiVersion();
  const { t } = useLanguage();
  const { rootVersion, setRootVersion, calendarVersion, setCalendarVersion, task, setTask,
    detailWorkout, setDetailWorkout, weekScroll, calendarPositions, calendarNavigation, locked, activityBusy, setTransientBusy,
    sheetOpen, setCalendarVisited, creationStep, setCreationStep, placementMode, setPlacementMode, reviewWorkoutId, setReviewWorkoutId, moveWorkoutId, setMoveWorkoutId } = usePlanningPresentation();
  const active = props.active ?? true;
  const previousRequest = useRef(requested);
  const calendarOpen = props.destination === 'calendar' ||
    (flow.view === 'calendar' && (rootVersion === 'v1' || task === 'existing'));
  const { fromDate, toDate } = calendarNavigation.range;
  const { loadCalendarRange, ensureCalendarRange } = calendar;
  useEffect(() => {
    if (active && calendarOpen) setCalendarVisited(true);
  }, [active, calendarOpen, setCalendarVisited]);
  // One range effect above both presentations; neither Calendar view fetches.
  useEffect(() => {
    if (active && calendarOpen) ensureCalendarRange(fromDate, toDate);
  }, [active, calendarOpen, fromDate, toDate, ensureCalendarRange]);
  const calendarScrollKey = `${calendarVersion}:${calendarNavigation.mode}:${fromDate}:${toDate}`;
  const calendarScrollProps: ScrollViewProps = {
    contentOffset: { x: 0, y: calendarPositions.current[calendarScrollKey] ?? 0 }, scrollEventThrottle: 16,
    onScroll: (event) => { calendarPositions.current[calendarScrollKey] = event.nativeEvent.contentOffset.y; },
  };
  // Detail comparison changes the preference, while its origin stays put.
  useEffect(() => {
    if (active && previousRequest.current !== requested && !detailWorkout && !locked && !activityBusy && !sheetOpen) {
      if (calendarOpen) { setCalendarVersion(effectiveVersion('calendar')); if (props.destination && !task) setRootVersion(effectiveVersion('week')); }
      else if (!task) setRootVersion(effectiveVersion('week'));
    }
    previousRequest.current = requested;
  }, [requested, effectiveVersion, task, detailWorkout, locked, activityBusy, calendarOpen, active, sheetOpen, props.destination, setCalendarVersion, setRootVersion]);
  useEffect(() => {
    if (task === 'prepare' && flow.view === 'deck' && flow.swipeDraft) {
      setCreationStep('selection');
      setPlacementMode('automatic');
      setTask('creation');
    }
    // A successful shared submit sets plan/view only after resume storage settles.
    if ((task === 'creation' && !flow.swipeDraft && flow.view === 'plan') ||
      (task === 'review' && ['active', 'rejected'].includes(flow.plan?.revision_state ?? ''))) {
      setTask(null);
      setRootVersion(effectiveVersion('week'));
    }
  }, [task, flow.view, flow.swipeDraft, flow.plan?.revision_state, setTask, setCreationStep, setPlacementMode, setRootVersion, effectiveVersion]);
  const returnToWeek = () => { if (!locked) { setTask(null); if (rootVersion === 'v1' && calendarOpen) flow.setView('plan'); if (props.destination === 'calendar') props.onWeekRoot?.(); } };
  useEffect(() => {
    if (!active || sheetOpen || (!locked && !task && !calendarOpen) || (!locked && props.destination === 'calendar' && !task)) return;
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!locked) { if (task === 'review' && reviewWorkoutId) setReviewWorkoutId(null); else { setTask(null); if (rootVersion === 'v1' && calendarOpen) flow.setView('plan'); } }
      return true;
    });
    return () => handler.remove();
  }, [task, locked, calendarOpen, rootVersion, flow.setView, active, props.destination, setTask, sheetOpen, reviewWorkoutId, setReviewWorkoutId]);
  const action = (kind: WeekAction) => {
    if (locked) return;
    if (kind === 'calendar' && props.onCalendarRoot) { props.onCalendarRoot(); return; }
    if (kind === 'draft' || (kind === 'prepare' && flow.swipeDraft)) flow.openDeck();
    else if (kind === 'calendar') { setCalendarVersion(effectiveVersion('calendar')); flow.openCalendar(); }
    else flow.setView('plan');
    setTask(kind === 'prepare' && !flow.swipeDraft ? 'prepare' :
      kind === 'draft' || (kind === 'prepare' && flow.swipeDraft) ? 'creation' : kind === 'review' ? 'review' : 'existing');
    if (kind === 'review') setReviewWorkoutId(null);
  };
  const controls = showUiVersionControl() && <UiVersionControl disabled={locked || activityBusy || sheetOpen} onSelect={(version) => {
    if (!locked && !activityBusy && !sheetOpen && !detailWorkout) {
      if (calendarOpen) { setCalendarVersion(effectiveUiVersion(version, 'calendar')); if (props.destination && !task) { if (version === 'v1') flow.openCalendar(); setRootVersion(effectiveUiVersion(version, 'week')); } }
      else if (!task) {
        setRootVersion(effectiveUiVersion(version, 'week'));
        setCalendarVersion(effectiveUiVersion(version, 'calendar'));
      }
    }
  }} />;
  // Date-only planning uses local noon. Actual "today" follows the loaded plan's
  // confirmed timezone; without a plan, retain the existing device-date convention.
  const now = new Date();
  const todayParts = flow.plan ? new Intl.DateTimeFormat('en-CA', {
    timeZone: flow.plan.timezone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now) : null;
  const part = (name: Intl.DateTimeFormatPartTypes) => todayParts?.find((item) => item.type === name)?.value;
  const today = todayParts ? [part('year'), part('month'), part('day')].join('-') : isoDate(now);
  const model = weekHomeViewModel({
    plan: flow.plan, activePlan: flow.activePlan, draft: flow.swipeDraft,
    today, resumeState: flow.resumeState, activeReadState: flow.activeReadState
  });
  if (!active) return null;
  return <View style={{ flex: 1 }}>
    {calendarOpen && calendarVersion === 'v2' ? <CalendarScreen
      model={calendarViewModel({
        dates: calendarNavigation.dates, anchor: calendarNavigation.anchor,
        selectedDate: calendarNavigation.selectedDate, today: isoDate(now), workouts: calendar.calendarWorkouts,
        restDays: calendar.calendarRestDays, loadedRange: calendar.calendarRange
      })}
      mode={calendarNavigation.mode} anchor={calendarNavigation.anchor} loading={calendar.calendarLoading} error={flow.error}
      onModeChange={calendarNavigation.changeMode} onMove={calendarNavigation.move} onToday={calendarNavigation.goToday}
      onSelectDate={calendarNavigation.selectDate} onRetry={() => loadCalendarRange(fromDate, toDate)} onBack={returnToWeek}
      onProfile={props.destination === 'calendar' ? props.onOpenProfile : undefined}
      onOpenWorkout={(id) => { const workout = calendar.calendarWorkouts.find((item) => item.id === id); if (workout) setDetailWorkout(workout); }}
      onMoveWorkout={id => {
        const workout = flow.plan?.revision_state === 'active' && flow.plan.workouts.find(item => item.id === id && item.status === 'scheduled');
        const shown = calendar.calendarWorkouts.find(item => item.id === id);
        return workout && shown?.scheduled_date === workout.scheduled_date ? () => { if (!locked) { flow.setError(null); setMoveWorkoutId(id); } } : undefined;
      }}
      controls={controls} scrollProps={calendarScrollProps} />
      : rootVersion === 'v2' && (!task || (task === 'creation' && !flow.swipeDraft && flow.view === 'plan') || (task === 'review' && ['active', 'rejected'].includes(flow.plan?.revision_state ?? ''))) ? <WeekScreen model={model} error={flow.error} busy={locked}
        onAction={action} onOpenWorkout={(id) => {
          const workout = flow.activePlan?.workouts.find((item) => item.id === id);
          if (workout) setDetailWorkout(workout);
        }} onProfile={props.onOpenProfile} onActivities={props.onOpenActivities}
        onCheckIn={props.onOpenCheckIn} onZones={() => props.onOpenZoneProfile(flow.plan?.id, flow.plan?.active_revision ?? undefined)}
        goalName={flow.primaryGoal?.race_name ?? null} onGoal={() => action('planning')}
        controls={controls} scrollProps={{
          contentOffset: { x: 0, y: weekScroll.current }, scrollEventThrottle: 16,
          onScroll: (event) => { weekScroll.current = event.nativeEvent.contentOffset.y; }
        }} />
        : task === 'review' && flow.plan && effectiveVersion('proposalReview') === 'v2' ? <PlanningProposalTask
          controls={controls} busy={locked} workoutId={reviewWorkoutId} onEdit={setReviewWorkoutId} onBack={returnToWeek} />
        : task === 'prepare' && effectiveVersion('planningCreation') === 'v2' ? <AvailabilityScreen
          busy={locked} error={flow.error} controls={controls} onBack={returnToWeek}
          weekStart={flow.weekStart} selectedDays={flow.selectedDays} reusePreviousWeek={flow.reusePreviousWeek}
          injuries={flow.injuries} crossTrainingOptIns={flow.crossTrainingOptIns}
          onWeekStart={flow.setWeekStart} onToggleDay={flow.toggleDay}
          onReuse={() => flow.setReusePreviousWeek((current) => !current)}
          onInjury={flow.toggleInjury} onCrossTraining={flow.toggleCrossTraining} onCreate={flow.generate} />
        : task === 'creation' && flow.swipeDraft && flow.view === 'deck' && effectiveVersion('planningCreation') === 'v2' ? (
          creationStep === 'placement' && flow.swipeDraft.state === 'placement' ? <PlacementScreen
            model={planningCreationViewModel(flow.swipeDraft)} busy={locked} error={flow.error} controls={controls}
            onBack={returnToWeek} mode={placementMode} onMode={setPlacementMode}
            onPlace={flow.placeDraftWorkout} onSubmit={flow.submitDraft} onSelection={() => setCreationStep('selection')} />
          : <SelectionScreen model={planningCreationViewModel(flow.swipeDraft)} busy={locked} error={flow.error}
            controls={controls} onBack={returnToWeek} onTransition={flow.transitionDraft} setTransientBusy={setTransientBusy}
            onContinue={() => setCreationStep('placement')} />
        ) : <PlanningPresentation {...props} onOpenWorkout={setDetailWorkout}
          calendarNavigation={calendarNavigation} calendarScrollProps={calendarOpen ? calendarScrollProps : undefined}
          onOpenCalendar={() => { if (props.onCalendarRoot && rootVersion === 'v2') { props.onCalendarRoot(); return; } setCalendarVersion(effectiveVersion('calendar')); flow.openCalendar(); }}
          prepareWeek={task === 'prepare'} versionControl={controls}
          taskBack={rootVersion === 'v2' && task ? <V2Button variant="tertiary" label={t('week.return')} disabled={locked} onPress={returnToWeek} /> : null} />}
    {moveWorkoutId ? <PlanningWorkoutMoveTask key={moveWorkoutId} workoutId={moveWorkoutId} onClose={() => setMoveWorkoutId(null)} controls={controls} /> : null}
    <WorkoutDetailBoundary workout={detailWorkout} onClose={() => setDetailWorkout(null)} />
  </View>;
}

function PlanningPresentation({
  onOpenWorkout,
  prepareWeek,
  versionControl,
  taskBack,
  calendarNavigation,
  calendarScrollProps,
  onOpenCalendar,
  onBackToOnboarding,
  onOpenActivities,
  onOpenCheckIn,
  onOpenIntegrations,
  onOpenProfile,
  onOpenZoneProfile,
  onSignOut,
}: Omit<PlanningScreenProps, 'accessToken' | 'athleteIdentity'> & {
  onOpenWorkout: (workout: PlannedWorkout) => void; prepareWeek: boolean;
  versionControl: React.ReactNode; taskBack: React.ReactNode;
  calendarNavigation: CalendarNavigation; calendarScrollProps?: ScrollViewProps; onOpenCalendar: () => void;
}) {
  const { locale, t } = useLanguage();
  const safeAreaInsets = useSafeAreaInsets();
  const { sheetOpen: profileMenuOpen, setSheetOpen: setProfileMenuOpen } = usePlanningPresentation();
  const profileSheetRef = useRef<BottomSheetModal>(null);
  const profileSheetNavigationRef = useRef(createDeferredDismissAction());
  useEffect(() => {
    if (!profileMenuOpen) return;
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      profileSheetRef.current?.dismiss();
      return true;
    });
    return () => handler.remove();
  }, [profileMenuOpen]);
  const {
    view, setView, weekStart, setWeekStart, reusePreviousWeek, setReusePreviousWeek,
    selectedDays, injuries, crossTrainingOptIns, plan, swipeDraft, pendingMove,
    primaryGoal, maintenanceMarked, busy, error, availableDates, toggleDay,
    toggleInjury, toggleCrossTraining, generate, approve, reject, openDeck,
    transitionDraft, placeDraftWorkout, submitDraft, requestWorkoutMove,
    markGoalAchievement, clearPlan, cancelWorkoutMove,
    confirmWorkoutMove,
  } = usePlanningFlow();
  const { calendarWorkouts, calendarRestDays, calendarLoading, loadCalendarRange } = usePlanningCalendar();
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
    setProfileMenuOpen(true);
    profileSheetRef.current?.present();
  };

  const closeProfileSheetThen = (action: () => void) => {
    profileSheetNavigationRef.current.request(action, () => {
      profileSheetRef.current?.dismiss();
    });
  };

  const confirmGoalAchievement = () => {
    if (!primaryGoal) return;
    Alert.alert(
      t('planning.goal.confirmTitle'),
      t('planning.goal.confirmMessage'),
      [
        { text: t('planning.cancel'), style: 'cancel' },
        {
          text: t('planning.confirm'),
          onPress: markGoalAchievement,
        },
      ],
    );
  };

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      {taskBack}
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
          accessibilityLabel={t('planning.profileMenuLabel')}
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
            <Text style={styles.avatarText}>{t('planning.avatar')}</Text>
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

      {versionControl}

      <BottomSheetModal
        backdropComponent={renderProfileBackdrop}
        topInset={Math.max(safeAreaInsets.top, StatusBar.currentHeight ?? 0)}
        backgroundStyle={styles.profileSheetBackground}
        bottomInset={safeAreaInsets.bottom}
        enableDynamicSizing
        handleIndicatorStyle={styles.profileSheetHandle}
        onChange={(index) => setProfileMenuOpen(index >= 0)}
        onDismiss={() => {
          setProfileMenuOpen(false);
          profileSheetNavigationRef.current.completeDismiss();
        }}
        ref={profileSheetRef}
      >
        <BottomSheetScrollView contentContainerStyle={styles.profileSheet}>
          <SupportingProfileMenu
            onOpenProfile={() => closeProfileSheetThen(onOpenProfile)}
            onOpenIntegrations={() => closeProfileSheetThen(onOpenIntegrations)}
            onSignOut={() => closeProfileSheetThen(() => void onSignOut())}
          />
        </BottomSheetScrollView>
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
          <Text style={styles.quickActionText}>{t('week.checkIn')}</Text>
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
          onPress={onOpenCalendar}
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
          {...calendarScrollProps}
          automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}
          contentContainerStyle={styles.content}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          style={styles.scroll}
        >
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy && (view !== 'deck' || !swipeDraft?.current_candidate) ? <ActivityIndicator color={colors.brand} /> : null}

        <FadeInView key={view} style={styles.viewContent}>
        {view === 'plan' ? (
          <>
            {!plan || prepareWeek ? (
              <View style={styles.panel}>
                <StatusPill label={t('planning.prepare.pill')} tone="brand" />
                <Text style={styles.title}>{t('creation.availability')}</Text>
                <Text style={styles.body}>{t('planning.prepare.body')}</Text>
                <FormField
                  autoCapitalize="none"
                  inputMode="numeric"
                  label={t('creation.weekStart')}
                  maxLength={10}
                  onChangeText={(value) =>
                    setWeekStart(formatIsoDateInput(value))
                  }
                  placeholder={t('planning.datePlaceholder')}
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
                    {t('creation.reuse')}
                  </Text>
                </Pressable>
                <Text style={styles.hint}>{t('planning.prepare.reuseHint')}</Text>
                <Text style={styles.fieldLabel}>{t('creation.injuries')}</Text>
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
                        {t(disciplineLabels[discipline])}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                {injuries.size > 0 ? (
                  <>
                    <Text style={styles.fieldLabel}>
                      {t('creation.crossTraining')}
                    </Text>
                    <Text style={styles.hint}>
                      {t('planning.prepare.crossTrainingHint')}
                    </Text>
                    <View style={styles.choiceRow}>
                      {(['bike', 'swim'] as const)
                        .filter((discipline) => !injuries.has(discipline))
                        .map((discipline) => (
                          <Pressable
                            accessibilityRole="checkbox"
                            accessibilityState={{
                              checked: crossTrainingOptIns.has(discipline),
                            }}
                            key={`cross-${discipline}`}
                            onPress={() => toggleCrossTraining(discipline)}
                            style={[
                              styles.disciplineChoice,
                              crossTrainingOptIns.has(discipline) &&
                                styles.choiceActive,
                            ]}
                          >
                            <Text style={styles.choiceText}>
                              {t(disciplineLabels[discipline])}
                            </Text>
                          </Pressable>
                        ))}
                    </View>
                  </>
                ) : null}
                <ActionButton
                  disabled={
                    busy || (!reusePreviousWeek && availableDates.length === 0)
                  }
                  label={t('planning.prepare.create')}
                  onPress={() => void generate()}
                />
                <ActionButton
                  label={t('planning.prepare.backToOnboarding')}
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
                          ? t('common.active')
                          : plan.revision_state === 'pending_approval'
                            ? t('planning.plan.waiting')
                            : plan.revision_state
                      }
                      tone={
                        plan.revision_state === 'active' ? 'brand' : 'accent'
                      }
                    />
                    <Text style={styles.cardMeta}>{t('planning.plan.revision', { revision: plan.revision })}</Text>
                  </View>
                  <Text style={styles.title}>{t('planning.plan.weekOf', { date: plan.week_start })}</Text>
                  <Text style={styles.body}>
                    {Number(plan.total_duration_minutes) > 0
                      ? t('planning.plan.timedMinutes', { minutes: Number(plan.total_duration_minutes) })
                      : ''}
                    {t('planning.plan.summary', { count: plan.workouts.length, phase: plan.phase })}
                  </Text>
                  <Text style={styles.body}>
                    {Number(plan.total_duration_minutes) > 0
                      ? t('planning.plan.timeSplit', { low: plan.display_low_intensity_percent, high: plan.display_high_intensity_percent })
                      : t('planning.plan.noTimeSplit')}
                  </Text>
                  {Number(plan.total_duration_minutes) > 0 ? (
                    <Text style={styles.hint}>
                      {t('planning.plan.intensityMinutes', { low: Number(plan.low_intensity_minutes), high: Number(plan.high_intensity_minutes) })}
                    </Text>
                  ) : null}
                  <View style={styles.selectionProgress}>
                    <Text style={styles.selectionProgressValue}>
                      {t('planning.chosenProgress', { accepted: plan.workouts.length, target: plan.workouts.length })}
                    </Text>
                    <Text style={styles.selectionProgressLabel}>
                      {plan.warnings.some(
                        (warning) =>
                          warning.code ===
                          'target_outside_catalog_capacity',
                      )
                        ? t('planning.plan.targetAttention')
                        : t('planning.plan.complete')}
                    </Text>
                  </View>
                  <Text style={styles.hint}>
                    {t('planning.plan.availability', {
                      dates: plan.available_dates.join(', '),
                      source: t(plan.availability_source === 'previous_week'
                        ? 'planning.plan.source.previousWeek'
                        : plan.availability_source === 'checkin'
                          ? 'planning.plan.source.checkin'
                          : 'planning.plan.source.selected'),
                    })}
                  </Text>
                  {primaryGoal ? (
                    <ActionButton
                      disabled={busy || maintenanceMarked}
                      label={
                        maintenanceMarked
                          ? t('planning.goal.maintenanceConfirmed')
                          : t('planning.goal.markAchieved', { name: primaryGoal.race_name })
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
                      <Text style={styles.warningTitle}>{t('planning.plan.coachExplanation')}</Text>
                      <Text style={styles.warningText}>
                        {coachExplanation(plan.proposal.public_explanation, t)}
                      </Text>
                    </View>
                  ) : null}
                  {['rejected', 'expired'].includes(plan.revision_state) ? (
                    <ActionButton
                      label={t('planning.plan.prepareNew')}
                      onPress={clearPlan}
                      secondary
                    />
                  ) : null}
                </View>
                {plan.revision_state === 'pending_approval' &&
                plan.proposal?.state === 'pending' ? (
                  <View style={styles.swipeIntro}>
                    <Text style={styles.swipeIntroTitle}>
                      {t('planning.composeWeek')}
                    </Text>
                    <Text style={styles.body}>{t('planning.plan.swipeIntro')}</Text>
                  </View>
                ) : null}
                {plan.revision_state === 'active' ? (
                  <>
                    <WeekSchedule
                      busy={busy}
                      onOpenWorkout={onOpenWorkout}
                      onMove={requestWorkoutMove}
                      weekStart={plan.week_start}
                      workouts={plan.workouts}
                    />
                    {pendingMove ? (
                      <MoveWarningPanel
                        onCancel={cancelWorkoutMove}
                        onConfirm={confirmWorkoutMove}
                        warnings={pendingMove.warnings}
                      />
                    ) : null}
                  </>
                ) : (
                  plan.workouts.map((workout, index) => (
                    <View key={workout.id} style={styles.workoutStack}>
                      {plan.revision_state === 'pending_approval' &&
                      plan.proposal?.state === 'pending' ? (
                        <PendingWorkoutEditor
                          busy={busy}
                          plan={plan}
                          slotIndex={index}
                          workout={workout}
                        />
                      ) : (
                        <WorkoutCard workout={workout} />
                      )}
                    </View>
                  ))
                )}
                {plan.proposal?.state === 'pending' ? (
                  <View style={styles.approvalPanel}>
                    <Text style={styles.approvalTitle}>{t('planning.plan.doneTitle')}</Text>
                    <Text style={styles.body}>{t('planning.plan.doneBody')}</Text>
                    <View style={styles.decisionRow}>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label={t('review.approve')}
                          onPress={approve}
                        />
                      </View>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label={t('planning.plan.reject')}
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
              <StatusPill label={t('planning.deck.pill')} tone="brand" />
              <Text style={styles.title}>{t('planning.deck.emptyTitle')}</Text>
              <Text style={styles.body}>{t('planning.deck.emptyBody')}</Text>
              <ActionButton label={t('planning.deck.toWeek')} onPress={() => setView('plan')} />
            </View>
          )
        ) : null}

        {view === 'calendar' ? (
          <View style={styles.panel}>
            <TrainingCalendar
              navigation={calendarNavigation}
              initialDate={plan?.week_start ?? weekStart}
              loading={calendarLoading}
              onRangeChange={loadCalendarRange}
              onOpenWorkout={onOpenWorkout}
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
  profileSheetBackground: { backgroundColor: finalColors.surface, borderRadius: finalRadius.sheet },
  profileSheetHandle: { backgroundColor: finalColors.borderControl, width: 42 },
  profileSheet: { padding: finalLayout.phoneGutter, paddingBottom: finalSpace[48] },
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
  swipeWindow: { overflow: 'hidden' },
  swipeLoading: { alignItems: 'center', justifyContent: 'center' },
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
  workoutSignals: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  calibrationSignal: {
    alignItems: 'center',
    backgroundColor: colors.highlightSoft,
    borderRadius: radius.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  calibrationLogo: {
    alignItems: 'center',
    backgroundColor: colors.highlight,
    borderRadius: radius.pill,
    height: 20,
    justifyContent: 'center',
    width: 20,
  },
  calibrationLogoText: {
    color: colors.brandDeep,
    fontSize: 7,
    fontWeight: '900',
  },
  calibrationSignalText: {
    color: colors.brandDeep,
    fontSize: 10,
    fontWeight: '900',
  },
  zoneEvidenceSignal: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  zoneEvidenceSignalText: {
    color: colors.brand,
    fontSize: 10,
    fontWeight: '800',
  },
  calibrationNotice: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  calibrationNoticeTitle: {
    color: colors.brand,
    fontSize: 13,
    fontWeight: '900',
  },
  calibrationNoticeText: {
    color: colors.ink,
    fontSize: 12,
    lineHeight: 18,
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
