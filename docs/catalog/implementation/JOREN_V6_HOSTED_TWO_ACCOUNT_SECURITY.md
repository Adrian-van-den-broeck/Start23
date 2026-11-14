# Two-account security and authenticated lifecycle

Only the two synthetic identities and their manifested record IDs were used. No real athlete identifiers were enumerated. The runner stops on unexpected foreign success or private-load fields. [Individual local-backend HTTP outcomes](hosted-auth-20261114/lifecycle-results.json) and [gateway outcomes](hosted-auth-20261114/auth-results.json) preserve actual status codes.

| Scenario | A accessing B | B accessing A |
| --- | --- | --- |
| Gateway weekly plans / physiology with exact foreign owner filter | 200, empty rows | 200, empty rows |
| Local plan read / pending confirmation | 404 / 404 | 404 / 404 |
| Foreign workout alternatives / move | 404 / 404 | 404 / 404 |
| Activity attachment to foreign workout | 404 | 404 |
| Read foreign activity / reuse foreign activity idempotency key and occurrence | 404 / 404 | 404 / 404 |
| Private schema access | 406 | 406 |
| Service generation / Auth administration as athlete | 403 / 403 | 403 / 403 |
| Foreign submitted swipe draft | Not separately repeated with a B-owned draft | B to A: 404 |

Victim pending state was reloaded and unchanged after foreign operations. No unexpected cross-account success occurred. Owner activity retry returned the original record. A stale revision with a current workout locator returned **409 plan_revision_stale** for both; the old historical locator after moving returned **404**, because that planner replaces workout IDs in a new revision. Missing, malformed and tampered real credentials were rejected by the actual local backend with 401.

Frequency preferences/authorizations, private reviewer evidence, V6 immutable operation receipts, V6 frozen context and V6 physical-occurrence boundaries are **BLOCKED by missing migrations**, not passed security tests. The missing frequency and A5-recovery routes returned 404 `resource_not_found`; this reflects unavailable RPCs, not proof of authorization rejection. No reviewer/operator, approval, individually authorized maximum or test-executor membership was created. No positive multi-session operation was attempted.

## Executed historical lifecycle

Both accounts completed normal onboarding: deterministic synthetic physiology/history/goal, separate sport-zone proposals and athlete confirmations, then normal onboarding completion. Both started and saved a check-in and confirmed its context. A5 proposal recovery/completion was unavailable. The ordinary route generated actual **historical** pending plans, and each athlete separately confirmed their own proposal, reloaded calendar/state, attached one supported synthetic activity, retried that attachment, and moved an unfinished workout. A also accepted five historical swipe choices and submitted a separate pending proposal, restored after logout/login. Two ordinary concurrent own-account reads passed once; no load or aggressive concurrency testing was performed.

Activity API evidence remained byte-equivalent as canonical JSON after the move for both accounts. **The completed workout's original physical ID was absent from the new active historical plan revision.** This is a documented historical lifecycle limitation, not a V6 completion or physical identity preservation pass. Activity evidence itself was not recalculated or lost. No production fix was attempted.

These are real GoTrue/gateway-backed checks of a locally running backend and the existing historical schema. There were **zero successful V6-specific lifecycle checks**. The V6 production dependency remained disabled, and the local-only injection helper was neither used nor weakened. Full bidirectional V6 receipt/frequency/evidence attacks and authorized concurrency remain release gates in an isolated, fully migrated official Supabase runtime.
