import { useState } from 'react';
import { Modal, StyleSheet, View, type ScrollViewProps } from 'react-native';
import type { PlannedWorkout } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { studioPresentation } from '../../ui-v3/presentation';
import { CardDivider, Surface } from '../../ui-v3/screens/support';
import { SessionLead } from '../../ui-v3/SessionLead';
import { WorkoutSummary } from '../components/WorkoutSummary';
import { RpeIndicator } from '../components/RpeIndicator';
import { SessionSequence } from '../components/SessionSequence';
import { ContentTransition } from '../motion/ContentTransition';
import { Button } from '../primitives/Button';
import { Icon } from '../primitives/Icon';
import { IconTile } from '../primitives/IconTile';
import { Divider } from '../primitives/Divider';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { colors, space } from '../tokens';
import { workoutDetailViewModel } from '../utils/workoutDetailViewModel';

export function WorkoutDetailScreen({ workout, onClose, embedded = false, scrollProps, focusHeading = true }: {
  workout: PlannedWorkout | null; onClose: () => void;
  embedded?: boolean; scrollProps?: ScrollViewProps; focusHeading?: boolean;
}) {
  const { t, locale } = useLanguage();
  const [referenceExpanded, setReferenceExpanded] = useState(false);
  const model = workout ? workoutDetailViewModel(workout) : null;
  const content = model ? <Screen title={t('detail.title')} onBack={onClose} scrollProps={scrollProps} topInsetOwned={embedded} focusHeading={focusHeading}>
    <ContentTransition>
      <View style={styles.content}>
        {studioPresentation ? <SessionLead summary={model.summary} statusInKicker showDescription={false} headingTestID="workout-detail-heading"
          heading={t(`detail.status.${model.summary.status}`)}
          date={model.summary.date ? new Date(`${model.summary.date}T12:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) : ''} />
          : <WorkoutSummary summary={model.summary} showDescription={false} variant="focus" />}
        <Surface elevated={false} style={styles.prescription}>
          {model.description ? <><Text>{model.description}</Text><CardDivider /></> : null}
          <View style={styles.expected}>
            {studioPresentation ? <Icon name="intensity" size={20} color={colors.primary} /> : <IconTile name="intensity" size="field" />}
            <View style={styles.expectedLabel}><RpeIndicator range={model.expectedRpe} /></View>
          </View>
        </Surface>
        <SessionSequence segments={model.segments} />
        {model.rpeReference.length ? <Surface elevated={false} style={styles.referenceGroup}>
          <Button variant="secondary" label={t('detail.rpeReference')}
            accessibilityState={{ expanded: referenceExpanded }} onPress={() => setReferenceExpanded((value) => !value)} />
          {referenceExpanded ? model.rpeReference.map((reference, index) => <View key={index} style={styles.reference}>
            <Divider />
            <Text variant={studioPresentation ? 'label' : 'cardTitle'} accessibilityRole="header">{reference.label}</Text>
            <RpeIndicator range={reference.range} kind="rpe" />
            <Text variant={studioPresentation ? 'supporting' : 'body'}>{reference.trainingType}</Text>
            <Text variant={studioPresentation ? 'supporting' : 'body'} tone={studioPresentation ? 'textMuted' : 'text'}>{reference.description}</Text>
          </View>) : null}
        </Surface> : null}
      </View>
    </ContentTransition>
  </Screen> : null;
  return embedded ? content : <Modal testID="workout-detail-modal" animationType="none" visible={workout !== null} onRequestClose={onClose}>{content}</Modal>;
}
const styles = StyleSheet.create({
  content: { gap: studioPresentation ? space[16] : space[24] }, prescription: { gap: studioPresentation ? space[12] : space[16] },
  expected: { flexDirection: 'row', alignItems: 'center', gap: studioPresentation ? space[8] : space[12] }, expectedLabel: { flex: 1 },
  referenceGroup: { gap: studioPresentation ? space[12] : space[16] }, reference: { gap: space[8] },
});
