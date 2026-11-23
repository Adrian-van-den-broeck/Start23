import { studioPresentation } from './presentation';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { useAnimatedStyle, useSharedValue, withTiming, withSequence, type SharedValue } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import * as Haptics from 'expo-haptics';
import { useLanguage } from '../i18n/LanguageProvider';
import { Text } from '../ui-v2/primitives/Text';
import { useMotionPolicy } from '../ui-v2/motion/useMotionPolicy';
import { Icon } from '../ui-v2/primitives/Icon';
import { palette } from './tokens';

type Props = {
  label: string;
  workout?: ReactNode;
  children: ReactNode;
  dates: readonly string[];
  selected?: string;
  showDate?: boolean;
  disabled: boolean;
  onSelect: (date: string) => void;
};

export function PlacementRail(props: Props) {
  return studioPresentation ? <DraggableDates {...props} /> : <>{props.workout}{props.children}</>;
}

function DraggableDates({ dates, selected, disabled, onSelect, label, children, workout, showDate = true }: Props) {
  const { locale, t } = useLanguage();
  const { fontScale } = useWindowDimensions();
  const [width, setWidth] = useState(0);
  const { reducedMotion } = useMotionPolicy();
  const [handleHeight, setHandleHeight] = useState(48);
  const lift = useSharedValue(0);
  const follow = useSharedValue(0);
  const pulse = useSharedValue(0);
  const requested = useRef<string | null>(null);
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
    requested.current = date;
    latest.onSelect(date);
  }, []);
  // A date is confirmed by the owning screen. Releasing the grip alone cannot
  // confirm a rejected save or a move still waiting for athlete review.
  useEffect(() => {
    if (!selected || selected !== requested.current) return;
    requested.current = null;
    if (!reducedMotion) {
      pulse.value = withSequence(withTiming(1, { duration: 110 }), withTiming(0, { duration: 240 }));
    }
    void Haptics.selectionAsync().catch(() => undefined);
  }, [selected, reducedMotion, pulse]);
  function target(x: number, y: number) {
    'worklet';
    if (!cell || x < 0 || x >= width || y < 0 || y >= rows * 64) return -1;
    const index = Math.floor(y / 64) * columns + Math.floor(x / cell);
    return index < dates.length && dates[index] !== selected ? index : -1;
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
  const drag = Gesture.Pan().withTestId('placement-grip').enabled(!disabled && cell >= 48).maxPointers(1).activateAfterLongPress(180)
    .onStart(() => { lift.value = reducedMotion ? 1 : withTiming(1, { duration: 130 }); })
    .onUpdate(event => {
      hovered.value = target(event.x, event.y - handleHeight - 8);
      if (!reducedMotion) follow.value = Math.max(-20, Math.min(20, event.translationX * 0.23));
    })
    .onEnd((event, committed) => {
      const index = target(event.x, event.y - handleHeight - 8);
      if (committed && index >= 0) scheduleOnRN(select, dates[index]);
    }).onFinalize(() => {
      hovered.value = -1;
      lift.value = reducedMotion ? 0 : withTiming(0, { duration: 160 });
      follow.value = reducedMotion ? 0 : withTiming(0, { duration: 160 });
    });
  const pickup = useAnimatedStyle(() => ({
    borderColor: lift.value > 0.1 ? palette.primary : palette.border,
    boxShadow: reducedMotion || lift.value <= 0.01 ? 'none' : '0 6px 15px rgba(16, 46, 34, 0.22)',
    transform: [{ translateX: reducedMotion ? 0 : follow.value }, { translateY: reducedMotion ? 0 : -8 * lift.value },
      { scale: reducedMotion ? 1 : 1 + 0.025 * lift.value }],
  }));
  return <View testID="placement-rail" onLayout={event => setWidth(event.nativeEvent.layout.width)}>
    {cell >= 48 && fontScale <= 1.2 && dates.length > 1 ? <View style={styles.stack}>
      <View>
        <Animated.View testID="placement-pickup" style={[styles.pickup, pickup]}>
          {workout && <View style={styles.workout}>{workout}</View>}
          <View style={styles.grip} onLayout={event => setHandleHeight(event.nativeEvent.layout.height)}>
            <View style={styles.handle} /><Text variant="caption" tone="primary">{t('creation.dragDate')}</Text>
          </View>
        </Animated.View>
        <GestureDetector gesture={drag} touchAction="none">
          <Animated.View collapsable={false} testID="placement-touch-grip"
            style={[styles.touchGrip, { height: handleHeight }]} />
        </GestureDetector>
      </View>
      <GestureDetector gesture={pan} touchAction="pan-y"><Animated.View collapsable={false} style={[styles.row, { height: rows * 64 }]}>
        {dates.map((date, index) => <DateTarget key={date} date={date} index={index} cell={cell} label={label}
          active={selected === date} disabled={disabled} onSelect={select} hovered={hovered}
          reducedMotion={reducedMotion} pulse={pulse} />)}
      </Animated.View></GestureDetector>
      {selected && showDate && <View style={styles.confirmation} accessibilityLiveRegion="polite"><Icon name="check" size={20} color={palette.primary} /><Text variant="supporting" tone="primary">{new Date(selected + 'T12:00:00').toLocaleDateString(locale, { dateStyle: 'full' })}</Text></View>}
    </View> : <View style={styles.stack}>{workout}{children}</View>}
  </View>;
}
function DateTarget({ date, index, cell, label, active, disabled, onSelect, hovered, reducedMotion, pulse }: {
  date: string; index: number; cell: number; label: string; active: boolean; disabled: boolean;
  onSelect: (date: string) => void; hovered: SharedValue<number>; reducedMotion: boolean; pulse: SharedValue<number>;
}) {
  const { locale } = useLanguage();
  const local = new Date(date + 'T12:00:00');
  const targetStyle = useAnimatedStyle(() => {
    const over = hovered.value === index && !disabled && !active;
    return {
      backgroundColor: active ? palette.primary : over ? '#FBE4D4' : 'transparent',
      borderColor: over ? '#B45325' : 'transparent',
      transform: [{ scale: reducedMotion ? 1 : active ? 1 + pulse.value * 0.055 : withTiming(over ? 1.045 : 1, { duration: 100 }) }],
    };
  });
  return <Pressable accessibilityRole="button" accessibilityLabel={label + ' \u00b7 ' + local.toLocaleDateString(locale, { dateStyle: 'full' })}
    aria-pressed={active} accessibilityState={{ selected: active, disabled }} disabled={disabled} onPress={() => onSelect(date)}
    style={[styles.day, { width: cell }]}>
    <Animated.View style={[styles.dateFace, targetStyle]}>
      <Text variant="caption" tone={active ? 'textInverse' : 'textMuted'}>{local.toLocaleDateString(locale, { weekday: 'short' })}</Text>
      <Text variant="label" tone={active ? 'textInverse' : 'text'}>{local.getDate()}</Text>
    </Animated.View>
  </Pressable>;
}

const styles = StyleSheet.create({
  pickup: { backgroundColor: palette.surface, borderWidth: 1, borderRadius: 14 },
  workout: { padding: 14 },
  grip: { minHeight: 48, padding: 8, borderRadius: 13, gap: 5, alignItems: 'center', justifyContent: 'center',
    backgroundColor: palette.surfaceSubtle },
  touchGrip: { position: 'absolute', bottom: 0, left: 0, right: 0 },
  handle: { height: 3, width: 24, borderRadius: 2, backgroundColor: palette.borderControl },
  stack: { gap: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: palette.surfaceSubtle, borderRadius: 12 },
  day: { height: 64, padding: 3 },
  dateFace: { flex: 1, alignItems: 'center', justifyContent: 'center', borderRadius: 9, borderWidth: 2 },
  confirmation: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, alignItems: 'center' },
});
