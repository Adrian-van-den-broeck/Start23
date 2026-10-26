# WOMBO remediation A10 — mobile verification

**26 October 2026. Implemented and verified locally.** Only WOMBO-015 and
WOMBO-016 are addressed. The complete mobile suite passes: **626 tests in
68 suites**, with no failures, skipped tests or todo tests. Strict TypeScript,
unused-code checks, privacy/public-data checks and local workflow validation
also pass. This does not establish beta or production readiness.

## Source and isolation

- Starting SHA: `aff74558d0a6511286a4a84a44ea25a03ca57549`.
- Fresh `git ls-remote origin refs/heads/main` returned that exact SHA. Local
  `main`, `origin/main` and `integration/wombo-ui-v2-main` matched it. Integration
  had **not advanced** beyond the audited revision when this remediation began.
- Branch: `fix/wombo-mobile-verification-gate`.
- Worktree: `.worktrees/wombo-mobile-verification-gate`.
- Final tested implementation commit (tests and CI):
  `a5a9cf36c6e53b2547ebda26f103edc557829c17`.
- This report is a subsequent documentation-only commit. Its final branch HEAD
  is recorded in the delivery message and is resolvable with
  `git rev-parse fix/wombo-mobile-verification-gate`; the implementation SHA
  above identifies the tested source without a self-referential report hash.

Root/mobile `AGENTS.md`, `docs/implementation/mvp-roadmap.md`, existing mobile
configuration and backend/database CI conventions were read. The full-system
audit, end-to-end matrix and prioritized fix plan were read from the sibling
audit worktree at `.worktrees/audit-wombo-full-system-review/docs/audits/`.
Those audit artifacts are not tracked on the starting integration revision and
were preserved in their existing workspace.

The original dirty worktree and existing UI V2 worktrees were not modified.
The integration worktree remained clean and its branch remained at the starting
SHA. Dependencies were installed into this new worktree, without a junction to
another worktree's dependencies.

## Root cause of both failures

Both failures came from the parameterized test in
`mobile/src/screens/PlanningProposalBoundary.test.tsx`, starting at line 183 in
the baseline:

1. `distinct active and pending schedules stay separate before and after explicit approve`
2. `distinct active and pending schedules stay separate before and after explicit reject`

The active fixture workout is dated **2026-10-07**, the pending workout
**2026-10-10**, and the plan week starts **2026-10-05**. No test clock was set.
`PlanningScreen.tsx:880–885` obtains the current instant and derives Today using
the plan's confirmed timezone. `weekHomeViewModel.ts:37–39` selects today's
workouts or the earliest future workout, and returns no Next Session when all
active workouts are past.

Consequently, after 7 October in the athlete's timezone, both tests' first
return-to-Week assertion at baseline line 191 expects an active workout that is
correctly absent from Next Session. Both fail **before the approve/reject
mutation is reached**. On the fresh baseline run on 26 October, the failure is
`findByText('Approved source workout')` in each case. This is a missing temporal
test precondition, not evidence that pending workouts replaced active state.

The expected contract remains: review displays the pending snapshot; Week
displays the active snapshot when it has a current/future workout; approval
adopts the authoritative returned revision; rejection preserves the previous
active revision. A past workout must remain past.

## Exact changes and date-independent assertions

Only three repository files change:

| File | Change |
| --- | --- |
| `mobile/src/screens/PlanningProposalBoundary.test.tsx` | Explicit suite clock, six date scenarios for both original decision paths, and three past-workout regressions |
| `.github/workflows/mobile-ci.yml` | Mobile-only verification workflow |
| `docs/audits/remediation/WOMBO_REMEDIATION_A10_REPORT.md` | This verification and handoff record |

The test setup at line 49 follows the existing move-boundary test convention:
Jest modern fake timers control Date, while `doNotFake` retains real scheduling
and asynchronous rendering APIs. The default fixture instant is
`2026-10-05T12:00:00Z`. Each date scenario uses `jest.setSystemTime` before
mounting. `afterEach` restores real timers. There is no global clock change in
Jest configuration and no production date mock.

The two original assertions are expanded at line 192 into **12 decision cases**:

