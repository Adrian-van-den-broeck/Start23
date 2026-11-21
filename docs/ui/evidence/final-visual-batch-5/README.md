# Calendar visual evidence

Public, inert DTO fixtures rendered by the actual native CalendarScreen, calendarViewModel, useCalendarNavigation, accepted shell/footer and read-only WorkoutDetailScreen. Captured on Android 15 / API 35, emulator-5554, 1080 × 2280 pixels. No athlete content or mutation responses are used.

The temporary route is retained as `temporary-dev-calendar-review.tsx.txt` for provenance and removed from the app after verification. Native movement-return fixtures demonstrate supplied stored locations; production controller and movement-boundary tests cover mutation behavior.

`case-ledger.json` lists 47 completed cases: Week and selected Month at 320/360/~393/412 dp, default/200% text and Dutch/English (32 cases); 11 canonical state variants; four additional 320 dp/200%/English stress cases. Each `*-page-N.png` is an entire native viewport, with its actual accessibility hierarchy in `.xml` and density/font/fixture metadata in `.json`. Numbered pages overlap to prove every control can become fully visible. `inspection/` contains labeled contact sheets of these complete viewport sequences.

`native-audit.json` checks mapped content, all dates, supplied counts/measures, independent siblings, authoritative movement locations, footer selection, responsive modes, single scroll owner and fully visible targets. Targets use native pixel quantization of the 48 dp minimum; source dimensions remain at least 48 dp. Its artifact hashes bind every accepted PNG/XML/metadata triple.

`native-interactions.json` records real local navigation, Today, outside-month selection, rapid mode changes, read-only detail entry and exact Close/Back restoration. `interaction-*.png` captures the corresponding native states. The Move seam invokes an inert callback for the exact occurrence.

`reduced-motion-calendar.*` records rendering with all three Android animation scales at zero. `talkback-*-focus.png` records actual TalkBack focus using emulator hardware touch exploration. Baseline and cleanup JSON record restoration of accessibility settings and the still-denied notification permission. `device-cleanup.json` records route removal, restored density/font/locale and return to normal Week without persisting live content.

On resume, the prior Metro server was absent and the emulator's host window stalled. Recovery restarted ADB and Metro on the original port, then reopened the same stored AVD in headless mode with the documented software renderer. `emulator-recovery.json` and `headless-recovery.json` record this environment recovery. A transient existing expired-session gate was observed; normal authenticated Dutch Week subsequently returned with the stored session. No logout, credentials, authentication override, app-data wipe or UI-version preference change was performed. The recovered Metro and headless emulator remain running.

`full-mobile-tests.json`, `jest.log`, `typecheck.log`, `unused.log` and `command-checks.json` record the final mobile checks. `scope-audit.json` fingerprints the exact Batch 5 source delta against accepted Batch 4. `contrast.json` includes text/control pairs and the worst-case Calendar landscape beneath copy. `reference-hashes.json` preserves M1/M2 and all Calendar/movement references. `verification-summary.json` binds the final gates.

The Python scripts are evidence/review helpers, not app dependencies. No backend bridge or authentication override is started. Keyboard evidence remains in accepted Batch 2: Calendar adds no editable input or keyboard owner. Physical iPhone and release validation remain roadmap gates outside this Android visual batch.
