import { useContext, type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaInsetsContext } from 'react-native-safe-area-context';

import { colors, layout, radius, space } from '../tokens';
import { Icon } from './Icon';
import { Text } from './Text';

// Shared sheet shell for compact pickers. The scrim and close button only
// dismiss; committing a choice is always the caller's explicit action.
export function BottomSheet({ visible, title, closeLabel, onClose, children, footer, scroll = true }: {
  visible: boolean; title: string; closeLabel: string; onClose: () => void;
  children: ReactNode; footer?: ReactNode; scroll?: boolean;
}) {
  // Read the context directly: a sheet may render outside a provider (tests, isolated stories).
  const bottomInset = useContext(SafeAreaInsetsContext)?.bottom ?? 0;
  return <Modal animationType="slide" transparent statusBarTranslucent visible={visible} onRequestClose={onClose}>
    <View style={styles.root}>
      <Pressable accessible={false} importantForAccessibility="no" style={styles.scrim} onPress={onClose} />
      <View accessibilityViewIsModal style={[styles.sheet, { paddingBottom: space[16] + bottomInset }]}>
        <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.handle} />
        <View style={styles.header}>
          <Text variant="cardTitle" accessibilityRole="header" style={styles.title}>{title}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel={closeLabel} hitSlop={space[4]} onPress={onClose} style={styles.close}>
            <Icon name="close" size={24} />
          </Pressable>
        </View>
        {scroll ? <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">{children}</ScrollView>
          : <View style={styles.body}>{children}</View>}
        {footer ? <View style={styles.footer}>{footer}</View> : null}
      </View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: 'flex-end' },
  scrim: { ...StyleSheet.absoluteFill, backgroundColor: colors.scrim },
  sheet: { maxHeight: '86%', backgroundColor: colors.surface, borderTopLeftRadius: radius.sheet,
    borderTopRightRadius: radius.sheet, paddingTop: space[8], paddingHorizontal: space[16] },
  handle: { alignSelf: 'center', width: 40, height: 4, borderRadius: radius.pill, backgroundColor: colors.border, marginBottom: space[8] },
  header: { flexDirection: 'row', alignItems: 'center', gap: space[8], marginBottom: space[8] },
  title: { flex: 1 },
  close: { width: layout.iconButton, height: layout.iconButton, borderRadius: radius.pill,
    alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceSubtle },
  body: { gap: space[8], paddingBottom: space[8] },
  footer: { paddingTop: space[12] },
});
