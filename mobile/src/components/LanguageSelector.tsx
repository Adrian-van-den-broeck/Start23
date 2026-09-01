import { StyleSheet, Text, View } from 'react-native';

import {
  type LanguagePreference,
  useLanguage,
} from '../i18n/LanguageProvider';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

const preferences: LanguagePreference[] = ['system', 'nl', 'en'];

export function LanguageSelector() {
  const { preference, setPreference, t } = useLanguage();
  const labels: Record<LanguagePreference, string> = {
    system: t('language.auto'),
    nl: t('language.nederlands'),
    en: t('language.english'),
  };

  return (
    <View style={styles.container}>
      <View>
        <Text style={styles.label}>{t('language.label')}</Text>
        <Text style={styles.hint}>{t('language.autoHint')}</Text>
      </View>
      <View accessibilityRole="radiogroup" style={styles.options}>
        {preferences.map((value) => {
          const selected = preference === value;
          return (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ checked: selected }}
              haptic="selection"
              key={value}
              onPress={() => void setPreference(value)}
              style={[styles.option, selected && styles.optionSelected]}
            >
              <Text style={[styles.optionText, selected && styles.optionTextSelected]}>
                {labels[value]}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.brandMid,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  label: { color: colors.white, fontSize: 13, fontWeight: '900' },
  hint: { color: colors.brandSoft, fontSize: 10, marginTop: 2 },
  options: { flexDirection: 'row', gap: spacing.xs },
  option: {
    alignItems: 'center',
    borderColor: colors.brandSoft,
    borderRadius: radius.pill,
    borderWidth: 1,
    flex: 1,
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.sm,
  },
  optionSelected: { backgroundColor: colors.highlight, borderColor: colors.highlight },
  optionText: { color: colors.white, fontSize: 10, fontWeight: '800' },
  optionTextSelected: { color: colors.brandDeep },
});
