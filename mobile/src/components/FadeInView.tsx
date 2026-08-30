import type { PropsWithChildren } from 'react';
import { useEffect } from 'react';
import type { StyleProp, ViewStyle } from 'react-native';
import Animated, {
  cancelAnimation,
  LinearTransition,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import { motion } from '../theme/tokens';

type FadeInViewProps = PropsWithChildren<{
  delay?: number;
  distance?: number;
  duration?: number;
  style?: StyleProp<ViewStyle>;
}>;

export function FadeInView({
  children,
  delay = 0,
  distance = 16,
  duration = 420,
  style,
}: FadeInViewProps) {
  const reduceMotion = useReducedMotion();
  const opacity = useSharedValue(reduceMotion ? 1 : 0);
  const translateY = useSharedValue(reduceMotion ? 0 : distance);

  useEffect(() => {
    if (reduceMotion) {
      opacity.value = 1;
      translateY.value = 0;
      return;
    }
    opacity.value = withDelay(delay, withTiming(1, { duration }));
    translateY.value = withDelay(
      delay,
      withSpring(0, motion.spring),
    );
    return () => {
      cancelAnimation(opacity);
      cancelAnimation(translateY);
    };
  }, [delay, duration, opacity, reduceMotion, translateY]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translateY.value }],
  }));

  return (
    <Animated.View
      layout={LinearTransition.springify()
        .damping(motion.spring.damping)
        .mass(motion.spring.mass)
        .stiffness(motion.spring.stiffness)}
      style={[style, animatedStyle]}
    >
      {children}
    </Animated.View>
  );
}
