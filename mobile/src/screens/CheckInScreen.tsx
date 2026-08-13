import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approvePlanProposal,
  confirmWeeklyCheckInContext,
  createCheckInPlanProposal,
  saveWeeklyCheckInContext,
  startWeeklyCheckIn,
} from '../api/client';
import type {
  AthletePlanChoice,
  Discipline,
  ExternalActivity,
  FatigueLevel,
  RestrictionStatus,
  WeeklyCheckIn,
  WeeklyPlan,
} from '../api/types';
import { FormField } from '../components/FormField';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

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
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[
        styles.action,
        secondary && styles.actionSecondary,
        disabled && styles.disabled,
      ]}
    >
      <Text style={[styles.actionText, secondary && styles.actionSecondaryText]}>
        {label}
      </Text>
    </Pressable>
  );
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
    if (!proposalPlan?.proposal || proposalPlan.proposal.base_plan_revision === null) {
      return;
    }
    void run(async () => {
      await approvePlanProposal(
        accessToken,
        proposalPlan.proposal!.id,
        proposalPlan.proposal!.base_plan_revision!,
      );
      onBack();
    });
  };

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" onPress={onBack}>
          <Text style={styles.link}>Weekplanning</Text>
        </Pressable>
        <View>
          <Text style={styles.logo}>Start23</Text>
          <Text style={styles.caption}>Wekelijkse check-in</Text>
        </View>
        <Pressable accessibilityRole="button" onPress={() => void onSignOut()}>
          <Text style={styles.link}>Afmelden</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}

        {!checkIn ? (
          <View style={styles.panel}>
            <StatusPill label="Zonder AI" tone="brand" />
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
          </View>
        ) : null}

        {checkIn && !isConfirmed && !isCompleted ? (
          <>
            <View style={styles.panel}>
              <StatusPill label="Gestructureerde bron" tone="brand" />
              <Text style={styles.title}>Week van {checkIn.week_start}</Text>
              <Text style={styles.body}>Welke dagen zijn volledig geblokkeerd?</Text>
              <View style={styles.rowWrap}>
                {dayLabels.map((label, offset) => (
                  <Pressable
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: blockedDays.has(offset) }}
                    key={label}
                    onPress={() =>
                      setBlockedDays((current) => {
                        const next = new Set(current);
                        if (next.has(offset)) next.delete(offset);
                        else next.add(offset);
                        return next;
                      })
                    }
                    style={[styles.choice, blockedDays.has(offset) && styles.active]}
                  >
                    <Text style={blockedDays.has(offset) ? styles.activeText : styles.choiceText}>
                      {label}
                    </Text>
                  </Pressable>
                ))}
              </View>
              <Text style={styles.label}>Vermoeidheid</Text>
              <View style={styles.rowWrap}>
                {(Object.keys(fatigueLabels) as FatigueLevel[]).map((value) => (
                  <Pressable
                    key={value}
                    onPress={() => setFatigue(value)}
                    style={[styles.pill, fatigue === value && styles.active]}
                  >
                    <Text style={fatigue === value ? styles.activeText : styles.choiceText}>
                      {fatigueLabels[value]}
                    </Text>
                  </Pressable>
                ))}
              </View>
              <Text style={styles.label}>Redenen voor gemiste trainingen</Text>
              <View style={styles.rowWrap}>
                {missedReasons.map(([value, label]) => (
                  <Pressable
                    key={value}
                    onPress={() =>
                      setReasons((current) => {
                        const next = new Set(current);
                        if (next.has(value)) next.delete(value);
                        else next.add(value);
                        return next;
                      })
                    }
                    style={[styles.pill, reasons.has(value) && styles.active]}
                  >
                    <Text style={reasons.has(value) ? styles.activeText : styles.choiceText}>
                      {label}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </View>

            <View style={styles.panel}>
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
                      <Pressable
                        key={value}
                        onPress={() =>
                          setRestrictions((current) => ({
                            ...current,
                            [discipline]: { ...current[discipline], choice: value },
                          }))
                        }
                        style={[
                          styles.pill,
                          restrictions[discipline].choice === value && styles.active,
                        ]}
                      >
                        <Text
                          style={
                            restrictions[discipline].choice === value
                              ? styles.activeText
                              : styles.choiceText
                          }
                        >
                          {label}
                        </Text>
                      </Pressable>
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
              <Pressable
                accessibilityRole="checkbox"
                accessibilityState={{ checked: alarmAcknowledged }}
                onPress={() => setAlarmAcknowledged((value) => !value)}
                style={[styles.notice, alarmAcknowledged && styles.noticeChecked]}
              >
                <Text style={styles.body}>
                  Ik begrijp dat alarmsymptomen medische beoordeling vragen en
                  niet door dit plan worden beoordeeld.
                </Text>
              </Pressable>
            </View>

            <View style={styles.panel}>
              <Text style={styles.title}>Sport buiten Start23</Text>
              <Pressable
                accessibilityRole="checkbox"
                accessibilityState={{ checked: recurringConfirmed }}
                onPress={() => setRecurringConfirmed((value) => !value)}
                style={[styles.notice, recurringConfirmed && styles.noticeChecked]}
              >
                <Text style={styles.body}>
                  Ik heb mijn terugkerende sportactiviteiten voor deze week
                  gecontroleerd.
                </Text>
              </Pressable>
              {externalActivities.map((activity, index) => (
                <View key={`${activity.scheduled_at}-${index}`} style={styles.activityRow}>
                  <Text style={styles.label}>{activity.name}</Text>
                  <Text style={styles.body}>
                    {disciplineLabels[activity.discipline]} · {activity.duration_minutes} min
                    {activity.strenuous ? ' · inspannend' : ''}
                    {activity.recurring ? ' · terugkerend' : ''}
                  </Text>
                  <Pressable
                    onPress={() =>
                      setExternalActivities((current) =>
                        current.filter((_, currentIndex) => currentIndex !== index),
                      )
                    }
                  >
                    <Text style={styles.link}>Verwijderen</Text>
                  </Pressable>
                </View>
              ))}
              <FormField label="Naam extra activiteit" onChangeText={setExternalName} value={externalName} />
              <View style={styles.rowWrap}>
                {disciplines.map((discipline) => (
                  <Pressable
                    key={discipline}
                    onPress={() => setExternalDiscipline(discipline)}
                    style={[styles.pill, externalDiscipline === discipline && styles.active]}
                  >
                    <Text style={externalDiscipline === discipline ? styles.activeText : styles.choiceText}>
                      {disciplineLabels[discipline]}
                    </Text>
                  </Pressable>
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
                <Pressable
                  onPress={() => setExternalStrenuous((value) => !value)}
                  style={[styles.pill, externalStrenuous && styles.active]}
                >
                  <Text style={externalStrenuous ? styles.activeText : styles.choiceText}>Inspannend</Text>
                </Pressable>
                <Pressable
                  onPress={() => setExternalRecurring((value) => !value)}
                  style={[styles.pill, externalRecurring && styles.active]}
                >
                  <Text style={externalRecurring ? styles.activeText : styles.choiceText}>Terugkerend</Text>
                </Pressable>
                <ActionButton label="Toevoegen" onPress={addExternalActivity} secondary />
              </View>
            </View>

            <View style={styles.panel}>
              <ActionButton disabled={busy || !recurringConfirmed} label="Context opslaan" onPress={save} />
              {checkIn.context ? (
                <>
                  <Text style={styles.body}>
                    Bron: gestructureerd formulier · geldig tot {expiryLabel}
                  </Text>
                  <ActionButton disabled={busy} label="Deze context bevestigen" onPress={confirm} />
                </>
              ) : null}
            </View>
          </>
        ) : null}

        {checkIn && isConfirmed && !isCompleted ? (
          <View style={styles.panel}>
            <StatusPill label="Context bevestigd" tone="brand" />
            <Text style={styles.title}>Klaar voor het voorstel</Text>
            <Text style={styles.body}>
              Alleen een nieuwe, nog goed te keuren planrevisie wordt gemaakt.
            </Text>
            <ActionButton disabled={busy} label="Maak planvoorstel" onPress={makeProposal} />
          </View>
        ) : null}

        {proposalPlan ? (
          <View style={styles.panel}>
            <StatusPill label="Wacht op jouw goedkeuring" tone="accent" />
            <Text style={styles.title}>Voorstel voor {proposalPlan.week_start}</Text>
            <Text style={styles.body}>
              {proposalPlan.workouts.length} trainingen · {proposalPlan.rest_days.length} rustdagen
            </Text>
            {proposalPlan.warnings.map((warning) => (
              <Text key={warning.id ?? warning.code} style={styles.warning}>
                {warning.message}
              </Text>
            ))}
            <ActionButton disabled={busy} label="Voorstel goedkeuren" onPress={approve} />
            <ActionButton label="Later beslissen" onPress={onBack} secondary />
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  logo: { color: colors.brand, fontSize: 20, fontWeight: '900', textAlign: 'center' },
  caption: { color: colors.inkMuted, fontSize: 11, textAlign: 'center' },
  link: { color: colors.brand, fontSize: 12, fontWeight: '800' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: 80 },
  panel: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.lg,
  },
  subsection: { borderTopColor: colors.line, borderTopWidth: 1, gap: spacing.sm, paddingTop: spacing.md },
  title: { color: colors.ink, fontSize: 22, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  label: { color: colors.ink, fontSize: 13, fontWeight: '800' },
  rowWrap: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  choice: {
    alignItems: 'center',
    borderColor: colors.line,
    borderRadius: radius.pill,
    borderWidth: 1,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  pill: { backgroundColor: colors.surfaceMuted, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  active: { backgroundColor: colors.brand, borderColor: colors.brand },
  choiceText: { color: colors.ink, fontSize: 12, fontWeight: '700' },
  activeText: { color: colors.white, fontSize: 12, fontWeight: '800' },
  notice: { backgroundColor: colors.surfaceMuted, borderRadius: radius.sm, padding: spacing.md },
  noticeChecked: { backgroundColor: colors.brandSoft },
  activityRow: { borderTopColor: colors.line, borderTopWidth: 1, gap: spacing.xs, paddingTop: spacing.sm },
  action: { alignItems: 'center', backgroundColor: colors.brand, borderRadius: radius.pill, padding: 14 },
  actionSecondary: { backgroundColor: colors.surface, borderColor: colors.line, borderWidth: 1 },
  actionText: { color: colors.white, fontSize: 14, fontWeight: '900' },
  actionSecondaryText: { color: colors.brand },
  disabled: { opacity: 0.45 },
  warning: { backgroundColor: colors.accentSoft, borderRadius: radius.sm, color: colors.ink, lineHeight: 19, padding: spacing.md },
  error: { backgroundColor: colors.dangerSoft, borderRadius: radius.sm, color: colors.danger, padding: spacing.md },
});
