# Joren V6 final prospective policy decision update

Intake: 2026-11-05, Europe/Amsterdam. Decision/policy version:
`joren-v6-final-prospective-policy-1`. Private offline development evidence.

Base: `experiment/joren-v6-partial-approval` at
`7dc3f22595d4b9e22e1e84abaf148d9bd791fd33`.
Isolated branch: `experiment/joren-v6-final-policy`; worktree:
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-final-policy`.

The product owner supplied these exact Joren quotations in the current task,
“WOMBO — V6 FINAL JOREN POLICY UPDATE: PARTIAL WEEKS AND NO HIGH-INTENSITY
MINIMUM”. This is attributable owner-relayed decision intake. Original answer
dates, a signature, reviewer credentials and an external scientific review-record
identifier were not supplied and are not invented. This version supersedes only
the two statuses below. The previous register, source records, calculations and
test expectations remain intact under their original versions.

## 1. Partial-week permission: confirmed prospectively

Exact question supplied in this intake:

> Als drie trainingen niet binnen het veilige budget passen, mogen we dan minder dan drie sporten plannen, of liever geen plan voorstellen totdat een geschikte combinatie beschikbaar is?

Initial answer:

> Ja, da's goed.

Explicit answer after clarification:

> Ja een gedeeltelijk schema met een of twee soorten inderdaad

The earlier [register, decision 3](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md#3-recovery-and-taper-no-forced-unsafe-three-sport-coverage)
recorded `PARTIAL_APPROVAL; EXACT_FALLBACK_REQUIRES_CLARIFICATION`. The new
clarification resolves permission for a partial week: when a suitable and safe
three-sport plan cannot fit the authorized weekly budget, a week containing one
or two sports may be proposed prospectively, including recovery/taper contexts.
It does not approve any particular omission, ranking or prescription.

Safety and individual suitability remain first. The explicit budget is a maximum.
Injury, recovery, taper, progression and confirmed availability remain mandatory
constraints. No unsuitable sport can be forced, and no workout, minute, permission,
reduction factor or redistribution allowance is supplied by this decision.
No suitable workout retains a safe no-plan/rest/fail-closed outcome. Lack of
evidence is not proof of physiological impossibility.

BIKE/RUN/SWIM 50/30/20 remains a soft planned-load target. It does not require
coverage of absent sports or authorize extra load. No mandatory omission order,
renormalized partial-week target or approved distance metric is introduced.
Exact ranking among competing safe partial plans remains unresolved; the approved
priorities must govern any later evidence-backed algorithm. See
[partial-week evidence](JOREN_V6_PARTIAL_WEEK_FEASIBILITY.md).

## 2. No high-intensity minimum: confirmed prospectively, including BUILD

Exact question supplied in this intake:

> De oude planner vereist een bepaalde hoeveelheid intensieve belasting, terwijl onze nieuwe 80/20-regel een maximum van 20% voorziet zonder minimum. Moet de oude minimumregel volledig verdwijnen, of wil je voor specifieke gevorderde trainingsfasen een afzonderlijke ondergrens behouden?

Exact answer:

> We zullen het zonder ondergrens doen.

The earlier [register, decision 5](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md#5-build-intensity-minima-answer-pending)
was `Answer pending`. It is now `CONFIRMED_PROSPECTIVE_NO_HIGH_MINIMUM`, including
every BUILD week. Zero HIGH active planned time is permitted. The existing maximum
is unchanged: at most 20% HIGH active planned time **per sport per athlete-local
Monday–Sunday week**, with Z1/Z2 LOW and Z3/Z4/Z5 HIGH. Stationary swimming rest is
excluded. Exactly 20% passes the maximum; above 20% fails. Twenty percent is a cap,
not a required amount. All other phase and individual eligibility rules still
apply; an all-easy BUILD plan is not automatically suitable.

This is a prospective scientific decision, not an immediate runtime removal.
[Exact supersession boundary and tests](JOREN_V6_NO_HIGH_MINIMUM_BUILD_POLICY.md)
identify the historical whole-session high-load minima, Z5 selection requirement,
high-load ceiling and scoring that remain unchanged in production.

## Preserved authority and open decisions

| Item | Current status |
| --- | --- |
| IF Z1/Z2/Z3/Z4/Z5 | Confirmed .55/.75/.88/.98/1.15; numerical values only |
| SWIM reference min/100m Z1–Z5 | Confirmed 2.17/2.00/1.83/1.67/1.50 |
| Planned SWIM reference-time estimates | Permitted offline; `ESTIMATED_FROM_APPROVED_REFERENCE_PACE`, estimator `joren-v6-swim-reference-active-time-offline-1` |
| Actual/performed SWIM time | Never inferred; original missing prescribed times remain missing |
| Selection priorities | Safety/suitability; injury/recovery/progression constraints; authorized budget maximum; suitable sport coverage where feasible; allocation closeness before budget utilization; deterministic choices |
| Exact selection algorithm | Still unapproved, including allocation metric, ties and competing partial alternatives |
| Complete IF² method / operational planned-P / Realized V2 compatibility | Still unapproved; confirmed parameters do not approve normalization, rounding or storage precision |
| Athlete/workout suitability | Joren's answer remains pending; level/phase/long-session/recovery/repeat metadata is unresolved |
| Operational estimated-time acceptance | Still unapproved, including uncertain/borderline coverage |
| Catalog replacement, activation and production | Still unapproved; no integration or deployment authorized |

The earlier six-question quotations remain exactly as recorded in the historical
register. The two question strings above are the precise forms supplied in this
new intake, without retrospectively editing the prefixed questions in that register.
The [current Dutch approvals brief](JOREN_V6_REMAINING_OPERATIONAL_APPROVALS_NL.md)
replaces its open-status summary only for the decisions explicitly settled here.

## Implementation and evidence boundary

Only new files are added. The pure Python evaluator is
`backend/benchmarks/v6_final_policy.py`, outside the application package. It reuses
the prior sandbox types, exact hypothetical source-display budget arithmetic and
unchanged active-time evaluator. It enumerates finite supplied alternatives;
there is no winner, default, runtime flag, planner score or training prescription.
Result provenance records this decision version separately from the older
estimator/parameter decision version. `operational_approval` and
`source_method_approved` are always false.

The evidence writer uses the existing 77-row catalog. Real metadata stays
unresolved. Counterfactual supported cases carry explicit `TEST_ONLY` evidence
for a synthetic athlete/week/template/phase and assumed safeguards. These fixtures
are logical tests, never permissions for the actual 77 workouts. Original rows
and source workbooks are unchanged. No source-reconciliation or optimization
campaign was performed.

Root AGENTS.md and the current MVP roadmap were read, together with the current
V6 partial approval register, sandbox, swimming-time report, outstanding decisions,
beginner/budget/allocation reports and preserved BUILD-search correctness report.
There is no nearer AGENTS.md for the changed backend/docs paths. The main checkout's
pre-existing modifications and the A5/A6 release were left untouched.

Private artifacts: [simulations](final-policy/evidence.json),
[verification](final-policy/verification.json), [unchanged regression](final-policy/regression.json).
Final local verification is recorded below. No push, merge, deploy,
migration, catalog activation, A5/A6 change or automatic C3–C8 continuation.

## Final local verification

| Check | Result |
| --- | --- |
| Focused new policy + partial approval + sandbox + C2.1 tests | **213 passed**, 14.38s; 28 new tests, all 185 earlier focused cases retained |
| Complete backend pytest | **2,250 passed**, 188.08s; one existing Starlette/httpx deprecation warning |
| Ruff `check app tests benchmarks` | PASS |
| Ruff `format --check app tests benchmarks` | PASS, 189 files |
| Strict mypy `app tests benchmarks` | PASS, 188 source files; existing `strict=true` preserved |
| Unchanged 40-case planner corpus | All full canonical outcomes and input fingerprints equal prior delivery; all 26 accepted reference completions preserved |
| Corpus outcomes / independent legacy checks | 29 returned pending hypothetical plans, all independently checked; 10 fail-closed; one unchanged `current:build_4` diagnostic timeout |
| Regression artifact | Exact semantic equality with prior partial-approval regression; canonical LF SHA-256 unchanged |
| Finite partial-week oracle | Complete ID-set equality for all subsets at budgets 45, 25.86 and 15.085; 18,675 possibilities per full-deck scope |
| Production/historical custody | No previous tracked file changed: application, source workbooks, historical records/tests, BUILD optimizations, A3–A9 and Realized V2 retained |
| Protected source worktree | Clean at supplied `7dc3f22595d4b9e22e1e84abaf148d9bd791fd33` |
| A5/A6 release | Clean at unchanged `cd3e2dd438031cfb565858d0a5929e9963f7b31f` |
| Mobile/strict TypeScript | Not applicable to these offline-only additions; no mobile/public-contract change |
| Hosted DB/pgTAP/RLS/device/release checks | Not run; existing external gates remain open; no schema, hosted access or migration |

The full backend suite includes unchanged OpenAPI/public-contract, recursive
TSS/private-load leak, A3–A9, Realized V2, retry, stale-version and athlete-confirmation
coverage. No earlier test, expected result or tolerance was weakened. Regression
ran in serial owned subprocesses after the test/typecheck work, with the unchanged
eight-second bound including imports. Host load is uncontrolled. The one timeout
remains a performance limitation, not infeasibility; no optimization was attempted.

From `backend`, using the existing project virtualenv:

```text
python -B -m benchmarks.v6_final_policy_evidence --private-output NEW_PRIVATE_PATH
python -B -m pytest -q -p no:cacheprovider tests/test_v6_final_policy.py tests/test_v6_partial_approval.py tests/test_v6_policy_sandbox.py tests/test_joren_c21.py
python -B -m pytest -q -p no:cacheprovider
python -m ruff check app tests benchmarks
python -m ruff format --check app tests benchmarks
python -m mypy app tests benchmarks
python -B -m benchmarks.v6_policy_sandbox --regression-output NEW_PRIVATE_REGRESSION_PATH
```

The test reproduces the committed private simulation artifact. Writers require a
fresh output path. Final evidence SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| final-policy/evidence.json | `90b35a3f99d3335bbe92f8e4f23103597bb91906b070a2353923674f9183c429` |
| final-policy/regression.json | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` |

This completes only the requested prospective decision intake, offline behavior
and validation. Athlete suitability, operational method/time acceptance and
activation remain blocked as documented. No operational phase or release is
declared complete. The local committed delivery SHA is supplied in the final
response and resolves with `git rev-parse experiment/joren-v6-final-policy`.

WOMBO V6 JOREN POLICY UPDATE COMPLETE — SUITABILITY AND METHOD APPROVALS STILL REQUIRED
