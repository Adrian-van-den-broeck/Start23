import { studioPresentation } from '../../ui-v3/presentation';
import { PlacementRail } from '../../ui-v3/PlacementRail';
import { ChosenRow } from '../../ui-v3/ChosenRow';
import { CandidateDeck } from '../../ui-v3/CandidateDeck';
import { useMemo, type ReactNode } from 'react';
import { Animated, StyleSheet, useWindowDimensions, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { useWorkoutSwipe, type WorkoutDecision } from '../../components/useWorkoutSwipe';
import { addDays, isoDate, nextMonday } from '../../features/planning/planningDates';
import { useLanguage } from '../../i18n/LanguageProvider';
import { isValidIsoDateInput } from '../../lib/dateInput';
import { WorkoutFacts } from '../components/WorkoutFacts';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { SelectField } from '../primitives/SelectField';
import { Icon } from '../primitives/Icon';
import { Notice } from '../primitives/Notice';
import { SportIndicator } from '../components/SportIndicator';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { PlanningCreationModel, SelectionWorkout } from '../utils/planningCreationViewModel';

// The server accepts any Monday as a week start and sets no past or future
// limit. Offered: the running week (to start right away) and the next four.
const UPCOMING_WEEKS = 4;

type TaskProps = { busy: boolean; error: string | null; onBack: () => void; controls: ReactNode };

export function AvailabilityScreen(props: TaskProps & {
  weekStart: string; selectedDays: ReadonlySet<number>; reusePreviousWeek: boolean;
  injuries: ReadonlySet<Discipline>; crossTrainingOptIns: ReadonlySet<Discipline>;
  onWeekStart: (value: string) => void; onToggleDay: (offset: number) => void;
  onReuse: () => void; onInjury: (discipline: Discipline) => void;
  onCrossTraining: (discipline: Discipline) => void; onCreate: () => Promise<void>;
}) {
  const { t, locale } = useLanguage();
  const validDate = isValidIsoDateInput(props.weekStart);
  const weekOptions = useMemo(() => {
    const next = nextMonday();
    const mondays = Array.from({ length: UPCOMING_WEEKS + 1 }, (_, index) => isoDate(addDays(next, (index - 1) * 7)));
    // A restored draft or plan keeps its own week, also when it is not one of the offered Mondays.
    const all = validDate && !mondays.includes(props.weekStart) ? [...mondays, props.weekStart].sort() : mondays;
    return all.map((monday) => {
      const date = addDays(monday, 0).toLocaleDateString(locale, { day: 'numeric', month: 'long' });
      const label = monday === next ? `${t('planning.week.next')} \u00b7 ${date}`
        : monday === mondays[0] ? `${t('planning.week.current')} \u00b7 ${date}` : `${t('planning.week.later')} ${date}`;
      return { value: monday, label };
    });
  }, [locale, props.weekStart, t, validDate]);
  return <Screen keyboardAware title={t('creation.availability')} landscape="ridges" titleVariant="display"
      onBack={props.onBack} backLabel={t('week.return')} backDisabled={props.busy}>
      <CreationStatus busy={props.busy} error={props.error} />
      <Text tone="textMuted">{t('creation.availabilityHint')}</Text>
      <Card padding="form" elevated style={styles.form}>
        <SelectField label={t('creation.weekStart')} value={validDate ? props.weekStart : null} options={weekOptions}
          onChange={props.onWeekStart} disabled={props.busy} placeholder={t('planning.week.choose')} />
        <View style={styles.stack}>
          {Array.from({ length: 7 }, (_, offset) => {
            // Weekday labels remain available while no valid week is chosen.
            const weekday = new Date(2026, 7, 3 + offset, 12).toLocaleDateString(locale, { weekday: 'long' });
            const date = validDate ? addDays(props.weekStart, offset).toLocaleDateString(locale, { day: 'numeric', month: 'long' }) : '';
            return <ChoiceRow key={offset} mode="checkbox" label={`${weekday}${date ? ` \u00b7 ${date}` : ''}`}
              selected={props.selectedDays.has(offset)} disabled={props.busy} onPress={() => props.onToggleDay(offset)} />;
          })}
        </View>
        <ChoiceRow mode="checkbox" label={t('creation.reuse')} hint={t('creation.reuseHint')}
          selected={props.reusePreviousWeek} disabled={props.busy} onPress={props.onReuse} />
      </Card>
      <Card padding="form" elevated style={styles.form}>
        <Text variant="sectionTitle" accessibilityRole="header">{t('creation.injuries')}</Text>
        <View style={styles.stack}>
          {(['swim', 'bike', 'run'] as const).map((sport) => <ChoiceRow key={sport} mode="checkbox"
            label={t(`common.${sport}`)} accessibilityLabel={`${t('creation.injuries')} \u00b7 ${t(`common.${sport}`)}`}
            selected={props.injuries.has(sport)} disabled={props.busy} onPress={() => props.onInjury(sport)} />)}
        </View>
        {props.injuries.size > 0 ? <>
          <Divider />
          <Text variant="sectionTitle" accessibilityRole="header">{t('creation.crossTraining')}</Text>
          <Text variant="supporting" tone="textMuted">{t('creation.crossTrainingHint')}</Text>
          <View style={styles.stack}>
            {(['bike', 'swim'] as const).filter((sport) => !props.injuries.has(sport)).map((sport) =>
              <ChoiceRow key={sport} mode="checkbox" label={t(`common.${sport}`)} accessibilityLabel={`${t('creation.crossTraining')} \u00b7 ${t(`common.${sport}`)}`}
                selected={props.crossTrainingOptIns.has(sport)} disabled={props.busy} onPress={() => props.onCrossTraining(sport)} />)}
          </View>
        </> : null}
        <Button label={t('creation.create')} trailingIcon="forward" busy={props.busy}
          disabled={!props.reusePreviousWeek && props.selectedDays.size === 0}
          disabledReason={!props.reusePreviousWeek && props.selectedDays.size === 0 ? t('creation.emptyDates') : undefined}
          onPress={props.onCreate} />
      </Card>
      {props.controls}
    </Screen>;
}

function AcceptedList({ accepted }: { accepted: readonly SelectionWorkout[] }) {
  const { t } = useLanguage();
  return <View style={studioPresentation ? styles.chosen : styles.summary} testID="accepted-occurrences">
    <Text variant="sectionTitle" accessibilityRole="header">{t('creation.accepted')}</Text>
    {accepted.length === 0 ? <Text tone="textMuted">{t('creation.acceptedEmpty')}</Text> : null}
    {accepted.map((workout, index) => studioPresentation ? <ChosenRow key={workout.occurrenceId} {...workout} position={index + 1} /> : <Card key={workout.occurrenceId} elevated style={styles.summary}>
      <Text variant="label" tone="textMuted">{t('creation.choiceNumber', { number: index + 1 })}</Text>
      <SelectionSummary workout={workout} />
    </Card>)}
  </View>;
}

function DraftWarnings({ model }: { model: PlanningCreationModel }) {
  return <>{model.warnings.map((warning, index) => <Notice key={index} tone="warning" title={warning.title}>
    {warning.message}
  </Notice>)}</>;
}

function CreationStatus({ busy, error }: Pick<TaskProps, 'busy' | 'error'>) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text tone="textMuted" accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('creation.saving')}</Text> : null}
    {error ? <View style={styles.error}>
      <Icon name="warning" color={colors.destructive} />
      <Text tone="destructive" style={styles.grow} accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text>
    </View> : null}
  </>;
}

