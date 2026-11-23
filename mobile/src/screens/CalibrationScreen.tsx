import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approveZoneProposal,
  confirmCalibrationThreshold,
  createActivity,
  evaluateCalibration,
  getCalibrationStatus,
  getOnboarding,
  listCalibrationProtocols,
  rejectCalibrationThreshold,
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
  ThresholdDecision,
  ZoneMetricKind,
} from '../api/types';
import { ZoneField as FormField } from '../ui-v2/components/ZoneField';
import { rpeChoices, type CanonicalRpe } from '../lib/rpe';
import { ZoneStatusChip, ZoneTable, zoneValue, ZoneInfoRow } from '../ui-v2/components/ZoneVisuals';
import { parseRunPace } from '../lib/runPace';
import { colors, layout, radius, shadows, space } from '../ui-v2/tokens';
import { Text } from '../ui-v2/primitives/Text';
import { Button } from '../ui-v2/primitives/Button';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { IconTile } from '../ui-v2/primitives/IconTile';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { Notice } from '../ui-v2/primitives/Notice';
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
import { translate } from '../i18n/runtime';

type Props = {
  accessToken: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
};

type Stage = 'feedback' | 'result';

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

type Translate = ReturnType<typeof useLanguage>['t'];

const disciplineLabels: Record<Discipline, TranslationKey> = {
  swim: 'calibration.discipline.swim',
  bike: 'calibration.discipline.bike',
  run: 'calibration.discipline.run',
};

const protocolLabels: Partial<Record<string, TranslationKey>> = {
  start23_run_threshold_30min_v1: 'calibration.protocol.runThreshold30',
  start23_bike_ftp_30min_v1: 'calibration.protocol.bikeFtp30',
  start23_bike_fthr_20min_v1: 'calibration.protocol.bikeFthr20',
  start23_swim_css_400_200_v1: 'calibration.protocol.swimCss',
  start23_week1_run_calibration_v1: 'calibration.protocol.week1Run',
  start23_week1_bike_calibration_v1: 'calibration.protocol.week1Bike',
  start23_week1_swim_calibration_v1: 'calibration.protocol.week1Swim',
};

const purposeLabels: Partial<Record<string, TranslationKey>> = {
  prepare: 'calibration.purpose.prepare',
  valid_test_segment: 'calibration.purpose.validTestSegment',
  recovery: 'calibration.purpose.recovery',
  recovery_between_tests: 'calibration.purpose.recoveryBetweenTests',
  calibration_observation: 'calibration.purpose.calibrationObservation',
  optional_calibration_observation: 'calibration.purpose.optionalCalibrationObservation',
};

const guidanceLabels: Record<GuidanceMode, TranslationKey> = {
  power: 'calibration.guidance.power',
  heart_rate: 'calibration.guidance.heartRate',
  combined: 'calibration.guidance.combined',
  pace: 'calibration.guidance.pace',
  rpe_only: 'calibration.guidance.rpeOnly',
};

const metricLabels: Record<ZoneMetricKind, TranslationKey> = {
  swim_css_seconds_per_100m: 'calibration.metric.swimCss',
  bike_ftp_watts: 'calibration.metric.bikeFtp',
  bike_threshold_heart_rate_bpm: 'calibration.metric.bikeThresholdHr',
  run_threshold_pace_seconds_per_km: 'calibration.metric.runThresholdPace',
  run_lthr_bpm: 'calibration.metric.runLthr',
};

const resultLabels: Record<CalibrationEvaluation['status'], TranslationKey> = {
  insufficient_data: 'calibration.result.insufficientData',
  insufficient_protocol: 'calibration.result.insufficientProtocol',
  rpe_only: 'calibration.result.rpeOnly',
  provisionally_calibrated: 'calibration.result.provisionallyCalibrated',
  threshold_estimated: 'calibration.result.thresholdEstimated',
};

