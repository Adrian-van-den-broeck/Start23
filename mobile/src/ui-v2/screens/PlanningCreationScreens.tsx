import type { ReactNode } from 'react';
import { StyleSheet, TextInput, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { addDays } from '../../features/planning/planningDates';
import { useLanguage } from '../../i18n/LanguageProvider';
import { formatIsoDateInput, isValidIsoDateInput } from '../../lib/dateInput';
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
  return <Screen title={t('creation.availability')} onBack={props.onBack} backLabel={t('week.return')} backDisabled={props.busy}>
    {props.controls}
    <TaskStatus busy={props.busy} error={props.error} />
    <Text>{t('creation.availabilityHint')}</Text>
    <View style={styles.stack}>
      <Text variant="label">{t('creation.weekStart')}</Text>
      <TextInput accessibilityLabel={t('creation.weekStart')} value={props.weekStart}
        onChangeText={(value) => props.onWeekStart(formatIsoDateInput(value))} editable={!props.busy}
        accessibilityState={{ disabled: props.busy }} inputMode="numeric" autoCapitalize="none"
        maxLength={10} placeholder="YYYY-MM-DD" style={styles.input} />
    </View>
    <View style={styles.stack}>
      {Array.from({ length: 7 }, (_, offset) => {
        // Weekday labels remain available while the date input is incomplete.
        const weekday = new Date(2026, 7, 3 + offset, 12).toLocaleDateString(locale, { weekday: 'long' });
        const date = validDate ? addDays(props.weekStart, offset).toLocaleDateString(locale, { day: 'numeric', month: 'long' }) : '';
        return <Button key={offset} variant="secondary" label={`${weekday}${date ? ` · ${date}` : ''}`}
          accessibilityRole="checkbox" accessibilityState={{ checked: props.selectedDays.has(offset) }}
          busy={props.busy} onPress={() => props.onToggleDay(offset)} />;
      })}
      <Button label={t('creation.reuse')} variant="secondary" accessibilityRole="checkbox"
        accessibilityState={{ checked: props.reusePreviousWeek }} busy={props.busy} onPress={props.onReuse} />
      <Text variant="supporting">{t('creation.reuseHint')}</Text>
    </View>
    <Divider />
    <Text variant="sectionTitle" accessibilityRole="header">{t('creation.injuries')}</Text>
    <View style={styles.stack}>
      {(['swim', 'bike', 'run'] as const).map((sport) => <Button key={sport} variant="secondary"
        label={t(`common.${sport}`)} accessibilityLabel={`${t('creation.injuries')} · ${t(`common.${sport}`)}`}
        accessibilityRole="checkbox" accessibilityState={{ checked: props.injuries.has(sport) }}
        busy={props.busy} onPress={() => props.onInjury(sport)} />)}
    </View>
    {props.injuries.size > 0 ? <>
      <Text variant="sectionTitle" accessibilityRole="header">{t('creation.crossTraining')}</Text>
      <Text variant="supporting">{t('creation.crossTrainingHint')}</Text>
      <View style={styles.stack}>
        {(['bike', 'swim'] as const).filter((sport) => !props.injuries.has(sport)).map((sport) =>
          <Button key={sport} variant="secondary" label={t(`common.${sport}`)}
            accessibilityLabel={`${t('creation.crossTraining')} · ${t(`common.${sport}`)}`}
            accessibilityRole="checkbox" accessibilityState={{ checked: props.crossTrainingOptIns.has(sport) }}
            busy={props.busy} onPress={() => props.onCrossTraining(sport)} />)}
      </View>
    </> : null}
    <Button label={t('creation.create')} busy={props.busy}
      disabled={!props.reusePreviousWeek && props.selectedDays.size === 0}
      disabledReason={!props.reusePreviousWeek && props.selectedDays.size === 0 ? t('creation.emptyDates') : undefined}
      onPress={props.onCreate} />
  </Screen>;
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

export function SelectionScreen({ model, onTransition, onContinue, ...task }: TaskProps & {
  model: PlanningCreationModel; onTransition: (action: 'accept' | 'pass' | 'undo' | 'reset_passed') => void;
  onContinue: () => void;
}) {
  const { t } = useLanguage();
  const candidate = model.state === 'collecting' ? model.candidate : null;
  return <Screen title={t('creation.selection')} onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    {task.controls}
    <TaskStatus busy={task.busy} error={task.error} />
    <DraftWarnings model={model} />
    {candidate ? <Card style={styles.stack}>
      <OccurrenceSummary key={candidate.occurrenceId} workout={candidate} />
      <Button label={t('creation.choose')} accessibilityLabel={`${t('creation.choose')} · ${candidate.name}`}
        busy={task.busy} onPress={() => onTransition('accept')} />
      <Button label={t('creation.pass')} accessibilityLabel={`${t('creation.pass')} · ${candidate.name}`}
        variant="secondary" busy={task.busy} onPress={() => onTransition('pass')} />
    </Card> : model.state === 'collecting' ? <Text>{t(model.exhausted ? 'creation.exhausted' : 'creation.unavailable')}</Text> : null}
    <Text variant="supporting">{t('creation.passed', { count: model.passedCount })}</Text>
    <Button label={t('creation.undo')} variant="secondary" busy={task.busy} disabled={!model.canUndo}
      onPress={() => onTransition('undo')} />
    <Button label={t('creation.reset')} variant="secondary" busy={task.busy} disabled={model.passedCount === 0}
      onPress={() => onTransition('reset_passed')} />
    <AcceptedList accepted={model.accepted} />
    <Button label={t('creation.continue')} busy={task.busy} disabled={model.state !== 'placement'} onPress={onContinue} />
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
  input: {
    minHeight: layout.primaryButton, padding: space[12], borderWidth: 1,
    borderColor: colors.textMuted, borderRadius: radius.control, color: colors.text,
    backgroundColor: colors.surface, fontSize: 18,
  },
});
