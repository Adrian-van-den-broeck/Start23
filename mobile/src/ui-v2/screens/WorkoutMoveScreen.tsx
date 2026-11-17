import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { addDays, isoDate } from '../../features/planning/planningDates';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Notice } from '../primitives/Notice';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { space } from '../tokens';
import type { WorkoutSummaryViewModel } from '../utils/workoutSummaryViewModel';

export type MoveWarning = { title: string; message: string };
export function WorkoutMoveScreen({ summary, currentDate, weekStart, targetDate, warnings, busy, error, available,
  onReview, onConfirm, onCancel, controls }: {
    summary: WorkoutSummaryViewModel; currentDate: string; weekStart: string; targetDate: string | null;
    warnings: readonly MoveWarning[] | null; busy: boolean; error: string | null; available: boolean;
    onReview: (date: string) => void; onConfirm: () => void; onCancel: () => void; controls: ReactNode;
  }) {
  const { locale, t } = useLanguage();
  const [selectedDate, setSelectedDate] = useState(currentDate);
  const fullDate = (date: string) => parseCalendarDate(date).toLocaleDateString(locale, {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
  return <Screen title={t(warnings ? 'move.warning' : 'move.title')} landscape="ridges" titleVariant="display"
    onBack={onCancel} backLabel={t('move.cancel')} backDisabled={busy}>
    {busy ? <Text tone="textMuted" accessibilityState={{ busy: true }} accessibilityLiveRegion="polite">{t('move.busy')}</Text> : null}
    {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error} accessibilityLiveRegion="polite">
      <Notice tone="error" title={t('move.title')}>{error}</Notice>
    </View> : null}
    {!available ? <View accessible accessibilityRole="alert" accessibilityLabel={t('move.unavailable')}>
      <Notice title={t('move.title')}>{t('move.unavailable')}</Notice>
    </View> : null}
    <WorkoutSummary summary={summary} dateLabel={t('move.currentDate', { date: fullDate(currentDate) })}
      footer={targetDate ? <View style={styles.actions}><Divider /><Text tone="primary">{t('move.targetDate', { date: fullDate(targetDate) })}</Text></View> : undefined} />
    {warnings ? <>
      {warnings.map((warning, index) => <Notice key={index} tone="warning" title={warning.title}>{warning.message}</Notice>)}
    </> : <>
      <Card elevated padding="form" style={styles.dates}>
        <Text variant="sectionTitle" accessibilityRole="header">{t('move.newDate')}</Text>
        {Array.from({ length: 7 }, (_, index) => isoDate(addDays(weekStart, index))).map(date =>
        <ChoiceRow key={date} selected={selectedDate === date}
          label={`${fullDate(date)}${date === currentDate ? ` · ${t('move.current')}` : ''}`}
          disabled={busy || !available} onPress={() => setSelectedDate(date)} />)}
        <Divider />
        <Text tone="textMuted">{t('move.targetDate', { date: fullDate(selectedDate) })}</Text>
      </Card>
    </>}
    <Card elevated padding="form" style={styles.actions}>
      {warnings ? <Button label={t('move.confirm')} trailingIcon="forward" busy={busy} disabled={!available} onPress={onConfirm} />
        : <Button label={t('move.review')} trailingIcon="forward" busy={busy} disabled={!available || selectedDate === currentDate} onPress={() => onReview(selectedDate)} />}
      <Divider />
      <Button label={t('move.cancel')} variant="secondary" busy={busy} onPress={onCancel} />
    </Card>
    {controls}
  </Screen>;
}
const styles = StyleSheet.create({ dates: { gap: space[12] }, actions: { gap: space[16] } });
