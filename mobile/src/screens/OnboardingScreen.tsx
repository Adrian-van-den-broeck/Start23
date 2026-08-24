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
  approveZoneProposal,
  completeOnboarding,
  getOnboarding,
  rejectZoneProposal,
  saveCalculatedZones,
  saveDisciplineSetup,
  savePrimaryGoal,
  saveProfile,
  saveTrainingHistory,
} from '../api/client';
import type {
  AthleteProfile,
  Discipline,
  DisciplineSetupInput,
  OnboardingState,
  OnboardingStep,
  PrimaryRaceGoal,
  ZoneBoundary,
} from '../api/types';
import { FormField } from '../components/FormField';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';
import { ZoneSetupStep } from './ZoneSetupStep';

const stepLabels: Array<{ step: OnboardingStep; label: string }> = [
  { step: 'profile', label: 'Profiel' },
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
    <View style={styles.step}>
      <View>
        <Text style={styles.eyebrow}>{eyebrow}</Text>
        <Text style={styles.stepTitle}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      {children}
    </View>
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
    date_of_birth: string;
    height_cm: string;
    weight_kg: string;
    resting_heart_rate_bpm: number;
    motivation_text: string;
    motivation_tag?: string;
    timezone: string;
  }) => Promise<void>;
};

function ProfileStep({ profile, saving, onSave }: ProfileStepProps) {
  const [dateOfBirth, setDateOfBirth] = useState(profile?.date_of_birth ?? '');
  const [height, setHeight] = useState(profile?.height_cm ?? '');
  const [weight, setWeight] = useState(profile?.weight_kg ?? '');
  const [restingHeartRate, setRestingHeartRate] = useState(
    profile?.resting_heart_rate_bpm?.toString() ?? '',
  );
  const [motivation, setMotivation] = useState(
    profile?.motivation_text ?? '',
  );
  const [motivationTag, setMotivationTag] = useState(
    profile?.motivation_tag ?? '',
  );
  const [timezone, setTimezone] = useState(
    profile?.timezone ?? 'Europe/Amsterdam',
  );
  const valid =
    Boolean(dateOfBirth && motivation && timezone) &&
    Number(height) > 0 &&
    Number(weight) > 0 &&
    Number(restingHeartRate) > 0;

  return (
    <StepFrame
      description="Deze gegevens ondersteunen alleen goedgekeurde, deterministische berekeningen. Er worden geen medische grenzen afgedwongen."
      eyebrow="Stap 1 van 5"
      title="Jouw basis"
    >
      <View style={styles.form}>
        <FormField
          hint="Gebruik JJJJ-MM-DD."
          inputMode="numeric"
          label="Geboortedatum"
          onChangeText={setDateOfBirth}
          placeholder="1990-05-20"
          value={dateOfBirth}
        />
        <View style={styles.twoColumns}>
          <View style={styles.column}>
            <FormField
              inputMode="decimal"
              label="Lengte"
              onChangeText={setHeight}
              placeholder="181"
              suffix={<Text style={styles.unit}>cm</Text>}
              value={height}
            />
          </View>
          <View style={styles.column}>
            <FormField
              inputMode="decimal"
              label="Gewicht"
              onChangeText={setWeight}
              placeholder="74"
              suffix={<Text style={styles.unit}>kg</Text>}
              value={weight}
            />
          </View>
        </View>
        <FormField
          inputMode="numeric"
          label="Rusthartslag"
          onChangeText={setRestingHeartRate}
          placeholder="52"
          suffix={<Text style={styles.unit}>bpm</Text>}
          value={restingHeartRate}
        />
        <FormField
          label="Wat wil je bereiken?"
          multiline
          onChangeText={setMotivation}
          placeholder="Vertel kort waarom je traint."
          style={styles.multiline}
          value={motivation}
        />
        <FormField
          label="Motivatielabel (optioneel)"
          onChangeText={setMotivationTag}
          placeholder="eerste-race"
          value={motivationTag}
        />
        <FormField
          hint="IANA-tijdzone voor correcte lokale trainingsweken."
          label="Tijdzone"
          onChangeText={setTimezone}
          placeholder="Europe/Amsterdam"
          value={timezone}
        />
      </View>
      <ActionButton
        disabled={!valid}
        label="Profiel opslaan"
        loading={saving}
        onPress={() =>
          void onSave({
            date_of_birth: dateOfBirth,
            height_cm: height,
            weight_kg: weight,
            resting_heart_rate_bpm: Number(restingHeartRate),
            motivation_text: motivation,
            ...(motivationTag ? { motivation_tag: motivationTag } : {}),
            timezone,
          })
        }
      />
    </StepFrame>
  );
}

