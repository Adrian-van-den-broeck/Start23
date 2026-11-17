import { Component, type ReactNode } from 'react';
import { G, Path } from 'react-native-svg';

// Shared original silhouettes, not raster tracing. Action and header artwork
// reuse the same foreground and tree group to keep a single asset family.
export const ridges = [
  'M-40 112C-12 95 18 79 42 73Q55 67 67 70L111 89Q127 94 143 86L176 72 196 62Q205 57 213 59L236 69 265 78Q280 84 296 76L329 65Q340 62 351 66L378 57Q389 54 403 61L433 76V180H-40Z',
  'M-40 141C4 130 45 115 77 119Q93 121 113 116L147 106 173 91Q186 84 200 89L218 94 239 106Q250 112 265 105L293 87Q306 80 317 84L332 79Q344 74 357 82L387 94 433 108V180H-40Z',
  'M-40 159C24 151 67 139 99 141Q119 143 140 133L165 121Q175 115 187 119L211 127Q222 130 236 121L268 107Q280 101 292 106L307 111 326 99Q336 94 348 101L373 112 401 117 433 131V180H-40Z',
] as const;
export const foreground = 'M-40 180C34 176 96 164 151 164Q180 163 210 155L241 143Q262 134 282 138L302 142Q318 137 333 127L357 119Q370 115 385 122L407 129 433 135V180H-40Z';

// Fixed original conifer silhouettes: three short branch tiers, varied height,
// one compound path shared by both assets. No procedural or semantic scenery.
function conifer(x: number, base: number, height: number) {
  const top = base - height;
  const half = height * 0.22;
  return `M${x} ${top}l${half * 0.42} ${height * 0.27}h${-half * 0.22}l${half * 0.5} ${height * 0.23}h${-half * 0.3}l${half * 0.62} ${height * 0.27}h${-half * 0.76}v${height * 0.23}h${-half * 0.48}v${-height * 0.23}h${-half * 0.76}l${half * 0.62} ${-height * 0.27}h${-half * 0.3}l${half * 0.5} ${-height * 0.23}h${-half * 0.22}Z`;
}
export const trees = [
  [296, 145, 17], [305, 141, 24], [315, 145, 19],
  [326, 141, 32], [337, 142, 24], [348, 140, 39],
  [360, 137, 28], [373, 138, 36], [385, 143, 29],
  [398, 140, 40], [411, 146, 31],
].map(([x, base, height]) => conifer(x, base, height)).join(' ');

export function TreesRiver({ color, riverColor }: { color: string; riverColor?: string }) {
  return (
    <G fill={color}>
      {riverColor ? <Path fill={riverColor} d="M341 91c7 4 9 7 2 11s-20 7-18 11 17 6 19 11-13 11-31 16l-24 40h22c4-21 38-33 42-44s-9-17-16-21 14-11 16-15-4-7-12-9Z" /> : null}
      <Path d={trees} />
    </G>
  );
}

// A render failure keeps the host's opaque background and bounded footprint.
// No exception text is surfaced to the athlete or logged by this decoration.
export class DecorativeSvgFallback extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? null : this.props.children; }
}
