import { useRef, type ReactNode } from 'react';
import { AccessibilityInfo, ScrollView, StyleSheet, View, type ScrollViewProps } from 'react-native';
import { ShellSafeArea } from '../components/ShellInsets';
import { AppHeader } from '../components/AppHeader';
import { useLanguage } from '../../i18n/LanguageProvider';
import { colors, layout, space } from '../tokens';

export function Screen({ title, children, onBack, scrollProps, topInsetOwned = false, focusHeading = true, backLabel, backDisabled = false, landscape, titleVariant }: {
  title: string; children: ReactNode; onBack: () => void; scrollProps?: ScrollViewProps; topInsetOwned?: boolean; focusHeading?: boolean; backLabel?: string; backDisabled?: boolean; landscape?: 'ridges' | 'treesRiver'; titleVariant?: 'display' | 'screenTitle' | 'sectionTitle';
}) {
  const { t } = useLanguage();
  const heading = useRef<View>(null);
  const focused = useRef(false);
  return <ShellSafeArea independent={topInsetOwned} style={styles.frame}>
    <ScrollView testID="workout-detail-scroll" {...scrollProps} style={styles.scroll} contentContainerStyle={styles.content}>
      <AppHeader title={title} task backIcon={backLabel ? 'back' : 'close'} onBack={onBack} backLabel={backLabel ?? t('common.close')} backDisabled={backDisabled}
        landscape={landscape} titleVariant={titleVariant} titleRef={heading} onTitleLayout={() => {
          if (focusHeading && !focused.current && heading.current) {
            focused.current = true;
            AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus');
          }
        }} />
      {children}
    </ScrollView>
  </ShellSafeArea>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: {
    width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center',
    padding: layout.phoneGutter, paddingBottom: space[32], gap: space[24]
  },
});
