import { Redirect, type Href } from 'expo-router';

export default function CalibrationRoute() {
  return <Redirect href={'/tests' as Href} />;
}
