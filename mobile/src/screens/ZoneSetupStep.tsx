import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
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
  ZoneBoundary,
  ZoneMetricKind,
  ZoneSetupOption,
  ZoneSetupRoute,
} from '../api/types';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

type MetricOption = {
  kind: ZoneMetricKind;
  label: string;
  unit: string;
  guidance: Exclude<GuidanceMode, 'combined' | 'rpe_only'>;
  descending: boolean;
};

const disciplines: readonly Discipline[] = ['swim', 'bike', 'run'];

const disciplineLabels: Record<Discipline, string> = {
  swim: 'zwemmen',
  bike: 'fietsen',
  run: 'hardlopen',
};

const metricOptions: Record<Discipline, readonly MetricOption[]> = {
  swim: [
    {
      kind: 'swim_css_seconds_per_100m',
      label: 'CSS',
      unit: 'sec/100 m',
      guidance: 'pace',
      descending: true,
    },
  ],
  bike: [
    {
      kind: 'bike_ftp_watts',
      label: 'FTP',
      unit: 'watt',
      guidance: 'power',
      descending: false,
    },
    {
      kind: 'bike_threshold_heart_rate_bpm',
      label: 'Drempelhartslag fiets',
      unit: 'bpm',
      guidance: 'heart_rate',
      descending: false,
    },
  ],
  run: [
    {
      kind: 'run_threshold_pace_seconds_per_km',
      label: 'Drempeltempo',
      unit: 'sec/km',
      guidance: 'pace',
      descending: true,
    },
    {
      kind: 'run_lthr_bpm',
      label: 'LTHR',
      unit: 'bpm',
      guidance: 'heart_rate',
      descending: false,
    },
  ],
};

const routeDescriptions: Record<ZoneSetupRoute, string> = {
  known_values:
    'Bevestig een bekende drempelwaarde. Wombo berekent een apart Zone 1-5-voorstel; bestaande grenzen kun je als override invoeren.',
  field_test:
    'Voer een beoordeelde maximale veldtest uit voor een drempelschatting.',
  calibration_week:
    'Train met dezelfde veilige RPE-workouts; Wombo bewaart daarnaast geschikte objectieve kalibratie-observaties.',
  rpe_only:
    'Train met dezelfde veilige RPE-workouts, zonder extra kalibratie-observaties.',
};

const guidanceLabels: Record<GuidanceMode, string> = {
  power: 'Vermogen',
  heart_rate: 'Hartslag',
  combined: 'Gecombineerd',
  pace: 'Tempo',
  rpe_only: 'Alleen RPE',
};

const protocolLabels: Record<string, string> = {
  start23_run_threshold_30min_v1: '30 min loopdrempeltest',
  start23_bike_ftp_30min_v1: '30 min FTP-test',
  start23_bike_fthr_20min_v1: '20 min fietsdrempelhartslagtest',
  start23_swim_css_400_200_v1: 'CSS 400/200 m-test',
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
  const entered = options.filter((option) => Number(values[option.kind]) > 0);
  if (entered.length > 1) return 'combined';
  return entered[0]?.guidance ?? options[0].guidance;
}

