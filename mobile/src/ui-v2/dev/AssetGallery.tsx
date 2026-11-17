import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ActionLandscape } from '../assets/ActionLandscape';
import { assetColors } from '../assets/assetColors';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { Icon, iconNames, type IconName, type IconSize } from '../primitives/Icon';

const sections = ['Icons', 'Sports', 'Headers', 'Action'] as const;
type Section = (typeof sections)[number];
const sizes: IconSize[] = [20, 24, 32];
const circles = [40, 48, 64] as const;
const sports: IconName[] = ['run', 'bike', 'swim'];

export function AssetGallery() {
  const [section, setSection] = useState<Section>('Icons');
  const [iconPage, setIconPage] = useState(0);
  const [showCircles, setShowCircles] = useState(false);
  const [headerPreview, setHeaderPreview] = useState<'Standard' | 'Compact' | 'Trees/river'>('Standard');
  const { width, fontScale } = useWindowDimensions();
  if (!__DEV__) return null;
  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.toolbar}>
        <Text accessibilityRole="header" style={styles.title}>Wombo asset proof</Text>
        <Text style={styles.meta}>DEV ONLY · {Math.round(width)} dp · font {fontScale.toFixed(2)}</Text>
        <View style={styles.tabs}>
          {sections.map((item) => <Pressable key={item} accessibilityRole="button" accessibilityState={{ selected: item === section }} onPress={() => setSection(item)} style={[styles.tab, item === section && styles.selected]}><Text style={[styles.tabText, item === section && styles.inverse]}>{item}</Text></Pressable>)}
        </View>
      </View>
      <ScrollView key={section} contentContainerStyle={styles.content}>
        {section === 'Icons' ? <>
          <Text style={styles.heading} accessibilityRole="header">Semantic icons · 20 / 24 / 32 dp</Text>
          <View style={styles.tabs}>{[0, 1, 2].map((page) => <Pressable key={page} accessibilityRole="button" accessibilityLabel={`Icon page ${page + 1}`} accessibilityState={{ selected: iconPage === page }} onPress={() => setIconPage(page)} style={[styles.tab, iconPage === page && styles.selected]}><Text style={[styles.tabText, iconPage === page && styles.inverse]}>{page + 1} / 3</Text></Pressable>)}</View>
          <View style={styles.iconPage}>{iconNames.filter((name) => !sports.includes(name)).slice(iconPage * 8, iconPage * 8 + 8).map((name) => <View key={name} style={styles.iconRow}><Text style={styles.name}>{name}</Text>{sizes.map((size) => <View key={size} style={styles.sample}><Icon name={name} size={size} /></View>)}</View>)}</View>
        </> : null}
        {section === 'Sports' ? <>
          <Text style={styles.heading} accessibilityRole="header">{showCircles ? 'UI icon circles' : 'Original sport vectors'}</Text>
          <Text style={styles.meta}>24-unit grid · 2-unit rounded stroke</Text>
          <Pressable accessibilityRole="button" onPress={() => setShowCircles(!showCircles)} style={styles.tab}><Text style={styles.tabText}>{showCircles ? 'Show sport vectors' : 'Show UI circles'}</Text></Pressable>
          {(showCircles ? ['profile', 'calendar', 'clock'] as const : sports).map((name) => <View key={name} style={styles.sportGroup}><Text style={styles.heading}>{name.toUpperCase()}</Text><View style={styles.discs}>{circles.map((circle, index) => <View key={circle} style={styles.discSample}><View style={[styles.disc, { width: circle, height: circle, borderRadius: circle / 2 }]}><Icon name={name} size={sizes[index]} /></View><Text style={styles.meta}>{sizes[index]} / {circle} dp</Text></View>)}</View></View>)}
        </> : null}
        {section === 'Headers' ? <>
          <View style={styles.tabs}>{(['Standard', 'Compact', 'Trees/river'] as const).map((preview) => <Pressable key={preview} accessibilityRole="button" accessibilityState={{ selected: headerPreview === preview }} onPress={() => setHeaderPreview(preview)} style={[styles.tab, headerPreview === preview && styles.selected]}><Text style={[styles.tabText, headerPreview === preview && styles.inverse]}>{preview}</Text></Pressable>)}</View>
          <Text style={styles.heading}>HeaderLandscape · {headerPreview}</Text>
          <View style={styles.bleed}><HeaderLandscape compact={headerPreview === 'Compact'} variant={headerPreview === 'Trees/river' ? 'treesRiver' : 'ridges'} /></View>
          <Text style={styles.meta}>Final 56 dp fade · static · text-overlap veil available</Text>
        </> : null}
        {section === 'Action' ? <>
          <Text style={styles.heading}>ActionLandscape</Text>
          <Text style={styles.meta}>Decorative proof · no athlete action</Text>
          <View style={styles.banner}>
            <ActionLandscape />
            <View style={styles.bannerLabel}><Icon name="add" color={assetColors.ivory} /><Text style={styles.bannerText}>Action inset proof</Text></View>
          </View>
          <Text style={styles.meta}>Rightmost 35% · 10% sage · shared ridge / trees</Text>
          <Text style={styles.heading}>Accessibility contract</Text>
          <Text style={styles.body}>Artwork and duplicate icons are hidden. Icon-only controls receive their label from the enclosing control. Gallery samples do not invoke training operations.</Text>
        </> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: assetColors.canvas },
  toolbar: { padding: 16, gap: 8 },
  title: { fontSize: 24, lineHeight: 30, fontWeight: '700', color: assetColors.text },
  meta: { fontSize: 14, lineHeight: 20, color: assetColors.muted },
  heading: { fontSize: 18, lineHeight: 24, fontWeight: '600', color: assetColors.text },
  body: { fontSize: 16, lineHeight: 24, color: assetColors.text },
  tabs: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tab: { minWidth: 64, minHeight: 48, paddingHorizontal: 12, paddingVertical: 12, borderRadius: 12, justifyContent: 'center', alignItems: 'center', backgroundColor: assetColors.soft },
  selected: { backgroundColor: assetColors.forest },
  tabText: { fontSize: 16, lineHeight: 24, color: assetColors.forest },
  inverse: { color: assetColors.ivory },
  content: { padding: 16, paddingBottom: 32, gap: 16 },
  iconRow: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8 },
  iconPage: { gap: 8 },
  name: { width: 128, flexGrow: 1, fontSize: 14, lineHeight: 20, color: assetColors.text },
  sample: { width: 40, minHeight: 40, alignItems: 'center', justifyContent: 'center' },
  sportGroup: { gap: 8 },
  discs: { flexDirection: 'row', flexWrap: 'wrap', gap: 24 },
  discSample: { minWidth: 72, gap: 8, alignItems: 'center' },
  disc: { backgroundColor: assetColors.soft, alignItems: 'center', justifyContent: 'center' },
  bleed: { marginHorizontal: -16 },
  banner: { backgroundColor: assetColors.forest, borderRadius: 16, overflow: 'hidden', minHeight: 96, padding: 16, justifyContent: 'center' },
  bannerLabel: { width: '65%', flexDirection: 'row', alignItems: 'center', gap: 12 },
  bannerText: { flex: 1, fontSize: 18, lineHeight: 24, fontWeight: '600', color: assetColors.ivory },
});