| Controlled instant | Plan week | Active date | Pending date | Week before decision / after approval |
| --- | --- | --- | --- | --- |
| 2026-10-05 12:00Z | 2026-10-05 | 2026-10-07 | 2026-10-10 | Next training day / Next training day |
| 2026-10-06 22:30Z | 2026-10-05 | 2026-10-07 | 2026-10-10 | Today / Next training day; Amsterdam is already 7 October |
| 2026-10-26 12:00Z | 2026-10-26 | 2026-10-28 | 2026-10-31 | Next training day / Next training day |
| 2027-01-01 12:00Z | 2026-12-28 | 2027-01-01 | 2027-01-02 | Today / Next training day across a year boundary |
| 2027-03-28 01:30Z | 2027-03-22 | 2027-03-28 | 2027-03-28 | Today / Today after Amsterdam's spring DST transition |
| 2026-10-25 01:30Z | 2026-10-19 | 2026-10-25 | 2026-10-25 | Today / Today after Amsterdam's autumn DST transition |

Every row runs both approve and reject. The existing display, exclusion,
object-identity and workout-count assertions remain. Additional assertions bind:

- Active occurrence `active-only` to `plan-a`, revision **2**, `revision-2`.
- Pending occurrence `pending-only` to the same plan, revision **3**,
  `revision-3`, proposal `proposal-a`, with active revision still **2**.
- Startup reads to the latest plan and the exact active revision **2**.
- Approval to `approvePlanProposal('token-a', 'proposal-a', 2)` exactly once;
  rejection to the exact proposal once, with no call to the other decision.
- Follow-up reads to the latest revision after approval or exact revision **3**
  after rejection, preserving authoritative snapshot adoption.
- Today versus Next training day to the supplied scenario dates before and
  after the decision. Rejection retains the original active workout.

The scenario-specific copies change only the week, availability and scheduled
dates needed to represent that scenario; shared fixture files, workout template
identities and server revision semantics are unchanged. This is not a rolling
future-month fixture substitution: both the clock and expected dates are fixed
within each case.

Three further tests at line 243 retain the **original October fixtures** while
setting the clock to 11 October 2026, 26 October 2026 and 1 January 2030. They
assert that Next Session is absent, the truthful no-upcoming-workout message is
present, both original snapshots remain intact, the exact pending proposal is
still reviewable, and navigation performs no decision. These prevent a fix that
would make expired workouts appear current.

All ten other tests in this file retain their assertions. The file increases
from **12 to 25 tests**: the original two become twelve (+10), plus three new
past-workout cases (+3). No test is deleted, skipped or converted to todo.

## CI configuration

`Mobile CI / quality` runs on Ubuntu with Node **24**, npm caching keyed by
`mobile/package-lock.json`, a 15-minute timeout and read-only repository
permissions. Local verification used Node **24.18.0** and npm **11.16.0**.

Triggers follow existing repository conventions: pull requests and pushes to
main that affect `mobile/**` or the workflow itself. `docs/ui/**` also triggers
the job because existing tests import public fixtures and the token contract
from that directory. Manual workflow dispatch is available.

The job runs:

1. `npm ci --no-audit --no-fund` — locked dependency installation.
2. Existing repository-style committed-environment and privileged-credential
   pattern guards, scoped to mobile where appropriate.
3. `npm run typecheck` — the existing strict TypeScript configuration.
4. `npm run check:unused` — unused locals and parameters.
5. `npm test -- --ci src/privacy.test.ts src/ui-v2/utils` — source privacy and
   public view-model projection/poison-data checks.
6. `npm test -- --ci` — the **entire** mobile suite in UTC, including existing
   asset, token-contract, source-boundary, transport and component checks.
7. The four date/calendar suites in `Europe/Amsterdam` and
   `America/Los_Angeles`, using process timezone settings and the same commands
   verified locally.

There is no native build, backend test job, EAS invocation, deployment command,
hosted mutation, service credential or dependency update. `--no-audit` avoids
turning A10 into the separately authorized dependency-advisory remediation A11;
it does not resolve or waive those advisories.

## Verification results

Commands below run from `mobile/` unless stated otherwise. JSON and console
output are retained locally under the ignored worktree `.runtime/` directory;
the report is the committed portable results record.

