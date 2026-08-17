import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  createActivity,
  evaluateCalibration,
  getCalibrationStatus,
  listCalibrationProtocols,
  saveCalibrationObservation,
  submitActivityRpe,
} from '../api/client';
import type {
  CalibrationEvaluation,
  CalibrationObservationInput,
  CalibrationProtocol,
  CalibrationProtocolSegment,
  Discipline,
  DisciplineSetup,
  GuidanceMode,
  SwimRepetition,
  ZoneMetricKind,
} from '../api/types';
import { FormField } from '../components/FormField';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

type Props = {
  accessToken: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
};

type Stage = 'protocol' | 'feedback' | 'result';

type SegmentDraft = {
  included: boolean;
  completed: boolean;
  interrupted: boolean;
  blockRpe: string;
  averageHeartRate: string;
  endingHeartRate: string;
  last20HeartRate: string;
  averagePower: string;
  last20Power: string;
  averagePace: string;
  elapsedTime: string;
  completenessPercent: string;
  steadyExecution: 'yes' | 'mostly' | 'no';
  stableSegment: boolean;
  calibratedPowerSource: boolean;
  repetitionTimes: string;
  repetitionRests: string;
};

const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Hardlopen',
};

const protocolLabels: Record<string, string> = {
  start23_run_threshold_30min_v1: '30 min loopdrempeltest',
  start23_bike_ftp_30min_v1: '30 min FTP-test',
  start23_bike_fthr_20min_v1: '20 min fietsdrempelhartslagtest',
  start23_swim_css_400_200_v1: 'CSS 400/200 m-test',
  start23_week1_run_calibration_v1: 'Week-1-loopkalibratie',
  start23_week1_bike_calibration_v1: 'Week-1-fietskalibratie',
  start23_week1_swim_calibration_v1: 'Week-1-zwemkalibratie',
};

const purposeLabels: Record<string, string> = {
  prepare: 'Opwarming/voorbereiding',
  valid_test_segment: 'Geldig testblok',
  recovery: 'Herstel/cooling-down',
  recovery_between_tests: 'Actief herstel',
  calibration_observation: 'Kalibratieblok',
  optional_calibration_observation: 'Optioneel kalibratieblok',
};

const guidanceLabels: Record<GuidanceMode, string> = {
  power: 'vermogen',
  heart_rate: 'hartslag',
  combined: 'hartslag en vermogen/tempo',
  pace: 'tempo',
  rpe_only: 'alleen RPE',
};

const metricLabels: Record<ZoneMetricKind, string> = {
  swim_css_seconds_per_100m: 'CSS (sec/100 m)',
  bike_ftp_watts: 'FTP (watt)',
  bike_threshold_heart_rate_bpm: 'Fietsdrempelhartslag (bpm)',
  run_threshold_pace_seconds_per_km: 'Loopdrempeltempo (sec/km)',
  run_lthr_bpm: 'Loop-LTHR (bpm)',
};

const resultLabels: Record<CalibrationEvaluation['status'], string> = {
  insufficient_data: 'Meer of betere gegevens nodig',
  insufficient_protocol: 'Protocolregel ontbreekt',
  rpe_only: 'Veilig als RPE-only opgeslagen',
  provisionally_calibrated: 'Voorlopig gekalibreerd',
  threshold_estimated: 'Drempel geschat',
};

const reasonLabels: Record<string, string> = {
  zone_model_not_approved:
    'Een compleet beoordeeld Zone 1-5-model ontbreekt; er zijn geen zones aangemaakt.',
  threshold_not_permitted_from_submaximal_calibration:
    'Een submaximale kalibratie mag geen drempel produceren.',
  sensor_data_missing:
    'Er waren geen bruikbare sensorgegevens; de RPE-observatie blijft wel bewaard.',
  missing_session_rpe: 'De sessie-RPE ontbreekt.',
  missing_block_rpe: 'Een verplichte blok-RPE ontbreekt.',
  sensor_quality_insufficient: 'De meetkwaliteit was onvoldoende.',
  required_segment_missing: 'Een verplicht protocolblok ontbreekt.',
  test_segment_incomplete: 'Een verplicht blok is niet voltooid.',
  interrupted: 'Een verplicht blok is onderbroken.',
  pace_rounding_rule_not_approved:
    'Het resultaat vraagt een nog niet goedgekeurde afrondingsregel.',
};

function newIdempotencyKey(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (value) => {
    const random = Math.floor(Math.random() * 16);
    const digit = value === 'x' ? random : (random & 0x3) | 0x8;
    return digit.toString(16);
  });
}

function initialDraft(segment: CalibrationProtocolSegment): SegmentDraft {
  return {
    included: !segment.optional,
    completed: true,
    interrupted: false,
    blockRpe: '',
    averageHeartRate: '',
    endingHeartRate: '',
    last20HeartRate: '',
    averagePower: '',
    last20Power: '',
    averagePace: '',
    elapsedTime: '',
    completenessPercent: '100',
    steadyExecution: 'yes',
    stableSegment: false,
    calibratedPowerSource: false,
    repetitionTimes: '',
    repetitionRests: '0, 0, 0, 0',
  };
}

