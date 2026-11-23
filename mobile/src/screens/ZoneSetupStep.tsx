import { studioPresentation } from '../ui-v3/presentation';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  useWindowDimensions,
  View,
} from 'react-native';

import {
  getZoneSetupOptions,
  listCalibrationProtocols,
} from '../api/client';
import type {
  CalibrationProtocol,
  Discipline,
  DisciplineSetupInput,
  GuidanceMode,
  OnboardingState,
  SelectableZoneSetupRoute,
  ZoneBoundary,
  ZoneMetricKind,
  ZoneSetupOption,
} from '../api/types';
import { FormSection, formGap } from '../ui-v2/components/FormComposition';
import { ZoneStatusChip } from '../ui-v2/components/ZoneVisuals';
import { parseRunPace } from '../lib/runPace';
import { colors, layout, space } from '../ui-v2/tokens';
import { Text } from '../ui-v2/primitives/Text';
import { Button } from '../ui-v2/primitives/Button';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Input } from '../ui-v2/primitives/Input';
import { Notice } from '../ui-v2/primitives/Notice';
import { useLanguage, type TranslationKey } from '../i18n/LanguageProvider';
import { ChoiceChips } from '../ui-v3/screens/support';

type MetricOption = {
  kind: ZoneMetricKind;
  labelKey: TranslationKey;
  unit: string;
  guidance: Exclude<GuidanceMode, 'combined' | 'rpe_only'>;
  descending: boolean;
};

const disciplineLabels: Record<Discipline, TranslationKey> = {
  swim: 'onboarding.zoneSetup.discipline.swim',
  bike: 'onboarding.zoneSetup.discipline.bike',
  run: 'onboarding.zoneSetup.discipline.run',
};

const metricOptions: Record<Discipline, readonly MetricOption[]> = {
  swim: [
    {
      kind: 'swim_css_seconds_per_100m',
      labelKey: 'onboarding.zoneSetup.metric.css',
      unit: 'sec/100 m',
      guidance: 'pace',
      descending: true,
    },
  ],
  bike: [
    {
      kind: 'bike_ftp_watts',
      labelKey: 'onboarding.zoneSetup.metric.ftp',
      unit: 'watt',
      guidance: 'power',
      descending: false,
    },
    {
      kind: 'bike_threshold_heart_rate_bpm',
      labelKey: 'onboarding.zoneSetup.metric.bikeThresholdHeartRate',
      unit: 'bpm',
      guidance: 'heart_rate',
      descending: false,
    },
  ],
  run: [
    {
      kind: 'run_threshold_pace_seconds_per_km',
      labelKey: 'onboarding.zoneSetup.metric.runThresholdPace',
      unit: 'min/km',
      guidance: 'pace',
      descending: true,
    },
    {
      kind: 'run_lthr_bpm',
      labelKey: 'onboarding.zoneSetup.metric.lthr',
      unit: 'bpm',
      guidance: 'heart_rate',
      descending: false,
    },
  ],
};

const routeDescriptions: Record<SelectableZoneSetupRoute, TranslationKey> = {
  known_values: 'onboarding.zoneSetup.route.knownValues',
  field_test: 'onboarding.zoneSetup.route.fieldTest',
  calibration_week: 'onboarding.zoneSetup.route.calibrationWeek',
};

const guidanceLabels: Record<GuidanceMode, TranslationKey> = {
  power: 'onboarding.zoneSetup.guidance.power',
  heart_rate: 'onboarding.zoneSetup.guidance.heartRate',
  combined: 'onboarding.zoneSetup.guidance.combined',
  pace: 'onboarding.zoneSetup.guidance.pace',
  rpe_only: 'onboarding.zoneSetup.guidance.rpeOnly',
};

const protocolLabels: Record<string, TranslationKey> = {
  start23_run_threshold_30min_v1: 'onboarding.zoneSetup.protocol.runThreshold30',
  start23_bike_ftp_30min_v1: 'onboarding.zoneSetup.protocol.bikeFtp30',
  start23_bike_fthr_20min_v1: 'onboarding.zoneSetup.protocol.bikeFthr20',
  start23_swim_css_400_200_v1: 'onboarding.zoneSetup.protocol.swimCss',
};

