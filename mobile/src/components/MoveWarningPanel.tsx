import { StyleSheet, Text, View } from 'react-native';

import type { PlanWarning } from '../api/types';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

const warningCopy: Record<string, { message: string; title: string }> = {
  all_disciplines_blocked_rest_only: {
    title: 'Rustweek voorgesteld',
    message:
      'Alle disciplines zijn momenteel geblokkeerd. Daarom bevat dit voorstel alleen rust.',
  },
  anti_stack_violation: {
    title: 'Meer herstel nodig',
    message:
      'Tussen deze intensieve trainingen is extra herstel nodig. Kies een andere datum.',
  },
  injured_disciplines_excluded: {
    title: 'Blessure verwerkt',
    message:
      'Trainingen voor de bevestigde geblesseerde disciplines zijn niet opgenomen.',
  },
  manual_review_required: {
    title: 'Extra controle nodig',
    message:
      'Er was geen veilig regulier weekdoel beschikbaar. Controleer dit herstelvoorstel extra zorgvuldig.',
  },
  outside_confirmed_availability: {
    title: 'Datum niet beschikbaar',
    message:
      'Een training valt buiten je bevestigde beschikbare dagen. Kies een beschikbare datum.',
  },
  realized_intensity_debt_applied: {
    title: 'Rustiger weekdoel',
    message:
      'Je recente trainingsgegevens verlagen de intensieve tijd voor deze week.',
  },
  restricted_disciplines_low_only: {
    title: 'Alleen rustige training',
    message:
      'Voor een beperkte discipline zijn alleen rustige trainingen opgenomen.',
  },
  target_outside_catalog_capacity: {
    title: 'Weekdoel nog niet compleet',
    message:
      'De beschikbare trainingen sluiten nog niet volledig aan op het weekdoel.',
  },
  workouts_consolidated_on_available_dates: {
    title: 'Trainingen gecombineerd',
    message:
      'Er staan meerdere trainingen op dezelfde beschikbare dag. Plan voldoende herstel tussen de sessies.',
  },
};

export function warningPresentation(warning: PlanWarning): {
  message: string;
  title: string;
} {
  return warningCopy[warning.code] ?? {
    title: 'Aandachtspunt',
    message: warning.message,
  };
}

function Button({
  label,
  onPress,
  secondary = false,
}: {
  label: string;
  onPress: () => void;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[styles.action, secondary && styles.actionSecondary]}
    >
      <Text style={[styles.actionText, secondary && styles.actionSecondaryText]}>
        {label}
      </Text>
    </Pressable>
  );
}

export function MoveWarningPanel({
  onCancel,
  onConfirm,
  warnings,
}: {
  onCancel: () => void;
  onConfirm: () => void;
  warnings: PlanWarning[];
}) {
  return (
    <View accessibilityRole="alert" style={styles.panel}>
      <Text style={styles.title}>Controleer deze verplaatsing</Text>
      {warnings.map((warning) => {
        const presentation = warningPresentation(warning);
        return (
          <View key={warning.id ?? `${warning.code}:${warning.planned_workout_id ?? ''}`} style={styles.warning}>
            <Text style={styles.warningTitle}>{presentation.title}</Text>
            <Text style={styles.warningText}>{presentation.message}</Text>
          </View>
        );
      })}
      <Text style={styles.body}>
        De server blijft leidend. Bevestig alleen als je deze kwalitatieve
        aandachtspunten hebt beoordeeld.
      </Text>
      <View style={styles.actions}>
        <View style={styles.actionCell}>
          <Button label="Toch verplaatsen" onPress={onConfirm} />
        </View>
        <View style={styles.actionCell}>
          <Button label="Annuleren" onPress={onCancel} secondary />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: { color: colors.ink, fontSize: 18, fontWeight: '900' },
  body: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  warning: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.xs,
    padding: spacing.md,
  },
  warningTitle: { color: colors.accent, fontSize: 12, fontWeight: '900' },
  warningText: { color: colors.ink, fontSize: 13, lineHeight: 18 },
  actions: { flexDirection: 'row', gap: spacing.sm },
  actionCell: { flex: 1 },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    justifyContent: 'center',
    minHeight: 48,
    padding: spacing.sm,
  },
  actionSecondary: { backgroundColor: colors.surface, borderColor: colors.brand, borderWidth: 1 },
  actionText: { color: colors.white, fontSize: 13, fontWeight: '900' },
  actionSecondaryText: { color: colors.brand },
});
