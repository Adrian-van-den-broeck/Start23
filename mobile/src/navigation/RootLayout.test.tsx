import { render } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';

jest.mock('../../global.css', () => ({}));

import RootLayout from '../../app/_layout';

jest.mock('@gorhom/bottom-sheet', () => {
  const ReactNative = jest.requireActual<typeof import('react-native')>(
    'react-native',
  );
  const language = jest.requireActual<
    typeof import('../i18n/LanguageProvider')
  >('../i18n/LanguageProvider');
  return {
    BottomSheetModalProvider: ({ children }: PropsWithChildren) => {
      const { preference } = language.useLanguage();
      return (
        <ReactNative.View>
          <ReactNative.Text>{`bottom-sheet-language:${preference}`}</ReactNative.Text>
          {children}
        </ReactNative.View>
      );
    },
  };
});

jest.mock('expo-router', () => {
  const ReactNative = jest.requireActual<typeof import('react-native')>(
    'react-native',
  );
  return { Stack: () => <ReactNative.Text>router-stack</ReactNative.Text> };
});

jest.mock('expo-status-bar', () => ({
  StatusBar: () => null,
}));

jest.mock('react-native-gesture-handler', () => {
  const ReactNative = jest.requireActual<typeof import('react-native')>(
    'react-native',
  );
  return {
    GestureHandlerRootView: ({ children }: PropsWithChildren) => (
      <ReactNative.View>{children}</ReactNative.View>
    ),
  };
});

jest.mock('react-native-safe-area-context', () => {
  const ReactNative = jest.requireActual<typeof import('react-native')>(
    'react-native',
  );
  return {
    initialWindowMetrics: null,
    SafeAreaProvider: ({ children }: PropsWithChildren) => (
      <ReactNative.View>{children}</ReactNative.View>
    ),
  };
});

jest.mock('../auth/AuthProvider', () => {
  const ReactNative = jest.requireActual<typeof import('react-native')>(
    'react-native',
  );
  return {
    AuthProvider: ({ children }: PropsWithChildren) => (
      <ReactNative.View>{children}</ReactNative.View>
    ),
  };
});

describe('RootLayout provider order', () => {
  test('keeps bottom-sheet profile content inside the language provider', async () => {
    const view = await render(<RootLayout />);

    expect(view.getByText('bottom-sheet-language:system')).toBeTruthy();
    expect(view.getByText('router-stack')).toBeTruthy();
  });
});
