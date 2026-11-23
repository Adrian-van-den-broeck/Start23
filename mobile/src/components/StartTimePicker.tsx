import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { useLanguage } from '../i18n/LanguageProvider';
import { resolveDeviceTimezone } from '../lib/onboardingForms';
import { fromWallClock, sameDate, shiftDate, toWallClock, type WallClock } from '../lib/zonedTime';
import { BottomSheet } from '../ui-v2/primitives/BottomSheet';
import { Button } from '../ui-v2/primitives/Button';
import { PickerField } from '../ui-v2/primitives/PickerField';
import { Text } from '../ui-v2/primitives/Text';
import { WheelColumn } from '../ui-v2/primitives/WheelColumn';
import { colors, layout, radius, space } from '../ui-v2/tokens';

type CalendarDate = Pick<WallClock, 'year' | 'month' | 'day'>;

// Activities are logged after the fact, so the sheet offers the last two weeks.
const DAYS_BACK = 14;

const pad = (value: number) => String(value).padStart(2, '0');

/**
 * Pick the day and clock time an activity started, in the athlete's confirmed
 * profile time zone. The owner receives an ISO instant; nothing is saved here.
 */
export function StartTimePicker({ label, valueIso, timeZone, onChange, error, now = new Date() }: {
  label: string; valueIso: string; timeZone: string; onChange: (valueIso: string) => void;
  error?: string; now?: Date;
}) {
  const { t, locale } = useLanguage();
  const zone = timeZone.trim() || resolveDeviceTimezone() || 'UTC';
  const [draft, setDraft] = useState<WallClock | null>(null);
  const today = toWallClock(now, zone);
  const value = Number.isNaN(new Date(valueIso).getTime()) ? null : toWallClock(new Date(valueIso), zone);
  const days = Array.from({ length: DAYS_BACK }, (_, offset) => shiftDate(today, offset));

  const dayLabel = (date: CalendarDate) => {
    if (sameDate(date, today)) return t('datetime.today');
    if (sameDate(date, shiftDate(today, 1))) return t('datetime.yesterday');
    return new Intl.DateTimeFormat(locale, { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' })
      .format(new Date(Date.UTC(date.year, date.month - 1, date.day))).replace(/\./g, '');
  };
  const describe = (clock: WallClock) => `${dayLabel(clock)} · ${pad(clock.hour)}:${pad(clock.minute)}`;
  const display = value ? describe(value) : null;

  return (
    <View>
      <PickerField
        label={label}
        required
        display={display}
        placeholder={t('datetime.placeholder')}
        spokenValue={display ?? t('onboarding.duration.notSetSpoken')}
        openHint={t('datetime.editHint')}
        onOpen={() => setDraft(value ?? today)}
        icon="calendar"
        error={error}
      />
      <BottomSheet
        visible={draft !== null}
        title={label}
        closeLabel={t('datetime.closeLabel')}
        onClose={() => setDraft(null)}
        scroll={false}
        footer={<Button label={t('common.done')} onPress={() => {
          if (draft) onChange(fromWallClock(draft, zone).toISOString());
          setDraft(null);
        }} />}
      >
        {draft ? <>
          <Text variant="numericCompact" tone="primary" accessibilityLiveRegion="polite" style={styles.preview}>
            {describe(draft)}
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.days}
            accessibilityRole="radiogroup" accessibilityLabel={t('datetime.day')}>
            {days.map((date) => {
              const selected = sameDate(date, draft);
              return <Pressable key={`${date.year}-${date.month}-${date.day}`} accessibilityRole="radio"
                accessibilityState={{ checked: selected }} accessibilityLabel={dayLabel(date)}
                onPress={() => setDraft((current) => (current ? { ...current, ...date } : current))}
                style={({ pressed }) => [styles.day, selected && styles.daySelected, pressed && styles.pressed]}>
                <Text variant="label" accessible={false} tone={selected ? 'textInverse' : 'text'}>{dayLabel(date)}</Text>
              </Pressable>;
            })}
          </ScrollView>
          <View style={styles.wheels}>
            <WheelColumn caption={t('datetime.hour')} count={24} value={draft.hour}
              spoken={(n) => `${pad(n)} ${t('datetime.hour')}`}
              onChange={(hour) => setDraft((current) => (current ? { ...current, hour } : current))} />
            <WheelColumn caption={t('datetime.minute')} count={60} value={draft.minute}
              spoken={(n) => `${n} ${t('datetime.minute')}`}
              onChange={(minute) => setDraft((current) => (current ? { ...current, minute } : current))} />
          </View>
        </> : null}
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  preview: { textAlign: 'center' },
  days: { gap: space[8], paddingVertical: space[4] },
  day: { minHeight: layout.touch, justifyContent: 'center', paddingHorizontal: space[16], borderRadius: radius.pill,
    borderWidth: layout.controlEdge, borderColor: colors.borderControl, backgroundColor: colors.surface },
  daySelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  pressed: { opacity: 0.72 },
  wheels: { flexDirection: 'row', gap: space[8], paddingTop: space[8] },
});
