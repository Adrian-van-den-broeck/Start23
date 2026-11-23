export type Presentation = 'v1' | 'v2' | 'v3';

export function resolvePresentation(value?: string): Presentation {
  if (value === 'v3') return 'v3';
  if (value === undefined) return 'v3';
  return value === 'v2' ? 'v2' : 'v1';
}

// Expo inlines the flag into the bundle. No account or device state is written.
export const studioPresentation = resolvePresentation(process.env.EXPO_PUBLIC_UI_VERSION) === 'v3';
