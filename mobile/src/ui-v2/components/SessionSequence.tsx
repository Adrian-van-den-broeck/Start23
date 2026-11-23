import { studioPresentation } from '../../ui-v3/presentation';
import { SegmentProfile } from '../../ui-v3/SegmentProfile';
import { Surface } from '../../ui-v3/screens/support';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { Divider } from '../primitives/Divider';
import { colors, layout, radius, space } from '../tokens';
import type { SegmentViewModel } from '../utils/workoutDetailViewModel';
import { RpeIndicator } from './RpeIndicator';
import { ZoneBadge } from './ZoneBadge';

// V3 sets each target apart as its own mark; V2 lists them in one tinted box.
function Target({ children }: { children: ReactNode }) {
  return studioPresentation ? <View style={styles.target}>{children}</View> : <>{children}</>;
}

export function SessionSequence({ segments }: { segments: readonly SegmentViewModel[] }) {
  const { t } = useLanguage();
  return <Surface elevated={false} style={styles.sequence}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('detail.sequence')}</Text>
    {studioPresentation && <SegmentProfile segments={segments} />}
    {segments.length === 0 ? <Text>{t('detail.noSegments')}</Text> : segments.map((segment, index) => (
      <View key={`${segment.sequence}:${index}`} style={styles.block}>
        {index > 0 && !studioPresentation ? <Divider /> : null}
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
        <Target>{segment.target.kind === 'zone' ? <ZoneBadge zone={segment.target.zone} /> :
          <RpeIndicator range={segment.target.range} kind={segment.target.kind === 'expected' ? 'expected' : segment.target.kind} />}</Target>
        {segment.rpeTarget && segment.target.kind !== 'rpe' ? <Target><RpeIndicator kind="rpe" range={segment.rpeTarget} /></Target> : null}
        {segment.protocolTarget && segment.target.kind !== 'protocol' ? <Target><RpeIndicator kind="protocol" range={segment.protocolTarget} /></Target> : null}
        </View>
        {segment.optionalProtocol ? <Text variant="supporting">{t('detail.optionalProtocol')}</Text> : null}
        {segment.heartRateObservationRequired ? <Text variant="supporting">{t('detail.heartRateObservation')}</Text> : null}
        {segment.technique ? <Text variant="label">{t('detail.technique')}</Text> : null}
        {segment.instructions ? <Text variant={studioPresentation ? 'supporting' : 'body'}>{segment.instructions}</Text> : null}
        </View>
      </View>
    ))}
  </Surface>;
}
const styles = StyleSheet.create({
  sequence: { gap: studioPresentation ? space[16] : space[24] }, block: { gap: space[24] },
  segment: studioPresentation ? { borderLeftWidth: 3, borderColor: colors.primary, paddingLeft: space[12], gap: space[8] }
    : { borderLeftWidth: layout.decorativeLine, borderColor: colors.primary, paddingLeft: space[16], gap: space[12] },
  measures: { flexDirection: 'row', flexWrap: 'wrap', columnGap: space[16], rowGap: space[4] },
  targets: studioPresentation ? { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] }
    : { gap: space[8], padding: space[12], borderRadius: radius.inset, backgroundColor: colors.primarySoft },
  target: { paddingHorizontal: space[8], paddingVertical: space[4], borderRadius: radius.inset, backgroundColor: colors.primarySoft },
});
