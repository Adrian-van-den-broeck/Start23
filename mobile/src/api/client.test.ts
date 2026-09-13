const API_URL = 'https://api.start23.test';

function successfulFetch(): jest.MockedFunction<typeof fetch> {
  return jest.fn(async (_input: URL | RequestInfo, _init?: RequestInit) => ({
    ok: true,
    status: 200,
    json: async () => ({}),
  } as Response));
}

function loadClient() {
  process.env.EXPO_PUBLIC_API_BASE_URL = API_URL;
  jest.resetModules();
  const fetchMock = successfulFetch();
  global.fetch = fetchMock;
  const client = jest.requireActual('./client') as typeof import('./client');
  return { client, fetchMock };
}

const headers = {
  Accept: 'application/json',
  Authorization: 'Bearer athlete-token',
  'Content-Type': 'application/json',
};

describe('mobile API transport contracts', () => {
  test('profile save serializes only the two separated mutation contracts', async () => {
    const { client, fetchMock } = loadClient();

    await client.saveProfile('athlete-token', {
      first_name: 'Ada',
      last_name: 'Lovelace',
      date_of_birth: '1990-05-20',
      resting_heart_rate_bpm: 52,
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `${API_URL}/api/v1/me/physiology-profile`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          date_of_birth: '1990-05-20',
          resting_heart_rate_bpm: 52,
        }),
        headers,
      },
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `${API_URL}/api/v1/me/identifying-profile`,
      {
        method: 'PATCH',
        body: JSON.stringify({ first_name: 'Ada', last_name: 'Lovelace' }),
        headers,
      },
    );
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).endsWith('/me/profile')),
    ).toBe(false);
  });

  test('timezone, race, and race-required zone requests are exact', async () => {
    const { client, fetchMock } = loadClient();

    await client.saveOperationalProfile('athlete-token', {
      timezone: 'Europe/Amsterdam',
      timezone_source: 'device',
      timezone_confirmed: true,
    });
    await client.savePrimaryGoal('athlete-token', {
      race_type: 'duathlon',
      race_name: 'Duo',
      race_date: '2099-06-15',
      bike_distance_meters: 40000,
      run_distance_meters: 10000,
      total_target_time_seconds: 10800,
    });
    await client.getZoneSetupOptions('athlete-token', 'bike');

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `${API_URL}/api/v1/me/operational-profile`,
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: 'PATCH',
      body: JSON.stringify({
        timezone: 'Europe/Amsterdam',
        timezone_source: 'device',
        timezone_confirmed: true,
      }),
    });
    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API_URL}/api/v1/me/goals`);
    expect(fetchMock.mock.calls[1]?.[1]).toMatchObject({
      method: 'POST',
      body: JSON.stringify({
        race_type: 'duathlon',
        race_name: 'Duo',
        race_date: '2099-06-15',
        bike_distance_meters: 40000,
        run_distance_meters: 10000,
        total_target_time_seconds: 10800,
      }),
    });
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      `${API_URL}/api/v1/onboarding/zone-options/bike`,
    );
  });

  test('calibration confirmation and RPE correction preserve exact payloads', async () => {
    const { client, fetchMock } = loadClient();
    const observation = {
      activity_id: 'activity-id',
      protocol_id: 'start23_week1_run_calibration_v1',
      discipline: 'run' as const,
      segment_id: 'comfortable_20min',
      performed_at: '2099-06-15T10:00:00+02:00',
      completed: true,
      interrupted: false,
      quality_status: 'sufficient' as const,
      target_rpe: 4,
      reported_block_rpe: 4,
      average_heart_rate_bpm: '148',
    };

    await client.saveDisciplineSetup('athlete-token', 'run', {
      setup_route: 'calibration_week',
      guidance_mode: 'heart_rate',
    });
    await client.saveCalibrationObservation('athlete-token', observation);
    await client.evaluateCalibration(
      'athlete-token',
      'activity-id',
      'start23_week1_run_calibration_v1',
    );
    await client.confirmCalibrationThreshold('athlete-token', 'evaluation-id');
    await client.submitActivityRpe('athlete-token', 'activity-id', 6, 148, 5);

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `${API_URL}/api/v1/onboarding/disciplines/run/setup`,
      `${API_URL}/api/v1/calibration/observations`,
      `${API_URL}/api/v1/calibration/evaluate`,
      `${API_URL}/api/v1/calibration/evaluations/evaluation-id/threshold/confirm`,
      `${API_URL}/api/v1/activities/activity-id/rpe`,
    ]);
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(
      JSON.stringify({
        setup_route: 'calibration_week',
        guidance_mode: 'heart_rate',
      }),
    );
    expect(fetchMock.mock.calls[1]?.[1]?.body).toBe(JSON.stringify(observation));
    expect(fetchMock.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({
        activity_id: 'activity-id',
        protocol_id: 'start23_week1_run_calibration_v1',
      }),
    );
    expect(fetchMock.mock.calls[3]?.[1]?.body).toBe(
      JSON.stringify({ confirmed: true }),
    );
    expect(fetchMock.mock.calls[4]?.[1]?.body).toBe(
      JSON.stringify({
        rpe: 6,
        expected_current_rpe: 5,
        average_heart_rate_bpm: 148,
      }),
    );
  });

  test('changed average HR is surfaced as a non-retryable correction rejection', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({
        error: {
          code: 'average_heart_rate_immutable',
          message: 'Average heart rate cannot change after load calculation.',
        },
      }),
    } as Response);

    await expect(
      client.submitActivityRpe('athlete-token', 'activity-id', 6, 151, 5),
    ).rejects.toMatchObject({
      message: 'Average heart rate cannot change after load calculation.',
      status: 409,
      code: 'average_heart_rate_immutable',
      retryable: false,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/api/v1/activities/activity-id/rpe`,
      {
        method: 'PUT',
        body: JSON.stringify({
          rpe: 6,
          expected_current_rpe: 5,
          average_heart_rate_bpm: 151,
        }),
        headers,
      },
    );
  });
});
