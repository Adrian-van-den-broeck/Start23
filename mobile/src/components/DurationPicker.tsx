import { useMemo, useState, type RefObject } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Icon } from '../ui-v2/primitives/Icon';
import { formatClockDuration } from '../lib/onboardingForms';
import { colors, radius, spacing } from '../theme/tokens';
import { colors as finalColors, layout, radius as finalRadius, space, typography } from '../ui-v2/tokens';

type DurationUnit = 'hours' | 'minutes' | 'seconds';

type DurationPickerProps = {
  label: string;
  valueSeconds: number | null;
  onChange: (valueSeconds: number | null) => void;
  error?: string;
  hint?: string;
  required?: boolean;
  maxHours?: number;
  appearance?: 'default' | 'final';
  focusRef?: RefObject<View | null>;
};

const unitCopy: Record<
  DurationUnit,
  { label: string; singular: string; short: string }
> = {
  hours: { label: 'uren', singular: 'uur', short: 'uur' },
  minutes: { label: 'minuten', singular: 'minuut', short: 'min' },
  seconds: { label: 'seconden', singular: 'seconde', short: 'sec' },
};

function parts(valueSeconds: number | null) {
  const safe = Math.max(0, valueSeconds ?? 0);
  return {
    hours: Math.floor(safe / 3600),
    minutes: Math.floor((safe % 3600) / 60),
    seconds: safe % 60,
  };
}