const reasonLabels: Partial<Record<string, TranslationKey>> = {
  calculated_threshold_unusually_low: 'calibration.reason.thresholdUnusuallyLow',
  zone_profile_pending_athlete_confirmation: 'calibration.reason.zonePendingConfirmation',
  threshold_not_permitted_from_submaximal_calibration:
    'calibration.reason.thresholdNotPermittedSubmaximal',
  sensor_data_missing: 'calibration.reason.sensorDataMissing',
  missing_session_rpe: 'calibration.reason.missingSessionRpe',
  missing_block_rpe: 'calibration.reason.missingBlockRpe',
  sensor_quality_insufficient: 'calibration.reason.sensorQualityInsufficient',
  required_segment_missing: 'calibration.reason.requiredSegmentMissing',
  test_segment_incomplete: 'calibration.reason.testSegmentIncomplete',
  interrupted: 'calibration.reason.interrupted',
  pace_rounding_rule_not_approved: 'calibration.reason.paceRoundingNotApproved',
};

// Server/protocol identifiers without a local label are shown as-is.
function labelOr(t: Translate, key: TranslationKey | undefined, fallback: string): string {
  return key ? t(key) : fallback;
}

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

function parseRpe(t: Translate, value: string, label: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 10) {
    throw new Error(t('calibration.error.rpeRange', { label }));
  }
  return parsed;
}

function parsePositive(t: Translate, value: string, label: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(t('calibration.error.positive', { label }));
  }
  return String(parsed);
}

function parseRunPaceRequired(t: Translate, value: string): string {
  const seconds = parseRunPace(value);
  if (seconds === null) throw new Error(t('calibration.error.runPace'));
  return String(seconds);
}

function parseCompleteness(t: Translate, value: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
    throw new Error(t('calibration.error.completeness'));
  }
  return String(parsed / 100);
}

function parseCsvNumbers(
  t: Translate,
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
    throw new Error(t('calibration.error.fourValues', { label }));
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
  return <ChoiceRow mode="checkbox" label={label} selected={checked} onPress={onPress} />;
}

