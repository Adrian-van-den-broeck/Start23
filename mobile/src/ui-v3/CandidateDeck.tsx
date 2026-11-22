import { useCallback, useEffect, useMemo, useRef } from 'react';
import { Image, StyleSheet, useWindowDimensions, View } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { cancelAnimation, Easing, type SharedValue, useAnimatedStyle, useSharedValue, withSequence, withSpring, withTiming } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import type { WorkoutDecision } from '../components/useWorkoutSwipe';
import { useLanguage } from '../i18n/LanguageProvider';
import { useMotionPolicy } from '../ui-v2/motion/useMotionPolicy';
import { Button } from '../ui-v2/primitives/Button';
import { Icon } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import type { SelectionWorkout } from '../ui-v2/utils/planningCreationViewModel';
import { identity, palette } from './tokens';

type Decision = Extract<WorkoutDecision, 'accept' | 'pass'>;

// Drag thresholds match the shared swipe hook so V1, V2 and V3 commit at the same distance.
const commitDistance = 80;
const flickDistance = 28;
const flickVelocity = 550;
const settle = { damping: 20, stiffness: 260, mass: 0.8 };
const peek = 12;

function ramp(value: number, from: number, to: number) {
  'worklet';
  return Math.min(1, Math.max(0, (value - from) / (to - from)));
}

// Same exit duration as useWorkoutSwipe, which waits for it before showing the next card.
function exitDuration(velocity: number) {
  return Math.max(150, Math.min(220, 200 - Math.abs(velocity) * 35));
}

type Props = {
  card: SelectionWorkout;
  action: Decision | undefined;
  locked: boolean;
  stacked: boolean;
  decide: (action: Decision, velocity?: number, y?: number) => Promise<void>;
};

