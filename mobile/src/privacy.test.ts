import { readFileSync, readdirSync } from 'node:fs';
import { extname, join } from 'node:path';

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(path);
    if (!['.ts', '.tsx'].includes(extname(path)) || path.includes('.test.')) {
      return [];
    }
    return [path];
  });
}

describe('mobile privacy boundary', () => {
  test('UI, DTOs, errors, accessibility copy, and analytics source expose no private load fields', () => {
    const files = sourceFiles(join(__dirname));
    const forbidden = [
      /\btss\b/i,
      /planned[_ -]?load/i,
      /realized[_ -]?load/i,
      /private[_ -]?load/i,
    ];

    for (const file of files) {
      const source = readFileSync(file, 'utf8');
      for (const pattern of forbidden) {
        expect({ file, match: source.match(pattern)?.[0] }).toEqual({
          file,
          match: undefined,
        });
      }
    }
  });
});
