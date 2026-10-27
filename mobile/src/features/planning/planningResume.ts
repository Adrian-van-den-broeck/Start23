import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export const latestPlanIdKey = 'start23.latest-plan-id';
export const latestSwipeDraftIdKey = 'start23.latest-swipe-draft-id';

export function scopedResumeKey(owner: string, key: string): string {
  // Auth subject, never a name/email or a backend authorization input.
  if (!/^[a-zA-Z0-9-]+$/.test(owner)) throw new Error('Invalid planning owner');
  return key.replace('start23.', `start23.${owner}.`);
}

export async function readResumeId(owner: string, key: string): Promise<{ id: string | null; legacy: boolean }> {
  if (Platform.OS === 'web') return { id: null, legacy: false };
  const scoped = await SecureStore.getItemAsync(scopedResumeKey(owner, key));
  if (scoped) return { id: scoped, legacy: false };
  // Legacy keys are read-only. Only an authenticated successful resource GET
  // permits copying one into this owner's namespace. Never delete global keys:
  // an inaccessible legacy identity could still belong to another athlete.
  return { id: await SecureStore.getItemAsync(key), legacy: true };
}

// Native writes cannot be cancelled once issued. Serialize per immutable owner;
// a slow A write never blocks B's independent namespace.
const resumeWrites = new Map<string, Promise<void>>();
function writeResume(owner: string, operation: () => Promise<void>, isCurrent: () => boolean): Promise<void> {
  const write = (resumeWrites.get(owner) ?? Promise.resolve()).catch(() => undefined).then(async () => {
    if (isCurrent()) await operation();
  });
  resumeWrites.set(owner, write);
  const release = () => { if (resumeWrites.get(owner) === write) resumeWrites.delete(owner); };
  void write.then(release, release);
  return write;
}

export async function rememberPlanId(owner: string, planId: string | null, isCurrent = () => true): Promise<void> {
  if (Platform.OS === 'web') return;
  return writeResume(owner, async () => {
    if (planId === null) await SecureStore.deleteItemAsync(scopedResumeKey(owner, latestPlanIdKey));
    else await SecureStore.setItemAsync(scopedResumeKey(owner, latestPlanIdKey), planId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }, isCurrent);
}

export async function rememberSwipeDraftId(owner: string, draftId: string | null, isCurrent = () => true): Promise<void> {
  if (Platform.OS === 'web') return;
  return writeResume(owner, async () => {
    if (draftId === null) await SecureStore.deleteItemAsync(scopedResumeKey(owner, latestSwipeDraftIdKey));
    else await SecureStore.setItemAsync(scopedResumeKey(owner, latestSwipeDraftIdKey), draftId, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  }, isCurrent);
}
