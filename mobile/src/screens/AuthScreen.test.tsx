import { fireEvent, render, waitFor } from '@testing-library/react-native';
import { getSupabaseClient } from '../lib/supabase';
import { AuthScreen } from './AuthScreen';
jest.mock('../lib/supabase', () => ({ getSupabaseClient: jest.fn() }));
const signIn = jest.fn(); const signUp = jest.fn();
beforeEach(() => { jest.clearAllMocks(); jest.mocked(getSupabaseClient).mockReturnValue({ auth: { signInWithPassword: signIn, signUp } } as unknown as ReturnType<typeof getSupabaseClient>); });
async function fill(view: Awaited<ReturnType<typeof render>>, password = 'password123') {
  await fireEvent.changeText(view.getByLabelText('E-mailadres'), ' ATHLETE@Example.com ');
  await fireEvent.changeText(view.getByLabelText('Wachtwoord'), password);
}
test('sign-in keeps normalized credentials, secure fields and busy submission lock', async () => {
  let finish!: (result: unknown) => void;
  signIn.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const view = await render(<AuthScreen />); await fill(view);
  expect(view.getByLabelText('Wachtwoord').props.secureTextEntry).toBe(true);
  await fireEvent.press(view.getByRole('button', { name: 'Aanmelden' }));
  await fireEvent.press(view.getByRole('button', { name: 'Aanmelden' }));
  await waitFor(() => expect(signIn).toHaveBeenCalledTimes(1));
  expect(signIn).toHaveBeenCalledWith({ email: 'athlete@example.com', password: 'password123' });
  expect(view.getByRole('tab', { name: 'Registreren' })).toBeDisabled();
  finish({ data: { session: null }, error: null });
  await waitFor(() => expect(view.getByRole('button', { name: 'Aanmelden' })).toBeEnabled());
});
test('registration rejects short or mismatched passwords before auth calls', async () => {
  const view = await render(<AuthScreen />);
  await fireEvent.press(view.getByRole('tab', { name: 'Registreren' })); await fill(view, '123');
  await fireEvent.changeText(view.getByLabelText('Herhaal wachtwoord'), '123');
  await fireEvent.press(view.getByRole('button', { name: 'Account maken' }));
  await view.findByRole('alert', { name: 'Kies een wachtwoord van minimaal 6 tekens.' });
  await fireEvent.changeText(view.getByLabelText('Wachtwoord'), 'long-enough');
  await fireEvent.press(view.getByRole('button', { name: 'Account maken' }));
  await view.findByRole('alert', { name: 'De wachtwoorden zijn niet gelijk.' });
  expect(signUp).not.toHaveBeenCalled(); expect(signIn).not.toHaveBeenCalled();
});
test('server registration without session returns to sign-in with email-confirmation notice', async () => {
  signUp.mockResolvedValue({ data: { session: null }, error: null });
  const view = await render(<AuthScreen />);
  await fireEvent.press(view.getByRole('tab', { name: 'Registreren' })); await fill(view);
  await fireEvent.changeText(view.getByLabelText('Herhaal wachtwoord'), 'password123');
  await fireEvent.press(view.getByRole('button', { name: 'Account maken' }));
  await view.findByText('Je account is aangemaakt. Controleer je e-mail en meld je daarna aan.');
  expect(view.getByRole('tab', { name: 'Aanmelden' })).toBeSelected();
  expect(view.getByLabelText('Wachtwoord').props.value).toBe('');
  expect(view.queryByLabelText('Herhaal wachtwoord')).toBeNull();
});
test('auth/config errors remain errors and mode selection clears current feedback', async () => {
  jest.mocked(getSupabaseClient).mockImplementation(() => { throw new Error('Supabase configuration unavailable'); });
  const view = await render(<AuthScreen />); await fill(view);
  await fireEvent.press(view.getByRole('button', { name: 'Aanmelden' }));
  await view.findByRole('alert', { name: 'Supabase configuration unavailable' });
  await fireEvent.press(view.getByRole('tab', { name: 'Registreren' }));
  expect(view.queryByRole('alert')).toBeNull(); expect(signIn).not.toHaveBeenCalled();
});
