import { Text as NativeText, type TextProps, type TextStyle } from 'react-native';

import { colors, typography } from '../tokens';

type Props = TextProps & {
  variant?: keyof typeof typography;
  tone?: 'text' | 'textMuted' | 'textInverse' | 'primary' | 'warning';
};

export function Text({ variant = 'body', tone = 'text', style, ...props }: Props) {
  const token = typography[variant];
  // Native text scales both glyphs and line height; leave scaling unclamped.
  const typeStyle: TextStyle = {
    ...token,
    fontVariant: 'fontVariant' in token ? [...token.fontVariant] : undefined,
  };
  return <NativeText {...props} allowFontScaling style={[typeStyle, { color: colors[tone] }, style]} />;
}
