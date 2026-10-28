import { act, render } from '@testing-library/react-native';
import { View } from 'react-native';
import { ProfileScreen } from './ProfileScreen';
import { CalibrationScreen } from './CalibrationScreen';
import { activityOnboarding } from '../features/activities/activities.test-fixtures';

// Configure, but do not substitute, the actual client and A8 transport.
jest.mock('../api/client', () => {
  process.env.EXPO_PUBLIC_API_BASE_URL = 'https://synthetic.local';
  return jest.requireActual('../api/client');
});

test('a profile read still in flight when calibration opens is shared by the actual screens', async () => {
  const original = global.fetch;
  let resolve!: (response: Response) => void;
  const pending = new Promise<Response>(yes => { resolve = yes; });
  const response = (body: unknown) => ({ ok: true, status: 200, json: async () => body }) as Response;
  const fetchMock = jest.fn(async (url: RequestInfo | URL) => String(url).endsWith('/onboarding')
    ? pending : response({ setups: [], evaluations: [], threshold_decisions: [] }));
  global.fetch = fetchMock;
  try {
    const props = { accessToken: 'synthetic-a', onBack: jest.fn(), onSignOut: jest.fn() };
    const profile = <ProfileScreen {...props} onOpenTests={jest.fn()} onOpenPioneerAccess={jest.fn()} />;
    const view = await render(profile);
    await view.rerender(<View>{profile}<CalibrationScreen {...props} /></View>);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/onboarding'))).toHaveLength(1);
    await act(async () => { resolve(response({ ...activityOnboarding, profile: {
      ...activityOnboarding.profile!, first_name: 'Synthetic', last_name: '', date_of_birth: '1990-05-20',
      resting_heart_rate_bpm: 52, revision: 4, identifying_revision: 2, physiology_revision: 2,
    } })); });
    expect(await view.findByDisplayValue('Synthetic')).toBeTruthy();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/onboarding'))).toHaveLength(1);
    await view.unmount();
  } finally { global.fetch = original; }
});
