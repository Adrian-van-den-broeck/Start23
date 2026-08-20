# Phase 8.5 and Phase 9: open business decisions

Last updated: 2026-08-20

Audience: Start23 business, product, clinical/physiology, privacy, security, and
engineering stakeholders.

## Executive summary

The functional cores of Phase 8.5 and Phase 9 are implemented. Their Supabase
migrations are applied, their hosted pgTAP suites pass, and the linked database
has no error-level lint finding. The database migration ledger was checked again
on 2026-08-20 and is fully synchronized; no new migration, seed, role, or Vault
change was needed.

The remaining work is mainly approval, product-policy, operational, and live
verification work. The system deliberately fails closed where a clinical or
product rule has not been approved. In particular, Start23 does not invent a
complete Zone 1-5 profile, silently match imported activities, or activate Polar
processing before the relevant decisions are made.

Recommendations in this document are proposals for discussion. They are not
recorded as approved decisions until the responsible stakeholders accept them.

## What is already decided

- Planned and realized TSS remain internal and are never returned to the mobile
  application.
- Physiological calculations remain deterministic Python rules; an LLM cannot
  change plans or zones independently.
- Threshold and zone changes remain pending until the athlete confirms them.
- The calibration feedback scale is canonical session RPE from 1 through 10.
- Submaximal calibration can collect useful observations but cannot manufacture
  a threshold.
- Polar is the provisional first wearable adapter, not an approved production
  processor.
- Provider credentials and tokens remain backend-only.
- Redis, Celery, microservices, and a second worker service are outside the MVP.

## Phase 8.5: zone intake, field tests, and Week-1 calibration

### 8.5-D1 — Approve the complete Zone 1-5 calculation model

**Decision needed:** Approve deterministic formulas per discipline, boundary
ownership, canonical rounding, ruleset versioning, and reviewer metadata for
turning a threshold into five zones.

**Why it matters:** Field tests can already produce CSS, FTP, LTHR, or run
threshold pace. Start23 intentionally stops before generating complete zones
because the approved source material does not define that conversion.

**Use case:** A runner completes the 30-minute field test and receives a
threshold pace of 290 seconds per kilometre. The app may show the pending
threshold, but it cannot safely calculate the athlete's five pace zones until
the model and rounding rules are approved.

**Recommended direction:** Have the named physiology reviewer provide and sign
off one versioned conversion table per discipline, including examples at every
boundary and explicit rounding rules.

### 8.5-D2 — Integrate calibration sessions into the normal Week-1 planner

**Decision needed:** Define a zone-independent planned-workout segment contract
and an approved internal load rule for calibration protocols.

**Why it matters:** The existing normal planner expects Zone 1-5 targets. The
approved calibration fixtures use protocol instructions and RPE instead, so
they currently run as explicit standalone sessions.

**Use case:** A new cyclist does not know FTP. Week 1 should schedule a safe
calibration workout without inventing power zones, exposing TSS, or pretending
the workout is a normal zone-based catalog session.

**Recommended direction:** Add a separate protocol-target segment type with
reviewed RPE/instruction targets. Keep its load calculation private and do not
insert it into normal planning until the load rule has been reviewed.

### 8.5-D3 — Decide whether to configure soft plausibility warnings

**Decision needed:** Decide whether the MVP needs evidence-based soft ranges for
manual thresholds and zones, and approve the values, sources, reviewer, and
version if it does.

**Why it matters:** Structurally valid values are accepted today with
`soft_range_not_configured`. They are not rejected merely because no approved
plausibility range exists.

**Use case:** An athlete enters an FTP of 600 watts. The value is technically
valid, but Start23 cannot say whether it is unusual or likely mistyped without
an approved range appropriate to the athlete and discipline.

**Recommended direction:** Keep the warning unconfigured until evidence and
review ownership exist. Never convert a soft warning into automatic rejection.

### 8.5-D4 — Decide whether to add the physiological-sex HR fallback

