import { StyleSheet, View } from 'react-native';
import { useRef, useState } from 'react';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { rpeChoices, type CanonicalRpe } from '../../lib/rpe';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Text } from '../primitives/Text';
import { space } from '../tokens';

export function RpeChoices({ discipline, busy, selectedValue, onSelect }: {
  discipline: Discipline; busy: boolean; selectedValue: number | null;
  onSelect: (value: CanonicalRpe) => Promise<void>;
}) {
  const { t } = useLanguage();
  return <View style={styles.stack}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('rpe.prompt')}</Text>
    <Text>{t('activities.saveOnChoice')}</Text>
    <View accessibilityRole="radiogroup" accessibilityLabel={t('rpe.prompt')} style={styles.stack}>
      {rpeChoices(discipline).map(choice => <SavingRpeChoice key={choice.value}
        label={`${choice.value} · ${choice.description}`}
        accessibilityLabel={`${t('activities.saveFeedback')} · ${choice.description} (RPE ${choice.value})`}
        selected={selectedValue === choice.value} busy={busy}
        onPress={() => onSelect(choice.value)} />)}
    </View>
  </View>;
}
// Preserve Button's immediate callback, per-choice async lock and pending state.
// Selection is supplied by the activity owner; a tap is never staged locally.
function SavingRpeChoice({ label, accessibilityLabel, selected, busy, onPress }: {
  label: string; accessibilityLabel: string; selected: boolean; busy: boolean; onPress: () => Promise<void>;
}) {
  const lock = useRef(false);
  const [pending, setPending] = useState(false);
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
  return <ChoiceRow label={label} accessibilityLabel={accessibilityLabel} selected={selected} busy={isBusy} onPress={() => { void press(); }} />;
}
const styles = StyleSheet.create({ stack: { gap: space[12] } });
