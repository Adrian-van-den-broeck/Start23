# V6 mobile lifecycle completion

8 November 2026. Branch `feat/joren-v6-lifecycle-completion`.
Implementation `bb4ac2c917780740551443380ef6fde7a4db4e09`, based on `31a8ed0cfad831780b405030121817df50e8fa2c`.

The existing Expo planning/check-in/calendar controllers support the newly
implemented server lifecycle paths without a product UI change. No screen,
navigation, client physiology or safety permission was added. The current default
application remains historical; the explicit local V6 test seam also injects V6
planning into the existing check-in route dependency.

`usePlanningController` already sends `physical_workout_id` when present, along
with the reviewed active revision and requested date. Server validation remains
authoritative. `PlanningFlowProvider` and `useCalendarController` replace the active
week's calendar rows when the active revision changes, preserving surrounding
ranges. Logical IDs stay stable while activity attachment resolves the new physical
row. Source-backed details use the original source prescription.

Four new component/controller cases consume actual PostgreSQL-backed FastAPI
responses from `v6-completion-http.test-fixture.json`:

1. Move a confirmed source workout: one existing PATCH using its exact physical
   locator/revision; calendar removes the old date and shows the new date; logical
   ID and source prescription survive; unrelated dates remain unchanged.
2. Unmount/remount: discovery retrieves the latest confirmed revision and physical
   mapping, while the original check-in proposal remains visibly pending in its
   own recorded snapshot.
3. Conflict: preserve the reviewed revision and show the existing reload message.
4. Lost acknowledgement: reload authoritative confirmed state without issuing a
   second move after a newer stored revision appears; retain the existing review
   message instead of claiming an ambiguous write succeeded.

All previous V6 source/swipe/submission/confirmation/calendar/activity presentation
and historical controller tests remain. **904 tests in 85 suites pass**, with no
skips; strict TypeScript and unused-local/parameter checks pass. The initial
accepted baseline was 900 tests in 84 suites. Recorded transport, identity and
secure storage are simulated; these are not authenticated device tests.

Android Hermes export and an offline x86_64 debug APK build pass using installed
SDK/Gradle caches and the existing task-only Windows short-path helper. No native
or dependency manifest was changed. The build performed 497 tasks and took
4m13s in its successful invocation. See the verification manifest for the APK
hash. No app installation or actual device scenario was executed. Windows has
no iOS/Xcode build/signing route here.

The service rejects evidence-bearing weeks, stale/foreign references, unsafe HIGH
spacing, unavailable dates and pending-successor conflicts. These errors do not
grant the mobile client permission to override the server. Independent release
and authentication gates remain in the [Dutch gate register](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).
