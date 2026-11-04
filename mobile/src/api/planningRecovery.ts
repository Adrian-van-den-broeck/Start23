export class PlanningRecoveryEndpointUnavailableError extends Error {
  constructor() {
    super('Planning recovery is unavailable on this server.');
    this.name = 'PlanningRecoveryEndpointUnavailableError';
  }
}

export type PlanningRecoveryFailure = 'endpoint_unavailable' | 'unknown' | 'transient' | 'authentication' | 'authorization';

export function planningRecoveryFailure(error: unknown): PlanningRecoveryFailure {
  if (error instanceof PlanningRecoveryEndpointUnavailableError) return 'endpoint_unavailable';
  if (!error || typeof error !== 'object') return 'unknown';
  const status = 'status' in error ? error.status : undefined;
  const code = 'code' in error ? error.code : undefined;
  if (status === 401) return 'authentication';
  if (status === 403) return 'authorization';
  if (code === 'response_invalid' || code === 'response_unreadable' || code === 'request_cancelled') return 'unknown';
  if (status === null || status === 408 || status === 429 ||
      (typeof status === 'number' && status >= 500) || code === 'network_unavailable' || code === 'request_timeout') return 'transient';
  return 'unknown'; // Resource 404 and validation 422 cannot prove endpoint absence.
}

export function recoveryEndpointAbsent(schema: unknown): boolean {
  if (!schema || typeof schema !== 'object' || !('openapi' in schema) ||
      typeof schema.openapi !== 'string' || !schema.openapi.startsWith('3.') ||
      !('paths' in schema) || !schema.paths || typeof schema.paths !== 'object' || Array.isArray(schema.paths)) return false;
  const path = (schema.paths as Record<string, unknown>)['/api/v1/weekly-plans/recovery'];
  return path === undefined || (!!path && typeof path === 'object' && !('get' in path));
}
