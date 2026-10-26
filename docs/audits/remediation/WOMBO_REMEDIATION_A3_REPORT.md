# WOMBO remediation A3 — lossless restriction check-in

**26 October 2026. Implemented and verified locally.** WOMBO-004 is addressed:
saved restrictions, advice and acknowledgements survive reopening; active
restrictions are presented for explicit review; missing answers cannot become
unrestricted decisions. Final verification passes **674 mobile tests in 70
suites** and **784 backend tests**. No production-readiness claim is made.

## 1. Exact source, branch and isolation

- Starting SHA: **`11591b9924ebfd3872314deecb82c57fc278126b`**, the accepted A10 head.
- `git show` verified that exact commit. The A10 worktree was clean and its HEAD
  matched before work began; both checks were repeated after implementation.
- Branch: **`fix/wombo-checkin-restriction-roundtrip`**.
- Worktree: **`.worktrees/wombo-checkin-restriction-roundtrip`**.
- Final implementation commit SHA:
  **`dc3dd01b12f4d595459ecb39220977e5e012ffb2`**.
- This report is committed subsequently as documentation only. The final
  report-inclusive branch HEAD is supplied in the delivery message and can be
  resolved with `git rev-parse fix/wombo-checkin-restriction-roundtrip`. The
  implementation hash above pins all tested application and test changes.

Root/mobile `AGENTS.md`, the MVP roadmap, the full audit, prioritized fix plan,
end-to-end matrix, A10 report, current screen/client, check-in schemas/services,
restriction rules, relevant decisions and migration definitions were read.
The original audit documents remain in the sibling audit worktree; they are
not tracked on the accepted A10 revision and were not copied or changed.

The new worktree has its own lockfile-installed `node_modules`; the existing
ignored npm package cache was reused. No dependency version or lockfile changed.
A10's tracked files/HEAD remain clean and unchanged. UI V2 worktrees, local main
and the original dirty implementation worktree were not reset or overwritten.

## 2. Root cause and previously lost fields

At the starting revision, `CheckInScreen.begin()` restored blocked dates,
fatigue, missed-workout reasons, recurring-sport confirmation and external
activities. It did **not** reconstruct `restrictions` or
`alarm_symptoms_acknowledged`. All sports initially selected `none`; the alarm
checkbox initially selected false. A subsequent save therefore supplied
`none/resume_unrestricted` even for a saved blocked sport.

The old `restrictionPayload()` also recreated professional decisions with
`source=physiotherapist` and a new advice timestamp at every save. It could not
faithfully represent saved `physician`/`other_professional` attribution or the
`clearance_required` and `expired` states. Starting a new week never read the
existing active-restriction endpoint.

The consequence matters at confirmation: the existing PostgreSQL function
clears each prior active discipline record and inserts the explicitly submitted
restriction unless its new status is `none`. That transaction was inspected,
not changed or executed against a hosted database.

Fields previously lost or reconstructed incorrectly:

- Restriction discipline/status and its exact `athlete_plan_choice`.
- Restriction source, professional advice text and original advice timestamp.
- Special blocked states `clearance_required` and `expired`.
- Saved alarm acknowledgement, including distinction from a missing answer.
- Awareness of still-active restrictions from earlier check-ins.

## 3. Complete lifecycle and persisted-field inventory

| Stage | Current behavior after the fix |
| --- | --- |
| Enter/reopen | Existing idempotent `POST /checkins` and token-scoped `GET /me/injury-restrictions` both complete before displaying the form |
| Hydrate | Every saved answer is restored; an unanswered sport remains unselected; active prior restrictions supply review context rather than a default clearance |
| Edit/review | Each active restriction displays status, review date and advice provenance. Explicit review or an explicit sport selection is required |
| Save | Existing expected revision is sent with all supported answer fields; unchanged restriction objects and advice timestamps are retained |
| Navigate away/remount | Server state is reloaded through the same start/resume path; no new general state owner or local health-data persistence is introduced |
| Confirm | Unsaved/incomplete/unreviewed answers cannot confirm. The exact saved revision and fingerprint are submitted separately |
| Plan | Only confirmed complete context enables the existing proposal request, using the exact check-in ID. Backend context conversion supplies its existing blocked and low-only arguments |

