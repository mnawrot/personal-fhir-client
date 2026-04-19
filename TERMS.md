# Terms of Use — Personal FHIR Client

**Effective date:** 2026-04-19

## 1. Nature of the application

Personal FHIR Client ("the app") is an open-source, self-hosted, patient-facing SMART on FHIR client. The app runs entirely on the user's own device and retrieves the user's own medical records from patient-facing FHIR endpoints operated by the user's healthcare providers.

There is no hosted service, backend, or server component operated by the developer. The developer does not host, process, transmit, store, or receive any user data.

## 2. What the app accesses

With the user's explicit authorization through each healthcare provider's standard OAuth 2.0 consent flow (e.g., MyChart login), the app may retrieve the authenticated user's own FHIR resources, which may include but are not limited to:

- Demographics (`Patient`)
- Medications (`MedicationRequest`, `MedicationDispense`)
- Laboratory and clinical observations (`Observation`)
- Diagnoses (`Condition`)
- Encounters (`Encounter`)
- Diagnostic reports (`DiagnosticReport`)
- Procedures (`Procedure`)
- Allergies (`AllergyIntolerance`)
- Immunizations (`Immunization`)
- Care plans, goals, and other clinical records granted by the authorizing endpoint

The app only requests read scopes. It never writes to, modifies, or deletes any medical record.

## 3. Where data is stored

All retrieved data is stored as JSON files in a directory on the user's own local device, chosen by the user. OAuth tokens (access tokens and refresh tokens) are stored on the user's local filesystem.

No data is transmitted to any third party. No analytics, telemetry, crash reporting, or usage metrics are collected or sent anywhere by the app.

## 4. User responsibilities

By running this app, the user is responsible for:

- Securing their own device and operating system, including filesystem access controls and disk encryption.
- Safeguarding the OAuth tokens stored on their device. Anyone with read access to the token file can act on the user's behalf against the authorized endpoints for the lifetime of those tokens.
- Protecting the `client_id` configuration and the local copy of retrieved medical records.
- Complying with the terms of service of each healthcare provider's patient portal when authorizing the app.
- Revoking the app's authorization at each portal (via MyChart account settings or equivalent) if they wish to stop the app from being able to retrieve further data.

## 5. No warranty

The app is provided "AS IS," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. The app is a personal, individual-use project and is not clinically validated. Nothing retrieved or displayed by the app constitutes medical advice.

In no event shall the developer be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the app or the use or other dealings in the app.

## 6. No support commitment

The app is maintained by one individual for their own use. No uptime, availability, bug-fix, or feature-delivery commitments are made. Use at your own discretion.

## 7. Open source

The app's source code is publicly available at https://github.com/mnawrot/personal-fhir-client under a license to be specified in the repository. Users are free to audit, modify, or self-host the app subject to that license.

## 8. Third-party services

The app interacts only with:

- Patient-facing FHIR OAuth 2.0 authorization and token endpoints of healthcare providers the user explicitly configures (e.g., Epic-powered MyChart portals).
- The patient-facing FHIR API endpoints of those same providers.

No other network calls are made by the app.

## 9. Changes to these terms

These terms may be updated from time to time. Material changes will be reflected by an updated effective date at the top of this document. The current version is always available at https://github.com/mnawrot/personal-fhir-client/blob/main/TERMS.md.

## 10. Contact

For questions, issues, or responsible-disclosure reports, open an issue at https://github.com/mnawrot/personal-fhir-client/issues.
