export function isoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function nextMonday(): string {
  const value = new Date();
  value.setHours(12, 0, 0, 0);
  const daysUntilMonday = (8 - value.getDay()) % 7 || 7;
  value.setDate(value.getDate() + daysUntilMonday);
  return isoDate(value);
}

export function addDays(dateValue: string, days: number): Date {
  const value = new Date(`${dateValue}T12:00:00`);
  value.setDate(value.getDate() + days);
  return value;
}

export function availableDatesFor(
  weekStart: string,
  selectedDays: ReadonlySet<number>,
): string[] {
  return [...selectedDays]
    .sort((left, right) => left - right)
    .map((dayOffset) => isoDate(addDays(weekStart, dayOffset)));
}

export function dayOffsetsFor(weekStart: string, dates: string[]): Set<number> {
  const start = new Date(`${weekStart}T12:00:00`);
  return new Set(
    dates.map((value) =>
      Math.round(
        (new Date(`${value}T12:00:00`).getTime() - start.getTime()) /
        86_400_000,
      ),
    ),
  );
}