All persisted answer fields covered by structural equality tests:

| Field | Preservation |
| --- | --- |
| `blocked_dates` | Same date-only values and order in the synthetic round trip |
| `fatigue_level` | All supported values; explicit `none` differs from unanswered |
| `missed_workout_reasons` | Restored selections and saved values |
| `recurring_activities_confirmed` | True/false retained; the existing requirement to confirm recurring-sport review before proceeding remains |
| `external_activities` | Name, discipline, timestamp/offset, exact duration string, strenuous and recurring flags retained |
| `restrictions` | Discipline, status, source, athlete choice, advice, advice time and supplied sequence retained; optional/null advice remains representable |
| `alarm_symptoms_acknowledged` | Saved true and explicit false retained; missing is not silently converted to false |

Server-owned metadata remains on the authoritative returned `WeeklyCheckIn`:
ID, week, timezone, status, context revision, proposal locator, start/completion
times, and context state/source/expiry/fingerprint/confirmation time. These are
not fabricated by the form or sent back as athlete-owned answer fields.

Optional unsaved free text and the not-yet-added external-activity editor are
not persisted API fields. This fix does not add persistence for those drafts.

## 4. Restoration and review implementation

`mobile/src/features/checkins/restrictionForm.ts` is a small pure presentation
adapter; the existing screen still owns the form locally. It retains original
decision objects, their sequence and their advice provenance. Special blocked
statuses have an explicit retain control, preserving the original status rather
than converting it to a self-reported state. Unsupported or incomplete critical
restriction records fail closed; a missing cleared marker is not evidence of
clearance.

`CheckInScreen.tsx:198` applies authoritative responses consistently on reopen,
save and confirmation. Missing sport answers, fatigue and acknowledgement stay
unanswered. Already-saved explicit negative answers remain negative. Existing
blocked-date, reason, recurrence and outside-activity values are restored too.
New or edited professional advice receives an entry timestamp when edited;
retrying or resaving does not restamp unchanged advice.

An active restriction retains its status when its review date passes. A draft
requires explicit review of each carried restriction. A previously confirmed
context that omits or disagrees with a current active restriction returns to
review rather than immediately enabling planning. Already-confirmed matching
context remains confirmed and shows its restriction summary; the athlete can
explicitly reopen answers for editing through the supported save-new-revision
path.

The presentation changes use existing V2 primitives and styles: status/advice
notices, per-sport review acknowledgement, retain controls for the special
states, a confirmed-context summary and an explicit review button. No styling,
token, icon or navigation redesign was performed.

The existing accepted policy says explicit athlete clearance is sufficient to
change confirmed injury context (`physiology-formula-specification.md:288` and
decision-register injury semantics). Selecting Vrij therefore records the
existing `none/resume_unrestricted` choice, followed by save and separate
confirmation. Advice shown during the choice is retained. No clinical
eligibility rule, professional-clearance verification or medical advice was
invented. `clearance_required` and `expired` remain blocked unless an explicit
supported new choice is made.

Inputs lock during a pending operation; a synchronous local lock prevents
duplicate mutations. Errors retain answers and reviewed identities. The route
supplies the authenticated athlete's identity only as a React lifecycle key;
all API authorization still uses the access token. Account switches discard
the old local form, and late old-account results cannot hydrate the new one.
Same-athlete token rotation retains answers and uses the new token. Already
issued requests are not cancelled or revoked by this local guard.

## 5. Regression evidence

The new component suite uses a synthetic persistence stub that records the
outgoing context, returns it as a new server revision, and reopens that stored
snapshot. Expectations compare complete answer structures with
`toStrictEqual`, including ordered restriction records, nulls, timestamps,
decimal duration strings and activity flags.

