# WOMBO V6 backup and recovery readiness

16 November 2026, Europe/Amsterdam. **NO VERIFIED RESTORABLE PRODUCTION CHECKPOINT — execution blocked.**

## Actual project observation

The existing authorized Management API `GET /v1/projects/isfumhgqphieoayqahjv/database/backups` returned **200**. It reported:

```json
{
  "region": "eu-west-1",
  "pitr_enabled": false,
  "walg_enabled": true,
  "physical_backup_data": {},
  "backups": []
}
```

[Current sanitized response and observation time](migration-readiness-20261116/hosted-detail-final.json). It exposes no backup identifier, successful backup timestamp or earliest/latest recovery point. WAL-G capability does **not** prove a usable snapshot or retained WAL chain. No provider-hidden backup, manual export, restore entitlement, paid plan or support recovery capability is inferred. Repeated metadata observations agree. Zero backup downloads, restores, resets or production data exports occurred.

## Recovery options and current status

| Option | Verified here | RPO / data loss | Downtime / prerequisites | Decision |
| --- | --- | --- | --- | --- |
| Uncommitted transaction rollback | Real synthetic G2 precommit-failure rehearsal; all schema/data returned equal from a new connection | None for aborted transaction | Locks held until abort/disconnect; uncertain connection outcomes require ledger/schema reconciliation | Available mechanism; not recovery from a committed migration |
| Forward corrective migration | Architecture/provenance constraints reviewed; exact needed compatibility correction not approved/authored | Preserve records; never recalculate historical load by default | Author, review and rehearse a new forward change; timing unknown | Required incident option; not a guaranteed ready fix |
| Forward V6 generation disable | Expanded local fixture PASS, 64-table hashes and confirmed public read equal; service wrappers + shared A5 persistence boundary covered | No deleted plan/activity/evidence data | Preserves reads/normal historical creation; V6 new generation/moves/draft writes unavailable | Local candidate only; production version needs own forward migration approval |
| Scheduled physical backup restore in place | **No available backup shown** | Would lose all writes after selected checkpoint; actual checkpoint/RPO unknown | Project unavailable during restore; actual duration unmeasured | BLOCKED |
| PITR in place | **Disabled**; no recovery interval exposed | Cannot claim PITR recovery now; enabling later does not prove a preexisting checkpoint | Add-on/retention approval, usable base/WAL checkpoint and rehearsed restore required | BLOCKED |
| Restore physical backup/PITR into new hosted project | Product capability documented; this project's backup/entitlement/restore permissions unverified | Original production remains; migration/cutover needs a controlled write boundary and reconciliation | New project, cost, access isolation, Auth/API/Storage/realtime/network/job review | BLOCKED; no clone provisioned |
| Encrypted logical backup in owner-controlled remote recovery storage | No backup produced or restore rehearsed | Snapshot-time recovery plus any independently captured post-snapshot changes | DB access and protected remote runner/storage, grants/roles/Auth/Storage handling, measured restore/cutover | Owner must select/prove this alternative if physical recovery unavailable; no athlete export to this workstation |

The G2 injected failure executed all 11 accepted bodies, then raised before commit: [transaction rollback evidence](migration-readiness-20261116/atomic-rollback/results.json). The [disable rehearsal](migration-readiness-20261116/disable-rehearsal/results.json) is a distinct operation. Neither restores a backup.

## Provider capabilities versus project evidence

Supabase documents daily backups for paid plans, plan-dependent retention and project unavailability during in-place restoration. Database recovery excludes Storage object contents; custom-role passwords and replication configuration need attention. These are provider rules, not confirmation that this project has a restorable backup. [Database backups](https://supabase.com/docs/guides/platform/backups).

The documented isolated restore copies the database, Auth records and roles; it needs paid-plan/physical-backup eligibility. External-effect extensions can resume on the restored project. Storage objects and several service settings require separate configuration. Therefore an actual production-data clone needs a privacy-approved hosted environment and side-effect containment; use a fresh schema-only synthetic target for routine verification. [Restore to a new project](https://supabase.com/docs/guides/platform/clone-project).

PITR is an add-on. Published indicative retention prices are about $100/$200/$400 monthly for 7/14/28 days, plus the project's other charges. Recheck the owner's actual quote before enabling anything. Published PITR targets can have a short WAL-upload lag; no such RPO applies while disabled. [PITR usage and pricing](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery).

Backup-list read permission was verified; restore/create-project/settings permissions were **not** tested through a mutation. Assign an accountable owner/operator with suitable project/organization and scoped-token rights, and confirm billing authority. Platform Owner/Administrator capabilities are documented separately; the existing read credential is not proof of restore authority. [Access control](https://supabase.com/docs/guides/platform/access-control).

## Required checkpoint before each production group

1. Record target project/environment, operator, actual deployed backend/mobile artifacts, ledger/schema fingerprints and a precise UTC write boundary. Confirm the selected backup belongs to this project and predates the group.
2. Obtain an available successful snapshot or PITR recovery interval through read-only metadata, not a configuration flag. Record retention/expiry and include Auth, identity, historical/private evidence and migration ledger in scope; inventory Storage separately.
3. Rehearse that checkpoint's restore into an approved isolated **hosted** recovery environment without downloading real athlete records here. Verify identity/cascades, grants/RLS, historical read/write behavior and provider/service configuration there. Record measured RTO/RPO, cleanup/retention and cost.
4. Agree the permitted post-checkpoint write-loss window and method for reconciling subsequent legitimate writes. Stop traffic/providers/scheduled processes only under a separately approved operational window; do not assume no active users from table-size estimates.
5. Before G2 and G3, prove the latest approved recovery checkpoint is still inside retention and covers prior committed groups. No accessible checkpoint means STOP. A schema-only dump is insufficient to recover health/provenance data.

## Incident procedures

- **Error before confirmed commit:** stop, retain private operator transcript, roll back/close the failed session, reconnect and inspect ledger/fingerprints. Do not replay a partially known group or repair the ledger. If no new versions committed and definitions equal the pre-group boundary, reschedule after fixing the cause.
- **Unknown commit acknowledgement:** reconcile exact version IDs and object fingerprints first. The next bundle rejects a mismatched boundary. Do not mark versions manually or rerun catalog insertion.
- **Committed functional issue:** keep V6 disconnected. Use a tested compatibility runtime/forward fix, or the separately reviewed generation-disable design. Preserve already attached/pending/confirmed records and exact retries. The old four-RPC disable fixture misses later frequency wrappers and direct private A5 dispatch.
- **Actual restoration:** obtain incident-specific owner approval for target/checkpoint, expected write loss, outage and cutover. Prefer recovery into an isolated hosted target where feasible. Restore verification must include Auth keys/settings, Storage, providers, schedules and endpoint routing. Production overwrite/reset was not authorized by this assessment.

Remaining open facts: actual backup availability beyond the empty list, provider/support emergency options, plan/retention entitlement, restore permissions, isolated restore feasibility for this account, costs quoted to this owner, measured restoration time and a validated data-loss/cutover budget. No rollback-readiness claim is made from reversible SQL alone.
