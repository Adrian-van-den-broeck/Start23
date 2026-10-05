import { StyleSheet, View, useWindowDimensions } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';
import { QuickActionRow } from './QuickActionRow';
import type { WeekAction, WeekAttention } from '../utils/weekHomeViewModel';
export function AttentionRow({ item, disabled, onAction }: { item: WeekAttention; disabled: boolean; onAction: (action: WeekAction) => void; }) {
  const { t } = useLanguage();
  const { fontScale, width } = useWindowDimensions();
  const warning = item.kind === 'warnings';
  const stacked = fontScale >= 1.5 || width < 360;
  return <View testID={`week-attention-${item.kind}`} style={[styles.row, warning && styles.warning,
  stacked && styles.stacked]}>
    <Text variant="supporting" tone={warning ? 'warning' : 'text'} style={[styles.part, stacked && styles.stackedPart]}>{t(`week.attention.${item.kind}`)}</Text>
    <QuickActionRow label={t(warning ? 'week.warningAction' : `week.action.${item.action}`)} disabled={disabled}
      onAction={() => onAction(item.action)} style={[styles.part, stacked && styles.stackedPart]} />
  </View>;
}
const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: space[12] },
  stacked: { flexDirection: 'column', alignItems: 'stretch', gap: space[4] },
  warning: { backgroundColor: colors.warningSoft, borderRadius: radius.inset, paddingHorizontal: space[12], paddingVertical: space[4] },
  part: { flexGrow: 1, flexShrink: 1, flexBasis: 0 },
  stackedPart: { flexGrow: 0, flexShrink: 0, flexBasis: 'auto' },
});
