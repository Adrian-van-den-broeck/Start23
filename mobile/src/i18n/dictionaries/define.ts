/**
 * An area dictionary: Dutch is the source of truth, and the type forces every
 * Dutch key to have an English translation, so a missing one fails typecheck.
 */
export function defineDictionary<const N extends Record<string, string>>(
  nl: N,
  en: { [K in keyof N]: string },
): { nl: N; en: { [K in keyof N]: string } } {
  return { nl, en };
}
