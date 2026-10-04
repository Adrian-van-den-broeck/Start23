import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export const latestPlanIdKey = 'start23.latest-plan-id';
export const latestSwipeDraftIdKey = 'start23.latest-swipe-draft-id';

export async function rememberPlanId(planId: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (planId === null) {
    await SecureStore.deleteItemAsync(latestPlanIdKey);
  } else {
    await SecureStore.setItemAsync(latestPlanIdKey, planId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }
}

export async function rememberSwipeDraftId(draftId: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (draftId === null) {
    await SecureStore.deleteItemAsync(latestSwipeDraftIdKey);
  } else {
    await SecureStore.setItemAsync(latestSwipeDraftIdKey, draftId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }
}
