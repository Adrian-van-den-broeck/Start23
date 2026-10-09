import type { ReactNode } from 'react';
import { View, type TextInputProps } from 'react-native';
import { Input } from '../primitives/Input';
import { space } from '../tokens';

// Retain existing field names, units, validation and callbacks in the real forms.
export function ZoneField({ label, required = false, suffix, ...props }: TextInputProps & {
  label: string; hint?: string; error?: string; required?: boolean; suffix?: ReactNode;
}) {
  return <View style={{ gap: space[4] }}>
    <Input {...props} label={required ? label + ' *' : label} accessibilityLabel={label}
      icon={label.toLowerCase().includes('hartslag') || label.includes('LTHR') ? 'heartRate' : 'document'} />
    {suffix}
  </View>;
}
