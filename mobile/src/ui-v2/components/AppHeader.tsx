import { useState, type RefObject } from 'react';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
import { HeaderLandscape, type HeaderLandscapeProps } from '../assets/HeaderLandscape';
import { Icon } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';

export function HeaderAction({ label, onPress, disabled = false, profile = false, icon = 'back' }: {
  label: string; onPress: () => void; disabled?: boolean; profile?: boolean; icon?: 'back' | 'close';
}) {
  const [focused, setFocused] = useState(false);
  const { width, fontScale } = useWindowDimensions();
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }}
    disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={[styles.action, profile && styles.profile, (width < 360 || fontScale >= 1.5) && styles.fullAction]}>
    <Icon name={profile ? 'profile' : icon} color={colors.text} />
    <Text variant="label" accessible={false} style={styles.actionLabel}>{label}</Text>
    {profile ? <Icon name="chevron" size={20} color={colors.textMuted} /> : null}
    {focused ? <View pointerEvents="none" style={styles.focus} /> : null}
  </Pressable>;
}
export function ProfileAction(props: Omit<Parameters<typeof HeaderAction>[0], 'profile'>) {
  return <HeaderAction {...props} profile />;
}
export function AppHeader({ title, onBack, backLabel, backDisabled, onProfile, profileLabel, profileDisabled,
  landscape, task = false, titleVariant, backIcon, titleRef, onTitleLayout, titleTestID }: {
  title: string; onBack?: () => void; backLabel?: string; backDisabled?: boolean;
  onProfile?: () => void; profileLabel?: string; profileDisabled?: boolean;
  landscape?: HeaderLandscapeProps['variant']; task?: boolean; titleVariant?: 'display' | 'screenTitle' | 'sectionTitle'; backIcon?: 'back' | 'close';
  titleRef?: RefObject<View | null>; onTitleLayout?: () => void; titleTestID?: string;
}) {
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 360 || fontScale >= 1.5;
  return <View testID="app-header" style={styles.header}>
    {(onBack || onProfile) ? <View style={[styles.utility, stacked && styles.stacked]}>
      {onBack ? <HeaderAction label={backLabel ?? title} onPress={onBack} disabled={backDisabled} icon={backIcon} /> : <View style={styles.spacer} />}
      {onProfile ? <ProfileAction label={profileLabel ?? title} onPress={onProfile} disabled={profileDisabled} /> : null}
    </View> : null}
    <View style={styles.titleRegion}>
      {landscape ? <View pointerEvents="none" style={styles.art}><HeaderLandscape variant={landscape} /></View> : null}
      <View testID={titleTestID} ref={titleRef} accessible accessibilityRole="header" accessibilityLabel={title}
        onLayout={onTitleLayout} style={styles.title}>
        <Text variant={titleVariant ?? (task ? 'sectionTitle' : 'screenTitle')} accessible={false}>{title}</Text>
      </View>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  header: { gap: space[8], width: '100%' },
  utility: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: space[8] },
  stacked: { flexDirection: 'column', alignItems: 'stretch' }, spacer: { flex: 1 },
  action: { minHeight: layout.headerUtility.minHeight, minWidth: layout.touch, paddingVertical: space[12],
    paddingHorizontal: layout.headerUtility.horizontalPadding, flexDirection: 'row', alignItems: 'center',
    gap: layout.headerUtility.gap, borderRadius: radius.pill, flexShrink: 1 },
  profile: { backgroundColor: colors.primarySoft }, fullAction: { alignSelf: 'stretch' },
  actionLabel: { flexShrink: 1 },
  titleRegion: { gap: space[8] },
  art: { marginHorizontal: -layout.phoneGutter },
  title: { width: '100%', flexGrow: 0, flexShrink: 0 },
  focus: { ...StyleSheet.absoluteFill, borderWidth: layout.focusOutline, borderColor: colors.focus, borderRadius: radius.pill },
});
