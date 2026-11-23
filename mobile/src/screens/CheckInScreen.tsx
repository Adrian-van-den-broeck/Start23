import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  type ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { DayTimePicker } from '../components/DayTimePicker';
import { DurationPicker } from '../components/DurationPicker';
import { FormScrollView } from '../components/FormScrollView';
import { fromWallClock } from '../lib/zonedTime';
import { SelectField } from '../ui-v2/primitives/SelectField';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approvePlanProposal,
  confirmWeeklyCheckInContext,
  createCheckInPlanProposal,
  extractWeeklyCheckInContextCandidate,
  saveWeeklyCheckInContext,
  startWeeklyCheckIn,
} from '../api/client';
import type {
  AthletePlanChoice,
  CheckInContextCandidateResponse,
  Discipline,
  ExternalActivity,
  FatigueLevel,
  RestrictionStatus,
  WeeklyCheckIn,
  WeeklyPlan,
} from '../api/types';
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
import { Input as FormField } from '../ui-v2/primitives/Input';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { Button } from '../ui-v2/primitives/Button';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';
import { studioPresentation } from '../ui-v3/presentation';
import { ChoiceChips, DayToggleStrip, Group, Heading, IconAction, Panel, screenGap, SportTile } from '../ui-v3/screens/support';
import { colors, layout, radius, space } from '../ui-v2/tokens';

type Props = {
  accessToken: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
};

type RestrictionChoice = 'none' | 'low' | 'blocked' | 'professional';

type RestrictionForm = {
  choice: RestrictionChoice;
  advice: string;
};

const disciplines: Discipline[] = ['swim', 'bike', 'run'];
const disciplineLabels: Record<Discipline, TranslationKey> = {
  swim: 'common.swim',
  bike: 'common.bike',
  run: 'common.run',
};
const dayLabels: readonly TranslationKey[] = [
  'checkin.day.mon', 'checkin.day.tue', 'checkin.day.wed', 'checkin.day.thu',
  'checkin.day.fri', 'checkin.day.sat', 'checkin.day.sun',
];
const fatigueLabels: Record<FatigueLevel, TranslationKey> = {
  none: 'checkin.fatigue.none',
  low: 'checkin.fatigue.low',
  moderate: 'checkin.fatigue.moderate',
  high: 'checkin.fatigue.high',
};
const missedReasons = [
  ['time_constraint', 'checkin.reason.time_constraint'],
  ['fatigue', 'checkin.reason.fatigue'],
  ['injury', 'checkin.reason.injury'],
  ['illness', 'checkin.reason.illness'],
  ['motivation', 'checkin.reason.motivation'],
  ['weather', 'checkin.reason.weather'],
  ['other', 'checkin.reason.other'],
] as const satisfies readonly (readonly [string, TranslationKey])[];
const restrictionChoices = [
  ['none', 'checkin.restriction.none'],
  ['low', 'checkin.restriction.low'],
  ['blocked', 'checkin.restriction.blocked'],
  ['professional', 'checkin.restriction.professional'],
] as const satisfies readonly (readonly [RestrictionChoice, TranslationKey])[];

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function nextMonday(): string {
  const value = new Date();
  value.setHours(12, 0, 0, 0);
  value.setDate(value.getDate() + ((8 - value.getDay()) % 7 || 7));
  return isoDate(value);
}

function upcomingMondays(count: number): string[] {
  const first = new Date(`${nextMonday()}T12:00:00`);
  return Array.from({ length: count }, (_, index) => {
    const value = new Date(first);
    value.setDate(first.getDate() + index * 7);
    return isoDate(value);
  });
}

function weekDays(weekStart: string) {
  return Array.from({ length: 7 }, (_, offset) => {
    const [year, month, day] = dateAtOffset(weekStart, offset).split('-').map(Number);
    return { year: year!, month: month!, day: day! };
  });
}

// Default for a new external activity: Monday of the check-in week, 18:00 local.
function weekEvening(weekStart: string, timeZone: string): string {
  const [year, month, day] = weekStart.split('-').map(Number);
  return fromWallClock({ year: year!, month: month!, day: day!, hour: 18, minute: 0 }, timeZone).toISOString();
}

