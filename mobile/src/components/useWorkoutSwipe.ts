import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, PanResponder, Platform, useWindowDimensions } from 'react-native';

export type WorkoutDecision = 'accept' | 'pass' | 'undo' | 'reset_passed';
type SwipeDecision = Extract<WorkoutDecision, 'accept' | 'pass'>;

export function useWorkoutSwipe<T>(candidate: T | null, busy: boolean,
  onTransition: (decision: WorkoutDecision) => void | Promise<void>,
  setTransientBusy?: (busy: boolean) => void,
  // The server's preview of the next card for a decision. Shown once the
  // outgoing card has left while the decision is still being saved.
  preview?: (decision: SwipeDecision) => T | null,
) {
  const { width } = useWindowDimensions();
  const motion = useRef(new Animated.ValueXY()).current;
  const opacity = useRef(new Animated.Value(1)).current;
  const animation = useRef<Animated.CompositeAnimation | null>(null);
  const inFlight = useRef(false);
  const mounted = useRef(true);
  const reducedMotion = useRef(false);
  const [departing, setDeparting] = useState<{ card: T; action?: SwipeDecision } | null>(null);
  const useNativeDriver = Platform.OS !== 'web';

  useEffect(() => {
    mounted.current = true;
    void AccessibilityInfo.isReduceMotionEnabled().then(value => { reducedMotion.current = value; }).catch(() => undefined);
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', value => { reducedMotion.current = value; });
    return () => {
      mounted.current = false;
      subscription.remove();
      animation.current?.stop();
      opacity.stopAnimation();
      if (inFlight.current) setTransientBusy?.(false);
    };
  }, [opacity, setTransientBusy]);

  const reset = useCallback(() => {
    animation.current?.stop();
    if (reducedMotion.current) {
      motion.setValue({ x: 0, y: 0 });
      return;
    }
    animation.current = Animated.spring(motion, {
      damping: 18, mass: 0.7, stiffness: 220, toValue: { x: 0, y: 0 }, useNativeDriver,
    });
    animation.current.start();
  }, [motion, useNativeDriver]);

  const decide = useCallback(async (action: SwipeDecision, velocity = 0, y = 0) => {
    if (busy || !candidate || inFlight.current) return;
    inFlight.current = true;
    setDeparting({ card: candidate, action });
    setTransientBusy?.(true);
    animation.current?.stop();
    // Puts the card surface back in place with a short fade, for the next card.
    let shown = false;
    const bringIn = () => {
      if (shown) return;
      shown = true;
      if (!reducedMotion.current) {
        opacity.setValue(0.75);
        Animated.timing(opacity, { toValue: 1, duration: 150, useNativeDriver }).start();
      }
      motion.setValue({ x: 0, y: 0 });
    };
    const exit = reducedMotion.current ? Promise.resolve() : new Promise<void>(resolve => {
      animation.current = Animated.timing(motion, {
        duration: Math.max(150, Math.min(220, 200 - Math.abs(velocity) * 35)),
        easing: Easing.out(Easing.cubic),
        toValue: { x: (action === 'accept' ? 1 : -1) * width * 1.25, y },
        useNativeDriver,
      });
      animation.current.start(() => resolve());
    });
    // Persist and look up the next card while the outgoing card is moving.
    let saved = false;
    const next = preview?.(action) ?? null;
    if (next !== null) {
      void exit.then(() => {
        // Still saving: show the previewed card (locked by `busy`) instead of an empty deck.
        if (saved || !mounted.current) return;
        bringIn();
        setDeparting({ card: next });
      });
    }
    try {
      await onTransition(action);
    } finally {
      saved = true;
      await exit;
      if (mounted.current) {
        bringIn();
        setDeparting(null);
        inFlight.current = false;
        setTransientBusy?.(false);
      }
    }
  }, [busy, candidate, motion, onTransition, opacity, preview, setTransientBusy, useNativeDriver, width]);

  const pan = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_, gesture) => !busy && !inFlight.current && candidate !== null &&
      Math.abs(gesture.dx) > 14 && Math.abs(gesture.dx) > 1.3 * Math.abs(gesture.dy),
    onPanResponderGrant: () => animation.current?.stop(),
    onPanResponderMove: (_, gesture) => {
      if (!reducedMotion.current) motion.setValue({ x: gesture.dx, y: gesture.dy * 0.18 });
    },
    onPanResponderRelease: (_, gesture) => {
      const deliberate = Math.abs(gesture.dx) >= 80 ||
        (Math.abs(gesture.dx) >= 28 && Math.abs(gesture.vx) >= 0.55);
      if (deliberate) void decide(gesture.dx > 0 ? 'accept' : 'pass', gesture.vx, gesture.dy * 0.18);
      else reset();
    },
    onPanResponderTerminate: reset,
  }), [busy, candidate, decide, motion, reset]);

  const rotation = motion.x.interpolate({
    inputRange: [-width, 0, width], outputRange: ['-11deg', '0deg', '11deg'], extrapolate: 'clamp',
  });
  const staticLoading = !!departing && reducedMotion.current;
  return {
    card: departing?.card ?? candidate, action: departing?.action, decide, panHandlers: pan.panHandlers,
    opacity: staticLoading ? 0 : opacity,
    transform: [{ translateX: motion.x }, { translateY: motion.y }, { rotate: rotation }],
    acceptOpacity: motion.x.interpolate({ inputRange: [20, 100], outputRange: [0, 1], extrapolate: 'clamp' }),
    passOpacity: motion.x.interpolate({ inputRange: [-100, -20], outputRange: [1, 0], extrapolate: 'clamp' }),
    loadingOpacity: staticLoading ? 1 : motion.x.interpolate({
      inputRange: [-width, -width * 0.7, width * 0.7, width],
      outputRange: [1, 0, 0, 1], extrapolate: 'clamp',
    }),
  };
}