type HistoryStepProps = {
  state: OnboardingState;
  saving: boolean;
  onSave: (
    values: Record<
      Discipline,
      { weeklyMinutes: string; experienceYears: string }
    >,
  ) => Promise<void>;
};

function HistoryStep({ state, saving, onSave }: HistoryStepProps) {
  const initial = (discipline: Discipline, key: 'minutes' | 'years') => {
    const entry = state.training_history.find(
      (history) => history.discipline === discipline,
    );
    return key === 'minutes'
      ? entry?.weekly_minutes.toString() ?? ''
      : entry?.experience_years ?? '';
  };
  const [values, setValues] = useState<
    Record<
      Discipline,
      { weeklyMinutes: string; experienceYears: string }
    >
  >({
    swim: {
      weeklyMinutes: initial('swim', 'minutes'),
      experienceYears: initial('swim', 'years'),
    },
    bike: {
      weeklyMinutes: initial('bike', 'minutes'),
      experienceYears: initial('bike', 'years'),
    },
    run: {
      weeklyMinutes: initial('run', 'minutes'),
      experienceYears: initial('run', 'years'),
    },
  });
  const update = (
    discipline: Discipline,
    key: 'weeklyMinutes' | 'experienceYears',
    value: string,
  ) => {
    setValues((current) => ({
      ...current,
      [discipline]: { ...current[discipline], [key]: value },
    }));
  };
  const valid = (Object.keys(values) as Discipline[]).every(
    (discipline) =>
      Number(values[discipline].weeklyMinutes) >= 0 &&
      Number(values[discipline].experienceYears) >= 0 &&
      values[discipline].weeklyMinutes !== '' &&
      values[discipline].experienceYears !== '',
  );

  return (
    <StepFrame
      description="Vul een normale trainingsweek in. Minuten mogen nul zijn als een discipline nieuw voor je is."
      eyebrow="Stap 2 van 5"
      title="Waar sta je nu?"
    >
      <View style={styles.form}>
        {(['swim', 'bike', 'run'] as const).map((discipline) => (
          <View key={discipline} style={styles.disciplineCard}>
            <Text style={styles.cardTitle}>
              {discipline === 'swim'
                ? 'Zwemmen'
                : discipline === 'bike'
                  ? 'Fietsen'
                  : 'Hardlopen'}
            </Text>
            <View style={styles.twoColumns}>
              <View style={styles.column}>
                <FormField
                  inputMode="numeric"
                  label="Per week"
                  onChangeText={(value) =>
                    update(discipline, 'weeklyMinutes', value)
                  }
                  placeholder="90"
                  suffix={<Text style={styles.unit}>min</Text>}
                  value={values[discipline].weeklyMinutes}
                />
              </View>
              <View style={styles.column}>
                <FormField
                  inputMode="decimal"
                  label="Ervaring"
                  onChangeText={(value) =>
                    update(discipline, 'experienceYears', value)
                  }
                  placeholder="2"
                  suffix={<Text style={styles.unit}>jaar</Text>}
                  value={values[discipline].experienceYears}
                />
              </View>
            </View>
          </View>
        ))}
      </View>
      <ActionButton
        disabled={!valid}
        label="Trainingshistorie opslaan"
        loading={saving}
        onPress={() => void onSave(values)}
      />
    </StepFrame>
  );
}