function dateAtOffset(weekStart: string, offset: number): string {
  const value = new Date(`${weekStart}T12:00:00`);
  value.setDate(value.getDate() + offset);
  return isoDate(value);
}

function dayOffsetsForCandidate(
  weekStart: string,
  dates: string[],
): Set<number> {
  const start = new Date(`${weekStart}T12:00:00`);
  return new Set(
    dates
      .map((value) =>
        Math.round(
          (new Date(`${value}T12:00:00`).getTime() - start.getTime()) /
            86_400_000,
        ),
      )
      .filter((offset) => offset >= 0 && offset <= 6),
  );
}

function restrictionPayload(
  discipline: Discipline,
  form: RestrictionForm,
  t: ReturnType<typeof useLanguage>['t'],
): {
  discipline: Discipline;
  status: RestrictionStatus;
  source: 'athlete' | 'physiotherapist';
  athlete_plan_choice: AthletePlanChoice;
  professional_advice?: string;
  professional_advice_at?: string;
} {
  if (form.choice === 'professional') {
    if (!form.advice.trim()) {
      throw new Error(
        t('checkin.adviceMissing', { discipline: t(disciplineLabels[discipline]) }),
      );
    }
    return {
      discipline,
      status: 'professional_restricted',
      source: 'physiotherapist',
      athlete_plan_choice: 'keep_blocked',
      professional_advice: form.advice.trim(),
      professional_advice_at: new Date().toISOString(),
    };
  }
  const values: Record<
    Exclude<RestrictionChoice, 'professional'>,
    [RestrictionStatus, AthletePlanChoice]
  > = {
    none: ['none', 'resume_unrestricted'],
    low: ['self_reported_limited', 'train_low_only'],
    blocked: ['self_reported_blocked', 'keep_blocked'],
  };
  const [status, athletePlanChoice] = values[form.choice];
  return {
    discipline,
    status,
    source: 'athlete',
    athlete_plan_choice: athletePlanChoice,
  };
}

function ActionButton({
  disabled = false,
  label,
  onPress,
  secondary = false,
}: {
  disabled?: boolean;
  label: string;
  onPress: () => void;
  secondary?: boolean;
}) {
  return <Button label={label} disabled={disabled} onPress={onPress} variant={secondary ? 'outline' : 'primary'} />;
}

