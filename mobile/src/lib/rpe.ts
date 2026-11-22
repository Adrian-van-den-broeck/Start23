import type { Discipline } from '../api/types';
import type { TranslationKey } from '../i18n/LanguageProvider';
import { translate } from '../i18n/runtime';

export type CanonicalRpe = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type RpeChoice = {
  description: string;
  value: CanonicalRpe;
};

// Approved scale: index + 1 is the canonical RPE value. The wording lives in
// the 'rpe.*' dictionary and follows the language the provider last applied.
const descriptions: Record<Discipline, readonly TranslationKey[]> = {
  swim: [
    'rpe.swim.1', 'rpe.swim.2', 'rpe.swim.3', 'rpe.swim.4', 'rpe.swim.5',
    'rpe.swim.6', 'rpe.swim.7', 'rpe.swim.8', 'rpe.swim.9', 'rpe.swim.10',
  ],
  bike: [
    'rpe.bike.1', 'rpe.bike.2', 'rpe.bike.3', 'rpe.bike.4', 'rpe.bike.5',
    'rpe.bike.6', 'rpe.bike.7', 'rpe.bike.8', 'rpe.bike.9', 'rpe.bike.10',
  ],
  run: [
    'rpe.run.1', 'rpe.run.2', 'rpe.run.3', 'rpe.run.4', 'rpe.run.5',
    'rpe.run.6', 'rpe.run.7', 'rpe.run.8', 'rpe.run.9', 'rpe.run.10',
  ],
};

export function rpeChoices(discipline: Discipline): readonly RpeChoice[] {
  return descriptions[discipline].map((key, index) => ({
    description: translate(key),
    value: (index + 1) as CanonicalRpe,
  }));
}

export function rpeDescription(
  discipline: Discipline,
  value: number,
): string {
  if (!Number.isInteger(value) || value < 1 || value > 10) {
    throw new Error('RPE must be an integer from 1 through 10.');
  }
  return translate(descriptions[discipline][value - 1]!);
}
