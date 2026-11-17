const primary = '#124D43';
const primarySoft = '#E7EFE8';

export const colors = {
  background: '#FAFAF6',
  surface: '#FFFEFA',
  surfaceElevated: '#FFFFFF',
  surfaceSubtle: '#E9EEE8',
  primary,
  primaryPressed: '#082E2A',
  primarySoft,
  secondary: primarySoft,
  text: '#071E22',
  textMuted: '#526874',
  textInverse: '#FFFEFA',
  border: '#DFE6E1',
  borderControl: '#70837D',
  focus: primary,
  success: '#2D6A52',
  successSoft: '#E4F0E8',
  warning: '#79520E',
  warningSoft: '#F8EED6',
  destructive: '#A23B2A',
  destructiveSoft: '#FBE5DF',
  sport: {
    run: { text: '#8F442F', soft: '#F5E8DF' },
    bike: { text: '#405C45', soft: '#E6ECE2' },
    swim: { text: '#285E70', soft: '#E2EDF0' },
  },
  scrim: 'rgba(16,43,40,0.28)',
  landscape: { sage: '#76A396', sun: '#FFE3A6' },
} as const;
