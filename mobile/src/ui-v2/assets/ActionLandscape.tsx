import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, LinearGradient, Path, Stop } from 'react-native-svg';

import { assetColors } from './assetColors';
import { DecorativeSvgFallback, foreground, trees } from './LandscapeArtwork';

// Mount inside a clipped forest banner; the left 65% stays completely plain.
export function ActionLandscape() {
  const id = `action${useId().replace(/[^a-zA-Z0-9]/g, '')}`;
  return (
    <View testID="action-landscape" pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.inset}>
      <DecorativeSvgFallback>
        <Svg width="100%" height="100%" viewBox="255 91 138 89" preserveAspectRatio="xMaxYMax meet" accessible={false}>
          <Defs><LinearGradient id={id} gradientUnits="userSpaceOnUse" x1={255} y1={0} x2={320} y2={0}>
            <Stop offset="0" stopColor={assetColors.sage} stopOpacity="0" />
            <Stop offset="1" stopColor={assetColors.sage} stopOpacity="1" />
          </LinearGradient></Defs>
          {/* One compound path bounds even overlapping silhouettes to 10%. */}
          <Path d={`${foreground} ${trees}`} fill={`url(#${id})`} opacity={0.10} />
        </Svg>
      </DecorativeSvgFallback>
    </View>
  );
}

const styles = StyleSheet.create({ inset: { position: 'absolute', right: 0, top: 0, bottom: 0, width: '35%', overflow: 'hidden' } });
