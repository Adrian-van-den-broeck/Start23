import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { WeekHomeViewModel } from '../utils/weekHomeViewModel';
export function WeekContext({ model, showStatus = true }: { model: WeekHomeViewModel; showStatus?: boolean; }) {
  const { t, locale } = useLanguage();
  const start = new Date(model.weekStart + 'T12:00:00');
  const end = new Date(model.weekEnd + 'T12:00:00');
  const sameYear = start.getFullYear() === end.getFullYear();
  const sameMonth = sameYear && start.getMonth() === end.getMonth();
  const first = start.toLocaleDateString(locale, { day: 'numeric', ...(sameMonth ? {} : { month: 'short' }), ...(sameYear ? {} : { year: 'numeric' }) });
  const last = end.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' });
  const range = `${first}${sameMonth ? '–' : ' – '}${last}`;
  const full = (date: Date) => date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  return <View style={styles.context}>
    <Text testID="week-range" variant="supporting" tone="textMuted" accessibilityLabel={`${full(start)} – ${full(end)}`}>
      {range}
    </Text>
    {showStatus ? <Text variant="label">{t(`week.state.${model.state}`)}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({ context: { gap: space[4] } });