// The whole card is the moving object. A second card waits underneath and rises
// into place while the next candidate loads, so the deck never looks empty.
export function CandidateDeck({ card, action, locked, stacked, decide }: Props) {
  const { t } = useLanguage();
  const { width } = useWindowDimensions();
  const { reducedMotion } = useMotionPolicy();
  const x = useSharedValue(0);
  const y = useSharedValue(0);
  const arrival = useSharedValue(1);
  const loading = useSharedValue(0);
  const wasTravelling = useRef(false);
  const started = useRef(false);
  const current = useRef({ locked, decide, reducedMotion, width });
  useEffect(() => { current.current = { locked, decide, reducedMotion, width }; }, [locked, decide, reducedMotion, width]);

  const springBack = useCallback(() => {
    x.value = withSpring(0, settle);
    y.value = withSpring(0, settle);
  }, [x, y]);

  const commit = useCallback((choice: Decision, velocity = 0) => {
    const { locked: blocked, decide: run, reducedMotion: still, width: span } = current.current;
    if (blocked) { springBack(); return; }
    started.current = false;
    loading.value = 1;
    if (still) arrival.value = 0;
    else {
      const duration = exitDuration(velocity);
      const easing = Easing.out(Easing.cubic);
      x.value = withTiming((choice === 'accept' ? 1 : -1) * span * 1.3, { duration, easing });
      y.value = withTiming(y.value + 24, { duration, easing });
    }
    void run(choice, velocity, 0).then(() => {
      // The hook declined without starting a transition, so bring the card back.
      if (started.current) return;
      loading.value = 0;
      arrival.value = 1;
      springBack();
    });
  }, [arrival, loading, springBack, x, y]);

  const release = useCallback((direction: number, velocityX: number) => {
    commit(direction > 0 ? 'accept' : 'pass', velocityX / 1000);
  }, [commit]);

  // The hook clears `action` once the save and the exit are both done. The next
  // card then fades in where the waiting card stood instead of jumping into view.
  const travelling = action !== undefined;
  useEffect(() => {
    if (travelling) { wasTravelling.current = true; started.current = true; return; }
    if (!wasTravelling.current) return;
    wasTravelling.current = false;
    cancelAnimation(x);
    cancelAnimation(y);
    loading.value = 0;
    x.value = 0;
    y.value = 0;
    arrival.value = reducedMotion ? 1 : withSequence(withTiming(0, { duration: 0 }), withTiming(1, { duration: 200, easing: Easing.out(Easing.cubic) }));
  }, [arrival, loading, reducedMotion, travelling, x, y]);

  const pan = useMemo(() => Gesture.Pan().withTestId('candidate-deck-swipe').enabled(!locked).maxPointers(1)
    .activeOffsetX([-14, 14]).failOffsetY([-12, 12])
    .onStart(() => { cancelAnimation(x); cancelAnimation(y); })
    .onUpdate(event => {
      x.value = event.translationX;
      y.value = event.translationY * 0.2;
    })
    .onEnd((event, success) => {
      const distance = Math.abs(event.translationX);
      const flick = distance >= flickDistance && Math.abs(event.velocityX) >= flickVelocity
        && Math.sign(event.velocityX) === Math.sign(event.translationX);
      if (success && (distance >= commitDistance || flick)) scheduleOnRN(release, event.translationX, event.velocityX);
      else {
        x.value = withSpring(0, settle);
        y.value = withSpring(0, settle);
      }
    }),
  [locked, release, x, y]);

  const frontStyle = useAnimatedStyle(() => ({
    opacity: arrival.value,
    transform: [
      { translateX: x.value }, { translateY: y.value },
      { rotate: `${reducedMotion ? 0 : (x.value / width) * 10}deg` },
      { scale: 0.97 + arrival.value * 0.03 },
    ],
  }));
  const backStyle = useAnimatedStyle(() => {
    const rise = Math.max(ramp(Math.abs(x.value), 0, width * 0.5), 1 - arrival.value);
    return { transform: [{ translateY: peek * (1 - rise) }, { scale: 0.94 + rise * 0.06 }] };
  });
  const loadingStyle = useAnimatedStyle(() => ({
    opacity: loading.value * Math.max(ramp(Math.abs(x.value), width * 0.6, width), 1 - arrival.value),
  }));
  const chooseStyle = useAnimatedStyle(() => ({
    opacity: ramp(x.value, 30, 80), transform: [{ rotate: '-8deg' }, { scale: 0.9 + ramp(x.value, 30, 80) * 0.1 }],
  }));
  const passStyle = useAnimatedStyle(() => ({
    opacity: ramp(-x.value, 30, 80), transform: [{ rotate: '8deg' }, { scale: 0.9 + ramp(-x.value, 30, 80) * 0.1 }],
  }));

  return <View style={styles.frame}>
    <View style={styles.deck}>
      <Animated.View pointerEvents="none" style={[styles.waiting, backStyle]}
        accessibilityElementsHidden={!travelling} importantForAccessibility={travelling ? 'auto' : 'no-hide-descendants'}>
        <Animated.View style={loadingStyle}>
          <Text variant="label" style={styles.soft} accessibilityLiveRegion="polite">{t('creation.nextCard')}</Text>
        </Animated.View>
      </Animated.View>
      <GestureDetector gesture={pan} touchAction="pan-y">
        <Animated.View testID="workout-swipe-surface" collapsable={false} style={[styles.card, frontStyle]}
          accessibilityElementsHidden={travelling} importantForAccessibility={travelling ? 'no-hide-descendants' : 'auto'}>
          <CandidateFace key={card.occurrenceId} workout={card} x={x} />
          <Animated.View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants"
            style={[styles.stamp, styles.chooseStamp, chooseStyle]}>
            <Icon name="check" size={20} color={identity.ink} />
            <Text variant="label" style={styles.chooseText}>{t('creation.choose')}</Text>
          </Animated.View>
          <Animated.View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants"
            style={[styles.stamp, styles.passStamp, passStyle]}>
            <Icon name="close" size={20} color={palette.textInverse} />
            <Text variant="label" tone="textInverse">{t('creation.pass')}</Text>
          </Animated.View>
        </Animated.View>
      </GestureDetector>
    </View>
    {/* Skip sits left and choose right, the same way the card travels. Choose is read first. */}
    <View style={[styles.actions, stacked && styles.stackedActions]}>
      <View style={styles.action}>
        <Button label={t('creation.choose')} accessibilityLabel={`${t('creation.choose')} · ${card.name}`}
          trailingIcon="check" disabled={locked} onPress={() => commit('accept')} />
      </View>
      <View style={styles.action}>
        <Button label={t('creation.pass')} accessibilityLabel={`${t('creation.pass')} · ${card.name}`}
          trailingIcon="close" variant="secondary" disabled={locked} onPress={() => commit('pass')} />
      </View>
    </View>
    <Text variant="supporting" tone="textMuted" style={styles.hint}>{t('creation.swipeChoice')}</Text>
  </View>;
}

