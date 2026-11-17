# Exact proposal for owner approval

Ordinary `authenticated EXECUTE` only, exactly these 13 signatures. No anonymous exception, grant option, private-table grant, generated-plan writer, reviewer enrolment or test-executor membership. Ownership comes from verified JWT identity, not a client-selected owner.

| Group | Exact signature | Why required; boundary retained |
| --- | --- | --- |
| G1 | `public.get_checkin_plan_proposal(uuid)` | Recover the owner's exact A5 attachment/revision and terminal retry through invoker RLS. |
| G2 | `public.create_activity_summary_v2(uuid,text,jsonb)` | Submit the owner's explicit V2 activity inputs with owner-scoped validation/idempotency; no calculated-load authority. C1 preserves the historical response. |
| G2 | `public.get_workout_registration(uuid)` | Read the owner's current effective physical workout and registration revision; foreign/stale membership denied. |
| G2 | `public.confirm_workout_registration(uuid,uuid,integer,text)` | Explicit skipped/unknown athlete confirmation with revision CAS, locking and activity exclusion; no plan generation. |
| G2 | `public.get_v6_weekly_plan(uuid,integer)` | Retained owner-filtered canonical public plan/revision read, including history. |
| G3 | `public.get_v6_mobile_weekly_plan(uuid,integer)` | Owner-filtered mobile plan with logical/physical workout mapping. |
| G3 | `public.get_v6_mobile_calendar(date,date)` | Owner/date-filtered active calendar with public identity mapping. |
| G3 | `public.get_v6_move_workout_context(uuid)` | Read owned effective unfinished-workout context before the separately guarded service-only move. |
| G3 | `private.v6_revision_workouts(uuid)` | Required dependency of existing invoker plan/calendar/rest reads. Exact owner check; revoking execution breaks those reads. No private membership-table access. |
| G3 | `public.get_frequency_preferences()` | Read only the caller's optional wishes/reconfirmation state. |
| G3 | `public.save_frequency_preferences(integer,uuid,jsonb)` | Save explicit owner wishes with operation receipts and revision CAS; C2 rejects NULL/negative revision or missing operation ID. Never issues maxima. |
| G3 | `public.report_frequency_interruption(uuid,text,text)` | Owner reports interruption and suspends/reconfirms authority; cannot increase maxima or register reviewers. |
| G3 | `public.get_v6_frequency_swipe_receipt(uuid)` | Recover the owner's immutable submitted swipe result; no generation or evidence-document authority. |

Exact machine allowlist SHA-256: `c98c1c5345ae18daa2b09efc1274bf8a30bbba58d71fc0d37a940ad6d930b267`. Original file: [authenticated-execute-allowlist.json](../../.worktrees/joren-v6-migration-blocker-resolution/docs/catalog/implementation/blocker-resolution-20261117/authenticated-execute-allowlist.json). Detailed security rationale remains in the accepted signature review; this packet does not redesign those permissions.

| Forward correction | Exact filename / SHA-256 | Decision |
| --- | --- | --- |
| C1, inside G2 before COMMIT | `20261116231106_v6_activity_projection_compatibility.sql` / `d0fba80a54cd263ae9ef4b5bf2efd48b8a6375507c0e1763c12bf9c8a8af73bb` | Restore historical activity projection; expose closed V2 presentation metadata through **service-only** `public.get_activity_presentation_v2(uuid)`. Its repository first proves ownership through the existing activity read. No activity/load rewriting. |
| C2, inside G3 before COMMIT | `20261116231107_v6_reviewed_privilege_closure.sql` / `e37c3c09bf71c1373de8c924c5dbdcb63094f4b445a7cd485f44056d65c72a98` | Reassert exact allowlist; close preference NULL-CAS defect; reduce application privileges/defaults below. No physiological/frequency-rule change. |

Drift disposition requiring owner acceptance:

- Preserve hosted `save_zone_profile(...)` only while the exact enabled `private.require_trusted_zone_metadata` guard remains verified; no policy/history change.
- Leave provider-sensitive `public.rls_auto_enable()` unchanged pending Supabase-supported definition/error-behavior evidence. Its missing rethrow is a recorded fail-open risk; explicit RLS postflight must pass. This is not general security clearance.
- C2 revokes `TRUNCATE`, `REFERENCES`, `TRIGGER`, `MAINTAIN` from `service_role` on `workout_templates`, `workout_segments`, `workout_template_phase_tags`, `workout_template_zone_requirements`, retaining supported reads.
- C2 removes those four default table powers only for `postgres`-created tables in `public` for `anon`, `authenticated`, `service_role`. Retain/pin other provider-owned Auth/Storage/Realtime/GraphQL/extension defaults and owner-only application defaults.

The refreshed function/effective-EXECUTE/table-privilege/default-ACL baselines equal the reviewed hosted baseline. Any later mismatch stops execution; no ledger repair or blanket ACL normalization.

Original A5 failure stays separate: unchanged fixture **8 passed, 1 failed**, `partial creation rolls back on attachment failure`, abort before the remaining 20 assertions. Only the explicit onboarding/fingerprint overlay passed **29/29**. The accepted original was not replaced; overlay is test evidence, not a changed product requirement. Original and overlay hashes/transcripts remain in the accepted [boundary evidence](../../.worktrees/joren-v6-migration-blocker-resolution/docs/catalog/implementation/blocker-resolution-20261117/final-boundary-hosted/).
