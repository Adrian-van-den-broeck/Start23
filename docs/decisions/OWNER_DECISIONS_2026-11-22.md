# Owner decisions, 2026-11-22

Recorded by the owner in a decision session on 2026-11-22. Each entry gives the
question as asked, the answer and the follow-up work it implies. Facts were checked
against these branch tips before asking:

| Branch | Commit |
|---|---|
| `save/wombo-ui-v3` (V3 UI refresh, app translation, Dutch default) | `71e1bac9` |
| `i18n/backend-athlete-language` (server text follows `Accept-Language`, stacked on V3) | `41a57d63` |
| `fix/pre-ui-beta-blockers` (holds `docs/releases/WOMBO_INTERNAL_TESTING_FINAL_GO_NO_GO.md`) | `2d320fc1` |
| `release/joren-v6-migration-blocker-resolution` (holds `JOREN_V6_REMAINING_RELEASE_GATES_NL.md`) | `1730a3f6` |
| `main` | `be11382e` |

No follow-up below changes physiology rules, zones, thresholds or plan logic. Where a
follow-up touches reviewed guidance text, the existing review requirement applies.

## Summary

| # | Topic | Answer |
|---|---|---|
| 1 | Coach workout catalog language | Machine-translate, coach reviews |
| 2 | RPE zone guidance language | Translate, physiology reviewer approves |
| 3 | Language-model text | Generate in the athlete's chosen language |
| 4 | Zone route wording | Short labels on both screens |
| 5 | English and staging wording | All four approved |
| 6 | Sign-in errors in English, stale error language | Accepted as known limits |
| 7 | V3 as default presentation | After the V3 review passes |
| 8 | V3 reviewer and devices | Joren, on his own phone |
| 9 | Calibration provenance line | Staging builds only |
| 10 | Zones header stats | Later |
| 11 | Merge V3 and backend language branches | Open PRs and merge now |
| 12 | Test credentials in `README.md` | Rotate passwords and remove from README |
| 13 | 21 November worktree cleanup | Check the unpreserved commits first |

## A. Language

### 1. Coach workout catalog

**Question.** The coach catalog (154 workouts: 50 bike, 50 run, 54 swim) has Dutch
names, descriptions and segment instructions, and stays Dutch in English mode. Keep
Dutch, have the coach supply English, or machine-translate with coach review?

**Answer.** Machine-translate, with coach review before anything is shown.

**Follow-up.**
- Draft English for every workout name, description and segment instruction, plus the
  server-composed segment sentence in `backend/app/modules/workouts/catalog.py`
  ("{name}: volg {label}; {description} gebruik geen onbevestigde numerieke zones.").
- Coach reviews and approves the English text. Record who approved it and when.
- Store English beside the Dutch source, keyed by template id, so the catalog version
  that produced a plan stays traceable. Serve it by `Accept-Language`.
- Until a workout's English is approved, English mode keeps showing the Dutch text.

### 2. RPE zone guidance from the server

**Question.** The 30 reviewed Dutch strings in `backend/app/modules/physiology/rpe_zones.py`
(training type and description per zone, shown in calibration and inside workout
instructions) stay Dutch in English mode. Translate, keep Dutch, or decide later?

**Answer.** Translate, with approval by the physiology reviewer.

**Follow-up.**
- Draft English for the 15 training types and 15 descriptions.
- The physiology reviewer approves the English wording as a versioned text change.
  The zone and RPE mapping itself does not change.
- Serve the approved English by `Accept-Language`, including where the guidance is
  embedded in workout segment instructions.
- Dutch stays the shown text until the English is approved.

### 3. Language-model text

**Question.** The weekly explanation is generated once in Dutch and stored; check-in
clarifying questions are generated in Dutch. Should model-written text follow the
athlete's chosen language?

**Answer.** Yes, generate in the athlete's chosen language.

**Follow-up.**
- Pass the request language into the prompts for the weekly explanation and the
  check-in clarifying questions.
- Store the language the text was generated in, next to the text.
- Open detail for the owner: what to show when an athlete switches language after a
  text was generated (show as stored, or regenerate). Until decided, show as stored.
- Existing stored Dutch explanations stay as they are; no backfill.
- The model still only explains; it does not calculate or change zones or plans.

### 4. Zone route wording

**Question.** The Zones screen uses short labels (Bekende waarden, Veldtest,
Kalibratieweek, Alleen RPE). Onboarding shows the server's sentences ("Ik ken mijn
waarden", "Ik wil rustig beginnen en laten kalibreren"). Which wording should both use?

**Answer.** The short labels, on both screens.

**Follow-up.**
- Change the onboarding zone setup options to the short labels in Dutch and English,
  keyed by `setup_route` (server labels in `backend/app/modules/calibration/service.py`
  and their English wording on `i18n/backend-athlete-language`).
- A short explanation under each option in onboarding is allowed, using existing
  approved text; no new product claims.
- Update tests that use the old wording, including the fixture label
  "Rustig kalibreren" in `mobile/src/screens/OnboardingScreen.resume.test.tsx`.

### 5. Wording to confirm

**Question.** Approve "watts" in the FTP labels, "lactic build-up" for "verzuring" in
the RPE scale, "Sign out" for the short "Uit" button, and the Dutch staging labels
"Diagnose stagingbuild" and "Stagingkandidaat"?

**Answer.** All four approved.

**Follow-up.** None. The wording on `save/wombo-ui-v3` is final.

### 6. Known language limits

**Question.** Supabase sign-in errors arrive in English, and an on-screen error keeps
the language it was shown in until the next error. Accept as known limits?

