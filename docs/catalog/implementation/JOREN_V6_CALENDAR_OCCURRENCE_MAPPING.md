# V6 calendar and immutable occurrence mapping

Branch `feat/joren-v6-mobile-lifecycle`; base `3d54615e6635cd662f5e3dfa246bedee924b9b06`.
Implementation f09941d405d25cdbb587b662fe1f5fe17c1c14eb. Local integration only.

| Identity | Authority and use |
| --- | --- |
| Plan ID + revision ID/number | Existing weekly plan/proposal contracts; explicit revision read on approval/recovery. |
| Logical workout `id` | `private.v6_occurrence_snapshots.occurrence_id`; stable across pending replacements, used by selection, pending edits and calendar rows. |
| `physical_workout_id` | Exact `planned_workout_id` in that revision; unique immutable row, used by activity FK and workout registration. |
| Template ID/key/version | Exact immutable source revision; never resolved by title, array index or workout-number suffix. |
| Scheduled date/status | Existing date-only snapshot and status lifecycle; wall rests remain source blocks, not independent workouts. |

Forward migration `20261108142454_inactive_v6_mobile_identity.sql` adds narrow
mobile read projections. It does not rewrite the old V6 read RPC, snapshots,
receipts, applied migration or any historical row. `get_v6_mobile_weekly_plan`
augments the existing owner-checked logical projection by exact revision and
occurrence mapping. `get_v6_mobile_calendar` uses the established calendar's
explicit owner/active-revision/date filters, then maps each physical row by its
primary key. Legacy rows pass through unchanged. Internal helpers have no public,
authenticated or service-role execute grant. Caller reads require the caller role;
the immutable edit-retry projection remains service only.

No pending revision appears in Calendar. `PlanningFlowProvider` continues to use
the identified active snapshot while another proposal is pending. Date-only range
end remains exclusive. Existing calendar tests cover UTC/local week rollover,
same-date siblings, rest records and retained ranges. V6 SQL and HTTP probes verify
pending exclusion, approved logical-ID equality, exact physical/revision mapping,
cross-owner denial and completed status after a supported activity. New Python
processes restore the confirmed state; this is not an app login/session test.

Replacing one pending workout keeps unrelated logical IDs, template revisions,
source blocks and manually selected dates. All physical rows are distinct in the
new revision, including retained occurrences. Retry projections map against the
receipt's original revision, preserving historical physical attachment.

## Active date change blocker

The existing `move_planned_workout` operation creates a legacy revision without
copying the V6 frozen source/context/occurrence mapping. It cannot be used to make
V6 moves reviewable and source-exact. The inactive service rejects this operation
with a safe public message before mutation. Supporting pending placement is not
evidence that confirmed moves work. An explicit V6 revision-preserving move path
and its concurrency/DB/device verification remain required. No immutable snapshot
guard or grants were weakened to make a move succeed.