type GoalStepProps = {
  goal: PrimaryRaceGoal | null;
  saving: boolean;
  onSave: (input: {
    title: string;
    specific_description: string;
    measurable_outcome: string;
    feasibility_score: number;
    target_date: string;
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

function GoalStep({ goal, saving, onSave }: GoalStepProps) {
  const [title, setTitle] = useState(goal?.title ?? '');
  const [description, setDescription] = useState(
    goal?.specific_description ?? '',
  );
  const [outcome, setOutcome] = useState(goal?.measurable_outcome ?? '');
  const [feasibility, setFeasibility] = useState(
    goal?.feasibility_score.toString() ?? '',
  );
  const [targetDate, setTargetDate] = useState(goal?.target_date ?? '');
  const normalizedTargetDate = normalizeRaceDate(targetDate);
  const valid =
    Boolean(title && description && outcome && normalizedTargetDate) &&
    Number(feasibility) >= 1 &&
    Number(feasibility) <= 10;

  return (
    <StepFrame
      description="De MVP gebruikt één actieve, racegerichte A-doelstelling voor zwemmen, fietsen en lopen."
      eyebrow="Stap 3 van 5"
      title="Kies je A-race"
    >
      <View style={styles.form}>
        <FormField
          label="Naam van de race"
          onChangeText={setTitle}
          placeholder="Amsterdam Olympic Triathlon"
          value={title}
        />
        <FormField
          label="Specifiek doel"
          multiline
          onChangeText={setDescription}
          placeholder="Ik wil gecontroleerd finishen en gelijkmatig lopen."
          style={styles.multiline}
          value={description}
        />
        <FormField
          label="Meetbaar resultaat"
          onChangeText={setOutcome}
          placeholder="Alle drie onderdelen voltooien."
          value={outcome}
        />
        <View style={styles.twoColumns}>
          <View style={styles.column}>
            <FormField
              hint="1 tot en met 10"
              inputMode="numeric"
              label="Haalbaarheid"
              onChangeText={setFeasibility}
              placeholder="8"
              value={feasibility}
            />
          </View>
          <View style={styles.column}>
            <FormField
              autoCapitalize="none"
              hint={
                targetDate && !normalizedTargetDate
                  ? 'Gebruik een toekomstige datum: JJJJ-MM-DD'
                  : 'JJJJ-MM-DD'
              }
              label="Racedatum"
              onChangeText={setTargetDate}
              placeholder="2027-06-15"
              value={targetDate}
            />
          </View>
        </View>
      </View>
      <ActionButton
        disabled={!valid}
        label="A-doel opslaan"
        loading={saving}
        onPress={() =>
          void onSave({
            title,
            specific_description: description,
            measurable_outcome: outcome,
            feasibility_score: Number(feasibility),
            target_date: normalizedTargetDate!,
          })
        }
      />
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

type ZonesStepProps = {
  state: OnboardingState;
  saving: boolean;
  onManual: (
    discipline: Discipline,
    metricKind: string,
    metricValue: string,
    boundaries: ZoneBoundary[],
  ) => Promise<void>;
  onFallback: (
    discipline: Exclude<Discipline, 'swim'>,
  ) => Promise<void>;
};

type ZoneSetupRoute = 'manual' | 'calibration' | 'fallback';

const zoneSetupRoutes: ReadonlyArray<{
  route: ZoneSetupRoute;
  piste: string;
  title: string;
  description: string;
}> = [
  {
    route: 'manual',
    piste: 'Piste A',
    title: 'Ik ken mijn waarden',
    description:
      'Vul je drempelwaarde en vijf bestaande zonegrenzen zelf in.',
  },
  {
    route: 'calibration',
    piste: 'Piste B',
    title: 'Automatisch kalibreren',
    description:
      'Laat Start23 een veilige test- of kalibratietraining in je schema opnemen.',
  },
  {
    route: 'fallback',
    piste: 'Piste C',
    title: 'Biometrische fallback',
    description:
      'Start tijdelijk met geschatte hartslagzones op basis van je profiel.',
  },
];

function ZonesStep({
  state,
  saving,
  onManual,
  onFallback,
}: ZonesStepProps) {
  const active = new Set(
    state.zones
      .filter((zone) => zone.status === 'active')
      .map((zone) => zone.discipline),
  );
  const discipline =
    (['swim', 'bike', 'run'] as const).find((item) => !active.has(item)) ??
    'run';
  const config = metricConfiguration[discipline];
  const [setupRoute, setSetupRoute] = useState<ZoneSetupRoute | null>(null);
  const [metricValue, setMetricValue] = useState('');
  const [boundaries, setBoundaries] = useState<ZoneBoundary[]>(
    Array.from({ length: 5 }, (_, index) => ({
      zone_number: index + 1,
      lower_value: '',
      upper_value: '',
    })),
  );
  const updateBoundary = (
    index: number,
    key: 'lower_value' | 'upper_value',
    value: string,
  ) => {
    setBoundaries((current) =>
      current.map((boundary, boundaryIndex) =>
        boundaryIndex === index ? { ...boundary, [key]: value } : boundary,
      ),
    );
  };
  const hasCompleteBoundaries = boundaries.every(
    (boundary) =>
      boundary.lower_value !== '' && boundary.upper_value !== '',
  );
  const rowsHavePositiveWidth = boundaries.every(
    (boundary) =>
      Number(boundary.lower_value) >= 0 &&
      Number(boundary.upper_value) > Number(boundary.lower_value),
  );
  const usesWholePaceSeconds =
    !config.descending ||
    (Number.isInteger(Number(metricValue)) &&
      boundaries.every(
        (boundary) =>
          Number.isInteger(Number(boundary.lower_value)) &&
          Number.isInteger(Number(boundary.upper_value)),
      ));
  const zonesAreContiguous = boundaries.slice(1).every((current, index) => {
    const previous = boundaries[index];
    return config.descending
      ? Number(previous.lower_value) === Number(current.upper_value)
      : Number(previous.upper_value) === Number(current.lower_value);
  });
  const valid =
    Number(metricValue) > 0 &&
    hasCompleteBoundaries &&
    rowsHavePositiveWidth &&
    usesWholePaceSeconds &&
    zonesAreContiguous;
  const boundaryValidationMessage = !hasCompleteBoundaries
    ? null
    : !rowsHavePositiveWidth
      ? 'Elke bovengrens moet numeriek groter zijn dan de ondergrens.'
      : !usesWholePaceSeconds
        ? 'Tempozones en CSS gebruiken alleen hele seconden.'
        : !zonesAreContiguous
          ? config.descending
            ? 'Bij tempo is Z1 het langzaamst. Laat de waarden dalen richting Z5: bijvoorbeeld Z1 120–140, Z2 110–120.'
            : 'Laat iedere zone aansluiten: de bovengrens van Z1 is de ondergrens van Z2, enzovoort.'
          : null;

  return (
    <StepFrame
      description="Kies per discipline hoe Start23 je trainingszones mag instellen. Een berekende wijziging wordt nooit automatisch actief."
      eyebrow="Stap 4 van 5"
      title={`Zones voor ${
        discipline === 'swim'
          ? 'zwemmen'
          : discipline === 'bike'
            ? 'fietsen'
            : 'hardlopen'
      }`}
    >
      <View style={styles.zoneProgress}>
        {(['swim', 'bike', 'run'] as const).map((item) => (
          <StatusPill
            key={item}
            label={`${active.has(item) ? '✓ ' : ''}${item}`}
            tone={active.has(item) ? 'brand' : 'neutral'}
          />
        ))}
      </View>

      <View accessibilityRole="radiogroup" style={styles.zoneRouteList}>
        {zoneSetupRoutes.map((option) => {
          const selected = setupRoute === option.route;
          return (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ checked: selected }}
              key={option.route}
              onPress={() => setSetupRoute(option.route)}
              style={({ pressed }) => [
                styles.zoneRouteCard,
                selected && styles.zoneRouteCardSelected,
                pressed && styles.actionPressed,
              ]}
            >
              <View style={styles.zoneRouteHeading}>
                <StatusPill
                  label={option.piste}
                  tone={selected ? 'brand' : 'neutral'}
                />
                <Text style={styles.zoneRouteTitle}>{option.title}</Text>
                <View
                  style={[
                    styles.zoneRouteRadio,
                    selected && styles.zoneRouteRadioSelected,
                  ]}
                />
              </View>
              <Text style={styles.zoneRouteDescription}>
                {option.description}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {setupRoute === 'manual' ? (
        <>
          <View style={styles.routeExplanation}>
            <Text style={styles.routeExplanationTitle}>
              Piste A · Handmatige invoer
            </Text>
            <Text style={styles.routeExplanationText}>
              Gebruik deze piste alleen wanneer je zowel je drempelwaarde als
              je vijf zonegrenzen kent.
            </Text>
          </View>

          <View style={styles.form}>
            <FormField
              hint={
                config.descending
                  ? 'Voor tempo betekent een lager getal een hogere intensiteit. Vul hele seconden in.'
                  : 'Waarden buiten toekomstige productranges worden beoordeeld, niet hard afgekeurd.'
              }
              inputMode="decimal"
              label={config.label}
              onChangeText={setMetricValue}
              placeholder="Drempelwaarde"
              suffix={<Text style={styles.unit}>{config.unit}</Text>}
              value={metricValue}
            />

            <View style={styles.boundaryHeader}>
              <Text style={styles.boundaryTitle}>Vijf aaneengesloten zones</Text>
              <Text style={styles.boundaryHint}>
                {config.descending
                  ? 'Z1 langzaam → Z5 snel'
                  : 'Z1 laag → Z5 hoog'}
              </Text>
            </View>
            {boundaries.map((boundary, index) => (
              <View key={boundary.zone_number} style={styles.boundaryRow}>
                <View style={styles.zoneNumber}>
                  <Text style={styles.zoneNumberText}>
                    Z{boundary.zone_number}
                  </Text>
                </View>
                <View style={styles.boundaryInput}>
                  <FormField
                    inputMode="decimal"
                    label="Onder"
                    onChangeText={(value) =>
                      updateBoundary(index, 'lower_value', value)
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
                      updateBoundary(index, 'upper_value', value)
                    }
                    placeholder="0"
                    value={boundary.upper_value}
                  />
                </View>
              </View>
            ))}
            {boundaryValidationMessage ? (
              <Text accessibilityLiveRegion="polite" style={styles.fieldError}>
                {boundaryValidationMessage}
              </Text>
            ) : null}
          </View>

          <ActionButton
            disabled={!valid}
            label="Handmatige zones bevestigen"
            loading={saving}
            onPress={() =>
              void onManual(
                discipline,
                config.kind,
                metricValue,
                boundaries,
              )
            }
          />
        </>
      ) : null}

      {setupRoute === 'calibration' ? (
        <View style={styles.routeUnavailableCard}>
          <StatusPill label="Piste B · Veilig geblokkeerd" tone="accent" />
          <Text style={styles.routeExplanationTitle}>
            Automatische kalibratie via je trainingsschema
          </Text>
          <Text style={styles.routeExplanationText}>
            Start23 zal hiervoor een gestandaardiseerde test- of
            kalibratietraining in je eerste trainingsweek plaatsen. Na je
            training worden meetgegevens en je gevoelsscore gebruikt voor een
            zonevoorstel dat je nog moet bevestigen.
          </Text>
          <Text style={styles.routeUnavailableText}>
            Deze route kan in deze build nog niet veilig worden opgeslagen: het
            beoordeelde protocol dat de test en gevoelsscore omzet naar
            {` ${config.label}`} en vijf zones ontbreekt nog. Er worden daarom
            geen waarden geschat of automatisch actief gemaakt.
          </Text>
          <ActionButton
            disabled
            label="Kalibratieroute nog niet beschikbaar"
            onPress={() => undefined}
          />
        </View>
      ) : null}

      {setupRoute === 'fallback' && discipline !== 'swim' ? (
        <View style={styles.fallbackCard}>
          <StatusPill label="Piste C · Geschatte fallback" tone="accent" />
          <Text style={styles.fallbackText}>
            Gebruik tijdelijk hartslagreserve-zones op basis van leeftijd en
            rusthartslag. Ze blijven zichtbaar als geschat en onbeoordeeld
            totdat je ze expliciet bevestigt of later laat testen.
          </Text>
          <ActionButton
            label="Tijdelijke fallback gebruiken"
            loading={saving}
            onPress={() => void onFallback(discipline)}
            secondary
          />
        </View>
      ) : null}

      {setupRoute === 'fallback' && discipline === 'swim' ? (
        <View style={styles.routeUnavailableCard}>
          <StatusPill label="Piste C · Niet voor CSS" tone="accent" />
          <Text style={styles.routeExplanationTitle}>
            Geen biometrische CSS-schatting
          </Text>
          <Text style={styles.routeUnavailableText}>
            Leeftijd en rusthartslag leveren geen betrouwbare zwem-CSS op.
            Kies voor zwemmen Piste A wanneer je je waarden kent, of Piste B
            zodra de beoordeelde kalibratieroute beschikbaar is.
          </Text>
        </View>
      ) : null}
    </StepFrame>
  );
}

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
      eyebrow="Stap 5 van 5"
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
          value={state.primary_goal?.title ?? 'Ontbreekt'}
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const next = await getOnboarding(accessToken);
    setState(next);
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
    getOnboarding(accessToken)
      .then((next) => {
        if (mounted) {
          setState(next);
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
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboard}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.logo}>Start23</Text>
            <Text style={styles.headerCaption}>Veilige intake</Text>
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

        {step !== 'completed' ? (
          <View style={styles.progress}>
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
          </View>
        ) : null}

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
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
                      weekly_minutes: Number(
                        values[discipline].weeklyMinutes,
                      ),
                      experience_years:
                        values[discipline].experienceYears,
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
              onSave={(input) =>
                mutate(() =>
                  savePrimaryGoal(
                    accessToken,
                    {
                      ...input,
                      race_discipline_profile: ['swim', 'bike', 'run'],
                    },
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
                mutate(() => completeOnboarding(accessToken))
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
  },
  logo: {
    color: colors.accent,
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
  headerCaption: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
  },
  signOut: {
    padding: spacing.sm,
  },
  signOutText: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  progress: {
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
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
    padding: spacing.lg,
    paddingBottom: 80,
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
  fieldError: {
    color: colors.danger,
    fontSize: 12,
    lineHeight: 17,
  },
  step: {
    gap: spacing.lg,
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
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    borderRadius: radius.pill,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 52,
    paddingHorizontal: spacing.lg,
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
    backgroundColor: colors.surface,
    borderColor: colors.line,
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
    borderColor: colors.line,
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
