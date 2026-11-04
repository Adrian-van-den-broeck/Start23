# WOMBO A5/A6 backend release gate

2026-11-04. **Backend release: NO-GO. Mobile-only release against the observed API: NO-GO.** Preparation is ready for review; hosted identity, A5 PostgreSQL execution and release signing are not verified. The confirmed destination remains Google Play Internal Testing, exclusively for the owner and Joren.

## Exact source and preservation

Start: `abcc800d594e9e46784148cc799c51834daed329`. Review branch: `fix/wombo-a5-a6-release-20261104`, worktree `.worktrees/wombo-a5-a6-release`. The earlier remediation commits and original audit's uncommitted overlay remain intact. No application/backend safeguard was removed. The UI V2 candidate retains the accepted mobile overlay: unsupported skipped/unknown requests blocked before I/O, V2 activity fields omitted, manual performed duration preserved, new catalog and V2 features disabled.

Final verified source SHA: **`5e990ccb831f03926ea35b722eaa4ec4493bcdbe`** (source fix `999ecddf4c24f200a45492cdf8f6bdeea71451db`, followed by LF preservation for byte-exact vendor hashes). Reports/evidence are committed afterward without changing runtime source. [Exact changed files and hashes](evidence/a5-a6/source-change-manifest.json) cover all 22 source/config/test/script files; no backend application source changed. All eight original uncommitted audit-overlay file hashes were rechecked and match their custody manifest.

The smallest **identified cumulative accepted backend component** is A9 `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`, checked out separately at `.worktrees/wombo-a5-a6-min-backend`. It includes A10/A3–A9, atomic A5 recovery and A6 discovery. It predates Realized TSS V2 and Catalog C1/C2/C2.1, so those implementations and all four deferred November migrations are absent. No blind branch merge or physiological change is needed to obtain A6.

**This is a conditional component selection, not permission to downgrade production.** First identify the actual deployed commit and database history. Any later migration, V2 storage/history or incompatible deployed behavior stops use of this pre-V2 component. Review the newer version-aware implementation instead; never reinterpret historical data. The full review/mobile tree still contains later source with its existing gates off; it is not the backend upload directory.

`scripts/prepare_a5_a6_release_kit.py` reproduces the component from Git objects, 48 historical migrations ending with A5, the accepted A5 test, read-only SQL and isolated concurrency probes. It refuses existing output directories and performs no network/database operation. Source/tar hashes and the generated catalog SQL are under [evidence/a5-a6](evidence/a5-a6/manifest.json). The source archive is reproducible; Docker dependencies still use existing ranges. An actual Linux image, dependency inventory and immutable image/deployment identity remain build gates.

## First blocker: real Railway production identity

One existing-session Railway CLI identity request returned **Unauthorized**. No login, link or repeated hosted CLI operation followed. Local linkage is **r6-staging**, not confirmed production:

| Local link only | Value |
| --- | --- |
| Project | `c0cf7bc7-abe8-4db5-857a-85cc39850640` |
| Environment | `875b7e64-0f3f-4e42-9efd-973dfb6e295b` / `r6-staging` |
| Service | `6c2cb45b-43e1-43c1-983f-1ed154b2ac76` |

Read-only public `/ready` at `https://start23-production.up.railway.app` reports `environment: local`, version `0.1.0`; it does not expose a SHA or test schema connectivity. Actual production project/environment/service IDs, deployed SHA/deployment ID, branch, auto-deploy rules, overrides and rollback identity are **UNKNOWN**. The first owner action is dashboard identification of the service owning that exact domain. No source branch or EAS build is evidence of the running Railway SHA.

## A5 gate, independently of V2

Required migration: `20261026224844_wombo_a5_checkin_proposal_recovery.sql`, plus its already-existing historical prerequisites. A5 is an active unconditional check-in dependency. The four deferred V2 migrations are unnecessary for this component and must not be applied to unblock it.

The migration intentionally grants replay `get_checkin_plan_proposal(uuid)` to **authenticated**, not service_role. It is SECURITY INVOKER, stable, with empty search_path; ownership is checked through the caller's token/RLS and matching check-in/proposal/revision identities. Service-key schema metadata omitting it is **not absence proof** and must not be “fixed” with broader grants. Generation `create_weekly_plan_proposal_v3(uuid,jsonb)` is service-only, SECURITY DEFINER, empty search_path, and verifies its trusted role. It locks the owned check-in before creating/attaching, returns the exact existing receipt, and recovers only an unambiguous legacy orphan. Invalid/ambiguous/terminal-unrecoverable state fails closed.

