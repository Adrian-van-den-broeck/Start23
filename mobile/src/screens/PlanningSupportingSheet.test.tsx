import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { onboarding } from '../features/planning/planning.test-fixtures';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { PlanningScreen } from './PlanningScreen';
let mockFinishDismiss: () => void;
const mockDismiss = jest.fn();
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../api/client', () => ({ getOnboarding: jest.fn(), getWeeklyPlan: jest.fn(), getSwipeWeekDraft: jest.fn(), getCalendar: jest.fn() }));
jest.mock('@gorhom/bottom-sheet', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const RN = jest.requireActual<typeof import('react-native')>('react-native');
  return {
    BottomSheetBackdrop: () => null,
    BottomSheetScrollView: ({children}: PropsWithChildren) => <RN.ScrollView>{children}</RN.ScrollView>,
    BottomSheetModal: React.forwardRef(({children, onDismiss, onChange}: PropsWithChildren<{onDismiss: () => void; onChange: (index: number) => void}>, ref) => {
      const [visible, setVisible] = React.useState(false);
      mockFinishDismiss = () => { setVisible(false); onDismiss(); };
      React.useImperativeHandle(ref, () => ({ present: () => { setVisible(true); onChange(0); }, dismiss: mockDismiss }));
      return visible ? <RN.View>{children}</RN.View> : null;
    }),
  };
});
jest.mock('react-native-reanimated-carousel', () => ({ Carousel: () => null }));
beforeEach(() => { jest.clearAllMocks(); process.env.EXPO_PUBLIC_UI_VERSION='v1'; jest.mocked(SecureStore.getItemAsync).mockImplementation(async key => key === 'start23.language-preference' ? 'nl' : null); jest.mocked(api.getOnboarding).mockResolvedValue(onboarding); });
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; });
test.each(['profile','integrations','signout'] as const)('existing sheet defers %s callback until modal dismissal', async destination => {
  const profile = jest.fn(); const integrations = jest.fn(); const signout = jest.fn(async () => undefined);
  const view = await render(<SafeAreaProvider initialMetrics={{frame:{x:0,y:0,width:393,height:830},insets:{top:24,bottom:24,left:0,right:0}}}><LanguageProvider><UiVersionProvider><PlanningScreen accessToken="athlete-token" onOpenProfile={profile} onOpenIntegrations={integrations} onSignOut={signout} onBackToOnboarding={jest.fn()} onOpenActivities={jest.fn()} onOpenCheckIn={jest.fn()} onOpenZoneProfile={jest.fn()} /></UiVersionProvider></LanguageProvider></SafeAreaProvider>);
  await view.findByRole('button', {name:'Profielmenu'});
  await fireEvent.press(view.getByRole('button', {name:'Profielmenu'}));
  await view.findByText('Alles over jouw setup');
  await fireEvent.press(view.getByRole('button', {name:destination === 'profile' ? 'Intakeprofiel' : destination === 'integrations' ? 'Integraties' : 'Veilig afmelden'}));
  expect(mockDismiss).toHaveBeenCalledTimes(1); expect(profile).not.toHaveBeenCalled(); expect(integrations).not.toHaveBeenCalled(); expect(signout).not.toHaveBeenCalled();
  await act(async () => mockFinishDismiss());
  await waitFor(() => expect(destination === 'profile' ? profile : destination === 'integrations' ? integrations : signout).toHaveBeenCalledTimes(1));
  expect(view.queryByText('Alles over jouw setup')).toBeNull();
});
