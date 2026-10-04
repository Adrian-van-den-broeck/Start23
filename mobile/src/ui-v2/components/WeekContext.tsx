import { View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import type { WeekHomeViewModel } from '../utils/weekHomeViewModel';
export function WeekContext({ model }: { model: WeekHomeViewModel; }) {
  const { t, locale } = useLanguage();
  const format = (date: string) => new Date(date + 'T12:00:00').toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' });
  return <View><Text variant="sectionTitle" accessibilityRole="header">{format(model.weekStart)} – {format(model.weekEnd)}</Text>
    <Text variant="supporting">{t(`week.state.${model.state}`)}</Text></View>;
}