function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        selected && styles.chipSelected,
        pressed && styles.pressed,
      ]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
        {label}
      </Text>
    </Pressable>
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
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || saving}
      onPress={onPress}
      style={({ pressed }) => [
        styles.saveButton,
        (disabled || saving) && styles.disabled,
        pressed && styles.pressed,
      ]}
    >
      {saving ? (
        <ActivityIndicator color={colors.white} />
      ) : (
        <Text style={styles.saveButtonText}>{label}</Text>
      )}
    </Pressable>
  );
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
  const configured = useMemo(
    () =>
      new Set<Discipline>([
        ...state.zones
          .filter((zone) => zone.status === 'active')
          .map((zone) => zone.discipline),
        ...state.discipline_setups.map((setup) => setup.discipline),
      ]),
    [state.discipline_setups, state.zones],
  );
  const discipline =
    disciplineOverride ??
    disciplines.find((candidate) => !configured.has(candidate)) ??
    'run';
  const availableMetrics = metricOptions[discipline];
  const [options, setOptions] = useState<ZoneSetupOption[]>([]);
  const [protocols, setProtocols] = useState<CalibrationProtocol[]>([]);
  const [loadingChoices, setLoadingChoices] = useState(true);
  const [choiceError, setChoiceError] = useState<string | null>(null);
  const [route, setRoute] = useState<ZoneSetupRoute | null>(null);
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

  useEffect(() => {
    let mounted = true;
    setLoadingChoices(true);
    setChoiceError(null);
    Promise.all([
      getZoneSetupOptions(accessToken),
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
            : 'De zonekeuzes konden niet worden geladen.',
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
      Number(boundary.lower_value) >= 0 &&
      Number(boundary.upper_value) > Number(boundary.lower_value),
  );
  const contiguous = boundaries.slice(1).every((current, index) => {
    const previous = boundaries[index];
    return boundaryOption.descending
      ? Number(previous.lower_value) === Number(current.upper_value)
      : Number(previous.upper_value) === Number(current.lower_value);
  });
  const wholePaceBoundaries =
    !boundaryOption.descending ||
    boundaries.every(
      (boundary) =>
        Number.isInteger(Number(boundary.lower_value)) &&
        Number.isInteger(Number(boundary.upper_value)),
    );
  const boundariesValid =
    !includeBoundaries ||
    (completeBoundaries &&
      positiveWidths &&
      contiguous &&
      wholePaceBoundaries);
  const enteredThresholds = availableMetrics.filter(
    (option) => Number(knownValues[option.kind]) > 0,
  );
  const wholePaceThresholds = enteredThresholds.every(
    (option) =>
      !option.descending || Number.isInteger(Number(knownValues[option.kind])),
  );
  const selectedThresholdPresent = enteredThresholds.some(
    (option) => option.kind === boundaryMetric,
  );

  const selectRoute = (nextRoute: ZoneSetupRoute) => {
    setRoute(nextRoute);
    if (nextRoute === 'known_values') {
      setGuidanceMode(guidanceForKnownValues(availableMetrics, knownValues));
    } else if (nextRoute === 'rpe_only') {
      setGuidanceMode('rpe_only');
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
    const thresholds = enteredThresholds.map((option) => ({
      metric_kind: option.kind,
      value: knownValues[option.kind]!,
    }));
    void onSave(discipline, {
      setup_route: 'known_values',
      guidance_mode: guidanceForKnownValues(availableMetrics, knownValues),
      source_quality: knownValueSource,
      thresholds,
      zone_profiles: includeBoundaries
        ? [{ metric_kind: boundaryMetric, boundaries }]
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

  return (
    <View style={styles.step}>
      <View>
        <Text style={styles.eyebrow}>
          {profileMode ? 'Profiel bijwerken' : 'Stap 4 van 5'}
        </Text>
        <Text style={styles.title}>Instellen voor {disciplineLabels[discipline]}</Text>
        <Text style={styles.description}>
          Kies één expliciete route. Drempels, voorlopige observaties en echte
          Zone 1-5-profielen blijven verschillende statussen.
        </Text>
      </View>

      <View style={styles.progressRow}>
        {disciplines.map((item) => (
          <StatusPill
            key={item}
            label={`${configured.has(item) ? '✓ ' : ''}${disciplineLabels[item]}`}
            tone={configured.has(item) ? 'brand' : 'neutral'}
          />
        ))}
      </View>

      {loadingChoices ? (
        <ActivityIndicator color={colors.brand} />
      ) : choiceError ? (
        <Text style={styles.error}>{choiceError}</Text>
      ) : (
        <View accessibilityRole="radiogroup" style={styles.routeList}>
          {options.map((option) => (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ checked: route === option.setup_route }}
              key={option.setup_route}
              onPress={() => selectRoute(option.setup_route)}
              style={({ pressed }) => [
                styles.routeCard,
                route === option.setup_route && styles.routeCardSelected,
                pressed && styles.pressed,
              ]}
            >
              <View style={styles.routeHeading}>
                <Text style={styles.routeTitle}>{option.label}</Text>
                <View
                  style={[
                    styles.radio,
                    route === option.setup_route && styles.radioSelected,
                  ]}
                />
              </View>
              <Text style={styles.routeDescription}>
                {routeDescriptions[option.setup_route]}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      {route === 'known_values' ? (
        <View style={styles.panel}>
          <Text style={styles.panelTitle}>Bekende waarden</Text>
          <Text style={styles.panelText}>
            Eén bekende drempel is genoeg. Laat de optionele grenzen leeg om
            het geversioneerde Wombo-model te gebruiken. De zones blijven
            daarna eerst een apart voorstel.
          </Text>
          <View accessibilityRole="radiogroup" style={styles.chips}>
            <Chip
              label="Zelf bekende waarde"
              onPress={() => setKnownValueSource('athlete_entered')}
              selected={knownValueSource === 'athlete_entered'}
            />
            <Chip
              label="Gemeten door arts/lab"
              onPress={() => setKnownValueSource('measured_lab')}
              selected={knownValueSource === 'measured_lab'}
            />
          </View>
          {availableMetrics.map((option) => (
            <FormField
              hint={
                option.descending
                  ? 'Gebruik hele seconden in de canonieke eenheid.'
                  : undefined
              }
              inputMode="decimal"
              key={option.kind}
              label={option.label}
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
                  Number(value) > 0 &&
                  availableMetrics.filter(
                    (candidate) =>
                      candidate.kind !== option.kind &&
                      Number(knownValues[candidate.kind]) > 0,
                  ).length === 0
                ) {
                  setBoundaryMetric(option.kind);
                }
                setGuidanceMode(
                  guidanceForKnownValues(availableMetrics, nextValues),
                );
              }}
              placeholder="Optioneel"
              suffix={<Text style={styles.unit}>{option.unit}</Text>}
              value={knownValues[option.kind] ?? ''}
            />
          ))}

          {!wholePaceThresholds ? (
            <Text style={styles.error}>
              CSS en drempeltempo gebruiken alleen hele seconden.
            </Text>
          ) : null}

          <Pressable
            accessibilityRole="checkbox"
            accessibilityState={{ checked: includeBoundaries }}
            onPress={() => setIncludeBoundaries((current) => !current)}
            style={styles.checkboxRow}
          >
            <View
              style={[styles.checkbox, includeBoundaries && styles.checkboxSelected]}
            />
            <Text style={styles.checkboxText}>Ik ken ook vijf zonegrenzen</Text>
          </Pressable>

          {includeBoundaries ? (
            <View style={styles.boundaryPanel}>
              {enteredThresholds.length > 1 ? (
                <View style={styles.chips}>
                  {enteredThresholds.map((option) => (
                    <Chip
                      key={option.kind}
                      label={option.label}
                      onPress={() => setBoundaryMetric(option.kind)}
                      selected={boundaryMetric === option.kind}
                    />
                  ))}
                </View>
              ) : null}
              <Text style={styles.panelText}>
                {boundaryOption.descending
                  ? 'Z1 is het langzaamst; de waarden dalen richting Z5.'
                  : 'Iedere bovengrens sluit aan op de volgende ondergrens.'}
              </Text>
              {boundaries.map((boundary, index) => (
                <View key={boundary.zone_number} style={styles.boundaryRow}>
                  <Text style={styles.zoneLabel}>Z{boundary.zone_number}</Text>
                  <View style={styles.boundaryInput}>
                    <FormField
                      inputMode="decimal"
                      label="Onder"
                      onChangeText={(value) =>
                        setBoundaries((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index
                              ? { ...item, lower_value: value }
                              : item,
                          ),
                        )
                      }
                      placeholder="0"
                      value={boundary.lower_value}
                    />
                  </View>
                  <View style={styles.boundaryInput}>
                    <FormField
                      inputMode="decimal"
                      label="Boven"
                      onChangeText={(value) =>
                        setBoundaries((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index
                              ? { ...item, upper_value: value }
                              : item,
                          ),
                        )
                      }
                      placeholder="0"
                      value={boundary.upper_value}
                    />
                  </View>
                </View>
              ))}
              {!boundariesValid ? (
                <Text style={styles.error}>
                  Vul vijf positieve, aaneengesloten grenzen in. Tempo gebruikt
                  hele seconden en daalt van Z1 naar Z5.
                </Text>
              ) : null}
            </View>
          ) : null}

          <SaveButton
            disabled={
              enteredThresholds.length === 0 ||
              !wholePaceThresholds ||
              !boundariesValid ||
              (includeBoundaries && !selectedThresholdPresent)
            }
            label="Bekende waarden bewaren"
            onPress={submitKnownValues}
            saving={saving}
          />
        </View>
      ) : null}

      {route === 'field_test' ? (
        <View style={styles.panel}>
          <StatusPill label="Maximale veldtest" tone="accent" />
          <Text style={styles.panelText}>
            Kies alleen een test die je veilig kunt uitvoeren en waarvoor de
            genoemde meetbron beschikbaar is.
          </Text>
          <View accessibilityRole="radiogroup" style={styles.chips}>
            {fieldTests.map((protocol) => (
              <Chip
                key={protocol.protocol_id}
                label={protocolLabels[protocol.protocol_id] ?? protocol.protocol_id}
                onPress={() => {
                  setSelectedProtocolId(protocol.protocol_id);
                  setGuidanceMode(protocol.guidance_modes[0]);
                }}
                selected={selectedProtocolId === protocol.protocol_id}
              />
            ))}
          </View>
          {selectedProtocol ? (
            <View accessibilityRole="radiogroup" style={styles.chips}>
              {selectedProtocol.guidance_modes.map((mode) => (
                <Chip
                  key={mode}
                  label={guidanceLabels[mode]}
                  onPress={() => setGuidanceMode(mode)}
                  selected={guidanceMode === mode}
                />
              ))}
            </View>
          ) : null}
          {discipline === 'swim' ? (
            <View accessibilityRole="radiogroup" style={styles.chips}>
              <Chip
                label="25 m-bad"
                onPress={() => setPoolLength(25)}
                selected={poolLength === 25}
              />
              <Chip
                label="50 m-bad"
                onPress={() => setPoolLength(50)}
                selected={poolLength === 50}
              />
            </View>
          ) : null}
          <Text style={styles.safetyText}>
            Een geldige test berekent een drempel en Zone 1-5-kandidaten. Je
            bevestigt eerst de drempel en daarna het zoneprofiel; niets wordt
            automatisch actief.
          </Text>
          <SaveButton
            disabled={!selectedProtocol}
            label="Veldtest kiezen"
            onPress={submitFieldTest}
            saving={saving}
          />
        </View>
      ) : null}

      {route === 'calibration_week' ? (
        <View style={styles.panel}>
          <StatusPill label="Submaximaal" tone="brand" />
          <Text style={styles.panelText}>
            Deze rustige kalibratie bewaart observaties uit hetzelfde blok. Ze
            maakt nooit zelfstandig CSS, FTP, LTHR of drempeltempo.
          </Text>
          <View accessibilityRole="radiogroup" style={styles.chips}>
            {calibrationProtocol?.guidance_modes.map((mode) => (
              <Chip
                key={mode}
                label={guidanceLabels[mode]}
                onPress={() => setGuidanceMode(mode)}
                selected={guidanceMode === mode}
              />
            ))}
          </View>
          {discipline === 'swim' ? (
            <View accessibilityRole="radiogroup" style={styles.chips}>
              <Chip
                label="25 m-bad"
                onPress={() => setPoolLength(25)}
                selected={poolLength === 25}
              />
              <Chip
                label="50 m-bad"
                onPress={() => setPoolLength(50)}
                selected={poolLength === 50}
              />
            </View>
          ) : null}
          <SaveButton
            disabled={!calibrationProtocol}
            label="Week-1-kalibratie kiezen"
            onPress={submitCalibration}
            saving={saving}
          />
        </View>
      ) : null}

      {route === 'rpe_only' ? (
        <View style={styles.panel}>
          <StatusPill label="Zonder zones" tone="neutral" />
          <Text style={styles.panelText}>
            RPE-only is een geldige configuratie en maakt geen verzonnen
            drempel of zoneprofiel. RPE 1 is minimaal en RPE 10 maximaal.
          </Text>
          <SaveButton
            disabled={false}
            label="RPE-only bevestigen"
            onPress={() =>
              void onSave(discipline, {
                setup_route: 'rpe_only',
                guidance_mode: 'rpe_only',
              })
            }
            saving={saving}
          />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  step: { gap: spacing.xl },
  eyebrow: {
    color: colors.brand,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -0.7,
    marginTop: spacing.xs,
  },
  description: {
    color: colors.inkMuted,
    fontSize: 15,
    lineHeight: 23,
    marginTop: spacing.sm,
  },
  progressRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  routeList: { gap: spacing.sm },
  routeCard: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  routeCardSelected: { borderColor: colors.brand, borderWidth: 2 },
  routeHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
    justifyContent: 'space-between',
  },
  routeTitle: { color: colors.ink, flex: 1, fontSize: 16, fontWeight: '900' },
  routeDescription: { color: colors.inkMuted, lineHeight: 20 },
  radio: {
    borderColor: colors.inkFaint,
    borderRadius: 8,
    borderWidth: 2,
    height: 16,
    width: 16,
  },
  radioSelected: { backgroundColor: colors.brand, borderColor: colors.brand },
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  panelTitle: { color: colors.ink, fontSize: 18, fontWeight: '900' },
  panelText: { color: colors.inkMuted, lineHeight: 21 },
  safetyText: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    color: colors.ink,
    fontWeight: '700',
    lineHeight: 20,
    padding: spacing.md,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  chipSelected: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  chipText: { color: colors.inkMuted, fontSize: 13, fontWeight: '800' },
  chipTextSelected: { color: colors.brand },
  checkboxRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  checkbox: {
    borderColor: colors.inkFaint,
    borderRadius: 4,
    borderWidth: 2,
    height: 20,
    width: 20,
  },
  checkboxSelected: { backgroundColor: colors.brand, borderColor: colors.brand },
  checkboxText: { color: colors.ink, flex: 1, fontWeight: '800' },
  boundaryPanel: { gap: spacing.md },
  boundaryRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  zoneLabel: { color: colors.brand, fontWeight: '900', width: 26 },
  boundaryInput: { flex: 1 },
  unit: { color: colors.inkMuted, fontSize: 13, fontWeight: '800' },
  error: { color: colors.danger, fontWeight: '700', lineHeight: 20 },
  saveButton: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    justifyContent: 'center',
    minHeight: 50,
    paddingHorizontal: spacing.lg,
  },
  saveButtonText: { color: colors.white, fontSize: 15, fontWeight: '900' },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.78 },
});
