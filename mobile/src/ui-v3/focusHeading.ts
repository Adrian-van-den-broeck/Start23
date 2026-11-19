import { AccessibilityInfo, Platform, type View } from 'react-native';

export function focusHeading(view: View) {
  if (Platform.OS === 'web') view.focus();
  else AccessibilityInfo.sendAccessibilityEvent(view, 'focus');
}
