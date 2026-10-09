import type { ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { HeaderAction } from './AppHeader';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { layout, space } from '../tokens';

export function BrandedFormHeader({ caption, onBack, onSignOut, children, backLabel = 'Week' }: {
  caption: string; backLabel?: string; onBack?: () => void; onSignOut: () => Promise<void>; children?: ReactNode;
}) {
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 393 || fontScale > 1 || backLabel.length > 8;
  const brand = <View style={styles.brand}><Text variant="screenTitle" tone="primary">WOMBO</Text><Text tone="textMuted">{caption}</Text></View>;
  return <View style={{ gap: space[8] }}>
    {stacked ? brand : null}
    <View style={styles.utility}>
      {stacked ? (onBack ? <HeaderAction label={backLabel} onPress={onBack} /> : null) : <View style={styles.column}>{onBack ? <HeaderAction label={backLabel} onPress={onBack} /> : null}</View>}
      {!stacked ? <View style={styles.column}>{brand}</View> : null}
      <View style={[styles.actions, !stacked && styles.column, styles.trailing]}>{children}<Button label="Uit" accessibilityLabel="Afmelden" onPress={onSignOut} variant="secondary" trailingIcon="logout" /></View>
    </View>
    <View pointerEvents="none" style={styles.art}><HeaderLandscape /></View>
  </View>;
}

export function FormComposition({ title, description, children, progress }: {
  title: string; description: string; children: ReactNode; progress?: ReactNode;
}) {
  return <View style={{ gap: space[24] }}>
    {progress}
    <View style={{ gap: space[8] }}><Text variant="display" accessibilityRole="header">{title}</Text><Text tone="textMuted">{description}</Text></View>
    <Card padding="form" elevated style={{ gap: layout.fieldGroupGap }}>{children}</Card>
  </View>;
}
const styles = StyleSheet.create({
  utility: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: space[8] },
  column: { flex: 1, minWidth: 0 },
  trailing: { justifyContent: 'flex-end' },
  brand: { alignItems: 'center', flexShrink: 1 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8], flexShrink: 1 },
  art: { marginHorizontal: -layout.phoneGutter, marginBottom: -space[48] },
});
