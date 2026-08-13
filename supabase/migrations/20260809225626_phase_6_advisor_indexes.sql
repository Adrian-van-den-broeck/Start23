-- Cover every Phase 6 foreign-key lookup reported by the hosted database
-- advisor. Keep the constrained-column order so parent-row updates/deletes do
-- not require sequential scans of the referencing tables.

create index change_proposals_decision_actor_idx
on public.change_proposals (decision_actor);

create index plan_revisions_initial_request_owner_idx
on public.plan_revisions (initial_plan_request_id, athlete_id);

create index plan_revisions_plan_owner_idx
on public.plan_revisions (plan_id, athlete_id);

create index weekly_plans_active_revision_owner_idx
on public.weekly_plans (id, active_revision, athlete_id);

create index planned_workouts_revision_owner_idx
on public.planned_workouts (revision_id, athlete_id);

create index planned_workouts_plan_owner_idx
on public.planned_workouts (plan_id, athlete_id);

create index planned_workouts_template_idx
on public.planned_workouts (template_id);

create index plan_warnings_revision_owner_idx
on public.plan_warnings (revision_id, athlete_id);

create index plan_warnings_workout_owner_idx
on public.plan_warnings (planned_workout_id, athlete_id);
