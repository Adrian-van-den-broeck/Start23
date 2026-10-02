import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { colors, layout, radius, space, typography } from './index';

test('semantic colors match every approved Astra table entry', () => {
  const contract = readFileSync(join(__dirname, '../../../../docs/ui/WOMBO_UI_V2_TOKENS.md'), 'utf8');
  const entries = [...contract.matchAll(/\| `([^`]+)` \| `(#[A-Fa-f0-9]{6}|rgba\([^`]+\))` \|/g)];
  const flat: Record<string, string> = {
    background: colors.background, surface: colors.surface, 'surface.elevated': colors.surfaceElevated,
    'surface.subtle': colors.surfaceSubtle, primary: colors.primary, 'primary.pressed': colors.primaryPressed,
    'primary.soft': colors.primarySoft, secondary: colors.secondary, text: colors.text, 'text.muted': colors.textMuted,
    'text.inverse': colors.textInverse, border: colors.border, 'border.control': colors.borderControl,
    focus: colors.focus, success: colors.success, 'success.soft': colors.successSoft, warning: colors.warning,
    'warning.soft': colors.warningSoft, destructive: colors.destructive, 'destructive.soft': colors.destructiveSoft,
    'sport.run': colors.sport.run.text, 'sport.run.soft': colors.sport.run.soft,
    'sport.bike': colors.sport.bike.text, 'sport.bike.soft': colors.sport.bike.soft,
    'sport.swim': colors.sport.swim.text, 'sport.swim.soft': colors.sport.swim.soft, scrim: colors.scrim,
  };
  expect(entries).toHaveLength(Object.keys(flat).length);
  for (const [, name, value] of entries) expect(flat[name]).toBe(value);
});

test('spacing, typography and targets retain approved scalable dimensions', () => {
  expect(Object.values(space)).toEqual([4, 8, 12, 16, 24, 32, 48]);
  expect(radius).toEqual({ inset: 8, control: 12, card: 20, sheet: 28, pill: 999 });
  expect(layout.readingWidth).toBe(600);
  expect(layout.touch).toBe(48);
  expect(layout.primaryButton).toBe(52);
  expect(typography.screenTitle).toEqual({ fontSize: 28, lineHeight: 34, fontWeight: '700' });
});

function luminance(hex: string) {
  const channels = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16) / 255)
    .map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function contrast(a: string, b: string) {
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test('all text pairs used by this slice, including disabled and high intensity, meet 4.5:1', () => {
  const pairs = [
    [colors.text, colors.background], [colors.text, colors.surface], [colors.text, colors.surfaceSubtle],
    [colors.textMuted, colors.surface], [colors.textMuted, colors.background],
    [colors.primary, colors.background], [colors.primary, colors.secondary],
    [colors.textInverse, colors.primary], [colors.textInverse, colors.primaryPressed],
    [colors.warning, colors.surface],
    ...Object.values(colors.sport).map((sport) => [sport.text, sport.soft]),
  ];
  for (const [foreground, background] of pairs) expect(contrast(foreground, background)).toBeGreaterThanOrEqual(4.5);
  expect(contrast(colors.borderControl, colors.background)).toBeGreaterThanOrEqual(3);
});
