import type { FrequencySummary as Summary } from '../../api/types';
import { Notice } from '../../ui-v2/primitives/Notice';
import { Text } from '../../ui-v2/primitives/Text';

const labels = { run: 'Hardlopen', bike: 'Fietsen', swim: 'Zwemmen' };
export function FrequencySummary({ rows }: { rows?: Summary[] }) {
  if (!rows?.length) return null;
  return <>
    {rows.map(row => <Text key={row.sport}>{labels[row.sport]}: {row.requested === null ? 'geen voorkeur' : `${row.requested} gevraagd`} · {row.proposed} voorgesteld</Text>)}
    {rows.some(row => row.requested !== null && row.proposed < row.requested)
      ? <Notice>We stellen deze week minder sessies voor binnen je huidige trainingsvoorwaarden.</Notice> : null}
  </>;
}
