import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { Divider } from '../primitives/Divider';
import { Icon } from '../primitives/Icon';
import { colors, radius, space } from '../tokens';
import type { WorkoutSummaryViewModel } from '../utils/workoutSummaryViewModel';
import { SportIndicator } from './SportIndicator';
import { WorkoutFacts } from './WorkoutFacts';

export function WorkoutSummary({ summary, showDescription = true, variant = 'scheduled', footer, context }: {
  summary: WorkoutSummaryViewModel; showDescription?: boolean; variant?: 'scheduled' | 'focus'; footer?: ReactNode; context?: ReactNode;
}) {
  const { t, locale } = useLanguage();
  const date = summary.date ? new Date(`${summary.date}T12:00:00`) : null;
  return <Card padding={variant === 'focus' ? 'focus' : 'standard'} elevated style={styles.summary}>
    {context}
    <SportIndicator discipline={summary.discipline} size={variant === 'focus' ? 'focus' : 'row'} tone="primary">
      <Text variant="cardTitle" accessibilityRole="header" testID="workout-detail-heading">{summary.name}</Text>
    </SportIndicator>
    <View style={styles.meta}>
      {date ? <Text variant="supporting" tone="textMuted">{date.toLocaleDateString(locale, {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
      })}</Text> : null}
      <View style={[styles.status, summary.status === 'cancelled' && styles.cancelled]}>
        <Icon name={summary.status === 'cancelled' ? 'close' : summary.status === 'completed' ? 'check' : 'calendar'}
          size={20} color={summary.status === 'cancelled' ? colors.destructive : colors.primary} />
        <Text variant="supporting" tone={summary.status === 'cancelled' ? 'destructive' : 'primary'} style={styles.statusLabel}>
          {t(`detail.status.${summary.status}`)}
        </Text>
      </View>
    </View>
    <Divider />
    <WorkoutFacts measures={summary.measures} intensity={summary.intensity} variant={variant} />
    {showDescription && summary.description ? <Text>{summary.description}</Text> : null}
    {footer ? <View style={styles.footer}>{footer}</View> : null}
  </Card>;
}
const styles = StyleSheet.create({
  summary: { gap: space[16] }, meta: { gap: space[8] },
  status: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: space[8],
    paddingVertical: space[4], paddingHorizontal: space[12], borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  cancelled: { backgroundColor: colors.destructiveSoft }, statusLabel: { flexShrink: 1, fontWeight: '600' },
  footer: { marginTop: space[8] },
});
