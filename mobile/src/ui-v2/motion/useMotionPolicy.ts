import { useEffect, useState } from 'react';
import { AccessibilityInfo } from 'react-native';
import { useReducedMotion } from 'react-native-reanimated';

export function useMotionPolicy() {
  const initialReducedMotion = useReducedMotion();
  const [reducedMotion, setReducedMotion] = useState(initialReducedMotion);
  useEffect(() => {
    let mounted = true;
    let receivedEvent = false;
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (value) => {
      receivedEvent = true;
      setReducedMotion(value);
    });
    AccessibilityInfo.isReduceMotionEnabled().then((value) => {
      if (mounted && !receivedEvent) setReducedMotion(value);
    }).catch(() => undefined);
    return () => { mounted = false; subscription.remove(); };
  }, []);
  return { reducedMotion } as const;
}
