# BUILD search correctness

2026-11-05, Europe/Amsterdam. Offline implementation evidence, no policy activation.

Accepted start: `12fde3bd542b42e8259b130be797f673a8c2ded6`.
Its verified implementation ancestor is
`c7c1b43a5db354d2abea4e128f42ca050179d2ad`.
Commit and verification results are recorded in the optimization report.

## Reference and scope

The accepted function is frozen byte-for-byte in
`backend/tests/fixtures/planner_performance/bounded_selection_12fde3b.py.txt`:
SHA-256 `597b3f2a0f4a3d66c691be96a698da489e95d871ae264aeeeb89855a38e85d8b`.
The harness verifies this digest before installing `accepted` in an owned child.
The older `99c03b1` oracle and every historical evidence file remain unchanged.

New paths apply only to BUILD with more than one required discipline. The
single-discipline path retains its exact accepted behavior, including A9's
internal scheduling trace. This conservative scope follows an exploratory A9
failure: an earlier shortcut returned the identical plan but skipped three
intermediate schedule results. The implementation was narrowed; no golden,
assertion, or accepted fixture was changed to accept that difference.

## Exact-addition lemma

Let E be the minimum of zero and all deck/prefix Decimal exponents, and A the
largest adjusted exponent. Loads are finite and nonnegative by `InternalLoad`.
The guard requires at most 24 occurrences, E >= Emin, A+2 <= Emax, and
A-E+3 <= precision. Every operand is an integer multiple of 10^E and less than
10^(A+1). Even the sum of two full paths (at most 48 operands) is less than
10^(A+3), so its scaled integer coefficient fits the context precision.
All nonzero sums are normal and finite. Adding zero remains numerically exact.
Thus bounded additions are associative in every admitted rounding mode.

No rounding mode or process context is changed. The extra reachability
arithmetic uses a local context copy so it does not publish diagnostic flags.
Contexts trapping Clamped, Inexact, Rounded, Subnormal, or Underflow retain the
accepted search for all new techniques. Unsupported precision/exponent/count
conditions also retain it. Phase 1's own Decimal-trap fallback remains intact.
These checks are deliberately sufficient, not necessary: missing an optimization
opportunity never removes a plan.

## Necessary high-load reachability

For weeks 1-3 the unchanged terminal rule permits high H in
[budget * .70, budget * .90] if high is available. Week 4 needs 0 < H <= budget;
its existing Z5 requirement is still checked at the terminal. With no eligible
high, H must be zero. Bounds use the same Decimal multiplications as the
terminal, including its context rounding.

R[k] contains zero and every sum of at most k high-option loads not exceeding
the terminal upper bound. Repetition is unrestricted in R: limited uses, sport
caps, athlete restrictions, high spacing, and Z5 can only reduce the actual
continuations. Therefore every legal continuation's high increment lies in R[k].
The table retains a prefix high value iff some increment can put it in the
terminal interval with the available slots. Discarded prefixes cannot terminate
validly at any permitted remaining depth. Monotonicity allows intermediate
high sums above the terminal upper bound to be omitted. Week 4's strict positive
condition is handled separately when the smallest increment is zero.

The original key includes H. If a canonical state is removed, every path
sharing that key has the same impossible high continuation, even when its
per-sport loads or history differ. This argument does not require sport caps to
be encoded in the historical key. Ignoring use limits and Z5 in this table is a
safe overapproximation, never permission to bypass them. Repeated templates and
limited-use exhaustion remain subject to their original transition checks.

Reachable entries and result entries each have a 32,768-entry ceiling. Exceeding
either abandons the entire optional table and retains the accepted search;
there is no truncated reachability set used for pruning.

## Canonical permutation elimination

For exact sums and **no sport caps**, the historical state
(total, high, sport counts, high sport counts, limited-use counts, Z5 flag),
together with depth and fixed prefix, determines transition eligibility.
The recorded limited IDs include every limit that can be exhausted before the
count bound; other explicit/default limits cannot bind within that bound.
Required composition uses the same counts. All load/count/use upper guards are
monotone. The original grouping and representative IDs are unchanged.

