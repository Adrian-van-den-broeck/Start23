import ArrowLeft from 'lucide-react-native/icons/arrow-left';
import ArrowRight from 'lucide-react-native/icons/arrow-right';
import Calendar from 'lucide-react-native/icons/calendar';
import CalendarDays from 'lucide-react-native/icons/calendar-days';
import ChartNoAxesColumnIncreasing from 'lucide-react-native/icons/chart-no-axes-column-increasing';
import Check from 'lucide-react-native/icons/check';
import ChevronLeft from 'lucide-react-native/icons/chevron-left';
import ChevronRight from 'lucide-react-native/icons/chevron-right';
import Clock from 'lucide-react-native/icons/clock';
import FileText from 'lucide-react-native/icons/file-text';
import Flag from 'lucide-react-native/icons/flag';
import HeartPulse from 'lucide-react-native/icons/heart-pulse';
import Info from 'lucide-react-native/icons/info';
import List from 'lucide-react-native/icons/list';
import LogOut from 'lucide-react-native/icons/log-out';
import MapPin from 'lucide-react-native/icons/map-pin';
import Minus from 'lucide-react-native/icons/minus';
import Plus from 'lucide-react-native/icons/plus';
import RefreshCw from 'lucide-react-native/icons/refresh-cw';
import TriangleAlert from 'lucide-react-native/icons/triangle-alert';
import Undo2 from 'lucide-react-native/icons/undo-2';
import UserRound from 'lucide-react-native/icons/user-round';
import X from 'lucide-react-native/icons/x';
import { View } from 'react-native';

import { assetColors } from '../assets/assetColors';
import { BikeVector, RunVector, SwimVector } from '../assets/SportVectors';

// Only these statically imported components are reachable. No icon-set lookup,
// dynamic import, emoji, font glyphs or athlete-state decisions belong here.
const glyphs = {
  profile: UserRound,
  back: ArrowLeft,
  forward: ArrowRight,
  chevron: ChevronRight,
  chevronLeft: ChevronLeft,
  week: CalendarDays,
  calendar: Calendar,
  activities: ChartNoAxesColumnIncreasing,
  intensity: ChartNoAxesColumnIncreasing,
  run: RunVector,
  bike: BikeVector,
  swim: SwimVector,
  clock: Clock,
  heartRate: HeartPulse,
  document: FileText,
  info: Info,
  warning: TriangleAlert,
  location: MapPin,
  undo: Undo2,
  list: List,
  add: Plus,
  minus: Minus,
  logout: LogOut,
  goal: Flag,
  check: Check,
  close: X,
  refresh: RefreshCw,
} as const;

export type IconName = keyof typeof glyphs;
export type IconSize = 20 | 24 | 32;
export const iconNames = Object.keys(glyphs) as IconName[];

export type IconProps = {
  name: IconName;
  size?: IconSize;
  color?: string;
} & (
  | { decorative?: true; accessibilityLabel?: never }
  | { decorative: false; accessibilityLabel: string }
);

export function Icon({ name, size = 24, color = assetColors.forest, decorative = true, accessibilityLabel }: IconProps) {
  const Glyph = glyphs[name];
  return (
    <View
      accessible={!decorative}
      accessibilityRole={decorative ? undefined : 'image'}
      accessibilityLabel={accessibilityLabel}
      accessibilityElementsHidden={decorative}
      importantForAccessibility={decorative ? 'no-hide-descendants' : 'yes'}
      pointerEvents="none"
      style={{ width: size, height: size }}
    >
      <Glyph size={size} color={color} strokeWidth={2} accessible={false} />
    </View>
  );
}
