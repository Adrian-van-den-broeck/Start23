# V6 activity compatibility implementation

17 November 2026, Europe/Amsterdam. Starting SHA: `0fa6509190d292d0c83e3076cda68c55624c202e`. Local implementation and PostgreSQL proof; no deployed-runtime certification or hosted installation.

## Decision: Option B, a forward versioned projection

Keep the historical shared projection exact and request V2 presentation metadata explicitly. This has the lowest existing-client and application rollback risk: G2 can commit with the historical JSON contract restored, without first deploying the complete V6 backend or an application bridge whose deployed base is still unidentified. A narrow backend bridge remains a possible alternative, but patching an assumed deployed source would not establish artifact compatibility.

New correction **C1**, `20261116231106_v6_activity_projection_compatibility.sql`, must be included **inside G2**, after accepted ordinals 2–12 and before its COMMIT. Its checksum is in the [rollout plan](JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN.md). No accepted migration was edited.

C1 restores `private.activity_public_json(uuid,uuid)` from the historical Phase-13 definition. All existing create, read, list, match, completion, correction, external-activity and provider consumers of that shared helper receive the old key set. Historical metrics, values and null semantics are retained. The migration changes function definitions and privileges only; it does not rewrite activities, inputs, loads or calculations.

The accepted expanded projection is retained as `private.activity_public_json_v2(uuid,uuid)`, with no direct EXECUTE for anonymous, authenticated or service roles. The new public-schema RPC `get_activity_presentation_v2(uuid)` is **service-only**, returning only the closed `session_rpe_version` metadata object. It exposes no private load, calculation or physiological evidence.

## Application use and ownership

`SupabaseActivityRepository` opts into this metadata only when its existing V2 storage contract is explicitly enabled. Every create/get/list/match/complete/revise result first comes from the existing owner-scoped operation. Only the returned, validated UUID is used for the metadata request. A foreign/not-found activity never reaches that service request. Unexpected keys or versions fail closed; the public strict model was not relaxed.

The metadata RPC is a trusted server read, not an end-user owner RPC: it does not itself prove end-user ownership. Its service-only ACL, the preceding owner-scoped operation and the repository's restricted input path form that boundary. The separate verification factory adds the manifested owner-map restriction. No service credential is returned to a client.

Normal startup keeps both existing V2 settings false and the historical planning repository. No V2 calculation, selection or V6 generation is automatically enabled. Explicit V2 consumers of the corrected schema require C1; the verification adapter targets the complete 65-file candidate.

## Actual PostgreSQL evidence

The historical strict model and its actual `_response` method were loaded from Git at `5d71c688deb610bf5ec79c0f6fac77c835be6b51`; their source hashes are recorded. That is a demonstrated historical consumer, **not the identified production artifact**.

| Actual SQL boundary | Historical strict consumer | Current consumer |
| --- | --- | --- |
| Accepted 47 files | PASS on stored activity get/list responses | PASS; legacy default |
| Accepted 63 files, uncorrected | Expected failure: `extra_forbidden(session_rpe_version)` | PASS |
| Corrected G2 and complete 65 files | PASS; historical projection has the exact old keys | PASS; explicit V2 metadata/guidance supported |

The uncorrected failure remains recorded. The 63→65 correction preserved all **64** public/private table hashes. The two 47→65 rehearsals, including the reproduced hosted definitions/default ACLs/catalog grants, preserved all **51** historical table hashes after every group. New V2 activity creation was exercised inside rollback transactions: its historical projection validates in the old model; the explicit projection produces all ten approved guidance entries in the current model.

Evidence: [47/63/65 results](blocker-resolution-20261117/activity-boundaries--boundary-results.json), [current/old model probes](blocker-resolution-20261117/activity-boundaries--corrected-65-activity-compatibility.json), and [complete verification](blocker-resolution-20261117/verification.json). The 17 new repository tests cover all six activity consumers, owner-first metadata lookup and closed metadata validation. Existing activity, lifecycle, deletion/cascade and recursive privacy tests remain in the complete regression.

## Deployment and rollback boundary

C1 closes the demonstrated projection incompatibility locally. No compatibility application deployment is required before G2 **for this projection correction**. C1 cannot be deferred to a separately committed G4: doing so would expose migration 5's incompatible intermediate response.

The actual Railway source SHA, runtime configuration and installed/mobile release routing remain unverified. Public OpenAPI and `/health` are not source identity. Other shared lifecycle changes still require the approved hosted historical smoke before production execution. Do not claim unchanged deployed-runtime compatibility from the model probe alone, and do not deploy or downgrade an unidentified backend.
