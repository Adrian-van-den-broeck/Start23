import { useState } from 'react';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
import { Icon, type IconName } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, shadows, space } from '../tokens';

export type RootDestination = { key: string; label: string; icon: Extract<IconName, 'week' | 'calendar' | 'activities'> };
export function NavigationFooter({ bottomInset, children }: { bottomInset: number; children: React.ReactNode }) {
  return <View style={[styles.footer, { paddingBottom: bottomInset + layout.bottomNav.bottomGap }]}>{children}</View>;
}
export function BottomNavigation({ destinations, selectedKey, onSelect, onHeight }: {
  destinations: readonly RootDestination[]; selectedKey: string; onSelect: (key: string) => void; onHeight?: (height: number) => void;
}) {
  const { width, fontScale } = useWindowDimensions();
  const [barWidth, setBarWidth] = useState(0);
  const [measurements, setMeasurements] = useState<Record<string, { label: string; fontScale: number; width: number }>>({});
  const [focused, setFocused] = useState<string | null>(null);
  const available = (barWidth - layout.bottomNav.inset * 2) / destinations.length;
  const stacked = width <= 360 || fontScale >= 1.5 || destinations.some((destination) => {
    const measured = measurements[destination.key];
    return !measured || measured.label !== destination.label || measured.fontScale !== fontScale ||
      measured.width + 24 + layout.navigationIconGap + space[8] * 2 > available;
  });
  return <View testID="training-root-navigation" accessibilityRole="tablist" style={styles.bar}
    onLayout={(event) => { setBarWidth(event.nativeEvent.layout.width); onHeight?.(event.nativeEvent.layout.height); }}>
    <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.measure}>
      {destinations.map((destination) => <Text key={`${destination.key}-${destination.label}-${fontScale}`} variant="navigationLabel" testID={`navigation-measure-${destination.key}`}
        onTextLayout={(event) => {
          const measuredWidth = event.nativeEvent.lines.reduce((total, line) => total + line.width, 0);
          setMeasurements((previous) => previous[destination.key]?.width === measuredWidth && previous[destination.key]?.label === destination.label && previous[destination.key]?.fontScale === fontScale
            ? previous : { ...previous, [destination.key]: { label: destination.label, fontScale, width: measuredWidth } });
        }}>{destination.label}</Text>)}
    </View>
    {destinations.map((destination) => {
      const selected = destination.key === selectedKey;
      return <Pressable key={destination.key} accessibilityRole="tab" accessibilityLabel={destination.label}
        accessibilityState={{ selected }} onPress={() => onSelect(destination.key)}
        onFocus={() => setFocused(destination.key)} onBlur={() => setFocused(null)}
        style={[styles.destination, stacked ? styles.stacked : styles.horizontal, selected && styles.selected]}>
        <Icon name={destination.icon} color={selected ? colors.textInverse : colors.textMuted} />
        <Text variant="navigationLabel" accessible={false} style={[styles.label, selected && styles.selectedLabel]}>{destination.label}</Text>
        {focused === destination.key ? <View pointerEvents="none" style={[styles.focus, { borderColor: selected ? colors.textInverse : colors.focus }]} /> : null}
      </Pressable>;
    })}
  </View>;
}
const styles = StyleSheet.create({
  footer: { backgroundColor: colors.background, paddingTop: space[8], paddingHorizontal: layout.bottomNav.horizontalMargin },
  bar: { flexDirection: 'row', minHeight: layout.bottomNav.minHeight, padding: layout.bottomNav.inset,
    borderRadius: radius.pill, backgroundColor: colors.surface, ...shadows.floatingNav },
  destination: { flex: 1, minHeight: layout.bottomNav.destinationHeight, minWidth: layout.touch,
    paddingHorizontal: space[8], paddingVertical: space[8], borderRadius: radius.pill, justifyContent: 'center', alignItems: 'center' },
  horizontal: { flexDirection: 'row', gap: layout.navigationIconGap }, stacked: { gap: layout.bottomNav.stackedIconGap, justifyContent: 'flex-start' },
  selected: { backgroundColor: colors.primary }, label: { color: colors.textMuted, textAlign: 'center', flexShrink: 1 },
  selectedLabel: { color: colors.textInverse },
  focus: { ...StyleSheet.absoluteFill, margin: layout.focusOutline, borderRadius: radius.pill, borderWidth: layout.focusOutline },
  measure: { position: 'absolute', opacity: 0, alignItems: 'flex-start' },
});