export function CheckInScreen({ accessToken, onBack, onSignOut }: Props) {
  const { t, locale } = useLanguage();
  const [weekStart, setWeekStart] = useState(nextMonday);
  const [checkIn, setCheckIn] = useState<WeeklyCheckIn | null>(null);
  const [blockedDays, setBlockedDays] = useState<Set<number>>(() => new Set());
  const [fatigue, setFatigue] = useState<FatigueLevel>('none');
  const [reasons, setReasons] = useState<Set<string>>(() => new Set());
  const [recurringConfirmed, setRecurringConfirmed] = useState(false);
  const [restrictions, setRestrictions] = useState<
    Record<Discipline, RestrictionForm>
  >({
    swim: { choice: 'none', advice: '' },
    bike: { choice: 'none', advice: '' },
    run: { choice: 'none', advice: '' },
  });
  const [alarmAcknowledged, setAlarmAcknowledged] = useState(false);
  const [externalActivities, setExternalActivities] = useState<ExternalActivity[]>(
    [],
  );
  const [externalName, setExternalName] = useState('');
  const [externalDiscipline, setExternalDiscipline] =
    useState<Discipline>('run');
  const [externalScheduledAt, setExternalScheduledAt] = useState(() =>
    new Date(`${nextMonday()}T18:00:00`).toISOString(),
  );
  const [externalDuration, setExternalDuration] = useState('60');
  const [externalStrenuous, setExternalStrenuous] = useState(true);
  const [externalRecurring, setExternalRecurring] = useState(false);
  const [proposalPlan, setProposalPlan] = useState<WeeklyPlan | null>(null);
  const [contextText, setContextText] = useState('');
  const [contextCandidate, setContextCandidate] =
    useState<CheckInContextCandidateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scroll = useRef<ScrollView>(null);
  const weekOptions = useMemo(() => upcomingMondays(4).map((monday, index) => ({
    value: monday,
    label: `${index === 0 ? t('checkin.week.next') : t('checkin.week.later')} · ${new Date(`${monday}T12:00:00`).toLocaleDateString(locale, { day: 'numeric', month: 'long' })}`,
  })), [locale, t]);

  // Errors render at the top of a long form; bring them into view.
  useEffect(() => {
    if (error) scroll.current?.scrollTo({ y: 0, animated: true });
  }, [error]);

  const isConfirmed = checkIn?.context?.state === 'confirmed';
  const isCompleted = checkIn?.status === 'completed';
  const expiryLabel = useMemo(() => {
    if (!checkIn?.context) return null;
    return new Date(checkIn.context.expires_at).toLocaleString(locale);
  }, [checkIn, locale]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t('checkin.failed'));
    } finally {
      setBusy(false);
    }
  };

  const begin = () =>
    run(async () => {
      const result = await startWeeklyCheckIn(accessToken, weekStart);
      setCheckIn(result);
      setExternalScheduledAt(weekEvening(result.week_start, result.timezone));
      if (result.context) {
        setBlockedDays(
          new Set(
            result.context.blocked_dates.map((value) =>
              Math.round(
                (new Date(`${value}T12:00:00`).getTime() -
                  new Date(`${result.week_start}T12:00:00`).getTime()) /
                  86_400_000,
              ),
            ),
          ),
        );
        setFatigue(result.context.fatigue_level);
        setReasons(new Set(result.context.missed_workout_reasons));
        setRecurringConfirmed(result.context.recurring_activities_confirmed);
        setExternalActivities(result.context.external_activities);
      }
    });

  const addExternalActivity = () => {
    const duration = Number(externalDuration);
    if (!externalName.trim() || !Number.isFinite(duration) || duration <= 0) {
      setError(t('checkin.externalInvalid'));
      return;
    }
    if (Number.isNaN(new Date(externalScheduledAt).getTime())) {
      setError(t('checkin.externalInvalidTime'));
      return;
    }
    setExternalActivities((current) => [
      ...current,
      {
        name: externalName.trim(),
        discipline: externalDiscipline,
        scheduled_at: externalScheduledAt,
        duration_minutes: String(duration),
        strenuous: externalStrenuous,
        recurring: externalRecurring,
      },
    ]);
    setExternalName('');
    setError(null);
  };

  const extractContext = () => {
    if (!checkIn || !contextText.trim()) return;
    void run(async () => {
      setContextCandidate(
        await extractWeeklyCheckInContextCandidate(
          accessToken,
          checkIn.id,
          contextText.trim(),
        ),
      );
    });
  };

  const useContextCandidate = () => {
    if (!checkIn || !contextCandidate) return;
    const candidate = contextCandidate.candidate;
    setBlockedDays(
      dayOffsetsForCandidate(checkIn.week_start, candidate.blocked_dates),
    );
    if (candidate.fatigue_level !== null) {
      setFatigue(candidate.fatigue_level);
    }
    setReasons(new Set(candidate.missed_workout_reasons));
    setContextCandidate(null);
    setError(null);
  };

  const save = () => {
    if (!checkIn) return;
    void run(async () => {
      const result = await saveWeeklyCheckInContext(accessToken, checkIn.id, {
        expected_revision: checkIn.context_revision,
        blocked_dates: [...blockedDays].map((offset) =>
          dateAtOffset(checkIn.week_start, offset),
        ),
        fatigue_level: fatigue,
        missed_workout_reasons: [...reasons],
        recurring_activities_confirmed: recurringConfirmed,
        external_activities: externalActivities,
        restrictions: disciplines.map((discipline) =>
          restrictionPayload(discipline, restrictions[discipline], t),
        ),
        alarm_symptoms_acknowledged: alarmAcknowledged,
      });
      setCheckIn(result);
    });
  };

  const confirm = () => {
    if (!checkIn?.context) return;
    void run(async () => {
      setCheckIn(
        await confirmWeeklyCheckInContext(
          accessToken,
          checkIn.id,
          checkIn.context!.revision,
          checkIn.context!.fingerprint,
        ),
      );
    });
  };

  const makeProposal = () => {
    if (!checkIn) return;
    void run(async () => {
      const result = await createCheckInPlanProposal(accessToken, checkIn.id);
      setProposalPlan(result.plan);
      setCheckIn((current) =>
        current
          ? {
              ...current,
              status: 'completed',
              plan_proposal_id: result.proposal.id,
            }
          : current,
      );
    });
  };

  const approve = () => {
    if (!proposalPlan?.proposal) return;
    void run(async () => {
      await approvePlanProposal(
        accessToken,
        proposalPlan.proposal!.id,
        proposalPlan.proposal!.base_plan_revision ?? 0,
      );
      onBack();
    });
  };

  const toggleBlockedDay = (offset: number) =>
    setBlockedDays((current) => {
      const next = new Set(current);
      if (next.has(offset)) next.delete(offset);
      else next.add(offset);
      return next;
    });

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <FormScrollView
        ref={scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        style={styles.scroll}
      >
        <BrandedFormHeader caption={t('checkin.caption')} backLabel={t('activity.back')} onBack={onBack} onSignOut={onSignOut} />
        {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
        {busy ? <ActivityIndicator color={colors.primary} /> : null}

        {!checkIn ? (
          <Panel divided={false}>
            <Heading kicker={t('checkin.start.chip')} title={t('checkin.start.title')} description={t('checkin.start.body')} />
            <SelectField
              label={t('creation.weekStart')}
              onChange={setWeekStart}
              options={weekOptions}
              placeholder={t('checkin.week.choose')}
              value={weekStart}
            />
            <ActionButton disabled={busy} label={t('checkin.start.action')} onPress={() => void begin()} />
          </Panel>
        ) : null}

        {checkIn && !isConfirmed && !isCompleted ? (
          <>
            <Panel divided={false}>
              <Heading kicker={t('checkin.form.chip')} title={t('checkin.form.title', { date: checkIn.week_start })} />
              <FormField
                hint={t('checkin.context.hint')}
                label={t('checkin.context.label')}
                maxLength={1000}
                multiline
                onChangeText={setContextText}
                placeholder={t('checkin.context.placeholder')}
                style={styles.contextInput}
                value={contextText}
              />
              <ActionButton
                disabled={busy || !contextText.trim()}
                label={t('checkin.context.extract')}
                onPress={extractContext}
                secondary
              />
              {contextCandidate ? (
                <View style={styles.candidatePanel}>
                  <Text variant="label" accessibilityRole="header">{t('checkin.candidate.title')}</Text>
                  <Text variant="supporting">
                    {t('checkin.candidate.blockedDates', {
                      dates: contextCandidate.candidate.blocked_dates.join(', ') || t('checkin.candidate.noDates'),
                    })}
                    {'\n'}
                    {t('checkin.candidate.fatigue', {
                      fatigue: contextCandidate.candidate.fatigue_level
                        ? t(fatigueLabels[contextCandidate.candidate.fatigue_level])
                        : t('checkin.candidate.noFatigue'),
                    })}
                  </Text>
                  {contextCandidate.candidate.agenda_context.map((line) => (
                    <Text key={line} variant="supporting">• {line}</Text>
                  ))}
                  {contextCandidate.candidate.possible_injury_disciplines.length > 0 ? (
                    <Notice tone="warning">{t('checkin.candidate.injury', { disciplines: contextCandidate.candidate.possible_injury_disciplines.map((discipline) => t(disciplineLabels[discipline])).join(', ') })}</Notice>
                  ) : null}
                  {contextCandidate.candidate.clarifying_questions.map((question) => (
                    <Notice key={question} tone="warning">{t('checkin.candidate.question', { question })}</Notice>
                  ))}
                  <ActionButton
                    label={t('checkin.candidate.use')}
                    onPress={useContextCandidate}
                  />
                  <ActionButton
                    label={t('checkin.candidate.ignore')}
                    onPress={() => setContextCandidate(null)}
                    secondary
                  />
                </View>
              ) : null}
              <Group label={t('checkin.blockedDays')}>
                {studioPresentation ? (
                  <DayToggleStrip
                    days={weekDays(checkIn.week_start).map((day, offset) => ({ label: t(dayLabels[offset]!), date: day.day }))}
                    isMarked={(offset) => blockedDays.has(offset)}
                    onToggle={toggleBlockedDay}
                  />
                ) : (
                  <ChoiceChips
                    isSelected={(offset) => blockedDays.has(offset)}
                    mode="checkbox"
                    onPress={toggleBlockedDay}
                    options={dayLabels.map((label, offset) => ({ value: offset, label: t(label) }))}
                  />
                )}
              </Group>
              <Group label={t('checkin.fatigue')}>
                <ChoiceChips
                  isSelected={(value) => fatigue === value}
                  mode="radio"
                  onPress={setFatigue}
                  options={(Object.keys(fatigueLabels) as FatigueLevel[]).map((value) => ({ value, label: t(fatigueLabels[value]) }))}
                />
              </Group>
              <Group label={t('checkin.missedReasons')}>
                <ChoiceChips
                  isSelected={(value) => reasons.has(value)}
                  mode="checkbox"
                  onPress={(value) =>
                    setReasons((current) => {
                      const next = new Set(current);
                      if (next.has(value)) next.delete(value);
                      else next.add(value);
                      return next;
                    })
                  }
                  options={missedReasons.map(([value, label]) => ({ value, label: t(label) }))}
                />
              </Group>
            </Panel>

            <Panel>
              <Heading title={t('checkin.injuries.title')} description={t('checkin.injuries.body')} />
              {disciplines.map((discipline) => (
                <View key={discipline} style={styles.subsection}>
                  <SelectField
                    label={t(disciplineLabels[discipline])}
                    onChange={(value) =>
                      setRestrictions((current) => ({
                        ...current,
                        [discipline]: { ...current[discipline], choice: value },
                      }))
                    }
                    options={restrictionChoices.map(([value, label]) => ({ value, label: t(label) }))}
                    placeholder={t('checkin.restriction.none')}
                    value={restrictions[discipline].choice}
                  />
                  {restrictions[discipline].choice === 'professional' ? (
                    <FormField
                      label={t('checkin.injuries.advice')}
                      onChangeText={(advice) =>
                        setRestrictions((current) => ({
                          ...current,
                          [discipline]: { ...current[discipline], advice },
                        }))
                      }
                      value={restrictions[discipline].advice}
                    />
                  ) : null}
                </View>
              ))}
              <ChoiceRow label={t('checkin.injuries.alarm')} selected={alarmAcknowledged} mode="checkbox" onPress={() => setAlarmAcknowledged((value) => !value)} />
            </Panel>

            <Panel>
              <Heading title={t('checkin.external.title')} />
              <ChoiceRow label={t('checkin.external.recurringConfirmed')} selected={recurringConfirmed} mode="checkbox" onPress={() => setRecurringConfirmed((value) => !value)} />
              {externalActivities.map((activity, index) => (
                <View key={`${activity.scheduled_at}-${index}`} style={styles.activityRow}>
                  {studioPresentation ? <SportTile discipline={activity.discipline} /> : null}
                  <View style={styles.activityCopy}>
                    <Text variant="label">{activity.name}</Text>
                    <Text variant="supporting" tone="textMuted">
                      {t(disciplineLabels[activity.discipline])} · {activity.duration_minutes} min
                      {activity.strenuous ? ` · ${t('checkin.external.strenuousSuffix')}` : ''}
                      {activity.recurring ? ` · ${t('checkin.external.recurringSuffix')}` : ''}
                    </Text>
                  </View>
                  <IconAction icon="close" label={t('checkin.external.remove')} onPress={() =>
                      setExternalActivities((current) =>
                        current.filter((_, currentIndex) => currentIndex !== index),
                      )
                    } />
                </View>
              ))}
              <FormField label={t('checkin.external.name')} onChangeText={setExternalName} value={externalName} />
              <ChoiceChips
                isSelected={(value) => externalDiscipline === value}
                mode="radio"
                onPress={setExternalDiscipline}
                options={disciplines.map((discipline) => ({ value: discipline, label: t(disciplineLabels[discipline]) }))}
              />
              <DayTimePicker
                dayOptions={weekDays(checkIn.week_start)}
                label={t('checkin.external.time')}
                onChange={setExternalScheduledAt}
                timeZone={checkIn.timezone}
                valueIso={externalScheduledAt}
              />
              <DurationPicker
                clearable={false}
                label={t('checkin.external.duration')}
                maxHours={12}
                onChange={(seconds) => setExternalDuration(seconds === null ? '' : String(seconds / 60))}
                units={['hours', 'minutes']}
                valueSeconds={externalDuration === '' ? null : Math.round(Number(externalDuration) * 60)}
              />
              <ChoiceChips
                isSelected={(value) => (value === 'strenuous' ? externalStrenuous : externalRecurring)}
                mode="checkbox"
                onPress={(value) =>
                  value === 'strenuous'
                    ? setExternalStrenuous((current) => !current)
                    : setExternalRecurring((current) => !current)
                }
                options={[
                  { value: 'strenuous', label: t('checkin.external.strenuous') },
                  { value: 'recurring', label: t('checkin.external.recurring') },
                ] as const}
              />
              <ActionButton label={t('checkin.external.add')} onPress={addExternalActivity} secondary />
            </Panel>

            <Panel>
              <ActionButton disabled={busy || !recurringConfirmed} label={t('checkin.save')} onPress={save} />
              {!recurringConfirmed ? <Text variant="supporting" tone="textMuted">{t('checkin.saveNeedsRecurring')}</Text> : null}
              {checkIn.context ? (
                <>
                  <Text variant="supporting" tone="textMuted">{t('checkin.source', { expiry: expiryLabel ?? '' })}</Text>
                  <ActionButton disabled={busy} label={t('checkin.confirm')} onPress={confirm} />
                </>
              ) : null}
            </Panel>
          </>
        ) : null}

        {checkIn && isConfirmed && !isCompleted ? (
          <Panel divided={false}>
            <Heading kicker={t('checkin.confirmed.chip')} title={t('checkin.confirmed.title')} description={t('checkin.confirmed.body')} />
            <ActionButton disabled={busy} label={t('checkin.confirmed.action')} onPress={makeProposal} />
          </Panel>
        ) : null}

        {proposalPlan ? (
          <Panel divided={false}>
            <Heading
              description={t('checkin.proposal.summary', { workouts: proposalPlan.workouts.length, restDays: proposalPlan.rest_days.length })}
              kicker={t('checkin.proposal.chip')}
              kickerTone="warning"
              title={t('checkin.proposal.title', { date: proposalPlan.week_start })}
            />
            {proposalPlan.warnings.map((warning) => (
              <Notice key={warning.id ?? warning.code} tone="warning">{warning.message}</Notice>
            ))}
            <ActionButton disabled={busy} label={t('checkin.proposal.approve')} onPress={approve} />
            <ActionButton label={t('checkin.proposal.later')} onPress={onBack} secondary />
          </Panel>
        ) : null}
      </FormScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  scroll: { flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: screenGap, padding: layout.phoneGutter, paddingBottom: space[48] },
  subsection: { gap: space[8] },
  contextInput: { minHeight: layout.multilineFieldHeight, textAlignVertical: 'top' },
  candidatePanel: { backgroundColor: colors.primarySoft, borderRadius: radius.card, gap: space[12], padding: space[16] },
  activityRow: { flexDirection: 'row', alignItems: 'center', gap: space[12] },
  activityCopy: { flex: 1, minWidth: 0, gap: 2 },
});
