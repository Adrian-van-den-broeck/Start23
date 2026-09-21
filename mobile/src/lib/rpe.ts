import type { Discipline } from '../api/types';

export type CanonicalRpe = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type RpeChoice = {
  description: string;
  value: CanonicalRpe;
};

const descriptions: Record<Discipline, readonly string[]> = {
  swim: [
    'Gevoelloos door het water glijden.',
    'Ontspannen slag, rustige ademhaling.',
    'Vlotte, ritmische slag.',
    'Doorzwemmen, gecontroleerde ademhaling.',
    'Doelgericht tempo.',
    'Hard werken, snakken naar adem op keerpunt.',
    'Verzuring begint, moeite met techniek.',
    'Net onder sprintniveau.',
    'Snelle verzuring, techniek brokkelt af.',
    'All-out sprint.',
  ],
  bike: [
    'Geen druk op de pedalen.',
    'Zeer licht trappen, uren vol te houden.',
    'Comfortabel duurtempo.',
    'Druk op de pedalen, zweet breekt uit.',
    'Ademhaling aanwezig, korte zinnen.',
    'Branderig gevoel bouwt op.',
    'Benen lopen vol, weinig praten.',
    'Op de limiet, net niet volledig verzuren.',
    'Extreem zwaar, korte intervallen.',
    'Volle sprint, maximale kracht.',
  ],
  run: [
    'Wandelen of extreem traag joggen.',
    'Zeer ontspannen, eindeloos kletsen.',
    'Vlot duurlooptempo, neusademhaling.',
    'Focus nodig, praten in zinnen.',
    "'Sweet spot', comfortabel oncomfortabel.",
    'Zwaar, net niet in het rood.',
    'Diepe ademhaling (10k wedstrijdtempo).',
    'Tegen verzuring aan (5k tempo).',
    'Naar adem happen, zware benen.',
    'Volle sprint, snel moeten stoppen.',
  ],
};

export function rpeChoices(discipline: Discipline): readonly RpeChoice[] {
  return descriptions[discipline].map((description, index) => ({
    description,
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
  return descriptions[discipline][value - 1]!;
}
