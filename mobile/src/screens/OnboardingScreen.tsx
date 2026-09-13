import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approveZoneProposal,
  completeOnboarding,
  getGoalPlanningOptions,
  getOnboarding,
  rejectZoneProposal,
  saveCalculatedZones,
  saveDisciplineSetup,
  saveOperationalProfile,
  savePrimaryGoal,
  saveProfile,
  saveTrainingHistory,
} from '../api/client';
import type {
  AthleteProfile,
  Discipline,
  DisciplineSetupInput,
  GoalPlanningOption,
  OnboardingState,
  OnboardingStep,
  PrimaryRaceGoal,
  RaceType,
  ZoneBoundary,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import {
  formatIsoDateInput,
  isPastIsoDateInput,
} from '../lib/dateInput';
import { colors, radius, shadows, spacing } from '../theme/tokens';
import {
  formatClockDuration,
  parseClockDuration,
  parsePositiveInteger,
  raceDisciplines,
  resolveDeviceTimezone,
} from '../lib/onboardingForms';
import { ZoneSetupStep } from './ZoneSetupStep';

const stepLabels: Array<{ step: OnboardingStep; label: string }> = [
  { step: 'profile', label: 'Profiel' },
  { step: 'heart_rate_monitor', label: 'Hartslag' },
  { step: 'timezone', label: 'Tijdzone' },
  { step: 'history', label: 'Historie' },
  { step: 'goal', label: 'Doel' },
  { step: 'zones', label: 'Zones' },
  { step: 'review', label: 'Afronden' },
];

type OnboardingScreenProps = {
  accessToken: string;
  onOpenCalibration: () => void;
  onOpenPlanning: () => void;
  onSignOut: () => Promise<void>;
};

type StepFrameProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
};

function StepFrame({
  eyebrow,
  title,
  description,
  children,
}: StepFrameProps) {
  return (
    <FadeInView style={styles.step}>
      <View style={styles.stepHero}>
        <View style={styles.eyebrowRow}>
          <View style={styles.eyebrowMark} />
          <Text style={styles.eyebrow}>{eyebrow}</Text>
        </View>
        <Text style={styles.stepTitle}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      <View style={styles.stepCard}>{children}</View>
    </FadeInView>
  );
}

type ActionButtonProps = {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  secondary?: boolean;
  onPress: () => void;
};

