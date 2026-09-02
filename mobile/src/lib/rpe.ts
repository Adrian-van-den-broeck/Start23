import type { RpeZone } from '../api/types';

export function formatRpeZones(zones: RpeZone[]): string {
  return zones.map((zone) => zone.display_label).join(' · ');
}
