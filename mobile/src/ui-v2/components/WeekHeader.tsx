import type { RefObject } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { Text } from '../primitives/Text';
import { layout, space } from '../tokens';
import { ProfileAction } from './AppHeader';

/** M6 root title/Profile composition; art remains bounded as text grows. */
export function WeekHeader({ title, profileLabel, onProfile, disabled, titleRef, onTitleLayout }: {
  title: string; profileLabel: string; onProfile: () => void; disabled: boolean;
  titleRef: RefObject<View | null>; onTitleLayout: () => void;
}) {
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 360 || fontScale >= 1.5;
  return <View style={[styles.header, { minHeight: stacked ? 96 : 140 }]}>
    <View pointerEvents="none" style={styles.art}><HeaderLandscape behindText={stacked} /></View>
    <View style={[styles.row, stacked && styles.stacked]}>
      <View testID="week-header-title" ref={titleRef} accessible accessibilityRole="header" accessibilityLabel={title}
        onLayout={onTitleLayout} style={[styles.title, stacked && styles.fullTitle]}>
        <Text variant="display" accessible={false}>{title}</Text>
      </View>
      <ProfileAction label={profileLabel} onPress={onProfile} disabled={disabled} />
    </View>
  </View>;
}
const styles = StyleSheet.create({
  header: { width: '100%' }, art: { position: 'absolute', top: 0, left: -layout.phoneGutter, right: -layout.phoneGutter },
  row: { flexDirection: 'row', alignItems: 'center', gap: space[12] },
  stacked: { flexDirection: 'column', alignItems: 'stretch' },
  title: { flexGrow: 1, flexShrink: 1, flexBasis: 0 }, fullTitle: { width: '100%', flexGrow: 0, flexShrink: 0, flexBasis: 'auto' },
});
