import { ActivityIndicator, Text, View } from 'react-native';

import { colors } from '../theme/tokens';

type ScreenStateProps = {
  loading?: boolean;
  message?: string;
  title: string;
};

export function ScreenState({ loading = false, message, title }: ScreenStateProps) {
  return (
    <View className="flex-1 items-center justify-center gap-4 bg-canvas px-6">
      {loading ? <ActivityIndicator color={colors.brand} size="large" /> : null}
      <Text className="text-center text-xl font-black text-ink">{title}</Text>
      {message ? (
        <Text className="text-center text-sm leading-5 text-muted">{message}</Text>
      ) : null}
    </View>
  );
}
