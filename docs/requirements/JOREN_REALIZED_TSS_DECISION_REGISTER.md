# Joren realized-load decision register

Date: 2026-11-03. Baseline: `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6`.

All options below are **PROPOSED BUT NOT APPROVED**. P0 means required before implementing the affected calculation/integration; P1 means required before enabling that scope. Owners are Joren for methodology and the product owner for product/contracts, with an accountable qualified reviewer where required. Approval should record the chosen option, exact versions, date and immutable record reference for each ID. Silence is not approval.

Evidence IDs refer to the [integration review](JOREN_REALIZED_TSS_MATRIX_INTEGRATION_REVIEW.md#source-authority-and-conversation-traceability); fixture groups refer to the [test matrix](JOREN_REALIZED_TSS_TEST_MATRIX.md). Implementation slices must cite the decisions they consume.

Confirmed inputs are not reopened: O01 actual duration must be included; O02/O03 subjective estimation and unvalidated heuristic limits are acknowledged by Joren as relayed by owner; O05 database execution is deferred. The exact duration formula remains open. O04 is both a **DOCUMENTATION DISCREPANCY** and an **IMPLEMENTATION CONFLICT**, supported by code/API/tests. D01 is an internal PDF mathematical discrepancy. Neither is resolved by this document. Scientific uncertainty is labelled **SCIENTIFIC VALIDATION LIMITATION**, not a failing arithmetic test.

## D01 - Matrix authority

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** For planned Z4/reported Z1 and planned Z5/reported Z2, is factor 0.600 authoritative, or must it be 0.625 under the stated linear rule?
- **Current code:** No active 5x5 matrix (C01-C03).
- **PDF / discussion:** P01 gives0.600; P03's additive12.5% steps give0.625 before the0.600 floor.
- **Proposed option:** Ask Joren to publish an explicit authoritative25-cell table plus explanation of the two exceptions; preserve the verified PDF as evidence, not silently correct it.
- **Alternatives:** Approve capped linear formula instead; or supply another complete deterministic rule. No option chosen here.
- **Mathematical impact:** At P120,72 versus75; at A/T0.5,36 versus37.5. Both require distinct versioned fixtures.
- **Example:** P120,T120,A120,p4,q1.
- **Required tests:** All25 cells, both -3 cases, floor/ceiling/diagonal/monotonicity; M01-M25.
- **Risk if unresolved:** Two conforming-looking implementations can disagree; source authority is unresolved.

## D02 - Duration function and overruns

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** For otherwise eligible sessions, is duration adjustment exactly A/T, and what happens when A>T: uncapped ratio, capped ratio, different final cap, or unavailable?
- **Current code:** Observed load uses actual zone time; mean-HR uses actual full duration. No planned-duration ratio (C01-C02).
- **PDF / discussion:** Duration absent; caps describe matrix factors, not final load. O01 confirms duration inclusion only.
- **Proposed option:** Consider A/T for narrowly approved unchanged single-zone sessions; leave overrun eligibility/caps explicit, without inventing a numeric safety bound.
- **Alternatives:** Use min(A/T,1), an owner-specified cap, or no matrix estimate for overruns; require separate approval for any final-load cap.
- **Mathematical impact:** P120,A180,T120,M1.25 gives225 under uncapped ratio versus150 with ratio capped1.
- **Example:** Matching zones, P120,T120,A60 gives60 candidate, PDF120.
- **Required tests:** U01-U05 and N01-N08; ensure ratio not applied twice and sport multiplier not repeated.
- **Risk if unresolved:** Wrong cap semantics can inflate later targets or defeat actual-duration correction.

## D03 - Definition of planned zone

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Which immutable field supplies planned zone p for single-zone and mixed-zone workouts, and are mixed sessions eligible at all?
- **Current code:** Ordered zone/RPE/protocol segments and whole low/high bucket exist. Processing expectation has no single p (C02,C05,C18).
- **PDF / discussion:** Rows assume one planned zone based on IF/goal; no aggregation algorithm.
- **Proposed option:** Require an explicit approved single-session zone or restrict fallback to genuinely single-zone unchanged prescriptions.
- **Alternatives:** Owner-approved dominant/target zone; a fully specified segment-level model with execution evidence; otherwise unavailable.
- **Mathematical impact:** Bike15Z1+30Z5+15Z1 has P75 but no uniquely defined p. Choosing1 versus5 with reportedZ1 gives75 versus45 at equal duration.
- **Example:** Mixed60-minute interval session.
- **Required tests:** S01-S04; ties, recovery intervals, RPE-only/protocol targets, source-catalog sessions.
- **Risk if unresolved:** An arbitrary representative zone silently becomes a new physiological formula.

## D04 - Incomplete or changed structure

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Should warm-up-only, skipped-hard-block and changed-structure sessions be ineligible for a whole-session duration-ratio estimate unless explicit execution evidence supports another approved method?
- **Current code:** No per-segment completion contract; observed partial time retained; processing complete is not prescription-complete (C01,C04).
- **PDF / discussion:** No structure/partial-session rule; its floor paragraph ambiguously discusses missed intensity while asserting time was performed.
- **Proposed option:** Mark structure-unknown/changed cases ineligible for fallback; keep observed results and subjective feedback.
- **Alternatives:** Approve clearly labelled uniform-average assumption; or design segment execution inputs and a new independently reviewed calculation.
- **Mathematical impact:** For P75,T60,A15 easy warm-up, measured7.5 versus candidate11.25 using illustrative p5,q1.
- **Example:** Formal-model interval counterexample.
- **Required tests:** S01-S04 plus retry/persistence of structure eligibility; never invent completed segments.
- **Risk if unresolved:** Duration-adjusted estimates can still overstate skipped intensity and feed unsafe progression assumptions.

## D05 - Measurement selection

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** May a matrix estimate be selected only after current observed/mean-HR methods are unavailable, and must partial observed data remain selected without extrapolation? What is the treatment of explicit all-zero zone bins?
- **Current code:** Partial bins outrank HR. HR branch runs only if bins are None; all-zero array remains unavailable. sRPE inactive (C01-C02).
- **PDF / discussion:** No measured-data hierarchy.
- **Proposed option:** Preserve current observed and approved HR precedence. Do not fill gaps or sum an entire RPE estimate with observed subtotal. Require explicit eligibility for all-zero bins.
- **Alternatives:** Store RPE estimate for comparison without selection; approve a distinct selection policy for partial data; no matrix fallback at all.
- **Mathematical impact:** Run partial41/60 currently40.76; replacing it with P120*0.5 is a semantic change, not a correction.
- **Example:** Observed41-minute subset plus averageHR and rpe8.
- **Required tests:** H01-H06; complete/partial/all-zero/absent bins, known/pending/no profile, unavailable swim.
- **Risk if unresolved:** Heuristic result could overwrite better evidence or double-count a session.

## D06 - Missing, zero and performed-duration truth

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Should missing A/T or T=0 always make the fallback unavailable; how is A=0 represented, and must the prefilled activity duration be explicitly confirmed as performed time?
- **Current code:** Duration positive<=1440; only distance-only swim may omit. UI prefills planned duration. No zero completed-activity path (C04,C16).
- **PDF / discussion:** No duration semantics. O01 requires performed duration, not merely prescribed time.
- **Proposed option:** Missing/zero denominator -> unavailable; do not substitute A=T. Preserve existing zero rejection until a separate skipped-session contract exists. Confirm performed-time source without redesign.
- **Alternatives:** Separate not-started/missed state; provider elapsed versus moving-time policy; explicit owner-approved duration confirmation design.
- **Mathematical impact:** Missing is undefined, not neutral1; A0 algebraic0 does not authorize a completed zero-load session or60% floor.
- **Example:** No-duration swim and a not-started planned ride.
- **Required tests:** U06-U13;0/null/negative/nonfinite; prefill changed/confirmed; missing duration must not fabricate load.
- **Risk if unresolved:** False precision, division errors or planned duration masquerading as actual performance.

## D07 - RPE mapping migration scope

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Is new mapping 1-2/3-4 limited to the new estimate version, or does it also replace catalog, public guidance and calibration target ranges?
- **Current code:** rpe3->Z1; Z1 displayed2-3, Z2=4. API emits old guidance and tests reject(3,4); calibration consumes shared resolver (C06-C07,C11).
- **PDF / discussion:** rpe3->Z2; Z1=1-2 and Z2=3-4.
- **Proposed option:** Prefer estimate-specific versioned mapping while explicitly retaining historical target semantics; seek separate approval if all guidance should migrate.
- **Alternatives:** Full prospective mapping migration with versioned source templates, API labels and calibration contracts; or revise new PDF mapping.
- **Mathematical impact:** At p2,r3,P120, old mapping gives0.875*120=105 if reused; PDF gives120. This is a hypothetical new-calculator misuse, not current load behavior.
- **Example:** RPE3 plannedZ2.
- **Required tests:** R01-R10, catalog/calibration/mobile contract fixtures, historical rendering.
- **Risk if unresolved:** Changing a shared helper could reinterpret stored prescriptions or alter calibration semantics.

## D08 - RPE input strictness and session meaning

**Priority:** P1. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Must the new calculator accept only integer Session-RPE1-10 excluding bool, and should existing API coercions remain compatible or be rejected prospectively?
- **Current code:** Pydantic accepts true->1, string3->3,3.0->3; rejects3.5,0,11. Mobile normally sends integer scores; calibration has separate block RPE (C04,C06).
- **PDF / discussion:** Specifies Session-RPE1-10; no transport coercion/timing policy.
- **Proposed option:** Pure function exact int, not bool. Keep session versus calibration-block scores distinct; review API strictness separately.
- **Alternatives:** Prospectively strict DTO with compatibility/version plan; retain validated API coercion and pass canonical integer.
- **Mathematical impact:** true currently becomesRPE1/Z1; it must not silently become an intentional athlete rating in a strict new path.
- **Example:** Boolean/string/integral-float inputs.
- **Required tests:** R11-R18, end-to-end existing integer clients, no scalar rounding of3.5.
- **Risk if unresolved:** Accidental ratings or unannounced client breakage; calibration RPE misused as whole-session feedback.

## D09 - Planned basis, occurrence and unplanned work

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Which immutable planned-load methods are eligible, what if P=0 or absent, and are unmatched/external activities excluded from matrix estimation?
- **Current code:** Timed source load retained; other planned load from segments; distance-only load absent. Planned occurrence and revision persisted. Current processing context lacks P-method/T/segments (C05,C10,C18).
- **PDF / discussion:** Assumes expectedTSS and plannedzone; no unplanned/version/zero contract.
- **Proposed option:** Require exact owner-matched approved occurrence/revision and compatible P/T/method; P absent/unmatched -> unavailable. Do not recompute P from a current template.
- **Alternatives:** Approve source-method eligibility table or a separately specified unplanned model; explicit zero-plan semantics.
- **Mathematical impact:** Different planned source revisions can have distinct P despite same duration. Old P must not be replaced by newer catalog load.
- **Example:** Repeated identical workouts have different occurrence IDs; source timed ride versus distance-only swim.
- **Required tests:** P01-P07; legacy P/version rejection, repeated IDs, stale/wrong-owner context.
- **Risk if unresolved:** Wrong plan basis, unit mixing or historical mutation; no baseline for unplanned estimates.

## D10 - U-001 weekly completeness

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** For each mixed week, which subtotal/quality fields must be returned and which evidence classes produce a planner-usable weekly load?
- **Current code:** v13 SUM ignores NULLs while counting all activities; v14/v15 add no completeness state (C08-C09,C17-C18).
- **PDF / discussion:** No aggregation contract.
- **Proposed option:** Separate known subtotal from nullable usable load. Carry counts/methods/versions/coverage and reasons; do not fill missing values. Approve an explicit eligibility table.
- **Alternatives:** Allow labelled mixed-method totals; observed-only subtotal for constrained uses; hold/fail closed. No numeric eligibility threshold supplied.
- **Mathematical impact:** 48 complete +34.20 partial +pending yields82.20 known subtotal, not complete weekly load.
- **Example:** Three60-minute bike sessions with mixed availability.
- **Required tests:** W01-W10, SQL/API/typed consumer parity deferred to integration; retain pending/unavailable/legacy distinctions.
- **Risk if unresolved:** Incomplete subtotal can become evidence of full-week adherence or undershoot.

## D11 - Planning consumer eligibility

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** For complete-observed, partial, mean-HR, RPE-estimated, mixed and unavailable weeks, which may drive 10% progression, debt,42-day baseline and intensity decisions?
- **Current code:** resolve_target uses any non-null realized value; NULL holds; fatigue/missed undershoot uses realized*1.10;>=80% and>110% branch thresholds exist. Classified intensity needs>=60% coverage (C09,C15).
- **PDF / discussion:** Says cap avoids runaway weekly plans, but defines no downstream eligibility.
- **Proposed option:** Approve per-decision evidence eligibility, preserving current precedence and constants. Proposed estimates should not enable growth until explicitly approved.
- **Alternatives:** Use only for feedback; permit debt/hold but not growth; fully approve comparable estimated totals. No choice assumed.
- **Mathematical impact:** P100, known subtotal79 versus estimate80 can change a boundary from baseline to planned110; rounding also matters.
- **Example:** Mixed week near80% or110%, sick week, returning athlete.
- **Required tests:** W11-W20; recovery/taper/injury, missing/zero distinction, baseline denominator and first-plan provenance.
- **Risk if unresolved:** New load semantics silently change multi-week behavior despite unchanged progression coefficients.

## D12 - Qualitative feedback and corrections

**Priority:** P1. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Should RPE-estimated loads participate in overshoot/perfect-match/unplanned classification, or retain incomplete/estimated feedback with existing fatigue signaling?
- **Current code:** Noncomplete measurement bypasses numeric matching; low/RPE>=7 can still flag hidden fatigue. System plan changes remain pending (C03,C13).
- **PDF / discussion:** Numerical estimate only; no application match/proposal contract.
- **Proposed option:** Retain honest estimated status and existing subjective-fatigue signal; decide comparison eligibility explicitly, without labelling estimates measured complete.
- **Alternatives:** A separate versioned qualitative policy for comparable estimates; feedback-only initially.
- **Mathematical impact:** P120,M1.25 gives150, exceeding current115% activity overshoot boundary if eligible; noncomplete current path instead deviates.
- **Example:** Planned low session rated8.
- **Required tests:** Q01-Q05; zero/NULL planned load, no auto-activation, correction proposal ownership/staleness.
- **Risk if unresolved:** False perfect matches or unexpected pending corrections; fatigue can be double-counted as measured excess.

## D13 - Rounding and numeric context

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** What Decimal precision/input scale, final storage precision and raw-versus-rounded threshold policy must the new estimate use?
- **Current code:** Zone calculations retain Decimal precision; Start-TSS alone has final one-decimal half-up convention. SQL load numeric has no fixed scale (C01,C08,C10).
- **PDF / discussion:** Factors decimal; no arithmetic/rounding policy.
- **Proposed option:** Fix a reproducible Decimal context; avoid intermediate ratio rounding; propose one final ROUND_HALF_UP if one-decimal storage is approved, preserving raw calculation inputs.
- **Alternatives:** Store unquantized context-defined result; approved alternative scale/rounding. Do not inherit Start-TSS rounding automatically.
- **Mathematical impact:** P1,T3,A1,M1.125 gives0.375; proposed one-decimal result0.4. Ratio0.33 first gives0.37125.
- **Example:** P0.1,T3,A1,M1.125 ->0.0375; one-decimal0.0 differs from missing.
- **Required tests:** N01-N08; repeating ratios, ties, threshold neighbors, negative/nonfinite, Decimal context.
- **Risk if unresolved:** Cross-runtime drift or thresholds changed by inconsistent rounding.

## D14 - Historical and correction policy

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Are all pre-activation loads retained unchanged, and may a current-week RPE revision append/reselect only an already-new-method estimate while retaining its original plan snapshot?
- **Current code:** Old methods and private before-update audit snapshots preserved; current-week expected_current_rpe checks; meanHR/profile immutable. New version currently misroutes as legacy (C02,C13).
- **PDF / discussion:** No history/correction policy.
- **Proposed option:** No retroactive recalculation. Append new-method revisions with original approved P/T/p and previous result; dispatch explicitly by stored method/version.
- **Alternatives:** Separate opt-in versioned migration proposal with scope/audit; freeze new-method estimates against corrections; neither assumed approved.
- **Mathematical impact:** Changing RPE3->8 on p2,P120 could change120->150 under new method; measured result must stay unchanged.
- **Example:** Retry after committed correction and historical record under retired method.
- **Required tests:** V01-V08; stale correction/window/HR immutability, no legacy reroute, byte-preserved old snapshots.
- **Risk if unresolved:** History rewritten, lost provenance or corrected new records recalculated with retired formula.

## D15 - Late measurements and provider coexistence

**Priority:** P1. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** When better evidence arrives after an RPE estimate, may selection change through an append-only event, and does this affect already-approved future plans?
- **Current code:** Polar summary/FIT storage exists, no FIT-to-zone calculation; no Garmin/Strava adapter. Completed meanHR observation currently immutable (C12-C14).
- **PDF / discussion:** No provider/late-evidence precedence.
- **Proposed option:** Preserve every result and append selected-source event under explicit policy; never auto-rewrite approved plans. Keep new provider work outside scope.
- **Alternatives:** Do not revise selection after completion; permit prospective use only; explicit owner reapproval workflow.
- **Mathematical impact:** Estimated75 and later observed60 are two results, not an additive135.
- **Example:** Delayed duplicate Polar import / later zone summary.
- **Required tests:** H07-H10,V09-V11; provider dedupe, metric origin, conflict/retry, plan approval boundaries.
- **Risk if unresolved:** Double counting, provenance loss, or provider brand treated as scientific authority.

## D16 - Version activation and persistence contract

**Priority:** P0. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Which exact new calculation/aggregate policy versions and approval record activate the behavior, and what forward-only storage/RPC contract supports them without changing old readers?
- **Current code:** Phase13 load and planning-v2 separate. CHECKs/RPC dispatch hardcode known methods; weekly filter admits only Phase13 (C02,C08,C18-C19).
- **PDF / discussion:** Document1.0 does not identify deployable ruleset or storage contract.
- **Proposed option:** Reserve joren-realized-tss-matrix-1 as proposed name; append versioned private calculations and explicit selection; version aggregate consumer policy. Activate only after decisions, fixtures and integration gates.
- **Alternatives:** New compatible versioned primary-load format; separate estimate table and selected pointer; owner chooses schema scope. No applied migration edited.
- **Mathematical impact:** A new label alone currently risks SQL rejection, weekly omission and legacy correction dispatch.
- **Example:** New version alongside old activity, plan and profile versions.
- **Required tests:** V01-V12, private RLS/grants/RPC tests at integration; rollback mixed-version readers.
- **Risk if unresolved:** Version string gives false provenance while code still interprets old semantics.

## D17 - Multi-sport and session boundaries

**Priority:** P1. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Must each swim/bike/run component have its own matched P/T/p/A/RPE, with combined bricks and other sports excluded until a separate allocation rule is supplied?
- **Current code:** Activity Discipline is swim/bike/run; goals may combine sports. No generic brick-load split or other-sport formula (C04,C10,C14).
- **PDF / discussion:** Triathlon branding but one planned/experienced zone per session; no leg allocation.
- **Proposed option:** Component activities only when independently observed/matched; no allocating one RPE/duration across disciplines.
- **Alternatives:** Approve a fully specified component/session split and transition-time policy later; leave combined sessions unavailable now.
- **Mathematical impact:** Splitting120 equally across bike/run creates arbitrary sport-specific loads without actual leg evidence.
- **Example:** One90-minute brick with one sessionRPE.
- **Required tests:** S05-S08; transitions, partial leg, overlapping/matched occurrence identities.
- **Risk if unresolved:** Fabricated per-sport load, duplicate imports, inconsistent weekly composition.

## D18 - Scientific review and athlete wording

**Priority:** P1. **Status:** PROPOSED BUT NOT APPROVED.

- **Exact question:** Who signs the new heuristic scope and validation limitation, and which privacy-safe wording distinguishes stored feedback from an estimated assessment?
- **Current code:** Versioned production review required; no private TSS in athlete contracts; existing subjective feedback separate from calibration (C04,C19).
- **PDF / discussion:** Strong physiological explanation but no validation references; O02/O03 acknowledge estimation limits.
- **Proposed option:** Record accountable reviewer, exact versions/scope and immutable decision reference. Proposed wording: feedback and performed duration saved; assessment is an estimate. No measured-work claim or TSS.
- **Alternatives:** Keep estimate internal/feedback-only until review; later validated model under separate version. No LLM-derived scientific approval.
- **Mathematical impact:** No numeric conversion can be certified merely because25 arithmetic fixtures pass.
- **Example:** Fatigued athlete reports higher RPE for same external work.
- **Required tests:** Q06 privacy/wording, V12 activation gate, leak tests across errors/logs/accessibility/LLM.
- **Risk if unresolved:** Scientific authority overstated or private load exposed; local tests mistaken for release approval.

## Approval handoff

Resolve D01-D07 and D09-D11 before selecting the core algorithm and eligible planning inputs. D13/D14/D16 govern reproducibility, persistence and history. D08/D12/D15/D17/D18 must be resolved before enabling their input, feedback, late-evidence, multi-sport or release scopes; an explicitly disabled scope can be documented instead of inventing behavior. Preserve all earlier accepted coefficients and progression constants.

An implementation may start only within an explicitly approved subset and must fail closed for the rest. This specification does not supply the approvals. The owner defers database execution to integration/release; that gate remains open without preventing this specification handoff.

