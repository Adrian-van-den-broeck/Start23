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
import { ZoneProfileValues as ProfileValues } from '../ui-v2/components/ZoneVisuals';
import { formatIsoDateInput } from '../lib/dateInput';
import { colors, layout, radius, shadows, space } from '../ui-v2/tokens';
import { Text } from '../ui-v2/primitives/Text';
import { Button } from '../ui-v2/primitives/Button';
import type { IconName } from '../ui-v2/primitives/Icon';
import { IconTile } from '../ui-v2/primitives/IconTile';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { Notice } from '../ui-v2/primitives/Notice';
import { ChoiceChips, Heading, Kicker, screenGap, SportTile, Tag } from '../ui-v3/screens/support';
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
    <View style={styles.block}>
      <Text variant="label">
        {assignment.scheduled_date} ·{' '}
        {assignment.scheduling_mode === 'standalone'
          ? t('zones.assignment.standalone')
          : t('zones.assignment.weeklyPlan')}
      </Text>
      <Text variant="supporting" tone="textMuted">
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

function Stat({ icon, value, label }: { icon: IconName; value: string | number; label: string }) {
  return (
    <View style={styles.stat}>
      {studioPresentation ? null : <IconTile name={icon} />}
      <View style={styles.statCopy}>
        <Text variant={studioPresentation ? 'numericCompact' : 'sectionTitle'}>{value}</Text>
        <Text variant={studioPresentation ? 'caption' : 'body'} tone="textMuted">{label}</Text>
      </View>
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
          {studioPresentation ? (
            <View style={styles.heroCopy}>
              <Kicker>{t('zones.hero.eyebrow')}</Kicker>
              <Text variant="supporting" tone="textMuted">{t('zones.hero.body')}</Text>
            </View>
          ) : (
            <View style={[styles.heroHeading, compact && styles.stacked]}>
              <IconTile name="profile" size="focus" />
              <View style={[styles.heroCopy, compact && styles.fullWidth]}>
                <Kicker>{t('zones.hero.eyebrow')}</Kicker>
                <Text variant="sectionTitle">{t('zones.hero.title')}</Text>
                <Text tone="textMuted">{t('zones.hero.body')}</Text>
              </View>
            </View>
          )}
          <View style={styles.summaryRow}>
            {profile ? <Stat icon="intensity" value={profile.disciplines.length} label={t('zones.summary.disciplines')} /> : null}
            <Stat icon="document" value={planContext ? t('zones.summary.planLinkedYes') : t('zones.summary.planLinkedNo')} label={t('zones.summary.planLinked')} />
          </View>
        </FadeInView>
        <Heading title={t('zones.disciplines.title')} description={t('zones.disciplines.body')} />

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
              <View style={styles.panelIdentity}>
                {studioPresentation ? <SportTile discipline={state.discipline} /> : <IconTile name={state.discipline} size="focus" />}
                <View style={styles.panelIdentityCopy}>
                  <Text variant={studioPresentation ? 'cardTitle' : 'sectionTitle'} accessibilityRole="header">{t(disciplineLabels[state.discipline])}</Text>
                  <Tag label={t(visibilityLabels[state.numeric_zone_visibility])} tone={state.numeric_zone_visibility === 'proposal_confirmation_pending' ? 'warning' : 'primary'} />
                </View>
              </View>
              <Text variant="supporting" tone="textMuted">{t('zones.route', { route: state.setup ? studioPresentation ? t(routeNames[state.setup.setup_route]) : state.setup.setup_route : t('zones.route.notSet') })}</Text>
              {state.active_profile ? (
                <View style={styles.block}>
                  <View style={styles.blockHeading}>
                    <Text variant="label" style={styles.grow}>{t('zones.activeProfile')}</Text>
                    <Tag label={`v${state.active_profile.version}`} tone="neutral" />
                  </View>
                  <ProfileValues profile={state.active_profile} />
                </View>
              ) : (
                <Text variant="supporting" tone="textMuted">{t('zones.noActiveProfile')}</Text>
              )}
              {pending ? (
                <View style={styles.pending}>
                  <View style={styles.blockHeading}>
                    <Text variant="label" style={styles.grow}>{t('zones.pendingProfile')}</Text>
                    <Text variant="caption" tone="warning">v{pending.version}</Text>
                  </View>
                  <ProfileValues profile={pending} />
                  {pending.proposal_id ? (
                    <View style={[styles.buttonRow, !compact && styles.buttonRowWide]}>
                      <View style={[styles.buttonCell, !compact && styles.grow]}>
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
                      <View style={[styles.buttonCell, !compact && styles.grow]}>
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
                <View style={styles.block}>
                  <Text variant="label">{t('zones.priorValues')}</Text>
                  {state.prior_profiles.map((previous) => (
                    <View key={previous.id} style={styles.prior}>
                      <Text variant="caption" tone="textMuted">
                        {t('zones.priorVersion', { version: previous.version, status: previous.status })}
                      </Text>
                      <ProfileValues profile={previous} />
                    </View>
                  ))}
                </View>
              ) : null}

              {state.available_test_scheduling_modes.length > 0 ? (
                <View style={styles.block}>
                  <Text variant="label" accessibilityRole="header">{t('zones.schedule.title')}</Text>
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
                  <ChoiceChips
                    isSelected={(mode) => modes[state.discipline] === mode}
                    mode="radio"
                    onPress={(mode) => setModes((current) => ({ ...current, [state.discipline]: mode }))}
                    options={state.available_test_scheduling_modes.map((mode) => ({
                      value: mode,
                      label: mode === 'standalone' ? t('zones.schedule.standalone') : t('zones.schedule.weeklyPlan'),
                      disabled: mode === 'weekly_plan' && !canIntegrate,
                    }))}
                  />
                  {state.discipline === 'swim' ? (
                    <Text variant="supporting" tone="textMuted">{t('zones.schedule.swimHint')}</Text>
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

              <Button
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
                trailingIcon={studioPresentation ? undefined : 'forward'}
                variant={studioPresentation ? 'secondary' : 'primary'}
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

const hairline = { borderTopColor: colors.border, borderTopWidth: StyleSheet.hairlineWidth } as const;
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 }, scroll: { flex: 1 },
  content: { alignSelf: 'center', gap: screenGap, maxWidth: layout.readingWidth, padding: layout.phoneGutter, paddingBottom: space[48], width: '100%' },
  grow: { flex: 1, minWidth: 0 },
  // V3 states the profile on the page itself; V2 keeps its hero card.
  intro: studioPresentation ? { gap: space[12] }
    : { ...shadows.card, backgroundColor: colors.surface, borderRadius: radius.card, gap: space[24], padding: space[16] },
  heroHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: space[16] },
  stacked: { flexDirection: 'column', flexWrap: 'nowrap', alignItems: 'flex-start' },
  heroCopy: { flex: studioPresentation ? undefined : 1, minWidth: 0, gap: space[8] },
  fullWidth: { flex: 0, width: '100%' },
  summaryRow: studioPresentation ? { flexDirection: 'row', flexWrap: 'wrap', gap: 10 }
    : { flexDirection: 'row', flexWrap: 'wrap', gap: space[24], borderTopWidth: 1, borderTopColor: colors.border, paddingTop: space[24] },
  stat: studioPresentation ? { flexGrow: 1, flexBasis: 130, backgroundColor: colors.surface, borderRadius: radius.card, padding: 14 }
    : { flexDirection: 'row', gap: space[12], alignItems: 'center', flexGrow: 1, flexBasis: 150 },
  statCopy: { flexShrink: 1, minWidth: 0, gap: studioPresentation ? 2 : space[8] },
  panel: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: radius.card, gap: space[16], padding: space[16],
    ...(studioPresentation ? { borderWidth: StyleSheet.hairlineWidth } : { ...shadows.card, borderWidth: 1 }) },
  panelIdentity: { alignItems: 'center', flexDirection: 'row', gap: studioPresentation ? space[12] : space[16] },
  panelIdentityCopy: { flex: 1, minWidth: 0, gap: studioPresentation ? space[4] : space[8] },
  block: { ...hairline, gap: space[12], paddingTop: space[16] },
  blockHeading: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: space[8] },
  pending: { backgroundColor: colors.warningSoft, borderRadius: radius.control, gap: space[12], padding: space[12] },
  prior: { gap: space[8] },
  buttonRow: { gap: space[12] }, buttonRowWide: { flexDirection: 'row' }, buttonCell: { minWidth: 0 },
});
