import { useRef, type ReactNode } from 'react';
import { AccessibilityInfo, ScrollView, StyleSheet, View, type ScrollViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../i18n/LanguageProvider';
import { colors, layout, space } from '../tokens';
import { Button } from './Button';
import { Text } from './Text';

export function Screen({ title, children, onBack, scrollProps, topInsetOwned = false, focusHeading = true }: {
  title: string; children: ReactNode; onBack: () => void; scrollProps?: ScrollViewProps; topInsetOwned?: boolean; focusHeading?: boolean;
}) {
  const { t } = useLanguage();
  const heading = useRef<View>(null);
  const focused = useRef(false);
  return <SafeAreaView edges={topInsetOwned ? ['bottom'] : ['top', 'bottom']} style={styles.frame}>
    <View style={styles.header}>
      <Button variant="tertiary" label={t('common.close')} onPress={onBack} />
      <View ref={heading} accessible accessibilityRole="header" accessibilityLabel={title}
        onLayout={() => {
          if (focusHeading && !focused.current && heading.current) {
            focused.current = true;
            AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus');
          }
        }}>
        <Text variant="sectionTitle">{title}</Text>
      </View>
    </View>
    <ScrollView testID="workout-detail-scroll" {...scrollProps} style={styles.scroll} contentContainerStyle={styles.content}>
      {children}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  header: { paddingHorizontal: layout.phoneGutter, gap: space[8], paddingBottom: space[12] },
  scroll: { flex: 1 },
  content: {
    width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center',
    padding: layout.phoneGutter, paddingBottom: space[32], gap: space[24]
  },
});
