import { useState, type ReactNode } from 'react';
import { useLanguage } from '../../i18n/LanguageProvider';
import { addDays, isoDate } from '../../features/planning/planningDates';
import { parseCalendarDate } from '../../features/calendar/calendarDates';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';

export type MoveWarning = { title: string; message: string };
export function WorkoutMoveScreen({ name, currentDate, weekStart, targetDate, warnings, busy, error, available,
  onReview, onConfirm, onCancel, controls }: {
    name: string; currentDate: string; weekStart: string; targetDate: string | null;
    warnings: readonly MoveWarning[] | null; busy: boolean; error: string | null; available: boolean;
    onReview: (date: string) => void; onConfirm: () => void; onCancel: () => void; controls: ReactNode;
  }) {
  const { locale, t } = useLanguage();
  const [selectedDate, setSelectedDate] = useState(currentDate);
  const fullDate = (date: string) => parseCalendarDate(date).toLocaleDateString(locale, {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
  return <Screen title={t(warnings ? 'move.warning' : 'move.title')} onBack={onCancel} backLabel={t('move.cancel')} backDisabled={busy}>
    {controls}
    <Card>
      <Text variant="cardTitle">{name}</Text>
      <Text>{t('move.currentDate', { date: fullDate(currentDate) })}</Text>
      {targetDate ? <Text>{t('move.targetDate', { date: fullDate(targetDate) })}</Text> : null}
    </Card>
    {busy ? <Text accessibilityState={{ busy: true }} accessibilityLiveRegion="polite">{t('move.busy')}</Text> : null}
    {error ? <Text accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text> : null}
    {!available ? <Text accessibilityRole="alert">{t('move.unavailable')}</Text> : null}
    {warnings ? <>
      {warnings.map((warning, index) => <Card key={index}>
        <Text variant="label" accessibilityRole="header">{warning.title}</Text>
        <Text>{warning.message}</Text>
      </Card>)}
      <Button label={t('move.confirm')} busy={busy} disabled={!available} onPress={onConfirm} />
    </> : <>
      <Text variant="sectionTitle" accessibilityRole="header">{t('move.newDate')}</Text>
      {Array.from({ length: 7 }, (_, index) => isoDate(addDays(weekStart, index))).map(date =>
        <Button key={date} accessibilityRole="radio" accessibilityState={{ checked: selectedDate === date }}
          label={`${fullDate(date)}${date === currentDate ? ` · ${t('move.current')}` : ''}`}
          disabled={busy || !available} variant="secondary" onPress={() => setSelectedDate(date)} />)}
      <Text>{t('move.targetDate', { date: fullDate(selectedDate) })}</Text>
      <Button label={t('move.review')} busy={busy} disabled={!available || selectedDate === currentDate} onPress={() => onReview(selectedDate)} />
    </>}
    <Divider />
    <Button label={t('move.cancel')} variant="secondary" busy={busy} onPress={onCancel} />
  </Screen>;
}
