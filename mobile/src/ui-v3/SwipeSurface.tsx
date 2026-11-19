import { useCallback, useEffect, useMemo, useRef, type ReactNode } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { cancelAnimation, useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import * as Haptics from 'expo-haptics';
import { useMotionPolicy } from '../ui-v2/motion/useMotionPolicy';
import { studioPresentation } from './presentation';

type Props = { children: ReactNode; disabled?: boolean; translate?: boolean; context?: string; style?: StyleProp<ViewStyle>; onSwipe: (direction: -1 | 1) => void };

export function SwipeSurface(props: Props) {
  return studioPresentation ? <HorizontalSwipe {...props} /> : <>{props.children}</>;
}

function HorizontalSwipe({ children, disabled = false, onSwipe, translate = true, context, style }: Props) {
  const { reducedMotion } = useMotionPolicy();
  const offset = useSharedValue(0);
  const live = useRef(true);
  const current = useRef({ onSwipe, disabled, context });
  useEffect(() => { current.current = { onSwipe, disabled, context }; }, [onSwipe, disabled, context]);
  useEffect(() => {
    live.current = true;
    return () => { live.current = false; cancelAnimation(offset); };
  }, [offset]);
  const finish = useCallback((direction: -1 | 1, startedIn?: string) => {
    if (!live.current || current.current.disabled || startedIn !== current.current.context) return;
    current.current.onSwipe(direction);
    void Haptics.selectionAsync().catch(() => undefined);
  }, []);
  const pan = useMemo(() => Gesture.Pan().withTestId('horizontal-presentation-swipe').enabled(!disabled).maxPointers(1)
    .activeOffsetX([-18, 18]).failOffsetY([-10, 10])
    .onStart(() => { cancelAnimation(offset); })
    .onUpdate(event => {
      if (translate && !reducedMotion) offset.value = Math.max(-32, Math.min(32, event.translationX * 0.3));
    })
    .onEnd((event, committed) => {
      if (committed && Math.abs(event.translationX) >= 60 && Math.abs(event.translationX) > Math.abs(event.translationY) * 1.5)
        scheduleOnRN(finish, event.translationX > 0 ? 1 : -1, context);
    })
    .onFinalize(() => {
      if (translate) offset.value = reducedMotion ? 0 : withSpring(0, { stiffness: 310, damping: 27 });
    }),
  [context, disabled, finish, offset, reducedMotion, translate]);
  const motionStyle = useAnimatedStyle(() => ({ transform: [{ translateX: offset.value }] }));
  return <GestureDetector gesture={pan} touchAction="pan-y">
    {translate ? <Animated.View collapsable={false} style={[style, motionStyle]}>{children}</Animated.View>
      : <View collapsable={false} style={style}>{children}</View>}
  </GestureDetector>;
}
