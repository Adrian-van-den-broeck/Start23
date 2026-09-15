-- R6 hosted-advisor remediation: add covering indexes for every foreign-key
-- access path reported by the Supabase performance advisor.

create index if not exists activity_loads_zone_profile_owner_idx
  on private.activity_loads (zone_profile_id, athlete_id);
create index if not exists activities_correction_proposal_owner_idx
  on public.activities (correction_proposal_id, athlete_id);
create index if not exists activities_planned_workout_owner_idx
  on public.activities (planned_workout_id, athlete_id);
create index if not exists activity_files_activity_owner_idx
  on public.activity_files (activity_id, athlete_id);
create index if not exists activity_rpe_revisions_activity_owner_idx
  on public.activity_rpe_revisions (activity_id, athlete_id);
create index if not exists calibration_decisions_base_zone_owner_idx
  on public.calibration_threshold_decisions (base_zone_profile_id, athlete_id);
create index if not exists calibration_decisions_zone_owner_idx
  on public.calibration_threshold_decisions (zone_profile_id, athlete_id);
create index if not exists calibration_decisions_proposal_idx
  on public.calibration_threshold_decisions (zone_proposal_id);
create index if not exists change_proposals_test_assignment_owner_idx
  on public.change_proposals (target_test_assignment_id, athlete_id);
create index if not exists discipline_assignments_plan_owner_idx
  on public.discipline_test_assignments (plan_id, athlete_id);
create index if not exists discipline_assignments_revision_owner_idx
  on public.discipline_test_assignments (target_plan_revision_id, athlete_id);
create index if not exists injury_restrictions_context_owner_idx
  on public.injury_restrictions (context_id, athlete_id);
create index if not exists plan_revisions_checkin_owner_idx
  on public.plan_revisions (checkin_id, athlete_id);
create index if not exists external_activities_completed_owner_idx
  on public.planned_external_activities (completed_activity_id, athlete_id);
create index if not exists external_activities_context_owner_idx
  on public.planned_external_activities (context_id, athlete_id);
create index if not exists swipe_week_drafts_current_template_idx
  on public.swipe_week_drafts (current_template_id);
create index if not exists swipe_week_drafts_request_owner_idx
  on public.swipe_week_drafts (initial_plan_request_id, athlete_id);
create index if not exists swipe_week_drafts_plan_owner_idx
  on public.swipe_week_drafts (plan_id, athlete_id);
create index if not exists swipe_week_drafts_proposal_owner_idx
  on public.swipe_week_drafts (proposal_id, athlete_id);
create index if not exists weekly_checkin_contexts_checkin_owner_idx
  on public.weekly_checkin_contexts (checkin_id, athlete_id);
create index if not exists weekly_checkins_proposal_owner_idx
  on public.weekly_checkins (plan_proposal_id, athlete_id);
create index if not exists zone_boundaries_profile_owner_idx
  on public.zone_boundaries (zone_profile_id, athlete_id);
create index if not exists zone_metrics_profile_owner_idx
  on public.zone_metrics (zone_profile_id, athlete_id);
create index if not exists zone_profiles_evaluation_owner_idx
  on public.zone_profile_versions (calibration_evaluation_id, athlete_id);
