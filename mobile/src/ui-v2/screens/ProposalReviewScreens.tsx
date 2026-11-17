import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { SportIndicator } from '../components/SportIndicator';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { WorkoutFacts } from '../components/WorkoutFacts';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Notice } from '../primitives/Notice';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { ProposalAlternativesModel, ProposalReviewModel } from '../utils/proposalReviewViewModel';

type TaskProps = { busy: boolean; error: string | null; controls: ReactNode; onBack: () => void };
function Status({ busy, error }: Pick<TaskProps, 'busy' | 'error'>) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text tone="textMuted" accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('review.busy')}</Text> : null}
    {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error} accessibilityLiveRegion="polite">
      <Notice tone="error" title={t('review.title')}>{error}</Notice>
    </View> : null}
  </>;
}
function Warnings({ warnings }: { warnings: ProposalReviewModel['warnings'] }) {
  return <>{warnings.map((warning, index) => <Notice key={warning.id ?? index}
    tone={warning.severity === 'info' ? 'info' : warning.severity === 'conflict' ? 'error' : 'warning'} title={warning.title}>
    {warning.message}
  </Notice>)}</>;
}

export function ProposalReviewScreen({ model, onEdit, onApprove, onReject, ...task }: TaskProps & {
  model: ProposalReviewModel; onEdit: (id: string) => void; onApprove: () => void; onReject: () => void;
}) {
  const { t, locale } = useLanguage();
  const date = new Date(`${model.weekStart}T12:00:00`).toLocaleDateString(locale, { day: 'numeric', month: 'long', year: 'numeric' });
  return <Screen title={t('review.title')} landscape="ridges" titleVariant="display"
    onBack={task.onBack} backLabel={t('week.return')} backDisabled={task.busy}>
    <Status {...task} />
    <Card padding="focus" elevated style={styles.overview}>
      <Text variant="label" tone="primary">{t('review.revision', { revision: model.revision })}</Text>
      <Text variant="cardTitle" accessibilityRole="header">{date}</Text>
      <Text>{t(model.pending ? 'review.pending' : 'review.unavailable')}</Text>
      {model.explanation ? <><Divider /><Text tone="textMuted">{model.explanation}</Text></> : null}
    </Card>
    {model.activeRevision !== null ? <Notice title={t('common.active')}>{t('review.activeSeparate')}</Notice> : null}
    <Warnings warnings={model.warnings} />
    <Text variant="sectionTitle" accessibilityRole="header">{t('review.workouts')}</Text>
    {model.workouts.length === 0 ? <Text tone="textMuted">{t('review.empty')}</Text> : null}
    {model.workouts.map((workout, index) => <View key={workout.id} testID={`proposed-${workout.id}`}>
      <WorkoutSummary summary={workout.summary}
        context={<Text variant="label" tone="textMuted">{t('creation.choiceNumber', { number: index + 1 })}</Text>}
        footer={<View style={styles.stack}>
          <Warnings warnings={workout.warnings} />
          {model.pending ? <Button label={t('review.edit')} trailingIcon="forward" variant="secondary" busy={task.busy}
            accessibilityLabel={`${t('review.edit')} · ${t('creation.choiceNumber', { number: index + 1 })} · ${workout.summary.name}`}
            onPress={() => onEdit(workout.id)} /> : null}
        </View>} />
    </View>)}
    <Card padding="form" elevated style={styles.stack}>
      <Text tone="textMuted">{t('review.decisionHint')}</Text>
      <Button label={t('review.approve')} trailingIcon="check" busy={task.busy} disabled={!model.pending} onPress={onApprove} />
      <Divider />
      <Button label={t('review.reject')} variant="secondary" busy={task.busy} disabled={!model.pending} onPress={onReject} />
    </Card>
    {task.controls}
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
  return <Screen title={t('review.alternatives')} landscape="ridges" titleVariant="display"
    onBack={task.onBack} backLabel={t('review.back')} backDisabled={blocked}>
    <Status busy={blocked} error={task.error} />
    <Text variant="sectionTitle" accessibilityRole="header">{t('review.current')}</Text>
    <WorkoutSummary summary={workout.summary} />
    {!model.pending ? <Notice title={t('review.title')}>{t('review.unavailable')}</Notice> : null}
    {!loading && !options ? <Button label={t('review.retry')} busy={blocked} onPress={onRetry} /> : null}
    {options ? <>
      {options.alternatives.length === 0 ? <Notice title={t('review.alternatives')}>{t('review.noAlternatives')}</Notice> : null}
      {options.alternatives.map((item, index) => <Card key={item.id} elevated padding="focus" style={styles.overview}>
        <SportIndicator discipline={item.discipline} size="focus" tone="primary">
          <Text variant="cardTitle" accessibilityRole="header">{item.name}</Text>
        </SportIndicator>
        <WorkoutFacts variant="focus" measures={{ durationMinutes: item.durationMinutes, distanceMeters: item.distanceMeters }} intensity={item.intensity} />
        {item.description ? <Text tone="textMuted">{item.description}</Text> : null}
        <ChoiceRow label={t('review.select')}
          accessibilityLabel={`${t('review.select')} · ${index + 1} · ${item.name}`}
          selected={selectedId === item.id} disabled={!model.pending || blocked}
          onPress={() => { setConfirmRemove(false); onSelect(item.id); }} />
      </Card>)}
      <Button label={t('review.replace')} trailingIcon="forward" busy={blocked}
        disabled={!model.pending || !options.alternatives.some((item) => item.id === selectedId)} onPress={onReplace} />
      {options.canRemove && model.pending ? <Card elevated style={styles.stack}>
        <Notice tone={confirmRemove ? 'error' : 'warning'} title={t('review.remove')}>
          {t('review.removeHint', { name: workout.summary.name })}
        </Notice>
        {confirmRemove ? <>
          <Button label={t('review.confirmRemove')} variant="destructive" busy={blocked} onPress={onRemove} />
          <Button label={t('review.keep')} variant="secondary" busy={blocked} onPress={() => setConfirmRemove(false)} />
        </> : <Button label={t('review.remove')} variant="secondary" busy={blocked} onPress={() => setConfirmRemove(true)} />}
      </Card> : null}
    </> : null}
    {task.controls}
  </Screen>;
}

const styles = StyleSheet.create({
  overview: { gap: space[16] }, stack: { gap: space[12] },
});
