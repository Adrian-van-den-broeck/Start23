import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  BackHandler,
  StyleSheet,
  View,
  type ScrollView,
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
import { colors, layout, radius, space } from '../ui-v2/tokens';
import { BrandedFormHeader, FormComposition, formGap } from '../ui-v2/components/FormComposition';
import { ProfileForm } from '../ui-v2/components/ProfileForm';
import { StepProgress } from '../ui-v2/components/StepProgress';
import { Button } from '../ui-v2/primitives/Button';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { Icon } from '../ui-v2/primitives/Icon';
import { Input } from '../ui-v2/primitives/Input';
import { Notice } from '../ui-v2/primitives/Notice';
import { SelectField } from '../ui-v2/primitives/SelectField';
import { Text } from '../ui-v2/primitives/Text';
import { StepNav } from '../ui-v3/onboarding/StepNav';
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

const stepOrder = stepLabelKeys.map((item) => item.step);

function stepIndex(step: OnboardingStep): number {
  const index = stepOrder.indexOf(step);
  return index === -1 ? stepOrder.length : index;
}

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
      <Notice title={t('onboarding.heartRate.rpeOnlyTitle')}>
        {t('onboarding.heartRate.rpeOnlyText')}
      </Notice>
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

const timezoneOptions = fallbackTimezones.map((value) => ({ value, label: value }));

export function TimezoneStep({ profile, saving, onSave }: TimezoneStepProps) {
  const { t } = useLanguage();
  const detected = useMemo(resolveDeviceTimezone, []);
  const [timezone, setTimezone] = useState(
    profile?.timezone_confirmed_at ? (profile.timezone ?? '') : '',
  );
  const [source, setSource] = useState<'device' | 'manual'>(
    profile?.timezone_source ?? (detected ? 'device' : 'manual'),
  );
  const listed = fallbackTimezones.find((value) => value === timezone) ?? null;

  return (
    <StepFrame
      description={t('onboarding.timezone.description')}
      title={t('onboarding.timezone.title')}
    >
      {detected ? (
        <View style={styles.detected}>
          <Text variant="caption" tone="textMuted">{t('onboarding.timezone.detectedHint')}</Text>
          <ChoiceRow
            accessibilityLabel={t('onboarding.timezone.detected', { timezone: detected })}
            label={detected}
            onPress={() => { setTimezone(detected); setSource('device'); }}
            selected={source === 'device' && timezone === detected}
          />
        </View>
      ) : (
        <Notice>{t('onboarding.timezone.noDetection')}</Notice>
      )}
      <SelectField
        label={t('onboarding.timezone.listLabel')}
        onChange={(value) => { setTimezone(value); setSource('manual'); }}
        options={timezoneOptions}
        placeholder={t('onboarding.timezone.listPlaceholder')}
        value={source === 'manual' ? listed : null}
      />
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
      {(['swim', 'bike', 'run'] as const).map((discipline) => {
        const name = t(discipline === 'swim' ? 'common.swim' : discipline === 'bike' ? 'common.bike' : 'onboarding.history.run');
        return (
          <Input
            accessibilityLabel={`${name}, ${t('onboarding.history.hoursLabel')}`}
            icon={discipline}
            inputMode="decimal"
            key={discipline}
            label={name}
            onChangeText={(value) => setValues((current) => ({ ...current, [discipline]: value }))}
            placeholder="0"
            unit={t('onboarding.history.hoursUnit')}
            value={values[discipline]}
          />
        );
      })}
      <ActionButton disabled={!valid} label={t('onboarding.history.save')} loading={saving}
        onPress={() => void onSave(values)} />
    </StepFrame>
  );
}

type ZoneProposalProps = {
  title: string;
  text: string;
  approveLabel: string;
  rejectLabel: string;
  disabled: boolean;
  onApprove: () => void;
  onReject: () => void;
};