| Check | Result |
| --- | --- |
| Fresh baseline: `npm test -- --runTestsByPath src/screens/PlanningProposalBoundary.test.tsx` | **1 failed suite; 10 passed, 2 failed, 12 total tests**. Only the two decision cases listed above fail |
| `npm ci --no-audit --no-fund --cache ../.runtime/npm-cache` | PASS; 952 packages installed; package manifest and lockfile unchanged |
| `npm run typecheck` | PASS, exit 0 |
| `npm run check:unused` | PASS, exit 0 |
| `npm test -- --ci src/privacy.test.ts src/ui-v2/utils` | **8/8 suites; 58/58 tests passed** |
| `TZ=UTC npm test -- --ci` | **68/68 suites; 626/626 tests passed; 0 failed, 0 skipped, 0 todo; 0 snapshots; 120.563 s** |
| Four targeted date/calendar suites, UTC | **4/4 suites; 53/53 tests passed** |
| Same suites, Europe/Amsterdam | **4/4 suites; 53/53 tests passed** |
| Same suites, America/Los_Angeles | **4/4 suites; 53/53 tests passed** |
| `actionlint 1.7.12 .github/workflows/mobile-ci.yml`, repository root | PASS, exit 0; official release archive verified against published SHA-256 checksums |
| Workflow YAML parse and Bash syntax validation of every `run` step | PASS; actual environment/credential guards also executed successfully with Git Bash |
| `git diff --check` and staged whitespace check | PASS |
| Backend/OpenAPI/database tests | Not run: no backend, database or shared API contract changed |
| Hosted GitHub Actions run / branch-protection enforcement | Not exercised: no push, pull request, merge or remote configuration change authorized/performed |

The four targeted paths are:

```text
src/screens/PlanningProposalBoundary.test.tsx
src/features/calendar/calendarDates.test.ts
src/ui-v2/utils/calendarViewModel.test.ts
src/ui-v2/utils/weekHomeViewModel.test.ts
```

The timezone runs retain existing Monday–Sunday/exclusive-end calendar
assertions, adjacent-month cells, DST/date-only handling, repeated occurrence
identity, pending/active separation and private-data allowlists. They do not
claim to fix Week/Calendar's separate device-versus-athlete Today defect.

The audit's prior full baseline was 611 passed / 2 failed out of 613 tests in
68 suites. This remediation freshly reproduced the two failures in isolation;
its full post-change run adds 13 tests, explaining the new total of 626.
**No post-change test failure remains.**

Console output still contains pre-existing React overlapping-`act()` warnings
in rapid-action tests. The focused baseline and corrected UTC run each emit six
of these warnings. They were not suppressed or turned into passing assertions.
Dependency-install deprecation notices also remain; no dependency was changed.

## Remaining findings and verification boundaries

WOMBO-015 has a locally validated, committed workflow ready for later authorized
integration. WOMBO-016 has deterministic passing regression coverage. The
workflow becomes an actual remote signal only after an authorized push/PR;
required-check branch protection and a real Ubuntu Actions run are still to be
observed. Local Windows verification and actionlint do not prove hosted execution.

All other audit findings are unchanged and outside this slice:

| Finding(s) | Remaining concern |
| --- | --- |
| WOMBO-001 / 002 | Production runtime identity and exact active-ruleset review coverage |
| WOMBO-003 | Adjacent-week high-intensity spacing |
| WOMBO-004 | Saved restriction loss on resumed check-in |
| WOMBO-005 / 006 | Shared plan-state handoff and replay of committed check-in proposals |
| WOMBO-007 | Synchronous multi-sport planning cost / server-worker blocking |
| WOMBO-008 / 009 | Destructive transient resume and account-scoped locator ownership |
| WOMBO-010 | Activity history invalidation and pending-feedback identity |
| WOMBO-011 / 012 / 013 | Transient auth recovery, transport deadlines and ambiguous successful responses |
| WOMBO-014 | Operational account deletion and retention |
| WOMBO-017 | Dependency advisories; separately scoped A11 |
| WOMBO-018 | Optional profile-name clearing |
| WOMBO-019 | Dependency/revision-aware readiness |
| WOMBO-020 | Shared athlete-local Today across Week and Calendar; separately scoped A13 |

That leaves **18 confirmed findings** outside A10 (7 P1, 10 P2, 1 P3).
U-001 measurement completeness and U-002 history truncation still require
verification. Exact deployed revisions/configuration, hosted grants/RLS,
synthetic two-token isolation, persisted multi-week fault injection, native
build/device behavior and the other original release/privacy gates remain open.
No new beta-readiness or scientific/legal-compliance claim is made.

## Preservation and handoff

No planner formulas, physiological rules, training coefficients, production
configuration, application domain behavior, public API contract, database schema
or real-athlete data changed. No production or staging service was modified.
No build, migration, push, merge or deployment was performed. The work is
committed locally on the isolated remediation branch for independent review.

WOMBO REMEDIATION A10 COMPLETE — MOBILE VERIFICATION GREEN
