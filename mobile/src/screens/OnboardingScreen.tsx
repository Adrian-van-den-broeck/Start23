import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { FormScrollView } from '../components/FormScrollView';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  approveZoneProposal,
  completeOnboarding,
  getGoalPlanningOptions,
  getOnboarding,
  getPhysiologyProfile,
  rejectZoneProposal,
  saveCalculatedZones,
  saveDisciplineSetup,
  saveOperationalProfile,
  savePrimaryGoal,
  saveProfile,
  saveTrainingHistory,
} from '../api/client';
import type {
  AthleteProfile,
  AthletePhysiologyProfile,
  Discipline,
  DisciplineSetupInput,
  GoalPlanningOption,
  OnboardingState,
  OnboardingStep,
} from '../api/types';
import { GoalStep } from '../ui-v2/screens/GoalForm';
export { GoalStep } from '../ui-v2/screens/GoalForm';
import { colors, layout, radius, space, typography } from '../ui-v2/tokens';
import { BrandedFormHeader, FormComposition } from '../ui-v2/components/FormComposition';
import { ProfileForm } from '../ui-v2/components/ProfileForm';
import { StepProgress } from '../ui-v2/components/StepProgress';
import { Button } from '../ui-v2/primitives/Button';
import { Input } from '../ui-v2/primitives/Input';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Notice } from '../ui-v2/primitives/Notice';
import {
  resolveDeviceTimezone,
} from '../lib/onboardingForms';
import { ZoneSetupStep } from './ZoneSetupStep';
import { useLanguage, type TranslationKey } from '../i18n/LanguageProvider';

const stepLabelKeys: Array<{ step: OnboardingStep; labelKey: TranslationKey }> = [
  { step: 'profile', labelKey: 'onboarding.step.profile' },
  { step: 'heart_rate_monitor', labelKey: 'onboarding.step.heartRateMonitor' },
  { step: 'timezone', labelKey: 'onboarding.step.timezone' },
  { step: 'history', labelKey: 'onboarding.step.history' },
  { step: 'goal', labelKey: 'onboarding.step.goal' },
  { step: 'zones', labelKey: 'onboarding.step.zones' },
  { step: 'review', labelKey: 'onboarding.step.review' },
];

type OnboardingScreenProps = {
  accessToken: string;
  active?: boolean;
  takeOnboardingSnapshot?: () => OnboardingState | undefined;
  onOpenCalibration: () => void;
  onOpenPlanning: () => void;
  onSignOut: () => Promise<void>;
};

type StepFrameProps = { title: string; description: string; children: React.ReactNode };
function StepFrame(props: StepFrameProps) { return <FormComposition {...props} />; }

type ActionButtonProps = { label: string; loading?: boolean; disabled?: boolean; secondary?: boolean; onPress: () => void };
function ActionButton({ label, loading = false, disabled = false, secondary = false, onPress }: ActionButtonProps) {
  return <Button label={label} busy={loading} disabled={disabled} variant={secondary ? 'secondary' : 'primary'} trailingIcon={secondary ? undefined : 'forward'} onPress={onPress} />;
}

export function ProfileStep(props: Parameters<typeof ProfileForm>[0]) { return <ProfileForm {...props} />; }

type ConfirmationStepProps = {
  saving: boolean;
  onSave: () => Promise<void>;
};

export function HeartRateMonitorStep({ saving, onSave }: ConfirmationStepProps) {
  const { t } = useLanguage();
  return (
    <StepFrame
      description={t('onboarding.heartRate.description')}
      title={t('onboarding.heartRate.title')}
    >
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>{t('onboarding.heartRate.rpeOnlyTitle')}</Text>
        <Text style={styles.approvalText}>
          {t('onboarding.heartRate.rpeOnlyText')}
        </Text>
      </View>
      <ActionButton
        label={t('onboarding.heartRate.confirm')}
        loading={saving}
        onPress={() => void onSave()}
      />
    </StepFrame>
  );
}

type TimezoneStepProps = {
  profile: AthleteProfile | null;
  saving: boolean;
  onSave: (timezone: string, source: 'device' | 'manual') => Promise<void>;
};

const fallbackTimezones = [
  'Europe/Amsterdam',
  'Europe/Brussels',
  'Europe/London',
  'Europe/Paris',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'Australia/Sydney',
] as const;

