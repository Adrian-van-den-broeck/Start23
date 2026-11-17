import { useId, type ReactNode } from 'react';
import { View } from 'react-native';
import { colors, layout, space } from '../tokens';
import { Icon } from './Icon';
import { Text } from './Text';

export type FieldDetails = {
  label: string; hint?: string; error?: string; optionalLabel?: string;
  disabledReason?: string;
};

export function FormField({ label, hint, error, optionalLabel, disabledReason, children }: FieldDetails & {
  children: (labelId: string) => ReactNode;
}) {
  const id = useId();
  return <View style={{ gap: layout.labelFieldGap }}>
    <Text nativeID={id} variant="label">{label}{optionalLabel ? <Text tone="textMuted"> {optionalLabel}</Text> : null}</Text>
    {children(id)}
    {hint || error || disabledReason ? <View style={{ gap: layout.fieldHelpGap, marginTop: -space[4] }}>
      {hint ? <Text variant="supporting" tone="textMuted">{hint}</Text> : null}
      {error ? <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: space[8] }}>
        <Icon name="warning" size={20} color={colors.destructive} />
        <Text variant="supporting" tone="destructive" accessibilityRole="alert" accessibilityLiveRegion="polite" style={{ flex: 1 }}>{error}</Text>
      </View> : null}
      {disabledReason ? <Text variant="supporting" tone="textMuted">{disabledReason}</Text> : null}
    </View> : null}
  </View>;
}
