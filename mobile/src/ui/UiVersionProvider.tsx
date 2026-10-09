import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

import { effectiveUiVersion, initialUiVersion, type UiVersion } from './uiVersion';

type UiVersionContextValue = {
  requested: UiVersion;
  setRequested: (version: UiVersion) => void;
  effectiveVersion: (slice: string) => UiVersion;
};

const UiVersionContext = createContext<UiVersionContextValue | null>(null);

export function UiVersionProvider({ children }: { children: ReactNode }) {
  const [requested, setRequested] = useState(() =>
    initialUiVersion(process.env.EXPO_PUBLIC_UI_VERSION),
  );
  const value = useMemo<UiVersionContextValue>(() => ({
    requested: initialUiVersion(requested),
    setRequested: (version) => setRequested(initialUiVersion(version)),
    effectiveVersion: (slice) => effectiveUiVersion(requested, slice),
  }), [requested]);
  return <UiVersionContext.Provider value={value}>{children}</UiVersionContext.Provider>;
}

export function useUiVersion(): UiVersionContextValue {
  const value = useContext(UiVersionContext);
  if (!value) throw new Error('useUiVersion must be used within UiVersionProvider.');
  return value;
}