export function TimezoneStep({ profile, saving, onSave }: TimezoneStepProps) {
  const { t } = useLanguage();
  const detected = useMemo(resolveDeviceTimezone, []);
  const [timezone, setTimezone] = useState(
    profile?.timezone_confirmed_at ? (profile.timezone ?? '') : '',
  );
  const [source, setSource] = useState<'device' | 'manual'>(
    profile?.timezone_source ?? (detected ? 'device' : 'manual'),
  );

  return (
    <StepFrame
      description={t('onboarding.timezone.description')}
      title={t('onboarding.timezone.title')}
    >
      {detected ? (
        <Button label={t('onboarding.timezone.detected', { timezone: detected })} variant="secondary" onPress={() => { setTimezone(detected); setSource('device'); }} />
      ) : (
        <Text style={styles.fieldError}>
          {t('onboarding.timezone.noDetection')}
        </Text>
      )}
      <View style={styles.goalModeList}>
        {fallbackTimezones.map((value) => (
          <ChoiceRow key={value} label={value} selected={timezone === value} onPress={() => { setTimezone(value); setSource('manual'); }} />
        ))}
      </View>
      <Input
        autoCapitalize="none"
        hint={t('onboarding.timezone.otherHint')}
        icon="location"
        label={t('onboarding.timezone.otherLabel')}
        onChangeText={(value) => {
          setTimezone(value);
          setSource('manual');
        }}
        placeholder="Europe/Amsterdam"
        value={timezone}
      />
      <ActionButton
        disabled={!timezone.trim()}
        label={t('onboarding.timezone.confirm')}
        loading={saving}
        onPress={() => void onSave(timezone.trim(), source)}
      />
    </StepFrame>
  );
}

type HistoryStepProps = {
  state: OnboardingState;
  saving: boolean;
  onSave: (values: Record<Discipline, string>) => Promise<void>;
};

export function HistoryStep({ state, saving, onSave }: HistoryStepProps) {
  const { t } = useLanguage();
  const initial = (discipline: Discipline): string => {
    const entry = state.training_history.find((item) => item.discipline === discipline);
    return entry?.previous_month_weekly_minutes != null
      ? String(Number(entry.previous_month_weekly_minutes) / 60)
      : '';
  };
  const [values, setValues] = useState<Record<Discipline, string>>({
    swim: initial('swim'), bike: initial('bike'), run: initial('run'),
  });
  const hours = Object.values(values).map((value) => Number(value.replace(',', '.')));
  const valid = Object.values(values).every((value) => value.trim() !== '') &&
    hours.every((value) => Number.isFinite(value) && value >= 0) &&
    hours.reduce((total, value) => total + value, 0) <= 168;
  return (
    <StepFrame
      description={t('onboarding.history.description')}
      title={t('onboarding.history.title')}
    >
      <View style={styles.form}>
        {(['swim', 'bike', 'run'] as const).map((discipline) => (
          <View key={discipline} style={styles.disciplineCard}>
            <Text style={styles.cardTitle}>
              {t(discipline === 'swim' ? 'common.swim' : discipline === 'bike' ? 'common.bike' : 'onboarding.history.run')}
            </Text>
            <Input
              inputMode="decimal"
              label={t('onboarding.history.hoursLabel')}
              onChangeText={(value) => setValues((current) => ({ ...current, [discipline]: value }))}
              placeholder="0"
              unit={t('onboarding.history.hoursUnit')}
              accessibilityLabel={t('onboarding.history.hoursLabel')}
              value={values[discipline]}
            />
          </View>
        ))}
      </View>
      <ActionButton disabled={!valid} label={t('onboarding.history.save')} loading={saving}
        onPress={() => void onSave(values)} />
    </StepFrame>
  );
}

type ReviewStepProps = {
  state: OnboardingState;
  saving: boolean;
  onComplete: () => Promise<void>;
  onApproveZone: (
    proposalId: string,
    baseZoneProfileId: string | null,
  ) => Promise<void>;
  onRejectZone: (proposalId: string) => Promise<void>;
};

