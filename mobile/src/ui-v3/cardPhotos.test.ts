import { cardPhoto, cardPhotoCount } from './cardPhotos';

test.each(['run', 'bike', 'swim'] as const)('%s has more than one photo and keeps one per training', (discipline) => {
  expect(cardPhotoCount(discipline)).toBeGreaterThan(1);
  const key = '57000000-0000-0000-0001-000000000012';
  expect(cardPhoto(discipline, key)).toBe(cardPhoto(discipline, key));
});

test('different trainings spread over the photo set', () => {
  const keys = Array.from({ length: 30 }, (_, index) => `57000000-0000-0000-0001-${String(index).padStart(12, '0')}`);
  expect(new Set(keys.map((key) => cardPhoto('bike', key))).size).toBe(cardPhotoCount('bike'));
});
