# Existing hosted drift disposition

17 November 2026. Read-only production inspection and synthetic local corrections; no production object, migration history or default privilege was changed.

The 16-November baseline and the new read-only function/permission/default-ACL observations agree. Existing statement-array fingerprints are not asserted to equal local file bytes. The generator pins the reviewed actual baseline and stops on further drift.

| Observed difference | Security and functional consequence | Disposition |
| --- | --- | --- |
| `public.rls_auto_enable()` logs an exception without the portable definition's rethrow | An auto-RLS failure could allow table DDL to finish without its intended protection. That is a general fail-open risk. These migrations explicitly enable/force required RLS and add no new public application table, so their protection does not depend solely on this event trigger. It does not disable existing RLS. | **Leave unchanged pending provider-specific evidence.** Do not replace a potentially platform-managed event trigger with the portable fixture. Require explicit RLS postflight and stop on any mismatch. Ask Supabase to confirm the supported hosted definition/error behavior before changing it. This is not a blanket security clearance. |
| `public.save_zone_profile(...)` omits redundant manual/fallback review-metadata checks | The RPC body has fewer checks, but the active downstream `private.require_trusted_zone_metadata` trigger still rejects forged manual/fallback metadata and unauthorized fallback input. Rewriting the whole older body could overwrite later hosted behavior without improving the proven boundary. | **Accept and document for this inactive migration scope**, conditional on that exact enabled trigger/body and owner/RLS tests. Preserve the observed body; do not change zone policy, provenance or historical records. A missing/altered guard reopens the gate. |
| Extra service-role `TRUNCATE`, `REFERENCES`, `TRIGGER`, `MAINTAIN` on four historical catalog tables | These are DDL/maintenance powers, not supported catalog reads. TRUNCATE bypasses RLS; a compromised service credential would have unnecessary destructive authority. Runtime FK checks and existing trigger invocation do not require client REFERENCES/TRIGGER creation privileges. | **Correct with C2.** Revoke only those four powers from `service_role` on `workout_templates`, `workout_segments`, `workout_template_phase_tags`, `workout_template_zone_requirements`. Retain existing SELECT and owner/platform privileges. |
| `postgres` defaults for new tables in `public` include Dxtm for anon/authenticated/service | A future public table could inherit dangerous powers even with RLS. The accepted new private tables explicitly revoke broad rights, but carrying these defaults forward is unnecessary application risk. | **Correct with C2**, only `ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public ...`. Remove Dxtm for those three roles. No new ordinary/anonymous grant is introduced. |
| Other hosted defaults: provider-owned Auth/Storage/Realtime/GraphQL/extensions and owner-only application sequence/function entries | Managed services legitimately need defaults different from the deliberately narrow portable bootstrap. Schema-local function defaults also do not replace effective EXECUTE inspection. Broad normalization could break provider operations. | **Retain and pin.** No edits to `supabase_admin`, `supabase_auth_admin`, Storage, Auth, Realtime, GraphQL or extension defaults. An unexpected effective application privilege still fails the bundle guards. |

## Actual local verification

Two independent fresh 47-file historical boundaries were upgraded:

1. Clean accepted replay.
2. Both actual differing function definitions, all observed hosted default-ACL rows and the four historical service ACL differences reproduced before upgrade.

Both pass **752 assertions in 38 pgTAP suites**, with the explicit A5 corrected overlay. Six historical smoke suites pass after each group. All 51 existing table hashes remain equal after every group. The final privilege tests prove catalog Dxtm removal and safe future application-table defaults; historical reads/writes remain functional.

The NULL-CAS defect found during the signature review is separately corrected in C2 and is not misclassified as either preexisting hosted body difference. Provider defaults outside the application correction remain unchanged in the reproduced boundary. The generator rejects unexpected permission, role, membership, schema and grant-option changes instead of relying on default ACL assumptions.

See [clean evidence](blocker-resolution-20261117/final-boundary-clean/pgtap-results.json), [reproduced-hosted evidence](blocker-resolution-20261117/final-boundary-hosted/pgtap-results.json), [allowlist](JOREN_V6_AUTHENTICATED_EXECUTE_ALLOWLIST.md) and [verification register](blocker-resolution-20261117/verification.json).

## Remaining hosted boundary

Portable PostgreSQL 17.11 on Windows does not reproduce Supabase 17.6/Linux, GoTrue, PostgREST, managed ownership or every provider service. The local fixture recreates the observed SQL/ACL differences; it is not a hosted parity pass. The approved isolated hosted target must repeat RLS, effective privileges, original historical flows and cleanup after installation. Production execution also remains dependent on recovery and deployed artifact identity.

Existing security-advisor findings remain independently scoped. No ledger repair, migration rewrite, provider-object normalization or global RLS/grant relaxation was performed.
