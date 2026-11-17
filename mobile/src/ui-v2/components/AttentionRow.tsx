import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { Icon } from '../primitives/Icon';
import { colors, radius, space } from '../tokens';
import { QuickActionRow } from './QuickActionRow';
import type { WeekAction, WeekAttention } from '../utils/weekHomeViewModel';
export function AttentionRow({ item, disabled, onAction }: { item: WeekAttention; disabled: boolean; onAction: (action: WeekAction) => void; }) {
  const { t } = useLanguage();
  const warning = item.kind === 'warnings';
  return <View testID={`week-attention-${item.kind}`} style={[styles.row, warning && styles.warning]}>
    <View style={styles.fact}><Icon name={warning ? 'warning' : item.kind === 'proposal' ? 'document' : 'list'} color={warning ? colors.warning : colors.primary} />
      <Text variant="label" tone={warning ? 'warning' : 'primary'} style={styles.copy}>{t(`week.attention.${item.kind}`)}</Text>
    </View>
    <QuickActionRow label={t(warning ? 'week.warningAction' : `week.action.${item.action}`)} disabled={disabled}
      onAction={() => onAction(item.action)} />
  </View>;
}
const styles = StyleSheet.create({
  row: { flexDirection: 'column', gap: space[4], backgroundColor: colors.primarySoft, borderRadius: radius.card, padding: space[16] },
  warning: { backgroundColor: colors.warningSoft },
  fact: { flexDirection: 'row', alignItems: 'flex-start', gap: space[12] }, copy: { flex: 1 },
});
