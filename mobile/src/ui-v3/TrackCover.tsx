import type { ReactNode } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { identity } from './tokens';

export function TrackCover({ children }: { children: ReactNode }) {
  return <View testID="track-cover" style={styles.frame}>
    <Image accessible={false} source={require('../../assets/wombo-track.jpg')} resizeMode="cover" style={styles.photo} />
    <View style={styles.copy}>{children}</View>
  </View>;
}
const styles = StyleSheet.create({
  photo: { ...StyleSheet.absoluteFill, width: '100%', height: '100%' },
  frame: { minHeight: 198, borderRadius: 18, overflow: 'hidden', backgroundColor: identity.ink, justifyContent: 'flex-end' },
  copy: { alignItems: 'flex-start', gap: 16, padding: 20, width: '73%' },
});