function ActionButton({
  label,
  loading = false,
  disabled = false,
  secondary = false,
  onPress,
}: ActionButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || loading}
      haptic={secondary ? undefined : 'light'}
      onPress={onPress}
      style={({ pressed }) => [
        styles.action,
        secondary && styles.actionSecondary,
        (disabled || loading) && styles.actionDisabled,
        pressed && styles.actionPressed,
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

type ProfileStepProps = {
  profile: AthleteProfile | null;
  saving: boolean;
  onSave: (input: {
    first_name?: string;
    last_name?: string;
    date_of_birth: string;
    resting_heart_rate_bpm: number;
  }) => Promise<void>;
};

function ProfileStep({ profile, saving, onSave }: ProfileStepProps) {
  const [firstName, setFirstName] = useState(profile?.first_name ?? '');
  const [lastName, setLastName] = useState(profile?.last_name ?? '');
  const [dateOfBirth, setDateOfBirth] = useState(profile?.date_of_birth ?? '');
  const [restingHeartRate, setRestingHeartRate] = useState(
    profile?.resting_heart_rate_bpm?.toString() ?? '',
  );
  const valid =
    isPastIsoDateInput(dateOfBirth) &&
    Number(restingHeartRate) > 0;

  return (
    <StepFrame
      description="Deze gegevens ondersteunen alleen goedgekeurde, deterministische berekeningen. Er worden geen medische grenzen afgedwongen."
      eyebrow="Stap 1 van 7"
      title="Jouw basis"
    >
      <View style={styles.form}>
        <FormField
          label="Voornaam (optioneel)"
          onChangeText={setFirstName}
          placeholder="Voornaam"
          value={firstName}
        />
        <FormField
          label="Achternaam (optioneel)"
          onChangeText={setLastName}
          placeholder="Achternaam"
          value={lastName}
        />
        <FormField
          hint="Gebruik JJJJ-MM-DD. De streepjes verschijnen automatisch."
          inputMode="numeric"
          label="Geboortedatum"
          maxLength={10}
          onChangeText={(value) => setDateOfBirth(formatIsoDateInput(value))}
          placeholder="1990-05-20"
          value={dateOfBirth}
        />
        <FormField
          inputMode="numeric"
          label="Rusthartslag"
          onChangeText={setRestingHeartRate}
          placeholder="52"
          suffix={<Text style={styles.unit}>bpm</Text>}
          value={restingHeartRate}
        />
      </View>
      <ActionButton
        disabled={!valid}
        label="Profiel opslaan"
        loading={saving}
        onPress={() =>
          void onSave({
            ...(firstName.trim() ? { first_name: firstName.trim() } : {}),
            ...(lastName.trim() ? { last_name: lastName.trim() } : {}),
            date_of_birth: dateOfBirth,
            resting_heart_rate_bpm: Number(restingHeartRate),
          })
        }
      />
    </StepFrame>
  );
}

type ConfirmationStepProps = {
  saving: boolean;
  onSave: () => Promise<void>;
};

function HeartRateMonitorStep({ saving, onSave }: ConfirmationStepProps) {
  return (
    <StepFrame
      description="Voor het huidige MVP moet je gemiddelde hartslag kunnen meten. Dat mag met iedere hartslagmeter en je kunt de waarde handmatig invoeren; een specifieke wearable is niet nodig."
      eyebrow="Stap 2 van 7"
      title="Heb je toegang tot een hartslagmeter?"
    >
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>RPE-only is niet beschikbaar</Text>
        <Text style={styles.approvalText}>
          Zonder bevestigde toegang kan onboarding niet worden afgerond en kan
          er geen planning worden aangemaakt.
        </Text>
      </View>
      <ActionButton
        label="Ja, ik kan gemiddelde hartslag meten"
        loading={saving}
        onPress={() => void onSave()}
      />
    </StepFrame>
  );
}

type TimezoneStepProps = {
  profile: AthleteProfile | null;
  saving: boolean;
  onSave: (timezone: string, source: 'device' | 'manual') => Promise<void>;
};

const fallbackTimezones = [
  'Europe/Amsterdam',
  'Europe/Brussels',
  'Europe/London',
  'Europe/Paris',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'Australia/Sydney',
] as const;

function TimezoneStep({ profile, saving, onSave }: TimezoneStepProps) {
  const detected = useMemo(resolveDeviceTimezone, []);
  const [timezone, setTimezone] = useState(
    profile?.timezone_confirmed_at ? (profile.timezone ?? '') : '',
  );
  const [source, setSource] = useState<'device' | 'manual'>(
    profile?.timezone_source ?? (detected ? 'device' : 'manual'),
  );

  return (
    <StepFrame
      description="Je tijdzone bepaalt lokale trainingsweken en datums. Controleer de gedetecteerde waarde of kies expliciet een IANA-tijdzone. We slaan nooit stilzwijgend een gok op."
      eyebrow="Stap 3 van 7"
      title="Bevestig je tijdzone"
    >
      {detected ? (
        <Pressable
          accessibilityRole="button"
          onPress={() => {
            setTimezone(detected);
            setSource('device');
          }}
          style={styles.goalModeCard}
        >
          <Text style={styles.goalModeTitle}>Gedetecteerd op dit apparaat</Text>
          <Text style={styles.goalModeDescription}>{detected}</Text>
        </Pressable>
      ) : (
        <Text style={styles.fieldError}>
          Automatische detectie is niet beschikbaar. Kies hieronder een tijdzone.
        </Text>
      )}
      <View style={styles.goalModeList}>
        {fallbackTimezones.map((value) => (
          <Pressable
            accessibilityRole="radio"
            accessibilityState={{ selected: timezone === value }}
            key={value}
            onPress={() => {
              setTimezone(value);
              setSource('manual');
            }}
            style={[
              styles.goalModeCard,
              timezone === value && styles.goalModeCardSelected,
            ]}
          >
            <Text style={styles.goalModeTitle}>{value}</Text>
          </Pressable>
        ))}
      </View>
      <FormField
        autoCapitalize="none"
        hint="Gebruik een geldige IANA-naam als je tijdzone niet in de lijst staat."
        label="Andere IANA-tijdzone"
        onChangeText={(value) => {
          setTimezone(value);
          setSource('manual');
        }}
        placeholder="Europe/Amsterdam"
        value={timezone}
      />
      <ActionButton
        disabled={!timezone.trim()}
        label="Tijdzone expliciet bevestigen"
        loading={saving}
        onPress={() => void onSave(timezone.trim(), source)}
      />
    </StepFrame>
  );
}

type HistoryStepProps = {
  state: OnboardingState;
  saving: boolean;
  onSave: (values: Record<Discipline, string>) => Promise<void>;
};

function HistoryStep({ state, saving, onSave }: HistoryStepProps) {
  const initial = (discipline: Discipline): string => {
    const entry = state.training_history.find((item) => item.discipline === discipline);
    return entry?.previous_month_weekly_minutes != null
      ? String(Number(entry.previous_month_weekly_minutes) / 60)
      : '';
  };
  const [values, setValues] = useState<Record<Discipline, string>>({
    swim: initial('swim'), bike: initial('bike'), run: initial('run'),
  });
  const hours = Object.values(values).map((value) => Number(value.replace(',', '.')));
  const valid = Object.values(values).every((value) => value.trim() !== '') &&
    hours.every((value) => Number.isFinite(value) && value >= 0) &&
    hours.reduce((total, value) => total + value, 0) <= 168;
  return (
    <StepFrame
      description="Hoeveel uur per week trainde je gemiddeld de afgelopen maand? Vul ook nul in als je een discipline niet deed."
      eyebrow="Stap 4 van 7"
      title="Waar sta je nu?"
    >
      <View style={styles.form}>
        {(['swim', 'bike', 'run'] as const).map((discipline) => (
          <View key={discipline} style={styles.disciplineCard}>
            <Text style={styles.cardTitle}>
              {discipline === 'swim' ? 'Zwemmen' : discipline === 'bike' ? 'Fietsen' : 'Hardlopen'}
            </Text>
            <FormField
              inputMode="decimal"
              label="Gemiddelde uren per week"
              onChangeText={(value) => setValues((current) => ({ ...current, [discipline]: value }))}
              placeholder="0"
              suffix={<Text style={styles.unit}>uur/week</Text>}
              value={values[discipline]}
            />
          </View>
        ))}
      </View>
      <ActionButton disabled={!valid} label="Trainingshistorie opslaan" loading={saving}
        onPress={() => void onSave(values)} />
    </StepFrame>
  );
}

type GoalStepProps = {
  goal: PrimaryRaceGoal | null;
  options: GoalPlanningOption[];
  saving: boolean;
  onSave: (input: {
    race_type: RaceType;
    race_name: string;
    race_date: string;
    swim_distance_meters?: number;
    bike_distance_meters?: number;
    run_distance_meters?: number;
    total_target_time_seconds: number;
    swim_target_time_seconds?: number;
    bike_target_time_seconds?: number;
    run_target_time_seconds?: number;
    specific_focus?: string;
  }) => Promise<void>;
};

function normalizeRaceDate(value: string): string | null {
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const candidate = new Date(Date.UTC(year, month - 1, day));
  if (
    candidate.getUTCFullYear() !== year ||
    candidate.getUTCMonth() !== month - 1 ||
    candidate.getUTCDate() !== day
  ) {
    return null;
  }
  const normalized = `${String(year).padStart(4, '0')}-${String(month).padStart(
    2,
    '0',
  )}-${String(day).padStart(2, '0')}`;
  const today = new Date();
  const localToday = `${today.getFullYear()}-${String(
    today.getMonth() + 1,
  ).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  return normalized > localToday ? normalized : null;
}

function GoalStep({ goal, options, saving, onSave }: GoalStepProps) {
  const [selectedKind, setSelectedKind] = useState<
    GoalPlanningOption['goal_kind'] | null
  >(goal ? 'race_event' : null);
  const [raceType, setRaceType] = useState<RaceType>(
    goal?.race_type ?? 'triathlon',
  );
  const [raceName, setRaceName] = useState(goal?.race_name ?? '');
  const [specificFocus, setSpecificFocus] = useState(goal?.specific_focus ?? '');
  const [targetDate, setTargetDate] = useState(goal?.race_date ?? '');
  const [totalTime, setTotalTime] = useState(
    formatClockDuration(goal?.total_target_time_seconds ?? null),
  );
  const [distances, setDistances] = useState<Record<Discipline, string>>({
    swim: goal?.swim_distance_meters?.toString() ?? '',
    bike: goal?.bike_distance_meters?.toString() ?? '',
    run: goal?.run_distance_meters?.toString() ?? '',
  });
  const [disciplineTimes, setDisciplineTimes] = useState<
    Record<Discipline, string>
  >({
    swim: formatClockDuration(goal?.swim_target_time_seconds ?? null),
    bike: formatClockDuration(goal?.bike_target_time_seconds ?? null),
    run: formatClockDuration(goal?.run_target_time_seconds ?? null),
  });
  const normalizedTargetDate = normalizeRaceDate(targetDate);
  const disciplines = raceDisciplines[raceType];
  const parsedTotalTime = parseClockDuration(totalTime);
  const parsedDistances = Object.fromEntries(
    disciplines.map((discipline) => [
      discipline,
      parsePositiveInteger(distances[discipline]),
    ]),
  ) as Partial<Record<Discipline, number | null>>;
  const parsedDisciplineTimes = Object.fromEntries(
    disciplines.map((discipline) => [
      discipline,
      disciplineTimes[discipline].trim()
        ? parseClockDuration(disciplineTimes[discipline])
        : undefined,
    ]),
  ) as Partial<Record<Discipline, number | null | undefined>>;
  const individualTotal = Object.values(parsedDisciplineTimes).reduce<number>(
    (sum, value) => sum + (value ?? 0),
    0,
  );
  const valid = Boolean(
    raceName.trim() &&
      normalizedTargetDate &&
      parsedTotalTime &&
      disciplines.every((discipline) => parsedDistances[discipline]) &&
      disciplines.every(
        (discipline) =>
          !disciplineTimes[discipline].trim() ||
          parsedDisciplineTimes[discipline] !== null,
      ) &&
      parsedTotalTime !== null &&
      individualTotal <= parsedTotalTime,
  );
  const raceOption = options.find(
    (option) => option.goal_family === 'race_event',
  );
  const personalOptions = options.filter(
    (option) => option.goal_kind === 'personal_goal',
  );

  return (
    <StepFrame
      description="Een wedstrijdplan rekent terug vanaf een racedatum. Een persoonlijk doel krijgt een eigen cyclus vanaf week 1 en gebruikt nooit stilzwijgend wedstrijdregels."
      eyebrow="Stap 5 van 7"
      title="Kies je trainingsdoel"
    >
      <View style={styles.goalModeList}>
        <Pressable
          accessibilityRole="radio"
          accessibilityState={{ selected: selectedKind === 'race_event' }}
          disabled={raceOption?.availability !== 'available'}
          onPress={() => setSelectedKind('race_event')}
          style={({ pressed }) => [
            styles.goalModeCard,
            selectedKind === 'race_event' && styles.goalModeCardSelected,
            pressed && styles.actionPressed,
          ]}
        >
          <View style={styles.goalModeHeading}>
            <View
              style={[
                styles.goalModeRadio,
                selectedKind === 'race_event' && styles.goalModeRadioSelected,
              ]}
            />
            <Text style={styles.goalModeTitle}>
              {raceOption?.label ?? 'Wedstrijd of evenement'}
            </Text>
            <Text style={styles.availableBadge}>Beschikbaar</Text>
          </View>
          <Text style={styles.goalModeDescription}>
            Verplichte racedatum; de trainingscyclus wordt vanaf die datum
            teruggerekend.
          </Text>
        </Pressable>
        <Pressable
          accessibilityHint="Toont persoonlijke doelen die nog niet beschikbaar zijn"
          accessibilityRole="radio"
          accessibilityState={{ selected: selectedKind === 'personal_goal' }}
          onPress={() => setSelectedKind('personal_goal')}
          style={({ pressed }) => [
            styles.goalModeCard,
            selectedKind === 'personal_goal' && styles.goalModeCardSelected,
            pressed && styles.actionPressed,
          ]}
        >
          <View style={styles.goalModeHeading}>
            <View
              style={[
                styles.goalModeRadio,
                selectedKind === 'personal_goal' &&
                  styles.goalModeRadioSelected,
              ]}
            />
            <Text style={styles.goalModeTitle}>Persoonlijk doel</Text>
            <Text style={styles.comingLaterBadge}>Komt later</Text>
          </View>
          <Text style={styles.goalModeDescription}>
            Begint bij cyclusweek 1 en krijgt eigen doelregels zodra die zijn
            beoordeeld.
          </Text>
        </Pressable>
      </View>
      {selectedKind === 'race_event' ? (
        <>
          <View style={styles.form}>
            <Text style={styles.cardTitle}>Type wedstrijd</Text>
            <View style={styles.goalModeList}>
              {(
                [
                  ['run', 'Lopen'],
                  ['bike', 'Fietsen'],
                  ['swim', 'Zwemmen'],
                  ['triathlon', 'Triatlon'],
                  ['duathlon', 'Duatlon'],
                ] as const
              ).map(([value, label]) => (
                <Pressable
                  accessibilityRole="radio"
                  accessibilityState={{ selected: raceType === value }}
                  key={value}
                  onPress={() => setRaceType(value)}
                  style={[
                    styles.goalModeCard,
                    raceType === value && styles.goalModeCardSelected,
                  ]}
                >
                  <Text style={styles.goalModeTitle}>{label}</Text>
                </Pressable>
              ))}
            </View>
            <FormField
              label="Naam van de race"
              onChangeText={setRaceName}
              placeholder="Amsterdam Olympic Triathlon"
              value={raceName}
            />
            <FormField
              autoCapitalize="none"
              hint={
                targetDate && !normalizedTargetDate
                  ? 'Gebruik een toekomstige datum: JJJJ-MM-DD'
                  : 'JJJJ-MM-DD'
              }
              inputMode="numeric"
              label="Racedatum"
              maxLength={10}
              onChangeText={(value) =>
                setTargetDate(formatIsoDateInput(value))
              }
              placeholder="2027-06-15"
              value={targetDate}
            />
            {disciplines.map((discipline) => (
              <View key={discipline} style={styles.disciplineCard}>
                <Text style={styles.cardTitle}>
                  {discipline === 'swim'
                    ? 'Zwemmen'
                    : discipline === 'bike'
                      ? 'Fietsen'
                      : 'Lopen'}
                </Text>
                <FormField
                  inputMode="numeric"
                  label="Afstand"
                  onChangeText={(value) =>
                    setDistances((current) => ({
                      ...current,
                      [discipline]: value,
                    }))
                  }
                  placeholder={discipline === 'swim' ? '1500' : '10000'}
                  suffix={<Text style={styles.unit}>meter</Text>}
                  value={distances[discipline]}
                />
                <FormField
                  hint="Optioneel, formaat U:MM:SS"
                  label="Richttijd onderdeel"
                  onChangeText={(value) =>
                    setDisciplineTimes((current) => ({
                      ...current,
                      [discipline]: value,
                    }))
                  }
                  placeholder="0:45:00"
                  value={disciplineTimes[discipline]}
                />
              </View>
            ))}
            <FormField
              hint="Verplicht, formaat U:MM:SS"
              label="Totale richttijd"
              onChangeText={setTotalTime}
              placeholder="3:00:00"
              value={totalTime}
            />
            <FormField
              label="Specifieke focus (optioneel)"
              multiline
              onChangeText={setSpecificFocus}
              placeholder="Bijvoorbeeld: extra aandacht voor het zwemonderdeel."
              style={styles.multiline}
              value={specificFocus}
            />
          </View>
          <ActionButton
            disabled={!valid}
            label="A-doel opslaan"
            loading={saving}
            onPress={() =>
              void onSave({
                race_type: raceType,
                race_name: raceName.trim(),
                race_date: normalizedTargetDate!,
                ...Object.fromEntries(
                  disciplines.map((discipline) => [
                    `${discipline}_distance_meters`,
                    parsedDistances[discipline],
                  ]),
                ),
                total_target_time_seconds: parsedTotalTime!,
                ...Object.fromEntries(
                  disciplines
                    .filter(
                      (discipline) =>
                        parsedDisciplineTimes[discipline] !== undefined,
                    )
                    .map((discipline) => [
                      `${discipline}_target_time_seconds`,
                      parsedDisciplineTimes[discipline],
                    ]),
                ),
                ...(specificFocus.trim()
                  ? { specific_focus: specificFocus.trim() }
                  : {}),
              })
            }
          />
        </>
      ) : null}
      {selectedKind === 'personal_goal' ? (
        <View style={styles.personalGoalsPanel}>
          <Text style={styles.personalGoalsTitle}>
            Persoonlijke planningsmodi komen later
          </Text>
          <Text style={styles.personalGoalsText}>
            De deterministische macrocycli, intensiteitsdoelen en herstelregels
            zijn nog niet beoordeeld. Daarom kan Wombo deze doelen nog niet
            opslaan of als wedstrijdplan behandelen.
          </Text>
          <View style={styles.personalGoalList}>
            {personalOptions.map((option) => (
              <View key={option.goal_family} style={styles.personalGoalRow}>
                <Text style={styles.personalGoalLabel}>{option.label}</Text>
                <Text style={styles.comingLaterBadge}>Komt later</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}
    </StepFrame>
  );
}

const metricConfiguration: Record<
  Discipline,
  { kind: string; label: string; unit: string; descending: boolean }
> = {
  swim: {
    kind: 'swim_css_seconds_per_100m',
    label: 'CSS',
    unit: 'sec/100m',
    descending: true,
  },
  bike: {
    kind: 'bike_ftp_watts',
    label: 'FTP',
    unit: 'watt',
    descending: false,
  },
  run: {
    kind: 'run_lthr_bpm',
    label: 'LTHR',
    unit: 'bpm',
    descending: false,
  },
};

type ReviewStepProps = {
  state: OnboardingState;
  saving: boolean;
  onComplete: () => Promise<void>;
  onApproveZone: (
    proposalId: string,
    baseZoneProfileId: string | null,
  ) => Promise<void>;
  onRejectZone: (proposalId: string) => Promise<void>;
};

function ReviewStep({
  state,
  saving,
  onComplete,
  onApproveZone,
  onRejectZone,
}: ReviewStepProps) {
  const pendingZones = state.zones.filter(
    (zone) => zone.status === 'pending' && zone.proposal_id !== null,
  );
  return (
    <StepFrame
      description="Afronden maakt geen trainingsplan actief. Het zet alleen een planningsverzoek klaar voor de volgende fase."
      eyebrow="Stap 7 van 7"
      title="Klaar voor je eerste voorstel"
    >
      <View style={styles.reviewCard}>
        <ReviewRow
          label="Profiel"
          value={state.profile?.timezone ?? 'Ontbreekt'}
        />
        <ReviewRow
          label="Historie"
          value={`${state.training_history.length}/3 disciplines`}
        />
        <ReviewRow
          label="A-doel"
          value={state.primary_goal?.race_name ?? 'Ontbreekt'}
        />
        <ReviewRow
          label="Actieve zones"
          value={`${
            new Set(
              state.zones
                .filter((zone) => zone.status === 'active')
                .map((zone) => zone.discipline),
            ).size
          }/3 disciplines`}
        />
      </View>
      {pendingZones.map((zone) => (
        <View key={zone.id} style={styles.approvalNotice}>
          <Text style={styles.approvalTitle}>
            Zonevoorstel {zone.discipline}
          </Text>
          <Text style={styles.approvalText}>
            {zone.metric_profiles.length > 1
              ? `${zone.metric_profiles.length} metrische representaties`
              : zone.metric?.metric_kind ?? 'Berekende zones'}{' '}
            volgens {zone.zone_model_version}. De huidige zones veranderen pas
            na jouw bevestiging.
          </Text>
          <ActionButton
            disabled={saving}
            label="Zones bevestigen"
            onPress={() =>
              void onApproveZone(
                zone.proposal_id!,
                zone.base_zone_profile_id,
              )
            }
          />
          <ActionButton
            disabled={saving}
            label="Zonevoorstel afwijzen"
            onPress={() => void onRejectZone(zone.proposal_id!)}
            secondary
          />
        </View>
      ))}
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>Jij houdt de controle</Text>
        <Text style={styles.approvalText}>
          Ook het toekomstige weekplan wordt eerst als voorstel getoond. Er
          verandert niets zonder een aparte goedkeuring.
        </Text>
      </View>
      <ActionButton
        disabled={!state.can_complete}
        label="Onboarding afronden"
        loading={saving}
        onPress={() => void onComplete()}
      />
    </StepFrame>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value}</Text>
    </View>
  );
}

function CompletedStep({
  state,
  onOpenPlanning,
  onSignOut,
}: {
  state: OnboardingState;
  onOpenPlanning: () => void;
  onSignOut: () => Promise<void>;
}) {
  return (
    <View style={styles.completed}>
      <View style={styles.completedMark}>
        <Text style={styles.completedMarkText}>✓</Text>
      </View>
      <Text style={styles.completedTitle}>Je basis staat.</Text>
      <Text style={styles.completedText}>
        Het eerste planningsverzoek staat in afwachting. Een trainingsplan wordt
        pas in de planningsfase opgebouwd en blijft daarna een voorstel.
      </Text>
      <View style={styles.requestCard}>
        <StatusPill label="In afwachting" tone="brand" />
        <Text style={styles.requestLabel}>Planningsverzoek</Text>
        <Text numberOfLines={1} style={styles.requestId}>
          {state.initial_plan_request_id}
        </Text>
      </View>
      <ActionButton label="Naar je weekplanning" onPress={onOpenPlanning} />
      <ActionButton
        label="Afmelden"
        onPress={() => void onSignOut()}
        secondary
      />
    </View>
  );
}

export function OnboardingScreen({
  accessToken,
  onOpenCalibration,
  onOpenPlanning,
  onSignOut,
}: OnboardingScreenProps) {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [goalOptions, setGoalOptions] = useState<GoalPlanningOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [next, nextGoalOptions] = await Promise.all([
      getOnboarding(accessToken),
      getGoalPlanningOptions(accessToken),
    ]);
    setState(next);
    setGoalOptions(nextGoalOptions);
  }, [accessToken]);

  const retryLoad = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await reload();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Onboarding laden is niet gelukt.',
      );
    } finally {
      setLoading(false);
    }
  }, [reload]);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      getOnboarding(accessToken),
      getGoalPlanningOptions(accessToken),
    ])
      .then(([next, nextGoalOptions]) => {
        if (mounted) {
          setState(next);
          setGoalOptions(nextGoalOptions);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error
              ? caught.message
              : 'Onboarding laden is niet gelukt.',
          );
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  const mutate = async (operation: () => Promise<unknown>) => {
    setSaving(true);
    setError(null);
    try {
      await operation();
      await reload();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Opslaan is niet gelukt.',
      );
    } finally {
      setSaving(false);
    }
  };

  const completed = useMemo(
    () => new Set(state?.completed_steps ?? []),
    [state?.completed_steps],
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={colors.brand} size="large" />
        <Text style={styles.loadingText}>Je intake wordt hervat…</Text>
      </SafeAreaView>
    );
  }

  if (!state) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.errorTitle}>We kunnen je intake niet laden.</Text>
        {error ? <Text style={styles.centeredError}>{error}</Text> : null}
        <ActionButton
          label="Opnieuw proberen"
          onPress={() => void retryLoad()}
        />
        <ActionButton
          label="Afmelden"
          onPress={() => void onSignOut()}
          secondary
        />
      </SafeAreaView>
    );
  }

  const step = state.current_step;
  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboard}
      >
        <View style={styles.header}>
          <View style={styles.brandLockup}>
            <View style={styles.logoMark}>
              <Text style={styles.logoMarkText}>23</Text>
            </View>
            <View>
              <Text style={styles.logo}>Wombo</Text>
              <Text style={styles.headerCaption}>Jouw profiel</Text>
            </View>
          </View>
          <View style={styles.headerActions}>
            {state.discipline_setups.some((setup) => setup.protocol_id) ? (
              <Pressable
                accessibilityRole="button"
                onPress={onOpenCalibration}
                style={styles.signOut}
              >
                <Text style={styles.signOutText}>Testen</Text>
              </Pressable>
            ) : null}
            <Pressable
              accessibilityRole="button"
              onPress={() => void onSignOut()}
              style={styles.signOut}
            >
              <Text style={styles.signOutText}>Afmelden</Text>
            </Pressable>
          </View>
        </View>

        {state.upgrade_required ? (
          <View accessibilityRole="alert" style={styles.upgradeBanner}>
            <Text style={styles.upgradeBannerTitle}>Werk je onboarding bij</Text>
            <Text style={styles.upgradeBannerText}>
              Je eerdere afronding blijft bewaard. Alleen deze onderdelen zijn nog
              nodig voor {state.current_onboarding_version}:{' '}
              {state.missing_upgrade_steps.length
                ? state.missing_upgrade_steps
                    .map(
                      (missing) =>
                        stepLabels.find((item) => item.step === missing)?.label ??
                        missing,
                    )
                    .join(', ')
                : 'controle en bevestiging'}.
            </Text>
          </View>
        ) : null}

        {step !== 'completed' ? (
          <FadeInView delay={80} distance={8} style={styles.progress}>
            {stepLabels.map((item) => (
              <View key={item.step} style={styles.progressItem}>
                <View
                  style={[
                    styles.progressDot,
                    (completed.has(item.step) || step === item.step) &&
                      styles.progressDotActive,
                  ]}
                />
                <Text
                  numberOfLines={1}
                  style={[
                    styles.progressLabel,
                    step === item.step && styles.progressLabelActive,
                  ]}
                >
                  {item.label}
                </Text>
              </View>
            ))}
          </FadeInView>
        ) : null}

        <ScrollView
          automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}
          contentContainerStyle={styles.scrollContent}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          style={styles.scroll}
        >
          {error ? <Text style={styles.errorBanner}>{error}</Text> : null}

          {step === 'profile' ? (
            <ProfileStep
              key={state.profile?.revision ?? 0}
              onSave={(input) =>
                mutate(() => saveProfile(accessToken, input))
              }
              profile={state.profile}
              saving={saving}
            />
          ) : null}
          {step === 'heart_rate_monitor' ? (
            <HeartRateMonitorStep
              onSave={() =>
                mutate(() =>
                  saveOperationalProfile(accessToken, {
                    heart_rate_monitor_confirmed: true,
                  }),
                )
              }
              saving={saving}
            />
          ) : null}
          {step === 'timezone' ? (
            <TimezoneStep
              onSave={(timezone, source) =>
                mutate(() =>
                  saveOperationalProfile(accessToken, {
                    timezone,
                    timezone_source: source,
                    timezone_confirmed: true,
                  }),
                )
              }
              profile={state.profile}
              saving={saving}
            />
          ) : null}
          {step === 'history' ? (
            <HistoryStep
              key={state.training_history
                .map((entry) => entry.updated_at)
                .join(':')}
              onSave={(values) =>
                mutate(() =>
                  saveTrainingHistory(
                    accessToken,
                    (['swim', 'bike', 'run'] as const).map((discipline) => ({
                      discipline,
                      average_hours_per_week: values[discipline].replace(',', '.'),
                    })),
                  ),
                )
              }
              saving={saving}
              state={state}
            />
          ) : null}
          {step === 'goal' ? (
            <GoalStep
              goal={state.primary_goal}
              key={state.primary_goal?.revision ?? 0}
              options={goalOptions}
              onSave={(input) =>
                mutate(() =>
                  savePrimaryGoal(
                    accessToken,
                    input,
                    state.primary_goal?.id,
                  ),
                )
              }
              saving={saving}
            />
          ) : null}
          {step === 'zones' ? (
            <ZoneSetupStep
              accessToken={accessToken}
              key={[
                ...state.zones.map((zone) => `${zone.id}:${zone.status}`),
                ...state.discipline_setups.map(
                  (setup) => `${setup.discipline}:${setup.revision}`,
                ),
              ].join(':')}
              onSave={(discipline, input: DisciplineSetupInput) =>
                mutate(async () => {
                  if (input.setup_route === 'known_values') {
                    await saveCalculatedZones(accessToken, discipline, {
                      thresholds: input.thresholds,
                      source_quality: input.source_quality,
                      boundary_overrides: input.zone_profiles,
                    });
                  }
                  await saveDisciplineSetup(accessToken, discipline, input);
                })
              }
              saving={saving}
              state={state}
            />
          ) : null}
          {step === 'review' ? (
            <ReviewStep
              onApproveZone={(proposalId, baseZoneProfileId) =>
                mutate(() =>
                  approveZoneProposal(
                    accessToken,
                    proposalId,
                    baseZoneProfileId,
                  ),
                )
              }
              onComplete={() =>
                mutate(() =>
                  completeOnboarding(accessToken, state.onboarding_revision),
                )
              }
              onRejectZone={(proposalId) =>
                mutate(() => rejectZoneProposal(accessToken, proposalId))
              }
              saving={saving}
              state={state}
            />
          ) : null}
          {step === 'completed' ? (
            <CompletedStep
              onOpenPlanning={onOpenPlanning}
              onSignOut={onSignOut}
              state={state}
            />
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.canvas,
    flex: 1,
  },
  keyboard: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  centered: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    flex: 1,
    gap: spacing.md,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  loadingText: {
    color: colors.inkMuted,
    fontSize: 14,
  },
  errorTitle: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'center',
  },
  centeredError: {
    color: colors.danger,
    lineHeight: 20,
    textAlign: 'center',
  },
  header: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    paddingTop: spacing.sm,
  },
  brandLockup: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  logoMark: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.sm,
    height: 38,
    justifyContent: 'center',
    transform: [{ rotate: '-4deg' }],
    width: 38,
  },
  logoMarkText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '900',
  },
  logo: {
    color: colors.brand,
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
  headerCaption: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '700',
    marginTop: 2,
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
  },
  signOut: {
    borderRadius: radius.pill,
    padding: spacing.sm,
  },
  signOutText: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  progress: {
    alignSelf: 'center',
    flexDirection: 'row',
    gap: spacing.xs,
    maxWidth: 720,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    width: '100%',
  },
  progressItem: {
    flex: 1,
    gap: spacing.xs,
  },
  progressDot: {
    backgroundColor: colors.line,
    borderRadius: radius.pill,
    height: 5,
  },
  progressDotActive: {
    backgroundColor: colors.accent,
  },
  progressLabel: {
    color: colors.inkFaint,
    fontSize: 9,
    fontWeight: '700',
  },
  progressLabelActive: {
    color: colors.ink,
  },
  scrollContent: {
    alignSelf: 'center',
    maxWidth: 720,
    padding: spacing.lg,
    paddingBottom: 80,
    width: '100%',
  },
  errorBanner: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.sm,
    color: colors.danger,
    fontSize: 13,
    lineHeight: 19,
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  upgradeBanner: {
    backgroundColor: colors.surface,
    borderColor: colors.brand,
    borderRadius: radius.md,
    borderWidth: 1,
    marginHorizontal: spacing.lg,
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  upgradeBannerTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '700',
  },
  upgradeBannerText: {
    color: colors.inkMuted,
    lineHeight: 20,
    marginTop: spacing.xs,
  },
  fieldError: {
    color: colors.danger,
    fontSize: 12,
    lineHeight: 17,
  },
  step: {
    gap: spacing.lg,
  },
  stepHero: {
    paddingHorizontal: spacing.xs,
  },
  eyebrowRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  eyebrowMark: {
    backgroundColor: colors.accent,
    borderRadius: radius.pill,
    height: 7,
    width: 7,
  },
  eyebrow: {
    color: colors.accent,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  stepTitle: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: '900',
    letterSpacing: -1,
    marginTop: spacing.xs,
  },
  description: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: spacing.sm,
    maxWidth: 580,
  },
  stepCard: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.white,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.lg,
    padding: spacing.lg,
  },
  form: {
    gap: spacing.md,
  },
  twoColumns: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  column: {
    flex: 1,
  },
  unit: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '700',
  },
  multiline: {
    minHeight: 92,
    textAlignVertical: 'top',
  },
  goalModeList: {
    gap: spacing.sm,
  },
  goalModeCard: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  goalModeCardSelected: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
  },
  goalModeHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  goalModeRadio: {
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 2,
    height: 20,
    width: 20,
  },
  goalModeRadioSelected: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    borderWidth: 5,
  },
  goalModeTitle: {
    color: colors.ink,
    flex: 1,
    fontSize: 15,
    fontWeight: '800',
  },
  goalModeDescription: {
    color: colors.inkMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  availableBadge: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    color: colors.success,
    fontSize: 10,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  comingLaterBadge: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.pill,
    color: colors.danger,
    fontSize: 10,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  personalGoalsPanel: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  personalGoalsTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '800',
  },
  personalGoalsText: {
    color: colors.inkMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  personalGoalList: {
    gap: spacing.xs,
  },
  personalGoalRow: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    flexDirection: 'row',
    gap: spacing.sm,
    justifyContent: 'space-between',
    padding: spacing.sm,
  },
  personalGoalLabel: {
    color: colors.ink,
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
  },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    borderRadius: radius.pill,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 52,
    paddingHorizontal: spacing.lg,
    ...shadows.card,
  },
  actionSecondary: {
    backgroundColor: colors.surface,
  },
  actionDisabled: {
    opacity: 0.4,
  },
  actionPressed: {
    opacity: 0.8,
  },
  actionText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '800',
  },
  actionTextSecondary: {
    color: colors.brand,
  },
  disciplineCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.md,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '800',
  },
  zoneProgress: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  zoneRouteList: {
    gap: spacing.sm,
  },
  zoneRouteCard: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  zoneRouteCardSelected: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.brand,
  },
  zoneRouteHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  zoneRouteTitle: {
    color: colors.ink,
    flex: 1,
    fontSize: 15,
    fontWeight: '800',
  },
  zoneRouteDescription: {
    color: colors.inkMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  zoneRouteRadio: {
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 2,
    height: 20,
    width: 20,
  },
  zoneRouteRadioSelected: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    borderWidth: 5,
  },
  routeExplanation: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.md,
  },
  routeExplanationTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '800',
  },
  routeExplanationText: {
    color: colors.inkMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  routeUnavailableCard: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.md,
  },
  routeUnavailableText: {
    color: colors.ink,
    fontSize: 13,
    lineHeight: 19,
  },
  boundaryHeader: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.xs,
  },
  boundaryTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
  },
  boundaryHint: {
    color: colors.inkMuted,
    fontSize: 10,
  },
  boundaryRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  zoneNumber: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radius.sm,
    height: 42,
    justifyContent: 'center',
    marginTop: 20,
    width: 42,
  },
  zoneNumberText: {
    color: colors.brand,
    fontSize: 13,
    fontWeight: '900',
  },
  boundaryInput: {
    flex: 1,
  },
  fallbackCard: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.md,
  },
  fallbackText: {
    color: colors.ink,
    fontSize: 13,
    lineHeight: 19,
  },
  reviewCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  reviewRow: {
    alignItems: 'center',
    borderBottomColor: colors.line,
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: spacing.md,
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
  },
  reviewLabel: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  reviewValue: {
    color: colors.ink,
    flex: 1,
    fontSize: 13,
    fontWeight: '800',
    textAlign: 'right',
  },
  approvalNotice: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.md,
  },
  approvalTitle: {
    color: colors.brand,
    fontSize: 15,
    fontWeight: '900',
  },
  approvalText: {
    color: colors.brand,
    fontSize: 13,
    lineHeight: 19,
  },
  completed: {
    alignItems: 'center',
    gap: spacing.lg,
    paddingTop: 48,
  },
  completedMark: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    height: 72,
    justifyContent: 'center',
    width: 72,
  },
  completedMarkText: {
    color: colors.white,
    fontSize: 32,
    fontWeight: '900',
  },
  completedTitle: {
    color: colors.ink,
    fontSize: 32,
    fontWeight: '900',
    letterSpacing: -1,
  },
  completedText: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 22,
    maxWidth: 350,
    textAlign: 'center',
  },
  requestCard: {
    alignItems: 'center',
    alignSelf: 'stretch',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  requestLabel: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '800',
  },
  requestId: {
    color: colors.inkMuted,
    fontSize: 11,
  },
});
