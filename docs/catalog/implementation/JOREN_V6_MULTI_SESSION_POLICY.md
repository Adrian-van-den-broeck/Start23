# V6 multi-session policy and authority

12 November 2026, Europe/Amsterdam. Accepted base
`b87d0e4f82702e168ec16441bbe7661fd0d10cb2`; isolated branch
`feat/joren-v6-multi-session-planning`. V6 remains inactive.

## Authoritative frequency findings

There is **no approved athlete/week frequency resolver or frequency intake** in
the accepted product context. This is an explicit dependency, not permission to
derive sessions from the TSS ceiling.

- `docs/requirements/phase-13-joren-ruleset-1.md`, authoritative onboarding
  decision 1, supersedes the old distance/frequency intake with previous-month
  weekly hours. It explicitly says not to use the old frequency proposal.
- `docs/requirements/workout-distribution-decision.md` (2026-10-01) confirms that
  hours/Start-TSS do not supply session frequency. It leaves the observation
  period, missing-data/injury treatment and selector interpretation for decision.
- `docs/requirements/joren-workout-selection-phase-2026-09-28.md` authorizes
  repeated immutable templates as distinct occurrences. Existing V6
  `maximum_uses` records impose revision-specific repetition ceilings where given.
- `JOREN_V6_AUTOMATIC_SELECTION_IMPLEMENTATION.md` defines the accepted V6
  automatic envelope: one new occurrence per goal sport, retained repeats allowed.
- The current owner request authorizes this extension and conditional testing;
  its 2 RUN / 2 BIKE / 1 SWIM example is not a universal athlete prescription.

The unchanged safe default is therefore one automatically generated occurrence
per eligible goal sport, subject to feasibility. A larger budget alone changes
neither that envelope nor athlete readiness.

## Explicit private contract

`SessionFrequency` is a trusted server control, never a public request field.
Every supplied record has a sport, nonnegative maximum, optional target,
nonempty authority reference and explicit `soft_target` status. Its controls
must be bound to one athlete and week. The inactive local dependency seam is the
only integration entry point; no onboarding, check-in or production setting
manufactures a frequency authorization.

| Concept | Implemented meaning |
| --- | --- |
| Authorized maximum | Complete-week ceiling, including retained/completed occurrences; never a fill instruction |
| Explicit soft target | Requested automatic coverage, ranked after sport coverage and all hard constraints; partial results permitted |
| Maximum without target | Existing one-per-sport request, capped by the maximum; a maximum of five does not request five |
| Mandatory minimum | None independently approved; unsupported statuses reject rather than inventing a minimum |
| Existing occurrences | Fixed retained prefix consumes counts, repetition allowances, load and HIGH time before extension |
| Availability | Scheduler input, never a session target or capability authorization |
| Repetition | Separate existing per-template `maximum_uses`; counted across the entire prefix plus additions |

Automatic additions stop at the soft requested count. Retained counts above a
soft target remain intact if within the hard maximum. A caller must supply the
complete retained week; logical occurrence IDs and fixed dates are preserved.
Pending replacements cannot append sessions and never reoptimize siblings.

The new count envelope has the existing 24-occurrence engineering bound and a
separate bounded search. Neither is a physiological statement about how many
sessions an athlete should perform. A context beyond the computation envelope
fails explicitly instead of silently dropping a retained workout.

## Policies preserved

Official method `joren-v6-planned-if2-1`, all 77 source revisions and source phase
assignments are unchanged. The authorized weekly ceiling, injury allocation and
discipline caps, capability checks, progression/recovery resolver, soft triathlon
50/30/20 allocation, per-sport maximum 20% HIGH active time, no HIGH minimum,
BUILD Z5 occurrence restriction and existing elapsed-hour anti-stack rules remain.
There are no experience categories, new rest periods or new duration limits.

Every weekly safety calculation includes retained and new occurrences, rather
than granting a new allowance per session. Completed physical members are never
reassigned or cloned by post-activity moves. Legacy evidence-incompatible plan
replacement remains fail-closed; this work does not authorize a new corrective
writer over recorded activities.

Swimming retains `ESTIMATED_FROM_APPROVED_REFERENCE_PACE` provenance in the
inactive preview. This is not measured individual duration or operational safety
approval. Realized V2 measured-data priority and unsupported Planned IF² / sRPE
fallback rejection are unchanged. No historical physiological value is recomputed.

## Remaining product decisions

Before a real product resolver can authorize additional sessions, identify the
versioned source of athlete-specific maxima and soft requests, how actual
frequency/capability is established, its observation period, missing-data and
injury/recovery handling, confirmation/revocation lifecycle, and precedence with
other authorized context. Decide any mandatory minima independently, if wanted.

All frequency records in the new examples and tests explicitly say `TEST_ONLY`.
The persisted SQL examples use normal approved onboarding hours and the existing
budget resolver; only their frequency requests are synthetic. They demonstrate
software capability, not a newly accepted prescription for real athletes.