**Decision needed:** Decide whether the optional maximum-heart-rate fallback is
valuable enough for the MVP to justify collecting a separate sensitive
physiological-sex field. If included, approve the formulas, consent language,
privacy treatment, ruleset, and forward migration.

**Why it matters:** The current profile does not collect this field. Gender
identity must not be used as a substitute, and the proposed fallback is not an
FTP estimator.

**Use case:** An athlete has no measured running threshold and asks for HR-based
guidance. Start23 must not silently infer physiology or apply a sex-specific
formula without the athlete's explicit input and reviewed rules.

**Recommended direction:** Defer this optional fallback from the MVP unless
research and customer validation show a clear benefit over RPE-only guidance.

### 8.5-D5 — Appoint the accountable physiology reviewer

**Decision needed:** Name the qualified person accountable for production
approval and record the first approval date and review cadence.

**Why it matters:** Automated tests prove that code matches a rule; they do not
prove that the physiological rule itself is clinically suitable.

**Use case:** Engineering implements a threshold formula exactly as specified
and every fixture passes. Production must still remain blocked if nobody is
accountable for approving the underlying specification.

**Recommended direction:** Appoint the reviewer before activating automatic
zone calculation or production calibration recommendations.

### 8.5-D6 — Choose the mobile dependency-advisory strategy

**Decision needed:** Continue monitoring compatible Expo SDK 57 patches or fund
a separately reviewed SDK upgrade. Do not use the currently suggested forced
audit fix because it crosses the locked Expo/React Native versions.

**Why it matters:** Expo Doctor passes, but `npm audit` still reports 8 moderate
and 11 high upstream/transitive findings with no critical finding.

**Use case:** A release checklist requires a clean dependency decision. The
automatic forced fix would downgrade or otherwise break the working SDK stack,
so the business must accept monitored exposure temporarily or approve an
upgrade project.

**Recommended direction:** Record a time-bounded risk acceptance, monitor
compatible patches, and reassess at each release. Escalate immediately if a
finding becomes critical or is shown to affect the shipped runtime path.

### 8.5-G1 — Complete real-session and device verification

**Gate remaining:** Test two real authenticated athletes plus Android and iOS
development builds through zone setup, protocol execution, RPE capture,
evaluation, interruption, and resume behavior.

**Use case:** Athlete B signs in after Athlete A completes a calibration test.
Athlete B must see none of Athlete A's setup, observations, or pending result;
an interrupted mobile flow must also resume without duplicate records.

**Recommended direction:** Treat this as a release gate, not an optional QA
task. Use real Supabase sessions and at least one physical-device pass per
supported mobile platform.

## Phase 9: first wearable integration

### 9-D1 — Give Polar a production go/no-go decision

**Decision needed:** Approve Polar AccessLink as the first production provider
or stop and select another provider after product, legal, privacy, commercial,
and provider-terms review.

**Why it matters:** The adapter is technically implemented, but no real client,
webhook, credential, athlete connection, or provider processing is active.

**Use case:** A triathlete authorizes Start23 to receive GPS and heart-rate data.
Start23 needs an approved processor relationship and lawful purpose before that
health/location data is processed.

**Recommended direction:** Keep the connector disabled until one documented
go/no-go review covers provider terms, commercial fit, supported regions, data
categories, and exit risk.

### 9-D2 — Approve consent, retention, deletion, and regional-processing policy

**Decision needed:** Approve the athlete-facing consent copy and rules for raw
files, canonical summaries, disconnection, deletion/export requests, regional
processing, and provider brand/attribution.

**Why it matters:** Disconnecting an account, deleting a provider token, and
deleting already imported health/location data are different actions.

**Use case:** An athlete disconnects Polar and then asks Start23 to delete all
imported FIT files while retaining manually entered training history. Product
and support need an unambiguous policy.

**Recommended direction:** Define a data inventory and retention table before
live use. Separate account disconnection from data deletion and make both
choices understandable in the mobile UI.

### 9-D3 — Choose the production callback domain and register the integration

**Decision needed:** Choose the production OAuth callback domain, register the
Polar client and webhook, store credentials in backend deployment variables,
and define credential-rotation ownership.

