import { View } from 'react-native';
import { colors, layout, radius } from '../tokens';
import { Icon, type IconName } from './Icon';

export function IconTile({ name, size = 'row', tone = 'primary' }: {
  name: IconName; size?: keyof typeof layout.iconDisc;
  tone?: 'primary' | keyof typeof colors.sport;
}) {
  const diameter = layout.iconDisc[size];
  const palette = tone === 'primary' ? { text: colors.primary, soft: colors.primarySoft } : colors.sport[tone];
  return <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
    pointerEvents="none" style={{ width: diameter, height: diameter, flexShrink: 0, borderRadius: radius.pill,
      backgroundColor: palette.soft, alignItems: 'center', justifyContent: 'center' }}>
    <Icon name={name} size={size === 'focus' ? 32 : size === 'row' ? 24 : 20} color={palette.text} />
  </View>;
}
