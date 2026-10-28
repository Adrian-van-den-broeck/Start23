# A9.2 local planning execution boundary

Pure catalog search now runs in one stdlib spawned process per ASGI application.
One calculation runs and one may wait; further admission returns the existing
503 planning-unavailable response. There is no new service, dependency, worker
configuration, retry loop or persisted queue. The shipped one-Uvicorn-process
configuration is unchanged. Adding ASGI workers later also adds one lazy child
per worker and requires memory/CPU capacity measurement before deployment.

Authentication, repository calls, input ownership, server revisions, proposal
fingerprints and persistence remain in the API process. Only detached planning
inputs and pure functions cross the executor boundary. The three formerly bound
pure swipe helpers are static functions, so no repository, HTTP client or access
credential is serialized. Immutable mapping proxies, enums, UUIDs and Decimal
values round-trip without JSON conversion. Each job receives a copy of its
caller's Decimal context. The original exception code and message survive the
process boundary; no fail-closed case becomes a successful result.

Cancellation while waiting removes admission. Cancellation after submission
abandons the owner's result but holds capacity until CPU execution finishes;
the abandoned continuation cannot reach persistence. A client disconnect or
deadline does not prove server cancellation or rollback. A write may already
have committed when a response conversion cannot run or its owner disconnects.
A8 still classifies uncertain writes as unknown and retains their original
identity and operation-specific reconciliation. No generic mutation retry was
added. Process failure fails closed to 503 and requires application restart;
there is no automatic process-restart/replay loop.

A bounded thread prototype was measured first, rather than assuming
`asyncio.to_thread` solves GIL contention. With two expensive planning requests,
its authenticated Calendar read waited a median 627 ms in the local fixture.
The spawned-process version measured 50 ms median (3 runs); the A8 event-loop
baseline was 31.277 s. These are synthetic authenticated ASGI measurements on
the documented Windows host, not production HTTP or database benchmarks.
The first planning request additionally pays process startup; steady-state
domain timing is reported separately. Safe public aggregate evidence is in
`evidence/a9`; no athlete records, request bodies or credentials are logged.

Verification includes real authenticated transport/service requests while a
controlled child job is held, cancellation before persistence, bounded
admission, queued cancellation, Decimal-context restoration, fail-closed error
serialization and all 15 exact A8 parity scenarios through the spawned process.
