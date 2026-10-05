import { StyleSheet, View } from 'react-native';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { layout, space } from '../tokens';

export function WeekTaskCard({ status, heading, supporting, actionLabel, onAction, disabled = false }: {
  status: string; heading: string; supporting?: string; actionLabel: string; onAction: () => void; disabled?: boolean;
}) {
  return <Card testID="week-task-card" style={styles.card}>
    <View style={styles.copy}>
      <Text variant="label">{status}</Text>
      <Text variant="sectionTitle" accessibilityRole="header">{heading}</Text>
      {supporting ? <Text variant="supporting" tone="textMuted">{supporting}</Text> : null}
    </View>
    <Button label={actionLabel} onPress={onAction} disabled={disabled} />
  </Card>;
}
const styles = StyleSheet.create({
  card: { padding: layout.focusPadding, gap: space[16] },
  copy: { gap: space[8] },
});
