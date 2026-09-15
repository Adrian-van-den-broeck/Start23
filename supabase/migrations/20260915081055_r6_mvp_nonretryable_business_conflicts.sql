-- MVP business conflicts are terminal HTTP 409 responses, not PostgreSQL
-- serialization failures. Preserve function signatures, ownership, grants,
-- security mode, search_path, and all state/owner preconditions.
-- Explicit names include active compatibility implementations called by MVP
-- wrappers. Optional provider import/webhook/retry functions are out of scope.
do $migration$
declare
  v_function record;
  v_definition text;
  v_count integer := 0;
begin
  for v_function in
    select p.oid, p.proname
    from pg_catalog.pg_proc p
    join pg_catalog.pg_namespace n on n.oid = p.pronamespace
    where n.nspname in ('public', 'private') and p.prokind = 'f'
      and p.proname = any(array[
        'approve_plan_proposal', 'approve_validation_test_proposal',
        'approve_zone_proposal', 'attach_checkin_plan_proposal',
        'complete_activity_rpe', 'complete_current_onboarding',
        'confirm_activity_planned_workout_match', 'confirm_weekly_checkin_context',
        'create_activity_summary', 'create_activity_summary_r6_pre_idempotency',
        'create_external_activity_summary', 'create_validation_test_proposal',
        'create_weekly_plan_proposal', 'create_weekly_plan_proposal_v2_legacy',
        'get_checkin_context_for_planning', 'move_planned_workout_legacy',
        'protect_phase_13_average_hr_observation', 'reject_plan_proposal',
        'reject_validation_test_proposal', 'reject_zone_proposal',
        'require_integrated_test_assignment_before_plan_apply',
        'revise_activity_rpe', 'revise_activity_rpe_r5_base',
        'save_calibration_observation', 'save_integrated_test_assignment',
        'save_measured_calculated_zone_profile', 'save_weekly_checkin_context',
        'update_swipe_week_draft'
      ])
      and p.prosrc like '%40001%'
    order by n.nspname, p.proname
  loop
    v_definition := pg_catalog.pg_get_functiondef(v_function.oid);
    -- Only deliberate literal RAISE codes change. Genuine engine failures
    -- continue to propagate as 40001; no exception handler translates them.
    v_definition := replace(v_definition, 'errcode = ''40001''', 'errcode = ''PT409''');
    if v_definition like '%errcode = ''40001''%' then
      raise exception 'unconverted business conflict in %', v_function.proname;
    end if;
    execute v_definition;
    v_count := v_count + 1;
  end loop;
  if v_count <> 28 then
    raise exception 'MVP conflict inventory mismatch: expected 28, found %', v_count;
  end if;
end;
$migration$;

notify pgrst, 'reload schema';
