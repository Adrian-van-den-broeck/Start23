type BackStackRouter = {
  back: () => void;
  canGoBack: () => boolean;
  replace: (path: '/planning') => void;
};

export function backToPreviousOrPlanning(router: BackStackRouter): void {
  if (router.canGoBack()) {
    router.back();
  } else {
    router.replace('/planning');
  }
}

export type DeferredDismissAction = {
  completeDismiss: () => void;
  request: (action: () => void, dismiss: () => void) => void;
};

export function createDeferredDismissAction(): DeferredDismissAction {
  let pending: (() => void) | null = null;
  return {
    request(action, dismiss) {
      pending = action;
      dismiss();
    },
    completeDismiss() {
      const action = pending;
      pending = null;
      action?.();
    },
  };
}
