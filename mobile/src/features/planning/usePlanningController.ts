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
type PlanApproval = Awaited<ReturnType<typeof approvePlanProposal>>;
// Supporting tasks publish server snapshots here; selected Week state and the
// resume locator remain owned by this controller. No task creates another owner.
export type TaskPlanHandoff = Readonly<{
  taskKey: string;
  reviewed: WeeklyPlan;
  plan: WeeklyPlan;
  receipt: PlanApproval | null;
  phase: 'pending' | 'verify' | 'read' | 'persist' | 'complete';
}>;

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
  const planResultGeneration = useRef(0);
  const [taskHandoff, setTaskHandoff] = useState<TaskPlanHandoff | null>(null);
  const currentHandoff = useRef(taskHandoff);
  const publishHandoff = (value: TaskPlanHandoff) => {
    currentHandoff.current = value;
    setTaskHandoff(value);
  };
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
    const generation = planResultGeneration.current;
    const isCurrent = () => mounted && generation === planResultGeneration.current;
    setResumeState('loading');
    let readFailed = false;
    const recordReadFailure = (caught: unknown) => {
      // Existing transport metadata; no message parsing or new recovery/retry.
      if (caught && typeof caught === 'object' && 'status' in caught && caught.status === 404) return;
      readFailed = true;
    };
    SecureStore.getItemAsync(latestSwipeDraftIdKey)
      .then(async (draftId) => {
        if (!isCurrent()) return true;
        if (!draftId) return false;
        try {
          const restored = await getSwipeWeekDraft(accessToken, draftId);
          if (restored.state === 'submitted' && restored.plan_id) {
            const submittedPlan = await getWeeklyPlan(
              accessToken,
              restored.plan_id,
            );
            await Promise.all([
              rememberPlanId(submittedPlan.id, isCurrent),
              rememberSwipeDraftId(null, isCurrent),
            ]);
            if (isCurrent()) {
              setPlan(submittedPlan);
              setWeekStart(submittedPlan.week_start);
              setView('plan');
            }
            return true;
          }
          if (isCurrent()) {
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
          if (!isCurrent()) return true;
          recordReadFailure(caught);
          await rememberSwipeDraftId(null, isCurrent);
          return false;
        }
      })
      .then(async (draftRestored) => {
        if (draftRestored || !isCurrent()) return;
        const planId = await SecureStore.getItemAsync(latestPlanIdKey);
        if (!planId || !isCurrent()) return;
        try {
          const restored = await getWeeklyPlan(accessToken, planId);
          if (isCurrent()) {
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
          if (!isCurrent()) return;
          recordReadFailure(caught);
          await rememberPlanId(null, isCurrent);
        }
      })
      .catch(recordReadFailure)
      .finally(() => { if (isCurrent()) setResumeState(readFailed ? 'failed' : 'ready'); });
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

  const applyApprovedSnapshot = (updated: WeeklyPlan) => {
    ++planResultGeneration.current;
    currentPlan.current = updated;
    setPlan(updated);
    setActiveSnapshot(updated);
    setResumeState('ready');
    setActiveReadState('ready');
    setWeekStart(updated.week_start);
    setSelectedDays(dayOffsetsFor(updated.week_start, updated.available_dates));
    setReusePreviousWeek(updated.availability_source === 'previous_week');
    setInjuries(new Set(updated.confirmed_injuries));
    setSwipeDraft(null);
    currentMove.current = null;
    setPendingMove(null);
    setView('plan');
  };
  const runTaskHandoff = async (operation: () => Promise<boolean>): Promise<boolean> => {
    if (!moveOwnerAlive.current) return false;
    if (mutationInFlight.current || pendingWorkouts.isLoading()) throw new Error('Wacht tot de huidige planningsactie klaar is.');
    mutationInFlight.current = true;
    setBusy(true);
    setError(null);
    try { return await operation(); }
    catch (caught) {
      if (moveOwnerAlive.current) setError(caught instanceof Error ? caught.message : 'Het plan kon niet worden gesynchroniseerd.');
      throw caught;
    } finally {
      mutationInFlight.current = false;
      if (moveOwnerAlive.current) setBusy(false);
    }
  };
  const persistTaskPlan = async (handoff: TaskPlanHandoff): Promise<boolean> => {
    const isCurrent = () => moveOwnerAlive.current && currentHandoff.current === handoff;
    if (!isCurrent()) return false;
    // Publish authoritative success before persistence, so a storage error cannot
    // roll the athlete back to an old week. Completion still requires both writes.
    await rememberPlanId(handoff.plan.id, isCurrent);
    if (!isCurrent()) return false;
    await rememberSwipeDraftId(null, isCurrent);
    if (!isCurrent()) return false;
    publishHandoff({ ...handoff, phase: 'complete' });
    return true;
  };
  const receiveTaskPlan = (taskKey: string, snapshot: WeeklyPlan): Promise<boolean> => runTaskHandoff(async () => {
    const existing = currentHandoff.current;
    const sameRevision = existing?.taskKey === taskKey && existing.reviewed.id === snapshot.id &&
      existing.reviewed.revision_id === snapshot.revision_id && existing.reviewed.revision === snapshot.revision;
    if (sameRevision && (snapshot.revision_state === 'pending_approval' || existing.plan.revision_state === 'active')) {
      return existing.phase === 'persist' ? persistTaskPlan(existing) : true;
    }
    if (snapshot.revision_state === 'pending_approval' && snapshot.proposal?.state === 'pending') {
      if (snapshot.proposal.kind !== 'plan_revision' || snapshot.proposal.target_plan_revision_id !== snapshot.revision_id) throw new Error('Het voorstel hoort niet bij deze planrevisie.');
      publishHandoff({ taskKey, reviewed: snapshot, plan: snapshot, receipt: null, phase: 'pending' });
      // A supporting task's next-week proposal is not the selected approved week.
      return true;
    }
    if (snapshot.state !== 'active' || snapshot.revision_state !== 'active' || snapshot.active_revision !== snapshot.revision) throw new Error('Het ontvangen plan is niet actief of reviewbaar.');
    const handoff: TaskPlanHandoff = { taskKey, reviewed: sameRevision ? existing.reviewed : snapshot, plan: snapshot, receipt: sameRevision ? existing.receipt : null, phase: 'persist' };
    publishHandoff(handoff);
    applyApprovedSnapshot(snapshot);
    return persistTaskPlan(handoff);
  });
  const approveTaskPlan = (taskKey: string, reviewed: WeeklyPlan): Promise<boolean> => runTaskHandoff(async () => {
    let handoff = currentHandoff.current;
    if (!handoff || handoff.taskKey !== taskKey || handoff.reviewed !== reviewed) throw new Error('Open het exacte planvoorstel opnieuw voordat je beslist.');
    if (handoff.phase === 'complete') return true;
    if (handoff.phase === 'persist') return persistTaskPlan(handoff);
    if (reviewed.revision_state !== 'pending_approval' || reviewed.proposal?.state !== 'pending') throw new Error('Dit voorstel kan niet worden goedgekeurd.');
    if (handoff.phase === 'pending') {
      try {
        const receipt = await approvePlanProposal(accessToken, reviewed.proposal.id, reviewed.proposal.base_plan_revision ?? 0);
        if (!moveOwnerAlive.current) return false;
        handoff = { ...handoff, receipt, phase: 'read' };
        publishHandoff(handoff);
      } catch (caught) {
        if (moveOwnerAlive.current) {
          const status = caught && typeof caught === 'object' && 'status' in caught ? caught.status : null;
          if (typeof status !== 'number' || status >= 500) publishHandoff({ ...handoff, phase: 'verify' });
        }
        throw caught;
      }
    }
    const receipt = handoff.receipt;
    if (receipt && (receipt.state !== 'applied' || receipt.plan_id !== reviewed.id || receipt.active_revision !== reviewed.revision)) throw new Error('De goedkeuring hoort niet bij het bekeken planvoorstel.');
    const updated = await getWeeklyPlan(accessToken, reviewed.id, receipt?.active_revision ?? reviewed.revision);
    if (!moveOwnerAlive.current || currentHandoff.current !== handoff) return false;
    if (updated.id !== reviewed.id || updated.revision_id !== reviewed.revision_id || updated.revision !== reviewed.revision || updated.week_start !== reviewed.week_start) throw new Error('Het opgehaalde plan hoort niet bij het bekeken voorstel.');
    if (handoff.phase === 'verify' && updated.revision_state === 'pending_approval' && updated.proposal?.id === reviewed.proposal.id && updated.proposal.state === 'pending') {
      publishHandoff({ ...handoff, phase: 'pending' });
      return false; // Reading status never silently replays the mutation.
    }
    if (updated.state !== 'active' || updated.revision_state !== 'active' || updated.active_revision !== updated.revision) throw new Error('Het plan is nog niet als actief bevestigd. Heropen het voorstel.');
    handoff = { ...handoff, plan: updated, phase: 'persist' };
    publishHandoff(handoff);
    applyApprovedSnapshot(updated);
    return persistTaskPlan(handoff);
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
    resumeState, activePlan, activeReadState, taskHandoff, receiveTaskPlan, approveTaskPlan,
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