**Why it matters:** OAuth cannot be tested end to end with production behavior
until the redirect and webhook endpoints are registered with the provider.

**Use case:** An athlete taps **Connect Polar**, approves access in the browser,
and must return to an approved Start23 callback rather than a developer URL.

**Recommended direction:** Use the final backend HTTPS domain, keep every
secret server-side, and assign one operational owner for registration and
rotation.

### 9-D4 — Approve the historical-import experience

**Decision needed:** Decide the default and athlete-facing explanation within
the implemented 1-to-30-day request range. Decide how to communicate that older
backfill is unavailable through this adapter.

**Why it matters:** The implementation enforces the provider's recent-history
limit and does not invent an older archive.

**Use case:** A new user expects six months of Polar history. Start23 can import
only the supported recent window and must avoid implying that the older history
will arrive later.

**Recommended direction:** Let the athlete select a supported range, state the
limit before confirmation, and avoid silently defaulting to maximum data
collection until the privacy review approves it.

### 9-D5 — Choose the failed-import retry operation

**Decision needed:** Choose a deployed retry mechanism, retry count/backoff,
terminal failure state, alerting, and support ownership.

**Why it matters:** Webhook work is safely persisted before processing and a
failure is recorded, but no production schedule currently picks failed work up
again.

**Use case:** Polar accepts the webhook but returns HTTP 503 when Start23 fetches
the exercise. The athlete should not need to disconnect and reconnect to recover
the activity.

**Recommended direction:** Use one bounded Railway scheduled command against the
existing modular monolith, with backoff, a terminal state, and an alert. Do not
introduce Redis, Celery, or another service for the MVP.

### 9-D6 — Define revoked-token and reconnect behavior

**Decision needed:** Decide how revoked or invalid long-lived Polar access is
detected, displayed, retried, and reconnected while preserving valid existing
activities.

**Why it matters:** Polar's implemented model uses a long-lived access token
until deregistration rather than an invented refresh-token flow.

**Use case:** The athlete revokes Start23 from the Polar account dashboard. The
next import should show **Reconnect required**, not repeatedly fail or delete
previously imported canonical activities.

**Recommended direction:** Preserve existing activities, mark the connection as
revoked/reconnect-required, remove unusable credentials safely, and require a
fresh explicit OAuth confirmation.

### 9-D7 — Approve the minimum mobile connector experience

**Decision needed:** Define the smallest production UI for connect, connection
status, import range, progress, failure/retry, disconnect, and privacy links.

**Why it matters:** The backend APIs exist, but no Phase 9 Expo connection or
import screen has been added.

**Use case:** An import fails after three activities were discovered. The
athlete needs to understand whether anything was imported, whether retry is
safe, and whether Polar is still connected.

**Recommended direction:** Build one small settings/integration surface after
provider approval. Show qualitative status and counts, never TSS.

### 9-D8 — Decide the raw FIT file product scope

**Decision needed:** Decide whether raw FIT files remain backend-only archives
for the MVP or require signed downloads, athlete-visible file management, and a
retention/deletion UI.

**Why it matters:** FIT files are stored privately when available, but a missing
FIT file does not invalidate the canonical activity summary. No download API or
raw-file UI exists.

**Use case:** An athlete asks for the original FIT file for use in another
service. Start23 needs either a secure export flow or a clear statement that raw
downloads are not part of the MVP.

**Recommended direction:** Keep raw files backend-only for the MVP unless data
portability requirements demand downloads. Retention and deletion rules are
required even if no athlete-facing download is built.

### 9-D9 — Approve imported-activity matching policy

**Decision needed:** Decide whether wearable activities remain explicitly
unmatched, are suggested to the athlete, or may be matched automatically under
strict deterministic rules.

**Why it matters:** No reviewed rule exists for proximity matching, bricks,
multisport sessions, or ambiguous same-discipline workouts. Current Polar
imports therefore enter the canonical activity path as unmatched.

