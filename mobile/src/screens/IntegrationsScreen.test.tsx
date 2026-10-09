import { Alert, Linking } from 'react-native';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import * as api from '../api/client';
import type { PolarConnection, PolarImportRun } from '../api/types';
import fixtures from '../../../docs/ui/evidence/final-visual-batch-12/public-fixtures.json';
import { IntegrationsScreen } from './IntegrationsScreen';
jest.mock('../api/client', () => ({ disconnectPolar: jest.fn(), getPolarConnection: jest.fn(), importPolarHistory: jest.fn(), listPolarImports: jest.fn(), retryPolarImport: jest.fn(), startPolarOAuth: jest.fn() }));
beforeEach(() => { jest.clearAllMocks(); jest.mocked(api.getPolarConnection).mockResolvedValue(null); jest.mocked(api.listPolarImports).mockResolvedValue([]); });
afterEach(() => jest.restoreAllMocks());
async function surface() { const back = jest.fn(); const activities = jest.fn(); const signOut = jest.fn(async () => undefined); const view = await render(<IntegrationsScreen accessToken="athlete-token" onBack={back} onOpenActivities={activities} onSignOut={signOut} />); await view.findByRole('button', { name: 'Status vernieuwen', disabled: false }); return { view, back, activities, signOut }; }
test('unlinked and empty imports retain supported destinations and OAuth URL action', async () => {
  jest.mocked(api.startPolarOAuth).mockResolvedValue({ provider: 'polar', authorization_url: 'https://example.test/oauth', expires_at: '2026-10-09T09:00:00Z' });
  const openURL = jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined);
  const { view, back, activities, signOut } = await surface();
  expect(view.getByText('Niet gekoppeld')).toBeTruthy(); expect(view.getByText('Nog geen imports.')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Polar koppelen' }));
  await waitFor(() => expect(openURL).toHaveBeenCalledWith('https://example.test/oauth'));
  await fireEvent.press(view.getByRole('button', { name: 'Geïmporteerde activiteiten bekijken' }));
  await fireEvent.press(view.getByRole('button', { name: 'Weekplanning' }));
  await fireEvent.press(view.getByRole('button', { name: 'Afmelden' }));
  expect(activities).toHaveBeenCalledTimes(1); expect(back).toHaveBeenCalledTimes(1); expect(signOut).toHaveBeenCalledTimes(1);
});
test('connected history uses exact supported days and idempotency key; retry eligibility remains bounded', async () => {
  jest.mocked(api.getPolarConnection).mockResolvedValue(fixtures.connection as PolarConnection);
  jest.mocked(api.listPolarImports).mockResolvedValue(fixtures.imports as PolarImportRun[]);
  const { view } = await surface();
  expect(view.getByRole('radio', { name: '14 dagen' })).toBeChecked();
  await fireEvent.press(view.getByRole('radio', { name: '30 dagen' }));
  expect(api.importPolarHistory).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Import starten' }));
  await waitFor(() => expect(api.importPolarHistory).toHaveBeenCalledWith('athlete-token', expect.stringMatching(/^[a-f0-9-]{36}$/), 30));
  expect(view.getAllByRole('button', { name: 'Nu opnieuw proberen' })).toHaveLength(1);
  await fireEvent.press(view.getByRole('button', { name: 'Nu opnieuw proberen' }));
  await waitFor(() => expect(api.retryPolarImport).toHaveBeenCalledWith('athlete-token', 'inert-import-retry'));
});
test('disconnect stays behind the existing explicit native confirmation', async () => {
  jest.mocked(api.getPolarConnection).mockResolvedValue(fixtures.connection as PolarConnection);
  const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
  const { view } = await surface(); await fireEvent.press(view.getByRole('button', { name: 'Ontkoppelen' }));
  expect(api.disconnectPolar).not.toHaveBeenCalled();
  const actions = alert.mock.calls[0][2]!;
  expect(alert.mock.calls[0][1]).toContain('niet automatisch gewist');
  await act(async () => { actions.find(item => item.style === 'destructive')!.onPress!(); });
  await waitFor(() => expect(api.disconnectPolar).toHaveBeenCalledWith('athlete-token'));
});
test('reconnect and real provider failure preserve status, error and refresh', async () => {
  jest.mocked(api.getPolarConnection).mockResolvedValue({ ...fixtures.connection, status: 'reconnect_required' } as PolarConnection);
  jest.mocked(api.startPolarOAuth).mockRejectedValue(new Error('De Wombo-server is tijdelijk niet beschikbaar. Probeer het zo opnieuw.'));
  const { view } = await surface();
  await fireEvent.press(view.getByRole('button', { name: 'Opnieuw toestemming geven' }));
  await view.findByRole('alert');
  expect(view.getByText('Opnieuw koppelen')).toBeTruthy();
  expect(view.getByRole('button', { name: 'Status vernieuwen' })).toBeEnabled();
});
