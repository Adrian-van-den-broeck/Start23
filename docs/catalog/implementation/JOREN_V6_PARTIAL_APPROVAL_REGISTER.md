# Joren V6 partial approval register

Intake: 2026-11-05, Europe/Amsterdam. Version: `joren-v6-partial-approval-1`.
Private development evidence; offline and inactive.

Base: `experiment/joren-v6-policy-sandbox` at
`4cb3a12e3f13b37a1d66c91ae265f99547370af9`. Follow-up branch:
`experiment/joren-v6-partial-approval`; isolated worktree:
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-partial-approval`.

The product owner relayed Joren's answers and subsequently supplied the exact
six questions below in this task. These are verbatim intake quotations, not an
invented signed scientific review. Original answer date, reviewer identity,
signature and external review-record reference were not supplied. Earlier
C1/C2/C2.1/V6 reports and artifacts remain historical evidence at their original
versions. This addendum supersedes only the specific pending parameter and
prospective-policy statuses identified below.

## 1. Numerical values; complete calculation method still open

Exact question:

> TSS-formule: Kun je Z3 IF = 0,88 bevestigen, samen met de zwemreferentietijden van 2,17 / 2,00 / 1,83 / 1,67 / 1,50 min per 100 m? Klopt de volledige IF²-berekening inclusief normalisatie en afronding op één decimaal? Moeten we de bron-TSS of de exact herberekende TSS als officiële geplande belasting gebruiken?

Exact answer:

> Ja, de waarden kloppen.

| Parameter | Confirmed value |
| --- | --- |
| Z1 IF, previously confirmed | 0.55 |
| Z2 IF, previously confirmed | 0.75 |
| Z3 IF, newly confirmed | 0.88 |
| Z4 IF, previously confirmed | 0.98 |
| Z5 IF, previously confirmed | 1.15 |
| Z1 swim reference minutes/100m | 2.17 |
| Z2 swim reference minutes/100m | 2.00 |
| Z3 swim reference minutes/100m | 1.83 |
| Z4 swim reference minutes/100m | 1.67 |
| Z5 swim reference minutes/100m | 1.50 |

**CONFIRMED_VALUES_ONLY.** The answer confirms the numerical values. It does not
answer the other parts of the bundled question. Full formula/normalization,
application of source multipliers, intermediate rounding, final rounding rule,
raw storage precision, official operational planned-P authority (source versus
recalculation), and Realized TSS V2 compatibility remain unapproved. IF² direction
was already confirmed; a matching display does not approve the complete method.

The new version supplies these parameters only to the existing experimental
calculator for offline fixtures. The diagnostic formula remains
`sum(minutes * IF²) * 100/60 * source_factor`, without intermediate rounding,
with exact rational evidence and the existing local Decimal review conversion.
That formula is an explicitly unapproved experiment. Its numerical results are
unchanged from the former reconstruction. The new evidence changes parameter
authority, not method authority. `require_operational_source` still rejects.

Historical `CONFIRMED_IF` with missing Z3, reconstructed inputs, fixed swim matrix,
exact-second experiments, source lexemes, manifests and historical occurrence
values retain their original version and meaning. No history is recalculated.
The new confirmed decimal-minute references encode 130.2/120/109.8/100.2/90 seconds
for the experimental calculator; these are parameters, not athlete durations.

## 2. Prospective beginner selection priorities

Exact question:

> Beginnersschema: Mijn voorkeur is dat het weekbudget een maximum is, niet iets dat volledig moet worden opgevuld. Eerst veiligheid en geschiktheid, dan waar mogelijk één training per sport, vervolgens de 50/30/20-streefverdeling en pas daarna budgetbenutting. Akkoord?

Exact answer:

> Ok.

The owner's scoped intake records agreement with this prospective, versioned
priority order:

1. Athlete safety and suitability.
2. Injury, recovery and progression restrictions.
3. Explicit authorized weekly budget as a maximum.
4. One suitable session per sport where feasible.
5. Closeness to the 50/30/20 triathlon target.
6. Remaining budget utilization.
7. Deterministic tie-breaks.

Coverage cannot override the first three priorities. The supplied budget is a
maximum, not a fill requirement; 45 is the existing zero-history example, not a
new global ceiling. No numerical allocation-distance metric, tolerance, exact
tie-break implementation or replacement of legacy minimum-fill semantics is
approved by this answer. The earlier L1/UUID ranking experiments remain diagnostic.
The legacy planner's scoring, tolerances, BUILD search and long-session fallback
are unchanged; no authoritative new selector is implemented here.

The actual automatic **45.1** result exceeds the prospective **45** ceiling by
**0.1**. The **40.2**, **43.1** and **44.8** examples remain hypothetical selection
witnesses, including those accepted as explicit legacy draft submissions. None
is an approved prescription, automatic replacement or evidence of suitability.

## 3. Recovery and taper: no forced unsafe three-sport coverage

Exact question:

> Herstelweken: Als drie trainingen niet binnen het veilige budget passen, mogen we dan minder dan drie sporten plannen, of liever geen plan voorstellen totdat een geschikte combinatie beschikbaar is?

Exact answer:

> Ja, da's goed.

**PARTIAL_APPROVAL; EXACT_FALLBACK_REQUIRES_CLARIFICATION.** This question offers
two alternatives. The answer does not choose between partial plan and no plan,
or define which sport could be omitted and by what priority. It confirms that
full three-sport coverage must not be forced by exceeding safe constraints.
It grants no authority to drop a sport or generate an incomplete athlete-facing
plan. Existing fail-closed behavior and restrictions are retained.

The existing finite one-per-sport experiment found no combination at recovery
25.86 or taper 15.085; its minimum was 29.3. This is not proof of physiological
impossibility, approval of a partial week or permission to change reduction factors.

## 4. Estimated planned swimming active time

Exact question:

> 80/20 bij zwemmen: Kun je betrouwbare geplande actieve zwemtijden voorzien? Zonder die tijden kunnen we niet exact controleren of maximaal 20% van de actieve tijd hoogintensief is.

Exact answer:

> We kunnen de referentie tijden uit punt 1 gebruiken.

**OFFLINE_PLANNED_ESTIMATION_APPROVED.** The confirmed two-decimal reference
minutes/100m may estimate planned active swimming time from the exact ordered
prescribed zone distances. They are not measured times or individualized
prescribed times. Original distance, source cells, segment identities and missing
individual durations remain intact. Stationary wall rest contributes zero active
time. Provenance is `ESTIMATED_FROM_APPROVED_REFERENCE_PACE` under estimator
`joren-v6-swim-reference-active-time-offline-1`.

The offline sport-week result is `ESTIMATED_COMPLIANT` or `ESTIMATED_EXCEEDED`;
authoritative-duration compliance remains `UNVERIFIED`. No performed duration,
Realized TSS, compatibility approval, API/database/planner activation or approved
operational safety gate follows. See the [estimator report](JOREN_V6_SWIM_ESTIMATED_ACTIVE_TIME.md)
for exact arithmetic, all 22 swims, sensitivity and limitations.

## 5. BUILD intensity minima: answer pending

Exact question:

> BUILD-weken: De oude planner vereist een bepaalde hoeveelheid intensieve belasting, terwijl onze nieuwe 80/20-regel een maximum van 20% voorziet zonder minimum. Moet de oude minimumregel volledig verdwijnen, of wil je voor specifieke gevorderde trainingsfasen een afzonderlijke ondergrens behouden?

Answer status: **Answer pending.** No Joren quotation or decision exists yet.
BUILD minima and training-phase suitability are unchanged. Neither zero-HIGH
permission in the prospective maximum nor numerical estimation retires legacy
minima. No new minimum is invented.

## 6. Athlete/workout suitability: answer pending

Exact question:

> Geschiktheid: Kun je per training of trainingscategorie aangeven voor welk niveau en welke fase die geschikt is, inclusief beperkingen rond lange sessies, herstel en herhaling?

Answer status: **Answer pending.** No Joren quotation or decision exists yet.
Beginner eligibility, phase suitability, long-session restrictions, repetition
eligibility and athlete capability/suitability metadata are unchanged. All real
77 rows still lack approved individual suitability evidence. No reference pace
or sensor capability proves readiness.

## Implementation and verification custody

Only new offline benchmark modules, independent fixtures, tests and private
reports/evidence are added. No existing application module, test, source workbook,
historical report, migration, public contract or active configuration is changed.
No push, merge, deploy, migration, catalog activation or A5/A6 release change.

Root AGENTS.md and the current MVP roadmap were read, together with the V6
policy/approval gates, IF²/source-method precision, strict-budget feasibility,
allocation, beginner simulation, and swimming reconciliation/Realized V2 reports.
Only root AGENTS.md applies to these backend/docs paths.

Independent fixtures: [77 IF² candidates and 22 ordered swims](../../../backend/tests/fixtures/v6_partial_approval.json).
Private results: [partial-approval evidence](partial-approval/evidence.json).

## Final local verification

| Check | Result |
| --- | --- |
| Focused partial-approval + policy sandbox + C2.1 tests | **185 passed**, 10.67s; 120 new cases, 35 existing policy cases, 30 existing C2.1 cases |
| Full backend pytest, final source state | **2,222 passed**, 162.61s; one existing Starlette/httpx deprecation warning |
| Ruff `check app tests benchmarks` | PASS |
| Ruff `format --check app tests benchmarks` | PASS, 186 files |
| Strict mypy `app tests benchmarks` | PASS, 185 source files; existing `strict=true` retained |
| Existing 40-case direct planner regression | All complete canonical outcomes and input fingerprints equal the prior delivery; all 26 accepted reference completions preserved; 29 returned plans pass independent legacy constraints |
| Regression artifact versus original policy-sandbox artifact | Exact JSON semantic equality and identical SHA-256 |
| Preserved diagnostic timeout | `current:build_4`, unchanged eight-second bound including imports; not declared infeasible |
| Custody | 19 ancestry checks pass, including Realized V2, C1/C2/C2.1, A3–A9, V6 and both performance optimizations |
| Source custody | All three archived V6 workbooks match supplied originals byte for byte and retain their pinned SHA-256 values |
| Protected worktrees | Policy sandbox and BUILD performance delivery remain clean at original tips; A5/A6 release remains clean at `cd3e2dd438031cfb565858d0a5929e9963f7b31f` |
| Scope | Only new files; zero prior tracked file changes, including tests and historical reports |
| Mobile/strict TypeScript | Not applicable: no mobile or public-contract changes |
| Hosted PostgreSQL/pgTAP/RLS/device/release checks | Not run; existing external gates remain open; no database access or migration |

The full backend suite includes the existing OpenAPI/public-contract, recursive
TSS/private-load leak, Realized TSS V2, stale/version/retry/confirmation and A3–A9
safeguard coverage. No older tests, expected results or tolerances were weakened.
The earlier preliminary full run passed 2,221 tests; the final run above includes
the additional evidence-artifact authority test and final strict-typing fixes.

Reproduction commands are in the [swimming report](JOREN_V6_SWIM_ESTIMATED_ACTIVE_TIME.md#evidence-and-verification).
Machine-readable results: [verification manifest](partial-approval/verification.json),
[40-case regression](partial-approval/regression.json).

| Immutable private artifact | SHA-256 |
| --- | --- |
| partial-approval/evidence.json | `3881b23421f5506519bea62d671902777c702cbe95d007794635228a4d8b2b66` |
| partial-approval/regression.json | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` |
| backend/tests/fixtures/v6_partial_approval.json | `a949508f310d713c23f563dc5689b291e78c342430a3e208a49aa1f6948a2471` |

## Operational integration remains blocked

Confirmed parameters, prospective priority order and permission for offline
reference-time estimates do not close complete source-method/precision/P/V2
approval; the exact partial-plan versus no-plan fallback; pending BUILD and
suitability decisions 5/6; the allocation metric/tie/minimum-fill integration;
or acceptance of estimated time and uncertainty as an operational safety gate.
Named accountable scientific review, catalog/release authorization and existing
external database/device gates also remain open. See the
[Dutch pending-decisions brief](JOREN_V6_PENDING_POLICY_DECISIONS_NL.md).

This completes only the requested offline partial-approval intake and evidence.
No operational phase or release is declared complete. Local commit SHA is supplied
in the delivery response and resolves with
`git rev-parse experiment/joren-v6-partial-approval`.
