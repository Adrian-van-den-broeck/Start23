import type { ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import type { ZoneMetricKind, ZoneProfileSnapshot } from '../../api/types';
import { formatRunPace } from '../../lib/runPace';
import { IconTile } from '../primitives/IconTile';
import type { IconName } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';

export const zoneMetricLabels: Record<ZoneMetricKind, string> = {
  swim_css_seconds_per_100m: 'CSS (sec/100 m)', bike_ftp_watts: 'FTP (watt)',
  bike_threshold_heart_rate_bpm: 'Fietsdrempelhartslag (bpm)',
  run_threshold_pace_seconds_per_km: 'Loopdrempeltempo (min/km)', run_lthr_bpm: 'Loop-LTHR (bpm)',
};
const units: Record<ZoneMetricKind, string> = {
  swim_css_seconds_per_100m: 'sec/100 m', bike_ftp_watts: 'watt',
  bike_threshold_heart_rate_bpm: 'bpm', run_threshold_pace_seconds_per_km: 'min/km', run_lthr_bpm: 'bpm',
};
export function zoneValue(kind: ZoneMetricKind | undefined, value: string | null): string {
  if (value === null) return 'open';
  if (kind === 'run_threshold_pace_seconds_per_km') return formatRunPace(value);
  return kind ? value + ' ' + units[kind] : value;
}
export function ZoneInfoRow({ icon, children }: { icon: IconName; children: ReactNode }) {
  return <View style={styles.infoRow}><IconTile name={icon} size="field" /><View style={styles.infoCopy}>{children}</View></View>;
}
export function ZoneStatusChip({ label, pending = false }: { label: string; pending?: boolean }) {
  return <View style={[styles.chip, pending && styles.pending]}><Text variant="supporting" style={{ color: pending ? colors.warning : colors.primary, fontWeight: '600' }}>{label}</Text></View>;
}
// Supplied boundaries are displayed verbatim. No zones are derived in the client.
export function ZoneTable({ boundaries, metricKind }: {
  boundaries: ZoneProfileSnapshot['boundaries']; metricKind?: ZoneMetricKind;
}) {
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 360 || fontScale >= 1.5;
  return <View style={styles.table}>
    {boundaries.map(boundary => <View key={boundary.zone_number} style={[styles.tableRow, stacked && styles.stacked]}>
      <Text variant="label" style={styles.zone}>Z{boundary.zone_number}</Text>
      <Text style={styles.range}>{zoneValue(metricKind, boundary.lower_value)}{' – '}{zoneValue(metricKind, boundary.upper_value)}</Text>
    </View>)}
  </View>;
}
export function ZoneProfileValues({ profile }: { profile: ZoneProfileSnapshot }) {
  // Guard the entire numeric subtree, even if a malformed DTO contains values.
  const visible = !profile.values_hidden;
  return <View style={styles.stack}>
    {!visible ? <ZoneInfoRow icon="info"><Text tone="textMuted">Numerieke waarden blijven verborgen. Je trainingen gebruiken voorlopig alleen RPE en observaties.</Text></ZoneInfoRow> : <>
      {profile.metric ? <View style={styles.metric}><Text variant="supporting" tone="textMuted">{zoneMetricLabels[profile.metric.metric_kind]}</Text><Text variant="sectionTitle" tone="primary">{zoneValue(profile.metric.metric_kind, profile.metric.value)}</Text></View> : null}
      {profile.metric_profiles.map(metric => <View key={metric.metric_kind} style={styles.stack}>
        <View style={styles.metric}><Text variant="label">{zoneMetricLabels[metric.metric_kind]}{metric.is_primary ? ' · primair' : ' · secundair'}</Text><Text tone="primary">{zoneValue(metric.metric_kind, metric.source_value)}</Text></View>
        <ZoneTable boundaries={metric.boundaries} metricKind={metric.metric_kind} />
        <Text variant="supporting" tone="textMuted">{metric.boundary_source} · {metric.zone_model_version}</Text>
      </View>)}
      {profile.metric_profiles.length === 0 && profile.boundaries.length > 0 ? <ZoneTable boundaries={profile.boundaries} metricKind={profile.metric?.metric_kind} /> : null}
    </>}
    <ZoneInfoRow icon="document"><Text variant="label">Bron</Text><Text variant="supporting" tone="textMuted">{profile.source_method} · {profile.source_quality} · {profile.review_status}</Text>
      {profile.zone_model_version ? <Text variant="supporting" tone="textMuted">Model: {profile.zone_model_version}</Text> : null}
      {profile.evidence_version ? <Text variant="supporting" tone="textMuted">Bewijs: {profile.evidence_version}</Text> : null}
    </ZoneInfoRow>
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: space[16] },
  infoRow: { borderTopWidth: layout.decorativeLine, borderTopColor: colors.border, paddingTop: space[16], flexDirection: 'row', alignItems: 'flex-start', gap: space[12] },
  infoCopy: { flex: 1, minWidth: 0, gap: space[4] },
  chip: { alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] },
  pending: { backgroundColor: colors.warningSoft },
  metric: { gap: space[4] },
  table: { borderRadius: radius.inset, borderWidth: layout.decorativeLine, borderColor: colors.border, overflow: 'hidden' },
  tableRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[8], padding: space[12], borderBottomWidth: layout.decorativeLine, borderBottomColor: colors.border },
  stacked: { flexDirection: 'column', alignItems: 'flex-start' },
  zone: { color: colors.primary }, range: { flexShrink: 1 },
});
