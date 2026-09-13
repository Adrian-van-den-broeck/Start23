import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import {
  formatClockDuration,
  hasPartialObservedZoneTime,
  parseClockDuration,
  parsePositiveInteger,
  raceDisciplines,
} from './onboardingForms.ts';

test('all five race types map to their exact disciplines', () => {
  assert.deepEqual(raceDisciplines.run, ['run']);
  assert.deepEqual(raceDisciplines.bike, ['bike']);
  assert.deepEqual(raceDisciplines.swim, ['swim']);
  assert.deepEqual(raceDisciplines.triathlon, ['swim', 'bike', 'run']);
  assert.deepEqual(raceDisciplines.duathlon, ['bike', 'run']);
});

test('target durations and distances fail closed', () => {
  assert.equal(parseClockDuration('3:45:30'), 13_530);
  assert.equal(parseClockDuration('1:60'), null);
  assert.equal(parseClockDuration('0:00'), null);
  assert.equal(formatClockDuration(13_530), '3:45:30');
  assert.equal(parsePositiveInteger('10000'), 10_000);
  assert.equal(parsePositiveInteger('10.5'), null);
});

test('partial HR presentation uses observed minutes without extrapolation', () => {
  assert.equal(hasPartialObservedZoneTime('60', ['10', '20', '8', '3', '0']), true);
  assert.equal(hasPartialObservedZoneTime('41', ['10', '20', '8', '3', '0']), false);
  assert.equal(hasPartialObservedZoneTime(null, null), false);
});

const source = (relativePath: string): string =>
  readFileSync(new URL(relativePath, import.meta.url), 'utf8');

test('onboarding source keeps the R4 steps resumable and uses only current inputs', () => {
  const onboarding = source('../screens/OnboardingScreen.tsx');
  const client = source('../api/client.ts');

  assert.match(onboarding, /step === 'heart_rate_monitor'/);
  assert.match(onboarding, /heart_rate_monitor_confirmed: true/);
  assert.match(onboarding, /step === 'timezone'/);
  assert.match(onboarding, /timezone_confirmed: true/);
  assert.match(onboarding, /resolveDeviceTimezone/);
  assert.match(onboarding, /average_hours_per_week/);
  assert.doesNotMatch(onboarding, /function ZonesStep/);
  assert.equal(onboarding.match(/<ZoneSetupStep/g)?.length, 1);
  assert.doesNotMatch(client, /saveProfile[\s\S]{0,700}timezone:/);
});

test('structured race UI and client contain no obsolete generic goal write', () => {
  const onboarding = source('../screens/OnboardingScreen.tsx');
  const client = source('../api/client.ts');
  for (const raceType of ['run', 'bike', 'swim', 'triathlon', 'duathlon']) {
    assert.match(onboarding, new RegExp(`\\['${raceType}',`));
  }
  for (const field of [
    'race_type',
    'race_name',
    'race_date',
    'total_target_time_seconds',
  ]) {
    assert.match(client, new RegExp(`${field}:`));
  }
  const goalClient = client.slice(client.indexOf('export function savePrimaryGoal'));
  assert.doesNotMatch(goalClient.slice(0, 1_500), /specific_description|measurable_outcome|feasibility_score/);
  assert.match(onboarding, /Komt later/);
});

test('calibration source uses confirmed profile timezone and a separate activation path', () => {
  const calibration = source('../screens/CalibrationScreen.tsx');
  assert.match(calibration, /getOnboarding\(accessToken\)/);
  assert.match(calibration, /timezone_confirmed_at/);
  assert.doesNotMatch(calibration, /Intl\.DateTimeFormat/);
  assert.match(calibration, /currentSetups = protocolSetups\.filter/);
  assert.match(calibration, /average_heart_rate_bpm/);
  assert.match(calibration, /reported_block_rpe/);
  assert.match(calibration, /elapsed_time_seconds/);
  assert.match(calibration, /confirmCalibrationThreshold/);
  assert.match(calibration, /approveZoneProposal/);
  assert.match(calibration, /nooit automatisch een actief[\s\S]{0,40}zoneprofiel/);
});

test('activity correction and incomplete-measurement presentation fail closed', () => {
  const activity = source('../screens/ActivityScreen.tsx');
  const client = source('../api/client.ts');
  assert.match(client, /expected_current_rpe: expectedCurrentRpe/);
  assert.match(activity, /timezone_confirmed_at/);
  assert.doesNotMatch(activity, /resolvedOptions\(\)\.timeZone \|\| 'UTC'/);
  assert.doesNotMatch(activity, /onChangeText=\{setAthleteTimezone\}/);
  assert.match(activity, /activity\.duration_minutes === null/);
  assert.match(activity, /Distance recorded\. Duration and time in zone were not measured/);
  assert.match(activity, /Partial sensor coverage: only observed zone time was used/);
  assert.doesNotMatch(activity, /Number\(activity\.duration_minutes\)\s*\|\|\s*0/);
  assert.doesNotMatch(activity.toLowerCase(), /planned_tss|realized_tss/);
});
