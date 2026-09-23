import {
  act,
  fireEvent,
  render,
  waitFor,
  within,
} from '@testing-library/react-native';

import {
  createActivity,
  getCalendar,
  getOnboarding,
  listActivities,
  listPlannedExternalActivities,
  submitActivityRpeWithRefresh,
} from '../api/client';
import type { CompletedActivity, OnboardingState } from '../api/types';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { ActivityScreen } from './ActivityScreen';

jest.mock('../api/client', () => ({
  confirmActivityMatch: jest.fn(),
  createActivity: jest.fn(),
  getCalendar: jest.fn(),
  getOnboarding: jest.fn(),
  listActivities: jest.fn(),
  listPlannedExternalActivities: jest.fn(),
  submitActivityRpeWithRefresh: jest.fn(),
}));

const pending: CompletedActivity = {
  id: 'activity-id',
  planned_workout_id: null,
  discipline: 'run',
  source: 'canonical_summary',
  started_at: '2026-09-22T10:00:00Z',
  timezone: 'Europe/Amsterdam',
  duration_minutes: '45',
  distance_meters: null,
  elevation_gain_meters: null,
  rpe: null,
  rpe_submitted_at: null,
  match_status: 'unmatched',
  processing_state: 'awaiting_rpe',
  qualitative_result: 'awaiting_rpe',
  public_message: 'RPE nodig.',
  correction_proposal_id: null,
  metrics: null,
  created_at: '2026-09-22T10:45:00Z',
  updated_at: '2026-09-22T10:45:00Z',
};

describe('unplanned workout regression', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('an unplanned workout can be created and later completed with HR and textual RPE', async () => {
    let activities: CompletedActivity[] = [];
    jest.mocked(listActivities).mockImplementation(async () => activities);
    jest.mocked(getCalendar).mockResolvedValue({
      from_date: '2026-09-08',
      to_date: '2026-10-06',
      workouts: [],
      rest_days: [],
    });
    jest.mocked(listPlannedExternalActivities).mockResolvedValue([]);
    jest.mocked(getOnboarding).mockResolvedValue({
      profile: {
        timezone: 'Europe/Amsterdam',
        timezone_confirmed_at: '2026-09-01T00:00:00Z',
      },
    } as unknown as OnboardingState);
    jest.mocked(createActivity).mockImplementation(async () => {
      activities = [pending];
      return pending;
    });
    jest.mocked(submitActivityRpeWithRefresh).mockImplementation(async () => {
      const completed = {
        ...pending,
        rpe: 7,
        rpe_submitted_at: '2026-09-22T11:00:00Z',
        processing_state: 'complete',
        qualitative_result: 'unplanned',
      } as CompletedActivity;
      activities = [completed];
      return completed;
    });

    const screen = await render(
      <LanguageProvider>
        <ActivityScreen
          accessToken="athlete-token"
          onBack={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />
      </LanguageProvider>,
    );
    await screen.findByText('Record a workout');
    await fireEvent.press(
      screen.getByRole('button', { name: 'Save activity' }),
    );

    await waitFor(() =>
      expect(createActivity).toHaveBeenCalledWith(
        'athlete-token',
        expect.any(String),
        expect.not.objectContaining({ planned_workout_id: expect.anything() }),
      ),
    );
    const prompt = await screen.findByText('How hard did this workout feel?');
    const card = prompt.parent?.parent;
    expect(card).toBeTruthy();
    await fireEvent.changeText(
      within(card!).getByLabelText('Average heart rate (bpm)'),
      '151',
    );
    await fireEvent.press(
      within(card!).getByRole('radio', {
        name: 'Diepe ademhaling (10k wedstrijdtempo). (RPE 7)',
      }),
    );

    await waitFor(() =>
      expect(submitActivityRpeWithRefresh).toHaveBeenCalledWith(
        'athlete-token',
        pending,
        7,
        151,
      ),
    );
    expect(await screen.findByText('Extra workout')).toBeTruthy();
  });

  test('rapid repeated create taps keep one logical submission in flight', async () => {
    let resolveCreate: ((activity: CompletedActivity) => void) | undefined;
    jest.mocked(listActivities).mockResolvedValue([]);
    jest.mocked(getCalendar).mockResolvedValue({
      from_date: '2026-09-08',
      to_date: '2026-10-06',
      workouts: [],
      rest_days: [],
    });
    jest.mocked(listPlannedExternalActivities).mockResolvedValue([]);
    jest.mocked(getOnboarding).mockResolvedValue({
      profile: {
        timezone: 'Europe/Amsterdam',
        timezone_confirmed_at: '2026-09-01T00:00:00Z',
      },
    } as unknown as OnboardingState);
    jest.mocked(createActivity).mockImplementation(
      () =>
        new Promise<CompletedActivity>((resolve) => {
          resolveCreate = resolve;
        }),
    );

    const screen = await render(
      <LanguageProvider>
        <ActivityScreen
          accessToken="athlete-token"
          onBack={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />
      </LanguageProvider>,
    );
    const saveButton = await screen.findByRole('button', {
      name: 'Save activity',
    });
    await fireEvent.press(saveButton);
    await fireEvent.press(saveButton);

    expect(createActivity).toHaveBeenCalledTimes(1);
    await act(() => {
      resolveCreate?.(pending);
    });
    await waitFor(() => expect(listActivities).toHaveBeenCalledTimes(2));
  });
});
