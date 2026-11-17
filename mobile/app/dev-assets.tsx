import { Redirect } from 'expo-router';

import { AssetGallery } from '@/ui-v2/dev/AssetGallery';

// Direct development deep link only. No production or training navigation link.
export default function DevAssetsRoute() {
  if (!__DEV__) return <Redirect href="/" />;
  return <AssetGallery />;
}
