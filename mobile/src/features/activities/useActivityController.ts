import { useCallback, useEffect, useRef, useState } from 'react';
import {
  confirmActivityMatch, createActivity, getActivity, getCalendar, getOnboarding,
  listActivities, listPlannedExternalActivities, submitActivityRpeWithRefresh,
  getWorkoutRegistration, confirmWorkoutRegistration,
} from '../../api/client';
import type { CompletedActivity, Discipline, PlannedExternalActivity, PlannedWorkout } from '../../api/types';
import { activityCreateInput, newIdempotencyKey } from './activityCreateInput';

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// One identity lifetime owns reads, logical create attempts and feedback.
// API contracts and recovery stay in the existing client helpers.
export function useActivityController(accessToken: string) {
  const token = useRef(accessToken);
  token.current = accessToken;
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);
  const [activities, setActivities] = useState<CompletedActivity[]>([]);
  const [workouts, setWorkouts] = useState<PlannedWorkout[]>([]);
  const [externalActivities, setExternalActivities] = useState<PlannedExternalActivity[]>([]);
  const [selectedWorkout, setSelectedWorkout] = useState<PlannedWorkout | null>(null);
  const [selectedExternal, setSelectedExternal] = useState<PlannedExternalActivity | null>(null);
  const [discipline, setDiscipline] = useState<Discipline>('run');
  const [duration, setDuration] = useState('');
  const [registrationOutcome, setRegistrationOutcome] = useState<'unknown' | 'skipped' | null>(null);
  const registrationAttempt = useRef<{ workoutId: string; input: Parameters<typeof confirmWorkoutRegistration>[2] } | null>(null);
  const [distance, setDistance] = useState('');
  const [startedAt, setStartedAt] = useState(() => new Date().toISOString());
  const [athleteTimezone, setAthleteTimezone] = useState('');
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [createdActivityId, setCreatedActivityId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mutationError = useRef<string | null>(null);
  const [heartRateByActivity, setHeartRateByActivity] = useState<Record<string, string>>({});
  // The shell pending endpoint and complete list publish to this single source.
  const [pendingRpe, setPendingRpe] = useState<CompletedActivity[]>([]);
  const [feedbackId, setFeedbackId] = useState<string | null>(null);
  const feedbackSelection = useRef(feedbackId);
  feedbackSelection.current = feedbackId;
  const feedbackActivity = pendingRpe.find(activity => activity.id === createdActivityId) ?? pendingRpe.find(activity => activity.id === feedbackId) ?? pendingRpe[0];
  const createInFlightRef = useRef(false);
  const createAttempt = useRef<{ key: string; input: ReturnType<typeof activityCreateInput> } | null>(null);
  const rpeInFlightRef = useRef<Set<string>>(new Set());
  const unresolvedRpe = useRef(new Map<string, {
    activity: CompletedActivity; rpe: number; averageHeartRate: number | undefined;
  }>());
  const historyLoaded = useRef(false);
  const activityEntered = useRef(false);
  const focused = useRef(false);
  const loadInFlight = useRef<{ token: string; promise: Promise<void> } | null>(null);
  const historySequence = useRef(0);
  const readClock = useRef(0);
  // An index of authenticated full entities in this owner, not another manager.
  const entities = useRef(new Map<string, { row: CompletedActivity; sequence: number }>());
  const staleIds = useRef(new Set<string>());
  const activitiesRef = useRef(activities);
  const pendingRef = useRef(pendingRpe);
  const createdIdRef = useRef(createdActivityId);
  createdIdRef.current = createdActivityId;
  const pendingSequence = useRef(0);
  const pendingInFlight = useRef<{ token: string; promise: Promise<void> } | null>(null);
  const pendingContext = useRef<{ path: string; token: string } | null>(null);

  const publishPending = useCallback((rows: CompletedActivity[]) => {
    pendingRef.current = rows;
    setPendingRpe(rows);
    setFeedbackId(current => rows.some(row => row.id === createdIdRef.current) ? createdIdRef.current
      : rows.some(row => row.id === current) ? current : rows[0]?.id ?? null);
  }, []);
  const indexRows = useCallback((rows: CompletedActivity[], sequence: number) => {
    for (const row of rows) {
      if ((entities.current.get(row.id)?.sequence ?? -1) <= sequence) {
        entities.current.set(row.id, { row, sequence });
        staleIds.current.delete(row.id);
        if (row.id === createdIdRef.current && row.processing_state === 'complete') {
          createdIdRef.current = null;
          setCreatedActivityId(null);
          createAttempt.current = null;
          setIdempotencyKey(newIdempotencyKey());
        }
      }
    }
    return rows.map(row => entities.current.get(row.id)!.row);
  }, []);
  const publishActivity = useCallback((row: CompletedActivity) => {
    if (!alive.current) return;
    const [current] = indexRows([row], ++readClock.current);
    const rows = activitiesRef.current.some(item => item.id === row.id)
      ? activitiesRef.current.map(item => item.id === row.id ? current : item)
      : [current, ...activitiesRef.current];
    activitiesRef.current = rows;
    setActivities(rows);
    publishPending([...pendingRef.current.filter(item => item.id !== row.id),
      ...(current.processing_state === 'awaiting_rpe' ? [current] : [])]);
  }, [indexRows, publishPending]);
  const forgetActivity = useCallback((id: string) => {
    unresolvedRpe.current.delete(id);
    ++historySequence.current;
    ++pendingSequence.current;
    loadInFlight.current = null;
    pendingInFlight.current = null;
    setRefreshing(false);
    if (createdIdRef.current === id) {
      createdIdRef.current = null;
      setCreatedActivityId(null);
      createAttempt.current = null;
      setIdempotencyKey(newIdempotencyKey());
    }
    entities.current.delete(id);
    staleIds.current.delete(id);
    activitiesRef.current = activitiesRef.current.filter(row => row.id !== id);
    setActivities(activitiesRef.current);
    publishPending(pendingRef.current.filter(row => row.id !== id));
  }, [publishPending]);

  const load = useCallback((access = token.current, supersede = false): Promise<void> => {
    if (!alive.current) return Promise.resolve();
    if (!supersede && loadInFlight.current?.token === access) return loadInFlight.current.promise;
    const requestNumber = ++historySequence.current;
    const pendingNumber = ++pendingSequence.current;
    const sequence = ++readClock.current;
    for (const id of entities.current.keys()) staleIds.current.add(id);
    const request = (async () => {
      const now = new Date();
      const from = new Date(now);
      const to = new Date(now);
      from.setDate(from.getDate() - 14);
      to.setDate(to.getDate() + 14);
      const [activityRows, calendar, onboarding, plannedExternal] = await Promise.all([
        listActivities(access),
        getCalendar(access, isoDate(from), isoDate(to)),
        getOnboarding(access),
        listPlannedExternalActivities(access),
      ]);
      if (!alive.current || requestNumber !== historySequence.current) return;
      const indexed = indexRows(activityRows, sequence);
      // A read started before an acknowledged write/targeted read cannot drop it.
      const retained = activitiesRef.current.filter(row => !indexed.some(item => item.id === row.id) &&
        (entities.current.get(row.id)?.sequence ?? -1) > sequence);
      activitiesRef.current = [...indexed, ...retained];
      setActivities(activitiesRef.current);
      if (pendingNumber === pendingSequence.current) {
        const known = pendingRef.current.filter(row => !indexed.some(item => item.id === row.id));
        publishPending([...indexed.filter(row => row.processing_state === 'awaiting_rpe'), ...known]);
      }
      setWorkouts(calendar.workouts.filter(workout => workout.status === 'scheduled'));
      setExternalActivities(plannedExternal.filter(activity => activity.status === 'planned'));
      if (!onboarding.profile?.timezone_confirmed_at || !onboarding.profile.timezone) {
        throw new Error('Bevestig eerst je tijdzone in de intake voordat je activiteiten registreert.');
      }
      setAthleteTimezone(onboarding.profile.timezone);
      historyLoaded.current = true;
    })().catch((caught: unknown) => {
      if (alive.current && requestNumber === historySequence.current) throw caught;
    });
    const current = { token: access, promise: request };
    loadInFlight.current = current;
    void request.finally(() => {
      if (loadInFlight.current === current) {
        loadInFlight.current = null;
        if (alive.current) setRefreshing(false);
      }
    }).catch(() => undefined);
    return request;
  }, [indexRows, publishPending]);

  const refreshActivities = useCallback(async (supersede = false) => {
    if (!alive.current) return;
    const initial = !historyLoaded.current;
    if (initial) setBusy(true);
    setRefreshing(true);
    const request = load(token.current, supersede);
    const attempt = historySequence.current;
    try {
      await request;
      if (alive.current && attempt === historySequence.current && !mutationError.current) setError(null);
    }
    catch (caught) { if (alive.current && attempt === historySequence.current && !mutationError.current) setError(caught instanceof Error ? caught.message : 'Laden is mislukt.'); }
    finally {
      if (alive.current && attempt === historySequence.current && !loadInFlight.current) {
        setRefreshing(false);
        if (initial) setBusy(createInFlightRef.current || rpeInFlightRef.current.size > 0);
      }
    }
  }, [load]);
  const ensureActivitiesLoaded = useCallback(async () => {
    if (!alive.current) return;
    if (!activityEntered.current) {
      activityEntered.current = true;
      setStartedAt(new Date().toISOString());
    }
    await refreshActivities();
  }, [refreshActivities]);
  const setActivitiesFocused = useCallback((active: boolean) => {
    if (!alive.current || focused.current === active) return;
    focused.current = active;
    if (active) void ensureActivitiesLoaded();
  }, [ensureActivitiesLoaded]);
  const invalidateActivities = useCallback(() => {
    if (!alive.current) return;
    for (const id of entities.current.keys()) staleIds.current.add(id);
    ++historySequence.current;
    ++pendingSequence.current;
    loadInFlight.current = null;
    pendingInFlight.current = null;
    pendingContext.current = null;
    if (focused.current) void refreshActivities(true);
  }, [refreshActivities]);

  // The reminder API already returns full public entities. Index them once so
  // a reminder can resolve its exact UUID without requiring a history download.
  const refreshPendingRpe = useCallback((path?: string): Promise<void> => {
    if (!alive.current) return Promise.resolve();
    const access = token.current;
    if (path !== undefined) {
      if (pendingContext.current?.path === path && pendingContext.current.token === access) return Promise.resolve();
      pendingContext.current = { path, token: access };
    }
    if (loadInFlight.current?.token === access) return loadInFlight.current.promise.catch(() => undefined);
    if (pendingInFlight.current?.token === access) return pendingInFlight.current.promise;
    const pendingNumber = ++pendingSequence.current;
    const sequence = ++readClock.current;
    const promise = listActivities(access, true).then(rows => {
      if (!alive.current || pendingNumber !== pendingSequence.current) return;
      const indexed = indexRows(rows, sequence);
      // Membership absence alone cannot erase the activity currently being
      // entered/retried. Resolve that exact stale identity before a later PUT.
      const retained = pendingRef.current.filter(row => !indexed.some(item => item.id === row.id) &&
        (row.id === feedbackSelection.current || row.id === createdIdRef.current || rpeInFlightRef.current.has(row.id)));
      for (const row of retained) staleIds.current.add(row.id);
      publishPending([...indexed.filter(row => row.processing_state === 'awaiting_rpe'), ...retained]);
      activitiesRef.current = activitiesRef.current.map(row => entities.current.get(row.id)?.row ?? row);
      setActivities(activitiesRef.current);
    }).catch(() => undefined);
    const request = { token: access, promise };
    pendingInFlight.current = request;
    void promise.finally(() => { if (pendingInFlight.current === request) pendingInFlight.current = null; });
    return promise;
  }, [indexRows, publishPending]);

  const selectWorkout = (workout: PlannedWorkout | null) => {
    setRegistrationOutcome(null);
    setSelectedWorkout(workout);
    setSelectedExternal(null);
    setDuration('');
    if (workout) {
      setDiscipline(workout.discipline);
      setDistance(workout.distance_meters === null ? '' : String(workout.distance_meters));
    }
  };
  const selectExternal = (activity: PlannedExternalActivity) => {
    setRegistrationOutcome(null);
    setSelectedWorkout(null);
    setSelectedExternal(activity);
    setDiscipline(activity.discipline);
    setDuration('');
    setDistance('');
  };

  const registerCompletion = async (status: 'unknown' | 'skipped') => {
    if (!alive.current || createInFlightRef.current || rpeInFlightRef.current.size || !selectedWorkout) return;
    createInFlightRef.current = true;
    setBusy(true); setError(null); setRegistrationOutcome(null);
    const access = token.current;
    const workoutId = selectedWorkout.id;
    try {
      if (createAttempt.current || createdIdRef.current) {
        throw new Error('Rond eerst de opgeslagen activiteit of het eerdere opslagverzoek af.');
      }
      const unresolved = registrationAttempt.current;
      if (unresolved && (unresolved.workoutId !== workoutId || unresolved.input.status !== status)) {
        throw new Error('Herhaal eerst de vorige registratie om de status te controleren.');
      }
      const current = await getWorkoutRegistration(access, workoutId);
      if (!alive.current) return;
      if (current.planned_workout_id !== workoutId || !Number.isInteger(current.registration_revision) ||
          !current.plan_revision_id || !['unknown', 'skipped'].includes(current.status)) {
        throw new Error('De registratiestatus kon niet betrouwbaar worden geladen.');
      }
      if (current.status !== status) {
        const attempt = unresolved ?? { workoutId, input: {
          plan_revision_id: current.plan_revision_id,
          expected_registration_revision: current.registration_revision, status,
        } };
        registrationAttempt.current = attempt;
        const confirmed = await confirmWorkoutRegistration(access, workoutId, attempt.input);
        if (!alive.current) return;
        if (confirmed.planned_workout_id !== workoutId || confirmed.status !== status) {
          throw new Error('De registratie kon niet worden bevestigd.');
        }
      }
      registrationAttempt.current = null;
      setRegistrationOutcome(status);
      // Keep the exact named context visible with its confirmation/undo action.
      setDuration('');
      mutationError.current = null;
    } catch (caught) {
      if (alive.current) {
        if (caught && typeof caught === 'object' && 'status' in caught && typeof caught.status === 'number' &&
            [400, 404, 409, 422].includes(caught.status)) registrationAttempt.current = null;
        const message = caught instanceof Error ? caught.message : 'Registreren is mislukt.';
        mutationError.current = message; setError(message);
      }
    } finally {
      createInFlightRef.current = false;
      if (alive.current) setBusy(rpeInFlightRef.current.size > 0);
    }
  };

  const save = async () => {
    if (!alive.current || createInFlightRef.current) return;
    createInFlightRef.current = true;
    let confirmed = false;
    const access = token.current;
    setBusy(true);
    mutationError.current = null;
    setError(null);
    try {
      if (registrationAttempt.current) throw new Error('Herhaal eerst de vorige registratie om de status te controleren.');
      if (registrationOutcome === 'skipped') throw new Error('Zet de uitvoering eerst terug op onbekend voordat je een activiteit opslaat.');
      setRegistrationOutcome(null);
      // A completed POST followed by a failed refresh must not create again.
      if (createdIdRef.current) { confirmed = true; await load(access, true); return; }
      if (pendingRef.current.length > 0 && !createAttempt.current) throw new Error('Rond eerst de RPE van de opgeslagen activiteit af.');
      const attempt = createAttempt.current ?? {
        key: idempotencyKey,
        input: activityCreateInput({ selectedWorkout, selectedExternal, discipline, duration, distance, startedAt, athleteTimezone }),
      };
      createAttempt.current = attempt;
      const created = await createActivity(access, attempt.key, attempt.input);
      if (!alive.current) return;
      confirmed = true;
      createdIdRef.current = created.processing_state === 'awaiting_rpe' ? created.id : null;
      setCreatedActivityId(createdIdRef.current);
      if (created.processing_state === 'complete') {
        createAttempt.current = null;
        setIdempotencyKey(newIdempotencyKey());
      }
      ++historySequence.current;
      ++pendingSequence.current;
      publishActivity(created);
      setSelectedWorkout(null);
      setSelectedExternal(null);
      setDuration('');
      setStartedAt(new Date().toISOString());
      await load(access, true);
    } catch (caught) {
      if (alive.current) {
        const message = caught instanceof Error ? caught.message : 'De activiteit kon niet worden opgeslagen.';
        mutationError.current = confirmed ? null : message;
        setError(message);
      }
    } finally {
      createInFlightRef.current = false;
      if (alive.current) setBusy(createInFlightRef.current || rpeInFlightRef.current.size > 0);
    }
  };

  const saveRpe = async (activityId: string, rpe: number): Promise<boolean> => {
    if (!alive.current || rpeInFlightRef.current.has(activityId)) return false;
    let confirmed = false;
    rpeInFlightRef.current.add(activityId);
    const access = token.current;
    setBusy(true);
    mutationError.current = null;
    setError(null);
    let attempted: { activity: CompletedActivity; rpe: number; averageHeartRate: number | undefined } | undefined;
    try {
      const previousAttempt = unresolvedRpe.current.get(activityId);
      const rawHeartRate = heartRateByActivity[activityId]?.trim() ?? '';
      const averageHeartRate = previousAttempt ? previousAttempt.averageHeartRate : rawHeartRate ? Number(rawHeartRate) : undefined;
      if (averageHeartRate !== undefined && (!Number.isInteger(averageHeartRate) || averageHeartRate < 20 || averageHeartRate > 260)) {
        throw new Error('Vul een gemiddelde hartslag tussen 20 en 260 bpm in.');
      }
      const cached = entities.current.get(activityId)?.row;
      const intendedPending = !cached || cached.processing_state === 'awaiting_rpe';
      let activity = cached;
      if (!activity || staleIds.current.has(activityId)) {
        const resolved = await getActivity(access, activityId);
        if (!alive.current) return false;
        if (!resolved || resolved.id !== activityId || !['awaiting_rpe', 'complete'].includes(resolved.processing_state) ||
          typeof resolved.started_at !== 'string' || typeof resolved.timezone !== 'string' ||
          (resolved.rpe !== null && typeof resolved.rpe !== 'number')) throw new Error('De activiteit kon niet betrouwbaar worden geladen.');
        // Prefer a newer owner read if one completed while resolution was pending.
        const newer = entities.current.get(activityId)?.row;
        activity = newer && newer !== cached && !staleIds.current.has(activityId) ? newer : resolved;
        publishActivity(activity);
        if (cached && cached.rpe !== activity.rpe && !intendedPending) throw new Error('De activiteit is intussen gewijzigd. Controleer de opgeslagen RPE.');
      }
      if (!previousAttempt && intendedPending && activity.processing_state !== 'awaiting_rpe') throw new Error('Deze activiteit is intussen verwerkt. Controleer de opgeslagen RPE.');
      if (!alive.current) return false;
      attempted = previousAttempt ?? { activity, rpe, averageHeartRate };
      let updated: CompletedActivity;
      if (previousAttempt) {
        // Explicit retry first verifies the original operation, including HR.
        // A new choice/input cannot rewrite an unresolved request's payload.
        const stored = await getActivity(access, activityId);
        if (!alive.current) return false;
        if (stored.processing_state === 'complete' && stored.rpe === attempted.rpe &&
          (attempted.averageHeartRate === undefined || stored.metrics?.average_heart_rate_bpm === attempted.averageHeartRate)) {
          updated = stored;
        } else if (stored.rpe !== attempted.activity.rpe) {
          publishActivity(stored);
          unresolvedRpe.current.delete(activityId);
          attempted = undefined;
          throw new Error('De activiteit is intussen gewijzigd. Controleer de opgeslagen RPE.');
        } else updated = await submitActivityRpeWithRefresh(access, attempted.activity, attempted.rpe, attempted.averageHeartRate);
      } else updated = await submitActivityRpeWithRefresh(access, activity, rpe, averageHeartRate);
      if (!alive.current) return false;
      unresolvedRpe.current.delete(activityId);
      ++historySequence.current;
      ++pendingSequence.current;
      publishActivity(updated);
      confirmed = true;
      if (createdIdRef.current === activityId) {
        createdIdRef.current = null;
        setCreatedActivityId(null);
        createAttempt.current = null;
        setIdempotencyKey(newIdempotencyKey());
      }
      setHeartRateByActivity(current => { const next = { ...current }; delete next[activityId]; return next; });
      await load(access, true);
      return true;
    } catch (caught) {
      if (alive.current) {
        if (attempted && caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown') unresolvedRpe.current.set(activityId, attempted);
        const status = caught && typeof caught === 'object' && 'status' in caught ? caught.status : null;
        if (status === 404) forgetActivity(activityId);
        const message = caught instanceof Error ? caught.message : 'RPE opslaan is mislukt.';
        mutationError.current = confirmed ? null : message;
        setError(message);
      }
      return confirmed;
    } finally {
      rpeInFlightRef.current.delete(activityId);
      if (alive.current) setBusy(createInFlightRef.current || rpeInFlightRef.current.size > 0);
    }
  };

  const confirmMatch = async (activityId: string, workoutId: string) => {
    if (!alive.current) return;
    const access = token.current;
    setBusy(true);
    mutationError.current = null;
    setError(null);
    try { await confirmActivityMatch(access, activityId, workoutId); if (alive.current) await load(access, true); }
    catch (caught) { if (alive.current) setError(caught instanceof Error ? caught.message : 'De koppeling kon niet worden bevestigd.'); }
    finally { if (alive.current) setBusy(createInFlightRef.current || rpeInFlightRef.current.size > 0); }
  };

  return {
    activities, workouts, externalActivities, selectedWorkout, selectedExternal,
    discipline, setDiscipline, duration, setDuration, distance, setDistance, startedAt, setStartedAt,
    athleteTimezone, busy, refreshing, error, heartRateByActivity, setHeartRateByActivity, pendingRpe, feedbackActivity,
    selectWorkout, selectExternal, save, saveRpe, confirmMatch, ensureActivitiesLoaded, refreshPendingRpe,
    registerCompletion, registrationOutcome,
    refreshActivities, setActivitiesFocused, invalidateActivities,
  };
}

export type ActivityController = ReturnType<typeof useActivityController>;
