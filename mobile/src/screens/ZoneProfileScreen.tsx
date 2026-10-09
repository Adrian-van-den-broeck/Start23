import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  useWindowDimensions,
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
  ZoneProfileState,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { ZoneField as FormField } from '../ui-v2/components/ZoneField';
import { ZoneStatusChip as StatusPill, ZoneInfoRow, ZoneProfileValues as ProfileValues } from '../ui-v2/components/ZoneVisuals';
import { formatIsoDateInput } from '../lib/dateInput';
import { colors, layout, radius, shadows, space } from '../ui-v2/tokens';
import { Text } from '../ui-v2/primitives/Text';
import { Button } from '../ui-v2/primitives/Button';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { IconTile } from '../ui-v2/primitives/IconTile';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { Notice } from '../ui-v2/primitives/Notice';
import { ZoneSetupStep } from './ZoneSetupStep';

type Props = {
  accessToken: string;
  onBack: () => void;
  onSignOut: () => Promise<void>;
  planContext: { planId: string; revision: number } | null;
};

const disciplineLabels: Record<Discipline, string> = {
  swim: 'Zwemmen',
  bike: 'Fietsen',
  run: 'Lopen',
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
  return <Button disabled={disabled} label={label} onPress={onPress}
    variant={secondary ? 'outline' : 'primary'} trailingIcon={secondary ? undefined : 'forward'} />;
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
  const { width, fontScale } = useWindowDimensions();
  const compact = width < 393 || fontScale > 1;
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
        <BrandedFormHeader caption="Mijn zones" onBack={onBack} onSignOut={onSignOut} />
        {error ? <Notice tone="error">{error}</Notice> : null}
        {busy ? <ActivityIndicator color={colors.primary} /> : null}
        <FadeInView style={styles.intro}>
          <View style={[styles.heroHeading, compact && styles.stacked]}>
            <IconTile name="profile" size="focus" />
            <View style={[styles.heroCopy, compact && { flex: 0, width: '100%' }]}>
              <Text variant="supporting" tone="primary" style={{ fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 }}>Persoonlijk profiel</Text>
              <Text variant="sectionTitle" style={styles.heroTitle}>Jouw zones, helder in beeld.</Text>
              <Text tone="textMuted">Bekijk actieve en eerdere versies, wijzig bekende waarden of kies een nieuwe test. Geen wijziging wordt actief zonder jouw bevestiging.</Text>
            </View>
          </View>
          <View style={[styles.summaryRow, compact && styles.stacked]}>
            {profile ? <View style={[styles.summaryItem, compact && styles.summaryItemCompact]}><IconTile name="intensity" /><View style={styles.heroCopy}><Text variant="sectionTitle">{profile.disciplines.length}</Text><Text tone="textMuted">Disciplines</Text></View></View> : null}
            <View style={[styles.summaryItem, compact && styles.summaryItemCompact]}><IconTile name="document" /><View style={styles.heroCopy}><Text variant="sectionTitle">{planContext ? 'Ja' : 'Los'}</Text><Text tone="textMuted">Plan gekoppeld</Text></View></View>
          </View>
        </FadeInView>
        <View style={styles.section}><Text variant="sectionTitle" accessibilityRole="header">Mijn disciplines</Text><Text tone="textMuted">Stel per discipline je zones, routes en profielen in.</Text></View>

        {profile?.disciplines.map((state, index) => {
          const pending = state.pending_profile;
          const canIntegrate =
            state.available_test_scheduling_modes.includes('weekly_plan') &&
            planContext !== null;
          return (
            <FadeInView
              delay={70 + index * 70}
              key={state.discipline}
              style={styles.panel}
            >
              <View style={[styles.panelIdentity, compact && styles.stacked]}>
                <IconTile name={state.discipline} size="focus" />
                <View style={[styles.panelIdentityCopy, compact && styles.fullWidth]}>
                  <Text variant="sectionTitle" accessibilityRole="header">{disciplineLabels[state.discipline]}</Text>
                  <StatusPill label={visibilityLabels[state.numeric_zone_visibility]} pending={state.numeric_zone_visibility === 'proposal_confirmation_pending'} />
                </View>
              </View>
              <ZoneInfoRow icon="location"><Text tone="textMuted">Route: {state.setup?.setup_route ?? 'nog niet ingesteld'}</Text></ZoneInfoRow>
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
                <ZoneInfoRow icon="info"><Text tone="textMuted">Geen actief numeriek profiel; trainingen blijven RPE-gestuurd.</Text></ZoneInfoRow>
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

              {state.available_test_scheduling_modes.length > 0 ? (
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
                    {state.available_test_scheduling_modes.map((mode) => {
                      const disabled = mode === 'weekly_plan' && !canIntegrate;
                      return (
                        <ChoiceRow key={mode} label={mode === 'standalone' ? 'Losse test' : 'In weekplan'}
                          selected={modes[state.discipline] === mode} disabled={disabled}
                          onPress={() => setModes((current) => ({ ...current, [state.discipline]: mode }))} />
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
  safeArea: { backgroundColor: colors.background, flex: 1 }, keyboard: { flex: 1 }, scroll: { flex: 1 },
  content: { alignSelf: 'center', gap: space[24], maxWidth: layout.readingWidth, padding: layout.phoneGutter, paddingBottom: space[48], width: '100%' },
  intro: { ...shadows.card, backgroundColor: colors.surface, borderRadius: radius.card, gap: space[24], padding: space[16] },
  heroHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: space[16] },
  stacked: { flexDirection: 'column', flexWrap: 'nowrap', alignItems: 'flex-start' },
  heroCopy: { flex: 1, minWidth: 0, gap: space[8] }, heroTitle: { fontSize: 24, lineHeight: 30 },
  summaryRow: { flexDirection: 'row', flexWrap: 'wrap', gap: space[24], borderTopWidth: 1, borderTopColor: colors.border, paddingTop: space[24] },
  summaryItem: { flexDirection: 'row', gap: space[12], alignItems: 'center', flexGrow: 1, flexBasis: 150 },
  summaryItemCompact: { flexGrow: 0, flexBasis: 'auto', width: '100%' }, fullWidth: { flex: 0, width: '100%' },
  section: { gap: space[8] }, body: { color: colors.textMuted, fontSize: 16, lineHeight: 24 }, hint: { color: colors.textMuted, fontSize: 14, lineHeight: 20 },
  panel: { ...shadows.card, backgroundColor: colors.surface, borderColor: colors.border, borderRadius: radius.card, borderWidth: 1, gap: space[16], padding: space[16] },
  panelIdentity: { alignItems: 'center', flexDirection: 'row', gap: space[16] }, panelIdentityCopy: { flex: 1, minWidth: 0, gap: space[8] },
  profileBlock: { borderTopColor: colors.border, borderTopWidth: 1, gap: space[16], paddingTop: space[16] },
  profileBlockActive: { gap: space[16] }, profileBlockPending: { backgroundColor: colors.warningSoft, borderRadius: radius.inset, padding: space[16] },
  profileBlockHeading: { alignItems: 'flex-start', flexDirection: 'row', flexWrap: 'wrap', gap: space[8], justifyContent: 'space-between' },
  versionLabel: { backgroundColor: colors.primarySoft, borderRadius: radius.inset, color: colors.primary, fontSize: 14, paddingHorizontal: space[8], paddingVertical: space[4] },
  pendingVersionLabel: { color: colors.warning, fontSize: 14 }, valueTitle: { color: colors.text, fontSize: 18, fontWeight: '600', lineHeight: 26 },
  history: { gap: space[16] }, schedulePanel: { backgroundColor: colors.primarySoft, borderRadius: radius.control, gap: space[24], padding: space[16] },
  assignment: { borderColor: colors.border, borderRadius: radius.control, borderWidth: 1, gap: space[16], padding: space[16] },
  buttonRow: { gap: space[12] }, buttonCell: { width: '100%' },
});