// A calculated zone proposal that waits for the athlete's own decision.
function ZoneProposal({ title, text, approveLabel, rejectLabel, disabled, onApprove, onReject }: ZoneProposalProps) {
  return (
    <View style={styles.proposal}>
      <View style={styles.proposalFact}>
        <Icon name="document" color={colors.primary} />
        <View style={styles.proposalCopy}>
          <Text variant="label" tone="primary">{title}</Text>
          <Text variant="supporting" tone="primary">{text}</Text>
        </View>
      </View>
      <Button disabled={disabled} label={approveLabel} onPress={onApprove} trailingIcon="forward" />
      <Button disabled={disabled} label={rejectLabel} onPress={onReject} variant="outline" />
    </View>
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
      <View style={styles.summary}>
        <SummaryRow
          label={t('onboarding.step.profile')}
          value={state.profile?.timezone ?? t('onboarding.review.missing')}
        />
        <SummaryRow
          label={t('onboarding.step.history')}
          value={t('onboarding.review.disciplineCount', { done: state.training_history.length, total: 3 })}
        />
        <SummaryRow
          label={t('onboarding.review.goal')}
          value={state.primary_goal?.race_name ?? t('onboarding.review.missing')}
        />
        <SummaryRow
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
        <ZoneProposal
          approveLabel={t('onboarding.review.approveZones')}
          disabled={saving}
          key={zone.id}
          onApprove={() =>
            void onApproveZone(
              zone.proposal_id!,
              zone.base_zone_profile_id,
            )
          }
          onReject={() => void onRejectZone(zone.proposal_id!)}
          rejectLabel={t('onboarding.review.rejectZones')}
          text={t('onboarding.review.zoneProposalText', {
            subject: zone.metric_profiles.length > 1
              ? t('onboarding.review.metricRepresentations', { count: zone.metric_profiles.length })
              : zone.metric?.metric_kind ?? t('onboarding.review.calculatedZones'),
            version: zone.zone_model_version ?? '',
          })}
          title={t('onboarding.review.zoneProposal', { discipline: zone.discipline })}
        />
      ))}
      <Notice title={t('onboarding.review.controlTitle')}>
        {t('onboarding.review.controlText')}
      </Notice>
      <ActionButton
        disabled={!state.can_complete}
        label={t('onboarding.review.complete')}
        loading={saving}
        onPress={() => void onComplete()}
      />
    </StepFrame>
  );
}

