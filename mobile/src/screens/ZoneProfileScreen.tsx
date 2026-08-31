import { useEffect, useState } from 'react';
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
  approvePlanProposal,
  approveTestAssignment,
  approveZoneProposal,
  getOnboarding,
  getZoneProfileState,
  rejectPlanProposal,
  rejectTestAssignment,
  rejectZoneProposal,
  saveCalculatedZones,
  saveDisciplineSetup,
  scheduleFieldTest,
} from '../api/client';
import type {
  Discipline,
  DisciplineSetupInput,
  DisciplineZoneProfile,
  OnboardingState,
  TestAssignment,
  TestSchedulingMode,
  ZoneProfileSnapshot,
  ZoneProfileState,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { StatusPill } from '../components/StatusPill';
import { formatIsoDateInput } from '../lib/dateInput';
import { colors, radius, shadows, spacing } from '../theme/tokens';
import { ZoneSetupStep } from './ZoneSetupStep';

type Props = {
  accessToken: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
  planContext: { planId: string; revision: number } | null;
};

const disciplines: readonly Discipline[] = ['swim', 'bike', 'run'];
const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
};
const disciplineCodes: Record<Discipline, string> = {
  swim: 'Z',
  bike: 'F',
  run: 'L',
};
const visibilityLabels: Record<
  DisciplineZoneProfile['numeric_zone_visibility'],
  string
