-- While Session A sleeps and Session B is waiting, this must return true.
-- If false/not observed, identical replay alone is NOT concurrency proof.
begin transaction read only;
select exists(
  select 1 from pg_stat_activity
  where application_name = 'wombo_a5_session_b' and wait_event_type = 'Lock'
) as session_b_observed_waiting_on_lock;
rollback;
