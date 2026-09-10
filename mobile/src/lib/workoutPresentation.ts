const rpeToken = /\bRPE\b/i;

/**
 * Keep physiological RPE guidance out of planning cards.
 *
 * Catalog descriptions can contain a separate sentence with an RPE range. The
 * underlying value remains available for execution and feedback, but sentences
 * containing that internal guidance are not rendered on workout cards.
 */
export function workoutCardDescription(description: string): string {
  const sentences = description.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [];
  return sentences
    .map((sentence) => sentence.trim())
    .filter((sentence) => !rpeToken.test(sentence))
    .join(' ');
}
