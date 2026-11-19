import 'react-native-gesture-handler/jestSetup';

jest.mock('expo-haptics', () => ({
  ImpactFeedbackStyle: { Light: 'light' },
  NotificationFeedbackType: { Success: 'success' },
  impactAsync: jest.fn(async () => undefined),
  notificationAsync: jest.fn(async () => undefined),
  selectionAsync: jest.fn(async () => undefined),
}));

jest.mock('react-native-reanimated', () => {
  const ReactNative = jest.requireActual('react-native');
  const transition = {
    damping: () => transition,
    mass: () => transition,
    springify: () => transition,
    stiffness: () => transition,
  };
  return {
    __esModule: true,
    default: {
      View: ReactNative.View,
      Text: ReactNative.Text,
      createAnimatedComponent: (component: unknown) => component,
    },
    LinearTransition: transition,
    Easing: ReactNative.Easing,
    cancelAnimation: jest.fn(),
    interpolateColor: (
      _value: number,
      _input: number[],
      output: string[],
    ) => output[0],
    useEvent: (callback: unknown) => callback,
    useAnimatedStyle: (factory: () => unknown) => factory(),
    useReducedMotion: () => true,
    useSharedValue: (value: unknown) => ({ value }),
    withDelay: (_delay: number, value: unknown) => value,
    withSpring: (value: unknown) => value,
    withTiming: (value: unknown) => value,
  };
});

// Jest has no native worklet VM. Deliver the completed gesture on the test thread.
jest.mock('react-native-worklets', () => ({
  scheduleOnRN: (callback: (...args: unknown[]) => void, ...args: unknown[]) => callback(...args),
}));
