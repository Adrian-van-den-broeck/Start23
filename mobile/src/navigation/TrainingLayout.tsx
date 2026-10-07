import { Stack, Tabs, usePathname, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../i18n/LanguageProvider';
import { ScreenState } from '../components/ScreenState';
import { BottomNavigation, NavigationFooter } from '../ui-v2/components/BottomNavigation';
import { ShellInsets } from '../ui-v2/components/ShellInsets';
import { layout } from '../ui-v2/tokens';
import { useOptionalPlanningPresentation } from './PlanningPresentationProvider';
import { TrainingReadiness } from './TrainingFlowHost';

export function TrainingLayout() {
  const insets = useSafeAreaInsets();
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
  const [destinationHeight, setDestinationHeight] = useState<number>(layout.bottomNav.minHeight);
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
  return <ShellInsets bottom={!navigationLocked || !!presentation.detailWorkout}><Tabs key="v2-training" initialRouteName="planning" backBehavior="initialRoute" screenOptions={{
    headerShown: false, lazy: true,
  }} screenListeners={{ tabPress: (event) => { if (navigationLocked) event.preventDefault(); } }}
    tabBar={({ state, descriptors, navigation }) => navigationLocked ? (
      presentation.detailWorkout ? <NavigationFooter bottomInset={insets.bottom}>
        <View testID="training-detail-footprint" pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <View style={{ height: destinationHeight }} />
        </View>
      </NavigationFooter> : null
    ) : (
      <NavigationFooter bottomInset={insets.bottom}>
        <BottomNavigation destinations={state.routes.map((route) => ({ key: route.key,
          label: descriptors[route.key].options.title ?? route.name,
          icon: route.name === 'planning' ? 'week' : route.name === 'calendar' ? 'calendar' : 'activities',
        }))} selectedKey={state.routes[state.index].key} onHeight={setDestinationHeight} onSelect={(key) => {
          const route = state.routes.find((destination) => destination.key === key);
          if (!route) return;
          const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
          if (state.routes[state.index].key !== key && !event.defaultPrevented) navigation.navigate(route.name);
        }} />
      </NavigationFooter>
    )}>
    <Tabs.Screen name="planning" options={{ title: t('shell.week') }} />
    <Tabs.Screen name="calendar" options={{ title: t('shell.calendar') }} />
    <Tabs.Screen name="activities" options={{ title: t('shell.activities') }} />
  </Tabs></ShellInsets>;
}