In this state graph, the least UUID path to a state has the usual optimal-prefix
property: replacing a prefix by a smaller path to the same state preserves every
possible extension and improves its path key. Because additions and state facts
commute, swapping a UUID inversion in the appended suffix preserves its final
state and all monotone guards, while reducing its key. Thus the canonical suffix
of every competitive state is sorted by UUID. The fixed prefix is never sorted.

Only continuations at or above the last appended UUID are expanded. Repeated
UUIDs remain allowed. Equal states still use the original strict path comparison.
Phase 1's incumbent pruning removes only strictly noncompetitive overshoots;
every prefix of a competitive winning path still survives that bound.

The historical state omits per-sport load. Consequently **any nonempty sport-cap
mapping disables this technique and the exact shortcut**, regardless of whether
the particular caps seem generous. Duplicate deck IDs also disable them. No
claim that the historical key is sufficient for capped or ambiguous catalogs is
needed. The optional precomputed option suffixes use all options, have at most
128 keys, and are request-local. Larger option sets retain the accepted expansion.

## Short exact meet-in-the-middle search

For the same Markov/exact-addition scope, all canonical suffixes in a short
layer are joined from two halves of up to three occurrences each. Each half
contains combinations **with replacement**. The shared Decimal exponent is
converted directly from coefficient digits to integers, including target and
prefix; integer joins are exact equality, with no quantization or rounded grid.
Exponent spans over 128 digits fall back. Source load values and returned
calculations remain Decimal and retain their existing representations.

Layers are considered in original occurrence-count order. Each join must have
the exact target total and nondecreasing suffix indices. For every matching
historical state the smallest complete UUID suffix is retained **before**
calling the original policy/feasibility predicates. The limited-ID set is
identical to the historical key, including omission of nonbinding limits.
Splitting those omitted identities into additional states would be unsound
when a callback rejects the historical canonical representative; a dedicated
regression covers this distinction.

Every exact terminal path's nonnegative prefixes lie at or below target, so
neither the historical total bound nor Phase 1 overshoot pruning can discard
it. Valid final high/count/use bounds likewise hold for its prefixes. By the
canonical lemma the joined representative is exactly the original DP
representative, including arbitrary deterministic feasibility rejection of that
representative. Existing scheduling, anti-stack, availability, and athlete
constraints run through the unchanged callback before an incumbent is accepted.

An exact first score component dominates every nonexact candidate. The original
engine stops after the first layer containing a feasible zero-error incumbent.
Within that layer the shortcut compares the unchanged high-error and full UUID
path; count is constant. It never picks a later, better-high exact layer over an
earlier exact layer. If an exact join exists, the target is on the proven normal
load grid; differences to all other reachable totals are exact nonzero normal
values unless equal. Thus an earlier rounded-to-zero nonexact error cannot
invalidate this early-layer argument, even for unusual caller contexts.

If there is no feasible exact result, or construction/work limits are reached,
the original dynamic-programming search runs, with only the separately proven
bounds above. Up to 64 options permit six appended occurrences (at most 45,760
triples); 65-128 permit four (at most 8,256 pairs). More options disable the
shortcut. A 200,000 matched-join ceiling abandons the shortcut rather than
returning the best result from an incomplete layer. None of these limits truncates
the actual planner search or excludes a candidate from its fallback.

## Determinism, identity, and isolation

All terminal score components and original equivalence grouping are preserved.
UUID comparison uses the existing string order. The returned template sequence
is the fixed prefix plus the same canonical suffix. Snapshot construction,
occurrence allocation, dates, warnings, failure codes, revision preconditions,
idempotency, pending confirmation, and persistence are outside the changes.
No new global cache exists. Tables contain only request inputs and die with the
call; concurrent callers share no athlete state or credentials. A9's bounded
spawned-process execution and cancellation behavior are unchanged.

The independent exhaustive suite spells out the terminal rules without calling
the production selection predicate. Seeded full-optimum cases use exact inputs
and sufficient state facts; arbitrary capped/history-dependent callbacks are
instead compared to the frozen accepted engine rather than falsely claiming the
old merging implements a different unrestricted optimum. Explicit cases cover
UUID ties, equal loads, repeats, fixed prefix order, exhausted limits, missing
high/Z5, interval boundaries, multiple caps, unavailable dates, impossible high
counts, no solution, zero loads, all eight rounding modes, exponent extremes,
and trapped arithmetic. A9 and the full 40-case parity evidence remain separate.
