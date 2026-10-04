import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../i18n/LanguageProvider';
import { Button } from '../ui-v2/primitives/Button';
import { Text } from '../ui-v2/primitives/Text';
import { space } from '../ui-v2/tokens';
import { useUiVersion } from './UiVersionProvider';

export function UiVersionControl({ disabled = false, onSelect }: { disabled?: boolean; onSelect?: (version: 'v1' | 'v2') => void }) {
  const { requested, setRequested } = useUiVersion();
  const { t } = useLanguage();
  if (!__DEV__) return null;
  return <View style={styles.control}>
    <Text variant="supporting">{t('uiVersion.development', { version: requested.toUpperCase() })}</Text>
    <View style={styles.options}>
      {(['v1', 'v2'] as const).map((version) => <Button key={version}
        label={t('uiVersion.choose', { version: version.toUpperCase() })}
        variant={requested === version ? 'primary' : 'secondary'} accessibilityState={{ selected: requested === version }}
        disabled={disabled} onPress={() => { setRequested(version); onSelect?.(version); }} />)}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  control: { paddingHorizontal: space[16], paddingVertical: space[8], gap: space[4] },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8] },
});
