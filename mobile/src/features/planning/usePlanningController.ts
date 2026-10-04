import * as SecureStore from 'expo-secure-store';
import * as Haptics from 'expo-haptics';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Platform } from 'react-native';

import {
  approvePlanProposal,
  createSwipeWeekDraft,
  getOnboarding,
  getSwipeWeekDraft,
  getWeeklyPlan,
  markGoalAchieved,
  movePlannedWorkout,
  placeSwipeWeekWorkout,
  rejectPlanProposal,
  submitSwipeWeekDraft,
  transitionSwipeWeekDraft,
  validatePlanLayout,
} from '../../api/client';
import type { Discipline, PlanWarning, PlannedWorkout, PrimaryRaceGoal, SwipeWeekDraft, WeeklyPlan } from '../../api/types';
import { isDateInWeek } from '../../components/WeekSchedule';
import { availableDatesFor, dayOffsetsFor, isoDate, nextMonday } from './planningDates';
import { latestPlanIdKey, latestSwipeDraftIdKey, rememberPlanId, rememberSwipeDraftId } from './planningResume';
import { usePendingWorkoutActions } from './usePendingWorkoutActions';

export type PlanningView = 'plan' | 'deck' | 'calendar';

// Called once by PlanningFlowProvider; presentations consume its context.
export function usePlanningController(accessToken: string) {
  const [view, setView] = useState<PlanningView>('plan');
  const [weekStart, setWeekStart] = useState(nextMonday);
  const [reusePreviousWeek, setReusePreviousWeek] = useState(false);
  const [selectedDays, setSelectedDays] = useState<Set<number>>(
    () => new Set([0, 2, 5]),
  );
  const [injuries, setInjuries] = useState<Set<Discipline>>(() => new Set());
  const [crossTrainingOptIns, setCrossTrainingOptIns] = useState<Set<Discipline>>(
    () => new Set(),
  );
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const [swipeDraft, setSwipeDraft] = useState<SwipeWeekDraft | null>(null);
  const [pendingMove, setPendingMove] = useState<{
    scheduledDate: string;
    warnings: PlanWarning[];
    workout: PlannedWorkout;
  } | null>(null);
  const [primaryGoal, setPrimaryGoal] = useState<PrimaryRaceGoal | null>(null);
  const [maintenanceMarked, setMaintenanceMarked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const availableDates = useMemo(
    () => availableDatesFor(weekStart, selectedDays),
    [selectedDays, weekStart],
  );

  useEffect(() => {
    if (Platform.OS === 'web') return;
    let mounted = true;
    SecureStore.getItemAsync(latestSwipeDraftIdKey)
      .then(async (draftId) => {
        if (!draftId) return false;
        try {
          const restored = await getSwipeWeekDraft(accessToken, draftId);
          if (restored.state === 'submitted' && restored.plan_id) {
            const submittedPlan = await getWeeklyPlan(
              accessToken,
              restored.plan_id,
            );
            await Promise.all([
              rememberPlanId(submittedPlan.id),
              rememberSwipeDraftId(null),
            ]);
            if (mounted) {
              setPlan(submittedPlan);
              setWeekStart(submittedPlan.week_start);
              setView('plan');
            }
            return true;
          }
          if (mounted) {
            setSwipeDraft(restored);
            setCrossTrainingOptIns(new Set(restored.cross_training_opt_ins));
            setWeekStart(restored.week_start);
            setReusePreviousWeek(
              restored.availability_source === 'previous_week',
            );
            setSelectedDays(
              dayOffsetsFor(restored.week_start, restored.available_dates),
            );
            setView('deck');
          }
          return true;
        } catch {
          await rememberSwipeDraftId(null);
          return false;
        }
      })
      .then(async (draftRestored) => {
        if (draftRestored) return;
        const planId = await SecureStore.getItemAsync(latestPlanIdKey);
        if (!planId) return;
        try {
          const restored = await getWeeklyPlan(accessToken, planId);
          if (mounted) {
            setPlan(restored);
            setWeekStart(restored.week_start);
            setReusePreviousWeek(
              restored.availability_source === 'previous_week',
            );
            setSelectedDays(
              dayOffsetsFor(restored.week_start, restored.available_dates),
            );
            setInjuries(new Set(restored.confirmed_injuries));
          }
        } catch {
          await rememberPlanId(null);
        }
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  useEffect(() => {
    getOnboarding(accessToken)
      .then((state) => setPrimaryGoal(state.primary_goal))
      .catch(() => undefined);
  }, [accessToken]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De planningsactie is niet gelukt.',
      );
    } finally {
      setBusy(false);
    }
  };

  const toggleDay = (day: number) => {
    setReusePreviousWeek(false);
    setSelectedDays((current) => {
      const next = new Set(current);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  };

  const toggleInjury = (discipline: Discipline) => {
    setInjuries((current) => {
      const next = new Set(current);
      if (next.has(discipline)) next.delete(discipline);
      else next.add(discipline);
      return next;
    });
    setCrossTrainingOptIns((current) => {
      const next = new Set(current);
      next.delete(discipline);
      return next;
    });
  };

  const toggleCrossTraining = (discipline: Discipline) => {
    setCrossTrainingOptIns((current) => {
      const next = new Set(current);
      if (next.has(discipline)) next.delete(discipline);
      else next.add(discipline);
      return next;
    });
  };

  const generate = () =>
    run(async () => {
      const dates = availableDatesFor(weekStart, selectedDays);
      if (!reusePreviousWeek && dates.length === 0) {
        throw new Error('Kies minstens één beschikbare trainingsdag.');
      }
      const boundPlan = plan?.revision_state === 'active' ? plan : null;
      const result = await createSwipeWeekDraft(accessToken, {
        week_start: weekStart,
        ...(reusePreviousWeek
          ? { reuse_previous_week: true }
          : { available_dates: dates }),
        confirmed_injuries: [...injuries],
        cross_training_opt_ins: [...crossTrainingOptIns],
        ...(boundPlan
          ? {
            plan_id: boundPlan.id,
            expected_base_revision: boundPlan.active_revision ?? 0,
          }
          : {}),
      });
      await rememberSwipeDraftId(result.id);
      setSwipeDraft(result);
      setView('deck');
    });

  const approve = () => {
    if (!plan?.proposal) return;
    void run(async () => {
      await approvePlanProposal(
        accessToken,
        plan.proposal!.id,
        plan.proposal!.base_plan_revision ?? 0,
      );
      setPlan(await getWeeklyPlan(accessToken, plan.id));
    });
  };

  const reject = () => {
    if (!plan?.proposal) return;
    void run(async () => {
      await rejectPlanProposal(accessToken, plan.proposal!.id);
      setPlan(await getWeeklyPlan(accessToken, plan.id, plan.revision));
    });
  };

  const openDeck = () => {
    setView('deck');
  };

  const transitionDraft = useCallback(
    (action: 'accept' | 'pass' | 'undo' | 'reset_passed') => {
      if (!swipeDraft) return;
      const candidateId = swipeDraft.current_candidate?.id;
      const candidateOccurrenceId = swipeDraft.current_candidate?.occurrence_id;
      if ((action === 'accept' || action === 'pass') &&
        (!candidateId || !candidateOccurrenceId)) return;
      void run(async () => {
        const updated = await transitionSwipeWeekDraft(
          accessToken,
          swipeDraft.id,
          {
            expected_revision: swipeDraft.revision,
            action,
            ...(candidateId && (action === 'accept' || action === 'pass')
              ? {
                candidate_template_id: candidateId,
                candidate_occurrence_id: candidateOccurrenceId,
              }
              : {}),
          },
        );
        setSwipeDraft(updated);
        void Haptics.selectionAsync().catch(() => undefined);
      });
    },
    [accessToken, swipeDraft],
  );

  const placeDraftWorkout = (templateId: string, scheduledDate: string) => {
    if (!swipeDraft) return;
    void run(async () => {
      const updated = await placeSwipeWeekWorkout(
        accessToken,
        swipeDraft.id,
        templateId,
        swipeDraft.revision,
        scheduledDate,
      );
      setSwipeDraft(updated);
    });
  };

  const submitDraft = (placementMode: 'automatic' | 'manual') => {
    if (!swipeDraft) return;
    void run(async () => {
      const result = await submitSwipeWeekDraft(
        accessToken,
        swipeDraft.id,
        swipeDraft.revision,
        placementMode,
      );
      await Promise.all([
        rememberPlanId(result.plan.id),
        rememberSwipeDraftId(null),
      ]);
      setSwipeDraft(null);
      setPlan(result.plan);
      setView('plan');
      void Haptics.notificationAsync(
        Haptics.NotificationFeedbackType.Success,
      ).catch(() => undefined);
    });
  };

  const applyWorkoutMove = async (
    workout: PlannedWorkout,
    scheduledDate: string,
  ) => {
    if (!plan?.active_revision) return;
    const updated = await movePlannedWorkout(
      accessToken,
      workout.id,
      plan.active_revision,
      scheduledDate,
    );
    setPlan(updated);
    setPendingMove(null);
    void Haptics.notificationAsync(
      Haptics.NotificationFeedbackType.Success,
    ).catch(() => undefined);
  };

  const requestWorkoutMove = (
    workout: PlannedWorkout,
    scheduledDate: string,
  ) => {
    if (!plan?.active_revision) return;
    if (!isDateInWeek(scheduledDate, plan.week_start)) {
      setError('Gebruik een geldige datum binnen deze planweek (JJJJ-MM-DD).');
      return;
    }
    void run(async () => {
      const workouts = plan.workouts.map((item) => ({
        workout_id: item.id,
        scheduled_date:
          item.id === workout.id ? scheduledDate : item.scheduled_date,
      }));
      const validation = await validatePlanLayout(
        accessToken,
        plan.id,
        plan.active_revision!,
        workouts,
      );
      if (validation.warnings.length === 0) {
        await applyWorkoutMove(workout, scheduledDate);
        return;
      }
      setPendingMove({ scheduledDate, warnings: validation.warnings, workout });
    });
  };

  const markGoalAchievement = () => {
    if (!primaryGoal) return;
    void run(async () => {
      await markGoalAchieved(accessToken, primaryGoal.id, isoDate(new Date()));
      setMaintenanceMarked(true);
    });
  };

  const openCalendar = () => {
    setView('calendar');
  };

  const pendingWorkouts = usePendingWorkoutActions(accessToken, plan, setPlan, setError);
  const clearPlan = () => {
    setPlan(null);
    void rememberPlanId(null);
  };
  const cancelWorkoutMove = () => setPendingMove(null);
  const confirmWorkoutMove = () => {
    if (!pendingMove) return;
    void run(() => applyWorkoutMove(pendingMove.workout, pendingMove.scheduledDate));
  };

  return {
    view, setView, weekStart, setWeekStart, reusePreviousWeek, setReusePreviousWeek,
    selectedDays, injuries, crossTrainingOptIns, plan, swipeDraft, pendingMove,
    primaryGoal, maintenanceMarked, busy, error, setError, availableDates,
    toggleDay, toggleInjury, toggleCrossTraining, generate, approve, reject,
    openDeck, transitionDraft, placeDraftWorkout, submitDraft, requestWorkoutMove,
    markGoalAchievement, openCalendar, clearPlan, cancelWorkoutMove,
    confirmWorkoutMove, pendingWorkouts,
  };
}

export type PlanningController = ReturnType<typeof usePlanningController>;
