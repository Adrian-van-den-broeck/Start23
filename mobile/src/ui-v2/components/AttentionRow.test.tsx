import { fireEvent, render } from '@testing-library/react-native';
import * as Native from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { colors } from '../tokens';
import { AttentionRow } from './AttentionRow';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
beforeEach(() => { jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });
afterEach(() => jest.restoreAllMocks());

test.each([{ width: 320, fontScale: 1 }, { width: 412, fontScale: 2 }])('attention stacks without dropping fact or action at $width dp / $fontScale text', async ({ width, fontScale }) => {
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width, height: 800, fontScale, scale: 1 });
  const action = jest.fn();
  const view = await render(<LanguageProvider><AttentionRow item={{ kind: 'warnings', action: 'review' }} disabled={false} onAction={action} /></LanguageProvider>);
  const row = Native.StyleSheet.flatten(view.getByTestId('week-attention-warnings').props.style);
  expect(row).toMatchObject({ flexDirection: 'column', backgroundColor: colors.warningSoft });
  expect(row.height).toBeUndefined();
  expect(view.getByText('Week needs attention').props.numberOfLines).toBeUndefined();
  await fireEvent.press(view.getByRole('button', { name: 'Review attention items' }));
  expect(action).toHaveBeenCalledWith('review');
});

test('ordinary pending remains neutral and respects the supplied lock', async () => {
  const action = jest.fn();
  const view = await render(<LanguageProvider><AttentionRow item={{ kind: 'proposal', action: 'review' }} disabled onAction={action} /></LanguageProvider>);
  expect(Native.StyleSheet.flatten(view.getByTestId('week-attention-proposal').props.style).backgroundColor).toBeUndefined();
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  expect(action).not.toHaveBeenCalled();
});
