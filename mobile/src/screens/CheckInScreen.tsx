import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
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
import { Input as FormField } from '../ui-v2/primitives/Input';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { QuickActionRow } from '../ui-v2/components/QuickActionRow';
import { Button } from '../ui-v2/primitives/Button';
import { Card } from '../ui-v2/primitives/Card';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';

import { colors, layout, radius, space, typography } from '../ui-v2/tokens';

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
const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
};
const dayLabels = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'] as const;
const fatigueLabels: Record<FatigueLevel, string> = {
  none: 'Geen',
  low: 'Licht',
  moderate: 'Matig',
  high: 'Hoog',
};
const missedReasons = [
  ['time_constraint', 'Tijd'],
  ['fatigue', 'Vermoeidheid'],
  ['injury', 'Blessure'],
  ['illness', 'Ziekte'],
  ['motivation', 'Motivatie'],
  ['weather', 'Weer'],
  ['other', 'Anders'],
] as const;

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
        `Vul het professionele advies voor ${disciplineLabels[discipline]} in.`,
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

  const isConfirmed = checkIn?.context?.state === 'confirmed';
  const isCompleted = checkIn?.status === 'completed';
  const expiryLabel = useMemo(() => {
    if (!checkIn?.context) return null;
    return new Date(checkIn.context.expires_at).toLocaleString('nl-NL');
  }, [checkIn]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'De check-in is mislukt.');
    } finally {
      setBusy(false);
    }
  };

  const begin = () =>
    run(async () => {
      const result = await startWeeklyCheckIn(accessToken, weekStart);
      setCheckIn(result);
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
      setError('Vul voor de extra activiteit een naam en geldige duur in.');
      return;
    }
    if (Number.isNaN(new Date(externalScheduledAt).getTime())) {
      setError('Gebruik een geldig ISO-tijdstip inclusief tijdzone.');
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
          restrictionPayload(discipline, restrictions[discipline]),
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
        <BrandedFormHeader caption="Wekelijkse check-in" backLabel="Weekplanning" onBack={onBack} onSignOut={onSignOut} />
        {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
        {busy ? <ActivityIndicator color={colors.primary} /> : null}

        {!checkIn ? (
          <Card elevated padding="form" style={styles.panel}>
            <View style={[styles.chip]}><Text variant="supporting" tone="primary">Zonder AI</Text></View>
            <Text style={styles.title}>Bereid je volgende week voor</Text>
            <Text style={styles.body}>
              Je antwoorden worden gestructureerd opgeslagen. Pas na jouw aparte
              bevestiging ontstaat een planvoorstel.
            </Text>
            <FormField
              autoCapitalize="none"
              label="Week start op maandag"
              onChangeText={setWeekStart}
              value={weekStart}
            />
            <ActionButton disabled={busy} label="Start check-in" onPress={() => void begin()} />
          </Card>
        ) : null}

        {checkIn && !isConfirmed && !isCompleted ? (
          <>
            <Card elevated padding="form" style={styles.panel}>
              <View style={[styles.chip]}><Text variant="supporting" tone="primary">Gestructureerde bron</Text></View>
              <Text style={styles.title}>Week van {checkIn.week_start}</Text>
              <FormField
                label="Vertel kort wat er deze week speelt (optioneel)"
                maxLength={1000}
                multiline
                onChangeText={setContextText}
                placeholder="Bijvoorbeeld: woensdag kan ik niet en ik voel me behoorlijk vermoeid."
                style={styles.contextInput}
                value={contextText}
              />
              <ActionButton
                disabled={busy || !contextText.trim()}
                label="Maak invulvoorstel"
                onPress={extractContext}
                secondary
              />
              <Text style={styles.body}>
                Dit maakt alleen een tijdelijk invulvoorstel. Controleer het en
                bevestig daarna nog steeds het gestructureerde formulier.
              </Text>
              {contextCandidate ? (
                <View style={styles.candidatePanel}>
                  <Text style={styles.label}>Controleer het invulvoorstel</Text>
                  <Text style={styles.body}>
                    Geblokkeerde datums:{' '}
                    {contextCandidate.candidate.blocked_dates.join(', ') || 'geen'}
                    {'\n'}Vermoeidheid:{' '}
                    {contextCandidate.candidate.fatigue_level
                      ? fatigueLabels[contextCandidate.candidate.fatigue_level]
                      : 'niet ingevuld'}
                  </Text>
                  {contextCandidate.candidate.agenda_context.map((line) => (
                    <Text key={line} style={styles.body}>• {line}</Text>
                  ))}
                  {contextCandidate.candidate.possible_injury_disciplines.length > 0 ? (
                    <Notice tone="warning">{`Mogelijke blessure genoemd voor: ${contextCandidate.candidate.possible_injury_disciplines.map((discipline) => disciplineLabels[discipline]).join(', ')}. Kies de beperking hieronder zelf; die wordt niet automatisch aangepast.`}</Notice>
                  ) : null}
                  {contextCandidate.candidate.clarifying_questions.map((question) => (
                    <Notice key={question} tone="warning">{`Vraag: ${question}`}</Notice>
                  ))}
                  <ActionButton
                    label="Neem datums, vermoeidheid en redenen over"
                    onPress={useContextCandidate}
                  />
                  <ActionButton
                    label="Negeer invulvoorstel"
                    onPress={() => setContextCandidate(null)}
                    secondary
                  />
                </View>
              ) : null}
              <Text style={styles.body}>Welke dagen zijn volledig geblokkeerd?</Text>
              <View style={styles.rowWrap}>
                {dayLabels.map((label, offset) => (
                  <ChoiceRow key={label} label={label}  selected={blockedDays.has(offset)} mode="checkbox" onPress={() =>
                      setBlockedDays((current) => {
                        const next = new Set(current);
                        if (next.has(offset)) next.delete(offset);
                        else next.add(offset);
                        return next;
                      })
                    } />
                ))}
              </View>
              <Text style={styles.label}>Vermoeidheid</Text>
              <View style={styles.rowWrap}>
                {(Object.keys(fatigueLabels) as FatigueLevel[]).map((value) => (
                  <ChoiceRow key={value} label={fatigueLabels[value]}  selected={fatigue === value} mode="radio" onPress={() => setFatigue(value)} />
                ))}
              </View>
              <Text style={styles.label}>Redenen voor gemiste trainingen</Text>
              <View style={styles.rowWrap}>
                {missedReasons.map(([value, label]) => (
                  <ChoiceRow key={value} label={label}  selected={reasons.has(value)} mode="checkbox" onPress={() =>
                      setReasons((current) => {
                        const next = new Set(current);
                        if (next.has(value)) next.delete(value);
                        else next.add(value);
                        return next;
                      })
                    } />
                ))}
              </View>
            </Card>

            <Card elevated padding="form" style={styles.panel}>
              <Text style={styles.title}>Blessures en advies</Text>
              <Text style={styles.body}>
                Beoordeel elke discipline opnieuw. Een beperking wordt nooit
                automatisch opgeheven.
              </Text>
              {disciplines.map((discipline) => (
                <View key={discipline} style={styles.subsection}>
                  <Text style={styles.label}>{disciplineLabels[discipline]}</Text>
                  <View style={styles.rowWrap}>
                    {(
                      [
                        ['none', 'Vrij'],
                        ['low', 'Alleen rustig'],
                        ['blocked', 'Geblokkeerd'],
                        ['professional', 'Professioneel advies'],
                      ] as const
                    ).map(([value, label]) => (
                      <ChoiceRow key={value} label={label} accessibilityLabel={`${disciplineLabels[discipline]}: ${label}`} selected={restrictions[discipline].choice === value} mode="radio" onPress={() =>
                          setRestrictions((current) => ({
                            ...current,
                            [discipline]: { ...current[discipline], choice: value },
                          }))
                        } />
                    ))}
                  </View>
                  {restrictions[discipline].choice === 'professional' ? (
                    <FormField
                      label="Advies en herleidbare bron"
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
              <ChoiceRow  label="Ik begrijp dat alarmsymptomen medische beoordeling vragen en niet door dit plan worden beoordeeld."  selected={alarmAcknowledged} mode="checkbox" onPress={() => setAlarmAcknowledged((value) => !value)} />
            </Card>

            <Card elevated padding="form" style={styles.panel}>
              <Text style={styles.title}>Sport buiten Wombo</Text>
              <ChoiceRow  label="Ik heb mijn terugkerende sportactiviteiten voor deze week gecontroleerd."  selected={recurringConfirmed} mode="checkbox" onPress={() => setRecurringConfirmed((value) => !value)} />
              {externalActivities.map((activity, index) => (
                <View key={`${activity.scheduled_at}-${index}`} style={styles.activityRow}>
                  <Text style={styles.label}>{activity.name}</Text>
                  <Text style={styles.body}>
                    {disciplineLabels[activity.discipline]} · {activity.duration_minutes} min
                    {activity.strenuous ? ' · inspannend' : ''}
                    {activity.recurring ? ' · terugkerend' : ''}
                  </Text>
                  <QuickActionRow label="Verwijderen" icon="close" onAction={() =>
                      setExternalActivities((current) =>
                        current.filter((_, currentIndex) => currentIndex !== index),
                      )
                    } />
                </View>
              ))}
              <FormField label="Naam extra activiteit" onChangeText={setExternalName} value={externalName} />
              <View style={styles.rowWrap}>
                {disciplines.map((discipline) => (
                  <ChoiceRow key={discipline} label={disciplineLabels[discipline]}  selected={externalDiscipline === discipline} mode="radio" onPress={() => setExternalDiscipline(discipline)} />
                ))}
              </View>
              <FormField
                autoCapitalize="none"
                label="Tijdstip (ISO inclusief tijdzone)"
                onChangeText={setExternalScheduledAt}
                value={externalScheduledAt}
              />
              <FormField
                inputMode="decimal"
                label="Geplande duur (minuten)"
                onChangeText={setExternalDuration}
                value={externalDuration}
              />
              <View style={styles.rowWrap}>
                <ChoiceRow  label="Inspannend"  selected={externalStrenuous} mode="checkbox" onPress={() => setExternalStrenuous((value) => !value)} />
                <ChoiceRow  label="Terugkerend"  selected={externalRecurring} mode="checkbox" onPress={() => setExternalRecurring((value) => !value)} />
                <ActionButton label="Toevoegen" onPress={addExternalActivity} secondary />
              </View>
            </Card>

            <Card elevated padding="form" style={styles.panel}>
              <ActionButton disabled={busy || !recurringConfirmed} label="Context opslaan" onPress={save} />
              {checkIn.context ? (
                <>
                  <Text style={styles.body}>
                    Bron: gestructureerd formulier · geldig tot {expiryLabel}
                  </Text>
                  <ActionButton disabled={busy} label="Deze context bevestigen" onPress={confirm} />
                </>
              ) : null}
            </Card>
          </>
        ) : null}

        {checkIn && isConfirmed && !isCompleted ? (
          <Card elevated padding="form" style={styles.panel}>
            <View style={[styles.chip]}><Text variant="supporting" tone="primary">Context bevestigd</Text></View>
            <Text style={styles.title}>Klaar voor het voorstel</Text>
            <Text style={styles.body}>
              Alleen een nieuwe, nog goed te keuren planrevisie wordt gemaakt.
            </Text>
            <ActionButton disabled={busy} label="Maak planvoorstel" onPress={makeProposal} />
          </Card>
        ) : null}

        {proposalPlan ? (
          <Card elevated padding="form" style={styles.panel}>
            <View style={[styles.chip, styles.pendingChip]}><Text variant="supporting" tone="warning">Wacht op jouw goedkeuring</Text></View>
            <Text style={styles.title}>Voorstel voor {proposalPlan.week_start}</Text>
            <Text style={styles.body}>
              {proposalPlan.workouts.length} trainingen · {proposalPlan.rest_days.length} rustdagen
            </Text>
            {proposalPlan.warnings.map((warning) => (
              <Notice key={warning.id ?? warning.code} tone="warning">{warning.message}</Notice>
            ))}
            <ActionButton disabled={busy} label="Voorstel goedkeuren" onPress={approve} />
            <ActionButton label="Later beslissen" onPress={onBack} secondary />
          </Card>
        ) : null}
      </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  keyboard: { flex: 1 }, scroll: { flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
  panel: { gap: layout.fieldGroupGap },
  subsection: { borderTopColor: colors.border, borderTopWidth: layout.decorativeLine, gap: space[12], paddingTop: space[16] },
  contextInput: { minHeight: layout.multilineFieldHeight, textAlignVertical: 'top' },
  candidatePanel: { backgroundColor: colors.primarySoft, borderRadius: radius.inset, gap: space[16], padding: space[16] },
  title: { ...typography.sectionTitle }, body: { color: colors.textMuted }, label: { ...typography.label },
  rowWrap: { gap: space[12] },
  activityRow: { borderTopColor: colors.border, borderTopWidth: layout.decorativeLine, gap: space[8], paddingTop: space[16] },
  chip: { alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] },
  pendingChip: { backgroundColor: colors.warningSoft },
});
