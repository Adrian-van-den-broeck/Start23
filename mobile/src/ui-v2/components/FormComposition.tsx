import { studioPresentation } from '../../ui-v3/presentation';
import { Masthead } from '../../ui-v3/Masthead';
import type { ReactNode } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { HeaderAction } from './AppHeader';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import { useLanguage } from '../../i18n/LanguageProvider';

export function BrandedFormHeader({ caption, onBack, onSignOut, children, backLabel: backLabelProp }: {
  caption: string; backLabel?: string; onBack?: () => void; onSignOut: () => Promise<void>; children?: ReactNode;
}) {
  const { t } = useLanguage();
  const backLabel = backLabelProp ?? t('shell.week');
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 393 || fontScale > 1 || backLabel.length > 8;
  if (studioPresentation) return <Masthead title={caption}
    leading={onBack ? <HeaderAction label={backLabel} onPress={onBack} /> : undefined}
    trailing={<View style={styles.actions}>{children}<Button label={t('onboarding.header.signOutShort')} accessibilityLabel={t('activity.signOut')} onPress={onSignOut} variant="tertiary" trailingIcon="logout" /></View>} />;
  const brand = <View style={styles.brand}><Text variant="screenTitle" tone="primary">WOMBO</Text><Text tone="textMuted">{caption}</Text></View>;
  return <View style={{ gap: space[8] }}>
    {stacked ? brand : null}
    <View style={styles.utility}>
      {stacked ? (onBack ? <HeaderAction label={backLabel} onPress={onBack} /> : null) : <View style={styles.column}>{onBack ? <HeaderAction label={backLabel} onPress={onBack} /> : null}</View>}
      {!stacked ? <View style={styles.column}>{brand}</View> : null}
      <View style={[styles.actions, !stacked && styles.column, styles.trailing]}>{children}<Button label={t('onboarding.header.signOutShort')} accessibilityLabel={t('activity.signOut')} onPress={onSignOut} variant="secondary" trailingIcon="logout" /></View>
    </View>
    <View pointerEvents="none" style={styles.art}><HeaderLandscape /></View>
  </View>;
}

// Vertical rhythm between the fields of one form. V3 forms sit directly on the
// page instead of inside a card, so they read tighter.
export const formGap = studioPresentation ? space[16] : layout.fieldGroupGap;

export function FormComposition({ title, description, children, progress }: {
  title: string; description: string; children: ReactNode; progress?: ReactNode;
}) {
  return <View style={{ gap: formGap }}>
    {progress}
    <View style={{ gap: space[8] }}>
      <Text variant={studioPresentation ? 'sectionTitle' : 'display'} accessibilityRole="header">{title}</Text>
      <Text variant={studioPresentation ? 'supporting' : 'body'} tone="textMuted">{description}</Text>
    </View>
    {studioPresentation
      ? <View style={{ gap: formGap }}>{children}</View>
      : <Card padding="form" elevated style={{ gap: formGap }}>{children}</Card>}
  </View>;
}

// A group of related fields inside a form, set apart by a hairline instead of
// a nested card.
export function FormSection({ title, children }: { title?: string; children: ReactNode }) {
  return <View style={styles.section}>
    {title ? <Text variant="caption" tone="primary" accessibilityRole="header" style={styles.sectionTitle}>{title}</Text> : null}
    {children}
  </View>;
}
const styles = StyleSheet.create({
  utility: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: space[8] },
  column: { flex: 1, minWidth: 0 },
  trailing: { justifyContent: 'flex-end' },
  brand: { alignItems: 'center', flexShrink: 1 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: space[8], flexShrink: 1 },
  art: { marginHorizontal: -layout.phoneGutter, marginBottom: -space[48] },
  section: { gap: formGap, paddingTop: space[16], borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  sectionTitle: { textTransform: 'uppercase', letterSpacing: 1 },
});
