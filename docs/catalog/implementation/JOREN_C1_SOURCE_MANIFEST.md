# C1 immutable draft source manifest

## C2.1 next source intake

2026-11-04: the C1 payload, original archives and C2 draft registry stay immutable.
The IF² six-row original conflict below is historical; the separate approved
correction overlay is [recorded here](JOREN_SWIMMING_IF2_CORRECTION_REQUEST_NL.md).
Joren's additional lighter workouts have **not arrived**. No placeholder source,
workout, hash, metadata approval or active entry is registered.

Prepared intake path for the actual delivery:

1. Archive the exact received bytes under a distinct revision filename. Record
   filename, byte count, SHA-256, sport, real row IDs/count, sheets and owner/Joren
   decision reference. Keep every predecessor and explicitly record any logical
   replacements; new IDs and replacements require their own mapping approval.
2. Use existing `SourceSpec` + `read_document(bytes, spec)` to pin and inspect the
   new archive before XML processing. These functions already accept an explicit
   revision specification. Register only real reviewed revisions; the existing C1
   `build_manifest` and C2 `read_revision` continue to reject changed bytes under
   old hashes. A differently formatted source needs inspection and a reviewed
   adapter change, never an assumed legacy schema.
3. Reuse `parse_events` and `normalize_row` with source-specific reviewed metadata
   to verify full-token parsing, exact seconds/meters, stationary rest, totals,
   every zone subtotal, formula/cache/format evidence and complete row coverage.
   Missing selection proposals remain a blocking error. Do not copy C1 approval
   metadata or its fixed 61-row coverage into an unknown future release.
4. Emit a new immutable private artifact with `write_immutable`: identical retries
   must return identical bytes, conflicting outputs reject. Retain raw cells and
   exact derived values separately; method, precision and operational P remain
   unapproved unless expressly accepted. The C2.1 correction job demonstrates this
   revision path without modifying originals or the C1/C2 artifacts.
5. Rerun arithmetic/provenance, identity collision and source-custody checks and
   the actual 45-baseline, recovery and taper feasibility probes with the delivered
   sessions. Evaluate the isolated per-sport active-time maximum; unknown swim
   minutes stay UNVERIFIED. Do not infer time from CSS/distance. Beginner-readiness
   remains open until real source tests establish coverage within existing limits.

No automatic loading of unknown files or operational selection is added. This is
intake preparation using the existing lossless pipeline, not a C3–C8 implementation.

## Historical C1/C2 source inventory

> C2 intake addendum (2026-11-04): the original C1 artifact and every historical
> source/identity below remain unchanged. A separately hashed revised swimming
> workbook is archived as `sources/Zwemtrainingen_IF2.xlsx` (7405 bytes,
> SHA-256 `7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`).
> It is a prospective IF² candidate, not an active catalog. The old swim workbook
> and PDF now serve as historical method evidence; their old calculations are
> not reinterpreted. See [current decision evidence](JOREN_C2_UPDATED_DECISIONS.md),
> [complete source diff](JOREN_SWIMMING_IF2_SOURCE_DIFF.md) and the separate
> `joren_c2_draft_revision_registry_v1.json`. Six revised rows (015–020) are
> SOURCE-CONFLICTED. All methods, release and activation remain disabled.

Date: 2026-11-04, Europe/Amsterdam. Private developer evidence.
Status: **DRAFT — SOURCE VALIDATED, METHODOLOGY NOT APPROVED**.

Start SHA: `cef4d0adfb09f5f1937528a98c594a6442816f20`. Final verified software
SHA and local delivery are recorded in [the implementation report](JOREN_C1_IMPLEMENTATION_REPORT.md).

## Artifact and acceptance

The versioned machine-readable artifact is [joren_c1_manifest_v1.json](joren_c1_manifest_v1.json).
Its SHA-256 is `3c149c9096dd568156eab0246f7f6c679fc6ac98416b073a798c7bde3b68bc85`.
Manifest schema/intake revision: `joren-optie1-c1-draft-1`. It contains 61 records
(RUN 20, BIKE 21, SWIM 20), all source cells/lexemes, source header and sheet evidence,
ordered execution events and the complete pinned selection proposal. No timestamps
or measurements are included in this reproducible payload. Regeneration must
return identical bytes; changed artifacts or source hashes fail closed.

