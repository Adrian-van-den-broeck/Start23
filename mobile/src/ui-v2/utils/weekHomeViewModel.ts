import type { SwipeWeekDraft, WeeklyPlan } from '../../api/types';
import { addDays, isoDate } from '../../features/planning/planningDates';
import { workoutSummaryViewModel, type WorkoutSummaryViewModel } from './workoutSummaryViewModel';
export type WeekAction = 'prepare' | 'draft' | 'review' | 'planning' | 'calendar';
export type WeekState = 'loading' | 'failed' | 'noPlan' | 'draft' | 'placement' | 'pending' | 'active' | 'activePending' | 'rejected' | 'expired' | 'unavailable';
export type WeekAttention = Readonly<{ kind: 'draft' | 'proposal' | 'warnings'; action: WeekAction; }>;
export type WeekHomeViewModel = Readonly<{
  weekStart: string; weekEnd: string; state: WeekState;
  sessions: readonly Readonly<{ id: string; summary: WorkoutSummaryViewModel; }>[];
  sessionDate: string | null; isToday: boolean;
  progress: Readonly<{ completed: number; planned: number; }> | null;
  empty: 'noPlan' | 'noFuture' | 'rest' | 'restrictedRest' | null;
  attention: readonly WeekAttention[]; mainAction: WeekAction | null; readState: 'loading' | 'ready' | 'failed';
}>;
export function currentWeekStart(today: string): string {
  const day = new Date(today + 'T12:00:00').getDay() || 7;
  return isoDate(addDays(today, 1 - day));
}
export function weekHomeViewModel(input: {
  plan: WeeklyPlan | null; activePlan: WeeklyPlan | null; draft: SwipeWeekDraft | null;
  today: string; resumeState: 'loading' | 'ready' | 'failed'; activeReadState: 'loading' | 'ready' | 'failed';
}): WeekHomeViewModel {
  const { plan, draft, today } = input;
  // Pending workout rows never supply the active schedule or completion count.
  const supplied = input.activePlan;
  const active = supplied?.revision_state === 'active' && supplied.active_revision === supplied.revision &&
    (!plan || (plan.id === supplied.id && plan.active_revision === supplied.revision && plan.week_start === supplied.week_start)) ? supplied : null;
  const pending = plan?.revision_state === 'pending_approval' && plan.proposal?.state === 'pending';
  const weekStart = active?.week_start ?? plan?.week_start ?? draft?.week_start ?? currentWeekStart(today);
  const known = !!(plan || draft || active);
  const readState = input.resumeState === 'loading' || input.activeReadState === 'loading' ? 'loading'
    : input.resumeState === 'failed' || input.activeReadState === 'failed' ? 'failed' : 'ready';
  const state: WeekState = !known && readState !== 'ready' ? readState : active ? pending ? 'activePending' : 'active'
    : draft ? draft.state === 'placement' ? 'placement' : 'draft' : pending ? 'pending'
      : plan?.revision_state === 'rejected' ? 'rejected' : plan?.revision_state === 'expired' ? 'expired' : plan ? 'unavailable' : 'noPlan';
  const workouts = active?.workouts.filter((item) => item.status !== 'cancelled') ?? [];
  const date = workouts.some((item) => item.scheduled_date === today) ? today
    : workouts.map((item) => item.scheduled_date).filter((value) => value > today).sort()[0] ?? null;
  const sessions = workouts.filter((item) => item.scheduled_date === date).map((item) => ({ id: item.id, summary: workoutSummaryViewModel(item) }));
  const rest = active?.rest_days.find((item) => item.date === today);
  const restOnly = active && workouts.length === 0 && active.rest_days.length > 0;
  const empty = active ? rest?.reason === 'restriction_rest' || (restOnly && active.rest_days.some((item) => item.reason === 'restriction_rest')) ? 'restrictedRest'
    : rest || restOnly ? 'rest' : date === null ? 'noFuture' : null : state === 'noPlan' ? 'noPlan' : null;
  const attention: WeekAttention[] = [];
  if (draft && draft.state !== 'submitted') attention.push({ kind: 'draft', action: 'draft' });
  if (pending) attention.push({ kind: 'proposal', action: 'review' });
  if (plan?.warnings.length || draft?.warnings.length || active?.warnings.length) attention.push({ kind: 'warnings', action: pending ? 'review' : draft ? 'draft' : 'planning' });
  return {
    weekStart, weekEnd: isoDate(addDays(weekStart, 6)), state, sessions, sessionDate: date, isToday: date === today,
    progress: active ? { completed: workouts.filter((item) => item.status === 'completed').length, planned: workouts.length } : null,
    empty, attention, mainAction: sessions.length ? null : draft ? 'draft' : pending ? 'review'
      : state === 'noPlan' ? 'prepare' : ['rejected', 'expired', 'unavailable'].includes(state) ? 'planning' : null, readState
  };
}