function SelectionSummary({ workout, focus = false }: { workout: SelectionWorkout; focus?: boolean }) {
  return <View style={styles.summary} testID={`selection-occurrence-${workout.occurrenceId}`}>
    <SportIndicator discipline={workout.discipline} size={focus ? 'focus' : 'row'} tone="primary">
      <Text variant="cardTitle" accessibilityRole="header">{workout.name}</Text>
    </SportIndicator>
    <WorkoutFacts variant="focus" measures={{ durationMinutes: workout.durationMinutes, distanceMeters: workout.distanceMeters }} intensity={workout.intensity} />
    {workout.description ? <Text tone="textMuted">{workout.description}</Text> : null}
  </View>;
}

export function SelectionScreen({ model, onTransition, onContinue, setTransientBusy, ...task }: TaskProps & {
  model: PlanningCreationModel; onTransition: (action: WorkoutDecision) => void | Promise<void>;
  onContinue: () => void;
  setTransientBusy?: (busy: boolean) => void;
}) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const swipe = useWorkoutSwipe(model.state === 'collecting' ? model.candidate : null, task.busy, onTransition, setTransientBusy,
    (decision) => model.upcoming[decision]);
  const candidate = swipe.card;
  const locked = task.busy || !!swipe.action;
  // Both history actions stack when labels cannot fit without shrinking.
  const stacked = width < 393 || fontScale >= 1.5;
  return <Screen title={t('creation.selection')} landscape="ridges" titleVariant="display"
    onBack={task.onBack} backLabel={t('week.return')} backDisabled={locked}>
    <CreationStatus busy={task.busy && !swipe.action} error={swipe.action ? null : task.error} />
    {model.warnings.map((warning, index) => <View key={index} style={styles.warning}>
      <Icon name="warning" color={colors.warning} />
      <View style={[styles.grow, styles.stack]}>
        <Text variant="label" tone="warning">{warning.title}</Text><Text tone="warning">{warning.message}</Text>
      </View>
    </View>)}
    {candidate && studioPresentation ? <View testID="selection-candidate">
      <CandidateDeck card={candidate} action={swipe.action} locked={locked} stacked={width < 340 || fontScale >= 1.5} decide={swipe.decide} />
    </View> : candidate ? <Card padding="focus" elevated style={styles.form} testID="selection-candidate">
      <View style={styles.swipeWindow}>
        <Animated.View pointerEvents="none" accessibilityElementsHidden={!swipe.action}
          importantForAccessibility={swipe.action ? 'auto' : 'no-hide-descendants'}
          style={[StyleSheet.absoluteFill, styles.swipeLoading, { opacity: swipe.loadingOpacity }]}>
          <Text tone="textMuted" accessibilityLiveRegion="polite">{t('creation.nextCard')}</Text>
        </Animated.View>
        <Animated.View {...swipe.panHandlers} testID="workout-swipe-surface"
          accessibilityElementsHidden={!!swipe.action}
          importantForAccessibility={swipe.action ? 'no-hide-descendants' : 'auto'}
          style={[styles.swipeCard, { transform: swipe.transform, opacity: swipe.opacity }]}>
          <SelectionSummary key={candidate.occurrenceId} workout={candidate} focus />
          <Text variant="supporting" tone="textMuted">{t('creation.swipeChoice')}</Text>
          <Animated.View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants"
            style={[styles.swipeBadge, styles.chooseBadge, { opacity: swipe.acceptOpacity }]}>
            <Text variant="label" tone="primary">{t('creation.choose')}</Text>
          </Animated.View>
          <Animated.View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants"
            style={[styles.swipeBadge, styles.passBadge, { opacity: swipe.passOpacity }]}>
            <Text variant="label" tone="textMuted">{t('creation.pass')}</Text>
          </Animated.View>
        </Animated.View>
      </View>
      <View style={styles.stack}>
        <Button label={t('creation.choose')} accessibilityLabel={`${t('creation.choose')} \u00b7 ${candidate.name}`}
          trailingIcon="forward" disabled={locked} onPress={() => { void swipe.decide('accept'); }} />
        <Button label={t('creation.pass')} accessibilityLabel={`${t('creation.pass')} \u00b7 ${candidate.name}`}
          variant="secondary" disabled={locked} onPress={() => { void swipe.decide('pass'); }} />
      </View>
    </Card> : model.state === 'collecting' ? <Card padding="focus" elevated style={styles.summary} testID="selection-empty">
      {!model.exhausted && task.busy ? <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.stack}>
        <View style={styles.skeletonCircle} /><View style={styles.skeletonLine} /><View style={styles.skeletonLine} />
      </View> : null}
      <Text tone="textMuted">{t(model.exhausted ? 'creation.exhausted' : 'creation.unavailable')}</Text>
    </Card> : null}
    <View style={styles.history}>
      <View style={styles.countRule}>
        <Text variant="supporting" tone="textMuted" style={styles.count}>{t('creation.passed', { count: model.passedCount })}</Text>
        <View style={styles.rule} />
      </View>
      <View style={[styles.actions, stacked && styles.stackedActions]}>
        <View style={styles.action}>
          <Button label={t('creation.undo')} trailingIcon="undo" variant={studioPresentation ? 'tertiary' : 'outline'} disabled={locked || !model.canUndo}
            onPress={() => onTransition('undo')} />
        </View>
        <View style={styles.action}>
          <Button label={t('creation.reset')} trailingIcon="list" variant={studioPresentation ? 'tertiary' : 'outline'} disabled={locked || model.passedCount === 0}
            onPress={() => onTransition('reset_passed')} />
        </View>
      </View>
    </View>
    <View style={studioPresentation ? styles.chosen : styles.summary} testID="accepted-occurrences">
      <Text variant="sectionTitle" accessibilityRole="header">{t('creation.accepted')}</Text>
      {model.accepted.length === 0 ? <Text tone="textMuted">{t('creation.acceptedEmpty')}</Text> : null}
      {model.accepted.map((workout, index) => studioPresentation ? <ChosenRow key={workout.occurrenceId} {...workout} position={index + 1} /> : <Card key={workout.occurrenceId} elevated style={styles.summary}>
        <Text variant="label" tone="textMuted">{t('creation.choiceNumber', { number: index + 1 })}</Text>
        <SelectionSummary workout={workout} />
      </Card>)}
    </View>
    <Button label={t('creation.continue')} trailingIcon="forward" disabled={locked || model.state !== 'placement'} onPress={onContinue} />
    {task.controls}
  </Screen>;
}

