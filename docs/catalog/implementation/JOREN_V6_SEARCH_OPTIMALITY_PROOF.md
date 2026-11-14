# V6 exact ranked search: correctness argument

14 November 2026, Europe/Amsterdam. Algorithm only; no physiological or
frequency-policy revision. Accepted baseline is
`e85cbaa8b5e702c283186fc61fcadda74ad36faf`. Selection provenance remains
`joren-v6-multi-session-selection-1` because its scope and objective are unchanged.

## Scope and existing necessary predicates

The eligible deck is still produced by `eligible_v6`. The original canonical
sport-multiset expansion is retained. Its prefix, exclusion set, repetition
ceilings, requested-count envelope, sport caps and weekly ceiling are unchanged.
Nonnegative loads and increasing uses/counts justify their existing upper-bound
checks. HIGH is tested only on a completed sport option; a HIGH-heavy prefix is
still extended with LOW options. A complete sport option includes all retained
occurrences of that sport in its load, count, HIGH arithmetic and identity key.

Nondecreasing appended template indices enumerate each multiset exactly once.
The retained prefix is not reordered. No load-equivalent templates, source
revisions, repeated occurrences or scheduling states are merged or dominated.
Every retained feasible complete week therefore remains a Cartesian product of
one complete option per goal sport, within the original authorized envelope.

All arithmetic below uses exact fractions of the existing final official
Decimal operands. It does not substitute the source formula's rational value
for an already approved final Decimal, quantize it or use ambient precision.

## Disjoint boxes

Options for each sport are stratified by their exact complete occurrence count.
Within a stratum they are ordered by load, then immutable UUID tuple. A span is
a contiguous half-open interval in that immutable sequence. A box is the product
of one span per sport. Initial boxes are every product of count strata. They are
disjoint and cover every sport option product. Splitting one span in half yields
two disjoint boxes whose union is the parent. Equal loads stay as separate rows.

Every count stratum has a constant sport-coverage contribution and a constant
`min(count, explicitly requested)` contribution. Thus a box's first two ranking
components are **exact**, including retained counts above a soft request and
sports with no explicit frequency record. These are not weighted scores.

Let option loads in a box satisfy `l_s <= x_s <= u_s`, let `B` be the hard weekly
budget, and write `L = sum(l_s)`, `U = sum(u_s)`. If `L > B`, every product is
over budget and the entire box may be discarded. This is the only new
feasibility exclusion. No schedule is inferred from these aggregates.

## Optimistic share-distance bound

When `L > 0`, every feasible nonzero product has sport share in this interval:

```text
minimum_s = l_s / min(B, l_s + sum(u_other))
maximum_s = u_s / (u_s + sum(l_other))
```

Proof: `x/(x+y)` increases with nonnegative `x` and decreases with nonnegative
`y`. Also `T <= B` implies `x/T >= x/B`. Combining these two lower bounds and
substituting `x >= l_s` gives the displayed minimum. Substituting `x <= u_s`
and `y >= sum(l_other)` gives the maximum. Denominators are positive when
`L > 0` and the box has not been discarded. The bounds can describe products
that do not actually exist; that makes them conservative, not unsafe.

For approved target share `w_s`, define
`d_s = max(minimum_s - w_s, w_s - maximum_s, 0)`. Every actual absolute
share error is at least `d_s`, so `sum(d_s)` is a lower bound for the approved
unrenormalized L1 objective. Ignoring cross-sport correlations cannot increase
this bound beyond an attainable error. For `L = 0`, use zero as the bound:
this safely includes the zero-total special case. Non-triathlon goals retain
their approved constant zero allocation component.

The optimistic fourth component is `-min(U, B)`, because every feasible total
is at most both `U` and `B`. A nonleaf's fifth component is the empty tuple,
which is lexicographically no greater than any sorted immutable UUID tuple.
All components are optimistic; when earlier components tie, the following
component remains a valid bound. Thus the complete five-part bound is no
greater than the actual rank of **every feasible product in that box**.

