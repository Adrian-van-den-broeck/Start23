# C1 offline adapter design

Date: 2026-11-04, Europe/Amsterdam. Private developer evidence.
Status: **DRAFT — SOURCE VALIDATED, METHODOLOGY NOT APPROVED**.

## Boundary and command

`backend/app/modules/workouts/joren_draft.py` contains source records and the
deterministic adapter. It follows the existing frozen-dataclass/Decimal domain
pattern, but deliberately returns `DraftWorkout`, never `WorkoutTemplate` or an
approved occurrence. No existing application module imports this adapter.
`backend/app/jobs/joren_catalog_dry_run.py` is the local command:

```powershell
cd backend
python -m app.jobs.joren_catalog_dry_run --dry-run
python -m app.jobs.joren_catalog_dry_run --dry-run --private-output ../docs/catalog/implementation/joren_c1_manifest_v1.json
```

Use the existing backend virtual environment with the project's installed
dependencies for the regression checks. The adapter itself uses standard-library
OOXML extraction and the existing pure physiology reference function. There is
no spreadsheet engine, resave, formula evaluation or dependency addition.

`--dry-run` is mandatory. There is no apply flag. Normal stdout contains counts,
fixed error codes, A–F approval gaps, inactivity and the manifest digest. Raw cell
values and mathematical references are emitted only to an explicitly requested
private developer artifact. These files must never be routed to athlete APIs,
logs, mobile assets, analytics or accessibility labels. Raw-bearing dataclasses
disable generated repr. Existing public serializers and contracts are unchanged.

All output writes use exclusive creation: identical manifest retries leave bytes
unchanged, and a different existing artifact causes `artifact_revision_conflict`.
The timing output uses the same protection; even an accidentally specified source
path cannot be overwritten. Parent directories must already exist. Timing files
contain varying runtime measurements and are excluded from the source manifest.

## Verification before parsing

All three workbook hashes and the specification PDF hash/byte counts are pinned
in `SOURCES`/`SPEC_PDF`. Every file is read and verified before any XML is parsed.
Parsing uses those verified in-memory bytes, avoiding a second unchecked read.
`read_document` verifies them again. Changed bytes, even formatting-only changes,
fail closed with `source_revision_mismatch`. `--sources` changes custody location,
never the allowed hashes. The pinned reconciliation report must be adjacent to
the source directory; moving an identical bundle does not change identities.

OOXML is inspected directly. Each original cell retains coordinate, XML type,
value, numeric lexeme, formula/cache independently, style index, number format
and serialized cell XML. Original archive bytes remain the byte-level authority;
serialized XML is not claimed to preserve ZIP/XML lexical formatting. Source
headers, spelling, newlines, notes, sheet name/state and extent are retained.
The supported intake has one visible sheet per workbook and no formulas. Unknown
schema/type/format and formula revisions are rejected, never calculated silently.

The exact 15-column headers are validated separately for RUN, BIKE and SWIM.
All expected rows must exist, with A–O coordinates in order. Duplicate source IDs,
missing proposals and unrecognized IDs fail closed. Unsupported row syntax and
numeric/aggregate errors are quarantined with document/row/fixed code; the command
returns failure without emitting a successful normalized artifact.

## Event representation

Each pipe-delimited source token maps to exactly one event, with source cell,
one-based sequence, unmodified raw token and character start/end span. Whitespace
and every repeated block survive. Full-token matching rejects suffixes, empty
tokens, missing units, nonpositive/nonfinite quantities and unsupported zones.

| Event | Measure | Zone | Time/distance not prescribed |
| --- | --- | --- | --- |
| `TimedZone` | Decimal seconds; source `m` × 60, `s` unchanged | explicit source Z1–Z5 | no distance inferred |
| `SwimDistance` | exact integral Decimal meters | explicit source Z1–Z5 | `duration_seconds=None` |
| `WallRest` | exact positive Decimal seconds | `None` | `distance_meters=None`, `rpe=None` |

For RUN/BIKE, canonical seconds are divided by 60 only for comparison with the
original per-zone minutes. Six/eight 30-second sprints remain six/eight events
and contribute exactly 3/4 minutes. For SWIM, `m` means meters, never minutes.
Wall rest contributes only to `stationary_rest_seconds`. It is never Z1 swimming.
The adapter validates all five per-zone aggregates and their total against the
original numeric cells. Swimming active/elapsed duration remains unknown; rest
seconds do not establish either duration. No CSS or distance conversion exists.

## Numeric and method separation

`build_manifest` fixes a local Decimal context at precision 50, HALF_EVEN, with no
intermediate quantization. Caller precision cannot change regeneration. Original
lexemes (including binary-export residues), digit count, Decimal exponent and
number format remain distinct from values rendered to the workbook's `#,##0.0`
display grid. Rendering an existing stored cell under Decimal HALF_EVEN does not
approve or identify the original methodology's rounding policy or locale.
`original_method_rounding_policy` stays `None`.

RUN/BIKE mathematical references call the unchanged `zone_load` function under
`phase-13-joren-ruleset-1`. They are labeled `planned_zone_minutes_REFERENCE_ONLY`.
SWIM's reference multiplies source zone meters by the PDF's published per-100m
constants `.98/1.44/1.98/2.40/2.70`, divides by 100 and records the PDF hash as
provenance. It does not apply the source `.90` again. This is evidence only.

The IF² method is named as a proposal only; there is no IF² calculator, Z3 anchor,
automatic method selection or coefficient update. Raw source TSS, rendered value,
numeric precision, reference and proposed method are separate fields. Every load
has `approved_operational_tss=None`, `operational_status=UNAVAILABLE`, and
`approval_status=PENDING`. Catalog release, method version and activation status
are independent fields, respectively `None`, `None`, `INACTIVE`.

## Technical lineage and draft metadata

The exact UUID5 recipe in the C1–C8 sequence is implemented with lowercase sports,
exact original TR identifiers, the original lowercase SHA-256 and template version
1. The full mapping is in [the source manifest report](JOREN_C1_SOURCE_MANIFEST.md).
Keys/IDs are collision-checked across all 61 records and against all 336 UUID
literals in offline migration history. This checks the available offline
evidence, not unqueried hosted/generated successor IDs. C8 must enforce durable
uniqueness. A changed hash is rejected by this intake, never used to overwrite a
version. A later accepted source revision requires explicit registry/version work.
No old RUN/BIK/SWI/SWIM identity is inferred from title, length or suffix.

The final reconciliation is pinned by hash. Its complete six-column 61-row
selection proposal is retained verbatim by column, report line and report hash.
Bucket/phases, capability, auto/manual selection, per-block RPE, beginner scope,
repeats, method compatibility and swim planning compatibility each use explicit
`DraftField(state=DRAFT)`. Missing eligibility/compatibility is `None`, never a
permissive Boolean. TR-BIKE-013 retains its archive/explicit-only proposal and
automatic beginner hold. No individual duration cap is invented. Expected source
Session-RPE stays separate from proposed per-zone block ranges; rests have no RPE.

No SQL, database client, network transport, application settings, feature flag,
planner selection or occurrence writer is invoked. Historical catalog readers,
snapshots, methods, approved plans and realized-load behavior remain unchanged.
