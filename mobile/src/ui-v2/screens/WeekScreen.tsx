import { useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, ScrollView, StyleSheet, View, type ScrollViewProps } from 'react-native';
import { ShellSafeArea } from '../components/ShellInsets';
import { WeekHeader } from '../components/WeekHeader';
import { useLanguage } from '../../i18n/LanguageProvider';
import { AttentionRow } from '../components/AttentionRow';
import { NextSession } from '../components/NextSession';
import { WeekContext } from '../components/WeekContext';
import { WeekTaskCard } from '../components/WeekTaskCard';
import { QuickActionRow } from '../components/QuickActionRow';
import { GoalSummaryRow } from '../components/GoalSummaryRow';
import { ContentTransition } from '../motion/ContentTransition';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Divider } from '../primitives/Divider';
import { Skeleton } from '../primitives/Skeleton';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { WeekAction, WeekHomeViewModel } from '../utils/weekHomeViewModel';
export function WeekScreen({ model, error, busy, onAction, onOpenWorkout, onProfile, onActivities, onCheckIn, onZones, goalName, onGoal, controls, scrollProps }: {
  model: WeekHomeViewModel; error: string | null; busy: boolean; onAction: (action: WeekAction) => void; onOpenWorkout: (id: string) => void;
  onProfile: () => void; onActivities: () => void; onCheckIn: () => void; onZones: () => void; goalName: string | null; onGoal: () => void; controls: ReactNode; scrollProps?: ScrollViewProps;
}) {
  const { t } = useLanguage();
  const [allAttention, setAllAttention] = useState(false);
  const heading = useRef<View>(null);
  const focused = useRef(false);
  const attention = model.attention.filter((item) => item.kind === 'warnings' || item.action !== model.mainAction);
  const initialLoading = model.readState === 'loading' && model.state === 'loading';
  // Compose the action already selected by the accepted model; never choose a next action here.
  const action = model.mainAction;
  const task = action ? {
    status: t(`week.state.${action === 'draft' ? model.state === 'placement' ? 'placement' : 'draft' : action === 'review' ? 'pending' : model.state}`),
    heading: action === 'draft' ? t(model.state === 'placement' ? 'week.task.placement' : 'week.task.draft')
      : action === 'review' ? t('week.task.review') : action === 'prepare' ? t('week.empty.noPlan') : t(`week.state.${model.state}`),
    supporting: action === 'draft' && model.state !== 'placement' ? t('week.attention.draft') : action === 'review' ? t('week.attention.proposal') : undefined,
  } : null;
  const attentionGroup = attention.length ? <View style={styles.attention}>
    <Text variant="sectionTitle" accessibilityRole="header">{t('week.attentionTitle', { count: attention.length })}</Text>
    {(allAttention ? attention : attention.slice(0, 2)).map((item) => <AttentionRow key={item.kind} item={item} disabled={busy} onAction={onAction} />)}
    {attention.length > 2 ? <Button variant="tertiary" label={t(allAttention ? 'week.lessAttention' : 'week.allAttention')} onPress={() => setAllAttention((value) => !value)} /> : null}
  </View> : null;
  return <ShellSafeArea style={styles.frame}>
    <ScrollView testID="week-home-scroll" {...scrollProps} contentContainerStyle={styles.content}>
      <WeekHeader title={t('planning.week')} onProfile={onProfile} profileLabel={t('planning.profile')}
        disabled={busy} titleRef={heading} onTitleLayout={() => {
          if (!focused.current && heading.current) { focused.current = true; AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus'); }
        }} />
      <View style={styles.context}><WeekContext model={model} showStatus={!task || model.state === 'active' || model.state === 'activePending'} /></View>
      {initialLoading ? <><Text accessibilityLiveRegion="polite">{t('common.loading')}</Text><Skeleton /></> : <ContentTransition>
        <View style={styles.sections}>
          {model.readState === 'failed' ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{t('week.loadFailed')}</Text> : null}
          {model.readState === 'loading' ? <Text accessibilityLiveRegion="polite">{t('common.loading')}</Text> : null}
          {error ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{error}</Text> : null}
          <NextSession model={model} onOpenWorkout={onOpenWorkout} />
          {model.empty && model.empty !== 'noPlan' ? model.sessions.length || task
            ? <Text variant="supporting" tone="textMuted">{t(`week.empty.${model.empty}`)}</Text>
            : <Card padding="focus" elevated><Text variant="body">{t(`week.empty.${model.empty}`)}</Text></Card> : null}
          {task && action ? <WeekTaskCard {...task} icon={action === 'review' ? 'document' : action === 'draft' ? 'list' : 'week'} actionLabel={t(`week.action.${action}`)} disabled={busy} onAction={() => onAction(action)} /> : null}
          <View style={styles.navigation}>
            {model.progress ? <Text variant="supporting" tone="textMuted">{t(model.progress.planned === 1 ? 'week.progress.one' : 'week.progress', model.progress)}</Text> : null}
            <QuickActionRow icon="calendar" label={t('week.action.calendar')} disabled={busy} onAction={() => onAction('calendar')} />
          </View>
          {attentionGroup}
          <View style={styles.tools} testID="week-training-tools">
            <Text variant="sectionTitle" accessibilityRole="header">{t('week.tools')}</Text>
            <Card elevated>
              <QuickActionRow icon="activities" label={t('week.activities')} disabled={busy} onAction={onActivities} />
              <View style={styles.rowDivider}><Divider /></View>
              <QuickActionRow icon="document" label={t('week.checkIn')} disabled={busy} onAction={onCheckIn} />
              <View style={styles.rowDivider}><Divider /></View>
              <QuickActionRow icon="intensity" label={t('planning.myZones')} disabled={busy} onAction={onZones} />
              {model.mainAction !== 'prepare' ? <><View style={styles.rowDivider}><Divider /></View><QuickActionRow icon="week" label={t('week.action.prepare')} disabled={busy} onAction={() => onAction('prepare')} /></> : null}
            </Card>
          </View>
          {goalName ? <Card elevated style={styles.goal}><GoalSummaryRow label={t('week.goalLabel')} name={goalName}
            accessibilityLabel={t('week.goal', { name: goalName })} disabled={busy} onAction={onGoal} /></Card> : null}
        </View>
      </ContentTransition>}
      {controls ? <View testID="week-version-controls" style={styles.development}><Divider /><View style={styles.developmentControls}>{controls}</View></View> : null}
    </ScrollView>
  </ShellSafeArea>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  content: { padding: layout.phoneGutter, width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center' },
  context: { marginTop: space[12], marginBottom: space[16] },
  sections: { gap: space[12] }, navigation: { gap: space[4] }, attention: { marginTop: space[12], gap: space[12] },
  tools: { marginTop: space[12], gap: space[12] }, goal: { marginTop: space[12] },
  rowDivider: { marginLeft: layout.iconDisc.row + space[12] + layout.focusOutline },
  development: { marginTop: space[24] }, developmentControls: { paddingTop: space[24] },
});