Catalog release and operational method version are `null`; activation is `INACTIVE`.
No source is accepted for operational selection. Accepted owner/decision references
remain `null`. All A–F approvals remain pending. No operational TSS is available.
The artifact is developer-only evidence and must never be distributed as an athlete
catalog or API response. Structural source validation is separate from acceptance.

## Original source custody

All originals were verified before processing, then copied byte-for-byte into
`docs/catalog/sources`. No workbook was opened for editing, resaved, recalculated
or rewritten. RUN's original remains in the older root `docs/trainings`; BIKE,
SWIM and the PDF remain in the accepted-engine worktree `docs/trainings`.

Original custody roots:

- RUN: `F:\Projecten Business\Start23\Code\docs\trainings`.
- BIKE/SWIM/PDF: `F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.

| Document identity | Original filename | Bytes | SHA-256 | Worksheet / rows |
| --- | --- | --- | --- | --- |
| joren-optie1-run | Looptrainingen_Definitief_Optie1.xlsx | 7198 | `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3` | Looptrainingen Catalogus; 5–24 |
| joren-optie1-bike | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | `5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df` | Fietstrainingen Catalogus; 5–25 |
| joren-optie1-swim | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` | Zwemtrainingen Catalogus; 5–24 |
| joren-optie1-swim-specification | Specificatie Zwem TSS.pdf | 149021 | `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a` | PDF, provenance only |

All three worksheets are visible; extents are `A1:O24`, `A1:O25`, `A1:O24`
for RUN, BIKE and SWIM. Each row's complete A–O cell list includes original name,
focus, Expected RPE, focus zone, total duration/distance, source multiplier, five
zone subtotals, expected TSS and exact ordered source structure. Raw numeric
lexemes, style/number format, formula/cache presence and cell XML are independent
fields. The original byte archives remain the lexical authority.

## Complete coverage and deterministic identity mapping

Every ID below preserves the original TR identity. Both UUID columns are
**provisional**, version 1, pending B. Each source row covers columns A–O; ordered
events point into N at that row. Source document/hash/sheet are in each record.
The recipe is exactly `uuid5(NAMESPACE_URL, 'wombo:joren:optie1:{sport}:{source_id}')`
for the key, then `uuid5(key, 'source-sha256:{sha256}|template-version:1')` for the ID.
Sports are lowercase. Paths/titles/suffix similarities do not establish identity.
All 122 UUIDs are mutually distinct and disjoint from 336 UUID literals in local
migration history. Durable/hosted successor uniqueness remains a C8 gate.

