# Local and production tasks

Run the Wombo tasks from **Terminal > Run Task** in VS Code.

## Select the backend target

- `Wombo: Switch to local mode` sets `mobile/.env` to
  `http://127.0.0.1:8000`. The existing `Wombo: Start backend` task then runs
  the local FastAPI development server.
- `Wombo: Switch to production mode` selects the public Railway HTTPS URL.
  The task looks up the service domain and generates a Railway-provided domain
  when needed. It also updates the Railway Polar callback without deploying.
  The `Wombo: Start backend` task then uploads and deploys the repository to
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

The fixed package is `com.adrivdbs.wombo`. EAS stores the Android `versionCode`
remotely and increments it for every Wombo store build, as configured by
`appVersionSource: remote` and `autoIncrement: true`.

Android signing credentials remain associated with the Wombo application
identifier.
