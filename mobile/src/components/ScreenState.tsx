import { Masthead } from '../ui-v3/Masthead';
import { studioPresentation } from '../ui-v3/presentation';
import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AppHeader } from '../ui-v2/components/AppHeader';
import { Card } from '../ui-v2/primitives/Card';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, space } from '../ui-v2/tokens';
type ScreenStateProps = { loading?: boolean; message?: string; title: string; };
export function ScreenState({ loading = false, message, title }: ScreenStateProps) {
  const state = <>
    {loading ? <View accessibilityState={{ busy: true }}><ActivityIndicator color={colors.primary} size="large" /></View> : null}
    {message ? <Notice>{message}</Notice> : null}
  </>;
  return <SafeAreaView style={styles.safeArea}>
    <ScrollView contentContainerStyle={styles.content}>
      {studioPresentation ? <Masthead title={title} /> : <AppHeader title="WOMBO" landscape="ridges" />}
      {/* V3 states loading and messages on the page; V2 keeps its card. */}
      {studioPresentation ? <View style={styles.state}>{state}</View> : <Card elevated padding="form" style={{ gap: space[24] }}>
        <Text variant="sectionTitle" accessibilityRole="header">{title}</Text>
        {state}
      </Card>}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
  state: { gap: space[16] },
});
