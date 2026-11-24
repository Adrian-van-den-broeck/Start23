import { Fragment, useState, useRef } from 'react';
import { StyleSheet, View, type TextInput } from 'react-native';
import type { Discipline, GoalPlanningOption, PrimaryRaceGoal, RaceType } from '../../api/types';
import { DatePicker } from '../../components/DatePicker';
import { DurationPicker } from '../../components/DurationPicker';
import { parseRunPace } from '../../lib/runPace';
import { parsePositiveInteger, raceDisciplines } from '../../lib/onboardingForms';
import { FormComposition, FormSection } from '../components/FormComposition';
import { Button } from '../primitives/Button';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Input, type InputProps } from '../primitives/Input';
import { Notice } from '../primitives/Notice';
import { SelectField, type SelectOption } from '../primitives/SelectField';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import { useLanguage } from '../../i18n/LanguageProvider';
import { ChoiceChips } from '../../ui-v3/screens/support';

function GoalInput({ required = false, optional = false, label, ...props }: InputProps & { required?: boolean; optional?: boolean }) {
  const { t } = useLanguage();
  const optionalLabel = optional ? t('onboarding.optional') : undefined;
  return <Input {...props} optionalLabel={optionalLabel}
    label={label + (required ? ' *' : '')} accessibilityLabel={props.accessibilityLabel ?? (optionalLabel ? `${label} ${optionalLabel}` : label)} />;
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

const RACE_HORIZON_YEARS = 10;

// The race must be after today (the server enforces the same and sets no upper
// limit), so the wheels start tomorrow. The picker needs an end: the last day of
// the year ten years ahead, far beyond any race an athlete can enter now.
function raceDateBounds(today = new Date()) {
  const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const min = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(
    tomorrow.getDate(),
  ).padStart(2, '0')}`;
  return { min, max: `${today.getFullYear() + RACE_HORIZON_YEARS}-12-31` };
}

export function GoalStep({ goal, options, saving, onSave }: GoalStepProps) {
  const { t } = useLanguage();
  const nameRef = useRef<TextInput>(null);
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
  const raceBounds = raceDateBounds();
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
          ? t('onboarding.goal.distanceRequired')
          : parsedDistances[discipline] === null
            ? t('onboarding.goal.distanceInvalid')
            : null,
      ];
    }),
  ) as Record<Discipline, string | null>;
  const disciplineTimeErrors = Object.fromEntries(
    disciplines.map((discipline) => [
      discipline,
      disciplineTimeSeconds[discipline] !== null &&
      disciplineTimeSeconds[discipline] <= 0
        ? t('onboarding.goal.splitInvalid')
        : null,
    ]),
  ) as Record<Discipline, string | null>;
  const goalValidationMessages = [
    !raceName.trim() ? t('onboarding.goal.missing.raceName') : null,
    !targetDate.trim()
      ? t('onboarding.goal.missing.raceDate')
      : !normalizedTargetDate
        ? t('onboarding.goal.missing.validRaceDate')
        : null,
    ...disciplines.map((discipline) =>
      distanceErrors[discipline]
        ? t(
            discipline === 'swim'
              ? 'onboarding.goal.missing.distance.swim'
              : discipline === 'bike'
                ? 'onboarding.goal.missing.distance.bike'
                : 'onboarding.goal.missing.distance.run',
          )
        : null,
    ),
    effectiveTotalTimeSeconds === null
      ? raceType === 'run' && runGoalInput === 'pace' ? t('onboarding.goal.missing.validPace') : t('onboarding.goal.missing.totalTime')
      : effectiveTotalTimeSeconds <= 0
        ? t('onboarding.goal.missing.validTotalTime')
        : null,
    ...disciplines.map((discipline) =>
      disciplineTimeErrors[discipline]
        ? t('onboarding.goal.missing.validSplit', { discipline: t(`common.${discipline}`).toLowerCase() })
        : null,
    ),
    effectiveTotalTimeSeconds !== null && individualTotal > effectiveTotalTimeSeconds
      ? t('onboarding.goal.missing.totalNotShorter')
      : null,
  ].filter((message): message is string => message !== null);
  const raceOption = options.find(
    (option) => option.goal_family === 'race_event',
  );
  const personalOptions = options.filter(
    (option) => option.goal_kind === 'personal_goal',
  );

  const raceTypeOptions: SelectOption<RaceType>[] = [
    { value: 'run', label: t('common.run') },
    { value: 'bike', label: t('common.bike') },
    { value: 'swim', label: t('common.swim') },
    { value: 'triathlon', label: t('onboarding.goal.raceType.triathlon') },
    { value: 'duathlon', label: t('onboarding.goal.raceType.duathlon') },
  ];
  // Several legs each get their own titled group; a single leg needs no heading.
  const grouped = disciplines.length > 1;
  const Closing = grouped ? FormSection : Fragment;

  return (
    <FormComposition
      description={t('onboarding.goal.description')}
      title={t('onboarding.goal.title')}
    >
      <View accessibilityRole="radiogroup" accessibilityLabel={t('onboarding.goal.groupLabel')} style={styles.choices}>
        <ChoiceRow label={t('onboarding.goal.available', { label: raceOption?.label ?? t('onboarding.goal.raceEvent') })}
          accessibilityLabel={raceOption?.label ?? t('onboarding.goal.raceEvent')}
          hint={t('onboarding.goal.raceHint')}
          selected={selectedKind === 'race_event'} disabled={raceOption?.availability !== 'available'} onPress={() => setSelectedKind('race_event')} />
        <ChoiceRow label={t('onboarding.goal.personalComingLater')} accessibilityLabel={t('onboarding.goal.personal')}
          hint={t('onboarding.goal.personalHint')}
          selected={selectedKind === 'personal_goal'} onPress={() => setSelectedKind('personal_goal')} />
      </View>
      {selectedKind === 'race_event' ? (
        <>
          <SelectField
            label={t('onboarding.goal.raceType')}
            onChange={setRaceType}
            options={raceTypeOptions}
            placeholder={t('onboarding.goal.raceTypePlaceholder')}
            value={raceType}
          />
          <GoalInput
            error={
              validationAttempted && !raceName.trim()
                ? t('onboarding.goal.raceNameRequired')
                : undefined
            }
            inputRef={nameRef}
            icon="goal"
            label={t('onboarding.goal.raceName')}
            onChangeText={setRaceName}
            placeholder="Amsterdam Olympic Triathlon"
            value={raceName}
            required
          />
          <DatePicker
            error={
              validationAttempted
                ? !targetDate.trim()
                  ? t('onboarding.goal.raceDateRequired')
                  : !normalizedTargetDate
                    ? t('onboarding.goal.raceDateInvalid')
                    : undefined
                : undefined
            }
            label={t('onboarding.goal.raceDate')}
            min={raceBounds.min}
            max={raceBounds.max}
            openAt={raceBounds.min}
            onChange={setTargetDate}
            value={targetDate}
            required
          />
          {disciplines.map((discipline) => {
            const fields = (
              <>
                <GoalInput
                  error={
                    validationAttempted
                      ? distanceErrors[discipline] ?? undefined
                      : undefined
                  }
                  inputMode="numeric"
                  inputRef={distanceRefs[discipline]}
                  icon={discipline}
                  label={t('onboarding.goal.distance')}
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
                {raceType !== 'run' ? <DurationPicker
                  error={
                    validationAttempted
                      ? disciplineTimeErrors[discipline] ?? undefined
                      : undefined
                  }
                  hint={t('onboarding.goal.splitHint')}
                  focusRef={splitRefs[discipline]}
                  label={t('onboarding.goal.splitLabel')}
                  onChange={(value) =>
                    setDisciplineTimeSeconds((current) => ({
                      ...current,
                      [discipline]: value,
                    }))
                  }
                  valueSeconds={disciplineTimeSeconds[discipline]}
                /> : null}
              </>
            );
            return grouped
              ? <FormSection key={discipline} title={t(`common.${discipline}`)}>{fields}</FormSection>
              : <Fragment key={discipline}>{fields}</Fragment>;
          })}
          <Closing>
            {raceType === 'run' ? (
              <ChoiceChips
                accessibilityLabel={t('onboarding.goal.targetMode')}
                isSelected={(mode) => mode === runGoalInput}
                mode="radio"
                onPress={(mode) => {
                  setRunGoalInput(mode);
                  if (mode === 'pace') setDisciplineTimeSeconds((current) => ({ ...current, run: null }));
                }}
                options={[
                  { value: 'time' as const, label: t('onboarding.goal.targetTime') },
                  { value: 'pace' as const, label: t('onboarding.goal.targetPaceOption') },
                ]}
              />
            ) : null}
            {raceType === 'run' && runGoalInput === 'pace' ? (
              <GoalInput inputRef={paceRef} icon="clock" label={t('onboarding.goal.targetPace')} inputMode="text" placeholder="5:00"
                hint="min:sec per km" value={runGoalPace} onChangeText={setRunGoalPace}
                error={validationAttempted && paceSeconds === null ? t('onboarding.paceFormat') : undefined}
                required />
            ) : <DurationPicker
              error={
                validationAttempted
                  ? effectiveTotalTimeSeconds === null
                    ? t('onboarding.goal.totalRequired')
                    : effectiveTotalTimeSeconds <= 0
                      ? t('onboarding.goal.totalPositive')
                      : individualTotal > effectiveTotalTimeSeconds
                        ? t('onboarding.goal.totalTooShort')
                        : undefined
                  : undefined
              }
              hint={t('onboarding.goal.totalHint')}
              focusRef={totalRef}
              label={t('onboarding.goal.totalLabel')}
              onChange={setTotalTimeSeconds}
              valueSeconds={totalTimeSeconds}
              required
            />}
            <GoalInput
              label={t('onboarding.goal.focus')}
              optional
              multiline
              onChangeText={setSpecificFocus}
              placeholder={t('onboarding.goal.focusPlaceholder')}
              style={styles.multiline}
              value={specificFocus}
            />
          </Closing>
          {validationAttempted && goalValidationMessages.length > 0 ? (
            <Notice tone="error">
              {t('onboarding.goal.missingFields', { fields: goalValidationMessages.join(', ') })}
            </Notice>
          ) : null}
          <Button
            label={t('onboarding.goal.save')}
            trailingIcon="forward"
            busy={saving}
            onPress={() => {
              setValidationAttempted(true);
              if (!valid) {
                const distance = disciplines.find((discipline) => distanceErrors[discipline]);
                const split = disciplines.find((discipline) => disciplineTimeErrors[discipline]);
                if (!raceName.trim()) nameRef.current?.focus();
                // The date picker has no focus target; its error is shown at the field.
                else if (!normalizedTargetDate) return;
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
        <FormSection>
          <View style={styles.copy}>
            <Text variant="label" accessibilityRole="header">{t('onboarding.goal.personalTitle')}</Text>
            <Text variant="supporting" tone="textMuted">{t('onboarding.goal.personalText')}</Text>
          </View>
          {personalOptions.length > 0 ? (
            <View>
              {personalOptions.map((option) => (
                <View key={option.goal_family} style={styles.personalRow}>
                  <Text variant="label" style={styles.personalLabel}>{option.label}</Text>
                  <View style={styles.badge}>
                    <Text variant="caption" tone="warning">{t('onboarding.goal.comingLater')}</Text>
                  </View>
                </View>
              ))}
            </View>
          ) : null}
        </FormSection>
      ) : null}
    </FormComposition>
  );
}

const styles = StyleSheet.create({
  choices: { gap: space[8] },
  copy: { gap: space[4] },
  multiline: { minHeight: layout.multilineFieldHeight, textAlignVertical: 'top' },
  personalRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between',
    columnGap: space[12], rowGap: space[4], paddingVertical: space[12],
    borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  personalLabel: { flexShrink: 1 },
  badge: { backgroundColor: colors.warningSoft, paddingHorizontal: space[8], paddingVertical: space[4], borderRadius: radius.inset },
});
