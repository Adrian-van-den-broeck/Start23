import { studioPresentation } from './presentation';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { useAnimatedStyle, useSharedValue } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import * as Haptics from 'expo-haptics';
import { useLanguage } from '../i18n/LanguageProvider';
import { Text } from '../ui-v2/primitives/Text';
import { palette } from './tokens';

type Props = {
  label: string;
  children: ReactNode;
  dates: readonly string[];
  selected?: string;
  showDate?: boolean;
  disabled: boolean;
  onSelect: (date: string) => void;
};

export function PlacementRail(props: Props) {
  return studioPresentation ? <DraggableDates {...props} /> : <>{props.children}</>;
}

function DraggableDates({ dates, selected, disabled, onSelect, label, children, showDate = true }: Props) {
  const { locale, t } = useLanguage();
  const { fontScale } = useWindowDimensions();
  const [width, setWidth] = useState(0);
  const [handleHeight, setHandleHeight] = useState(48);
  const hovered = useSharedValue(-1);
  // Use two rows when seven full-size day targets do not fit on one line.
  const capacity = Math.max(1, Math.floor(width / 48));
  const columns = Math.ceil(dates.length / Math.max(1, Math.ceil(dates.length / capacity)));
  const cell = columns ? width / columns : 0;
  const rows = columns ? Math.ceil(dates.length / columns) : 0;
  const current = useRef({ dates, selected, disabled, onSelect });
  const mounted = useRef(true);
  useEffect(() => { current.current = { dates, selected, disabled, onSelect }; }, [dates, selected, disabled, onSelect]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const select = useCallback((date: string) => {
    const latest = current.current;
    if (!mounted.current || latest.disabled || !latest.dates.includes(date) || date === latest.selected) return;
    latest.onSelect(date);
    void Haptics.selectionAsync().catch(() => undefined);
  }, []);
  function target(x: number, y: number) {
    'worklet';
    if (!cell || x < 0 || x >= width || y < 0 || y >= rows * 64) return -1;
    const index = Math.floor(y / 64) * columns + Math.floor(x / cell);
    return index < dates.length ? index : -1;
  }
  const pan = Gesture.Pan().enabled(!disabled && cell >= 48).maxPointers(1)
    .activeOffsetX([-12, 12]).failOffsetY([-10, 10])
    .onUpdate(event => { hovered.value = target(event.x, event.y); })
    .onEnd((event, committed) => {
      const index = target(event.x, event.y);
      if (committed && index >= 0) scheduleOnRN(select, dates[index]);
    }).onFinalize(() => { hovered.value = -1; });
  // Only the grip owns vertical drags. A normal vertical swipe on the dates or
  // workout content continues scrolling. The rail begins just below the grip.
  const drag = Gesture.Pan().enabled(!disabled && cell >= 48).maxPointers(1).activateAfterLongPress(180)
    .onUpdate(event => { hovered.value = target(event.x, event.y - handleHeight - 8); })
    .onEnd((event, committed) => {
      const index = target(event.x, event.y - handleHeight - 8);
      if (committed && index >= 0) scheduleOnRN(select, dates[index]);
    }).onFinalize(() => { hovered.value = -1; });
  const cursor = useAnimatedStyle(() => ({
    opacity: hovered.value < 0 ? 0 : 1,
    transform: [{ translateX: (Math.max(0, hovered.value) % Math.max(1, columns)) * cell },
      { translateY: Math.floor(Math.max(0, hovered.value) / Math.max(1, columns)) * 64 }],
  }));
  return <View onLayout={event => setWidth(event.nativeEvent.layout.width)}>
    {cell >= 48 && fontScale <= 1.2 && dates.length > 1 ? <View style={styles.stack}>
      <GestureDetector gesture={drag} touchAction="none">
        <Animated.View collapsable={false} style={styles.grip} onLayout={e => setHandleHeight(e.nativeEvent.layout.height)}>
          <View style={styles.handle} /><Text variant="supporting" tone="primary">{t('creation.dragDate')}</Text>
        </Animated.View>
      </GestureDetector>
      <GestureDetector gesture={pan} touchAction="pan-y"><Animated.View collapsable={false} style={[styles.row, { height: rows * 64 }]}>
        {dates.map(date => {
          const local = new Date(date + 'T12:00:00');
          const active = date === selected;
          return <Pressable key={date} accessibilityRole="button" accessibilityLabel={label + ' \u00b7 ' + local.toLocaleDateString(locale, { dateStyle: 'full' })}
            accessibilityState={{ selected: active, disabled }} disabled={disabled} onPress={() => select(date)} style={[styles.day, { width: cell }, active && styles.active]}>
            <Text variant="caption" tone={active ? 'textInverse' : 'textMuted'}>{local.toLocaleDateString(locale, { weekday: 'short' })}</Text>
            <Text variant="label" tone={active ? 'textInverse' : 'text'}>{local.getDate()}</Text>
          </Pressable>;
        })}
        <Animated.View pointerEvents="none" style={[styles.cursor, { width: cell }, cursor]} />
      </Animated.View></GestureDetector>
      {selected && showDate && <Text variant="supporting" tone="primary">{new Date(selected + 'T12:00:00').toLocaleDateString(locale, { dateStyle: 'full' })}</Text>}
    </View> : <View style={styles.stack}>{children}</View>}
  </View>;
}
const styles = StyleSheet.create({
  grip: { minHeight: 48, padding: 8, borderColor: palette.border, borderWidth: 1, borderRadius: 10, gap: 4, alignItems: 'center', justifyContent: 'center' },
  handle: { height: 3, width: 24, borderRadius: 2, backgroundColor: palette.borderControl },
  stack: { gap: 8 }, row: { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: palette.surfaceSubtle, borderRadius: 10 },
  day: { height: 64, justifyContent: 'center', alignItems: 'center', borderRadius: 10 },
  active: { backgroundColor: palette.primary }, cursor: { position: 'absolute', height: 64, left: 0, top: 0, borderWidth: 3, borderRadius: 10, borderColor: palette.warning },
});
