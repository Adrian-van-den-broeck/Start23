import { StyleSheet, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { colors, radius, space } from '../tokens';
import { Text } from '../primitives/Text';

export function SportIndicator({ discipline }: { discipline: Discipline }) {
  const { t } = useLanguage();
  const accent = colors.sport[discipline];
  return <View style={[styles.marker, { backgroundColor: accent.soft, borderColor: accent.text }]}>
    <Text variant="label" style={{ color: accent.text }}>{t(`common.${discipline}`)}</Text>
  </View>;
}
const styles = StyleSheet.create({
  marker: {
    alignSelf: 'flex-start', borderLeftWidth: space[4], borderRadius: radius.inset,
    paddingVertical: space[8], paddingHorizontal: space[12]
  },
});
