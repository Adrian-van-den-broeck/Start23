# WOMBO remediation A8 — authentication and network recovery

**28 October 2026 (Europe/Amsterdam). Implemented and verified locally.**
Only WOMBO-011, WOMBO-012 and WOMBO-013 are addressed. This is local software
verification, not database, physical-device, beta or production sign-off.

## Source, isolation and commits

- Exact accepted A7 starting SHA: `75f172d4161f71a763247b04c027fd165901afbd`.
- Branch: `fix/wombo-auth-network-recovery`.
- Worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-auth-network-recovery`.
- Final tested implementation SHA: `3e519f58460ab27bc97617484a2ba2caa1d80f52`.
- A8a: `0b41134c9f2ce2854cd454962b8dd08c537a3093` — auth classification/retry.
- A8b: `7c990747c506fed2ead5c0c5d567a1245f40fdbc` — bounded transport/cancellation.
- A8c: the final implementation SHA above — decoding/reconciliation and final
  lifecycle regressions. All software checks passed before this commit.

This report follows in a documentation-only commit, as in A3–A7. Its final
report-inclusive HEAD is supplied in the delivery message and resolves with
`git rev-parse fix/wombo-auth-network-recovery`; a report cannot contain its own
commit hash. No application source changes follow the tested implementation.

The accepted A7 worktree was clean at the resolved full SHA, and remains clean
and unchanged. Ancestry checks passed for accepted A10, A3, A4, A5, A6 and A7.
The new worktree started clean. The original dirty worktree and unrelated
worktrees were not reset, stashed or overwritten. Dependencies were installed
locally from the unchanged lockfile: 952 packages, Node 24.18.0, npm 11.16.0;
no shared node_modules junction or dependency update was introduced.

Root/mobile AGENTS.md, the MVP roadmap, all four requested audit documents and
completed A10/A3–A7 reports were read. Original audit documents remain in the
sibling `audit-wombo-full-system-review/docs/audits` worktree. The Supabase skill,
current official documentation and pinned SDK source were used. No hosted Auth,
Data API, database, staging or production session was used for verification.

A7 changed no backend implementation: its diff from accepted A6 is mobile and
documentation only. **828 passing backend tests** is therefore the accepted
inherited full-suite baseline, not a fresh A7/A8 full-backend execution. A7's
mobile baseline was **791 tests / 74 suites**. A8 adds **86 tests / six suites**.

## Reproduced root causes

**WOMBO-011:** bootstrap deleted `start23.refresh-token` for every SDK refresh
error. The auth callback also persisted a null session without distinguishing
initialization, temporary refresh failure and explicit logout. Storage errors
had no explicit recovery state. The new offline regression, run against A7's
original provider, failed because `deleteItemAsync` was called once for a real
`AuthRetryableFetchError`. Corrected provider passes without deleting the token.

**WOMBO-012:** request awaited fetch and JSON consumption without an application
deadline or owner cancellation. The new never-settling GET regression, run
against A7's original client, remained unsettled after **300,000 simulated ms**.
The corrected client settles and aborts best effort within its documented budget.

**WOMBO-013:** successful responses were direct `response.json()` casts. A raw
`SyntaxError` bypassed the `ApiRequestError` branch in RPE recovery. The new
committed-RPE malformed-response regression failed against A7's original client
with that raw parser error and no read-back. It now performs exact authenticated
GET recovery without repeating the PUT.

These are deterministic local reproductions, not injected hosted failures.
Baseline JSON/logs are retained under ignored `.runtime/a8-*-baseline.*`.

## Auth classification, identity and rotation

| Evidence | Classification / action |
| --- | --- |
| Explicit refresh-token not found/already used, session expired/not found, user missing/banned | Invalid credential: clear secure token and local authenticated state; no credential replay |
| `AuthRetryableFetchError` with transport status 0 | Recoverable network failure; preserve secure token |
| Application deadline or provider `request_timeout` | Recoverable timeout; preserve secure token |
| Retryable 5xx, API 429/5xx | Recoverable provider unavailability; preserve secure token |
| Other API/client errors or malformed successful Auth DTO | Recoverable unavailable state; no claim that credentials are revoked |
| SecureStore read failure | Explicit storage-read recovery; do not delete or refresh an unread credential |
| SecureStore write/delete failure | Explicit storage-write recovery; retry the latest in-memory credential/storage intent |
| Successful refresh | Adopt usable access session and persist its newly rotated refresh token |

Supabase documents the distinction between API/client errors and explicit refresh
rejections in its [Auth error-code guide](https://supabase.com/docs/guides/auth/debugging/error-codes).
Rotation behavior is described in [Auth sessions](https://supabase.com/docs/guides/auth/sessions).
Implementation decisions additionally use the exact installed auth-js source.

The pinned SDK uses `AuthSessionMissingError` both for a server session-not-found
rejection and a successful response missing tokens. The Auth fetch adapter first
validates successful refresh JSON/token/user structure. Malformed 200 responses
therefore become safe recoverable failures before SDK decoding; only the explicit
server rejection reaches the invalid-session classification. Actual-SDK tests
cover both paths. Parser/provider body text is not copied into new public errors.

There is one AuthProvider and one Supabase client. Provider refresh attempts
coalesce; the provider schedules refresh before expiry and on foreground rather
than competing with SDK auto-refresh. App background stops the scheduled refresh.
The access session remains usable only until actual expiry. Cold offline startup
cannot safely infer an athlete identity from an opaque refresh token and grants
no authenticated access. Expired access returns to explicit recovery, preserving
the credential; no expired access session is published as usable authentication.
Backend JWT verification and token-derived athlete identity are unchanged.

Auth events and responses are guarded by owner epoch, originating refresh token
and account identity. Late A results cannot replace B or resurrect logout. SDK
INITIAL_SESSION null and refresh-side SIGNED_OUT are not independently treated
as proof that a stored credential is invalid. SecureStore writes serialize and
skip stale queued epochs/tokens; an issued old write finishes before the newer
write. Storage retry uses the rotated in-memory token, not an older disk value.
Explicit local logout invalidates owners first, clears credentials, cancels API
requests and bounds SDK cleanup; sign-in gating stays busy during that cleanup.

The installed SDK caches same-token refresh failures for **60 seconds**. Retry
can retain the recovery state during that cooldown; it succeeds after connectivity
returns and the cooldown expires. This is verified with the actual SDK, whose
private cooldown state is not modified. Native keychain/backup behavior and
provider-side real-session revocation remain integration/device verification.

## Request deadlines and cancellation

| Operation | Application budget |
| --- | --- |
| Ordinary API reads and writes, including activity/RPE, check-in context/confirmation, approval and movement | **45 seconds per HTTP attempt**, including body decoding |
| Planning generation: proposal/draft/schedule/check-in/edit proposals and swipe-draft submission | **120 seconds per HTTP attempt**, including body decoding |
| Individual Supabase Auth fetch, including response text | **15 seconds** |
| Whole SDK refresh, including its own bounded retries | **45 seconds** |
| SDK local logout cleanup, including waiting on refresh | **60 seconds** |

The audit measured roughly 15.84–19.46 seconds for full-catalog planning examples.
The generation budget allows substantial headroom for those existing operations;
the ordinary budget also avoids rejecting normal planning immediately. These are
initial engineering budgets, not a measured hosted SLA or an A9 CPU optimization.
No new live latency/load experiment or production configuration change occurred.

`withDeadline` races the whole operation independently of native abort support.
Timers and owner listeners are cleaned in finally. Completed/failed requests
unregister their controllers. Multiple overlapping requests have independent
controllers. The Auth owner cancels all requests belonging to retired access
tokens; token retirement also stops GET retries sleeping between attempts.
Cancellation before dispatch is definitely unsent. Cancellation/timeout after a
write starts cannot prove rollback and remains an unknown outcome.

Wall-clock expiry is checked as well as the timer callback. If native backgrounding
pauses JS timers, a late 200 or 404 cannot win before the resumed timeout callback.
HTTP headers arriving only after the deadline are not published as authoritative
status, protecting A6 locator retention. Actual physical-device suspension and
radio cancellation are not claimed verified; settlement occurs when JS can run.

The existing onboarding-only read retries remain bounded (two delays: 400/1200 ms;
maximum three attempts). There is no generic POST/PUT/PATCH retry policy. A
mutation plus its authoritative recovery read can use two ordinary budgets.
Busy/loading flags settle through the existing controller finally paths.

## Decoding, mutation ambiguity and idempotency

`ApiRequestError` preserves method, observed HTTP status, safe code, retryability
and `rejected` versus `unknown` write outcome. A valid authoritative success is
returned normally; this is the committed branch, not a fabricated success flag.
Transport loss, deadline, cancellation after dispatch, 408, 5xx and successful
unreadable/invalid mutation DTOs are uncertain. Ordinary definitive 4xx responses
retain their rejection semantics. Failed verification reads cannot erase the
original uncertain write's HTTP context or relabel it definitely rejected.

JSON parsing failures are normalized to `response_unreadable`; critical DTO
failures become `response_invalid`. Reads return safe recoverable errors rather
than fabricated objects. Runtime checks cover Activity entities/lists, exact
activity UUID reads/writes, plan/revision/proposal attachments, approval receipts,
swipe drafts, planning discovery and check-in context. Nested structures needed
by those boundaries are checked. Unrelated API DTOs were not comprehensively
redesigned. Error envelopes retain safe codes/validation locations, never arbitrary
server messages, payloads, health measurements or credentials.

| Write | Recovery / preserved identity |
| --- | --- |
| Activity creation | Existing A7 key and immutable input retained; only explicit retry replays that key/payload. Malformed committed POST does not create a second activity |
| Initial RPE / correction | Exact GET checks UUID, completed state, requested RPE and supplied HR. Matching committed state resolves without another PUT. Old read-back alone does not trigger automatic replay |
| Unresolved RPE explicit retry | Per-activity attempt retains original RPE, HR and expected-current-RPE; read first. Input edits/refresh cannot rewrite it. Definitively newer feedback is presented for review |
| Plan approval | Ordinary approval now shares A4's pending/verify/read/persist handoff. Unknown result reads the exact reviewed revision on explicit recovery, retaining receipt/base/proposal identity. No automatic reapproval |
| Proposal generation | A5 check-in UUID and attachment replay unchanged. Uncertain draft generation retains its input snapshot; expected revisions and backend fingerprint/idempotency contracts remain authoritative |
| Check-in start/context/confirmation | Start retains original week locator after uncertainty. Context/confirmation retain immutable answers or revision/fingerprint. Existing GET by UUID can verify exact committed state; no generic resubmission loop |
| Workout movement | Original workout/date/revision retained. Explicit retry first reads the plan. A newer schedule with renewed occurrence IDs is adopted for review without claiming the uncertain PATCH succeeded or sending another old PATCH |

Same-tick create, per-activity RPE and shared planning/check-in locks remain.
No health snapshot/request queue was added to persistent storage. No current-user
singleton, background sync framework, unconditional overwrite, physiological
calculation, training rule, private-load calculation or historical recalculation
was introduced. Athlete identity is still derived by the backend from a verified
access token; client local owner identifiers do not authorize API operations.

NL/EN auth recovery and new transport notices use existing components/conventions.
V2 styling is unchanged. Entry values and unresolved attempts survive request
failures and read refresh. RPE still saves immediately on choice. Recovery does
not navigate to an empty plan merely because a result is unknown.

## Required failure-injection evidence

All evidence is synthetic, with controlled timers/network mocks; API/owner/UI
integration tests use the actual client transport, not mocked API functions.

| Requested cases | Coverage |
| --- | --- |
| 1–5 offline bootstrap, online retry, revoked credential, logout/refresh race, rotation race | AuthProvider lifecycle tests plus eight actual pinned-SDK tests; storage read/write failures, restart and late A/B responses included |
| 6 hung GET | Deadline/late-response tests, including five simulated minutes and paused-clock late 200/404 |
| 7 hung activity POST | Actual Activity owner: busy settles, rapid taps coalesce, form/key/payload survive, explicit replay yields one entity |
| 8 hung RPE PUT | Actual transport/helper and Activity owner: exact read-back, immutable explicit retry, no blind duplicate PUT |
| 9 hung check-in proposal | Actual CheckIn UI/Planning owner: 120-second deadline, explicit retry and remount recovery use original check-in attachment |
| 10 hung approval | Actual Planning owner holds exact proposal and verifies committed revision without reapproval |
| 11–12 timeout after/before commit | Stateful Activity/Planning fixtures and RPE read-back tests distinguish committed versus still unknown |
| 13 original logical identity on retry | Create key/payload, RPE/HR/precondition, check-in week/UUID and proposal/base revision checks |
| 14 malformed successful RPE | Raw-SyntaxError baseline reproduction; exact GET resolves committed write with one PUT |
| 15 malformed successful create | Actual Activity owner retains one original-key attempt for explicit replay |
| 16 invalid DTO | Nested Activity metrics, UUID mismatch, plan attachment, receipt, discovery and Auth success-shape negative cases |
| 17 authoritative RPE read-back | Exact ID, completed state, RPE and HR required; failed/mismatched reads cannot invent success |
| 18 duplicate prevention | Actual rapid create/RPE calls plus existing owner locks and backend idempotency tests |
| 19 navigation away | Actual unmount/late read, existing retained-route/task navigation regressions; no stale publication/navigation |
| 20 account switch | Actual Activity owner replacement, isolated cancellation and actual SDK late-A/B sign-in test |
| 21 overlapping reads | Independent transport requests plus actual four-read Activity bundles and A7 sequence/coalescing regressions |
| 22 abort while server processes write | Abort-ineffective mocks later commit; caller stays unknown, no fabricated success/replay |
| 23 stale result after deadline | Both timer-triggered and wall-clock-after-background late completion tests |
| 24 form survives timeout | Actual V2 duration field/save control in NL and EN, plus owner HR/create-attempt cases |
| 25 A5 proposal identity | Same check-in/proposal/revision attachment after timeout, explicit retry and restart |
| 26 A6 locator retention | Hung real GET preserves scoped locator/failed resume; explicit read retry recovers |
| 27 A7 state retention | Failed authoritative refresh preserves pending entity, HR, form and unresolved attempts |
| 28 NL/EN recovery | Auth retry presentation and actual V2 entry timeout error/save presentation |

## Verification and prior-remediation status

| Check | Final result |
| --- | --- |
| Full mobile suite, UTC | **877/877 tests, 80/80 suites; 0 failed/skipped/todo, 0 snapshots; 119.648 s** |
| Focused Auth/SDK/recovery UI/API/deadlines/decoding/owner integration | **109/109 tests, 8/8 suites; 7.903 s** |
| New A8 cases contained in full suite | **86/86 tests in six new suites** |
| Privacy/source/public view-model checks | **58/58 tests, 8/8 suites; 3.102 s** |
| Strict TypeScript: npm run typecheck | **PASS**, exit 0 |
| Unused code: npm run check:unused | **PASS**, exit 0 |
| Relevant backend/API/idempotency/auth tests | **148/148 passed; 130.11 s** |
| Full backend / Ruff / mypy | Not rerun: no backend/Python implementation changed; inherited full baseline is 828, not a new execution |
| Environment-file / privileged-mobile-credential checks | **PASS** |
| git diff --check / staged whitespace check | **PASS** |
| Accepted ancestry / unchanged clean A7 / unchanged dependencies | **PASS** |
| PostgreSQL/pgTAP | **DEFERRED BY OWNER — PRE-BETA** |

Final JSON/log evidence remains under ignored worktree `.runtime/a8-*`. Full
mobile run uses UTC and a worktree-local Jest cache. No test is deleted, skipped,
marked todo or weakened. Existing React act/FlashList timing warnings remain
unsuppressed. The backend run reports one existing Starlette/httpx deprecation.

Superseded expectations were corrected explicitly: ordinary approvals now read
the exact reviewed revision through A4, so fixtures must return that same revision
ID and target proposal ID. A fixture returning revision 2 for a revision-3 approval,
or targeting revision 3 from a revision-4 proposal, is not an authoritative success.
The Calendar test now verifies A4's actual full-week merge, changed occurrence
identity and stale-row removal without a redundant range fetch. Check-in tests
provide the language context and deterministic locale needed by localized recovery.
The initial full development run exposed these old fixtures; final results above
have no failures. All original approval/isolation/privacy assertions remain.

A3 restriction round trip/professional advice: **29 + 18 adapter + 6 original tests
pass**. A4/A5 handoff and completed-proposal recovery: **30 pass**. A6 account-scoped
recovery: **39 pass**. A7 synchronization: **30 + 3 plan integration tests pass**.
Retained Planning owner **76**, Activity owner **36**, Calendar owner **11** and
actual training navigation **48** tests pass. These counts are contained in the
full mobile run, not additional tests to sum into its total.

Backend verification used the existing interpreter with PYTHONPATH explicitly
set to this isolated worktree; the imported app path was checked. Command:

```text
python -m pytest -p no:cacheprovider tests/test_activities.py
  tests/test_activity_repository.py tests/test_checkins.py
  tests/test_checkin_proposal_recovery.py tests/test_planning.py
  tests/test_planning_recovery.py tests/test_contracts.py
  tests/test_authentication.py
