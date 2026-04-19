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

In development. Built by one individual for their own longitudinal health tracking, but usable by anyone willing to register their own Epic developer app.

## Getting started

**Requirements:** Python 3.9+ (stdlib only — no `pip install` needed), `openssl` on `PATH` (macOS and most Linux distros have it).

**1. Register your own app with Epic.**

Go to https://fhir.epic.com/Developer/Apps and register a patient-facing SMART on FHIR app. Epic will issue you a `client_id`. This client is per-user — you need your own; you cannot use someone else's.

During registration, use these values:

- **Application Audience:** Patients
- **SMART on FHIR Version:** R4
- **SMART Scope Version:** v1
- **FHIR ID Generation Scheme:** Use Unconstrained FHIR IDs
- **Is Confidential Client:** No
- **Can Register Dynamic Clients:** No
- **Automatic Client Distribution:** USCDI v3
- **Redirect URI:** `https://127.0.0.1:8765/smart/callback`
- **Incoming APIs:** select all `(R4)` Read/Search variants for the resources you care about

**2. Set up a data directory.**

Pick a directory on your machine to hold your config, tokens, and exports. Save your Epic-issued production `client_id` to `.client_id` in that directory (just the UUID, one line, nothing else):

```bash
mkdir -p ~/my-health-data
echo "YOUR-PRODUCTION-CLIENT-ID" > ~/my-health-data/.client_id
chmod 600 ~/my-health-data/.client_id
```

If you also want to test against the Epic sandbox (which uses a separate, non-production `client_id` issued by the same app registration), drop that into a per-portal override file:

```bash
echo "YOUR-SANDBOX-CLIENT-ID" > ~/my-health-data/.client_id.epic_sandbox
chmod 600 ~/my-health-data/.client_id.epic_sandbox
```

At runtime the client uses `.client_id.<portal_name>` if it exists, else falls back to `.client_id`. So `.client_id` = production (works across any Epic customer via USCDI distribution), `.client_id.epic_sandbox` = sandbox-only override.

**3. Authenticate against a portal.**

```bash
python3 /path/to/client.py auth --data-dir ~/my-health-data
```

Your browser opens to the portal's OAuth page. Log in with your MyChart credentials, approve the scopes, and get redirected to `https://127.0.0.1:8765/...`. The browser will warn about a self-signed cert for `127.0.0.1` — click through once ("Advanced → Proceed to 127.0.0.1 (unsafe)"). Tokens are saved to `~/my-health-data/tokens/<portal>.json`.

**4. Pull your FHIR resources.**

```bash
python3 /path/to/client.py sync --data-dir ~/my-health-data
```

This writes JSON files per resource type to `~/my-health-data/exports/<portal>/`. Override the destination with `--exports-dir`.

**Default portal** is `epic_sandbox` (Epic's public test endpoint with fake patients like `fhircamila / epicepic1`). Add your real portals by editing the `PORTALS` dict near the top of `client.py`.

## Command reference

```
python3 client.py auth [--data-dir DIR] [--portal NAME]
python3 client.py sync [--data-dir DIR] [--exports-dir DIR] [--portal NAME]
```

| Flag | Default | Purpose |
|---|---|---|
| `--data-dir` | cwd | Directory holding `.client_id`, `tokens/`, `certs/` |
| `--exports-dir` | `<data-dir>/exports` | Where FHIR JSON is written on sync |
| `--portal` | `epic_sandbox` | Which entry from `PORTALS` to use |

## Privacy and security

- All medical data stays on the user's own device.
- OAuth tokens (access + refresh) are stored locally and are the user's responsibility to protect.
- The `client_id` issued by Epic is embedded in the app — per the SMART on FHIR "public client" model for patient-facing apps. Authentication is anchored in the user's own MyChart login, not in a shared secret.

## License

[MIT](LICENSE).
