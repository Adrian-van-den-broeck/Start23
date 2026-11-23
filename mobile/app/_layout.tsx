import { useMotionPolicy } from '@/ui-v2/motion/useMotionPolicy';
import '../global.css';

import { BottomSheetModalProvider } from '@gorhom/bottom-sheet';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import {
  initialWindowMetrics,
  SafeAreaProvider,
} from 'react-native-safe-area-context';

import { AuthProvider } from '@/auth/AuthProvider';
import { LanguageProvider } from '@/i18n/LanguageProvider';
import { UiVersionProvider } from '@/ui/UiVersionProvider';
import { colors } from '@/theme/tokens';

export default function RootLayout() {
  const { reducedMotion } = useMotionPolicy();
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider initialMetrics={initialWindowMetrics}>
        <LanguageProvider>
          <BottomSheetModalProvider>
            <StatusBar style="dark" />
            <AuthProvider>
              <UiVersionProvider>
                <Stack
                  screenOptions={{
                    animation: reducedMotion ? 'none' : 'fade_from_bottom',
                    animationDuration: 240,
                    contentStyle: { backgroundColor: colors.canvas },
                    headerShown: false,
                  }}
                />
              </UiVersionProvider>
            </AuthProvider>
          </BottomSheetModalProvider>
        </LanguageProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
