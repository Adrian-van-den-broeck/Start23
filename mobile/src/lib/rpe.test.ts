import { rpeChoices, rpeDescription } from './rpe';

describe('Phase 15 textual RPE catalog', () => {
  const expected = {
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
  } as const;

  test.each(['swim', 'bike', 'run'] as const)(
    '%s has all ten exact discipline-specific choices and canonical values',
    (discipline) => {
      expect(rpeChoices(discipline)).toEqual(
        expected[discipline].map((description, index) => ({
          description,
          value: index + 1,
        })),
      );
      expected[discipline].forEach((description, index) => {
        expect(rpeDescription(discipline, index + 1)).toBe(description);
      });
    },
  );

  test('invalid canonical values fail closed', () => {
    expect(() => rpeDescription('run', 0)).toThrow();
    expect(() => rpeDescription('bike', 11)).toThrow();
    expect(() => rpeDescription('swim', 1.5)).toThrow();
  });
});
