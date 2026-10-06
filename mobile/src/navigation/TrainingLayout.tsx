import { Stack, Tabs, usePathname, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../i18n/LanguageProvider';
import { ScreenState } from '../components/ScreenState';
import { colors } from '../theme/tokens';
import { useOptionalPlanningPresentation } from './PlanningPresentationProvider';
import { TrainingReadiness } from './TrainingFlowHost';

export function TrainingLayout() {
  const presentation = useOptionalPlanningPresentation();
  const { t } = useLanguage();
  const rootVersion = presentation?.rootVersion;
  const [navigatorVersion, setNavigatorVersion] = useState(rootVersion);
  const pathname = usePathname();
  const router = useRouter();
  const activityOrigin = useRef(pathname === '/activities');
  const comparisonDestination = useRef<'activities' | null>(null);
  // Keep Activities as the destination of its own safe presentation comparison.
  // Calendar's accepted V1 fallback still uses Planning's internal Calendar view.
  if (navigatorVersion === rootVersion) activityOrigin.current = pathname === '/activities';
  else if (pathname === '/activities') comparisonDestination.current = 'activities';
  const [destinationHeight, setDestinationHeight] = useState(56);
  useEffect(() => { setNavigatorVersion(rootVersion); }, [rootVersion]);
  useEffect(() => {
    if (navigatorVersion !== rootVersion) return;
    const destination = comparisonDestination.current;
    comparisonDestination.current = null;
    // Keep Week as Tabs' initial/back destination, then restore the comparison origin.
    if (rootVersion === 'v2' && destination === 'activities') router.navigate('/activities');
  }, [navigatorVersion, rootVersion, router]);
  // A direct task -> root transition can mount the child layout before its
  // parent's pathname update. Never expose root content before the ready host.
  if (!presentation) return <TrainingReadiness />;
  const { navigationLocked } = presentation;
  // Let the old navigator unregister and clear its route state before mounting
  // a different router type. A key alone still races the old cleanup on native.
  // Flow and presentation owners remain above this presentation-only gap.
  if (navigatorVersion !== rootVersion) return <ScreenState loading title={t('shell.readinessLoading')} />;
  if (rootVersion === 'v1') return <Stack key="v1-training" initialRouteName={activityOrigin.current ? 'activities' : 'planning'} screenOptions={{ headerShown: false }} />;
  return <Tabs key="v2-training" initialRouteName="planning" backBehavior="initialRoute" screenOptions={{
    headerShown: false, lazy: true,
  }} screenListeners={{ tabPress: (event) => { if (navigationLocked) event.preventDefault(); } }}
    tabBar={({ state, descriptors, navigation }) => navigationLocked ? (
      presentation.detailWorkout ? <SafeAreaView testID="training-detail-footprint" edges={['bottom']} style={styles.bar} pointerEvents="none"
        accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <View style={{ height: destinationHeight }} />
      </SafeAreaView> : null
    ) : (
      <SafeAreaView edges={['bottom']} style={styles.bar}>
        <View testID="training-root-navigation" accessibilityRole="tablist" style={styles.destinations}
          onLayout={(event) => setDestinationHeight(event.nativeEvent.layout.height)}>
          {state.routes.map((route, index) => {
            const selected = state.index === index;
            const label = descriptors[route.key].options.title ?? route.name;
            return <Pressable key={route.key} accessible accessibilityRole="tab"
              accessibilityState={{ selected }} accessibilityLabel={label}
              style={[styles.destination, selected && styles.selected]}
              onPress={() => {
                const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
                if (!selected && !event.defaultPrevented) navigation.navigate(route.name);
              }}>
              <Text accessible={false} style={[styles.label, selected && styles.selectedLabel]}>{label}</Text>
            </Pressable>;
          })}
        </View>
      </SafeAreaView>
    )}>
    <Tabs.Screen name="planning" options={{ title: t('shell.week') }} />
    <Tabs.Screen name="calendar" options={{ title: t('shell.calendar') }} />
    <Tabs.Screen name="activities" options={{ title: t('shell.activities') }} />
  </Tabs>;
}
const styles = StyleSheet.create({
  bar: { backgroundColor: colors.canvas, borderTopWidth: 1, borderTopColor: colors.brand },
  destinations: { flexDirection: 'row' },
  destination: { flex: 1, minHeight: 56, minWidth: 48, padding: 8, justifyContent: 'center', alignItems: 'center' },
  selected: { backgroundColor: colors.brand },
  label: { fontSize: 16, color: colors.ink, textAlign: 'center' },
  selectedLabel: { color: colors.white, fontWeight: '700' },
});
