import { listActivities, submitActivityRpeWithRefresh } from '../../../mobile/src/api/client';
import { pendingActivity } from '../../../mobile/src/features/activities/activities.test-fixtures';

beforeEach(() => { process.env.EXPO_PUBLIC_API_BASE_URL = 'https://synthetic.invalid'; });
afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

test('AUD-010: a hung fetch has no application timeout even after five minutes', async () => {
  jest.useFakeTimers();
  jest.spyOn(global, 'fetch').mockImplementation(() => new Promise(() => undefined));
  let settled = false;
  void listActivities('synthetic-token').finally(() => { settled = true; });
  await jest.advanceTimersByTimeAsync(300000);
  expect(settled).toBe(false);
  expect(global.fetch).toHaveBeenCalledWith(expect.any(String), expect.not.objectContaining({ signal: expect.anything() }));
});

test('AUD-011: malformed JSON after RPE write bypasses committed-write recovery', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({ ok: true, status: 200, json: async () => { throw new SyntaxError('truncated response'); } } as unknown as Response);
  await expect(submitActivityRpeWithRefresh('synthetic-token', pendingActivity, 4)).rejects.toThrow('truncated response');
  expect(global.fetch).toHaveBeenCalledTimes(1);
});
