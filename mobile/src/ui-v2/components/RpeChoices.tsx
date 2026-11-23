import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';
import { useRef, useState } from 'react';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { rpeChoices, type CanonicalRpe } from '../../lib/rpe';
import { studioPresentation } from '../../ui-v3/presentation';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Icon } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';

export function RpeChoices({ discipline, busy, selectedValue, onSelect }: {
  discipline: Discipline; busy: boolean; selectedValue: number | null;
  onSelect: (value: CanonicalRpe) => Promise<void>;
}) {
  const { t } = useLanguage();
  return <View style={styles.stack}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('rpe.prompt')}</Text>
    <Text variant={studioPresentation ? 'supporting' : 'body'} tone={studioPresentation ? 'textMuted' : 'text'}>{t('activities.saveOnChoice')}</Text>
    <View accessibilityRole="radiogroup" accessibilityLabel={t('rpe.prompt')} style={studioPresentation ? styles.scale : styles.stack}>
      {rpeChoices(discipline).map(choice => <SavingRpeChoice key={choice.value}
        value={choice.value} description={choice.description}
        accessibilityLabel={`${t('activities.saveFeedback')} · ${choice.description} (RPE ${choice.value})`}
        selected={selectedValue === choice.value} busy={busy}
        onPress={() => onSelect(choice.value)} />)}
    </View>
  </View>;
}
// Preserve Button's immediate callback, per-choice async lock and pending state.
// Selection is supplied by the activity owner; a tap is never staged locally.
function SavingRpeChoice({ value, description, accessibilityLabel, selected, busy, onPress }: {
  value: number; description: string; accessibilityLabel: string; selected: boolean; busy: boolean; onPress: () => Promise<void>;
}) {
  const lock = useRef(false);
  const [pending, setPending] = useState(false);
  const [focused, setFocused] = useState(false);
  const isBusy = busy || pending;
  async function press() {
    if (isBusy || lock.current) return;
    lock.current = true;
    try {
      const result = onPress();
      if (result) { setPending(true); await result; }
    } finally {
      lock.current = false;
      setPending(false);
    }
  }
  if (!studioPresentation) return <ChoiceRow label={`${value} · ${description}`} accessibilityLabel={accessibilityLabel} selected={selected} busy={isBusy} onPress={() => { void press(); }} />;
  // V3: the score as a badge and its meaning beside it, the scale the compact RPE field opens.
  return <Pressable accessibilityRole="radio" accessibilityLabel={accessibilityLabel}
    accessibilityState={{ checked: selected, disabled: isBusy, busy: isBusy }} disabled={isBusy}
    onPress={() => { void press(); }} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={[styles.row, selected && styles.rowSelected, isBusy && styles.rowBusy, focused && styles.rowFocused]}>
    <View accessible={false} importantForAccessibility="no-hide-descendants" style={[styles.badge, selected && styles.badgeSelected]}>
      <Text variant="label" tone={selected ? 'textInverse' : 'primary'}>{value}</Text>
    </View>
    <Text variant={selected ? 'label' : 'body'} accessible={false} style={styles.description}>{description}</Text>
    {pending ? <ActivityIndicator accessible={false} color={colors.primary} />
      : selected ? <Icon name="check" size={20} color={colors.primary} /> : null}
  </Pressable>;
}
const styles = StyleSheet.create({
  stack: { gap: space[12] }, scale: { gap: space[4] },
  row: { minHeight: layout.touch, flexDirection: 'row', alignItems: 'center', gap: space[12], paddingHorizontal: space[8],
    paddingVertical: space[8], borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: 'transparent' },
  rowSelected: { backgroundColor: colors.primarySoft },
  rowBusy: { opacity: 0.6 },
  rowFocused: { borderColor: colors.focus },
  badge: { width: 36, height: 36, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primarySoft },
  badgeSelected: { backgroundColor: colors.primary },
  description: { flex: 1 },
});