export function ReviewStep({
  state,
  saving,
  onComplete,
  onApproveZone,
  onRejectZone,
}: ReviewStepProps) {
  const { t } = useLanguage();
  const pendingZones = state.zones.filter(
    (zone) =>
      state.required_disciplines.includes(zone.discipline) &&
      zone.status === 'pending' &&
      zone.proposal_id !== null,
  );
  return (
    <StepFrame
      description={t('onboarding.review.description')}
      title={t('onboarding.review.title')}
    >
      <View style={styles.reviewCard}>
        <ReviewRow
          label={t('onboarding.step.profile')}
          value={state.profile?.timezone ?? t('onboarding.review.missing')}
        />
        <ReviewRow
          label={t('onboarding.step.history')}
          value={t('onboarding.review.disciplineCount', { done: state.training_history.length, total: 3 })}
        />
        <ReviewRow
          label={t('onboarding.review.goal')}
          value={state.primary_goal?.race_name ?? t('onboarding.review.missing')}
        />
        <ReviewRow
          label={t('onboarding.review.activeZones')}
          value={t('onboarding.review.disciplineCount', {
            done: new Set(
              state.zones
                .filter(
                  (zone) =>
                    state.required_disciplines.includes(zone.discipline) &&
                    zone.status === 'active',
                )
                .map((zone) => zone.discipline),
            ).size,
            total: state.required_disciplines.length,
          })}
        />
      </View>
      {pendingZones.map((zone) => (
        <View key={zone.id} style={styles.approvalNotice}>
          <Text style={styles.approvalTitle}>
            {t('onboarding.review.zoneProposal', { discipline: zone.discipline })}
          </Text>
          <Text style={styles.approvalText}>
            {t('onboarding.review.zoneProposalText', {
              subject: zone.metric_profiles.length > 1
                ? t('onboarding.review.metricRepresentations', { count: zone.metric_profiles.length })
                : zone.metric?.metric_kind ?? t('onboarding.review.calculatedZones'),
              version: zone.zone_model_version ?? '',
            })}
          </Text>
          <ActionButton
            disabled={saving}
            label={t('onboarding.review.approveZones')}
            onPress={() =>
              void onApproveZone(
                zone.proposal_id!,
                zone.base_zone_profile_id,
              )
            }
          />
          <ActionButton
            disabled={saving}
            label={t('onboarding.review.rejectZones')}
            onPress={() => void onRejectZone(zone.proposal_id!)}
            secondary
          />
        </View>
      ))}
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>{t('onboarding.review.controlTitle')}</Text>
        <Text style={styles.approvalText}>
          {t('onboarding.review.controlText')}
        </Text>
      </View>
      <ActionButton
        disabled={!state.can_complete}
        label={t('onboarding.review.complete')}
        loading={saving}
        onPress={() => void onComplete()}
      />
    </StepFrame>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  const { width, fontScale } = useWindowDimensions();
  const compact = width < 393 || fontScale > 1;
  return (
    <View style={[styles.reviewRow, compact && { flexDirection: 'column', alignItems: 'stretch' }]}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={[styles.reviewValue, compact && { textAlign: 'left' }]}>{value}</Text>
    </View>
  );
}

export function OnboardingScreen({
  accessToken,
  active = true,
  takeOnboardingSnapshot,
  onOpenCalibration,
  onOpenPlanning,
  onSignOut,
}: OnboardingScreenProps) {
  const { t } = useLanguage();
  const stepLabels = useMemo(
    () => stepLabelKeys.map(({ step, labelKey }) => ({ step, label: t(labelKey) })),
    [t],
  );
  const [state, setState] = useState<OnboardingState | null>(null);
  const [physiologyProfile, setPhysiologyProfile] =
    useState<AthletePhysiologyProfile | null>(null);
  const [goalOptions, setGoalOptions] = useState<GoalPlanningOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (snapshot?: OnboardingState) => {
    const nextState = snapshot ?? getOnboarding(accessToken);
    const [next, nextPhysiologyProfile, nextGoalOptions] = await Promise.all([
      nextState,
      getPhysiologyProfile(accessToken),
      Promise.resolve(nextState).then((state) =>
        state.current_step === 'goal' ? getGoalPlanningOptions(accessToken) : [],
      ),
    ]);
    return { next, nextGoalOptions, nextPhysiologyProfile };
  }, [accessToken]);

  const apply = useCallback(({ next, nextGoalOptions, nextPhysiologyProfile }: Awaited<ReturnType<typeof load>>) => {
    if (next.current_step === 'completed') {
      onOpenPlanning();
      return;
    }
    setState(next);
    setGoalOptions(nextGoalOptions);
    setPhysiologyProfile(nextPhysiologyProfile);
  }, [onOpenPlanning]);

  const reload = useCallback(async () => {
    apply(await load());
  }, [apply, load]);

  const retryLoad = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await reload();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('onboarding.loadFailed'),
      );
    } finally {
      setLoading(false);
    }
  }, [reload]);

  useEffect(() => {
    if (!active) return;
    let mounted = true;
    load(takeOnboardingSnapshot?.())
      .then((result) => {
        if (mounted) {
          apply(result);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error
              ? caught.message
              : t('onboarding.loadFailed'),
          );
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [active, apply, load, takeOnboardingSnapshot]);

  const mutate = async (
    operation: () => Promise<unknown>,
    options: {
      reloadAfter?: boolean;
      onSuccess?: () => void;
    } = {},
  ) => {
    setSaving(true);
    setError(null);
    try {
      await operation();
      if (options.reloadAfter ?? true) await reload();
      options.onSuccess?.();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('onboarding.saveFailed'),
      );
    } finally {
      setSaving(false);
    }
  };

  const finishOnboarding = async (expectedRevision: number) => {
    setSaving(true);
    setError(null);
    try {
      await completeOnboarding(accessToken, expectedRevision);
      onOpenPlanning();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('onboarding.completeFailed'),
      );
    } finally {
      setSaving(false);
    }
  };

  const completed = useMemo(
    () => {
      const steps = new Set(state?.completed_steps ?? []);
      if (
        physiologyProfile?.date_of_birth &&
        physiologyProfile.resting_heart_rate_bpm !== null
      ) {
        steps.add('profile');
      }
      return steps;
    }, [physiologyProfile, state?.completed_steps],
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={colors.primary} size="large" />
        <Text style={styles.loadingText}>{t('onboarding.loading')}</Text>
      </SafeAreaView>
    );
  }

  if (!state) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.errorTitle}>{t('onboarding.loadFailedTitle')}</Text>
        {error ? <Text style={styles.centeredError}>{error}</Text> : null}
        <ActionButton
          label={t('shell.retry')}
          onPress={() => void retryLoad()}
        />
        <ActionButton
          label={t('activity.signOut')}
          onPress={() => void onSignOut()}
          secondary
        />
      </SafeAreaView>
    );
  }

  const physiologyProfileComplete =
    physiologyProfile?.date_of_birth !== null &&
    physiologyProfile?.date_of_birth !== undefined &&
    physiologyProfile.resting_heart_rate_bpm !== null;
  const step =
    state.current_step === 'profile' && physiologyProfileComplete
      ? 'heart_rate_monitor'
      : state.current_step;
  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.keyboard}>
        <FormScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} style={styles.scroll}>
          <BrandedFormHeader caption={t('onboarding.headerCaption')} onSignOut={onSignOut}>
            {state.discipline_setups.some((setup) => setup.protocol_id) ? <Button label={t('onboarding.openCalibration')} variant="secondary" onPress={onOpenCalibration} /> : null}
          </BrandedFormHeader>
          {state.upgrade_required ? <Notice title={t('onboarding.upgrade.title')}>{t('onboarding.upgrade.text', {
            version: state.current_onboarding_version,
            steps: state.missing_upgrade_steps.length ? state.missing_upgrade_steps.map((missing) => stepLabels.find((item) => item.step === missing)?.label ?? missing).join(', ') : t('onboarding.upgrade.reviewOnly'),
          })}</Notice> : null}
          <StepProgress current={step} steps={stepLabels} completed={completed} />
          {error ? <Notice tone="error">{error}</Notice> : null}

          {step === 'profile' ? (
            <ProfileStep
              key={state.profile?.revision ?? 0}
              onSave={(input) =>
                mutate(() => saveProfile(accessToken, input))
              }
              profile={state.profile}
              saving={saving}
            />
          ) : null}
          {step === 'heart_rate_monitor' ? (
            <HeartRateMonitorStep
              onSave={() =>
                mutate(() =>
                  saveOperationalProfile(accessToken, {
                    heart_rate_monitor_confirmed: true,
                  }),
                )
              }
              saving={saving}
            />
          ) : null}
          {step === 'timezone' ? (
            <TimezoneStep
              onSave={(timezone, source) =>
                mutate(() =>
                  saveOperationalProfile(accessToken, {
                    timezone,
                    timezone_source: source,
                    timezone_confirmed: true,
                  }),
                )
              }
              profile={state.profile}
              saving={saving}
            />
          ) : null}
          {step === 'history' ? (
            <HistoryStep
              key={state.training_history
                .map((entry) => entry.updated_at)
                .join(':')}
              onSave={(values) =>
                mutate(() =>
                  saveTrainingHistory(
                    accessToken,
                    (['swim', 'bike', 'run'] as const).map((discipline) => ({
                      discipline,
                      average_hours_per_week: values[discipline].replace(',', '.'),
                    })),
                  ),
                )
              }
              saving={saving}
              state={state}
            />
          ) : null}
          {step === 'goal' ? (
            <GoalStep
              goal={state.primary_goal}
              key={state.primary_goal?.revision ?? 0}
              options={goalOptions}
              onSave={(input) =>
                mutate(() =>
                  savePrimaryGoal(
                    accessToken,
                    input,
                    state.primary_goal?.id,
                  ),
                )
              }
              saving={saving}
            />
          ) : null}
          {step === 'zones' ? (
            <>
              <ZoneSetupStep
                accessToken={accessToken}
                key={[
                  ...state.zones.map((zone) => `${zone.id}:${zone.status}`),
                  ...state.discipline_setups.map(
                    (setup) => `${setup.discipline}:${setup.revision}`,
                  ),
                ].join(':')}
                onSave={(discipline, input: DisciplineSetupInput) =>
                  mutate(
                    async () => {
                      if (input.setup_route === 'known_values') {
                        await saveCalculatedZones(accessToken, discipline, {
                          thresholds: input.thresholds,
                          source_quality: input.source_quality,
                          boundary_overrides: input.zone_profiles,
                        });
                      }
                      await saveDisciplineSetup(accessToken, discipline, input);
                    },
                    input.setup_route === 'known_values'
                      ? {}
                      : {
                          reloadAfter: false,
                          onSuccess: onOpenCalibration,
                        },
                  )
                }
                saving={saving}
                state={state}
              />
              {state.zones
                .filter(
                  (zone) =>
                    state.required_disciplines.includes(zone.discipline) &&
                    zone.status === 'pending' &&
                    zone.proposal_id !== null,
                )
                .map((zone) => (
                  <View key={zone.id} style={styles.approvalNotice}>
                    <Text style={styles.approvalTitle}>
                      {t('onboarding.zones.pendingTitle', { discipline: zone.discipline })}
                    </Text>
                    <Text style={styles.approvalText}>
                      {t('onboarding.zones.pendingText')}
                    </Text>
                    <ActionButton
                      disabled={saving}
                      label={t('onboarding.zones.approve', { discipline: zone.discipline })}
                      onPress={() =>
                        void mutate(() =>
                          approveZoneProposal(
                            accessToken,
                            zone.proposal_id!,
                            zone.base_zone_profile_id,
                          ),
                        )
                      }
                    />
                    <ActionButton
                      disabled={saving}
                      label={t('onboarding.zones.reject', { discipline: zone.discipline })}
                      onPress={() =>
                        void mutate(() =>
                          rejectZoneProposal(accessToken, zone.proposal_id!),
                        )
                      }
                      secondary
                    />
                  </View>
                ))}
            </>
          ) : null}
          {step === 'review' ? (
            <ReviewStep
              onApproveZone={(proposalId, baseZoneProfileId) =>
                mutate(() =>
                  approveZoneProposal(
                    accessToken,
                    proposalId,
                    baseZoneProfileId,
                  ),
                )
              }
              onComplete={() =>
                finishOnboarding(state.onboarding_revision)
              }
              onRejectZone={(proposalId) =>
                mutate(() => rejectZoneProposal(accessToken, proposalId))
              }
              saving={saving}
              state={state}
            />
          ) : null}
        </FormScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create(
{
  safeArea: {
    backgroundColor: colors.background,
    flex: 1,
  },
  keyboard: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  centered: {
    alignItems: 'center',
    backgroundColor: colors.background,
    flex: 1,
    gap: space[16],
    justifyContent: 'center',
    padding: space[24],
  },
  loadingText: {
    color: colors.textMuted,
    fontSize: 14,
  },
  errorTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'center',
  },
  centeredError: {
    color: colors.destructive,
    lineHeight: 20,
    textAlign: 'center',
  },
  scrollContent: {
    alignSelf: 'center',
    maxWidth: layout.readingWidth,
    padding: layout.phoneGutter,
    gap: space[24],
    paddingBottom: space[48],
    width: '100%',
  },
  fieldError: {
    color: colors.destructive,
    ...typography.supporting,
  },
  form: {
    gap: layout.fieldGroupGap,
  },
  goalModeList: {
    gap: space[8],
  },
  disciplineCard: { gap: space[16] },
  cardTitle: {
    color: colors.text,
    ...typography.cardTitle,
  },
  reviewCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.control,
    padding: space[16],
  },
  reviewRow: {
    alignItems: 'center',
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    gap: space[16],
    justifyContent: 'space-between',
    paddingVertical: space[16],
  },
  reviewLabel: {
    color: colors.textMuted,
    ...typography.label,
    flexShrink: 1,
  },
  reviewValue: {
    color: colors.text,
    flex: 1,
    ...typography.body,
    fontWeight: '600',
    textAlign: 'right',
  },
  approvalNotice: {
    backgroundColor: colors.primarySoft,
    borderRadius: radius.control,
    gap: space[4],
    padding: space[16],
  },
  approvalTitle: {
    color: colors.primary,
    ...typography.label,
  },
  approvalText: {
    color: colors.primary,
    ...typography.body,
  }
});