function protocolDurationMinutes(protocol: CalibrationProtocol): string {
  if (protocol.segments.some((segment) => segment.duration_seconds === null)) {
    return '';
  }
  const seconds = protocol.segments.reduce(
    (total, segment) => total + (segment.duration_seconds ?? 0),
    0,
  );
  return seconds > 0 ? String(seconds / 60) : '';
}

function protocolDistance(protocol: CalibrationProtocol): number | undefined {
  const meters = protocol.segments.reduce(
    (total, segment) => total + (segment.distance_meters ?? 0),
    0,
  );
  return meters > 0 ? meters : undefined;
}

function parseRpe(value: string, label: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 10) {
    throw new Error(`${label} moet een heel getal van 1 tot en met 10 zijn.`);
  }
  return parsed;
}

function parsePositive(value: string, label: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${label} moet positief zijn.`);
  }
  return String(parsed);
}

function parseCompleteness(value: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
    throw new Error('Meetdekking moet tussen 0 en 100 procent liggen.');
  }
  return String(parsed / 100);
}

function parseCsvNumbers(
  value: string,
  label: string,
  allowZero: boolean,
): number[] {
  const parts = value.split(',');
  const values = parts.map((part) => Number(part.trim()));
  if (
    parts.length !== 4 ||
    values.some(
      (part) => !Number.isFinite(part) || (allowZero ? part < 0 : part <= 0),
    )
  ) {
    throw new Error(`${label} vereist precies vier komma-gescheiden waarden.`);
  }
  return values;
}

function Toggle({
  checked,
  label,
  onPress,
}: {
  checked: boolean;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
      onPress={onPress}
      style={styles.toggleRow}
    >
      <View style={[styles.toggleBox, checked && styles.toggleBoxChecked]} />
      <Text style={styles.toggleLabel}>{label}</Text>
    </Pressable>
  );
}

function ActionButton({
  label,
  onPress,
  disabled = false,
  secondary = false,
  loading = false,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  secondary?: boolean;
  loading?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.action,
        secondary && styles.actionSecondary,
        (disabled || loading) && styles.disabled,
        pressed && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={secondary ? colors.brand : colors.white} />
      ) : (
        <Text
          style={[
            styles.actionText,
            secondary && styles.actionTextSecondary,
          ]}
        >
          {label}
        </Text>
      )}
    </Pressable>
  );
}

function isMainSegment(segment: CalibrationProtocolSegment): boolean {
  return segment.purpose.includes('observation') ||
    segment.purpose === 'valid_test_segment';
}

function needsSwimConditions(protocol: CalibrationProtocol): boolean {
  return protocol.discipline === 'swim';
}

function objectiveMetricsPresent(draft: SegmentDraft): boolean {
  return [
    draft.averageHeartRate,
    draft.endingHeartRate,
    draft.last20HeartRate,
    draft.averagePower,
    draft.last20Power,
    draft.averagePace,
    draft.elapsedTime,
    draft.repetitionTimes,
  ].some((value) => value.trim() !== '');
}

export function CalibrationScreen({ accessToken, onBack, onSignOut }: Props) {
  const [setups, setSetups] = useState<DisciplineSetup[]>([]);
  const [protocols, setProtocols] = useState<Record<string, CalibrationProtocol>>(
    {},
  );
  const [evaluations, setEvaluations] = useState<CalibrationEvaluation[]>([]);
  const [selectedProtocolId, setSelectedProtocolId] = useState<string | null>(
    null,
  );
  const [stage, setStage] = useState<Stage>('protocol');
  const [drafts, setDrafts] = useState<Record<string, SegmentDraft>>({});
  const [performedAt, setPerformedAt] = useState(new Date().toISOString());
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  );
  const [durationMinutes, setDurationMinutes] = useState('');
  const [sessionRpe, setSessionRpe] = useState('');
  const [swimConditionsConfirmed, setSwimConditionsConfirmed] = useState(false);
  const [activityId, setActivityId] = useState<string | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [result, setResult] = useState<CalibrationEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const status = await getCalibrationStatus(accessToken);
    const protocolSetups = status.setups.filter((setup) => setup.protocol_id);
    const disciplineProtocols = await Promise.all(
      [...new Set(protocolSetups.map((setup) => setup.discipline))].map(
        async (discipline) => listCalibrationProtocols(accessToken, discipline),
      ),
    );
    const protocolMap: Record<string, CalibrationProtocol> = {};
    for (const protocol of disciplineProtocols.flat()) {
      protocolMap[protocol.protocol_id] = protocol;
    }
    setSetups(protocolSetups);
    setProtocols(protocolMap);
    setEvaluations(status.evaluations);
    setSelectedProtocolId((current) => {
      if (current && protocolMap[current]) return current;
      return protocolSetups[0]?.protocol_id ?? null;
    });
  }, [accessToken]);

  useEffect(() => {
    let mounted = true;
    load()
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error
              ? caught.message
              : 'De kalibratiestatus kon niet worden geladen.',
          );
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [load]);

  const selectedProtocol = selectedProtocolId
    ? protocols[selectedProtocolId]
    : undefined;
  const selectedSetup = setups.find(
    (setup) => setup.protocol_id === selectedProtocolId,
  );

  useEffect(() => {
    if (!selectedProtocol) return;
    setDrafts(
      Object.fromEntries(
        selectedProtocol.segments.map((segment) => [
          segment.segment_id,
          initialDraft(segment),
        ]),
      ),
    );
    setDurationMinutes(protocolDurationMinutes(selectedProtocol));
    setSessionRpe('');
    setSwimConditionsConfirmed(false);
    setActivityId(null);
    setIdempotencyKey(newIdempotencyKey());
    setResult(null);
    setStage('protocol');
  }, [selectedProtocolId]);

  const updateDraft = (
    segmentId: string,
    update: Partial<SegmentDraft>,
  ) => {
    setDrafts((current) => ({
      ...current,
      [segmentId]: { ...current[segmentId], ...update },
    }));
  };

  const priorResults = useMemo(
    () =>
      evaluations
        .filter((evaluation) => evaluation.protocol_id === selectedProtocolId)
        .sort((left, right) => right.created_at.localeCompare(left.created_at)),
    [evaluations, selectedProtocolId],
  );

  const validateFeedback = (
    protocol: CalibrationProtocol,
    setup: DisciplineSetup,
  ) => {
    if (Number.isNaN(new Date(performedAt).getTime())) {
      throw new Error('Gebruik een geldig ISO-tijdstip inclusief tijdzone.');
    }
    if (!timezone.trim()) throw new Error('Vul een IANA-tijdzone in.');
    parsePositive(durationMinutes, 'Totale duur');
    parseRpe(sessionRpe, 'Sessie-RPE');
    if (needsSwimConditions(protocol) && !swimConditionsConfirmed) {
      throw new Error(
        'Bevestig badlengte, vrije slag en trainen zonder hulpmiddelen.',
      );
    }
    for (const segment of protocol.segments) {
      const draft = drafts[segment.segment_id];
      if (!draft || !draft.included) continue;
      if (isMainSegment(segment)) {
        parseRpe(draft.blockRpe, `Blok-RPE voor ${segment.segment_id}`);
      }
      if (!draft.completed) continue;
      if (
        protocol.protocol_id === 'start23_run_threshold_30min_v1' &&
        segment.segment_id === 'test_30min'
      ) {
        parsePositive(draft.averagePace, 'Gemiddeld drempeltempo');
        parseCompleteness(draft.completenessPercent);
        if (!draft.stableSegment) {
          throw new Error('Bevestig dat het looptestblok stabiel is uitgevoerd.');
        }
      }
      if (
        protocol.protocol_id === 'start23_bike_ftp_30min_v1' &&
        segment.segment_id === 'test_30min'
      ) {
        parsePositive(draft.last20Power, 'Vermogen over de laatste 20 minuten');
        parseCompleteness(draft.completenessPercent);
        if (!draft.stableSegment || !draft.calibratedPowerSource) {
          throw new Error(
            'Bevestig een stabiel testblok en een gekalibreerde vermogensbron.',
          );
        }
      }
      if (
        protocol.protocol_id === 'start23_bike_fthr_20min_v1' &&
        segment.segment_id === 'test_20min'
      ) {
        parsePositive(draft.averageHeartRate, 'Gemiddelde hartslag');
        parseCompleteness(draft.completenessPercent);
      }
      if (
        protocol.protocol_id === 'start23_swim_css_400_200_v1' &&
        ['tt_400m', 'tt_200m'].includes(segment.segment_id)
      ) {
        parsePositive(draft.elapsedTime, 'Zwemtesttijd');
      }
      if (protocol.protocol_type === 'submaximal_calibration') {
        if (protocol.discipline === 'swim') {
          parseCsvNumbers(draft.repetitionTimes, 'Herhalingstijden', false);
          parseCsvNumbers(draft.repetitionRests, 'Rusttijden', true);
        } else {
          if (setup.guidance_mode === 'rpe_only') continue;
          const needsHeartRate = ['heart_rate', 'combined'].includes(
            setup.guidance_mode,
          );
          const needsPace = setup.guidance_mode === 'pace';
          const needsPower = ['power', 'combined'].includes(setup.guidance_mode);
          if (needsHeartRate) {
            parsePositive(draft.averageHeartRate, 'Gemiddelde hartslag');
          }
          if (needsPace) {
            parsePositive(draft.averagePace, 'Gemiddeld tempo');
          }
          if (needsPower) {
            parsePositive(draft.averagePower, 'Gemiddeld vermogen');
          }
        }
      }
    }
  };

  const buildObservation = (
    protocol: CalibrationProtocol,
    setup: DisciplineSetup,
    segment: CalibrationProtocolSegment,
    draft: SegmentDraft,
    savedActivityId: string,
  ): CalibrationObservationInput => {
    const hasMetrics = objectiveMetricsPresent(draft);
    const input: CalibrationObservationInput = {
      activity_id: savedActivityId,
      protocol_id: protocol.protocol_id,
      discipline: protocol.discipline,
      segment_id: segment.segment_id,
      performed_at: new Date(performedAt).toISOString(),
      completed: draft.completed,
      interrupted: draft.interrupted,
      quality_status: hasMetrics ? 'sufficient' : 'missing',
      target_rpe: segment.target_rpe_max,
      ...(segment.duration_seconds === null
        ? {}
        : { duration_seconds: segment.duration_seconds }),
      ...(segment.distance_meters === null
        ? {}
        : { distance_meters: segment.distance_meters }),
    };
    if (isMainSegment(segment)) {
      input.reported_block_rpe = parseRpe(
        draft.blockRpe,
        `Blok-RPE voor ${segment.segment_id}`,
      );
      input.steady_execution = draft.steadyExecution;
    }
    if (segment.segment_id === 'cooldown') {
      input.reported_session_rpe = parseRpe(sessionRpe, 'Sessie-RPE');
    }
    if (draft.averageHeartRate) {
      input.average_heart_rate_bpm = parsePositive(
        draft.averageHeartRate,
        'Gemiddelde hartslag',
      );
    }
    if (draft.endingHeartRate) {
      input.ending_heart_rate_bpm = parsePositive(
        draft.endingHeartRate,
        'Eindhartslag',
      );
    }
    if (draft.last20HeartRate) {
      input.average_heart_rate_last_20min_bpm = parsePositive(
        draft.last20HeartRate,
        'Hartslag over de laatste 20 minuten',
      );
    }
    if (draft.averagePower) {
      input.average_power_watts = parsePositive(
        draft.averagePower,
        'Gemiddeld vermogen',
      );
    }
    if (draft.last20Power) {
      input.average_power_last_20min_watts = parsePositive(
        draft.last20Power,
        'Vermogen over de laatste 20 minuten',
      );
    }
    if (draft.averagePace) {
      input.average_pace_seconds_per_km = parsePositive(
        draft.averagePace,
        'Gemiddeld tempo',
      );
    }
    if (draft.elapsedTime) {
      input.elapsed_time_seconds = parsePositive(
        draft.elapsedTime,
        'Verstreken tijd',
      );
    }
    if (hasMetrics && draft.completenessPercent) {
      input.data_completeness = parseCompleteness(draft.completenessPercent);
    }
    if (draft.stableSegment) input.stable_segment = true;
    if (draft.calibratedPowerSource) input.power_source_calibrated = true;
    if (protocol.discipline === 'swim') {
      input.pool_length_meters = setup.pool_length_meters ?? 25;
      input.stroke = 'freestyle';
      input.equipment = 'none';
      if (
        protocol.protocol_type === 'submaximal_calibration' &&
        isMainSegment(segment)
      ) {
        const times = parseCsvNumbers(
          draft.repetitionTimes,
          'Herhalingstijden',
          false,
        );
        const rests = parseCsvNumbers(
          draft.repetitionRests,
          'Rusttijden',
          true,
        );
        const repetitionDistance = segment.segment_id.startsWith('4x200')
          ? 200
          : 100;
        input.repetitions = times.map<SwimRepetition>((time, index) => ({
          distance_meters: repetitionDistance,
          elapsed_time_seconds: String(time),
          rest_time_seconds: Math.round(rests[index]),
          completed: true,
        }));
      }
    }
    return input;
  };

  const submit = async () => {
    if (!selectedProtocol || !selectedSetup) return;
    setBusy(true);
    setError(null);
    try {
      validateFeedback(selectedProtocol, selectedSetup);
      let savedActivityId = activityId;
      if (!savedActivityId) {
        const activity = await createActivity(accessToken, idempotencyKey, {
          discipline: selectedProtocol.discipline,
          started_at: new Date(performedAt).toISOString(),
          timezone: timezone.trim(),
          duration_minutes: parsePositive(durationMinutes, 'Totale duur'),
          ...(protocolDistance(selectedProtocol) === undefined
            ? {}
            : { distance_meters: protocolDistance(selectedProtocol) }),
        });
        savedActivityId = activity.id;
        setActivityId(savedActivityId);
      }
      await submitActivityRpe(
        accessToken,
        savedActivityId,
        parseRpe(sessionRpe, 'Sessie-RPE'),
      );
      for (const segment of selectedProtocol.segments) {
        const draft = drafts[segment.segment_id];
        if (!draft?.included) continue;
        await saveCalibrationObservation(
          accessToken,
          buildObservation(
            selectedProtocol,
            selectedSetup,
            segment,
            draft,
            savedActivityId,
          ),
        );
      }
      const evaluation = await evaluateCalibration(
        accessToken,
        savedActivityId,
        selectedProtocol.protocol_id,
      );
      setResult(evaluation);
      setStage('result');
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De protocolfeedback kon niet worden verwerkt.',
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={colors.brand} size="large" />
        <Text style={styles.muted}>Protocolstatus laden…</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboard}
      >
        <View style={styles.header}>
          <Pressable accessibilityRole="button" onPress={onBack} style={styles.link}>
            <Text style={styles.linkText}>← Terug</Text>
          </Pressable>
          <View style={styles.headerTitleBlock}>
            <Text style={styles.logo}>Start23</Text>
            <Text style={styles.headerTitle}>Test & kalibratie</Text>
          </View>
          <Pressable
            accessibilityRole="button"
            onPress={() => void onSignOut()}
            style={styles.link}
          >
            <Text style={styles.linkText}>Afmelden</Text>
          </Pressable>
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {error ? <Text style={styles.errorBanner}>{error}</Text> : null}

          {setups.length === 0 ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Geen protocol gekozen</Text>
              <Text style={styles.muted}>
                Kies tijdens de intake eerst een veldtest of Week-1-kalibratie.
                RPE-only en bekende waarden hebben geen protocoluitvoering.
              </Text>
              <ActionButton label="Terug naar intake" onPress={onBack} />
            </View>
          ) : (
            <>
              <View style={styles.selectorRow}>
                {setups.map((setup) => (
                  <Pressable
                    accessibilityRole="radio"
                    accessibilityState={{
                      checked: selectedProtocolId === setup.protocol_id,
                    }}
                    key={`${setup.discipline}:${setup.protocol_id}`}
                    onPress={() => setSelectedProtocolId(setup.protocol_id)}
                    style={({ pressed }) => [
                      styles.selector,
                      selectedProtocolId === setup.protocol_id &&
                        styles.selectorSelected,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={styles.selectorText}>
                      {disciplineLabels[setup.discipline]}
                    </Text>
                  </Pressable>
                ))}
              </View>

              {selectedProtocol && selectedSetup && stage === 'protocol' ? (
                <View style={styles.card}>
                  <View style={styles.badges}>
                    <StatusPill
                      label={
                        selectedProtocol.protocol_type === 'field_test'
                          ? 'Veldtest'
                          : 'Submaximaal'
                      }
                      tone={
                        selectedProtocol.protocol_type === 'field_test'
                          ? 'accent'
                          : 'brand'
                      }
                    />
                    <StatusPill label="Beoordeeld v1" tone="neutral" />
                  </View>
                  <Text style={styles.pageTitle}>
                    {protocolLabels[selectedProtocol.protocol_id] ??
                      selectedProtocol.protocol_id}
                  </Text>
                  <Text style={styles.muted}>
                    Uitvoering op {guidanceLabels[selectedSetup.guidance_mode]}.
                    Gebruik per blok de canonieke RPE-schaal 1–10.
                  </Text>
                  <View style={styles.segmentList}>
                    {selectedProtocol.segments.map((segment) => (
                      <View key={segment.segment_id} style={styles.segmentSummary}>
                        <View style={styles.segmentNumber}>
                          <Text style={styles.segmentNumberText}>{segment.order}</Text>
                        </View>
                        <View style={styles.segmentBody}>
                          <Text style={styles.segmentTitle}>
                            {purposeLabels[segment.purpose] ?? segment.purpose}
                            {segment.optional ? ' · optioneel' : ''}
                          </Text>
                          <Text style={styles.muted}>
                            {segment.duration_seconds
                              ? `${segment.duration_seconds / 60} min`
                              : `${segment.distance_meters} m`}{' '}
                            · doel-RPE {segment.target_rpe_min}–
                            {segment.target_rpe_max}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                  <Text style={styles.safety}>
                    Stop bij pijn, alarmsymptomen of een onveilige situatie. Een
                    veldtestresultaat wordt nooit automatisch een actief
                    zoneprofiel.
                  </Text>
                  <ActionButton
                    label="Training uitgevoerd · feedback invullen"
                    onPress={() => setStage('feedback')}
                  />
                  {priorResults.length > 0 ? (
                    <Text style={styles.historyText}>
                      {priorResults.length} eerdere evaluatie
                      {priorResults.length === 1 ? '' : 's'} voor dit protocol.
                    </Text>
                  ) : null}
                </View>
              ) : null}

              {selectedProtocol && selectedSetup && stage === 'feedback' ? (
                <View style={styles.card}>
                  <Text style={styles.eyebrow}>Feedback</Text>
                  <Text style={styles.pageTitle}>Objectief + jouw RPE</Text>
                  <Text style={styles.muted}>
                    Ontbrekende sensordata blokkeert de activiteit niet. Laat
                    velden leeg als je ze niet betrouwbaar hebt.
                  </Text>
                  <FormField
                    autoCapitalize="none"
                    label="Starttijd (ISO inclusief tijdzone)"
                    onChangeText={setPerformedAt}
                    placeholder="2026-08-15T09:00:00+02:00"
                    value={performedAt}
                  />
                  <FormField
                    autoCapitalize="none"
                    label="IANA-tijdzone"
                    onChangeText={setTimezone}
                    placeholder="Europe/Amsterdam"
                    value={timezone}
                  />
                  <View style={styles.twoColumns}>
                    <View style={styles.column}>
                      <FormField
                        inputMode="decimal"
                        label="Totale duur"
                        onChangeText={setDurationMinutes}
                        placeholder="minuten"
                        value={durationMinutes}
                      />
                    </View>
                    <View style={styles.column}>
                      <FormField
                        inputMode="numeric"
                        label="Sessie-RPE"
                        onChangeText={setSessionRpe}
                        placeholder="1–10"
                        value={sessionRpe}
                      />
                    </View>
                  </View>

                  {needsSwimConditions(selectedProtocol) ? (
                    <Toggle
                      checked={swimConditionsConfirmed}
                      label={`${selectedSetup.pool_length_meters} m-bad, vrije slag en zonder paddles/vliezen/pull buoy`}
                      onPress={() =>
                        setSwimConditionsConfirmed((current) => !current)
                      }
                    />
                  ) : null}

                  {selectedProtocol.segments.map((segment) => {
                    const draft = drafts[segment.segment_id];
                    if (!draft) return null;
                    const main = isMainSegment(segment);
                    const runTest =
                      selectedProtocol.protocol_id ===
                        'start23_run_threshold_30min_v1' &&
                      segment.segment_id === 'test_30min';
                    const bikeFtp =
                      selectedProtocol.protocol_id ===
                        'start23_bike_ftp_30min_v1' &&
                      segment.segment_id === 'test_30min';
                    const bikeHr =
                      selectedProtocol.protocol_id ===
                        'start23_bike_fthr_20min_v1' &&
                      segment.segment_id === 'test_20min';
                    const swimTest =
                      selectedProtocol.protocol_id ===
                        'start23_swim_css_400_200_v1' &&
                      ['tt_400m', 'tt_200m'].includes(segment.segment_id);
                    const calibrationMain =
                      selectedProtocol.protocol_type ===
                        'submaximal_calibration' && main;
                    return (
                      <View key={segment.segment_id} style={styles.segmentCard}>
                        <Text style={styles.segmentTitle}>
                          {segment.order}.{' '}
                          {purposeLabels[segment.purpose] ?? segment.purpose}
                        </Text>
                        <Text style={styles.muted}>
                          Doel-RPE {segment.target_rpe_min}–
                          {segment.target_rpe_max}
                        </Text>
                        {segment.optional ? (
                          <Toggle
                            checked={draft.included}
                            label="Optioneel blok uitgevoerd"
                            onPress={() =>
                              updateDraft(segment.segment_id, {
                                included: !draft.included,
                              })
                            }
                          />
                        ) : null}
                        {draft.included ? (
                          <>
                            <View style={styles.twoColumns}>
                              <View style={styles.column}>
                                <Toggle
                                  checked={draft.completed}
                                  label="Voltooid"
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      completed: !draft.completed,
                                    })
                                  }
                                />
                              </View>
                              <View style={styles.column}>
                                <Toggle
                                  checked={draft.interrupted}
                                  label="Onderbroken"
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      interrupted: !draft.interrupted,
                                    })
                                  }
                                />
                              </View>
                            </View>
                            {main ? (
                              <FormField
                                inputMode="numeric"
                                label="Werkelijke blok-RPE"
                                onChangeText={(value) =>
                                  updateDraft(segment.segment_id, {
                                    blockRpe: value,
                                  })
                                }
                                placeholder="1–10"
                                value={draft.blockRpe}
                              />
                            ) : null}
                            {runTest ? (
                              <>
                                <FormField
                                  inputMode="decimal"
                                  label="Gemiddeld tempo testblok"
                                  onChangeText={(value) =>
                                    updateDraft(segment.segment_id, {
                                      averagePace: value,
                                    })
                                  }
                                  placeholder="hele sec/km"
                                  value={draft.averagePace}
                                />
                                <FormField
                                  inputMode="decimal"
                                  label="Gem. HR laatste 20 min (optioneel)"
                                  onChangeText={(value) =>
                                    updateDraft(segment.segment_id, {
                                      last20HeartRate: value,
                                    })
                                  }
                                  placeholder="bpm"
                                  value={draft.last20HeartRate}
                                />
                                <Toggle
                                  checked={draft.stableSegment}
                                  label="Tempo was stabiel"
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      stableSegment: !draft.stableSegment,
                                    })
                                  }
                                />
                              </>
                            ) : null}
                            {bikeFtp ? (
                              <>
                                <FormField
                                  inputMode="decimal"
                                  label="Gem. vermogen laatste 20 min"
                                  onChangeText={(value) =>
                                    updateDraft(segment.segment_id, {
                                      last20Power: value,
                                    })
                                  }
                                  placeholder="watt"
                                  value={draft.last20Power}
                                />
                                <Toggle
                                  checked={draft.calibratedPowerSource}
                                  label="Vermogensbron was gekalibreerd"
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      calibratedPowerSource:
                                        !draft.calibratedPowerSource,
                                    })
                                  }
                                />
                                <Toggle
                                  checked={draft.stableSegment}
                                  label="Vermogen was stabiel"
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      stableSegment: !draft.stableSegment,
                                    })
                                  }
                                />
                              </>
                            ) : null}
                            {bikeHr ? (
                              <FormField
                                inputMode="decimal"
                                label="Gemiddelde hartslag testblok"
                                onChangeText={(value) =>
                                  updateDraft(segment.segment_id, {
                                    averageHeartRate: value,
                                  })
                                }
                                placeholder="bpm"
                                value={draft.averageHeartRate}
                              />
                            ) : null}
                            {swimTest ? (
                              <FormField
                                inputMode="decimal"
                                label={`Tijd ${segment.distance_meters} m`}
                                onChangeText={(value) =>
                                  updateDraft(segment.segment_id, {
                                    elapsedTime: value,
                                  })
                                }
                                placeholder="seconden"
                                value={draft.elapsedTime}
                              />
                            ) : null}
                            {(runTest || bikeFtp || bikeHr) ? (
                              <FormField
                                inputMode="decimal"
                                label="Meetdekking"
                                onChangeText={(value) =>
                                  updateDraft(segment.segment_id, {
                                    completenessPercent: value,
                                  })
                                }
                                placeholder="95–100"
                                suffix={<Text style={styles.unit}>%</Text>}
                                value={draft.completenessPercent}
                              />
                            ) : null}
                            {calibrationMain &&
                            (selectedSetup.guidance_mode !== 'rpe_only' ||
                              selectedProtocol.discipline === 'swim') ? (
                              <>
                                {selectedProtocol.discipline === 'swim' ? (
                                  <>
                                    <FormField
                                      inputMode="decimal"
                                      label="Vier herhalingstijden"
                                      onChangeText={(value) =>
                                        updateDraft(segment.segment_id, {
                                          repetitionTimes: value,
                                        })
                                      }
                                      placeholder="bijv. 210, 212, 211, 213"
                                      value={draft.repetitionTimes}
                                    />
                                    <FormField
                                      inputMode="decimal"
                                      label="Vier rusttijden"
                                      onChangeText={(value) =>
                                        updateDraft(segment.segment_id, {
                                          repetitionRests: value,
                                        })
                                      }
                                      placeholder="seconden, komma-gescheiden"
                                      value={draft.repetitionRests}
                                    />
                                  </>
                                ) : (
                                  <>
                                    {['heart_rate', 'combined'].includes(
                                      selectedSetup.guidance_mode,
                                    ) ? (
                                      <FormField
                                        inputMode="decimal"
                                        label="Gemiddelde hartslag"
                                        onChangeText={(value) =>
                                          updateDraft(segment.segment_id, {
                                            averageHeartRate: value,
                                          })
                                        }
                                        placeholder="bpm"
                                        value={draft.averageHeartRate}
                                      />
                                    ) : null}
                                    {selectedSetup.guidance_mode === 'pace' ? (
                                      <FormField
                                        inputMode="decimal"
                                        label="Gemiddeld tempo"
                                        onChangeText={(value) =>
                                          updateDraft(segment.segment_id, {
                                            averagePace: value,
                                          })
                                        }
                                        placeholder="sec/km"
                                        value={draft.averagePace}
                                      />
                                    ) : null}
                                    {['power', 'combined'].includes(
                                      selectedSetup.guidance_mode,
                                    ) ? (
                                      <FormField
                                        inputMode="decimal"
                                        label="Gemiddeld vermogen"
                                        onChangeText={(value) =>
                                          updateDraft(segment.segment_id, {
                                            averagePower: value,
                                          })
                                        }
                                        placeholder="watt"
                                        value={draft.averagePower}
                                      />
                                    ) : null}
                                  </>
                                )}
                              </>
                            ) : null}
                          </>
                        ) : null}
                      </View>
                    );
                  })}

                  {activityId ? (
                    <Text style={styles.safety}>
                      De activiteit is al opgeslagen. Een retry gebruikt exact
                      dezelfde activiteit en immutable segmentidentiteiten.
                    </Text>
                  ) : null}
                  <ActionButton
                    label="Opslaan en deterministisch evalueren"
                    loading={busy}
                    onPress={() => void submit()}
                  />
                  <ActionButton
                    disabled={busy || activityId !== null}
                    label="Terug naar protocol"
                    onPress={() => setStage('protocol')}
                    secondary
                  />
                </View>
              ) : null}

              {stage === 'result' && result ? (
                <View style={styles.card}>
                  <Text style={styles.eyebrow}>Resultaat</Text>
                  <Text style={styles.pageTitle}>{resultLabels[result.status]}</Text>
                  <View style={styles.badges}>
                    <StatusPill label={`Vertrouwen: ${result.confidence}`} tone="neutral" />
                    <StatusPill label={`Zones: ${result.zone_status}`} tone="accent" />
                  </View>
                  {result.thresholds.map((threshold) => (
                    <View key={threshold.metric_kind} style={styles.resultMetric}>
                      <Text style={styles.resultMetricLabel}>
                        {metricLabels[threshold.metric_kind]}
                      </Text>
                      <Text style={styles.resultMetricValue}>{threshold.value}</Text>
                    </View>
                  ))}
                  {result.reason_codes.map((reason) => (
                    <Text key={reason} style={styles.reason}>
                      • {reasonLabels[reason] ?? reason.replaceAll('_', ' ')}
                    </Text>
                  ))}
                  {result.requires_athlete_confirmation ? (
                    <Text style={styles.safety}>
                      Deze drempel wacht op bevestigingssemantiek én een
                      goedgekeurd Zone 1-5-model. Er is nu niets actief gemaakt.
                    </Text>
                  ) : null}
                  <ActionButton
                    label="Protocoloverzicht"
                    onPress={() => setStage('protocol')}
                  />
                  <ActionButton label="Terug" onPress={onBack} secondary />
                </View>
              ) : null}
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  keyboard: { flex: 1 },
  centered: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    flex: 1,
    gap: spacing.md,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  headerTitleBlock: { alignItems: 'center' },
  logo: {
    color: colors.accent,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  headerTitle: { color: colors.ink, fontSize: 13, fontWeight: '900' },
  link: { padding: spacing.sm },
  linkText: { color: colors.inkMuted, fontSize: 12, fontWeight: '800' },
  content: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 56 },
  errorBanner: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.md,
    color: colors.danger,
    fontWeight: '800',
    lineHeight: 20,
    padding: spacing.md,
  },
  selectorRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  selector: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  selectorSelected: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  selectorText: { color: colors.ink, fontSize: 13, fontWeight: '900' },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.lg,
    padding: spacing.lg,
  },
  cardTitle: { color: colors.ink, fontSize: 20, fontWeight: '900' },
  eyebrow: {
    color: colors.brand,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  pageTitle: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  muted: { color: colors.inkMuted, lineHeight: 21 },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  segmentList: { gap: spacing.sm },
  segmentSummary: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    borderRadius: radius.md,
    flexDirection: 'row',
    gap: spacing.md,
    padding: spacing.md,
  },
  segmentNumber: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: 18,
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  segmentNumberText: { color: colors.white, fontWeight: '900' },
  segmentBody: { flex: 1, gap: 2 },
  segmentTitle: { color: colors.ink, fontSize: 15, fontWeight: '900' },
  safety: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    color: colors.ink,
    fontWeight: '700',
    lineHeight: 20,
    padding: spacing.md,
  },
  historyText: { color: colors.inkFaint, fontSize: 12, textAlign: 'center' },
  twoColumns: { flexDirection: 'row', gap: spacing.sm },
  column: { flex: 1 },
  segmentCard: {
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.md,
  },
  toggleRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  toggleBox: {
    borderColor: colors.inkFaint,
    borderRadius: 5,
    borderWidth: 2,
    height: 20,
    width: 20,
  },
  toggleBoxChecked: { backgroundColor: colors.brand, borderColor: colors.brand },
  toggleLabel: { color: colors.ink, flex: 1, fontWeight: '700', lineHeight: 19 },
  unit: { color: colors.inkMuted, fontWeight: '800' },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    justifyContent: 'center',
    minHeight: 50,
    paddingHorizontal: spacing.lg,
  },
  actionSecondary: {
    backgroundColor: colors.surface,
    borderColor: colors.brand,
    borderWidth: 1,
  },
  actionText: { color: colors.white, fontSize: 15, fontWeight: '900' },
  actionTextSecondary: { color: colors.brand },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.78 },
  resultMetric: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  resultMetricLabel: { color: colors.inkMuted, fontSize: 13, fontWeight: '800' },
  resultMetricValue: { color: colors.brand, fontSize: 28, fontWeight: '900' },
  reason: { color: colors.inkMuted, lineHeight: 21 },
});
