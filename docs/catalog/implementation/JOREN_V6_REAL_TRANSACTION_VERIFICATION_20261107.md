# V6 real transaction results ? 7 November 2026

Successor to the prepared transactional report at base
`45b8bb8deb6a7c30e224a9472a28345940141f35`.
**The following are EXECUTED/PASS, not anticipated assertions.**

The corrected `backend/scripts/verify_v6_postgres.py` ran against
`wombo_v6_final_gate_20261107` and the final corrected-fixture rerun
`wombo_v6_final_repeatable_20261107`, PostgreSQL 17.11. Every SQL request uses a separate
psql connection and transaction. Create, resume and confirmed reload use separate
Python processes. No .env is read and no network repository fallback is allowed.
The duplicate/reconfirmation fixtures reverse and reapply the actual winning
edit, using authoritative alternatives. Hardcoded swim/bike follow-up choices
can legitimately be exhausted after a different race winner; no planner rule
or conflict assertion was weakened to accommodate that test-fixture issue.

Normal PostgreSQL READ COMMITTED isolation and the implementation's row/advisory
locks are used; isolation was not strengthened to conceal a CAS defect.

| Scenario | Observed result |
| --- | --- |
| Automatic creation for two synthetic subjects | Each gets its own pending proposal and frozen source/method/context. |
| New-process resume and confirmed reload | Public snapshot, ordering and logical occurrence identities match exactly. |
| Persist an alternative | A new pending revision is created; unrelated workout objects and dates remain equal. |
| Competing validated swipes | Both cross a write barrier; exactly one commits, the other conflicts. |
| Concurrent duplicate operation key | Both cross a write barrier and return one immutable receipt/revision. |
| Swipe versus confirmation | Both reach the transition barrier; exactly one commits and the other conflicts. The resulting proposal is confirmed explicitly if the swipe wins. |
| Terminal replay | Original edit receipt survives later replacements and confirmation; confirmation retry returns its applied receipt. |
| Tampered plan/revision/proposal/owner/week/source/occurrence | Rejected; original week and revision count remain unchanged. |
| Failed nested transaction | An edit rolled back after nested writes leaves no receipt; a rolled-back generation leaves no plan. |
| Source/prescription/load immutability | Direct administrative snapshot updates, load updates and added confirmed-workout inserts reject. |
| Authenticated critical-write spoofing | New V6 revisions and workout inserts reject even with the legacy GUC set. |
| Rejection and repeated rejection | The second subject's proposal remains rejected with identical replay. |
| Composite owner foreign keys | All three private owner-bound snapshot/occurrence/receipt tables reject a foreign owner with 23503; preceding synthetic revision/workout writes roll back. |

The composite-FK helper was also executed independently against the final-schema
rollback clone. Its successful checks did not alter the retained dataset.

## A real unknown transaction outcome

`backend/scripts/verify_v6_commit_loss.py` used a loopback HTTP proxy and the real
PostgREST service-role RPC on `wombo_v6_verify_final_20261107`. The proxy first
received the successful upstream write response (the database transaction had
committed), then closed the actual downstream socket without sending an HTTP
acknowledgement. The application-side request reported unavailable/unknown outcome.
Retrying the identical operation recovered the original immutable receipt; a
second retry was identical and only **one** revision was added.

This is an executed lost-acknowledgement test, not a mocked exception or a
pre-commit rollback substituted for an unknown committed outcome. It does not
simulate every operating-system crash, disk failure or production network topology.

The SQL runner still intentionally does not prove GoTrue authentication. Real
signed-token PostgREST isolation has its [own report](JOREN_V6_SIGNED_TOKEN_ISOLATION_20261107.md).
No numerical policy, selection rule, deadline or historical golden changed.