// The value moves below its label by itself when the two do not fit on one line.
function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.summaryRow}>
      <Text variant="supporting" tone="textMuted">{label}</Text>
      <Text variant="label" style={styles.summaryValue}>{value}</Text>
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
  // Only the goal step needs these, so they stay null until that step is shown.
  const [goalOptions, setGoalOptions] = useState<GoalPlanningOption[] | null>(null);
  const [goalOptionsError, setGoalOptionsError] = useState<string | null>(null);
  const goalOptionsRequested = useRef(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Earlier step the athlete navigated back to. The server stays authoritative
  // for progress: this never moves the view past the server's current step.
  const [viewedStep, setViewedStep] = useState<OnboardingStep | null>(null);
  const scroll = useRef<ScrollView>(null);

  const load = useCallback(async (snapshot?: OnboardingState) => {
    const nextState = snapshot ?? getOnboarding(accessToken);
    const [next, nextPhysiologyProfile, nextGoalOptions] = await Promise.all([
      nextState,
      getPhysiologyProfile(accessToken),
      Promise.resolve(nextState).then((state) =>
        state.current_step === 'goal' ? getGoalPlanningOptions(accessToken) : null,
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
    // A load for another step fetches no goal options; keep the ones already shown.
    if (nextGoalOptions) {
      setGoalOptions(nextGoalOptions);
      setGoalOptionsError(null);
    }
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

  const physiologyProfileComplete =
    physiologyProfile?.date_of_birth !== null &&
    physiologyProfile?.date_of_birth !== undefined &&
    physiologyProfile.resting_heart_rate_bpm !== null;
  const serverStep: OnboardingStep | null = state
    ? state.current_step === 'profile' && physiologyProfileComplete
      ? 'heart_rate_monitor'
      : state.current_step
    : null;
  const revisiting =
    serverStep !== null &&
    viewedStep !== null &&
    stepIndex(viewedStep) < stepIndex(serverStep);
  const step = revisiting ? viewedStep : serverStep;
  const previousStep =
    step !== null && stepIndex(step) > 0 && stepIndex(step) < stepOrder.length
      ? stepOrder[stepIndex(step) - 1]
      : null;
  const nextStep =
    revisiting && step !== null ? stepOrder[stepIndex(step) + 1] ?? null : null;

  const showStep = useCallback(
    (target: OnboardingStep | null) => {
      setError(null);
      setViewedStep(
        target !== null &&
          serverStep !== null &&
          stepIndex(target) < stepIndex(serverStep)
          ? target
          : null,
      );
    },
    [serverStep],
  );

  useEffect(() => {
    if (!active || previousStep === null) return;
    const subscription = BackHandler.addEventListener(
      'hardwareBackPress',
      () => {
        if (!saving) showStep(previousStep);
        return true;
      },
    );
    return () => subscription.remove();
  }, [active, previousStep, saving, showStep]);

  // The first load only fetches goal options when the server is on the goal
  // step. Going back to that step from a later one fetches them here.
  const loadGoalOptions = useCallback(async () => {
    if (goalOptionsRequested.current) return;
    goalOptionsRequested.current = true;
    setGoalOptionsError(null);
    try {
      setGoalOptions(await getGoalPlanningOptions(accessToken));
    } catch (caught) {
      setGoalOptionsError(
        caught instanceof Error
          ? caught.message
          : t('onboarding.goal.loadFailed'),
      );
    } finally {
      goalOptionsRequested.current = false;
    }
  }, [accessToken, t]);

  const goalOptionsMissing =
    step === 'goal' && goalOptions === null && goalOptionsError === null;
  useEffect(() => {
    if (active && goalOptionsMissing) void loadGoalOptions();
  }, [active, goalOptionsMissing, loadGoalOptions]);

  // Each step starts at its top, and a save error shown there is not missed
  // below a long form.
  useEffect(() => {
    scroll.current?.scrollTo?.({ y: 0, animated: false });
  }, [step]);
  useEffect(() => {
    if (error) scroll.current?.scrollTo?.({ y: 0, animated: true });
  }, [error]);

  // After saving a step the athlete went back to, walk forward one step so
  // they can review the following answers; the server step still caps this.
  const saveStep = (
    operation: () => Promise<unknown>,
    options: { reloadAfter?: boolean; onSuccess?: () => void } = {},
  ) => {
    const savedStep = step;
    return mutate(operation, {
      ...options,
      onSuccess: () => {
        if (revisiting && savedStep !== null) {
          setViewedStep(stepOrder[stepIndex(savedStep) + 1] ?? null);
        }
        options.onSuccess?.();
      },
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={colors.primary} size="large" />
        <Text variant="supporting" tone="textMuted">{t('onboarding.loading')}</Text>
      </SafeAreaView>
    );
  }

  if (!state || step === null) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text variant="sectionTitle" accessibilityRole="header" style={styles.centeredText}>
          {t('onboarding.loadFailedTitle')}
        </Text>
        {error ? <Text tone="destructive" style={styles.centeredText}>{error}</Text> : null}
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

  const stepName = (target: OnboardingStep) =>
    stepLabels.find((item) => item.step === target)?.label ?? target;

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.keyboard}>
        <FormScrollView contentContainerStyle={styles.scrollContent} ref={scroll} showsVerticalScrollIndicator={false} style={styles.scroll}>
          <BrandedFormHeader caption={t('onboarding.headerCaption')} onSignOut={onSignOut}>
            {state.discipline_setups.some((setup) => setup.protocol_id) ? <Button label={t('onboarding.openCalibration')} variant="secondary" onPress={onOpenCalibration} /> : null}
          </BrandedFormHeader>
          {state.upgrade_required ? <Notice title={t('onboarding.upgrade.title')}>{t('onboarding.upgrade.text', {
            version: state.current_onboarding_version,
            steps: state.missing_upgrade_steps.length ? state.missing_upgrade_steps.map(stepName).join(', ') : t('onboarding.upgrade.reviewOnly'),
          })}</Notice> : null}
          <StepProgress
            completed={completed}
            current={step}
            navigation={
              <StepNav
                disabled={saving}
                next={nextStep ? {
                  label: t('onboarding.nav.next'),
                  accessibilityLabel: t('onboarding.nav.nextLabel'),
                  hint: t('onboarding.nav.nextHint', { step: stepName(nextStep) }),
                  onPress: () => showStep(nextStep),
                } : undefined}
                previous={previousStep ? {
                  label: t('onboarding.nav.previous'),
                  accessibilityLabel: t('onboarding.nav.previousLabel'),
                  hint: t('onboarding.nav.previousHint', { step: stepName(previousStep) }),
                  onPress: () => showStep(previousStep),
                } : undefined}
              />
            }
            steps={stepLabels}
          />
          {error ? <View accessibilityLiveRegion="polite"><Notice tone="error">{error}</Notice></View> : null}

          {step === 'profile' ? (
            <ProfileStep
              key={state.profile?.revision ?? 0}
              onSave={(input) =>
                saveStep(() => saveProfile(accessToken, input))
              }
              profile={state.profile}
              saving={saving}
            />
          ) : null}
          {step === 'heart_rate_monitor' ? (
            <HeartRateMonitorStep
              onSave={() =>
                saveStep(() =>
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
                saveStep(() =>
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
                saveStep(() =>
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
          {step === 'goal' && goalOptions ? (
            <GoalStep
              goal={state.primary_goal}
              key={state.primary_goal?.revision ?? 0}
              options={goalOptions}
              onSave={(input) =>
                saveStep(() =>
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
          {step === 'goal' && !goalOptions ? (
            goalOptionsError ? (
              <Notice
                action={{ label: t('shell.retry'), onPress: loadGoalOptions }}
                tone="error"
              >
                {goalOptionsError}
              </Notice>
            ) : (
              <ActivityIndicator accessibilityLabel={t('common.loading')} color={colors.primary} />
            )
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
                  saveStep(
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
                  <ZoneProposal
                    approveLabel={t('onboarding.zones.approve', { discipline: zone.discipline })}
                    disabled={saving}
                    key={zone.id}
                    onApprove={() =>
                      void mutate(() =>
                        approveZoneProposal(
                          accessToken,
                          zone.proposal_id!,
                          zone.base_zone_profile_id,
                        ),
                      )
                    }
                    onReject={() =>
                      void mutate(() =>
                        rejectZoneProposal(accessToken, zone.proposal_id!),
                      )
                    }
                    rejectLabel={t('onboarding.zones.reject', { discipline: zone.discipline })}
                    text={t('onboarding.zones.pendingText')}
                    title={t('onboarding.zones.pendingTitle', { discipline: zone.discipline })}
                  />
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

const styles = StyleSheet.create({
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
  centeredText: {
    textAlign: 'center',
  },
  scrollContent: {
    alignSelf: 'center',
    maxWidth: layout.readingWidth,
    padding: layout.phoneGutter,
    gap: formGap,
    paddingBottom: space[48],
    width: '100%',
  },
  detected: {
    gap: space[8],
  },
  summary: {
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  summaryRow: {
    alignItems: 'baseline',
    borderTopColor: colors.border,
    borderTopWidth: StyleSheet.hairlineWidth,
    columnGap: space[16],
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingVertical: space[12],
    rowGap: space[4],
  },
  summaryValue: {
    flexShrink: 1,
  },
  proposal: {
    backgroundColor: colors.primarySoft,
    borderRadius: radius.card,
    gap: space[12],
    padding: space[16],
  },
  proposalFact: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: space[12],
  },
  proposalCopy: {
    flex: 1,
    gap: space[4],
  },
});
