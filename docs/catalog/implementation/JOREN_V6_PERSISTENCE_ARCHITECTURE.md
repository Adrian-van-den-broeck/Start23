# V6 persistent planning architecture

7 November 2026, Europe/Amsterdam. Branch `feat/joren-v6-persistence-hardening`.
Exact starting commit: `4b3a76d9d764567e7bb438ad7493953faed6dea2`.
Implementation commit is recorded in the delivery addendum after local verification.

**Prepared inactive implementation. Real PostgreSQL verification has not run.**
The historical planner remains the application default. No setting, route, mobile
screen, deployment configuration, production database or A5/A6 worktree is changed.

## Reuse and minimal extensions

| Concern | Decision |
| --- | --- |
| Athlete/account ownership | Reuse verified-token identity, opaque athlete map, legacy RPC adapter, dual-owner triggers and composite owner foreign keys. No new athlete entity. |
| Catalog identities | Reuse `public.workout_templates` identity/key/version constraints and immutable rows. V6 identities are hash-bound source revisions. New rows have immutable `inactive_v6=true`. |
| Historical catalog default | Do not add V6 rows to `private.workout_template_loads`. The existing catalog projection's inner join therefore excludes all 77. A restrictive authenticated SELECT policy also hides their public template rows. No historical template is retired. |
| Exact source provenance | Add private `v6_source_revisions`: worksheet/row/hash, tagged lossless document, complete source snapshot, original cells/lexemes/events/RPE/focus, predecessor revision evidence, official Decimal and rational evidence. Activation is constrained to INACTIVE. |
| Draft selection | Reuse `swipe_week_drafts`, existing create/update RPCs, revision CAS, decision history and occurrence-aware validator. Extend only version dispatch to include V6. The historical predicates remain equivalent. |
| Pending/confirmed plans | Reuse `weekly_plans`, `plan_revisions`, `change_proposals`, `planned_workouts`, private occurrence/revision loads, and existing approve/reject RPCs. No second approval or revision system. |
| Frozen context | Add private `v6_plan_snapshots`, owner-bound to an existing revision. Store the exact validated payload and confirmed input snapshot. Reuse Realized V2 plan-evidence persistence and confirmation trigger. |
| Occurrence identity | Existing workout rows have globally unique physical primary keys. Add private `v6_occurrence_snapshots` to retain logical V6 occurrence IDs and ordering across distinct immutable physical revision rows. |
| Edit receipts | Add private `v6_edit_results`, keyed by athlete/operation. Store the immutable original public response, including terminal replay after later edits/approval. |
| Application boundary | `InactiveSupabaseV6Repository` extends the established repository. `InactiveSupabaseV6CatalogProvider` reads durable documents. Both require explicit injection; startup never constructs them. |

The logical/physical occurrence distinction was invisible in the earlier memory
fixture. A V6-only database read projection returns logical IDs in frozen order;
existing historical reads and physical activity foreign keys are unchanged.
Before exposing V6 to devices, calendar move/activity/registration consumers must
explicitly resolve this mapping and pass their device/contract gates. The present
inactive workflow supports initial pending selection, pending replacements,
resume, rejection and confirmation/reload. V6 check-in-driven generation currently
fails closed rather than bypassing the separate A5 attachment/replay contract;
historical A3–A9 check-in behavior remains unchanged. Neither limitation is an
authorization to expose the preview through the default application.

## Numeric authority and durable source format

Official method: `joren-v6-planned-if2-1`; parameter reference:
`joren-v6-approved-if-reference-1`; acceptance:
`joren-v6-official-tss-acceptance-1`.

The physiology implementation is unchanged: exact rational operands followed by
one final 50-significant-digit HALF_EVEN Decimal conversion. Store that final
Decimal as canonical text **and** unconstrained PostgreSQL `numeric`, with an
equality constraint. Keep numerator/denominator as separate exact integer strings.
Budget totals sum the final official Decimals exactly; they never substitute the
infinite rational or use workbook display rounding.

