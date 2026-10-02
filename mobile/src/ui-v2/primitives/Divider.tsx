import { View } from 'react-native';
import { colors } from '../tokens';

export function Divider() {
  return <View accessible={false} importantForAccessibility="no" style={{ height: 1, backgroundColor: colors.border }} />;
}
