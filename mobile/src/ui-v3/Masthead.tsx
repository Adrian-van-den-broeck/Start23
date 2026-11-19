import type { ReactNode, RefObject } from 'react';
import { StyleSheet, View, useWindowDimensions } from 'react-native';
import { Text } from '../ui-v2/primitives/Text';
import { colors, space } from '../ui-v2/tokens';
import { identity } from './tokens';

export function Wordmark({ inverse = false }: { inverse?: boolean }) {
  return <View accessible accessibilityLabel="Wombo" style={styles.lockup}>
    <View accessible={false} style={styles.strokes}>
      <View style={styles.stroke} /><View style={styles.stroke} /><View style={styles.stroke} />
    </View>
    <Text accessible={false} style={[styles.word, inverse && styles.inverse]}>wombo</Text>
  </View>;
}

export function Masthead({ title, leading, trailing, children, titleRef, onTitleLayout, titleTestID }: {
  title: string; leading?: ReactNode; trailing?: ReactNode; children?: ReactNode;
  titleRef?: RefObject<View | null>; onTitleLayout?: () => void; titleTestID?: string;
}) {
  const { width, fontScale } = useWindowDimensions();
  return <View style={styles.header}>
    <View style={[styles.tools, (width < 350 || fontScale > 1.35) && styles.wrapped]}>
      {leading ?? <Wordmark />}{trailing}
    </View>
    <View testID={titleTestID} accessible accessibilityRole="header" accessibilityLabel={title}
      tabIndex={-1} ref={titleRef} onLayout={onTitleLayout} style={styles.title}>
      <Text variant="display" accessible={false}>{title}</Text>
    </View>
    {children}
  </View>;
}

const styles = StyleSheet.create({
  lockup: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  strokes: { flexDirection: 'row', alignItems: 'center', gap: 2, paddingHorizontal: 3 },
  stroke: { backgroundColor: identity.orange, width: 4, height: 18, transform: [{ skewX: '-19deg' }] },
  word: { fontSize: 23, lineHeight: 30, fontWeight: '800', letterSpacing: -1.3, color: identity.ink },
  inverse: { color: colors.textInverse },
  title: { width: '100%', flexGrow: 0, flexShrink: 0, flexBasis: 'auto' },
  header: { gap: space[12] },
  tools: { minHeight: 48, paddingBottom: space[8], borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth, flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', flexWrap: 'wrap', gap: space[8] },
  wrapped: { alignItems: 'flex-start' },
});
