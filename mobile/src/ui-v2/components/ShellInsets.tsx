import { createContext, useContext, type PropsWithChildren } from 'react';
import { SafeAreaView, type SafeAreaViewProps } from 'react-native-safe-area-context';

// Presentation inset ownership only; retained flow/data owners stay above it.
const Context = createContext({ top: false, bottom: false });
export function ShellInsets({ top, bottom, children }: PropsWithChildren<{ top?: boolean; bottom?: boolean }>) {
  const parent = useContext(Context);
  return <Context.Provider value={{ top: top ?? parent.top, bottom: bottom ?? parent.bottom }}>{children}</Context.Provider>;
}
export function ShellSafeArea({ independent = false, ...props }: SafeAreaViewProps & { independent?: boolean }) {
  const owned = useContext(Context);
  return <SafeAreaView {...props} edges={independent ? ['bottom'] : [
    ...(!owned.top ? ['top' as const] : []), ...(!owned.bottom ? ['bottom' as const] : []),
  ]} />;
}
