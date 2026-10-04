import { useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, ScrollView, StyleSheet, View, type ScrollViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../i18n/LanguageProvider';
import { AttentionRow } from '../components/AttentionRow';
import { NextSession } from '../components/NextSession';
import { WeekContext } from '../components/WeekContext';
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
  return <SafeAreaView edges={['top', 'bottom']} style={styles.frame}>
    <ScrollView testID="week-home-scroll" {...scrollProps} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View ref={heading} accessible accessibilityRole="header" accessibilityLabel={t('planning.week')} onLayout={() => {
          if (!focused.current && heading.current) { focused.current = true; AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus'); }
        }}><Text variant="screenTitle" accessible={false}>Wombo · {t('planning.week')}</Text></View>
        <Button variant="tertiary" label={t('planning.profile')} onPress={onProfile} disabled={busy} />
      </View>
      <WeekContext model={model} />
      {initialLoading ? <><Text accessibilityLiveRegion="polite">{t('common.loading')}</Text><Skeleton /></> : <ContentTransition>
        <View style={styles.sections}>
          {model.readState === 'failed' ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{t('week.loadFailed')}</Text> : null}
          {model.readState === 'loading' ? <Text accessibilityLiveRegion="polite">{t('common.loading')}</Text> : null}
          {error ? <Text style={{ color: colors.destructive }} accessibilityLiveRegion="polite">{error}</Text> : null}
          <NextSession model={model} onOpenWorkout={onOpenWorkout} />
          {model.empty ? <Card><Text variant="sectionTitle">{t(`week.empty.${model.empty}`)}</Text></Card> : null}
          {model.mainAction ? <Button label={t(`week.action.${model.mainAction}`)} disabled={busy} onPress={() => onAction(model.mainAction!)} /> : null}
          {model.progress ? <Text variant="body">{t('week.progress', model.progress)}</Text> : null}
          {attention.length ? <View style={styles.attention}>
            <Text variant="sectionTitle" accessibilityRole="header">{t('week.attentionTitle', { count: attention.length })}</Text>
            {(allAttention ? attention : attention.slice(0, 2)).map((item) => <AttentionRow key={item.kind} item={item} disabled={busy} onAction={onAction} />)}
            {attention.length > 2 ? <Button variant="tertiary" label={t(allAttention ? 'week.lessAttention' : 'week.allAttention')} onPress={() => setAllAttention((value) => !value)} /> : null}
          </View> : null}
          <Divider />
          <View style={styles.support}>
            <Button variant="secondary" label={t('week.action.calendar')} disabled={busy} onPress={() => onAction('calendar')} />
            <Button variant="tertiary" label={t('week.activities')} disabled={busy} onPress={onActivities} />
            <Button variant="tertiary" label={t('week.checkIn')} disabled={busy} onPress={onCheckIn} />
            <Button variant="tertiary" label={t('planning.myZones')} disabled={busy} onPress={onZones} />
            {model.mainAction !== 'prepare' ? <Button variant="tertiary" label={t('week.action.prepare')} disabled={busy} onPress={() => onAction('prepare')} /> : null}
            {goalName ? <Button variant="tertiary" label={t('week.goal', { name: goalName })} disabled={busy} onPress={onGoal} /> : null}
          </View>
        </View>
      </ContentTransition>}
      {controls}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  content: { padding: layout.phoneGutter, paddingBottom: space[32], width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center', gap: space[24] },
  header: { gap: space[8] }, sections: { gap: space[24] }, attention: { gap: space[12] }, support: { gap: space[4] }
});
