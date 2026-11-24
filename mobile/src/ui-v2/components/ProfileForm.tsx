import { useState } from 'react';
import { View } from 'react-native';
import type { AthleteProfile } from '../../api/types';
import { DatePicker } from '../../components/DatePicker';
import { isPastIsoDateInput } from '../../lib/dateInput';
import { Button } from '../primitives/Button';
import { Input } from '../primitives/Input';
import { FormComposition, formGap } from './FormComposition';
import { useLanguage } from '../../i18n/LanguageProvider';

const pad = (value: number) => String(value).padStart(2, '0');

// The birth date must lie in the past (the server enforces the same), so the
// wheels stop at yesterday. They go back a century and open on a typical adult
// birth year instead of on yesterday.
function birthDateBounds(today = new Date()) {
  const yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1);
  const max = `${yesterday.getFullYear()}-${pad(yesterday.getMonth() + 1)}-${pad(yesterday.getDate())}`;
  return { min: `${today.getFullYear() - 100}-01-01`, max, openAt: `${today.getFullYear() - 30}-01-01` };
}

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
  const birthBounds = birthDateBounds();
  const valid =
    isPastIsoDateInput(dateOfBirth) &&
    Number(restingHeartRate) > 0;

  return (
    <FormComposition
      description={t('onboarding.profile.description')}
      title={t('onboarding.profile.title')}
    >
      <View style={{ gap: formGap }}>
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
        <DatePicker
          label={t('onboarding.profile.dateOfBirth')}
          min={birthBounds.min}
          max={birthBounds.max}
          openAt={birthBounds.openAt}
          onChange={setDateOfBirth}
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
