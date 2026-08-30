import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { MotionPressable as Pressable } from '../components/MotionPressable';

import { StatusPill } from '../components/StatusPill';
import { colors, radius, spacing } from '../theme/tokens';

const weekDays = [
  { day: 'Ma', date: '20', selected: false },
  { day: 'Di', date: '21', selected: false },
  { day: 'Wo', date: '22', selected: true },
  { day: 'Do', date: '23', selected: false },
  { day: 'Vr', date: '24', selected: false },
] as const;

export function HomeScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>Start23</Text>
            <Text style={styles.title}>Jouw training, jouw keuze.</Text>
          </View>
          <View accessibilityLabel="Start23 profiel" style={styles.avatar}>
            <Text style={styles.avatarText}>23</Text>
          </View>
        </View>

        <View style={styles.previewNotice}>
          <StatusPill label="Ontwerpvoorbeeld" tone="neutral" />
          <Text style={styles.previewText}>
            Deze data is visueel voorbeeldmateriaal en bevat geen actief
            trainingsadvies.
          </Text>
        </View>

        <View style={styles.weekRow}>
          {weekDays.map((item) => (
            <View
              key={item.day}
              style={[styles.day, item.selected && styles.daySelected]}
            >
              <Text
                style={[
                  styles.dayLabel,
                  item.selected && styles.dayTextSelected,
                ]}
              >
                {item.day}
              </Text>
              <Text
                style={[
                  styles.dayDate,
                  item.selected && styles.dayTextSelected,
                ]}
              >
                {item.date}
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.heroCard}>
          <View style={styles.heroTopRow}>
            <StatusPill label="Vandaag" tone="accent" />
            <Text style={styles.heroMeta}>45 min</Text>
          </View>
          <Text style={styles.heroTitle}>Rustige duurloop</Text>
          <Text style={styles.heroDescription}>
            Zone 2 · ontspannen tempo · vlak parcours
          </Text>
          <View style={styles.heroFooter}>
            <View>
              <Text style={styles.heroCaption}>Geplande start</Text>
              <Text style={styles.heroValue}>18:30</Text>
            </View>
            <Pressable
              accessibilityRole="button"
              disabled
              style={styles.secondaryButton}
            >
              <Text style={styles.secondaryButtonText}>Bekijk training</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionEyebrow}>Komende week</Text>
            <Text style={styles.sectionTitle}>Voorstel wacht op jou</Text>
          </View>
          <StatusPill label="In afwachting" tone="brand" />
        </View>

        <View style={styles.proposalCard}>
          <View style={styles.proposalMarker} />
          <View style={styles.proposalBody}>
            <Text style={styles.proposalTitle}>Nieuw weekritme beschikbaar</Text>
            <Text style={styles.proposalText}>
              Bekijk straks de trainingen, waarschuwingen en vrije dagen.
              Wijzigingen worden pas toegepast nadat jij ze goedkeurt.
            </Text>
            <Pressable
              accessibilityRole="button"
              disabled
              style={styles.primaryButton}
            >
              <Text style={styles.primaryButtonText}>
                Beschikbaar na API-koppeling
              </Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Week in balans</Text>
          <View style={styles.summaryRow}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>3u 45m</Text>
              <Text style={styles.summaryLabel}>Voorbeeldduur</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>4</Text>
              <Text style={styles.summaryLabel}>Trainingen</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>2</Text>
              <Text style={styles.summaryLabel}>Rustdagen</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      <View style={styles.tabBar}>
        {['Vandaag', 'Week', 'Coach'].map((label, index) => (
          <View key={label} style={styles.tabItem}>
            <View style={[styles.tabDot, index === 0 && styles.tabDotActive]} />
            <Text style={[styles.tabLabel, index === 0 && styles.tabLabelActive]}>
              {label}
            </Text>
          </View>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 120,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: spacing.lg,
    paddingTop: spacing.md,
  },
  eyebrow: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: '800',
    letterSpacing: -0.8,
    marginTop: spacing.xs,
  },
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  avatarText: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '800',
  },
  previewNotice: {
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    marginBottom: spacing.lg,
    padding: spacing.md,
  },
  previewText: {
    color: colors.inkMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  weekRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  day: {
    alignItems: 'center',
    borderRadius: radius.md,
    gap: 3,
    paddingHorizontal: 13,
    paddingVertical: spacing.sm,
  },
  daySelected: {
    backgroundColor: colors.brand,
  },
  dayLabel: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '600',
  },
  dayDate: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
  },
  dayTextSelected: {
    color: colors.white,
  },
  heroCard: {
    backgroundColor: colors.brand,
    borderRadius: radius.lg,
    marginBottom: spacing.xl,
    padding: spacing.lg,
  },
  heroTopRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  heroMeta: {
    color: colors.brandSoft,
    fontSize: 13,
    fontWeight: '700',
  },
  heroTitle: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '800',
    letterSpacing: -0.8,
    marginTop: spacing.lg,
  },
  heroDescription: {
    color: colors.brandSoft,
    fontSize: 14,
    lineHeight: 21,
    marginTop: spacing.xs,
  },
  heroFooter: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.xl,
  },
  heroCaption: {
    color: colors.brandSoft,
    fontSize: 11,
  },
  heroValue: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '800',
    marginTop: 2,
  },
  secondaryButton: {
    backgroundColor: colors.white,
    borderRadius: radius.pill,
    opacity: 0.8,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  secondaryButtonText: {
    color: colors.brand,
    fontSize: 12,
    fontWeight: '800',
  },
  sectionHeader: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  sectionEyebrow: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: '800',
    marginTop: 3,
  },
  proposalCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    flexDirection: 'row',
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  proposalMarker: {
    backgroundColor: colors.accent,
    width: 6,
  },
  proposalBody: {
    flex: 1,
    padding: spacing.lg,
  },
  proposalTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '800',
  },
  proposalText: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: spacing.sm,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    marginTop: spacing.md,
    opacity: 0.45,
    paddingVertical: 13,
  },
  primaryButtonText: {
    color: colors.white,
    fontSize: 13,
    fontWeight: '800',
  },
  summaryCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: spacing.lg,
  },
  summaryTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
    marginBottom: spacing.md,
  },
  summaryRow: {
    alignItems: 'center',
    flexDirection: 'row',
  },
  summaryItem: {
    flex: 1,
  },
  summaryValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: '800',
  },
  summaryLabel: {
    color: colors.inkMuted,
    fontSize: 11,
    marginTop: 3,
  },
  summaryDivider: {
    backgroundColor: colors.line,
    height: 34,
    marginHorizontal: spacing.sm,
    width: 1,
  },
  tabBar: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderTopWidth: 1,
    bottom: 0,
    flexDirection: 'row',
    left: 0,
    paddingBottom: spacing.md,
    paddingTop: spacing.sm,
    position: 'absolute',
    right: 0,
  },
  tabItem: {
    alignItems: 'center',
    flex: 1,
    gap: spacing.xs,
  },
  tabDot: {
    backgroundColor: colors.line,
    borderRadius: radius.pill,
    height: 5,
    width: 18,
  },
  tabDotActive: {
    backgroundColor: colors.accent,
    width: 28,
  },
  tabLabel: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '700',
  },
  tabLabelActive: {
    color: colors.ink,
  },
});