export function DurationPicker({
  label,
  valueSeconds,
  onChange,
  error,
  hint,
  required = false,
  maxHours = 168,
  appearance = 'default',
  focusRef,
}: DurationPickerProps) {
  const [focusedControl, setFocusedControl] = useState<string | null>(null);
  const [pressedControl, setPressedControl] = useState<string | null>(null);
  const controlProps = (key: string) => ({ onPressIn: () => setPressedControl(key), onPressOut: () => setPressedControl(null), ...(appearance === 'final' ? {
    onFocus: () => setFocusedControl(key), onBlur: () => setFocusedControl(null),
  } : {}) });
  const focusRing = (key: string) => appearance === 'final' && focusedControl === key ?
    <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" style={finalStyles.focus} /> : null;
  const styles = appearance === 'final' ? finalStyles : legacyStyles;
  const [openUnit, setOpenUnit] = useState<DurationUnit | null>(null);
  const value = parts(valueSeconds);
  const atMaximumDuration = (valueSeconds ?? 0) >= maxHours * 3600;
  const options = useMemo(
    () =>
      openUnit === 'hours'
        ? Array.from({ length: maxHours + 1 }, (_, index) => index)
        : Array.from({ length: 60 }, (_, index) => index),
    [maxHours, openUnit],
  );

  const setPart = (unit: DurationUnit, nextValue: number) => {
    const next = { ...value, [unit]: nextValue };
    onChange(
      Math.min(
        maxHours * 3600,
        next.hours * 3600 + next.minutes * 60 + next.seconds,
      ),
    );
  };

  const adjust = (unit: DurationUnit, delta: number) => {
    const maximum = unit === 'hours' ? maxHours : 59;
    setPart(unit, Math.min(maximum, Math.max(0, value[unit] + delta)));
  };

  return (
    <View style={styles.group}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>
          {label}
          {required ? ' *' : ''}
        </Text>
        {!required && valueSeconds !== null ? (
          <Pressable
            {...controlProps('clear')}
            accessibilityLabel={`${label} wissen`}
            accessibilityRole="button"
            onPress={() => onChange(null)}
            style={styles.clearButton}
          >
            <Text style={styles.clearText}>Wissen</Text>{focusRing('clear')}
          </Pressable>
        ) : null}
      </View>

      <Text
        accessibilityLabel={`${label}: ${
          valueSeconds === null
            ? 'nog niet ingesteld'
            : formatClockDuration(valueSeconds)
        }`}
        style={[styles.result, error ? styles.resultError : null]}
      >
        {valueSeconds === null
          ? 'Nog niet ingesteld'
          : formatClockDuration(valueSeconds)}
      </Text>

      <View style={styles.units}>
        {(Object.keys(unitCopy) as DurationUnit[]).map((unit) => (
          <View key={unit} style={styles.unitCard}>
            <Text style={styles.unitLabel}>{unitCopy[unit].label}</Text>
            <View style={styles.stepper}>
              <Pressable
                {...controlProps(unit + '-decrease')}
                accessibilityLabel={`Verlaag ${unitCopy[unit].label} voor ${label}`}
                accessibilityRole="button"
                disabled={value[unit] === 0}
                onPress={() => adjust(unit, -1)}
                style={[
                  styles.stepButton,
                  value[unit] === 0 && styles.disabled,
                  pressedControl === (unit + '-decrease') && styles.pressed,
                ]}
              >
                {appearance === 'final' ? <Icon name="minus" /> : <Text style={styles.stepButtonText}>-</Text>}{focusRing(unit + '-decrease')}
              </Pressable>
              <Pressable
                ref={unit === 'hours' ? focusRef : undefined}
                {...controlProps(unit + '-choose')}
                accessibilityLabel={`Kies ${unitCopy[unit].label} voor ${label}`}
                accessibilityRole="button"
                onPress={() => setOpenUnit(unit)}
                style={[
                  styles.valueButton,
                  pressedControl === (unit + '-choose') && styles.pressed,
                ]}
              >
                <Text style={styles.valueText}>
                  {String(value[unit]).padStart(2, '0')}
                </Text>{focusRing(unit + '-choose')}
              </Pressable>
              <Pressable
                {...controlProps(unit + '-increase')}
                accessibilityLabel={`Verhoog ${unitCopy[unit].label} voor ${label}`}
                accessibilityRole="button"
                disabled={
                  atMaximumDuration ||
                  value[unit] === (unit === 'hours' ? maxHours : 59)
                }
                onPress={() => adjust(unit, 1)}
                style={[
                  styles.stepButton,
                  (atMaximumDuration ||
                    value[unit] === (unit === 'hours' ? maxHours : 59)) &&
                    styles.disabled,
                  pressedControl === (unit + '-increase') && styles.pressed,
                ]}
              >
                {appearance === 'final' ? <Icon name="add" /> : <Text style={styles.stepButtonText}>+</Text>}{focusRing(unit + '-increase')}
              </Pressable>
            </View>
          </View>
        ))}
      </View>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}

      <Modal
        animationType="slide"
        onRequestClose={() => setOpenUnit(null)}
        transparent
        visible={openUnit !== null}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                Kies {openUnit ? unitCopy[openUnit].label : ''}
              </Text>
              <Pressable
                {...controlProps('close')}
                accessibilityLabel="Duurkeuze sluiten"
                accessibilityRole="button"
                onPress={() => setOpenUnit(null)}
                style={styles.closeButton}
              >
                <Text style={styles.closeText}>Sluiten</Text>{focusRing('close')}
              </Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.optionGrid}>
              {openUnit
                ? options.map((option) => {
                    const selected = value[openUnit] === option;
                    const copy = `${option} ${
                      option === 1
                        ? unitCopy[openUnit].singular
                        : unitCopy[openUnit].short
                    }`;
                    return (
                      <Pressable
                        {...controlProps('option-' + option)}
                        accessibilityRole="radio"
                        accessibilityState={{ selected }}
                        key={option}
                        onPress={() => {
                          setPart(openUnit, option);
                          setOpenUnit(null);
                        }}
                        style={[
                          styles.option,
                          selected && styles.optionSelected,
                          pressedControl === ('option-' + option) && styles.pressed,
                        ]}
                      >
                        <Text
                          style={[
                            styles.optionText,
                            selected && styles.optionTextSelected,
                          ]}
                        >
                          {copy}
                        </Text>{focusRing('option-' + option)}
                      </Pressable>
                    );
                  })
                : null}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const legacyStyles = StyleSheet.create({
  group: { gap: spacing.xs },
  labelRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  label: { color: colors.ink, fontSize: 13, fontWeight: '700' },
  clearButton: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs },
  clearText: { color: colors.accentDark, fontSize: 13, fontWeight: '800' },
  result: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.lineStrong,
    borderRadius: radius.md,
    borderWidth: 1,
    color: colors.brandDeep,
    fontSize: 25,
    fontVariant: ['tabular-nums'],
    fontWeight: '900',
    letterSpacing: 1.5,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    textAlign: 'center',
  },
  resultError: { borderColor: colors.danger, borderWidth: 2 },
  units: { gap: spacing.xs },
  unitCard: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  unitLabel: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '800',
    width: 72,
    textTransform: 'uppercase',
  },
  stepper: {
    alignItems: 'center',
    flex: 1,
    flexDirection: 'row',
    gap: spacing.xs,
  },
  stepButton: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  stepButtonText: { color: colors.brandDeep, fontSize: 23, fontWeight: '900' },
  valueButton: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.sm,
    borderWidth: 1,
    flex: 1,
    height: 48,
    justifyContent: 'center',
  },
  valueText: {
    color: colors.ink,
    fontSize: 17,
    fontVariant: ['tabular-nums'],
    fontWeight: '900',
  },
  disabled: { opacity: 0.35 },
  pressed: { opacity: 0.72 },
  error: { color: colors.danger, fontSize: 12, lineHeight: 17 },
  hint: { color: colors.inkMuted, fontSize: 12, lineHeight: 17 },
  modalBackdrop: {
    backgroundColor: 'rgba(8, 46, 42, 0.45)',
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    maxHeight: '72%',
    padding: spacing.md,
  },
  modalHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  modalTitle: { color: colors.ink, fontSize: 20, fontWeight: '900' },
  closeButton: { padding: spacing.sm },
  closeText: { color: colors.brand, fontSize: 14, fontWeight: '900' },
  optionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    paddingBottom: spacing.xl,
  },
  option: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
    minHeight: 48,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
  },
  optionSelected: { backgroundColor: colors.brand },
  optionText: { color: colors.ink, fontSize: 14, fontWeight: '700' },
  optionTextSelected: { color: colors.white },
});

