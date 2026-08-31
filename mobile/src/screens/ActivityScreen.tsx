import { FlashList } from '@shopify/flash-list';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  confirmActivityMatch,
  createActivity,
  getCalendar,
  getOnboarding,
  listActivities,
  listPlannedExternalActivities,
  submitActivityRpe,
} from '../api/client';
import type {
  CompletedActivity,
  Discipline,
  PlannedExternalActivity,
  PlannedWorkout,
} from '../api/types';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

type ActivityScreenProps = {
  accessToken: string;
  onBack: () => void;
  onPendingRpeChange?: (count: number) => void;
  onSignOut: () => Promise<void>;
};

const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
};

function newIdempotencyKey(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (value) => {
    const random = Math.floor(Math.random() * 16);
    const digit = value === 'x' ? random : (random & 0x3) | 0x8;
    return digit.toString(16);
  });
}

function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function resultLabel(activity: CompletedActivity): string {
  return {
    awaiting_rpe: 'RPE nodig',
    perfect_match: 'Goed aangesloten',
    overshoot: 'Zwaarder dan gepland',
    hidden_fatigue: 'Herstelsignaal',
    deviation: 'Afwijkende uitvoering',
    unplanned: 'Extra training',
  }[activity.qualitative_result];
}

function localWeekKey(instant: Date, timezoneName: string): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    day: '2-digit',
    month: '2-digit',
    timeZone: timezoneName,
    year: 'numeric',
  }).formatToParts(instant);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const local = new Date(
    Date.UTC(Number(value.year), Number(value.month) - 1, Number(value.day)),
  );
  const weekday = local.getUTCDay() || 7;
  local.setUTCDate(local.getUTCDate() - weekday + 1);
  return local.toISOString().slice(0, 10);
}

function suggestedWorkout(
  activity: CompletedActivity,
  workouts: PlannedWorkout[],
): PlannedWorkout | null {
  const candidates = workouts
    .filter(
      (workout) =>
        workout.discipline === activity.discipline &&
        workout.status === 'scheduled',
    )
    .map((workout) => ({
      workout,
      difference: Math.abs(
        new Date(`${workout.scheduled_date}T12:00:00`).getTime() -
          new Date(activity.started_at).getTime(),
      ),
    }))
    .filter(({ difference }) => difference <= 24 * 60 * 60 * 1000)
    .sort((left, right) => left.difference - right.difference);
  return candidates[0]?.workout ?? null;
}

