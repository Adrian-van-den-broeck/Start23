import { useState, useRef } from 'react';
import { StyleSheet, View, type TextInput } from 'react-native';
import type { Discipline, GoalPlanningOption, PrimaryRaceGoal, RaceType } from '../../api/types';
import { DurationPicker } from '../../components/DurationPicker';
import { formatIsoDateInput } from '../../lib/dateInput';
import { parseRunPace } from '../../lib/runPace';
import { parsePositiveInteger, raceDisciplines } from '../../lib/onboardingForms';
import { FormComposition } from '../components/FormComposition';
import { Button } from '../primitives/Button';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Input, type InputProps } from '../primitives/Input';
import { Notice } from '../primitives/Notice';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space, typography } from '../tokens';

function GoalInput({ required = false, label, ...props }: InputProps & { required?: boolean }) {
  const optional = label.endsWith(' (optioneel)');
  return <Input {...props} optionalLabel={optional ? '(optioneel)' : undefined}
    label={(optional ? label.slice(0, -11) : label) + (required ? ' *' : '')} accessibilityLabel={props.accessibilityLabel ?? label} />;
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

export function GoalStep({ goal, options, saving, onSave }: GoalStepProps) {
  const nameRef = useRef<TextInput>(null);
  const dateRef = useRef<TextInput>(null);
  const paceRef = useRef<TextInput>(null);
  const totalRef = useRef<View>(null);
  const distanceRefs = { swim: useRef<TextInput>(null), bike: useRef<TextInput>(null), run: useRef<TextInput>(null) };
  const splitRefs = { swim: useRef<View>(null), bike: useRef<View>(null), run: useRef<View>(null) };
  const [validationAttempted, setValidationAttempted] = useState(false);
  const [selectedKind, setSelectedKind] = useState<
    GoalPlanningOption['goal_kind'] | null
  >(goal ? 'race_event' : null);
  const [raceType, setRaceType] = useState<RaceType>(
    goal?.race_type ?? 'triathlon',
  );
  const [raceName, setRaceName] = useState(goal?.race_name ?? '');
  const [specificFocus, setSpecificFocus] = useState(goal?.specific_focus ?? '');
  const [targetDate, setTargetDate] = useState(goal?.race_date ?? '');
  const [totalTimeSeconds, setTotalTimeSeconds] = useState<number | null>(
    goal?.total_target_time_seconds ?? null,
  );
  const [runGoalInput, setRunGoalInput] = useState<'time' | 'pace'>('time');
  const [runGoalPace, setRunGoalPace] = useState('');
  const [distances, setDistances] = useState<Record<Discipline, string>>({
    swim: goal?.swim_distance_meters?.toString() ?? '',
    bike: goal?.bike_distance_meters?.toString() ?? '',
    run: goal?.run_distance_meters?.toString() ?? '',
  });
  const [disciplineTimeSeconds, setDisciplineTimeSeconds] = useState<
    Record<Discipline, number | null>
  >({
    swim: goal?.swim_target_time_seconds ?? null,
    bike: goal?.bike_target_time_seconds ?? null,
    run: goal?.run_target_time_seconds ?? null,
  });
  const normalizedTargetDate = normalizeRaceDate(targetDate);
  const disciplines = raceDisciplines[raceType];
  const parsedDistances = Object.fromEntries(
    disciplines.map((discipline) => [
      discipline,
      parsePositiveInteger(distances[discipline]),
    ]),
  ) as Partial<Record<Discipline, number | null>>;
  const paceSeconds = parseRunPace(runGoalPace);
  const effectiveTotalTimeSeconds = raceType === 'run' && runGoalInput === 'pace'
    ? paceSeconds !== null && parsedDistances.run
      ? Math.round(paceSeconds * parsedDistances.run / 1000)
      : null
    : totalTimeSeconds;
  const individualTotal = disciplines.reduce<number>(
    (sum, discipline) => sum + (disciplineTimeSeconds[discipline] ?? 0),
    0,
  );
  const valid = Boolean(
    raceName.trim() &&
      normalizedTargetDate &&
      effectiveTotalTimeSeconds !== null &&
      effectiveTotalTimeSeconds > 0 &&
      disciplines.every((discipline) => parsedDistances[discipline]) &&
      disciplines.every(
        (discipline) =>
          disciplineTimeSeconds[discipline] === null ||
          disciplineTimeSeconds[discipline] > 0,
      ) &&
      individualTotal <= effectiveTotalTimeSeconds,
  );
  const distanceErrors = Object.fromEntries(
    disciplines.map((discipline) => {
      const value = distances[discipline].trim();
      return [
        discipline,
        !value
          ? 'Afstand is verplicht.'
          : parsedDistances[discipline] === null
            ? 'Vul een positief aantal meters in.'
            : null,
      ];
    }),
  ) as Record<Discipline, string | null>;
  const disciplineTimeErrors = Object.fromEntries(
    disciplines.map((discipline) => [
      discipline,
      disciplineTimeSeconds[discipline] !== null &&
      disciplineTimeSeconds[discipline] <= 0
        ? 'Kies een tijd langer dan 00:00:00 of wis deze optionele tijd.'
        : null,
    ]),
  ) as Record<Discipline, string | null>;
  const goalValidationMessages = [
    !raceName.trim() ? 'naam van de race' : null,
    !targetDate.trim()
      ? 'racedatum'
      : !normalizedTargetDate
        ? 'geldige toekomstige racedatum'
        : null,
    ...disciplines.map((discipline) =>
      distanceErrors[discipline]
        ? `afstand ${
            discipline === 'swim'
              ? 'zwemmen'
              : discipline === 'bike'
                ? 'fietsen'
                : 'lopen'
          }`
        : null,
    ),
    effectiveTotalTimeSeconds === null
      ? raceType === 'run' && runGoalInput === 'pace' ? 'geldig richttempo' : 'totale richttijd'
      : effectiveTotalTimeSeconds <= 0
        ? 'geldige totale richttijd'
        : null,
    ...disciplines.map((discipline) =>
      disciplineTimeErrors[discipline]
        ? `geldige richttijd ${discipline}`
        : null,
    ),
    effectiveTotalTimeSeconds !== null && individualTotal > effectiveTotalTimeSeconds
      ? 'een totale richttijd die niet korter is dan de onderdeeltijden'
      : null,
  ].filter((message): message is string => message !== null);
  const raceOption = options.find(
    (option) => option.goal_family === 'race_event',
  );
  const personalOptions = options.filter(
    (option) => option.goal_kind === 'personal_goal',
  );

  return (
    <FormComposition
      description="Een wedstrijdplan rekent terug vanaf een racedatum. Een persoonlijk doel krijgt een eigen cyclus vanaf week 1 en gebruikt nooit stilzwijgend wedstrijdregels."
      title="Kies je trainingsdoel"
    >
      <View accessibilityRole="radiogroup" accessibilityLabel="Trainingsdoel" style={styles.goalModeList}>
        <ChoiceRow label={(raceOption?.label ?? 'Wedstrijd of evenement') + ' · Beschikbaar'}
          accessibilityLabel={raceOption?.label ?? 'Wedstrijd of evenement'}
          hint="Verplichte racedatum; de trainingscyclus wordt vanaf die datum teruggerekend."
          selected={selectedKind === 'race_event'} disabled={raceOption?.availability !== 'available'} onPress={() => setSelectedKind('race_event')} />
        <ChoiceRow label="Persoonlijk doel · Komt later" accessibilityLabel="Persoonlijk doel"
          hint="Begint bij cyclusweek 1 en krijgt eigen doelregels zodra die zijn beoordeeld. Toont persoonlijke doelen die nog niet beschikbaar zijn."
          selected={selectedKind === 'personal_goal'} onPress={() => setSelectedKind('personal_goal')} />
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
                <ChoiceRow key={value} label={label} selected={raceType === value} onPress={() => setRaceType(value)} />
              ))}
            </View>
            <GoalInput
              error={
                validationAttempted && !raceName.trim()
                  ? 'Naam van de race is verplicht.'
                  : undefined
              }
              inputRef={nameRef}
              icon="goal"
              label="Naam van de race"
              onChangeText={setRaceName}
              placeholder="Amsterdam Olympic Triathlon"
              value={raceName}
              required
            />
            <GoalInput
              autoCapitalize="none"
              error={
                validationAttempted
                  ? !targetDate.trim()
                    ? 'Racedatum is verplicht.'
                    : !normalizedTargetDate
                      ? 'Gebruik een geldige toekomstige datum.'
                      : undefined
                  : undefined
              }
              hint="JJJJ-MM-DD"
              inputMode="numeric"
              inputRef={dateRef}
              icon="calendar"
              label="Racedatum"
              maxLength={10}
              onChangeText={(value) =>
                setTargetDate(formatIsoDateInput(value))
              }
              placeholder="2027-06-15"
              value={targetDate}
              required
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
                <GoalInput
                  error={
                    validationAttempted
                      ? distanceErrors[discipline] ?? undefined
                      : undefined
                  }
                  inputMode="numeric"
                  inputRef={distanceRefs[discipline]}
                  icon={discipline}
                  label="Afstand"
                  onChangeText={(value) =>
                    setDistances((current) => ({
                      ...current,
                      [discipline]: value,
                    }))
                  }
                  placeholder={discipline === 'swim' ? '1500' : '10000'}
                  unit="meter"
                  value={distances[discipline]}
                  required
                />
                {raceType !== 'run' ? <DurationPicker appearance="final"
                  error={
                    validationAttempted
                      ? disciplineTimeErrors[discipline] ?? undefined
                      : undefined
                  }
                  hint="Optioneel. Kies uren, minuten en seconden zonder toetsenbord."
                  focusRef={splitRefs[discipline]}
                  label="Richttijd onderdeel"
                  onChange={(value) =>
                    setDisciplineTimeSeconds((current) => ({
                      ...current,
                      [discipline]: value,
                    }))
                  }
                  valueSeconds={disciplineTimeSeconds[discipline]}
                /> : null}
              </View>
            ))}
            {raceType === 'run' ? (
              <View accessibilityRole="radiogroup" style={styles.goalModeList}>
                <ChoiceRow label="Richttijd" selected={runGoalInput === 'time'} onPress={() => setRunGoalInput('time')} />
                <ChoiceRow label="Richttempo (min/km)" selected={runGoalInput === 'pace'} onPress={() => {
                  setRunGoalInput('pace');
                  setDisciplineTimeSeconds((current) => ({ ...current, run: null }));
                }} />
              </View>
            ) : null}
            {raceType === 'run' && runGoalInput === 'pace' ? (
              <GoalInput inputRef={paceRef} icon="clock" label="Richttempo" inputMode="text" placeholder="5:00"
                hint="min:sec per km" value={runGoalPace} onChangeText={setRunGoalPace}
                error={validationAttempted && paceSeconds === null ? 'Gebruik min:sec per km, bijvoorbeeld 5:00.' : undefined}
                required />
            ) : <DurationPicker appearance="final"
              error={
                validationAttempted
                  ? effectiveTotalTimeSeconds === null
                    ? 'Totale richttijd is verplicht.'
                    : effectiveTotalTimeSeconds <= 0
                      ? 'Kies een tijd langer dan 00:00:00.'
                      : individualTotal > effectiveTotalTimeSeconds
                        ? 'De totale richttijd mag niet korter zijn dan de onderdeeltijden samen.'
                        : undefined
                  : undefined
              }
              hint="Verplicht. Kies uren, minuten en seconden zonder toetsenbord."
              focusRef={totalRef}
              label="Totale richttijd"
              onChange={setTotalTimeSeconds}
              valueSeconds={totalTimeSeconds}
              required
            />}
            <GoalInput
              label="Specifieke focus (optioneel)"
              multiline
              onChangeText={setSpecificFocus}
              placeholder="Bijvoorbeeld: extra aandacht voor het zwemonderdeel."
              style={styles.multiline}
              value={specificFocus}
            />
          </View>
          {validationAttempted && goalValidationMessages.length > 0 ? (
            <Notice tone="error">
              {'Vul de gemarkeerde verplichte velden in: ' + goalValidationMessages.join(', ') + '.'}
            </Notice>
          ) : null}
          <Button
            label="A-doel opslaan"
            trailingIcon="forward"
            busy={saving}
            onPress={() => {
              setValidationAttempted(true);
              if (!valid) {
                const distance = disciplines.find((discipline) => distanceErrors[discipline]);
                const split = disciplines.find((discipline) => disciplineTimeErrors[discipline]);
                if (!raceName.trim()) nameRef.current?.focus();
                else if (!normalizedTargetDate) dateRef.current?.focus();
                else if (distance) distanceRefs[distance].current?.focus();
                else if (raceType === 'run' && runGoalInput === 'pace' && paceSeconds === null) paceRef.current?.focus();
                else if (split) splitRefs[split].current?.focus();
                else totalRef.current?.focus();
                return;
              }
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
                total_target_time_seconds: effectiveTotalTimeSeconds!,
                ...Object.fromEntries(
                  disciplines
                    .filter(
                      (discipline) =>
                        disciplineTimeSeconds[discipline] !== null,
                    )
                    .map((discipline) => [
                      `${discipline}_target_time_seconds`,
                      disciplineTimeSeconds[discipline],
                    ]),
                ),
                ...(specificFocus.trim()
                  ? { specific_focus: specificFocus.trim() }
                  : {}),
              });
            }}
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
    </FormComposition>
  );
}


const styles = StyleSheet.create({
  form: { gap: layout.fieldGroupGap },
  goalModeList: { gap: space[12] },
  disciplineCard: { gap: space[16] },
  cardTitle: { ...typography.cardTitle },
  multiline: { minHeight: layout.multilineFieldHeight, textAlignVertical: 'top' },
  personalGoalsPanel: { gap: space[16] },
  personalGoalList: { gap: space[12] },
  personalGoalRow: { gap: space[4] },
  personalGoalsTitle: { ...typography.cardTitle },
  personalGoalsText: { ...typography.body, color: colors.textMuted },
  personalGoalLabel: { ...typography.label },
  comingLaterBadge: { ...typography.supporting, color: colors.warning, backgroundColor: colors.warningSoft, paddingHorizontal: space[12], paddingVertical: space[4], borderRadius: radius.control, alignSelf: 'flex-start' },
});
