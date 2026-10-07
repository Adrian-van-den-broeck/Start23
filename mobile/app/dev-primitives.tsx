import { Redirect, useLocalSearchParams } from 'expo-router';
import { PrimitiveGallery, type ReviewSection } from '@/ui-v2/dev/PrimitiveGallery';

export default function DevPrimitivesRoute() {
  const params = useLocalSearchParams<{ language?: string; section?: string }>();
  if (!__DEV__) return <Redirect href="/" />;
  const language = params.language === 'nl' ? 'nl' : 'en';
  const section: ReviewSection = params.section === 'workout' || params.section === 'states' || params.section === 'notices'
    ? params.section : 'form';
  return <PrimitiveGallery language={language} section={section} />;
}
