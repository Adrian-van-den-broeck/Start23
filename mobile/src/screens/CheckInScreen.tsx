import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react';
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
  confirmWeeklyCheckInContext,
  createCheckInPlanProposal,
  extractWeeklyCheckInContextCandidate,
  getInjuryRestrictions,
  getWeeklyCheckIn,
  rejectPlanProposal,
  saveWeeklyCheckInContext,
  startWeeklyCheckIn,
} from '../api/client';
import type {
  CheckInContextCandidateResponse,
  Discipline,
  ExternalActivity,
  FatigueLevel,
  InjuryRestriction,
  WeeklyCheckIn,
  WeeklyPlan,
} from '../api/types';
import { restoreRestrictions, restrictionPayload, restrictionLabels, sameRestriction } from '../features/checkins/restrictionForm';
import { useOptionalPlanningFlow } from '../features/planning/PlanningFlowProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { localizeRecoveryMessage } from '../i18n/recoveryMessages';
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
  athleteIdentity?: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
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

export function CheckInScreen(props: Props) {
  return <CheckInFormScreen key={props.athleteIdentity ?? props.accessToken} {...props} />;
}

function CheckInFormScreen({ accessToken, onBack, onSignOut }: Props) {
  const { language } = useLanguage();
  const planning = useOptionalPlanningFlow();
  const [weekStart, setWeekStart] = useState(nextMonday);
  const [checkIn, setCheckIn] = useState<WeeklyCheckIn | null>(null);
  const [blockedDays, setBlockedDaysState] = useState<Set<number>>(() => new Set());
  const [fatigue, setFatigueState] = useState<FatigueLevel | null>(null);
  const [reasons, setReasonsState] = useState<Set<string>>(() => new Set());
  const [recurringConfirmed, setRecurringConfirmedState] = useState<boolean | null>(null);
  const [restrictions, setRestrictionsState] = useState(() => restoreRestrictions([], []));
  const [alarmAcknowledged, setAlarmAcknowledgedState] = useState<boolean | null>(null);
  const [externalActivities, setExternalActivitiesState] = useState<ExternalActivity[]>([]);
  const [contextDirty, setContextDirty] = useState(false);
  const [editingContext, setEditingContext] = useState(false);
  const mutationRunning = useRef(false);
  const beginWeekAttempt = useRef<string | null>(null);
  const saveAttempt = useRef<Parameters<typeof saveWeeklyCheckInContext>[2] | null>(null);
  const confirmationAttempt = useRef<{ revision: number; fingerprint: string } | null>(null);
  const update = <T,>(setter: Dispatch<SetStateAction<T>>) => (value: SetStateAction<T>) => {
    if (mutationRunning.current) return;
    setContextDirty(true);
    setter(value);
  };
  const setBlockedDays = update(setBlockedDaysState);
  const setFatigue = update(setFatigueState);
  const setReasons = update(setReasonsState);
  const setRecurringConfirmed = update(setRecurringConfirmedState);
  const setRestrictions = update(setRestrictionsState);
  const setAlarmAcknowledged = update(setAlarmAcknowledgedState);
  const setExternalActivities = update(setExternalActivitiesState);
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

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  const formReady = fatigue !== null && alarmAcknowledged !== null &&
    Object.values(restrictions).every(item => item.choice !== null && (!item.previous || item.reviewed));
  const isConfirmed = checkIn?.context?.state === 'confirmed' && !editingContext;
  const taskKey = checkIn ? `check-in:${checkIn.id}` : null;
  const handoff = planning?.taskHandoff?.taskKey === taskKey ? planning.taskHandoff : null;
  // A freshly recovered terminal snapshot supersedes any retained pending copy.
  const displayedPlan = proposalPlan && !['pending_approval', 'active'].includes(proposalPlan.revision_state)
    ? proposalPlan : handoff?.plan ?? proposalPlan;
  const reviewable = displayedPlan?.revision_state === 'pending_approval' && displayedPlan.proposal?.state === 'pending';
  const terminal = displayedPlan !== null && !reviewable && displayedPlan.revision_state !== 'active';
  const isCompleted = checkIn?.status === 'completed' || displayedPlan !== null;
  const expiryLabel = useMemo(() => {
    if (!checkIn?.context) return null;
    return new Date(checkIn.context.expires_at).toLocaleString('nl-NL');
  }, [checkIn]);

  const run = async <T,>(operation: () => Promise<T>, apply: (value: T) => void) => {
    if (mutationRunning.current) return;
    mutationRunning.current = true;
    setBusy(true);
    setError(null);
    try {
      const value = await operation();
      if (mounted.current) apply(value);
    } catch (caught) {
      if (mounted.current) setError(localizeRecoveryMessage(caught instanceof Error ? caught.message : 'De check-in is mislukt.', language));
    } finally {
      mutationRunning.current = false;
      if (mounted.current) setBusy(false);
    }
  };

  const restore = (result: WeeklyCheckIn, active: InjuryRestriction[], preserveReview = false) => {
    const restored = restoreRestrictions(result.context?.restrictions ?? [], active);
    const needsCurrentReview = !preserveReview && active.some(item => {
      if (item.cleared_at !== null || item.status === 'none') return false;
      const saved = result.context?.restrictions.find(answer => answer.discipline === item.discipline);
      return !saved || !sameRestriction(saved, item);
    });
    for (const discipline of disciplines) {
      if (preserveReview) restored[discipline].reviewed = restrictions[discipline].reviewed;
      else if (result.context?.state === 'confirmed' && !needsCurrentReview) restored[discipline].reviewed = true;
    }
    setRestrictionsState(restored);
    setBlockedDaysState(dayOffsetsForCandidate(result.week_start, result.context?.blocked_dates ?? []));
    setFatigueState(result.context?.fatigue_level ?? null);
    setReasonsState(new Set(result.context?.missed_workout_reasons ?? []));
    setRecurringConfirmedState(result.context?.recurring_activities_confirmed ?? null);
    setAlarmAcknowledgedState(result.context?.alarm_symptoms_acknowledged ?? null);
    setExternalActivitiesState(result.context?.external_activities ?? []);
    setContextDirty(needsCurrentReview);
    setEditingContext(result.context?.state === 'confirmed' && needsCurrentReview);
    setContextCandidate(null);
    setCheckIn(result);
  };

  const begin = () => run(
    async () => {
      const requestedWeek = beginWeekAttempt.current ?? weekStart;
      beginWeekAttempt.current = requestedWeek;
      const starting = startWeeklyCheckIn(accessToken, requestedWeek).catch((caught: unknown) => {
        if (mounted.current && caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'rejected' &&
          'status' in caught && caught.status === 422) beginWeekAttempt.current = null;
        throw caught;
      });
      const [result, active] = await Promise.all([starting, getInjuryRestrictions(accessToken)]);
      // The week-scoped check-in is the durable locator, including after restart.
      // The create endpoint replays its exact attachment without generation.
      const recovered = result.status === 'completed' || result.plan_proposal_id
        ? await createCheckInPlanProposal(accessToken, result.id) : null;
      if (recovered && planning) {
        await planning.receiveTaskPlan(`check-in:${result.id}`, recovered.plan);
      }
      return { result, active, recovered };
    },
    ({ result, active, recovered }) => {
      beginWeekAttempt.current = null;
      restore(result, active);
      setProposalPlan(recovered?.plan ?? null);
    },
  );

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
    void run(
      () => extractWeeklyCheckInContextCandidate(accessToken, checkIn.id, contextText.trim()),
      setContextCandidate,
    );
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
    if (!checkIn || !formReady || !recurringConfirmed) return;
    void run(async () => {
      const previous = saveAttempt.current;
      const input = previous ?? {
        expected_revision: checkIn.context_revision,
        blocked_dates: [...blockedDays].map((offset) =>
          dateAtOffset(checkIn.week_start, offset),
        ),
        fatigue_level: fatigue!,
        missed_workout_reasons: [...reasons],
        recurring_activities_confirmed: recurringConfirmed,
        external_activities: externalActivities,
        restrictions: (Object.keys(restrictions) as Discipline[]).map((discipline) =>
          restrictionPayload(discipline, restrictions[discipline]),
        ),
        alarm_symptoms_acknowledged: alarmAcknowledged!,
      };
      try {
        const result = await saveWeeklyCheckInContext(accessToken, checkIn.id, input);
        if (mounted.current) saveAttempt.current = null;
        return result;
      } catch (caught) {
        if (mounted.current && (previous || (caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown'))) saveAttempt.current = input;
        throw caught;
      }
    }, result => restore(result, Object.values(restrictions).flatMap(item => item.previous ? [item.previous] : []), true));
  };

  const confirm = () => {
    if (!checkIn?.context || contextDirty || !formReady || !recurringConfirmed) return;
    void run(
      async () => {
        const previous = confirmationAttempt.current;
        const input = previous ?? { revision: checkIn.context!.revision, fingerprint: checkIn.context!.fingerprint };
        try {
          const result = await confirmWeeklyCheckInContext(accessToken, checkIn.id, input.revision, input.fingerprint);
          if (mounted.current) confirmationAttempt.current = null;
          return result;
        } catch (caught) {
          if (mounted.current && (previous || (caught && typeof caught === 'object' && 'outcome' in caught && caught.outcome === 'unknown'))) confirmationAttempt.current = input;
          throw caught;
        }
      },
      result => restore(result, []),
    );
  };

  const makeProposal = () => {
    if (!checkIn || !isConfirmed || contextDirty || !formReady || !recurringConfirmed) return;
    void run(async () => {
      const result = await createCheckInPlanProposal(accessToken, checkIn.id);
      if (mounted.current) {
        setProposalPlan(result.plan);
        setCheckIn(current => current ? { ...current, status: 'completed', plan_proposal_id: result.proposal.id } : current);
      }
      if (!planning) throw new Error('Open de check-in vanuit de weekplanning om het voorstel te bewaren.');
      await planning.receiveTaskPlan(`check-in:${checkIn.id}`, result.plan);
    }, () => undefined);
  };

  const reject = () => {
    if (!checkIn || !reviewable || !displayedPlan?.proposal) return;
    const proposalId = displayedPlan.proposal.id;
    void run(async () => {
      await rejectPlanProposal(accessToken, proposalId);
      const result = await createCheckInPlanProposal(accessToken, checkIn.id);
      if (planning) await planning.receiveTaskPlan(`check-in:${checkIn.id}`, result.plan);
      return result;
    }, result => setProposalPlan(result.plan));
  };

  const approve = () => {
    if (!planning || !taskKey || !displayedPlan) return;
    void run(async () => {
      if (!handoff) {
        await planning.receiveTaskPlan(taskKey, displayedPlan);
        return false; // Review the retained proposal before a separate approval.
      }
      return planning.approveTaskPlan(taskKey, handoff.reviewed);
    }, completed => { if (completed) onBack(); });
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
        {error && checkIn && (saveAttempt.current || confirmationAttempt.current) ? <ActionButton disabled={busy}
          label={language === 'nl' ? 'Controleer opgeslagen check-in' : 'Check saved check-in'}
          onPress={() => void run(() => getWeeklyCheckIn(accessToken, checkIn.id), result => {
            if (saveAttempt.current && result.context_revision > saveAttempt.current.expected_revision) saveAttempt.current = null;
            if (result.context?.state === 'confirmed') confirmationAttempt.current = null;
            restore(result, []);
          })} /> : null}
        {busy ? <ActivityIndicator color={colors.primary} /> : null}

        {!checkIn ? (
          <Card elevated padding="form" style={styles.panel}>
            <View style={[styles.chip]}><Text variant="supporting" tone="primary">Zonder AI</Text></View>
            <Text style={styles.title}>Bereid je volgende week voor</Text>
            <Text style={styles.body}>
              Je antwoorden worden gestructureerd opgeslagen. Pas na jouw aparte
              bevestiging ontstaat een planvoorstel.
            </Text>
            <FormField disabled={busy}
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
              <FormField disabled={busy}
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
                    disabled={busy} label="Neem datums, vermoeidheid en redenen over"
                    onPress={useContextCandidate}
                  />
                  <ActionButton
                    disabled={busy} label="Negeer invulvoorstel"
                    onPress={() => setContextCandidate(null)}
                    secondary
                  />
                </View>
              ) : null}
              <Text style={styles.body}>Welke dagen zijn volledig geblokkeerd?</Text>
              <View style={styles.rowWrap}>
                {dayLabels.map((label, offset) => (
                  <ChoiceRow disabled={busy} key={label} label={label}  selected={blockedDays.has(offset)} mode="checkbox" onPress={() =>
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
                  <ChoiceRow disabled={busy} key={value} label={fatigueLabels[value]}  selected={fatigue === value} mode="radio" onPress={() => setFatigue(value)} />
                ))}
              </View>
              <Text style={styles.label}>Redenen voor gemiste trainingen</Text>
              <View style={styles.rowWrap}>
                {missedReasons.map(([value, label]) => (
                  <ChoiceRow disabled={busy} key={value} label={label}  selected={reasons.has(value)} mode="checkbox" onPress={() =>
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
                  {restrictions[discipline].previous ? <Notice tone="warning">
                    {`Bestaande beperking: ${restrictionLabels[restrictions[discipline].previous!.status]}. Herbeoordeling: ${new Date(restrictions[discipline].previous!.review_at).toLocaleDateString('nl-NL')}. De beperking vervalt niet door tijdsverloop.`}
                  </Notice> : null}
                  {(restrictions[discipline].previous?.professional_advice || restrictions[discipline].original?.professional_advice) ? <Text style={styles.body}>
                    {`Opgeslagen advies (${restrictions[discipline].previous?.source ?? restrictions[discipline].original?.source}): ${restrictions[discipline].previous?.professional_advice ?? restrictions[discipline].original?.professional_advice} - ${restrictions[discipline].previous?.professional_advice_at ?? restrictions[discipline].original?.professional_advice_at}`}
                  </Text> : null}
                  {restrictions[discipline].previous?.professional_advice && restrictions[discipline].original?.professional_advice &&
                    !sameRestriction(restrictions[discipline].original!, restrictions[discipline].previous!) ? <Text style={styles.body}>
                    {`Advies in dit opgeslagen antwoord (${restrictions[discipline].original!.source}): ${restrictions[discipline].original!.professional_advice} - ${restrictions[discipline].original!.professional_advice_at}`}
                  </Text> : null}
                  {restrictions[discipline].original && ['clearance_required', 'expired'].includes(restrictions[discipline].original!.status) ? <ChoiceRow
                    label={`Bestaande beperking behouden: ${restrictionLabels[restrictions[discipline].original!.status]}`}
                    accessibilityLabel={`${disciplineLabels[discipline]}: Bestaande beperking behouden`}
                    selected={restrictions[discipline].choice === 'retain'} mode="radio"
                    onPress={() => setRestrictions(current => ({ ...current, [discipline]: { ...current[discipline], choice: 'retain', reviewed: true } }))}
                  /> : null}
                  <View style={styles.rowWrap}>
                    {(
                      [
                        ['none', 'Vrij'],
                        ['low', 'Alleen rustig'],
                        ['blocked', 'Geblokkeerd'],
                        ['professional', 'Professioneel advies'],
                      ] as const
                    ).map(([value, label]) => (
                      <ChoiceRow disabled={busy} key={value} label={label} accessibilityLabel={`${disciplineLabels[discipline]}: ${label}`} selected={restrictions[discipline].choice === value} mode="radio" onPress={() =>
                          setRestrictions((current) => ({
                            ...current,
                            [discipline]: { ...current[discipline], choice: value, reviewed: true },
                          }))
                        } />
                    ))}
                  </View>
                  {restrictions[discipline].previous ? <ChoiceRow
                    label={`Ik heb de bestaande beperking voor ${disciplineLabels[discipline]} opnieuw beoordeeld.`}
                    selected={restrictions[discipline].reviewed} mode="checkbox"
                    onPress={() => setRestrictions(current => ({ ...current, [discipline]: { ...current[discipline], reviewed: !current[discipline].reviewed } }))}
                  /> : null}
                  {restrictions[discipline].choice === 'professional' ? (
                    <FormField disabled={busy}
                      label="Advies en herleidbare bron"
                      onChangeText={(advice) =>
                        setRestrictions((current) => ({
                          ...current,
                          [discipline]: { ...current[discipline], advice, adviceAt: advice === (current[discipline].original?.professional_advice ?? '') ? current[discipline].original?.professional_advice_at : new Date().toISOString() },
                        }))
                      }
                      value={restrictions[discipline].advice}
                    />
                  ) : null}
                </View>
              ))}
              <ChoiceRow disabled={busy}  label="Ik begrijp dat alarmsymptomen medische beoordeling vragen en niet door dit plan worden beoordeeld."  selected={alarmAcknowledged === true} mode="checkbox" onPress={() => setAlarmAcknowledged((value) => !value)} />
            </Card>

            <Card elevated padding="form" style={styles.panel}>
              <Text style={styles.title}>Sport buiten Wombo</Text>
              <ChoiceRow disabled={busy}  label="Ik heb mijn terugkerende sportactiviteiten voor deze week gecontroleerd."  selected={recurringConfirmed === true} mode="checkbox" onPress={() => setRecurringConfirmed((value) => !value)} />
              {externalActivities.map((activity, index) => (
                <View key={`${activity.scheduled_at}-${index}`} style={styles.activityRow}>
                  <Text style={styles.label}>{activity.name}</Text>
                  <Text style={styles.body}>
                    {disciplineLabels[activity.discipline]} · {activity.duration_minutes} min
                    {activity.strenuous ? ' · inspannend' : ''}
                    {activity.recurring ? ' · terugkerend' : ''}
                  </Text>
                  <QuickActionRow disabled={busy} label="Verwijderen" icon="close" onAction={() =>
                      setExternalActivities((current) =>
                        current.filter((_, currentIndex) => currentIndex !== index),
                      )
                    } />
                </View>
              ))}
              <FormField disabled={busy} label="Naam extra activiteit" onChangeText={setExternalName} value={externalName} />
              <View style={styles.rowWrap}>
                {disciplines.map((discipline) => (
                  <ChoiceRow disabled={busy} key={discipline} label={disciplineLabels[discipline]}  selected={externalDiscipline === discipline} mode="radio" onPress={() => setExternalDiscipline(discipline)} />
                ))}
              </View>
              <FormField disabled={busy}
                autoCapitalize="none"
                label="Tijdstip (ISO inclusief tijdzone)"
                onChangeText={setExternalScheduledAt}
                value={externalScheduledAt}
              />
              <FormField disabled={busy}
                inputMode="decimal"
                label="Geplande duur (minuten)"
                onChangeText={setExternalDuration}
                value={externalDuration}
              />
              <View style={styles.rowWrap}>
                <ChoiceRow disabled={busy}  label="Inspannend"  selected={externalStrenuous} mode="checkbox" onPress={() => setExternalStrenuous((value) => !value)} />
                <ChoiceRow disabled={busy}  label="Terugkerend"  selected={externalRecurring} mode="checkbox" onPress={() => setExternalRecurring((value) => !value)} />
                <ActionButton disabled={busy} label="Toevoegen" onPress={addExternalActivity} secondary />
              </View>
            </Card>

            <Card elevated padding="form" style={styles.panel}>
              {!formReady ? <Text style={styles.body}>Beantwoord elke discipline en vermoeidheid, controleer de alarmmelding en beoordeel bestaande beperkingen voordat je opslaat.</Text> : null}
              <ActionButton disabled={busy || !recurringConfirmed || !formReady} label="Context opslaan" onPress={save} />
              {checkIn.context ? (
                <>
                  <Text style={styles.body}>
                    Bron: gestructureerd formulier · geldig tot {expiryLabel}
                  </Text>
                  <ActionButton disabled={busy || contextDirty || !formReady || !recurringConfirmed} label="Deze context bevestigen" onPress={confirm} />
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
            {checkIn.context?.restrictions.map(item => <View key={item.discipline}>
              <Text style={styles.body}>{`${disciplineLabels[item.discipline]}: ${restrictionLabels[item.status]}`}</Text>
              {item.professional_advice ? <Text style={styles.body}>{`${item.source}: ${item.professional_advice} - ${item.professional_advice_at}`}</Text> : null}
            </View>)}
            <ActionButton disabled={busy || contextDirty || !formReady || !recurringConfirmed} label="Maak planvoorstel" onPress={makeProposal} />
            <ActionButton disabled={busy} label="Antwoorden opnieuw beoordelen" secondary onPress={() => { setEditingContext(true); setContextDirty(true); }} />
          </Card>
        ) : null}

        {displayedPlan ? (
          <Card elevated padding="form" style={styles.panel}>
            <View style={[styles.chip, styles.pendingChip]}><Text variant="supporting" tone="warning">{terminal ? 'Voorstel afgesloten' : handoff?.receipt || displayedPlan.revision_state === 'active' ? 'Goedkeuring ontvangen' : 'Wacht op jouw goedkeuring'}</Text></View>
            <Text style={styles.title}>Voorstel voor {displayedPlan.week_start}</Text>
            <Text style={styles.body}>
              {displayedPlan.workouts.length} trainingen · {displayedPlan.rest_days.length} rustdagen
            </Text>
            {displayedPlan.warnings.map((warning) => (
              <Notice key={warning.id ?? warning.code} tone="warning">{warning.message}</Notice>
            ))}
            {handoff && ['read', 'persist'].includes(handoff.phase) ? <Notice tone="warning">Je goedkeuring is ontvangen. De synchronisatie is nog niet voltooid. Hervat zonder opnieuw goed te keuren.</Notice> : null}
            {handoff?.phase === 'verify' ? <Notice tone="warning">De uitkomst is onzeker. Controleer eerst de opgeslagen status voordat je opnieuw beslist.</Notice> : null}
            {terminal ? <Notice>{`Dit voorstel is afgesloten (${displayedPlan.proposal?.state ?? displayedPlan.revision_state}). Er wordt geen vervangend voorstel gemaakt.`}</Notice> : null}
            {!terminal && handoff?.phase !== 'complete' ? <ActionButton disabled={busy || !planning} label={handoff?.phase === 'verify' ? 'Goedkeuringsstatus controleren' : handoff && ['read', 'persist'].includes(handoff.phase) ? 'Synchronisatie hervatten' : !handoff ? 'Voorstel bewaren' : 'Voorstel goedkeuren'} onPress={approve} /> : null}
            {reviewable ? <ActionButton disabled={busy || handoff?.phase !== 'pending'} label="Voorstel afwijzen" onPress={reject} secondary /> : null}
            <ActionButton label={handoff?.phase === 'complete' ? 'Terug naar Week' : 'Later beslissen'} onPress={onBack} secondary />
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
