import { resolvePresentation } from '../ui-v3/presentation';

export type UiVersion = 'v1' | 'v2';

export const implementedSlices = { workoutDetail: true, week: true, calendar: true, planningCreation: true, proposalReview: true, activities: true } as const;

// V3 shares the existing controller-backed V2 route adapters.
export function initialUiVersion(flag?: string): UiVersion {
  return resolvePresentation(flag) === 'v1' ? 'v1' : 'v2';
}

export function effectiveUiVersion(requested: UiVersion, slice: string): UiVersion {
  return requested === 'v2' && Object.hasOwn(implementedSlices, slice) ? 'v2' : 'v1';
}
