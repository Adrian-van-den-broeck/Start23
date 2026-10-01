/** Canonical run pace is a whole number of seconds per kilometre. */
export function parseRunPace(value: string): number | null {
  const match = /^(\d{1,2}):([0-5]\d)$/.exec(value.trim());
  if (!match) return null;
  const seconds = Number(match[1]) * 60 + Number(match[2]);
  return seconds > 0 && seconds <= 3600 ? seconds : null;
}

export function formatRunPace(value: string | number | null): string {
  if (value === null) return 'open';
  const seconds = Number(value);
  if (!Number.isInteger(seconds) || seconds <= 0 || seconds > 3600) {
    return 'ongeldig tempo';
  }
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')} /km`;
}

export function observedRunPace(durationMinutes: string | null, distanceMeters: number | null): string | null {
  if (durationMinutes === null || distanceMeters === null || distanceMeters <= 0) return null;
  const seconds = Math.round(Number(durationMinutes) * 60_000 / distanceMeters);
  return Number.isFinite(seconds) ? formatRunPace(seconds) : null;
}