function CandidateFace({ workout, x }: { workout: SelectionWorkout; x: SharedValue<number> }) {
  const { t } = useLanguage();
  // The choose stamp takes the sport label's corner, so the label steps aside for it.
  const labelStyle = useAnimatedStyle(() => ({ opacity: 1 - ramp(x.value, 6, 30) }));
  const { discipline, durationMinutes, distanceMeters } = workout;
  const run = discipline === 'run';
  return <View testID={`selection-occurrence-${workout.occurrenceId}`} style={styles.face}>
    <View style={[styles.cover, { backgroundColor: palette.sport[discipline].text }, run && styles.trackCover]}>
      {run ? <Image accessible={false} source={require('../../assets/wombo-track.jpg')} resizeMode="cover" style={styles.photo} /> : null}
      <Animated.View style={[styles.sport, labelStyle]}>
        <Icon name={discipline} size={20} color={palette.textInverse} />
        <Text variant="label" tone="textInverse">{t(`common.${discipline}`)}</Text>
      </Animated.View>
    </View>
    <View style={styles.body}>
      <Text variant="display" tone="textInverse" accessibilityRole="header">{workout.name}</Text>
      <View style={styles.facts}>
        {durationMinutes !== null && <Text variant="numeric" tone="textInverse"
          accessibilityLabel={t('detail.minutesSpoken', { value: durationMinutes })}>{t('common.durationMinutes', { minutes: durationMinutes })}</Text>}
        {distanceMeters !== null && <Text variant="numeric" tone="textInverse"
          accessibilityLabel={t('detail.metersSpoken', { value: distanceMeters })}>{t('detail.meters', { value: distanceMeters })}</Text>}
        <View style={styles.intensity}>
          <Icon name="intensity" size={20} color={palette.primarySoft} />
          <Text variant="label" style={styles.soft}>{t(`detail.intensity.${workout.intensity}`)}</Text>
        </View>
      </View>
      {workout.description ? <Text variant="supporting" style={styles.soft}>{workout.description}</Text> : null}
    </View>
  </View>;
}

const radius = 24;
const styles = StyleSheet.create({
  frame: { gap: 20, zIndex: 1 },
  deck: { paddingBottom: peek },
  waiting: { position: 'absolute', top: 0, left: 0, right: 0, bottom: peek, borderRadius: radius,
    backgroundColor: palette.primary, alignItems: 'center', justifyContent: 'center', padding: 24, transformOrigin: 'bottom' },
  card: { borderRadius: radius, backgroundColor: identity.ink, transformOrigin: 'bottom',
    shadowColor: identity.ink, shadowOpacity: 0.22, shadowOffset: { width: 0, height: 10 }, shadowRadius: 22, elevation: 8 },
  face: { borderRadius: radius, overflow: 'hidden', minHeight: 280 },
  cover: { minHeight: 84, justifyContent: 'flex-start', alignItems: 'flex-start', padding: 16 },
  trackCover: { minHeight: 136 },
  photo: { ...StyleSheet.absoluteFill, width: '100%', height: '100%' },
  sport: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 8, backgroundColor: identity.ink },
  body: { flex: 1, padding: 20, paddingTop: 18, gap: 10 },
  facts: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'baseline', columnGap: 14, rowGap: 4 },
  intensity: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  soft: { color: palette.primarySoft },
  stamp: { position: 'absolute', top: 14, flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 12, borderWidth: 2 },
  chooseStamp: { left: 16, backgroundColor: identity.orange, borderColor: identity.orange },
  chooseText: { color: identity.ink },
  passStamp: { right: 16, backgroundColor: identity.ink, borderColor: palette.primarySoft },
  actions: { flexDirection: 'row-reverse', gap: 12 },
  stackedActions: { flexDirection: 'column' },
  action: { flex: 1 },
  hint: { textAlign: 'center' },
});
