export type UiVersion = 'v1' | 'v2';

export const implementedSlices = { workoutDetail: true, week: true, calendar: true, planningCreation: true } as const;

export function initialUiVersion(isDevelopment: boolean, flag?: string): UiVersion {
  return isDevelopment && flag === 'v2' ? 'v2' : 'v1';
}

export function effectiveUiVersion(
  isDevelopment: boolean,
  requested: UiVersion,
  slice: string,
): UiVersion {
  return isDevelopment && requested === 'v2' &&
    Object.hasOwn(implementedSlices, slice) ? 'v2' : 'v1';
}
