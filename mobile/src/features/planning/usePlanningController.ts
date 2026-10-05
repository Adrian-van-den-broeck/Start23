import * as SecureStore from 'expo-secure-store';
import * as Haptics from 'expo-haptics';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import type { Discipline, OnboardingState, PlanWarning, PlannedWorkout, PrimaryRaceGoal, SwipeWeekDraft, WeeklyPlan } from '../../api/types';
import { isDateInWeek } from '../../components/WeekSchedule';
import { availableDatesFor, dayOffsetsFor, isoDate, nextMonday } from './planningDates';
import { latestPlanIdKey, latestSwipeDraftIdKey, rememberPlanId, rememberSwipeDraftId } from './planningResume';
import { usePendingWorkoutActions } from './usePendingWorkoutActions';

export type PlanningView = 'plan' | 'deck' | 'calendar';

// Called once by PlanningFlowProvider; presentations consume its context.
export function usePlanningController(accessToken: string, initialOnboarding?: OnboardingState) {
  const initialOnboardingRef = useRef({ accessToken, state: initialOnboarding });
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
  const [resumeState, setResumeState] = useState<'loading' | 'ready' | 'failed'>(Platform.OS === 'web' ? 'ready' : 'loading');
  const [activeSnapshot, setActiveSnapshot] = useState<WeeklyPlan | null>(null);
  const [activeReadState, setActiveReadState] = useState<'ready' | 'loading' | 'failed'>('ready');
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const currentPlan = useRef(plan);
  currentPlan.current = plan;
  const moveOwnerAlive = useRef(true);
  useEffect(() => {
    moveOwnerAlive.current = true;
    return () => { moveOwnerAlive.current = false; };
  }, []);
  const [swipeDraft, setSwipeDraft] = useState<SwipeWeekDraft | null>(null);
  const [pendingMove, setPendingMove] = useState<{
    scheduledDate: string;
    warnings: PlanWarning[];
    workout: PlannedWorkout;
    reviewedPlan: WeeklyPlan;
  } | null>(null);
  const currentMove = useRef(pendingMove);
  currentMove.current = pendingMove;
  const [primaryGoal, setPrimaryGoal] = useState<PrimaryRaceGoal | null>(null);
  const [maintenanceMarked, setMaintenanceMarked] = useState(false);
  const [busy, setBusy] = useState(false);
  // Shared across presentations: React's busy render alone cannot block two
  // actions dispatched in the same tick, or from two different controls.
  const mutationInFlight = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const availableDates = useMemo(
    () => availableDatesFor(weekStart, selectedDays),
    [selectedDays, weekStart],
  );

  useEffect(() => {
    if (Platform.OS === 'web') return;
    let mounted = true;
    setResumeState('loading');
    let readFailed = false;
    const recordReadFailure = (caught: unknown) => {
      // Existing transport metadata; no message parsing or new recovery/retry.
      if (caught && typeof caught === 'object' && 'status' in caught && caught.status === 404) return;
      readFailed = true;
    };
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
        } catch (caught) {
          recordReadFailure(caught);
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
        } catch (caught) {
          recordReadFailure(caught);
          await rememberPlanId(null);
        }
      })
      .catch(recordReadFailure)
      .finally(() => { if (mounted) setResumeState(readFailed ? 'failed' : 'ready'); });
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  useEffect(() => {
    const initial = initialOnboardingRef.current;
    if (initial.accessToken === accessToken && initial.state) {
      setPrimaryGoal(initial.state.primary_goal);
      return;
    }
    getOnboarding(accessToken)
      .then((state) => setPrimaryGoal(state.primary_goal))
      .catch(() => undefined);
  }, [accessToken]);

  // Week needs the identified active snapshot, never the pending workout rows.
  // This owner alone reads a known revision; presentation toggles are not dependencies.
  useEffect(() => { if (plan?.revision_state === 'active') setActiveSnapshot(plan); }, [plan]);
  const activeId = plan?.id;
  const activeRevision = plan?.active_revision;
  const isActive = plan?.revision_state === 'active';
  useEffect(() => {
    if (!activeId || !activeRevision || isActive) {
      setActiveReadState('ready');
      return;
    }
    let mounted = true;
    setActiveReadState('loading');
    getWeeklyPlan(accessToken, activeId, activeRevision)
      .then((snapshot) => {
        if (!mounted) return;
        if (snapshot.id === activeId && snapshot.revision === activeRevision &&
          snapshot.revision_state === 'active') {
          setActiveSnapshot(snapshot);
          setActiveReadState('ready');
        } else {
          setActiveReadState('failed');
        }
      })
      .catch(() => { if (mounted) setActiveReadState('failed'); });
    return () => { mounted = false; };
  }, [accessToken, activeId, activeRevision, isActive]);
  const activePlan = isActive ? plan : activeSnapshot && activeSnapshot.id === activeId &&
    activeSnapshot.revision === activeRevision && activeSnapshot.week_start === plan?.week_start
      ? activeSnapshot : null;

  const run = async (operation: () => Promise<void>) => {
    if (mutationInFlight.current || pendingWorkouts.isLoading()) return;
    mutationInFlight.current = true;
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
      mutationInFlight.current = false;
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
    if (currentPlan.current !== plan || plan?.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending') return;
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
    if (currentPlan.current !== plan || plan?.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending') return;
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
    reviewedPlan: WeeklyPlan,
  ) => {
    if (!moveOwnerAlive.current || currentPlan.current !== reviewedPlan || !reviewedPlan.active_revision) return;
    const updated = await movePlannedWorkout(
      accessToken,
      workout.id,
      reviewedPlan.active_revision,
      scheduledDate,
    );
    if (!moveOwnerAlive.current || currentPlan.current !== reviewedPlan) return;
    setPlan(updated);
    currentMove.current = null;
    setPendingMove(null);
    void Haptics.notificationAsync(
      Haptics.NotificationFeedbackType.Success,
    ).catch(() => undefined);
  };

  const requestWorkoutMove = (
    workout: PlannedWorkout,
    scheduledDate: string,
  ) => {
    if (!moveOwnerAlive.current || currentPlan.current !== plan || plan?.revision_state !== 'active' || !plan.active_revision ||
      currentMove.current || !plan.workouts.some(item => item.id === workout.id && item.status === 'scheduled' && item.scheduled_date === workout.scheduled_date)) return;
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
      if (!moveOwnerAlive.current || currentPlan.current !== plan) return;
      if (validation.warnings.length === 0) {
        await applyWorkoutMove(workout, scheduledDate, plan);
        return;
      }
      const review = { scheduledDate, warnings: validation.warnings, workout, reviewedPlan: plan };
      currentMove.current = review;
      setPendingMove(review);
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

  const pendingWorkouts = usePendingWorkoutActions(accessToken, plan, setPlan, setError, mutationInFlight);
  const clearPlan = () => {
    setPlan(null);
    void rememberPlanId(null);
  };
  const cancelWorkoutMove = () => {
    if (mutationInFlight.current) return;
    currentMove.current = null;
    setPendingMove(null);
  };
  const confirmWorkoutMove = () => {
    if (!pendingMove || currentMove.current !== pendingMove || currentPlan.current !== pendingMove.reviewedPlan) return;
    void run(() => applyWorkoutMove(pendingMove.workout, pendingMove.scheduledDate, pendingMove.reviewedPlan));
  };

  return {
    resumeState, activePlan, activeReadState,
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
