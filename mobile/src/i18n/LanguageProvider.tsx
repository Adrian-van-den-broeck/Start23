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

export type AppLanguage = 'nl' | 'en';
export type LanguagePreference = 'system' | AppLanguage;

const preferenceStorageKey = 'start23.language-preference';

const nl = {
  'common.active': 'Actief',
  'common.bike': 'Fietsen',
  'common.close': 'Sluiten',
  'common.durationMinutes': '{minutes} min',
  'common.loading': 'Laden…',
  'common.next': 'Volgende',
  'common.previous': 'Vorige',
  'common.restDay': 'Rustdag',
  'common.run': 'Lopen',
  'common.swim': 'Zwemmen',
  'common.today': 'Vandaag',
  'language.auto': 'Automatisch',
  'language.autoHint': 'Volgt de taal van dit toestel',
  'language.english': 'English',
  'language.label': 'Taal',
  'language.nederlands': 'Nederlands',
  'planning.calendar': 'Kalender',
  'planning.choose': 'Kiezen',
  'planning.headerCaption': 'Jouw trainingsweek',
  'planning.myZones': 'Mijn zones',
  'planning.profile': 'Profiel',
  'planning.profileData': 'Gegevens en doel',
  'planning.profileIntegrations': 'Apps en data',
  'planning.profileMenu': 'Open menu',
  'planning.profilePersonal': 'Persoonlijke ruimte',
  'planning.profileSetup': 'Alles over jouw setup',
  'planning.safeSignOut': 'Veilig afmelden',
  'planning.trainingRpe': 'Training & RPE',
  'planning.week': 'Week',
  'calendar.approvedOnly': 'Alleen goedgekeurde trainingen verschijnen hier.',
  'calendar.emptyDay': 'Geen training gepland.',
  'calendar.month': 'Maand',
  'calendar.noWorkouts': 'Geen actieve trainingen in deze periode.',
  'calendar.restrictionRest': 'Rust vanwege een bevestigde beperking.',
  'calendar.scheduledRest': 'Bewust leeg gelaten in het actieve plan.',
  'calendar.title': 'Trainingskalender',
  'calendar.viewDay': 'Bekijk {date}',
  'calendar.week': 'Week',
  'activity.back': 'Weekplanning',
  'activity.correction': 'RPE deze week corrigeren',
  'activity.distance': 'Afstand (meter, optioneel)',
  'activity.duration': 'Werkelijke duur (minuten)',
  'activity.external': 'Buiten Wombo',
  'activity.heartRate': 'Gemiddelde hartslag (bpm)',
  'activity.heartRateHint': 'Vul dit in als hartslagobservatie bij de toegewezen training vereist is.',
  'activity.heartRatePlaceholder': 'bijv. 149',
  'activity.noRecent': 'Nog geen activiteiten geregistreerd.',
  'activity.recent': 'Recente activiteiten',
  'activity.register': 'Training registreren',
  'activity.registerHint': 'Kies een geplande training, of registreer bewust een extra training.',
  'activity.save': 'Activiteit opslaan',
  'activity.signOut': 'Afmelden',
  'activity.startedAt': 'Werkelijk gestart (ISO inclusief tijdzone)',
  'activity.timezone': 'Tijdzone van de activiteit',
  'activity.title': 'Training & RPE',
  'activity.unplanned': 'Extra, ongeplande training',
  'activity.result.awaiting_rpe': 'RPE nodig',
  'activity.result.deviation': 'Afwijkende uitvoering',
  'activity.result.hidden_fatigue': 'Herstelsignaal',
  'activity.result.overshoot': 'Zwaarder dan gepland',
  'activity.result.perfect_match': 'Goed aangesloten',
  'activity.result.unplanned': 'Extra training',
  'activity.message.deviation': 'De uitvoering week af van de planning, maar vraagt niet automatisch om een correctie.',
  'activity.message.hidden_fatigue': 'Deze rustige training voelde duidelijk zwaarder dan verwacht. Controleer een eventueel herstelvoorstel.',
  'activity.message.overshoot': 'Deze training viel zwaarder uit dan gepland. Een eventuele aanpassing blijft eerst een voorstel.',
  'activity.message.perfect_match': 'De training sloot goed aan op de geplande inspanning.',
  'activity.message.unplanned': 'Deze extra training stond niet in je actieve planning. Een eventuele aanpassing blijft eerst een voorstel.',
  'rpe.awaiting': 'RPE nodig',
  'rpe.prompt': 'Hoe zwaar voelde deze training?',
  'rpe.reminder': '{count} training{suffix} wacht{verbSuffix} op RPE · open Training & RPE',
} as const;

