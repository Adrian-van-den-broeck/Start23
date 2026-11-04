-- Read local results only; every boolean must be true, both session receipts required.
begin transaction read only;
select (select count(*) from a5_release_probe.receipts)=2 as both_sessions_finished,
 (select result from a5_release_probe.receipts where session='A') =
 (select result from a5_release_probe.receipts where session='B') as exact_same_receipt,
 (select count(*) from public.plan_revisions where
 checkin_id='c0000000-0000-0000-0000-0000000000a5')=1 as exactly_one_revision,
 (select status='completed' and plan_proposal_id::text =
 (select result->>'proposal_id' from a5_release_probe.receipts where session='A')
 from public.weekly_checkins where id='c0000000-0000-0000-0000-0000000000a5') as exact_atomic_attachment;
rollback;
