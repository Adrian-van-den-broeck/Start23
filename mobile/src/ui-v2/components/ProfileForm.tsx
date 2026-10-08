import { useState } from 'react';
import { View } from 'react-native';
import type { AthleteProfile } from '../../api/types';
import { formatIsoDateInput, isPastIsoDateInput } from '../../lib/dateInput';
import { Button } from '../primitives/Button';
import { Input } from '../primitives/Input';
import { layout } from '../tokens';
import { FormComposition } from './FormComposition';

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
      description="Deze gegevens ondersteunen alleen goedgekeurde, deterministische berekeningen. Er worden geen medische grenzen afgedwongen."
      title="Jouw basis"
    >
      <View style={{ gap: layout.fieldGroupGap }}>
        <Input
          label="Voornaam"
          optionalLabel="(optioneel)"
          icon="profile"
          accessibilityLabel="Voornaam (optioneel)"
          onChangeText={setFirstName}
          placeholder="Voornaam"
          value={firstName}
        />
        <Input
          label="Achternaam"
          optionalLabel="(optioneel)"
          icon="profile"
          accessibilityLabel="Achternaam (optioneel)"
          onChangeText={setLastName}
          placeholder="Achternaam"
          value={lastName}
        />
        <Input
          hint="Gebruik JJJJ-MM-DD. De streepjes verschijnen automatisch."
          inputMode="numeric"
          label="Geboortedatum"
          icon="calendar"
          maxLength={10}
          onChangeText={(value) => setDateOfBirth(formatIsoDateInput(value))}
          placeholder="1990-05-20"
          value={dateOfBirth}
        />
        <Input
          inputMode="numeric"
          label="Rusthartslag"
          icon="heartRate"
          onChangeText={setRestingHeartRate}
          placeholder="52"
          unit="bpm"
          accessibilityLabel="Rusthartslag"
          value={restingHeartRate}
        />
      </View>
      <Button
        disabled={!valid}
        label="Profiel opslaan"
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
