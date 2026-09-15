-- Phase 14 v2 completion stores monitor and timezone confirmation as completed
-- steps. Expand the immutable history vocabulary without rewriting old rows.
alter table public.onboarding_completion_records
  drop constraint onboarding_completion_records_steps_valid;
alter table public.onboarding_completion_records
  add constraint onboarding_completion_records_steps_valid check (
    completed_steps <@ array[
      'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones', 'review'
    ]::text[]
  );
