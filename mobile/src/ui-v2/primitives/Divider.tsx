import { View } from 'react-native';
import { colors, layout } from '../tokens';

export function Divider() {
  return <View accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
    style={{ height: layout.decorativeLine, backgroundColor: colors.border }} />;
}