type TranslationKey = keyof typeof nl;

const en: Record<TranslationKey, string> = {
  'common.active': 'Active',
  'common.bike': 'Cycling',
  'common.close': 'Close',
  'common.durationMinutes': '{minutes} min',
  'common.loading': 'Loading…',
  'common.next': 'Next',
  'common.previous': 'Previous',
  'common.restDay': 'Rest day',
  'common.run': 'Running',
  'common.swim': 'Swimming',
  'common.today': 'Today',
  'language.auto': 'Automatic',
  'language.autoHint': 'Uses this device’s language',
  'language.english': 'English',
  'language.label': 'Language',
  'language.nederlands': 'Nederlands',
  'planning.calendar': 'Calendar',
  'planning.choose': 'Choose',
  'planning.headerCaption': 'Your training week',
  'planning.myZones': 'My zones',
  'planning.profile': 'Profile',
  'planning.profileData': 'Details and goal',
  'planning.profileIntegrations': 'Apps and data',
  'planning.profileMenu': 'Open menu',
  'planning.profilePersonal': 'Personal space',
  'planning.profileSetup': 'Everything about your setup',
  'planning.safeSignOut': 'Sign out securely',
  'planning.trainingRpe': 'Training & RPE',
  'planning.week': 'Week',
  'calendar.approvedOnly': 'Only approved workouts appear here.',
  'calendar.emptyDay': 'No workout planned.',
  'calendar.month': 'Month',
  'calendar.noWorkouts': 'No active workouts in this period.',
  'calendar.restrictionRest': 'Rest due to a confirmed restriction.',
  'calendar.scheduledRest': 'Intentionally left open in the active plan.',
  'calendar.title': 'Training calendar',
  'calendar.viewDay': 'View {date}',
  'calendar.week': 'Week',
  'activity.back': 'Weekly plan',
  'activity.correction': 'Correct this week’s RPE',
  'activity.distance': 'Distance (metres, optional)',
  'activity.duration': 'Actual duration (minutes)',
  'activity.external': 'Outside Wombo',
  'activity.heartRate': 'Average heart rate (bpm)',
  'activity.heartRateHint': 'Enter this when a heart-rate observation is required for the assigned workout.',
  'activity.heartRatePlaceholder': 'e.g. 149',
  'activity.noRecent': 'No activities recorded yet.',
  'activity.recent': 'Recent activities',
  'activity.register': 'Record a workout',
  'activity.registerHint': 'Choose a planned workout or deliberately record an extra workout.',
  'activity.save': 'Save activity',
  'activity.signOut': 'Sign out',
  'activity.startedAt': 'Actual start (ISO including time zone)',
  'activity.timezone': 'Activity time zone',
  'activity.title': 'Training & RPE',
  'activity.unplanned': 'Extra, unplanned workout',
  'activity.result.awaiting_rpe': 'RPE needed',
  'activity.result.deviation': 'Different execution',
  'activity.result.hidden_fatigue': 'Recovery signal',
  'activity.result.overshoot': 'Harder than planned',
  'activity.result.perfect_match': 'Matched well',
  'activity.result.unplanned': 'Extra workout',
  'activity.message.deviation': 'The execution differed from the plan, but does not automatically require a correction.',
  'activity.message.hidden_fatigue': 'This easy workout felt notably harder than expected. Review any recovery proposal.',
  'activity.message.overshoot': 'This workout was harder than planned. Any adjustment will remain a proposal first.',
  'activity.message.perfect_match': 'The workout matched the planned effort well.',
  'activity.message.unplanned': 'This extra workout was not in your active plan. Any adjustment will remain a proposal first.',
  'rpe.awaiting': 'RPE needed',
  'rpe.prompt': 'How hard did this workout feel?',
  'rpe.reminder': '{count} workout{suffix} waiting for RPE · open Training & RPE',
};

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

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [preference, setStoredPreference] =
    useState<LanguagePreference>('system');

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
  const value = useMemo<LanguageContextValue>(() => {
    const translations = language === 'nl' ? nl : en;
    return {
      language,
      locale: language === 'nl' ? 'nl-NL' : 'en-GB',
      preference,
      setPreference: async (nextPreference) => {
        setStoredPreference(nextPreference);
        await writePreference(nextPreference);
      },
      t: (key, values = {}) =>
        Object.entries(values).reduce(
          (text, [name, replacement]) =>
            text.replaceAll(`{${name}}`, String(replacement)),
          translations[key],
        ),
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
