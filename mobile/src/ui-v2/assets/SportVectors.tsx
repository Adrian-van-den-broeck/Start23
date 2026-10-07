import Svg, { Circle, Path } from 'react-native-svg';

export type VectorProps = { size: 20 | 24 | 32; color: string };

// Original local artwork, drawn on a shared 24-unit grid. No catalog paths or
// third-party sport artwork are used. The SVGs have no independent semantics.
export function RunVector({ size, color }: VectorProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" accessible={false}>
      <Circle cx={15} cy={4} r={2} fill={color} stroke="none" />
      <Path d="m7 9 3-2 4 2 3 4 4-2 M14 9l-4 6 4 3-3 4 M10 15l-3 5-5 1" />
    </Svg>
  );
}

export function BikeVector({ size, color }: VectorProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" accessible={false}>
      <Circle cx={5} cy={18} r={3.7} />
      <Circle cx={19} cy={18} r={3.7} />
      <Circle cx={14.5} cy={3.5} r={1.8} fill={color} stroke="none" />
      <Path d="m7 7 4 .5 4 3 4 .5 M11 7.5 8.5 12 13 14l-2 5 M5 18l3.5-6 M19 18l-3-6" />
    </Svg>
  );
}

export function SwimVector({ size, color }: VectorProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" accessible={false}>
      <Circle cx={17.5} cy={8} r={2} fill={color} stroke="none" />
      <Path d="m2 10 4-3c1-.8 2-.6 2.8.3l5 5 M2 15c2.2 2 3.2 2 5.5 0s3.3-2 5.5 0 3.3 2 5.5 0c1.2-1 2-1.2 3.5-.4 M2 20c2.2 2 3.2 2 5.5 0s3.3-2 5.5 0 3.3 2 5.5 0c1.2-1 2-1.2 3.5-.4" />
    </Svg>
  );
}
