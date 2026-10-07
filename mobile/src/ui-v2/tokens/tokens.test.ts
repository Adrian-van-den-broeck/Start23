import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { colors, focusCardPadding, layout, radius, space, typography } from './index';

function finalContract() {
  // Works in the integrated worktree and after the batch is merged into root.
  let directory = __dirname;
  while (dirname(directory) !== directory) {
    const path = join(directory, 'docs/ui/WOMBO_UI_V2_FINAL_TOKENS.md');
    if (existsSync(path)) return readFileSync(path, 'utf8');
    directory = dirname(directory);
  }
  throw new Error('Authoritative FINAL token contract missing');
}

test('one V2 palette implements every FINAL color row including aliases and artwork', () => {
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
    'landscape.sage': colors.landscape.sage, 'landscape.sun': colors.landscape.sun,
  };
  const seen: string[] = [];
  const table = finalContract().split('## Typography')[0];
  for (const row of table.split('\n').filter((line) => line.startsWith('| `'))) {
    const columns = row.split('|');
    const names = [...columns[1].matchAll(/`([^`]+)`/g)].map((match) => match[1]);
    const final = columns[3].split('\u2192').pop()!;
    const values = [...final.matchAll(/#[A-Fa-f0-9]{6}|rgba\([^`]+\)/g)].map((match) => match[0]);
    names.forEach((name, index) => {
      const key = name.startsWith('.') ? names[0] + name : name;
      const alias = final.match(/alias `([^`]+)`/);
      expect(flat[key]).toBe(alias ? flat[alias[1]] : values[index]);
      seen.push(key);
    });
  }
  expect(seen.sort()).toEqual(Object.keys(flat).sort());
});

test('FINAL scalable typography matches the document rather than superseded V2 values', () => {
  const seen: string[] = [];
  const table = finalContract().split('## Typography')[1].split('## Spacing')[0];
  for (const row of table.split('\n').filter((line) => line.startsWith('| `'))) {
    const columns = row.split('|');
    const name = columns[1].match(/`([^`]+)`/)![1].replace('numeric.compact', 'numericCompact') as keyof typeof typography;
    const values = columns[3].match(/\*\*(\d+)\/(\d+)\/(\d+)\*\*/)!;
    expect(typography[name]).toMatchObject({ fontSize: Number(values[1]), lineHeight: Number(values[2]), fontWeight: values[3] });
    seen.push(name);
  }
  expect(seen.sort()).toEqual(Object.keys(typography).sort());
});

test('FINAL layout roles keep the single scale, responsive padding and minimum metrics', () => {
  expect(Object.values(space)).toEqual([4, 8, 12, 16, 24, 32, 48]);
  expect(radius).toEqual({ inset: 8, control: 12, button: 16, card: 20, sheet: 28, pill: 999 });
  expect(layout).toMatchObject({ readingWidth: 600, touch: 48, primaryButton: 56, secondaryButton: 52, fieldHeight: 56,
    multilineFieldHeight: 112, segmentedHeight: 56, segmentedInset: 4, fieldGroupGap: 24, labelFieldGap: 8, fieldHelpGap: 4 });
  expect(layout.formPadding).toBe(layout.focusPadding);
  expect(focusCardPadding(393, 1)).toBe(24);
  expect(focusCardPadding(320, 1)).toBe(16);
  expect(focusCardPadding(412, 2)).toBe(16);
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

test('every informative FINAL text pair reaches 4.5 and control/focus edges reach 3 without rounding', () => {
  const pairs = [
    ...[colors.background, colors.surface, colors.surfaceSubtle, colors.primarySoft].flatMap((fill) =>
      [[colors.text, fill], [colors.textMuted, fill]]),
    [colors.primary, colors.primarySoft], [colors.primary, colors.surface],
    [colors.textInverse, colors.primary], [colors.textInverse, colors.primaryPressed],
    [colors.success, colors.successSoft], [colors.warning, colors.warningSoft],
    [colors.destructive, colors.destructiveSoft], [colors.destructive, colors.surface],
    ...Object.values(colors.sport).map((sport) => [sport.text, sport.soft]),
  ];
  for (const [foreground, background] of pairs) expect(contrast(foreground, background)).toBeGreaterThanOrEqual(4.5);
  for (const [edge, fill] of [[colors.borderControl, colors.surface], [colors.focus, colors.surface],
    [colors.textInverse, colors.primary], [colors.destructive, colors.surface]]) {
    expect(contrast(edge, fill)).toBeGreaterThanOrEqual(3);
  }
});
