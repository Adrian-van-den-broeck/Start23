import { Stack, Tabs } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../i18n/LanguageProvider';
import { colors } from '../theme/tokens';
import { useOptionalPlanningPresentation } from './PlanningPresentationProvider';
import { TrainingReadiness } from './TrainingFlowHost';

export function TrainingLayout() {
  const presentation = useOptionalPlanningPresentation();
  const { t } = useLanguage();
  // A direct task -> root transition can mount the child layout before its
  // parent's pathname update. Never expose root content before the ready host.
  if (!presentation) return <TrainingReadiness />;
  const { rootVersion, navigationLocked } = presentation;
  if (rootVersion === 'v1') return <Stack screenOptions={{ headerShown: false }} />;
  return <Tabs initialRouteName="planning" backBehavior="initialRoute" screenOptions={{
    headerShown: false, lazy: true,
  }} screenListeners={{ tabPress: (event) => { if (navigationLocked) event.preventDefault(); } }}
    tabBar={({ state, descriptors, navigation }) => navigationLocked ? null : (
      <SafeAreaView edges={['bottom']} style={styles.bar}>
        <View testID="training-root-navigation" accessibilityRole="tablist" style={styles.destinations}>
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
