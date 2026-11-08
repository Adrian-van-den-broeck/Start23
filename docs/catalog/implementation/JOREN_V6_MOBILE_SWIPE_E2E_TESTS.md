# V6 mobile swipe lifecycle evidence

Branch `feat/joren-v6-mobile-lifecycle`; implementation f09941d405d25cdbb587b662fe1f5fe17c1c14eb.
Full counts/hashes: [verification.json](mobile-lifecycle/verification.json).

This is combined local contract/component/SQL evidence, **not one authenticated
device E2E run**. The exported JSON is generated from actual V6 HTTP responses
with a spawned selector and synthetic in-memory storage. Jest mocks transport and
secure storage while exercising the existing mobile owner/screens. The separate
PostgreSQL probes use durable storage and simulated SQL JWT claims.

| Requested step | Executed evidence |
| --- | --- |
| 1–3 Eligible synthetic context, request week, actual selection/cards | Real routes/selector; exported cards rendered in existing SelectionScreen. Production onboarding is not bypassed or device-verified. |
| 4–5 Pass and eligible alternative | Real HTTP transitions; mobile sends exact candidate/occurrence/revision. |
| 6–8 Accept, modify another slot, retain first | Real HTTP pending edit/whole-week validation; existing mobile pending editor; exact logical template/date retention. |
| 9 Dates | Actual placement, undo and reaccept preserve another occurrence's chosen date. |
| 10–11 Submit remains pending | HTTP and mobile owner; approval is not called by submission; pending calendar is empty. |
| 12 Explicit confirmation | Separate existing approval route and mobile action, exact revision read. |
| 13–14 Calendar and source details | Actual PostgreSQL mappings/status; component and view-model rendering of exact source blocks, session effort, zones and qualified swim estimate. |
| 15 Supported activity | Real PostgreSQL measured activity attaches to exact physical occurrence and retains source method. Mobile input mapper independently checks the same FK. |
| 16 Restart | New service/Python processes reload durable confirmed state and activity. GoTrue logout/login and app kill/relaunch were not executed. |
| 17 Stale write | HTTP stale edit rejected; PostgreSQL competing edits/approval, immutable retries and rollback preserve the winning state. |
| 18 Historical state | Historical catalog rows/load snapshots preserved; existing planner corpus and historical mobile suites retained. |

| Additional case | Evidence / limit |
| --- | --- |
| Partial two/one sport and rest-only | Real deterministic backend selection tests; component-only partial/rest models render actual source cards without missing-discipline errors. No partial-week device run. |
| No feasible workout / no alternatives | Existing V6 selector and HTTP exhaustion/reset tests; retained cards remain intact. |
| Expired/superseded proposal | Existing mobile recovery/proposal and backend CAS tests. No real-session expiry/device proof. |
| Ownership and repeated/concurrent requests | Real SQL authorization, exact retry receipts, concurrent writes; mocked mobile account-lifetime tests. |
| Distance-only swim / wall rest | All 77 source presentations checked; actual distance-source and wall-rest components; estimate remains separate from prescribed/measured duration. |
| Long duration / missing capability / injury | Existing genuine deterministic V6 selector/HTTP restriction cases in full pytest; no new suitability threshold. |
| Missing actual measurements / unsupported fallback | Existing API/Realized tests plus actual SQL null fallback and ineligible provenance assertion. |
| Timezone and same-date siblings | Existing ISO date-only/calendar component suites plus actual V6 calendar range/occurrence checks. |
| Confirmed date moves | Explicitly rejected; implementation blocker documented in occurrence mapping. |
| A5 V6 check-in generation | Fail-closed; no successful check-in lifecycle claim. |

## Reproduction

Use the pinned lockfile and project Python environment. No `.env` or hosted
credentials are required for software tests. Export the public trace by setting
`WOMBO_V6_PUBLIC_TRACE` to `../mobile/src/features/planning/v6-http.test-fixture.json`
and running `pytest tests/test_v6_mobile_lifecycle.py` from backend. Then run full
pytest, Ruff lint/format and strict mypy; from mobile run `tsc --noEmit`, the unused
checks and `TZ=UTC jest --runInBand --ci`. The JSON is consumed only by test code.

The disposable SQL workflow is `scripts.verify_v6_final_sql` with explicit local
psql/cluster/port/database arguments, then `scripts.verify_v6_postgres` and
`scripts.verify_v6_mobile_lifecycle`, each requiring
`--execute-disposable-local-only`. They refuse non-loopback database DSNs and never
read `.env`. The latter probe expects the former's confirmed snapshot. Do not run
these synthetic fixtures on staging, production or real athlete data.
