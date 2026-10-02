import { useState } from 'react';
import { Modal, StyleSheet, View, type ScrollViewProps } from 'react-native';
import type { PlannedWorkout } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { RpeIndicator } from '../components/RpeIndicator';
import { SessionSequence } from '../components/SessionSequence';
import { ContentTransition } from '../motion/ContentTransition';
import { Button } from '../primitives/Button';
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
        <WorkoutSummary summary={model.summary} showDescription={false} />
        {model.description ? <Text>{model.description}</Text> : null}
        <RpeIndicator range={model.expectedRpe} />
        <Divider />
        <SessionSequence segments={model.segments} />
        {model.rpeReference.length ? <>
          <Divider />
          <Button variant="tertiary" label={t('detail.rpeReference')}
            accessibilityState={{ expanded: referenceExpanded }} onPress={() => setReferenceExpanded((value) => !value)} />
          {referenceExpanded ? model.rpeReference.map((reference, index) => <View key={index} style={styles.reference}>
            <Text variant="cardTitle" accessibilityRole="header">{reference.label}</Text>
            <RpeIndicator range={reference.range} kind="rpe" />
            <Text>{reference.trainingType}</Text><Text>{reference.description}</Text>
          </View>) : null}
        </> : null}
      </View>
    </ContentTransition>
  </Screen> : null;
  return embedded ? content : <Modal testID="workout-detail-modal" animationType="none" visible={workout !== null} onRequestClose={onClose}>{content}</Modal>;
}
const styles = StyleSheet.create({ content: { gap: space[24] }, reference: { gap: space[8] } });
