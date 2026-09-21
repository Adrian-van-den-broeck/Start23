import { render } from '@testing-library/react-native';

import type { PlanWarning } from '../api/types';
import { MoveWarningPanel } from '../components/MoveWarningPanel';

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

describe('move warnings', () => {
  test('recovery, injury, and spacing warnings are qualitative and visible', async () => {
    const screen = await render(
      <MoveWarningPanel
        onCancel={jest.fn()}
        onConfirm={jest.fn()}
        warnings={[
          warning('manual_review_required', 'server recovery'),
          warning('injured_disciplines_excluded', 'server injury'),
          warning('anti_stack_violation', 'server spacing'),
        ]}
      />,
    );

    expect(screen.getByText('Extra controle nodig')).toBeTruthy();
    expect(screen.getByText('Blessure verwerkt')).toBeTruthy();
    expect(screen.getByText('Meer herstel nodig')).toBeTruthy();
    expect(screen.queryByText(/TSS/i)).toBeNull();
  });
});
