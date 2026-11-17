# Wombo Privacy Policy

**Last updated:** [OWNER INPUT REQUIRED: publication date]

## Introduction

Wombo is a training planning app operated by **[OWNER INPUT REQUIRED: legal name of the Belgian developer/controller]**, based at **[OWNER INPUT REQUIRED: business address in Belgium]**. This policy explains how Wombo handles personal information when you create an account, plan training, record activities, complete check-ins, or connect Polar. Contact us at **[OWNER INPUT REQUIRED: working privacy contact email]**.

Some features, including Polar connection and AI-assisted suggestions, may be unavailable depending on how Wombo is configured. **[OWNER INPUT REQUIRED: confirm which features are enabled before publication.]**

## Information we collect

| Information | When and why we collect it | Choice and storage |
| --- | --- | --- |
| Account information | Your email address, password, account identifier, and authentication sessions let you register and sign in. | Required for an account. Supabase Auth processes account credentials and sessions. The app stores a refresh token in device secure storage. |
| Profile and setup | Your date of birth, time zone, confirmation that you have a heart-rate monitor, and prior training hours help set up your training. You can also provide a first and last name and resting heart rate. | Core setup fields are required to complete onboarding; names and resting heart rate can be omitted. Profile and training records are stored in Supabase. Your language choice is stored on your device. |
| Goals, plans, and training history | Race type, name and date, distances, target times, optional focus text, available days, training choices, scheduled workouts, plan approvals, and historical training information are used to build and manage your plan. | Required only when you use the related planning features. Stored in Supabase. |
| Activity and fitness information | Activities you enter or import may include sport, date and time, time zone, duration, distance, elevation, heart rate, pace, speed, power, time in training zones, perceived effort, and links to planned workouts. We use these to record progress, evaluate training, and suggest changes for your approval. | You choose whether to record an activity or connect Polar. Stored in Supabase. |
| Health-related information | Check-ins can include fatigue, injury or illness reasons, symptoms acknowledgement, exercise restrictions, and any professional advice you enter. Calibration and zone setup can include heart-rate measurements, thresholds, test results, and calculated zones. We use this information for the training and safety features you choose to use. | Some measurements are required for particular setup or check-in steps; optional text and advice can be left blank. Stored in Supabase. This information may qualify as sensitive health data under the GDPR. |
| Check-in text and other content | If you use the optional free-text check-in helper, you may enter up to 1,000 characters about your week. The server uses it to suggest fields for you to review. The submitted text is not saved as a check-in record by that helper; fields you confirm are saved. You may also enter a race focus, external activity name, or professional advice. | Optional. The text is sent to Wombo's backend and, if the AI service is enabled, to OpenAI. Confirmed fields and other content are stored in Supabase. |
| Polar connection data | If you choose to connect Polar, Wombo sends a Wombo account reference to Polar, receives your Polar user identifier and access token, and requests exercise summaries and available FIT activity files. A FIT file may contain detailed workout information, potentially including a route or location if your Polar device recorded it. | Optional. Connection details, imported activities, and private FIT files are stored in Supabase. Polar also processes the connection and activity data under its own privacy terms. |
| Beta access | If you redeem a Pioneer access code, Wombo processes a digest of the code, redemption status, time, and security/rate-limit attempts. | Optional. Stored in Supabase. |
| Technical records | Requests to the backend generate a request identifier, request path, method, error details and timestamps in server logs. Hosting and authentication services may also process network information such as IP addresses as part of operating their services. | Necessary to operate and protect the service. Backend logs are sent to Railway; provider-side logging and retention require confirmation. **[OWNER INPUT REQUIRED: confirm production logs, IP handling and log retention.]** |

The app does not currently include advertising, app analytics, crash reporting, push notifications, camera or photo capture, payments, or advertising-ID collection. It does not ask for Android location or camera access. The current Android configuration includes internet and vibration permission, plus system alert and older Android storage permissions. We found no app feature that reads your photos or files from the phone; Polar files are fetched by the server from Polar. **[OWNER INPUT REQUIRED: verify the final release permissions and remove unused ones.]**

## How we use information

We use the information above to create and secure your account; provide training plans, zones, activities, check-ins, and optional Polar imports; show and apply changes you approve; respond to support and privacy requests; and investigate service failures or misuse. Wombo calculates training decisions on its own backend. If OpenAI is configured, it may receive limited plan facts to write an explanation, or optional check-in text, week and time zone to suggest check-in fields. OpenAI does not decide or apply your training plan. The OpenAI requests in the reviewed code set `store` to `false`; this is not a guarantee that no provider security or abuse records exist.

