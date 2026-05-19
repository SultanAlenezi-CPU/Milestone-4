import json
import os
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PKI_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "pki"))
CA_CERT_PATH = os.path.join(PKI_DIR, "ca.crt")
CA_KEY_PATH = os.path.join(PKI_DIR, "ca.key")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "enroll_log.jsonl")
PROVISION_LOG_PATH = os.path.join(LOG_DIR, "provision_log.jsonl")

B2_TOKENS_PATH = os.path.join(BASE_DIR, "b2_tokens.json")
B2_TOKENS_EXAMPLE_PATH = os.path.join(BASE_DIR, "b2_tokens.example.json")

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Token store — loaded once at startup, mutations are in-memory only.
# Tokens reset to unused state on server restart, which is the intended
# behaviour for repeatable testbed sessions.
# ---------------------------------------------------------------------------

def _load_token_store():
    """Load token store from b2_tokens.json; fall back to example file."""
    path = B2_TOKENS_PATH if os.path.exists(B2_TOKENS_PATH) else B2_TOKENS_EXAMPLE_PATH
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Build in-memory dict: {token_str: {"used": bool}}
    raw = data.get("tokens", {})
    return {tok: {"used": bool(meta.get("used", False))} for tok, meta in raw.items()}


TOKEN_STORE = _load_token_store()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_ca_material():
    with open(CA_CERT_PATH, "rb") as cert_file:
        ca_cert = x509.load_pem_x509_certificate(cert_file.read())
    with open(CA_KEY_PATH, "rb") as key_file:
        ca_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return ca_cert, ca_key


def _append_log(entry, path=None):
    if path is None:
        path = LOG_PATH
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")


# ---------------------------------------------------------------------------
# Generic after-request logger — catches all routes (enroll_log.jsonl)
# ---------------------------------------------------------------------------

@app.after_request
def _log_request(response):
    request_json = request.get_json(silent=True)
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "run_id": request_json.get("run_id") if isinstance(request_json, dict) else None,
        "device_id": request_json.get("device_id") if isinstance(request_json, dict) else None,
    }
    _append_log(log_entry)
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/enroll")
def enroll():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON body"}), 400

    run_id = payload.get("run_id")
    device_id = payload.get("device_id")
    csr_pem = payload.get("csr_pem")

    if not run_id or not device_id or not csr_pem:
        return (
            jsonify(
                {
                    "error": "Missing required fields",
                    "required_fields": ["run_id", "device_id", "csr_pem"],
                }
            ),
            400,
        )

    try:
        csr = x509.load_pem_x509_csr(csr_pem.encode("utf-8"))
    except ValueError:
        return jsonify({"error": "Invalid csr_pem format"}), 400

    ca_cert, ca_key = _load_ca_material()
    not_before = datetime.now(timezone.utc) - timedelta(minutes=1)
    not_after = datetime.now(timezone.utc) + timedelta(days=365)

    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
    )

    for extension in csr.extensions:
        cert_builder = cert_builder.add_extension(extension.value, extension.critical)

    device_cert = cert_builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
    device_cert_pem = device_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    return (
        jsonify(
            {
                "run_id": run_id,
                "device_id": device_id,
                "device_cert_pem": device_cert_pem,
                "ca_cert_pem": ca_cert_pem,
            }
        ),
        200,
    )


@app.post("/provision")
def provision():
    """
    Baseline 2 — Token/QR provisioning endpoint.

    Accepts: {run_id, device_id, token}
    Validates that the token is known and has not been used before.
    Tokens are single-use (in-memory, reset on server restart).
    Intentionally plaintext — designed to demonstrate token sniffing vulnerability.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON body"}), 400

    run_id = payload.get("run_id")
    device_id = payload.get("device_id")
    token = payload.get("token")

    if not run_id or not device_id or not token:
        return (
            jsonify(
                {
                    "error": "Missing required fields",
                    "required_fields": ["run_id", "device_id", "token"],
                }
            ),
            400,
        )

    token_entry = TOKEN_STORE.get(token)
    token_known = token_entry is not None
    token_used_before = token_entry["used"] if token_known else False

    if not token_known or token_used_before:
        status_code = 401
        response_body = {"error": "invalid or expired token"}
    else:
        TOKEN_STORE[token]["used"] = True
        status_code = 200
        response_body = {
            "run_id": run_id,
            "device_id": device_id,
            "provisioning_status": "ok",
        }

    # Provision-specific log (richer than the generic after_request log)
    provision_log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "POST",
        "path": "/provision",
        "run_id": run_id,
        "device_id": device_id,
        "token_known": token_known,
        "token_used_before": token_used_before,
        "token_valid": token_known and not token_used_before,
        "status_code": status_code,
    }
    _append_log(provision_log_entry, path=PROVISION_LOG_PATH)

    return jsonify(response_body), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
