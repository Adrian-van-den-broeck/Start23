# Start23 Mobile Instructions

These instructions extend the repository-root AGENTS.md.
All root architecture, physiology, security, privacy and approval constraints
continue to apply.

## Stack

- React Native with Expo SDK 57 and TypeScript.
- Use strict TypeScript.
- Follow the exact installed Expo SDK version and its corresponding documentation.
- Do not upgrade Expo, React Native or Expo-managed dependencies unless the task
  explicitly requires it.

## Architecture

- The mobile client is presentation and interaction logic, not the authority
  for physiological or planning decisions.
- FastAPI is authoritative for domain validation and state transitions.
- Client-side validation may improve UX but must not replace server validation.
- Do not duplicate physiological formulas or planning rules in TypeScript.
- Never calculate, infer or expose planned/realized private load or TSS.

## Authentication and secrets

- Send the verified athlete access token to FastAPI.
- Never place Supabase secret/service-role keys, database credentials or LLM keys
  in Expo configuration, source code or the application bundle.
- Do not accept or persist an authoritative user_id from UI state.
- Store credentials only through the project's established secure-storage flow.

## State and mutations

- Respect server revision/precondition semantics.
- Do not work around stale-state conflicts with last-write-wins behavior.
- System-generated plan/zone changes remain pending until explicitly approved.
- Prevent accidental duplicate submissions from rapid taps and retries.
- Preserve server idempotency semantics.

## UX

- Handle loading, empty, error, stale and retry states explicitly.
- Preserve onboarding/resume behavior.
- Keep accessibility labels free of private load/TSS data.
- Do not present fail-closed backend behavior as successful completion.

## Engineering

- Reuse existing components and API clients before introducing parallel abstractions.
- Keep screens thin when practical.
- Add regression coverage for changed navigation/state behavior.
- Run strict TypeScript and applicable mobile tests before declaring completion.
- Do not modify backend files unless the task requires a cross-stack change.