function emptyBoundaries(): ZoneBoundary[] {
  return Array.from({ length: 5 }, (_, index) => ({
    zone_number: index + 1,
    lower_value: '',
    upper_value: '',
  }));
}

function guidanceForKnownValues(
  options: readonly MetricOption[],
  values: Partial<Record<ZoneMetricKind, string>>,
): GuidanceMode {
  const entered = options.filter((option) => metricValue(option, values[option.kind]) > 0);
  if (entered.length > 1) return 'combined';
  return entered[0]?.guidance ?? options[0].guidance;
}

function metricValue(option: MetricOption, raw?: string): number {
  return option.kind === 'run_threshold_pace_seconds_per_km'
    ? parseRunPace(raw ?? '') ?? NaN
    : Number(raw);
}

// One labelled choice inside a route. A single option leaves nothing to choose,
// so it reads as a plain fact instead of a control.
function OptionGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}) {
  if (options.length === 0) return null;
  return (
    <View style={styles.group}>
      <Text variant="label">{label}</Text>
      {options.length === 1 ? (
        <Text tone="textMuted">{options[0].label}</Text>
      ) : (
        <ChoiceChips
          accessibilityLabel={label}
          isSelected={(option) => option === value}
          mode="radio"
          onPress={onChange}
          options={options}
        />
      )}
    </View>
  );
}

function SaveButton({
  disabled,
  saving,
  label,
  onPress,
}: {
  disabled: boolean;
  saving: boolean;
  label: string;
  onPress: () => void;
}) {
  return <Button disabled={disabled} busy={saving} label={label} onPress={onPress} trailingIcon="forward" />;
}

type Props = {
  accessToken: string;
  disciplineOverride?: Discipline;
  profileMode?: boolean;
  state: OnboardingState;
  saving: boolean;
  onSave: (
    discipline: Discipline,
    input: DisciplineSetupInput,
  ) => Promise<void>;
};

