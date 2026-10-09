import { View } from 'react-native';
import { type LanguagePreference, useLanguage } from '../i18n/LanguageProvider';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Text } from '../ui-v2/primitives/Text';
import { space } from '../ui-v2/tokens';
const preferences: LanguagePreference[] = ['system', 'nl', 'en'];
export function LanguageSelector() {
  const { preference, setPreference, t } = useLanguage();
  const labels: Record<LanguagePreference, string> = {
    system: t('language.auto'), nl: t('language.nederlands'), en: t('language.english'),
  };
  return <View style={{ gap: space[12] }}>
    <View style={{ gap: space[4] }}><Text variant="label">{t('language.label')}</Text><Text variant="supporting" tone="textMuted">{t('language.autoHint')}</Text></View>
    <View accessibilityRole="radiogroup" accessibilityLabel={t('language.label')} style={{ gap: space[12] }}>
      {preferences.map(value => <ChoiceRow key={value} label={labels[value]} selected={preference === value} onPress={() => void setPreference(value)} />)}
    </View>
  </View>;
}
