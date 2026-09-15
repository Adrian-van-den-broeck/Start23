-- R6 runtime remediation: planning snapshots refreshed from row triggers must
-- observe the input row mutation performed by the current statement.
--
-- STABLE functions execute against the calling statement's initial snapshot,
-- which caused an AFTER UPDATE trigger on goals to rebuild a pending planning
-- request from the previous goal revision. VOLATILE gives each triggered call
-- a current command snapshot while preserving the function's read-only body.

alter function private.build_planning_input_snapshot(uuid) volatile;

comment on function private.build_planning_input_snapshot(uuid) is
  'Builds the current planning input snapshot, including mutations visible to row-trigger refreshes.';
