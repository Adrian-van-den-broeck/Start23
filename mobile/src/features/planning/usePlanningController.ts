import * as Haptics from 'expo-haptics';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AppState } from 'react-native';

import {
  approvePlanProposal,
  createSwipeWeekDraft,
  discoverPlanning,
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
import { latestPlanIdKey, latestSwipeDraftIdKey, readResumeId, rememberPlanId as savePlanId, rememberSwipeDraftId as saveDraftId } from './planningResume';
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
export function usePlanningController(accessToken: string, athleteIdentity: string, initialOnboarding?: OnboardingState) {
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
  const [resumeState, setResumeState] = useState<'loading' | 'ready' | 'failed'>('loading');
  const [activeSnapshot, setActiveSnapshot] = useState<WeeklyPlan | null>(null);
  const [activeReadState, setActiveReadState] = useState<'ready' | 'loading' | 'failed'>('ready');
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const currentPlan = useRef(plan);
  currentPlan.current = plan;
  const planResultGeneration = useRef(0);
  const unresolvedGeneration = useRef<Parameters<typeof createSwipeWeekDraft>[1] | null>(null);
  const unresolvedMove = useRef<{ workout: PlannedWorkout; scheduledDate: string; reviewedPlan: WeeklyPlan } | null>(null);
  const [taskHandoff, setTaskHandoff] = useState<TaskPlanHandoff | null>(null);
  const currentHandoff = useRef(taskHandoff);
  const publishHandoff = (value: TaskPlanHandoff | null) => {
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

  const rememberPlanId = (id: string | null, current = () => true) =>
    savePlanId(athleteIdentity, id, () => moveOwnerAlive.current && current());
  const rememberSwipeDraftId = (id: string | null, current = () => true) =>
    saveDraftId(athleteIdentity, id, () => moveOwnerAlive.current && current());
  const [resumeAttempt, setResumeAttempt] = useState(0);
  const resumeRunning = useRef(false);
  const retryResume = useCallback(() => {
    if (!resumeRunning.current && !mutationInFlight.current) setResumeAttempt(value => value + 1);
  }, []);
  const [recoveryVersion, setRecoveryVersion] = useState(0);

  useEffect(() => {
    let mounted = true;
    resumeRunning.current = true;
    const generation = planResultGeneration.current;
    const isCurrent = () => mounted && moveOwnerAlive.current && generation === planResultGeneration.current;
    setResumeState('loading');
    const validatePlan = (snapshot: WeeklyPlan) => {
      if (!snapshot || typeof snapshot.id !== 'string' || typeof snapshot.week_start !== 'string' ||
        typeof snapshot.timezone !== 'string' || !Number.isInteger(snapshot.revision) ||
        typeof snapshot.revision_id !== 'string' || !Array.isArray(snapshot.available_dates) ||
        !Array.isArray(snapshot.confirmed_injuries) || !Array.isArray(snapshot.workouts) ||
        !Array.isArray(snapshot.warnings) || !Array.isArray(snapshot.rest_days) ||
        !['active', 'pending_approval', 'rejected', 'expired', 'superseded', 'draft'].includes(snapshot.revision_state)) throw new Error('Invalid plan recovery response');
      return snapshot;
    };
    const validateDraft = (snapshot: SwipeWeekDraft) => {
      if (!snapshot || typeof snapshot.id !== 'string' || typeof snapshot.week_start !== 'string' ||
        !Number.isInteger(snapshot.revision) || !Array.isArray(snapshot.available_dates) ||
        !Array.isArray(snapshot.cross_training_opt_ins) || !Array.isArray(snapshot.accepted_workouts) ||
        !Array.isArray(snapshot.placements) || !Array.isArray(snapshot.warnings) ||
        !['collecting', 'placement', 'submitted'].includes(snapshot.state)) throw new Error('Invalid draft recovery response');
      return snapshot;
    };
    const hydratePlan = (snapshot: WeeklyPlan) => {
      if (!isCurrent()) return;
      currentPlan.current = snapshot;
      setPlan(snapshot);
      setWeekStart(snapshot.week_start);
      setReusePreviousWeek(snapshot.availability_source === 'previous_week');
      setSelectedDays(dayOffsetsFor(snapshot.week_start, snapshot.available_dates));
      setInjuries(new Set(snapshot.confirmed_injuries));
    };
    const verify = async <T extends { id: string }>(key: string, get: (id: string) => Promise<T>, save: (id: string | null, current: () => boolean) => Promise<void>): Promise<T | null> => {
      const locator = await readResumeId(athleteIdentity, key).catch(() => ({ id: null, legacy: false }));
      if (!locator.id || !isCurrent()) return null;
      try {
        const value = await get(locator.id);
        if (!value || value.id !== locator.id) throw new Error('Invalid recovery response');
        if (locator.legacy) await save(value.id, isCurrent);
        return isCurrent() ? value : null;
      } catch (caught) {
        const status = caught && typeof caught === 'object' && 'status' in caught ? caught.status : null;
        if (status === 404) {
          if (!locator.legacy) await save(null, isCurrent);
          return null;
        }
        if (locator.legacy) return null; // Unverified global hints never block owner discovery.
        // Stale draft/revision: retain the locator and reconcile via discovery.
        if (status === 409) return null;
        throw caught; // Offline/timeout/auth/5xx/malformed is never proof of absence.
      }
    };
    const resume = async () => {
      const localPlan = await verify(latestPlanIdKey, async id => validatePlan(await getWeeklyPlan(accessToken, id)), rememberPlanId);
      if (localPlan) hydratePlan(localPlan); // Trustworthy owner-scoped state survives discovery failure.
      const localDraft = await verify(latestSwipeDraftIdKey, async id => validateDraft(await getSwipeWeekDraft(accessToken, id)), rememberSwipeDraftId);
      if (!isCurrent()) return;
      if (localDraft?.state !== 'submitted' && localDraft) setSwipeDraft(localDraft);
      const found = await discoverPlanning(accessToken);
      if (!found || !('active' in found) || !('pending' in found) || !('draft' in found)) throw new Error('Invalid recovery response');
      if (found.active !== null) validatePlan(found.active);
      if (found.pending !== null) validatePlan(found.pending);
      if (found.draft !== null && (!found.draft || typeof found.draft.id !== 'string' || !Number.isInteger(found.draft.revision) || !['collecting', 'placement'].includes(found.draft.state))) throw new Error('Invalid draft locator');
      const localActive = localPlan?.revision_state === 'active' ? localPlan : null;
      const active = found.active && (!localActive || found.active.week_start >= localActive.week_start) ? found.active : localActive;
      const pending = found.pending ?? (localPlan?.revision_state === 'pending_approval' && (!active || localPlan.week_start >= active.week_start) && !(found.active?.id === localPlan.id && found.active.revision >= localPlan.revision) ? localPlan : null);
      if (active && (active.state !== 'active' || active.revision_state !== 'active' || active.active_revision !== active.revision)) throw new Error('Invalid active recovery response');
      if (pending && (pending.revision_state !== 'pending_approval' || pending.proposal?.state !== 'pending' || pending.proposal.target_plan_revision_id !== pending.revision_id)) throw new Error('Invalid pending recovery response');
      let selected = pending && (!active || pending.id === active.id) ? pending : active ?? localPlan;
      let restoredDraft = found.draft ? validateDraft(await getSwipeWeekDraft(accessToken, found.draft.id)) : localDraft;
      if (found.draft && (!restoredDraft || restoredDraft.id !== found.draft.id || restoredDraft.revision !== found.draft.revision || restoredDraft.state !== found.draft.state)) throw new Error('Draft changed during recovery');
      if (!isCurrent()) return;
      if (restoredDraft?.state === 'submitted' && restoredDraft.plan_id) {
        const submitted = validatePlan(await getWeeklyPlan(accessToken, restoredDraft.plan_id));
        if (submitted.id !== restoredDraft.plan_id) throw new Error('Invalid submitted plan identity');
        if (!selected || submitted.week_start >= selected.week_start) selected = submitted;
        restoredDraft = null;
      }
      if (restoredDraft && active && restoredDraft.week_start < active.week_start) restoredDraft = null;
      if (!isCurrent()) return;
      setActiveSnapshot(active);
      if (selected) hydratePlan(selected);
      else { setPlan(null); currentPlan.current = null; }
      if (pending && active && pending.id !== active.id) {
        publishHandoff({ taskKey: `recovery:${pending.id}`, reviewed: pending, plan: pending, receipt: null, phase: 'pending' });
      } else if (currentHandoff.current?.taskKey.startsWith('recovery:')) publishHandoff(null);
      setSwipeDraft(restoredDraft);
      if (restoredDraft) {
        setCrossTrainingOptIns(new Set(restoredDraft.cross_training_opt_ins));
        // Keep the approved week selected; the draft opens through existing actions.
        if (!selected) {
          setWeekStart(restoredDraft.week_start);
          setReusePreviousWeek(restoredDraft.availability_source === 'previous_week');
          setSelectedDays(dayOffsetsFor(restoredDraft.week_start, restoredDraft.available_dates));
          setView('deck');
        }
      }
      if (selected && selected.id !== localPlan?.id) await rememberPlanId(selected.id, isCurrent);
      if (restoredDraft && restoredDraft.id !== localDraft?.id) await rememberSwipeDraftId(restoredDraft.id, isCurrent);
      else if (localDraft && !restoredDraft) await rememberSwipeDraftId(null, isCurrent);
      if (isCurrent()) { setRecoveryVersion(value => value + 1); setResumeState('ready'); }
    };
    void resume().catch(() => { if (isCurrent()) setResumeState('failed'); }).finally(() => {
      if (mounted) resumeRunning.current = false;
    });
    return () => { mounted = false; resumeRunning.current = false; };
  }, [accessToken, athleteIdentity, resumeAttempt]);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => { if (state === 'active') retryResume(); });
    return () => subscription.remove();
  }, [retryResume]);

  useEffect(() => {
    const initial = initialOnboardingRef.current;
    if (initial.accessToken === accessToken && initial.state) {
      setPrimaryGoal(initial.state.primary_goal);
      return;
    }
    let current = true;
    getOnboarding(accessToken)
      .then((state) => { if (current) setPrimaryGoal(state.primary_goal); })
      .catch(() => undefined);
    return () => { current = false; };
  }, [accessToken]);

  // Week needs the identified active snapshot, never the pending workout rows.
  // This owner alone reads a known revision; presentation toggles are not dependencies.
  useEffect(() => { if (plan?.revision_state === 'active') setActiveSnapshot(plan); }, [plan]);
  const activeId = plan?.id;
  const activeRevision = plan?.active_revision;
  const isActive = plan?.revision_state === 'active';
  useEffect(() => {
    if (!activeId || !activeRevision || isActive || (activeSnapshot?.id === activeId && activeSnapshot.revision === activeRevision && activeSnapshot.revision_state === 'active')) {
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
  }, [accessToken, activeId, activeRevision, isActive, resumeAttempt, activeSnapshot]);
  const activePlan = isActive ? plan : activeSnapshot && activeSnapshot.id === activeId &&
    activeSnapshot.revision === activeRevision && activeSnapshot.week_start === plan?.week_start
      ? activeSnapshot : null;

  const run = async (operation: () => Promise<void>) => {
    if (!moveOwnerAlive.current || mutationInFlight.current || pendingWorkouts.isLoading()) return;
    mutationInFlight.current = true;
    ++planResultGeneration.current;
    if (currentPlan.current || swipeDraft) setResumeState('ready');
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      if (moveOwnerAlive.current) setError(
        caught instanceof Error
          ? caught.message
          : 'De planningsactie is niet gelukt.',
      );
    } finally {
      mutationInFlight.current = false;
      if (moveOwnerAlive.current) setBusy(false);
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
      const input = unresolvedGeneration.current ?? {
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
      };
      let result: SwipeWeekDraft;
      try { result = await createSwipeWeekDraft(accessToken, input); }
      catch (caught) {
        if (moveOwnerAlive.current && caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown') unresolvedGeneration.current = input;
        throw caught;
      }
      if (!moveOwnerAlive.current) return;
      unresolvedGeneration.current = null;
      try { await rememberSwipeDraftId(result.id); }
      catch (caught) {
        if (moveOwnerAlive.current) { setSwipeDraft(result); setView('deck'); setResumeState('failed'); }
        throw caught;
      }
      if (!moveOwnerAlive.current) return;
      setSwipeDraft(result);
      setResumeState('ready');
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
    ++planResultGeneration.current;
    if (currentPlan.current || swipeDraft) setResumeState('ready');
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
    if (['rejected', 'expired', 'superseded'].includes(snapshot.revision_state) || (snapshot.proposal && ['rejected', 'expired'].includes(snapshot.proposal.state))) {
      if (existing?.taskKey === taskKey) publishHandoff(null);
      return true; // Preserve terminal server semantics; never revive a review.
    }
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
          if ((caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown') || typeof status !== 'number' || status >= 500) publishHandoff({ ...handoff, phase: 'verify' });
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

  const openRecoveredReview = useCallback(() => {
    if (!moveOwnerAlive.current) return;
    const handoff = currentHandoff.current;
    if (handoff?.taskKey.startsWith('recovery:') && handoff.phase === 'pending') setPlan(handoff.reviewed);
  }, []);
  const closeRecoveredReview = useCallback(() => {
    if (!moveOwnerAlive.current) return;
    if (currentHandoff.current?.taskKey.startsWith('recovery:') && activeSnapshot && currentPlan.current === currentHandoff.current.reviewed) setPlan(activeSnapshot);
  }, [activeSnapshot]);

  const approve = () => {
    const handoff = currentHandoff.current;
    if (handoff && handoff.reviewed === plan) {
      void approveTaskPlan(handoff.taskKey, handoff.reviewed).catch(() => undefined);
      return;
    }
    if (currentPlan.current !== plan || plan?.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending') return;
    const taskKey = `plan:${plan.revision_id}`;
    void receiveTaskPlan(taskKey, plan).then(ready => {
      if (ready && moveOwnerAlive.current) return approveTaskPlan(taskKey, plan);
      return false;
    }).catch(() => undefined);
  };

  const reject = () => {
    if (currentPlan.current !== plan || plan?.revision_state !== 'pending_approval' || plan.proposal?.state !== 'pending') return;
    void run(async () => {
      await rejectPlanProposal(accessToken, plan.proposal!.id);
      const updated = await getWeeklyPlan(accessToken, plan.id, plan.revision);
      if (moveOwnerAlive.current) {
        if (currentHandoff.current?.taskKey.startsWith('recovery:')) {
          publishHandoff(null);
          setPlan(activeSnapshot ?? updated);
        } else setPlan(updated);
      }
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
        if (!moveOwnerAlive.current) return;
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
      if (!moveOwnerAlive.current) return;
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
      if (!moveOwnerAlive.current) return;
      setSwipeDraft(null);
      setPlan(result.plan);
      setResumeState('ready');
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
    const unresolved = unresolvedMove.current;
    if (unresolved) {
      const stored = await getWeeklyPlan(accessToken, unresolved.reviewedPlan.id);
      if (!moveOwnerAlive.current) return;
      if (stored.revision !== unresolved.reviewedPlan.revision) {
        // The newer authoritative schedule may include another device's edit.
        // Adopt it for review without claiming our ambiguous PATCH committed.
        setPlan(stored);
        unresolvedMove.current = null;
        currentMove.current = null;
        setPendingMove(null);
        throw new Error('De weekplanning is intussen gewijzigd. Controleer de opgeslagen planning.');
      }
      workout = unresolved.workout;
      scheduledDate = unresolved.scheduledDate;
      // A6 may have refreshed an equal authoritative revision into a new
      // object. Keep the original wire identity/precondition, using the live
      // snapshot solely for the existing publication guard.
      if (!currentPlan.current || currentPlan.current.id !== unresolved.reviewedPlan.id || currentPlan.current.revision !== unresolved.reviewedPlan.revision) return;
      reviewedPlan = currentPlan.current;
    }
    let updated: WeeklyPlan;
    try { updated = await movePlannedWorkout(
      accessToken,
      workout.physical_workout_id ?? workout.id,
      reviewedPlan.active_revision!,
      scheduledDate,
    ); }
    catch (caught) {
      if (moveOwnerAlive.current && caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown') unresolvedMove.current = { workout, scheduledDate, reviewedPlan };
      throw caught;
    }
    if (!moveOwnerAlive.current || currentPlan.current !== reviewedPlan) return;
    setPlan(updated);
    unresolvedMove.current = null;
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
      if (unresolvedMove.current) {
        const attempt = unresolvedMove.current;
        await applyWorkoutMove(attempt.workout, attempt.scheduledDate, plan);
        return;
      }
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
      if (moveOwnerAlive.current) setMaintenanceMarked(true);
    });
  };

  const openCalendar = () => {
    setView('calendar');
  };

  const pendingWorkouts = usePendingWorkoutActions(accessToken, plan, setPlan, setError, mutationInFlight);
  const clearPlan = () => {
    if (!moveOwnerAlive.current) return;
    ++planResultGeneration.current;
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
    openRecoveredReview, closeRecoveredReview,
    resumeState, retryResume, recoveryVersion, activePlan, activeReadState, taskHandoff, receiveTaskPlan, approveTaskPlan,
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
