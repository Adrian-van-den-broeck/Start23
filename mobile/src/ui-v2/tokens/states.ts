import { colors } from './colors';

export const states = {
  primary: { backgroundColor: colors.primary, color: colors.textInverse },
  pressed: { backgroundColor: colors.primaryPressed, color: colors.textInverse },
  disabled: { backgroundColor: colors.surfaceSubtle, color: colors.text },
  selected: { backgroundColor: colors.primarySoft, color: colors.primary },
  focus: { borderColor: colors.focus, borderWidth: 2 },
} as const;
