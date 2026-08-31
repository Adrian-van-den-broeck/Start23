import * as Haptics from 'expo-haptics';
import { forwardRef } from 'react';
import {
  Pressable,
  type PressableProps,
  type PressableStateCallbackType,
  type View,
} from 'react-native';
import { useReducedMotion } from 'react-native-reanimated';

export type HapticKind = 'light' | 'selection' | 'success';

type MotionPressableProps = PressableProps & {
  haptic?: HapticKind;
  pressedScale?: number;
};

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
    const reduceMotion = useReducedMotion();

    return (
      <Pressable
        {...props}
        disabled={disabled}
        onPress={(event) => {
          if (haptic) playHaptic(haptic);
          onPress?.(event);
        }}
        onPressIn={(event) => {
          onPressIn?.(event);
        }}
        onPressOut={(event) => {
          onPressOut?.(event);
        }}
        ref={ref}
        style={(state: PressableStateCallbackType) => [
          typeof style === 'function' ? style(state) : style,
          state.pressed &&
            !disabled &&
            !reduceMotion && {
              opacity: 0.88,
              transform: [{ scale: pressedScale }],
            },
        ]}
      />
    );
  },
);
