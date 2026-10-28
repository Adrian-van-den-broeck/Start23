import { writeFileSync } from 'fs';

test('overlapping owner onboarding reads through the actual A8 transport', async () => {
  process.env.EXPO_PUBLIC_API_BASE_URL = 'https://synthetic.local';
  jest.resetModules();
  const client: typeof import('./client') = require('./client');
  const original = global.fetch;
  const measurements: { milliseconds: number; requests: number }[] = [];
  try {
    for (let run = 0; run < 5; run++) {
      const fetchMock = jest.fn(async () => {
        await new Promise(resolve => setTimeout(resolve, 40));
        return { ok: true, status: 200, json: async () => ({ current_step: 'completed' }) } as Response;
      });
      global.fetch = fetchMock;
      const start = performance.now();
      await Promise.all([client.getOnboarding('synthetic-a'), client.getOnboarding('synthetic-a')]);
      measurements.push({ milliseconds: performance.now() - start, requests: fetchMock.mock.calls.length });
    }
    writeFileSync(process.env.A9_READ_BENCH_OUTPUT!, JSON.stringify({ environment: 'Actual client/deadline/controller integration, synthetic 40 ms fetch, development Jest; no device latency', measurements }, null, 2));
  } finally { global.fetch = original; }
});