const finalStyles = StyleSheet.create({
  focus: { ...StyleSheet.absoluteFill, borderColor: finalColors.focus, borderWidth: layout.focusOutline, borderRadius: finalRadius.control },
  ...legacyStyles,
  group: { gap: space[8] },
  labelRow: { gap: space[8] },
  label: { ...typography.label, color: finalColors.text },
  clearButton: { minWidth: layout.touch, minHeight: layout.touch, justifyContent: 'center', padding: space[8], borderRadius: finalRadius.control },
  clearText: { ...typography.label, color: finalColors.primary },
  result: { ...typography.body, fontWeight: '600', fontVariant: ['tabular-nums'], color: finalColors.primary, backgroundColor: finalColors.primarySoft, borderColor: finalColors.borderControl, borderWidth: layout.controlEdge, borderRadius: finalRadius.control, padding: space[12] },
  resultError: { borderColor: finalColors.destructive, borderWidth: layout.focusOutline },
  units: { gap: space[16] },
  unitCard: { gap: space[8] },
  unitLabel: { ...typography.label, color: finalColors.textMuted },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: space[8] },
  stepButton: { minWidth: layout.touch, minHeight: layout.touch, alignItems: 'center', justifyContent: 'center', backgroundColor: finalColors.primarySoft, borderRadius: finalRadius.control, padding: space[8] },
  stepButtonText: { ...typography.button, color: finalColors.primary },
  valueButton: { flex: 1, minWidth: layout.touch, minHeight: layout.touch, alignItems: 'center', justifyContent: 'center', padding: space[8], backgroundColor: finalColors.surface, borderColor: finalColors.borderControl, borderWidth: layout.controlEdge, borderRadius: finalRadius.control },
  valueText: { ...typography.numericCompact, fontVariant: ['tabular-nums'], color: finalColors.text },
  disabled: { backgroundColor: finalColors.surfaceSubtle },
  error: { ...typography.supporting, color: finalColors.destructive },
  hint: { ...typography.supporting, color: finalColors.textMuted },
  modalBackdrop: { backgroundColor: finalColors.scrim, flex: 1, justifyContent: 'flex-end' },
  modalCard: { backgroundColor: finalColors.surface, borderTopLeftRadius: finalRadius.sheet, borderTopRightRadius: finalRadius.sheet, maxHeight: '80%', padding: space[16] },
  modalHeader: { gap: space[8], marginBottom: space[16] },
  modalTitle: { ...typography.sectionTitle, color: finalColors.text },
  closeButton: { minWidth: layout.touch, minHeight: layout.touch, justifyContent: 'center', padding: space[12], backgroundColor: finalColors.primarySoft, borderRadius: finalRadius.button },
  closeText: { ...typography.button, color: finalColors.primary },
  optionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8], paddingBottom: space[32] },
  option: { minWidth: layout.touch, minHeight: layout.touch, padding: space[12], justifyContent: 'center', alignItems: 'center', backgroundColor: finalColors.primarySoft, borderRadius: finalRadius.control },
  optionSelected: { backgroundColor: finalColors.primary },
  optionText: { ...typography.label, color: finalColors.text },
  optionTextSelected: { color: finalColors.textInverse },
});
