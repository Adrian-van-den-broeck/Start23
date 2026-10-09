import { Children, cloneElement, isValidElement, useRef, type ReactElement } from 'react';
import { Modal, ScrollView, View, type ModalProps, type ScrollViewProps, type ViewProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { PlannedWorkout } from '../api/types';
import { WorkoutDetail } from '../components/WorkoutDetail';
import { WorkoutDetailScreen } from '../ui-v2/screens/WorkoutDetailScreen';
import { colors } from '../ui-v2/tokens';
import { UiVersionControl } from './UiVersionControl';
import type { UiVersion } from './uiVersion';
import { useUiVersion } from './UiVersionProvider';

export function WorkoutDetailBoundary({ workout, onClose }: {
  workout: PlannedWorkout | null; onClose: () => void;
}) {
  const { effectiveVersion } = useUiVersion();
  const version = effectiveVersion('workoutDetail');
  const position = useRef({ workout, offsets: {} as Partial<Record<UiVersion, number>>, lastY: 0, version, compared: false });
  if (position.current.workout !== workout) position.current = { workout, offsets: {}, lastY: 0, version, compared: false };
  if (position.current.version !== version) {
    position.current.version = version;
    position.current.compared = true;
  }
  const restoredY = position.current.offsets[version] ?? position.current.lastY;
  position.current.offsets[version] = restoredY;
  const scrollProps: ScrollViewProps = {
    contentOffset: { x: 0, y: restoredY },
    scrollEventThrottle: 16,
    onScroll: (event) => {
      // Different content heights can clamp an offset. Keep each presentation's
      // last position so returning to it never inherits the other view's clamp.
      position.current.offsets[version] = event.nativeEvent.contentOffset.y;
      position.current.lastY = event.nativeEvent.contentOffset.y;
    },
  };

  // The approved V1 component is stateless and returns a native Modal. Reuse its
  // exact content for the selected presentation so this one Modal and comparison control
  // remain mounted. If V1 gains hooks or changes its frame, revisit this adapter.
  let legacyContent = null;
  if (version === 'v1') {
    const legacyModal = WorkoutDetail({ workout, onClose }) as ReactElement<ModalProps>;
    const page = legacyModal.props.children;
    if (isValidElement<ViewProps>(page)) {
      legacyContent = cloneElement(page, {}, Children.map(page.props.children, (child) => {
        if (isValidElement<ScrollViewProps>(child) && child.type === ScrollView) {
          return cloneElement(child, { ...scrollProps, testID: 'workout-detail-scroll' });
        }
        return child;
      }));
    }
  }
  return <Modal testID="workout-detail-modal" animationType="none" visible={workout !== null} onRequestClose={onClose}>
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <SafeAreaView edges={['top']}><UiVersionControl /></SafeAreaView>
      {version === 'v1' ? legacyContent : <WorkoutDetailScreen workout={workout} onClose={onClose}
        embedded scrollProps={scrollProps} focusHeading={!position.current.compared} />}
    </View>
  </Modal>;
}