export function PlacementScreen({ model, mode, onMode, onPlace, onSubmit, onSelection, ...task }: TaskProps & {
  model: PlanningCreationModel; mode: 'automatic' | 'manual'; onMode: (mode: 'automatic' | 'manual') => void;
  onPlace: (occurrenceId: string, date: string) => void;
  onSubmit: (mode: 'automatic' | 'manual') => void; onSelection: () => void;
}) {
  const { t, locale } = useLanguage();
  // Same mechanical completion requirement as V1; server validates the layout.
  const manualComplete = model.placements.length === model.accepted.length;
  const placements = new Map(model.placements.map((placement) => [placement.occurrenceId, placement.date]));
  return <Screen title={t('creation.placement')} landscape="ridges" titleVariant="display"
    onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    {task.busy ? <Text tone="textMuted" accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('creation.saving')}</Text> : null}
    {task.error ? <View accessible accessibilityRole="alert" accessibilityLabel={task.error} accessibilityLiveRegion="polite">
      <Notice tone="error" title={t('creation.placement')}>{task.error}</Notice>
    </View> : null}
    <DraftWarnings model={model} />
    <Card padding="form" elevated style={styles.summary}>
      <Text tone="textMuted">{t('creation.pendingHint')}</Text>
      <ChoiceRow label={t('creation.automatic')} selected={mode === 'automatic'} disabled={task.busy} onPress={() => onMode('automatic')} />
      <ChoiceRow label={t('creation.manual')} selected={mode === 'manual'} disabled={task.busy} onPress={() => onMode('manual')} />
    </Card>
    {mode === 'automatic' ? <>
      <Text tone="textMuted">{t('creation.automaticHint')}</Text>
      <AcceptedList accepted={model.accepted} />
    </> : <View style={styles.summary}>
      <Text tone="textMuted">{t('creation.manualHint')}</Text>
      {model.accepted.map((workout, index) => <Card key={workout.occurrenceId} elevated style={[styles.summary, studioPresentation && styles.placementGroup]}>
        <Text variant="label" tone="textMuted">{t('creation.choiceNumber', { number: index + 1 })}</Text>
        <PlacementRail workout={studioPresentation ? <View testID={`selection-occurrence-${workout.occurrenceId}`} style={styles.stack}>
          <View style={styles.placementSport}><Icon name={workout.discipline} size={20} color={colors.primary} />
            <Text variant="caption" tone="primary">{t(`common.${workout.discipline}`)}</Text></View>
          <Text variant="cardTitle" accessibilityRole="header">{workout.name}</Text>
          <View style={styles.placementSport}>
            {workout.durationMinutes !== null && <Text variant="label">{t('common.durationMinutes', { minutes: workout.durationMinutes })}</Text>}
            {workout.distanceMeters !== null && <Text variant="label">{t('detail.meters', { value: workout.distanceMeters })}</Text>}
            <Text variant="supporting" tone="textMuted">{t(`detail.intensity.${workout.intensity}`)}</Text>
          </View>
          {workout.description ? <Text variant="supporting" tone="textMuted">{workout.description}</Text> : null}
        </View> : <><SelectionSummary workout={workout} /><Divider /></>} label={t('creation.choiceNumber', { number: index + 1 }) + ' \u00b7 ' + workout.name} dates={model.availableDates} selected={placements.get(workout.occurrenceId)} disabled={task.busy}
          onSelect={date => onPlace(workout.occurrenceId, date)}>
          {model.availableDates.map((date) => {
            const label = new Date(`${date}T12:00:00`).toLocaleDateString(locale, {
              weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
            });
            return <ChoiceRow key={date} label={label}
              accessibilityLabel={`${t('creation.choiceNumber', { number: index + 1 })} · ${workout.name} · ${label}`}
              selected={placements.get(workout.occurrenceId) === date} disabled={task.busy}
              onPress={() => onPlace(workout.occurrenceId, date)} />;
          })}
        </PlacementRail>
      </Card>)}
    </View>}
    <Button label={t(mode === 'automatic' ? 'creation.submitAutomatic' : 'creation.submitManual')}
      trailingIcon="forward" busy={task.busy} disabled={model.state !== 'placement' || (mode === 'manual' && !manualComplete)}
      disabledReason={mode === 'manual' && !manualComplete ? t('creation.incomplete') : undefined}
      onPress={() => onSubmit(mode)} />
    <Button label={t('creation.backSelection')} variant="tertiary" busy={task.busy} onPress={onSelection} />
    {task.controls}
  </Screen>;
}

