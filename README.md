# Personal FHIR Client

A patient-facing SMART on FHIR client. Lets an individual patient pull their own structured medical records from Epic-powered patient portals (MyChart and similar) and store them locally as JSON, for longitudinal self-tracking and personal health analytics.

## Why

Patients with complex medical histories often receive care across multiple unaffiliated health systems, each with its own patient portal. The portals offer PDF downloads that are slow to collect and produce unstructured data that can't be queried, graphed, or aggregated. This client gives the patient a single structured view of their own records without handing data to a third party.

## What it does

- Runs locally on the user's own machine (macOS, Linux).
- Uses the SMART on FHIR OAuth 2.0 authorization code flow with loopback redirect ([RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252)).
- Authenticates against Epic patient-facing FHIR endpoints (and any other SMART-on-FHIR-conformant EHR endpoints added in future).
- Pulls the authenticated patient's own FHIR resources: `MedicationRequest`, `MedicationDispense`, `Observation`, `Condition`, `Encounter`, `DiagnosticReport`.
- Stores each portal's results as JSON files in a user-configured local directory.
- Refreshes tokens for subsequent unattended re-syncs.

## What it does not do

- No cloud component, no server-side deployment, no analytics.
- No external API calls beyond the user's own chosen portals and those portals' OAuth/FHIR endpoints.
- No sharing of data between users.
- No write access to any medical record. Read-only.

## Status

In development. Built by one individual for their own longitudinal health tracking.

## Privacy and security

- All medical data stays on the user's own device.
- OAuth tokens (access + refresh) are stored locally and are the user's responsibility to protect.
- The `client_id` issued by Epic is embedded in the app — per the SMART on FHIR "public client" model for patient-facing apps. Authentication is anchored in the user's own MyChart login, not in a shared secret.

## License

TBD.