| Requested scenario | Evidence |
| --- | --- |
| Save -> navigate away -> reopen | Full answer equality before and after both saves; restored selections and advice checked |
| Save -> app remount -> reload | Same structural assertions after a new component instance |
| One injured sport | Saved blocked selection restored; other absent sport answers stay unanswered |
| Multiple restricted sports | Run professional restriction, blocked swim and low-only bike retained independently |
| No restrictions / explicit negative answers | Three explicit unrestricted decisions, fatigue none and alarm false retained |
| Missing answers | Absent sport decisions, fatigue, alarm and recurrence block advancement; missing status/choice/cleared marker cannot imply clearance |
| Advice and acknowledgement | Original professional source/date/text and alarm true/false preserved; differing prior/current advice both visible |
| Existing restriction still active | Prior-week restrictions load through the existing GET even beyond their review date |
| Explicit supported removal | Reviewed Vrij sends none/resume_unrestricted, retains advice and requires exact separate confirmation |
| Incomplete review | Save/confirm remain disabled until every active discipline is reviewed |
| Stale/conflicting update | API 409 coverage and mobile rejection tests retain inputs; no silent revision refresh, retry or confirmation |
| Network error during save/reload | Failed saves preserve payloads for retry; failed context/restriction loads expose no default injury answers |
| Repeated save | Advice timestamps, nulls, order and unrelated answers remain identical across revisions |
| Different athlete | Late read and late save results cannot populate or confirm the next account's form |
| Next-week contract | Mobile confirms exact revision/fingerprint and requests the exact check-in; six backend cases verify the existing planner arguments |

Four new preservation tests were also run against the accepted **pre-fix**
screen: navigation reload, app remount reload, one saved injured sport and
overdue active-restriction review. **All four failed as expected.** The current
implementation was then restored byte-for-byte before final verification. This
diagnostic is separate from the final green suite.

The six existing screen tests remain. Their setup now supplies explicit saved
negative decisions where a completed answer set is required. The structured
entry test explicitly answers the previously defaulted controls. The old
assertion that extraction left a new sport selected Vrij is replaced by the
required assertion that extraction does not answer the injury question. No
test is deleted, skipped or converted to todo, and existing payload/revision
assertions remain.

## 6. Next-week input and backend/API/schema scope

Six new backend cases exercise actual FastAPI/Pydantic save, GET/resume,
repeated-save and confirmation contracts with an owner-scoped in-memory
repository. They cover all six restriction statuses with advice provenance,
an additional low-only sport, outside activity and explicit alarm false.
Public answers are equal across reads/revisions/confirmation; foreign-athlete
reads remain denied.

The confirmed context is then passed through the actual
`CheckInService.generate_plan_proposal()` orchestration. A planner boundary spy
checks the exact athlete/check-in identity, week, available dates, blocked
disciplines and low-only disciplines. It deliberately stops at that boundary:
these tests prove the input contract, not new scientific or planner output.
The full existing planning suite also passes.

**Backend implementation changes: none. API endpoint/Pydantic changes: none.
Database/schema/migration changes: none.** Mobile adds a typed wrapper for the
already-existing token-scoped restriction GET. Mobile advice fields now admit
the null values the backend already returns, and save inputs reuse the existing
restriction and fatigue types. No new payload field is introduced.

## 7. Complete final verification

Environment: Node 24.18.0, npm 11.16.0, Python 3.10.10; mobile uses the unchanged
accepted lockfile. Commands run from the relevant mobile/backend directories.

| Check | Final result |
| --- | --- |
| Locked mobile `npm ci --no-audit --no-fund` | PASS; 952 packages installed, manifest/lockfile unchanged |
| Check-in screen, round-trip, restriction adapter and API transport suites | **69/69 tests, 4/4 suites passed** |
| Full `TZ=UTC npm test -- --ci` | **674/674 tests, 70/70 suites passed; 0 failed, 0 skipped, 0 todo; 0 snapshots; 98.511 s** |
| `npm run typecheck` | PASS, exit 0 |
| `npm run check:unused` | PASS, exit 0 |
| `npm test -- --ci src/privacy.test.ts src/ui-v2/utils` | **58/58 tests, 8/8 suites passed** |
| Backend check-in, domain and physiology injury tests | **26/26 passed** |
| Full backend `pytest -p no:cacheprovider` | **784/784 passed; 0 failed/errors/skipped; 197.79 s** |
| Backend `ruff check .` | PASS |
| Backend `ruff format --check .` | PASS; 141 files formatted correctly |
| Backend strict `mypy app tests` | PASS; 139 source files |
| Whitespace and protected-path diff checks | PASS; no backend application, Supabase, CI or dependency/configuration changes |
| Hosted DB/pgTAP/native device/Actions execution | Not run; no hosted mutation, native build or push performed |

