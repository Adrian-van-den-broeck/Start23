import { useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, ScrollView, StyleSheet, View, useWindowDimensions, type ScrollViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
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
  const { fontScale } = useWindowDimensions();
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
  const attentionByTask = task && !model.sessions.length;
  return <SafeAreaView edges={['top', 'bottom']} style={styles.frame}>
    <ScrollView testID="week-home-scroll" {...scrollProps} style={styles.scroll} contentContainerStyle={styles.content}>
      <View style={[styles.header, fontScale >= 1.5 && styles.stackedHeader]}>
        <View testID="week-header-title" style={[styles.title, fontScale >= 1.5 && styles.stackedTitle]} ref={heading} accessible accessibilityRole="header" accessibilityLabel={t('planning.week')} onLayout={() => {
          if (!focused.current && heading.current) { focused.current = true; AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus'); }
        }}><Text variant="screenTitle" accessible={false}>Wombo · {t('planning.week')}</Text></View>
        <QuickActionRow label={t('planning.profile')} onAction={onProfile} disabled={busy} style={[styles.profile, fontScale >= 1.5 && styles.stackedProfile]} />
      </View>
      <View style={styles.context}><WeekContext model={model} showStatus={!task || model.state === 'active' || model.state === 'activePending'} /></View>
      {initialLoading ? <><Text accessibilityLiveRegion="polite">{t('common.loading')}</Text><Skeleton /></> : <ContentTransition>
        <View style={styles.sections}>
          {model.readState === 'failed' ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{t('week.loadFailed')}</Text> : null}
          {model.readState === 'loading' ? <Text accessibilityLiveRegion="polite">{t('common.loading')}</Text> : null}
          {error ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{error}</Text> : null}
          <NextSession model={model} onOpenWorkout={onOpenWorkout} />
          {model.empty && model.empty !== 'noPlan' ? model.sessions.length || task
            ? <Text variant="supporting" tone="textMuted">{t(`week.empty.${model.empty}`)}</Text>
            : <Card><Text variant="body">{t(`week.empty.${model.empty}`)}</Text></Card> : null}
          {task && action ? <WeekTaskCard {...task} actionLabel={t(`week.action.${action}`)} disabled={busy} onAction={() => onAction(action)} /> : null}
          {attentionByTask ? attentionGroup : null}
          <View style={styles.navigation}>
            {model.progress ? <Text variant="supporting" tone="textMuted">{t(model.progress.planned === 1 ? 'week.progress.one' : 'week.progress', model.progress)}</Text> : null}
            <QuickActionRow label={t('week.action.calendar')} disabled={busy} onAction={() => onAction('calendar')} />
          </View>
          {!attentionByTask ? attentionGroup : null}
          <View style={styles.tools} testID="week-training-tools">
            <Text variant="sectionTitle" accessibilityRole="header">{t('week.tools')}</Text>
            <View>
              <QuickActionRow label={t('week.activities')} disabled={busy} onAction={onActivities} />
              <Divider />
              <QuickActionRow label={t('week.checkIn')} disabled={busy} onAction={onCheckIn} />
              <Divider />
              <QuickActionRow label={t('planning.myZones')} disabled={busy} onAction={onZones} />
              {model.mainAction !== 'prepare' ? <><Divider /><QuickActionRow label={t('week.action.prepare')} disabled={busy} onAction={() => onAction('prepare')} /></> : null}
            </View>
          </View>
          {goalName ? <View style={styles.goal}><Divider /><GoalSummaryRow label={t('week.goalLabel')} name={goalName}
            accessibilityLabel={t('week.goal', { name: goalName })} disabled={busy} onAction={onGoal} /></View> : null}
        </View>
      </ContentTransition>}
      {__DEV__ && controls ? <View testID="week-development-footer" style={styles.development}><Divider /><View style={styles.developmentControls}>{controls}</View></View> : null}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  scroll: { overflow: 'hidden' },
  content: { padding: layout.phoneGutter, width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center' },
  header: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[8] },
  stackedHeader: { flexDirection: 'column', flexWrap: 'nowrap', alignItems: 'stretch' },
  stackedTitle: { flexGrow: 0, flexShrink: 0, width: '100%' }, stackedProfile: { alignSelf: 'stretch' },
  title: { flexGrow: 1, flexShrink: 1 }, profile: { flexGrow: 0, flexShrink: 0, minWidth: space[48] * 2, alignSelf: 'flex-end' },
  context: { marginTop: space[12], marginBottom: space[16] },
  sections: { gap: space[12] }, navigation: { gap: space[4] }, attention: { gap: space[12] },
  tools: { marginTop: space[12], gap: space[8] }, goal: { marginTop: space[4] },
  development: { marginTop: space[24] }, developmentControls: { paddingTop: space[24] },
});
