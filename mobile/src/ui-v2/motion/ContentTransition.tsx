import { useEffect, type ReactNode } from 'react';
import Animated, { cancelAnimation, Easing, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { motion } from '../tokens';
import { useMotionPolicy } from './useMotionPolicy';

export function ContentTransition({ children }: { children: ReactNode }) {
  const { reducedMotion } = useMotionPolicy();
  const opacity = useSharedValue(reducedMotion ? 1 : 0);
  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));
  useEffect(() => {
    cancelAnimation(opacity);
    opacity.value = reducedMotion ? 1 : withTiming(1, {
      duration: motion.loadingContent, easing: Easing.out(Easing.quad),
    });
    return () => cancelAnimation(opacity);
  }, [opacity, reducedMotion]);
  return <Animated.View style={style}>{children}</Animated.View>;
}