```

This exercises the matching create/RPE/precondition, check-in replay, planning
approval/move, owner and public-contract tests. **148 passed**, 130.11 seconds.
No backend/Python/shared server contract changed; a full backend rerun and Python
Ruff/mypy were therefore not required or represented as fresh results. No new
endpoint, request/response schema, migration, grant, RLS or backend behavior was
added. `getWeeklyCheckIn` only exposes the existing authenticated GET in the client.

## Database decision and remaining limitations

**PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA**

This remains an open integration/release gate, not a failed remediation and not
passing database verification. No Docker, Podman, PostgreSQL, psql or pgTAP tooling
was installed or provisioned. No database behavior, hosted grants/RLS, real-token
isolation, atomic transaction race or live Auth revocation is claimed verified.

Abort cannot stop a server that already received a mutation. A read can still
find old state while that server request continues; this remains unknown until
later authoritative recovery. Requests are bounded while JS can execute; native
radio/background/keychain behavior remains a device gate. The deadlines need
later representative hosted measurements; A9 remains outside scope.

SecureStore failure cannot guarantee that a newly rotated credential is durable
across process death. The in-memory latest token and explicit storage retry are
retained. Local activity attempts and some UI state remain memory-only, as in
A7; process-death durability and a generic background synchronization framework
are not added. SDK failure cooldown can delay successful explicit Auth retry.
Runtime DTO validation is deliberately concentrated on critical recovery boundaries.

A2 spacing, A9 CPU work, A1 production configuration, A11 dependencies, new activity
features, training formulas/catalog rules and unrelated navigation/auth features
remain excluded. No beta/production readiness or scientific/privacy certification
is made by this local remediation.

Production and staging are unchanged. No real athlete records, hosted mutations,
push, merge to main, deployment, migration or native build were performed. All
commits are local to this isolated branch.

## Files modified

- `docs/audits/remediation/WOMBO_REMEDIATION_A8_REPORT.md`
- `mobile/App.tsx`
- `mobile/app/(authenticated)/_layout.tsx`
- `mobile/app/index.tsx`
- `mobile/src/api/client.test.ts`
- `mobile/src/api/client.ts`
- `mobile/src/api/deadlines.test.ts`
- `mobile/src/api/networkRecovery.test.tsx`
- `mobile/src/api/responseRecovery.test.ts`
- `mobile/src/api/responseValidation.ts`
- `mobile/src/auth/AuthProvider.integration.test.tsx`
- `mobile/src/auth/AuthProvider.test.tsx`
- `mobile/src/auth/AuthProvider.tsx`
- `mobile/src/auth/AuthRecoveryState.test.tsx`
- `mobile/src/auth/AuthRecoveryState.tsx`
- `mobile/src/components/ScreenState.tsx`
- `mobile/src/features/activities/useActivityController.ts`
- `mobile/src/features/planning/PlanningFlowProvider.test.tsx`
- `mobile/src/features/planning/usePlanningController.ts`
- `mobile/src/i18n/LanguageProvider.tsx`
- `mobile/src/i18n/recoveryMessages.ts`
- `mobile/src/lib/apiCancellation.ts`
- `mobile/src/lib/deadline.ts`
- `mobile/src/lib/supabase.ts`
- `mobile/src/navigation/TrainingNavigation.test.tsx`
- `mobile/src/screens/ActivityScreen.tsx`
- `mobile/src/screens/CheckInScreen.roundtrip.test.tsx`
- `mobile/src/screens/CheckInScreen.test.tsx`
- `mobile/src/screens/CheckInScreen.tsx`
- `mobile/src/screens/PlanningProposalBoundary.test.tsx`
- `mobile/src/screens/PlanningScreen.tsx`
- `mobile/src/screens/PlanningWeekBoundary.test.tsx`
- `mobile/src/ui/ActivityBoundary.tsx`

WOMBO REMEDIATION A8 COMPLETE — AUTH AND NETWORK RECOVERY VERIFIED LOCALLY
