# Pre-UI beta stabilization audit

Date: 2026-10-01. Branch: `fix/pre-ui-beta-blockers`. This audit separates the device observation from behavior reproducible in the current checkout. No production mutation is authorized.

## Feedback classification

| Feedback | Class | Evidence and disposition |
| --- | --- | --- |
| Activity and HR/RPE save failed | A — confirmed bug | Device failure is confirmed. Current source uses `POST /activities`, then `PUT /activities/{id}/rpe`; local backend and client tests pass. Exact failed endpoint/status/request ID remains unknown. |
| Repeated Save stacked HR/RPE dialogs | A — confirmed bug | Device observation is confirmed. Current source has an inline pending-RPE card, not a modal, indicating build/source drift. Client now shows one pending feedback form and blocks another create while it remains pending. Device build still needs verification. |
| Timeout, delayed response and retry can duplicate submissions | A — confirmed bug | Before this change the client rotated its create key after a successful POST even if the subsequent refresh failed. It now holds the key and the created activity identity until feedback completes. The server already replays the create key and RPE retry refreshes state. |
| Suspected RUN zone from the 30 km example | D — physiology decision still open | The failed feedback cannot prove a zone formula error. Ordinary completed activity and RPE do not invoke the separate calibration evaluation. The observed pace is 300 seconds/km = 5:00 /km. A reviewed test or Week-1 calibration observation is required for a pending threshold/zone proposal. Do not infer Zone 2 from average activity pace and HR. |
| RUN pace shown as raw seconds | A — confirmed presentation bug | Zone and calibration screens displayed canonical numeric seconds without min/km formatting. Shared parsing/formatting now covers input and display; numeric canonical API values remain unchanged. |
| Week drag is hard to activate and can target the wrong row | A — confirmed bug | `PanResponder` captured the whole card and used a fixed 116 px row height although rows grow. The drag handle now captures immediately and measured row centers select the date. Server validation and revision checks remain authoritative. Android frame-time verification remains open. |
| Rapid Month → Week can lose display | A — confirmed bug | Calendar loads lacked a latest-request guard. Older completions can no longer overwrite the current range. Rapid mode regression covers visible week and requested range. |
| Planning is slow; one apparent crash | E — needs more evidence | Source has a full-screen ScrollView around carousels and calendars, plus fetches on view changes. No Android trace, crash log, or before/after frame measurement is available in this environment. Do not claim a performance fix. |
| Workout detail is incomplete | B — confirmed product requirement | Planned-workout public snapshots already include ordered segments, instructions, duration or distance, targets, and expected RPE. The current detail view exposes them from Week and Calendar. Repetitions and recovery are available only when catalog instruction/segment text supplies them; equipment is missing from the public snapshot. No generated prescription is added. |
| Choose target pace or finish time | B — confirmed product requirement | The goal contract supports total and optional discipline target time, but no pace field or transition model. Run-only pace entry now derives the existing total-time value from entered distance. Multi-discipline pace/transition changes remain open. |
| A few very long workouts rather than more sessions | D — physiology/product decision still open | See `workout-distribution-decision.md`. No new cap or onboarding frequency field implemented. |
| “Weekdoel nog niet compleet” | A — misleading state copy | `target_outside_catalog_capacity` means selected catalog load does not exactly match the weekly target. It does not prove incomplete swipes or too few workouts. Copy now asks the athlete to review the week combination without exposing private load. |
| Less text, stronger daily workout, one calendar, hierarchy | C — UI V2 | Recorded in `ui-v2-backlog.md`; no visual system redesign here. |
| One unexpected logout | E — needs more evidence | No matching auth/session evidence or reproducible steps supplied. |

## Activity trace and remaining diagnostic gate

The mobile form sends discipline, start instant, timezone, duration and distance with an `Idempotency-Key` to `POST /api/v1/activities`. FastAPI validates the summary; the service fingerprints it; the repository calls `create_activity_summary` or its external-activity variant. The response is pending RPE. The inline feedback form sends `rpe` and optional average HR to `PUT /api/v1/activities/{id}/rpe`. The service stores HR through `save_rpe_heart_rate_observation`, evaluates the already approved activity rules, then calls `complete_activity_rpe` or the stale-safe correction RPC. The client refreshes after retryable errors to detect a committed response.

The quoted Dutch message is the generic mobile fallback for a server response outside its specific mappings. A domain `422` without field violations, a `403`, or a `500` can lead there. It does not identify the failed mutation. A request ID or timestamp plus the tested build and its backend environment is needed to correlate the exact status and stable code. This is an open P0 verification gate; local unit tests cannot establish the device root cause.

The latest local mobile screen contains no HR/RPE modal. The reported stack therefore needs comparison with the installed build before calling its exact modal implementation fixed. The checkout now prevents multiple inline feedback instances and duplicate creates in the same session, including retry after a timeout.

## Calibration and units

The 30 km / 150 minute fixture yields `300 s/km`, displayed as `5:00 /km`. Activity HR and RPE are persisted feedback and can affect approved activity decisions, but ordinary activity completion does not recalculate LTHR or a threshold pace. Reviewed calibration protocols create a separate observation, evaluation, pending threshold and pending zone profile. Its RUN submaximal path uses the protocol block HR/RPE; its RUN field-test path uses stable test-block pace and optionally last-20-minute HR. A zone must be separately confirmed before activation. There is no approved rule mapping the example long run to a Zone 2 pace bound.

## Verification still needed on an Android build

Record the build SHA, API base environment, request ID, status and stable error for the failed activity attempt. Confirm one create and one RPE record across tap, timeout, delayed response, restart and refetch. Capture a frame trace and crash log for planning, drag and alternatives; check actual pickup latency, frame timing, network call counts and rollback after a failed move. Hosted owner isolation and database/pgTAP checks must run against development/staging before declaring this beta gate closed.
