# Isolated A9 native benchmark

Development tooling only. Never point this fixture at hosted services. It serves
existing synthetic public test DTOs on **127.0.0.1:18749**, with 40 ms reads and
240 ms auxiliary intake reads. It never logs bodies, credentials or health values.
The fake Auth endpoint is a performance fixture, not an authentication/security
test. No telemetry, new dependency or production entry point is introduced.

The recorded environment is Windows, Android SDK emulator/ADB, existing JDK 17,
an Android 15 API 35 x86_64 Pixel 4 AVD, Expo 57 / RN 0.86.3 / Hermes release
variant. The JS bundle runs with development mode disabled, with no Metro server
or debugger. Generated local signing/configuration is for this benchmark only.

Use a disposable checkout at the desired commit. Install its locked mobile
dependencies. Copy `app.config.benchmark.cjs` to `mobile/app.config.js` only if
that file does not already exist. Set:

```powershell
$env:EXPO_OFFLINE='1'
$env:EXPO_NO_TELEMETRY='1'
$env:EXPO_PUBLIC_UI_VERSION='v1'
$env:EXPO_PUBLIC_API_BASE_URL='http://10.0.2.2:18749'
$env:EXPO_PUBLIC_SUPABASE_URL='http://10.0.2.2:18749'
$env:EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY='synthetic-local-benchmark-public-key'
```

Run Expo `prebuild --platform android --no-install`. In that **generated benchmark
project only**, enable `android:usesCleartextTraffic="true"` on the application
element so the emulator can access localhost. Build `:app:assembleRelease`, with
`-PreactNativeArchitectures=x86_64`, using existing SDK/cache tooling. No native
dependency upgrade is needed. Windows may need a temporary short `SUBST` alias
and short CMake staging paths; the report records that build workaround. Always
remove temporary configuration afterward; do not commit generated native folders.

Run `node mobile/performance/native/server.cjs`. Start a read-only existing AVD
and install **only** `com.adrivdbs.wombo.a9benchmark`. Never clear/open the ordinary
Wombo package. Sign in with arbitrary synthetic test credentials. Once the V1
Week is ready, run from the checkout root:

```powershell
python mobile/performance/native/benchmark.py --runs 5 --output .runtime/native.json
```

The fixture uses current local dates and existing synthetic plan/workout DTOs.
It captures screenshots in memory through the already-installed `pngjs` package.
Only public Week/Calendar headings and a form-label pixel mask are compared;
no screenshot, field value, account identity or full response is written by the
measurement runner. JSON contains operation names, safe route counts, aggregate
server timings and marker/capture durations only. Package scope is fixed to the
benchmark app. Profile is opened through the real V1 menu; Back returns to the
retained owner. External deep links are unsuitable because they can reload the
app and distort warm-navigation counts.

The marker metric is an **upper bound** for a stable readable heading/form label
after the required response, including ADB/screenshot/PNG overhead. It is not an
exact first-frame, JS-thread, touch-latency or physical-device measurement.
Sampling cost is recorded in every run. Keep before/after inputs, display, build,
marker rule and sampling identical; report medians and observed maxima, without
CI timing thresholds or significance claims. API counters exclude the fixture's
own metrics/reset requests. Warm Week/Calendar requires zero network requests.

Stop this local server and the read-only emulator after use. The process restart
and screen revisit cases do not replace A8's deterministic offline, cancellation,
account-switch and ambiguous-write tests.