// Calibration choices edit the observation draft; only explicit submission saves it.
function RpeChoiceList({ disabled = false, discipline, label, onSelect, selectedValue = null }: {
  disabled?: boolean; discipline: Discipline; label: string; onSelect: (value: CanonicalRpe) => void; selectedValue?: number | null;
}) {
  return <View style={{ gap: space[12] }}><Text variant="label">{label}</Text>
    <View accessibilityRole="radiogroup" accessibilityLabel={label} style={{ gap: space[12] }}>
      {rpeChoices(discipline).map(choice => <ChoiceRow key={choice.value} label={choice.value + ' · ' + choice.description}
        accessibilityLabel={choice.description + ' (RPE ' + choice.value + ')'} selected={selectedValue === choice.value}
        disabled={disabled} onPress={() => onSelect(choice.value)} />)}
    </View>
  </View>;
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
  return <Button label={label} onPress={onPress} disabled={disabled} busy={loading}
    variant={secondary ? 'outline' : 'primary'} trailingIcon={secondary ? undefined : 'forward'} />;
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
  const { t, locale } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const compact = width < 480 || fontScale > 1;
  const [setups, setSetups] = useState<DisciplineSetup[]>([]);
  const [protocols, setProtocols] = useState<Record<string, CalibrationProtocol>>(
    {},
  );
  const [evaluations, setEvaluations] = useState<CalibrationEvaluation[]>([]);
  const [thresholdDecisions, setThresholdDecisions] = useState<
    ThresholdDecision[]
  >([]);
  const [selectedProtocolId, setSelectedProtocolId] = useState<string | null>(
    null,
  );
  const [stage, setStage] = useState<Stage>('feedback');
  const [drafts, setDrafts] = useState<Record<string, SegmentDraft>>({});
  const [performedAt, setPerformedAt] = useState(new Date().toISOString());
  const [timezone, setTimezone] = useState('');
  const [durationMinutes, setDurationMinutes] = useState('');
  const [sessionRpe, setSessionRpe] = useState('');
  const [swimConditionsConfirmed, setSwimConditionsConfirmed] = useState(false);
  const [activityId, setActivityId] = useState<string | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [result, setResult] = useState<CalibrationEvaluation | null>(null);
  const [thresholdDecision, setThresholdDecision] =
    useState<ThresholdDecision | null>(null);
  const [zonesActivated, setZonesActivated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [status, onboarding] = await Promise.all([
      getCalibrationStatus(accessToken),
      getOnboarding(accessToken),
    ]);
    if (
      !onboarding.profile?.timezone_confirmed_at ||
      !onboarding.profile.timezone
    ) {
      throw new Error(translate('calibration.error.timezoneUnconfirmed'));
    }
    setTimezone(onboarding.profile.timezone);
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
    const currentSetups = protocolSetups.filter(
      (setup) => setup.protocol_id && protocolMap[setup.protocol_id],
    );
    setSetups(currentSetups);
    setProtocols(protocolMap);
    setEvaluations(status.evaluations);
    setThresholdDecisions(status.threshold_decisions);
    setSelectedProtocolId((current) => {
      if (current && protocolMap[current]) return current;
      return currentSetups[0]?.protocol_id ?? null;
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
              : translate('calibration.error.loadFailed'),
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
    setThresholdDecision(null);
    setZonesActivated(false);
    setStage('feedback');
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

  const openPriorResult = (evaluation: CalibrationEvaluation) => {
    const decision =
      thresholdDecisions.find(
        (candidate) => candidate.evaluation_id === evaluation.id,
      ) ?? null;
    setResult(evaluation);
    setThresholdDecision(decision);
    setZonesActivated(decision?.zone_proposal_state === 'applied');
    setStage('result');
  };

  const validateFeedback = (
    protocol: CalibrationProtocol,
  ) => {
    if (Number.isNaN(new Date(performedAt).getTime())) {
      throw new Error(t('calibration.error.invalidTimestamp'));
    }
    if (!timezone.trim()) throw new Error(t('calibration.error.timezoneMissing'));
    parsePositive(t, durationMinutes, t('calibration.field.totalDuration'));
    parseRpe(t, sessionRpe, t('calibration.field.sessionRpe'));
    if (needsSwimConditions(protocol) && !swimConditionsConfirmed) {
      throw new Error(t('calibration.error.swimConditions'));
    }
    for (const segment of protocol.segments) {
      const draft = drafts[segment.segment_id];
      if (!draft || !draft.included) continue;
      if (isMainSegment(segment)) {
        parseRpe(t, draft.blockRpe, t('calibration.field.blockRpe', { segment: segment.segment_id }));
      }
      if (!draft.completed) continue;
      if (
        protocol.protocol_id === 'start23_run_threshold_30min_v1' &&
        segment.segment_id === 'test_30min'
      ) {
        parseRunPaceRequired(t, draft.averagePace);
        parseCompleteness(t, draft.completenessPercent);
        if (!draft.stableSegment) {
          throw new Error(t('calibration.error.runStable'));
        }
      }
      if (
        protocol.protocol_id === 'start23_bike_ftp_30min_v1' &&
        segment.segment_id === 'test_30min'
      ) {
        parsePositive(t, draft.last20Power, t('calibration.field.last20Power'));
        parseCompleteness(t, draft.completenessPercent);
        if (!draft.stableSegment || !draft.calibratedPowerSource) {
          throw new Error(t('calibration.error.bikeStable'));
        }
      }
      if (
        protocol.protocol_id === 'start23_bike_fthr_20min_v1' &&
        segment.segment_id === 'test_20min'
      ) {
        parsePositive(t, draft.averageHeartRate, t('calibration.field.averageHeartRate'));
        parseCompleteness(t, draft.completenessPercent);
      }
      if (
        protocol.protocol_id === 'start23_swim_css_400_200_v1' &&
        ['tt_400m', 'tt_200m'].includes(segment.segment_id)
      ) {
        parsePositive(t, draft.elapsedTime, t('calibration.field.swimTestTime'));
      }
      if (
        protocol.protocol_type === 'submaximal_calibration' &&
        isMainSegment(segment)
      ) {
        if (protocol.discipline === 'swim') {
          parsePositive(t, draft.elapsedTime, t('calibration.field.swimTotalTime'));
          parseCsvNumbers(t, draft.repetitionTimes, t('calibration.field.repetitionTimes'), false);
          parseCsvNumbers(t, draft.repetitionRests, t('calibration.field.restTimes'), true);
        } else {
          parsePositive(t, draft.averageHeartRate, t('calibration.field.averageHeartRate'));
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
        t,
        draft.blockRpe,
        t('calibration.field.blockRpe', { segment: segment.segment_id }),
      );
      input.steady_execution = draft.steadyExecution;
    }
    if (segment.segment_id === 'cooldown') {
      input.reported_session_rpe = parseRpe(t, sessionRpe, t('calibration.field.sessionRpe'));
    }
    if (draft.averageHeartRate) {
      input.average_heart_rate_bpm = parsePositive(
        t,
        draft.averageHeartRate,
        t('calibration.field.averageHeartRate'),
      );
    }
    if (draft.endingHeartRate) {
      input.ending_heart_rate_bpm = parsePositive(
        t,
        draft.endingHeartRate,
        t('calibration.field.endingHeartRate'),
      );
    }
    if (draft.last20HeartRate) {
      input.average_heart_rate_last_20min_bpm = parsePositive(
        t,
        draft.last20HeartRate,
        t('calibration.field.last20HeartRate'),
      );
    }
    if (draft.averagePower) {
      input.average_power_watts = parsePositive(
        t,
        draft.averagePower,
        t('calibration.field.averagePower'),
      );
    }
    if (draft.last20Power) {
      input.average_power_last_20min_watts = parsePositive(
        t,
        draft.last20Power,
        t('calibration.field.last20Power'),
      );
    }
    if (draft.averagePace) {
      input.average_pace_seconds_per_km = parseRunPaceRequired(t, draft.averagePace);
    }
    if (draft.elapsedTime) {
      input.elapsed_time_seconds = parsePositive(
        t,
        draft.elapsedTime,
        t('calibration.field.elapsedTime'),
      );
    }
    if (hasMetrics && draft.completenessPercent) {
      input.data_completeness = parseCompleteness(t, draft.completenessPercent);
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
          t,
          draft.repetitionTimes,
          t('calibration.field.repetitionTimes'),
          false,
        );
        const rests = parseCsvNumbers(
          t,
          draft.repetitionRests,
          t('calibration.field.restTimes'),
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
      validateFeedback(selectedProtocol);
      let savedActivityId = activityId;
      if (!savedActivityId) {
        const activity = await createActivity(accessToken, idempotencyKey, {
          discipline: selectedProtocol.discipline,
          started_at: new Date(performedAt).toISOString(),
          timezone: timezone.trim(),
          duration_minutes: parsePositive(t, durationMinutes, t('calibration.field.totalDuration')),
          ...(protocolDistance(selectedProtocol) === undefined
            ? {}
            : { distance_meters: protocolDistance(selectedProtocol) }),
        });
        savedActivityId = activity.id;
        setActivityId(savedActivityId);
      }
      const calibrationHeartRate =
        selectedProtocol.protocol_type === 'submaximal_calibration' &&
        selectedProtocol.discipline !== 'swim'
          ? Number(
              parsePositive(
                t,
                drafts[
                  selectedProtocol.segments.find(
                    (segment) => isMainSegment(segment) && !segment.optional,
                  )?.segment_id ?? ''
                ]?.averageHeartRate ?? '',
                t('calibration.field.averageHeartRate'),
              ),
            )
          : undefined;
      await submitActivityRpe(
        accessToken,
        savedActivityId,
        parseRpe(t, sessionRpe, t('calibration.field.sessionRpe')),
        calibrationHeartRate,
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
          : t('calibration.error.submitFailed'),
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmThreshold = async () => {
    if (!result) return;
    setBusy(true);
    setError(null);
    try {
      const decision = await confirmCalibrationThreshold(accessToken, result.id);
      setThresholdDecision(decision);
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('calibration.error.confirmFailed'),
      );
    } finally {
      setBusy(false);
    }
  };

  const rejectThreshold = async () => {
    if (!result) return;
    setBusy(true);
    setError(null);
    try {
      const decision = await rejectCalibrationThreshold(accessToken, result.id);
      setThresholdDecision(decision);
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('calibration.error.rejectFailed'),
      );
    } finally {
      setBusy(false);
    }
  };

  const activateZones = async () => {
    if (!thresholdDecision?.zone_proposal_id) return;
    setBusy(true);
    setError(null);
    try {
      await approveZoneProposal(
        accessToken,
        thresholdDecision.zone_proposal_id,
        thresholdDecision.base_zone_profile_id,
      );
      setZonesActivated(true);
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('calibration.error.zonesFailed'),
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={colors.primary} size="large" />
        <Text style={styles.muted}>{t('calibration.loading')}</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboard}
      >
        <ScrollView
          automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}
          contentContainerStyle={styles.content}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          style={styles.scroll}
        >
          <BrandedFormHeader caption={t('calibration.caption')} backLabel={t('calibration.back')} onBack={onBack} onSignOut={onSignOut} />
          {error ? <Notice tone="error">{error}</Notice> : null}

          {setups.length === 0 ? (
            <View style={styles.card}>
              <IconTile name="document" size="focus" />
              <Text style={styles.cardTitle}>{t('calibration.empty.title')}</Text>
              <Text style={styles.muted}>{t('calibration.empty.body')}</Text>
              <ActionButton label={t('calibration.empty.backToIntake')} onPress={onBack} />
            </View>
          ) : (
            <>
              <View accessibilityRole="radiogroup" style={styles.selectorRow}>
                {setups.map((setup) => (
                  <ChoiceRow key={setup.discipline + ':' + setup.protocol_id} label={t(disciplineLabels[setup.discipline])}
                    selected={selectedProtocolId === setup.protocol_id} onPress={() => setSelectedProtocolId(setup.protocol_id)} />
                ))}
              </View>

              {selectedProtocol && selectedSetup && stage === 'feedback' ? (
                <View style={styles.card}>
                  <View
                    accessibilityLabel={t('calibration.painWarning')}
                    accessibilityRole="alert"
                    accessible
                    style={styles.painWarning}
                  >
                    <Text style={styles.painWarningText}>{t('calibration.painWarning')}</Text>
                  </View>
                  <View style={styles.badges}>
                    <ZoneStatusChip
                      label={
                        selectedProtocol.protocol_type === 'field_test'
                          ? t('calibration.type.fieldTest')
                          : t('calibration.type.submaximal')
                      }
                    />
                    <ZoneStatusChip label={t('calibration.reviewedVersion', { version: selectedProtocol.version })} />
                  </View>
                  <Text style={styles.pageTitle}>
                    {labelOr(t, protocolLabels[selectedProtocol.protocol_id], selectedProtocol.protocol_id)}
                  </Text>
                  <Text style={styles.muted}>
                    {t('calibration.guidanceIntro', { guidance: t(guidanceLabels[selectedSetup.guidance_mode]) })}
                  </Text>
                  <View style={styles.segmentList}>
                    {selectedProtocol.segments.map((segment) => (
                      <View key={segment.segment_id} style={styles.segmentSummary}>
                        <View style={styles.segmentNumber}>
                          <Text style={styles.segmentNumberText}>{segment.order}</Text>
                        </View>
                        <View style={styles.segmentBody}>
                          <Text style={styles.segmentTitle}>
                            {labelOr(t, purposeLabels[segment.purpose], segment.purpose)}
                            {segment.optional ? ' · ' + t('calibration.optional') : ''}
                          </Text>
                          <Text style={styles.muted}>
                            {segment.duration_seconds
                              ? `${segment.duration_seconds / 60} min`
                              : `${segment.distance_meters} m`}
                          </Text>
                          <Text style={styles.muted}>
                            {segment.rpe_display_label} · {segment.rpe_training_type}
                          </Text>
                          <Text style={styles.muted}>{segment.rpe_description}</Text>
                        </View>
                      </View>
                    ))}
                  </View>
                  <ZoneInfoRow icon="document"><Text variant="supporting" tone="textMuted">{t('calibration.protocolProvenance', { id: selectedProtocol.protocol_id, version: selectedProtocol.version, status: selectedProtocol.review_status })}</Text></ZoneInfoRow>
                  <Text style={styles.eyebrow}>{t('calibration.observation.eyebrow')}</Text>
                  <Text style={styles.pageTitle}>{t('calibration.observation.title')}</Text>
                  <Text style={styles.muted}>{t('calibration.observation.hint')}</Text>
                  <FormField
                    autoCapitalize="none"
                    label={t('calibration.field.startTime')}
                    onChangeText={setPerformedAt}
                    placeholder="2026-08-15T09:00:00+02:00"
                    value={performedAt}
                  />
                  <FormField
                    inputMode="decimal"
                    label={t('calibration.field.totalDuration')}
                    onChangeText={setDurationMinutes}
                    placeholder={t('calibration.placeholder.minutes')}
                    value={durationMinutes}
                  />
                  <RpeChoiceList
                    disabled={busy}
                    discipline={selectedProtocol.discipline}
                    label={t('calibration.sessionFeel')}
                    onSelect={(value) => setSessionRpe(String(value))}
                    selectedValue={Number(sessionRpe) || null}
                  />

                  {needsSwimConditions(selectedProtocol) ? (
                    <Toggle
                      checked={swimConditionsConfirmed}
                      label={t('calibration.swimConditions', { pool: String(selectedSetup.pool_length_meters) })}
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
                          {labelOr(t, purposeLabels[segment.purpose], segment.purpose)}
                        </Text>
                        {segment.optional ? (
                          <Toggle
                            checked={draft.included}
                            label={t('calibration.optionalPerformed')}
                            onPress={() =>
                              updateDraft(segment.segment_id, {
                                included: !draft.included,
                              })
                            }
                          />
                        ) : null}
                        {draft.included ? (
                          <>
                            <View style={[styles.twoColumns, compact && styles.stacked]}>
                              <View style={[styles.column, compact && styles.fullWidth]}>
                                <Toggle
                                  checked={draft.completed}
                                  label={t('calibration.completed')}
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      completed: !draft.completed,
                                    })
                                  }
                                />
                              </View>
                              <View style={[styles.column, compact && styles.fullWidth]}>
                                <Toggle
                                  checked={draft.interrupted}
                                  label={t('calibration.interrupted')}
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      interrupted: !draft.interrupted,
                                    })
                                  }
                                />
                              </View>
                            </View>
                            {main ? (
                              <RpeChoiceList
                                disabled={busy}
                                discipline={selectedProtocol.discipline}
                                label={t('calibration.blockFeel')}
                                onSelect={(value) =>
                                  updateDraft(segment.segment_id, {
                                    blockRpe: String(value),
                                  })
                                }
                                selectedValue={Number(draft.blockRpe) || null}
                              />
                            ) : null}
                            {runTest ? (
                              <>
                                <FormField
                                  inputMode="decimal"
                                  label={t('calibration.field.runAveragePace')}
                                  onChangeText={(value) =>
                                    updateDraft(segment.segment_id, {
                                      averagePace: value,
                                    })
                                  }
                                  placeholder={t('calibration.placeholder.pace')}
                                  value={draft.averagePace}
                                />
                                <FormField
                                  inputMode="decimal"
                                  label={t('calibration.field.last20HeartRateOptional')}
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
                                  label={t('calibration.paceStable')}
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
                                  label={t('calibration.field.last20PowerShort')}
                                  onChangeText={(value) =>
                                    updateDraft(segment.segment_id, {
                                      last20Power: value,
                                    })
                                  }
                                  placeholder={t('calibration.placeholder.watt')}
                                  value={draft.last20Power}
                                />
                                <Toggle
                                  checked={draft.calibratedPowerSource}
                                  label={t('calibration.powerCalibrated')}
                                  onPress={() =>
                                    updateDraft(segment.segment_id, {
                                      calibratedPowerSource:
                                        !draft.calibratedPowerSource,
                                    })
                                  }
                                />
                                <Toggle
                                  checked={draft.stableSegment}
                                  label={t('calibration.powerStable')}
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
                                label={t('calibration.field.bikeTestHeartRate')}
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
                                label={t('calibration.field.swimDistanceTime', { distance: String(segment.distance_meters) })}
                                onChangeText={(value) =>
                                  updateDraft(segment.segment_id, {
                                    elapsedTime: value,
                                  })
                                }
                                placeholder={t('calibration.placeholder.seconds')}
                                value={draft.elapsedTime}
                              />
                            ) : null}
                            {(runTest || bikeFtp || bikeHr) ? (
                              <FormField
                                inputMode="decimal"
                                label={t('calibration.field.coverage')}
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
                            {calibrationMain ? (
                              <>
                                {selectedProtocol.discipline === 'swim' ? (
                                  <>
                                    <FormField
                                      inputMode="decimal"
                                      label={t('calibration.field.blockTotalTime')}
                                      onChangeText={(value) =>
                                        updateDraft(segment.segment_id, {
                                          elapsedTime: value,
                                        })
                                      }
                                      placeholder={t('calibration.placeholder.seconds')}
                                      value={draft.elapsedTime}
                                    />
                                    <FormField
                                      inputMode="decimal"
                                      label={t('calibration.field.fourRepetitionTimes')}
                                      onChangeText={(value) =>
                                        updateDraft(segment.segment_id, {
                                          repetitionTimes: value,
                                        })
                                      }
                                      placeholder={t('calibration.placeholder.repetitionTimes')}
                                      value={draft.repetitionTimes}
                                    />
                                    <FormField
                                      inputMode="decimal"
                                      label={t('calibration.field.fourRestTimes')}
                                      onChangeText={(value) =>
                                        updateDraft(segment.segment_id, {
                                          repetitionRests: value,
                                        })
                                      }
                                      placeholder={t('calibration.placeholder.restTimes')}
                                      value={draft.repetitionRests}
                                    />
                                  </>
                                ) : (
                                  <FormField
                                    hint={t('calibration.averageHeartRateHint')}
                                    inputMode="decimal"
                                    label={t('calibration.field.averageHeartRate')}
                                    onChangeText={(value) =>
                                      updateDraft(segment.segment_id, {
                                        averageHeartRate: value,
                                      })
                                    }
                                    placeholder="bpm"
                                    value={draft.averageHeartRate}
                                  />
                                )}
                              </>
                            ) : null}
                          </>
                        ) : null}
                      </View>
                    );
                  })}

                  {activityId ? (
                    <Text style={styles.safety}>{t('calibration.retryNotice')}</Text>
                  ) : null}
                  <ActionButton
                    label={t('calibration.submit')}
                    loading={busy}
                    onPress={() => void submit()}
                  />
                  {priorResults.length > 0 ? (
                    <View style={styles.segmentList}>
                      <Text style={styles.historyText}>
                        {t(priorResults.length === 1 ? 'calibration.priorOne' : 'calibration.priorMany', { count: priorResults.length })}
                      </Text>
                      {priorResults.slice(0, 3).map((evaluation) => (
                        <ActionButton
                          key={evaluation.id}
                          label={t('calibration.viewResult', { date: new Date(evaluation.created_at).toLocaleDateString(locale) })}
                          onPress={() => openPriorResult(evaluation)}
                          secondary
                        />
                      ))}
                    </View>
                  ) : null}
                </View>
              ) : null}

              {stage === 'result' && result ? (
                <View style={styles.card}>
                  <Text style={styles.eyebrow}>{t('calibration.result.eyebrow')}</Text>
                  <Text style={styles.pageTitle}>{t(resultLabels[result.status])}</Text>
                  <View style={styles.badges}>
                    <ZoneStatusChip label={t('calibration.confidence', { value: result.confidence })} />
                    <ZoneStatusChip label={t('calibration.zoneStatus', { value: result.zone_status })} pending />
                  </View>
                  {result.thresholds.map((threshold) => (
                    <View key={threshold.metric_kind} style={styles.resultMetric}>
                      <Text style={styles.resultMetricLabel}>
                        {t(metricLabels[threshold.metric_kind])}
                      </Text>
                      <Text style={styles.resultMetricValue}>
                        {zoneValue(threshold.metric_kind, threshold.value)}
                      </Text>
                    </View>
                  ))}
                  {result.zone_profiles.map((profile) => (
                    <View key={profile.metric_kind} style={styles.resultMetric}>
                      <Text style={styles.resultMetricLabel}>
                        {t(metricLabels[profile.metric_kind])}
                        {' · ' + t(profile.is_primary ? 'calibration.primary' : 'calibration.secondary')}
                      </Text>
                      <ZoneTable boundaries={profile.boundaries} metricKind={profile.metric_kind} />
                      <Text variant="supporting" tone="textMuted">{profile.boundary_source} · {profile.zone_model_version}</Text>
                    </View>
                  ))}
                  <ZoneInfoRow icon="document"><Text variant="supporting" tone="textMuted">{t('calibration.rulesProvenance', { version: result.ruleset_version })}{result.zone_model_version ? ' · ' + t('calibration.modelProvenance', { version: result.zone_model_version }) : ''}</Text></ZoneInfoRow>
                  {result.reason_codes.map((reason) => (
                    <Text key={reason} style={styles.reason}>
                      • {labelOr(t, reasonLabels[reason], reason.replaceAll('_', ' '))}
                    </Text>
                  ))}
                  {result.requires_athlete_confirmation && !thresholdDecision ? (
                    <>
                      <Text style={styles.safety}>{t('calibration.confirmHint')}</Text>
                      <ActionButton
                        label={t('calibration.confirmThreshold')}
                        loading={busy}
                        onPress={() => void confirmThreshold()}
                      />
                      <ActionButton
                        disabled={busy}
                        label={t('calibration.rejectThreshold')}
                        onPress={() => void rejectThreshold()}
                        secondary
                      />
                    </>
                  ) : null}
                  {thresholdDecision?.state === 'accepted' &&
                  thresholdDecision.zone_proposal_state === 'pending' &&
                  !zonesActivated ? (
                    <>
                      <Text style={styles.safety}>{t('calibration.thresholdAccepted')}</Text>
                      <ActionButton
                        label={t('calibration.confirmZones')}
                        loading={busy}
                        onPress={() => void activateZones()}
                      />
                    </>
                  ) : null}
                  {thresholdDecision?.state === 'rejected' ? (
                    <Text style={styles.safety}>{t('calibration.thresholdRejected')}</Text>
                  ) : null}
                  {thresholdDecision?.state === 'accepted' &&
                  thresholdDecision.zone_proposal_state === 'rejected' ? (
                    <Text style={styles.safety}>{t('calibration.zoneProposalRejected')}</Text>
                  ) : null}
                  {zonesActivated ? (
                    <Text style={styles.safety}>{t('calibration.zonesActive')}</Text>
                  ) : null}
                  <ActionButton
                    label={t('calibration.newAttempt')}
                    onPress={() => setStage('feedback')}
                  />
                  <ActionButton label={t('calibration.back')} onPress={onBack} secondary />
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
  safeArea: { backgroundColor: colors.background, flex: 1 }, keyboard: { flex: 1 }, scroll: { flex: 1 },
  centered: { alignItems: 'center', backgroundColor: colors.background, flex: 1, gap: space[16], justifyContent: 'center' },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
  selectorRow: { gap: space[12] },
  card: { ...shadows.card, backgroundColor: colors.surface, borderColor: colors.border, borderRadius: radius.card, borderWidth: 1, gap: space[24], padding: space[16] },
  cardTitle: { color: colors.text, fontSize: 22, fontWeight: '600', lineHeight: 28 },
  eyebrow: { color: colors.primary, fontSize: 12, fontWeight: '600', letterSpacing: 1.2, textTransform: 'uppercase' },
  pageTitle: { color: colors.text, fontSize: 24, fontWeight: '600', letterSpacing: -0.5, lineHeight: 30 },
  muted: { color: colors.textMuted, fontSize: 16, lineHeight: 24 }, badges: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] },
  segmentList: { gap: space[16] }, segmentSummary: { alignItems: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.control, flexDirection: 'row', gap: space[12], padding: space[12] },
  segmentNumber: { alignItems: 'center', backgroundColor: colors.primary, borderRadius: radius.pill, height: 40, justifyContent: 'center', width: 40 },
  segmentNumberText: { color: colors.textInverse, fontWeight: '600' }, segmentBody: { flex: 1, minWidth: 0, gap: space[4] },
  segmentTitle: { color: colors.text, fontSize: 18, lineHeight: 26, fontWeight: '600' },
  safety: { backgroundColor: colors.primarySoft, borderRadius: radius.control, color: colors.text, fontSize: 16, lineHeight: 24, padding: space[16] },
  painWarning: { backgroundColor: colors.destructiveSoft, borderColor: colors.destructive, borderRadius: radius.control, borderWidth: 1, padding: space[16] },
  painWarningText: { color: colors.destructive, fontSize: 20, lineHeight: 28, fontWeight: '600' },
  historyText: { color: colors.textMuted, fontSize: 14, lineHeight: 20 }, twoColumns: { flexDirection: 'row', gap: space[12] }, column: { flex: 1 },
  stacked: { flexDirection: 'column' }, fullWidth: { flex: 0, width: '100%' },
  segmentCard: { borderColor: colors.border, borderRadius: radius.control, borderWidth: 1, gap: space[24], padding: space[16] },
  unit: { color: colors.textMuted, fontSize: 14, lineHeight: 20 },
  resultMetric: { backgroundColor: colors.primarySoft, borderRadius: radius.control, gap: space[8], padding: space[16] },
  resultMetricLabel: { color: colors.textMuted, fontSize: 14, lineHeight: 20 }, resultMetricValue: { color: colors.primary, fontSize: 24, lineHeight: 30, fontWeight: '600' },
  reason: { color: colors.textMuted, fontSize: 16, lineHeight: 24 },
});
