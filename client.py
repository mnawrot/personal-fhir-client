#!/usr/bin/env python3
"""Personal FHIR Client — SMART-on-FHIR OAuth + data pull.

Patient-facing client for Epic-powered MyChart portals (and any other
SMART-on-FHIR conformant endpoints added to PORTALS). All data stays on
the user's local device. No cloud, no third parties, no analytics.

Usage:
  python3 client.py auth [--data-dir DIR] [--portal NAME]
  python3 client.py sync [--data-dir DIR] [--exports-dir DIR] [--portal NAME]

Defaults:
  --data-dir     current working directory
  --exports-dir  <data-dir>/exports
  --portal       epic_sandbox

data-dir layout (all gitignored by default):
  .client_id                 # Epic-issued client_id, one line (the default)
  .client_id.<portal_name>   # optional per-portal override (e.g. .client_id.epic_sandbox)
  tokens/<portal>.json       # auto-created; OAuth tokens
  certs/                     # auto-created; self-signed TLS cert for loopback
"""
import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 8765
REDIRECT_URI = f"https://{REDIRECT_HOST}:{REDIRECT_PORT}/smart/callback"

PORTALS = {
    "epic_sandbox": {
        "name": "Epic Sandbox",
        "authorize_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize",
        "token_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token",
        "fhir_base": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    },
}

SCOPES = " ".join([
    "openid", "fhirUser", "launch/patient", "offline_access",
    "patient/AllergyIntolerance.read",
    "patient/CarePlan.read",
    "patient/CareTeam.read",
    "patient/Condition.read",
    "patient/DiagnosticReport.read",
    "patient/DocumentReference.read",
    "patient/Encounter.read",
    "patient/Goal.read",
    "patient/Immunization.read",
    "patient/MedicationDispense.read",
    "patient/MedicationRequest.read",
    "patient/MedicationStatement.read",
    "patient/Observation.read",
    "patient/Patient.read",
    "patient/Procedure.read",
])

RESOURCE_TYPES = [
    "AllergyIntolerance", "CarePlan", "CareTeam", "Condition",
    "Coverage", "Device", "DiagnosticReport", "DocumentReference",
    "Encounter", "ExplanationOfBenefit", "Goal", "Immunization",
    "MedicationDispense", "MedicationRequest", "Observation",
    "Procedure", "ServiceRequest",
]

# Epic requires category/code filters for some resources. We issue one search
# per variant and accumulate, dedup by resource id.
RESOURCE_QUERIES = {
    "Observation": [
        {"category": "laboratory"},
        {"category": "vital-signs"},
        {"category": "social-history"},
        {"category": "smartdata"},
        {"category": "activity"},
        {"category": "therapy"},
        {"category": "exam"},
    ],
    "CarePlan": [
        {"category": "assess-plan"},
    ],
}


def read_client_id(data_dir, portal_key):
    # Per-portal override wins if present; fall back to generic .client_id.
    # Typical setup: .client_id = production ID (works across Epic community
    # members via USCDI distribution); .client_id.epic_sandbox = sandbox ID.
    specific = data_dir / f".client_id.{portal_key}"
    generic = data_dir / ".client_id"
    for p in (specific, generic):
        if p.exists():
            cid = p.read_text().strip()
            if not cid:
                sys.exit(f"[err] {p} is empty.")
            return cid
    sys.exit(
        f"[err] No client_id file found in {data_dir}. "
        f"Create either {generic} or {specific} with your Epic client_id (one line)."
    )


def ensure_cert(cert_dir):
    cert_dir.mkdir(exist_ok=True)
    cert = cert_dir / "localhost.pem"
    key = cert_dir / "localhost-key.pem"
    if cert.exists() and key.exists():
        return cert, key
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(key), "-out", str(cert),
            "-days", "365",
            "-subj", "/CN=127.0.0.1",
            "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost",
        ],
        check=True,
        capture_output=True,
    )
    os.chmod(key, 0o600)
    return cert, key


def pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def auth(portal_key, data_dir):
    client_id = read_client_id(data_dir, portal_key)
    cert_dir = data_dir / "certs"
    token_dir = data_dir / "tokens"
    portal = PORTALS[portal_key]
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "aud": portal["fhir_base"],
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = f"{portal['authorize_url']}?{urllib.parse.urlencode(params)}"

    captured = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            if p.path == "/smart/callback":
                qs = urllib.parse.parse_qs(p.query)
                captured["code"] = qs.get("code", [None])[0]
                captured["state"] = qs.get("state", [None])[0]
                captured["error"] = qs.get("error", [None])[0]
                captured["error_description"] = qs.get("error_description", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                if captured["code"]:
                    msg = "Auth complete. You can close this tab."
                else:
                    msg = f"Error: {captured['error']} — {captured['error_description']}"
                self.wfile.write(
                    f"<!doctype html><html><body style='font-family:sans-serif;padding:2em;'><h2>{msg}</h2></body></html>".encode()
                )
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *_):
            pass

    cert, key = ensure_cert(cert_dir)
    httpd = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(key))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    print(f"[info] Opening browser for {portal['name']} authorization…")
    print(f"[info] Listening on {REDIRECT_URI}")
    print(f"[warn] Browser will flag a TLS warning for the self-signed cert — click 'Advanced' → 'Proceed to 127.0.0.1 (unsafe)'. One-time per session.")
    webbrowser.open(authorize_url)
    while not captured.get("code") and not captured.get("error"):
        try:
            httpd.handle_request()
        except (ssl.SSLError, OSError):
            continue
    httpd.server_close()

    if captured.get("error"):
        sys.exit(f"[err] OAuth error: {captured['error']} — {captured.get('error_description')}")
    if captured.get("state") != state:
        sys.exit("[err] State mismatch — aborting")
    if not captured.get("code"):
        sys.exit("[err] No authorization code returned")

    print("[ok]   Authorization code received. Exchanging for access token.")
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": captured["code"],
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(
        portal["token_url"],
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"[err] Token exchange failed: {e.code} — {e.read().decode()}")

    token_dir.mkdir(exist_ok=True)
    token_path = token_dir / f"{portal_key}.json"
    token_path.write_text(json.dumps(tokens, indent=2))
    os.chmod(token_path, 0o600)
    print(f"[ok]   Tokens saved to {token_path}")
    print(f"[ok]   Patient FHIR ID: {tokens.get('patient')}")
    print(f"[ok]   Access token expires in {tokens.get('expires_in')} s")
    print(f"[ok]   Granted scope: {tokens.get('scope')}")


def sync(portal_key, data_dir, exports_dir):
    token_dir = data_dir / "tokens"
    portal = PORTALS[portal_key]
    token_path = token_dir / f"{portal_key}.json"
    if not token_path.exists():
        sys.exit(f"[err] No tokens at {token_path}. Run `auth` first.")
    tokens = json.loads(token_path.read_text())
    access = tokens["access_token"]
    patient = tokens.get("patient")
    if not patient:
        sys.exit("[err] No patient ID in token response — re-run auth with launch/patient scope")

    out_dir = exports_dir / portal_key
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for rsrc in RESOURCE_TYPES:
        queries = RESOURCE_QUERIES.get(rsrc, [{}])
        entries = []
        seen_ids = set()
        for query in queries:
            params = {"patient": patient, "_count": "200"}
            params.update(query)
            url = f"{portal['fhir_base']}/{rsrc}?{urllib.parse.urlencode(params)}"
            while url:
                req = urllib.request.Request(
                    url,
                    headers={
                        "Authorization": f"Bearer {access}",
                        "Accept": "application/fhir+json",
                    },
                )
                try:
                    with urllib.request.urlopen(req) as resp:
                        bundle = json.loads(resp.read())
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode()[:300]
                    qdesc = ",".join(f"{k}={v}" for k, v in query.items()) or "(no filter)"
                    print(f"[err]  {rsrc} [{qdesc}]: HTTP {e.code} — {err_body}")
                    break
                for entry in bundle.get("entry", []):
                    rid = entry.get("resource", {}).get("id")
                    if rid and rid in seen_ids:
                        continue
                    if rid:
                        seen_ids.add(rid)
                    entries.append(entry)
                url = None
                for link in bundle.get("link", []):
                    if link.get("relation") == "next":
                        url = link["url"]
                        break
        (out_dir / f"{rsrc}.json").write_text(json.dumps(entries, indent=2))
        print(f"[sync] {rsrc:22s} {len(entries):4d} records")
        total += len(entries)

    print(f"[ok]   Wrote {total} resources to {out_dir}/")


def main():
    p = argparse.ArgumentParser(description="Personal FHIR Client — SMART-on-FHIR OAuth + data pull")
    p.add_argument("command", choices=["auth", "sync"])
    p.add_argument("--data-dir", default=".",
                   help="Directory containing .client_id, plus tokens/ and certs/ subdirs (default: cwd)")
    p.add_argument("--exports-dir", default=None,
                   help="Where to write FHIR JSON exports (default: <data-dir>/exports)")
    p.add_argument("--portal", default="epic_sandbox", choices=list(PORTALS.keys()))
    args = p.parse_args()

    data_dir = Path(args.data_dir).expanduser().resolve()
    if not data_dir.is_dir():
        sys.exit(f"[err] data-dir does not exist: {data_dir}")
    exports_dir = Path(args.exports_dir).expanduser().resolve() if args.exports_dir else data_dir / "exports"

    if args.command == "auth":
        auth(args.portal, data_dir)
    elif args.command == "sync":
        sync(args.portal, data_dir, exports_dir)


if __name__ == "__main__":
    main()