> = {
  visible: 'Actieve zones',
  rpe_guided: 'RPE-gestuurd',
  week_2_evaluation_pending: 'Cijfers verborgen tot evaluatie na week 2',
  proposal_confirmation_pending: 'Zonevoorstel wacht op bevestiging',
};

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
      haptic={secondary ? undefined : 'light'}
      onPress={onPress}
      style={({ pressed }) => [
        styles.action,
        secondary && styles.actionSecondary,
        disabled && styles.disabled,
        pressed && styles.pressed,
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

function BoundaryList({
  boundaries,
}: {
  boundaries: ZoneProfileSnapshot['boundaries'];
}) {
  return (
    <View style={styles.boundaryList}>
      {boundaries.map((boundary) => (
        <View key={boundary.zone_number} style={styles.boundaryChip}>
          <Text style={styles.boundaryZone}>Z{boundary.zone_number}</Text>
          <Text style={styles.boundaryValue}>
            {boundary.lower_value ?? 'open'} - {boundary.upper_value ?? 'open'}
          </Text>
        </View>
      ))}
    </View>
  );
}

function ProfileValues({ profile }: { profile: ZoneProfileSnapshot }) {
  if (profile.values_hidden) {
    return (
      <View style={styles.hiddenState}>
        <View style={styles.hiddenStateIcon}>
          <Text style={styles.hiddenStateIconText}>RPE</Text>
        </View>
        <Text style={styles.body}>
          Numerieke waarden blijven verborgen. Je trainingen gebruiken voorlopig
          alleen RPE en observaties.
        </Text>
      </View>
    );
  }
  const metricProfiles = profile.metric_profiles;
  return (
    <View style={styles.valueList}>
      {profile.metric ? (
        <View style={styles.primaryMetric}>
          <Text style={styles.primaryMetricLabel}>
            {profile.metric.metric_kind}
          </Text>
          <Text style={styles.primaryMetricValue}>{profile.metric.value}</Text>
        </View>
      ) : null}
      {metricProfiles.map((metric) => (
        <View key={metric.metric_kind} style={styles.valueBlock}>
          <View style={styles.metricHeader}>
            <Text style={styles.metricLabel}>{metric.metric_kind}</Text>
            <Text style={styles.metricValue}>{metric.source_value}</Text>
          </View>
          <BoundaryList boundaries={metric.boundaries} />
        </View>
      ))}
      {metricProfiles.length === 0 && profile.boundaries.length > 0 ? (
        <BoundaryList boundaries={profile.boundaries} />
      ) : null}
      <View style={styles.sourceRow}>
        <Text style={styles.sourceLabel}>Bron</Text>
        <Text style={styles.sourceValue}>
          {profile.source_method} · {profile.source_quality} ·{' '}
          {profile.review_status}
        </Text>
      </View>
    </View>
  );
}

function AssignmentCard({
  assignment,
  busy,
  canDecideIntegrated,
  onApprove,
  onReject,
}: {
  assignment: TestAssignment;
  busy: boolean;
  canDecideIntegrated: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  const canDecide =
    assignment.state === 'pending_approval' &&
    (assignment.scheduling_mode === 'standalone' || canDecideIntegrated);
  return (
    <View style={styles.assignment}>
      <Text style={styles.valueTitle}>
        {assignment.scheduled_date} ·{' '}
        {assignment.scheduling_mode === 'standalone'
          ? 'losse test'
          : 'in weekplan'}
      </Text>
      <Text style={styles.hint}>
        {assignment.protocol_id} · status {assignment.state}
      </Text>
      {canDecide ? (
        <View style={styles.buttonRow}>
          <View style={styles.buttonCell}>
            <ActionButton disabled={busy} label="Bevestigen" onPress={onApprove} />
          </View>
          <View style={styles.buttonCell}>
            <ActionButton
              disabled={busy}
              label="Afwijzen"
              onPress={onReject}
              secondary
            />
          </View>
        </View>
      ) : null}
    </View>
  );
}

export function ZoneProfileScreen({
  accessToken,
  onBack,
  onSignOut,
  planContext,
}: Props) {
  const [profile, setProfile] = useState<ZoneProfileState | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingState | null>(null);
  const [editingDiscipline, setEditingDiscipline] =
    useState<Discipline | null>(null);
  const [dates, setDates] = useState<Record<Discipline, string>>({
    swim: '',
    bike: '',
    run: '',
  });
  const [modes, setModes] = useState<Record<Discipline, TestSchedulingMode>>({
    swim: 'standalone',
    bike: 'standalone',
    run: 'standalone',
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const [nextProfile, nextOnboarding] = await Promise.all([
      getZoneProfileState(accessToken),
      getOnboarding(accessToken),
    ]);
    setProfile(nextProfile);
    setOnboarding(nextOnboarding);
  };

  useEffect(() => {
    setBusy(true);
    load()
      .catch((caught) =>
        setError(
          caught instanceof Error ? caught.message : 'Het zoneprofiel kon niet laden.',
        ),
      )
      .finally(() => setBusy(false));
    // load is intentionally scoped to this screen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
      await load();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'De wijziging is niet opgeslagen.',
      );
    } finally {
      setBusy(false);
    }
  };

  const saveSetup = async (
    discipline: Discipline,
    input: DisciplineSetupInput,
  ) => {
    await run(async () => {
      if (input.setup_route === 'known_values') {
        await saveCalculatedZones(accessToken, discipline, {
          thresholds: input.thresholds,
          source_quality: input.source_quality,
          boundary_overrides: input.zone_profiles,
        });
      }
      await saveDisciplineSetup(accessToken, discipline, input);
      setEditingDiscipline(null);
    });
  };

  const schedule = (state: DisciplineZoneProfile) => {
    const scheduledDate = dates[state.discipline].trim();
    const mode = modes[state.discipline];
    if (!/^\d{4}-\d{2}-\d{2}$/.test(scheduledDate)) {
      setError('Gebruik voor de testdatum JJJJ-MM-DD.');
      return;
    }
    if (!state.setup?.protocol_id) {
      setError('Kies eerst een beoordeeld veldtestprotocol.');
      return;
    }
    void run(async () => {
      await scheduleFieldTest(accessToken, {
        discipline: state.discipline,
        protocol_id: state.setup!.protocol_id!,
        scheduling_mode: mode,
        scheduled_date: scheduledDate,
        ...(mode === 'weekly_plan' && planContext
          ? {
              plan_id: planContext.planId,
              expected_plan_revision: planContext.revision,
            }
          : {}),
      });
    });
  };

  const decideAssignment = (
    assignment: TestAssignment,
    decision: 'approve' | 'reject',
  ) => {
    void run(async () => {
      if (assignment.scheduling_mode === 'standalone') {
        if (decision === 'approve') {
          await approveTestAssignment(
            accessToken,
            assignment.proposal_id,
            assignment.revision,
          );
        } else {
          await rejectTestAssignment(accessToken, assignment.proposal_id);
        }
        return;
      }
      if (!planContext) throw new Error('Open dit profiel vanuit het actieve weekplan.');
      if (decision === 'approve') {
        await approvePlanProposal(
          accessToken,
          assignment.proposal_id,
          planContext.revision,
        );
      } else {
        await rejectPlanProposal(accessToken, assignment.proposal_id);
      }
    });
  };

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={onBack}
          style={({ pressed }) => [
            styles.headerButton,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.headerButtonSymbol}>{'<'}</Text>
          <Text style={styles.headerButtonText}>Week</Text>
        </Pressable>
        <View style={styles.headerBrand}>
          <Text style={styles.logo}>START23</Text>
          <Text style={styles.caption}>Mijn zones</Text>
        </View>
        <Pressable
          accessibilityLabel="Afmelden"
          accessibilityRole="button"
          onPress={() => void onSignOut()}
          style={({ pressed }) => [
            styles.signOutButton,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.signOutButtonText}>Uit</Text>
        </Pressable>
      </View>
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
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}
        <FadeInView style={styles.intro}>
          <View style={styles.introOrb} />
          <Text style={styles.introEyebrow}>Persoonlijk profiel</Text>
          <Text style={styles.title}>Jouw zones, helder in beeld.</Text>
          <Text style={styles.introBody}>
            Bekijk actieve en eerdere versies, wijzig bekende waarden of kies een
            nieuwe test. Geen wijziging wordt actief zonder jouw bevestiging.
          </Text>
          <View style={styles.summaryRow}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>
                {profile?.disciplines.length ?? disciplines.length}
              </Text>
              <Text style={styles.summaryLabel}>Disciplines</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>{planContext ? 'Ja' : 'Los'}</Text>
              <Text style={styles.summaryLabel}>Plan gekoppeld</Text>
            </View>
          </View>
        </FadeInView>

        {profile?.disciplines.map((state, index) => {
          const pending = state.pending_profile;
          const canIntegrate =
            state.discipline !== 'swim' && planContext !== null;
          return (
            <FadeInView
              delay={70 + index * 70}
              key={state.discipline}
              style={styles.panel}
            >
              <View style={styles.panelHeader}>
                <View style={styles.panelIdentity}>
                  <View style={styles.disciplineIcon}>
                    <Text style={styles.disciplineIconText}>
                      {disciplineCodes[state.discipline]}
                    </Text>
                  </View>
                  <View style={styles.panelIdentityCopy}>
                    <Text style={styles.panelTitle}>
                      {disciplineLabels[state.discipline]}
                    </Text>
                    <Text style={styles.hint}>
                      Route: {state.setup?.setup_route ?? 'nog niet ingesteld'}
                    </Text>
                  </View>
                </View>
                <StatusPill
                  label={visibilityLabels[state.numeric_zone_visibility]}
                  tone={state.active_profile ? 'brand' : 'neutral'}
                />
              </View>
              {state.active_profile ? (
                <View style={[styles.profileBlock, styles.profileBlockActive]}>
                  <View style={styles.profileBlockHeading}>
                    <Text style={styles.valueTitle}>Actief profiel</Text>
                    <Text style={styles.versionLabel}>
                      v{state.active_profile.version}
                    </Text>
                  </View>
                  <ProfileValues profile={state.active_profile} />
                </View>
              ) : (
                <Text style={styles.body}>
                  Geen actief numeriek profiel; trainingen blijven RPE-gestuurd.
                </Text>
              )}
              {pending ? (
                <View style={[styles.profileBlock, styles.profileBlockPending]}>
                  <View style={styles.profileBlockHeading}>
                    <Text style={styles.valueTitle}>Nieuw voorstel</Text>
                    <Text style={styles.pendingVersionLabel}>
                      v{pending.version}
                    </Text>
                  </View>
                  <ProfileValues profile={pending} />
                  {pending.proposal_id ? (
                    <View style={styles.buttonRow}>
                      <View style={styles.buttonCell}>
                        <ActionButton
                          disabled={busy}
                          label="Zones goedkeuren"
                          onPress={() =>
                            void run(async () => {
                              await approveZoneProposal(
                                accessToken,
                                pending.proposal_id!,
                                pending.base_zone_profile_id,
                              );
                            })
                          }
                        />
                      </View>
                      <View style={styles.buttonCell}>
                        <ActionButton
                          disabled={busy}
                          label="Afwijzen"
                          onPress={() =>
                            void run(async () => {
                              await rejectZoneProposal(
                                accessToken,
                                pending.proposal_id!,
                              );
                            })
                          }
                          secondary
                        />
                      </View>
                    </View>
                  ) : null}
                </View>
              ) : null}
              {state.prior_profiles.length > 0 ? (
                <View style={styles.history}>
                  <Text style={styles.valueTitle}>Eerdere waarden</Text>
                  {state.prior_profiles.map((previous) => (
                    <View key={previous.id} style={styles.profileBlock}>
                      <Text style={styles.hint}>
                        Versie {previous.version} · {previous.status}
                      </Text>
                      <ProfileValues profile={previous} />
                    </View>
                  ))}
                </View>
              ) : null}

              {state.setup?.setup_route === 'field_test' ? (
                <View style={styles.schedulePanel}>
                  <Text style={styles.valueTitle}>Veldtest plannen</Text>
                  <FormField
                    autoCapitalize="none"
                    inputMode="numeric"
                    label="Lokale testdatum"
                    maxLength={10}
                    onChangeText={(value) =>
                      setDates((current) => ({
                        ...current,
                        [state.discipline]: formatIsoDateInput(value),
                      }))
                    }
                    placeholder="JJJJ-MM-DD"
                    value={dates[state.discipline]}
                  />
                  <View style={styles.buttonRow}>
                    {(['standalone', 'weekly_plan'] as const).map((mode) => {
                      const disabled = mode === 'weekly_plan' && !canIntegrate;
                      return (
                        <Pressable
                          accessibilityRole="radio"
                          accessibilityState={{
                            checked: modes[state.discipline] === mode,
                            disabled,
                          }}
                          disabled={disabled}
                          key={mode}
                          onPress={() =>
                            setModes((current) => ({
                              ...current,
                              [state.discipline]: mode,
                            }))
                          }
                          style={[
                            styles.modeChoice,
                            modes[state.discipline] === mode && styles.modeActive,
                            disabled && styles.disabled,
                          ]}
                        >
                          <Text style={styles.modeText}>
                            {mode === 'standalone' ? 'Losse test' : 'In weekplan'}
                          </Text>
                        </Pressable>
                      );
                    })}
                  </View>
                  {state.discipline === 'swim' ? (
                    <Text style={styles.hint}>
                      De CSS-test blijft los: er is nog geen goedgekeurde duur- en
                      loaddefinitie voor veilige planintegratie.
                    </Text>
                  ) : null}
                  <ActionButton
                    disabled={busy}
                    label="Maak voorstel"
                    onPress={() => schedule(state)}
                  />
                </View>
              ) : null}

              {state.test_assignments.map((assignment) => (
                <AssignmentCard
                  assignment={assignment}
                  busy={busy}
                  canDecideIntegrated={
                    planContext?.planId === assignment.plan_id
                  }
                  key={assignment.id}
                  onApprove={() => decideAssignment(assignment, 'approve')}
                  onReject={() => decideAssignment(assignment, 'reject')}
                />
              ))}

              <ActionButton
                disabled={busy}
                label={
                  editingDiscipline === state.discipline
                    ? 'Bewerken sluiten'
                    : 'Waarden of route wijzigen'
                }
                onPress={() =>
                  setEditingDiscipline((current) =>
                    current === state.discipline ? null : state.discipline,
                  )
                }
                secondary
              />
              {editingDiscipline === state.discipline && onboarding ? (
                <FadeInView distance={8} duration={300}>
                  <ZoneSetupStep
                    accessToken={accessToken}
                    disciplineOverride={state.discipline}
                    key={`${state.discipline}:${state.setup?.revision ?? 0}`}
                    onSave={saveSetup}
                    profileMode
                    saving={busy}
                    state={onboarding}
                  />
                </FadeInView>
              ) : null}
            </FadeInView>
          );
        })}
      </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  keyboard: { flex: 1 },
  scroll: { flex: 1 },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  headerBrand: { alignItems: 'center' },
  logo: {
    color: colors.brand,
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 1.3,
  },
  caption: {
    color: colors.inkMuted,
    fontSize: 10,
    marginTop: 2,
    textAlign: 'center',
  },
  headerButton: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.line,
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.xs,
    minHeight: 38,
    paddingHorizontal: spacing.sm,
  },
  headerButtonSymbol: { color: colors.brand, fontSize: 14, fontWeight: '900' },
  headerButtonText: { color: colors.brand, fontSize: 11, fontWeight: '800' },
  signOutButton: {
    alignItems: 'center',
    backgroundColor: colors.accentSoft,
    borderRadius: radius.pill,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  signOutButtonText: {
    color: colors.accentDark,
    fontSize: 10,
    fontWeight: '900',
  },
  content: {
    alignSelf: 'center',
    gap: spacing.md,
    maxWidth: 760,
    padding: spacing.lg,
    paddingBottom: 80,
    width: '100%',
  },
  intro: {
    ...shadows.floating,
    backgroundColor: colors.brandDeep,
    borderRadius: radius.xl,
    gap: spacing.sm,
    overflow: 'hidden',
    padding: spacing.lg,
    position: 'relative',
  },
  introOrb: {
    backgroundColor: colors.brandMid,
    borderRadius: radius.pill,
    height: 170,
    opacity: 0.7,
    position: 'absolute',
    right: -70,
    top: -85,
    width: 170,
  },
  introEyebrow: {
    color: colors.highlight,
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -0.9,
    lineHeight: 32,
    maxWidth: 330,
  },
  introBody: {
    color: colors.brandSoft,
    fontSize: 13,
    lineHeight: 20,
    maxWidth: 560,
  },
  summaryRow: {
    alignItems: 'center',
    backgroundColor: colors.brandMid,
    borderRadius: radius.md,
    flexDirection: 'row',
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  summaryItem: { flex: 1 },
  summaryValue: { color: colors.white, fontSize: 19, fontWeight: '900' },
  summaryLabel: { color: colors.brandSoft, fontSize: 10, marginTop: 2 },
  summaryDivider: {
    backgroundColor: colors.brand,
    height: 32,
    marginHorizontal: spacing.md,
    width: 1,
  },
  body: { color: colors.inkMuted, fontSize: 14, lineHeight: 21 },
  hint: { color: colors.inkMuted, fontSize: 12, lineHeight: 18 },
  error: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.md,
    color: colors.danger,
    padding: spacing.md,
  },
  panel: {
    ...shadows.card,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.white,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  panelHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    justifyContent: 'space-between',
  },
  panelIdentity: {
    alignItems: 'center',
    flex: 1,
    flexDirection: 'row',
    gap: spacing.sm,
  },
  panelIdentityCopy: { flex: 1 },
  disciplineIcon: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    height: 46,
    justifyContent: 'center',
    width: 46,
  },
  disciplineIconText: {
    color: colors.brand,
    fontSize: 15,
    fontWeight: '900',
  },
  panelTitle: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: -0.4,
  },
  profileBlock: {
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  profileBlockActive: {
    backgroundColor: '#F5FAF7',
    borderColor: '#C8DED3',
  },
  profileBlockPending: {
    backgroundColor: colors.accentSoft,
    borderColor: '#F3CABB',
  },
  profileBlockHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  versionLabel: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    color: colors.brand,
    fontSize: 10,
    fontWeight: '900',
    overflow: 'hidden',
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  pendingVersionLabel: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.pill,
    color: colors.accentDark,
    fontSize: 10,
    fontWeight: '900',
    overflow: 'hidden',
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  valueList: { gap: spacing.sm },
  valueBlock: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.sm,
    gap: spacing.sm,
    padding: spacing.sm,
  },
  primaryMetric: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radius.sm,
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: spacing.sm,
  },
  primaryMetricLabel: {
    color: colors.brand,
    fontSize: 10,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  primaryMetricValue: { color: colors.brand, fontSize: 18, fontWeight: '900' },
  metricHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricLabel: {
    color: colors.inkMuted,
    fontSize: 10,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  metricValue: { color: colors.ink, fontSize: 16, fontWeight: '900' },
  boundaryList: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  boundaryChip: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    gap: 2,
    minWidth: 72,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  boundaryZone: { color: colors.brand, fontSize: 9, fontWeight: '900' },
  boundaryValue: { color: colors.ink, fontSize: 10, fontWeight: '700' },
  sourceRow: {
    borderTopColor: colors.line,
    borderTopWidth: 1,
    gap: 2,
    paddingTop: spacing.sm,
  },
  sourceLabel: {
    color: colors.inkFaint,
    fontSize: 9,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  sourceValue: { color: colors.inkMuted, fontSize: 10, lineHeight: 15 },
  hiddenState: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  hiddenStateIcon: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    height: 42,
    justifyContent: 'center',
    width: 42,
  },
  hiddenStateIconText: { color: colors.brand, fontSize: 9, fontWeight: '900' },
  valueTitle: { color: colors.ink, fontSize: 14, fontWeight: '800' },
  history: { gap: spacing.sm },
  schedulePanel: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    gap: spacing.md,
    padding: spacing.md,
  },
  assignment: {
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  buttonRow: { flexDirection: 'row', gap: spacing.sm },
  buttonCell: { flex: 1 },
  modeChoice: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    flex: 1,
    padding: spacing.sm,
  },
  modeActive: { backgroundColor: colors.accentSoft, borderColor: colors.accent },
  modeText: { color: colors.ink, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  action: {
    ...shadows.card,
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  actionSecondary: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderWidth: 1,
  },
  actionText: { color: colors.white, fontSize: 13, fontWeight: '800' },
  actionSecondaryText: { color: colors.brand },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.78, transform: [{ scale: 0.98 }] },
});
