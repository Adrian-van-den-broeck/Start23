import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { Card } from '../../ui-v2/primitives/Card';
import { ChoiceRow } from '../../ui-v2/primitives/ChoiceRow';
import { Divider } from '../../ui-v2/primitives/Divider';
import { Icon, type IconName } from '../../ui-v2/primitives/Icon';
import { IconTile } from '../../ui-v2/primitives/IconTile';
import { Text } from '../../ui-v2/primitives/Text';
import { colors, layout, radius, space } from '../../ui-v2/tokens';
import { studioPresentation } from '../presentation';

// Shared layout for the screens behind Week and Calendar: check-in, calibration,
// zones, profile, integrations, activities and proposal review.

// Vertical rhythm between the groups of a screen.
export const screenGap = studioPresentation ? space[16] : space[24];

// One group of a longer screen. V3 keeps it flat on the page and separates
// groups with a hairline; V2 keeps its card.
export function Panel({ children, style, divided = true, testID }: {
  children: ReactNode; style?: StyleProp<ViewStyle>; divided?: boolean; testID?: string;
}) {
  if (!studioPresentation) return <Card elevated padding="form" testID={testID} style={[styles.card, style]}>{children}</Card>;
  return <View testID={testID} style={[styles.panel, divided && styles.divided, style]}>{children}</View>;
}

// Content that V2 groups in a card and V3 leaves on the page.
export function Surface({ children, style, padding, elevated = true, testID }: {
  children: ReactNode; style?: StyleProp<ViewStyle>; padding?: 'standard' | 'focus' | 'form'; elevated?: boolean; testID?: string;
}) {
  if (studioPresentation) return <View testID={testID} style={style}>{children}</View>;
  return <Card testID={testID} padding={padding} elevated={elevated} style={style}>{children}</Card>;
}

// The rule between the parts of a V2 card. V3 spaces the same parts instead.
export function CardDivider() {
  return studioPresentation ? null : <Divider />;
}

export function Kicker({ children, tone = 'primary' }: { children: string; tone?: 'primary' | 'warning' | 'textMuted' }) {
  return <Text variant="caption" tone={tone} style={styles.kicker}>{children}</Text>;
}

export function Heading({ title, kicker, kickerTone, description, trailing, variant = 'sectionTitle' }: {
  title: string; kicker?: string; kickerTone?: 'primary' | 'warning'; description?: string; trailing?: ReactNode;
  variant?: 'sectionTitle' | 'cardTitle' | 'label';
}) {
  return <View style={styles.heading}>
    {kicker ? <Kicker tone={kickerTone}>{kicker}</Kicker> : null}
    <View style={styles.headingRow}>
      <Text variant={variant} accessibilityRole="header" style={styles.grow}>{title}</Text>
      {trailing}
    </View>
    {description ? <Text variant={studioPresentation ? 'supporting' : 'body'} tone="textMuted">{description}</Text> : null}
  </View>;
}

