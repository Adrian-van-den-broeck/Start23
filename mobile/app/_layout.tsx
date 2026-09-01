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
import { colors } from '@/theme/tokens';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider initialMetrics={initialWindowMetrics}>
        <BottomSheetModalProvider>
          <StatusBar style="dark" />
          <LanguageProvider>
            <AuthProvider>
              <Stack
                screenOptions={{
                  animation: 'fade_from_bottom',
                  animationDuration: 240,
                  contentStyle: { backgroundColor: colors.canvas },
                  headerShown: false,
                }}
              />
            </AuthProvider>
          </LanguageProvider>
        </BottomSheetModalProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
