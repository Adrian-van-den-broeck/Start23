import type { ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { colors, radius, space } from '../tokens';
import { Text } from '../primitives/Text';
import { IconTile } from '../primitives/IconTile';

export function SportIndicator({ discipline, size = 'row', tone = 'discipline', children }: {
  discipline: Discipline; size?: 'row' | 'focus'; tone?: 'discipline' | 'primary'; children?: ReactNode;
}) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const accent = tone === 'primary' ? { soft: colors.primarySoft, text: colors.primary } : colors.sport[discipline];
  const stacked = size === 'focus' && (width < 360 || fontScale >= 1.5);
  return <View style={[styles.header, stacked && styles.stacked]}>
    <IconTile name={discipline} size={size} tone={tone === 'primary' ? 'primary' : discipline} />
    <View style={[styles.content, stacked && styles.stackedContent]}>
      <View style={[styles.marker, { backgroundColor: accent.soft }]}>
        <Text variant="supporting" style={{ color: accent.text, fontWeight: '600' }}>{t(`common.${discipline}`)}</Text>
      </View>
      {children}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', gap: space[16] },
  stacked: { flexDirection: 'column', alignItems: 'flex-start' },
  content: { flex: 1, gap: space[8], alignSelf: 'stretch', justifyContent: 'center' },
  stackedContent: { flex: 0 },
  marker: {
    alignSelf: 'flex-start', borderRadius: radius.pill,
    paddingVertical: space[4], paddingHorizontal: space[12]
  },
});
