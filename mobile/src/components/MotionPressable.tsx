import * as Haptics from 'expo-haptics';
import { forwardRef, useState } from 'react';
import {
  Pressable,
  type PressableProps,
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
    const [pressed, setPressed] = useState(false);
    const isPressed = pressed && !disabled;
    // NativeWind's Pressable interop drops function-valued style props before
    // React Native can resolve them, so always pass it a concrete style array.
    const resolvedStyle =
      typeof style === 'function'
        ? style({ hovered: false, pressed: isPressed })
        : style;

    return (
      <Pressable
        {...props}
        disabled={disabled}
        onPress={(event) => {
          if (haptic) playHaptic(haptic);
          onPress?.(event);
        }}
        onPressIn={(event) => {
          if (!disabled) setPressed(true);
          onPressIn?.(event);
        }}
        onPressOut={(event) => {
          setPressed(false);
          onPressOut?.(event);
        }}
        ref={ref}
        style={[
          resolvedStyle,
          isPressed &&
            !reduceMotion && {
              opacity: 0.88,
              transform: [{ scale: pressedScale }],
            },
        ]}
      />
    );
  },
);