export function ActivityScreen({
  accessToken,
  onBack,
  onPendingRpeChange,
  onSignOut,
}: ActivityScreenProps) {
  const [activities, setActivities] = useState<CompletedActivity[]>([]);
  const [workouts, setWorkouts] = useState<PlannedWorkout[]>([]);
  const [externalActivities, setExternalActivities] = useState<
    PlannedExternalActivity[]
  >([]);
  const [selectedWorkout, setSelectedWorkout] = useState<PlannedWorkout | null>(
    null,
  );
  const [selectedExternal, setSelectedExternal] =
    useState<PlannedExternalActivity | null>(null);
  const [discipline, setDiscipline] = useState<Discipline>('run');
  const [duration, setDuration] = useState('45');
  const [distance, setDistance] = useState('');
  const [startedAt, setStartedAt] = useState(() => new Date().toISOString());
  const [athleteTimezone, setAthleteTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  );
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingRpeActivityId, setEditingRpeActivityId] = useState<string | null>(
    null,
  );
  const [heartRateByActivity, setHeartRateByActivity] = useState<
    Record<string, string>
  >({});

  const pendingRpe = useMemo(
    () => activities.filter((activity) => activity.processing_state === 'awaiting_rpe'),
    [activities],
  );

  const load = async () => {
    const now = new Date();
    const from = new Date(now);
    const to = new Date(now);
    from.setDate(from.getDate() - 14);
    to.setDate(to.getDate() + 14);
    const [activityRows, calendar, onboarding, plannedExternal] = await Promise.all([
      listActivities(accessToken),
      getCalendar(accessToken, isoDate(from), isoDate(to)),
      getOnboarding(accessToken),
      listPlannedExternalActivities(accessToken),
    ]);
    setActivities(activityRows);
    onPendingRpeChange?.(
      activityRows.filter(
        (activity) => activity.processing_state === 'awaiting_rpe',
      ).length,
    );
    setWorkouts(calendar.workouts.filter((workout) => workout.status === 'scheduled'));
    setExternalActivities(
      plannedExternal.filter((activity) => activity.status === 'planned'),
    );
    if (onboarding.profile?.timezone) {
      setAthleteTimezone(onboarding.profile.timezone);
    }
  };

  useEffect(() => {
    setBusy(true);
    load()
      .catch((caught) =>
        setError(caught instanceof Error ? caught.message : 'Laden is mislukt.'),
      )
      .finally(() => setBusy(false));
    // The callback is stable in AppContent; load is intentionally local.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const selectWorkout = (workout: PlannedWorkout | null) => {
    setSelectedWorkout(workout);
    setSelectedExternal(null);
    if (workout) {
      setDiscipline(workout.discipline);
      setDuration(String(Number(workout.duration_minutes)));
      setDistance(
        workout.distance_meters === null ? '' : String(workout.distance_meters),
      );
    }
  };

  const selectExternal = (activity: PlannedExternalActivity) => {
    setSelectedWorkout(null);
    setSelectedExternal(activity);
    setDiscipline(activity.discipline);
    setDuration(String(Number(activity.duration_minutes)));
    setDistance('');
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const numericDuration = Number(duration);
      const numericDistance = distance ? Number(distance) : undefined;
      if (!Number.isFinite(numericDuration) || numericDuration <= 0) {
        throw new Error('Vul een geldige duur in minuten in.');
      }
      if (
        numericDistance !== undefined &&
        (!Number.isInteger(numericDistance) || numericDistance <= 0)
      ) {
        throw new Error('Vul afstand in hele meters in.');
      }
      if (Number.isNaN(new Date(startedAt).getTime())) {
        throw new Error('Gebruik een geldig werkelijk starttijdstip in ISO-formaat.');
      }
      await createActivity(accessToken, idempotencyKey, {
        ...(selectedWorkout
          ? { planned_workout_id: selectedWorkout.id }
          : {}),
        ...(selectedExternal
          ? { planned_external_activity_id: selectedExternal.id }
          : {}),
        discipline,
        started_at: startedAt,
        timezone: athleteTimezone,
        duration_minutes: String(numericDuration),
        ...(numericDistance === undefined
          ? {}
          : { distance_meters: numericDistance }),
      });
      setIdempotencyKey(newIdempotencyKey());
      setSelectedWorkout(null);
      setSelectedExternal(null);
      setStartedAt(new Date().toISOString());
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De activiteit kon niet worden opgeslagen.',
      );
    } finally {
      setBusy(false);
    }
  };

  const saveRpe = async (activityId: string, rpe: number) => {
    setBusy(true);
    setError(null);
    try {
      const rawHeartRate = heartRateByActivity[activityId]?.trim() ?? '';
      const averageHeartRate = rawHeartRate ? Number(rawHeartRate) : undefined;
      if (
        averageHeartRate !== undefined &&
        (!Number.isInteger(averageHeartRate) ||
          averageHeartRate < 20 ||
          averageHeartRate > 260)
      ) {
        throw new Error('Vul een gemiddelde hartslag tussen 20 en 260 bpm in.');
      }
      await submitActivityRpe(
        accessToken,
        activityId,
        rpe,
        averageHeartRate,
      );
      setHeartRateByActivity((current) => {
        const next = { ...current };
        delete next[activityId];
        return next;
      });
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'RPE opslaan is mislukt.',
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmMatch = async (activityId: string, workoutId: string) => {
    setBusy(true);
    setError(null);
    try {
      await confirmActivityMatch(accessToken, activityId, workoutId);
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De koppeling kon niet worden bevestigd.',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" onPress={onBack}>
          <Text style={styles.link}>Weekplanning</Text>
        </Pressable>
        <View>
          <Text style={styles.logo}>Start23</Text>
          <Text style={styles.caption}>Training & RPE</Text>
        </View>
        <Pressable accessibilityRole="button" onPress={() => void onSignOut()}>
          <Text style={styles.link}>Afmelden</Text>
        </Pressable>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboard}
      >
      <FlashList
        contentContainerStyle={styles.content}
        data={activities}
        extraData={{ busy, editingRpeActivityId, heartRateByActivity }}
        ItemSeparatorComponent={() => <View style={styles.listSeparator} />}
        keyboardShouldPersistTaps="handled"
        keyExtractor={(activity) => activity.id}
        ListHeaderComponent={
          <>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}

        {pendingRpe.map((activity) => (
          <View key={activity.id} style={styles.alertCard}>
            <StatusPill label="RPE nodig" tone="accent" />
            <Text style={styles.cardTitle}>
              {disciplineLabels[activity.discipline]} ·{' '}
              {Number(activity.duration_minutes)} min
            </Text>
            <Text style={styles.body}>Hoe zwaar voelde deze training?</Text>
            <FormField
              hint="Verplicht bij een toegewezen training die op RPE is gestuurd; deze observatie maakt zelf geen zones."
              inputMode="numeric"
              label="Gemiddelde hartslag (bpm)"
              onChangeText={(value) =>
                setHeartRateByActivity((current) => ({
                  ...current,
                  [activity.id]: value,
                }))
              }
              placeholder="bijv. 149"
              value={heartRateByActivity[activity.id] ?? ''}
            />
            <View style={styles.rpeGrid}>
              {Array.from({ length: 10 }, (_, index) => index + 1).map((rpe) => (
                <Pressable
                  accessibilityLabel={`RPE ${rpe}`}
                  accessibilityRole="button"
                  disabled={busy}
                  haptic="selection"
                  key={rpe}
                  onPress={() => void saveRpe(activity.id, rpe)}
                  style={styles.rpeButton}
                >
                  <Text style={styles.rpeText}>{rpe}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        ))}

        <View style={styles.panel}>
          <Text style={styles.title}>Training registreren</Text>
          <Text style={styles.body}>
            Kies een geplande training, of registreer bewust een extra training.
          </Text>
          <Pressable
            accessibilityRole="radio"
            accessibilityState={{
              checked: selectedWorkout === null && selectedExternal === null,
            }}
            onPress={() => selectWorkout(null)}
            style={[
              styles.choice,
              selectedWorkout === null &&
                selectedExternal === null &&
                styles.choiceActive,
            ]}
          >
            <Text style={styles.choiceTitle}>Extra, ongeplande training</Text>
          </Pressable>
          {workouts.map((workout) => (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ checked: selectedWorkout?.id === workout.id }}
              key={workout.id}
              onPress={() => selectWorkout(workout)}
              style={[
                styles.choice,
                selectedWorkout?.id === workout.id && styles.choiceActive,
              ]}
            >
              <Text style={styles.choiceTitle}>{workout.name}</Text>
              <Text style={styles.meta}>
                {disciplineLabels[workout.discipline]} ·{' '}
                {new Date(`${workout.scheduled_date}T12:00:00`).toLocaleDateString('nl-NL')}
              </Text>
            </Pressable>
          ))}

          {externalActivities.map((activity) => (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ checked: selectedExternal?.id === activity.id }}
              key={activity.id}
              onPress={() => selectExternal(activity)}
              style={[
                styles.choice,
                selectedExternal?.id === activity.id && styles.choiceActive,
              ]}
            >
              <Text style={styles.choiceTitle}>{activity.name}</Text>
              <Text style={styles.meta}>
                Buiten Start23 · {disciplineLabels[activity.discipline]} ·{' '}
                {new Date(activity.scheduled_at).toLocaleDateString('nl-NL')}
              </Text>
            </Pressable>
          ))}

          {!selectedWorkout && !selectedExternal ? (
            <View style={styles.disciplineRow}>
              {(Object.keys(disciplineLabels) as Discipline[]).map((value) => (
                <Pressable
                  key={value}
                  onPress={() => setDiscipline(value)}
                  style={[
                    styles.discipline,
                    discipline === value && styles.disciplineActive,
                  ]}
                >
                  <Text
                    style={
                      discipline === value
                        ? styles.disciplineTextActive
                        : styles.disciplineText
                    }
                  >
                    {disciplineLabels[value]}
                  </Text>
                </Pressable>
              ))}
            </View>
          ) : null}
          <FormField
            autoCapitalize="none"
            label="Werkelijk gestart (ISO inclusief tijdzone)"
            onChangeText={setStartedAt}
            value={startedAt}
          />
          <FormField
            autoCapitalize="none"
            label="Tijdzone van de activiteit"
            onChangeText={setAthleteTimezone}
            value={athleteTimezone}
          />
          <FormField
            inputMode="decimal"
            label="Werkelijke duur (minuten)"
            onChangeText={setDuration}
            value={duration}
          />
          <FormField
            inputMode="numeric"
            label="Afstand (meter, optioneel)"
            onChangeText={setDistance}
            value={distance}
          />
          <Pressable
            accessibilityRole="button"
            disabled={busy}
            onPress={() => void save()}
            style={[styles.action, busy && styles.disabled]}
          >
            <Text style={styles.actionText}>Activiteit opslaan</Text>
          </Pressable>
        </View>

        <View style={styles.recentHeading}>
          <Text style={styles.title}>Recente activiteiten</Text>
          {activities.length === 0 ? (
            <Text style={styles.body}>Nog geen activiteiten geregistreerd.</Text>
          ) : null}
        </View>
          </>
        }
        ListHeaderComponentStyle={styles.listHeader}
        renderItem={({ item: activity }) => (
            <View key={activity.id} style={styles.activityRow}>
              <View style={styles.activityHeader}>
                <Text style={styles.cardTitle}>
                  {disciplineLabels[activity.discipline]}
                </Text>
                <StatusPill
                  label={resultLabel(activity)}
                  tone={
                    activity.qualitative_result === 'perfect_match'
                      ? 'brand'
                      : activity.qualitative_result === 'awaiting_rpe'
                        ? 'accent'
                        : 'neutral'
                  }
                />
              </View>
              <Text style={styles.meta}>
                {Number(activity.duration_minutes)} min
                {activity.rpe === null ? '' : ` · RPE ${activity.rpe}`}
              </Text>
              <Text style={styles.body}>{activity.public_message}</Text>
              {activity.match_status === 'unmatched' &&
              activity.processing_state === 'awaiting_rpe' &&
              suggestedWorkout(activity, workouts) ? (
                <View style={styles.matchSuggestion}>
                  <Text style={styles.choiceTitle}>Mogelijke geplande training</Text>
                  <Text style={styles.body}>
                    {suggestedWorkout(activity, workouts)?.name}. Start23 koppelt
                    dit nooit automatisch.
                  </Text>
                  <Pressable
                    disabled={busy}
                    onPress={() => {
                      const suggestion = suggestedWorkout(activity, workouts);
                      if (suggestion) {
                        void confirmMatch(activity.id, suggestion.id);
                      }
                    }}
                  >
                    <Text style={styles.link}>Koppeling expliciet bevestigen</Text>
                  </Pressable>
                </View>
              ) : null}
              {activity.correction_proposal_id ? (
                <Text style={styles.proposalText}>
                  Er staat een apart correctievoorstel klaar. Niets is automatisch
                  aangepast.
                </Text>
              ) : null}
              {activity.rpe !== null &&
              localWeekKey(new Date(activity.started_at), activity.timezone) ===
                localWeekKey(new Date(), activity.timezone) ? (
                <>
                  <Pressable
                    accessibilityRole="button"
                    onPress={() =>
                      setEditingRpeActivityId((current) =>
                        current === activity.id ? null : activity.id,
                      )
                    }
                  >
                    <Text style={styles.link}>RPE deze week corrigeren</Text>
                  </Pressable>
                  {editingRpeActivityId === activity.id ? (
                    <View style={styles.rpeGrid}>
                      {Array.from({ length: 10 }, (_, index) => index + 1).map(
                        (rpe) => (
                          <Pressable
                            accessibilityLabel={`RPE corrigeren naar ${rpe}`}
                            accessibilityRole="button"
                            disabled={busy || rpe === activity.rpe}
                            haptic="selection"
                            key={rpe}
                            onPress={() => {
                              setEditingRpeActivityId(null);
                              void saveRpe(activity.id, rpe);
                            }}
                            style={[
                              styles.rpeButton,
                              rpe === activity.rpe && styles.disabled,
                            ]}
                          >
                            <Text style={styles.rpeText}>{rpe}</Text>
                          </Pressable>
                        ),
                      )}
                    </View>
                  ) : null}
                </>
              ) : null}
            </View>
        )}
      />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  keyboard: { flex: 1 },
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
  content: { padding: spacing.lg, paddingBottom: 80 },
  listHeader: { gap: spacing.md, paddingBottom: spacing.md },
  listSeparator: { height: spacing.md },
  panel: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.lg,
  },
  recentHeading: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  alertCard: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    gap: spacing.sm,
    padding: spacing.lg,
  },
  title: { color: colors.ink, fontSize: 22, fontWeight: '900' },
  cardTitle: { color: colors.ink, fontSize: 16, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  meta: { color: colors.inkMuted, fontSize: 12, marginTop: 3 },
  choice: { backgroundColor: colors.surfaceRaised, borderColor: colors.lineStrong, borderRadius: radius.sm, borderWidth: 1, padding: spacing.md },
  choiceActive: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  choiceTitle: { color: colors.ink, fontSize: 14, fontWeight: '800' },
  disciplineRow: { flexDirection: 'row', gap: spacing.sm },
  discipline: { backgroundColor: colors.surfaceMuted, borderColor: colors.lineStrong, borderRadius: radius.pill, borderWidth: 1, flex: 1, padding: spacing.sm },
  disciplineActive: { backgroundColor: colors.brand },
  disciplineText: { color: colors.ink, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  disciplineTextActive: { color: colors.white, fontSize: 12, fontWeight: '800', textAlign: 'center' },
  rpeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  rpeButton: { alignItems: 'center', backgroundColor: colors.surfaceRaised, borderColor: colors.lineStrong, borderRadius: radius.pill, borderWidth: 1, height: 40, justifyContent: 'center', width: 40 },
  rpeText: { color: colors.brand, fontWeight: '900' },
  action: { alignItems: 'center', backgroundColor: colors.brand, borderRadius: radius.pill, padding: 14 },
  actionText: { color: colors.white, fontSize: 14, fontWeight: '900' },
  disabled: { opacity: 0.45 },
  activityRow: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  activityHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  proposalText: { color: colors.brand, fontSize: 12, fontWeight: '700', lineHeight: 18 },
  matchSuggestion: { backgroundColor: colors.brandSoft, borderRadius: radius.sm, gap: spacing.xs, padding: spacing.md },
  error: { backgroundColor: colors.dangerSoft, borderRadius: radius.sm, color: colors.danger, padding: spacing.md },
});