The kit checks catalog presence, pinned function bodies, role privileges, PUBLIC/anon denial, RLS/owner columns, relationship FK and migration ledger. This is prepared SQL, **not executed hosted evidence**. Syntax parsing succeeded offline; it cannot establish PostgreSQL compilation, grants, RLS, rollback or concurrency. No Docker/PostgreSQL/Supabase CLI was available; none was installed. The accepted pgTAP suite and real two-session lock/replay probes are prepared. All database execution remains open. See the [owner runbook](WOMBO_A5_A6_OWNER_RUNBOOK.md).

## A6 and client compatibility

`GET /api/v1/weekly-plans/recovery` requires a verified athlete token, takes no owner ID, and returns exactly `{active, pending, draft}`. Active/pending are full public snapshots or null; draft is an open-draft locator or null. It uses the caller JWT plus an explicit opaque owner filter, existing RLS-visible tables/profile and existing plan hydration. It needs **no new A6 migration/RPC**. Missing tables/relationship/profile RPC, malformed state or failed I/O cannot become an empty success. See exact public models in [minimal-backend-openapi.json](evidence/a5-a6/minimal-backend-openapi.json).

The observed API has 69 paths; this component has 70, adding only A6 with no removed common path or newly required request field. Existing activity inputs remain supported. One generated duration-string regex differs because the schema generator advertises the existing `max_digits=8` constraint; the documents are not byte-identical. This static comparison is not proof of the installed APK's source or actual hosted schema.

The new UI safely distinguishes endpoint unavailable, authoritative no-plan, unknown recovery, existing plan, transient I/O and auth failures. It does not generate on failed discovery, discard owned locators, or recreate an ambiguously submitted proposal. The old API cannot prove absence/recover every unscheduled/rest-only/pending plan; no general safe mobile fallback was found. Existing distributed app identity/source and installed versions remain unknown, so hosted/device cross-version compatibility is still required.

## Verification and remaining gates

| Check | Result |
| --- | --- |
| Exact A9 backend full suite | **850 passed**, one existing Starlette/httpx deprecation warning |
| A9 Ruff / format / strict mypy | PASS; 152 files formatted, 148 mypy source files |
| Cumulative UI candidate backend full suite / static checks | **1,282 passed**; Ruff/format PASS, strict mypy 171 source files PASS |
| Full UI candidate mobile suite | **933 passed / 85 suites** |
| TypeScript / unused code | PASS |
| Release-kit and read-only probe tests | **5 passed**; no services contacted |
| Tool Ruff / format / strict mypy | PASS, four source files |
| SQL syntax parser | PASS; execution/pgTAP/concurrency **NOT RUN** |
| Decoder adversarial/consumer/provenance checks | PASS; upstream algorithm unchanged |
| Android Hermes export | PASS; source map contains the patched decoder |
| Signed release AAB / cloud build / real devices | **NOT RUN / NOT PRODUCED** for this change |

The remaining runtime decoder advisory is addressed by the targeted [decoder fix](WOMBO_RUNTIME_DECODER_FIX.md); the dependency audit now reports 0 critical, 3 high, 31 moderate, 6 low. The three high entries belong to build tooling and still need a documented security disposition; none is automatically accepted. The previous local native AAB was debug-signed with placeholders and is not distributable. This task's Hermes export is also verification-only.

Owner actions, in order: establish real production identity/configuration; authorize isolated A5 execution; obtain passing catalog/upgrade/pgTAP/concurrency/compatibility evidence; resolve genuine production approvals/credentials; approve any narrowly scoped A5 production migration if actually missing; separately approve backend/config deployment; verify A6 and both clients; review remaining security risks and authorize a signed EAS build; verify Play/signing/device evidence before separate Internal Testing submission approval. No stage authorizes the next implicitly.

No push, merge, deployment, hosted configuration change, migration, hosted data write, cloud build, signing rotation, submission, publication or tester-list change occurred.