// A labelled set of controls inside a panel.
export function Group({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <View style={styles.group}>
    <Text variant="label">{label}</Text>
    {children}
    {hint ? <Text variant="supporting" tone="textMuted">{hint}</Text> : null}
  </View>;
}

const tagTones = {
  primary: { fill: colors.primarySoft, ink: colors.primary },
  warning: { fill: colors.warningSoft, ink: colors.warning },
  success: { fill: colors.successSoft, ink: colors.success },
  destructive: { fill: colors.destructiveSoft, ink: colors.destructive },
  neutral: { fill: colors.surfaceSubtle, ink: colors.textMuted },
} as const;

// A short state label. The text carries the meaning; the tint only supports it.
export function Tag({ label, tone = 'primary' }: { label: string; tone?: keyof typeof tagTones }) {
  const tint = tagTones[tone];
  return <View style={[styles.tag, { backgroundColor: tint.fill }]}>
    <Text variant={studioPresentation ? 'caption' : 'supporting'} style={{ color: tint.ink }}>{label}</Text>
  </View>;
}

export type ChoiceOption<T extends string | number> = Readonly<{ value: T; label: string; accessibilityLabel?: string; disabled?: boolean }>;

// A short set of options. V3 lays them out as wrapping chips so four levels or
// seven reasons take one or two lines; V2 keeps one full-width row per option.
export function ChoiceChips<T extends string | number>({ mode, options, isSelected, onPress, disabled = false, accessibilityLabel }: {
  mode: 'radio' | 'checkbox'; options: readonly ChoiceOption<T>[]; isSelected: (value: T) => boolean;
  onPress: (value: T) => void; disabled?: boolean; accessibilityLabel?: string;
}) {
  return <View accessibilityRole={mode === 'radio' ? 'radiogroup' : undefined}
    accessibilityLabel={accessibilityLabel} style={studioPresentation ? styles.chips : styles.rows}>
    {options.map((option) => studioPresentation
      ? <Chip key={String(option.value)} mode={mode} label={option.label} accessibilityLabel={option.accessibilityLabel}
        selected={isSelected(option.value)} disabled={disabled || option.disabled === true} onPress={() => onPress(option.value)} />
      : <ChoiceRow key={String(option.value)} mode={mode} label={option.label} accessibilityLabel={option.accessibilityLabel}
        selected={isSelected(option.value)} disabled={disabled || option.disabled === true} onPress={() => onPress(option.value)} />)}
  </View>;
}

function Chip({ mode, label, accessibilityLabel = label, selected, disabled, onPress }: {
  mode: 'radio' | 'checkbox'; label: string; accessibilityLabel?: string; selected: boolean; disabled: boolean; onPress: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  // The chip is 40 high; the slop keeps the 48 touch target.
  return <Pressable accessibilityRole={mode} accessibilityLabel={accessibilityLabel}
    accessibilityState={{ checked: selected, disabled }} disabled={disabled} onPress={onPress} hitSlop={chipSlop}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    style={[styles.chip, selected && styles.chipSelected, disabled && styles.chipDisabled, pressed && styles.pressed, focused && styles.chipFocused]}>
    <Text variant="label" tone={selected && !disabled ? 'textInverse' : 'text'} accessible={false}>{label}</Text>
  </Pressable>;
}

const chipSlop = { top: 4, bottom: 4 } as const;

export type StripDay = Readonly<{ label: string; date: number }>;

// Seven days in one line, in the manner of the week strip. A marked day is
// filled and carries a cross, so the state never depends on colour alone.
export function DayToggleStrip({ days, isMarked, onToggle, disabled = false }: {
  days: readonly StripDay[]; isMarked: (index: number) => boolean; onToggle: (index: number) => void; disabled?: boolean;
}) {
  return <View style={styles.strip}>
    {days.map((day, index) => <StripCell key={day.label} day={day} marked={isMarked(index)} disabled={disabled} onPress={() => onToggle(index)} />)}
  </View>;
}

function StripCell({ day, marked, disabled, onPress }: { day: StripDay; marked: boolean; disabled: boolean; onPress: () => void }) {
  const [focused, setFocused] = useState(false);
  return <Pressable accessibilityRole="checkbox" accessibilityLabel={day.label} accessibilityState={{ checked: marked, disabled }}
    disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={[styles.cell, focused && styles.cellFocused, disabled && styles.cellDisabled]}>
    <Text variant="caption" tone="textMuted" accessible={false} style={styles.weekday}>{day.label}</Text>
    <View accessible={false} importantForAccessibility="no-hide-descendants" style={[styles.date, marked && styles.dateMarked]}>
      <Text variant="label" tone={marked ? 'textInverse' : 'text'}>{day.date}</Text>
    </View>
    <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.cellMark}>
      {marked ? <Icon name="close" size={20} color={colors.text} /> : null}
    </View>
  </Pressable>;
}

// A destination with a one-line explanation, e.g. the profile's further pages.
export function LinkRow({ icon, label, hint, onPress, disabled = false }: {
  icon: IconName; label: string; hint?: string; onPress: () => void; disabled?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityHint={hint} accessibilityState={{ disabled }}
    disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    style={[styles.link, pressed && styles.linkPressed, disabled && styles.cellDisabled, focused && styles.chipFocused]}>
    <IconTile name={icon} size="field" />
    <View style={styles.linkCopy}>
      <Text variant="label" accessible={false} importantForAccessibility="no">{label}</Text>
      {hint ? <Text variant="supporting" tone="textMuted" accessible={false} importantForAccessibility="no">{hint}</Text> : null}
    </View>
    <Icon name="chevron" size={20} color={colors.textMuted} />
  </Pressable>;
}

// A single-glyph action at the end of a row. The label is what assistive technology reads.
export function IconAction({ icon, label, onPress, disabled = false }: {
  icon: IconName; label: string; onPress: () => void; disabled?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }}
    disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    style={[styles.iconAction, pressed && styles.linkPressed, disabled && styles.cellDisabled, focused && styles.chipFocused]}>
    <Icon name={icon} size={20} color={colors.textMuted} />
  </Pressable>;
}

// A coloured sport mark, the same tile the chosen-workout rows use.
export function SportTile({ discipline }: { discipline: keyof typeof colors.sport }) {
  return <View accessible={false} importantForAccessibility="no-hide-descendants"
    style={[styles.sportTile, { backgroundColor: colors.sport[discipline].soft }]}>
    <Icon name={discipline} color={colors.sport[discipline].text} />
  </View>;
}

const styles = StyleSheet.create({
  grow: { flex: 1, minWidth: 0 },
  card: { gap: layout.fieldGroupGap },
  panel: { gap: space[16] },
  divided: { borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border, paddingTop: space[16] },
  kicker: { textTransform: 'uppercase', letterSpacing: 1 },
  heading: { gap: space[4] },
  group: { gap: space[8] },
  headingRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[8] },
  tag: { alignSelf: 'flex-start', borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] },
  rows: { gap: space[12] },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] },
  chip: { minHeight: 40, minWidth: layout.touch, alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: space[16], paddingVertical: space[8], borderRadius: radius.pill,
    borderWidth: layout.controlEdge, borderColor: colors.borderControl, backgroundColor: colors.surface },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipDisabled: { backgroundColor: colors.surfaceSubtle },
  chipFocused: { borderColor: colors.focus },
  pressed: { opacity: 0.72 },
  strip: { flexDirection: 'row', paddingVertical: space[12], paddingHorizontal: space[4], borderRadius: 20, backgroundColor: colors.surface },
  cell: { flex: 1, minHeight: layout.touch, alignItems: 'center', gap: 6, borderRadius: radius.control,
    borderWidth: layout.focusOutline, borderColor: 'transparent' },
  cellFocused: { borderColor: colors.focus },
  cellDisabled: { opacity: 0.6 },
  weekday: { textTransform: 'uppercase' },
  date: { minWidth: 32, minHeight: 32, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center',
    borderWidth: layout.controlEdge, borderColor: colors.borderControl },
  dateMarked: { backgroundColor: colors.text, borderColor: colors.text },
  cellMark: { minHeight: 20, alignItems: 'center', justifyContent: 'center' },
  link: { minHeight: layout.actionRow, flexDirection: 'row', alignItems: 'center', gap: space[12], paddingVertical: space[8],
    borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: 'transparent' },
  linkPressed: { backgroundColor: colors.primarySoft },
  linkCopy: { flex: 1, minWidth: 0, gap: 2 },
  iconAction: { width: layout.touch, height: layout.touch, alignItems: 'center', justifyContent: 'center',
    borderRadius: radius.pill, borderWidth: layout.focusOutline, borderColor: 'transparent' },
  sportTile: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
});
