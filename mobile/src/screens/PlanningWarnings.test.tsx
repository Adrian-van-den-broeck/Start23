import { render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';

import type { PlanWarning } from '../api/types';
import { MoveWarningPanel } from '../components/MoveWarningPanel';
import { LanguageProvider } from '../i18n/LanguageProvider';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));

function warning(code: string, message: string): PlanWarning {
  return {
    id: code,
    rule_id: 'test-rule',
    code,
    severity: 'warning',
    message,
    planned_workout_id: null,
  };
}

function panel() {
  return (
    <LanguageProvider>
      <MoveWarningPanel
        onCancel={jest.fn()}
        onConfirm={jest.fn()}
        warnings={[
          warning('manual_review_required', 'server recovery'),
          warning('injured_disciplines_excluded', 'server injury'),
          warning('anti_stack_violation', 'server spacing'),
          warning('unknown_server_code', 'Server-provided message'),
        ]}
      />
    </LanguageProvider>
  );
}

describe('move warnings', () => {
  beforeEach(() => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  });

  test('recovery, injury, and spacing warnings are qualitative and visible', async () => {
    const screen = await render(panel());

    expect(screen.getByText('Extra controle nodig')).toBeTruthy();
    expect(screen.getByText('Blessure verwerkt')).toBeTruthy();
    expect(screen.getByText('Meer herstel nodig')).toBeTruthy();
    expect(screen.getByText('Controleer deze verplaatsing')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Toch verplaatsen' })).toBeTruthy();
    expect(screen.queryByText(/TSS/i)).toBeNull();
  });

  test('English shows translated client copy and keeps unknown server messages as sent', async () => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en');
    const screen = await render(panel());
    expect(await screen.findByText('Review this move')).toBeTruthy();
    expect(screen.getByText('Extra review needed')).toBeTruthy();
    expect(screen.getByText('Injury taken into account')).toBeTruthy();
    expect(screen.getByText('More recovery needed')).toBeTruthy();
    expect(screen.getByText('Attention point')).toBeTruthy();
    expect(screen.getByText('Server-provided message')).toBeTruthy();
    expect(screen.getByText(/The server stays authoritative/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Move anyway' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeTruthy();
    expect(screen.queryByText('Meer herstel nodig')).toBeNull();
    expect(screen.queryByText(/TSS/i)).toBeNull();
  });
});
