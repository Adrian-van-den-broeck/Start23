import { render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { weekHomeViewModel } from '../utils/weekHomeViewModel';
import { WeekContext } from './WeekContext';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));

test.each(['nl', 'en'] as const)('compact dates preserve same-month, cross-month and cross-year context in %s', async (language) => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  const locale = language === 'nl' ? 'nl-NL' : 'en-GB';
  for (const today of ['2026-10-12', '2026-09-28', '2026-12-28']) {
    const model = weekHomeViewModel({ plan: null, activePlan: null, draft: null, today, resumeState: 'ready', activeReadState: 'ready' });
    const view = await render(<LanguageProvider><WeekContext model={model} showStatus={false} /></LanguageProvider>);
    const range = view.getByTestId('week-range');
    const start = new Date(model.weekStart + 'T12:00:00');
    const end = new Date(model.weekEnd + 'T12:00:00');
    const full = (date: Date) => date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    expect(range.props.accessibilityLabel).toBe(`${full(start)} – ${full(end)}`);
    const visible = range.props.children as string;
    expect(visible).toContain(end.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' }));
    if (today === '2026-10-12') expect(visible).toMatch(/^12–18 /);
    if (today === '2026-09-28') expect(visible).toContain(start.toLocaleDateString(locale, { day: 'numeric', month: 'short' }));
    if (today === '2026-12-28') expect(visible).toContain('2026');
    expect(view.queryByText(language === 'nl' ? 'Nog geen week geladen' : 'No week loaded yet')).toBeNull();
    await view.unmount();
  }
});
