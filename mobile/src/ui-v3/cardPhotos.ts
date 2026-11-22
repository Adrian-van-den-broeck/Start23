import type { ImageSourcePropType } from 'react-native';
import type { Discipline } from '../api/types';

// Unsplash License photos; see assets/cards/CREDITS.md. Decorative only: every
// card still names its sport in text.
const photos: Record<Discipline, readonly ImageSourcePropType[]> = {
  bike: [
    require('../../assets/cards/bike-forest-road.jpg'),
    require('../../assets/cards/bike-motion-blur.jpg'),
    require('../../assets/cards/bike-winding-hills.jpg'),
  ],
  run: [
    require('../../assets/wombo-track.jpg'),
    require('../../assets/cards/run-forest-jump.jpg'),
  ],
  swim: [
    require('../../assets/cards/swim-butterfly-pool.jpg'),
    require('../../assets/cards/swim-open-water.jpg'),
  ],
};

// The same training always gets the same photo, so a card never changes its
// picture between renders, undo or a return to the screen.
export function cardPhoto(discipline: Discipline, key: string): ImageSourcePropType {
  const set = photos[discipline];
  let hash = 0;
  for (let index = 0; index < key.length; index += 1) hash = (hash * 31 + key.charCodeAt(index)) >>> 0;
  return set[hash % set.length];
}

export const cardPhotoCount = (discipline: Discipline) => photos[discipline].length;
