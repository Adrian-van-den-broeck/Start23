import * as Haptics from 'expo-haptics';
import { useCallback, useRef, useState } from 'react';

import { editPendingWorkout, getPendingWorkoutAlternatives } from '../../api/client';
import type { PendingWorkoutAlternatives, WeeklyPlan } from '../../api/types';

type PendingEditor = { options: PendingWorkoutAlternatives | null; loading: boolean; };

// One slot map in the flow owner. Carousel position and gestures stay in V1.
export function usePendingWorkoutActions(
  accessToken: string,
  plan: WeeklyPlan | null,
  onEdited: (updated: WeeklyPlan) => void,
  onError: (message: string) => void,
) {
  const [editors, setEditors] = useState<Record<string, PendingEditor>>({});
  // A released V1 editor used to lose its local state. Late local updates
  // must not populate a newly mounted editor with the same workout ID.
  const lifetimes = useRef<Record<string, number>>({});
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
    if (!planId || revision === undefined) return false;
    const lifetime = lifetimes.current[workoutId] ?? 0;
    setLoading(workoutId, true, lifetime);
    onError('');
    try {
      const result = await getPendingWorkoutAlternatives(accessToken, planId, workoutId, revision);
      if ((lifetimes.current[workoutId] ?? 0) === lifetime) {
        setEditors((current) => ({ ...current, [workoutId]: { options: result, loading: true } }));
      }
      onLoaded();
      return true;
    } catch (caught) {
      onError(caught instanceof Error ? caught.message : 'De vervangingen konden niet worden geladen.');
      return false;
    } finally {
      setLoading(workoutId, false, lifetime);
    }
  }, [accessToken, onError, planId, revision, setLoading]);

  const release = useCallback((workoutId: string) => {
    lifetimes.current[workoutId] = (lifetimes.current[workoutId] ?? 0) + 1;
    setEditors((current) => {
      const next = { ...current };
      delete next[workoutId];
      return next;
    });
  }, []);

  const apply = async (workoutId: string, replacementTemplateId: string | null) => {
    const options = editors[workoutId]?.options;
    if (!options || !planId) return;
    const lifetime = lifetimes.current[workoutId] ?? 0;
    setLoading(workoutId, true, lifetime);
    onError('');
    try {
      const result = await editPendingWorkout(accessToken, planId, workoutId, {
        expected_revision: options.revision,
        expected_proposal_id: options.proposal_id,
        replacement_template_id: replacementTemplateId,
      });
      onEdited(result.plan);
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
    } catch (caught) {
      onError(caught instanceof Error ? caught.message : 'De wijziging kon niet als nieuw voorstel worden opgeslagen.');
    } finally {
      setLoading(workoutId, false, lifetime);
    }
  };

  return { editors, load, apply, release };
}
