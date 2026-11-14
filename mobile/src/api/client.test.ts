import { approvedNext, nextProposal, pendingNext } from '../features/planning/planningTask.test-fixtures';
import { activePlan, draft } from '../features/planning/planning.test-fixtures';

const API_URL = 'https://api.start23.test';

function successfulFetch(): jest.MockedFunction<typeof fetch> {
  return jest.fn(async (input: URL | RequestInfo, _init?: RequestInit) => ({
    ok: true,
    status: 200,
    json: async () => String(input).endsWith('/swipe-drafts') ? draft
      : String(input).includes('/activities/') ? activityResponse(6, 148)
      : String(input).includes('/planned-workouts/') ? activePlan : {},
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

test('frequency preference transport carries exact revision and logical save without an owner override', async () => {
  const { client, fetchMock } = loadClient();
  const saved = { revision: 1, operation_id: 'operation-a', preferences: { run: 0, bike: 2, swim: null },
    confirmed_at: '2026-11-13T12:00:00Z', recorded_at: '2026-11-13T12:00:00Z', reconfirmation_required: [] };
  fetchMock.mockResolvedValueOnce(response(200, saved)).mockResolvedValueOnce(response(200, saved));
  await expect(client.getFrequencyPreferences('athlete-token')).resolves.toEqual(saved);
  const input = { expected_revision: 0, operation_id: 'operation-a', preferences: saved.preferences };
  await expect(client.saveFrequencyPreferences('athlete-token', input)).resolves.toEqual(saved);
  expect(fetchMock.mock.calls[0][0]).toBe(`${API_URL}/api/v1/me/frequency-preferences`);
  expect(fetchMock.mock.calls[1][1]).toMatchObject({ headers, method: 'PUT', body: JSON.stringify(input) });
});

test('incomplete frequency search has different copy from an infeasible proposal and never retries automatically', async () => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(409, { error: { code: 'v6_search_incomplete', message: 'private server diagnostic' } }));
  await expect(client.createCheckInPlanProposal('athlete-token', 'checkin-a')).rejects.toMatchObject({
    code: 'v6_search_incomplete', message: 'Het weekvoorstel kon niet volledig worden berekend. Er is geen nieuw voorstel opgeslagen. Pas je voorkeur aan of vraag ondersteuning.',
  });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test('an exhaustively infeasible selection does not claim an incomplete search', async () => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(409, { error: { code: 'v6_selection_invalid' } }));
  await expect(client.createCheckInPlanProposal('athlete-token', 'checkin-a')).rejects.toMatchObject({
    code: 'v6_selection_invalid', message: 'Er is geen passend weekvoorstel binnen de huidige keuzes en trainingsvoorwaarden. Controleer je beschikbare dagen en voorkeur.',
  });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test('A5 additive incomplete discriminator keeps the legacy rejection contract and never retries', async () => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(422, { error: {
    code: 'validation_failed', message: 'private diagnostic must never be shown',
    details: { planning_code: 'v6_search_incomplete', frozen_context: 'private' },
  } }));
  const error = await client.createCheckInPlanProposal('athlete-token', 'checkin-a').catch(e => e);
  expect(error).toMatchObject({ status: 422, code: 'validation_failed', outcome: 'rejected',
    message: 'Het weekvoorstel kon niet volledig worden berekend. Er is geen nieuw voorstel opgeslagen. Pas je voorkeur aan of vraag ondersteuning.',
    retryable: false,
  });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(JSON.stringify(error)).not.toContain('private');
});

test('A4 check-in generation, explicit approval receipt and exact revision read preserve the public wire contracts', async () => {
  const { client, fetchMock } = loadClient();
  const receipt = { state: 'applied', plan_id: pendingNext.id, active_revision: 1 };
  fetchMock.mockResolvedValueOnce(response(200, { plan: pendingNext, proposal: nextProposal }))
    .mockResolvedValueOnce(response(200, receipt)).mockResolvedValueOnce(response(200, approvedNext));
  const generated = await client.createCheckInPlanProposal('athlete-token', 'check-in-a');
  expect(generated.plan).toEqual(pendingNext);
  const applied = await client.approvePlanProposal('athlete-token', generated.proposal.id, generated.proposal.base_plan_revision!);
  expect(applied).toEqual(receipt);
  await expect(client.getWeeklyPlan('athlete-token', applied.plan_id, applied.active_revision)).resolves.toEqual(approvedNext);
  expect(fetchMock.mock.calls.map(call => call[0])).toEqual([
    `${API_URL}/api/v1/checkins/check-in-a/plan-proposals`,
    `${API_URL}/api/v1/change-proposals/next-proposal/approve`,
    `${API_URL}/api/v1/weekly-plans/next-plan?revision=1`,
  ]);
  for (const call of fetchMock.mock.calls) expect(call[1]?.headers).toEqual(headers);
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: 'POST' });
  expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST', body: JSON.stringify({ expected_base_revision: 0 }) });
  expect(fetchMock.mock.calls[2][1]?.body).toBeUndefined();
});

