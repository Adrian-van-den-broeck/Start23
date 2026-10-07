export const space = { 4: 4, 8: 8, 12: 12, 16: 16, 24: 24, 32: 32, 48: 48 } as const;
export const radius = { inset: 8, control: 12, button: 16, card: 20, sheet: 28, pill: 999 } as const;
const focusPadding = space[24];
export const layout = {
  phoneGutter: 16, wideGutter: 24, readingWidth: 600, cardPadding: 16,
  focusPadding, formPadding: focusPadding, touch: 48, primaryButton: 56,
  secondaryButton: 52, fieldHeight: 56, multilineFieldHeight: 112,
  fieldGroupGap: space[24], labelFieldGap: space[8], fieldHelpGap: space[4],
  controlEdge: 1, decorativeLine: 1, focusOutline: 2,
  segmentedInset: space[4], segmentedHeight: 56,
  iconDisc: { field: 40, row: 48, focus: 64 },
  sectionGap: space[24], majorHeadingGap: space[32],
  iconGap: space[12], navigationIconGap: space[8], heroIconGap: space[16],
  actionRow: 64, iconButton: 48,
  bottomNav: { minHeight: 64, inset: space[4], horizontalMargin: space[12],
    bottomGap: space[8], destinationHeight: 56, stackedIconGap: space[4] },
  taskActionInset: { top: space[12], horizontal: space[16], bottom: space[12] },
  headerUtility: { minHeight: 48, horizontalPadding: space[16], gap: space[8], chevron: 20 },
  artwork: { normal: 140, compact: 96, max: 180, fade: 56 },
} as const;

export function focusCardPadding(width: number, fontScale: number) {
  return width >= 393 && fontScale === 1 ? layout.focusPadding : layout.cardPadding;
}
