import * as Haptics from 'expo-haptics';
import { useRef } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { colors, radius, space } from '../tokens';
import { Text } from './Text';

const ROW_HEIGHT = 44;
const VISIBLE_ROWS = 5;
const EDGE_ROWS = Math.floor(VISIBLE_ROWS / 2);

// A snapping number wheel: scrolling settles on the centred row, tapping a row
// jumps to it. It reports the index; the owner keeps the value.
export function WheelColumn({ caption, count, value, spoken, onChange, format = (n) => String(n).padStart(2, '0') }: {
  caption: string; count: number; value: number;
  spoken: (value: number) => string; onChange: (value: number) => void;
  format?: (value: number) => string;
}) {
  const scroller = useRef<ScrollView>(null);
  const current = useRef(value);
  const positioned = useRef(false);

  const settle = (offsetY: number) => {
    const next = Math.max(0, Math.min(count - 1, Math.round(offsetY / ROW_HEIGHT)));
    if (next === current.current) return;
    current.current = next;
    onChange(next);
    void Haptics.selectionAsync().catch(() => undefined);
  };

  return (
    <View style={styles.wheel}>
      <Text variant="caption" tone="textMuted" style={styles.caption}>{caption}</Text>
      <View style={styles.window}>
        <View pointerEvents="none" style={styles.band} />
        <ScrollView
          ref={scroller}
          accessibilityLabel={caption}
          nestedScrollEnabled
          showsVerticalScrollIndicator={false}
          snapToInterval={ROW_HEIGHT}
          decelerationRate="fast"
          scrollEventThrottle={16}
          contentContainerStyle={styles.content}
          onLayout={() => {
            if (positioned.current) return;
            positioned.current = true;
            scroller.current?.scrollTo({ y: value * ROW_HEIGHT, animated: false });
          }}
          onScroll={(event) => settle(event.nativeEvent.contentOffset.y)}
        >
          {Array.from({ length: count }, (_, n) => {
            const distance = Math.abs(n - value);
            return (
              <Pressable
                key={n}
                accessibilityRole="radio"
                accessibilityLabel={spoken(n)}
                accessibilityState={{ checked: n === value }}
                onPress={() => {
                  current.current = n;
                  onChange(n);
                  scroller.current?.scrollTo({ y: n * ROW_HEIGHT, animated: true });
                }}
                style={styles.row}
              >
                <Text
                  variant="numericCompact"
                  accessible={false}
                  numberOfLines={1}
                  tone={distance === 0 ? 'primary' : 'text'}
                  style={{ opacity: distance === 0 ? 1 : distance === 1 ? 0.55 : 0.28 }}
                >
                  {format(n)}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wheel: { flex: 1, gap: space[4] },
  caption: { textAlign: 'center' },
  window: { height: ROW_HEIGHT * VISIBLE_ROWS, overflow: 'hidden' },
  content: { paddingVertical: ROW_HEIGHT * EDGE_ROWS },
  band: {
    position: 'absolute', left: 0, right: 0, top: ROW_HEIGHT * EDGE_ROWS, height: ROW_HEIGHT,
    backgroundColor: colors.primarySoft, borderRadius: radius.control,
  },
  row: { height: ROW_HEIGHT, alignItems: 'center', justifyContent: 'center', paddingHorizontal: space[4] },
});