| Original ID | Row / cells | Measure | Ordered events | Wall rest seconds | Provisional key | Provisional ID |
| --- | --- | --- | --- | --- | --- | --- |
| TR-RUN-001 | 5 / A5:O5 | 30 min | 1 | 0 | `d8520c07-aadb-5529-a0c7-6b78cf53ae15` | `9d732bc4-85c9-52f9-a2ce-6caac4b841be` |
| TR-RUN-002 | 6 / A6:O6 | 40 min | 1 | 0 | `aff77410-81f9-5ffc-8ba7-e0a978d4bdc7` | `cbecb174-34cd-5fcd-a4be-b51065777607` |
| TR-RUN-003 | 7 / A7:O7 | 50 min | 1 | 0 | `c9a0afa3-a4b4-5d26-b627-a6630afbb052` | `5dcec933-c4c2-574a-84b5-d0e9d64cb3ac` |
| TR-RUN-004 | 8 / A8:O8 | 30 min | 1 | 0 | `5c714e10-85b2-543a-b604-9b7dd146bbc1` | `32e98fc2-d12c-5d69-87a1-14e0fb628c50` |
| TR-RUN-005 | 9 / A9:O9 | 40 min | 1 | 0 | `e25fa38e-9265-56c9-ab7b-3558e11a56f2` | `fba2e792-488d-5395-b4b6-2737f1257f22` |
| TR-RUN-006 | 10 / A10:O10 | 50 min | 1 | 0 | `31f3258e-1f99-52bb-91a4-f9f5b310b884` | `a1f16894-f968-5f5e-a576-1a011862a9c8` |
| TR-RUN-007 | 11 / A11:O11 | 60 min | 1 | 0 | `580782d2-c4b9-56dd-9c74-5e4fc9fe6eaf` | `1417809e-5f48-5fcd-a625-e0bff9e17d0f` |
| TR-RUN-008 | 12 / A12:O12 | 70 min | 1 | 0 | `2fb92cf4-ab8c-5201-ad5f-5a5f66b0fab4` | `8c3a0308-6a1b-5110-8286-781134a0c963` |
| TR-RUN-009 | 13 / A13:O13 | 80 min | 1 | 0 | `6e651aed-e03a-5a45-ab49-a453d98128e3` | `715c0e27-5758-552f-b1a0-4d61d1eb8a3a` |
| TR-RUN-010 | 14 / A14:O14 | 90 min | 1 | 0 | `0af431e3-3d21-5b7a-aeb0-f1e0b64857f2` | `d0661bee-1a0f-5f01-bdf9-f69a434bf237` |
| TR-RUN-011 | 15 / A15:O15 | 100 min | 1 | 0 | `4a4b5195-aae7-5fcc-8194-2117767189f3` | `8c1acd8f-b94e-5399-b71d-621634675585` |
| TR-RUN-012 | 16 / A16:O16 | 110 min | 1 | 0 | `ecd4c0b6-f93b-53a5-941e-a4c651d8babb` | `7d1f2466-d5f9-5778-95f8-804e20445e2f` |
| TR-RUN-013 | 17 / A17:O17 | 120 min | 1 | 0 | `f61b48f6-2ce5-5e6a-81ed-c5419f4436c7` | `f661497f-806b-5236-90cb-65ec43632191` |
| TR-RUN-014 | 18 / A18:O18 | 130 min | 1 | 0 | `54f7159c-0dff-500a-955f-12955cbbe7fc` | `e54f3286-bc2e-55ad-b540-c50380fe2c2e` |
| TR-RUN-015 | 19 / A19:O19 | 140 min | 1 | 0 | `94779968-2b56-5a98-a570-e957b66a2817` | `1994d1a0-9be6-5772-9e40-89d7970be176` |
| TR-RUN-016 | 20 / A20:O20 | 150 min | 1 | 0 | `70a65453-b074-54b7-ae96-9fa46e0d84fa` | `25efc372-665d-50be-8f3e-dbe5ab069e4f` |
| TR-RUN-017 | 21 / A21:O21 | 60 min | 7 | 0 | `1cfa1722-811f-5a3a-8a29-3ef33386e0f9` | `56aba110-75cc-525d-a28d-392e371c6de3` |
| TR-RUN-018 | 22 / A22:O22 | 55 min | 9 | 0 | `1fe5e99a-dee6-51fd-9f2a-ca4ce1c31608` | `2aade7fa-40bc-5569-b997-08d6befac9ef` |
| TR-RUN-019 | 23 / A23:O23 | 68 min | 11 | 0 | `4a0da97c-185c-5797-b4e4-af79f975e478` | `2b5ddac4-c84f-5fe6-b35d-c0c08cb736b6` |
| TR-RUN-020 | 24 / A24:O24 | 68 min | 9 | 0 | `bec3dc02-12a2-564e-ad2f-5155a8512731` | `1a0c9dbf-1ebb-54a6-b818-cff573e16594` |
| TR-BIKE-001 | 5 / A5:O5 | 60 min | 1 | 0 | `b2cfa062-b8a8-51be-af35-41054fb4b2a7` | `7b71861a-c2d0-5176-86e0-b338731d9824` |
| TR-BIKE-002 | 6 / A6:O6 | 90 min | 1 | 0 | `73cb4d1c-f283-5fd0-bad9-9ac6b779a164` | `7043be9c-3120-5cab-ac81-5cd0ee737b21` |
| TR-BIKE-003 | 7 / A7:O7 | 120 min | 1 | 0 | `9af848e6-b868-5d6e-8a9b-fea1693b867a` | `5cb8a9fd-0a1e-58d8-98d0-80d5dae0b598` |
| TR-BIKE-004 | 8 / A8:O8 | 90 min | 1 | 0 | `35ff6e57-921e-5219-b0d2-cc0bc53e3b3f` | `f047047c-752b-5390-9131-06382adf5508` |
| TR-BIKE-005 | 9 / A9:O9 | 120 min | 1 | 0 | `d435ab79-e0bf-51dc-9919-29dc6dca057a` | `7a6d1a48-f57c-54f1-a61a-d7eeaa223647` |
| TR-BIKE-006 | 10 / A10:O10 | 150 min | 1 | 0 | `de1cd069-20f9-5fb2-80d9-b8d8e6fd9710` | `e2f59109-3523-5e6f-86f6-c256f2e3e4ea` |
| TR-BIKE-007 | 11 / A11:O11 | 180 min | 1 | 0 | `2a7feb7d-5af4-58cf-98c5-594778e5938d` | `0573cf0b-937e-5b96-abcb-a3f3bee91f29` |
| TR-BIKE-008 | 12 / A12:O12 | 210 min | 1 | 0 | `0a2563a7-f6a2-5a2b-a0a4-6f25947f0a2f` | `d0afdaf8-5dd0-5412-ae32-27a771570d96` |
| TR-BIKE-009 | 13 / A13:O13 | 240 min | 1 | 0 | `96120c5e-ac24-5055-ae36-4bdd69d587ef` | `af07b0b6-aa90-51af-9ffc-3b70ee0b3307` |
| TR-BIKE-010 | 14 / A14:O14 | 300 min | 1 | 0 | `9de8c80d-f188-5f08-b2ca-524b4ab3c2c3` | `dc213c8a-441f-5ae0-a289-a878f7c421f1` |
| TR-BIKE-011 | 15 / A15:O15 | 330 min | 1 | 0 | `3c5d43bc-cf1e-57bf-942d-e7f4a0524e2f` | `4971cc7a-4dfd-5c47-87ba-b5e860e5ddcd` |
| TR-BIKE-012 | 16 / A16:O16 | 360 min | 1 | 0 | `156c6ffd-bf84-576d-84f0-31e7cb08ecee` | `338535da-d870-5468-8aa3-215ea36bbb20` |
| TR-BIKE-013 | 17 / A17:O17 | 420 min | 1 | 0 | `f0211507-2f6a-5213-bddb-7dce1e4394c8` | `3be0dbe2-6ec0-5ea1-aa29-02cc08463059` |
| TR-BIKE-014 | 18 / A18:O18 | 180 min | 10 | 0 | `f8b9e317-0faf-5be7-9420-0267bbf37426` | `703b4666-f846-5a37-a39f-6fc8530e3fba` |
| TR-BIKE-015 | 19 / A19:O19 | 120 min | 10 | 0 | `342b516e-10f7-5bf4-9404-edf086dbfc9c` | `6eabbaee-8540-5e72-a832-4f9b8046dfe2` |
| TR-BIKE-016 | 20 / A20:O20 | 180 min | 18 | 0 | `90136762-6f6e-554c-9f9a-a8a864297dbe` | `e7e90942-a2fd-5fc3-9f9b-843bbc82e103` |
| TR-BIKE-017 | 21 / A21:O21 | 220 min | 10 | 0 | `868c99e2-2be6-580e-a668-050043a86d24` | `a52b464e-91ad-5646-9211-867a3774af4b` |
| TR-BIKE-018 | 22 / A22:O22 | 150 min | 11 | 0 | `c9ee3e7b-dfbb-5081-8453-654d0e3f7452` | `023808a4-9259-50a5-b60f-8d07a8d0364e` |
| TR-BIKE-019 | 23 / A23:O23 | 100 min | 10 | 0 | `f5eedca2-6a65-58fb-9efe-920d170bcaeb` | `09429b34-451d-5d9d-a911-8bd5b6f917ea` |
| TR-BIKE-020 | 24 / A24:O24 | 93 min | 15 | 0 | `a546b501-57f2-5d6b-84df-f59a9c69e6ea` | `82fa023d-42a8-56a0-80f4-e37ce83980b3` |
| TR-BIKE-021 | 25 / A25:O25 | 104 min | 19 | 0 | `f0bb7819-69fc-546e-b109-2948bc12ff62` | `61d70511-ecd9-5cd7-ab39-35edc07084f2` |
| TR-SWIM-001 | 5 / A5:O5 | 1000 m | 1 | 0 | `9c9e54eb-b2a7-5e02-8aba-d7999909565c` | `d176d407-a925-53a1-a708-4535237304c7` |
| TR-SWIM-002 | 6 / A6:O6 | 1500 m | 1 | 0 | `70441b5f-d30e-5438-afe9-5f966afa51a2` | `aca894d4-847e-5145-b024-b373bc9a554c` |
| TR-SWIM-003 | 7 / A7:O7 | 2000 m | 1 | 0 | `9e1dc788-b404-5200-9b51-6d9f0b05cba6` | `5adf2de4-b3af-534a-ade6-7214fb1d6c9c` |
| TR-SWIM-004 | 8 / A8:O8 | 2500 m | 1 | 0 | `f94b8e7a-f842-57a1-aa4d-f25349cb3bcb` | `26d6c633-4e14-595f-bbde-d2daad0e367f` |
| TR-SWIM-005 | 9 / A9:O9 | 3000 m | 1 | 0 | `f1f5d6a2-4904-513e-b8c7-5f87e3c3a718` | `e7e86bfe-00d4-5cf9-9da9-4261c5ddd3dc` |
| TR-SWIM-006 | 10 / A10:O10 | 3500 m | 1 | 0 | `519e3d64-6fb3-54dd-b471-69e8ecfce9e7` | `2e36c911-0695-5d03-a69c-d5708f290d4a` |
| TR-SWIM-007 | 11 / A11:O11 | 4000 m | 1 | 0 | `53f8b3e4-0ec6-5f00-8e0d-1d74094c6b2b` | `9ebdd1ec-60d8-5299-91d0-f9c5db5bb071` |
| TR-SWIM-008 | 12 / A12:O12 | 4500 m | 1 | 0 | `e20a422e-b1ae-5f85-9918-39a48a45f6cc` | `c67edd98-2417-590d-a4eb-b5c86e05e370` |
| TR-SWIM-009 | 13 / A13:O13 | 5000 m | 1 | 0 | `2d60c436-4288-5ce7-8ef5-5a8216193c05` | `41307d92-73ee-5268-8c1e-f6ff2e0aaa0e` |
| TR-SWIM-010 | 14 / A14:O14 | 1600 m | 12 | 150 | `ffa4c527-2068-57b2-8222-8ff142519bb4` | `6d598622-d73a-5b26-b894-cc2242de9877` |
| TR-SWIM-011 | 15 / A15:O15 | 2600 m | 22 | 300 | `dae19bce-a715-55df-971c-2bc1859dff38` | `7747198e-100f-5356-bcf0-4df0e6815c7d` |
| TR-SWIM-012 | 16 / A16:O16 | 2600 m | 12 | 300 | `47a706d5-c46b-5671-938a-e914b013a3eb` | `68986d11-c616-5984-b04a-d1ca38766cbf` |
| TR-SWIM-013 | 17 / A17:O17 | 2600 m | 10 | 240 | `9375f32a-3b41-5731-81b2-53b6561cb01a` | `2395bb8c-74d5-58a1-bb56-e3a1d0a8befc` |
| TR-SWIM-014 | 18 / A18:O18 | 3000 m | 19 | 240 | `fe80e291-59bb-5c4e-ae08-46fe0ff061c6` | `1f4fe951-2df1-5267-998b-691a1447bc76` |
| TR-SWIM-015 | 19 / A19:O19 | 1600 m | 22 | 300 | `79930f44-844c-51f0-a004-ea7a2db9491a` | `ff0880f6-8d53-5aa7-a61f-2ee7b1797e1a` |
| TR-SWIM-016 | 20 / A20:O20 | 2100 m | 32 | 450 | `c9e244d3-1675-56ca-ad59-303795f4b156` | `dd741a99-abd4-59a9-8b16-39270daccd4f` |
| TR-SWIM-017 | 21 / A21:O21 | 2600 m | 42 | 600 | `686d8823-1a6c-5427-a17e-5c1d34d1e964` | `09ea1e3b-4400-5aa9-8cdc-5d3658467d32` |
| TR-SWIM-018 | 22 / A22:O22 | 1600 m | 22 | 150 | `54ba9755-a148-5574-98b9-480fcc448730` | `0acd745c-b39c-5172-aa57-8fdc9e4af0c4` |
| TR-SWIM-019 | 23 / A23:O23 | 2100 m | 32 | 225 | `7f51a709-bacf-52f6-a13b-2ed065742510` | `1364cd56-bd5c-5841-bec7-380cf977929e` |
| TR-SWIM-020 | 24 / A24:O24 | 2600 m | 42 | 300 | `6369026c-698c-53c9-842a-0d46ca452ece` | `c4ed3ba4-dd20-5496-8963-6cf273e9d418` |