export function ZoneSetupStep({
  accessToken,
  disciplineOverride,
  profileMode = false,
  state,
  saving,
  onSave,
}: Props) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  // Two boundary fields fit beside the zone number on a phone; only very
  // narrow screens and large text stack them.
  const compact = width < 340 || fontScale > 1.3;
  const configured = useMemo(
    () =>
      new Set<Discipline>(
        state.zones
          .filter((zone) => zone.status === 'active')
          .map((zone) => zone.discipline),
      ),
    [state.zones],
  );
  const started = useMemo(
    () =>
      new Set<Discipline>([
        ...configured,
        ...state.discipline_setups.map((setup) => setup.discipline),
      ]),
    [configured, state.discipline_setups],
  );
  const requiredDisciplines = state.required_disciplines;
  const discipline =
    disciplineOverride ??
    requiredDisciplines.find((candidate) => !started.has(candidate)) ??
    requiredDisciplines.find((candidate) => !configured.has(candidate)) ??
    // Everything is configured when the athlete comes back from a later step;
    // stay on a discipline the goal actually requires.
    requiredDisciplines[0] ??
    'run';
  const availableMetrics = metricOptions[discipline];
  const [options, setOptions] = useState<ZoneSetupOption[]>([]);
  const [protocols, setProtocols] = useState<CalibrationProtocol[]>([]);
  const [loadingChoices, setLoadingChoices] = useState(true);
  const [choiceError, setChoiceError] = useState<string | null>(null);
  const [route, setRoute] = useState<SelectableZoneSetupRoute | null>(null);
  const [knownValues, setKnownValues] = useState<
    Partial<Record<ZoneMetricKind, string>>
  >({});
  const [knownValueSource, setKnownValueSource] = useState<
    'athlete_entered' | 'measured_lab'
  >('athlete_entered');
  const [includeBoundaries, setIncludeBoundaries] = useState(false);
  const [boundaryMetric, setBoundaryMetric] = useState<ZoneMetricKind>(
    availableMetrics[0].kind,
  );
  const [boundaries, setBoundaries] = useState<ZoneBoundary[]>(emptyBoundaries);
  const [selectedProtocolId, setSelectedProtocolId] = useState<string | null>(
    null,
  );
  const [guidanceMode, setGuidanceMode] = useState<GuidanceMode>(
    availableMetrics[0].guidance,
  );
  const [poolLength, setPoolLength] = useState<25 | 50>(25);
  const [knownValuesValidationAttempted, setKnownValuesValidationAttempted] =
    useState(false);

  useEffect(() => {
    let mounted = true;
    setLoadingChoices(true);
    setChoiceError(null);
    Promise.all([
      getZoneSetupOptions(accessToken, discipline),
      listCalibrationProtocols(accessToken, discipline),
    ])
      .then(([nextOptions, nextProtocols]) => {
        if (!mounted) return;
        setOptions(nextOptions);
        setProtocols(nextProtocols);
      })
      .catch((caught: unknown) => {
        if (!mounted) return;
        setChoiceError(
          caught instanceof Error
            ? caught.message
            : t('onboarding.zoneSetup.loadFailed'),
        );
      })
      .finally(() => {
        if (mounted) setLoadingChoices(false);
      });
    return () => {
      mounted = false;
    };
  }, [accessToken, discipline]);

  const fieldTests = protocols.filter(
    (protocol) => protocol.protocol_type === 'field_test',
  );
  const selectedProtocol = fieldTests.find(
    (protocol) => protocol.protocol_id === selectedProtocolId,
  );
  const calibrationProtocol = protocols.find(
    (protocol) => protocol.protocol_type === 'submaximal_calibration',
  );
  const boundaryOption = availableMetrics.find(
    (option) => option.kind === boundaryMetric,
  )!;
  const completeBoundaries = boundaries.every(
    (boundary) =>
      boundary.lower_value.trim() !== '' &&
      boundary.upper_value.trim() !== '',
  );
  const positiveWidths = boundaries.every(
    (boundary) =>
      metricValue(boundaryOption, boundary.lower_value) >= 0 &&
      metricValue(boundaryOption, boundary.upper_value) > metricValue(boundaryOption, boundary.lower_value),
  );
  const contiguous = boundaries.slice(1).every((current, index) => {
    const previous = boundaries[index];
    return boundaryOption.descending
      ? metricValue(boundaryOption, previous.lower_value) === metricValue(boundaryOption, current.upper_value)
      : metricValue(boundaryOption, previous.upper_value) === metricValue(boundaryOption, current.lower_value);
  });
  const wholePaceBoundaries =
    !boundaryOption.descending ||
    boundaries.every(
      (boundary) =>
        Number.isInteger(metricValue(boundaryOption, boundary.lower_value)) &&
        Number.isInteger(metricValue(boundaryOption, boundary.upper_value)),
    );
  const boundariesValid =
    !includeBoundaries ||
    (completeBoundaries &&
      positiveWidths &&
      contiguous &&
      wholePaceBoundaries);
  const enteredThresholds = availableMetrics.filter(
    (option) => metricValue(option, knownValues[option.kind]) > 0,
  );
  const wholePaceThresholds = enteredThresholds.every(
    (option) =>
      !option.descending || Number.isInteger(metricValue(option, knownValues[option.kind])),
  );
  const selectedThresholdPresent = enteredThresholds.some(
    (option) => option.kind === boundaryMetric,
  );
  const invalidThresholds = availableMetrics.filter((option) => {
    const rawValue = knownValues[option.kind]?.trim() ?? '';
    if (!rawValue) return false;
    const numericValue = metricValue(option, rawValue);
    return (
      !Number.isFinite(numericValue) ||
      numericValue <= 0 ||
      (option.descending && !Number.isInteger(numericValue))
    );
  });
  const knownValuesValid =
    enteredThresholds.length > 0 &&
    invalidThresholds.length === 0 &&
    boundariesValid &&
    (!includeBoundaries || selectedThresholdPresent);

  const selectRoute = (nextRoute: SelectableZoneSetupRoute) => {
    setRoute(nextRoute);
    if (nextRoute === 'known_values') {
      setGuidanceMode(guidanceForKnownValues(availableMetrics, knownValues));
    } else if (nextRoute === 'field_test') {
      const first = fieldTests[0];
      setSelectedProtocolId(first?.protocol_id ?? null);
      setGuidanceMode(first?.guidance_modes[0] ?? availableMetrics[0].guidance);
    } else {
      setGuidanceMode(
        calibrationProtocol?.guidance_modes[0] ??
          availableMetrics[0].guidance,
      );
    }
  };

  const submitKnownValues = () => {
    setKnownValuesValidationAttempted(true);
    if (!knownValuesValid) return;
    const thresholds = enteredThresholds.map((option) => ({
      metric_kind: option.kind,
      value: String(metricValue(option, knownValues[option.kind])),
    }));
    void onSave(discipline, {
      setup_route: 'known_values',
      guidance_mode: guidanceForKnownValues(availableMetrics, knownValues),
      source_quality: knownValueSource,
      thresholds,
      zone_profiles: includeBoundaries
        ? [{ metric_kind: boundaryMetric, boundaries: boundaries.map((boundary) => ({
            ...boundary,
            lower_value: String(metricValue(boundaryOption, boundary.lower_value)),
            upper_value: String(metricValue(boundaryOption, boundary.upper_value)),
          })) }]
        : [],
    });
  };

  const submitFieldTest = () => {
    if (!selectedProtocol) return;
    void onSave(discipline, {
      setup_route: 'field_test',
      guidance_mode: guidanceMode,
      protocol_id: selectedProtocol.protocol_id,
      ...(discipline === 'swim'
        ? { pool_length_meters: poolLength }
        : {}),
    });
  };

  const submitCalibration = () => {
    void onSave(discipline, {
      setup_route: 'calibration_week',
      guidance_mode: guidanceMode,
      ...(discipline === 'swim'
        ? { pool_length_meters: poolLength }
        : {}),
    });
  };

  const guidanceOptions = (modes: readonly GuidanceMode[]) =>
    modes.map((mode) => ({ value: mode, label: t(guidanceLabels[mode]) }));
  const poolChoice = discipline === 'swim' ? (
    <OptionGroup
      label={t('onboarding.zoneSetup.poolLabel')}
      onChange={(value) => setPoolLength(value === '50' ? 50 : 25)}
      options={[
        { value: '25', label: t('onboarding.zoneSetup.pool25') },
        { value: '50', label: t('onboarding.zoneSetup.pool50') },
      ]}
      value={String(poolLength)}
    />
  ) : null;

  return (
    <View style={styles.step}>
      <View style={styles.heading}>
        {/* V3 onboarding already shows this step above in its progress rail. */}
        {profileMode || !studioPresentation ? <Text variant="caption" tone="primary" style={styles.eyebrow}>
          {profileMode ? t('onboarding.zoneSetup.eyebrowProfile') : t('onboarding.zoneSetup.eyebrowStep')}
        </Text> : null}
        <Text variant="sectionTitle" accessibilityRole="header">{t('onboarding.zoneSetup.title', { discipline: t(disciplineLabels[discipline]) })}</Text>
        <Text variant={studioPresentation ? 'supporting' : 'body'} tone="textMuted">
          {t('onboarding.zoneSetup.description')}
        </Text>
      </View>

      {requiredDisciplines.length > 1 ? (
        <View style={styles.progressRow}>
          {requiredDisciplines.map((item) => (
            <ZoneStatusChip
              key={item}
              label={`${configured.has(item) ? '✓ ' : ''}${t(disciplineLabels[item])}`}
            />
          ))}
        </View>
      ) : null}

      {loadingChoices ? (
        <ActivityIndicator accessibilityLabel={t('common.loading')} color={colors.primary} />
      ) : choiceError ? (
        <Notice tone="error">{choiceError}</Notice>
      ) : (
        <View accessibilityRole="radiogroup" style={styles.routeList}>
          {options.map((option) => (
            <ChoiceRow key={option.setup_route} label={option.label} hint={t(routeDescriptions[option.setup_route])}
              selected={route === option.setup_route} onPress={() => selectRoute(option.setup_route)} />
          ))}
        </View>
      )}

      {route === 'known_values' ? (
        <FormSection>
          <View style={styles.copy}>
            <Text variant="label" accessibilityRole="header">{t('onboarding.zoneSetup.known.title')}</Text>
            <Text variant="supporting" tone="textMuted">
              {t('onboarding.zoneSetup.known.text')}
            </Text>
          </View>
          <OptionGroup
            label={t('onboarding.zoneSetup.known.sourceLabel')}
            onChange={setKnownValueSource}
            options={[
              { value: 'athlete_entered', label: t('onboarding.zoneSetup.known.athleteEntered') },
              { value: 'measured_lab', label: t('onboarding.zoneSetup.known.measuredLab') },
            ]}
            value={knownValueSource}
          />
          {availableMetrics.map((option) => (
            <Input
              accessibilityLabel={t(option.labelKey)}
              error={
                knownValuesValidationAttempted
                  ? invalidThresholds.includes(option)
                    ? option.descending
                      ? option.kind === 'run_threshold_pace_seconds_per_km'
                        ? t('onboarding.paceFormat')
                        : t('onboarding.zoneSetup.known.wholeSeconds')
                      : t('onboarding.zoneSetup.known.positive')
                    : enteredThresholds.length === 0
                      ? availableMetrics.length === 1
                        ? t('onboarding.zoneSetup.known.required', { label: t(option.labelKey) })
                        : t('onboarding.zoneSetup.known.atLeast', {
                            labels: availableMetrics
                              .map((candidate) => t(candidate.labelKey))
                              .join(t('onboarding.zoneSetup.known.or')),
                          })
                      : undefined
                  : undefined
              }
              hint={
                option.descending
                  ? option.kind === 'run_threshold_pace_seconds_per_km'
                    ? t('onboarding.paceFormat')
                    : t('onboarding.zoneSetup.known.canonicalHint')
                  : undefined
              }
              inputMode={option.kind === 'run_threshold_pace_seconds_per_km' ? 'text' : 'decimal'}
              key={option.kind}
              label={availableMetrics.length === 1 ? `${t(option.labelKey)} *` : t(option.labelKey)}
              onChangeText={(value) => {
                const nextValues = {
                  ...knownValues,
                  [option.kind]: value,
                };
                setKnownValues((current) => ({
                  ...current,
                  [option.kind]: value,
                }));
                if (
                  metricValue(option, value) > 0 &&
                  availableMetrics.filter(
                    (candidate) =>
                      candidate.kind !== option.kind &&
                      metricValue(candidate, knownValues[candidate.kind]) > 0,
                  ).length === 0
                ) {
                  setBoundaryMetric(option.kind);
                }
                setGuidanceMode(
                  guidanceForKnownValues(availableMetrics, nextValues),
                );
              }}
              placeholder={
                option.kind === 'run_threshold_pace_seconds_per_km'
                  ? '5:00'
                  : availableMetrics.length === 1
                  ? t('onboarding.zoneSetup.known.placeholderRequired')
                  : t('onboarding.zoneSetup.known.placeholderAtLeastOne')
              }
              unit={option.unit}
              value={knownValues[option.kind] ?? ''}
            />
          ))}

          {!wholePaceThresholds ? (
            <Text variant="supporting" tone="destructive">
              {t('onboarding.zoneSetup.known.wholePaceError')}
            </Text>
          ) : null}

          {knownValuesValidationAttempted && enteredThresholds.length === 0 ? (
            <Text accessibilityRole="alert" variant="supporting" tone="destructive">
              {t('onboarding.zoneSetup.known.noneEntered')}
            </Text>
          ) : null}

          <ChoiceRow mode="checkbox" label={t('onboarding.zoneSetup.known.includeBoundaries')} selected={includeBoundaries}
            onPress={() => setIncludeBoundaries((current) => !current)} />

          {includeBoundaries ? (
            <View style={styles.boundaries}>
              {enteredThresholds.length > 1 ? (
                <OptionGroup
                  label={t('onboarding.zoneSetup.known.boundaryMetricLabel')}
                  onChange={setBoundaryMetric}
                  options={enteredThresholds.map((option) => ({ value: option.kind, label: t(option.labelKey) }))}
                  value={boundaryMetric}
                />
              ) : null}
              <Text variant="supporting" tone="textMuted">
                {boundaryOption.descending
                  ? t('onboarding.zoneSetup.known.descendingHint')
                  : t('onboarding.zoneSetup.known.ascendingHint')}
              </Text>
              {boundaries.map((boundary, index) => (
                <View key={boundary.zone_number} style={[styles.boundaryRow, compact && styles.stacked]}>
                  <View style={compact ? undefined : styles.zoneLabel}>
                    <Text variant="label" tone="primary">Z{boundary.zone_number}</Text>
                  </View>
                  {(['lower_value', 'upper_value'] as const).map((edge) => (
                    <View key={edge} style={compact ? styles.fullWidth : styles.boundaryInput}>
                      <Input
                        inputMode={boundaryMetric === 'run_threshold_pace_seconds_per_km' ? 'text' : 'decimal'}
                        label={t(edge === 'lower_value' ? 'onboarding.zoneSetup.known.lower' : 'onboarding.zoneSetup.known.upper')}
                        onChangeText={(value) =>
                          setBoundaries((current) =>
                            current.map((item, itemIndex) =>
                              itemIndex === index
                                ? { ...item, [edge]: value }
                                : item,
                            ),
                          )
                        }
                        placeholder={boundaryMetric === 'run_threshold_pace_seconds_per_km' ? '5:00' : '0'}
                        value={boundary[edge]}
                      />
                    </View>
                  ))}
                </View>
              ))}
              {!boundariesValid ? (
                <Text variant="supporting" tone="destructive">
                  {t('onboarding.zoneSetup.known.boundariesError')}
                </Text>
              ) : null}
            </View>
          ) : null}

          <SaveButton
            disabled={false}
            label={t('onboarding.zoneSetup.known.save')}
            onPress={submitKnownValues}
            saving={saving}
          />
        </FormSection>
      ) : null}

      {route === 'field_test' ? (
        <FormSection>
          <View style={styles.copy}>
            <ZoneStatusChip label={t('onboarding.zoneSetup.field.chip')} pending />
            <Text variant="supporting" tone="textMuted">
              {t('onboarding.zoneSetup.field.text')}
            </Text>
          </View>
          <OptionGroup
            label={t('onboarding.zoneSetup.field.protocolLabel')}
            onChange={(protocolId) => {
              const protocol = fieldTests.find((candidate) => candidate.protocol_id === protocolId);
              if (!protocol) return;
              setSelectedProtocolId(protocol.protocol_id);
              setGuidanceMode(protocol.guidance_modes[0]);
            }}
            options={fieldTests.map((protocol) => ({
              value: protocol.protocol_id,
              label: protocolLabels[protocol.protocol_id] ? t(protocolLabels[protocol.protocol_id]) : protocol.protocol_id,
            }))}
            value={selectedProtocolId ?? ''}
          />
          {selectedProtocol ? (
            <OptionGroup
              label={t('onboarding.zoneSetup.guidanceLabel')}
              onChange={setGuidanceMode}
              options={guidanceOptions(selectedProtocol.guidance_modes)}
              value={guidanceMode}
            />
          ) : null}
          {poolChoice}
          <Notice>{t('onboarding.zoneSetup.field.safety')}</Notice>
          <SaveButton
            disabled={!selectedProtocol}
            label={t('onboarding.zoneSetup.field.save')}
            onPress={submitFieldTest}
            saving={saving}
          />
        </FormSection>
      ) : null}

      {route === 'calibration_week' ? (
        <FormSection>
          <View style={styles.copy}>
            <ZoneStatusChip label={t('onboarding.zoneSetup.calibration.chip')} />
            <Text variant="supporting" tone="textMuted">
              {t('onboarding.zoneSetup.calibration.text')}
            </Text>
          </View>
          <OptionGroup
            label={t('onboarding.zoneSetup.guidanceLabel')}
            onChange={setGuidanceMode}
            options={guidanceOptions(calibrationProtocol?.guidance_modes ?? [])}
            value={guidanceMode}
          />
          {poolChoice}
          <SaveButton
            disabled={!calibrationProtocol}
            label={t('onboarding.zoneSetup.calibration.save')}
            onPress={submitCalibration}
            saving={saving}
          />
        </FormSection>
      ) : null}

    </View>
  );
}

const styles = StyleSheet.create({
  step: { gap: formGap },
  heading: { gap: space[8] },
  eyebrow: { textTransform: 'uppercase', letterSpacing: 1 },
  copy: { gap: space[8] },
  progressRow: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] },
  routeList: { gap: space[8] },
  group: { gap: layout.labelFieldGap },
  boundaries: { gap: formGap },
  boundaryRow: { alignItems: 'flex-end', flexDirection: 'row', gap: space[12] },
  stacked: { flexDirection: 'column', alignItems: 'stretch' },
  fullWidth: { alignSelf: 'stretch' },
  // Centres the zone number on the field beside it; field labels sit above.
  zoneLabel: { height: layout.fieldHeight, justifyContent: 'center', minWidth: space[32] },
  boundaryInput: { flex: 1 },
});