const styles = StyleSheet.create({
  stack: { gap: space[12] }, chosen: { gap: space[8] },
  placementGroup: { borderWidth: 0, padding: 0, backgroundColor: 'transparent', gap: 8 },
  placementSport: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[8] },
  frame: { flex: 1 }, grow: { flex: 1 },
  form: { gap: space[24] }, summary: { gap: space[16] },
  error: { flexDirection: 'row', alignItems: 'flex-start', gap: space[12], padding: space[16], borderRadius: radius.inset, backgroundColor: colors.destructiveSoft },
  warning: { flexDirection: 'row', alignItems: 'flex-start', gap: space[12], padding: space[16], borderRadius: radius.inset, backgroundColor: colors.warningSoft },
  history: { gap: space[16], marginTop: space[8] },
  countRule: { flexDirection: 'row', alignItems: 'center', gap: space[12] },
  count: { flexShrink: 1 }, rule: { height: layout.decorativeLine, flex: 1, backgroundColor: colors.border },
  actions: { flexDirection: 'row', alignItems: 'stretch', gap: space[12] },
  stackedActions: { flexDirection: 'column' }, action: { flex: 1 },
  swipeWindow: { overflow: 'hidden' },
  swipeCard: { gap: space[16], backgroundColor: colors.surface },
  swipeLoading: { alignItems: 'center', justifyContent: 'center' },
  swipeBadge: { position: 'absolute', top: space[8], padding: space[8], borderRadius: radius.pill, backgroundColor: colors.surfaceSubtle },
  chooseBadge: { left: space[8], backgroundColor: colors.primarySoft },
  passBadge: { right: space[8] },
  skeletonCircle: { width: layout.iconDisc.focus, height: layout.iconDisc.focus, borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  skeletonLine: { height: space[24], borderRadius: radius.inset, backgroundColor: colors.surfaceSubtle },
});
