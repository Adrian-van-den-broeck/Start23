import { View } from 'react-native';
import { colors, radius, space } from '../tokens';
import { Button } from './Button';
import { Icon, type IconName } from './Icon';
import { Text } from './Text';

const tones = {
  info: { fill: colors.primarySoft, ink: colors.primary, icon: 'info' },
  warning: { fill: colors.warningSoft, ink: colors.warning, icon: 'warning' },
  error: { fill: colors.destructiveSoft, ink: colors.destructive, icon: 'close' },
  success: { fill: colors.successSoft, ink: colors.success, icon: 'check' },
} satisfies Record<string, { fill: string; ink: string; icon: IconName }>;

export function Notice({ tone = 'info', title, children, action }: {
  tone?: keyof typeof tones; title: string; children: string;
  action?: { label: string; onPress: () => void | Promise<void>; busy?: boolean; disabled?: boolean };
}) {
  const palette = tones[tone];
  return <View style={{ backgroundColor: palette.fill, borderRadius: radius.inset, padding: space[16], gap: space[12] }}>
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: space[12] }}>
      <Icon name={palette.icon} color={palette.ink} />
      <View style={{ flex: 1, gap: space[4] }}>
        <Text variant="label" style={{ color: palette.ink }}>{title}</Text>
        <Text style={{ color: palette.ink }}>{children}</Text>
      </View>
    </View>
    {action ? <Button {...action} variant="outline" /> : null}
  </View>;
}
