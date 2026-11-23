import { StyleSheet, Text, View } from 'react-native';

import type { PlanWarning } from '../api/types';
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
import { translate } from '../i18n/runtime';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

const warningCodes = [
  'all_disciplines_blocked_rest_only',
  'anti_stack_violation',
  'cross_training_choice_available',
  'distance_only_swim_excluded_from_time_ratio',
  'injury_replacement_capacity_limited',
  'injured_disciplines_excluded',
  'manual_review_required',
  'outside_confirmed_availability',
  'realized_intensity_debt_applied',
  'restricted_disciplines_low_only',
  'target_outside_catalog_capacity',
  'workouts_consolidated_on_available_dates',
] as const;
type WarningCode = (typeof warningCodes)[number];

const warningCopy: Record<WarningCode, { message: TranslationKey; title: TranslationKey }> = {
  all_disciplines_blocked_rest_only: {
    title: 'planning.warning.all_disciplines_blocked_rest_only.title',
    message: 'planning.warning.all_disciplines_blocked_rest_only.message',
  },
  anti_stack_violation: {
    title: 'planning.warning.anti_stack_violation.title',
    message: 'planning.warning.anti_stack_violation.message',
  },
  injured_disciplines_excluded: {
    title: 'planning.warning.injured_disciplines_excluded.title',
    message: 'planning.warning.injured_disciplines_excluded.message',
  },
  manual_review_required: {
    title: 'planning.warning.manual_review_required.title',
    message: 'planning.warning.manual_review_required.message',
  },
  outside_confirmed_availability: {
    title: 'planning.warning.outside_confirmed_availability.title',
    message: 'planning.warning.outside_confirmed_availability.message',
  },
  realized_intensity_debt_applied: {
    title: 'planning.warning.realized_intensity_debt_applied.title',
    message: 'planning.warning.realized_intensity_debt_applied.message',
  },
  restricted_disciplines_low_only: {
    title: 'planning.warning.restricted_disciplines_low_only.title',
    message: 'planning.warning.restricted_disciplines_low_only.message',
  },
  target_outside_catalog_capacity: {
    title: 'planning.warning.target_outside_catalog_capacity.title',
    message: 'planning.warning.target_outside_catalog_capacity.message',
  },
  workouts_consolidated_on_available_dates: {
    title: 'planning.warning.workouts_consolidated_on_available_dates.title',
    message: 'planning.warning.workouts_consolidated_on_available_dates.message',
  },  // The server words these three in one language only; the app shows them in the chosen one.
  cross_training_choice_available: {
    title: 'planning.warning.cross_training_choice_available.title',
    message: 'planning.warning.cross_training_choice_available.message',
  },
  distance_only_swim_excluded_from_time_ratio: {
    title: 'planning.warning.distance_only_swim_excluded_from_time_ratio.title',
    message: 'planning.warning.distance_only_swim_excluded_from_time_ratio.message',
  },
  injury_replacement_capacity_limited: {
    title: 'planning.warning.injury_replacement_capacity_limited.title',
    message: 'planning.warning.injury_replacement_capacity_limited.message',
  },
};

function isWarningCode(code: string): code is WarningCode {
  return (warningCodes as readonly string[]).includes(code);
}

// Called from render paths and view models alike, so it reads the language the
// provider last applied. Unknown codes keep the server's own message.
export function warningPresentation(warning: PlanWarning): {
  message: string;
  title: string;
} {
  if (isWarningCode(warning.code)) {
    const copy = warningCopy[warning.code];
    return { title: translate(copy.title), message: translate(copy.message) };
  }
  return {
    title: translate('planning.warning.fallbackTitle'),
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
  const { t } = useLanguage();
  return (
    <View accessibilityRole="alert" style={styles.panel}>
      <Text style={styles.title}>{t('move.warning')}</Text>
      {warnings.map((warning) => {
        const presentation = warningPresentation(warning);
        return (
          <View key={warning.id ?? `${warning.code}:${warning.planned_workout_id ?? ''}`} style={styles.warning}>
            <Text style={styles.warningTitle}>{presentation.title}</Text>
            <Text style={styles.warningText}>{presentation.message}</Text>
          </View>
        );
      })}
      <Text style={styles.body}>{t('planning.move.serverAuthoritative')}</Text>
      <View style={styles.actions}>
        <View style={styles.actionCell}>
          <Button label={t('move.confirm')} onPress={onConfirm} />
        </View>
        <View style={styles.actionCell}>
          <Button label={t('move.cancel')} onPress={onCancel} secondary />
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
