import { StyleSheet, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { rpeChoices, type CanonicalRpe } from '../../lib/rpe';
import { Button } from '../primitives/Button';
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
      {rpeChoices(discipline).map(choice => <Button key={choice.value} variant="secondary"
        label={`${choice.value} · ${choice.description}`} accessibilityRole="radio"
        accessibilityLabel={`${t('activities.saveFeedback')} · ${choice.description} (RPE ${choice.value})`}
        accessibilityState={{ checked: selectedValue === choice.value }} busy={busy}
        onPress={() => onSelect(choice.value)} />)}
    </View>
  </View>;
}
const styles = StyleSheet.create({ stack: { gap: space[12] } });
