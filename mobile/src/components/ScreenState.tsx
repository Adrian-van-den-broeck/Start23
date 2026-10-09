import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AppHeader } from '../ui-v2/components/AppHeader';
import { Card } from '../ui-v2/primitives/Card';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, space } from '../ui-v2/tokens';
type ScreenStateProps = { loading?: boolean; message?: string; title: string; };
export function ScreenState({ loading = false, message, title }: ScreenStateProps) {
  return <SafeAreaView style={styles.safeArea}>
    <ScrollView contentContainerStyle={styles.content}>
      <AppHeader title="WOMBO" landscape="ridges" />
      <Card elevated padding="form" style={{ gap: space[24] }}>
        <Text variant="sectionTitle" accessibilityRole="header">{title}</Text>
        {loading ? <View accessibilityState={{ busy: true }}><ActivityIndicator color={colors.primary} size="large" /></View> : null}
        {message ? <Notice>{message}</Notice> : null}
      </Card>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
});
