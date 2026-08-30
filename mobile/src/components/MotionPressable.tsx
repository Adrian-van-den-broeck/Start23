import * as Haptics from 'expo-haptics';
import { forwardRef } from 'react';
import {
  Pressable,
  type PressableProps,
  type PressableStateCallbackType,
  type View,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import { motion } from '../theme/tokens';

export type HapticKind = 'light' | 'selection' | 'success';

type MotionPressableProps = PressableProps & {
  haptic?: HapticKind;
  pressedScale?: number;
};

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

function playHaptic(kind: HapticKind): void {
  const feedback =
    kind === 'selection'
      ? Haptics.selectionAsync()
      : kind === 'success'
        ? Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
        : Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  void feedback.catch(() => undefined);
}

export const MotionPressable = forwardRef<View, MotionPressableProps>(
  function MotionPressable(
    {
      disabled,
      haptic,
      onPress,
      onPressIn,
      onPressOut,
      pressedScale = 0.975,
      style,
      ...props
    },
    ref,
  ) {
    const scale = useSharedValue(1);
    const opacity = useSharedValue(1);
    const reduceMotion = useReducedMotion();
    const animatedStyle = useAnimatedStyle(() => ({
      opacity: opacity.value,
      transform: [{ scale: scale.value }],
    }));

    return (
      <AnimatedPressable
        {...props}
        disabled={disabled}
        onPress={(event) => {
          if (haptic) playHaptic(haptic);
          onPress?.(event);
        }}
        onPressIn={(event) => {
          if (!disabled && !reduceMotion) {
            scale.value = withSpring(pressedScale, motion.spring);
            opacity.value = withTiming(0.88, {
              duration: motion.duration.fast,
            });
          }
          onPressIn?.(event);
        }}
        onPressOut={(event) => {
          scale.value = withSpring(1, motion.spring);
          opacity.value = withTiming(1, { duration: motion.duration.fast });
          onPressOut?.(event);
        }}
        ref={ref}
        style={(state: PressableStateCallbackType) => [
          typeof style === 'function' ? style(state) : style,
          animatedStyle,
        ]}
      />
    );
  },
);
