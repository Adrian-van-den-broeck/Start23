import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import type { RpeRange } from '../utils/workoutDetailViewModel';

export function RpeIndicator({ range, kind = 'expected' }: {
  range: RpeRange; kind?: 'expected' | 'rpe' | 'protocol';
}) {
  const { t } = useLanguage();
  const value = range.min === range.max ? String(range.min) : `${range.min}–${range.max}`;
  return <Text variant="supporting">{t(`detail.${kind}Rpe`, { value })}</Text>;
}