At a singleton box `L = U = T`. Its share intervals collapse to the actual
shares (or the approved zero-total special case). Its total and immutable
multiset key are exact. Therefore its bound equals its full authoritative rank.

## Lazy ordering and optimality certificate

A request-local min-heap stores boxes by these lower bounds. Every initial box
is admitted before any candidate can be emitted. On removal of a nonsingleton,
both children are admitted before continuing. On removal of a singleton, its
actual rank is the smallest heap bound. Every still-unexplored product belongs
to a remaining box with bound at least that rank. Consequently no remaining
product can have a better rank. Emitted complete candidates are in exact order.

The caller gives each emitted candidate to the **unchanged** deterministic
scheduler, with the original prefix ordering, occurrence UUID construction,
fixed template/occurrence dates, availability, rest and HIGH anti-stack rules.
Rejected candidates do not stop the search. The first successfully scheduled
candidate is optimal among all feasible scheduled weeks in the original scope:
earlier emitted candidates failed placement; later ones cannot rank better.
An empty week is considered only at its actual rank and only when the original
prefix/composition rules permit it. The chosen week receives a final independent
call to the existing complete-week validator before returning.

This is an optimality certificate from a partition and admissible bounds, not
an incumbent or a heuristic convergence claim. The heap need not be exhausted
to certify the first schedulable leaf. Scheduler errors remain distinct from
resource exhaustion; the latter always propagates as `v6_search_incomplete`.

## Resources and cancellation

The original maximum of 24 occurrences and 200,000 shared worknodes remains.
Each sport expansion, admitted/tested box and scheduler recursion is charged.
Each heap removal corresponds to one previously charged box; each split creates
exactly two charged children. There is no uncharged unbounded product walk.
Sorting is limited to the already bounded sport-option lists. The heap and
immutable metadata use O(N*K) reference storage at worst, for N <= 200,000
charged operations and K <= 24; full-week materialization is lazy. Metadata
and spans share template/string/option sequences rather than copying catalogs.
There is no cross-request or cross-athlete cache. Actual peaks and the explicit
24-request exhaustion case are in the benchmark report.

Exhaustion while generating options, admitting a root, splitting a box or
scheduling aborts the entire computation. A partially admitted partition is
never used to claim optimality. No arbitrary feasible week can be published.
The A9 process executor, bounded admission and shielded cancellation ownership
are unchanged, as are pending-only persistence and subsequent confirmation.

## Independent falsification and full-catalog evidence

`benchmarks/v6_search_oracle.py` enumerates **every** complete product with
`combinations_with_replacement`/`product`. It implements source eligibility,
source-event active times, repetition, count/cap/budget checks, exact ranking
and date feasibility independently. It uses lossless scaled integers and cross
multiplication for rank comparison, not the production box bounds or heap.
It does not import production ranking, validation, pruning or scheduling.
Its date search independently tests elapsed UTC HIGH spacing and the existing
best-effort rest rule, including fixed identities/dates and same-day sessions.

The original 30 seeded oracles remain unchanged. Additional differential tests
exercise restricted dates, injuries/capabilities, phases/BUILD, repetition,
retained identities and composition. Direct bound tests compare boxes against
every member's independently written exact score, including zero loads and
budget cuts. A full lazy iteration checks global ordering and preservation of
repeated/distinct immutable identities. A scheduling counterexample proves
that the mathematical best cannot bypass actual placement. Existing exact
Decimal and HIGH equality/excess tests remain unchanged.

For each original large-catalog fixture the independent reference visits its
entire count/HIGH-valid product space and confirms the exact five-part returned
rank and UUID multiset. Thus the three formerly incomplete results have both
the above partition proof and a separate exhaustive verification without its
bounding assumptions. Machine results, executable fixture definitions and
verification hashes are linked in the accompanying reports.
