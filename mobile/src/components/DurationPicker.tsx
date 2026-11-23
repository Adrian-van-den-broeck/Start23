import { useState, type RefObject } from 'react';
import { StyleSheet, View } from 'react-native';

import { useLanguage, type TranslationKey } from '../i18n/LanguageProvider';
import { formatClockDuration } from '../lib/onboardingForms';
import { BottomSheet } from '../ui-v2/primitives/BottomSheet';
import { Button } from '../ui-v2/primitives/Button';
import { PickerField } from '../ui-v2/primitives/PickerField';
import { Text } from '../ui-v2/primitives/Text';
import { WheelColumn } from '../ui-v2/primitives/WheelColumn';
import { space } from '../ui-v2/tokens';

export type DurationUnit = 'hours' | 'minutes' | 'seconds';
type DurationParts = Record<DurationUnit, number>;

const ALL_UNITS: readonly DurationUnit[] = ['hours', 'minutes', 'seconds'];

type DurationPickerProps = {
  label: string;
  valueSeconds: number | null;
  onChange: (valueSeconds: number | null) => void;
  error?: string;
  hint?: string;
  required?: boolean;
  // Defaults to optional fields only; turn off where a clear button would crowd a small cell.
  clearable?: boolean;
  // Wheels to show, largest first. Without hours, minutes may exceed 59 (e.g. swim times).
  units?: readonly DurationUnit[];
  maxHours?: number;
  maxMinutes?: number;
  // Shown after the value, e.g. "/km" for a pace.
  suffix?: string;
  icon?: boolean;
  focusRef?: RefObject<View | null>;
};

const unitCopy: Record<DurationUnit, { short: TranslationKey; singular: TranslationKey }> = {
  hours: { short: 'onboarding.duration.short.hours', singular: 'onboarding.duration.singular.hours' },
  minutes: { short: 'onboarding.duration.short.minutes', singular: 'onboarding.duration.singular.minutes' },
  seconds: { short: 'onboarding.duration.short.seconds', singular: 'onboarding.duration.singular.seconds' },
};

function split(valueSeconds: number | null, units: readonly DurationUnit[]): DurationParts {
  const safe = Math.max(0, Math.round(valueSeconds ?? 0));
  const hours = units.includes('hours') ? Math.floor(safe / 3600) : 0;
  const minutes = units.includes('minutes') ? Math.floor((safe - hours * 3600) / 60) : 0;
  const seconds = units.includes('seconds') ? safe - hours * 3600 - minutes * 60 : 0;
  return { hours, minutes, seconds };
}

function join(parts: DurationParts): number {
  return parts.hours * 3600 + parts.minutes * 60 + parts.seconds;
}

function format(valueSeconds: number, units: readonly DurationUnit[]): string {
  if (units.includes('hours')) return formatClockDuration(valueSeconds);
  const minutes = Math.floor(valueSeconds / 60);
  return `${minutes}:${String(valueSeconds % 60).padStart(2, '0')}`;
}

export function DurationPicker({
  label,
  valueSeconds,
  onChange,
  error,
  hint,
  required = false,
  clearable = !required,
  units = ALL_UNITS,
  maxHours = 168,
  maxMinutes = 59,
  suffix,
  icon = true,
  focusRef,
}: DurationPickerProps) {
  const { t } = useLanguage();
  // The sheet edits a draft; the owner only hears about the value on "Done".
  const [draft, setDraft] = useState<DurationParts | null>(null);
  const hasHours = units.includes('hours');
  const draftTotal = draft ? (hasHours ? Math.min(maxHours * 3600, join(draft)) : join(draft)) : 0;
  const withSuffix = (text: string) => (suffix ? `${text} ${suffix}` : text);
  const display = valueSeconds === null ? null : withSuffix(format(Math.round(valueSeconds), units));

  return (
    <View>
      <PickerField
        label={label}
        required={required}
        display={display}
        placeholder={t('onboarding.duration.placeholder')}
        spokenValue={display ?? t('onboarding.duration.notSetSpoken')}
        openHint={t('onboarding.duration.editHint')}
        onOpen={() => setDraft(split(valueSeconds, units))}
        clearLabel={t('onboarding.duration.clearLabel', { label })}
        onClear={clearable && valueSeconds !== null ? () => onChange(null) : undefined}
        icon={icon ? 'clock' : undefined}
        error={error}
        hint={hint}
        focusRef={focusRef}
      />
      <BottomSheet
        visible={draft !== null}
        title={label}
        closeLabel={t('onboarding.duration.closeLabel')}
        onClose={() => setDraft(null)}
        scroll={false}
        footer={<Button label={t('common.done')} onPress={() => { onChange(draftTotal); setDraft(null); }} />}
      >
        <Text variant="numeric" tone="primary" accessibilityLiveRegion="polite" style={styles.preview}>
          {withSuffix(format(draftTotal, units))}
        </Text>
        <View style={styles.wheels}>
          {draft ? units.map((unit) => (
            <WheelColumn
              key={unit}
              caption={t(unitCopy[unit].short)}
              count={unit === 'hours' ? maxHours + 1 : unit === 'minutes' && !hasHours ? maxMinutes + 1 : 60}
              value={draft[unit]}
              spoken={(n) => `${n} ${t(n === 1 ? unitCopy[unit].singular : unitCopy[unit].short)}`}
              onChange={(n) => setDraft((current) => (current ? { ...current, [unit]: n } : current))}
            />
          )) : null}
        </View>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  preview: { textAlign: 'center' },
  wheels: { flexDirection: 'row', gap: space[8], paddingTop: space[8] },
});
