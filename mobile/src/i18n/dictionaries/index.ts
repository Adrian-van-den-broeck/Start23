import { baseEn, baseNl } from './base';
import activity from './activity';
import auth from './auth';
import calibration from './calibration';
import checkin from './checkin';
import errors from './errors';
import integrations from './integrations';
import onboarding from './onboarding';
import planning from './planning';
import rpe from './rpe';
import zones from './zones';

export const nl = {
  ...baseNl, ...activity.nl, ...auth.nl, ...calibration.nl, ...checkin.nl, ...errors.nl,
  ...integrations.nl, ...onboarding.nl, ...planning.nl, ...rpe.nl, ...zones.nl,
};
export type TranslationKey = keyof typeof nl;
export const en: Record<TranslationKey, string> = {
  ...baseEn, ...activity.en, ...auth.en, ...calibration.en, ...checkin.en, ...errors.en,
  ...integrations.en, ...onboarding.en, ...planning.en, ...rpe.en, ...zones.en,
};
export type TranslationValues = Record<string, string | number>;

export function format(language: 'nl' | 'en', key: TranslationKey, values: TranslationValues = {}): string {
  return Object.entries(values).reduce(
    (text, [name, replacement]) => text.replaceAll(`{${name}}`, String(replacement)),
    (language === 'nl' ? nl : en)[key],
  );
}
