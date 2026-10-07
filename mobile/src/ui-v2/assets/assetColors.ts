import { colors } from '../tokens/colors';

// Compatibility names for the accepted artwork; the V2 palette is authoritative.
export const assetColors = {
  canvas: colors.background,
  forest: colors.primary,
  sage: colors.landscape.sage,
  sun: colors.landscape.sun,
  soft: colors.primarySoft,
  ivory: colors.surface,
  text: colors.text,
  muted: colors.textMuted,
} as const;
