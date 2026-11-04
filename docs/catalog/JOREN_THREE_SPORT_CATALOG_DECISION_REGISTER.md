# Joren three-sport catalog decision register

## Current C2.1 decisions — 2026-11-04

This entry and [current approval evidence](implementation/JOREN_C2_UPDATED_DECISIONS.md#c21-approval)
supersede the older all-open tables below. C2.1-INTENSITY-1 formally confirms
Joren's **maximum 20% high-intensity planned active segment time per sport per
athlete-local week**. Zero high time is valid; zero active time is NOT APPLICABLE;
missing reliable time is UNVERIFIED. Stationary swim rest is excluded. Existing
Z1/Z2 low and Z3–Z5 high taxonomy applies; no TSS or whole-session-focus allocation.
Only an isolated versioned evaluator is implemented, without planner integration.

C2.1-SWIM-1 confirms ordered 300m Z3 → 300m Z2 for TR-SWIM-015–020. A separate
lossless correction manifest is structurally valid; the original remains preserved
and conflicted. Method/precision and release approvals remain open; activation is
disabled. See [correction record](implementation/JOREN_SWIMMING_IF2_CORRECTION_REQUEST_NL.md).

C2.1-BEGINNER-1 records that Joren will supply lighter sessions. The 45 versus
64.5 beginner conflict is **OPEN — AWAITING ACTUAL SOURCE**, with no load increase,
arbitrary shortening, progression exception or premature beginner-readiness claim.
The separate BIKE/RUN/SWIM 50/30/20 planned-TSS allocation still needs target/hard
constraint and infeasibility decisions. Source paces, normalization, Z3 IF,
rounding/storage/P authority, replacement mapping and V2 compatibility remain open.
No C3–C8 work, operational catalog entries, activation or deployment is performed.

## Historical review entries

> Final review update, 2026-11-03: all three sources are now supplied. The current
> entry below supersedes prior-stage availability statements. Historical text
> is retained after the marked boundary; no previous source finding is discarded.

## Current final review — all three sources supplied

This final-stage entry supersedes source-availability statements and outstanding
question identifiers in the historical swimming-stage text retained below. That
text remains original evidence, not the current delivery inventory.

All 61 workouts are supplied and checked: RUN 20 (16single/4mixed), BIKE 21
(13/8), SWIM 20 (9/11). The cycling workbook is7,376 bytes, SHA-256
`5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df`, at
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Fietstrainingen_Definitief_Optie1.xlsx`.
RUN/SWIM/PDF hashes below remain unchanged. B01's **delivery** item is closed;
cycling methodology acceptance is not. IF² reproduces RUN/BIKE displays but
remains an unapproved reconstruction. SWIM published matrix/rest0 is explicit.

There is one Dutch approval brief with six grouped issues; do not send the older
questions as additional separate approval requests:

| Final issue | Earlier IDs consolidated | Present state |
| --- | --- | --- |
| A — Planned source method/precision | R01, new BIKE formula evidence, C04 | OPEN; no formal RUN/BIKE formula approval or operational-P decision |
| B — Version/source replacement | C01, identity part of C05 | OPEN; files/hashes now all present; proposed UUID5 mapping is engineering |
| C — Bucket/phase/athlete scope | C02 | OPEN;61-row proposal, seven-hour beginner exposure explicitly held for scope review |
| D — Mixed block RPE | C03 | OPEN; source session focus kept separate; no hard RPE assigned to recovery |
| E — Swim distance planning/realization | S01–S04 | OPEN in integration scope; fixed source constants and rest0 are resolved facts |
| F — Prospective activation scope | C05 release portion | OPEN; no permission to import/activate/deploy |

Actual approvals are tracked separately from source delivery and engineering
recommendations:

| Issue | Actual new approval received | Approval evidence/date/owner | Effective acceptance |
| --- | --- | --- | --- |
| A | No | None supplied | Not active |
| B | No | None supplied | Not active |
| C | No | None supplied | Not active |
| D | No | None supplied | Not active |
| E | No | None supplied | Not active |
| F | No | None supplied | Not active |

Owner instructions to perform this review, preserve history, avoid activation
and defer PostgreSQL/pgTAP are recorded task constraints, not answers A–F.
Engineering resolves exact seconds parsing, lossless raw/normalized separation,
deterministic UUID5 derivation, immutable lineage and no legacy CSV coercion as
specified in C1–C8. These choices approve no physiological value or athlete scope.
Silence is not acceptance; later answers must include exact scope/version/source
hash and acceptance conditions, retaining this review record.

See [Dutch A–F brief](JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md),
[all 61 reconciliation/metadata](JOREN_THREE_SPORT_FINAL_RECONCILIATION.md),
[actual simulation results](JOREN_THREE_SPORT_PLANNING_SIMULATION.md) and
[implementation C1–C8](JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md).
439 focused tests passed; no app/SQL behavior changed. Eight bounded automatic
search timeouts remain performance findings; explicit build witnesses are not
performance passes. PostgreSQL/pgTAP: **DEFERRED BY OWNER — PRE-BETA**.

## Historical prior-stage report — retained unchanged

Review date: 2026-11-03 (Europe/Amsterdam). Review and preparation only.
Accepted engine: `feat/joren-realized-tss-v2` at `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch/worktree: `review/joren-new-workout-catalog`,
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Swimming originals are in the accepted engine worktree's `docs/trainings`, not the older root checkout:

| Original | Bytes | SHA-256 |
| --- | --- | --- |
| `Zwemtrainingen_Definitief_Optie1.xlsx` | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` |
| `Specificatie Zwem TSS.pdf` | 149021 | `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a` |

Full original paths:
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Zwemtrainingen_Definitief_Optie1.xlsx`
and `F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Specificatie Zwem TSS.pdf`.
Private load numbers below are developer review evidence and must remain outside athlete-facing contracts.

## Overall status and authority

**Three-sport integration is not ready for activation.** Running and swimming
sources are available; cycling is not yet supplied in the searched source
locations. Swimming fixed-distance arithmetic is verified. Running method
provenance, shared selection/version/guidance decisions and distance-only swimming
planning/realization compatibility remain open. No new physiology or metadata
policy is approved by this review.

The running original remains `Looptrainingen_Definitief_Optie1.xlsx`, 7,198 bytes,
SHA-256 `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3`,
in the older root `docs/trainings`. Its 20 rows, 16 structural single-zone and four
mixed findings, 17 zone-method load differences and IF-squared **hypothesis** are
preserved. No swimming evidence confirms that RUN uses the same formula.

## Resolved source/engine facts: do not ask these again

| Fact | Evidence and consequence |
| --- | --- |
| Swim published constants | PDF p.1 explicitly directs software to 0.98/1.44/1.98/2.40/2.70 per 100 m. Use these for this source reconciliation, not raw pace-products. |
| All swim arithmetic | 20/20 one-decimal matches; TR-SWIM-010 exact 28.44, stored/display 28.4; source and derived precision kept separate. |
| Stationary rest load in source method | PDF pp.1–2 and workbook note specify exactly zero; not active Z1 swimming. |
| Swim 0.90 placement | Already reflected in listed sport-specific minute coefficients used by the distance matrix. Additional 0.90 contradicts the worked example. |
| CSS delivery scope | 1:55/100 m underlies the fixed published reference; no athlete-adjustment function exists in delivery or accepted engine. |
| Single/mixed swim count | Nine single Z2; eleven mixed; all are distance-only. |
| Current fallback | Needs genuine P/T plus confirmed A and supported method/version; zero new swims fully eligible now. Mixed rows cannot use whole-session matrix. |
| Existing distance source planning | Immutable original P/distance retained, current `with_current_load` yields P=None; no invented minutes or usable source P. |
| Cycling availability | **CYCLING CATALOG — SOURCE NOT YET AVAILABLE**. Historical BIK rows are not the new workbook. |

## Shared decisions: one question per issue

These questions are for a future accepted specification. They do not require an
answer to finish this review or authorize activation now. Recommendations below
are concrete proposals, not inferred owner decisions.

| ID / owner | Exact question to resolve | Concrete proposed acceptance / engineering consequence | Prior running issue |
| --- | --- | --- | --- |
| C01 — owner/Joren | What immutable catalog/method revision and accepted file-hash manifest identify each sport, and which new IDs explicitly replace which old logical templates? | Register independent sport-source versions bound to original hashes, new TR namespaces and explicit replacement table; retain all prior versions. No merge by title or suffix. | J2 and identity part of J5 |
| C02 — Joren | Do you accept the per-row swimming selection proposal below, and what complete bucket/phase/capability/selection metadata should apply to each RUN row? | Accept or edit explicit row mapping; preserve unchanged planner filters, injury restrictions, repeats/occurrence identity and spacing. Missing metadata withholds selection. | J3 |
| C03 — Joren for prescription intent; engineering for representation | What are the intended per-block exertion ranges for mixed workouts, while preserving each source's session-focus RPE range and stationary rests? | Preserve source range; accept explicit zone-based block guidance under a named mapping version; design a lossless ordered rest representation. Do not widen source ranges or assign Z1/RPE to rest silently. | J4 |
| C04 — owner with Joren's source acceptance | For prospective P, should the importer use the exact approved calculation or the workbook's stored rounded number, and what general rounding/storage policy applies? | Retain raw source P separately from exact derived P and method/precision evidence; recommend unrounded approved computation for consumers only after acceptance. Bind corrections to original occurrence P; preserve history. | Precision part of J1 |
| C05 — owner | After all three accepted intakes and gates, what prospective activation date/set and rollback selection are approved? | Add immutable successors/new templates; keep old records/readers; rollback affects future selection and never rewrites accepted occurrences. No activation in this task. | Remaining J5 |

C01 is a governance/mapping decision; hashes are already known and do not need to
be rediscovered. C04 preserves original workbook values regardless of which future
operational P is selected. C02 cannot make distance-only swim capacity usable by
itself; S02 must define that scope separately.

## Sport-specific questions

| ID / owner | Exact unresolved question | Evidence, recommended next artifact and current boundary |
| --- | --- | --- |
| R01 — Joren | What exact source formula/anchors and rounding produced the 20 RUN TSS values, including 86.2 for TR-RUN-009 and raw 87.59999999999999 for 017; is 1.15 already incorporated? | Preserve running J1. Numerical IF reconstruction is not confirmation. Obtain versioned worked examples. No coefficient tuning or source overwrite. |
| S01 — Joren | Is this fixed 1:55-reference matrix intended as the catalog P reference for every athlete, or is a separate CSS-dependent model intended? | PDF's delivered computation is fixed. Propose a versioned fixed-source reference initially; any CSS-dependent alternative requires a complete separately reviewed function before use. No inference of actual/planned minutes. |
| S02 — Joren/owner | Should distance-only swims become eligible for load-target planning using the published distance P while planned duration remains absent, or should they remain excluded until an independently approved prescription supplies time? | Present engine withholds P. If distance selection is desired, specify a new planned-load method/version and how unknown swim duration affects weekly 80/20, availability and phase/capacity decisions. Do not change coefficients or fabricate time. |
| S03 — Joren for evidence semantics | For actual swimming with identified wall rests, what active-versus-elapsed duration and rest-evidence policy can establish complete measured coverage without counting rest as a zone? | Zero rest contribution is resolved; current zone-minute API cannot distinguish known rest from unobserved gaps. Require explicit trustworthy evidence/completeness policy. Until then preserve partial status. |
| S04 — owner/Joren | Should a separately specified distance-based realized fallback be commissioned, or should distance-only/RPE-only swim completion remain unavailable for automatic weekly load? | Neither the duration model nor fixed planned P approves a distance-ratio alternative. If commissioned, supply formula, confirmed actual distance, eligibility/reliability/mixed exclusions, provenance and scientific review. Not implemented. |
| B01 — delivery owner | Supply the new cycling workbook and its applicable method/specification evidence when finalized. | Not a formula approval request yet. Inspect every actual sheet/row before adding sport-specific questions; do not assume RUN/SWIM methods or multiplier handling. |

S04 is a scope decision and may be deferred without blocking retention of source
evidence; it does block any claim of full RPE-only swimming coverage. S03 blocks
automatic “complete” classification of rest-containing observed gaps, not ordinary
supported actual zone-minute arithmetic. These distinctions avoid duplicating or
reopening the PDF's explicit zero-rest rule.

## Concrete swimming selection proposal (unapproved)

| IDs | Proposed bucket | Proposed phase eligibility | Proposed capability and repeat treatment |
| --- | --- | --- | --- |
| TR-SWIM-001–009 | low | base, build, recovery, taper | Confirmed swim pace/CSS; incompatible HR fallback; automatic/swipe only after S02; repeat with separate occurrence IDs, existing bound 24 |
| TR-SWIM-010–011 | high | build | Same capability; explicit mixed block guidance/rest events; existing 48 h swim-high spacing |
| TR-SWIM-012–013 | high | build | Same; preserve 400/500 m repetition and rest-count differences |
| TR-SWIM-014 | high | build | Same; retain pyramid order and eight rests |
| TR-SWIM-015–020 | high | build, Z5 selectable only at build position 4 under current rules | Same; preserve speed/resistance rest differences; no matrix fallback |

Per-row version is in the [swimming validation](JOREN_SWIMMING_CATALOG_VALIDATION.md).
The running selection question remains open as recorded in its original reports;
this grouping does not assign swimming tags to running workouts. No new minimum
beginner distance, per-athlete capacity, rest cutoff or safety threshold is invented.

## Gate ownership and deferred verification

Engineering can implement the accepted manifest, lossless segments, immutable
source/load lineage and tests only in a later authorized task. PostgreSQL/pgTAP
is **DEFERRED BY OWNER — PRE-BETA**. Fresh/upgrade replay, RLS/owner/grants,
actual numeric storage, concurrency/idempotency and stale occurrence/proposal
checks remain execution gates; static contracts are not a pass. Scientific/
release review for new methods, real-token/device workflows and complete catalog
performance/three-sport multi-week scenarios also remain open. No push, merge,
deployment or hosted mutation is authorized by the existence of this register.
