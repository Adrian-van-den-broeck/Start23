// Matte paper, deep pine and track orange. Every sport and state also has a text label.
export const palette = {
  background: '#F5F6F2', surface: '#FFFFFF', surfaceElevated: '#FFFFFF',
  surfaceSubtle: '#E7EAE5', primary: '#174D38', primaryPressed: '#103726',
  primarySoft: '#E1EBDF', secondary: '#E1EBDF', text: '#16221C', textMuted: '#506159',
  textInverse: '#FFFFFF', border: '#CFD8D1', borderControl: '#718278', focus: '#174D38',
  success: '#286143', successSoft: '#E0F0E4', warning: '#883810', warningSoft: '#FFEBDB',
  destructive: '#97332D', destructiveSoft: '#FBE7E4',
  sport: {
    run: { text: '#913B16', soft: '#FCE5D5' },
    bike: { text: '#225638', soft: '#DDEADB' },
    swim: { text: '#314F52', soft: '#DFEAEB' },
  },
  scrim: 'rgba(15,32,22,0.38)', landscape: { sage: '#809788', sun: '#EF763D' },
} as const;

export const identity = { ink: '#102E22', orange: '#FF8347' } as const;

export const typeScale = {
  display: { fontSize: 32, lineHeight: 38, fontWeight: '700', letterSpacing: -1.1 },
  screenTitle: { fontSize: 28, lineHeight: 34, fontWeight: '700', letterSpacing: -0.8 },
  sectionTitle: { fontSize: 21, lineHeight: 28, fontWeight: '700', letterSpacing: -0.45 },
  cardTitle: { fontSize: 20, lineHeight: 26, fontWeight: '700', letterSpacing: -0.4 },
  body: { fontSize: 16, lineHeight: 24, fontWeight: '400' },
  supporting: { fontSize: 14, lineHeight: 21, fontWeight: '400' },
  caption: { fontSize: 12, lineHeight: 17, fontWeight: '600' },
  label: { fontSize: 15, lineHeight: 21, fontWeight: '600' },
  button: { fontSize: 16, lineHeight: 22, fontWeight: '700' },
  navigationLabel: { fontSize: 13, lineHeight: 18, fontWeight: '600' },
  numeric: { fontSize: 28, lineHeight: 34, fontWeight: '600', fontVariant: ['tabular-nums'] },
  numericCompact: { fontSize: 20, lineHeight: 26, fontWeight: '600', fontVariant: ['tabular-nums'] },
} as const;