**Answer.** Accepted, both.

**Follow-up.** List both as known limits in the internal-testing notes. No code work.

## B. UI V3

### 7. V3 as the default presentation

**Question.** Builds default to V2 unless `EXPO_PUBLIC_UI_VERSION=v3`. When should V3
become the default?

**Answer.** After the V3 review (question 8) passes.

**Follow-up.**
- When Joren's review passes, switch the default to V3 in `mobile/.env.example`,
  the Metro cache fallback in `mobile/metro.config.js` and the presentation resolver.
- Keep V2 selectable as today.

### 8. V3 reviewer and devices

**Question.** Who reviews the V3 refresh before athletes use it, and on which devices?

**Answer.** Joren reviews, on his own phone.

**Follow-up.**
- Prepare a V3 build and a review checklist covering every screen in Dutch and English.
- Record the phone model, OS version and build number at review time.
- The other mobile platform stays unreviewed on a real device; keep it as an open
  verification gate.
- Review findings decide question 7.

### 9. Calibration provenance line

**Question.** The V3 calibration screen always shows athletes
"Protocol: start23_week1_run_calibration_v1 · v1 · approved_active". Keep, hide,
reword, or show in staging builds only?

**Answer.** Staging builds only.

**Follow-up.**
- Render the `calibration.protocolProvenance` line in `CalibrationScreen.tsx` only in
  staging or diagnostic builds.
- Add a test that an athlete (production) build does not render it.
- The provenance data itself stays stored and returned by the API unchanged.

### 10. Zones header stats

**Question.** The Zones header shows "Disciplines" with a count and
"Plan gekoppeld: Ja / Los". Keep, reword or remove?

**Answer.** Later.

**Follow-up.** None now. Keep as is; revisit, ideally after Joren's V3 review.

## C. Release and repository

### 11. Merge plan

**Question.** `save/wombo-ui-v3` and `i18n/backend-athlete-language` are not in `main`.
The internal-testing GO/NO-GO document (on `fix/pre-ui-beta-blockers`) and the V6
release-gates document both still say NO-GO pending owner actions. Open PRs now?

**Answer.** Open both PRs and merge into `main` now. V2 remains the default build
presentation until question 7 is met.

**Follow-up.**
1. Before merging the backend branch, confirm whether Railway deploys `main`
   automatically. The release document records the production revision and deploy
   configuration as unknown; merging `i18n/backend-athlete-language` changes backend
   behavior (error wording, `Content-Language`, response text) if `main` deploys.
2. Open the PR for `save/wombo-ui-v3`, then the PR for
   `i18n/backend-athlete-language` (it is stacked on V3), and merge in that order.
3. Run the full checks on each PR: backend tests, Ruff, strict mypy, OpenAPI contract
   tests, TSS/private-load leak tests, strict TypeScript and mobile tests.
4. On a device, verify that an iOS build sends the chosen language and not the device
   locale in `Accept-Language` (open point from the backend language work).
5. This merge does not change any release verdict. Internal testing and the V6 engine
   stay NO-GO until the owner actions in those documents are done.

### 12. Test credentials in `README.md`

**Question.** The emails and plain-text passwords of the two test athletes are in
`README.md` on `main` and on every branch since commit `cd0611c5` (13 August 2026),
and have been pushed to GitHub. Removing the file does not clean history. What should
happen?

**Answer.** Rotate both passwords and remove them from the README. History is kept
as is.

**Follow-up.**
- Owner: rotate the passwords of both test athletes in Supabase Auth. Keep the new
  passwords in a password manager, never in the repo.
- Remove the credentials from `README.md` in a normal commit on `main` (the file is
  UTF-16 encoded; convert it to UTF-8 at the same time). Other branches pick this up
  when they are merged or rebased.
- Search scripts, test fixtures and CI configuration for the old passwords and update
  any place that depends on them.
- Check the repository's visibility on GitHub. The old passwords stay in history but
  are worthless once rotated.

### 13. Worktree cleanup on 21 November

**Question.** A cleanup on 21 November (23:23) removed worktrees and deleted 31 local
branches. It left an archive at `.worktrees/_archive-removed-worktrees-20261121`
(untracked files from 18 worktrees, plus `DELETED_BRANCHES_AND_SHAS.txt`). 23 of the
31 branch tips are in `main`. Eight are in neither `main` nor GitHub. Was this
intended?

**Answer.** Check the eight unpreserved branches before deciding.

**Follow-up.**
- Do not run `git gc` or `git prune` in the main checkout until the check is done;
  the eight commits exist only as unreferenced objects.
- For each commit below, compare it with `main` and with its parent, and report what
  it contains and whether that work exists elsewhere:

  | Deleted branch | Commit |
  |---|---|
  | `feat/joren-v6-multi-session-planning` | `8786440e` |
  | `experiment/joren-v6-partial-approval` | `5c2127cd` |
  | `feat/joren-realized-tss-v2` | `57df803d` |
  | `release/wombo-internal-testing-audit-20261104` | `542a7147` |
  | `review/joren-new-workout-catalog` | `8cad7eb6` |
  | `feat/wombo-ui-v2-activities` | `7514ee38` |
  | `save/workout-detail-20261117` | `76da0645` |
  | `backup/wombo-ui-v2-final-batch-10-before-squash` | `7cbe01b3` |

- The owner then decides per branch: restore and push, keep as a local tag, or let go.

## Not covered in this session

Two open points from the backend language work were not asked and stay open:
uncoded 422 error reasons are generic in Dutch (they would need stable error codes to
be specific), and the iOS `Accept-Language` behavior of older builds (see 11.4).
