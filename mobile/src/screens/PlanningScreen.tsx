import * as SecureStore from 'expo-secure-store';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approvePlanProposal,
  createScheduleProposal,
  createWeeklyPlanProposal,
  getCalendar,
  getOnboarding,
  getWeeklyPlan,
  getWorkoutDeck,
  markGoalAchieved,
  movePlannedWorkout,
  rejectPlanProposal,
  validatePlanLayout,
} from '../api/client';
import type {
  AvailabilityWindow,
  Discipline,
  PlannedWorkout,
  PrimaryRaceGoal,
  RestDay,
  WeeklyPlan,
  WorkoutDeck,
} from '../api/types';
import { FormField } from '../components/FormField';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

type PlanningScreenProps = {
  accessToken: string;
  onSignOut: () => Promise<void>;
  onBackToOnboarding: () => void;
  onOpenActivities: () => void;
  onOpenCheckIn: () => void;
};

type ViewName = 'plan' | 'deck' | 'calendar';

const dayLabels = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'] as const;
const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
};
const latestPlanIdKey = 'start23.latest-plan-id';

async function rememberPlanId(planId: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (planId === null) {
    await SecureStore.deleteItemAsync(latestPlanIdKey);
  } else {
    await SecureStore.setItemAsync(latestPlanIdKey, planId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }
}

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function nextMonday(): string {
  const value = new Date();
  value.setHours(12, 0, 0, 0);
  const daysUntilMonday = (8 - value.getDay()) % 7 || 7;
  value.setDate(value.getDate() + daysUntilMonday);
  return isoDate(value);
}

function addDays(dateValue: string, days: number): Date {
  const value = new Date(`${dateValue}T12:00:00`);
  value.setDate(value.getDate() + days);
  return value;
}

function availabilityFor(
  weekStart: string,
  selectedDays: ReadonlySet<number>,
  startTime: string,
  endTime: string,
): AvailabilityWindow[] {
  const timePattern = /^([01]\d|2[0-3]):([0-5]\d)$/;
  const startMatch = timePattern.exec(startTime);
  const endMatch = timePattern.exec(endTime);
  if (!startMatch || !endMatch) {
    throw new Error('Gebruik tijden in het formaat UU:MM.');
  }
  return [...selectedDays]
    .sort((left, right) => left - right)
    .map((dayOffset) => {
      const startsAt = addDays(weekStart, dayOffset);
      const endsAt = addDays(weekStart, dayOffset);
      startsAt.setHours(Number(startMatch[1]), Number(startMatch[2]), 0, 0);
      endsAt.setHours(Number(endMatch[1]), Number(endMatch[2]), 0, 0);
      if (endsAt <= startsAt) {
        throw new Error('De eindtijd moet na de starttijd liggen.');
      }
      return {
        starts_at: startsAt.toISOString(),
        ends_at: endsAt.toISOString(),
      };
    });
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
        disabled && styles.actionDisabled,
      ]}
    >
      <Text
        style={[
          styles.actionText,
          secondary && styles.actionSecondaryText,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

function WorkoutCard({ workout }: { workout: PlannedWorkout }) {
  const scheduled = new Date(workout.scheduled_at);
  return (
    <View style={styles.workoutCard}>
      <View style={styles.cardHeader}>
        <StatusPill
          label={disciplineLabels[workout.discipline]}
          tone={workout.intensity_bucket === 'high' ? 'accent' : 'neutral'}
        />
        <Text style={styles.cardMeta}>
          {scheduled.toLocaleDateString('nl-NL', {
            weekday: 'short',
            day: 'numeric',
          })}{' '}
          ·{' '}
          {scheduled.toLocaleTimeString('nl-NL', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </Text>
      </View>
      <Text style={styles.cardTitle}>{workout.name}</Text>
      <Text style={styles.cardDescription}>{workout.description}</Text>
      <Text style={styles.cardMeta}>
        {Number(workout.duration_minutes)} min · RPE {workout.expected_rpe_min}–
        {workout.expected_rpe_max}
      </Text>
    </View>
  );
}

export function PlanningScreen({
  accessToken,
  onBackToOnboarding,
  onOpenActivities,
  onOpenCheckIn,
  onSignOut,
}: PlanningScreenProps) {
  const [view, setView] = useState<ViewName>('plan');
  const [weekStart, setWeekStart] = useState(nextMonday);
  const [startTime, setStartTime] = useState('07:00');
  const [endTime, setEndTime] = useState('09:00');
  const [selectedDays, setSelectedDays] = useState<Set<number>>(
    () => new Set([0, 2, 5]),
  );
  const [injuries, setInjuries] = useState<Set<Discipline>>(() => new Set());
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const [deck, setDeck] = useState<WorkoutDeck | null>(null);
  const [selectedTemplates, setSelectedTemplates] = useState<Set<string>>(
    () => new Set(),
  );
  const [eligibleTemplateIds, setEligibleTemplateIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [calendarWorkouts, setCalendarWorkouts] = useState<PlannedWorkout[]>([]);
  const [calendarRestDays, setCalendarRestDays] = useState<RestDay[]>([]);
  const [moveTimes, setMoveTimes] = useState<Record<string, string>>({});
  const [primaryGoal, setPrimaryGoal] = useState<PrimaryRaceGoal | null>(null);
  const [maintenanceMarked, setMaintenanceMarked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availability = useMemo(() => {
    try {
      return availabilityFor(weekStart, selectedDays, startTime, endTime);
    } catch {
      return [];
    }
  }, [endTime, selectedDays, startTime, weekStart]);

  useEffect(() => {
    if (Platform.OS === 'web') return;
    let mounted = true;
    SecureStore.getItemAsync(latestPlanIdKey)
      .then(async (planId) => {
        if (!planId) return;
        try {
          const restored = await getWeeklyPlan(accessToken, planId);
          if (mounted) {
            setPlan(restored);
            setWeekStart(restored.week_start);
            setInjuries(new Set(restored.confirmed_injuries));
            setSelectedTemplates(
              new Set(
                restored.workouts.map((workout) => workout.template_id),
              ),
            );
          }
        } catch {
          await rememberPlanId(null);
        }
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  useEffect(() => {
    getOnboarding(accessToken)
      .then((state) => setPrimaryGoal(state.primary_goal))
      .catch(() => undefined);
  }, [accessToken]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De planningsactie is niet gelukt.',
      );
    } finally {
      setBusy(false);
    }
  };

  const toggleDay = (day: number) => {
    setSelectedDays((current) => {
      const next = new Set(current);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  };

  const toggleInjury = (discipline: Discipline) => {
    setInjuries((current) => {
      const next = new Set(current);
      if (next.has(discipline)) next.delete(discipline);
      else next.add(discipline);
      return next;
    });
  };

  const generate = () =>
    run(async () => {
      const windows = availabilityFor(
        weekStart,
        selectedDays,
        startTime,
        endTime,
      );
      if (windows.length === 0) {
        throw new Error('Kies minstens één beschikbare trainingsdag.');
      }
      const result = await createWeeklyPlanProposal(accessToken, {
        week_start: weekStart,
        availability: windows,
        confirmed_injuries: [...injuries],
      });
      await rememberPlanId(result.plan.id);
      setPlan(result.plan);
      setDeck(null);
      setEligibleTemplateIds(new Set());
      setSelectedTemplates(
        new Set(result.plan.workouts.map((workout) => workout.template_id)),
      );
    });

  const approve = () => {
    if (!plan?.proposal || plan.proposal.base_plan_revision === null) return;
    void run(async () => {
      await approvePlanProposal(
        accessToken,
        plan.proposal!.id,
        plan.proposal!.base_plan_revision!,
      );
      setPlan(await getWeeklyPlan(accessToken, plan.id));
    });
  };

  const reject = () => {
    if (!plan?.proposal) return;
    void run(async () => {
      await rejectPlanProposal(accessToken, plan.proposal!.id);
      setPlan(await getWeeklyPlan(accessToken, plan.id, plan.revision));
    });
  };

  const openDeck = () => {
    setView('deck');
    if (!plan || deck) return;
    void run(async () => {
      const result = await getWorkoutDeck(accessToken, plan.id);
      setDeck(result);
      setEligibleTemplateIds(new Set(result.templates.map((template) => template.id)));
      if (selectedTemplates.size === 0) {
        setSelectedTemplates(
          new Set(plan.workouts.map((workout) => workout.template_id)),
        );
      }
    });
  };

  const toggleTemplate = (templateId: string) => {
    if (!plan) return;
    const next = new Set(selectedTemplates);
    if (next.has(templateId)) next.delete(templateId);
    else next.add(templateId);
    setSelectedTemplates(next);
    void run(async () => {
      const recalculated = await getWorkoutDeck(
        accessToken,
        plan.id,
        plan.revision,
        [...next],
      );
      setEligibleTemplateIds(
        new Set([
          ...next,
          ...recalculated.templates.map((template) => template.id),
        ]),
      );
    });
  };

  const moveWorkout = (workout: PlannedWorkout) => {
    if (!plan?.active_revision) return;
    const scheduledAt = moveTimes[workout.id] ?? workout.scheduled_at;
    if (Number.isNaN(new Date(scheduledAt).getTime())) {
      setError('Gebruik een geldig ISO-tijdstip inclusief tijdzone.');
      return;
    }
    void run(async () => {
      const workouts = plan.workouts.map((item) => ({
        workout_id: item.id,
        scheduled_at: item.id === workout.id ? scheduledAt : item.scheduled_at,
      }));
      const validation = await validatePlanLayout(
        accessToken,
        plan.id,
        plan.active_revision!,
        workouts,
      );
      const apply = async () => {
        const updated = await movePlannedWorkout(
          accessToken,
          workout.id,
          plan.active_revision!,
          scheduledAt,
        );
        setPlan(updated);
        setMoveTimes((current) => ({
          ...current,
          [workout.id]: scheduledAt,
        }));
      };
      if (validation.warnings.length === 0) {
        await apply();
        return;
      }
      Alert.alert(
        'Let op bij verplaatsen',
        validation.warnings.map((warning) => warning.message).join('\n\n'),
        [
          { text: 'Annuleren', style: 'cancel' },
          { text: 'Toch verplaatsen', onPress: () => void run(apply) },
        ],
      );
    });
  };

  const confirmGoalAchievement = () => {
    if (!primaryGoal) return;
    Alert.alert(
      'Doel behaald?',
      'Nieuwe voorstellen gaan naar onderhoud: geen opbouw, wel het 4+1-ritme en de rustige/intensieve verdeling.',
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Bevestigen',
          onPress: () =>
            void run(async () => {
              await markGoalAchieved(accessToken, primaryGoal.id, isoDate(new Date()));
              setMaintenanceMarked(true);
            }),
        },
      ],
    );
  };

  const proposeSelection = () => {
    if (!plan?.active_revision) return;
    void run(async () => {
      const result = await createScheduleProposal(accessToken, plan.id, {
        expected_base_revision: plan.active_revision!,
        availability: availabilityFor(
          weekStart,
          selectedDays,
          startTime,
          endTime,
        ),
        confirmed_injuries: [...injuries],
        selected_template_ids: [...selectedTemplates],
      });
      await rememberPlanId(result.plan.id);
      setPlan(result.plan);
      setView('plan');
    });
  };

  const openCalendar = () => {
    setView('calendar');
    void run(async () => {
      const start = addDays(plan?.week_start ?? weekStart, 0);
      start.setHours(0, 0, 0, 0);
      const end = addDays(plan?.week_start ?? weekStart, 7);
      end.setHours(0, 0, 0, 0);
      const result = await getCalendar(
        accessToken,
        start.toISOString(),
        end.toISOString(),
      );
      setCalendarWorkouts(result.workouts);
      setCalendarRestDays(result.rest_days);
    });
  };

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <View style={styles.header}>
        <View>
          <Text style={styles.logo}>Start23</Text>
          <Text style={styles.headerCaption}>Weekplanning</Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable accessibilityRole="button" onPress={onOpenCheckIn}>
            <Text style={styles.link}>Wekelijkse check-in</Text>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={onOpenActivities}>
            <Text style={styles.link}>Training & RPE</Text>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => void onSignOut()}>
            <Text style={styles.link}>Afmelden</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.tabs}>
        <Pressable onPress={() => setView('plan')} style={styles.tab}>
          <Text style={[styles.tabText, view === 'plan' && styles.tabTextActive]}>
            Voorstel
          </Text>
        </Pressable>
        <Pressable onPress={openDeck} style={styles.tab}>
          <Text style={[styles.tabText, view === 'deck' && styles.tabTextActive]}>
            Deck
          </Text>
        </Pressable>
        <Pressable onPress={openCalendar} style={styles.tab}>
          <Text
            style={[styles.tabText, view === 'calendar' && styles.tabTextActive]}
          >
            Kalender
          </Text>
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}

        {view === 'plan' ? (
          <>
            {!plan ? (
              <View style={styles.panel}>
                <StatusPill label="Jij bevestigt" tone="brand" />
                <Text style={styles.title}>Wanneer kun je trainen?</Text>
                <Text style={styles.body}>
                  Kies je beschikbare dagen en tijd. Het resultaat blijft een
                  voorstel totdat jij het goedkeurt.
                </Text>
                <FormField
                  autoCapitalize="none"
                  label="Week start op maandag"
                  onChangeText={setWeekStart}
                  placeholder="JJJJ-MM-DD"
                  value={weekStart}
                />
                <View style={styles.dayRow}>
                  {dayLabels.map((label, index) => (
                    <Pressable
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: selectedDays.has(index) }}
                      key={label}
                      onPress={() => toggleDay(index)}
                      style={[
                        styles.choice,
                        selectedDays.has(index) && styles.choiceActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.choiceText,
                          selectedDays.has(index) && styles.choiceTextActive,
                        ]}
                      >
                        {label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                <View style={styles.timeRow}>
                  <View style={styles.timeField}>
                    <FormField
                      label="Vanaf"
                      onChangeText={setStartTime}
                      value={startTime}
                    />
                  </View>
                  <View style={styles.timeField}>
                    <FormField
                      label="Tot"
                      onChangeText={setEndTime}
                      value={endTime}
                    />
                  </View>
                </View>
                <Text style={styles.fieldLabel}>Bevestigde blessure</Text>
                <View style={styles.choiceRow}>
                  {(['swim', 'bike', 'run'] as const).map((discipline) => (
                    <Pressable
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: injuries.has(discipline) }}
                      key={discipline}
                      onPress={() => toggleInjury(discipline)}
                      style={[
                        styles.disciplineChoice,
                        injuries.has(discipline) && styles.injuryChoice,
                      ]}
                    >
                      <Text style={styles.choiceText}>
                        {disciplineLabels[discipline]}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                <ActionButton
                  disabled={busy || availability.length === 0}
                  label="Maak weekvoorstel"
                  onPress={() => void generate()}
                />
                <ActionButton
                  label="Terug naar intake"
                  onPress={onBackToOnboarding}
                  secondary
                />
              </View>
            ) : (
              <>
                <View style={styles.panel}>
                  <View style={styles.cardHeader}>
                    <StatusPill
                      label={
                        plan.revision_state === 'active'
                          ? 'Actief'
                          : plan.revision_state === 'pending_approval'
                            ? 'Wacht op jou'
                            : plan.revision_state
                      }
                      tone={
                        plan.revision_state === 'active' ? 'brand' : 'accent'
                      }
                    />
                    <Text style={styles.cardMeta}>Revisie {plan.revision}</Text>
                  </View>
                  <Text style={styles.title}>Week van {plan.week_start}</Text>
                  <Text style={styles.body}>
                    {Number(plan.total_duration_minutes)} minuten ·{' '}
                    {plan.workouts.length} trainingen · fase {plan.phase}
                  </Text>
                  <Text style={styles.body}>
                    {plan.display_low_intensity_percent}% rustig /{' '}
                    {plan.display_high_intensity_percent}% intensief
                  </Text>
                  <Text style={styles.hint}>
                    {Number(plan.low_intensity_minutes)} min rustig ·{' '}
                    {Number(plan.high_intensity_minutes)} min intensief
                  </Text>
                  {primaryGoal ? (
                    <ActionButton
                      disabled={busy || maintenanceMarked}
                      label={
                        maintenanceMarked
                          ? 'Onderhoudsmodus bevestigd'
                          : `Markeer “${primaryGoal.title}” als behaald`
                      }
                      onPress={confirmGoalAchievement}
                      secondary
                    />
                  ) : null}
                  {plan.warnings.map((warning) => (
                    <View key={warning.id ?? warning.code} style={styles.warning}>
                      <Text style={styles.warningTitle}>{warning.rule_id}</Text>
                      <Text style={styles.warningText}>{warning.message}</Text>
                    </View>
                  ))}
                  {plan.proposal?.state === 'pending' ? (
                    <View style={styles.decisionRow}>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label="Goedkeuren"
                          onPress={approve}
                        />
                      </View>
                      <View style={styles.decisionButton}>
                        <ActionButton
                          disabled={busy}
                          label="Afwijzen"
                          onPress={reject}
                          secondary
                        />
                      </View>
                    </View>
                  ) : null}
                  {['rejected', 'expired'].includes(plan.revision_state) ? (
                    <ActionButton
                      label="Nieuw voorstel voorbereiden"
                      onPress={() => {
                        setPlan(null);
                        setDeck(null);
                        void rememberPlanId(null);
                      }}
                      secondary
                    />
                  ) : null}
                </View>
                {plan.workouts.map((workout) => (
                  <View key={workout.id} style={styles.workoutStack}>
                    <WorkoutCard workout={workout} />
                    {plan.revision_state === 'active' ? (
                      <View style={styles.movePanel}>
                        <FormField
                          autoCapitalize="none"
                          label="Nieuw tijdstip (ISO inclusief tijdzone)"
                          onChangeText={(value) =>
                            setMoveTimes((current) => ({
                              ...current,
                              [workout.id]: value,
                            }))
                          }
                          value={moveTimes[workout.id] ?? workout.scheduled_at}
                        />
                        <ActionButton
                          disabled={busy}
                          label="Controleer en verplaats"
                          onPress={() => moveWorkout(workout)}
                          secondary
                        />
                      </View>
                    ) : null}
                  </View>
                ))}
              </>
            )}
          </>
        ) : null}

        {view === 'deck' ? (
          <View style={styles.panel}>
            <Text style={styles.title}>Beschikbare trainingen</Text>
            {!plan ? (
              <Text style={styles.body}>Maak eerst een weekvoorstel.</Text>
            ) : null}
            {deck?.templates.map((template) => {
              const selected = selectedTemplates.has(template.id);
              const eligible =
                selected || eligibleTemplateIds.has(template.id);
              return (
                <Pressable
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: selected }}
                  disabled={!eligible || busy}
                  key={template.id}
                  onPress={() => toggleTemplate(template.id)}
                  style={[
                    styles.deckCard,
                    selected && styles.deckCardSelected,
                    !eligible && styles.actionDisabled,
                  ]}
                >
                  <Text style={styles.cardTitle}>{template.name}</Text>
                  <Text style={styles.cardDescription}>
                    {disciplineLabels[template.discipline]} ·{' '}
                    {Number(template.duration_minutes)} min · RPE{' '}
                    {template.expected_rpe_min}–{template.expected_rpe_max}
                  </Text>
                </Pressable>
              );
            })}
            {plan?.active_revision ? (
              <ActionButton
                disabled={busy || selectedTemplates.size === 0}
                label="Maak nieuw voorstel met selectie"
                onPress={proposeSelection}
              />
            ) : (
              <Text style={styles.hint}>
                Keur het eerste voorstel goed voordat je een vervangend deck
                maakt.
              </Text>
            )}
          </View>
        ) : null}

        {view === 'calendar' ? (
          <View style={styles.panel}>
            <Text style={styles.title}>Actieve kalender</Text>
            <Text style={styles.body}>
              Alleen goedgekeurde trainingen verschijnen hier.
            </Text>
            {calendarWorkouts.length === 0 && !busy ? (
              <Text style={styles.hint}>Geen actieve trainingen in deze week.</Text>
            ) : null}
            {calendarWorkouts.map((workout) => (
              <WorkoutCard key={workout.id} workout={workout} />
            ))}
            {calendarRestDays.map((restDay) => (
              <View key={restDay.date} style={styles.restDay}>
                <StatusPill label="Rustdag" tone="neutral" />
                <Text style={styles.cardTitle}>{restDay.date}</Text>
                <Text style={styles.body}>
                  {restDay.reason === 'restriction_rest'
                    ? 'Bewuste rust door bevestigde beperkingen.'
                    : 'Bewust leeg gelaten in het actieve plan.'}
                </Text>
              </View>
            ))}
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
  logo: { color: colors.brand, fontSize: 22, fontWeight: '900' },
  headerCaption: { color: colors.inkMuted, fontSize: 12, marginTop: 2 },
  headerActions: { alignItems: 'flex-end', gap: spacing.xs },
  link: { color: colors.brand, fontSize: 13, fontWeight: '800' },
  tabs: {
    borderBottomColor: colors.line,
    borderBottomWidth: 1,
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
  },
  tab: { flex: 1, paddingVertical: spacing.sm },
  tabText: { color: colors.inkMuted, textAlign: 'center' },
  tabTextActive: { color: colors.brand, fontWeight: '900' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: 80 },
  panel: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: { color: colors.ink, fontSize: 23, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 14, lineHeight: 21 },
  fieldLabel: { color: colors.ink, fontSize: 13, fontWeight: '700' },
  dayRow: { flexDirection: 'row', justifyContent: 'space-between' },
  choice: {
    alignItems: 'center',
    borderColor: colors.line,
    borderRadius: radius.pill,
    borderWidth: 1,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  choiceActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  choiceText: { color: colors.ink, fontSize: 12, fontWeight: '700' },
  choiceTextActive: { color: colors.white },
  timeRow: { flexDirection: 'row', gap: spacing.sm },
  timeField: { flex: 1 },
  choiceRow: { flexDirection: 'row', gap: spacing.sm },
  disciplineChoice: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
    flex: 1,
    padding: spacing.sm,
  },
  injuryChoice: { backgroundColor: colors.dangerSoft },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    padding: 14,
  },
  actionSecondary: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderWidth: 1,
  },
  actionDisabled: { opacity: 0.45 },
  actionText: { color: colors.white, fontSize: 14, fontWeight: '900' },
  actionSecondaryText: { color: colors.brand },
  workoutCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  workoutStack: { gap: spacing.xs },
  movePanel: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.md,
  },
  restDay: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  cardHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  cardTitle: { color: colors.ink, fontSize: 17, fontWeight: '900' },
  cardDescription: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  cardMeta: { color: colors.inkMuted, fontSize: 12 },
  warning: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.sm,
    gap: spacing.xs,
    padding: spacing.md,
  },
  warningTitle: { color: colors.accent, fontSize: 12, fontWeight: '900' },
  warningText: { color: colors.ink, fontSize: 13, lineHeight: 18 },
  decisionRow: { flexDirection: 'row', gap: spacing.sm },
  decisionButton: { flex: 1 },
  deckCard: {
    borderColor: colors.line,
    borderRadius: radius.sm,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  deckCardSelected: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  hint: { color: colors.inkMuted, fontSize: 12, lineHeight: 18 },
  error: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.sm,
    color: colors.danger,
    padding: spacing.md,
  },
});
