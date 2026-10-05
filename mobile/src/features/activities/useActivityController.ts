import { useCallback, useEffect, useRef, useState } from 'react';
import {
  confirmActivityMatch, createActivity, getCalendar, getOnboarding,
  listActivities, listPlannedExternalActivities, submitActivityRpeWithRefresh,
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
  const [duration, setDuration] = useState('45');
  const [distance, setDistance] = useState('');
  const [startedAt, setStartedAt] = useState(() => new Date().toISOString());
  const [athleteTimezone, setAthleteTimezone] = useState('');
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [createdActivityId, setCreatedActivityId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [heartRateByActivity, setHeartRateByActivity] = useState<Record<string, string>>({});
  // The shell pending endpoint and complete list publish to this single source.
  const [pendingRpe, setPendingRpe] = useState<CompletedActivity[]>([]);
  const feedbackActivity = pendingRpe.find(activity => activity.id === createdActivityId) ?? pendingRpe[0];
  const createInFlightRef = useRef(false);
  const rpeInFlightRef = useRef<Set<string>>(new Set());
  const historyLoaded = useRef(false);
  const activityEntered = useRef(false);
  const loadInFlight = useRef<Promise<void> | null>(null);
  const pendingSequence = useRef(0);
  const pendingInFlight = useRef<{ token: string; promise: Promise<void> } | null>(null);
  const pendingContext = useRef<{ path: string; token: string } | null>(null);

  const load = useCallback((access = token.current): Promise<void> => {
    if (!alive.current) return Promise.resolve();
    if (loadInFlight.current) return loadInFlight.current;
    // An older reminder read cannot overwrite post-mutation feedback identity.
    ++pendingSequence.current;
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
      if (!alive.current) return;
      setActivities(activityRows);
      setPendingRpe(activityRows.filter(activity => activity.processing_state === 'awaiting_rpe'));
      setWorkouts(calendar.workouts.filter(workout => workout.status === 'scheduled'));
      setExternalActivities(plannedExternal.filter(activity => activity.status === 'planned'));
      if (!onboarding.profile?.timezone_confirmed_at || !onboarding.profile.timezone) {
        throw new Error('Bevestig eerst je tijdzone in de intake voordat je activiteiten registreert.');
      }
      setAthleteTimezone(onboarding.profile.timezone);
      historyLoaded.current = true;
    })();
    loadInFlight.current = request;
    void request.finally(() => { if (loadInFlight.current === request) loadInFlight.current = null; }).catch(() => undefined);
    return request;
  }, []);

  const ensureActivitiesLoaded = useCallback(async () => {
    if (!alive.current || historyLoaded.current || loadInFlight.current) return;
    // V1 initialized the actual-start default on Activity entry, not shell entry.
    // Later mounts keep the same unresolved form and logical attempt.
    if (!activityEntered.current) {
      activityEntered.current = true;
      setStartedAt(new Date().toISOString());
    }
    setBusy(true);
    try { await load(); }
    catch (caught) { if (alive.current) setError(caught instanceof Error ? caught.message : 'Laden is mislukt.'); }
    finally { if (alive.current) setBusy(false); }
  }, [load]);

  // Preserve the shell's route/token reminder trigger, without another count owner.
  const refreshPendingRpe = useCallback((path?: string): Promise<void> => {
    if (!alive.current) return Promise.resolve();
    const access = token.current;
    // The training readiness host can reparent the reminder. Its presentation
    // mount is not another route/token event and must not repeat the read.
    if (path !== undefined) {
      if (pendingContext.current?.path === path && pendingContext.current.token === access) return Promise.resolve();
      pendingContext.current = { path, token: access };
    }
    if (loadInFlight.current) return loadInFlight.current.catch(() => undefined);
    if (pendingInFlight.current?.token === access) return pendingInFlight.current.promise;
    const sequence = ++pendingSequence.current;
    const promise = listActivities(access, true).then(rows => {
      if (alive.current && sequence === pendingSequence.current) setPendingRpe(rows);
    }).catch(() => undefined);
    const request = { token: access, promise };
    pendingInFlight.current = request;
    void promise.finally(() => { if (pendingInFlight.current === request) pendingInFlight.current = null; });
    return promise;
  }, []);

  const selectWorkout = (workout: PlannedWorkout | null) => {
    setSelectedWorkout(workout);
    setSelectedExternal(null);
    if (workout) {
      setDiscipline(workout.discipline);
      setDuration(workout.duration_minutes === null ? '' : String(Number(workout.duration_minutes)));
      setDistance(workout.distance_meters === null ? '' : String(workout.distance_meters));
    }
  };
  const selectExternal = (activity: PlannedExternalActivity) => {
    setSelectedWorkout(null);
    setSelectedExternal(activity);
    setDiscipline(activity.discipline);
    setDuration(String(Number(activity.duration_minutes)));
    setDistance('');
  };

  const save = async () => {
    if (!alive.current || createInFlightRef.current) return;
    createInFlightRef.current = true;
    const access = token.current;
    setBusy(true);
    setError(null);
    try {
      // A completed POST followed by a failed refresh must not create again.
      if (createdActivityId) { await load(access); return; }
      if (pendingRpe.length > 0) throw new Error('Rond eerst de RPE van de opgeslagen activiteit af.');
      const created = await createActivity(access, idempotencyKey, activityCreateInput({
        selectedWorkout, selectedExternal, discipline, duration, distance, startedAt, athleteTimezone,
      }));
      if (!alive.current) return;
      setCreatedActivityId(created.id);
      setSelectedWorkout(null);
      setSelectedExternal(null);
      setStartedAt(new Date().toISOString());
      await load(access);
    } catch (caught) {
      if (alive.current) setError(caught instanceof Error ? caught.message : 'De activiteit kon niet worden opgeslagen.');
    } finally {
      createInFlightRef.current = false;
      if (alive.current) setBusy(false);
    }
  };

  const saveRpe = async (activityId: string, rpe: number) => {
    if (!alive.current || rpeInFlightRef.current.has(activityId)) return;
    rpeInFlightRef.current.add(activityId);
    const access = token.current;
    setBusy(true);
    setError(null);
    try {
      const rawHeartRate = heartRateByActivity[activityId]?.trim() ?? '';
      const averageHeartRate = rawHeartRate ? Number(rawHeartRate) : undefined;
      if (averageHeartRate !== undefined && (!Number.isInteger(averageHeartRate) || averageHeartRate < 20 || averageHeartRate > 260)) {
        throw new Error('Vul een gemiddelde hartslag tussen 20 en 260 bpm in.');
      }
      const activity = activities.find(candidate => candidate.id === activityId);
      if (!activity) throw new Error('De activiteit is niet meer beschikbaar.');
      await submitActivityRpeWithRefresh(access, activity, rpe, averageHeartRate);
      if (!alive.current) return;
      if (createdActivityId === activityId) {
        setCreatedActivityId(null);
        setIdempotencyKey(newIdempotencyKey());
      }
      setHeartRateByActivity(current => { const next = { ...current }; delete next[activityId]; return next; });
      await load(access);
    } catch (caught) {
      if (alive.current) setError(caught instanceof Error ? caught.message : 'RPE opslaan is mislukt.');
    } finally {
      rpeInFlightRef.current.delete(activityId);
      if (alive.current) setBusy(false);
    }
  };

  const confirmMatch = async (activityId: string, workoutId: string) => {
    if (!alive.current) return;
    const access = token.current;
    setBusy(true);
    setError(null);
    try { await confirmActivityMatch(access, activityId, workoutId); if (alive.current) await load(access); }
    catch (caught) { if (alive.current) setError(caught instanceof Error ? caught.message : 'De koppeling kon niet worden bevestigd.'); }
    finally { if (alive.current) setBusy(false); }
  };

  return {
    activities, workouts, externalActivities, selectedWorkout, selectedExternal,
    discipline, setDiscipline, duration, setDuration, distance, setDistance, startedAt, setStartedAt,
    athleteTimezone, busy, error, heartRateByActivity, setHeartRateByActivity, pendingRpe, feedbackActivity,
    selectWorkout, selectExternal, save, saveRpe, confirmMatch, ensureActivitiesLoaded, refreshPendingRpe,
  };
}

export type ActivityController = ReturnType<typeof useActivityController>;
