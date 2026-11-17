import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { colors, layout, radius, space } from '../tokens';
import type { SegmentViewModel } from '../utils/workoutDetailViewModel';
import { RpeIndicator } from './RpeIndicator';
import { ZoneBadge } from './ZoneBadge';

export function SessionSequence({ segments }: { segments: readonly SegmentViewModel[] }) {
  const { t } = useLanguage();
  return <Card style={styles.sequence}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('detail.sequence')}</Text>
    {segments.length === 0 ? <Text>{t('detail.noSegments')}</Text> : segments.map((segment, index) => (
      <View key={`${segment.sequence}:${index}`} style={styles.block}>
        {index > 0 ? <Divider /> : null}
        <View style={styles.segment}>
        <Text variant="cardTitle" accessibilityRole="header" testID={`segment-heading-${index}`}>
          {segment.sequence}. {segment.name}
        </Text>
        <View style={styles.measures}>
        {segment.measures.durationMinutes !== null ? <Text variant="label"
          accessibilityLabel={t('detail.minutesSpoken', { value: segment.measures.durationMinutes })}>
          {t('common.durationMinutes', { minutes: segment.measures.durationMinutes })}
        </Text> : null}
        {segment.measures.distanceMeters !== null ? <Text variant="label"
          accessibilityLabel={t('detail.metersSpoken', { value: segment.measures.distanceMeters })}>
          {t('detail.meters', { value: segment.measures.distanceMeters })}
        </Text> : null}
        </View>
        <View style={styles.targets}>
        {segment.target.kind === 'zone' ? <ZoneBadge zone={segment.target.zone} /> :
          <RpeIndicator range={segment.target.range} kind={segment.target.kind === 'expected' ? 'expected' : segment.target.kind} />}
        {segment.rpeTarget && segment.target.kind !== 'rpe' ? <RpeIndicator kind="rpe" range={segment.rpeTarget} /> : null}
        {segment.protocolTarget && segment.target.kind !== 'protocol' ? <RpeIndicator kind="protocol" range={segment.protocolTarget} /> : null}
        </View>
        {segment.optionalProtocol ? <Text variant="supporting">{t('detail.optionalProtocol')}</Text> : null}
        {segment.heartRateObservationRequired ? <Text variant="supporting">{t('detail.heartRateObservation')}</Text> : null}
        {segment.technique ? <Text variant="label">{t('detail.technique')}</Text> : null}
        {segment.instructions ? <Text>{segment.instructions}</Text> : null}
        </View>
      </View>
    ))}
  </Card>;
}
const styles = StyleSheet.create({
  sequence: { gap: space[24] }, block: { gap: space[24] },
  segment: { borderLeftWidth: layout.decorativeLine, borderColor: colors.primary,
    paddingLeft: space[16], gap: space[12] },
  measures: { flexDirection: 'row', flexWrap: 'wrap', columnGap: space[16], rowGap: space[4] },
  targets: { gap: space[8], padding: space[12], borderRadius: radius.inset, backgroundColor: colors.primarySoft },
});
