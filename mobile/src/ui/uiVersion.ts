export type UiVersion = 'v1' | 'v2';

export const implementedSlices = { workoutDetail: true, week: true, calendar: true, planningCreation: true, proposalReview: true, activities: true } as const;

// V1 remains the default/rollback presentation. Explicit V2 works in release builds too.
export function initialUiVersion(flag?: string): UiVersion {
  return flag === 'v2' ? 'v2' : 'v1';
}

export function effectiveUiVersion(requested: UiVersion, slice: string): UiVersion {
  return requested === 'v2' && Object.hasOwn(implementedSlices, slice) ? 'v2' : 'v1';
}
