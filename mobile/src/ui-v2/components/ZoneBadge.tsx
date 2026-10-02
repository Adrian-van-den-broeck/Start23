import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';

export function ZoneBadge({ zone }: { zone: number }) {
  const { t } = useLanguage();
  return <Text variant="label">{t('detail.zone', { value: zone })}</Text>;
}
