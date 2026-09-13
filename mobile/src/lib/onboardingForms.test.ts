import {
  formatClockDuration,
  hasPartialObservedZoneTime,
  parseClockDuration,
  parsePositiveInteger,
  raceDisciplines,
  resolveDeviceTimezone,
} from './onboardingForms';

describe('onboarding form rules', () => {
  test('all five race types map to their exact disciplines', () => {
    expect(raceDisciplines.run).toEqual(['run']);
    expect(raceDisciplines.bike).toEqual(['bike']);
    expect(raceDisciplines.swim).toEqual(['swim']);
    expect(raceDisciplines.triathlon).toEqual(['swim', 'bike', 'run']);
    expect(raceDisciplines.duathlon).toEqual(['bike', 'run']);
  });

  test('target durations and distances fail closed', () => {
    expect(parseClockDuration('3:45:30')).toBe(13_530);
    expect(parseClockDuration('1:60')).toBeNull();
    expect(parseClockDuration('0:00')).toBeNull();
    expect(formatClockDuration(13_530)).toBe('3:45:30');
    expect(parsePositiveInteger('10000')).toBe(10_000);
    expect(parsePositiveInteger('10.5')).toBeNull();
  });

  test('partial HR presentation uses only observed minutes', () => {
    expect(hasPartialObservedZoneTime('60', ['10', '20', '8', '3', '0'])).toBe(
      true,
    );
    expect(hasPartialObservedZoneTime('41', ['10', '20', '8', '3', '0'])).toBe(
      false,
    );
    expect(hasPartialObservedZoneTime(null, null)).toBe(false);
  });

  test('device timezone detection fails closed without a valid IANA name', () => {
    const resolvedOptions = jest.spyOn(
      Intl.DateTimeFormat.prototype,
      'resolvedOptions',
    );
    resolvedOptions.mockReturnValue({
      timeZone: 'Europe/Amsterdam',
    } as Intl.ResolvedDateTimeFormatOptions);
    expect(resolveDeviceTimezone()).toBe('Europe/Amsterdam');
    resolvedOptions.mockReturnValue({
      timeZone: '',
    } as Intl.ResolvedDateTimeFormatOptions);
    expect(resolveDeviceTimezone()).toBeNull();
    resolvedOptions.mockRestore();
  });
});
