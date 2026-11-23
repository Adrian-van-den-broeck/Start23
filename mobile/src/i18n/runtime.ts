import { format, type TranslationKey, type TranslationValues } from './dictionaries';

// Text produced outside React (API errors, RPE scale descriptions) follows the
// language the provider last applied. Dutch until the provider says otherwise.
let current: 'nl' | 'en' = 'nl';

export function setRuntimeLanguage(language: 'nl' | 'en'): void {
  current = language;
}

export function runtimeLanguage(): 'nl' | 'en' {
  return current;
}

export function translate(key: TranslationKey, values?: TranslationValues): string {
  return format(current, key, values);
}