test('active injury restrictions use the existing token-scoped GET contract', async () => {
  const { client, fetchMock } = loadClient();
  const supplied: import('./types').InjuryRestriction[] = [{ id: 'restriction-a', discipline: 'run', status: 'professional_restricted', allowed_intensity: 'none', source: 'physician', athlete_plan_choice: 'keep_blocked', start_at: '2026-10-01T12:00:00Z', review_at: '2026-10-08T12:00:00Z', confirmed_at: '2026-10-01T12:00:00Z', professional_advice: 'Synthetic advice', professional_advice_at: '2026-10-01T12:00:00Z', cleared_at: null }];
  fetchMock.mockResolvedValueOnce(response(200, supplied));
  await expect(client.getInjuryRestrictions('athlete-token')).resolves.toEqual(supplied);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toBe(`${API_URL}/api/v1/me/injury-restrictions`);
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ headers });
  expect(fetchMock.mock.calls[0][1]?.body).toBeUndefined();
});

function activityResponse(rpe: number | null, averageHeartRate = 151) {
  return {
    id: 'activity-id',
    planned_workout_id: null,
    discipline: 'run' as const,
    source: 'canonical_summary' as const,
    started_at: '2026-09-22T10:00:00Z',
    timezone: 'Europe/Amsterdam',
    duration_minutes: '45',
    distance_meters: null,
    elevation_gain_meters: null,
    rpe,
    rpe_submitted_at: rpe === null ? null : '2026-09-22T11:00:00Z',
    match_status: 'unmatched' as const,
    processing_state: rpe === null ? ('awaiting_rpe' as const) : ('complete' as const),
    qualitative_result: rpe === null ? ('awaiting_rpe' as const) : ('unplanned' as const),
    public_message: rpe === null ? 'RPE needed.' : 'Saved.',
    correction_proposal_id: null,
    metrics:
      rpe === null
        ? null
        : {
            average_heart_rate_bpm: averageHeartRate,
            max_heart_rate_bpm: null,
            normalized_power_watts: null,
            average_speed_kmh: null,
            max_speed_kmh: null,
            average_pace_seconds_per_km: null,
            zone_minutes: null,
            low_intensity_minutes: null,
            high_intensity_minutes: null,
          },
    created_at: '2026-09-22T10:45:00Z',
    updated_at: '2026-09-22T11:00:00Z',
  };
}

