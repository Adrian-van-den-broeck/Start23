# Hosted migration readiness: read-only assessment

The hosted project has **47/63 accepted migration versions**, no extra versions. All 63 local historical migration bytes remain unchanged. [Preflight evidence](hosted-auth-20261114/preflight.json) records their SHA-256 hashes, hosted statement fingerprints, complete missing filenames and inspected RLS/grant/RPC metadata. Matching version IDs alone do not prove historical SQL bytes equal to hosted statement arrays; no byte-equivalence claim is made for a reformatted or originally split hosted statement history.

The missing migrations start at `20261026224844_wombo_a5_checkin_proposal_recovery.sql`; remaining gaps cover private Realized V2 provenance/registration/evidence, session-RPE guidance, inactive V6 persistence/catalog, frozen snapshots/custody, business conflicts, mobile identity/lifecycle/evidence memberships and approved frequency policy, ending at `20261113154716_inactive_v6_approved_frequency_policy.sql`. The exact ordered list is authoritative in the evidence. No migration was applied.

Existing opaque Auth mapping is compatible with the genuine GoTrue subject and `get_current_athlete_id`. Existing user-owned public tables have inspected RLS/grants; gateway foreign-plan/physiology reads were empty, private schema access was denied, and service-only generation was denied to athlete credentials. This proves only the exercised historical surfaces. Missing V6 relations/functions cannot have their hosted grants or RLS verified. No role memberships or grants were changed.

PostgreSQL 17.6 and the five installed extensions were inspected. Hosted pgTAP, cron and pg_net were not installed. Do not install test extensions or execute fixtures here. The prior 722 local assertions retain their historical scope and A5 overlay caveat; they are not new hosted results.

Security advisors returned **12 findings**: three INFO `rls_enabled_no_policy`, eight WARN `authenticated_security_definer_function_executable`, one WARN `auth_leaked_password_protection`. No advisor remediation or Auth setting change was made. Existing intentional fail-closed/private relations and SECURITY DEFINER contracts need review before deciding whether each finding requires a change. These names/counts do not establish exploitability or clearance.

Before/after metadata and complete Auth configuration matched. Schema, triggers, RLS policies, grants, RPCs, extensions and migration history were unchanged. No catalog was activated; V6 catalog tables do not yet exist hosted, so **77 hosted inactive rows are not claimed**. The accepted local catalog still specifies 77 inactive V6 revisions.

The separate [proposed deployment plan](JOREN_V6_HOSTED_MIGRATION_DEPLOYMENT_PLAN.md) is not executed or approved by this report. Authentication success does not close migration/runtime parity, scientific or release gates.
