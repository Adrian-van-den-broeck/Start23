import { useId, useState } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import Svg, { Circle, Defs, G, LinearGradient, Path, RadialGradient, Rect, Stop } from 'react-native-svg';

import { assetColors } from './assetColors';
import { DecorativeSvgFallback, foreground, ridges, TreesRiver } from './LandscapeArtwork';

export type HeaderLandscapeProps = {
  compact?: boolean;
  variant?: 'ridges' | 'treesRiver';
  // Shells that place text over the art must enable this canvas veil.
  behindText?: boolean;
  // Calendar leaves a clear decorative band above its copy; other shells veil from the top.
  textStart?: number;
};

export function HeaderLandscape({ compact = false, variant = 'ridges', behindText = false, textStart = 0 }: HeaderLandscapeProps) {
  const { width: windowWidth, fontScale } = useWindowDimensions();
  const [measuredWidth, setMeasuredWidth] = useState<number>();
  const width = measuredWidth ?? windowWidth;
  const height = compact || width < 360 || fontScale >= 1.5 ? 96 : 140;
  const id = `landscape${useId().replace(/[^a-zA-Z0-9]/g, '')}`;
  // Wider layouts scale uniformly; narrower ones crop the composition centrally.
  const scale = Math.max(1, width / 393);
  const artHeight = height / scale;
  return (
    <View
      testID="header-landscape"
      pointerEvents="none"
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      onLayout={(event) => {
        const nextWidth = event.nativeEvent.layout.width;
        if (nextWidth > 0) setMeasuredWidth(nextWidth);
      }}
      style={[styles.host, { height }]}
    >
      <DecorativeSvgFallback>
        <Svg width="100%" height={height} viewBox={`${(393 - width / scale) / 2} 0 ${width / scale} ${artHeight}`} preserveAspectRatio="xMidYMid slice" accessible={false}>
          <Defs>
            {behindText && textStart > 0 ? <LinearGradient id={`${id}veil`} gradientUnits="userSpaceOnUse"
              x1="0" y1={(textStart - 16) / scale} x2="0" y2={textStart / scale}>
              <Stop offset="0" stopColor={assetColors.canvas} stopOpacity="0" />
              <Stop offset="1" stopColor={assetColors.canvas} stopOpacity="0.84" />
            </LinearGradient> : null}
            <RadialGradient id={`${id}sun`}>
              <Stop offset="0" stopColor={assetColors.sun} stopOpacity="1" />
              <Stop offset="0.65" stopColor={assetColors.sun} stopOpacity="0.8" />
              <Stop offset="1" stopColor={assetColors.sun} stopOpacity="0.2" />
            </RadialGradient>
            {[assetColors.sage, assetColors.forest].map((color, index) => (
              <LinearGradient key={color} id={`${id}ridge${index}`} gradientUnits="userSpaceOnUse" x1="0" y1="50" x2="0" y2="180">
                <Stop offset="0" stopColor={color} stopOpacity="1" />
                <Stop offset="0.65" stopColor={color} stopOpacity="0.65" />
                <Stop offset="1" stopColor={color} stopOpacity="0.1" />
              </LinearGradient>
            ))}
            <LinearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <Stop offset="0" stopColor={assetColors.canvas} stopOpacity="0" />
              <Stop offset="1" stopColor={assetColors.canvas} stopOpacity="1" />
            </LinearGradient>
          </Defs>
          <Circle cx={277} cy={49} r={14} fill={`url(#${id}sun)`} opacity={0.4} />
          <G transform={`translate(0 ${height === 96 || (behindText && textStart > 0) ? -28 : 0})`}>
            <Path d={ridges[0]} fill={`url(#${id}ridge0)`} opacity={0.10} />
            <Path d={ridges[1]} fill={`url(#${id}ridge0)`} opacity={0.16} />
            <Path d={ridges[2]} fill={`url(#${id}ridge1)`} opacity={0.22} />
            <Path d={foreground} fill={`url(#${id}ridge1)`} opacity={0.28} />
            {variant === 'treesRiver' ? <G opacity={0.28}><TreesRiver color={assetColors.forest} riverColor={assetColors.canvas} /></G> : null}
          </G>
          {/* The full canvas veil protects all copy; Calendar fades into it before its title. */}
          {behindText ? <Rect x={-40} y={0} width={473} height={180}
            fill={textStart > 0 ? `url(#${id}veil)` : assetColors.canvas} opacity={textStart > 0 ? 1 : 0.84} /> : null}
          <Rect x={-40} y={(height - 56) / scale} width={473} height={56 / scale} fill={`url(#${id})`} />
        </Svg>
      </DecorativeSvgFallback>
    </View>
  );
}

const styles = StyleSheet.create({ host: { width: '100%', overflow: 'hidden', backgroundColor: assetColors.canvas } });
