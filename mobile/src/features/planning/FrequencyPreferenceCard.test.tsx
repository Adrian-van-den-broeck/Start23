import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import { ApiRequestError, getFrequencyPreferences, saveFrequencyPreferences } from '../../api/client';
import type { FrequencyPreferences } from '../../api/types';
import { FrequencyPreferenceCard } from './FrequencyPreferenceCard';
import { FrequencySummary } from './FrequencySummary';
import { LanguageProvider } from '../../i18n/LanguageProvider';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'nl') }));
jest.mock('../../api/client', () => ({ ...jest.requireActual('../../api/client'), getFrequencyPreferences: jest.fn(), saveFrequencyPreferences: jest.fn() }));
const read = jest.mocked(getFrequencyPreferences);
const write = jest.mocked(saveFrequencyPreferences);
const empty: FrequencyPreferences = { revision: 0, operation_id: null, confirmed_at: null, recorded_at: null, reconfirmation_required: [], preferences: { run: null, bike: null, swim: null } };
const card = (token = 'owner-a', key = 'a') => <LanguageProvider><FrequencyPreferenceCard key={key} accessToken={token} sports={['run', 'bike', 'swim']} /></LanguageProvider>;

beforeEach(() => {
  jest.clearAllMocks(); read.mockResolvedValue(structuredClone(empty));
  write.mockImplementation(async (_token, input) => ({ ...empty, ...input, revision: input.expected_revision + 1, confirmed_at: '2026-11-13T12:00:00Z', recorded_at: '2026-11-13T12:00:00Z' }));
});

test('optional card starts with no preference and never saves on mount or skip', async () => {
  const view = await render(card());
  await view.findByText(/Opgeslagen voorkeur \(revisie 0\)/);
  expect(view.getByLabelText('Hardlopen: gewenste sessies').props.value).toBe('');
  expect(view.getByText('Gewenste sessies per week (optioneel)')).toBeTruthy();
  expect(write).not.toHaveBeenCalled();
});

test('zero, a saved soft request and null are distinct, with exact CAS and operation ID', async () => {
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '0');
  await fireEvent.changeText(view.getByLabelText('Fietsen: gewenste sessies'), '8');
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  await view.findByText(/Voorkeur opgeslagen/);
  expect(write).toHaveBeenCalledWith('owner-a', { expected_revision: 0, operation_id: expect.any(String), preferences: { run: 0, bike: 8, swim: null } });
  expect(view.getByText(/Hardlopen 0.*Fietsen 8.*Zwemmen geen voorkeur/)).toBeTruthy();
});

test.each(['-1','1.5','25','abc'])('invalid count %s does not submit', async value => {
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), value);
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  expect(view.getByText(/Vul een geheel aantal/)).toBeTruthy(); expect(write).not.toHaveBeenCalled();
});

test('technical total is validated without turning it into a training maximum', async () => {
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '24');
  await fireEvent.changeText(view.getByLabelText('Fietsen: gewenste sessies'), '1');
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  expect(view.getByText(/technisch maximaal 24/)).toBeTruthy(); expect(write).not.toHaveBeenCalled();
});

test('a saved preference can be revoked by clearing it', async () => {
  read.mockResolvedValueOnce({ ...empty, revision: 3, preferences: { run: 2, bike: null, swim: null } });
  const view = await render(card()); await view.findByText(/revisie 3/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '');
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  await view.findByText(/Voorkeur opgeslagen/);
  expect(write.mock.calls[0][1]).toMatchObject({ expected_revision: 3, preferences: { run: null, bike: null, swim: null } });
});

test('unknown acknowledgement retries the exact logical save and freezes editing', async () => {
  write.mockRejectedValueOnce(new ApiRequestError('unknown', null, 'network_unavailable', 'unknown', 'PUT'));
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '2');
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  await view.findByText(/Opslaan kon niet worden bevestigd/);
  expect(view.getByLabelText('Hardlopen: gewenste sessies').props.editable).toBe(false);
  await fireEvent.press(view.getByRole('button', { name: 'Dezelfde voorkeur opnieuw opslaan' }));
  await view.findByText(/Voorkeur opgeslagen/);
  expect(write.mock.calls[0]).toEqual(write.mock.calls[1]);
});

test('stale save preserves draft and requires an explicit authoritative read', async () => {
  write.mockRejectedValueOnce(new ApiRequestError('stale', 409, 'conflict'));
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '2');
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  await view.findByText(/Je voorkeur is intussen gewijzigd/);
  expect(view.getByLabelText('Hardlopen: gewenste sessies').props.value).toBe('2');
  expect(read).toHaveBeenCalledTimes(1);
  read.mockResolvedValueOnce({ ...empty, revision: 4, preferences: { run: 1, bike: null, swim: null } });
  await fireEvent.press(view.getByRole('button', { name: 'Opgeslagen voorkeur ophalen' }));
  await view.findByText(/revisie 4/);
});

test('read failure cannot hydrate a default permission and can be retried', async () => {
  read.mockRejectedValueOnce(new Error('private internal failure'));
  const view = await render(card()); await view.findByText(/Je voorkeur kon niet worden opgehaald/);
  expect(view.queryByRole('button', { name: 'Voorkeur opslaan' })).toBeNull();
  expect(view.queryByText('private internal failure')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Opgeslagen voorkeur ophalen' }));
  await view.findByText(/Opgeslagen voorkeur \(revisie 0\)/);
});

test('token rotation preserves input and uses the new token', async () => {
  const view = await render(card()); await view.findByText(/Opgeslagen voorkeur/);
  await fireEvent.changeText(view.getByLabelText('Hardlopen: gewenste sessies'), '3');
  await view.rerender(card('new-owner-a-token'));
  await fireEvent.press(view.getByRole('button', { name: 'Voorkeur opslaan' }));
  await waitFor(() => expect(write).toHaveBeenCalledWith('new-owner-a-token', expect.objectContaining({ preferences: { run: 3, bike: null, swim: null } })));
  expect(read).toHaveBeenCalledTimes(1);
});

test('late account A read cannot populate account B', async () => {
  let finish!: (value: FrequencyPreferences) => void;
  read.mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
  const view = await render(card());
  await view.rerender(card('owner-b', 'b'));
  await view.findByText(/revisie 0/);
  await act(async () => { finish({ ...empty, revision: 9, preferences: { run: 9, bike: null, swim: null } }); });
  expect(view.queryByText(/revisie 9/)).toBeNull();
});

test('reconfirmation notice retains the preference after interruption', async () => {
  read.mockResolvedValueOnce({ ...empty, revision: 2, preferences: { run: 2, bike: null, swim: null }, reconfirmation_required: ['run'] });
  const view = await render(card()); await view.findByText(/Controleer je voorkeur na je onderbreking/);
  expect(view.getByLabelText('Hardlopen: gewenste sessies').props.value).toBe('2');
  expect(write).not.toHaveBeenCalled();
});

test('requested and proposed counts include a qualitative partial explanation', async () => {
  const view = await render(<LanguageProvider><FrequencySummary rows={[{ sport: 'run', requested: 2, proposed: 1 }, { sport: 'bike', requested: 0, proposed: 0 }]} /></LanguageProvider>);
  expect(view.getByText('Hardlopen: 2 gevraagd · 1 voorgesteld')).toBeTruthy();
  expect(view.getByText(/minder sessies.*huidige trainingsvoorwaarden/)).toBeTruthy();
});
