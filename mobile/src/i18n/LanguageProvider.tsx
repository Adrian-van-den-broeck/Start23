import * as SecureStore from 'expo-secure-store';
import { getLocales } from 'expo-localization';
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { Platform } from 'react-native';

import { format, type TranslationKey } from './dictionaries';
import { setRuntimeLanguage } from './runtime';

export type AppLanguage = 'nl' | 'en';
export type LanguagePreference = 'system' | AppLanguage;

export type { TranslationKey };

const preferenceStorageKey = 'start23.language-preference';


type TranslationValues = Record<string, string | number>;

type LanguageContextValue = {
  language: AppLanguage;
  locale: 'nl-NL' | 'en-GB';
  preference: LanguagePreference;
  setPreference: (preference: LanguagePreference) => Promise<void>;
  t: (key: TranslationKey, values?: TranslationValues) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function deviceLanguage(): AppLanguage {
  return getLocales()[0]?.languageCode === 'nl' ? 'nl' : 'en';
}

async function readPreference(): Promise<LanguagePreference | null> {
  if (Platform.OS === 'web') {
    const value = globalThis.localStorage?.getItem(preferenceStorageKey);
    return value === 'system' || value === 'nl' || value === 'en' ? value : null;
  }
  const value = await SecureStore.getItemAsync(preferenceStorageKey);
  return value === 'system' || value === 'nl' || value === 'en' ? value : null;
}

async function writePreference(preference: LanguagePreference): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.setItem(preferenceStorageKey, preference);
    return;
  }
  await SecureStore.setItemAsync(preferenceStorageKey, preference, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

export function LanguageProvider({ children }: { children: ReactNode; }) {
  // Dutch unless the athlete chooses otherwise. 'system' (follow the phone) is
  // only used when explicitly selected.
  const [preference, setStoredPreference] =
    useState<LanguagePreference>('nl');

  useEffect(() => {
    let mounted = true;
    readPreference()
      .then((stored) => {
        if (mounted && stored) setStoredPreference(stored);
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, []);

  const language = preference === 'system' ? deviceLanguage() : preference;
  setRuntimeLanguage(language);
  const value = useMemo<LanguageContextValue>(() => {
    return {
      language,
      locale: language === 'nl' ? 'nl-NL' : 'en-GB',
      preference,
      setPreference: async (nextPreference) => {
        setStoredPreference(nextPreference);
        await writePreference(nextPreference);
      },
      t: (key, values = {}) => format(language, key, values),
    };
  }, [language, preference]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider.');
  }
  return context;
}
