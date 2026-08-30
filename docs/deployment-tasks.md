# Local and production tasks

Run the Start23 tasks from **Terminal > Run Task** in VS Code.

## Select the backend target

- `Start23: Switch to local mode` sets `mobile/.env` to
  `http://127.0.0.1:8000`. The existing `Start23: Start backend` task then runs
  the local FastAPI development server.
- `Start23: Switch to production mode` selects the public Railway HTTPS URL.
  The task looks up the service domain and generates a Railway-provided domain
  when needed. It also updates the Railway Polar callback without deploying.
  The `Start23: Start backend` task then uploads and deploys the repository to
  the Railway service named `start23` and verifies `/ready`.

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
2. Run `Start23: Start backend` and wait for the Railway health check.
3. Run `Start23: Build Play Store AAB`.

To build the same Start23 application under the additional Android package
`com.adrivdbs.wombo`, run
`Start23: Build Play Store AAB (com.adrivdbs.wombo)` instead. The original
task continues to build `com.adrivdbs.start23`.

The build task synchronizes these public values from `mobile/.env` to the EAS
production environment:

- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

It then creates a production Android App Bundle with EAS and downloads it to
`mobile/dist/start23-playstore-<versionCode>.aab`. Google Play uses `.aab`
bundles for new app releases; `.apk` is an installable device format, not the
Play Store upload format.

The default package remains `com.adrivdbs.start23`; the `wombo` profile uses
`com.adrivdbs.wombo`. EAS stores the Android `versionCode` remotely and
increments it for every production build, as configured by
`appVersionSource: remote` and `autoIncrement: true`.

The first `wombo` build may ask EAS to create a separate Android keystore because
Android signing credentials are associated with the application identifier.