Existing load columns already use unscaled `numeric`. No precision/scale change,
historical P update, snapshot recalculation or Realized V2 change is needed.
PostgreSQL documents that unconstrained numeric does not coerce values to a fixed
scale ([numeric type reference](https://www.postgresql.org/docs/current/datatype-numeric.html)).
Actual PostgreSQL round-trip/comparison behavior is still an unexecuted gate.

The private versioned codec tags Decimal/UUID/enum/tuple/frozenset/dataclass values,
uses an explicit class registry and checks immutable dataclass constants. It
imports no stored class name and never opens a workbook while restoring a row.
All original source cell strings, ordered segments and explicit wall-rest events
survive. Private method/source fields never enter an athlete DTO. The V6 HTTP
adapter decodes JSON fractional numbers directly to Decimal, including private
historical load reads; the historical adapter retains its existing behavior.

| Pinned phase source | Rows | SHA-256 |
| --- | ---: | --- |
| RUN | 28 | `7380c88ef8bccb3cb35b0f6416d9debba8342b9802fc716f0a99dcfcb8626d88` |
| BIKE | 27 | `6322d7f93b3e074c77c4efa28b2a95de3f04f0f5c6af226ce50e8c2ff716ddbc` |
| SWIM | 22 | `48a0f6448f003ef048f40e53fda74b5220f272ebd4300180c108777c6e0be3ba` |

The generated inactive catalog migration's canonical SHA-256 is
`6e77d8d54650c7be554a90bb87cdf339b72a2db334be1a8dd98e82d6e22efe34`.
The offline historical collision scanner exempts only this exact reviewed import,
which intentionally contains its own source and predecessor IDs. A modified
import or collision in another migration still rejects; new tests prove both.

## Transaction and concurrency decision

Physiology and complete-week validation remain in deterministic Python. SQL is a
snapshot/CAS writer, not a second selector or a second physiological ruleset.

1. Python reconstructs the exact pending revision and frozen authorized target,
   restores athlete/week-bound evidence and validates the complete resulting week.
   Retained occurrences/dates remain fixed. Current controls may tighten stored
   restrictions, never expand them. Request-local adapters prevent shared-service
   cross-athlete namespace mutation across awaits.
2. One RPC transaction acquires the athlete/week advisory lock, checks an existing
   idempotent receipt, and locks proposal, revision, then plan in the same order
   as the established approve/reject operations.
3. Under those locks, compare active revision, exact pending revision/proposal,
   frozen target/controls, input fingerprint, unchanged week/restriction context,
   current confirmed input snapshot, and weekly-registration evidence. Selected
   immutable source snapshots/methods/loads must match the durable catalog.
   Null/tampered expected versions do not bypass checks.
4. Lock logical occurrence references in sorted order, reject foreign athlete/week
   references, expire the previous pending revision, and insert the new physical
   snapshots, exact loads, ordered occurrence mapping, proposal, frozen context,
   registration evidence and immutable edit receipt. Any failure aborts all writes.
5. Separate athlete approval uses the existing authenticated invoker RPC and its
   expected base revision. The V6 input-custody trigger and existing V2 evidence
   trigger run before activation. Frozen public fields and private loads cannot
   subsequently be rewritten, including through direct SQL with a spoofed legacy
   critical-write GUC. Existing status/state transitions and deletion cascades remain.

This is optimistic validation with atomic snapshot preconditions: expensive pure
calculation does not hold database locks. The result can commit only against the
same pending revision and immutable evidence it validated. Stale edits cannot
silently overwrite another swipe or confirmation. An unknown write outcome is
reconciled using the original key; there is no generic mutation retry or automatic
proposal recreation. Genuine engine failures are not turned into successful writes.

## Privileged access and database authorization

Normal reads and approval keep caller tokens. Generated writes use the existing
server-secret exception path and resolve the verified opaque athlete to its
legacy owner key. New private tables have forced RLS and no direct grants to
anon, authenticated or service_role. Narrow generated-write/private-read RPCs
explicitly require the service-role claim, use an empty search_path, and constrain
all joins by owner. The new public read RPC derives its owner from `auth.uid()`;
its private projection helper is not externally granted. Its SECURITY DEFINER
ownership checks are database checks, not application filtering. The helper
temporarily binds/restores the subject only after an owned plan lookup.

Existing public ownership RLS and opaque-owner restrictive policies are retained.
Composite foreign keys prevent owner-swapped revisions/occurrence snapshots.
No table grant or RLS policy is weakened to make V6 work. This follows the
[Supabase RLS guidance](https://supabase.com/docs/guides/database/postgres/row-level-security);
actual role/RLS behavior still requires the supplied real database suites.

## Prepared SQL and remaining boundaries

Forward-only, unexecuted migrations:

- `20261105120000_inactive_v6_persistence.sql`: minimal extensions, protected
  storage, bounded RPCs and V6-only validator dispatch.
- `20261105120100_inactive_v6_catalog.sql`: deterministic 77-row inactive import.

The CLI is absent, so the requested candidate files were prepared locally rather
than generated/applied using a linked Supabase project. No dependency or database
infrastructure was installed. SQL parsing does not prove PL/pgSQL runtime,
constraints, locks, grants or RLS. See the [database results and commands](JOREN_V6_POSTGRES_RLS_TEST_RESULTS.md),
[transaction verification](JOREN_V6_TRANSACTIONAL_SWIPE_VERIFICATION.md),
[rollback plan](JOREN_V6_PERSISTENCE_ROLLBACK_PLAN.md), and
[remaining activation gates](JOREN_V6_REMAINING_ACTIVATION_GATES_NL.md).
