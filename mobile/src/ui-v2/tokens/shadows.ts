import { colors } from './colors';

const soft = {
  shadowColor: colors.primary, shadowOpacity: 0.06,
  shadowOffset: { width: 0, height: 3 }, shadowRadius: 12, elevation: 2,
} as const;

export const shadows = {
  card: soft,
  floatingNav: soft,
  lift: {
    shadowColor: colors.primary, shadowOpacity: 0.12,
    shadowOffset: { width: 0, height: 4 }, shadowRadius: 16, elevation: 6,
  },
} as const;
