import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { useLanguage } from '../i18n/LanguageProvider';
import { BottomSheet } from '../ui-v2/primitives/BottomSheet';
import { Button } from '../ui-v2/primitives/Button';
import { PickerField } from '../ui-v2/primitives/PickerField';
import { Text } from '../ui-v2/primitives/Text';
import { WheelColumn } from '../ui-v2/primitives/WheelColumn';
import { space } from '../ui-v2/tokens';

type Parts = { year: number; month: number; day: number };

const pad = (value: number) => String(value).padStart(2, '0');

function parse(value: string | null | undefined): Parts | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value ?? '');
  if (!match) return null;
  const parts = { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
  const check = new Date(Date.UTC(parts.year, parts.month - 1, parts.day));
  return check.getUTCMonth() === parts.month - 1 && check.getUTCDate() === parts.day ? parts : null;
}

const iso = ({ year, month, day }: Parts) => `${year}-${pad(month)}-${pad(day)}`;
const daysIn = (year: number, month: number) => new Date(Date.UTC(year, month, 0)).getUTCDate();

/**
 * A calendar date (YYYY-MM-DD) chosen with day, month and year wheels instead of
 * typing. `min`/`max` bound the years offered and the confirmed value; the
 * owner still validates, this only reports the chosen date.
 */
export function DatePicker({ label, value, onChange, min, max, openAt, required = false, error, hint, placeholder }: {
  label: string; value: string; onChange: (value: string) => void;
  min: string; max: string;
  // Where an empty picker opens (defaults to `max`), e.g. a typical birth year.
  openAt?: string;
  required?: boolean; error?: string; hint?: string; placeholder?: string;
}) {
  const { t, locale } = useLanguage();
  const [draft, setDraft] = useState<Parts | null>(null);
  const low = parse(min)!;
  const high = parse(max)!;
  const current = parse(value);
  const format = (parts: Parts) => new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(Date.UTC(parts.year, parts.month - 1, parts.day)));
  const monthName = (month: number) => new Intl.DateTimeFormat(locale, { month: 'short', timeZone: 'UTC' })
    .format(new Date(Date.UTC(2000, month - 1, 1))).replace(/\./g, '');
  const clamp = (parts: Parts): Parts => {
    const day = Math.min(parts.day, daysIn(parts.year, parts.month));
    const value = iso({ ...parts, day });
    return value < min ? low : value > max ? high : { ...parts, day };
  };
  const display = current ? format(current) : null;
  const years = high.year - low.year + 1;

  return <View>
    <PickerField
      label={label}
      required={required}
      display={display}
      placeholder={placeholder ?? t('datetime.datePlaceholder')}
      spokenValue={display ?? t('onboarding.duration.notSetSpoken')}
      openHint={t('datetime.dateEditHint')}
      onOpen={() => setDraft(clamp(current ?? parse(openAt) ?? high))}
      icon="calendar"
      error={error}
      hint={hint}
    />
    <BottomSheet visible={draft !== null} title={label} closeLabel={t('datetime.closeLabel')} onClose={() => setDraft(null)}
      scroll={false}
      footer={<Button label={t('common.done')} onPress={() => {
        if (draft) onChange(iso(clamp(draft)));
        setDraft(null);
      }} />}>
      {draft ? <>
        <Text variant="numericCompact" tone="primary" accessibilityLiveRegion="polite" style={styles.preview}>
          {format(clamp(draft))}
        </Text>
        <View style={styles.wheels}>
          <WheelColumn caption={t('datetime.day')} count={daysIn(draft.year, draft.month)} value={Math.min(draft.day, daysIn(draft.year, draft.month)) - 1}
            format={(index) => String(index + 1)} spoken={(index) => `${t('datetime.day')} ${index + 1}`}
            onChange={(index) => setDraft((parts) => (parts ? { ...parts, day: index + 1 } : parts))} />
          <WheelColumn caption={t('datetime.month')} count={12} value={draft.month - 1}
            format={(index) => monthName(index + 1)} spoken={(index) => monthName(index + 1)}
            onChange={(index) => setDraft((parts) => (parts ? { ...parts, month: index + 1 } : parts))} />
          <WheelColumn caption={t('datetime.year')} count={years} value={draft.year - low.year}
            format={(index) => String(low.year + index)} spoken={(index) => String(low.year + index)}
            onChange={(index) => setDraft((parts) => (parts ? { ...parts, year: low.year + index } : parts))} />
        </View>
      </> : null}
    </BottomSheet>
  </View>;
}

const styles = StyleSheet.create({
  preview: { textAlign: 'center' },
  wheels: { flexDirection: 'row', gap: space[8], paddingTop: space[8] },
});
