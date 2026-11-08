# V6 activity and registration compatibility

Branch `feat/joren-v6-mobile-lifecycle`; base `3d54615e6635cd662f5e3dfa246bedee924b9b06`.
Implementation f09941d405d25cdbb587b662fe1f5fe17c1c14eb. No production activation.

Calendar/plan presentation retains logical occurrence identity. Activity creation
and skipped/unknown registration now explicitly use `physical_workout_id` from
the exact persisted revision. Historical workouts continue using their existing
physical `id`. Source-backed V6 without this locator fails closed. The server's
existing active-revision, ownership, immutable observation, idempotency and
registration CAS requirements remain authoritative.

Selecting a V6 workout clears actual duration/distance inputs. Neither source
meters nor reference-pace minutes become observations. The athlete supplies actual
measurements independently. Existing measured zone-time / average-HR processing
and historical Realized V2 behavior are unchanged.

The real PostgreSQL probe verifies: exact attachment; repeated creation with the
same key; original `joren-v6-planned-if2-1` context; measured zone-time processing;
completed calendar state; subsequent read; and physical skipped/unknown registration
with the exact plan revision and expected registration revision. These use synthetic
users and real SQL transactions with simulated JWT claims. No wearable record,
duration or completion for a real athlete was fabricated.

Session-RPE alone does **not** authorize a load under the new planned method.
The existing contract may save actual duration and RPE as activity feedback, but
persists `unsupported_planned_method_version`, no fallback value and
`planner_eligible=false`. The SQL probe asserts those private results. Saving the
activity is not a successful fallback calculation. Distance-only swimming without
actual duration remains unsupported for that calculation; reference pace is never
used as realized swimming evidence. Existing missing-measurement and observed-data
priority tests remain intact. No new Realized dispatcher/mapping was introduced.

## A5 check-in blocker

The V6 persistence writer deliberately refuses check-in-driven generation. A5
requires attachment lookup/replay before computation and atomic creation plus
attachment under the same check-in lock. A completed/terminal result must replay
the exact original locator without regeneration. The separate V6 writer does not
participate in that transaction. Calling attachment later from mobile or adding
another replay table would not satisfy the authoritative contract.

The original A5 test still has incomplete synthetic onboarding and a 64-character
fingerprint where 32 is required. It was not edited. SQL verification used only
the separately disclosed corrected overlay in a disposable database. Adopting
that fixture correction, adopting the protected A5/A6 release work and integrating
the V6 writer into the A5 transaction are distinct review dependencies. Onboarding,
eligibility, restriction confirmation and check-in safeguards are unchanged.

Exact fail-closed boundary: `create_v6_weekly_plan_proposal`, in
`20261105120000_inactive_v6_persistence.sql`, rejects non-null `checkin_id` with
SQLSTATE `23514` and `V6 check-in generation is unavailable`. The authoritative
existing orchestration/replay contract is documented in
`docs/audits/remediation/WOMBO_REMEDIATION_A5_REPORT.md` and implemented by
`20261026224844_wombo_a5_checkin_proposal_recovery.sql`.

Full GoTrue/gateway, genuine accounts, session refresh/new-login recovery and
authenticated Android/iOS activity scenarios remain unverified.
