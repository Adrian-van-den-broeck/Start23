import { View } from 'react-native';
import { LanguageSelector } from '../../components/LanguageSelector';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Divider } from '../primitives/Divider';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';
import { QuickActionRow } from './QuickActionRow';

// Presentation of the existing modal destinations; dismissal remains with its owner.
export function SupportingProfileMenu({ onOpenProfile, onOpenIntegrations, onSignOut }: {
  onOpenProfile: () => void; onOpenIntegrations: () => void; onSignOut: () => void;
}) {
  const { t } = useLanguage();
  return <View style={{ gap: space[24] }}>
    <View style={{ gap: space[8] }}>
      <Text variant="supporting" tone="primary">{t('planning.profilePersonal')}</Text>
      <Text variant="sectionTitle" accessibilityRole="header">{t('planning.profileSetup')}</Text>
      <View style={{ alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] }}>
        <Text variant="supporting" tone="primary">{t('common.active')}</Text>
      </View>
    </View>
    <View style={{ gap: space[8] }}>
      <QuickActionRow label="Intakeprofiel" icon="profile" onAction={onOpenProfile} />
      <Text variant="supporting" tone="textMuted">{t('planning.profileData')}</Text>
      <Divider />
      <QuickActionRow label="Integraties" icon="activities" onAction={onOpenIntegrations} />
      <Text variant="supporting" tone="textMuted">{t('planning.profileIntegrations')}</Text>
    </View>
    <Divider />
    <LanguageSelector />
    <Button label={t('planning.safeSignOut')} variant="outline" trailingIcon="logout" onPress={onSignOut} />
  </View>;
}
