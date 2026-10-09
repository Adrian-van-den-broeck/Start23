import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
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

const stepLabels: Array<{ step: OnboardingStep; label: string }> = [
  { step: 'profile', label: 'Profiel' },
  { step: 'heart_rate_monitor', label: 'Hartslag' },
  { step: 'timezone', label: 'Tijdzone' },
  { step: 'history', label: 'Historie' },
  { step: 'goal', label: 'Doel' },
  { step: 'zones', label: 'Zones' },
  { step: 'review', label: 'Afronden' },
];

type OnboardingScreenProps = {
  accessToken: string;
  active?: boolean;
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
  return (
    <StepFrame
      description="Voor het huidige MVP moet je gemiddelde hartslag kunnen meten. Dat mag met iedere hartslagmeter en je kunt de waarde handmatig invoeren; een specifieke wearable is niet nodig."
      title="Heb je toegang tot een hartslagmeter?"
    >
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>RPE-only is niet beschikbaar</Text>
        <Text style={styles.approvalText}>
          Zonder bevestigde toegang kan onboarding niet worden afgerond en kan
          er geen planning worden aangemaakt.
        </Text>
      </View>
      <ActionButton
        label="Ja, ik kan gemiddelde hartslag meten"
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
  const detected = useMemo(resolveDeviceTimezone, []);
  const [timezone, setTimezone] = useState(
    profile?.timezone_confirmed_at ? (profile.timezone ?? '') : '',
  );
  const [source, setSource] = useState<'device' | 'manual'>(
    profile?.timezone_source ?? (detected ? 'device' : 'manual'),
  );

  return (
    <StepFrame
      description="Je tijdzone bepaalt lokale trainingsweken en datums. Controleer de gedetecteerde waarde of kies expliciet een IANA-tijdzone. We slaan nooit stilzwijgend een gok op."
      title="Bevestig je tijdzone"
    >
      {detected ? (
        <Button label={"Gedetecteerd op dit apparaat: " + detected} variant="secondary" onPress={() => { setTimezone(detected); setSource('device'); }} />
      ) : (
        <Text style={styles.fieldError}>
          Automatische detectie is niet beschikbaar. Kies hieronder een tijdzone.
        </Text>
      )}
      <View style={styles.goalModeList}>
        {fallbackTimezones.map((value) => (
          <ChoiceRow key={value} label={value} selected={timezone === value} onPress={() => { setTimezone(value); setSource('manual'); }} />
        ))}
      </View>
      <Input
        autoCapitalize="none"
        hint="Gebruik een geldige IANA-naam als je tijdzone niet in de lijst staat."
        icon="location"
        label="Andere IANA-tijdzone"
        onChangeText={(value) => {
          setTimezone(value);
          setSource('manual');
        }}
        placeholder="Europe/Amsterdam"
        value={timezone}
      />
      <ActionButton
        disabled={!timezone.trim()}
        label="Tijdzone expliciet bevestigen"
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
      description="Hoeveel uur per week trainde je gemiddeld de afgelopen maand? Vul ook nul in als je een discipline niet deed."
      title="Waar sta je nu?"
    >
      <View style={styles.form}>
        {(['swim', 'bike', 'run'] as const).map((discipline) => (
          <View key={discipline} style={styles.disciplineCard}>
            <Text style={styles.cardTitle}>
              {discipline === 'swim' ? 'Zwemmen' : discipline === 'bike' ? 'Fietsen' : 'Hardlopen'}
            </Text>
            <Input
              inputMode="decimal"
              label="Gemiddelde uren per week"
              onChangeText={(value) => setValues((current) => ({ ...current, [discipline]: value }))}
              placeholder="0"
              unit="uur/week"
              accessibilityLabel="Gemiddelde uren per week"
              value={values[discipline]}
            />
          </View>
        ))}
      </View>
      <ActionButton disabled={!valid} label="Trainingshistorie opslaan" loading={saving}
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
  const pendingZones = state.zones.filter(
    (zone) =>
      state.required_disciplines.includes(zone.discipline) &&
      zone.status === 'pending' &&
      zone.proposal_id !== null,
  );
  return (
    <StepFrame
      description="Afronden maakt geen trainingsplan actief. Het zet alleen een planningsverzoek klaar voor de volgende fase."
      title="Klaar voor je eerste voorstel"
    >
      <View style={styles.reviewCard}>
        <ReviewRow
          label="Profiel"
          value={state.profile?.timezone ?? 'Ontbreekt'}
        />
        <ReviewRow
          label="Historie"
          value={`${state.training_history.length}/3 disciplines`}
        />
        <ReviewRow
          label="A-doel"
          value={state.primary_goal?.race_name ?? 'Ontbreekt'}
        />
        <ReviewRow
          label="Actieve zones"
          value={`${
            new Set(
              state.zones
                .filter(
                  (zone) =>
                    state.required_disciplines.includes(zone.discipline) &&
                    zone.status === 'active',
                )
                .map((zone) => zone.discipline),
            ).size
          }/${state.required_disciplines.length} disciplines`}
        />
      </View>
      {pendingZones.map((zone) => (
        <View key={zone.id} style={styles.approvalNotice}>
          <Text style={styles.approvalTitle}>
            Zonevoorstel {zone.discipline}
          </Text>
          <Text style={styles.approvalText}>
            {zone.metric_profiles.length > 1
              ? `${zone.metric_profiles.length} metrische representaties`
              : zone.metric?.metric_kind ?? 'Berekende zones'}{' '}
            volgens {zone.zone_model_version}. De huidige zones veranderen pas
            na jouw bevestiging.
          </Text>
          <ActionButton
            disabled={saving}
            label="Zones bevestigen"
            onPress={() =>
              void onApproveZone(
                zone.proposal_id!,
                zone.base_zone_profile_id,
              )
            }
          />
          <ActionButton
            disabled={saving}
            label="Zonevoorstel afwijzen"
            onPress={() => void onRejectZone(zone.proposal_id!)}
            secondary
          />
        </View>
      ))}
      <View style={styles.approvalNotice}>
        <Text style={styles.approvalTitle}>Jij houdt de controle</Text>
        <Text style={styles.approvalText}>
          Ook het toekomstige weekplan wordt eerst als voorstel getoond. Er
          verandert niets zonder een aparte goedkeuring.
        </Text>
      </View>
      <ActionButton
        disabled={!state.can_complete}
        label="Onboarding afronden"
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
  onOpenCalibration,
  onOpenPlanning,
  onSignOut,
}: OnboardingScreenProps) {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [physiologyProfile, setPhysiologyProfile] =
    useState<AthletePhysiologyProfile | null>(null);
  const [goalOptions, setGoalOptions] = useState<GoalPlanningOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [next, nextGoalOptions, nextPhysiologyProfile] = await Promise.all([
      getOnboarding(accessToken),
      getGoalPlanningOptions(accessToken),
      getPhysiologyProfile(accessToken),
    ]);
    if (next.current_step === 'completed') {
      onOpenPlanning();
      return;
    }
    setState(next);
    setGoalOptions(nextGoalOptions);
    setPhysiologyProfile(nextPhysiologyProfile);
  }, [accessToken, onOpenPlanning]);

  const retryLoad = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await reload();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Onboarding laden is niet gelukt.',
      );
    } finally {
      setLoading(false);
    }
  }, [reload]);

  useEffect(() => {
    if (!active) return;
    let mounted = true;
    Promise.all([
      getOnboarding(accessToken),
      getGoalPlanningOptions(accessToken),
      getPhysiologyProfile(accessToken),
    ])
      .then(([next, nextGoalOptions, nextPhysiologyProfile]) => {
        if (mounted) {
          if (next.current_step === 'completed') {
            onOpenPlanning();
            return;
          }
          setState(next);
          setGoalOptions(nextGoalOptions);
          setPhysiologyProfile(nextPhysiologyProfile);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error
              ? caught.message
              : 'Onboarding laden is niet gelukt.',
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
  }, [accessToken, active, onOpenPlanning]);

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
          : 'Opslaan is niet gelukt.',
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
          : 'Afronden is niet gelukt.',
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
        <Text style={styles.loadingText}>Je intake wordt hervat…</Text>
      </SafeAreaView>
    );
  }

  if (!state) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.errorTitle}>We kunnen je intake niet laden.</Text>
        {error ? <Text style={styles.centeredError}>{error}</Text> : null}
        <ActionButton
          label="Opnieuw proberen"
          onPress={() => void retryLoad()}
        />
        <ActionButton
          label="Afmelden"
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
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboard}
      >
        <ScrollView automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'} contentContainerStyle={styles.scrollContent}
          keyboardDismissMode="on-drag" keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} style={styles.scroll}>
          <BrandedFormHeader caption="Jouw profiel" onSignOut={onSignOut}>
            {state.discipline_setups.some((setup) => setup.protocol_id) ? <Button label="Testen" variant="secondary" onPress={onOpenCalibration} /> : null}
          </BrandedFormHeader>
          {state.upgrade_required ? <Notice title="Werk je onboarding bij">{'Je eerdere afronding blijft bewaard. Alleen deze onderdelen zijn nog nodig voor ' + state.current_onboarding_version + ': ' + (state.missing_upgrade_steps.length ? state.missing_upgrade_steps.map((missing) => stepLabels.find((item) => item.step === missing)?.label ?? missing).join(', ') : 'controle en bevestiging') + '.'}</Notice> : null}
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
                      Zonevoorstel {zone.discipline} wacht op bevestiging
                    </Text>
                    <Text style={styles.approvalText}>
                      De berekende zones worden pas na deze aparte, stale-safe
                      bevestiging actief.
                    </Text>
                    <ActionButton
                      disabled={saving}
                      label={`Zones ${zone.discipline} bevestigen`}
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
                      label={`Zonevoorstel ${zone.discipline} afwijzen`}
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
        </ScrollView>
      </KeyboardAvoidingView>
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
