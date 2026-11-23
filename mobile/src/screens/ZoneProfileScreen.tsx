import { studioPresentation } from '../ui-v3/presentation';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  useWindowDimensions,
  View,
} from 'react-native';
import { FormScrollView } from '../components/FormScrollView';
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
  ZoneSetupRoute,
} from '../api/types';
import { FadeInView } from '../components/FadeInView';
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
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

// V3 names the setup route instead of printing its API code.
const routeNames: Record<ZoneSetupRoute, TranslationKey> = {
  known_values: 'zones.route.known_values', field_test: 'zones.route.field_test', calibration_week: 'zones.route.calibration_week', rpe_only: 'zones.route.rpe_only',
};
const disciplineLabels: Record<Discipline, TranslationKey> = {
  swim: 'common.swim',
  bike: 'common.bike',
  run: 'common.run',
};
const visibilityLabels: Record<
  DisciplineZoneProfile['numeric_zone_visibility'],
  TranslationKey
> = {
  visible: 'zones.visibility.visible',
  rpe_guided: 'zones.visibility.rpe_guided',
  week_2_evaluation_pending: 'zones.visibility.week_2_evaluation_pending',
  proposal_confirmation_pending: 'zones.visibility.proposal_confirmation_pending',
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
  const { t } = useLanguage();
  const canDecide =
    assignment.state === 'pending_approval' &&
    (assignment.scheduling_mode === 'standalone' || canDecideIntegrated);
  return (
    <View style={styles.assignment}>
      <Text style={styles.valueTitle}>
        {assignment.scheduled_date} ·{' '}
        {assignment.scheduling_mode === 'standalone'
          ? t('zones.assignment.standalone')
          : t('zones.assignment.weeklyPlan')}
      </Text>
      <Text style={styles.hint}>
        {assignment.protocol_id} · {t('zones.assignment.status', { state: assignment.state })}
      </Text>
      {canDecide ? (
        <View style={styles.buttonRow}>
          <View style={styles.buttonCell}>
            <ActionButton disabled={busy} label={t('zones.confirm')} onPress={onApprove} />
          </View>
          <View style={styles.buttonCell}>
            <ActionButton
              disabled={busy}
              label={t('zones.reject')}
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
  const { t } = useLanguage();
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
          caught instanceof Error ? caught.message : t('zones.loadFailed'),
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
        caught instanceof Error ? caught.message : t('zones.saveFailed'),
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
      setError(t('zones.dateInvalid'));
      return;
    }
    if (!state.setup?.protocol_id) {
      setError(t('zones.protocolMissing'));
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
      if (!planContext) throw new Error(t('zones.openFromPlan'));
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
      <FormScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        style={styles.scroll}
      >
        <BrandedFormHeader caption={t('planning.myZones')} onBack={onBack} onSignOut={onSignOut} />
        {error ? <Notice tone="error">{error}</Notice> : null}
        {busy ? <ActivityIndicator color={colors.primary} /> : null}
        <FadeInView style={styles.intro}>
          <View style={[styles.heroHeading, compact && styles.stacked]}>
            <IconTile name="profile" size="focus" />
            <View style={[styles.heroCopy, compact && { flex: 0, width: '100%' }]}>
              <Text variant="supporting" tone="primary" style={{ fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 }}>{t('zones.hero.eyebrow')}</Text>
              <Text variant="sectionTitle" style={styles.heroTitle}>{t('zones.hero.title')}</Text>
              <Text tone="textMuted">{t('zones.hero.body')}</Text>
            </View>
          </View>
          <View style={[styles.summaryRow, compact && styles.stacked]}>
            {profile ? <View style={[styles.summaryItem, compact && styles.summaryItemCompact]}><IconTile name="intensity" /><View style={styles.heroCopy}><Text variant="sectionTitle">{profile.disciplines.length}</Text><Text tone="textMuted">{t('zones.summary.disciplines')}</Text></View></View> : null}
            <View style={[styles.summaryItem, compact && styles.summaryItemCompact]}><IconTile name="document" /><View style={styles.heroCopy}><Text variant="sectionTitle">{planContext ? t('zones.summary.planLinkedYes') : t('zones.summary.planLinkedNo')}</Text><Text tone="textMuted">{t('zones.summary.planLinked')}</Text></View></View>
          </View>
        </FadeInView>
        <View style={styles.section}><Text variant="sectionTitle" accessibilityRole="header">{t('zones.disciplines.title')}</Text><Text tone="textMuted">{t('zones.disciplines.body')}</Text></View>

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
                  <Text variant="sectionTitle" accessibilityRole="header">{t(disciplineLabels[state.discipline])}</Text>
                  <StatusPill label={t(visibilityLabels[state.numeric_zone_visibility])} pending={state.numeric_zone_visibility === 'proposal_confirmation_pending'} />
                </View>
              </View>
              <ZoneInfoRow icon="location"><Text tone="textMuted">{t('zones.route', { route: state.setup ? studioPresentation ? t(routeNames[state.setup.setup_route]) : state.setup.setup_route : t('zones.route.notSet') })}</Text></ZoneInfoRow>
              {state.active_profile ? (
                <View style={[styles.profileBlock, styles.profileBlockActive]}>
                  <View style={styles.profileBlockHeading}>
                    <Text style={styles.valueTitle}>{t('zones.activeProfile')}</Text>
                    <Text style={styles.versionLabel}>
                      v{state.active_profile.version}
                    </Text>
                  </View>
                  <ProfileValues profile={state.active_profile} />
                </View>
              ) : (
                <ZoneInfoRow icon="info"><Text tone="textMuted">{t('zones.noActiveProfile')}</Text></ZoneInfoRow>
              )}
              {pending ? (
                <View style={[styles.profileBlock, styles.profileBlockPending]}>
                  <View style={styles.profileBlockHeading}>
                    <Text style={styles.valueTitle}>{t('zones.pendingProfile')}</Text>
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
                          label={t('zones.approve')}
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
                          label={t('zones.reject')}
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
                  <Text style={styles.valueTitle}>{t('zones.priorValues')}</Text>
                  {state.prior_profiles.map((previous) => (
                    <View key={previous.id} style={styles.profileBlock}>
                      <Text style={styles.hint}>
                        {t('zones.priorVersion', { version: previous.version, status: previous.status })}
                      </Text>
                      <ProfileValues profile={previous} />
                    </View>
                  ))}
                </View>
              ) : null}

              {state.available_test_scheduling_modes.length > 0 ? (
                <View style={styles.schedulePanel}>
                  <Text style={styles.valueTitle}>{t('zones.schedule.title')}</Text>
                  <FormField
                    autoCapitalize="none"
                    inputMode="numeric"
                    label={t('zones.schedule.date')}
                    maxLength={10}
                    onChangeText={(value) =>
                      setDates((current) => ({
                        ...current,
                        [state.discipline]: formatIsoDateInput(value),
                      }))
                    }
                    placeholder={t('zones.schedule.datePlaceholder')}
                    value={dates[state.discipline]}
                  />
                  <View style={styles.buttonRow}>
                    {state.available_test_scheduling_modes.map((mode) => {
                      const disabled = mode === 'weekly_plan' && !canIntegrate;
                      return (
                        <ChoiceRow key={mode} label={mode === 'standalone' ? t('zones.schedule.standalone') : t('zones.schedule.weeklyPlan')}
                          selected={modes[state.discipline] === mode} disabled={disabled}
                          onPress={() => setModes((current) => ({ ...current, [state.discipline]: mode }))} />
                      );
                    })}
                  </View>
                  {state.discipline === 'swim' ? (
                    <Text style={styles.hint}>{t('zones.schedule.swimHint')}</Text>
                  ) : null}
                  <ActionButton
                    disabled={busy}
                    label={t('zones.schedule.submit')}
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
                    ? t('zones.edit.close')
                    : t('zones.edit.open')
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
      </FormScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 }, scroll: { flex: 1 },
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