**Use case:** A Polar run begins 20 minutes after a scheduled run and has a
similar duration. Start23 must decide whether to suggest that workout or require
manual selection; silently attaching the wrong workout would corrupt feedback.

**Recommended direction:** Start with suggestion-only matching and explicit
athlete confirmation. Automatic matching should require a separate reviewed
rule table with ambiguity tests.

### 9-D10 — Accept or refactor the authenticated privileged RPC boundary

**Decision needed:** Security must formally accept the current owner-scoped
`SECURITY DEFINER` design or request a refactor, especially for the read-only
connection and import-list RPCs.

**Why it matters:** Supabase Security Advisor reports warnings for
`start_polar_oauth`, `get_polar_connection`, and `list_polar_imports`. Public and
anonymous execution is revoked, each operation derives `auth.uid()`, and hosted
ownership tests pass, but the warning still requires an explicit review outcome.

**Use case:** A signed-in attacker changes request parameters in an attempt to
enumerate another athlete's import history. The review must prove that identity
is derived from the verified session and cannot be selected by the caller.

**Recommended direction:** Refactor the read-only RPCs to invoker/RLS paths if
that reduces privilege without complicating the contract. Retain a narrowly
reviewed privileged write boundary only where private OAuth state requires it.

### 9-D11 — Enable leaked-password protection

**Decision needed:** Decide when to enable Supabase Auth leaked-password
protection and update authentication/support messaging if required.

**Why it matters:** The project-level Security Advisor still reports this
protection as disabled. This is a shared production-security gate discovered
during the Phase 9 review.

**Use case:** A customer attempts to register with a password already present in
a known public breach. Without the setting, Start23 misses an available control
that could reject that password.

**Recommended direction:** Enable it before production unless product testing
finds a concrete onboarding problem that cannot be solved with clear messaging.

### 9-G1 — Complete live end-to-end integration verification

**Gate remaining:** Verify real OAuth, webhook delivery and replay handling,
historical import, FIT transfer, two-session ownership isolation, Railway
background execution, disconnect/revocation, and Android/iOS runtime behavior.

**Use case:** A real Polar exercise should create exactly one owner-visible
canonical activity, remain private from a second athlete, recover from a
temporary provider failure, and retain no active token after confirmed
disconnect.

**Recommended direction:** Run this only after the provider and privacy go/no-go
decisions, using dedicated test athletes and a written evidence checklist.

## Recommended decision order

1. Appoint the accountable physiology reviewer.
2. Approve the Zone 1-5 model and calibration-planner contract.
3. Decide whether soft ranges and the physiological-sex fallback belong in the
   MVP.
4. Give Polar and its data-processing package a production go/no-go decision.
5. Approve consent, retention, deletion, historical import, and matching rules.
6. Lock the callback domain, retry operation, reconnect behavior, and minimum
   mobile UI.
7. Complete security decisions and live two-athlete/device verification.

## Decision sign-off checklist

- [ ] Named physiology reviewer appointed.
- [ ] Zone 1-5 formulas and rounding approved.
- [ ] Week-1 calibration planner/load contract approved.
- [ ] Soft-range and physiological-sex fallback scope decided.
- [ ] Mobile dependency risk accepted or upgrade funded.
- [ ] Polar production provider approved or rejected.
- [ ] Consent, retention, deletion, regional, and attribution policy approved.
- [ ] Production callback, credentials, webhook, and rotation owner assigned.
- [ ] Historical import, retry, reconnect, raw FIT, and matching policies approved.
- [ ] Privileged RPC review and leaked-password setting decided.
- [ ] Real-session, hosted integration, Android, and iOS evidence accepted.

## References

- [MVP roadmap](mvp-roadmap.md)
- [Backend zone calculation and calibration](backend-zone-calculation.md)
- [API contracts](../architecture/api-contracts.md)
- [Security model](../architecture/security-model.md)
- [Supabase database migration workflow](https://supabase.com/docs/guides/deployment/database-migrations)
- [Supabase Data API explicit-grant change](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
- [Supabase breaking-change changelog](https://supabase.com/changelog?types=breaking-change)
