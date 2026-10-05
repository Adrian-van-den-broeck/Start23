import { useState, type ReactNode } from 'react';
import { View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { SportIndicator } from '../components/SportIndicator';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { colors, space } from '../tokens';
import type { ProposalAlternativesModel, ProposalReviewModel } from '../utils/proposalReviewViewModel';

type TaskProps = { busy: boolean; error: string | null; controls: ReactNode; onBack: () => void };
function Status({ busy, error }: Pick<TaskProps, 'busy' | 'error'>) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('review.busy')}</Text> : null}
    {error ? <Text accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text> : null}
  </>;
}
function Warnings({ warnings }: { warnings: ProposalReviewModel['warnings'] }) {
  return <>{warnings.map((warning, index) => <Card key={warning.id ?? index}>
    <Text variant="label" tone={warning.severity === 'info' ? 'text' : 'warning'} style={warning.severity === 'conflict' ? { color: colors.destructive } : undefined}>{warning.title}</Text>
    <Text>{warning.message}</Text>
  </Card>)}</>;
}

export function ProposalReviewScreen({ model, onEdit, onApprove, onReject, ...task }: TaskProps & {
  model: ProposalReviewModel; onEdit: (id: string) => void; onApprove: () => void; onReject: () => void;
}) {
  const { t, locale } = useLanguage();
  const date = new Date(`${model.weekStart}T12:00:00`).toLocaleDateString(locale, { day: 'numeric', month: 'long', year: 'numeric' });
  return <Screen title={t('review.title')} onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    {task.controls}<Status {...task} />
    <Card>
      <Text variant="sectionTitle">{date}</Text>
      <Text>{t(model.pending ? 'review.pending' : 'review.unavailable')}</Text>
      <Text variant="supporting">{t('review.revision', { revision: model.revision })}</Text>
      {model.activeRevision !== null ? <Text>{t('review.activeSeparate')}</Text> : null}
      {model.explanation ? <Text>{model.explanation}</Text> : null}
    </Card>
    <Warnings warnings={model.warnings} />
    <Text variant="sectionTitle" accessibilityRole="header">{t('review.workouts')}</Text>
    {model.workouts.length === 0 ? <Text>{t('review.empty')}</Text> : null}
    {model.workouts.map((workout, index) => <View key={workout.id} style={{ gap: space[12] }} testID={`proposed-${workout.id}`}>
      <Text variant="label">{t('creation.choiceNumber', { number: index + 1 })}</Text>
      <WorkoutSummary summary={workout.summary} />
      <Warnings warnings={workout.warnings} />
      {model.pending ? <Button label={t('review.edit')} variant="secondary" busy={task.busy}
        accessibilityLabel={`${t('review.edit')} · ${t('creation.choiceNumber', { number: index + 1 })} · ${workout.summary.name}`}
        onPress={() => onEdit(workout.id)} /> : null}
    </View>)}
    <Divider />
    <Text>{t('review.decisionHint')}</Text>
    <Button label={t('review.approve')} busy={task.busy} disabled={!model.pending} onPress={onApprove} />
    <Divider />
    <Button label={t('review.reject')} variant="secondary" busy={task.busy} disabled={!model.pending} onPress={onReject} />
  </Screen>;
}

export function ProposalAlternativesScreen({ model, workout, options, loading, onSelect, selectedId, onReplace, onRemove, onRetry, ...task }: TaskProps & {
  model: ProposalReviewModel; workout: ProposalReviewModel['workouts'][number]; options: ProposalAlternativesModel | null;
  loading: boolean; selectedId: string | null; onSelect: (id: string) => void;
  onReplace: () => void; onRemove: () => void; onRetry: () => void;
}) {
  const { t } = useLanguage();
  const [confirmRemove, setConfirmRemove] = useState(false);
  const blocked = task.busy || loading;
  return <Screen title={t('review.alternatives')} onBack={task.onBack} backLabel={t('review.back')} backDisabled={blocked}>
    {task.controls}<Status busy={blocked} error={task.error} />
    <Text>{t('review.current')}</Text><WorkoutSummary summary={workout.summary} />
    {!model.pending ? <Text>{t('review.unavailable')}</Text> : null}
    {!loading && !options ? <Button label={t('review.retry')} busy={blocked} onPress={onRetry} /> : null}
    {options ? <>
      {options.alternatives.length === 0 ? <Text>{t('review.noAlternatives')}</Text> : null}
      {options.alternatives.map((item, index) => <Card key={item.id} style={{ gap: space[12] }}>
        <SportIndicator discipline={item.discipline} />
        <Text variant="sectionTitle" accessibilityRole="header">{item.name}</Text>
        {item.durationMinutes !== null ? <Text>{t('common.durationMinutes', { minutes: item.durationMinutes })}</Text> : null}
        {item.distanceMeters !== null ? <Text>{t('detail.meters', { value: item.distanceMeters })}</Text> : null}
        <Text>{t(`detail.intensity.${item.intensity}`)}</Text>
        {item.description ? <Text>{item.description}</Text> : null}
        <Button variant="secondary" label={t('review.select')} accessibilityRole="radio"
          accessibilityLabel={`${t('review.select')} · ${index + 1} · ${item.name}`}
          accessibilityState={{ checked: selectedId === item.id }} disabled={!model.pending} busy={blocked}
          onPress={() => { setConfirmRemove(false); onSelect(item.id); }} />
      </Card>)}
      <Button label={t('review.replace')} busy={blocked}
        disabled={!model.pending || !options.alternatives.some((item) => item.id === selectedId)} onPress={onReplace} />
      {options.canRemove && model.pending ? <>
        <Divider />
        <Text>{t('review.removeHint', { name: workout.summary.name })}</Text>
        {confirmRemove ? <>
          <Button label={t('review.confirmRemove')} busy={blocked} onPress={onRemove} />
          <Button label={t('review.keep')} variant="secondary" busy={blocked} onPress={() => setConfirmRemove(false)} />
        </> : <Button label={t('review.remove')} variant="secondary" busy={blocked} onPress={() => setConfirmRemove(true)} />}
      </> : null}
    </> : null}
  </Screen>;
}
