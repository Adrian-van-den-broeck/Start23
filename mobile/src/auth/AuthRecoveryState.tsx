import { useLanguage } from '../i18n/LanguageProvider';
import { ScreenState } from '../components/ScreenState';
import { useAuth } from './AuthProvider';
import { View } from 'react-native';
import { Notice } from '../ui-v2/primitives/Notice';
import { Button } from '../ui-v2/primitives/Button';

export function AuthRecoveryState() {
  const { recovery, retry, loading } = useAuth();
  const { t } = useLanguage();
  return <ScreenState title={t('auth.recoveryTitle')} loading={loading}
    message={t(recovery === 'storage_read' || recovery === 'storage_write' ? 'auth.storageRecovery' : 'auth.networkRecovery')}
    retryLabel={t('common.retry')} onRetry={() => void retry()} />;
}

export function AuthRecoveryNotice() {
  const { recovery, retry, loading } = useAuth();
  const { t } = useLanguage();
  if (!recovery) return null;
  return <View accessibilityLiveRegion="polite">
    <Notice>{t(recovery === 'storage_read' || recovery === 'storage_write' ? 'auth.storageRecovery' : 'auth.networkRecovery')}</Notice>
    <Button label={t('common.retry')} disabled={loading} onPress={() => void retry()} />
  </View>;
}
