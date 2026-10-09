# Batch 11 review evidence

Baseline: accepted Batch 10, f25379d. Production changes are split into A (Zones overview/history) and B (calibration lifecycle). The direct target is docs/ui/mockups-final/03-zones.png, supported by M4 for forms.

Native PNGs are Android 15/API 35 Pixel 4 development-client captures. Matching XML and JSON preserve accessibility bounds, logical width, font scale, state, time and fixture provenance. Contact sheets only arrange unmodified captured viewports; their cropped edges represent scrolling positions, not accepted clipped controls.

The temporary root renders actual production screens with inert typed DTOs. Transport to athlete services is blocked. Callback captures prove UI dispatch only. Test-result fixtures are copied from existing tests; they do not establish a successfully executed calibration or server persistence. Current protocol projections were exported read-only from the unchanged CalibrationService, with hashes in protocol-provenance.json. No DB, service key or real athlete was used.

Source-hash and functional-freeze evidence protect domain/state handlers, API contracts, navigation, dependencies, backend, database and references. Root routes are restored before final integration verification. Fixture sources are retained as text for reproduction, not as shipped executable routes.

Rejected captures and preliminary failed verification are excluded from accepted totals. Required production tests retain their assertions. The external clock setup affects only the two existing proposal tests that name Wednesday 7 October; it retains the normal Jest setup.

Native scripts require the existing owned emulator/dev client, an inert Metro gallery on localhost 8084 and the fixture root snapshots. They never run against a live backend. Use run-matrix.py, native-audit.py, make-inspection.py, then native-interactions.py sequentially for the one device.

Final integration: strict TypeScript passes; focused 5 suites / 35 tests and full 63 suites / 583 tests pass on restored production roots. See command-checks.json for the retained normal Jest setup plus scoped fixture date. Native matrix: 51 cases / 357 viewports / 138 inspected contact sheets, 232 state/privacy checks and 597 fully visible controls. Target PNG copies are byte-identical to the canonical user-provided references. TalkBack-enabled source selection and result display are captured; focus retention, speech and physical/iOS behavior remain unverified. All owned preview processes and temporary device settings are restored.

Committed test logs normalize trailing whitespace on blank console-warning lines; results and warning text are unchanged. Original stdout is retained locally with rejected/raw logs.
