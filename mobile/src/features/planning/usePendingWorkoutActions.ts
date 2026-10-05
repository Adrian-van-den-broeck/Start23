import * as Haptics from 'expo-haptics';
import { useCallback, useRef, useState, type MutableRefObject } from 'react';

import { editPendingWorkout, getPendingWorkoutAlternatives } from '../../api/client';
import type { PendingWorkoutAlternatives, WeeklyPlan } from '../../api/types';

type PendingEditor = { options: PendingWorkoutAlternatives | null; loading: boolean; };

// One slot map in the flow owner. Carousel position and gestures stay in V1.
export function usePendingWorkoutActions(
  accessToken: string,
  plan: WeeklyPlan | null,
  onEdited: (updated: WeeklyPlan) => void,
  onError: (message: string) => void,
  mutationLock: MutableRefObject<boolean>,
) {
  const [editors, setEditors] = useState<Record<string, PendingEditor>>({});
  // A released V1 editor used to lose its local state. Late local updates
  // must not populate a newly mounted editor with the same workout ID.
  const lifetimes = useRef<Record<string, number>>({});
  const currentPlan = useRef(plan);
  currentPlan.current = plan;
  const requests = useRef<Record<string, { lifetime: number; plan: WeeklyPlan; }>>({});
  const loadedFor = useRef<Record<string, WeeklyPlan>>({});
  const planId = plan?.id;
  const revision = plan?.revision;
  const setLoading = useCallback((workoutId: string, loading: boolean, lifetime: number) => {
    if ((lifetimes.current[workoutId] ?? 0) !== lifetime) return;
    setEditors((current) => ({
      ...current,
      [workoutId]: { options: current[workoutId]?.options ?? null, loading },
    }));
  }, []);

  const load = useCallback(async (workoutId: string, onLoaded: () => void = () => undefined) => {
    if (!planId || revision === undefined || !plan || plan.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending' || currentPlan.current !== plan || mutationLock.current) return false;
    const lifetime = lifetimes.current[workoutId] ?? 0;
    if (requests.current[workoutId]?.lifetime === lifetime && requests.current[workoutId]?.plan === plan) return false;
    const request = { lifetime, plan };
    requests.current[workoutId] = request;
    setLoading(workoutId, true, lifetime);
    onError('');
    try {
      const result = await getPendingWorkoutAlternatives(accessToken, planId, workoutId, revision);
      if ((lifetimes.current[workoutId] ?? 0) === lifetime && currentPlan.current === plan && requests.current[workoutId] === request) {
        loadedFor.current[workoutId] = plan;
        setEditors((current) => ({ ...current, [workoutId]: { options: result, loading: true } }));
        onLoaded();
        return true;
      }
      return false;
    } catch (caught) {
      if ((lifetimes.current[workoutId] ?? 0) === lifetime && currentPlan.current === plan) onError(caught instanceof Error ? caught.message : 'De vervangingen konden niet worden geladen.');
      return false;
    } finally {
      if (requests.current[workoutId] === request) {
        delete requests.current[workoutId];
        setLoading(workoutId, false, lifetime);
      }
    }
  }, [accessToken, onError, plan, planId, revision, setLoading, mutationLock]);

  const release = useCallback((workoutId: string) => {
    lifetimes.current[workoutId] = (lifetimes.current[workoutId] ?? 0) + 1;
    delete loadedFor.current[workoutId];
    setEditors((current) => {
      const next = { ...current };
      delete next[workoutId];
      return next;
    });
  }, []);

  const apply = async (workoutId: string, replacementTemplateId: string | null) => {
    const options = editors[workoutId]?.options;
    if (!options || !planId || !plan || currentPlan.current !== plan || loadedFor.current[workoutId] !== plan || mutationLock.current || Object.keys(requests.current).length > 0 || plan.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending') return false;
    if (replacementTemplateId === null ? options.can_remove !== true : !options.alternatives.some((item) => item.id === replacementTemplateId)) return false;
    mutationLock.current = true;
    const lifetime = lifetimes.current[workoutId] ?? 0;
    setLoading(workoutId, true, lifetime);
    onError('');
    try {
      const result = await editPendingWorkout(accessToken, planId, workoutId, {
        expected_revision: options.revision,
        expected_proposal_id: options.proposal_id,
        replacement_template_id: replacementTemplateId,
      });
      if (currentPlan.current !== plan) return false;
      onEdited(result.plan);
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
      return true;
    } catch (caught) {
      if (currentPlan.current === plan) onError(caught instanceof Error ? caught.message : 'De wijziging kon niet als nieuw voorstel worden opgeslagen.');
      return false;
    } finally {
      mutationLock.current = false;
      setLoading(workoutId, false, lifetime);
    }
  };

  return { editors, load, apply, release, isLoading: () => Object.keys(requests.current).length > 0 };
}