function response(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe('mobile API transport contracts', () => {
  test('maps impossible planner failures to actionable Dutch copy without private load', async () => {
    const { client, fetchMock } = loadClient();
    const publicMessage =
      'Deze trainingscombinatie past niet veilig op de gekozen dagen. Kies extra beschikbare dagen, liefst verder uit elkaar, of kies een andere training.';
    fetchMock.mockResolvedValueOnce(
      response(409, {
        error: {
          code: 'rest_or_anti_stack_unsatisfied',
          message:
            'The generated schedule cannot satisfy rest-day and anti-stack constraints.',
        },
      }),
    );

    await expect(
      client.createSwipeWeekDraft('athlete-token', {
        week_start: '2026-09-28',
        available_dates: ['2026-09-28'],
        confirmed_injuries: [],
      }),
    ).rejects.toMatchObject({
      code: 'rest_or_anti_stack_unsatisfied',
      message: publicMessage,
    });

    expect(publicMessage.toLowerCase()).not.toContain('tss');
    expect(publicMessage.toLowerCase()).not.toContain('load');
  });

  test('explains catalog capacity failure without exposing private load', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce(
      response(409, {
        error: {
          code: 'catalog_capacity_unsatisfied',
          message: 'The reviewed automatic workout catalog cannot cover this week.',
        },
      }),
    );

    await expect(
      client.createSwipeWeekDraft('athlete-token', {
        week_start: '2026-09-28',
        available_dates: ['2026-09-28'],
        confirmed_injuries: [],
      }),
    ).rejects.toMatchObject({
      code: 'catalog_capacity_unsatisfied',
      message: expect.stringContaining('beoordeeld trainingsvoorstel'),
    });
  });

  test('sends October Monday/Wednesday/Saturday as local dates with the v2 contract', async () => {
    const { client, fetchMock } = loadClient();
    const input = {
      week_start: '2026-10-05',
      available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
      confirmed_injuries: [] as Array<'run'>,
      cross_training_opt_ins: [] as Array<'bike'>,
    };

    await client.createSwipeWeekDraft('athlete-token', input);

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/api/v1/weekly-plans/swipe-drafts`,
      {
        method: 'POST',
        body: JSON.stringify(input),
        headers,
        signal: expect.anything(),
      },
    );
  });

  test('reports a stale server request contract instead of blaming athlete fields', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce(
      response(422, {
        error: {
          code: 'validation_failed',
          details: {
            violations: [
              { location: ['body', 'cross_training_opt_ins'], type: 'extra_forbidden' },
            ],
          },
        },
      }),
    );

    await expect(
      client.createSwipeWeekDraft('athlete-token', {
        week_start: '2026-10-05',
        available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
        confirmed_injuries: [],
        cross_training_opt_ins: [],
      }),
    ).rejects.toMatchObject({
      code: 'validation_failed',
      message: expect.stringContaining('verschillende versies'),
    });
  });

  test('explains recoverable swipe feasibility without a field-validation message', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce(
      response(409, {
        error: { code: 'swipe_draft_no_completion' },
      }),
    );

    await expect(
      client.createSwipeWeekDraft('athlete-token', {
        week_start: '2026-10-05',
        available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
        confirmed_injuries: [],
        cross_training_opt_ins: [],
      }),
    ).rejects.toMatchObject({
      code: 'swipe_draft_no_completion',
      message: expect.stringContaining('Kies extra beschikbare dagen'),
    });
  });

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
        signal: expect.anything(),
      },
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `${API_URL}/api/v1/me/identifying-profile`,
      {
        method: 'PATCH',
        body: JSON.stringify({ first_name: 'Ada', last_name: 'Lovelace' }),
        headers,
        signal: expect.anything(),
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
      message:
        'De gemiddelde hartslag kan niet meer worden gewijzigd nadat deze training is verwerkt.',
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
        signal: expect.anything(),
      },
    );
  });

  test('normal RPE save succeeds without refresh', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce(response(200, activityResponse(6)));

    await expect(
      client.submitActivityRpeWithRefresh(
        'athlete-token',
        activityResponse(null),
        6,
        151,
      ),
    ).resolves.toMatchObject({ rpe: 6 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test('safe stale-state refresh retries once with the refreshed precondition', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock
      .mockResolvedValueOnce(
        response(409, {
          error: {
            code: 'activity_state_conflict',
            message: 'The activity state changed.',
          },
        }),
      )
      .mockResolvedValueOnce(
        response(200, {
          ...activityResponse(5),
          planned_workout_id: 'newly-confirmed-workout-id',
        }),
      )
      .mockResolvedValueOnce(response(200, activityResponse(6)));

    await expect(
      client.submitActivityRpeWithRefresh(
        'athlete-token',
        activityResponse(5),
        6,
        151,
      ),
    ).resolves.toMatchObject({ rpe: 6 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({
        rpe: 6,
        expected_current_rpe: 5,
        average_heart_rate_bpm: 151,
      }),
    );
  });

  test('genuine stale RPE edit fails without overwriting newer state', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock
      .mockResolvedValueOnce(
        response(409, {
          error: {
            code: 'activity_correction_stale',
            message: 'The activity correction is stale.',
          },
        }),
      )
      .mockResolvedValueOnce(response(200, activityResponse(7)));

    await expect(
      client.submitActivityRpeWithRefresh(
        'athlete-token',
        activityResponse(5),
        6,
        151,
      ),
    ).rejects.toMatchObject({
      code: 'activity_correction_stale',
      status: 409,
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  test('lost identical RPE response resolves from refreshed server state', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock
      .mockRejectedValueOnce(new TypeError('connection closed'))
      .mockResolvedValueOnce(response(200, activityResponse(6)));

    await expect(
      client.submitActivityRpeWithRefresh(
        'athlete-token',
        activityResponse(null),
        6,
        151,
      ),
    ).resolves.toMatchObject({ rpe: 6 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  test('same-week move uses the exact revision-safe server contract', async () => {
    const { client, fetchMock } = loadClient();

    await client.validatePlanLayout('athlete-token', 'plan-id', 4, [
      { workout_id: 'workout-id', scheduled_date: '2026-09-23' },
    ]);
    await client.movePlannedWorkout(
      'athlete-token',
      'workout-id',
      4,
      '2026-09-23',
    );

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `${API_URL}/api/v1/weekly-plans/plan-id/validate`,
      {
        method: 'POST',
        body: JSON.stringify({
          expected_revision: 4,
          workouts: [
            { workout_id: 'workout-id', scheduled_date: '2026-09-23' },
          ],
        }),
        headers,
        signal: expect.anything(),
      },
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `${API_URL}/api/v1/planned-workouts/workout-id`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          expected_revision: 4,
          scheduled_date: '2026-09-23',
        }),
        headers,
        signal: expect.anything(),
      },
    );
  });

  test('stale-revision move fails safely without a retry', async () => {
    const { client, fetchMock } = loadClient();
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({
        error: {
          code: 'plan_revision_stale',
          message: 'The plan changed after this calendar edit was prepared.',
        },
      }),
    } as Response);

    await expect(
      client.movePlannedWorkout(
        'athlete-token',
        'workout-id',
        4,
        '2026-09-23',
      ),
    ).rejects.toMatchObject({
      code: 'plan_revision_stale',
      retryable: false,
      status: 409,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});


test('A6 discovery sends only the bearer token and no client owner or mutation body', async () => {
  const { client, fetchMock } = loadClient();
  const found = { active: approvedNext, pending: pendingNext, draft: null };
  fetchMock.mockResolvedValueOnce(response(200, found));
  await expect(client.discoverPlanning('athlete-token')).resolves.toEqual(found);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toBe(`${API_URL}/api/v1/weekly-plans/recovery`);
  expect(fetchMock.mock.calls[0][1]?.headers).toEqual(headers);
  expect(fetchMock.mock.calls[0][1]?.body).toBeUndefined();
  expect(fetchMock.mock.calls[0][1]?.method).toBeUndefined();
});


test('A7 targeted activity resolution uses the existing owner-token GET with no identity override', async () => {
  const { client, fetchMock } = loadClient();
  const id = '6a8c2a77-1d7f-4c88-bdc4-0d2ad4b08010';
  fetchMock.mockResolvedValueOnce(response(200, { ...activityResponse(null), id }));
  await client.getActivity('athlete-token', id);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toBe(`${API_URL}/api/v1/activities/${id}`);
  expect(fetchMock.mock.calls[0][1]?.headers).toEqual(headers);
  expect(fetchMock.mock.calls[0][1]?.body).toBeUndefined();
});
