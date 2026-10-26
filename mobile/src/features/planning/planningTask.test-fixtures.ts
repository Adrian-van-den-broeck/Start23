import type { WeeklyPlan } from '../../api/types';
import { activePlan, proposal, workout } from './planning.test-fixtures';

export const nextProposal = { ...proposal, id: 'next-proposal', base_plan_revision: 0, target_plan_revision_id: 'next-revision-1' };
export const nextWorkout = { ...workout, id: 'next-workout-1', template_id: 'next-template', template_key: 'next-template-key', discipline: 'bike' as const, name: 'Next week supplied bike', scheduled_date: '2026-10-14' };
export const pendingNext: WeeklyPlan = {
  ...activePlan, id: 'next-plan', week_start: '2026-10-12', state: 'pending_approval', active_revision: null,
  revision: 1, revision_id: 'next-revision-1', revision_state: 'pending_approval',
  available_dates: ['2026-10-12', '2026-10-14', '2026-10-17'],
  confirmed_injuries: ['run', 'swim'], low_only_disciplines: ['bike'],
  workouts: [nextWorkout, { ...nextWorkout, id: 'next-workout-2', name: 'Repeated supplied bike' }], proposal: nextProposal,
};
export const approvedNext: WeeklyPlan = { ...pendingNext, state: 'active', active_revision: 1, revision_state: 'active', proposal: { ...nextProposal, state: 'applied' } };