The full backend run includes 50 planning API/service tests, 89 planning-domain
tests, 13 planning-repository tests, 6 public-contract tests, 10 check-in API
tests, 5 check-in domain tests and 11 injury tests, plus the existing recursive
private-data and other contract checks. It is not a hosted PostgreSQL run.

New coverage adds **48 mobile tests** (29 round-trip component, 18 restriction
adapter, 1 transport) and **6 backend cases**. Accepted A10 totals were 626
mobile tests in 68 suites and the audit baseline had 778 backend tests.

Final failures: **none**. Development syntax/type issues were corrected before
final checks. Existing rapid-action tests elsewhere still emit React act
warnings; they were not suppressed. Backend reports one existing Starlette
httpx deprecation warning. Neither warning triggered dependency changes.

Machine-readable Jest results, pytest XML and console output remain locally
under the ignored worktree `.runtime/` directory. This report is the committed
portable verification record. The inherited A10 CI workflow is unchanged;
there was no hosted Actions run or remote branch-protection change.

## 8. Files modified

1. `mobile/app/(authenticated)/check-in.tsx` — account lifecycle key.
2. `mobile/src/screens/CheckInScreen.tsx` — complete restoration/review and local operation guards.
3. `mobile/src/features/checkins/restrictionForm.ts` — lossless restriction presentation adapter.
4. `mobile/src/api/types.ts` — existing public restriction projection and nullable advice.
5. `mobile/src/api/client.ts` — existing GET wrapper and typed save inputs.
6. `mobile/src/screens/CheckInScreen.test.tsx` — explicit-answer setup and unanswered-injury assertion.
7. `mobile/src/screens/CheckInScreen.roundtrip.test.tsx` — lifecycle/failure regression coverage.
8. `mobile/src/features/checkins/restrictionForm.test.ts` — status/provenance/invalid-record tests.
9. `mobile/src/features/checkins/checkIn.test-fixtures.ts` — synthetic fixtures only.
10. `mobile/src/api/client.test.ts` — token-scoped restriction-read contract.
11. `backend/tests/test_checkins.py` — six save/reload/confirmation/planner-input cases.
12. `docs/audits/remediation/WOMBO_REMEDIATION_A3_REPORT.md` — this report.

## 9. Remaining findings and verification limits

This closes the local implementation/test scope of WOMBO-004. It does not
authorize beta promotion. Apart from A10's accepted 015/016 fixes, the other
**17 confirmed findings** remain unchanged: WOMBO-001–003, 005–014 and 017–020.

Specifically, A2 neighboring-week scheduling, A4 Week/Calendar handoff, A5
completed-proposal replay, A6 discovery, A7 activity invalidation, A8 general
auth/network recovery and A9 performance optimization are not implemented.
There is no new reconciliation for a committed save whose response is lost.
Current context revision/fingerprint checks are retained; this change does not
introduce a global restriction revision or solve simultaneous different-week
restriction updates after the opening read.

Current hosted RLS/migrations, the real PostgreSQL restriction-clear
transaction, persisted multi-week/two-device fault injection, physical device
keyboard/scroll/account lifecycle and exact deployed compatibility still need
the original authorized release verification. U-001/U-002 and the original
scientific/privacy/deployment gates remain open. No scientific formula,
coefficient, catalog, candidate selection, redistribution, progression or load
calculation was changed.

## 10. Production and integration confirmation

Production and staging were not modified. No real athlete data was used.
No schema migration, push, main merge, deployment, native build or remote
configuration change was performed. The tested fix and report are committed
locally on the isolated A3 branch, preserving the accepted A10 changes.

WOMBO REMEDIATION A3 COMPLETE — CHECK-IN RESTRICTIONS PRESERVED
