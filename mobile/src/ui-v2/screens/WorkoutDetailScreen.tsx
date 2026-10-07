import { useState } from 'react';
import { Modal, StyleSheet, View, type ScrollViewProps } from 'react-native';
import type { PlannedWorkout } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { RpeIndicator } from '../components/RpeIndicator';
import { SessionSequence } from '../components/SessionSequence';
import { ContentTransition } from '../motion/ContentTransition';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { IconTile } from '../primitives/IconTile';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import { workoutDetailViewModel } from '../utils/workoutDetailViewModel';

export function WorkoutDetailScreen({ workout, onClose, embedded = false, scrollProps, focusHeading = true }: {
  workout: PlannedWorkout | null; onClose: () => void;
  embedded?: boolean; scrollProps?: ScrollViewProps; focusHeading?: boolean;
}) {
  const { t } = useLanguage();
  const [referenceExpanded, setReferenceExpanded] = useState(false);
  const model = workout ? workoutDetailViewModel(workout) : null;
  const content = model ? <Screen title={t('detail.title')} onBack={onClose} scrollProps={scrollProps} topInsetOwned={embedded} focusHeading={focusHeading}>
    <ContentTransition>
      <View style={styles.content}>
        <WorkoutSummary summary={model.summary} showDescription={false} variant="focus" />
        <Card style={styles.prescription}>
          {model.description ? <><Text>{model.description}</Text><Divider /></> : null}
          <View style={styles.expected}>
            <IconTile name="intensity" size="field" />
            <View style={styles.expectedLabel}><RpeIndicator range={model.expectedRpe} /></View>
          </View>
        </Card>
        <SessionSequence segments={model.segments} />
        {model.rpeReference.length ? <Card style={styles.referenceGroup}>
          <Button variant="secondary" label={t('detail.rpeReference')}
            accessibilityState={{ expanded: referenceExpanded }} onPress={() => setReferenceExpanded((value) => !value)} />
          {referenceExpanded ? model.rpeReference.map((reference, index) => <View key={index} style={styles.reference}>
            <Divider />
            <Text variant="cardTitle" accessibilityRole="header">{reference.label}</Text>
            <RpeIndicator range={reference.range} kind="rpe" />
            <Text>{reference.trainingType}</Text><Text>{reference.description}</Text>
          </View>) : null}
        </Card> : null}
      </View>
    </ContentTransition>
  </Screen> : null;
  return embedded ? content : <Modal testID="workout-detail-modal" animationType="none" visible={workout !== null} onRequestClose={onClose}>{content}</Modal>;
}
const styles = StyleSheet.create({
  content: { gap: space[24] }, prescription: { gap: space[16] },
  expected: { flexDirection: 'row', alignItems: 'center', gap: space[12] }, expectedLabel: { flex: 1 },
  referenceGroup: { gap: space[16] }, reference: { gap: space[8] },
});