## Preserved review proposal and report custody

The six-column 61-row final selection proposal is preserved in each record's
`selection.original_columns`, with line number, report name and exact report hash.
Explicit draft wrappers retain bucket/phases, capability, selection, block RPE,
beginner/repeat eligibility and method/swim planning compatibility. Unknown values
stay `null`. No field is used by an active catalog. TR-BIKE-013 retains its
explicit-only/archive and automatic-beginner hold. No duration cap is inferred.

All 16 review reports were copied without modifying originals. Copied report hashes:

| Report | SHA-256 |
| --- | --- |
| JOREN_CYCLING_CATALOG_VALIDATION.md | `4b104855e5ee0a25e00ada966e4ec7fb25dff59439a18e0265975932e7a6e807` |
| JOREN_CYCLING_REALIZED_V2_ELIGIBILITY.md | `bdf6ba90908015856d2534d55d60bf511f8cb08f1417c1b2eabd6847f149a7a6` |
| JOREN_CYCLING_TSS_RECONCILIATION.md | `1076ed90f52ab0f655337d7ae6f08c10b93cf04b7048d4d212bfbbe642ea0405` |
| JOREN_RUNNING_CATALOG_VALIDATION.md | `f908ee52c1ab093faaae07849ca4ce43fc790ef6b29e45f7b93d0cb44f7c8efb` |
| JOREN_RUNNING_REALIZED_V2_ELIGIBILITY.md | `8bbaf19aca59198da4a6daebd9548e582aaf7dfe9ff859532a2c6dbd2eaa33b1` |
| JOREN_RUNNING_TSS_RECONCILIATION.md | `fc64b05f16738cca70cddeff6b6e1fdfd3acc6e0d00e1328f6c4f7da134ac2c4` |
| JOREN_SWIMMING_CATALOG_VALIDATION.md | `bb0bfc350c9aca2bb2c86d9330cb479d7410f5b22dffe20b379db4f73b1af533` |
| JOREN_SWIMMING_REALIZED_V2_ELIGIBILITY.md | `7793c3c707ebeb4cb02ffc41f6c6ba01fd51bceadb0c5e14fdcb15d95a107c5b` |
| JOREN_SWIMMING_TSS_RECONCILIATION.md | `6ff7e67a397c4d7d8debe067a96ddc8fb388440ee20b2a314c7cff8f380b8cb5` |
| JOREN_THREE_SPORT_CATALOG_DECISION_REGISTER.md | `3981d6e5990af55a8a485c8e69baa1728fe81e78ee884234e9a30b6d67adc4e8` |
| JOREN_THREE_SPORT_CATALOG_IMPORT_READINESS.md | `5ddbb61e78b505f50db339b6f199f23d977286f847a23baa37fe4ba6c8fabef9` |
| JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md | `070b6cbe50ea3e6ea1f8ce6912dfe94e43e4191f7af39d62d1b18ca7a878d17d` |
| JOREN_THREE_SPORT_FINAL_RECONCILIATION.md | `7ab267fedf1c2e7ff4e1ee043e5a0896047235ed15d6cc0592314cf50c4a59e0` |
| JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md | `e4c20459bfe5f8b62d549e974892f477a2d0f51b192fa4596e5767ef37fe7983` |
| JOREN_THREE_SPORT_PLANNING_SIMULATION.md | `d3996c3f32412f9389ceb91aa5e08a2b524d560243c5f6919e195d4862512e89` |
| JOREN_WORKOUT_CATALOG_IMPORT_PLAN.md | `6a032a9ae29e98e3ff0b323d2a1fbf60eb04edd39d765093299c913462436675` |
