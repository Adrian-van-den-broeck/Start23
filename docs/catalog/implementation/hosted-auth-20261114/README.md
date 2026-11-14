# Sanitized hosted evidence

`verification.json` indexes fresh local regression results, genuine hosted Auth/gateway evidence, blocked V6 coverage and historical-only limitations. `preflight.json` contains read-only permission/schema metadata and the exact 16 missing migrations; `postflight.json` records unchanged schema/Auth configuration.

`auth-results.json` and `lifecycle-results.json` contain explicitly allowlisted case/status metadata only, including intermediate attempts and the initial B-expiry HTTP 500. They do not contain token payloads, credentials, synthetic user/athlete/record identifiers or private responses. `cleanup.json` contains before/after per-table counts, supported account-deletion outcomes and local credential-removal confirmation.

`historical*.json` and `oracle*.json` are fresh offline synthetic planner outputs/comparisons; they are not hosted V6 execution. `source-custody.json` records unchanged accepted migrations, SQL fixtures and planner/benchmark source. The previous release-gate report in `history` is the exact accepted Git blob, with binary attributes to preserve its bytes. `SHA256SUMS.json` fingerprints every other artifact in this directory.

The 722 prior local SQL assertions, including their A5-overlay limitation, remain historical evidence in the existing `real-auth-20261114` directory. No hosted migrations, pgTAP fixtures, deployment or activation were performed.
