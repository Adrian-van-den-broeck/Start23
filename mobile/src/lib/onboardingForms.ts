import type { Discipline, RaceType } from '../api/types.ts';

export const raceDisciplines: Record<RaceType, readonly Discipline[]> = {
  run: ['run'],
  bike: ['bike'],
  swim: ['swim'],
  triathlon: ['swim', 'bike', 'run'],
  duathlon: ['bike', 'run'],
};

export function parsePositiveInteger(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

export function parseClockDuration(value: string): number | null {
  const match = /^(\d{1,3}):(\d{2})(?::(\d{2}))?$/.exec(value.trim());
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  const seconds = Number(match[3] ?? 0);
  if (minutes > 59 || seconds > 59) return null;
  const total = hours * 3600 + minutes * 60 + seconds;
  return total > 0 && total <= 604_800 ? total : null;
}

export function formatClockDuration(seconds: number | null): string {
  if (seconds === null) return '';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`;
}

export function resolveDeviceTimezone(): string | null {
  try {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!timezone) return null;
    new Intl.DateTimeFormat('en', { timeZone: timezone }).format();
    return timezone;
  } catch {
    return null;
  }
}

export function hasPartialObservedZoneTime(
  durationMinutes: string | null,
  zoneMinutes: string[] | null | undefined,
): boolean {
  if (durationMinutes === null || !zoneMinutes) return false;
  const duration = Number(durationMinutes);
  const observed = zoneMinutes.reduce((sum, value) => sum + Number(value), 0);
  return Number.isFinite(duration) && Number.isFinite(observed) && observed < duration;
}
