import { Redirect } from 'expo-router';
import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from 'react';
import { View } from 'react-native';
import { getOnboarding } from '../api/client';
import type { OnboardingState } from '../api/types';
import { ScreenState } from '../components/ScreenState';
import { PlanningFlowProvider } from '../features/planning/PlanningFlowProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { Button } from '../ui-v2/primitives/Button';
import { PlanningPresentationProvider } from './PlanningPresentationProvider';

type Gate = 'idle' | 'loading' | 'ready' | 'onboarding' | 'failed';
const GateContext = createContext<{ gate: Gate; retry: () => void; requestTraining: () => void; } | null>(null);

// Retained above the authenticated Stack after first ready training entry.
// The authenticated layout keys this host by athlete identity, never by token.
export function TrainingFlowHost({ accessToken, athleteIdentity, children }: PropsWithChildren<{
  accessToken: string; athleteIdentity: string;
}>) {
  const [gate, setGate] = useState<Gate>('idle');
  const [readySnapshot, setReadySnapshot] = useState<OnboardingState | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [trainingRequested, setTrainingRequested] = useState(false);
  const requestTraining = useCallback(() => {
    setTrainingRequested(true);
    setAttempt((value) => value + 1);
  }, []);
  useEffect(() => {
    if (!trainingRequested || gate === 'ready') return;
    let current = true;
    setGate('loading');
    getOnboarding(accessToken).then((state) => {
      if (current) {
        if (state.current_step === 'completed') setReadySnapshot(state);
        setGate(state.current_step === 'completed' ? 'ready' : 'onboarding');
      }
    }).catch(() => { if (current) setGate('failed'); });
    return () => { current = false; };
    // A ready host survives navigation and token refresh. Failed reads retry explicitly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trainingRequested, accessToken, attempt]);

  return <GateContext.Provider value={{ gate, requestTraining, retry: () => setAttempt((value) => value + 1) }}>
    {gate === 'ready' ? <PlanningFlowProvider accessToken={accessToken} athleteIdentity={athleteIdentity} initialOnboarding={readySnapshot ?? undefined}>
      <PlanningPresentationProvider>{children}</PlanningPresentationProvider>
    </PlanningFlowProvider> : children}
  </GateContext.Provider>;
}

// Keep the authenticated Stack mounted during readiness: replacing it with a
// spinner would erase task -> root navigation before the gate could finish.
export function TrainingReadiness() {
  const { t } = useLanguage();
  const value = useContext(GateContext);
  const requestTraining = value?.requestTraining;
  useEffect(() => { requestTraining?.(); }, [requestTraining]);
  if (!value) throw new Error('Training readiness requires the authenticated host');
  const { gate, retry } = value;
  if (gate === 'onboarding') return <Redirect href="/onboarding" />;
  if (gate === 'failed') return <View style={{ flex: 1 }}>
    <ScreenState title={t('shell.readinessFailed')} />
    <Button label={t('shell.retry')} onPress={retry} />
  </View>;
  return <ScreenState loading title={t('shell.readinessLoading')} />;
}
