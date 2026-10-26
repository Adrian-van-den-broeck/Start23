import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export const latestPlanIdKey = 'start23.latest-plan-id';
export const latestSwipeDraftIdKey = 'start23.latest-swipe-draft-id';

// Native writes cannot be cancelled once issued. Preserve call order across
// owner replacement, and let handoffs discard queued writes from a dead owner.
let resumeWrites: Promise<void> = Promise.resolve();
function writeResume(operation: () => Promise<void>, isCurrent: () => boolean): Promise<void> {
  const write = resumeWrites.catch(() => undefined).then(async () => {
    if (isCurrent()) await operation();
  });
  resumeWrites = write;
  return write;
}

export async function rememberPlanId(planId: string | null, isCurrent = () => true): Promise<void> {
  if (Platform.OS === 'web') return;
  return writeResume(async () => {
    if (planId === null) await SecureStore.deleteItemAsync(latestPlanIdKey);
    else await SecureStore.setItemAsync(latestPlanIdKey, planId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }, isCurrent);
}

export async function rememberSwipeDraftId(draftId: string | null, isCurrent = () => true): Promise<void> {
  if (Platform.OS === 'web') return;
  return writeResume(async () => {
    if (draftId === null) await SecureStore.deleteItemAsync(latestSwipeDraftIdKey);
    else await SecureStore.setItemAsync(latestSwipeDraftIdKey, draftId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }, isCurrent);
}
