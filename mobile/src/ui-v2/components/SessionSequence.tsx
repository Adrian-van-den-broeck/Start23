import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { colors, space } from '../tokens';
import type { SegmentViewModel } from '../utils/workoutDetailViewModel';
import { RpeIndicator } from './RpeIndicator';
import { ZoneBadge } from './ZoneBadge';

export function SessionSequence({ segments }: { segments: readonly SegmentViewModel[] }) {
  const { t } = useLanguage();
  return <View style={styles.sequence}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('detail.sequence')}</Text>
    {segments.length === 0 ? <Text>{t('detail.noSegments')}</Text> : segments.map((segment, index) => (
      <View key={`${segment.sequence}:${index}`} style={styles.segment}>
        <Text variant="cardTitle" accessibilityRole="header" testID={`segment-heading-${index}`}>
          {segment.sequence}. {segment.name}
        </Text>
        {segment.measures.durationMinutes !== null ? <Text variant="supporting"
          accessibilityLabel={t('detail.minutesSpoken', { value: segment.measures.durationMinutes })}>
          {t('common.durationMinutes', { minutes: segment.measures.durationMinutes })}
        </Text> : null}
        {segment.measures.distanceMeters !== null ? <Text variant="supporting"
          accessibilityLabel={t('detail.metersSpoken', { value: segment.measures.distanceMeters })}>
          {t('detail.meters', { value: segment.measures.distanceMeters })}
        </Text> : null}
        {segment.target.kind === 'zone' ? <ZoneBadge zone={segment.target.zone} /> :
          <RpeIndicator range={segment.target.range} kind={segment.target.kind === 'expected' ? 'expected' : segment.target.kind} />}
        {segment.rpeTarget && segment.target.kind !== 'rpe' ? <RpeIndicator kind="rpe" range={segment.rpeTarget} /> : null}
        {segment.protocolTarget && segment.target.kind !== 'protocol' ? <RpeIndicator kind="protocol" range={segment.protocolTarget} /> : null}
        {segment.optionalProtocol ? <Text variant="supporting">{t('detail.optionalProtocol')}</Text> : null}
        {segment.heartRateObservationRequired ? <Text variant="supporting">{t('detail.heartRateObservation')}</Text> : null}
        {segment.technique ? <Text variant="label">{t('detail.technique')}</Text> : null}
        {segment.instructions ? <Text>{segment.instructions}</Text> : null}
      </View>
    ))}
  </View>;
}
const styles = StyleSheet.create({
  sequence: { gap: space[24] },
  segment: { borderLeftWidth: 1, borderColor: colors.borderControl, paddingLeft: space[16], gap: space[8] },
});
