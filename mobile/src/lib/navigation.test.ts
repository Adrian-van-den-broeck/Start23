import {
  backToPreviousOrPlanning,
  createDeferredDismissAction,
} from './navigation';

describe('authenticated navigation regression contracts', () => {
  test('profile navigation waits for the native sheet dismissal', () => {
    const coordinator = createDeferredDismissAction();
    const dismiss = jest.fn();
    const navigate = jest.fn();

    coordinator.request(navigate, dismiss);

    expect(dismiss).toHaveBeenCalledTimes(1);
    expect(navigate).not.toHaveBeenCalled();

    coordinator.completeDismiss();
    coordinator.completeDismiss();

    expect(navigate).toHaveBeenCalledTimes(1);
  });

  test('normal back navigation preserves the existing stack', () => {
    const router = {
      back: jest.fn(),
      canGoBack: jest.fn(() => true),
      replace: jest.fn(),
    };

    backToPreviousOrPlanning(router);

    expect(router.back).toHaveBeenCalledTimes(1);
    expect(router.replace).not.toHaveBeenCalled();
  });

  test('a direct Tests or Profile route restores to planning without history', () => {
    const router = {
      back: jest.fn(),
      canGoBack: jest.fn(() => false),
      replace: jest.fn(),
    };

    backToPreviousOrPlanning(router);

    expect(router.back).not.toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith('/planning');
  });
});
