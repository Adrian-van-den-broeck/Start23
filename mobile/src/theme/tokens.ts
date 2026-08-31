export const colors = {
  canvas: '#F4F2EC',
  canvasDeep: '#EAEDE5',
  surface: '#FFFEFA',
  surfaceRaised: '#FFFFFF',
  surfaceMuted: '#E9EEE8',
  ink: '#102B28',
  inkMuted: '#5D706B',
  inkFaint: '#5F716C',
  brand: '#123F39',
  brandDeep: '#082E2A',
  brandMid: '#1D554D',
  brandSoft: '#DCEBE3',
  accent: '#B83D27',
  accentDark: '#8F2A18',
  accentSoft: '#FDE5DD',
  highlight: '#E8B95B',
  highlightSoft: '#F8EED6',
  danger: '#A23B2A',
  dangerSoft: '#FBE5DF',
  success: '#2D6A52',
  line: '#D9E0DA',
  lineStrong: '#70837D',
  white: '#FFFFFF',
} as const;

export const spacing = {
  xs: 6,
  sm: 10,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  xs: 8,
  sm: 12,
  md: 20,
  lg: 28,
  xl: 36,
  pill: 999,
} as const;

export const shadows = {
  card: {
    elevation: 3,
    shadowColor: colors.brandDeep,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 18,
  },
  floating: {
    elevation: 8,
    shadowColor: colors.brandDeep,
    shadowOffset: { height: 12, width: 0 },
    shadowOpacity: 0.14,
    shadowRadius: 24,
  },
} as const;

export const motion = {
  duration: {
    fast: 140,
    base: 220,
    slow: 360,
  },
  spring: {
    damping: 18,
    mass: 0.72,
    stiffness: 230,
  },
} as const;
