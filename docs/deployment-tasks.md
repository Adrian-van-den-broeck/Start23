# Local and production tasks

Run the Wombo tasks from **Terminal > Run Task** in VS Code.

## Run on an Android emulator

Run `Wombo: Run Android app`. It starts directly with `Pixel_4_API_35_2` and
UI V2, without input prompts. The task reuses the selected
emulator or boots the selected AVD, waits for Android, configures the localhost
bridges, builds and installs the development APK, then starts Metro and opens
the app. The first native build takes longer; later builds reuse Gradle caches.

It runs Metro
from a local worktree at the current `feat/wombo-ui-v2` integration commit;
the stabilization checkout itself contains only V1. In the app, use **UI V1**
and **UI V2** near the Week screen header to compare the implemented screens
without signing out. Switching is disabled while an operation is in progress.
Screens that have not yet been migrated retain their existing presentation.
The comparison is available only in development builds.

The launcher shares this checkout's native build when the UI worktree's package
files and Expo app configuration match. When they differ, it builds and installs
the UI worktree's own native app so new native dependencies are included. It uses
this workspace's public backend configuration. It does
not change branches or merge UI code into the stabilization checkout. The UI
worktree must have its mobile dependencies installed. When this workspace's
Metro server is already running, the task restarts it automatically with the
selected source and UI version. If another service owns port 8081, it chooses
a free port between 8082 and 8099 and configures Android to use that port.
Only Node processes running this workspace's known Expo CLI paths are stopped.
The app is reopened at its start route with stored login and app data retained.
Launcher ADB commands have a 20-second timeout. If Android's SDK connection
hangs, the task restarts the verified SDK daemon and retries once without
resetting the emulator.

The task checks the selected emulator's internal storage before building and
again using the APK size before installation. It reserves at least 512 MiB (or
three times the APK size plus 256 MiB) for staging, extracted files and Android's
storage reserve. When space is low, it trims disposable caches and removes the
stale `/data/local/tmp/app-debug.apk` installer. If space is still insufficient,
it stops with the AVD name and available space before starting Metro. Select
another AVD, such as the default `Pixel_4_API_35_2`, or free internal storage in
the emulator's **Settings > Storage**. The task preserves installed apps and
app data; it does not wipe the emulator.

The app uses the backend URL already configured in `mobile/.env`. For local
mode, start `Wombo: Start backend` separately before using API features. The
Android task can also use the existing production backend directly.

On Windows, the script temporarily maps the selected native source to a free drive letter
and places CMake build files in `.runtime/android-native` through that short
path. CMake hashes long object paths to stay below Ninja's path limit. This
also supports worktrees with a shared `mobile/node_modules` junction. The
React Native code-generation paths use the original drive consistently so
autolinking cannot mix drive letters. The mapping is removed when the task
exits; no repository move is required.

Run the same flow directly from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-start23-android.ps1
```

Pass `-UiVersion v1` to start the comparison in V1; the in-app buttons still
let you switch to V2. Pass `-AvdName <name>` to use a different emulator.

Use `-BuildOnly` to verify the x86_64 development build without starting an
emulator or Metro. `npm run android` only starts Metro and requires a development
app already installed on the emulator.

## Select the backend target

- `Wombo: Switch to local mode` sets `mobile/.env` to
  `http://127.0.0.1:8000`. The existing `Wombo: Start backend` task then runs
  the local FastAPI development server.
- `Wombo: Switch to production mode` selects the public Railway HTTPS URL.
  The task looks up the service domain and generates a Railway-provided domain
  when needed. It also updates the Railway Polar callback without deploying.
  The `Wombo: Start backend` task first applies pending migrations to the linked
  Supabase project, then uploads and deploys the repository to the Railway
  service named `start23` and verifies `/ready`. The database step runs first so
  a backend cannot be released before the schema and RPCs it requires.

The Railway private address `start23.railway.internal` is intentionally not
used by the mobile app. It is only reachable by services inside Railway. A
phone or emulator needs a public `https://...up.railway.app` or custom domain.

The first production run asks you to sign in to Railway when needed and to link
this local directory to the existing Railway project and production environment.
The task uses a pinned Railway CLI through `npx`; no global CLI installation is
required. Railway's local `.railway/` link metadata is ignored by Git.

Mode state is stored under `.runtime/` and is ignored by Git. Supabase server
secrets and Railway variables are never written into the mobile application.

## Create a Google Play build

1. Switch to production mode.
2. Run `Wombo: Start backend` and wait for the Railway health check.
3. Run `Wombo: Build Play Store AAB`.

Wombo is the only mobile application variant. The task always builds Android
package `com.adrivdbs.wombo` with EAS profile `wombo`; there is no Start23
package or production build profile fallback.

The build task synchronizes these public values from `mobile/.env` to the EAS
production environment:

- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

It then creates a production Android App Bundle with EAS and downloads it to
`mobile/dist/wombo-playstore-<versionCode>.aab`. Google Play uses `.aab`
bundles for new app releases; `.apk` is an installable device format, not the
Play Store upload format.

If EAS finishes the cloud build but local validation or downloading is
interrupted, resume that exact build without consuming another `versionCode`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\scripts\build-start23-playstore.ps1 -BuildId <eas-build-id>
```

The script validates the resumed build status and Android package before it
downloads the artifact.

The fixed package is `com.adrivdbs.wombo`. EAS stores the Android `versionCode`
remotely and increments it for every Wombo store build, as configured by
`appVersionSource: remote` and `autoIncrement: true`.

Android signing credentials remain associated with the Wombo application
identifier.
