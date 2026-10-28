export const uncertainWriteMessage = 'De uitkomst van het opslaan is nog onbekend. Controleer eerst de opgeslagen status. Bij opnieuw proberen blijft de oorspronkelijke actie behouden.';
export const unreadableResponseMessage = 'Het antwoord van Wombo kon niet betrouwbaar worden gelezen. Probeer het laden opnieuw.';
const translations: Record<string, string> = {
  [uncertainWriteMessage]: 'The save outcome is still unknown. Check the stored status first. Retrying preserves the original action.',
  [unreadableResponseMessage]: 'The Wombo response could not be read reliably. Please retry loading.',
  'De Wombo-server is niet bereikbaar. Controleer je verbinding en probeer opnieuw.': 'The Wombo server could not be reached. Check your connection and retry.',
};
export function localizeRecoveryMessage(message: string | null, language: 'nl' | 'en'): string | null {
  return message && language === 'en' ? translations[message] ?? message : message;
}