**[OWNER INPUT REQUIRED: identify the GDPR Article 6 legal basis for each purpose and the Article 9 condition for health data. The app currently has no explicit health-data consent flow.]**

## Third-party services and data sharing

- **Supabase** provides account authentication, database services and private activity-file storage. It processes account, profile, training, health and integration records on our behalf.
- **Railway** hosts the Wombo backend and receives requests and operational logs. The backend processes the personal information needed for the feature you use.
- **Polar**, only if you connect it, handles authorization and receives a Wombo member reference. Wombo then retrieves your Polar exercise information and available FIT files. Disconnecting stops new access and removes Wombo's stored Polar access token, but does not remove activities or FIT files already imported.
- **OpenAI**, if enabled on the server, receives limited training-plan facts for explanations and optional check-in text, week start and time zone for check-in suggestions. The AI feature is not required to use the structured check-in form.
- **Expo and Google Play** are used to build and distribute the Android app. **[OWNER INPUT REQUIRED: confirm any production update, telemetry, or store services and their data practices in the shipped build.]**

We do not use the app to sell personal information or serve targeted ads. We disclose information to the services above to deliver the features described. **[OWNER INPUT REQUIRED: verify processor agreements, any additional subprocessors and any other legally required disclosures.]**

## Data retention

The current code does not establish a general retention period for account, profile, training, health, or log data. Polar production configuration requires retention settings for raw FIT files and imported activity records, but the reviewed code does not contain an automatic job that enforces those periods. OAuth connection states expire after a short period for use, but no general cleanup schedule was verified. **[OWNER INPUT REQUIRED: set and implement retention periods for each data group, including logs, backups, Supabase Auth records, FIT files and provider records.]**

## Account and data deletion

You can request deletion of your account and associated Wombo data through **[OWNER INPUT REQUIRED: public account-deletion request URL]** or by contacting **[OWNER INPUT REQUIRED: working privacy email]**. **The app version reviewed does not yet provide an in-app deletion option, and the deletion workflow is not fully implemented. [OWNER INPUT REQUIRED: implement and verify the in-app and web deletion paths before publishing this statement as a live service.]**

Signing out or disconnecting Polar does not delete your Wombo account. Deleting your Wombo account does not necessarily delete information Polar keeps under your Polar account. **[OWNER INPUT REQUIRED: define verified deletion timing, backup handling and any legally required retention exceptions.]**

## Data security

The app stores its refresh token in the device's secure storage. The backend verifies account access tokens; user-owned database records use access controls, and the Polar activity-file bucket is private. Wombo's connections to Supabase, Polar and OpenAI use HTTPS in the reviewed configuration. **[OWNER INPUT REQUIRED: confirm that the production mobile API URL and every shipped network path use encryption in transit, and review Android backup settings.]** No system can be guaranteed perfectly secure.

## Children's privacy

Wombo asks for a date of birth during setup but the reviewed app does not implement an age gate or parental consent flow. **[OWNER INPUT REQUIRED: state the intended minimum age, whether children may use Wombo, and implement the required age/parental-consent controls before release.]** If you believe a child provided information contrary to that policy, contact us at the privacy address above.

## Your privacy rights

If the GDPR applies to you, you may ask to access, correct, erase or receive a copy of your personal information, and in applicable cases restrict or object to processing or withdraw consent. You may also complain to a data protection authority, including the [Belgian Data Protection Authority](https://www.gegevensbeschermingsautoriteit.be/burger/acties/klacht-indienen). Contact **[OWNER INPUT REQUIRED: working privacy email]** to exercise your rights. We may need to verify your identity before acting on a request. **[OWNER INPUT REQUIRED: confirm the rights-request process and response arrangements.]**

## International transfers

Supabase, Railway, Polar and OpenAI may process information in different countries. The deployment region, subprocessors and applicable international-transfer safeguards cannot be confirmed from the repository. **[OWNER INPUT REQUIRED: identify hosting regions, cross-border transfers and the relevant GDPR safeguards, then describe them here.]**

## Changes to this policy

We may update this policy when our app or data practices change. The updated version will show a new date on this page. **[OWNER INPUT REQUIRED: decide how material changes will be notified to users.]**

## Contact

**[OWNER INPUT REQUIRED: legal operator name]**  
**[OWNER INPUT REQUIRED: Belgian business address]**  
**[OWNER INPUT REQUIRED: working privacy email]**
