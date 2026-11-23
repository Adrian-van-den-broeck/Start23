import { useState } from 'react';
import { View } from 'react-native';
import type { AthleteProfile } from '../../api/types';
import { formatIsoDateInput, isPastIsoDateInput } from '../../lib/dateInput';
import { Button } from '../primitives/Button';
import { Input } from '../primitives/Input';
import { layout } from '../tokens';
import { FormComposition } from './FormComposition';
import { useLanguage } from '../../i18n/LanguageProvider';

type ProfileFormProps = {
  profile: AthleteProfile | null;
  saving: boolean;
  onSave: (input: {
    first_name?: string;
    last_name?: string;
    date_of_birth: string;
    resting_heart_rate_bpm: number;
  }) => Promise<void>;
};

export function ProfileForm({ profile, saving, onSave }: ProfileFormProps) {
  const { t } = useLanguage();
  const optional = t('onboarding.optional');
  const [firstName, setFirstName] = useState(profile?.first_name ?? '');
  const [lastName, setLastName] = useState(profile?.last_name ?? '');
  const [dateOfBirth, setDateOfBirth] = useState(profile?.date_of_birth ?? '');
  const [restingHeartRate, setRestingHeartRate] = useState(
    profile?.resting_heart_rate_bpm?.toString() ?? '',
  );
  const valid =
    isPastIsoDateInput(dateOfBirth) &&
    Number(restingHeartRate) > 0;

  return (
    <FormComposition
      description={t('onboarding.profile.description')}
      title={t('onboarding.profile.title')}
    >
      <View style={{ gap: layout.fieldGroupGap }}>
        <Input
          label={t('onboarding.profile.firstName')}
          optionalLabel={optional}
          icon="profile"
          accessibilityLabel={`${t('onboarding.profile.firstName')} ${optional}`}
          onChangeText={setFirstName}
          placeholder={t('onboarding.profile.firstName')}
          value={firstName}
        />
        <Input
          label={t('onboarding.profile.lastName')}
          optionalLabel={optional}
          icon="profile"
          accessibilityLabel={`${t('onboarding.profile.lastName')} ${optional}`}
          onChangeText={setLastName}
          placeholder={t('onboarding.profile.lastName')}
          value={lastName}
        />
        <Input
          hint={t('onboarding.profile.dateOfBirthHint')}
          inputMode="numeric"
          label={t('onboarding.profile.dateOfBirth')}
          icon="calendar"
          maxLength={10}
          onChangeText={(value) => setDateOfBirth(formatIsoDateInput(value))}
          placeholder="1990-05-20"
          value={dateOfBirth}
        />
        <Input
          inputMode="numeric"
          label={t('onboarding.profile.restingHeartRate')}
          icon="heartRate"
          onChangeText={setRestingHeartRate}
          placeholder="52"
          unit="bpm"
          accessibilityLabel={t('onboarding.profile.restingHeartRate')}
          value={restingHeartRate}
        />
      </View>
      <Button
        disabled={!valid}
        label={t('onboarding.profile.save')}
        trailingIcon="forward"
        busy={saving}
        onPress={() =>
          void onSave({
            ...(firstName.trim() ? { first_name: firstName.trim() } : {}),
            ...(lastName.trim() ? { last_name: lastName.trim() } : {}),
            date_of_birth: dateOfBirth,
            resting_heart_rate_bpm: Number(restingHeartRate),
          })
        }
      />
    </FormComposition>
  );
}
