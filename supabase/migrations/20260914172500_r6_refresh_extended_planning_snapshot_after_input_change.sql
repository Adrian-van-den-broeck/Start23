-- R6 runtime remediation: the Phase 8.5 wrapper is the function invoked by the
-- initial-plan snapshot trigger, so it must share the VOLATILE visibility of
-- the base builder when called from an input-row AFTER trigger.

alter function private.build_phase_8_5_planning_input_snapshot(uuid) volatile;

comment on function private.build_phase_8_5_planning_input_snapshot(uuid) is
  'Builds the current extended planning input snapshot, including mutations visible to row-trigger refreshes.';
