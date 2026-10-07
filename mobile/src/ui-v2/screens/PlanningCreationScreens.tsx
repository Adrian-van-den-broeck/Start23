import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, useWindowDimensions, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { addDays } from '../../features/planning/planningDates';
import { useLanguage } from '../../i18n/LanguageProvider';
import { formatIsoDateInput, isValidIsoDateInput } from '../../lib/dateInput';
import { WorkoutFacts } from '../components/WorkoutFacts';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Input } from '../primitives/Input';
import { Icon } from '../primitives/Icon';
import { SportIndicator } from '../components/SportIndicator';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import type { PlanningCreationModel, SelectionWorkout } from '../utils/planningCreationViewModel';

type TaskProps = { busy: boolean; error: string | null; onBack: () => void; controls: ReactNode };

function TaskStatus({ busy, error }: Pick<TaskProps, 'busy' | 'error'>) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('creation.saving')}</Text> : null}
    {error ? <Text style={{ color: colors.destructive }} accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text> : null}
  </>;
}

export function AvailabilityScreen(props: TaskProps & {
  weekStart: string; selectedDays: ReadonlySet<number>; reusePreviousWeek: boolean;
  injuries: ReadonlySet<Discipline>; crossTrainingOptIns: ReadonlySet<Discipline>;
  onWeekStart: (value: string) => void; onToggleDay: (offset: number) => void;
  onReuse: () => void; onInjury: (discipline: Discipline) => void;
  onCrossTraining: (discipline: Discipline) => void; onCreate: () => Promise<void>;
}) {
  const { t, locale } = useLanguage();
  const validDate = isValidIsoDateInput(props.weekStart);
  return <KeyboardAvoidingView style={styles.frame} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
    <Screen title={t('creation.availability')} landscape="ridges" titleVariant="display"
      onBack={props.onBack} backLabel={t('week.return')} backDisabled={props.busy}
      scrollProps={{ keyboardShouldPersistTaps: 'handled', automaticallyAdjustKeyboardInsets: true }}>
      <CreationStatus busy={props.busy} error={props.error} />
      <Text tone="textMuted">{t('creation.availabilityHint')}</Text>
      <Card padding="form" elevated style={styles.form}>
        <Input label={t('creation.weekStart')} icon="calendar" value={props.weekStart}
          onChangeText={(value) => props.onWeekStart(formatIsoDateInput(value))} disabled={props.busy}
          inputMode="numeric" autoCapitalize="none" maxLength={10} placeholder="YYYY-MM-DD" />
        <View style={styles.stack}>
          {Array.from({ length: 7 }, (_, offset) => {
            // Weekday labels remain available while the date input is incomplete.
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
    </Screen>
  </KeyboardAvoidingView>;
}

function OccurrenceSummary({ workout }: { workout: SelectionWorkout }) {
  const { t } = useLanguage();
  return <View style={styles.stack} testID={`selection-occurrence-${workout.occurrenceId}`}>
    <SportIndicator discipline={workout.discipline} />
    <Text variant="sectionTitle" accessibilityRole="header">{workout.name}</Text>
    {workout.durationMinutes !== null ? <Text accessibilityLabel={t('detail.minutesSpoken', { value: workout.durationMinutes })}>
      {t('common.durationMinutes', { minutes: workout.durationMinutes })}</Text> : null}
    {workout.distanceMeters !== null ? <Text accessibilityLabel={t('detail.metersSpoken', { value: workout.distanceMeters })}>
      {t('detail.meters', { value: workout.distanceMeters })}</Text> : null}
    <Text>{t(`detail.intensity.${workout.intensity}`)}</Text>
    {workout.description ? <Text variant="supporting">{workout.description}</Text> : null}
  </View>;
}

function AcceptedList({ accepted }: { accepted: readonly SelectionWorkout[] }) {
  const { t } = useLanguage();
  return <View style={styles.stack} testID="accepted-occurrences">
    <Text variant="sectionTitle" accessibilityRole="header">{t('creation.accepted')}</Text>
    {accepted.length === 0 ? <Text>{t('creation.acceptedEmpty')}</Text> : null}
    {accepted.map((workout, index) => <Card key={workout.occurrenceId} style={styles.stack}>
      <Text variant="label">{t('creation.choiceNumber', { number: index + 1 })}</Text>
      <OccurrenceSummary workout={workout} />
    </Card>)}
  </View>;
}

function DraftWarnings({ model }: { model: PlanningCreationModel }) {
  return <>{model.warnings.map((warning, index) => <Card key={index}>
    <Text variant="label">{warning.title}</Text><Text>{warning.message}</Text>
  </Card>)}</>;
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

export function SelectionScreen({ model, onTransition, onContinue, ...task }: TaskProps & {
  model: PlanningCreationModel; onTransition: (action: 'accept' | 'pass' | 'undo' | 'reset_passed') => void;
  onContinue: () => void;
}) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const candidate = model.state === 'collecting' ? model.candidate : null;
  // Both history actions stack when labels cannot fit without shrinking.
  const stacked = width < 393 || fontScale >= 1.5 || task.busy;
  return <Screen title={t('creation.selection')} landscape="ridges" titleVariant="display"
    onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    <CreationStatus busy={task.busy} error={task.error} />
    {model.warnings.map((warning, index) => <View key={index} style={styles.warning}>
      <Icon name="warning" color={colors.warning} />
      <View style={[styles.grow, styles.stack]}>
        <Text variant="label" tone="warning">{warning.title}</Text><Text tone="warning">{warning.message}</Text>
      </View>
    </View>)}
    {candidate ? <Card padding="focus" elevated style={styles.form} testID="selection-candidate">
      <SelectionSummary key={candidate.occurrenceId} workout={candidate} focus />
      <View style={styles.stack}>
        <Button label={t('creation.choose')} accessibilityLabel={`${t('creation.choose')} \u00b7 ${candidate.name}`}
          trailingIcon="forward" busy={task.busy} onPress={() => onTransition('accept')} />
        <Button label={t('creation.pass')} accessibilityLabel={`${t('creation.pass')} \u00b7 ${candidate.name}`}
          variant="secondary" busy={task.busy} onPress={() => onTransition('pass')} />
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
          <Button label={t('creation.undo')} trailingIcon="undo" variant="outline" busy={task.busy} disabled={!model.canUndo}
            onPress={() => onTransition('undo')} />
        </View>
        <View style={styles.action}>
          <Button label={t('creation.reset')} trailingIcon="list" variant="outline" busy={task.busy} disabled={model.passedCount === 0}
            onPress={() => onTransition('reset_passed')} />
        </View>
      </View>
    </View>
    <View style={styles.summary} testID="accepted-occurrences">
      <Text variant="sectionTitle" accessibilityRole="header">{t('creation.accepted')}</Text>
      {model.accepted.length === 0 ? <Text tone="textMuted">{t('creation.acceptedEmpty')}</Text> : null}
      {model.accepted.map((workout, index) => <Card key={workout.occurrenceId} elevated style={styles.summary}>
        <Text variant="label" tone="textMuted">{t('creation.choiceNumber', { number: index + 1 })}</Text>
        <SelectionSummary workout={workout} />
      </Card>)}
    </View>
    <Button label={t('creation.continue')} trailingIcon="forward" busy={task.busy} disabled={model.state !== 'placement'} onPress={onContinue} />
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
  return <Screen title={t('creation.placement')} onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    {task.controls}
    <TaskStatus busy={task.busy} error={task.error} />
    <DraftWarnings model={model} />
    <Text>{t('creation.pendingHint')}</Text>
    <Button variant="secondary" label={t('creation.automatic')} accessibilityRole="radio"
      accessibilityState={{ checked: mode === 'automatic' }} busy={task.busy} onPress={() => onMode('automatic')} />
    <Button variant="secondary" label={t('creation.manual')} accessibilityRole="radio"
      accessibilityState={{ checked: mode === 'manual' }} busy={task.busy} onPress={() => onMode('manual')} />
    {mode === 'automatic' ? <>
      <Text>{t('creation.automaticHint')}</Text>
      <AcceptedList accepted={model.accepted} />
    </> : <View style={styles.stack}>
      <Text>{t('creation.manualHint')}</Text>
      {model.accepted.map((workout, index) => <Card key={workout.occurrenceId} style={styles.stack}>
        <Text variant="label">{t('creation.choiceNumber', { number: index + 1 })}</Text>
        <OccurrenceSummary workout={workout} />
        {model.availableDates.map((date) => {
          const label = new Date(`${date}T12:00:00`).toLocaleDateString(locale, {
            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
          });
          return <Button key={date} variant="secondary" label={label}
            accessibilityLabel={`${t('creation.choiceNumber', { number: index + 1 })} · ${workout.name} · ${label}`} accessibilityRole="radio"
            accessibilityState={{ checked: placements.get(workout.occurrenceId) === date }} busy={task.busy}
            onPress={() => onPlace(workout.occurrenceId, date)} />;
        })}
      </Card>)}
    </View>}
    <Button label={t(mode === 'automatic' ? 'creation.submitAutomatic' : 'creation.submitManual')}
      busy={task.busy} disabled={model.state !== 'placement' || (mode === 'manual' && !manualComplete)}
      disabledReason={mode === 'manual' && !manualComplete ? t('creation.incomplete') : undefined}
      onPress={() => onSubmit(mode)} />
    <Button label={t('creation.backSelection')} variant="tertiary" busy={task.busy} onPress={onSelection} />
  </Screen>;
}

const styles = StyleSheet.create({
  stack: { gap: space[12] },
  frame: { flex: 1 }, grow: { flex: 1 },
  form: { gap: space[24] }, summary: { gap: space[16] },
  error: { flexDirection: 'row', alignItems: 'flex-start', gap: space[12], padding: space[16], borderRadius: radius.inset, backgroundColor: colors.destructiveSoft },
  warning: { flexDirection: 'row', alignItems: 'flex-start', gap: space[12], padding: space[16], borderRadius: radius.inset, backgroundColor: colors.warningSoft },
  history: { gap: space[16], marginTop: space[8] },
  countRule: { flexDirection: 'row', alignItems: 'center', gap: space[12] },
  count: { flexShrink: 1 }, rule: { height: layout.decorativeLine, flex: 1, backgroundColor: colors.border },
  actions: { flexDirection: 'row', alignItems: 'stretch', gap: space[12] },
  stackedActions: { flexDirection: 'column' }, action: { flex: 1 },
  skeletonCircle: { width: layout.iconDisc.focus, height: layout.iconDisc.focus, borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  skeletonLine: { height: space[24], borderRadius: radius.inset, backgroundColor: colors.surfaceSubtle },
});
