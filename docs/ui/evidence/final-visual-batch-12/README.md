# Batch 12 evidence

Baseline: accepted Batch 11, 75fa891. Production: feat/wombo-ui-v2-final-batch-12.

- [Report](../../WOMBO_UI_V2_FINAL_VISUAL_BATCH_12_REPORT.md) contains scope, acceptance and open gates.
- [Commands](command-results.json), [full mobile result](full-mobile-tests.json), focused-final.log and strict-types-production.log record final checks.
- [51-case ledger](case-ledger.json), [95-sheet index](inspection-index.json) and [visual review](visual-review.json) record the 227 Android viewports. Raw PNG/XML/JSON captures are named by logical width, text scale and actual fixture state.
- [10 native interaction checks](native-interactions.json), [4 additional contact sheets](interaction-inspection-index.json) and eight interaction captures prove dispatch, explicit cancellation, current translations and visible secure keyboard behavior. The profile/sign-out captures show the existing owner after modal dismissal; their callback markers are review instrumentation, not invented destinations or real successful account transactions.
- [State audit](native-state-audit.json), [control audit](native-target-audit.json), [contrast](contrast.json), [functional freeze](functional-freeze.json) and [production hashes](production-provenance.json) make verification reviewable.
- [Original-reference protection](batch-12-reference-protection.json), [accepted-reference protection](reference-protection.json) and reference-real-check-in-error.png preserve source evidence. The native error replay uses the original documented 422 rejection and exact existing client endpoint; it is not a new staging capture.
- gallery-source contains text-only snapshots of temporary review entry points. public-fixtures.json is typed inert review data; native scripts are QA drivers. No review entry point, endpoint, credential or fixture enters production. Live fetch is blocked by the harness.
- device-baseline.json/device-restored.json document settings restoration. Rejected attempts and scratch runtime configuration are ignored and are not acceptance evidence.

The default Jest setup remains enabled. deterministic-proposal-fixture-date.cjs stabilizes only the two unchanged named Wednesday-7-October proposal boundary tests and resets the clock after each. All other tests use the normal clock. Existing accepted-baseline act warnings are not assertion failures.

Completed Check-in remains **OPEN and UNACCEPTED**. No completed Check-in or successful Pioneer fixture exists. Standalone Settings and goal-achievement confirmation remain unresolved and were not created. Physical/iOS/spoken screen-reader/focus, reduced-motion review, live Auth/provider/redemption/persistence and whole-app release acceptance remain open/outside this visual batch.

[Scope audit](scope-audit.json) confirms protected owners and cross-stack files are unchanged. [Log normalization](log-normalization.json) records removal of trailing whitespace from two superseded test logs only; assertions/results are unchanged. The private cleanup ADB server recovered settings without restarting the unresponsive shared server. Owned Metro/emulator/private server were stopped.
