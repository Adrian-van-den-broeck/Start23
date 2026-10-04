import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { WeekAction, WeekAttention } from '../utils/weekHomeViewModel';
export function AttentionRow({ item, disabled, onAction }: { item: WeekAttention; disabled: boolean; onAction: (action: WeekAction) => void; }) {
  const { t } = useLanguage();
  return <View style={styles.row}><Text variant="body">{t(`week.attention.${item.kind}`)}</Text>
    <Button variant="tertiary" label={t(item.kind === 'warnings' ? 'week.warningAction' : `week.action.${item.action}`)} disabled={disabled} onPress={() => onAction(item.action)} /></View>;
}
const styles = StyleSheet.create({ row: { gap: space[4] } });
