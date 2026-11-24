import { studioPresentation } from '../../ui-v3/presentation';
import type { ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import type { ZoneMetricKind, ZoneProfileSnapshot } from '../../api/types';
import { formatRunPace } from '../../lib/runPace';
import { IconTile } from '../primitives/IconTile';
import { Icon, type IconName } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import { useLanguage, type TranslationKey } from '../../i18n/LanguageProvider';
import { translate } from '../../i18n/runtime';

export const zoneMetricLabels: Record<ZoneMetricKind, TranslationKey> = {
  swim_css_seconds_per_100m: 'onboarding.zoneVisuals.metric.swimCss', bike_ftp_watts: 'onboarding.zoneVisuals.metric.bikeFtp',
  bike_threshold_heart_rate_bpm: 'onboarding.zoneVisuals.metric.bikeThresholdHeartRate',
  run_threshold_pace_seconds_per_km: 'onboarding.zoneVisuals.metric.runThresholdPace', run_lthr_bpm: 'onboarding.zoneVisuals.metric.runLthr',
};
const units: Record<ZoneMetricKind, string> = {
  swim_css_seconds_per_100m: 'sec/100 m', bike_ftp_watts: 'watt',
  bike_threshold_heart_rate_bpm: 'bpm', run_threshold_pace_seconds_per_km: 'min/km', run_lthr_bpm: 'bpm',
};
type Translate = ReturnType<typeof useLanguage>['t'];
type Labels = Partial<Record<string, TranslationKey>>;

// API codes are never shown to the athlete. Every known value has a label; a
// value this build does not know falls back to a neutral one.
export function codeLabel(t: Translate, labels: Labels, code: string | null | undefined, fallback: TranslationKey): string {
  return t((code ? labels[code] : undefined) ?? fallback);
}

export const protocolLabels: Labels = {
  start23_run_threshold_30min_v1: 'calibration.protocol.runThreshold30',
  start23_bike_ftp_30min_v1: 'calibration.protocol.bikeFtp30',
  start23_bike_fthr_20min_v1: 'calibration.protocol.bikeFthr20',
  start23_swim_css_400_200_v1: 'calibration.protocol.swimCss',
  start23_week1_run_calibration_v1: 'calibration.protocol.week1Run',
  start23_week1_bike_calibration_v1: 'calibration.protocol.week1Bike',
  start23_week1_swim_calibration_v1: 'calibration.protocol.week1Swim',
};
export const profileStatusLabels: Labels = {
  pending: 'zones.profileStatus.pending', active: 'zones.profileStatus.active', superseded: 'zones.profileStatus.superseded',
  rejected: 'zones.profileStatus.rejected', expired: 'zones.profileStatus.expired',
};
// A zone version made from a protocol evaluation stores that protocol as its method.
const sourceMethodLabels: Labels = {
  ...protocolLabels,
  athlete_entered: 'zones.sourceMethod.athlete_entered', field_test: 'zones.sourceMethod.field_test',
  wearable_import: 'zones.sourceMethod.wearable_import', estimated: 'zones.sourceMethod.estimated',
  tanaka_karvonen_age_hrrest: 'zones.sourceMethod.tanaka_karvonen_age_hrrest',
  physician_or_lab_reported: 'zones.sourceMethod.physician_or_lab_reported',
};
const sourceQualityLabels: Labels = {
  measured_lab: 'zones.sourceQuality.measured_lab', measured_field: 'zones.sourceQuality.measured_field',
  reviewed_field_threshold: 'zones.sourceQuality.reviewed_field_threshold',
  submaximal_calibration_estimate: 'zones.sourceQuality.submaximal_calibration_estimate',
  athlete_entered: 'zones.sourceQuality.athlete_entered', estimated: 'zones.sourceQuality.estimated',
};
const reviewLabels: Labels = {
  pending_athlete_confirmation: 'zones.review.pending_athlete_confirmation', confirmed_by_athlete: 'zones.review.confirmed_by_athlete',
  rejected_by_athlete: 'zones.review.rejected_by_athlete', unreviewed: 'zones.review.unreviewed', not_applicable: 'zones.review.not_applicable',
};
const boundarySourceLabels: Labels = {
  model_derived: 'zones.boundarySource.model_derived', athlete_entered: 'zones.boundarySource.athlete_entered',
};
// Ruleset, zone model and evidence versions keep their provenance under a readable name.
const versionLabels: Labels = {
  'start23-zone-model-1.0': 'zones.version.zoneModel1', 'phase-13-joren-ruleset-1': 'zones.version.ruleset1',
  'start23-calibration-ruleset-v2': 'zones.version.calibrationRuleset2',
  'voorstel-start23-zone-1-5-rekenmodel-v1.0': 'zones.version.zoneEvidence1',
};
export function versionLabel(t: Translate, version: string | null | undefined): string {
  return codeLabel(t, versionLabels, version, 'zones.version.other');
}
export function boundarySourceLabel(t: Translate, source: string): string {
  return codeLabel(t, boundarySourceLabels, source, 'zones.sourceMethod.other');
}
// Method, quality and review state in words; an entered value reads the same
// as method and as quality, so it is said once.
function profileSourceLine(t: Translate, profile: ZoneProfileSnapshot): string {
  return [...new Set([
    codeLabel(t, sourceMethodLabels, profile.source_method, 'zones.sourceMethod.other'),
    codeLabel(t, sourceQualityLabels, profile.source_quality, 'zones.sourceQuality.unknown'),
    codeLabel(t, reviewLabels, profile.review_status, 'zones.review.other'),
  ])].join(' · ');
}
export function zoneValue(kind: ZoneMetricKind | undefined, value: string | null): string {
  if (value === null) return translate('onboarding.zoneVisuals.open');
  if (kind === 'run_threshold_pace_seconds_per_km') return formatRunPace(value);
  return kind ? value + ' ' + units[kind] : value;
}
export function ZoneInfoRow({ icon, children }: { icon: IconName; children: ReactNode }) {
  // V3 keeps supporting facts as a quiet line; the icon tile and rule belong to V2.
  return <View style={styles.infoRow}>{studioPresentation ? <Icon name={icon} size={20} color={colors.textMuted} /> : <IconTile name={icon} size="field" />}<View style={styles.infoCopy}>{children}</View></View>;
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
      <Text variant="label" style={[styles.zone, studioPresentation && styles.zoneLabel]}>Z{boundary.zone_number}</Text>
      <Text style={[styles.range, studioPresentation && styles.numeric]}>{zoneValue(metricKind, boundary.lower_value)}{' – '}{zoneValue(metricKind, boundary.upper_value)}</Text>
    </View>)}
  </View>;
}
export function ZoneProfileValues({ profile }: { profile: ZoneProfileSnapshot }) {
  const { t } = useLanguage();
  // Guard the entire numeric subtree, even if a malformed DTO contains values.
  const visible = !profile.values_hidden;
  return <View style={styles.stack}>
    {!visible ? <ZoneInfoRow icon="info"><Text tone="textMuted">{t('onboarding.zoneVisuals.valuesHidden')}</Text></ZoneInfoRow> : <>
      {profile.metric ? <View style={styles.metric}><Text variant="supporting" tone="textMuted">{t(zoneMetricLabels[profile.metric.metric_kind])}</Text><Text variant={studioPresentation ? 'numeric' : 'sectionTitle'} tone="primary">{zoneValue(profile.metric.metric_kind, profile.metric.value)}</Text></View> : null}
      {profile.metric_profiles.map(metric => <View key={metric.metric_kind} style={styles.stack}>
        <View style={styles.metric}><Text variant="label">{t(zoneMetricLabels[metric.metric_kind])}{t(metric.is_primary ? 'onboarding.zoneVisuals.primary' : 'onboarding.zoneVisuals.secondary')}</Text><Text tone="primary">{zoneValue(metric.metric_kind, metric.source_value)}</Text></View>
        <ZoneTable boundaries={metric.boundaries} metricKind={metric.metric_kind} />
        <Text variant="supporting" tone="textMuted">{boundarySourceLabel(t, metric.boundary_source)} · {versionLabel(t, metric.zone_model_version)}</Text>
      </View>)}
      {profile.metric_profiles.length === 0 && profile.boundaries.length > 0 ? <ZoneTable boundaries={profile.boundaries} metricKind={profile.metric?.metric_kind} /> : null}
    </>}
    <ZoneInfoRow icon="document"><Text variant={studioPresentation ? 'caption' : 'label'}>{t('onboarding.zoneVisuals.source')}</Text><Text variant="supporting" tone="textMuted">{profileSourceLine(t, profile)}</Text>
      {profile.zone_model_version ? <Text variant="supporting" tone="textMuted">{t('onboarding.zoneVisuals.model', { version: versionLabel(t, profile.zone_model_version) })}</Text> : null}
      {profile.evidence_version ? <Text variant="supporting" tone="textMuted">{t('onboarding.zoneVisuals.evidence', { version: versionLabel(t, profile.evidence_version) })}</Text> : null}
    </ZoneInfoRow>
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: studioPresentation ? space[12] : space[16] },
  infoRow: studioPresentation ? { flexDirection: 'row', alignItems: 'flex-start', gap: space[8] }
    : { borderTopWidth: layout.decorativeLine, borderTopColor: colors.border, paddingTop: space[16], flexDirection: 'row', alignItems: 'flex-start', gap: space[12] },
  infoCopy: { flex: 1, minWidth: 0, gap: space[4] },
  chip: { alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] },
  pending: { backgroundColor: colors.warningSoft },
  metric: { gap: space[4] },
  // V3 lists the zones as ruled lines; V2 keeps its boxed table.
  table: studioPresentation ? { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border }
    : { borderRadius: radius.inset, borderWidth: layout.decorativeLine, borderColor: colors.border, overflow: 'hidden' },
  tableRow: studioPresentation ? { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[12], paddingVertical: space[8], borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border }
    : { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[8], padding: space[12], borderBottomWidth: layout.decorativeLine, borderBottomColor: colors.border },
  stacked: { flexDirection: 'column', alignItems: 'flex-start' },
  zoneLabel: { minWidth: 40, color: colors.primary, backgroundColor: colors.primarySoft, paddingHorizontal: 8, borderRadius: 4, textAlign: 'center' },
  numeric: { fontVariant: ['tabular-nums'], fontWeight: '600' },
  zone: { color: colors.primary }, range: { flexShrink: 1 },
});
