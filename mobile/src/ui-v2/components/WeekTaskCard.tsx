import { StyleSheet, View } from 'react-native';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { Icon, type IconName } from '../primitives/Icon';
import { colors, radius, space } from '../tokens';

export function WeekTaskCard({ status, heading, supporting, actionLabel, onAction, disabled = false, icon = 'week' }: {
  status: string; heading: string; supporting?: string; actionLabel: string; onAction: () => void; disabled?: boolean; icon?: IconName;
}) {
  return <Card testID="week-task-card" padding="focus" elevated style={styles.card}>
    <View style={styles.copy}>
      <View style={styles.status}><Icon name={icon} size={20} /><Text variant="supporting" tone="primary" style={styles.statusLabel}>{status}</Text></View>
      <Text variant="sectionTitle" accessibilityRole="header">{heading}</Text>
      {supporting ? <Text variant="supporting" tone="textMuted">{supporting}</Text> : null}
    </View>
    <Button label={actionLabel} trailingIcon="forward" onPress={onAction} disabled={disabled} />
  </Card>;
}
const styles = StyleSheet.create({
  card: { gap: space[24] },
  copy: { gap: space[8] },
  status: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: space[8], paddingHorizontal: space[12], paddingVertical: space[4], borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  statusLabel: { flexShrink: 1, fontWeight: '600' },
});
